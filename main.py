"""Ponto de entrada da aplicação.

Nesta fase, apenas inicializamos configuração e logging.
"""

from src.config import get_settings
from src.logger_setup import setup_logger
from src.email_service import EmailService
from src.inbox_service import InboxService
from src.market_service import MarketService
from src.signal_service import SignalService
from src.timing_service import TimingService
from src.opportunity_service import OpportunityService
from src.report_service import ReportService


def main() -> None:
    """Inicialização mínima e segura para a Fase 1."""
    settings = get_settings()
    logger = setup_logger(settings.log_dir, settings.log_file, settings.log_level)

    logger.info("Aplicação iniciada.")
    logger.info("Modo atual: %s", settings.app_mode)
    logger.info("Nome da aplicação: %s", settings.app_name)
    logger.info("Timezone: %s", settings.timezone)

    # Exemplo de uso do serviço de e-mail nesta fase (somente envio).
    email_service = EmailService(settings, logger)
    ok = email_service.enviar_email(
        assunto="[Fase 2] Teste de envio",
        corpo="Este é um e-mail de teste do sistema de alertas.",
    )
    logger.info("Resultado enviar_email: %s", ok)

    # Fase 3: leitura da caixa de entrada via IMAP e processamento básico.
    inbox_service = InboxService(settings, logger, email_service)
    total = inbox_service.processar_caixa_entrada(max_emails=10)
    logger.info("Total processado na caixa de entrada: %s", total)

    # Fase 4: monitoramento simples de mercado para BTC/ETH/SOL/BNB/XRP.
    market_service = MarketService(logger, email_service)
    snapshots = market_service.buscar_mercado()
    market_service.gerar_alerta_simples(snapshots, threshold_pct=3.0)

    # Fase 5: indicadores simples e decisão textual (sem executar ordens).
    signal_service = SignalService()
    opportunity_service = OpportunityService(max_signals_per_day=5)
    for coin_id, symbol in market_service.ASSETS.items():
        prices, volumes = market_service.buscar_historico(coin_id, days=30)
        if len(prices) < 15 or len(volumes) < 15:
            logger.warning("Histórico insuficiente para indicadores | ativo=%s", symbol)
            continue

        result = signal_service.calcular_indicadores(symbol=symbol, close_prices=prices, volumes=volumes)
        logger.info(
            "Indicadores %s | RSI=%.2f SMA=%.2f EMA=%.2f Suporte=%.2f Resistência=%.2f Vol=%.2f%% VolAnormal=%s Decisão=%s",
            result.symbol,
            result.rsi,
            result.sma,
            result.ema,
            result.suporte,
            result.resistencia,
            result.volatilidade_pct,
            result.volume_anormal,
            result.decisao,
        )

        # Fase 6: recomendação por horário (Brasília), liquidez e volatilidade.
        timing_service = TimingService()
        liquidez_score = min(result.volume_atual / max(result.volume_medio, 1e-9), 1.0)
        timing = timing_service.analisar_momento(
            liquidez_score=liquidez_score,
            volatilidade_pct=result.volatilidade_pct,
        )
        logger.info(
            "Timing %s | BRT=%s | JanelaEUA=%s | Recomendação=%s | Motivo=%s",
            result.symbol,
            timing.brasilia_time,
            timing.janela_eua,
            timing.recomendacao,
            timing.motivo,
        )

        # Fase 7: score final, anti-FOMO, overtrading e confiança do sinal.
        final_signal = opportunity_service.gerar_sinal(result, timing)
        logger.info(
            "Sinal final %s | Score=%s | Confiança=%s | Recomendação=%s | Motivo=%s",
            final_signal.symbol,
            final_signal.score,
            final_signal.confianca,
            final_signal.recomendacao,
            final_signal.motivo,
        )

    # Fase 7: relatório diário por e-mail.
    report_service = ReportService(email_service)
    report_ok = report_service.enviar_relatorio_diario()
    logger.info("Relatório diário enviado? %s", report_ok)


if __name__ == "__main__":
    main()
