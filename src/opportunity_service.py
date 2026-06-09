"""Serviço de pontuação final de oportunidade (Fase 7).

Inclui:
- Score final de 0 a 100.
- Filtro anti-FOMO.
- Proteção contra overtrading.
- Confiança do sinal.
- Histórico de sinais enviados (JSONL).
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from src.signal_service import IndicatorResult
from src.timing_service import TimingRecommendation


@dataclass
class OpportunitySignal:
    symbol: str
    score: int
    confianca: str
    recomendacao: str
    motivo: str
    anti_fomo_bloqueado: bool
    overtrading_bloqueado: bool
    created_at_utc: str


class OpportunityService:
    """Calcula score final e controla envio de sinais."""

    def __init__(self, max_signals_per_day: int = 5) -> None:
        self.max_signals_per_day = max_signals_per_day
        self.history_path = Path("data") / "signals_history.jsonl"
        self.history_path.parent.mkdir(parents=True, exist_ok=True)

    def gerar_sinal(self, indicator: IndicatorResult, timing: TimingRecommendation) -> OpportunitySignal:
        """Gera sinal com score 0-100 e filtros de proteção."""
        anti_fomo_bloqueado = self._anti_fomo(indicator)
        overtrading_bloqueado = self._overtrading_ativo()

        score = self._score_base(indicator, timing)
        if anti_fomo_bloqueado:
            score = max(score - 30, 0)
        if overtrading_bloqueado:
            score = max(score - 40, 0)

        confianca = self._confianca(score)

        if anti_fomo_bloqueado:
            recomendacao = "Aguardar"
            motivo = "Filtro anti-FOMO ativado: preço esticado perto de resistência."
        elif overtrading_bloqueado:
            recomendacao = "Aguardar"
            motivo = "Proteção contra overtrading ativada: limite diário de sinais excedido."
        elif timing.recomendacao == "Operar agora" and indicator.decisao == "Sim" and score >= 70:
            recomendacao = "Operar agora"
            motivo = "Conjunto técnico e timing favoráveis com score alto."
        else:
            recomendacao = "Aguardar"
            motivo = "Condição parcial; aguardar confirmação adicional."

        signal = OpportunitySignal(
            symbol=indicator.symbol,
            score=int(score),
            confianca=confianca,
            recomendacao=recomendacao,
            motivo=motivo,
            anti_fomo_bloqueado=anti_fomo_bloqueado,
            overtrading_bloqueado=overtrading_bloqueado,
            created_at_utc=datetime.now(timezone.utc).isoformat(),
        )

        self._registrar_signal(signal)
        return signal

    def _score_base(self, indicator: IndicatorResult, timing: TimingRecommendation) -> int:
        """Monta score simples (0-100) por componentes."""
        score = 50

        # RSI saudável
        if 45 <= indicator.rsi <= 65:
            score += 10
        elif indicator.rsi > 75:
            score -= 15

        # Tendência
        if indicator.price > indicator.sma and indicator.price > indicator.ema:
            score += 12
        else:
            score -= 8

        # Volatilidade controlada
        if indicator.volatilidade_pct <= 4:
            score += 10
        elif indicator.volatilidade_pct > 8:
            score -= 12

        # Volume anormal como confirmação
        if indicator.volume_anormal:
            score += 10

        # Timing
        if timing.recomendacao == "Operar agora":
            score += 10
        else:
            score -= 5

        return max(min(score, 100), 0)

    def _anti_fomo(self, indicator: IndicatorResult) -> bool:
        """Bloqueia quando preço estiver esticado."""
        perto_resistencia = indicator.price >= indicator.resistencia * 0.995
        rsi_esticado = indicator.rsi >= 72
        return perto_resistencia or rsi_esticado

    def _overtrading_ativo(self) -> bool:
        """Ativa bloqueio quando limite diário de sinais já foi atingido."""
        if not self.history_path.exists():
            return False

        hoje = datetime.now(timezone.utc).date().isoformat()
        count = 0
        with self.history_path.open("r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                    created = str(row.get("created_at_utc", ""))
                    if created.startswith(hoje):
                        count += 1
                except json.JSONDecodeError:
                    continue

        return count >= self.max_signals_per_day

    def _confianca(self, score: int) -> str:
        if score >= 80:
            return "Alta"
        if score >= 60:
            return "Média"
        return "Baixa"

    def _registrar_signal(self, signal: OpportunitySignal) -> None:
        with self.history_path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(asdict(signal), ensure_ascii=False) + "\n")
