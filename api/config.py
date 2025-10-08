from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    api_key: str
    api_port: int = 8000
    db_host: str
    db_port: int = 5432
    db_name: str
    db_username: str
    db_password: str

    class Config:
        env_file = [
            Path(__file__).resolve().parents[1] / ".env",
            Path(__file__).resolve().parents[1] / ".env.local",
        ]


settings = Settings()
