"""Testes dos indicadores sem depender de internet."""

import unittest

from src.signal_service import SignalService


class SignalServiceTests(unittest.TestCase):
    def test_indicator_result_has_safe_decision(self) -> None:
        prices = [100 + index * 0.5 for index in range(30)]
        volumes = [1000.0] * 29 + [2000.0]
        result = SignalService().calcular_indicadores("TEST", prices, volumes)
        self.assertIn(result.decisao, {"Sim", "Não", "Aguardar confirmação"})
        self.assertGreater(result.suporte, 0)

    def test_rejects_short_history(self) -> None:
        with self.assertRaises(ValueError):
            SignalService().calcular_indicadores("TEST", [1, 2], [1, 2])


if __name__ == "__main__":
    unittest.main()
