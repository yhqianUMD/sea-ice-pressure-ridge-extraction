#!/usr/bin/env python3

import csv
import time
from typing import List, Tuple, Dict, Any
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

from modules.io_utils import read_ridge_segments, write_summary_text
from modules.geometry_utils import assign_ridge_ids
from modules.stats_utils import summarize_ridges, summarize_filtered_ridge_rows
from modules.plot_utils import save_histogram
from modules.filter_utils import filter_ridge_rows_by_length, write_long_ridge_segments, write_max_length_ridge_segments

import shapely
from shapely import wkt as shapely_wkt
from shapely.geometry import Point
from shapely.strtree import STRtree

SHAPELY2 = int(shapely.__version__.split(".")[0]) >= 2

def main():
    print("=== Filter ridges and save filtered distributions ===")

    # the original ridges, e.g., C:\Users\yhqian\Downloads\ridges_csv\ALS_L1B_20190410T174554_181213_3\ALS_L1B_20190410T174554_181213_3_as_100000_A1_saddle_toposimp_from_r1_merge_r2_resimplify_r6_simplify_ele_0.25_HA_0.5_rough_0.02_01262026.csv
    input_csv = input("Input ridge CSV: ").strip()

    input_path = Path(input_csv)

    # the predefined ridge length for filtering, e.g., 3 m
    length_threshold_txt = input("Ridge-length threshold in meters: ").strip()
    length_threshold_m = float(length_threshold_txt)
    
    # the file name of Output filtered ridges CSV for QGIS
    output_filtered_ridges_csv = input_path.with_name(input_path.stem + "_filtered_" + str(length_threshold_m) + "_m.csv")

    # the file name of Output maximum-length ridge CSV for QGIS
    output_max_ridge_csv = input_path.with_name(input_path.stem + "_maxLength.csv")

    # Output filtered ridge-length summary TXT
    output_filtered_length_summary_txt = input_path.with_name(input_path.stem + "_filtered_" + str(length_threshold_m) + "m_sum_len.txt")
    # Output filtered ridge-length figure PDF
    output_filtered_length_fig_pdf = input_path.with_name(input_path.stem + "_filtered_" + str(length_threshold_m) + "_m_hist_len.pdf")

    # Output filtered ridge-elevation summary TXT
    output_filtered_elev_summary_txt = input_path.with_name(input_path.stem + "_filtered_" + str(length_threshold_m) + "m_sum_ele.txt")
    # Output filtered ridge-elevation figure PDF
    output_filtered_elev_fig_pdf = input_path.with_name(input_path.stem + "_filtered_" + str(length_threshold_m) + "_m_hist_ele.pdf")

    tolerance_txt = input("Endpoint proximity tolerance in meters [default 0.1]: ").strip()
    tolerance = float(tolerance_txt) if tolerance_txt else 0.1

    length_bin_width_txt = input("Filtered ridge-length histogram bin width in meters [default 10]: ").strip()
    length_bin_width = float(length_bin_width_txt) if length_bin_width_txt else 10.0

    length_xmax_txt = input("Filtered ridge-length histogram x-axis max in meters [default 400]: ").strip()
    length_xmax = float(length_xmax_txt) if length_xmax_txt else 400.0

    elev_bin_width_txt = input("Filtered elevation-anomaly histogram bin width in meters [default 0.1]: ").strip()
    elev_bin_width = float(elev_bin_width_txt) if elev_bin_width_txt else 0.1

    elev_xmax_txt = input("Filtered elevation-anomaly histogram x-axis max in meters [default 5.0]: ").strip()
    elev_xmax = float(elev_xmax_txt) if elev_xmax_txt else 5.0

    ridge_elev_method = input('Ridge anomaly aggregation method [default "max"; options: max, mean]: ').strip().lower()
    if ridge_elev_method not in ("max", "mean"):
        ridge_elev_method = "max"

    t_start = time.time()

    records = read_ridge_segments(
        input_csv=input_csv,
        eid_col="eid",
        geom_col="geometry",
    )

    ridge_ids = assign_ridge_ids(records, tolerance=tolerance)

    ridge_rows, _, _, _, _ = summarize_ridges(
        records, ridge_ids, ridge_elev_method=ridge_elev_method
    )

    max_ridge_id, max_ridge_length = write_max_length_ridge_segments(
        records, ridge_ids, ridge_rows, output_max_ridge_csv
    )

    long_ridge_out = write_long_ridge_segments(
        records, ridge_ids, ridge_rows, length_threshold_m, output_filtered_ridges_csv
    )

    filtered_ridge_rows = filter_ridge_rows_by_length(ridge_rows, length_threshold_m)

    filtered_length_stats, filtered_elev_stats, filtered_lengths, filtered_elevations = summarize_filtered_ridge_rows(
        filtered_ridge_rows
    )

    write_summary_text(
        filtered_length_stats,
        output_filtered_length_summary_txt,
        tolerance,
        title=f"Filtered ridge length distribution summary (length > {length_threshold_m:.2f} m)",
        value_label="Ridge length (m)",
        key_prefix="ridge_length_m",
    )

    write_summary_text(
        filtered_elev_stats,
        output_filtered_elev_summary_txt,
        tolerance,
        title=f"Filtered ridge sail elevation anomaly distribution summary (length > {length_threshold_m:.2f} m)",
        value_label="Ridge sail elevation anomaly (m)",
        key_prefix="ridge_elevation_anomaly_m",
    )

    save_histogram(
        filtered_lengths,
        output_filtered_length_fig_pdf,
        filtered_length_stats,
        value_label="Ridge length (m)",
        key_prefix="ridge_length_m",
        bin_width=length_bin_width,
        x_max=length_xmax,
    )

    save_histogram(
        filtered_elevations,
        output_filtered_elev_fig_pdf,
        filtered_elev_stats,
        value_label="Ridge sail elevation anomaly (m)",
        key_prefix="ridge_elevation_anomaly_m",
        bin_width=elev_bin_width,
        x_max=elev_xmax,
    )

    print("\nDone.")
    print(f"Filtered ridges CSV:         {output_filtered_ridges_csv}")
    print(f"Selected ridges:             {long_ridge_out['n_selected_ridges']}")
    print(f"Selected segments:           {long_ridge_out['n_selected_segments']}")
    print(f"Filtered length summary TXT: {output_filtered_length_summary_txt}")
    print(f"Filtered length figure PDF:  {output_filtered_length_fig_pdf}")
    print(f"Filtered elev summary TXT:   {output_filtered_elev_summary_txt}")
    print(f"Filtered elev figure PDF:    {output_filtered_elev_fig_pdf}")
    print(f"Max-length ridge ID:         {max_ridge_id}")
    print(f"Max-length ridge (m):        {max_ridge_length:.6f}")
    print(f"Max-length ridge CSV:        {output_max_ridge_csv}")

    t_end = time.time()
    print(f"\nTotal time cost of this program: {t_end - t_start:.6f} seconds")

if __name__ == "__main__":
    main()