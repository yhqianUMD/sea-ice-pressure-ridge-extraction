import csv
import re
import numpy as np
from shapely.geometry import LineString
from shapely.strtree import STRtree
import time

WKT_RE = re.compile(
    r'LINESTRING\s*\(\s*([-\d.eE]+)\s+([-\d.eE]+)\s*,\s*([-\d.eE]+)\s+([-\d.eE]+)\s*\)'
)

def load_segments_from_csv(csv_path):
    """Load all 2-point line segments as an (N, 2, 2) numpy array and Shapely lines."""
    coords = []
    with open(csv_path, "r", newline="", encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f, skipinitialspace=True)
        if "geometry" not in reader.fieldnames:
            raise ValueError(f'Expected a "geometry" column. Got {reader.fieldnames}')
        for row in reader:
            m = WKT_RE.search(row["geometry"])
            if not m:
                continue
            x0, y0, x1, y1 = map(float, m.groups())
            coords.append(((x0, y0), (x1, y1)))

    arr = np.array(coords, dtype=np.float64)          # shape (N, 2, 2)
    lines = [LineString(c) for c in coords]
    return arr, lines


# ── vectorised segment-to-segment distance ──────────────────────────
def _seg_closest_t(P, D, Q):
    """For segment P+t*D (t in [0,1]), return clamped t closest to point Q."""
    PQ = Q - P
    d2 = np.einsum("...i,...i->...", D, D)             # |D|^2
    t = np.where(d2 > 0, np.einsum("...i,...i->...", PQ, D) / d2, 0.0)
    return np.clip(t, 0.0, 1.0)

def min_dist_segments(A0, A1, B0, B1):
    """
    Minimum distance between segment A0→A1 and segment B0→B1.
    All inputs broadcastable (…, 2).  Returns scalar or array of distances.
    """
    dA = A1 - A0
    dB = B1 - B0

    # closest approach on the infinite lines
    b = np.einsum("...i,...i->...", dA, dB)
    d00 = np.einsum("...i,...i->...", dA, dA)
    d11 = np.einsum("...i,...i->...", dB, dB)
    denom = d00 * d11 - b * b

    r = A0 - B0
    d02 = np.einsum("...i,...i->...", dA, r)
    d12 = np.einsum("...i,...i->...", dB, r)

    parallel = denom < 1e-20
    s = np.where(parallel, 0.0, np.clip((b * d12 - d11 * d02) / denom, 0, 1))
    t = np.where(parallel, 0.0, np.clip((d00 * d12 - b * d02) / denom, 0, 1))

    # re-clamp in two rounds (standard segment-segment recipe)
    t = _seg_closest_t(B0, dB, A0 + s[..., None] * dA)
    s = _seg_closest_t(A0, dA, B0 + t[..., None] * dB)
    t = _seg_closest_t(B0, dB, A0 + s[..., None] * dA)

    diff = (A0 + s[..., None] * dA) - (B0 + t[..., None] * dB)
    return np.sqrt(np.einsum("...i,...i->...", diff, diff))


