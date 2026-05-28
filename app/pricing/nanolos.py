from datetime import date, timedelta

import httpx

from app.pricing.base import QuoteRequest, QuoteResult

NANOLOS_BASE_URL = "https://api.nanolos.com/micro/quotes"


class PricingApiError(Exception):
    pass


def parse_rate_sheet(rate_data: str) -> list[tuple[float, float]]:
    """Parse the ResolvedDefaultRate string into (rate, points) pairs.

    Format: "4.75000: 11.34200; 4.87500: 10.44800; ..."
    """
    sheet: list[tuple[float, float]] = []
    for pair in rate_data.split(";"):
        pair = pair.strip()
        if not pair or ":" not in pair:
            continue
        rate_str, points_str = pair.split(":", 1)
        try:
            sheet.append((float(rate_str.strip()), float(points_str.strip())))
        except ValueError:
            continue
    return sorted(sheet, key=lambda x: x[0])


def _extract_rate_sheet(best: dict) -> list[tuple[float, float]]:
    fees = best.get("feesItemization", {}) or {}
    findings = fees.get("Error", []) or []
    for finding in findings:
        if finding.get("code") == "ResolvedDefaultRate":
            data = finding.get("data") or ""
            return parse_rate_sheet(data)
    return []


def _par_rate(rate_sheet: list[tuple[float, float]], fallback: float) -> float:
    """The par rate is the lowest rate whose points cost is still >= 0
    (i.e. the cheapest rate the borrower can get without a lender credit)."""
    non_negative = [(rate, cost) for rate, cost in rate_sheet if cost >= 0]
    if not non_negative:
        return fallback
    return min(non_negative, key=lambda x: x[1])[0]


class NanolosPricingClient:
    def __init__(self, organization: str):
        self._organization = organization

    async def get_quote(self, req: QuoteRequest) -> QuoteResult:
        closing_date = (date.today() + timedelta(days=30)).isoformat()

        params = {
            "amortizationType": "Fixed",
            "closingDate": closing_date,
            "countyFipsId": req.county_fips_id,
            "creditScore": req.credit_score,
            "escrowsWaived": str(req.escrows_waived).lower(),
            "hasPreviousVALoan": "false",
            "isCashOut": "false",
            "isVADisabled": "false",
            "isVeteran": "false",
            "loanAmount": req.loan_amount,
            "loanProductId": req.loan_product_id,
            "loanPurpose": req.loan_purpose,
            "lockPeriod": req.lock_period,
            "occupancyType": req.occupancy_type,
            "organization": self._organization,
            "propertyTypeId": req.property_type_id,
            "salesPrice": req.purchase_price,
            "state": req.state,
        }

        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            resp = await client.get(NANOLOS_BASE_URL, params=params)
            if resp.status_code >= 400:
                raise PricingApiError(f"Quote request failed: {resp.status_code} {resp.text}")
            data = resp.json()

        quote = data.get("quote", data)
        errors = quote.get("errors", [])
        if errors:
            raise PricingApiError(f"Quote returned errors: {errors}")

        rate_details = quote.get("rateDetails", [])
        if not rate_details:
            raise PricingApiError("Quote returned no rateDetails")

        best = self._pick_best_rate(rate_details)
        rate_sheet = _extract_rate_sheet(best)

        interest_rate_decimal = best.get("InterestRate") or best.get("rate") or 0
        apr_decimal = best.get("APR") or best.get("apr") or 0
        note_rate = round(float(interest_rate_decimal) * 100, 3)

        base_rate = _par_rate(rate_sheet, fallback=note_rate) if rate_sheet else note_rate

        return QuoteResult(
            base_rate=base_rate,
            apr=round(float(apr_decimal) * 100, 3),
            total_closing_costs=best.get("totalCosts"),
            monthly_payment=best.get("PITIMI") or best.get("PrincipalAndInterestPayment"),
            rate_sheet=rate_sheet,
            raw=best,
        )

    @staticmethod
    def _pick_best_rate(rate_details: list[dict]) -> dict:
        valid = [r for r in rate_details if r.get("IsValid", True)]
        candidates = valid or rate_details
        return min(
            candidates,
            key=lambda r: float(r.get("APR") or r.get("apr") or 999),
        )
