"""Serviço de análise de timing operacional (Fase 6).

Inclui:
- Análise por horário de Brasília.
- Janela de abertura/fechamento dos EUA.
- Heurísticas de liquidez e volatilidade.
- Bloqueio de horários ruins e horários de notícia.
- Recomendação final: operar agora ou aguardar.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time
from zoneinfo import ZoneInfo


@dataclass
class TimingRecommendation:
    operar_agora: bool
    recomendacao: str
    motivo: str
    brasilia_time: str
    janela_eua: str


class TimingService:
    """Regras simples de janela operacional e contexto de risco."""

    BRAZIL_TZ = ZoneInfo("America/Sao_Paulo")

    def analisar_momento(
        self,
        liquidez_score: float,
        volatilidade_pct: float,
        now_utc: datetime | None = None,
    ) -> TimingRecommendation:
        """Retorna recomendação de operar agora ou aguardar."""
        now_utc = now_utc or datetime.utcnow().replace(tzinfo=ZoneInfo("UTC"))
        br_now = now_utc.astimezone(self.BRAZIL_TZ)
        current = br_now.time()

        janela_eua = self._janela_mercado_eua(current)

        # Horários ruins (baixa liquidez geral em cripto para esta estratégia)
        if self._is_horario_ruim(current):
            return TimingRecommendation(
                operar_agora=False,
                recomendacao="Aguardar",
                motivo="Horário ruim (baixa eficiência histórica para operação assistida).",
                brasilia_time=br_now.strftime("%Y-%m-%d %H:%M:%S %Z"),
                janela_eua=janela_eua,
            )

        # Janela de notícias macro (heurística fixa da fase 6)
        if self._is_horario_noticia(current):
            return TimingRecommendation(
                operar_agora=False,
                recomendacao="Aguardar",
                motivo="Janela de notícia macro dos EUA; risco de movimento errático.",
                brasilia_time=br_now.strftime("%Y-%m-%d %H:%M:%S %Z"),
                janela_eua=janela_eua,
            )

        if liquidez_score < 0.4:
            return TimingRecommendation(
                operar_agora=False,
                recomendacao="Aguardar",
                motivo="Liquidez baixa para entrada segura.",
                brasilia_time=br_now.strftime("%Y-%m-%d %H:%M:%S %Z"),
                janela_eua=janela_eua,
            )

        if volatilidade_pct > 8.0:
            return TimingRecommendation(
                operar_agora=False,
                recomendacao="Aguardar",
                motivo="Volatilidade alta; preservar capital.",
                brasilia_time=br_now.strftime("%Y-%m-%d %H:%M:%S %Z"),
                janela_eua=janela_eua,
            )

        # Momento favorável simplificado
        if janela_eua in {"ABERTURA_EUA", "MEIO_SESSAO_EUA"} and 0.4 <= liquidez_score <= 1.0:
            return TimingRecommendation(
                operar_agora=True,
                recomendacao="Operar agora",
                motivo="Janela favorável com liquidez adequada e volatilidade controlada.",
                brasilia_time=br_now.strftime("%Y-%m-%d %H:%M:%S %Z"),
                janela_eua=janela_eua,
            )

        return TimingRecommendation(
            operar_agora=False,
            recomendacao="Aguardar",
            motivo="Condições neutras; aguarde melhor alinhamento de janela e fluxo.",
            brasilia_time=br_now.strftime("%Y-%m-%d %H:%M:%S %Z"),
            janela_eua=janela_eua,
        )

    def _janela_mercado_eua(self, current: time) -> str:
        """Classifica janela relativa ao pregão dos EUA em horário de Brasília.

        Referência típica (aprox):
        - Abertura EUA: 10:30 BRT (ou 09:30 em parte do ano)
        - Fechamento EUA: 17:00 BRT (ou 16:00 em parte do ano)
        """
        # Janelas amplas para robustez sem calendário DST detalhado nesta fase
        if time(9, 30) <= current <= time(11, 30):
            return "ABERTURA_EUA"
        if time(11, 31) <= current <= time(15, 59):
            return "MEIO_SESSAO_EUA"
        if time(16, 0) <= current <= time(17, 30):
            return "FECHAMENTO_EUA"
        return "FORA_JANELA_EUA"

    def _is_horario_ruim(self, current: time) -> bool:
        """Define horários geralmente ruins para esta abordagem.

        Exemplo: madrugada profunda BRT (baixa liquidez relativa).
        """
        return time(2, 0) <= current <= time(6, 0)

    def _is_horario_noticia(self, current: time) -> bool:
        """Bloqueia janela curta de possível impacto de notícias macro.

        Heurística inicial: 09:20-10:10 BRT (transição pré-abertura EUA).
        """
        return time(9, 20) <= current <= time(10, 10)
