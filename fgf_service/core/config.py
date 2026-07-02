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

    # Token propio: el servicio genera y renueva su token con estas credenciales
    # (van en el .env, NO en el código). El token en sí NO va acá: vence, así que
    # vive en memoria dentro del cliente (core/finnegans.py).
    finnegans_client_id: str
    finnegans_client_secret: str
    finnegans_token_url: str = "https://api.finneg.com/api/oauth/token"

    # Redis
    redis_url: str = "redis://localhost:6379"
    redis_ttl_seconds: int = 300

    # App
    app_env: str = "production"
    log_level: str = "INFO"


settings = Settings()
