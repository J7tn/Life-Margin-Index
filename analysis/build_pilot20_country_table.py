"""Build a pilot 20-country LMI table from official public data sources.

Sources:
- World Bank WDI API:
  - NY.GNP.PCAP.PP.CD (GNI per capita, PPP current international $)
  - SH.XPD.CHEX.PP.CD (Current health expenditure per capita, PPP current international $)
- FAO CoAHD API:
  - item_code 70040 (Cost of a healthy diet, PPP dollar per person per day)
- OECD published average household expenditure shares (2022):
  - Food: 15.6%
  - Housing and utilities: 22.5%
  - Transport: 12.2%
"""

from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List
from urllib.request import urlopen

PROJECT_ROOT = Path(__file__).resolve().parents[1]
import sys

SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from lmi import compute_income_index, compute_lmi

OUTPUT_DATA = PROJECT_ROOT / "data" / "lmi_country_observations_pilot20_2022.csv"
OUTPUT_TIMESTAMPED = (
    PROJECT_ROOT
    / "analysis"
    / "output"
    / f"lmi_country_table_2022_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.csv"
)
OUTPUT_TABLE_MARKDOWN = PROJECT_ROOT / "analysis" / "output" / "lmi_country_table_2022.md"
OUTPUT_TABLE_PRETTY = PROJECT_ROOT / "analysis" / "output" / "lmi_country_table_2022_pretty.txt"

TARGET_YEAR = "2022"
PILOT_COUNTRIES = [
    ("AUS", "Australia"),
    ("AUT", "Austria"),
    ("BEL", "Belgium"),
    ("CAN", "Canada"),
    ("CHE", "Switzerland"),
    ("DEU", "Germany"),
    ("DNK", "Denmark"),
    ("ESP", "Spain"),
    ("FIN", "Finland"),
    ("FRA", "France"),
    ("GBR", "United Kingdom of Great Britain and Northern Ireland"),
    ("IRL", "Ireland"),
    ("ITA", "Italy"),
    ("JPN", "Japan"),
    ("KOR", "Republic of Korea"),
    ("NLD", "Netherlands (Kingdom of the)"),
    ("NOR", "Norway"),
    ("NZL", "New Zealand"),
    ("SWE", "Sweden"),
    ("USA", "United States of America"),
]

# OECD shares (2022 averages)
FOOD_SHARE = 0.156
HOUSING_SHARE = 0.225
TRANSPORT_SHARE = 0.122
CONTINGENCY_RATE = 0.08
DAYS_PER_MONTH = 365.25 / 12.0


def _fetch_world_bank_indicator(indicator_code: str) -> Dict[str, float]:
    country_codes = ";".join(code for code, _ in PILOT_COUNTRIES)
    url = (
        f"https://api.worldbank.org/v2/country/{country_codes}/indicator/{indicator_code}"
        f"?format=json&date={TARGET_YEAR}:{TARGET_YEAR}&per_page=200"
    )
    payload = json.loads(urlopen(url, timeout=90).read().decode("utf-8"))
    rows = payload[1] if isinstance(payload, list) and len(payload) > 1 else []
    out: Dict[str, float] = {}
    for row in rows:
        country_id = row["countryiso3code"]
        value = row.get("value")
        if country_id and value is not None:
            out[country_id] = float(value)
    return out


def _fetch_fao_cohd_ppp_per_day() -> Dict[str, float]:
    url = (
        "https://api.data.apps.fao.org/api/v2/bigquery?"
        "sql_url=https://data.apps.fao.org/catalog/dataset/"
        "bc84bd3e-4c98-46ae-b964-21e93f3f5e87/resource/"
        "5656e46c-5b76-4786-b7ae-e37862abc252/download/"
        "cost-affordabilty-healthy-diet-cahd-query.sql&item_code=70040&download=true"
    )
    text = urlopen(url, timeout=120).read().decode("utf-8", "ignore")
    rows = list(csv.DictReader(io.StringIO(text)))
    by_country_name: Dict[str, float] = {}
    target_names = {name for _, name in PILOT_COUNTRIES}
    for row in rows:
        if row.get("year") != TARGET_YEAR:
            continue
        country_name = row.get("country_name_en", "")
        value = row.get("value_int_ppp_per_person_per_day", "")
        if country_name in target_names and value not in ("", None):
            by_country_name[country_name] = float(value)
    return by_country_name


