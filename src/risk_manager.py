"""Regras conservadoras de gestão de risco para alertas informativos.

O módulo nunca envia ordens. Ele apenas calcula níveis educativos para que
uma pessoa avalie a operação antes de tomar qualquer decisão.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RiskAssessment:
    """Resultado imutável da avaliação de risco."""

    level: str
    profile: str
    stop: float
    target: float
    risk_reward: float
    max_exposure_pct: float
    approved: bool
    reason: str


class RiskManager:
    """Calcula stop, alvo, relação risco/retorno e exposição máxima."""

    def avaliar(
        self,
        price: float,
        support: float,
        resistance: float,
        volatility_pct: float,
    ) -> RiskAssessment:
        """Avalia uma possível entrada compradora sem executar uma ordem."""
        if price <= 0 or support <= 0 or resistance <= 0:
            raise ValueError("Preço, suporte e resistência devem ser positivos.")

        # O stop fica abaixo do suporte e nunca é igual ao preço de entrada.
        buffer_pct = max(0.01, min(volatility_pct / 100, 0.05))
        stop = min(support * (1 - buffer_pct), price * 0.99)
        target = resistance
        risk = price - stop
        reward = target - price
        ratio = reward / risk if risk > 0 else 0.0

        if volatility_pct >= 8:
            level, profile, exposure = "ALTO", "AGRESSIVO", 1.0
        elif volatility_pct >= 4:
            level, profile, exposure = "MÉDIO", "MODERADO", 3.0
        else:
            level, profile, exposure = "BAIXO", "CONSERVADOR", 5.0

        approved = reward > risk and ratio >= 1.5 and volatility_pct < 8
        reason = (
            "Relação risco/retorno aceitável e volatilidade controlada."
            if approved
            else "Entrada bloqueada: retorno potencial não compensa o risco ou volatilidade está alta."
        )
        return RiskAssessment(
            level=level,
            profile=profile,
            stop=stop,
            target=target,
            risk_reward=ratio,
            max_exposure_pct=exposure,
            approved=approved,
            reason=reason,
        )
