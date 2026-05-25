from datetime import date, timedelta

import httpx

from app.pricing.base import QuoteRequest, QuoteResult

NANOLOS_BASE_URL = "https://api.nanolos.com/micro/quotes"


class PricingApiError(Exception):
    pass


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

        interest_rate_decimal = best.get("InterestRate") or best.get("rate") or 0
        apr_decimal = best.get("APR") or best.get("apr") or 0

        return QuoteResult(
            base_rate=round(float(interest_rate_decimal) * 100, 3),
            apr=round(float(apr_decimal) * 100, 3),
            total_closing_costs=best.get("totalCosts"),
            monthly_payment=best.get("PITIMI") or best.get("PrincipalAndInterestPayment"),
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
