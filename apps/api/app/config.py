"""MarketReality OS – Application configuration.

Uses pydantic-settings to load from environment variables and .env files.
All secrets stay server-side.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # CMC Pro API
    cmc_pro_api_key: str | None = None
    cmc_base_url: str = "https://pro-api.coinmarketcap.com"

    # CMC MCP
    cmc_mcp_api_key: str | None = None
    cmc_mcp_url: str = "https://mcp.coinmarketcap.com/mcp"


    # Cache TTL in seconds
    cache_ttl: int = 120

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
