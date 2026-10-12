"""Serviço de envio de e-mails (somente saída via Gmail SMTP).

Regras desta fase:
- Apenas envio de e-mail (não lê caixa de entrada).
- Respeita modo TEST para evitar envio real acidental.
- Usa credenciais vindas de variáveis de ambiente via Settings.
"""

from __future__ import annotations

import logging
import smtplib
import json
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.config import Settings


class EmailService:
    """Serviço responsável pelo envio de e-mail de alerta."""

    def __init__(self, settings: Settings, logger: logging.Logger) -> None:
        """Inicializa o serviço com configurações e logger compartilhado."""
        self.settings = settings
        self.logger = logger
        self.history_path = Path("data") / "email_send_history.jsonl"
        self.history_path.parent.mkdir(parents=True, exist_ok=True)

    def enviar_email(self, assunto: str, corpo: str, destinatario: str | None = None) -> bool:
        """Envia um e-mail de alerta.

        No modo TEST, não envia de verdade; apenas registra no log.

        Args:
            assunto: Assunto do e-mail.
            corpo: Conteúdo em texto simples.

        Returns:
            True quando operação foi bem-sucedida (ou simulada em TEST), False em erro.
        """
        destino = (destinatario or self.settings.alert_email_to).strip()

        # Em modo teste, fazemos somente simulação para evitar disparos acidentais.
        if self.settings.app_mode == "TEST":
            self.logger.info(
                "[TEST MODE] Simulação de envio de e-mail | para=%s | assunto=%s",
                destino or "não configurado",
                assunto,
            )
            self.logger.debug("[TEST MODE] Corpo do e-mail: %s", corpo)
            return True

        # Validação mínima de campos obrigatórios para envio real
        if not self.settings.smtp_user or not self.settings.smtp_app_password or not destino:
            self.logger.error(
                "Configuração SMTP incompleta. Verifique SMTP_USER, SMTP_APP_PASSWORD e ALERT_EMAIL_TO."
            )
            return False

        if self._limite_horario_atingido():
            self.logger.warning("Envio bloqueado pelo limite horário anti-spam.")
            return False

        message = EmailMessage()
        message["From"] = self.settings.smtp_user
        message["To"] = destino
        message["Subject"] = assunto
        message.set_content(corpo)

        try:
            self.logger.info("Iniciando envio de e-mail | host=%s | porta=%s", self.settings.smtp_host, self.settings.smtp_port)

            # Fluxo padrão do Gmail SMTP: conecta, inicia TLS, autentica e envia
            with smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port, timeout=30) as smtp:
                smtp.ehlo()
                smtp.starttls()
                smtp.ehlo()
                smtp.login(self.settings.smtp_user, self.settings.smtp_app_password)
                smtp.send_message(message)

            self._registrar_envio(destino, assunto)
            self.logger.info("E-mail enviado com sucesso | para=%s | assunto=%s", destino, assunto)
            return True

        except smtplib.SMTPAuthenticationError as exc:
            self.logger.exception("Falha de autenticação SMTP (Gmail app password). Detalhes: %s", exc)
            return False
        except smtplib.SMTPException as exc:
            self.logger.exception("Erro SMTP ao enviar e-mail. Detalhes: %s", exc)
            return False
        except Exception as exc:  # Captura defensiva para evitar quebra da aplicação
            self.logger.exception("Erro inesperado no envio de e-mail. Detalhes: %s", exc)
            return False

    def _limite_horario_atingido(self) -> bool:
        """Conta envios reais na última hora para evitar spam acidental."""
        if not self.history_path.exists():
            return False
        cutoff = datetime.now(timezone.utc) - timedelta(hours=1)
        total = 0
        with self.history_path.open("r", encoding="utf-8") as file:
            for line in file:
                try:
                    sent_at = datetime.fromisoformat(json.loads(line)["sent_at_utc"])
                except (json.JSONDecodeError, KeyError, ValueError):
                    continue
                if sent_at >= cutoff:
                    total += 1
        return total >= self.settings.max_emails_per_hour

    def _registrar_envio(self, destinatario: str, assunto: str) -> None:
        """Persiste metadados mínimos do envio, sem armazenar o corpo."""
        event = {
            "sent_at_utc": datetime.now(timezone.utc).isoformat(),
            "recipient": destinatario,
            "subject": assunto,
        }
        with self.history_path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(event, ensure_ascii=False) + "\n")
