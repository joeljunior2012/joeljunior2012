"""Configuração básica de logging da aplicação.

Este logger escreve no console e em arquivo.
"""

from __future__ import annotations

import logging
from pathlib import Path


def setup_logger(log_dir: str, log_file: str, log_level: str = "INFO") -> logging.Logger:
    """Configura logger raiz com saída em arquivo e console.

    Args:
        log_dir: Diretório onde os logs serão gravados.
        log_file: Nome do arquivo de log.
        log_level: Nível de log (ex.: DEBUG, INFO, WARNING, ERROR).

    Returns:
        Logger configurado.
    """
    # Garante que o diretório de logs exista
    Path(log_dir).mkdir(parents=True, exist_ok=True)

    # Converte texto do nível para constante do módulo logging
    level = getattr(logging, log_level.upper(), logging.INFO)

    # Formato padrão para facilitar auditoria
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    logger = logging.getLogger()
    logger.setLevel(level)

    # Evita duplicidade de handlers quando executar várias vezes em debug
    logger.handlers.clear()

    file_handler = logging.FileHandler(Path(log_dir) / log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    return logger
