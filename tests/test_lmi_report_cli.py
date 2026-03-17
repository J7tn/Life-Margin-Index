"""Unit tests for LMI reporting CLI utilities."""

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

from lmi_report_cli import run_report, summarize_lmi_by_group, summarize_lmi_rows  # noqa: E402


class TestLmiReportCli(unittest.TestCase):
    def test_summarize_lmi_rows(self) -> None:
        rows = [{"LMI": "-0.1"}, {"LMI": "0.2"}, {"LMI": "0.0"}]
        summary = summarize_lmi_rows(rows)
        self.assertEqual(summary["sample_size"], 3)
        self.assertEqual(summary["mean_lmi"], 0.033333)
        self.assertEqual(summary["median_lmi"], 0.0)
        self.assertEqual(summary["share_below_baseline"], 0.333333)

    def test_summarize_lmi_rows_missing_column(self) -> None:
        with self.assertRaises(ValueError):
            summarize_lmi_rows([{"Region": "A"}])

    def test_summarize_lmi_rows_with_weights(self) -> None:
        rows = [
            {"LMI": "-0.2", "Weight": "9"},
            {"LMI": "0.1", "Weight": "1"},
        ]
        summary = summarize_lmi_rows(rows, weight_column="Weight")
        self.assertEqual(summary["sample_size"], 2)
        self.assertEqual(summary["weighted_sample_size"], 10.0)
        self.assertEqual(summary["mean_lmi"], -0.17)
        self.assertEqual(summary["median_lmi"], -0.2)
        self.assertEqual(summary["share_below_baseline"], 0.9)
        self.assertEqual(summary["weighting_applied"], 1.0)

    def test_summarize_lmi_by_group_with_group_weights(self) -> None:
        rows = [
            {"City": "A", "LMI": "0.5", "City Weight": "1000"},
            {"City": "A", "LMI": "0.3", "City Weight": "1000"},
            {"City": "B", "LMI": "-0.1", "City Weight": "5000"},
            {"City": "B", "LMI": "-0.1", "City Weight": "5000"},
        ]
        summary = summarize_lmi_by_group(
            rows,
            group_column="City",
            group_weight_column="City Weight",
        )
        self.assertEqual(summary["sample_size"], 4)
        self.assertEqual(summary["group_count"], 2)
        self.assertEqual(summary["weighted_group_size"], 6000.0)
        self.assertEqual(summary["mean_lmi"], -0.016667)
        self.assertEqual(summary["share_below_baseline"], 0.833333)

    def test_summarize_lmi_by_group_inconsistent_group_weight_raises(self) -> None:
        rows = [
            {"City": "A", "LMI": "0.1", "City Weight": "100"},
            {"City": "A", "LMI": "0.2", "City Weight": "200"},
        ]
        with self.assertRaises(ValueError):
            summarize_lmi_by_group(
                rows,
                group_column="City",
                group_weight_column="City Weight",
            )

    def test_run_report_writes_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "in.csv"
            output_path = Path(temp_dir) / "summary.json"

            with input_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=["LMI"])
                writer.writeheader()
                writer.writerow({"LMI": "-0.1"})
                writer.writerow({"LMI": "0.3"})

            summary = run_report(input_path=input_path, output_path=output_path)
            self.assertEqual(summary["sample_size"], 2)

            with output_path.open("r", encoding="utf-8") as handle:
                persisted = json.load(handle)

            self.assertEqual(persisted["median_lmi"], 0.1)
            self.assertEqual(persisted["share_below_baseline"], 0.5)

    def test_run_report_grouped_writes_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "in_grouped.csv"
            output_path = Path(temp_dir) / "summary_grouped.json"

            with input_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=["City", "LMI", "Sample Weight", "City Population"],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "City": "A",
                        "LMI": "0.2",
                        "Sample Weight": "2",
                        "City Population": "1000",
                    }
                )
                writer.writerow(
                    {
                        "City": "A",
                        "LMI": "0.0",
                        "Sample Weight": "1",
                        "City Population": "1000",
                    }
                )
                writer.writerow(
                    {
                        "City": "B",
                        "LMI": "-0.1",
                        "Sample Weight": "1",
                        "City Population": "3000",
                    }
                )
                writer.writerow(
                    {
                        "City": "B",
                        "LMI": "-0.3",
                        "Sample Weight": "3",
                        "City Population": "3000",
                    }
                )

            summary = run_report(
                input_path=input_path,
                output_path=output_path,
                lmi_column="LMI",
                weight_column="Sample Weight",
                group_column="City",
                group_weight_column="City Population",
            )
            self.assertEqual(summary["group_count"], 2)
            self.assertEqual(summary["mean_lmi"], -0.154167)

            with output_path.open("r", encoding="utf-8") as handle:
                persisted = json.load(handle)

            self.assertEqual(persisted["group_weighting_applied"], 1.0)
            self.assertEqual(persisted["within_group_weighting_applied"], 1.0)


if __name__ == "__main__":
    unittest.main()
