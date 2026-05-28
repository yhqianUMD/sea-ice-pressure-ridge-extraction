#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Converted from Jupyter notebook: Read_ICESat-2_projection_drift_correct.ipynb

This script provides utilities to:
  1) Project ICESat-2 (lon,lat) points to EPSG:3413
  2) Apply drift correction using velocities (vx, vy) and a reference time (delta_time)
  3) Optionally write CSV and GeoPackage outputs
  4) Convert between UTC timestamps and ICESat-2 delta_time (seconds since 2018-01-01 GPS)
"""

from __future__ import annotations

import argparse
from pathlib import Path
import numpy as np
import pandas as pd
from pyproj import CRS, Transformer
import time

# For geometry output
import geopandas as gpd
from shapely.geometry import Point

#!/usr/bin/env python3
"""
Read a comma-separated TXT file with columns:
  lon, lat, time, ele
Project lon/lat (EPSG:4326) to x/y in EPSG:3413,
apply constant drift correction (vx, vy),
and store drift-corrected coordinates as Point geometry.

Usage:
  python project_txt_to_3413_drift.py input.txt --vx 12.3 --vy -45.6
  python project_txt_to_3413_drift.py input.txt --vx 12.3 --vy -45.6 --out_csv out.csv --out_gpkg out.gpkg
