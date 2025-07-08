from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    POSTGRES_DB: str = "aironman"
    POSTGRES_USER: str = "aironman_user"
    POSTGRES_PASSWORD: str = "aironman_pass"
    POSTGRES_HOST: str = "db"
    POSTGRES_PORT: int = 5432
    GARMIN_EMAIL: str = ""
    GARMIN_PASSWORD: str = ""
    GARMINTOKENS: str = ""
    PAUSE_THRESHOLD: int = 5
    OPENAI_API_KEY: str = ""

    class Config:
        env_file = ".env"

settings = Settings()
