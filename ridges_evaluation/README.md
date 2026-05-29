# Ridge Evaluation

This folder contains scripts for evaluating the pressure ridges extracted from the IceBird ALS-derived TIN surface.

## Folder Contents

```text
ridges_evaluation/
├── compare_ridge_lines_distributed_single_machine.py
├── compare_ridge_peaks_between_IceBird_and_ICESat-2.py
└── ridge_length_height_distribution/
```

## Script Description

### `compare_ridge_lines_distributed_single_machine.py`

This script compares ridge lines extracted using the distributed approach with ridge lines extracted using the single-machine approach.

**Inputs:**

- A CSV file containing ridge lines extracted by the distributed approach
- A CSV file containing ridge lines extracted by the single-machine approach

**Output:**

- Matching ratio between the two ridge-line datasets, including precision and recall values

### `compare_ridge_peaks_between_IceBird_and_ICESat-2.py`

This script compares ridge peaks detected from ICESat-2 using the UMD-RDA algorithm with ridge maxima detected from the IceBird ALS data using the distributed approach.

**Inputs:**

- ICESat-2 ridge peaks detected by the UMD-RDA algorithm
- IceBird ridge maxima detected by the distributed approach

**Output:**

- Matching ratios between the ICESat-2 ridge peaks and IceBird ridge maxima

### `ridge_length_height_distribution/`

This folder contains code for computing and visualizing the distributions of extracted ridge length and ridge height.

## Notes

The scripts in this folder are used for ridge-evaluation experiments, including comparison with ICESat-2 ridge detections, comparison with single-machine ridge-extraction results, and statistical analysis of extracted ridge morphology.
