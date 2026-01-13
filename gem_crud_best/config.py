from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DB_USER: str = "postgres"
    DB_PASS: str = "postgres"
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "app_db"
    ECHO_SQL: bool = True  # Useful for debugging

    @property
    def DATABASE_URL(self) -> str:
        # Modern AsyncPG connection string
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # For testing/demo purposes, we might want to allow overriding the entire URL
    # e.g. to "sqlite+aiosqlite:///./test.db"
    OVERRIDE_DATABASE_URL: str | None = None

    @property
    def FINAL_DATABASE_URL(self) -> str:
        return self.OVERRIDE_DATABASE_URL or self.DATABASE_URL

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
