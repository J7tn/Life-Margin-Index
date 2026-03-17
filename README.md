# Life Margin Index (LMI)

The **Life Margin Index (LMI)** is a universal, human-centered economic metric that quantifies how far an individual stands above or below the minimum income required for stable and dignified living.

Rather than treating income as an isolated number, LMI reframes economic wellbeing as a **margin from the dignified stability baseline**. This framing supports policy design, social analysis, and practical interventions centered on lived economic reality.

## Why It Matters

Conventional income measures often obscure material insecurity by focusing on averages, broad poverty thresholds, or nominal earnings without context. LMI addresses this gap by:

- Expressing income relative to a regionally grounded baseline for dignified living.
- Identifying not only deprivation, but also the degree of financial resilience.
- Enabling comparable analysis across regions, demographics, and time.
- Supporting targeted policy action for households near or below economic stability.

## How It Works (High-Level)

The framework uses three core quantities:

- **Baseline Income (B)**: minimum monthly income required for stable, dignified living in a specific context.
- **Actual Income (A)**: observed monthly income for an individual or household.
- **Income Index (II)**: ratio of actual income to baseline income, where `II = A / B`.

From this:

- **Life Margin Index** is defined as `LMI = II - 1`.
- `LMI = 0` indicates exact baseline sufficiency.
- `LMI < 0` indicates poverty or precarity relative to the dignified stability baseline.
- `LMI > 0` indicates a surplus above baseline.

## Repository Contents

- `docs/LMI_Research_Paper.md` - full academic-style paper.
- `docs/LMI_Methodology.md` - computational methods and data protocol.
- `docs/LMI_Visualization_Guide.md` - standards for visual communication of LMI.
- `docs/LMI_Framework_Overview.md` - complete multi-index framework summary.
- `docs/LMI_CLI_Manual.md` - full command-line manual and reference.
- `docs/Install_Like_You_Are_5.md` - beginner-friendly installation walkthrough.
- `docs/LMI_Empirical_Demo.md` - reproducible demonstration results and interpretation.
- `docs/LMI_Pilot20_Data_Method.md` - official-source pilot method for country table generation.
- `docs/LMI_Methodology_Versioning.md` - governance standard for methodology updates.
- `docs/LMI_Methodology_Changelog.md` - version history for methodological changes.
- `data/lmi_country_observations_pilot20_2022.csv` - pilot 20-country LMI table from validated sources.
- `examples/sample_dataset.csv` - synthetic dataset with baseline and derived metrics.
- `examples/example_calculations.md` - step-by-step worked examples.
- `src/lmi.py` - core LMI and Income Index computation functions.
- `src/baseline_calculator.py` - baseline income calculator interface placeholder.
- `analysis/run_empirical_demo.py` - executable reproducibility script for summary outputs.
- `tests/` - unit tests for LMI and baseline calculator behavior.
- `src/lmi_cli.py` - command-line CSV processor for Income Index and LMI.
- `src/lmi_report_cli.py` - command-line summary statistics generator for LMI CSVs.
- `src/lmi_tool.py` - unified `lmi` CLI with `validate`, `compute`, and `report` subcommands.
- `CITATION.cff` - GitHub-compatible citation metadata.
- `references.bib` - baseline bibliography for framework literature.
- `CHANGELOG.md` - project-level release and change history.
- `CONTRIBUTING.md` - contributor workflow and validation standards.
- `CODE_OF_CONDUCT.md` - standards for respectful, professional collaboration.
- `SECURITY.md` - process for responsible vulnerability reporting.
- `docs/releases/` - versioned release notes.
- `docs/Collaboration_Policy.md` - formal review and release policy.

## Quickstart

Run the reproducible empirical demo:

`python analysis/run_empirical_demo.py`

Run the test suite:

`python -m unittest discover tests`

Install local package metadata and CLI:

`pip install -e .`

Full CLI documentation:

`docs/LMI_CLI_Manual.md`

Beginner install guide:

`docs/Install_Like_You_Are_5.md`

Unified CLI validate command:

`lmi validate --input examples/sample_dataset.csv`

For publication-grade datasets, enable metadata checks:

`lmi validate --input data/lmi_observations.csv --require-metadata`

This enforces required non-empty metadata columns by default:
`Region`, `Observation Period`, `Unit of Analysis`, `Population Scope`,
`Income Definition`, `Currency`, `Actual Income Period`, `Baseline Income Period`.

