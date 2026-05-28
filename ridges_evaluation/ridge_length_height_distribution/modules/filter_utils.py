import csv
from typing import Dict

def filter_ridge_rows_by_length(ridge_rows, length_threshold_m):
    """
    Keep only ridges whose ridge_length_m is greater than length_threshold_m.
    """
    return [
        row for row in ridge_rows
        if row["ridge_length_m"] > length_threshold_m
    ]


def write_max_length_ridge_segments(records, ridge_ids, ridge_rows, output_csv):
    """
    Find the ridge with the maximum ridge_length_m and export all of its
    original segment rows to a CSV file for QGIS.
    """
    if not ridge_rows:
        raise ValueError("ridge_rows is empty.")

    max_ridge = max(ridge_rows, key=lambda r: r["ridge_length_m"])
    max_ridge_id = max_ridge["ridge_id"]

    fieldnames = list(records[0]["row"].keys())
    extra_fields = ["ridge_id", "ridge_seg_length_m"]

    for f in extra_fields:
        if f not in fieldnames:
            fieldnames.append(f)

    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for rec, rid in zip(records, ridge_ids):
            if rid != max_ridge_id:
                continue
            out_row = dict(rec["row"])
            out_row["ridge_id"] = rid
            out_row["ridge_seg_length_m"] = float(rec["geometry"].length)
            writer.writerow(out_row)

    return max_ridge_id, max_ridge["ridge_length_m"]


def write_long_ridge_segments(records, ridge_ids, ridge_rows, length_threshold_m, output_csv):
    """
    Export all original segment rows whose parent ridge has
    ridge_length_m > length_threshold_m.
    """
    if not ridge_rows:
        raise ValueError("ridge_rows is empty.")

    selected_ridge_ids = {
        row["ridge_id"] for row in ridge_rows
        if row["ridge_length_m"] > length_threshold_m
    }

    fieldnames = list(records[0]["row"].keys())
    extra_fields = ["ridge_id", "ridge_seg_length_m", "parent_ridge_length_m"]

    for f in extra_fields:
        if f not in fieldnames:
            fieldnames.append(f)

    ridge_len_map = {
        row["ridge_id"]: row["ridge_length_m"]
        for row in ridge_rows
    }

    n_selected_segments = 0
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for rec, rid in zip(records, ridge_ids):
            if rid not in selected_ridge_ids:
                continue

            out_row = dict(rec["row"])
            out_row["ridge_id"] = rid
            out_row["ridge_seg_length_m"] = float(rec["geometry"].length)
            out_row["parent_ridge_length_m"] = ridge_len_map[rid]
            writer.writerow(out_row)
            n_selected_segments += 1

    return {
        "n_selected_ridges": len(selected_ridge_ids),
        "n_selected_segments": n_selected_segments,
        "length_threshold_m": length_threshold_m,
    }