import numpy as np

from typing import Dict

def compute_distribution_stats(values: np.ndarray,
                               seg_counts: np.ndarray,
                               n_segments_total: int,
                               n_ridges_total: int,
                               key_prefix: str,
                               mode_bin_width: float | None = None,
                               mode_x_min: float | None = None,
                               mode_x_max: float | None = None):
    """
    Compute summary statistics.
    If mode_bin_width is provided, the mode is estimated from a histogram
    with fixed bin width and optional fixed x-range.
    Otherwise, fallback to np.histogram(..., bins="auto").
    """

    if mode_bin_width is not None:
        x_min = float(np.min(values)) if mode_x_min is None else mode_x_min
        x_max = float(np.max(values)) if mode_x_max is None else mode_x_max

        if x_max <= x_min:
            x_max = x_min + mode_bin_width

        bin_edges = np.arange(x_min, x_max + mode_bin_width, mode_bin_width)
        if len(bin_edges) < 2:
            bin_edges = np.array([x_min, x_min + mode_bin_width])

        hist_counts, hist_edges = np.histogram(values, bins=bin_edges)
    else:
        hist_counts, hist_edges = np.histogram(values, bins="auto")

    mode_idx = int(np.argmax(hist_counts))
    mode_val = float((hist_edges[mode_idx] + hist_edges[mode_idx + 1]) / 2.0)

    return {
        "N_segments_total": float(n_segments_total),
        "N_ridges_total": float(n_ridges_total),
        "mean_segments_per_ridge": float(np.mean(seg_counts)),
        "median_segments_per_ridge": float(np.median(seg_counts)),
        f"min_{key_prefix}": float(np.min(values)),
        f"q1_{key_prefix}": float(np.percentile(values, 25)),
        f"median_{key_prefix}": float(np.median(values)),
        f"mean_{key_prefix}": float(np.mean(values)),
        f"q3_{key_prefix}": float(np.percentile(values, 75)),
        f"p90_{key_prefix}": float(np.percentile(values, 90)),
        f"p95_{key_prefix}": float(np.percentile(values, 95)),
        f"max_{key_prefix}": float(np.max(values)),
        f"std_{key_prefix}": float(np.std(values, ddof=0)),
        f"mode_{key_prefix}": mode_val,
    }


def summarize_ridges(records, ridge_ids, ridge_elev_method="max"):
    ridge_map = {}

    for rec, rid in zip(records, ridge_ids):
        seg_len = float(rec["geometry"].length)
        seg_elev = float(rec["elevation_anomaly"])

        if rid not in ridge_map:
            ridge_map[rid] = {
                "ridge_id": rid,
                "n_segments": 0,
                "ridge_length_m": 0.0,
                "member_eids": [],
                "segment_elevations": [],
            }

        ridge_map[rid]["n_segments"] += 1
        ridge_map[rid]["ridge_length_m"] += seg_len
        ridge_map[rid]["member_eids"].append(str(rec["eid"]))
        ridge_map[rid]["segment_elevations"].append(seg_elev)

    ridge_rows = []
    for rid in sorted(ridge_map.keys()):
        row = ridge_map[rid]
        elevs = np.array(row["segment_elevations"], dtype=float)

        if ridge_elev_method == "mean":
            ridge_elev = float(np.mean(elevs))
        else:
            ridge_elev = float(np.max(elevs))

        ridge_rows.append({
            "ridge_id": row["ridge_id"],
            "n_segments": row["n_segments"],
            "ridge_length_m": row["ridge_length_m"],
            "ridge_elevation_anomaly": ridge_elev,
            "member_eids": ";".join(row["member_eids"]),
        })

    lengths = np.array([row["ridge_length_m"] for row in ridge_rows], dtype=float)
    elevations = np.array([row["ridge_elevation_anomaly"] for row in ridge_rows], dtype=float)
    seg_counts = np.array([row["n_segments"] for row in ridge_rows], dtype=float)

    if len(lengths) == 0:
        raise ValueError("No ridge objects were created.")
    
    length_stats = compute_distribution_stats(
        lengths, seg_counts, len(records), len(ridge_rows),
        "ridge_length_m",
        mode_bin_width=10.0
    )

    elev_stats = compute_distribution_stats(
        elevations, seg_counts, len(records), len(ridge_rows), "ridge_elevation_anomaly_m"
    )

    return ridge_rows, length_stats, elev_stats, lengths, elevations


def summarize_filtered_ridge_rows(filtered_ridge_rows):
    """
    Compute length/elevation distributions directly from an already filtered
    ridge_rows list.
    """
    if not filtered_ridge_rows:
        raise ValueError("No ridges remain after filtering.")

    lengths = np.array([row["ridge_length_m"] for row in filtered_ridge_rows], dtype=float)
    elevations = np.array([row["ridge_elevation_anomaly"] for row in filtered_ridge_rows], dtype=float)
    seg_counts = np.array([row["n_segments"] for row in filtered_ridge_rows], dtype=float)

    n_segments_total = int(np.sum(seg_counts))
    n_ridges_total = len(filtered_ridge_rows)

    length_stats = compute_distribution_stats(
        lengths, seg_counts, n_segments_total, n_ridges_total, "ridge_length_m"
    )
    elev_stats = compute_distribution_stats(
        elevations, seg_counts, n_segments_total, n_ridges_total, "ridge_elevation_anomaly_m"
    )

    return length_stats, elev_stats, lengths, elevations

