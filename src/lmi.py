"""Core computation utilities for the Life Margin Index (LMI)."""

from typing import Union

Number = Union[int, float]


def _validate_numeric(value: Number, name: str) -> float:
    """Validate that a value is numeric and return it as float."""
    if not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be numeric (int or float).")
    return float(value)


def compute_income_index(actual_income: Number, baseline_income: Number) -> float:
    """Compute the Income Index as actual income divided by baseline income.

    Args:
        actual_income: Observed monthly income. Must be non-negative.
        baseline_income: Minimum monthly income for dignified stability.
            Must be strictly positive.

    Returns:
        The Income Index value as a float.

    Raises:
        TypeError: If either input is not numeric.
        ValueError: If inputs violate domain constraints.
    """
    actual = _validate_numeric(actual_income, "actual_income")
    baseline = _validate_numeric(baseline_income, "baseline_income")

    if actual < 0:
        raise ValueError("actual_income must be non-negative.")
    if baseline <= 0:
        raise ValueError("baseline_income must be greater than zero.")

    return actual / baseline


def compute_lmi(actual_income: Number, baseline_income: Number) -> float:
    """Compute the Life Margin Index (LMI).

    The LMI is defined as:
        LMI = (actual_income / baseline_income) - 1

    Args:
        actual_income: Observed monthly income. Must be non-negative.
        baseline_income: Minimum monthly income for dignified stability.
            Must be strictly positive.

    Returns:
        The LMI value as a float.

    Raises:
        TypeError: If either input is not numeric.
        ValueError: If inputs violate domain constraints.
    """
    income_index = compute_income_index(actual_income, baseline_income)
    return income_index - 1.0