def build_rows() -> List[Dict[str, str]]:
    gni_ppp_year = _fetch_world_bank_indicator("NY.GNP.PCAP.PP.CD")
    health_ppp_year = _fetch_world_bank_indicator("SH.XPD.CHEX.PP.CD")
    food_ppp_day = _fetch_fao_cohd_ppp_per_day()

    computed_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    rows: List[Dict[str, str]] = []

    for iso3, fao_name in PILOT_COUNTRIES:
        if iso3 not in gni_ppp_year:
            raise ValueError(f"Missing World Bank GNI PPP value for {iso3}.")
        if iso3 not in health_ppp_year:
            raise ValueError(f"Missing World Bank health PPP value for {iso3}.")
        if fao_name not in food_ppp_day:
            raise ValueError(f"Missing FAO CoAHD PPP value for {fao_name}.")

        actual_income_monthly = gni_ppp_year[iso3] / 12.0
        healthcare_monthly = health_ppp_year[iso3] / 12.0
        food_monthly = food_ppp_day[fao_name] * DAYS_PER_MONTH
        housing_utilities_monthly = food_monthly * (HOUSING_SHARE / FOOD_SHARE)
        transport_monthly = food_monthly * (TRANSPORT_SHARE / FOOD_SHARE)

        subtotal = (
            food_monthly
            + housing_utilities_monthly
            + transport_monthly
            + healthcare_monthly
        )
        contingency_amount = subtotal * CONTINGENCY_RATE
        baseline_income_monthly = subtotal + contingency_amount

        income_index = compute_income_index(actual_income_monthly, baseline_income_monthly)
        lmi = compute_lmi(actual_income_monthly, baseline_income_monthly)

        rows.append(
            {
                "Country": fao_name,
                "Region": fao_name,
                "ISO3": iso3,
                "Observation Period": TARGET_YEAR,
                "Unit of Analysis": "individual",
                "Population Scope": "country-level per-capita proxy",
                "Income Definition": "GNI per capita PPP (current international $), monthly equivalent",
                "Currency": "USD",
                "Actual Income": f"{actual_income_monthly:.6f}",
                "Actual Income Period": "monthly",
                "Baseline Income": f"{baseline_income_monthly:.6f}",
                "Baseline Income Period": "monthly",
                "Food Component (PPP Monthly)": f"{food_monthly:.6f}",
                "Housing and Utilities Component (PPP Monthly)": f"{housing_utilities_monthly:.6f}",
                "Transport Component (PPP Monthly)": f"{transport_monthly:.6f}",
                "Healthcare Component (PPP Monthly)": f"{healthcare_monthly:.6f}",
                "Contingency Rate": f"{CONTINGENCY_RATE:.4f}",
                "Contingency Amount (PPP Monthly)": f"{contingency_amount:.6f}",
                "Income Index": f"{income_index:.6f}",
                "LMI": f"{lmi:.6f}",
                "Baseline Method": (
                    "Composite baseline: FAO CoAHD food cost + OECD housing/transport share scaling "
                    "+ World Bank health expenditure + 8% contingency."
                ),
                "Source - Actual Income": "World Bank WDI NY.GNP.PCAP.PP.CD",
                "Source - Healthcare": "World Bank WDI SH.XPD.CHEX.PP.CD",
                "Source - Food": "FAO CoAHD item 70040",
                "Source - Share Ratios": "OECD household expenditure shares (food 15.6%, housing 22.5%, transport 12.2%)",
                "Computed At (UTC)": computed_at,
            }
        )

    return rows


