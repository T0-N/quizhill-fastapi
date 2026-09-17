from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://quizhill:quizhill@127.0.0.1:5432/quizhill"
    jwt_secret: str = "dev-change-me-please-use-32-bytes+"
    jwt_expire_minutes: int = 60 * 24 * 30
    google_client_ids: str = ""
    auth_dev_mode: bool = True
    admin_password: str = "quizhill"
    seed_on_empty: bool = True

    @property
    def google_audiences(self) -> list[str]:
        return [item.strip() for item in self.google_client_ids.split(",") if item.strip()]


settings = Settings()
