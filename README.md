# Code for Extracting and Evaluating Sea-Ice Pressure Ridges

This repository contains the code used for extracting and evaluating sea-ice pressure ridges from IceBird airborne laser scanner (ALS) point clouds. The workflow is based on a distributed topology-based approach implemented with Apache Spark. The input surface is represented as a triangulated irregular network (TIN), and pressure ridges are extracted as connected ridge structures from the triangulated sea-ice surface.

The code is organized into four main folders:

```text
.
├── drift_correction/
├── ridge_line_extraction_Apache_Spark/
├── ridges_evaluation/
└── TIN_evaluation_with_ICESat-2_profile/
```

## Folder Description

### `ridge_line_extraction_Apache_Spark/`

This folder contains the main code for extracting sea-ice pressure ridges using the Apache Spark-based distributed workflow.

The input is a TIN file in OFF format. The code computes the surface network of the TIN, applies distributed topological simplification, and extracts candidate pressure ridge lines. The final output is a CSV file containing the extracted ridge lines.

This folder corresponds to the main ridge-extraction methodology described in the accompanying paper, including surface-network computation, distributed topological simplification, and postprocessing of ridge candidates.

**Input:**

- TIN surface model in `.off` format

**Output:**

- Extracted ridge lines in `.csv` format

### `drift_correction/`

This folder contains code for correcting sea-ice drift between the ICESat-2 overpass and the IceBird ALS acquisition.

Because ICESat-2 and IceBird observations were collected at different times, sea ice may have drifted between the two acquisitions. The scripts in this folder are used to estimate and apply a spatial correction so that the ICESat-2 profile and ridge locations can be better aligned with the IceBird point cloud or TIN surface.

**Input:**

- Two DEMs correspond to two ALS segments collected at the same location but in different time

**Output:**

- Drift-corrected ICESat-2 profile

### `TIN_evaluation_with_ICESat-2_profile/`

This folder contains code for evaluating the generated TIN surface by comparing it with a spatiotemporally coincident ICESat-2 elevation profile.

The evaluation is performed by projecting the ICESat-2 profile onto the IceBird-derived TIN surface and comparing the interpolated TIN elevations with the ICESat-2 elevations along the same track. This corresponds to Section 6.1 of the accompanying paper.

**Purpose:**

- Evaluate whether the generated TIN preserves the observed sea-ice surface topography
- Compare IceBird TIN-derived elevations with ICESat-2 elevation measurements

**Input:**

- IceBird-derived TIN surface
- Drift-corrected ICESat-2 profile

**Output:**

- Statistical summaries and/or figures comparing IceBird TIN elevations with ICESat-2 elevations

### `ridges_evaluation/`

This folder contains code for evaluating the extracted pressure ridges. It corresponds to Section 6.2 of the accompanying paper.

The evaluation includes comparing the ridge lines extracted by the distributed Apache Spark workflow with reference ridge features. These references include ridge peaks detected from ICESat-2 using the UMD-RDA algorithm and ridge lines extracted using a single-machine TIN-based workflow.

**Purpose:**

- Evaluate extracted ridge lines against ICESat-2 ridge peaks
- Compare distributed ridge-extraction results with single-machine results
- Compute matching statistics such as matched ratio, recall, precision, and ridge-frequency-related measures

**Input:**

- Extracted ridge lines from the distributed workflow
- ICESat-2 ridge peaks
- Extracted ridge lines from the single-machine approach

**Output:**

- Evaluation statistics
- Comparison figures

## General Workflow

The code follows the general workflow below:

1. Generate or provide a TIN surface model from IceBird ALS point cloud data.
2. Use `ridge_line_extraction_Apache_Spark/` to extract pressure ridge lines from the TIN.
3. Use `drift_correction/` to correct spatial drift between the ICESat-2 and IceBird observations.
4. Use `TIN_evaluation_with_ICESat-2_profile/` to evaluate the generated TIN surface against the ICESat-2 profile.
5. Use `ridges_evaluation/` to evaluate the extracted ridge lines against ICESat-2 ridge peaks and/or single-machine ridge-extraction results.

## Notes

- The ridge-extraction workflow is designed for large-scale TIN data and uses Apache Spark for distributed processing.
- The input TIN should be provided in OFF format.
- The extracted ridge lines are saved in CSV format.
- Some evaluation scripts require drift-corrected ICESat-2 data to ensure meaningful spatial comparison.

