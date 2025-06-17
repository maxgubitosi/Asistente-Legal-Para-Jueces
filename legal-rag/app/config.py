from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache

class Settings(BaseSettings):
    azure_api_key: str  = Field(..., env="AZURE_KEY")
    azure_endpoint: str = Field(..., env="AZURE_ENDPOINT")
    azure_deployment: str = Field(...,
                                  env="AZURE_DEPLOYMENT")
    azure_api_version: str = "2024-02-15-preview"

    model_config = {"extra": "ignore"}   # ignora cualquier otra env var

@lru_cache
def get_settings():
    return Settings()
