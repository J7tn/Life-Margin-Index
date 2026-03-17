"""Unit tests for the unified `lmi` CLI."""

import csv
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from lmi_tool import main  # noqa: E402


class TestLmiTool(unittest.TestCase):
    def test_compute_and_report_subcommands(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "input.csv"
            computed_path = Path(temp_dir) / "computed.csv"
            summary_path = Path(temp_dir) / "summary.json"

            with input_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=[
                        "Region",
                        "Baseline Income",
                        "Baseline Income Period",
                        "Actual Income",
                        "Actual Income Period",
                    ],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "Region": "A",
                        "Baseline Income": "2000",
                        "Baseline Income Period": "monthly",
                        "Actual Income": "2200",
                        "Actual Income Period": "monthly",
                    }
                )
                writer.writerow(
                    {
                        "Region": "B",
                        "Baseline Income": "15",
                        "Baseline Income Period": "hourly",
                        "Actual Income": "2000",
                        "Actual Income Period": "monthly",
                    }
                )

            exit_code_compute = main(
                [
                    "compute",
                    "--input",
                    str(input_path),
                    "--output",
                    str(computed_path),
                ]
            )
            self.assertEqual(exit_code_compute, 0)
            self.assertTrue(computed_path.exists())
            with computed_path.open("r", encoding="utf-8", newline="") as handle:
                computed_rows = list(csv.DictReader(handle))
            self.assertEqual(
                computed_rows[0]["Normalized Baseline Income (Monthly)"], "2000.000000"
            )
            self.assertEqual(
                computed_rows[1]["Normalized Baseline Income (Monthly)"], "2600.000000"
            )

            exit_code_report = main(
                [
                    "report",
                    "--input",
                    str(computed_path),
                    "--output",
                    str(summary_path),
                ]
            )
            self.assertEqual(exit_code_report, 0)
            self.assertTrue(summary_path.exists())

            with summary_path.open("r", encoding="utf-8") as handle:
                summary = json.load(handle)

            self.assertEqual(summary["sample_size"], 2)
            self.assertEqual(summary["mean_lmi"], -0.065384)
            self.assertEqual(summary["share_below_baseline"], 0.5)

    def test_validate_subcommand(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "input.csv"
            with input_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=["Region", "Baseline Income", "Actual Income", "LMI"],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "Region": "A",
                        "Baseline Income": "2000",
                        "Actual Income": "2200",
                        "LMI": "0.1",
                    }
                )

            exit_code_validate = main(["validate", "--input", str(input_path)])
            self.assertEqual(exit_code_validate, 0)

    def test_validate_subcommand_with_required_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "input_metadata.csv"
            with input_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=[
                        "Region",
                        "Observation Period",
                        "Unit of Analysis",
                        "Population Scope",
                        "Income Definition",
                        "Currency",
                        "Actual Income Period",
                        "Baseline Income Period",
                        "Baseline Income",
                        "Actual Income",
                    ],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "Region": "City-A",
                        "Observation Period": "2026-03",
                        "Unit of Analysis": "household",
                        "Population Scope": "all households",
                        "Income Definition": "net disposable income",
                        "Currency": "GBP",
                        "Actual Income Period": "monthly",
                        "Baseline Income Period": "monthly",
                        "Baseline Income": "2000",
                        "Actual Income": "2200",
                    }
                )

            exit_code_validate = main(
                ["validate", "--input", str(input_path), "--require-metadata"]
            )
            self.assertEqual(exit_code_validate, 0)

    def test_validate_subcommand_rejects_invalid_values(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "invalid.csv"
            with input_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(
                    handle, fieldnames=["Baseline Income", "Actual Income"]
                )
                writer.writeheader()
                writer.writerow({"Baseline Income": "0", "Actual Income": "100"})

            with self.assertRaises(ValueError):
                main(["validate", "--input", str(input_path)])

    def test_validate_subcommand_rejects_missing_required_metadata_values(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "invalid_metadata.csv"
            with input_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=[
                        "Region",
                        "Observation Period",
                        "Unit of Analysis",
                        "Population Scope",
                        "Income Definition",
                        "Currency",
                        "Actual Income Period",
                        "Baseline Income Period",
                        "Baseline Income",
                        "Actual Income",
                    ],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "Region": "City-A",
                        "Observation Period": "2026-03",
                        "Unit of Analysis": "",
                        "Population Scope": "all households",
                        "Income Definition": "net disposable income",
                        "Currency": "GBP",
                        "Actual Income Period": "monthly",
                        "Baseline Income Period": "monthly",
                        "Baseline Income": "2000",
                        "Actual Income": "2200",
                    }
                )

            with self.assertRaises(ValueError):
                main(["validate", "--input", str(input_path), "--require-metadata"])

    def test_validate_subcommand_rejects_invalid_metadata_semantics(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "invalid_metadata_semantics.csv"
            with input_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=[
                        "Region",
                        "Observation Period",
                        "Unit of Analysis",
                        "Population Scope",
                        "Income Definition",
                        "Currency",
                        "Actual Income Period",
                        "Baseline Income Period",
                        "Baseline Income",
                        "Actual Income",
                    ],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "Region": "City-A",
                        "Observation Period": "03/2026",
                        "Unit of Analysis": "family",
                        "Population Scope": "all households",
                        "Income Definition": "net disposable income",
                        "Currency": "gbp",
                        "Actual Income Period": "weekly",
                        "Baseline Income Period": "monthly",
                        "Baseline Income": "2000",
                        "Actual Income": "2200",
                    }
                )

            with self.assertRaises(ValueError):
                main(["validate", "--input", str(input_path), "--require-metadata"])


if __name__ == "__main__":
    unittest.main()
