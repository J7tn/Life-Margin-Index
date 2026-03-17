# LMI Methodology

This document defines the computational and data methodology for producing the Life Margin Index (LMI) in a consistent, auditable manner.

## 1) Baseline Income Calculation

Baseline Income (`B`) is the minimum monthly income required for stable, dignified living in a specific region and household context.

### Formula

`B = H + F + U + T + HC + EC + C`

Where:

- `H` = housing cost (rent/mortgage + essential housing fees)
- `F` = basic nutrition cost
- `U` = utilities and communications
- `T` = essential transportation cost
- `HC` = baseline healthcare access cost
- `EC` = essential education/childcare cost (if applicable)
- `C` = contingency allowance (recommended 5-10% of subtotal)

### Estimation Principles

- Use region-specific, current-period prices.
- Use household-size adjustments where applicable.
- Ensure all components represent essentials, not aspirational consumption.
- Publish component assumptions for transparency.

## 2) Income Index Calculation

Income Index (`II`) normalizes observed income against baseline requirements.

### Formula

`II = A / B`

Where:

- `A` = actual monthly income
- `B` = baseline monthly income

### Interpretation

- `II < 1`: income shortfall relative to dignified baseline
- `II = 1`: baseline sufficiency
- `II > 1`: income surplus above baseline

## 3) LMI Calculation

Life Margin Index (`LMI`) is the centered version of the Income Index.

### Formula

`LMI = II - 1 = (A / B) - 1`

### Interpretation

- `LMI < 0`: below baseline (negative margin)
- `LMI = 0`: at baseline
- `LMI > 0`: above baseline (positive margin)

### Optional Percent Form

`LMI% = 100 * LMI`

## 4) Data Requirements

Minimum required fields per observation:

- Region
- Observation period (month/year)
- Baseline Income (`B`)
- Actual Income (`A`)

Recommended additional fields:

- Household size and composition
- Employment type and hours worked
- Debt-service burden
- Liquid savings
- Demographic identifiers (for disaggregated analysis)

Data quality rules:

- `B` must be strictly positive.
- `A` must be non-negative.
- Missing values must be flagged and excluded from index computation.
- Currency and period units must be consistent.

## 5) Update Frequency

Recommended update cadence:

- **Baseline components**: monthly where possible, quarterly at minimum.
- **Computed indices**: recompute on every baseline update and new income data release.
- **Method audit**: at least annually, including component definitions and data-source review.

Rapid-update triggers:

- Inflation spikes
- Housing market discontinuities
- Policy changes materially affecting essential costs

## 6) Regional Adjustments

Regional comparability requires local calibration of baseline components.

Adjustment practices:

- Use regional price indices or local microdata for each baseline component.
- Maintain a regional metadata table documenting data sources and update dates.
- If comparing across regions, present both:
  - local LMI values (computed with local baselines), and
  - standardized analyses with explicit normalization assumptions.

### Household Equivalence Note

Where household structures differ, apply equivalence scales consistently and document:

- adult and child weighting assumptions,
- shared-cost treatment (housing/utilities),
- any caps or floors used for policy comparability.

## 7) Computational Workflow (Recommended)

1. Ingest regional baseline component data.
2. Construct and validate baseline income (`B`).
3. Ingest actual income observations (`A`).
4. Validate numeric integrity and unit consistency.
5. Compute `II` and `LMI`.
6. Produce distributional summaries and threshold statistics.
7. Publish outputs with versioned methodology notes.

## 8) Reporting Standards

Each published LMI dataset should include:

- methodology version,
- data sources and extraction dates,
- regional scope,
- currency and period definitions,
- quality-control notes,
- known limitations.