def write_csv(path: Path, rows: List[Dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_markdown_table(path: Path, rows: List[Dict[str, str]]) -> None:
    """Write a clean human-readable markdown table ranked by LMI."""
    ranked_rows = sorted(rows, key=lambda row: float(row["LMI"]), reverse=True)
    lines = [
        "# Pilot 20-Country LMI Table (2022)",
        "",
        "Ranked by `LMI` (highest to lowest).",
        "",
        "| Rank | Country | ISO3 | Actual Income (Monthly PPP) | Baseline Income (Monthly PPP) | Income Index | LMI |",
        "| ---: | --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for index, row in enumerate(ranked_rows, start=1):
        lines.append(
            "| "
            f"{index} | "
            f"{row['Country']} | "
            f"{row['ISO3']} | "
            f"{float(row['Actual Income']):,.2f} | "
            f"{float(row['Baseline Income']):,.2f} | "
            f"{float(row['Income Index']):.3f} | "
            f"{float(row['LMI']):.3f} |"
        )

    lines.extend(
        [
            "",
            "Notes:",
            "- Baseline is the composite dignified-stability baseline from the pilot method.",
            "- `LMI < 0` indicates poverty/precarity relative to dignified stability baseline.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_pretty_table(path: Path, rows: List[Dict[str, str]]) -> None:
    """Write a fixed-width aligned table for easy terminal/editor reading."""
    ranked_rows = sorted(rows, key=lambda row: float(row["LMI"]), reverse=True)
    formatted = []
    for index, row in enumerate(ranked_rows, start=1):
        formatted.append(
            {
                "Rank": str(index),
                "Country": row["Country"],
                "ISO3": row["ISO3"],
                "Actual": f"{float(row['Actual Income']):,.2f}",
                "Baseline": f"{float(row['Baseline Income']):,.2f}",
                "Index": f"{float(row['Income Index']):.3f}",
                "LMI": f"{float(row['LMI']):.3f}",
            }
        )

    columns = [
        ("Rank", "Rank"),
        ("Country", "Country"),
        ("ISO3", "ISO3"),
        ("Actual", "Actual Income (Monthly PPP)"),
        ("Baseline", "Baseline Income (Monthly PPP)"),
        ("Index", "Income Index"),
        ("LMI", "LMI"),
    ]

    widths = {}
    for key, header in columns:
        widths[key] = max(len(header), *(len(row[key]) for row in formatted))

    def _line(row: dict[str, str]) -> str:
        return " | ".join(
            row[key].ljust(widths[key]) if key in {"Country"} else row[key].rjust(widths[key])
            for key, _ in columns
        )

    header = _line({key: title for key, title in columns})
    separator = "-+-".join("-" * widths[key] for key, _ in columns)
    lines = [
        "Pilot 20-Country LMI Table (2022)",
        "Ranked by LMI (highest to lowest)",
        "",
        header,
        separator,
    ]
    for row in formatted:
        lines.append(_line(row))

    lines.extend(
        [
            "",
            "Notes:",
            "- Baseline is the composite dignified-stability baseline from the pilot method.",
            "- LMI < 0 indicates poverty/precarity relative to dignified stability baseline.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    rows = build_rows()
    write_csv(OUTPUT_DATA, rows)
    write_csv(OUTPUT_TIMESTAMPED, rows)
    write_markdown_table(OUTPUT_TABLE_MARKDOWN, rows)
    write_pretty_table(OUTPUT_TABLE_PRETTY, rows)
    print(f"Wrote: {OUTPUT_DATA}")
    print(f"Wrote: {OUTPUT_TIMESTAMPED}")
    print(f"Wrote: {OUTPUT_TABLE_MARKDOWN}")
    print(f"Wrote: {OUTPUT_TABLE_PRETTY}")


if __name__ == "__main__":
    main()
