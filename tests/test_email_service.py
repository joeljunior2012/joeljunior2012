"""Garante que o modo TEST nunca abra conexão SMTP."""

import logging
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from src.email_service import EmailService


class EmailServiceTests(unittest.TestCase):
    def test_test_mode_simulates_without_credentials(self) -> None:
        settings = SimpleNamespace(
            app_mode="TEST",
            alert_email_to="",
            max_emails_per_hour=10,
        )
        service = EmailService(settings, logging.getLogger("test"))
        with tempfile.TemporaryDirectory() as directory:
            service.history_path = Path(directory) / "history.jsonl"
            self.assertTrue(service.enviar_email("Assunto", "Corpo", "teste@example.com"))
            self.assertFalse(service.history_path.exists())


if __name__ == "__main__":
    unittest.main()
