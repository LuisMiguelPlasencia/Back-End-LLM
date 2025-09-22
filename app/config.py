# settings_db.py
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field
from sqlalchemy import create_engine, text
from sqlalchemy.engine.url import URL
from sqlalchemy.engine import Engine


class Settings(BaseSettings):
    # Opcional: usar una URL completa (overrides campos individuales si está presente)
    database_url: Optional[str] = Field(default=None, env="DATABASE_URL")

    # Campos individuales (se usan si database_url es None)
    db_driver: str = Field(default="postgresql+psycopg2", env="DB_DRIVER")
    db_user: str = Field(default="user", env="DB_USER")
    db_password: str = Field(default="password", env="DB_PASSWORD")
    db_host: str = Field(default="localhost", env="DB_HOST")
    db_port: str = Field(default="5432", env="DB_PORT")
    db_name: str = Field(default="conversa", env="DB_NAME")

    # Otros settings
    openai_api_key: str = Field(default="", env="OPENAI_API_KEY")
    debug: bool = Field(default=True, env="DEBUG")
    environment: str = Field(default="development", env="ENVIRONMENT")

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"

    # Propiedad que devuelve un objeto URL de SQLAlchemy (ó string si prefieres)
    @property
    def sqlalchemy_url(self) -> URL | str:
        if self.database_url:
            # Si el usuario proporciona DATABASE_URL completo, úsalo directamente
            return self.database_url
        # Construye la URL a partir de campos individuales
        return URL.create(
            drivername=self.db_driver,
            username=self.db_user,
            password=self.db_password,
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
        )

    def create_engine(self, **create_engine_kwargs) -> Engine:
        # valores por defecto útiles
        defaults = {"echo": False, "future": True, "pool_pre_ping": True}
        # merge de kwargs
        params = {**defaults, **create_engine_kwargs}
        return create_engine(self.sqlalchemy_url, **params)
    
settings = Settings()

