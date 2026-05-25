import httpx

from app.pricing.base import QuoteRequest, QuoteResult

NANOLOS_BASE_URL = "https://api.nanolos.com/micro/quotes"


class PricingApiError(Exception):
    pass


class NanolosPricingClient:
    def __init__(self, organization: str):
        self._organization = organization

    async def get_quote(self, req: QuoteRequest) -> QuoteResult:
        params = {
            "amortizationType": "Fixed",
            "closingDate": "",
            "countyFipsId": req.county_fips_id,
            "creditScore": req.credit_score,
            "escrowsWaived": str(req.escrows_waived).lower(),
            "isCashOut": "false",
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

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(NANOLOS_BASE_URL, params=params)
            if resp.status_code >= 400:
                raise PricingApiError(f"Quote request failed: {resp.status_code} {resp.text}")
            data = resp.json()

        quote = data.get("quote", {})
        errors = quote.get("errors", [])
        if errors:
            raise PricingApiError(f"Quote returned errors: {errors}")

        rate_details = quote.get("rateDetails", [])
        if not rate_details:
            raise PricingApiError("Quote returned no rateDetails")

        best = rate_details[0]
        return QuoteResult(
            base_rate=float(best.get("apr", 0)),
            apr=best.get("apr"),
            total_closing_costs=best.get("totalCosts"),
            monthly_payment=best.get("pitimi") or best.get("pitmi"),
            raw=quote,
        )
