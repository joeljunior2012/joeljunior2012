"""Serviço de leitura e processamento de e-mails via IMAP (Gmail).

Fase 3:
- Lê e-mails recebidos por IMAP.
- Filtra por palavras-chave.
- Classifica prioridade.
- Evita resposta duplicada por Message-ID.
- Em TEST, mostra resposta no log sem enviar.
- Gera log de e-mails processados (JSONL).
"""

from __future__ import annotations

import imaplib
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from email import message_from_bytes
from email.message import Message
from email.utils import parseaddr
from pathlib import Path
from typing import Iterable

from src.config import Settings
from src.email_service import EmailService


@dataclass
class ProcessedEmail:
    """Representa um e-mail já normalizado para processamento."""

    message_id: str
    from_email: str
    subject: str
    body: str


class InboxService:
    """Serviço de leitura IMAP + classificação de prioridade."""

    def __init__(self, settings: Settings, logger: logging.Logger, email_service: EmailService) -> None:
        self.settings = settings
        self.logger = logger
        self.email_service = email_service

        # Palavras-chave iniciais para filtro e prioridade (podem evoluir depois)
        self.keywords = ["alerta", "urgente", "erro", "falha", "suporte", "dúvida"]

        # Arquivo local para evitar resposta duplicada e auditar o processamento
        self.processed_log_path = Path("data") / "processed_emails.jsonl"
        self.processed_log_path.parent.mkdir(parents=True, exist_ok=True)

    def processar_caixa_entrada(self, max_emails: int = 20) -> int:
        """Lê os e-mails mais recentes e processa cada item.

        Returns:
            Quantidade de e-mails processados nesta execução.
        """
        emails = self._ler_emails_imap(max_emails=max_emails)
        processed_count = 0

        for item in emails:
            if self._ja_processado(item.message_id):
                self.logger.info("E-mail duplicado ignorado | message_id=%s", item.message_id)
                continue

            if not self._tem_palavra_chave(item.subject, item.body):
                self.logger.info("E-mail sem palavra-chave ignorado | subject=%s", item.subject)
                self._registrar_processamento(item, prioridade="IGNORADO", resposta_preview="Sem ação")
                continue

            prioridade = self._classificar_prioridade(item.subject, item.body)
            resposta = self._montar_resposta(item, prioridade)

            if self.settings.app_mode == "TEST":
                self.logger.info(
                    "[TEST MODE] Resposta simulada | para=%s | prioridade=%s | subject=%s",
                    item.from_email,
                    prioridade,
                    item.subject,
                )
                self.logger.info("[TEST MODE] Conteúdo da resposta: %s", resposta)
                sucesso_envio = True
            else:
                sucesso_envio = self.email_service.enviar_email(
                    assunto=f"Re: {item.subject}",
                    corpo=resposta,
                )

            status = "RESPONDIDO" if sucesso_envio else "ERRO_RESPOSTA"
            self._registrar_processamento(item, prioridade=prioridade, resposta_preview=resposta, status=status)
            processed_count += 1

        self.logger.info("Processamento IMAP finalizado | processados=%s", processed_count)
        return processed_count

    def _ler_emails_imap(self, max_emails: int) -> list[ProcessedEmail]:
        """Lê e normaliza e-mails da caixa de entrada via IMAP."""
        if not self.settings.smtp_user or not self.settings.smtp_app_password:
            self.logger.error("Credenciais ausentes para IMAP. Defina SMTP_USER e SMTP_APP_PASSWORD no .env")
            return []

        imap_host = "imap.gmail.com"
        emails: list[ProcessedEmail] = []

        try:
            with imaplib.IMAP4_SSL(imap_host) as imap:
                imap.login(self.settings.smtp_user, self.settings.smtp_app_password)
                imap.select("INBOX")

                status, data = imap.search(None, "ALL")
                if status != "OK":
                    self.logger.error("Falha ao listar e-mails da INBOX via IMAP.")
                    return []

                all_ids = data[0].split()
                selected_ids = all_ids[-max_emails:]

                for msg_id in selected_ids:
                    fetch_status, msg_data = imap.fetch(msg_id, "(RFC822)")
                    if fetch_status != "OK" or not msg_data or not msg_data[0]:
                        self.logger.warning("Falha ao buscar e-mail id=%s", msg_id)
                        continue

                    raw = msg_data[0][1]
                    mime_message = message_from_bytes(raw)
                    normalized = self._normalizar_email(mime_message)
                    emails.append(normalized)

        except imaplib.IMAP4.error as exc:
            self.logger.exception("Erro IMAP ao ler caixa de entrada. Detalhes: %s", exc)
            return []
        except Exception as exc:
            self.logger.exception("Erro inesperado na leitura IMAP. Detalhes: %s", exc)
            return []

        self.logger.info("Leitura IMAP concluída | encontrados=%s", len(emails))
        return emails

    def _normalizar_email(self, mime_message: Message) -> ProcessedEmail:
        """Extrai campos principais do e-mail MIME."""
        message_id = (mime_message.get("Message-ID") or "").strip()
        if not message_id:
            message_id = f"sem-id-{datetime.now(timezone.utc).timestamp()}"

        from_header = mime_message.get("From", "")
        from_email = parseaddr(from_header)[1]
        subject = (mime_message.get("Subject") or "").strip()

        body = self._extrair_texto(mime_message)

        return ProcessedEmail(
            message_id=message_id,
            from_email=from_email,
            subject=subject,
            body=body,
        )

    def _extrair_texto(self, mime_message: Message) -> str:
        """Extrai corpo em texto simples, inclusive em e-mails multipart."""
        if mime_message.is_multipart():
            parts_text: list[str] = []
            for part in mime_message.walk():
                content_type = part.get_content_type()
                disposition = str(part.get("Content-Disposition", "")).lower()
                if content_type == "text/plain" and "attachment" not in disposition:
                    payload = part.get_payload(decode=True) or b""
                    charset = part.get_content_charset() or "utf-8"
                    parts_text.append(payload.decode(charset, errors="replace"))
            return "\n".join(parts_text).strip()

        payload = mime_message.get_payload(decode=True) or b""
        charset = mime_message.get_content_charset() or "utf-8"
        return payload.decode(charset, errors="replace").strip()

    def _tem_palavra_chave(self, subject: str, body: str) -> bool:
        """Verifica se subject/body contém pelo menos uma palavra-chave."""
        text = f"{subject} {body}".lower()
        return any(word in text for word in self.keywords)

    def _classificar_prioridade(self, subject: str, body: str) -> str:
        """Classificação simples de prioridade por palavras-chave."""
        text = f"{subject} {body}".lower()

        alta = ["urgente", "falha crítica", "indisponível", "erro grave"]
        media = ["erro", "falha", "suporte", "alerta"]

        if any(word in text for word in alta):
            return "ALTA"
        if any(word in text for word in media):
            return "MEDIA"
        return "BAIXA"

    def _montar_resposta(self, item: ProcessedEmail, prioridade: str) -> str:
        """Monta resposta padrão para o e-mail processado."""
        return (
            f"Olá, recebemos sua mensagem com prioridade {prioridade}.\n"
            "Esta é uma resposta automática de confirmação de recebimento.\n"
            "Em breve retornaremos com mais detalhes."
        )

    def _ja_processado(self, message_id: str) -> bool:
        """Verifica no JSONL se o Message-ID já foi processado."""
        if not self.processed_log_path.exists():
            return False

        with self.processed_log_path.open("r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                    if row.get("message_id") == message_id:
                        return True
                except json.JSONDecodeError:
                    continue

        return False

    def _registrar_processamento(
        self,
        item: ProcessedEmail,
        prioridade: str,
        resposta_preview: str,
        status: str = "PROCESSADO",
    ) -> None:
        """Registra e-mail processado no JSONL para auditoria e deduplicação."""
        event = {
            "processed_at_utc": datetime.now(timezone.utc).isoformat(),
            "status": status,
            "message_id": item.message_id,
            "from_email": item.from_email,
            "subject": item.subject,
            "prioridade": prioridade,
            "resposta_preview": resposta_preview[:300],
        }

        with self.processed_log_path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(event, ensure_ascii=False) + "\n")

        self.logger.info(
            "E-mail registrado no histórico | message_id=%s | prioridade=%s | status=%s",
            item.message_id,
            prioridade,
            status,
        )
