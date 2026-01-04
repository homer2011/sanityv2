from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# docs: https://docs.pydantic.dev/latest/concepts/pydantic_settings/#dotenv-env-support


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    DB_URL: str = Field(alias="DB_URL", default="")


settings = Settings()
