import csv
from typing import List, Dict, Any

from shapely import wkt as shapely_wkt

def read_ridge_segments(input_csv: str,
                        eid_col: str = "eid",
                        geom_col: str = "geometry",
                        elev_col_1: str = "first vertex elevation",
                        elev_col_2: str = "second vertex elevation",
                        seg_elev_method: str = "max"):
    records = []
    with open(input_csv, "r", newline="", encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f, skipinitialspace=True)
        if reader.fieldnames is None:
            raise ValueError("Input CSV has no header.")

        if eid_col not in reader.fieldnames or geom_col not in reader.fieldnames:
            raise ValueError(
                f'Expected columns "{eid_col}" and "{geom_col}". Got {reader.fieldnames}'
            )

        if elev_col_1 not in reader.fieldnames or elev_col_2 not in reader.fieldnames:
            raise ValueError(
                f'Expected elevation columns "{elev_col_1}" and "{elev_col_2}". Got {reader.fieldnames}'
            )

        for row in reader:
            eid = row.get(eid_col, "")
            wkt_text = row.get(geom_col, "")

            if not wkt_text:
                continue

            try:
                geom = shapely_wkt.loads(wkt_text)
            except Exception:
                continue

            if geom is None or geom.is_empty:
                continue
            if geom.geom_type not in ("LineString", "MultiLineString"):
                continue

            try:                
                e1 = float(row[elev_col_1])
                e2 = float(row[elev_col_2])

                if seg_elev_method == "mean":
                    elev_val = (e1 + e2) / 2.0
                else:
                    elev_val = max(e1, e2)
            except Exception:
                continue

            records.append({
                "row": row,
                "eid": eid,
                "geometry": geom,
                "elevation_anomaly": elev_val,
            })

    if not records:
        raise ValueError("No valid ridge segment geometries were found in the input CSV.")
    return records


def write_segment_output(records: List[Dict[str, Any]],
                         ridge_ids: List[int],
                         output_csv: str) -> None:
    ridge_counts: Dict[int, int] = {}
    for rid in ridge_ids:
        ridge_counts[rid] = ridge_counts.get(rid, 0) + 1

    fieldnames = list(records[0]["row"].keys())
    extra_fields = ["ridge_id", "ridge_seg_length_m", "n_segments_in_ridge"]
    for field in extra_fields:
        if field not in fieldnames:
            fieldnames.append(field)

    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for rec, rid in zip(records, ridge_ids):
            out_row = dict(rec["row"])
            out_row["ridge_id"] = rid
            out_row["ridge_seg_length_m"] = float(rec["geometry"].length)
            out_row["n_segments_in_ridge"] = ridge_counts[rid]
            writer.writerow(out_row)


def write_ridge_output(ridge_rows, output_csv):
    fieldnames = ["ridge_id", "n_segments", "ridge_length_m", "ridge_elevation_anomaly", "member_eids"]
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in ridge_rows:
            writer.writerow(row)


def write_summary_text(stats: Dict[str, float],
                       summary_txt: str,
                       tolerance: float,
                       title: str,
                       value_label: str,
                       key_prefix: str) -> None:
    lines = [
        title,
        "=" * len(title),
        f"Endpoint tolerance (m): {tolerance:.6f}",
        "",
        f"Total number of ridge segments: {int(stats['N_segments_total'])}",
        f"Total number of independent ridges: {int(stats['N_ridges_total'])}",
        f"Mean segments per ridge: {stats['mean_segments_per_ridge']:.6f}",
        f"Median segments per ridge: {stats['median_segments_per_ridge']:.6f}",
        "",
        f"{value_label} distribution:",
        f"  Min:    {stats[f'min_{key_prefix}']:.6f}",
        f"  Q1:     {stats[f'q1_{key_prefix}']:.6f}",
        f"  Median: {stats[f'median_{key_prefix}']:.6f}",
        f"  Mean:   {stats[f'mean_{key_prefix}']:.6f}",
        f"  Q3:     {stats[f'q3_{key_prefix}']:.6f}",
        f"  P90:    {stats[f'p90_{key_prefix}']:.6f}",
        f"  P95:    {stats[f'p95_{key_prefix}']:.6f}",
        f"  Max:    {stats[f'max_{key_prefix}']:.6f}",
        f"  Std:    {stats[f'std_{key_prefix}']:.6f}",
        f"  Mode (hist-bin center): {stats[f'mode_{key_prefix}']:.6f}",
    ]

    with open(summary_txt, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")