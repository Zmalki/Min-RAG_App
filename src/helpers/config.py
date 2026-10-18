from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str
    APP_VERSION: str
    OPENAI_API_KEY: str

    FILE_ALLOWED_TYPES: list
    FILE_MAX_SIZE: int
    FILE_DEFAULT_CHUNK_SIZE: int

    model_config = SettingsConfigDict(
        env_file="/home/schule/Min-RAG_App/src/.env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


def get_settings():
    return Settings()
