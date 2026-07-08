from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql://automl:automl_dev_pw@localhost:5432/automl"
    data_service_url: str = "http://localhost:8001"
    service_port: int = 8002
    log_level: str = "INFO"
    http_timeout_seconds: float = 30.0

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


settings = Settings()
