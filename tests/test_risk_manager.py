"""Testes unitários da camada que impede alertas de risco desfavorável."""

import unittest

from src.risk_manager import RiskManager


class RiskManagerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manager = RiskManager()

    def test_approves_positive_risk_reward(self) -> None:
        result = self.manager.avaliar(100, 98, 110, 2)
        self.assertTrue(result.approved)
        self.assertGreaterEqual(result.risk_reward, 1.5)
        self.assertLess(result.stop, 100)

    def test_blocks_high_volatility(self) -> None:
        result = self.manager.avaliar(100, 95, 130, 9)
        self.assertFalse(result.approved)
        self.assertEqual(result.level, "ALTO")

    def test_rejects_invalid_price(self) -> None:
        with self.assertRaises(ValueError):
            self.manager.avaliar(0, 95, 110, 2)


if __name__ == "__main__":
    unittest.main()
