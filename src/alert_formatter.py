"""Formatação padronizada dos alertas de apoio à decisão."""

from src.risk_manager import RiskAssessment
from src.signal_service import IndicatorResult


DISCLAIMER = (
    "Ferramenta educacional de apoio à decisão. Não é recomendação financeira, "
    "não promete lucro e não executa ordens ou alavancagem."
)


def format_market_alert(indicator: IndicatorResult, risk: RiskAssessment) -> str:
    """Monta o formato obrigatório e sempre inclui stop e aviso de segurança."""
    buy_now = indicator.decisao if risk.approved else "Não"
    action = "Possível oportunidade" if risk.approved else "Aguardar / preservar capital"
    trend = "Alta" if indicator.price > indicator.sma and indicator.price > indicator.ema else "Indefinida"
    return "\n".join(
        [
            f"Ativo: {indicator.symbol}",
            f"Preço atual: {indicator.price:.4f}",
            f"Tendência: {trend}",
            f"Indicadores principais: RSI {indicator.rsi:.2f}; SMA {indicator.sma:.4f}; EMA {indicator.ema:.4f}",
            f"Nível de risco: {risk.level} ({risk.profile})",
            f"Possível ação: {action}",
            f"Comprar agora? {buy_now}",
            f"Justificativa: {risk.reason} {indicator.motivo}",
            f"Stop sugerido: {risk.stop:.4f}",
            f"Alvo possível: {risk.target:.4f}",
            f"Relação risco/retorno: {risk.risk_reward:.2f}",
            f"Exposição máxima sugerida: {risk.max_exposure_pct:.1f}%",
            f"Observação importante: {DISCLAIMER}",
        ]
    )
