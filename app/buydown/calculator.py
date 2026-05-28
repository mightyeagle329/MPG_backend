from dataclasses import dataclass


@dataclass
class BuydownScenarios:
    base_rate: float
    permanent_rate: float
    permanent_points_used: float
    one_one_year1: float
    one_one_year2_plus: float
    two_one_year1: float
    two_one_year2: float
    two_one_year3_plus: float


def permanent_buydown_rate(
    base_rate: float,
    rate_sheet: list[tuple[float, float]],
    point_budget: float,
) -> float:
    """Find the lowest rate the borrower can reach by spending up to
    `point_budget` discount points, based on the pricing API rate sheet.

    rate_sheet entries are (rate_percent, points_cost). Positive cost means
    the borrower pays points to reach that rate.
    """
    if not rate_sheet:
        return base_rate

    affordable = [
        (rate, cost)
        for rate, cost in rate_sheet
        if cost <= point_budget and rate <= base_rate
    ]
    if not affordable:
        return base_rate

    return min(affordable, key=lambda x: x[0])[0]


def calculate_buydowns(
    base_rate: float,
    loan_amount: float,
    incentive_amount: float,
    rate_sheet: list[tuple[float, float]],
) -> BuydownScenarios:
    point_budget = (incentive_amount / loan_amount * 100) if loan_amount else 0.0
    perm_rate = permanent_buydown_rate(base_rate, rate_sheet, point_budget)

    return BuydownScenarios(
        base_rate=round(base_rate, 3),
        permanent_rate=round(perm_rate, 3),
        permanent_points_used=round(point_budget, 3),
        one_one_year1=round(base_rate - 1.0, 3),
        one_one_year2_plus=round(base_rate, 3),
        two_one_year1=round(base_rate - 2.0, 3),
        two_one_year2=round(base_rate - 1.0, 3),
        two_one_year3_plus=round(base_rate, 3),
    )
