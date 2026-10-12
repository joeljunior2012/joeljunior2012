"""Serviço de indicadores e decisão simples (Fase 5).

Inclui:
- RSI
- Média Móvel Simples (SMA)
- Média Móvel Exponencial (EMA)
- Suporte
- Resistência
- Volatilidade
- Volume anormal

Também expõe:
- comprar_agora? -> Sim / Não / Aguardar confirmação

Nunca executa ordens.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class IndicatorResult:
    symbol: str
    price: float
    rsi: float
    sma: float
    ema: float
    suporte: float
    resistencia: float
    volatilidade_pct: float
    volume_atual: float
    volume_medio: float
    volume_anormal: bool
    decisao: str
    motivo: str


class SignalService:
    """Calcula indicadores e retorna decisão textual de compra (sem executar ordem)."""

    def calcular_indicadores(
        self,
        symbol: str,
        close_prices: list[float],
        volumes: list[float],
        rsi_period: int = 14,
        ma_period: int = 14,
    ) -> IndicatorResult:
        """Calcula conjunto de indicadores para um ativo."""
        if len(close_prices) < max(rsi_period + 1, ma_period):
            raise ValueError("Histórico insuficiente para cálculo dos indicadores.")
        if len(volumes) < ma_period:
            raise ValueError("Histórico de volume insuficiente para cálculo.")

        price = close_prices[-1]
        rsi = self._rsi(close_prices, rsi_period)
        sma = self._sma(close_prices, ma_period)
        ema = self._ema(close_prices, ma_period)

        # Suporte e resistência simples: mín/máx da janela recente
        janela_sr = close_prices[-ma_period:]
        suporte = min(janela_sr)
        resistencia = max(janela_sr)

        volatilidade_pct = self._volatilidade(close_prices, period=ma_period)

        volume_atual = volumes[-1]
        volume_medio = sum(volumes[-ma_period:]) / ma_period
        volume_anormal = volume_atual >= (volume_medio * 1.8)

        decisao, motivo = self.comprar_agora(
            price=price,
            rsi=rsi,
            sma=sma,
            ema=ema,
            suporte=suporte,
            resistencia=resistencia,
            volatilidade_pct=volatilidade_pct,
            volume_anormal=volume_anormal,
        )

        return IndicatorResult(
            symbol=symbol,
            price=price,
            rsi=rsi,
            sma=sma,
            ema=ema,
            suporte=suporte,
            resistencia=resistencia,
            volatilidade_pct=volatilidade_pct,
            volume_atual=volume_atual,
            volume_medio=volume_medio,
            volume_anormal=volume_anormal,
            decisao=decisao,
            motivo=motivo,
        )

    def comprar_agora(
        self,
        price: float,
        rsi: float,
        sma: float,
        ema: float,
        suporte: float,
        resistencia: float,
        volatilidade_pct: float,
        volume_anormal: bool,
    ) -> tuple[str, str]:
        """Retorna decisão: Sim / Não / Aguardar confirmação."""
        # Regras simples de proteção de capital
        if volatilidade_pct > 8.0:
            return "Não", "Volatilidade elevada (>8%), risco alto."

        perto_suporte = abs(price - suporte) / max(price, 1e-9) <= 0.015
        acima_medias = price > sma and price > ema
        abaixo_resistencia = price < resistencia * 0.99

        if 45 <= rsi <= 65 and acima_medias and perto_suporte and abaixo_resistencia and volume_anormal:
            return "Sim", "Tendência favorável, RSI equilibrado e volume anormal confirmando interesse."

        if rsi > 75 or price >= resistencia:
            return "Não", "Preço esticado (sobrecompra/resistência), maior chance de correção."

        return "Aguardar confirmação", "Sinais mistos; aguarde melhor alinhamento de tendência e volume."

    def _sma(self, prices: list[float], period: int) -> float:
        janela = prices[-period:]
        return sum(janela) / period

    def _ema(self, prices: list[float], period: int) -> float:
        """EMA com inicialização pela SMA da primeira janela."""
        k = 2 / (period + 1)
        ema_value = sum(prices[:period]) / period
        for p in prices[period:]:
            ema_value = p * k + ema_value * (1 - k)
        return ema_value

    def _rsi(self, prices: list[float], period: int) -> float:
        gains = []
        losses = []
        for i in range(-period, 0):
            delta = prices[i] - prices[i - 1]
            gains.append(max(delta, 0.0))
            losses.append(abs(min(delta, 0.0)))

        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    def _volatilidade(self, prices: list[float], period: int) -> float:
        """Volatilidade histórica simples em % via desvio padrão dos retornos."""
        window = prices[-period:]
        returns = []
        for i in range(1, len(window)):
            prev = window[i - 1]
            curr = window[i]
            if prev == 0:
                continue
            returns.append((curr - prev) / prev)

        if not returns:
            return 0.0

        mean_ret = sum(returns) / len(returns)
        variance = sum((r - mean_ret) ** 2 for r in returns) / len(returns)
        stdev = math.sqrt(variance)
        return stdev * 100
