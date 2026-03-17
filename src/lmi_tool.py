"""Unified CLI for Life Margin Index validation, compute, and reporting workflows."""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path
from typing import Dict, List, Sequence

from lmi_cli import run_csv
from lmi_report_cli import run_report

_SUPPORTED_INCOME_PERIODS = {"hourly", "monthly", "yearly"}
_SUPPORTED_UNITS_OF_ANALYSIS = {"individual", "household", "cohort"}
_CURRENCY_PATTERN = re.compile(r"^[A-Z]{3}$")
_OBSERVATION_PERIOD_PATTERN = re.compile(r"^\d{4}(-\d{2})?$")


def _validate_numeric(value: str, field_name: str, row_number: int) -> float:
    """Convert a CSV string value to float with row-aware errors."""
    try:
        return float(value)
    except ValueError as exc:
        raise ValueError(
            f"Row {row_number}: field '{field_name}' contains non-numeric value '{value}'."
        ) from exc


def _split_csv_columns(raw_columns: str) -> List[str]:
    """Parse a comma-separated column list into normalized names."""
    return [column.strip() for column in raw_columns.split(",") if column.strip()]


def _validate_non_empty(value: str, field_name: str, row_number: int) -> None:
    """Ensure a required metadata field is present and non-empty."""
    if value.strip() == "":
        raise ValueError(f"Row {row_number}: field '{field_name}' must be non-empty.")


def _validate_allowed_value(
    value: str,
    *,
    field_name: str,
    row_number: int,
    allowed_values: Sequence[str],
) -> None:
    token = value.strip().lower()
    if token not in allowed_values:
        allowed = ", ".join(sorted(allowed_values))
        raise ValueError(
            f"Row {row_number}: field '{field_name}' must be one of [{allowed}], got '{value}'."
        )


def _validate_metadata_semantics(
    row: Dict[str, str],
    *,
    row_number: int,
    metadata_columns: Sequence[str],
) -> None:
    """Validate semantic constraints for standard metadata fields."""
    if "Unit of Analysis" in metadata_columns:
        _validate_allowed_value(
            row["Unit of Analysis"],
            field_name="Unit of Analysis",
            row_number=row_number,
            allowed_values=tuple(_SUPPORTED_UNITS_OF_ANALYSIS),
        )

    for period_field in ("Actual Income Period", "Baseline Income Period"):
        if period_field in metadata_columns:
            _validate_allowed_value(
                row[period_field],
                field_name=period_field,
                row_number=row_number,
                allowed_values=tuple(_SUPPORTED_INCOME_PERIODS),
            )

    if "Currency" in metadata_columns:
        currency = row["Currency"].strip()
        if not _CURRENCY_PATTERN.match(currency):
            raise ValueError(
                f"Row {row_number}: field 'Currency' must be ISO 4217 style (e.g., USD, EUR)."
            )

    if "Observation Period" in metadata_columns:
        period = row["Observation Period"].strip()
        if not _OBSERVATION_PERIOD_PATTERN.match(period):
            raise ValueError(
                f"Row {row_number}: field 'Observation Period' must use YYYY or YYYY-MM format."
            )


def validate_dataset(
    input_path: Path,
    actual_income_column: str = "Actual Income",
    baseline_income_column: str = "Baseline Income",
    lmi_column: str = "LMI",
    required_metadata_columns: Sequence[str] | None = None,
) -> Dict[str, float]:
    """Validate CSV schema and value constraints for LMI workflows."""
    with input_path.open("r", encoding="utf-8", newline="") as input_file:
        reader = csv.DictReader(input_file)
        if not reader.fieldnames:
            raise ValueError("Input CSV has no header row.")
        rows: List[Dict[str, str]] = list(reader)

    required_columns = [actual_income_column, baseline_income_column]
    metadata_columns = list(required_metadata_columns or [])
    for column in required_columns:
        if column not in reader.fieldnames:
            raise ValueError(f"Missing required column: '{column}'")
    for column in metadata_columns:
        if column not in reader.fieldnames:
            raise ValueError(f"Missing required column: '{column}'")

    lmi_present = lmi_column in reader.fieldnames
    invalid_lmi_rows = 0
    metadata_violations = 0

    for idx, row in enumerate(rows, start=2):  # header is row 1
        actual = _validate_numeric(row[actual_income_column], actual_income_column, idx)
        baseline = _validate_numeric(
            row[baseline_income_column], baseline_income_column, idx
        )

        if actual < 0:
            raise ValueError(
                f"Row {idx}: field '{actual_income_column}' must be non-negative."
            )
        if baseline <= 0:
            raise ValueError(
                f"Row {idx}: field '{baseline_income_column}' must be greater than zero."
            )

        if lmi_present and row.get(lmi_column, "") != "":
            _validate_numeric(row[lmi_column], lmi_column, idx)
        elif lmi_present:
            invalid_lmi_rows += 1

        for metadata_column in metadata_columns:
            try:
                _validate_non_empty(row[metadata_column], metadata_column, idx)
            except ValueError:
                metadata_violations += 1
                raise
        try:
            _validate_metadata_semantics(
                row,
                row_number=idx,
                metadata_columns=metadata_columns,
            )
        except ValueError:
            metadata_violations += 1
            raise

    return {
        "row_count": len(rows),
        "lmi_column_present": 1.0 if lmi_present else 0.0,
        "empty_lmi_rows": float(invalid_lmi_rows),
        "metadata_columns_checked": float(len(metadata_columns)),
        "metadata_violations": float(metadata_violations),
    }


