"""Testes offline de backup, integridade e restauração."""

import logging
import tempfile
import unittest
import zipfile
from pathlib import Path

from src.backup_service import BackupError, BackupService


class BackupServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        self.data_dir = root / "data"
        self.backup_dir = root / "backup"
        self.data_dir.mkdir()
        self.service = BackupService(logging.getLogger("backup-test"), self.data_dir, self.backup_dir)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_cria_e_restaura_historico(self) -> None:
        original = '{"symbol": "BTC"}\n'
        (self.data_dir / "signals_history.jsonl").write_text(original, encoding="utf-8")
        backup = self.service.criar_backup()
        (self.data_dir / "signals_history.jsonl").unlink()

        restored = self.service.restaurar_backup(backup)

        self.assertEqual(restored, 1)
        self.assertEqual((self.data_dir / "signals_history.jsonl").read_text(encoding="utf-8"), original)

    def test_nao_sobrescreve_sem_confirmacao(self) -> None:
        history = self.data_dir / "signals_history.jsonl"
        history.write_text("antigo", encoding="utf-8")
        backup = self.service.criar_backup()
        history.write_text("novo", encoding="utf-8")

        with self.assertRaises(BackupError):
            self.service.restaurar_backup(backup)
        self.assertEqual(history.read_text(encoding="utf-8"), "novo")

    def test_detecta_backup_corrompido(self) -> None:
        history = self.data_dir / "signals_history.jsonl"
        history.write_text("original", encoding="utf-8")
        backup = self.service.criar_backup()
        corrupt = self.backup_dir / "corrompido.zip"
        with zipfile.ZipFile(backup, "r") as source, zipfile.ZipFile(corrupt, "w") as target:
            target.writestr("manifest.json", source.read("manifest.json"))
            target.writestr("data/signals_history.jsonl", "alterado")

        with self.assertRaises(BackupError):
            self.service.validar_backup(corrupt)


if __name__ == "__main__":
    unittest.main()
