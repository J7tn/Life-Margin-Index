# LMI CLI Manual

This manual covers the command-line tools included in the Life Margin Index repository.

## 1) What the CLI Does

The CLI helps you:

- validate LMI input datasets,
- compute `Income Index` and `LMI` columns from income data,
- generate summary statistics reports in JSON format.

## 2) Available Commands

After installation, you get three command entry points:

- `lmi` (recommended unified interface)
- `lmi-calc` (legacy compute command)
- `lmi-report` (legacy reporting command)

Use `lmi` unless you need backward compatibility.

## 3) Installation (Standard)

From repository root:

`pip install -e .`

Check command availability:

`lmi --help`

## 4) Quick Workflow

### Step 1: Validate your dataset

`lmi validate --input examples/sample_dataset.csv`

### Step 2: Compute LMI outputs

`lmi compute --input examples/sample_dataset.csv --output analysis/output/lmi_output.csv`

### Step 3: Generate summary report

`lmi report --input analysis/output/lmi_output.csv --output analysis/output/lmi_summary.json`

## 5) Command Reference

## `lmi validate`

Validates schema and value constraints for input data.

### Required arguments

- `--input`: path to CSV file

### Optional arguments

- `--actual-column` (default: `Actual Income`)
- `--baseline-column` (default: `Baseline Income`)
- `--lmi-column` (default: `LMI`)
- `--require-metadata` (flag)
- `--metadata-columns` (comma-separated list used when metadata is required)

### What it checks

- Required numeric columns exist.
- `Actual Income` values are numeric and non-negative.
- `Baseline Income` values are numeric and greater than zero.
- If `LMI` column is present and non-empty, values are numeric.
- If `--require-metadata` is used:
  - listed metadata columns are present and non-empty;
  - semantic checks are applied for common fields:
    - `Unit of Analysis` in `{individual, household, cohort}`
    - period fields in `{hourly, monthly, yearly}`
    - `Currency` in 3-letter ISO-like format (for example `USD`)
    - `Observation Period` in `YYYY` or `YYYY-MM`

### Example

`lmi validate --input data/lmi_observations.csv --require-metadata`

## `lmi compute`

Computes normalized monthly incomes, `Income Index`, and `LMI`.

### Required arguments

- `--input`: path to source CSV
- `--output`: path to destination CSV

### Optional arguments

- `--actual-column` (default: `Actual Income`)
- `--baseline-column` (default: `Baseline Income`)
- `--actual-period-column` (default: `Actual Income Period`)
- `--baseline-period-column` (default: `Baseline Income Period`)
- `--default-actual-period` (default: `monthly`)
- `--default-baseline-period` (default: `monthly`)
- `--hours-per-week` (default: `40`)
- `--weeks-per-year` (default: `52`)

### Period handling

Supported periods:

- `hourly`
- `monthly`
- `yearly`

Normalization behavior:

- `monthly` -> unchanged
- `yearly` -> divided by 12
- `hourly` -> multiplied by `hours_per_week * weeks_per_year / 12`

### Output columns added

- `Normalized Actual Income (Monthly)`
- `Normalized Baseline Income (Monthly)`
- `Normalization Period` (always `monthly`)
- `Income Index`
- `LMI`

### Example

`lmi compute --input data/lmi_observations.csv --output analysis/output/lmi_observations_computed.csv --default-actual-period monthly --default-baseline-period monthly`

## `lmi report`

Generates summary statistics from a CSV containing LMI values.

### Required arguments

- `--input`: path to CSV
- `--output`: path to JSON

### Optional arguments

- `--lmi-column` (default: `LMI`)
- `--weight-column` (row-level weighting)
- `--group-column` (grouped two-stage aggregation)
- `--group-weight-column` (weight for group-level means)

### Modes

- **Simple mode**: no weights, no grouping.
- **Weighted mode**: use `--weight-column`.
- **Grouped mode**: use `--group-column`; optionally include `--weight-column` and `--group-weight-column`.

### Output keys (typical)

- `sample_size`
- `mean_lmi`
- `median_lmi`
- `min_lmi`
- `max_lmi`
- `share_below_baseline`

Depending on mode, output may also include:

- `weighted_sample_size`
- `weighting_applied`
- `group_count`
- `weighted_group_size`
- `aggregation_level`
- `group_weighting_applied`
- `within_group_weighting_applied`

### Example (grouped weighted aggregation)

`lmi report --input data/lmi_observations.csv --output analysis/output/lmi_country_summary.json --lmi-column LMI --weight-column Sample Weight --group-column City --group-weight-column City Population`

## 6) Legacy Commands

You can still run:

- `lmi-calc ...` (equivalent compute functionality)
- `lmi-report ...` (equivalent report functionality)

The `lmi` unified command is preferred for new workflows.

## 7) Input Data Expectations

Minimum compute dataset columns:

- `Actual Income`
- `Baseline Income`

Recommended metadata columns for high-quality datasets:

- `Region`
- `Observation Period`
- `Unit of Analysis`
- `Population Scope`
- `Income Definition`
- `Currency`
- `Actual Income Period`
- `Baseline Income Period`

## 8) Output Interpretation

Core interpretation:

- `LMI < 0`: poverty/precarity relative to dignified stability baseline
- `LMI = 0`: at dignified stability baseline
- `LMI > 0`: above dignified stability baseline

## 9) Troubleshooting

### `command not found: lmi`

- Ensure installation ran in the environment you are using:
  - `pip install -e .`
- Try running directly via Python script:
  - `python src/lmi_tool.py --help`

### `Missing required column`

- Confirm CSV header names match command options exactly.
- Use `--actual-column`, `--baseline-column`, or `--lmi-column` to map custom names.

### Non-numeric or invalid values

- Ensure income columns contain numbers only.
- Ensure baseline values are greater than zero.
- Ensure weights are greater than zero when weighting is enabled.

### Metadata validation errors

- If using `--require-metadata`, verify non-empty values for all required metadata fields.
- Check that period fields use `hourly`, `monthly`, or `yearly`.
