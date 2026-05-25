from dataclasses import dataclass
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


@dataclass
class IncentiveTier:
    amount: int
    brand_template_id: str
    permanent_buydown_points: float


class Settings(BaseSettings):
    canva_client_id: str
    canva_client_secret: str
    canva_redirect_uri: str = "http://127.0.0.1:7000/oauth/callback"

    canva_template_5k: str = ""
    canva_template_10k: str = ""

    permanent_points_5k: float = 1.0
    permanent_points_10k: float = 2.0

    pricing_organization: str = "JasminaKrnjetin1465"

    token_file: Path = Path("./.canva_token.json")

    host: str = "127.0.0.1"
    port: int = 7000

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    def tier(self, tier: str) -> IncentiveTier:
        mapping = {
            "5k": IncentiveTier(
                amount=5000,
                brand_template_id=self.canva_template_5k,
                permanent_buydown_points=self.permanent_points_5k,
            ),
            "10k": IncentiveTier(
                amount=10000,
                brand_template_id=self.canva_template_10k,
                permanent_buydown_points=self.permanent_points_10k,
            ),
        }
        info = mapping.get(tier)
        if not info or not info.brand_template_id:
            raise ValueError(f"No configuration for tier '{tier}'")
        return info

    def template_for_tier(self, tier: str) -> str:
        return self.tier(tier).brand_template_id


settings = Settings()