def build_parser() -> argparse.ArgumentParser:
    """Build a unified parser with validate, compute, and report subcommands."""
    parser = argparse.ArgumentParser(
        prog="lmi",
        description="Unified command-line interface for LMI data processing.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    compute_parser = subparsers.add_parser(
        "compute",
        help="Compute Income Index and LMI columns from a CSV dataset.",
    )
    compute_parser.add_argument("--input", required=True, help="Path to input CSV.")
    compute_parser.add_argument("--output", required=True, help="Path to output CSV.")
    compute_parser.add_argument(
        "--actual-column",
        default="Actual Income",
        help="Column name for actual income values.",
    )
    compute_parser.add_argument(
        "--baseline-column",
        default="Baseline Income",
        help="Column name for baseline income values.",
    )
    compute_parser.add_argument(
        "--actual-period-column",
        default="Actual Income Period",
        help="Optional column containing actual income period (hourly/monthly/yearly).",
    )
    compute_parser.add_argument(
        "--baseline-period-column",
        default="Baseline Income Period",
        help="Optional column containing baseline period (hourly/monthly/yearly).",
    )
    compute_parser.add_argument(
        "--default-actual-period",
        default="monthly",
        help="Fallback period for actual income when period column is missing/blank.",
    )
    compute_parser.add_argument(
        "--default-baseline-period",
        default="monthly",
        help="Fallback period for baseline income when period column is missing/blank.",
    )
    compute_parser.add_argument(
        "--hours-per-week",
        default=40.0,
        type=float,
        help="Hours per week used for hourly -> monthly normalization.",
    )
    compute_parser.add_argument(
        "--weeks-per-year",
        default=52.0,
        type=float,
        help="Weeks per year used for hourly -> monthly normalization.",
    )

    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate required columns and value constraints for an input CSV.",
    )
    validate_parser.add_argument("--input", required=True, help="Path to input CSV.")
    validate_parser.add_argument(
        "--actual-column",
        default="Actual Income",
        help="Column name for actual income values.",
    )
    validate_parser.add_argument(
        "--baseline-column",
        default="Baseline Income",
        help="Column name for baseline income values.",
    )
    validate_parser.add_argument(
        "--lmi-column",
        default="LMI",
        help="Optional LMI column name to validate if present.",
    )
    validate_parser.add_argument(
        "--require-metadata",
        action="store_true",
        help="Require metadata columns and non-empty values for each row.",
    )
    validate_parser.add_argument(
        "--metadata-columns",
        default=(
            "Region,Observation Period,Unit of Analysis,Population Scope,Income Definition,"
            "Currency,Actual Income Period,Baseline Income Period"
        ),
        help="Comma-separated metadata columns used when --require-metadata is enabled.",
    )

    report_parser = subparsers.add_parser(
        "report",
        help="Generate LMI summary statistics JSON from a CSV dataset.",
    )
    report_parser.add_argument("--input", required=True, help="Path to input CSV.")
    report_parser.add_argument("--output", required=True, help="Path to output JSON.")
    report_parser.add_argument(
        "--lmi-column",
        default="LMI",
        help="Column name containing LMI values.",
    )
    report_parser.add_argument(
        "--weight-column",
        default=None,
        help="Optional row-level weight column (for survey/population weighting).",
    )
    report_parser.add_argument(
        "--group-column",
        default=None,
        help="Optional grouping column (for two-stage city -> country aggregation).",
    )
    report_parser.add_argument(
        "--group-weight-column",
        default=None,
        help="Optional group-level weight column (for weighted group means).",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    """Unified CLI entrypoint."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "compute":
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
    elif args.command == "validate":
        required_metadata_columns = (
            _split_csv_columns(args.metadata_columns) if args.require_metadata else []
        )
        validation = validate_dataset(
            input_path=Path(args.input),
            actual_income_column=args.actual_column,
            baseline_income_column=args.baseline_column,
            lmi_column=args.lmi_column,
            required_metadata_columns=required_metadata_columns,
        )
        print(validation)
    elif args.command == "report":
        summary = run_report(
            input_path=Path(args.input),
            output_path=Path(args.output),
            lmi_column=args.lmi_column,
            weight_column=args.weight_column,
            group_column=args.group_column,
            group_weight_column=args.group_weight_column,
        )
        print(summary)
    else:
        parser.error(f"Unknown command: {args.command}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
