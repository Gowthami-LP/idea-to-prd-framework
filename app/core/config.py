from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central application configuration.
    Values are loaded from environment variables
    and the .env file.
    """

    APP_NAME: str = "Idea-to-PRD-to-Outcome Framework"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DATABASE: str = "framework"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


# Create a shared settings object.
settings = Settings()
