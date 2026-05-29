# Drift Correction

This folder contains code for correcting the spatial drift between ICESat-2 observations and IceBird airborne laser scanner (ALS) point cloud data.

Because the ICESat-2 profile and the IceBird ALS segments were acquired at different times, sea ice may have moved between the two observations. The scripts in this folder estimate the horizontal drift between two ALS-derived DEMs and use the estimated drift to correct the ICESat-2 profile.

## Folder Contents

```text
drift_correction/
├── drift_results_with_SIFT.ipynb
└── drift_correction_for_ICESat-2.py
```

## Input Data

The main inputs are:

- Two DEMs generated from two IceBird ALS segments
- An ICESat-2 profile to be drift corrected

The two DEMs should correspond to ALS segments that overlap spatially but were acquired at different times. They are used to estimate the sea-ice drift between the two acquisition times.

## Script Description

### `drift_results_with_SIFT.ipynb`

This notebook estimates the drift between two ALS-derived DEMs using the SIFT feature-matching algorithm.

The general procedure is:

1. Load two DEMs generated from two IceBird ALS segments.
2. Detect image features in both DEMs using SIFT.
3. Match corresponding features between the two DEMs.
4. Estimate the horizontal displacement between the two DEMs.
5. Use the displacement results as the basis for drift correction.

The estimated drift may be further checked and fine-tuned before being applied to the ICESat-2 profile.

### `drift_correction_for_ICESat-2.py`

This Python script applies the estimated and fine-tuned drift correction to the ICESat-2 profile.

The general procedure is:

1. Load the original ICESat-2 profile.
2. Apply the estimated horizontal drift correction.
3. Save the corrected ICESat-2 profile.

## Output Data

The final output is a drift-corrected ICESat-2 profile saved in `.txt` format.

This corrected profile can then be used for comparison with the IceBird ALS-derived TIN surface and extracted ridge features.

## General Workflow

The recommended workflow is:

1. Prepare two DEMs from two overlapping IceBird ALS segments.
2. Run `drift_results_with_SIFT.ipynb` to estimate the drift between the two DEMs.
3. Fine-tune the estimated drift if needed.
4. Run `drift_correction_for_ICESat-2.py` to apply the drift correction to the ICESat-2 profile.
5. Use the output drift-corrected ICESat-2 profile for subsequent TIN or ridge evaluation.

## Notes

- The two ALS-derived DEMs should have sufficient spatial overlap for reliable SIFT feature matching.
- The estimated drift should be visually inspected before being applied to the ICESat-2 profile.
- The output drift-corrected ICESat-2 profile is intended for spatial comparison with IceBird ALS-derived products.
- The final corrected profile is saved as a `.txt` file.
