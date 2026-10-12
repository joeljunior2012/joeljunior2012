"""Orquestrador do sistema de alertas — nunca executa ordens financeiras."""

from __future__ import annotations

import argparse
import logging
import time

from src.alert_formatter import format_market_alert
from src.backup_service import BackupError, BackupService
from src.config import Settings, get_settings
from src.email_service import EmailService
from src.inbox_service import InboxService
from src.logger_setup import setup_logger
from src.market_service import MarketService
from src.opportunity_service import OpportunityService
from src.report_service import ReportService
from src.risk_manager import RiskManager
from src.signal_service import SignalService
from src.timing_service import TimingService


def run_cycle(settings: Settings, logger: logging.Logger) -> None:
    """Executa um ciclo isolado; falhas de um ativo não interrompem os demais."""
    email_service = EmailService(settings, logger)

    if settings.run_inbox:
        InboxService(settings, logger, email_service).processar_caixa_entrada(max_emails=20)
    else:
        logger.info("Leitura IMAP desativada (RUN_INBOX=false).")

    if not settings.run_market:
        logger.info("Monitoramento de mercado desativado (RUN_MARKET=false).")
        return

    market = MarketService(logger, email_service)
    snapshots = market.buscar_mercado()
    market.gerar_alerta_simples(snapshots, threshold_pct=3.0)

    signals = SignalService()
    timing_service = TimingService()
    risk_manager = RiskManager()
    opportunities = OpportunityService(max_signals_per_day=settings.max_signals_per_day)

    for coin_id, symbol in market.ASSETS.items():
        try:
            prices, volumes = market.buscar_historico(coin_id, days=30)
            if len(prices) < 15 or len(volumes) < 15:
                logger.warning("Histórico insuficiente | ativo=%s", symbol)
                continue

            indicator = signals.calcular_indicadores(symbol, prices, volumes)
            liquidity = min(indicator.volume_atual / max(indicator.volume_medio, 1e-9), 1.0)
            timing = timing_service.analisar_momento(liquidity, indicator.volatilidade_pct)
            risk = risk_manager.avaliar(
                indicator.price,
                indicator.suporte,
                indicator.resistencia,
                indicator.volatilidade_pct,
            )
            opportunity = opportunities.gerar_sinal(indicator, timing)
            logger.info(
                "Análise %s | score=%s | confiança=%s | risco=%s | decisão=%s",
                symbol, opportunity.score, opportunity.confianca, risk.level, indicator.decisao,
            )

            # Alertas fortes ou de risco são informativos e sempre passam pelo modo TEST.
            if (opportunity.score >= 71 and risk.approved) or risk.level == "ALTO":
                sent = email_service.enviar_email(
                    f"[Alerta {risk.level}] {symbol} — score {opportunity.score}",
                    format_market_alert(indicator, risk),
                )
                if sent:
                    opportunities.registrar_sinal_enviado(opportunity)
        except (ValueError, ArithmeticError) as exc:
            logger.warning("Análise inválida | ativo=%s | erro=%s", symbol, exc)
        except Exception:
            logger.exception("Falha inesperada ao analisar o ativo %s", symbol)

    if settings.send_daily_report:
        ReportService(email_service).enviar_relatorio_diario()


def main() -> None:
    """Inicia uma execução única ou um loop no intervalo configurado."""
    parser = argparse.ArgumentParser(description="Sistema informativo de alertas, sem auto-trade.")
    parser.add_argument("--loop", action="store_true", help="Repete a análise no intervalo do .env.")
    maintenance = parser.add_mutually_exclusive_group()
    maintenance.add_argument("--backup", action="store_true", help="Cria um backup dos históricos e encerra.")
    maintenance.add_argument("--restore", metavar="ARQUIVO", help="Restaura um arquivo ZIP de backup e encerra.")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Permite que --restore substitua históricos existentes.",
    )
    args = parser.parse_args()
    if args.overwrite and not args.restore:
        parser.error("--overwrite só pode ser usado junto com --restore.")

    settings = get_settings()
    logger = setup_logger(settings.log_dir, settings.log_file, settings.log_level)
    logger.info("Aplicação iniciada | modo=%s | auto-trade=DESATIVADO", settings.app_mode)
    backup_service = BackupService(
        logger,
        backup_dir=settings.backup_dir,
        retention=settings.backup_retention,
    )

    if args.backup:
        backup_service.criar_backup()
        return
    if args.restore:
        try:
            backup_service.restaurar_backup(args.restore, overwrite=args.overwrite)
        except BackupError as exc:
            parser.error(str(exc))
        return

    while True:
        run_cycle(settings, logger)
        if settings.backup_enabled:
            backup_service.criar_backup()
        if not args.loop:
            break
        logger.info("Próximo ciclo em %s minutos.", settings.analysis_interval_minutes)
        time.sleep(settings.analysis_interval_minutes * 60)


if __name__ == "__main__":
    main()
