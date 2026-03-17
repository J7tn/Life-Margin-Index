# Example LMI Calculations

This document provides step-by-step Life Margin Index (LMI) calculations for illustrative synthetic cases.

## Formula Reference

- Income Index: `II = A / B`
- Life Margin Index: `LMI = II - 1 = (A / B) - 1`

Where:

- `A` = actual monthly income
- `B` = baseline monthly income

## Case 1: Individual Below Baseline

- Region: Metro-North
- Baseline Income (`B`): 2,800
- Actual Income (`A`): 2,500

### Step 1: Compute Income Index

`II = 2500 / 2800 = 0.8929`

### Step 2: Compute LMI

`LMI = 0.8929 - 1 = -0.1071`

### Interpretation

This individual is approximately **10.71% below** the dignified baseline.

## Case 2: Individual Above Baseline

- Region: Coastal-East
- Baseline Income (`B`): 3,400
- Actual Income (`A`): 3,900

### Step 1: Compute Income Index

`II = 3900 / 3400 = 1.1471`

### Step 2: Compute LMI

`LMI = 1.1471 - 1 = 0.1471`

### Interpretation

This individual is approximately **14.71% above** the dignified baseline.

## Case 3: Individual at Baseline

- Region: Central-West
- Baseline Income (`B`): 2,500
- Actual Income (`A`): 2,500

### Step 1: Compute Income Index

`II = 2500 / 2500 = 1.0000`

### Step 2: Compute LMI

`LMI = 1.0000 - 1 = 0.0000`

### Interpretation

This individual is exactly at the sufficiency threshold.

## Case 4: Comparing Two Individuals in Same Region

Region: Rural-South (`B = 2,100`)

- Person A income: 1,800
- Person B income: 2,600

### Person A

- `II = 1800 / 2100 = 0.8571`
- `LMI = 0.8571 - 1 = -0.1429`

Interpretation: **14.29% below** baseline.

### Person B

- `II = 2600 / 2100 = 1.2381`
- `LMI = 1.2381 - 1 = 0.2381`

Interpretation: **23.81% above** baseline.

## Practical Notes

- Compare LMI values directly only when baseline methodology is consistent.
- Use LMI distributions (not only averages) for policy analysis.
- Pair LMI with volatility and buffer metrics for resilience assessment.
