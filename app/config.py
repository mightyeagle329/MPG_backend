from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    canva_client_id: str
    canva_client_secret: str
    canva_redirect_uri: str = "http://127.0.0.1:7000/oauth/callback"

    canva_template_5k: str = ""
    canva_template_10k: str = ""

    token_file: Path = Path("./.canva_token.json")

    host: str = "127.0.0.1"
    port: int = 7000

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    def template_for_tier(self, tier: str) -> str:
        mapping = {
            "5k": self.canva_template_5k,
            "10k": self.canva_template_10k,
        }
        template_id = mapping.get(tier)
        if not template_id:
            raise ValueError(f"No Brand Template configured for tier '{tier}'")
        return template_id


settings = Settings()
