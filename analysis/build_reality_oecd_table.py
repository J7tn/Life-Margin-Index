"""Build a reality-first LMI table using direct official cost components.

Baseline definition:
    B = monthly per-capita food spending + monthly per-capita housing/utilities spending

Direct component source:
    OECD Table 5 (COICOP), national currency current prices
      - CP01: Food and non-alcoholic beverages
      - CP04: Housing, water, electricity, gas and other fuels

Income proxy source:
    OECD Table 5 total household final consumption expenditure (COICOP total `_T`)

Population source:
    World Bank WDI SP.POP.TOTL (for converting OECD household totals to per-capita)
"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

PROJECT_ROOT = Path(__file__).resolve().parents[1]
import sys

SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from lmi import compute_income_index, compute_lmi

TARGET_YEAR = 2022
OECD_VALUE_SCALE = 1_000_000.0  # Table 5 monetary values are reported in millions.
WB_COUNTRIES_URL = "https://api.worldbank.org/v2/country/all?format=json&per_page=400"
WB_GNI_LCU_URL = (
    "https://api.worldbank.org/v2/country/{iso}/indicator/NY.GNP.PCAP.CN"
    "?format=json&date={year}:{year}&per_page=5"
)
WB_POP_URL = (
    "https://api.worldbank.org/v2/country/{iso}/indicator/SP.POP.TOTL"
    "?format=json&date={year}:{year}&per_page=5"
)

OECD_SERIES_TEMPLATE = (
    "https://api.db.nomics.world/v22/series/OECD/DSD_NAMAIN10@DF_TABLE5_T501/"
    "A.{iso}.S14.S1.P31DC._Z._Z.{coicop}.XDC.V.N.T0117?metadata=1&observations=1"
)

OUTPUT_DATA = PROJECT_ROOT / "data" / f"lmi_country_observations_reality_oecd_{TARGET_YEAR}.csv"
OUTPUT_PRETTY = (
    PROJECT_ROOT / "analysis" / "output" / f"lmi_country_table_reality_oecd_{TARGET_YEAR}_pretty.txt"
)
OUTPUT_MARKDOWN = (
    PROJECT_ROOT / "analysis" / "output" / f"lmi_country_table_reality_oecd_{TARGET_YEAR}.md"
)
OUTPUT_UNMATCHED = (
    PROJECT_ROOT / "analysis" / "output" / f"lmi_country_reality_oecd_unmatched_{TARGET_YEAR}.csv"
)

BOTTOM10_INDICATOR = "SI.DST.FRST.10"
TOP10_INDICATOR = "SI.DST.10TH.10"
WB_BULK_GNI_URL = (
    f"https://api.worldbank.org/v2/country/all/indicator/NY.GNP.PCAP.CN"
    f"?format=json&date={TARGET_YEAR}:{TARGET_YEAR}&per_page=30000"
)
WB_BULK_POP_URL = (
    f"https://api.worldbank.org/v2/country/all/indicator/SP.POP.TOTL"
    f"?format=json&date={TARGET_YEAR}:{TARGET_YEAR}&per_page=30000"
)
WB_BULK_BOTTOM10_URL = (
    f"https://api.worldbank.org/v2/country/all/indicator/{BOTTOM10_INDICATOR}"
    f"?format=json&date=2000:{TARGET_YEAR}&per_page=30000"
)
WB_BULK_TOP10_URL = (
    f"https://api.worldbank.org/v2/country/all/indicator/{TOP10_INDICATOR}"
    f"?format=json&date=2000:{TARGET_YEAR}&per_page=30000"
)

OECD_ISO3 = [
    "AUS",
    "AUT",
    "BEL",
    "CAN",
    "CHL",
    "COL",
    "CRI",
    "CZE",
    "DNK",
    "EST",
    "FIN",
    "FRA",
    "DEU",
    "GRC",
    "HUN",
    "ISL",
    "IRL",
    "ISR",
    "ITA",
    "JPN",
    "KOR",
    "LVA",
    "LTU",
    "LUX",
    "MEX",
    "NLD",
    "NZL",
    "NOR",
    "POL",
    "PRT",
    "SVK",
    "SVN",
    "ESP",
    "SWE",
    "CHE",
    "TUR",
    "GBR",
    "USA",
]


def _fetch_json(url: str, timeout: int = 20) -> dict | list:
    return json.loads(urlopen(url, timeout=timeout).read().decode("utf-8"))


def _fetch_wb_country_codes() -> List[Tuple[str, str]]:
    payload = _fetch_json(WB_COUNTRIES_URL)
    rows = payload[1] if isinstance(payload, list) and len(payload) > 1 else []
    out = []
    for row in rows:
        iso3 = row.get("id")
        name = row.get("name")
        if iso3 and name and iso3 not in {"", "WLD"}:
            out.append((iso3, name))
    return out


def _fetch_wb_point(iso3: str, indicator: str, year: int) -> Optional[float]:
    if indicator == "NY.GNP.PCAP.CN":
        url = WB_GNI_LCU_URL.format(iso=iso3, year=year)
    elif indicator == "SP.POP.TOTL":
        url = WB_POP_URL.format(iso=iso3, year=year)
    else:
        raise ValueError(f"Unsupported indicator {indicator}")
    try:
        payload = _fetch_json(url, timeout=15)
    except (HTTPError, URLError, TimeoutError):
        return None
    rows = payload[1] if isinstance(payload, list) and len(payload) > 1 else []
    if rows and rows[0].get("value") is not None:
        return float(rows[0]["value"])
    return None


def _fetch_wb_bulk_indicator(url: str) -> Dict[str, float]:
    try:
        payload = _fetch_json(url, timeout=20)
    except (HTTPError, URLError, TimeoutError):
        return {}
    rows = payload[1] if isinstance(payload, list) and len(payload) > 1 else []
    out: Dict[str, float] = {}
    for row in rows:
        iso3 = row.get("countryiso3code")
        value = row.get("value")
        if iso3 and value is not None:
            out[iso3] = float(value)
    return out


def _fetch_wb_bulk_latest_indicator(url: str) -> Dict[str, Tuple[float, int]]:
    try:
        payload = _fetch_json(url, timeout=20)
    except (HTTPError, URLError, TimeoutError):
        return {}
    rows = payload[1] if isinstance(payload, list) and len(payload) > 1 else []
    out: Dict[str, Tuple[float, int]] = {}
    for row in rows:
        iso3 = row.get("countryiso3code")
        value = row.get("value")
        date = row.get("date")
        if not iso3 or value is None or date is None:
            continue
        year = int(date)
        prev = out.get(iso3)
        if prev is None or year > prev[1]:
            out[iso3] = (float(value), year)
    return out


def _fetch_wb_latest_share(iso3: str, indicator: str, latest_year: int) -> Optional[Tuple[float, int]]:
    url = (
        f"https://api.worldbank.org/v2/country/{iso3}/indicator/{indicator}"
        f"?format=json&date=2000:{latest_year}&per_page=200"
    )
    try:
        payload = _fetch_json(url, timeout=15)
    except (HTTPError, URLError, TimeoutError):
        return None
    rows = payload[1] if isinstance(payload, list) and len(payload) > 1 else []
    best: Optional[Tuple[float, int]] = None
    for row in rows:
        value = row.get("value")
        date = row.get("date")
        if value is None or date is None:
            continue
        year = int(date)
        if best is None or year > best[1]:
            best = (float(value), year)
    return best


def _fetch_oecd_component_total(iso3: str, coicop: str, target_year: int) -> Optional[Tuple[float, int]]:
    url = OECD_SERIES_TEMPLATE.format(iso=iso3, coicop=coicop)
    try:
        payload = _fetch_json(url, timeout=5)
    except (HTTPError, URLError, TimeoutError):
        return None

    docs = payload.get("series", {}).get("docs", []) if isinstance(payload, dict) else []
    if not docs:
        return None
    series = docs[0]
    periods = series.get("period", [])
    values = series.get("value", [])
    period_map = {int(p): float(v) for p, v in zip(periods, values) if v is not None}
    for y in range(target_year, 1999, -1):
        if y in period_map:
            return period_map[y], y
    return None


def build_rows() -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    rows: List[Dict[str, str]] = []
    unmatched: List[Dict[str, str]] = []
    computed_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    wb_country_map = {iso: name for iso, name in _fetch_wb_country_codes()}
    wb_pop_bulk = _fetch_wb_bulk_indicator(WB_BULK_POP_URL)
    wb_bottom_bulk = _fetch_wb_bulk_latest_indicator(WB_BULK_BOTTOM10_URL)
    wb_top_bulk = _fetch_wb_bulk_latest_indicator(WB_BULK_TOP10_URL)

    for iso3 in OECD_ISO3:
        country_name = wb_country_map.get(iso3, iso3)
        food = _fetch_oecd_component_total(iso3, "CP01", TARGET_YEAR)
        housing = _fetch_oecd_component_total(iso3, "CP04", TARGET_YEAR)
        total_consumption = _fetch_oecd_component_total(iso3, "_T", TARGET_YEAR)
        if food is None or housing is None or total_consumption is None:
            unmatched.append(
                {
                    "ISO3": iso3,
                    "Country": country_name,
                    "Reason": "Missing direct OECD CP01/CP04/_T component series",
                }
            )
            continue

        component_year = min(food[1], housing[1], total_consumption[1])
        pop = wb_pop_bulk.get(iso3)
        if pop is None or pop <= 0:
            unmatched.append(
                {
                    "ISO3": iso3,
                    "Country": country_name,
                    "Reason": "Missing WB population for target year",
                }
            )
            continue

        food_monthly_per_capita = ((food[0] * OECD_VALUE_SCALE) / pop) / 12.0
        housing_monthly_per_capita = ((housing[0] * OECD_VALUE_SCALE) / pop) / 12.0
        total_monthly_per_capita = ((total_consumption[0] * OECD_VALUE_SCALE) / pop) / 12.0
        baseline = food_monthly_per_capita + housing_monthly_per_capita
        actual_income = total_monthly_per_capita
        income_index = compute_income_index(actual_income, baseline)
        mean_lmi = compute_lmi(actual_income, baseline)

        bottom10 = wb_bottom_bulk.get(iso3)
        top10 = wb_top_bulk.get(iso3)
        median_multiplier = None
        median_lmi = None
        share_lt_1x = None
        share_ge_1x = None
        share_ge_2x = None
        share_ge_5x = None
        dist_year = ""
        if bottom10 and top10:
            b = bottom10[0] / 100.0
            t = top10[0] / 100.0
            middle = 1.0 - b - t
            if middle >= 0:
                dist_year = str(min(bottom10[1], top10[1]))
                shares = [b] + [middle / 8.0] * 8 + [t]
                decile_multipliers = [income_index * share * 10.0 for share in shares]
                median_multiplier = (decile_multipliers[4] + decile_multipliers[5]) / 2.0
                median_lmi = median_multiplier - 1.0
                share_lt_1x = sum(1 for m in decile_multipliers if m < 1.0) / 10.0
                share_ge_1x = sum(1 for m in decile_multipliers if m >= 1.0) / 10.0
                share_ge_2x = sum(1 for m in decile_multipliers if m >= 2.0) / 10.0
                share_ge_5x = sum(1 for m in decile_multipliers if m >= 5.0) / 10.0

        headline_index = income_index if median_multiplier is None else median_multiplier
        headline_lmi = mean_lmi if median_lmi is None else median_lmi
        lmi_method = "mean-income proxy fallback" if median_lmi is None else "median-citizen decile proxy"

        rows.append(
            {
                "Country": country_name,
                "Region": country_name,
                "ISO3": iso3,
                "Observation Period": str(component_year),
                "Unit of Analysis": "individual",
                "Population Scope": "country-level per-capita proxy",
                "Income Definition": "Household final consumption expenditure (COICOP total), monthly per-capita LCU proxy",
                "Currency": "LCU",
                "Actual Income": f"{actual_income:.6f}",
                "Actual Income Period": "monthly",
                "Baseline Income": f"{baseline:.6f}",
                "Baseline Income Period": "monthly",
                "Food Component (Monthly Per-Capita LCU)": f"{food_monthly_per_capita:.6f}",
                "Housing+Utilities Component (Monthly Per-Capita LCU)": f"{housing_monthly_per_capita:.6f}",
                "Total Household Consumption (Monthly Per-Capita LCU)": f"{total_monthly_per_capita:.6f}",
                "Income Index (Mean Proxy)": f"{income_index:.6f}",
                "LMI (Mean Proxy)": f"{mean_lmi:.6f}",
                "Income Index": f"{headline_index:.6f}",
                "LMI": f"{headline_lmi:.6f}",
                "LMI Construction": lmi_method,
                "Median-Citizen Multiplier (Decile Proxy)": "" if median_multiplier is None else f"{median_multiplier:.6f}",
                "Share Below Baseline (Decile Approx)": "" if share_lt_1x is None else f"{share_lt_1x:.6f}",
                "Share At or Above 1x Baseline (Decile Approx)": "" if share_ge_1x is None else f"{share_ge_1x:.6f}",
                "Share At or Above 2x Baseline (Decile Approx)": "" if share_ge_2x is None else f"{share_ge_2x:.6f}",
                "Share At or Above 5x Baseline (Decile Approx)": "" if share_ge_5x is None else f"{share_ge_5x:.6f}",
                "Distribution Data Year (Deciles)": dist_year,
                "Baseline Method": "Direct cost baseline: food + housing/utilities (official OECD components).",
                "OECD Monetary Scale Applied": "values x 1,000,000 (series reported in millions)",
                "Source - Baseline Components": "OECD DSD_NAMAIN10@DF_TABLE5_T501 (CP01, CP04, XDC.V)",
                "Source URL - Baseline Components": "https://db.nomics.world/OECD/DSD_NAMAIN10@DF_TABLE5_T501",
                "Source - Income Proxy": "OECD DSD_NAMAIN10@DF_TABLE5_T501 (COICOP total _T, XDC.V)",
                "Source URL - Income Proxy": "https://db.nomics.world/OECD/DSD_NAMAIN10@DF_TABLE5_T501",
                "Source - Population": "World Bank WDI SP.POP.TOTL",
                "Source URL - Population": "https://api.worldbank.org/v2/en/indicator/SP.POP.TOTL?format=json",
                "Source - Distribution": "World Bank WDI SI.DST.FRST.10 and SI.DST.10TH.10",
                "Source URL - Distribution": "https://api.worldbank.org/v2/en/indicator/SI.DST.FRST.10?format=json",
                "Computed At (UTC)": computed_at,
            }
        )

    rows.sort(key=lambda r: float(r["LMI"]), reverse=True)
    return rows, unmatched


def _write_csv(path: Path, rows: List[Dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _write_pretty(path: Path, rows: List[Dict[str, str]]) -> None:
    formatted = []
    for i, row in enumerate(rows, start=1):
        formatted.append(
            {
                "Rank": str(i),
                "Country": row["Country"],
                "ISO3": row["ISO3"],
                "LMI": f"{float(row['LMI']):.3f}",
                "MedianMult": (
                    "NA"
                    if row["Median-Citizen Multiplier (Decile Proxy)"] == ""
                    else f"{float(row['Median-Citizen Multiplier (Decile Proxy)']):.2f}x"
                ),
                "GE1": (
                    "NA"
                    if row["Share At or Above 1x Baseline (Decile Approx)"] == ""
                    else f"{float(row['Share At or Above 1x Baseline (Decile Approx)']):.0%}"
                ),
                "LT1": (
                    "NA"
                    if row["Share Below Baseline (Decile Approx)"] == ""
                    else f"{float(row['Share Below Baseline (Decile Approx)']):.0%}"
                ),
            }
        )
    cols = [
        ("Rank", "Rank"),
        ("Country", "Country"),
        ("ISO3", "ISO3"),
        ("LMI", "LMI"),
        ("MedianMult", "Median Mult"),
        ("GE1", "% >= 1x"),
        ("LT1", "% < 1x"),
    ]
    widths = {k: max(len(h), *(len(r[k]) for r in formatted)) for k, h in cols}
    lines = [
        f"LMI Reality-First Table ({TARGET_YEAR})",
        "Direct baseline components only: food + housing/utilities",
        "",
        " | ".join((h.ljust(widths[k]) if k == "Country" else h.rjust(widths[k])) for k, h in cols),
        "-+-".join("-" * widths[k] for k, _ in cols),
    ]
    for r in formatted:
        lines.append(
            " | ".join((r[k].ljust(widths[k]) if k == "Country" else r[k].rjust(widths[k])) for k, _ in cols)
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_markdown(path: Path, rows: List[Dict[str, str]]) -> None:
    lines = [
        f"# LMI Reality-First Table ({TARGET_YEAR})",
        "",
        "Direct baseline components only: food + housing/utilities.",
        "",
        "| Rank | Country | ISO3 | LMI | Median Mult | % >= 1x | % < 1x |",
        "| ---: | --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for i, row in enumerate(rows, start=1):
        median = row["Median-Citizen Multiplier (Decile Proxy)"]
        ge1 = row["Share At or Above 1x Baseline (Decile Approx)"]
        lt1 = row["Share Below Baseline (Decile Approx)"]
        lines.append(
            f"| {i} | {row['Country']} | {row['ISO3']} | {float(row['LMI']):.3f} | "
            f"{('NA' if median == '' else f'{float(median):.2f}x')} | "
            f"{('NA' if ge1 == '' else f'{float(ge1):.0%}')} | "
            f"{('NA' if lt1 == '' else f'{float(lt1):.0%}')} |"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    rows, unmatched = build_rows()
    _write_csv(OUTPUT_DATA, rows)
    _write_csv(OUTPUT_UNMATCHED, unmatched)
    _write_pretty(OUTPUT_PRETTY, rows)
    _write_markdown(OUTPUT_MARKDOWN, rows)
    print(f"Wrote: {OUTPUT_DATA}")
    print(f"Wrote: {OUTPUT_UNMATCHED}")
    print(f"Wrote: {OUTPUT_PRETTY}")
    print(f"Wrote: {OUTPUT_MARKDOWN}")
    print(f"Included countries: {len(rows)}")
    print(f"Excluded countries: {len(unmatched)}")


if __name__ == "__main__":
    main()
