"""Build an all-available-country LMI table from validated public sources.

This script scales the pilot method to all countries where source coverage and
country matching are available for the target year.
"""

from __future__ import annotations

import csv
import io
import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple
from urllib.request import urlopen

PROJECT_ROOT = Path(__file__).resolve().parents[1]
import sys

SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from lmi import compute_income_index, compute_lmi

TARGET_YEAR = "2022"
FOOD_SHARE = 0.156
HOUSING_UTILITIES_SHARE = 0.225
DAYS_PER_MONTH = 365.25 / 12.0

FAO_URL = (
    "https://api.data.apps.fao.org/api/v2/bigquery?"
    "sql_url=https://data.apps.fao.org/catalog/dataset/"
    "bc84bd3e-4c98-46ae-b964-21e93f3f5e87/resource/"
    "5656e46c-5b76-4786-b7ae-e37862abc252/download/"
    "cost-affordabilty-healthy-diet-cahd-query.sql&item_code=70040&download=true"
)
WB_COUNTRY_URL = "https://api.worldbank.org/v2/country/all?format=json&per_page=400"
WB_GNI_URL = (
    f"https://api.worldbank.org/v2/country/all/indicator/NY.GNP.PCAP.PP.CD"
    f"?format=json&date={TARGET_YEAR}:{TARGET_YEAR}&per_page=20000"
)
OECD_REF_URL = "https://data.oecd.org/hha/household-spending.htm"
WB_DECILE_SOURCE_NOTE = (
    "World Bank WDI income shares: bottom 10% and top 10% (latest <= target year); "
    "middle deciles reconstructed by equal-split assumption."
)

OUTPUT_DATA = PROJECT_ROOT / "data" / f"lmi_country_observations_all_{TARGET_YEAR}.csv"
OUTPUT_MANIFEST = (
    PROJECT_ROOT / "data" / f"lmi_country_observations_all_{TARGET_YEAR}_sources.json"
)
OUTPUT_UNMATCHED = PROJECT_ROOT / "analysis" / "output" / f"lmi_country_unmatched_{TARGET_YEAR}.csv"
OUTPUT_TIMESTAMPED = (
    PROJECT_ROOT
    / "analysis"
    / "output"
    / f"lmi_country_table_all_{TARGET_YEAR}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.csv"
)
OUTPUT_MARKDOWN = PROJECT_ROOT / "analysis" / "output" / f"lmi_country_table_all_{TARGET_YEAR}.md"
OUTPUT_PRETTY = (
    PROJECT_ROOT / "analysis" / "output" / f"lmi_country_table_all_{TARGET_YEAR}_pretty.txt"
)

BOTTOM10_INDICATOR = "SI.DST.FRST.10"
TOP10_INDICATOR = "SI.DST.10TH.10"

ALIASES = {
    "china hong kong sar": "hong kong sar china",
    "china taiwan province of": "taiwan china",
    "lao peoples democratic republic": "lao pdr",
    "netherlands kingdom of the": "netherlands",
    "palestine": "west bank and gaza",
    "republic of moldova": "moldova",
    "saint kitts and nevis": "st kitts and nevis",
    "saint lucia": "st lucia",
    "saint vincent and the grenadines": "st vincent and the grenadines",
    "united republic of tanzania": "tanzania",
    "bolivia plurinational state of": "bolivia",
    "democratic republic of the congo": "congo dem rep",
    "congo": "congo rep",
    "czechia": "czech republic",
    "turkiye": "turkiye",
    "bahamas": "bahamas the",
    "gambia": "gambia the",
    "kyrgyzstan": "kyrgyz republic",
    "brunei darussalam": "brunei",
    "iran islamic republic of": "iran islamic rep",
    "venezuela bolivarian republic of": "venezuela rb",
    "viet nam": "vietnam",
    "egypt": "egypt arab rep",
    "republic of korea": "korea rep",
    "united states of america": "united states",
    "united kingdom of great britain and northern ireland": "united kingdom",
}


def _normalize_name(name: str) -> str:
    text = unicodedata.normalize("NFKD", name)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"[^a-z0-9 ]+", " ", text)
    text = " ".join(text.split())
    return ALIASES.get(text, text)


def _fetch_json(url: str) -> list:
    return json.loads(urlopen(url, timeout=120).read().decode("utf-8"))


def _fetch_wb_country_name_map() -> Dict[str, Tuple[str, str]]:
    payload = _fetch_json(WB_COUNTRY_URL)
    rows = payload[1] if isinstance(payload, list) and len(payload) > 1 else []
    mapping: Dict[str, Tuple[str, str]] = {}
    for row in rows:
        iso3 = row.get("id")
        name = row.get("name")
        if not iso3 or not name:
            continue
        mapping[_normalize_name(name)] = (iso3, name)
    return mapping


