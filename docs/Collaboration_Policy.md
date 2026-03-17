# Collaboration and Review Policy

This policy defines contribution and review expectations for methodological integrity and implementation quality.

## 1) Contribution Categories

- **Documentation updates**: conceptual or editorial improvements.
- **Methodology updates**: formula, baseline, or interpretation changes.
- **Implementation updates**: source code and analysis workflow changes.
- **Governance updates**: process, templates, release operations.

## 2) Review Requirements

### Documentation updates

- At least one maintainer review.

### Methodology updates

- Maintainer review required.
- Must include rationale, expected impact, and comparability implications.
- Must update:
  - `docs/LMI_Methodology_Changelog.md`
  - `CHANGELOG.md`

### Implementation updates

- Must pass CI checks.
- Must include or update tests for behavior changes.

## 3) Evidence and Reproducibility

All behavior-changing PRs should include:

- validation steps run locally,
- resulting outputs or summary evidence,
- links to updated docs where interpretation changes.

## 4) Release Hygiene

Before tagging a release:

- verify test suite and empirical demo pass,
- verify documentation consistency across key files,
- ensure release notes are added under `docs/releases/`.
