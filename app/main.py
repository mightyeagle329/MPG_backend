import secrets

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel

from app.canva.client import CanvaClient
from app.canva.oauth import (
    build_authorize_url,
    exchange_code_for_token,
    generate_pkce_pair,
    token_store,
)
from app.flyer.service import generate_flyer
from app.package.service import generate_package

app = FastAPI(title="Marketing Package Generator - V1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_pkce_cache: dict[str, str] = {}


@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    return """
    <html><body style="font-family: sans-serif; padding: 2rem;">
      <h1>Marketing Package Generator - V1</h1>
      <ol>
        <li><a href="/oauth/login">Connect to Canva</a></li>
        <li>POST /flyer with JSON: {"address": "...", "tier": "5k"}</li>
      </ol>
    </body></html>
    """


@app.get("/oauth/login")
async def oauth_login() -> RedirectResponse:
    verifier, challenge = generate_pkce_pair()
    state = secrets.token_urlsafe(16)
    _pkce_cache[state] = verifier
    url = build_authorize_url(state=state, code_challenge=challenge)
    return RedirectResponse(url)


@app.get("/oauth/callback")
async def oauth_callback(
    code: str = Query(...),
    state: str = Query(...),
) -> dict:
    verifier = _pkce_cache.pop(state, None)
    if not verifier:
        raise HTTPException(status_code=400, detail="Invalid or expired state")
    token = await exchange_code_for_token(code=code, code_verifier=verifier)
    token_store.save(token)
    return {"status": "ok", "message": "Canva connected. You can close this tab."}


@app.get("/brand-templates")
async def list_brand_templates() -> dict:
    try:
        access_token = await token_store.get_access_token()
        client = CanvaClient(access_token)
        items = await client.list_brand_templates()
        return {"count": len(items), "items": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class FlyerRequest(BaseModel):
    address: str
    tier: str


@app.post("/flyer")
async def create_flyer(req: FlyerRequest) -> dict:
    try:
        return await generate_flyer(address=req.address, tier=req.tier)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class PackageRequest(BaseModel):
    address: str
    purchase_price: float
    seller_contribution: float
    tier: str
    credit_score: int = 760
    county_fips_id: str = "13121"
    state: str = "GA"


@app.post("/package")
async def create_package(req: PackageRequest) -> dict:
    try:
        return await generate_package(
            address=req.address,
            purchase_price=req.purchase_price,
            seller_contribution=req.seller_contribution,
            tier=req.tier,
            credit_score=req.credit_score,
            county_fips_id=req.county_fips_id,
            state=req.state,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