def _fetch_wb_indicator_values(url: str) -> Dict[str, float]:
    payload = _fetch_json(url)
    rows = payload[1] if isinstance(payload, list) and len(payload) > 1 else []
    values: Dict[str, float] = {}
    for row in rows:
        iso3 = row.get("countryiso3code")
        value = row.get("value")
        if iso3 and value is not None:
            values[iso3] = float(value)
    return values


def _fetch_wb_indicator_latest(indicator_code: str) -> Dict[str, Tuple[float, int]]:
    """Fetch latest non-null indicator value per country up to target year."""
    url = (
        f"https://api.worldbank.org/v2/country/all/indicator/{indicator_code}"
        f"?format=json&date=2000:{TARGET_YEAR}&per_page=30000"
    )
    payload = _fetch_json(url)
    rows = payload[1] if isinstance(payload, list) and len(payload) > 1 else []
    out: Dict[str, Tuple[float, int]] = {}
    for row in rows:
        iso3 = row.get("countryiso3code")
        value = row.get("value")
        date_str = row.get("date")
        if not iso3 or value is None or not date_str:
            continue
        year = int(date_str)
        prev = out.get(iso3)
        if prev is None or year > prev[1]:
            out[iso3] = (float(value), year)
    return out


def _fetch_fao_rows() -> List[Dict[str, str]]:
    text = urlopen(FAO_URL, timeout=180).read().decode("utf-8", "ignore")
    all_rows = list(csv.DictReader(io.StringIO(text)))
    return [
        row
        for row in all_rows
        if row.get("year") == TARGET_YEAR
        and row.get("value_int_ppp_per_person_per_day") not in ("", None)
    ]


