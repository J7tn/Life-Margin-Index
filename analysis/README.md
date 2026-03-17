# Analysis Workflow

This directory contains a reproducible demonstration pipeline for the Life Margin Index.

## Run the Empirical Demo

From repository root:

`python analysis/run_empirical_demo.py`

The script reads `examples/sample_dataset.csv`, recomputes Income Index and LMI values from source functions in `src/lmi.py`, and writes:

- `analysis/output/empirical_demo_results.csv`
- `analysis/output/empirical_demo_summary.json`

## Purpose

- Verify metric calculations against a known synthetic dataset.
- Produce reproducible summary statistics for documentation.
- Establish a template for larger data pipelines in future releases.
