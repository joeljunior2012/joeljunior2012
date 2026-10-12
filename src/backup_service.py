"""Backup e restauração dos históricos locais do sistema.

Os arquivos JSONL em ``data/`` funcionam como a base de dados atual. O backup
é um ZIP versionado, com manifesto e hashes SHA-256 para detectar corrupção.
Credenciais do arquivo ``.env`` nunca são incluídas.
"""

from __future__ import annotations

import hashlib
import json
import logging
import shutil
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path


class BackupError(RuntimeError):
    """Indica que um backup não é válido ou não pôde ser restaurado."""


class BackupService:
    """Cria, valida e restaura cópias dos arquivos persistentes."""

    MANIFEST_NAME = "manifest.json"

    def __init__(
        self,
        logger: logging.Logger,
        data_dir: str | Path = "data",
        backup_dir: str | Path = "backups",
        retention: int = 30,
    ) -> None:
        self.logger = logger
        self.data_dir = Path(data_dir).resolve()
        self.backup_dir = Path(backup_dir).resolve()
        self.retention = retention
        if retention < 1:
            raise ValueError("A retenção de backups deve ser maior que zero.")
        if self.backup_dir == self.data_dir or self.data_dir in self.backup_dir.parents:
            raise ValueError("BACKUP_DIR não pode ficar dentro de DATA_DIR.")

    def criar_backup(self) -> Path:
        """Cria um ZIP íntegro dos JSONL e remove cópias além da retenção."""
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        destination = self.backup_dir / f"alert-system-{timestamp}.zip"
        files = sorted(self.data_dir.glob("*.jsonl")) if self.data_dir.exists() else []
        manifest = {
            "format_version": 1,
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "files": {item.name: self._sha256(item) for item in files},
        }

        with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for item in files:
                archive.write(item, arcname=f"data/{item.name}")
            archive.writestr(self.MANIFEST_NAME, json.dumps(manifest, indent=2))

        self.validar_backup(destination)
        self._aplicar_retencao()
        self.logger.info("Backup criado | arquivo=%s | históricos=%s", destination, len(files))
        return destination

    def validar_backup(self, backup_path: str | Path) -> dict:
        """Valida estrutura e hashes e retorna o manifesto do ZIP."""
        path = Path(backup_path).resolve()
        if not path.is_file():
            raise BackupError(f"Backup não encontrado: {path}")
        try:
            with zipfile.ZipFile(path, "r") as archive:
                names = set(archive.namelist())
                if self.MANIFEST_NAME not in names:
                    raise BackupError("Backup sem manifesto.")
                manifest = json.loads(archive.read(self.MANIFEST_NAME))
                expected = manifest.get("files")
                if manifest.get("format_version") != 1 or not isinstance(expected, dict):
                    raise BackupError("Formato de backup não suportado.")
                for name, digest in expected.items():
                    member = f"data/{name}"
                    if Path(name).name != name or member not in names:
                        raise BackupError(f"Arquivo inválido ou ausente no backup: {name}")
                    actual = hashlib.sha256(archive.read(member)).hexdigest()
                    if actual != digest:
                        raise BackupError(f"Falha de integridade no arquivo: {name}")
                return manifest
        except (zipfile.BadZipFile, json.JSONDecodeError, KeyError, TypeError) as exc:
            raise BackupError(f"Backup inválido: {exc}") from exc

    def restaurar_backup(self, backup_path: str | Path, overwrite: bool = False) -> int:
        """Restaura um backup validado, preservando dados existentes por padrão."""
        path = Path(backup_path).resolve()
        manifest = self.validar_backup(path)
        names = list(manifest["files"])
        conflicts = [name for name in names if (self.data_dir / name).exists()]
        if conflicts and not overwrite:
            raise BackupError(
                "Restauração cancelada para não sobrescrever: " + ", ".join(conflicts)
            )

        self.data_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory() as temporary:
            temp_dir = Path(temporary)
            with zipfile.ZipFile(path, "r") as archive:
                for name in names:
                    extracted = temp_dir / name
                    extracted.write_bytes(archive.read(f"data/{name}"))
            for name in names:
                shutil.copy2(temp_dir / name, self.data_dir / name)

        self.logger.info("Backup restaurado | arquivo=%s | históricos=%s", path, len(names))
        return len(names)

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as file:
            for chunk in iter(lambda: file.read(64 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def _aplicar_retencao(self) -> None:
        backups = sorted(self.backup_dir.glob("alert-system-*.zip"), reverse=True)
        for old_backup in backups[self.retention :]:
            old_backup.unlink()
            self.logger.info("Backup antigo removido pela retenção | arquivo=%s", old_backup)
