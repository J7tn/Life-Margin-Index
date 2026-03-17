# Pilot-20 Country Data Method (B + C)

This document specifies the first empirical implementation requested for the repository:

- **B**: composite dignified stability baseline from multiple official sources.
- **C**: pilot rollout to 20 countries before global scaling.

## Scope

- Geographic scope: 20 pilot countries.
- Unit: per-capita proxy (individual-equivalent).
- Observation period: 2022.
- Output: timestamped LMI country table with source traceability.

## Official Data Sources

### 1) Actual Income

- **Source**: World Bank WDI API
- **Indicator**: `NY.GNP.PCAP.PP.CD`
- **Definition**: GNI per capita, PPP (current international $)

### 2) Food Cost Component

- **Source**: FAO CoAHD dataset
- **Item code**: `70040`
- **Definition**: Cost of a healthy diet, PPP dollar per person per day

### 3) Healthcare Component

- **Source**: World Bank WDI API
- **Indicator**: `SH.XPD.CHEX.PP.CD`
- **Definition**: Current health expenditure per capita, PPP (current international $)

### 4) Housing/Transport Share Ratios

- **Source**: OECD published household expenditure shares (2022 average)
- **Ratios used**:
  - Food: 15.6%
  - Housing and utilities: 22.5%
  - Transport: 12.2%

## Composite Baseline Formula

Let:

- `F` = food monthly cost (from FAO CoAHD, PPP/day converted to monthly)
- `HC` = healthcare monthly cost (from World Bank health PPP indicator)
- `HU` = housing and utilities monthly proxy
- `T` = transport monthly proxy
- `C` = contingency amount

Computation:

1. `F = CoAHD_PPP_per_day * 365.25 / 12`
2. `HU = F * (0.225 / 0.156)`
3. `T = F * (0.122 / 0.156)`
4. `HC = SH.XPD.CHEX.PP.CD / 12`
5. `Subtotal = F + HU + T + HC`
6. `C = 0.08 * Subtotal`
7. `Baseline Income (B) = Subtotal + C`

Actual income monthly:

- `A = NY.GNP.PCAP.PP.CD / 12`

LMI computations:

- `Income Index = A / B`
- `LMI = (A / B) - 1`

## Why This Is a Pilot Method

This is a documented and reproducible composite baseline method using official public sources, but it remains a pilot proxy. The OECD share ratios are currently applied as common coefficients across all pilot countries rather than country-specific expenditure structures.

## Reproducibility

Script:

- `analysis/build_pilot20_country_table.py`

Outputs:

- `data/lmi_country_observations_pilot20_2022.csv`
- `analysis/output/lmi_country_table_2022_<UTC timestamp>.csv`

Validation command:

- `lmi validate --input data/lmi_country_observations_pilot20_2022.csv --require-metadata`
