from functools import lru_cache
import json

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def normalize_database_url(url: str) -> str:
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://") :]
    host = url.split("@")[-1].split("/")[0].split(":")[0]
    if "render.com" in host and "sslmode=" not in url:
        url += ("&" if "?" in url else "?") + "sslmode=require"
    return url


class Settings(BaseSettings):
    app_name: str = "FactoryHR Lite API"
    database_url: str = (
        "postgresql+psycopg://factoryhr:factoryhr@localhost:5432/factoryhr"
    )
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    frontend_url: str = ""
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.1-flash-lite"

    @field_validator("database_url", mode="before")
    @classmethod
    def coerce_database_url(cls, value: object) -> object:
        if isinstance(value, str):
            return normalize_database_url(value)
        return value

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> object:
        if isinstance(value, str):
            text = value.strip()
            if not text:
                return ["http://localhost:3000", "http://127.0.0.1:3000"]
            if text.startswith("["):
                return json.loads(text)
            return [part.strip().rstrip("/") for part in text.split(",") if part.strip()]
        return value

    @model_validator(mode="after")
    def merge_frontend_origin(self) -> "Settings":
        extra = self.frontend_url.strip().rstrip("/")
        if extra and extra not in self.cors_origins:
            self.cors_origins = [*self.cors_origins, extra]
        return self

    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
