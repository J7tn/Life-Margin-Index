"""Unit tests for core LMI computation functions."""

import os
import sys
import unittest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from lmi import compute_income_index, compute_lmi  # noqa: E402


class TestLmiFunctions(unittest.TestCase):
    def test_compute_income_index_nominal(self) -> None:
        self.assertAlmostEqual(compute_income_index(2500, 2800), 0.8928571429)
        self.assertAlmostEqual(compute_income_index(2800, 2800), 1.0)
        self.assertAlmostEqual(compute_income_index(3500, 2800), 1.25)

    def test_compute_lmi_nominal(self) -> None:
        self.assertAlmostEqual(compute_lmi(2500, 2800), -0.1071428571)
        self.assertAlmostEqual(compute_lmi(2800, 2800), 0.0)
        self.assertAlmostEqual(compute_lmi(3500, 2800), 0.25)

    def test_negative_actual_income_raises(self) -> None:
        with self.assertRaises(ValueError):
            compute_income_index(-1, 1000)

    def test_non_positive_baseline_raises(self) -> None:
        with self.assertRaises(ValueError):
            compute_income_index(1000, 0)
        with self.assertRaises(ValueError):
            compute_lmi(1000, -5)

    def test_non_numeric_inputs_raise_type_error(self) -> None:
        with self.assertRaises(TypeError):
            compute_income_index("1000", 800)  # type: ignore[arg-type]
        with self.assertRaises(TypeError):
            compute_lmi(1200, None)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
