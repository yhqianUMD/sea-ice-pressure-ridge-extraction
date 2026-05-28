#!/usr/bin/env python3
"""
ICESat-2 ridge peaks (points) vs extracted ridges (lines).

A peak is matched if any extracted ridge is within `buffer_dist` meters of it
(equivalent to "line intersects point-buffer").

Uses STRtree spatial index on ridges + bbox prefilter on each peak.
Reads peak coords from x_3413_dc / y_3413_dc.
"""

import csv
import argparse
import shapely
import numpy as np
from shapely.geometry import LineString, Point, box
from shapely.strtree import STRtree
import time

SHAPELY2 = int(shapely.__version__.split(".")[0]) >= 2


def parse_linestring_wkt(wkt: str):
    """Parse WKT LINESTRING with any number of vertices. Returns LineString or None."""
    if not wkt:
        return None
    w = wkt.strip()
    if not w.upper().startswith("LINESTRING"):
        return None
    lpar = w.find("(")
    rpar = w.rfind(")")
    if lpar == -1 or rpar == -1 or rpar <= lpar:
        return None

    coords_txt = w[lpar + 1 : rpar].strip()
    pts = []
    for token in coords_txt.split(","):
        parts = token.strip().split()
        if len(parts) < 2:
            continue
        try:
            x = float(parts[0])
            y = float(parts[1])
            pts.append((x, y))
        except ValueError:
            continue

    if len(pts) < 2:
        return None
    return LineString(pts)


def iter_lines_from_csv(csv_path: str, geom_col: str = "geometry"):
    with open(csv_path, "r", newline="", encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f, skipinitialspace=True)
        if reader.fieldnames is None or geom_col not in reader.fieldnames:
            raise ValueError(f'Expected "{geom_col}" column. Got {reader.fieldnames}')
        for row in reader:
            geom = parse_linestring_wkt(row.get(geom_col, ""))
            if geom is not None and not geom.is_empty:
                yield geom


def iter_peaks_from_csv(csv_path: str, x_col="x_3413_dc", y_col="y_3413_dc"):
    with open(csv_path, "r", newline="", encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f, skipinitialspace=True)
        if reader.fieldnames is None or x_col not in reader.fieldnames or y_col not in reader.fieldnames:
            raise ValueError(f'Expected "{x_col}" and "{y_col}" columns. Got {reader.fieldnames}')
        for row in reader:
            try:
                x = float(row[x_col])
                y = float(row[y_col])
            except (ValueError, TypeError, KeyError):
                continue
            yield Point(x, y), row


def build_index(geoms):
    geoms = list(geoms)
    tree = STRtree(geoms)
    return geoms, tree


def peak_matches(pt: Point, ridges, ridge_tree, buffer_dist: float) -> bool:
    # bbox prefilter (fast)
    env = box(pt.x - buffer_dist, pt.y - buffer_dist, pt.x + buffer_dist, pt.y + buffer_dist)
    cand = ridge_tree.query(env)
    if len(cand) == 0:
        return False

    # Shapely 2 STRtree may return indices
    if isinstance(cand[0], (int, np.integer)):
        cand_geoms = (ridges[i] for i in cand)
    else:
        cand_geoms = cand

    # exact check (fast for point-line): distance <= buffer_dist
    if SHAPELY2:
        for ln in cand_geoms:
            if shapely.distance(ln, pt) <= buffer_dist:
                return True
    else:
        for ln in cand_geoms:
            if ln.distance(pt) <= buffer_dist:
                return True

    return False


def evaluate(extracted_ridges_csv: str, peaks_csv: str, buffer_dist: float = 5.0, out_unmatched: str | None = None):
    # Build ridge index once (dominant memory cost)
    ridges, ridge_tree = build_index(iter_lines_from_csv(extracted_ridges_csv))

    total = 0
    matched = 0
    unmatched_rows = []

    # Stream peaks (no need to load all peaks into memory)
    for pt, row in iter_peaks_from_csv(peaks_csv, x_col="x_3413_dc", y_col="y_3413_dc"):
        total += 1
        if peak_matches(pt, ridges, ridge_tree, buffer_dist):
            matched += 1
        elif out_unmatched is not None:
            unmatched_rows.append(row)

    pct = (matched / total * 100.0) if total else float("nan")

    if out_unmatched is not None:
        # write unmatched peaks (could still be big; if huge, write streaming instead)
        with open(out_unmatched, "w", newline="", encoding="utf-8") as f:
            if unmatched_rows:
                fieldnames = list(unmatched_rows[0].keys())
            else:
                # fallback: reuse input headers
                with open(peaks_csv, "r", newline="", encoding="utf-8", errors="ignore") as fin:
                    fieldnames = csv.DictReader(fin).fieldnames or ["x_3413_dc", "y_3413_dc"]
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            for r in unmatched_rows:
                w.writerow(r)

    return {
        "buffer_dist_m": buffer_dist,
        "N_total_peaks": total,
        "N_matched_peaks": matched,
        "percent_matched_peaks": pct,
        "N_unmatched_peaks": max(0, total - matched),
        "N_ridge_lines_indexed": len(ridges),
    }

if __name__ == "__main__":
    # extracted ridges (lines)
    reference_csv = input("reference ridge peaks CSV: ").strip()
    # ICESat-2 ridge peaks (points)
    extracted_csv = input("extracted ridges CSV: ").strip()
    d = float(input("buffer distance (e.g. 5m): ").strip())

    t_start = time.time()
    out = evaluate(extracted_csv, reference_csv, d)
    for k, v in out.items():
        if isinstance(v, float):
            print(f"{k}: {v:.6f}")
        else:
            print(f"{k}: {v}")
    
    t_end = time.time()
    print("Total time cost of this program:", t_end - t_start)
    