It also enforces semantic consistency for common fields:
- `Unit of Analysis` in `{individual, household, cohort}`
- income periods in `{hourly, monthly, yearly}`
- `Currency` in 3-letter ISO style (for example, `USD`, `EUR`)
- `Observation Period` format `YYYY` or `YYYY-MM`

Unified CLI compute command:

`lmi compute --input examples/sample_dataset.csv --output analysis/output/lmi_output.csv`

`lmi compute` now supports mixed period inputs (`hourly`, `monthly`, `yearly`) via
optional columns `Actual Income Period` and `Baseline Income Period`. Values are
normalized to monthly equivalents before computing `Income Index` and `LMI`.

Unified CLI report command:

`lmi report --input analysis/output/lmi_output.csv --output analysis/output/lmi_summary.json`

Build the validated pilot 20-country table (official-source composite baseline):

`python analysis/build_pilot20_country_table.py`

This now writes both CSV and a clean Markdown table:

- `data/lmi_country_observations_pilot20_2022.csv`
- `analysis/output/lmi_country_table_2022.md`
- `analysis/output/lmi_country_table_2022_pretty.txt` (fixed-width aligned table)

Validate pilot table with required metadata checks:

`lmi validate --input data/lmi_country_observations_pilot20_2022.csv --require-metadata`

`lmi report` supports weighted estimation:

- `--weight-column` for row-level survey/population weights.
- `--group-column` for two-stage aggregation (for example, city-level means).
- `--group-weight-column` for weighting group means into national estimates.

Compute LMI values for a CSV file:

`lmi-calc --input examples/sample_dataset.csv --output analysis/output/lmi_cli_output.csv`

If period columns are not present, both incomes default to `monthly`. You can
override defaults with:

`--default-actual-period`, `--default-baseline-period`, `--hours-per-week`, and `--weeks-per-year`.

Generate summary statistics JSON from an LMI CSV:

`lmi-report --input analysis/output/lmi_cli_output.csv --output analysis/output/lmi_cli_summary.json`

Example country-level aggregation from city observations:

`lmi report --input data/lmi_observations.csv --output analysis/output/lmi_country_summary.json --lmi-column LMI --weight-column Sample Weight --group-column City --group-weight-column City Population`

Backward-compatible commands `lmi-calc` and `lmi-report` remain available.

## Validation Release Scope (v0.1.0)

This release establishes a reproducible and test-backed foundation:

- deterministic metric computation in `src/`,
- synthetic data workflow in `analysis/`,
- verification via automated tests in `tests/`,
- documented methodological governance in `docs/`.

Methodology standard version: **v1.0.0**.

## Implementation Pathways

### For Researchers

- Use the formal model in `docs/LMI_Research_Paper.md`.
- Cite using `CITATION.cff` and extend references from `references.bib`.
- Reproduce baseline outputs with `analysis/run_empirical_demo.py`.

### For Policymakers and Public Institutions

- Use `docs/LMI_Methodology.md` for operational specification.
- Apply reporting and update governance from `docs/LMI_Methodology_Versioning.md`.
- Use visualization standards in `docs/LMI_Visualization_Guide.md` for public reporting.

### For NGOs and Social Programs

- Use `LMI < 0` thresholds for vulnerability triage.
- Pair LMI with extension metrics in `docs/LMI_Framework_Overview.md`.
- Track trend movement and subgroup distributions over time.

## Contributing Workflow

- Use GitHub issue templates for bug reports and feature proposals.
- Use the pull request template to document scope, validation, and methodology impact.
- For methodology changes, update both:
  - `docs/LMI_Methodology_Changelog.md`
  - `CHANGELOG.md`
- Follow contribution and validation guidance in `CONTRIBUTING.md`.
- Review expectations are defined in `docs/Collaboration_Policy.md`.

## Continuous Integration

Automated CI is configured in `.github/workflows/ci.yml` and runs on pushes and pull requests. It executes:

- `python -m unittest discover tests`
- `python analysis/run_empirical_demo.py`

## Project Governance

- Ownership rules are defined in `.github/CODEOWNERS`.
- Collaboration behavior standards are defined in `CODE_OF_CONDUCT.md`.
- Responsible security disclosure guidance is defined in `SECURITY.md`.

## How to Cite

If you use this framework in academic, policy, or analytical work, cite as:

> Flare. (2026). *Life Margin Index (LMI): A human-centered economic metric for dignified living thresholds* [Repository]. GitHub.

You may also reference the research manuscript in `docs/LMI_Research_Paper.md` as the canonical conceptual description. For machine-readable citation metadata, use `CITATION.cff`.

## Attribution

Created by **Flare (2026)**.
