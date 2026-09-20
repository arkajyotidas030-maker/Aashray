from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    jwt_secret: str = "change-me-before-demo-use-32-chars+"
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 12
    database_url: str = "sqlite:///./aashray.db"
    demo_mode: bool = True
    llm_api_key: str = ""
    llm_base_url: str = ""
    osrm_url: str = ""
    media_dir: str = "./media"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    seed_citizen_email: str = "citizen@demo"
    seed_ops_email: str = "ops@demo"
    seed_password: str = "demo"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def llm_configured(self) -> bool:
        return bool(self.llm_api_key)

    @property
    def osrm_configured(self) -> bool:
        return bool(self.osrm_url)


@lru_cache
def get_settings() -> Settings:
    return Settings()
