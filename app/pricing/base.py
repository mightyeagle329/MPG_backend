from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class QuoteRequest:
    purchase_price: float
    loan_amount: float
    credit_score: int
    county_fips_id: str
    state: str
    occupancy_type: str = "Primary Residence"
    property_type_id: int = 1
    loan_product_id: int = 1
    loan_purpose: str = "Purchase"
    lock_period: int = 30
    escrows_waived: bool = False


@dataclass
class QuoteResult:
    base_rate: float
    apr: float | None = None
    total_closing_costs: float | None = None
    monthly_payment: float | None = None
    # Rate sheet: list of (rate_percent, points_cost) pairs from the pricing API.
    # Positive points = borrower pays; negative = lender credit.
    rate_sheet: list[tuple[float, float]] = field(default_factory=list)
    raw: dict | None = None


class PricingClient(Protocol):
    async def get_quote(self, req: QuoteRequest) -> QuoteResult:
        ...
