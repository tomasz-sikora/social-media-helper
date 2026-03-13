"""Application configuration loaded from environment variables / .env file."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # OpenAI / LLM
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_base_url: str = "https://api.openai.com/v1"

    # Feed sources
    hackernews_top_n: int = 30
    rss_feeds: list[str] = [
        "https://wiadomosci.onet.pl/rss.xml",
        "https://feeds.feedburner.com/wiadomosci-onet",
    ]
    # Optional RSSHub instance for social platforms
    rsshub_base_url: str = ""

    # Processing
    dedup_similarity_threshold: float = 0.85
    summary_max_items: int = 50
    cache_ttl_seconds: int = 900  # 15 minutes

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "info"


settings = Settings()
