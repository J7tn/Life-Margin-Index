# Life Margin Index (LMI)

The **Life Margin Index (LMI)** is a universal, human-centered economic metric that quantifies how far an individual stands above or below the minimum income required for stable and dignified living.

Rather than treating income as an isolated number, LMI reframes economic wellbeing as a **margin from survival**. This framing supports policy design, social analysis, and practical interventions centered on lived economic reality.

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
- `LMI < 0` indicates a shortfall below baseline.
- `LMI > 0` indicates a surplus above baseline.

## Repository Contents

- `docs/LMI_Research_Paper.md` - full academic-style paper.
- `docs/LMI_Methodology.md` - computational methods and data protocol.
- `docs/LMI_Visualization_Guide.md` - standards for visual communication of LMI.
- `docs/LMI_Framework_Overview.md` - complete multi-index framework summary.
- `examples/sample_dataset.csv` - synthetic dataset with baseline and derived metrics.
- `examples/example_calculations.md` - step-by-step worked examples.
- `src/lmi.py` - core LMI and Income Index computation functions.
- `src/baseline_calculator.py` - baseline income calculator interface placeholder.

## How to Cite

If you use this framework in academic, policy, or analytical work, cite as:

> Flare. (2026). *Life Margin Index (LMI): A human-centered economic metric for dignified living thresholds* [Repository]. GitHub.

You may also reference the research manuscript contained in `docs/LMI_Research_Paper.md` as the canonical conceptual description.

## Attribution

Created by **Flare (2026)**.
