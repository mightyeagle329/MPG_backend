from app.buydown.calculator import calculate_buydowns
from app.canva.client import CanvaClient
from app.canva.oauth import token_store
from app.config import settings
from app.pricing.base import QuoteRequest
from app.pricing.nanolos import NanolosPricingClient
from app.statements.generator import statement_generator


async def generate_package(
    address: str,
    purchase_price: float,
    seller_contribution: float,
    tier: str,
    credit_score: int = 760,
    county_fips_id: str = "13121",
    state: str = "GA",
) -> dict:
    tier_info = settings.tier(tier)

    pricing_client = NanolosPricingClient(organization=settings.pricing_organization)
    quote = await pricing_client.get_quote(
        QuoteRequest(
            purchase_price=purchase_price,
            loan_amount=purchase_price * 0.8,
            credit_score=credit_score,
            county_fips_id=county_fips_id,
            state=state,
        )
    )

    buydowns = calculate_buydowns(
        base_rate=quote.base_rate,
        permanent_points=tier_info.permanent_buydown_points,
    )

    statements = statement_generator.generate(
        {
            "address": address,
            "incentive_amount": tier_info.amount,
            "base_rate": buydowns.base_rate,
            "permanent_rate": buydowns.permanent_rate,
            "one_one_year1": buydowns.one_one_year1,
            "two_one_year1": buydowns.two_one_year1,
            "two_one_year2": buydowns.two_one_year2,
        }
    )

    access_token = await token_store.get_access_token()
    canva_client = CanvaClient(access_token)
    design_id = await canva_client.autofill_brand_template(
        brand_template_id=tier_info.brand_template_id,
        data={"Address": address},
    )
    pdf_urls = await canva_client.export_design_as_pdf(design_id)

    return {
        "tier": tier,
        "incentive_amount": tier_info.amount,
        "address": address,
        "purchase_price": purchase_price,
        "seller_contribution": seller_contribution,
        "financing": {
            "base_rate": buydowns.base_rate,
            "permanent": buydowns.permanent_rate,
            "one_one": {
                "year1": buydowns.one_one_year1,
                "year2_plus": buydowns.one_one_year2_plus,
            },
            "two_one": {
                "year1": buydowns.two_one_year1,
                "year2": buydowns.two_one_year2,
                "year3_plus": buydowns.two_one_year3_plus,
            },
        },
        "statements": statements,
        "flyer": {
            "brand_template_id": tier_info.brand_template_id,
            "design_id": design_id,
            "pdf_urls": pdf_urls,
        },
    }