# ── matched length via numpy distance sampling ──────────────────────
def matched_length_numpy(A_arr, A_lines, B_arr, B_lines, buffer_dist):
    """
    For each segment in A, estimate the fraction of its length that lies
    within *buffer_dist* of any segment in B, using the STRtree for candidate
    pruning and vectorised segment-segment distance for the actual check.
    """
    if len(A_arr) == 0 or len(B_arr) == 0:
        total_A = sum(a.length for a in A_lines)
        return total_A, 0.0

    # Build STRtree on B bounding boxes expanded by buffer_dist
    B_boxes = [line.buffer(buffer_dist, cap_style="flat").envelope for line in B_lines]
    tree = STRtree(B_boxes)

    # Precompute B endpoints
    B0 = B_arr[:, 0, :]   # (M, 2)
    B1 = B_arr[:, 1, :]   # (M, 2)

    total_A = 0.0
    matched = 0.0
    N_SAMPLE = 10          # points per segment for length estimation

    # Fraction along each A segment to sample
    fracs = np.linspace(0.0, 1.0, N_SAMPLE + 1)      # include both endpoints

    for i, a_line in enumerate(A_lines):
        seg_len = a_line.length
        total_A += seg_len
        if seg_len == 0:
            continue

        # STRtree candidate query
        cand_idx = tree.query(a_line.buffer(buffer_dist, cap_style="flat"))
        if len(cand_idx) == 0:
            continue

        # A segment endpoints
        a0 = A_arr[i, 0]   # (2,)
        a1 = A_arr[i, 1]   # (2,)

        # Sample points along A
        Ps = a0[None, :] + fracs[:, None] * (a1 - a0)[None, :]  # (N_SAMPLE+1, 2)

        # B candidate endpoints
        cb0 = B0[cand_idx]  # (C, 2)
        cb1 = B1[cand_idx]  # (C, 2)

        # Distance from each sample point to each candidate B segment
        # Broadcast: Ps (S,1,2) vs cb0/cb1 (1,C,2) → (S, C)
        dists = min_dist_segments(
            Ps[:, None, :], Ps[:, None, :],   # point = degenerate segment
            cb0[None, :, :], cb1[None, :, :]
        )
        # For each sample point, min distance over all B candidates
        min_d = dists.min(axis=1)              # (S,)

        # Count fraction of sub-intervals where BOTH endpoints are within buffer
        inside = min_d <= buffer_dist          # (S,)
        # Use trapezoidal-style: interval is "matched" if both ends are inside
        intervals_matched = inside[:-1] & inside[1:]
        matched += seg_len * intervals_matched.sum() / N_SAMPLE

    return total_A, matched

def precision_recall_csv(reference_csv, extracted_csv, buffer_dist=0.5):
    ref_arr, ref_lines = load_segments_from_csv(reference_csv)
    ext_arr, ext_lines = load_segments_from_csv(extracted_csv)

    # Recall: how much of reference is covered by extracted buffer
    L_R, M_R = matched_length_numpy(ref_arr, ref_lines, ext_arr, ext_lines, buffer_dist)
    recall = M_R / L_R if L_R > 0 else float("nan")

    # Precision: how much of extracted is covered by reference buffer
    L_E, M_E = matched_length_numpy(ext_arr, ext_lines, ref_arr, ref_lines, buffer_dist)
    precision = M_E / L_E if L_E > 0 else float("nan")

    return {
        "buffer_dist": buffer_dist,
        "L_R_total_ref": L_R,
        "M_R_matched_ref": M_R,
        "recall_len_based": recall,
        "L_E_total_ext": L_E,
        "M_E_matched_ext": M_E,
        "precision_len_based": precision,
        "FN_len_missing_ref": max(0.0, L_R - M_R),
        "FP_len_extra_ext": max(0.0, L_E - M_E),
    }

# Example
if __name__ == "__main__":
    # reference_csv = 'C:\Users\yhqian\Downloads\ridges_csv\ALS_L1B_20190410T183726_185444_1_pers_025\ALS_L1B_20190410T183726_185444_1_after_0.25_l0_roughness_filtered_r0.08_Rayleigh_enabled_kv_200_asc1cells_filtered_ridge_lines_wkt_rela0.csv'
    # reference_csv = 'C:\Users\yhqian\Downloads\ridges_csv\ALS_L1B_20190410T153919_155000_1_pers_025\ALS_L1B_20190410T153919_155000_1_after_0.25_l0_roughness_filtered_r0.08_Rayleigh_enabled_kv_200_asc1cells_filtered_ridge_lines_wkt.csv'
    reference_csv = input("reference ridges CSV: ").strip()
    extracted_csv = input("extracted ridges CSV: ").strip()
    d = float(input("buffer distance (e.g. 1.0): ").strip())

    t_start = time.time()

    out = precision_recall_csv(reference_csv, extracted_csv, buffer_dist=d)
    for k, v in out.items():
        print(f"{k}: {v:.6f}" if isinstance(v, float) else f"{k}: {v}")
    
    t_end = time.time()
    print("Total time cost of this program:", t_end - t_start)