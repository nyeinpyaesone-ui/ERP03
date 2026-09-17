from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "ERP03 API"
    environment: str = "production"
    ollama_base_url: str = "http://ollama:11434"
    ollama_model: str = "qwen2.5:1.5b"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
