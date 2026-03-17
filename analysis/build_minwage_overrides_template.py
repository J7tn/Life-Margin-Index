"""Create a template for calibrated minimum-wage/cost inputs.

This helper writes one row per OECD country so manual monthly ranges can be
filled quickly in `data/minwage_cost_inputs_2022.csv`.
"""

from __future__ import annotations

import csv
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = PROJECT_ROOT / "data" / "minwage_cost_inputs_2022_template.csv"
CURRENT_OVERRIDES_PATH = PROJECT_ROOT / "data" / "minwage_cost_inputs_2022.csv"

OECD_ROWS = [
    ("Australia", "AUS"), ("Austria", "AUT"), ("Belgium", "BEL"), ("Canada", "CAN"),
    ("Chile", "CHL"), ("Colombia", "COL"), ("Costa Rica", "CRI"), ("Czechia", "CZE"),
    ("Denmark", "DNK"), ("Estonia", "EST"), ("Finland", "FIN"), ("France", "FRA"),
    ("Germany", "DEU"), ("Greece", "GRC"), ("Hungary", "HUN"), ("Iceland", "ISL"),
    ("Ireland", "IRL"), ("Israel", "ISR"), ("Italy", "ITA"), ("Japan", "JPN"),
    ("Korea, Rep.", "KOR"), ("Latvia", "LVA"), ("Lithuania", "LTU"), ("Luxembourg", "LUX"),
    ("Mexico", "MEX"), ("Netherlands", "NLD"), ("New Zealand", "NZL"), ("Norway", "NOR"),
    ("Poland", "POL"), ("Portugal", "PRT"), ("Slovak Republic", "SVK"), ("Slovenia", "SVN"),
    ("Spain", "ESP"), ("Sweden", "SWE"), ("Switzerland", "CHE"), ("Turkiye", "TUR"),
    ("United Kingdom", "GBR"), ("United States", "USA"),
]


def _load_existing() -> dict[str, dict[str, str]]:
    if not CURRENT_OVERRIDES_PATH.exists():
        return {}
    out: dict[str, dict[str, str]] = {}
    with CURRENT_OVERRIDES_PATH.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            iso3 = (row.get("ISO3") or "").strip().upper()
            if iso3:
                out[iso3] = row
    return out


def main() -> None:
    existing = _load_existing()
    TEMPLATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with TEMPLATE_PATH.open("w", encoding="utf-8", newline="") as handle:
        fieldnames = [
            "Country",
            "ISO3",
            "Minimum Wage Monthly After Tax Low",
            "Minimum Wage Monthly After Tax High",
            "Minimum Cost of Living Monthly Low",
            "Minimum Cost of Living Monthly High",
            "Currency",
            "Source Notes",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for country, iso3 in OECD_ROWS:
            row = existing.get(iso3, {})
            writer.writerow(
                {
                    "Country": row.get("Country", country),
                    "ISO3": iso3,
                    "Minimum Wage Monthly After Tax Low": row.get("Minimum Wage Monthly After Tax Low", ""),
                    "Minimum Wage Monthly After Tax High": row.get("Minimum Wage Monthly After Tax High", ""),
                    "Minimum Cost of Living Monthly Low": row.get("Minimum Cost of Living Monthly Low", ""),
                    "Minimum Cost of Living Monthly High": row.get("Minimum Cost of Living Monthly High", ""),
                    "Currency": row.get("Currency", ""),
                    "Source Notes": row.get("Source Notes", ""),
                }
            )
    print(f"Wrote: {TEMPLATE_PATH}")


if __name__ == "__main__":
    main()
