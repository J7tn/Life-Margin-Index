# LMI Visualization Guide

This guide defines recommended charting standards for communicating Life Margin Index (LMI) results clearly and consistently.

## 1) Recommended Chart Types

- **Distribution charts**: histogram or density plot of LMI values.
- **Group comparison charts**: boxplot/violin plot by region, demographic group, or employment class.
- **Time-series charts**: line chart of median LMI with quantile bands.
- **Geographic charts**: choropleth or tile heatmap for regional median LMI.
- **Composition charts**: stacked bars for share below zero (poverty/precarity), near zero, and above zero.

## 2) Example Axes

### Distribution

- X-axis: `LMI` (or `LMI %`)
- Y-axis: count, density, or population-weighted frequency

### Demographic Comparison

- X-axis: demographic category (e.g., age band, household type)
- Y-axis: LMI value

### Time Series

- X-axis: period (monthly/quarterly)
- Y-axis: median LMI
- Optional overlays: P25 and P75 bands, sufficiency reference line at `LMI = 0`

### Regional Heatmap

- X-axis: region
- Y-axis: period
- Color: median LMI

## 3) Interpretation Guidelines

- Always include a visible reference line at `LMI = 0` (dignified stability threshold).
- Treat values near zero as potentially fragile when volatility is high.
- Use quantiles to avoid over-reliance on means in skewed distributions.
- Report subgroup sample sizes for interpretive integrity.
- Clearly distinguish absolute currency displays from normalized LMI displays.

## 4) Color Palette Suggestions

Use a diverging palette centered at zero:

- **Negative LMI (below baseline)**: red spectrum
- **Near zero (at baseline)**: neutral gray
- **Positive LMI (above baseline)**: blue or green spectrum

Example hex palette:

- Deep deficit: `#B2182B`
- Moderate deficit: `#EF8A62`
- Near threshold: `#F7F7F7`
- Moderate surplus: `#67A9CF`
- High surplus: `#2166AC`

Accessibility recommendations:

- Ensure contrast ratios are readable.
- Use shape/pattern cues in addition to color for critical thresholds.
- Validate for common forms of color-vision deficiency.

## 5) Visualizing LMI Distributions

Recommended outputs:

- Histogram with kernel density overlay.
- Vertical line at zero.
- Annotated statistics: median, interquartile range, share below zero.

Useful segmentation:

- Region
- Household composition
- Employment class
- Age cohort

## 6) Visualizing Demographics

Recommended approach:

- Use boxplots for each demographic subgroup.
- Overlay median markers and confidence intervals where possible.
- Sort categories by median LMI for readability.

Suggested annotation set:

- sample size (`n`)
- median LMI
- percent below baseline

## 7) Visualizing Time-Series Dynamics

Recommended approach:

- Plot median LMI per period.
- Add uncertainty/dispersion ribbons (P25-P75).
- Mark policy shocks or macro events on the timeline.

Interpretive focus:

- trend direction (improving vs worsening margins),
- volatility changes,
- subgroup divergence over time.

## 8) Reporting and Layout Standards

Each figure should include:

- clear title with region and period,
- axis labels with units,
- legend with threshold explanation,
- source note,
- methodology version reference.

Figure caption best practice:

- one sentence on what is shown,
- one sentence on the principal takeaway,
- one sentence on caveats or context.
