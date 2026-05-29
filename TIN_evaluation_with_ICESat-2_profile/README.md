# TIN Evaluation with ICESat-2 Profile

This folder contains notebooks for evaluating the IceBird ALS-derived TIN surface by comparing it with a spatiotemporally coincident ICESat-2 elevation profile.

## Folder Contents

```text
TIN_evaluation_with_ICESat-2_profile/
├── IceBird_and_ICESat-2_profile_statistics.ipynb
└── IceBird_and_ICESat-2_profile_plots.ipynb
```

## Notebook Description

### `IceBird_and_ICESat-2_profile_statistics.ipynb`

This notebook is used to compute statistical comparisons between the ICESat-2 elevation profile and the corresponding elevations interpolated from the IceBird TIN surface.

**Main outputs:**

- Elevation distributions of the ICESat-2 profile the interpolated IceBird TIN profile
- Pearson correlation between the two profiles

### `IceBird_and_ICESat-2_profile_plots.ipynb`

This notebook is used to generate plots comparing the elevation profiles from ICESat-2 and the IceBird TIN surface.

**Main outputs:**

- Distribution of the elevation-profile comparison plots

## Notes

The notebooks in this folder are used to evaluate whether the generated TIN surface preserves the sea-ice topography observed by the ICESat-2 profile.
