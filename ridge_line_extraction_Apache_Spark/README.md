# Ridge Line Extraction with Apache Spark

This folder contains notebooks for extracting sea-ice pressure ridge lines from an IceBird ALS-derived TIN surface using an Apache Spark-based distributed workflow.

The workflow starts from a TIN surface and progressively computes roughness, Forman gradient, surface network, topological simplification, ridge merging, and final ridge filtering.

## Folder Contents

```text
ridge_line_extraction_Apache_Spark/
├── Seaice_step0_compute_roughness.ipynb
├── Seaice_step1_compute_Forman_gradient.ipynb
├── Seaice_step2_compute_and_simplify_surface_network.ipynb
├── Seaice_step3_topological_simplification.ipynb
├── Seaice_step4_merge_for_Rayleigh.ipynb
├── Seaice_step5_resimplify_to_fine_tune.ipynb
└── Seaice_step6_post_processing_and_visualization.ipynb
```

## Workflow Description

### `Seaice_step0_compute_roughness.ipynb`

Computes local surface roughness for the TIN. The roughness values are later used to filter candidate ridge segments.

### `Seaice_step1_compute_Forman_gradient.ipynb`

Computes the Forman gradient on the TIN using discrete Morse theory.

### `Seaice_step2_compute_and_simplify_surface_network.ipynb`

Computes the surface network from the Forman gradient. The surface network represents the topological structure of the TIN using critical points and arcs.

### `Seaice_step3_topological_simplification.ipynb`

Performs topological simplification on the surface network and extracts the initial ridge segments.

### `Seaice_step4_merge_for_Rayleigh.ipynb`

Merges initial ridge segments or arcs using the Rayleigh criterion.

### `Seaice_step5_resimplify_to_fine_tune.ipynb`

Further simplifies the processed or merged ridge segments to obtain candidate ridge segments.

### `Seaice_step6_post_processing_and_visualization.ipynb`

Filters the candidate ridge segments using roughness and cut-off height criteria, and generates the final ridge-extraction results and visualizations.

## Notes

- Steps 4 and 5 may need to be run multiple times to more completely remove small snow or ice features.
- The final extracted ridge lines are generated after postprocessing in Step 6.
- Parameter settings such as roughness threshold, persistence threshold, and cut-off height should be adjusted based on the dataset and analysis goal.
