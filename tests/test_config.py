"""Testes do carregador de configuração sem dependências externas."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.config import _read_dotenv, get_settings


class ConfigTests(unittest.TestCase):
    def test_environment_overrides_defaults(self) -> None:
        with patch.dict(os.environ, {"APP_MODE": "real", "RUN_MARKET": "false"}, clear=True):
            with tempfile.TemporaryDirectory() as directory:
                previous = os.getcwd()
                try:
                    os.chdir(directory)
                    settings = get_settings()
                finally:
                    os.chdir(previous)
        self.assertEqual(settings.app_mode, "REAL")
        self.assertFalse(settings.run_market)

    def test_rejects_invalid_dotenv_line(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".env"
            path.write_text("LINHA SEM IGUAL\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                _read_dotenv(path)

    def test_rejects_unsafe_interval(self) -> None:
        with patch.dict(os.environ, {"ANALYSIS_INTERVAL_MINUTES": "1"}, clear=True):
            with self.assertRaises(ValueError):
                get_settings()


if __name__ == "__main__":
    unittest.main()
