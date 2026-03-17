"""Build an OECD minimum-wage-based LMI table.

Model:
  - Baseline (B): direct cost components = food + housing/utilities
    from OECD Table 5 (CP01 + CP04, current prices, national currency).
  - Income (A): statutory minimum wage
    from OECD DSD_EARNINGS@MW_CURP (SM_WG, annual, current prices, national currency).

Headline:
  - Income Index = A / B
  - LMI = Income Index - 1

Optional calibration layer:
  - Country-specific monthly after-tax minimum wage and monthly minimum
    cost-of-living ranges can override fetched proxy values.
  - This lets the table reflect lived-reality assumptions directly where the
    default proxy inputs are not satisfactory.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import urlopen
import xml.etree.ElementTree as ET

PROJECT_ROOT = Path(__file__).resolve().parents[1]
import sys

SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from lmi import compute_income_index, compute_lmi

TARGET_YEAR = 2022
OECD_VALUE_SCALE = 1_000_000.0
WB_COUNTRIES_URL = "https://api.worldbank.org/v2/country/all?format=json&per_page=400"
WB_BULK_POP_URL = (
    f"https://api.worldbank.org/v2/country/all/indicator/SP.POP.TOTL"
    f"?format=json&date={TARGET_YEAR}:{TARGET_YEAR}&per_page=30000"
)

OECD_TABLE5_TEMPLATE = (
    "https://api.db.nomics.world/v22/series/OECD/DSD_NAMAIN10@DF_TABLE5_T501/"
    "A.{iso}.S14.S1.P31DC._Z._Z.{coicop}.XDC.V.N.T0117?metadata=1&observations=1"
)
OECD_MW_DATASET = "https://api.db.nomics.world/v22/series/OECD/DSD_EARNINGS@MW_CURP"
ILO_MW_DATASET = "https://api.db.nomics.world/v22/series/ILO/EAR_4MMN_CUR_NB"
UN_HH_SIZE_XLSX = (
    "https://www.un.org/development/desa/pd/sites/www.un.org.development.desa.pd/files/"
    "undesa_pd_2022_hh-size-composition.xlsx"
)
OECD_DP_LIVE_SERIES = "https://api.db.nomics.world/v22/series/OECD/DP_LIVE"

OUTPUT_DATA = PROJECT_ROOT / "data" / f"lmi_country_observations_minwage_oecd_{TARGET_YEAR}.csv"
OUTPUT_PRETTY = (
    PROJECT_ROOT / "analysis" / "output" / f"lmi_country_table_minwage_oecd_{TARGET_YEAR}_pretty.txt"
)
OUTPUT_PRETTY_CALIBRATED = (
    PROJECT_ROOT / "analysis" / "output" / f"lmi_country_table_minwage_oecd_{TARGET_YEAR}_calibrated_pretty.txt"
)
OUTPUT_MARKDOWN = (
    PROJECT_ROOT / "analysis" / "output" / f"lmi_country_table_minwage_oecd_{TARGET_YEAR}.md"
)
OUTPUT_UNMATCHED = (
    PROJECT_ROOT / "analysis" / "output" / f"lmi_country_minwage_oecd_unmatched_{TARGET_YEAR}.csv"
)
OVERRIDES_PATH = PROJECT_ROOT / "data" / f"minwage_cost_inputs_{TARGET_YEAR}.csv"

OECD_ISO3 = [
    "AUS","AUT","BEL","CAN","CHL","COL","CRI","CZE","DNK","EST","FIN","FRA","DEU","GRC",
    "HUN","ISL","IRL","ISR","ITA","JPN","KOR","LVA","LTU","LUX","MEX","NLD","NZL","NOR",
    "POL","PRT","SVK","SVN","ESP","SWE","CHE","TUR","GBR","USA",
]


def _fetch_json(url: str, timeout: int = 20) -> dict | list:
    return json.loads(urlopen(url, timeout=timeout).read().decode("utf-8"))


def _fetch_wb_country_codes() -> Dict[str, str]:
    payload = _fetch_json(WB_COUNTRIES_URL)
    rows = payload[1] if isinstance(payload, list) and len(payload) > 1 else []
    return {row["id"]: row["name"] for row in rows if row.get("id") and row.get("name")}


def _fetch_wb_population() -> Dict[str, float]:
    payload = _fetch_json(WB_BULK_POP_URL)
    rows = payload[1] if isinstance(payload, list) and len(payload) > 1 else []
    out: Dict[str, float] = {}
    for row in rows:
        iso3 = row.get("countryiso3code")
        value = row.get("value")
        if iso3 and value is not None:
            out[iso3] = float(value)
    return out


def _fetch_oecd_table5_value(iso3: str, coicop: str, target_year: int) -> Optional[Tuple[float, int]]:
    url = OECD_TABLE5_TEMPLATE.format(iso=iso3, coicop=coicop)
    try:
        payload = _fetch_json(url, timeout=10)
    except (HTTPError, URLError, TimeoutError):
        return None
    docs = payload.get("series", {}).get("docs", []) if isinstance(payload, dict) else []
    if not docs:
        return None
    s = docs[0]
    period_map = {int(p): float(v) for p, v in zip(s.get("period", []), s.get("value", [])) if v is not None}
    for y in range(target_year, 1999, -1):
        if y in period_map:
            return period_map[y], y
    return None


def _fetch_oecd_minwage_annual(iso3: str, target_year: int) -> Optional[Tuple[float, int, str]]:
    dims = {
        "REF_AREA": [iso3],
        "MEASURE": ["SM_WG"],
        "PAY_PERIOD": ["A"],
        "PRICE_BASE": ["V"],
        "AGGREGATION_OPERATION": ["_Z"],
        "SEX": ["_Z"],
    }
    url = (
        f"{OECD_MW_DATASET}?metadata=1&observations=1&limit=50&dimensions={quote(json.dumps(dims))}"
    )
    try:
        payload = _fetch_json(url, timeout=15)
    except (HTTPError, URLError, TimeoutError):
        return None
    docs = payload.get("series", {}).get("docs", []) if isinstance(payload, dict) else []
    if not docs:
        return None

    # Prefer a unit that matches country currency when multiple exist.
    best = None
    for s in docs:
        period_map = {int(p): float(v) for p, v in zip(s.get("period", []), s.get("value", [])) if v is not None}
        for y in range(target_year, 1999, -1):
            if y in period_map:
                candidate = (period_map[y], y, s["dimensions"]["UNIT_MEASURE"])
                if best is None or y > best[1]:
                    best = candidate
                break
    return best


def _fetch_ilo_minwage_monthly(iso3: str, target_year: int) -> Optional[Tuple[float, int, str]]:
    dims = {
        "ref_area": [iso3],
        "classif1": ["CUR_TYPE_LCU"],
        "frequency": ["A"],
    }
    url = (
        f"{ILO_MW_DATASET}?metadata=1&observations=1&limit=300&dimensions={quote(json.dumps(dims))}"
    )
    try:
        payload = _fetch_json(url, timeout=15)
    except (HTTPError, URLError, TimeoutError):
        return None
    docs = payload.get("series", {}).get("docs", []) if isinstance(payload, dict) else []
    if not docs:
        return None

    by_year: Dict[int, List[float]] = {}
    for s in docs:
        for p, v in zip(s.get("period", []), s.get("value", [])):
            if v is None:
                continue
            year = int(p)
            if year <= target_year:
                by_year.setdefault(year, []).append(float(v))
    if not by_year:
        return None

    year = max(by_year.keys())
    avg_value = sum(by_year[year]) / len(by_year[year])
    return avg_value, year, "LCU"


def _fetch_oecd_tax_wedge_percent(iso3: str, target_year: int) -> Optional[Tuple[float, int]]:
    dims = {
        "LOCATION": [iso3],
        "INDICATOR": ["TAXWEDGE"],
        "SUBJECT": ["TOT"],
        "MEASURE": ["PC_LC"],
        "FREQUENCY": ["A"],
    }
    url = (
        f"{OECD_DP_LIVE_SERIES}?metadata=1&observations=1&limit=20&dimensions={quote(json.dumps(dims))}"
    )
    try:
        payload = _fetch_json(url, timeout=15)
    except (HTTPError, URLError, TimeoutError):
        return None
    docs = payload.get("series", {}).get("docs", []) if isinstance(payload, dict) else []
    if not docs:
        return None
    s = docs[0]
    period_map: Dict[int, float] = {}
    for p, v in zip(s.get("period", []), s.get("value", [])):
        if v is None:
            continue
        try:
            period_map[int(p)] = float(v)
        except (TypeError, ValueError):
            continue
    for y in range(target_year, 1999, -1):
        if y in period_map:
            return period_map[y], y
    return None


def _norm_country(name: str) -> str:
    return "".join(ch.lower() for ch in name if ch.isalnum())


def _excel_serial_to_year(value: str) -> Optional[int]:
    text = (value or "").strip()
    if not text:
        return None
    if "/" in text:
        parts = text.split("/")
        try:
            return int(parts[-1])
        except ValueError:
            return None
    try:
        serial = int(float(text))
    except ValueError:
        return None
    base = datetime(1899, 12, 30)
    try:
        return (base.fromordinal(base.toordinal() + serial)).year
    except Exception:
        return None


def _fetch_un_household_size_latest() -> Dict[str, float]:
    ns = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    raw = urlopen(UN_HH_SIZE_XLSX, timeout=30).read()
    zf = zipfile.ZipFile(io.BytesIO(raw))

    shared: List[str] = []
    ss = ET.fromstring(zf.read("xl/sharedStrings.xml"))
    for si in ss.findall("a:si", ns):
        shared.append("".join((t.text or "") for t in si.iterfind(".//a:t", ns)))

    sheet = ET.fromstring(zf.read("xl/worksheets/sheet3.xml"))
    sheet_data = sheet.find("a:sheetData", ns)
    if sheet_data is None:
        return {}

    latest: Dict[str, Tuple[int, float]] = {}
    for row in sheet_data.findall("a:row", ns):
        cells: Dict[str, str] = {}
        for c in row.findall("a:c", ns):
            ref = c.attrib.get("r", "")
            col = "".join(ch for ch in ref if ch.isalpha())
            v = c.find("a:v", ns)
            if v is None:
                continue
            txt = v.text or ""
            if c.attrib.get("t") == "s":
                txt = shared[int(txt)]
            cells[col] = txt

        country = (cells.get("A") or "").strip()
        year = _excel_serial_to_year(cells.get("D", ""))
        hh_size_txt = (cells.get("E") or "").strip()
        if not country or year is None or hh_size_txt in {"", ".."}:
            continue
        try:
            hh_size = float(hh_size_txt)
        except ValueError:
            continue
        if hh_size <= 0:
            continue

        key = _norm_country(country)
        prev = latest.get(key)
        if prev is None or year > prev[0]:
            latest[key] = (year, hh_size)

    return {k: v for k, (_, v) in latest.items()}


def _household_size_for_country(iso3: str, country: str, hh_map: Dict[str, float]) -> Optional[float]:
    aliases = {
        "KOR": ["Republic of Korea", "Korea, Republic of"],
        "SVK": ["Slovakia", "Slovak Republic"],
        "USA": ["United States of America", "United States"],
        "TUR": ["Türkiye", "Turkiye", "Turkey"],
        "GBR": ["United Kingdom"],
        "CZE": ["Czechia", "Czech Republic"],
    }
    candidates = [country]
    candidates.extend(aliases.get(iso3, []))
    for name in candidates:
        value = hh_map.get(_norm_country(name))
        if value is not None:
            return value
    return None


def _safe_float(value: str) -> Optional[float]:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _load_overrides() -> Dict[str, Dict[str, object]]:
    if not OVERRIDES_PATH.exists():
        return {}

    out: Dict[str, Dict[str, object]] = {}
    with OVERRIDES_PATH.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            iso3 = (row.get("ISO3") or "").strip().upper()
            if not iso3:
                continue
            wage_low = _safe_float(row.get("Minimum Wage Monthly After Tax Low"))
            wage_high = _safe_float(row.get("Minimum Wage Monthly After Tax High"))
            base_low = _safe_float(row.get("Minimum Cost of Living Monthly Low"))
            base_high = _safe_float(row.get("Minimum Cost of Living Monthly High"))
            currency = (row.get("Currency") or "LCU").strip()
            source = (row.get("Source Notes") or "").strip()
            if None in (wage_low, wage_high, base_low, base_high):
                continue
            if wage_low <= 0 or wage_high <= 0 or base_low <= 0 or base_high <= 0:
                continue
            out[iso3] = {
                "country": (row.get("Country") or iso3).strip(),
                "wage_low": wage_low,
                "wage_high": wage_high,
                "base_low": base_low,
                "base_high": base_high,
                "currency": currency or "LCU",
                "source": source or "manual calibrated input",
            }
    return out


def build_rows(
    use_overrides: bool = False,
    apply_after_tax_estimate: bool = True,
) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    wb_names = _fetch_wb_country_codes()
    wb_pop = _fetch_wb_population()
    overrides = _load_overrides() if use_overrides else {}
    hh_sizes = _fetch_un_household_size_latest()
    rows: List[Dict[str, str]] = []
    unmatched: List[Dict[str, str]] = []
    computed_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    for iso3 in OECD_ISO3:
        country = wb_names.get(iso3, iso3)
        override = overrides.get(iso3)

        if override is not None:
            year = TARGET_YEAR
            wage_low = float(override["wage_low"])
            wage_high = float(override["wage_high"])
            base_low = float(override["base_low"])
            base_high = float(override["base_high"])
            gross_wage_monthly = (wage_low + wage_high) / 2.0
            min_wage_monthly = (wage_low + wage_high) / 2.0
            baseline = (base_low + base_high) / 2.0
            food_monthly = 0.0
            housing_monthly = 0.0
            hh_size = 0.0
            mw_unit = str(override["currency"])
            income_source = f"Manual calibrated after-tax monthly wage range ({override['source']})"
            baseline_source = f"Manual calibrated monthly minimum living cost range ({override['source']})"
            source_url_income = ""
            source_url_baseline = ""
            source_population = "N/A (manual calibration)"
            source_url_population = ""
            population_scope = "country-level calibrated minimum-wage household proxy"
            income_definition = "After-tax minimum wage monthly range midpoint"
            baseline_method = "Calibrated monthly minimum cost-of-living range midpoint"
            input_mode = "calibrated"
            calibration_notes = str(override["source"])
            estimated_tax_wedge_pct = 0.0
            net_conversion_factor = 1.0
        else:
            food = _fetch_oecd_table5_value(iso3, "CP01", TARGET_YEAR)
            housing = _fetch_oecd_table5_value(iso3, "CP04", TARGET_YEAR)
            mw_ilo = _fetch_ilo_minwage_monthly(iso3, TARGET_YEAR)
            pop = wb_pop.get(iso3)
            hh_size = _household_size_for_country(iso3, country, hh_sizes)

            if food is None or housing is None:
                unmatched.append({"ISO3": iso3, "Country": country, "Reason": "Missing OECD CP01/CP04 direct cost series"})
                continue
            if mw_ilo is None:
                unmatched.append({"ISO3": iso3, "Country": country, "Reason": "Missing ILO monthly minimum wage series"})
                continue
            if pop is None or pop <= 0:
                unmatched.append({"ISO3": iso3, "Country": country, "Reason": "Missing WB population"})
                continue
            if hh_size is None or hh_size <= 0:
                unmatched.append({"ISO3": iso3, "Country": country, "Reason": "Missing UN average household size"})
                continue

            year = min(food[1], housing[1], mw_ilo[1], TARGET_YEAR)
            food_monthly = ((food[0] * OECD_VALUE_SCALE) / pop) / 12.0
            housing_monthly = ((housing[0] * OECD_VALUE_SCALE) / pop) / 12.0
            baseline_per_capita = food_monthly + housing_monthly
            baseline = baseline_per_capita * hh_size
            gross_wage_monthly = mw_ilo[0]
            tax_year = year
            if apply_after_tax_estimate:
                tax_wedge = _fetch_oecd_tax_wedge_percent(iso3, TARGET_YEAR)
                if tax_wedge is None:
                    unmatched.append({"ISO3": iso3, "Country": country, "Reason": "Missing OECD tax wedge estimate"})
                    continue
                estimated_tax_wedge_pct, tax_year = tax_wedge
                net_conversion_factor = max(0.0, 1.0 - (estimated_tax_wedge_pct / 100.0))
                min_wage_monthly = gross_wage_monthly * net_conversion_factor
            else:
                estimated_tax_wedge_pct = 0.0
                net_conversion_factor = 1.0
                min_wage_monthly = gross_wage_monthly
            mw_unit = mw_ilo[2]
            wage_low = min_wage_monthly
            wage_high = min_wage_monthly
            base_low = baseline
            base_high = baseline
            if apply_after_tax_estimate:
                income_source = (
                    "ILOSTAT EAR_4MMN_CUR_NB (gross monthly minimum wage, LCU) adjusted by "
                    "OECD DP_LIVE TAXWEDGE (TOT, PC_LC)"
                )
                income_definition = "Estimated net minimum wage monthly (gross * (1 - tax wedge))"
                calibration_notes = (
                    f"Tax wedge year {tax_year}; net conversion factor {net_conversion_factor:.4f}."
                )
            else:
                income_source = "ILOSTAT EAR_4MMN_CUR_NB (statutory nominal gross monthly minimum wage, LCU)"
                income_definition = "Statutory minimum wage monthly (gross)"
                calibration_notes = ""
            baseline_source = (
                "OECD DSD_NAMAIN10@DF_TABLE5_T501 (CP01, CP04, XDC.V) converted to per-capita monthly; "
                "scaled to household baseline using UN average household size"
            )
            source_url_income = "https://db.nomics.world/ILO/EAR_4MMN_CUR_NB"
            source_url_baseline = "https://db.nomics.world/OECD/DSD_NAMAIN10@DF_TABLE5_T501"
            source_population = "World Bank WDI SP.POP.TOTL"
            source_url_population = "https://api.worldbank.org/v2/en/indicator/SP.POP.TOTL?format=json"
            population_scope = "country-level proxy using statutory minimum wage"
            baseline_method = "Direct baseline: (food + housing/utilities) per-capita scaled by average household size"
            input_mode = "proxy"

        # Core math requested by user:
        # normalized wage multiple = wage / baseline; LMI = multiple - 1.
        income_index = compute_income_index(min_wage_monthly, baseline)
        lmi = compute_lmi(min_wage_monthly, baseline)
        index_low = wage_low / base_high
        index_high = wage_high / base_low
        lmi_low = index_low - 1.0
        lmi_high = index_high - 1.0

        rows.append(
            {
                "Country": country,
                "Region": country,
                "ISO3": iso3,
                "Observation Period": str(year),
                "Unit of Analysis": "individual",
                "Population Scope": population_scope,
                "Income Definition": income_definition,
                "Input Mode": input_mode,
                "Currency": mw_unit,
                "Gross Minimum Wage Monthly": f"{gross_wage_monthly:.6f}",
                "Estimated Tax Wedge Percent": f"{estimated_tax_wedge_pct:.6f}",
                "Net Conversion Factor": f"{net_conversion_factor:.6f}",
                "Actual Income": f"{min_wage_monthly:.6f}",
                "Actual Income Period": "monthly",
                "Baseline Income": f"{baseline:.6f}",
                "Baseline Income Period": "monthly",
                "Food Component (Monthly Per-Capita LCU)": f"{food_monthly:.6f}",
                "Housing+Utilities Component (Monthly Per-Capita LCU)": f"{housing_monthly:.6f}",
                "Average Household Size": f"{(baseline / (food_monthly + housing_monthly)) if (food_monthly + housing_monthly) > 0 else 0.0:.6f}",
                "Minimum Wage Unit": mw_unit,
                "Minimum Wage Monthly After Tax Low": f"{wage_low:.6f}",
                "Minimum Wage Monthly After Tax High": f"{wage_high:.6f}",
                "Minimum Cost of Living Monthly Low": f"{base_low:.6f}",
                "Minimum Cost of Living Monthly High": f"{base_high:.6f}",
                "Income Index": f"{income_index:.6f}",
                "LMI": f"{lmi:.6f}",
                "Income Index Low": f"{index_low:.6f}",
                "Income Index High": f"{index_high:.6f}",
                "LMI Low": f"{lmi_low:.6f}",
                "LMI High": f"{lmi_high:.6f}",
                "Baseline Method": baseline_method,
                "Calibration Notes": calibration_notes,
                "Source - Baseline Components": baseline_source,
                "Source URL - Baseline Components": source_url_baseline,
                "Source - Income": income_source,
                "Source URL - Income": source_url_income,
                "Source - Population": source_population,
                "Source URL - Population": source_url_population,
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
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text(
            f"LMI Minimum-Wage Table ({TARGET_YEAR})\n"
            "Baseline: monthly minimum living cost. Income: monthly minimum wage (with optional calibrated overrides).\n\n"
            "No rows available.\n",
            encoding="utf-8",
        )
        return

    formatted = [
        {
            "Rank": str(i),
            "Country": r["Country"],
            "ISO3": r["ISO3"],
            "Mode": "CAL" if r.get("Input Mode") == "calibrated" else "PRX",
            "Index": f"{float(r['Income Index']):.2f}x",
            "LMI": f"{float(r['LMI']):.3f}",
            "Range": f"[{float(r['LMI Low']):.2f},{float(r['LMI High']):.2f}]",
        }
        for i, r in enumerate(rows, start=1)
    ]
    cols = [
        ("Rank", "Rank"),
        ("Country", "Country"),
        ("ISO3", "ISO3"),
        ("Mode", "Mode"),
        ("Index", "Min-Wage Mult"),
        ("LMI", "LMI"),
        ("Range", "LMI Range"),
    ]
    widths = {k: max(len(h), *(len(r[k]) for r in formatted)) for k, h in cols}
    lines = [
        f"LMI Minimum-Wage Table ({TARGET_YEAR})",
        "Baseline: monthly minimum living cost. Income: monthly minimum wage (with optional calibrated overrides).",
        "",
        " | ".join((h.ljust(widths[k]) if k == "Country" else h.rjust(widths[k])) for k, h in cols),
        "-+-".join("-" * widths[k] for k, _ in cols),
    ]
    for r in formatted:
        lines.append(" | ".join((r[k].ljust(widths[k]) if k == "Country" else r[k].rjust(widths[k])) for k, _ in cols))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_markdown(path: Path, rows: List[Dict[str, str]]) -> None:
    lines = [
        f"# LMI Minimum-Wage Table ({TARGET_YEAR})",
        "",
        "Baseline: monthly minimum living cost. Income: monthly minimum wage (with optional calibrated overrides).",
        "",
        "| Rank | Country | ISO3 | Mode | Min-Wage Mult | LMI | LMI Range |",
        "| ---: | --- | --- | --- | ---: | ---: | ---: |",
    ]
    for i, r in enumerate(rows, start=1):
        mode = "CAL" if r.get("Input Mode") == "calibrated" else "PRX"
        lines.append(
            f"| {i} | {r['Country']} | {r['ISO3']} | {mode} | {float(r['Income Index']):.2f}x | "
            f"{float(r['LMI']):.3f} | [{float(r['LMI Low']):.2f},{float(r['LMI High']):.2f}] |"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build minimum-wage LMI table with real-source proxies.")
    parser.add_argument(
        "--use-overrides",
        action="store_true",
        help="Use manual calibrated overrides from data/minwage_cost_inputs_2022.csv.",
    )
    parser.add_argument(
        "--after-tax-estimate",
        action=argparse.BooleanOptionalAction,
        default=True,
        help=(
            "Estimate net income from gross monthly minimum wage using OECD tax wedge. "
            "Use --no-after-tax-estimate to keep gross values."
        ),
    )
    args = parser.parse_args()

    rows, unmatched = build_rows(
        use_overrides=args.use_overrides,
        apply_after_tax_estimate=args.after_tax_estimate,
    )
    _write_csv(OUTPUT_DATA, rows)
    _write_csv(OUTPUT_UNMATCHED, unmatched)
    _write_pretty(OUTPUT_PRETTY, rows)
    _write_pretty(OUTPUT_PRETTY_CALIBRATED, [r for r in rows if r.get("Input Mode") == "calibrated"])
    _write_markdown(OUTPUT_MARKDOWN, rows)
    print(f"Wrote: {OUTPUT_DATA}")
    print(f"Wrote: {OUTPUT_UNMATCHED}")
    print(f"Wrote: {OUTPUT_PRETTY}")
    print(f"Wrote: {OUTPUT_PRETTY_CALIBRATED}")
    print(f"Wrote: {OUTPUT_MARKDOWN}")
    print(f"Included countries: {len(rows)}")
    print(f"Excluded countries: {len(unmatched)}")


if __name__ == "__main__":
    main()
