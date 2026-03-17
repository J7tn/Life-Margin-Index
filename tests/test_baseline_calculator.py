"""Unit tests for baseline income placeholder calculator."""

import os
import sys
import unittest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from baseline_calculator import calculate_baseline_income  # noqa: E402


class TestBaselineCalculator(unittest.TestCase):
    def test_calculate_baseline_nominal(self) -> None:
        result = calculate_baseline_income(
            region="Metro-North",
            period="2026-03",
            household_size=2,
            component_costs={
                "housing": 1400,
                "food": 500,
                "utilities": 250,
                "transport": 220,
                "healthcare": 180,
            },
            contingency_rate=0.1,
        )

        self.assertAlmostEqual(result["subtotal"], 2550.0)
        self.assertAlmostEqual(result["contingency_amount"], 255.0)
        self.assertAlmostEqual(result["baseline_income"], 2805.0)

    def test_validation_errors(self) -> None:
        with self.assertRaises(ValueError):
            calculate_baseline_income(region="", period="2026-03", household_size=1)
        with self.assertRaises(ValueError):
            calculate_baseline_income(region="X", period="", household_size=1)
        with self.assertRaises(ValueError):
            calculate_baseline_income(region="X", period="2026-03", household_size=0)
        with self.assertRaises(ValueError):
            calculate_baseline_income(
                region="X",
                period="2026-03",
                household_size=1,
                contingency_rate=-0.01,
            )

    def test_component_cost_validation(self) -> None:
        with self.assertRaises(TypeError):
            calculate_baseline_income(
                region="X",
                period="2026-03",
                household_size=1,
                component_costs={"food": "100"},  # type: ignore[dict-item]
            )
        with self.assertRaises(ValueError):
            calculate_baseline_income(
                region="X",
                period="2026-03",
                household_size=1,
                component_costs={"food": -100},
            )


if __name__ == "__main__":
    unittest.main()
