import pydantic_settings


class Settings(pydantic_settings.BaseSettings):
    app_name: str = "Saleor FastAPI Backend"
    app_version: str = "0.1.0"

    environment: str = "development"
    debug: bool = True

    api_v1_prefix: str = "/api/v1"

    log_level: str = "INFO"

    model_config = pydantic_settings.SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


settings = Settings()