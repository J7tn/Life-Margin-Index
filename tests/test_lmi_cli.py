"""Unit tests for CSV-based LMI CLI utilities."""

import csv
import os
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from lmi_cli import compute_rows, run_csv  # noqa: E402


class TestLmiCli(unittest.TestCase):
    def test_compute_rows_adds_columns(self) -> None:
        rows = [
            {"Region": "A", "Actual Income": "2500", "Baseline Income": "2800"},
            {"Region": "B", "Actual Income": "3000", "Baseline Income": "2500"},
        ]
        out = compute_rows(rows)
        self.assertEqual(len(out), 2)
        self.assertIn("Income Index", out[0])
        self.assertIn("LMI", out[0])
        self.assertEqual(out[0]["Income Index"], "0.892857")
        self.assertEqual(out[0]["LMI"], "-0.107143")

    def test_compute_rows_missing_required_column(self) -> None:
        rows = [{"Region": "A", "Actual Income": "1000"}]
        with self.assertRaises(ValueError):
            compute_rows(rows)

    def test_compute_rows_normalizes_mixed_periods(self) -> None:
        rows = [
            {
                "Region": "A",
                "Actual Income": "20",
                "Actual Income Period": "hourly",
                "Baseline Income": "3000",
                "Baseline Income Period": "monthly",
            }
        ]
        out = compute_rows(rows)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["Normalized Actual Income (Monthly)"], "3466.666667")
        self.assertEqual(out[0]["Normalized Baseline Income (Monthly)"], "3000.000000")
        self.assertEqual(out[0]["Normalization Period"], "monthly")
        self.assertEqual(out[0]["Income Index"], "1.155556")
        self.assertEqual(out[0]["LMI"], "0.155556")

    def test_compute_rows_invalid_period_raises(self) -> None:
        rows = [
            {
                "Region": "A",
                "Actual Income": "1000",
                "Actual Income Period": "daily",
                "Baseline Income": "900",
                "Baseline Income Period": "monthly",
            }
        ]
        with self.assertRaises(ValueError):
            compute_rows(rows)

    def test_run_csv_writes_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "in.csv"
            output_path = Path(temp_dir) / "out.csv"

            with input_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(
                    handle, fieldnames=["Region", "Baseline Income", "Actual Income"]
                )
                writer.writeheader()
                writer.writerow(
                    {"Region": "A", "Baseline Income": "2000", "Actual Income": "2200"}
                )

            run_csv(input_path=input_path, output_path=output_path)

            with output_path.open("r", encoding="utf-8", newline="") as handle:
                reader = csv.DictReader(handle)
                rows = list(reader)

            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["Normalized Actual Income (Monthly)"], "2200.000000")
            self.assertEqual(rows[0]["Normalized Baseline Income (Monthly)"], "2000.000000")
            self.assertEqual(rows[0]["Income Index"], "1.100000")
            self.assertEqual(rows[0]["LMI"], "0.100000")


if __name__ == "__main__":
    unittest.main()
