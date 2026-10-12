"""Serviço de monitoramento de mercado (Fase 4).

Escopo desta fase:
- Buscar BTC, ETH, SOL, BNB e XRP.
- Trazer preço em USD e BRL.
- Trazer variação de 24h e volume.
- Disparar alerta simples por e-mail.
- Sem indicadores avançados.
"""

from __future__ import annotations

import logging
import json
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from src.email_service import EmailService


@dataclass
class AssetSnapshot:
    """Representa um snapshot de mercado por ativo."""

    symbol: str
    price_usd: float
    price_brl: float
    change_24h_pct: float
    volume_24h: float


class MarketService:
    """Busca dados de mercado e aciona alerta simples por e-mail."""

    COINGECKO_URL = "https://api.coingecko.com/api/v3/simple/price"
    ASSETS = {
        "bitcoin": "BTC",
        "ethereum": "ETH",
        "solana": "SOL",
        "binancecoin": "BNB",
        "ripple": "XRP",
    }

    def __init__(self, logger: logging.Logger, email_service: EmailService) -> None:
        self.logger = logger
        self.email_service = email_service

    def _get_json(self, url: str, params: dict[str, object]) -> dict:
        """Consulta JSON com User-Agent explícito e timeout, sem biblioteca externa."""
        request = Request(
            f"{url}?{urlencode(params)}",
            headers={"Accept": "application/json", "User-Agent": "alert-system/1.0"},
        )
        with urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))

    def buscar_mercado(self) -> list[AssetSnapshot]:
        """Busca preços/variação/volume dos ativos definidos."""
        params = {
            "ids": ",".join(self.ASSETS.keys()),
            "vs_currencies": "usd,brl",
            "include_24hr_change": "true",
            "include_24hr_vol": "true",
        }

        try:
            data = self._get_json(self.COINGECKO_URL, params)
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            self.logger.exception("Erro ao buscar dados de mercado. Detalhes: %s", exc)
            return []

        snapshots: list[AssetSnapshot] = []
        for coin_id, symbol in self.ASSETS.items():
            row = data.get(coin_id, {})
            snapshot = AssetSnapshot(
                symbol=symbol,
                price_usd=float(row.get("usd") or 0.0),
                price_brl=float(row.get("brl") or 0.0),
                change_24h_pct=float(row.get("usd_24h_change") or 0.0),
                volume_24h=float(row.get("usd_24h_vol") or 0.0),
            )
            snapshots.append(snapshot)

        self.logger.info("Monitoramento de mercado concluído | ativos=%s", len(snapshots))
        return snapshots

    def gerar_alerta_simples(self, snapshots: list[AssetSnapshot], threshold_pct: float = 3.0) -> bool:
        """Gera alerta por e-mail se algum ativo passar do limiar de variação 24h.

        Regra simples desta fase:
        - enviar alerta quando |variação 24h| >= threshold_pct.
        """
        relevantes = [s for s in snapshots if abs(s.change_24h_pct) >= threshold_pct]
        if not relevantes:
            self.logger.info("Sem alerta de mercado | nenhuma variação acima de %.2f%%", threshold_pct)
            return True

        linhas = ["Alerta simples de mercado (Fase 4)", ""]
        for s in relevantes:
            linhas.append(
                f"{s.symbol}: USD {s.price_usd:,.4f} | BRL {s.price_brl:,.4f} | "
                f"24h {s.change_24h_pct:+.2f}% | Vol24h USD {s.volume_24h:,.2f}"
            )

        corpo = "\n".join(linhas)
        self.logger.info("Disparando alerta simples de mercado | ativos_alerta=%s", len(relevantes))
        return self.email_service.enviar_email("[Alerta Mercado] Variação 24h", corpo)


    def buscar_historico(self, coin_id: str, days: int = 30) -> tuple[list[float], list[float]]:
        """Busca histórico diário (preço e volume) para cálculo de indicadores."""
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
        params = {"vs_currency": "usd", "days": days, "interval": "daily"}

        try:
            data = self._get_json(url, params)
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            self.logger.exception("Erro ao buscar histórico de %s. Detalhes: %s", coin_id, exc)
            return [], []

        prices = [float(item[1]) for item in data.get("prices", [])]
        volumes = [float(item[1]) for item in data.get("total_volumes", [])]

        self.logger.info("Histórico carregado | ativo=%s | pontos_preco=%s | pontos_volume=%s", coin_id, len(prices), len(volumes))
        return prices, volumes
