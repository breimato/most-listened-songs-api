from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///canciones.db"
    youtube_api_key: str = ""
    google_client_id: str = ""
    google_client_secret: str = ""
    google_drive_folder: str = "Takeout"
    data_dir: str = "data"
    lastfm_api_key: str = ""
    lastfm_username: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