def build_rows() -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    wb_name_map = _fetch_wb_country_name_map()
    wb_gni = _fetch_wb_indicator_values(WB_GNI_URL)
    wb_bottom10 = _fetch_wb_indicator_latest(BOTTOM10_INDICATOR)
    wb_top10 = _fetch_wb_indicator_latest(TOP10_INDICATOR)
    fao_rows = _fetch_fao_rows()
    computed_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    output_rows: List[Dict[str, str]] = []
    unmatched_rows: List[Dict[str, str]] = []

    for row in fao_rows:
        country_name = row["country_name_en"]
        normalized = _normalize_name(country_name)
        wb_entry = wb_name_map.get(normalized)
        if wb_entry is None:
            unmatched_rows.append(
                {
                    "Country": country_name,
                    "Reason": "No country-name match in World Bank country list",
                }
            )
            continue

        iso3, wb_name = wb_entry
        gni_year = wb_gni.get(iso3)
        if gni_year is None:
            unmatched_rows.append(
                {
                    "Country": country_name,
                    "ISO3": iso3,
                    "Reason": "Missing required World Bank income indicator value for target year",
                }
            )
            continue

        food_ppp_day = float(row["value_int_ppp_per_person_per_day"])
        actual_income_monthly = gni_year / 12.0
        food_monthly = food_ppp_day * DAYS_PER_MONTH
        housing_utilities_monthly = food_monthly * (HOUSING_UTILITIES_SHARE / FOOD_SHARE)

        baseline_income_monthly = food_monthly + housing_utilities_monthly
        mean_income_index = compute_income_index(actual_income_monthly, baseline_income_monthly)
        mean_lmi = compute_lmi(actual_income_monthly, baseline_income_monthly)

        bottom10 = wb_bottom10.get(iso3)
        top10 = wb_top10.get(iso3)
        has_distribution = bottom10 is not None and top10 is not None
        median_income_proxy = None
        median_lmi = None
        median_multiplier = None
        share_below_baseline_decile = None
        share_at_or_above_1x = None
        share_at_or_above_2x = None
        share_at_or_above_5x = None
        decile_data_year = ""
        if has_distribution:
            bottom_share = bottom10[0] / 100.0
            top_share = top10[0] / 100.0
            middle_share = 1.0 - bottom_share - top_share
            if middle_share < 0:
                has_distribution = False
            else:
                decile_data_year = str(min(bottom10[1], top10[1]))
                # Reconstructed deciles: D1=bottom10, D10=top10, D2-D9 share middle equally.
                shares = [bottom_share] + [middle_share / 8.0] * 8 + [top_share]
                decile_incomes = [actual_income_monthly * share * 10.0 for share in shares]
                decile_multipliers = [income / baseline_income_monthly for income in decile_incomes]
                median_income_proxy = (decile_incomes[4] + decile_incomes[5]) / 2.0
                median_lmi = compute_lmi(median_income_proxy, baseline_income_monthly)
                median_multiplier = (decile_multipliers[4] + decile_multipliers[5]) / 2.0
                share_below_baseline_decile = (
                    sum(1 for income in decile_incomes if income < baseline_income_monthly) / 10.0
                )
                share_at_or_above_1x = (
                    sum(1 for mult in decile_multipliers if mult >= 1.0) / 10.0
                )
                share_at_or_above_2x = (
                    sum(1 for mult in decile_multipliers if mult >= 2.0) / 10.0
                )
                share_at_or_above_5x = (
                    sum(1 for mult in decile_multipliers if mult >= 5.0) / 10.0
                )

        final_income_index = mean_income_index if median_multiplier is None else median_multiplier
        final_lmi = mean_lmi if median_lmi is None else median_lmi
        final_lmi_method = "mean-income proxy fallback" if median_lmi is None else "median-citizen decile proxy"

        output_rows.append(
            {
                "Country": country_name,
                "Region": country_name,
                "ISO3": iso3,
                "World Bank Country Name": wb_name,
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
                "Income Index (Mean Proxy)": f"{mean_income_index:.6f}",
                "LMI (Mean Proxy)": f"{mean_lmi:.6f}",
                "Income Index": f"{final_income_index:.6f}",
                "LMI": f"{final_lmi:.6f}",
                "LMI Construction": final_lmi_method,
                "Median-Citizen Income Proxy (Monthly PPP)": (
                    "" if median_income_proxy is None else f"{median_income_proxy:.6f}"
                ),
                "Median-Citizen LMI (Decile Proxy)": (
                    "" if median_lmi is None else f"{median_lmi:.6f}"
                ),
                "Median-Citizen Multiplier (Decile Proxy)": (
                    "" if median_multiplier is None else f"{median_multiplier:.6f}"
                ),
                "Share Below Baseline (Decile Approx)": (
                    "" if share_below_baseline_decile is None else f"{share_below_baseline_decile:.6f}"
                ),
                "Share At or Above 1x Baseline (Decile Approx)": (
                    "" if share_at_or_above_1x is None else f"{share_at_or_above_1x:.6f}"
                ),
                "Share At or Above 2x Baseline (Decile Approx)": (
                    "" if share_at_or_above_2x is None else f"{share_at_or_above_2x:.6f}"
                ),
                "Share At or Above 5x Baseline (Decile Approx)": (
                    "" if share_at_or_above_5x is None else f"{share_at_or_above_5x:.6f}"
                ),
                "Distribution Data Year (Deciles)": decile_data_year,
                "Baseline Method": (
                    "Cost-of-living baseline: food + housing/utilities, where housing/utilities "
                    "is scaled from food using OECD share ratios."
                ),
                "Source - Actual Income": "World Bank WDI NY.GNP.PCAP.PP.CD",
                "Source URL - Actual Income": WB_GNI_URL,
                "Source - Food": "FAO CoAHD item 70040",
                "Source URL - Food": FAO_URL,
                "Source - Share Ratios": "OECD household expenditure shares (food 15.6%, housing+utilities 22.5%)",
                "Source URL - Share Ratios": OECD_REF_URL,
                "Source - Distribution": WB_DECILE_SOURCE_NOTE,
                "Source URL - Distribution": (
                    "https://api.worldbank.org/v2/country/all/indicator/"
                    "SI.DST.FRST.10?format=json&date=2000:2022&per_page=30000 ; "
                    "https://api.worldbank.org/v2/country/all/indicator/"
                    "SI.DST.10TH.10?format=json&date=2000:2022&per_page=30000"
                ),
                "Computed At (UTC)": computed_at,
            }
        )

    output_rows.sort(key=lambda r: float(r["LMI"]), reverse=True)
    return output_rows, unmatched_rows


