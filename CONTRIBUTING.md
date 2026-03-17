# Contributing Guide

Thank you for contributing to the Life Margin Index (LMI) project.

## Scope of Contributions

Contributions are welcome across:

- methodology refinements,
- empirical workflows,
- implementation quality and tests,
- documentation clarity and citation quality,
- visualization and reporting standards.

## Before You Open a Pull Request

1. Open or reference an issue describing the problem and expected outcome.
2. Keep changes scoped to a single objective where possible.
3. For methodology-impacting changes, update:
   - `docs/LMI_Methodology_Changelog.md`
   - `CHANGELOG.md`

## Local Validation Requirements

From repository root:

`python -m unittest discover tests`

`python analysis/run_empirical_demo.py`

Your pull request should pass both checks unless the change is clearly docs-only.

## Documentation Standards

- Use clear, professional academic tone.
- Keep formulas and notation consistent with `docs/LMI_Methodology.md`.
- Avoid ambiguous claims without references.
- Add or update citation entries in `references.bib` when introducing new evidence.

## Methodology Governance

If your change modifies formulas, assumptions, or baseline construction logic:

- describe rationale and expected effect,
- document comparability implications,
- update version/changelog notes in governance docs.

Refer to:

- `docs/LMI_Methodology_Versioning.md`
- `docs/LMI_Methodology_Changelog.md`
- `docs/Collaboration_Policy.md`

## Conduct and Security

- Follow collaboration behavior standards in `CODE_OF_CONDUCT.md`.
- Report vulnerabilities through the process in `SECURITY.md`.

## Pull Request Checklist

- [ ] Scope is clear and justified.
- [ ] Tests added or updated when behavior changes.
- [ ] Docs updated to match implementation.
- [ ] Changelog entries updated where required.
- [ ] Local validation commands completed.
