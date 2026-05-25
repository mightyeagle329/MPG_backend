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

        print("=== NANOLOS RAW RESPONSE ===")
        print(data)
        print("=== END ===")

        quote = data.get("quote", {})
        errors = quote.get("errors", [])
        if errors:
            raise PricingApiError(f"Quote returned errors: {errors}")

        rate_details = quote.get("rateDetails", [])
        if not rate_details:
            raise PricingApiError(
                f"Quote returned no rateDetails. Full response: {data}"
            )

        best = rate_details[0]
        fees = best.get("feesItemization", {}) or {}
        return QuoteResult(
            base_rate=float(fees.get("interestRate") or best.get("APR") or 0),
            apr=fees.get("APR") or best.get("APR"),
            total_closing_costs=fees.get("totalClosingCosts") or fees.get("BaseLoanAmount"),
            monthly_payment=fees.get("PITIMI") or fees.get("PIPMI"),
            raw=quote,
        )