def write_csv(path: Path, rows: List[Dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: Path, rows: List[Dict[str, str]]) -> None:
    lines = [
        f"# LMI All-Country Table ({TARGET_YEAR})",
        "",
        "Ranked by `LMI` (highest to lowest) for countries with complete source coverage.",
        "",
        "| Rank | Country | ISO3 | LMI | Median Multiplier | % >= 1x | % >= 2x | % >= 5x | % < 1x |",
        "| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for i, row in enumerate(rows, start=1):
        median_mult = row["Median-Citizen Multiplier (Decile Proxy)"] or "NA"
        share_ge_1 = row["Share At or Above 1x Baseline (Decile Approx)"] or "NA"
        share_ge_2 = row["Share At or Above 2x Baseline (Decile Approx)"] or "NA"
        share_ge_5 = row["Share At or Above 5x Baseline (Decile Approx)"] or "NA"
        share_below = row["Share Below Baseline (Decile Approx)"] or "NA"
        lines.append(
            f"| {i} | {row['Country']} | {row['ISO3']} | "
            f"{float(row['LMI']):.3f} | "
            f"{('NA' if median_mult == 'NA' else f'{float(median_mult):.2f}x')} | "
            f"{('NA' if share_ge_1 == 'NA' else f'{float(share_ge_1):.0%}')} | "
            f"{('NA' if share_ge_2 == 'NA' else f'{float(share_ge_2):.0%}')} | "
            f"{('NA' if share_ge_5 == 'NA' else f'{float(share_ge_5):.0%}')} | "
            f"{('NA' if share_below == 'NA' else f'{float(share_below):.2%}')} |"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_pretty(path: Path, rows: List[Dict[str, str]]) -> None:
    formatted = []
    for i, row in enumerate(rows, start=1):
        formatted.append(
            {
                "Rank": str(i),
                "Country": row["Country"],
                "ISO3": row["ISO3"],
                "Actual": f"{float(row['Actual Income']):,.2f}",
                "Baseline": f"{float(row['Baseline Income']):,.2f}",
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
                "GE2": (
                    "NA"
                    if row["Share At or Above 2x Baseline (Decile Approx)"] == ""
                    else f"{float(row['Share At or Above 2x Baseline (Decile Approx)']):.0%}"
                ),
                "GE5": (
                    "NA"
                    if row["Share At or Above 5x Baseline (Decile Approx)"] == ""
                    else f"{float(row['Share At or Above 5x Baseline (Decile Approx)']):.0%}"
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
        ("GE2", "% >= 2x"),
        ("GE5", "% >= 5x"),
        ("LT1", "% < 1x"),
    ]
    widths = {k: max(len(h), *(len(r[k]) for r in formatted)) for k, h in cols}

    def line(r: Dict[str, str]) -> str:
        return " | ".join(
            r[k].ljust(widths[k]) if k == "Country" else r[k].rjust(widths[k]) for k, _ in cols
        )

    content = [
        f"LMI All-Country Table ({TARGET_YEAR})",
        "Ranked by LMI (highest to lowest).",
        "Quick-read distribution columns answer: 'What % of people make at least Yx baseline?'",
        "",
        line({k: h for k, h in cols}),
        "-+-".join("-" * widths[k] for k, _ in cols),
    ] + [line(r) for r in formatted]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(content) + "\n", encoding="utf-8")


def write_manifest(path: Path, included_count: int, unmatched_count: int) -> None:
    payload = {
        "dataset": f"lmi_country_observations_all_{TARGET_YEAR}",
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "included_country_count": included_count,
        "excluded_country_count": unmatched_count,
        "method": (
            "Baseline = food + housing/utilities. Headline LMI uses median-citizen decile proxy "
            "when available; otherwise mean-income proxy fallback."
        ),
        "sources": [
            {
                "name": "World Bank WDI",
                "indicator": "NY.GNP.PCAP.PP.CD",
                "url": WB_GNI_URL,
            },
            {
                "name": "FAO CoAHD",
                "indicator": "item_code 70040",
                "url": FAO_URL,
            },
            {
                "name": "OECD household expenditure shares",
                "indicator": "Food/Housing/Transport shares",
                "url": OECD_REF_URL,
            },
        ],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    rows, unmatched = build_rows()
    write_csv(OUTPUT_DATA, rows)
    write_csv(OUTPUT_TIMESTAMPED, rows)
    write_markdown(OUTPUT_MARKDOWN, rows)
    write_pretty(OUTPUT_PRETTY, rows)
    write_csv(OUTPUT_UNMATCHED, unmatched)
    write_manifest(OUTPUT_MANIFEST, len(rows), len(unmatched))
    print(f"Wrote: {OUTPUT_DATA}")
    print(f"Wrote: {OUTPUT_TIMESTAMPED}")
    print(f"Wrote: {OUTPUT_MARKDOWN}")
    print(f"Wrote: {OUTPUT_PRETTY}")
    print(f"Wrote: {OUTPUT_UNMATCHED}")
    print(f"Wrote: {OUTPUT_MANIFEST}")
    print(f"Included countries: {len(rows)}")
    print(f"Excluded countries: {len(unmatched)}")


if __name__ == "__main__":
    main()
