# LMI Methodology Versioning and Governance

## Purpose

This document defines governance rules for methodological changes to the Life Margin Index framework. The objective is to preserve comparability over time while enabling transparent, evidence-based updates.

## Versioning Standard

The methodology uses semantic-style versioning:

- **Major (`X.0.0`)**: conceptual or formula-level changes that break comparability with prior versions.
- **Minor (`0.X.0`)**: non-breaking additions (new recommended fields, reporting expansions, extension metric refinements).
- **Patch (`0.0.X`)**: clarifications, typo fixes, and non-substantive documentation corrections.

Current methodology version: **v1.0.0**

## Mandatory Metadata for Published Results

Every LMI publication should include:

- methodology version
- baseline component definitions
- data sources and extraction dates
- regional scope and currency basis
- observation period
- quality-control and exclusion rules
- known limitations

## Change Control Rules

1. All methodology changes must be documented before release.
2. Any baseline component redefinition requires an explicit comparability note.
3. Formula changes require impact assessment on historical results.
4. Public documents (`README`, methodology docs, empirical reports) must reference the current version.
5. Historical versions remain archived and citable.

## Release Review Checklist

- [ ] Version increment follows semantic rules.
- [ ] Changelog entry added with date and rationale.
- [ ] Affected docs updated.
- [ ] Reproducible scripts run successfully.
- [ ] Test suite passes.

## Recommended Governance Cadence

- **Routine review**: quarterly
- **Urgent review triggers**: inflation shocks, major policy shifts, structural cost changes
- **Comprehensive audit**: annual external or cross-functional review
