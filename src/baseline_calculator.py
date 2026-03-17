"""Baseline income calculator interface for the Life Margin framework."""

from typing import Dict, Mapping, Optional, Union

Number = Union[int, float]


def calculate_baseline_income(
    *,
    region: str,
    period: str,
    household_size: int,
    component_costs: Optional[Mapping[str, Number]] = None,
    contingency_rate: float = 0.08,
) -> Dict[str, float]:
    """Calculate baseline income from essential cost components.

    This is a placeholder implementation for the production baseline engine.
    In a real system, inputs would be sourced from regional data pipelines and
    validated against versioned methodology rules.

    Args:
        region: Region identifier used for cost calibration.
        period: Observation period (for example, "2026-03").
        household_size: Number of household members.
        component_costs: Optional monthly essential cost components. Typical
            keys include housing, food, utilities, transport, healthcare, and
            childcare. Values must be non-negative numerics.
        contingency_rate: Fraction added to subtotal as a resilience cushion.

    Returns:
        A dictionary containing:
        - baseline_income: total baseline monthly income
        - subtotal: sum of provided essential components
        - contingency_amount: subtotal multiplied by contingency_rate

    Raises:
        ValueError: If inputs are malformed or outside allowed ranges.
        TypeError: If numeric fields contain non-numeric values.
    """
    if not region or not isinstance(region, str):
        raise ValueError("region must be a non-empty string.")
    if not period or not isinstance(period, str):
        raise ValueError("period must be a non-empty string.")
    if not isinstance(household_size, int) or household_size <= 0:
        raise ValueError("household_size must be a positive integer.")
    if not isinstance(contingency_rate, (int, float)) or contingency_rate < 0:
        raise ValueError("contingency_rate must be a non-negative number.")

    costs = dict(component_costs or {})
    subtotal = 0.0
    for key, value in costs.items():
        if not isinstance(value, (int, float)):
            raise TypeError(f"component_costs['{key}'] must be numeric.")
        if value < 0:
            raise ValueError(f"component_costs['{key}'] must be non-negative.")
        subtotal += float(value)

    contingency_amount = subtotal * float(contingency_rate)
    baseline_income = subtotal + contingency_amount

    return {
        "baseline_income": baseline_income,
        "subtotal": subtotal,
        "contingency_amount": contingency_amount,
    }
