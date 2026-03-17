"""Command-line reporting utility for LMI summary statistics."""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from pathlib import Path
from typing import Dict, Iterable, List, Optional


def _weighted_mean(values: List[float], weights: List[float]) -> float:
    return sum(value * weight for value, weight in zip(values, weights)) / sum(weights)


def _weighted_share_below_zero(values: List[float], weights: List[float]) -> float:
    below_weight = sum(weight for value, weight in zip(values, weights) if value < 0)
    return below_weight / sum(weights)


def _weighted_median(values: List[float], weights: List[float]) -> float:
    ordered = sorted(zip(values, weights), key=lambda pair: pair[0])
    half_weight = sum(weights) / 2.0
    cumulative_weight = 0.0
    for value, weight in ordered:
        cumulative_weight += weight
        if cumulative_weight >= half_weight:
            return value
    return ordered[-1][0]


def _parse_rows(
    rows: Iterable[Dict[str, str]],
    *,
    lmi_column: str,
    weight_column: Optional[str],
) -> tuple[List[float], List[float]]:
    lmi_values: List[float] = []
    weights: List[float] = []
    for row in rows:
        if lmi_column not in row:
            raise ValueError(f"Missing required column: '{lmi_column}'")
        lmi_values.append(float(row[lmi_column]))
        if weight_column:
            if weight_column not in row:
                raise ValueError(f"Missing required column: '{weight_column}'")
            weight = float(row[weight_column])
            if weight <= 0:
                raise ValueError(f"Weight must be greater than zero in column '{weight_column}'.")
            weights.append(weight)
        else:
            weights.append(1.0)
    return lmi_values, weights


def summarize_lmi_rows(
    rows: Iterable[Dict[str, str]],
    lmi_column: str = "LMI",
    weight_column: Optional[str] = None,
) -> Dict[str, float]:
    """Compute summary statistics from rows containing an LMI column."""
    lmi_values, weights = _parse_rows(
        rows,
        lmi_column=lmi_column,
        weight_column=weight_column,
    )
    if not lmi_values:
        raise ValueError("No rows available for summary.")

    if weight_column:
        mean_lmi = _weighted_mean(lmi_values, weights)
        median_lmi = _weighted_median(lmi_values, weights)
    else:
        mean_lmi = statistics.mean(lmi_values)
        median_lmi = statistics.median(lmi_values)

    return {
        "sample_size": len(lmi_values),
        "weighted_sample_size": round(sum(weights), 6),
        "mean_lmi": round(mean_lmi, 6),
        "median_lmi": round(median_lmi, 6),
        "min_lmi": round(min(lmi_values), 6),
        "max_lmi": round(max(lmi_values), 6),
        "share_below_baseline": round(_weighted_share_below_zero(lmi_values, weights), 6),
        "weighting_applied": 1.0 if weight_column else 0.0,
    }


def summarize_lmi_by_group(
    rows: Iterable[Dict[str, str]],
    *,
    lmi_column: str = "LMI",
    group_column: str = "City",
    row_weight_column: Optional[str] = None,
    group_weight_column: Optional[str] = None,
) -> Dict[str, float]:
    """Compute a weighted national summary from grouped LMI observations."""
    rows_list = list(rows)
    if not rows_list:
        raise ValueError("No rows available for summary.")

    grouped_rows: Dict[str, List[Dict[str, str]]] = {}
    for row in rows_list:
        if group_column not in row:
            raise ValueError(f"Missing required column: '{group_column}'")
        group_key = row[group_column]
        grouped_rows.setdefault(group_key, []).append(row)

    group_means: List[float] = []
    group_weights: List[float] = []
    for group_key, group_items in grouped_rows.items():
        group_summary = summarize_lmi_rows(
            group_items,
            lmi_column=lmi_column,
            weight_column=row_weight_column,
        )
        group_means.append(group_summary["mean_lmi"])

        if group_weight_column:
            if group_weight_column not in group_items[0]:
                raise ValueError(f"Missing required column: '{group_weight_column}'")
            group_weight = float(group_items[0][group_weight_column])
            if group_weight <= 0:
                raise ValueError(
                    f"Group weight must be greater than zero in column '{group_weight_column}'."
                )
            for row in group_items[1:]:
                if float(row[group_weight_column]) != group_weight:
                    raise ValueError(
                        f"Inconsistent '{group_weight_column}' within group '{group_key}'."
                    )
            group_weights.append(group_weight)
        else:
            group_weights.append(1.0)

    return {
        "sample_size": len(rows_list),
        "group_count": len(group_means),
        "weighted_group_size": round(sum(group_weights), 6),
        "mean_lmi": round(_weighted_mean(group_means, group_weights), 6),
        "median_lmi": round(_weighted_median(group_means, group_weights), 6),
        "min_lmi": round(min(group_means), 6),
        "max_lmi": round(max(group_means), 6),
        "share_below_baseline": round(
            _weighted_share_below_zero(group_means, group_weights), 6
        ),
        "aggregation_level": 1.0,
        "group_weighting_applied": 1.0 if group_weight_column else 0.0,
        "within_group_weighting_applied": 1.0 if row_weight_column else 0.0,
    }


def run_report(
    input_path: Path,
    output_path: Path,
    lmi_column: str = "LMI",
    weight_column: Optional[str] = None,
    group_column: Optional[str] = None,
    group_weight_column: Optional[str] = None,
) -> Dict[str, float]:
    """Read CSV, compute LMI summary stats, and write JSON output."""
    with input_path.open("r", encoding="utf-8", newline="") as input_file:
        reader = csv.DictReader(input_file)
        rows = list(reader)

    if group_column:
        summary = summarize_lmi_by_group(
            rows,
            lmi_column=lmi_column,
            group_column=group_column,
            row_weight_column=weight_column,
            group_weight_column=group_weight_column,
        )
    else:
        summary = summarize_lmi_rows(
            rows,
            lmi_column=lmi_column,
            weight_column=weight_column,
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as output_file:
        json.dump(summary, output_file, indent=2)
    return summary


def build_parser() -> argparse.ArgumentParser:
    """Build command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="lmi-report",
        description="Generate summary statistics from an LMI CSV dataset.",
    )
    parser.add_argument("--input", required=True, help="Path to input CSV file.")
    parser.add_argument("--output", required=True, help="Path to output JSON file.")
    parser.add_argument(
        "--lmi-column",
        default="LMI",
        help="Column name containing LMI values.",
    )
    parser.add_argument(
        "--weight-column",
        default=None,
        help="Optional row-level weight column (for survey/population weighting).",
    )
    parser.add_argument(
        "--group-column",
        default=None,
        help="Optional grouping column (for two-stage city -> country aggregation).",
    )
    parser.add_argument(
        "--group-weight-column",
        default=None,
        help="Optional group-level weight column (for weighted aggregation of group means).",
    )
    return parser


def main() -> int:
    """CLI entrypoint."""
    parser = build_parser()
    args = parser.parse_args()
    summary = run_report(
        input_path=Path(args.input),
        output_path=Path(args.output),
        lmi_column=args.lmi_column,
        weight_column=args.weight_column,
        group_column=args.group_column,
        group_weight_column=args.group_weight_column,
    )
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
