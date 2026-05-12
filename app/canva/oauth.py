import base64
import hashlib
import json
import secrets
import time
from pathlib import Path
from urllib.parse import urlencode

import httpx

from app.config import settings

CANVA_AUTH_URL = "https://www.canva.com/api/oauth/authorize"
CANVA_TOKEN_URL = "https://api.canva.com/rest/v1/oauth/token"

SCOPES = [
    "design:content:read",
    "design:content:write",
    "design:meta:read",
    "asset:read",
]


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def generate_pkce_pair() -> tuple[str, str]:
    verifier = _b64url(secrets.token_bytes(64))
    challenge = _b64url(hashlib.sha256(verifier.encode("ascii")).digest())
    return verifier, challenge


def build_authorize_url(state: str, code_challenge: str) -> str:
    params = {
        "response_type": "code",
        "client_id": settings.canva_client_id,
        "redirect_uri": settings.canva_redirect_uri,
        "scope": " ".join(SCOPES),
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "state": state,
    }
    return f"{CANVA_AUTH_URL}?{urlencode(params)}"


async def exchange_code_for_token(code: str, code_verifier: str) -> dict:
    auth = (settings.canva_client_id, settings.canva_client_secret)
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "code_verifier": code_verifier,
        "redirect_uri": settings.canva_redirect_uri,
    }
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(CANVA_TOKEN_URL, data=data, auth=auth)
        resp.raise_for_status()
        return resp.json()


async def refresh_access_token(refresh_token: str) -> dict:
    auth = (settings.canva_client_id, settings.canva_client_secret)
    data = {"grant_type": "refresh_token", "refresh_token": refresh_token}
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(CANVA_TOKEN_URL, data=data, auth=auth)
        resp.raise_for_status()
        return resp.json()


class TokenStore:
    def __init__(self, path: Path):
        self.path = path

    def save(self, token: dict) -> None:
        token = dict(token)
        token.setdefault("obtained_at", int(time.time()))
        self.path.write_text(json.dumps(token, indent=2))

    def load(self) -> dict | None:
        if not self.path.exists():
            return None
        return json.loads(self.path.read_text())

    async def get_access_token(self) -> str:
        token = self.load()
        if not token:
            raise RuntimeError(
                "No Canva token found. Visit /oauth/login to authenticate first."
            )
        expires_in = token.get("expires_in", 0)
        obtained_at = token.get("obtained_at", 0)
        if int(time.time()) >= obtained_at + expires_in - 60:
            refreshed = await refresh_access_token(token["refresh_token"])
            self.save(refreshed)
            return refreshed["access_token"]
        return token["access_token"]


token_store = TokenStore(settings.token_file)
