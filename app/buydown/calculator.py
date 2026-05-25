from dataclasses import dataclass


@dataclass
class BuydownScenarios:
    base_rate: float
    permanent_rate: float
    one_one_year1: float
    one_one_year2_plus: float
    two_one_year1: float
    two_one_year2: float
    two_one_year3_plus: float


def calculate_buydowns(base_rate: float, permanent_points: float) -> BuydownScenarios:
    return BuydownScenarios(
        base_rate=round(base_rate, 3),
        permanent_rate=round(base_rate - permanent_points, 3),
        one_one_year1=round(base_rate - 1.0, 3),
        one_one_year2_plus=round(base_rate, 3),
        two_one_year1=round(base_rate - 2.0, 3),
        two_one_year2=round(base_rate - 1.0, 3),
        two_one_year3_plus=round(base_rate, 3),
    )
