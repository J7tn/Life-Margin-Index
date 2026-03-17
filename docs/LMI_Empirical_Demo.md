# LMI Empirical Demo (v0.1)

## Purpose

This document reports a reproducible demonstration of Life Margin Index (LMI) outputs using the synthetic dataset in `examples/sample_dataset.csv`. The goal is to validate computation flow, summarize initial distributional behavior, and establish a template for larger empirical studies.

## Data and Reproducibility

- **Dataset**: `examples/sample_dataset.csv`
- **Computation source**: `src/lmi.py`
- **Reproducible script**: `analysis/run_empirical_demo.py`
- **Generated outputs**:
  - `analysis/output/empirical_demo_results.csv`
  - `analysis/output/empirical_demo_summary.json`

Run command:

`python analysis/run_empirical_demo.py`

## Key Results (Synthetic Sample)

Using 8 observations:

- Mean LMI: `0.0500`
- Median LMI: `0.0714`
- Minimum LMI: `-0.142857`
- Maximum LMI: `0.2400`
- Share below dignified stability baseline (`LMI < 0`, poverty/precarity): `37.5%`

## Interpretation

The synthetic sample includes both deficit and surplus cases, with a slight positive central tendency and substantial heterogeneity around the sufficiency threshold. A non-trivial fraction below baseline indicates that average values alone are insufficient for policy interpretation; distribution and subgroup analysis remain essential.

## Regional Illustration

- **Metro-North**: one observation below baseline, one above baseline.
- **Coastal-East**: mixed outcomes near +/- 0.15.
- **Rural-South**: widest spread in sample, ranging from strong deficit to strong surplus.
- **Central-West**: one exactly at threshold and one with clear surplus.

## Methodological Caveats

- The dataset is synthetic and does not represent real populations.
- No sampling weights are applied.
- Baseline values are illustrative rather than estimated from real component-cost pipelines.

## Next Empirical Steps

- Replace synthetic data with regional pilot data.
- Add weighted estimates and confidence intervals.
- Produce distribution charts and subgroup decomposition aligned with `docs/LMI_Visualization_Guide.md`.
- Compare trajectories across periods for stability diagnostics.
