"""Reproducible empirical demo for Life Margin Index (LMI).

This script:
1) Loads the synthetic sample dataset.
2) Recomputes Income Index and LMI using src/lmi.py.
3) Produces summary statistics and threshold shares.
4) Writes outputs to analysis/output for transparent reuse.
"""

from __future__ import annotations

import csv
import json
import os
import statistics
import sys
from typing import Dict, List

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from lmi import compute_income_index, compute_lmi  # noqa: E402


def _read_dataset(path: str) -> List[Dict[str, str]]:
    with open(path, "r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader)


def _to_float(value: str, field: str) -> float:
    try:
        return float(value)
    except ValueError as exc:
        raise ValueError(f"Invalid numeric value for '{field}': {value}") from exc


def main() -> None:
    dataset_path = os.path.join(PROJECT_ROOT, "examples", "sample_dataset.csv")
    output_dir = os.path.join(PROJECT_ROOT, "analysis", "output")
    os.makedirs(output_dir, exist_ok=True)

    rows = _read_dataset(dataset_path)
    if not rows:
        raise ValueError("Dataset is empty.")

    enriched: List[Dict[str, object]] = []
    lmi_values: List[float] = []
    below_baseline = 0

    for row in rows:
        region = row["Region"]
        baseline = _to_float(row["Baseline Income"], "Baseline Income")
        actual = _to_float(row["Actual Income"], "Actual Income")
        provided_ii = _to_float(row["Income Index"], "Income Index")
        provided_lmi = _to_float(row["LMI"], "LMI")

        computed_ii = compute_income_index(actual, baseline)
        computed_lmi = compute_lmi(actual, baseline)
        ii_diff = computed_ii - provided_ii
        lmi_diff = computed_lmi - provided_lmi

        if computed_lmi < 0:
            below_baseline += 1

        lmi_values.append(computed_lmi)
        enriched.append(
            {
                "Region": region,
                "Baseline Income": baseline,
                "Actual Income": actual,
                "Provided Income Index": provided_ii,
                "Computed Income Index": round(computed_ii, 6),
                "Income Index Difference": round(ii_diff, 6),
                "Provided LMI": provided_lmi,
                "Computed LMI": round(computed_lmi, 6),
                "LMI Difference": round(lmi_diff, 6),
            }
        )

    summary = {
        "sample_size": len(rows),
        "mean_lmi": round(statistics.mean(lmi_values), 6),
        "median_lmi": round(statistics.median(lmi_values), 6),
        "min_lmi": round(min(lmi_values), 6),
        "max_lmi": round(max(lmi_values), 6),
        "share_below_baseline": round(below_baseline / len(rows), 6),
    }

    csv_out = os.path.join(output_dir, "empirical_demo_results.csv")
    with open(csv_out, "w", encoding="utf-8", newline="") as handle:
        fieldnames = list(enriched[0].keys())
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in enriched:
            writer.writerow(row)

    json_out = os.path.join(output_dir, "empirical_demo_summary.json")
    with open(json_out, "w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)

    print("Empirical demo complete.")
    print(f"Wrote: {csv_out}")
    print(f"Wrote: {json_out}")
    print(f"Summary: {summary}")


if __name__ == "__main__":
    main()
