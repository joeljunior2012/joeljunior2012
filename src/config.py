"""Configuração da aplicação sem dependências externas.

O carregador lê ``.env`` e depois aplica variáveis do Windows/Linux. Variáveis
do sistema têm precedência, como é esperado em ambientes de produção.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _read_dotenv(path: Path = Path(".env")) -> dict[str, str]:
    """Lê pares CHAVE=VALOR básicos sem executar conteúdo do arquivo."""
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ValueError(f"Linha inválida no .env: {number}")
        key, value = line.split("=", 1)
        key = key.strip()
        if not key or not key.replace("_", "").isalnum():
            raise ValueError(f"Nome de variável inválido no .env: linha {number}")
        values[key] = value.strip().strip('"').strip("'")
    return values


def _boolean(value: str, name: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "sim", "yes", "on"}:
        return True
    if normalized in {"0", "false", "nao", "não", "no", "off"}:
        return False
    raise ValueError(f"{name} deve ser true ou false.")


@dataclass(frozen=True)
class Settings:
    app_mode: str = "TEST"
    app_name: str = "alert-system"
    timezone: str = "UTC"
    log_level: str = "INFO"
    log_dir: str = "logs"
    log_file: str = "app.log"
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_app_password: str = ""
    alert_email_to: str = ""
    imap_host: str = "imap.gmail.com"
    run_inbox: bool = False
    run_market: bool = True
    send_daily_report: bool = False
    max_emails_per_hour: int = 10
    analysis_interval_minutes: int = 15
    max_signals_per_day: int = 5
    backup_enabled: bool = False
    backup_dir: str = "backups"
    backup_retention: int = 30


def get_settings() -> Settings:
    """Carrega e valida configurações do ``.env`` e do ambiente."""
    file_values = _read_dotenv()

    def value(name: str, default: str) -> str:
        return os.environ.get(name, file_values.get(name, default))

    mode = value("APP_MODE", "TEST").strip().upper()
    if mode not in {"TEST", "REAL"}:
        raise ValueError("APP_MODE deve ser TEST ou REAL.")
    interval = int(value("ANALYSIS_INTERVAL_MINUTES", "15"))
    if interval not in {5, 15, 30, 60}:
        raise ValueError("ANALYSIS_INTERVAL_MINUTES deve ser 5, 15, 30 ou 60.")
    positive = {
        "smtp_port": int(value("SMTP_PORT", "587")),
        "max_emails_per_hour": int(value("MAX_EMAILS_PER_HOUR", "10")),
        "max_signals_per_day": int(value("MAX_SIGNALS_PER_DAY", "5")),
        "backup_retention": int(value("BACKUP_RETENTION", "30")),
    }
    if any(item < 1 for item in positive.values()):
        raise ValueError("Portas, limites e retenção devem ser maiores que zero.")

    return Settings(
        app_mode=mode,
        app_name=value("APP_NAME", "alert-system"),
        timezone=value("TIMEZONE", "UTC"),
        log_level=value("LOG_LEVEL", "INFO").upper(),
        log_dir=value("LOG_DIR", "logs"),
        log_file=value("LOG_FILE", "app.log"),
        smtp_host=value("SMTP_HOST", "smtp.gmail.com"),
        smtp_port=positive["smtp_port"],
        smtp_user=value("SMTP_USER", ""),
        smtp_app_password=value("SMTP_APP_PASSWORD", ""),
        alert_email_to=value("ALERT_EMAIL_TO", ""),
        imap_host=value("IMAP_HOST", "imap.gmail.com"),
        run_inbox=_boolean(value("RUN_INBOX", "false"), "RUN_INBOX"),
        run_market=_boolean(value("RUN_MARKET", "true"), "RUN_MARKET"),
        send_daily_report=_boolean(value("SEND_DAILY_REPORT", "false"), "SEND_DAILY_REPORT"),
        max_emails_per_hour=positive["max_emails_per_hour"],
        analysis_interval_minutes=interval,
        max_signals_per_day=positive["max_signals_per_day"],
        backup_enabled=_boolean(value("BACKUP_ENABLED", "false"), "BACKUP_ENABLED"),
        backup_dir=value("BACKUP_DIR", "backups"),
        backup_retention=positive["backup_retention"],
    )
