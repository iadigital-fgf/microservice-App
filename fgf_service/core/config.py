from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# .env en la raíz del repo (Marco-App), aunque uvicorn se ejecute desde ahí o desde fgf_service
_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    finnegans_base_url: str

    # Redis
    redis_url: str = "redis://localhost:6379"
    redis_ttl_seconds: int = 300

    # App
    app_env: str = "production"
    log_level: str = "INFO"


settings = Settings()
