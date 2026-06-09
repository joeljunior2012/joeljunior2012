"""Configurações centrais da aplicação.

Este módulo é responsável por:
1) Ler variáveis de ambiente do arquivo .env
2) Validar tipos e valores
3) Expor configurações de forma segura para os demais módulos
"""

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Classe de configuração tipada da aplicação.

    Todos os campos podem ser sobrescritos por variáveis de ambiente.
    """

    # Configuração interna do Pydantic Settings:
    # - lê variáveis do .env
    # - ignora variáveis extras para facilitar evolução incremental
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Modo de execução (por padrão, seguro para iniciantes)
    app_mode: str = Field(default="TEST", alias="APP_MODE")

    # Identificação da aplicação
    app_name: str = Field(default="alert-system", alias="APP_NAME")
    timezone: str = Field(default="UTC", alias="TIMEZONE")

    # Configurações de log
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_dir: str = Field(default="logs", alias="LOG_DIR")
    log_file: str = Field(default="app.log", alias="LOG_FILE")

    # Configurações de e-mail (Gmail)
    smtp_host: str = Field(default="smtp.gmail.com", alias="SMTP_HOST")
    smtp_port: int = Field(default=587, alias="SMTP_PORT")
    smtp_user: str = Field(default="", alias="SMTP_USER")
    smtp_app_password: str = Field(default="", alias="SMTP_APP_PASSWORD")
    alert_email_to: str = Field(default="", alias="ALERT_EMAIL_TO")

    @field_validator("app_mode")
    @classmethod
    def validate_app_mode(cls, value: str) -> str:
        """Garante que o modo esteja entre os valores permitidos."""
        normalized = value.strip().upper()
        if normalized not in {"TEST", "REAL"}:
            raise ValueError("APP_MODE deve ser TEST ou REAL.")
        return normalized


def get_settings() -> Settings:
    """Retorna uma instância validada de Settings."""
    return Settings()
