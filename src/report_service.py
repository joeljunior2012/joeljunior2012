"""Serviço de relatório diário por e-mail (Fase 7)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from src.email_service import EmailService


class ReportService:
    def __init__(self, email_service: EmailService) -> None:
        self.email_service = email_service
        self.history_path = Path("data") / "signals_history.jsonl"

    def enviar_relatorio_diario(self) -> bool:
        """Gera resumo diário dos sinais e envia por e-mail."""
        hoje = datetime.now(timezone.utc).date().isoformat()
        sinais = self._sinais_do_dia(hoje)

        if not sinais:
            corpo = f"Relatório diário ({hoje}): nenhum sinal registrado hoje."
        else:
            total = len(sinais)
            operar = sum(1 for s in sinais if s.get("recomendacao") == "Operar agora")
            aguardar = sum(1 for s in sinais if s.get("recomendacao") == "Aguardar")
            score_medio = sum(int(s.get("score", 0)) for s in sinais) / total

            linhas = [
                f"Relatório diário ({hoje})",
                f"Total de sinais: {total}",
                f"Operar agora: {operar}",
                f"Aguardar: {aguardar}",
                f"Score médio: {score_medio:.2f}",
                "",
                "Últimos sinais:",
            ]
            for s in sinais[-10:]:
                linhas.append(
                    f"- {s.get('symbol')} | score={s.get('score')} | confianca={s.get('confianca')} | rec={s.get('recomendacao')}"
                )
            corpo = "\n".join(linhas)

        return self.email_service.enviar_email("[Relatório Diário] Sinais", corpo)

    def _sinais_do_dia(self, day_iso: str) -> list[dict]:
        if not self.history_path.exists():
            return []

        items: list[dict] = []
        with self.history_path.open("r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                    if str(row.get("created_at_utc", "")).startswith(day_iso):
                        items.append(row)
                except json.JSONDecodeError:
                    continue
        return items
