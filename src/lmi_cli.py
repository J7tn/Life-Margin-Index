"""Command-line interface for batch LMI computation from CSV files."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Dict, Iterable, List

from lmi import compute_income_index, compute_lmi

_SUPPORTED_PERIODS = {"hourly", "monthly", "yearly"}
_NORM_ACTUAL_COLUMN = "Normalized Actual Income (Monthly)"
_NORM_BASELINE_COLUMN = "Normalized Baseline Income (Monthly)"
_NORM_PERIOD_COLUMN = "Normalization Period"


def _normalize_period(raw_period: str | None, *, default_period: str, field_name: str) -> str:
    """Normalize and validate an income period token."""
    token = (raw_period or "").strip().lower() or default_period.strip().lower()
    if token not in _SUPPORTED_PERIODS:
        raise ValueError(
            f"Unsupported {field_name}: '{token}'. Supported periods: "
            f"{', '.join(sorted(_SUPPORTED_PERIODS))}."
        )
    return token


def _to_monthly_income(
    value: float,
    *,
    period: str,
    hours_per_week: float,
    weeks_per_year: float,
) -> float:
    """Convert income from the given period to a monthly equivalent."""
    if period == "monthly":
        return value
    if period == "yearly":
        return value / 12.0
    return value * hours_per_week * weeks_per_year / 12.0


def compute_rows(
    rows: Iterable[Dict[str, str]],
    actual_income_column: str = "Actual Income",
    baseline_income_column: str = "Baseline Income",
    actual_period_column: str = "Actual Income Period",
    baseline_period_column: str = "Baseline Income Period",
    default_actual_period: str = "monthly",
    default_baseline_period: str = "monthly",
    hours_per_week: float = 40.0,
    weeks_per_year: float = 52.0,
) -> List[Dict[str, str]]:
    """Compute Income Index and LMI for CSV row dictionaries.

    Args:
        rows: Iterable of CSV row dictionaries.
        actual_income_column: Column name containing actual income.
        baseline_income_column: Column name containing baseline income.
        actual_period_column: Optional column name containing actual income period.
        baseline_period_column: Optional column name containing baseline period.
        default_actual_period: Period used when actual period column is absent/blank.
        default_baseline_period: Period used when baseline period column is absent/blank.
        hours_per_week: Hours worked weekly when converting hourly -> monthly.
        weeks_per_year: Weeks worked yearly when converting hourly -> monthly.

    Returns:
        A list of row dictionaries with normalized values and computed metrics.
    """
    if hours_per_week <= 0:
        raise ValueError("hours_per_week must be greater than zero.")
    if weeks_per_year <= 0:
        raise ValueError("weeks_per_year must be greater than zero.")

    normalized_default_actual_period = _normalize_period(
        default_actual_period,
        default_period="monthly",
        field_name="default_actual_period",
    )
    normalized_default_baseline_period = _normalize_period(
        default_baseline_period,
        default_period="monthly",
        field_name="default_baseline_period",
    )

    output: List[Dict[str, str]] = []
    for row in rows:
        if actual_income_column not in row:
            raise ValueError(f"Missing required column: '{actual_income_column}'")
        if baseline_income_column not in row:
            raise ValueError(f"Missing required column: '{baseline_income_column}'")

        actual = float(row[actual_income_column])
        baseline = float(row[baseline_income_column])
        actual_period = _normalize_period(
            row.get(actual_period_column),
            default_period=normalized_default_actual_period,
            field_name=actual_period_column,
        )
        baseline_period = _normalize_period(
            row.get(baseline_period_column),
            default_period=normalized_default_baseline_period,
            field_name=baseline_period_column,
        )
        normalized_actual = _to_monthly_income(
            actual,
            period=actual_period,
            hours_per_week=hours_per_week,
            weeks_per_year=weeks_per_year,
        )
        normalized_baseline = _to_monthly_income(
            baseline,
            period=baseline_period,
            hours_per_week=hours_per_week,
            weeks_per_year=weeks_per_year,
        )

        row_out = dict(row)
        row_out[_NORM_ACTUAL_COLUMN] = f"{normalized_actual:.6f}"
        row_out[_NORM_BASELINE_COLUMN] = f"{normalized_baseline:.6f}"
        row_out[_NORM_PERIOD_COLUMN] = "monthly"
        row_out["Income Index"] = f"{compute_income_index(normalized_actual, normalized_baseline):.6f}"
        row_out["LMI"] = f"{compute_lmi(normalized_actual, normalized_baseline):.6f}"
        output.append(row_out)
    return output


def run_csv(
    input_path: Path,
    output_path: Path,
    actual_income_column: str = "Actual Income",
    baseline_income_column: str = "Baseline Income",
    actual_period_column: str = "Actual Income Period",
    baseline_period_column: str = "Baseline Income Period",
    default_actual_period: str = "monthly",
    default_baseline_period: str = "monthly",
    hours_per_week: float = 40.0,
    weeks_per_year: float = 52.0,
) -> None:
    """Read input CSV, compute metrics, and write output CSV."""
    with input_path.open("r", encoding="utf-8", newline="") as input_file:
        reader = csv.DictReader(input_file)
        if not reader.fieldnames:
            raise ValueError("Input CSV has no header row.")
        rows = list(reader)

    computed_rows = compute_rows(
        rows,
        actual_income_column=actual_income_column,
        baseline_income_column=baseline_income_column,
        actual_period_column=actual_period_column,
        baseline_period_column=baseline_period_column,
        default_actual_period=default_actual_period,
        default_baseline_period=default_baseline_period,
        hours_per_week=hours_per_week,
        weeks_per_year=weeks_per_year,
    )

    computed_fields = {
        _NORM_ACTUAL_COLUMN,
        _NORM_BASELINE_COLUMN,
        _NORM_PERIOD_COLUMN,
        "Income Index",
        "LMI",
    }
    base_fields = [f for f in reader.fieldnames if f not in computed_fields]
    fieldnames = base_fields + [
        _NORM_ACTUAL_COLUMN,
        _NORM_BASELINE_COLUMN,
        _NORM_PERIOD_COLUMN,
        "Income Index",
        "LMI",
    ]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=fieldnames)
        writer.writeheader()
        for row in computed_rows:
            writer.writerow(row)


def build_parser() -> argparse.ArgumentParser:
    """Build command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="lmi-calc",
        description="Compute Income Index and LMI columns for a CSV dataset.",
    )
    parser.add_argument("--input", required=True, help="Path to input CSV file.")
    parser.add_argument("--output", required=True, help="Path to output CSV file.")
    parser.add_argument(
        "--actual-column",
        default="Actual Income",
        help="Column name for actual income values.",
    )
    parser.add_argument(
        "--baseline-column",
        default="Baseline Income",
        help="Column name for baseline income values.",
    )
    parser.add_argument(
        "--actual-period-column",
        default="Actual Income Period",
        help="Optional column containing actual income period (hourly/monthly/yearly).",
    )
    parser.add_argument(
        "--baseline-period-column",
        default="Baseline Income Period",
        help="Optional column containing baseline period (hourly/monthly/yearly).",
    )
    parser.add_argument(
        "--default-actual-period",
        default="monthly",
        help="Fallback period for actual income when period column is missing/blank.",
    )
    parser.add_argument(
        "--default-baseline-period",
        default="monthly",
        help="Fallback period for baseline income when period column is missing/blank.",
    )
    parser.add_argument(
        "--hours-per-week",
        default=40.0,
        type=float,
        help="Hours per week used for hourly -> monthly normalization.",
    )
    parser.add_argument(
        "--weeks-per-year",
        default=52.0,
        type=float,
        help="Weeks per year used for hourly -> monthly normalization.",
    )
    return parser


def main() -> int:
    """CLI entrypoint."""
    parser = build_parser()
    args = parser.parse_args()
    run_csv(
        input_path=Path(args.input),
        output_path=Path(args.output),
        actual_income_column=args.actual_column,
        baseline_income_column=args.baseline_column,
        actual_period_column=args.actual_period_column,
        baseline_period_column=args.baseline_period_column,
        default_actual_period=args.default_actual_period,
        default_baseline_period=args.default_baseline_period,
        hours_per_week=args.hours_per_week,
        weeks_per_year=args.weeks_per_year,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
