from functools import lru_cache
import re

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "identity-service"
    app_env: str = "development"
    log_level: str = "INFO"
    port: int = 8101

    database_url: str
    jwt_access_secret: SecretStr = Field(min_length=32)
    jwt_access_expires_in: int = Field(default=900, gt=0)
    jwt_refresh_secret: SecretStr = Field(min_length=32)
    jwt_refresh_expires_in: int = Field(default=604800, gt=0)
    jwt_algorithm: str = "HS256"

    auth_max_failed_attempts: int = Field(default=5, gt=0)
    auth_lock_minutes: int = Field(default=15, gt=0)
    auth_login_rate_limit_window_seconds: int = Field(default=60, gt=0)
    auth_login_rate_limit_max: int = Field(default=10, gt=0)

    seed_admin_name: str | None = None
    seed_admin_email: str | None = None
    seed_admin_password: SecretStr | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator(
        "jwt_access_expires_in", "jwt_refresh_expires_in", mode="before"
    )
    @classmethod
    def parse_duration(cls, value: int | str) -> int:
        if isinstance(value, int):
            return value
        text = str(value).strip().lower()
        if text.isdigit():
            return int(text)
        match = re.fullmatch(r"(\d+)([smhd])", text)
        if not match:
            raise ValueError("duration must use seconds or s/m/h/d suffix")
        amount, unit = match.groups()
        multiplier = {"s": 1, "m": 60, "h": 3600, "d": 86400}[unit]
        return int(amount) * multiplier

    @model_validator(mode="after")
    def require_distinct_jwt_secrets(self) -> "Settings":
        if (
            self.jwt_access_secret.get_secret_value()
            == self.jwt_refresh_secret.get_secret_value()
        ):
            raise ValueError("access and refresh JWT secrets must be different")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
