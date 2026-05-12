from app.canva.client import CanvaClient
from app.canva.oauth import token_store
from app.config import settings


async def generate_flyer(address: str, tier: str) -> dict:
    brand_template_id = settings.template_for_tier(tier)
    access_token = await token_store.get_access_token()
    client = CanvaClient(access_token)

    design_id = await client.autofill_brand_template(
        brand_template_id=brand_template_id,
        data={"address": address},
    )
    pdf_urls = await client.export_design_as_pdf(design_id)

    return {
        "tier": tier,
        "brand_template_id": brand_template_id,
        "design_id": design_id,
        "pdf_urls": pdf_urls,
    }
