from __future__ import annotations

import unittest
import sys
import types

try:
    import flask  # noqa: F401
    import google.genai  # noqa: F401
    import yfinance  # noqa: F401
except ModuleNotFoundError as exc:
    raise unittest.SkipTest(f"Python test dependency missing: {exc.name}") from exc

fake_finbert = types.ModuleType("sentiment.finbert")
fake_finbert.get_finbert = lambda: None
sys.modules.setdefault("sentiment.finbert", fake_finbert)

import server


class ApiRouteTests(unittest.TestCase):
    def setUp(self) -> None:
        server.app.config.update(TESTING=True)
        self.client = server.app.test_client()

    def test_health_endpoint_reports_ok(self) -> None:
        response = self.client.get("/api/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "ok")

    def test_settings_tickers_validates_empty_watchlist(self) -> None:
        response = self.client.post("/api/settings/tickers", json={"tickers": []})

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertFalse(payload["success"])
        self.assertIn("at least one ticker", payload["error"])

    def test_settings_tickers_accepts_comma_separated_string(self) -> None:
        response = self.client.post("/api/settings/tickers", json={"tickers": "tcs.ns, infy.ns"})

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(payload["success"])
        self.assertEqual(payload["tickers"], ["TCS.NS", "INFY.NS"])

    def test_ticker_analysis_requires_ticker(self) -> None:
        response = self.client.post("/api/analyze/ticker", json={})

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.get_json())

    def test_admin_verify_rejects_missing_token(self) -> None:
        response = self.client.get("/api/admin/verify")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.get_json()["error"], "Missing admin token")


if __name__ == "__main__":
    unittest.main()
