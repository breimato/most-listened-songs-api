from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Full connection string wins over the individual DB_* variables.
    database_url: str | None = None

    # Set DB_HOST (e.g. "postgres" in Docker/Kubernetes) to build a PostgreSQL URL.
    db_host: str | None = None
    db_port: int = 5432
    db_name: str = "canciones_db"
    db_username: str = "canciones_user"
    db_password: str = "canciones_pass"

    lastfm_api_key: str = ""
    lastfm_username: str = ""

    # Llave compartida para proteger la API. Vacía = sin autenticación (solo local).
    access_key: str = ""

    # Zona horaria para agrupar reproducciones por día (obsesiones, actividad).
    timezone: str = "Europe/Madrid"

    cors_origins: str = (
        "http://127.0.0.1:5173,http://localhost:5173,"
        "https://breimato.es,https://www.breimato.es"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def sqlalchemy_url(self) -> str:
        if self.database_url:
            return self.database_url
        if self.db_host:
            credentials = f"{quote_plus(self.db_username)}:{quote_plus(self.db_password)}"
            return (
                f"postgresql+psycopg://{credentials}"
                f"@{self.db_host}:{self.db_port}/{self.db_name}"
            )
        return "sqlite:///canciones.db"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
