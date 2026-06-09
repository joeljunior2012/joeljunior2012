"""Serviço de envio de e-mails (somente saída via Gmail SMTP).

Regras desta fase:
- Apenas envio de e-mail (não lê caixa de entrada).
- Respeita modo TEST para evitar envio real acidental.
- Usa credenciais vindas de variáveis de ambiente via Settings.
"""

from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

from src.config import Settings


class EmailService:
    """Serviço responsável pelo envio de e-mail de alerta."""

    def __init__(self, settings: Settings, logger: logging.Logger) -> None:
        """Inicializa o serviço com configurações e logger compartilhado."""
        self.settings = settings
        self.logger = logger

    def enviar_email(self, assunto: str, corpo: str) -> bool:
        """Envia um e-mail de alerta.

        No modo TEST, não envia de verdade; apenas registra no log.

        Args:
            assunto: Assunto do e-mail.
            corpo: Conteúdo em texto simples.

        Returns:
            True quando operação foi bem-sucedida (ou simulada em TEST), False em erro.
        """
        # Em modo teste, fazemos somente simulação para evitar disparos acidentais.
        if self.settings.app_mode == "TEST":
            self.logger.info(
                "[TEST MODE] Simulação de envio de e-mail | para=%s | assunto=%s",
                self.settings.alert_email_to,
                assunto,
            )
            self.logger.debug("[TEST MODE] Corpo do e-mail: %s", corpo)
            return True

        # Validação mínima de campos obrigatórios para envio real
        if not self.settings.smtp_user or not self.settings.smtp_app_password or not self.settings.alert_email_to:
            self.logger.error(
                "Configuração SMTP incompleta. Verifique SMTP_USER, SMTP_APP_PASSWORD e ALERT_EMAIL_TO."
            )
            return False

        message = EmailMessage()
        message["From"] = self.settings.smtp_user
        message["To"] = self.settings.alert_email_to
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

            self.logger.info("E-mail enviado com sucesso | para=%s | assunto=%s", self.settings.alert_email_to, assunto)
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
