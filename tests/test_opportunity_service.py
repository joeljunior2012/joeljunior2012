"""Testa que análises comuns não são gravadas como alertas enviados."""

import tempfile
import unittest
from pathlib import Path

from src.opportunity_service import OpportunityService
from src.signal_service import IndicatorResult
from src.timing_service import TimingRecommendation


class OpportunityHistoryTests(unittest.TestCase):
    def test_history_is_written_only_after_send_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            service = OpportunityService(max_signals_per_day=5)
            service.history_path = Path(directory) / "signals.jsonl"
            indicator = IndicatorResult(
                "BTC", 100, 50, 99, 99, 95, 110, 2, 2000, 1000, True, "Sim", "ok"
            )
            timing = TimingRecommendation(True, "Operar agora", "ok", "agora", "ABERTURA_EUA")

            signal = service.gerar_sinal(indicator, timing)
            self.assertFalse(service.history_path.exists())

            service.registrar_sinal_enviado(signal)
            self.assertEqual(len(service.history_path.read_text(encoding="utf-8").splitlines()), 1)


if __name__ == "__main__":
    unittest.main()
