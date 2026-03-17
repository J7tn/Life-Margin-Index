# Changelog

All notable changes to this project are documented in this file.

The format follows the spirit of [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project uses semantic versioning for software artifacts.

## [0.1.0] - 2026-03-16

### Added

- Core project scaffold with publication-grade documentation and source modules.
- Foundational framework documents:
  - `docs/LMI_Research_Paper.md`
  - `docs/LMI_Methodology.md`
  - `docs/LMI_Visualization_Guide.md`
  - `docs/LMI_Framework_Overview.md`
- Synthetic sample data and worked calculations:
  - `examples/sample_dataset.csv`
  - `examples/example_calculations.md`
- Core computation modules:
  - `src/lmi.py`
  - `src/baseline_calculator.py`
- Reproducible empirical workflow:
  - `analysis/run_empirical_demo.py`
  - `analysis/README.md`
- Automated tests:
  - `tests/test_lmi.py`
  - `tests/test_baseline_calculator.py`
- Academic citation support:
  - `CITATION.cff`
  - `references.bib`
- Methodology governance and release documentation:
  - `docs/LMI_Methodology_Versioning.md`
  - `docs/LMI_Methodology_Changelog.md`
  - `docs/LMI_Empirical_Demo.md`
  - `docs/releases/v0.1.0.md`
- Community contribution templates:
  - `.github/ISSUE_TEMPLATE/bug_report.md`
  - `.github/ISSUE_TEMPLATE/feature_request.md`
  - `.github/ISSUE_TEMPLATE/config.yml`
  - `.github/pull_request_template.md`
- Contributor and automation assets:
  - `CONTRIBUTING.md`
  - `.github/workflows/ci.yml`
  - `.github/CODEOWNERS`
  - `CODE_OF_CONDUCT.md`
  - `SECURITY.md`
  - `docs/Collaboration_Policy.md`
- Packaging and CLI assets:
  - `pyproject.toml`
  - `src/lmi_cli.py`
  - `tests/test_lmi_cli.py`
  - `src/lmi_report_cli.py`
  - `tests/test_lmi_report_cli.py`
  - `src/lmi_tool.py`
  - `tests/test_lmi_tool.py`
  - Unified `lmi validate` command for schema and value checks
  - `analysis/build_pilot20_country_table.py`
  - `docs/LMI_Pilot20_Data_Method.md`
  - `data/lmi_country_observations_pilot20_2022.csv`

### Changed

- Expanded `README.md` with quickstart, validation scope, implementation pathways, and citation guidance.
- Replaced placeholder references in `docs/LMI_Research_Paper.md` with concrete scholarly and institutional citations.
- Updated `.gitignore` to exclude generated analysis outputs under `analysis/output/`.

### Verified

- Empirical demo script executes successfully and generates deterministic outputs.
- Unit test suite passes (`python -m unittest discover tests`).
