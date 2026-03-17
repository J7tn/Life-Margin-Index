# Life Margin Framework Overview

The Life Margin Framework is a multi-index system for evaluating economic wellbeing as lived capacity rather than nominal income alone. The framework centers on the **Life Margin Index (LMI)** and extends it with complementary indicators that capture stability, resilience, debt pressure, and time burden.

## 1) Core Index: Life Margin Index (LMI)

### Definition

`LMI = (A / B) - 1`

Where:

- `A` = actual income
- `B` = baseline income required for stable, dignified living

### Interpretation

- `LMI < 0`: deficit below baseline
- `LMI = 0`: baseline sufficiency
- `LMI > 0`: surplus above baseline

LMI is the principal measure of current economic position.

## 2) Stability Index (SI)

### Purpose

Measures how stable an individual's or household's margin position remains over time.

### Concept

High SI indicates low volatility in income-to-baseline ratios and greater predictability of day-to-day conditions.

### Suggested Inputs

- Time-series of actual income
- Time-series of baseline income
- Volatility window and smoothing parameters

## 3) Buffer Index (BI)

### Purpose

Measures resilience capacity in terms of how long baseline living can be sustained from liquid resources.

### Concept

`BI = liquid_reserves / B`

Interpretable as baseline-equivalent months of protection against income shocks.

### Suggested Inputs

- Liquid savings and near-cash assets
- Baseline income
- Optional stress-adjusted reserve assumptions

## 4) Debt Drag Index (DDI)

### Purpose

Captures the extent to which mandatory debt payments constrain economic margin.

### Concept

`DDI = required_debt_payments / B`

Higher DDI implies more margin is absorbed by debt obligations, reducing effective flexibility.

### Suggested Inputs

- Required monthly debt service
- Baseline income
- Debt composition metadata (secured/unsecured, interest profile)

## 5) Time Cost Index (TCI)

### Purpose

Represents non-financial burdens that reduce effective economic agency, such as unpaid care, mandatory commute, or administrative burden.

### Concept

`TCI = burden_hours / available_hours`

Higher TCI indicates greater time pressure and reduced adaptive capacity.

### Suggested Inputs

- Total required non-discretionary hours
- Available productive/recovery hours
- Household care burden characteristics

## 6) How the Indices Interrelate

- **LMI** indicates current position relative to dignified baseline.
- **SI** indicates whether that position is stable or fragile over time.
- **BI** indicates ability to withstand temporary shocks.
- **DDI** indicates how debt obligations compress effective margin.
- **TCI** indicates temporal constraints that reduce real-life adaptability.

Together, these indices convert static income assessment into a richer view of lived economic capacity.

## 7) Framework Use Cases

- Policy targeting and preventive support design
- Household vulnerability segmentation
- Labor market adequacy analysis
- Program evaluation and impact tracking
- Longitudinal resilience monitoring

## 8) Implementation Principles

- Use transparent formulas and versioned methodology.
- Update baseline and extension inputs regularly.
- Report uncertainty and known data limitations.
- Preserve comparability by documenting all regional adjustments.
- Pair numeric indicators with contextual interpretation.