"""

def project_txt(
    in_txt: str,
    dx: float = 0.0,
    dy: float = 0.0,
    delta_time: float = 0.0,
    sys_error_correct: float = 0.0,
    out_csv: str | None = None,
    out_txt: str | None = None,
    out_gpkg: str | None = None,
    save_csv: bool = True,
    save_txt: bool = False,
    save_gpkg: bool = False,
    already_project_epsg3413: bool = False,
) -> tuple[Path, Path | None]:
    in_path = Path(in_txt)

    date = time.strftime("%m,%d,%Y")
    date_name = date.split(',')[0] + date.split(',')[1] + date.split(',')[2]

    # Default output paths
    if out_csv is None:
        out_csv_path = in_path.with_suffix("").with_name(in_path.stem + "_epsg3413_drift_" + str(vx) + '_' + str(vy) + '_' + date_name + ".csv")
    else:
        out_csv_path = Path(out_csv)
    
    if out_txt is None:
        out_txt_path = in_path.with_suffix("").with_name(in_path.stem + "_epsg3413_drift_xy_" + str(vx) + '_' + str(vy) + '_' + date_name + ".txt")
    else:
        out_txt_path = Path(out_txt)

    if out_gpkg is None:
        out_gpkg_path = in_path.with_suffix("").with_name(in_path.stem + "_epsg3413_drift_" + date_name + ".gpkg")
    else:
        out_gpkg_path = Path(out_gpkg)

    if not already_project_epsg3413:
        # Read: lon, lat, time, ele (comma-separated, no header)
        df = pd.read_csv(
            in_path,
            header=None,
            names=["lon", "lat", "time", "ele"],
            sep=",",
            engine="c",
            comment="#",
            skip_blank_lines=True,
        )

        # Ensure numeric (robust to stray whitespace)
        for c in ["lon", "lat", "time", "ele"]:
            df[c] = pd.to_numeric(df[c], errors="coerce")

        # Drop rows that can't be projected
        valid = np.isfinite(df["lon"].to_numpy()) & np.isfinite(df["lat"].to_numpy())
        df = df.loc[valid].reset_index(drop=True)
    
        # Project lon/lat to EPSG:3413
        transformer = Transformer.from_crs(
            CRS.from_epsg(4326),  # WGS84 lon/lat
            CRS.from_epsg(3413),  # NSIDC Sea Ice Polar Stereographic North
            always_xy=True
        )

        lon = df["lon"].to_numpy(dtype=np.float64)
        lat = df["lat"].to_numpy(dtype=np.float64)
        x_3413, y_3413 = transformer.transform(lon, lat)

        df["x_3413"] = x_3413
        df["y_3413"] = y_3413
    else: # already projected to 3413
        df = pd.read_csv(in_path)
        for c in ["x_3413", "y_3413", "time", "ele"]:
            df[c] = pd.to_numeric(df[c], errors="coerce").to_numpy(dtype=np.float64)

    # ---- Drift correction (constant offsets, in same units as EPSG:3413, i.e., meters) ----
    t = df["time"].to_numpy(dtype=np.float64)
    dt = delta_time - t  # seconds since reference
    # df["x_3413_dc"] = df["x_3413"] + vx * dt
    # df["y_3413_dc"] = df["y_3413"] + vy * dt
    df["x_3413_dc"] = df["x_3413"] + dx
    df["y_3413_dc"] = df["y_3413"] + dy
    df["ele"] -= sys_error_correct

    # Quick sanity prints
    print(f"Read {len(df):,} valid rows from: {in_path}")
    print(f"Drift velocity: dx={dx} m/s, dy={dy} m/s")
    print(f"X_3413 range:    {np.nanmin(df['x_3413']):.3f} to {np.nanmax(df['x_3413']):.3f}")
    print(f"Y_3413 range:    {np.nanmin(df['y_3413']):.3f} to {np.nanmax(df['y_3413']):.3f}")
    print(f"X_3413_dc range: {np.nanmin(df['x_3413_dc']):.3f} to {np.nanmax(df['x_3413_dc']):.3f}")
    print(f"Y_3413_dc range: {np.nanmin(df['y_3413_dc']):.3f} to {np.nanmax(df['y_3413_dc']):.3f}")

    # Save CSV
    # df.to_csv(out_csv_path, index=False)
    if save_csv:
        # cols_out = ["x_3413_dc", "y_3413_dc", "ele"]
        cols_out = ["x_3413_dc", "y_3413_dc", "time", "ele"]
        df_out = df[cols_out]

        df_out.to_csv(out_csv_path, index=False)
        print(f"Wrote CSV:  {out_csv_path}")

    # Save txt with only x and y, and the first row specifies the number of points
    if save_txt:
        write_xy_count_txt(out_txt_path, df["x_3413_dc"], df["y_3413_dc"])
        print(f"Wrote XY TXT: {out_txt_path}")

    if save_csv and save_gpkg:
        gdf = gpd.GeoDataFrame(
            df_out.copy(),
            geometry=gpd.points_from_xy(df_out["x_3413_dc"], df_out["y_3413_dc"]),
            crs="EPSG:3413"
        )

        # Write to GeoPackage (recommended) - works well in QGIS/ArcGIS
        # Layer name can be customized; default "points"
        gdf.to_file(out_gpkg_path, layer="points", driver="GPKG")
        print(f"Wrote GPKG: {out_gpkg_path}")

    return out_csv_path

def write_xy_count_txt(out_txt: str | Path, x: np.ndarray, y: np.ndarray, fmt: str = "%.6f") -> Path:
    """
    Write a TXT file:
      line 1: number of points (N)
      lines 2..N+1: "x y" per line

    Args:
      out_txt: output path
      x, y: 1D arrays of same length
      fmt: float format for x/y
    """
    out_txt = Path(out_txt)
    x = np.asarray(x).ravel()
    y = np.asarray(y).ravel()
    if x.size != y.size:
        raise ValueError(f"x and y length mismatch: {x.size} vs {y.size}")

    N = x.size
    with out_txt.open("w", newline="\n") as f:
        f.write(f"{N}\n")
        # write one point per line
        for xi, yi in zip(x, y):
            f.write((fmt % xi) + " " + (fmt % yi) + "\n")

    return out_txt

if __name__ == "__main__":    
    # method to call drift correct partitioned ICESat-2 profile in csv file with headers ["time", "ele", "x_3413", "y_3413"]
    out = project_txt(
        in_txt=r"C:/Users/yhqian/Downloads/QGIS_maps/PointClouds_2_Raster/ICESat-2/strong_beams/UMDRDA_ATL03_20190410152144_01890303_007_01_gt2l_DTU21_ModifiedYuehui_SailHeight_subset_FINAL.txt",
        dx= -128.5,
        dy= -5.91,
        delta_time= 40154361.5,
        sys_error_correct= 0, # a system error correct of elevations for ICESat-2
        out_csv=r'C:/Users/yhqian/Downloads/QGIS_maps/PointClouds_2_Raster/ICESat-2/strong_beams/QGIS_partition/UMDRDA_ATL03_20190410152144_01890303_007_01_gt2l_DTU21_ModifiedYuehui_SailHeight_subset_FINAL_epsg3413_drift_correct_dx0128.5_dy05.91_0420.csv',
        out_txt= r'C:/Users/yhqian/Downloads/QGIS_maps/PointClouds_2_Raster/ICESat-2/strong_beams/QGIS_partition/UMDRDA_ATL03_20190410152144_01890303_007_01_gt2l_DTU21_ModifiedYuehui_SailHeight_subset_FINAL_epsg3413_drift_correct_dx0128.5_dy05.91_0420.txt',
        out_gpkg= None,
        save_csv= True,
        save_txt= False,
        save_gpkg= False,
        already_project_epsg3413= False,
    )
    print(f"Wrote drift-corrected file to: {out}")
