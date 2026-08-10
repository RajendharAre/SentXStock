from __future__ import annotations

import unittest

try:
    import pandas as pd
except ModuleNotFoundError as exc:
    raise unittest.SkipTest(f"Python test dependency missing: {exc.name}") from exc

from admin import dataset_manager
from admin.trainer import _classify_columns, _sanitize


class AdminDatasetTests(unittest.TestCase):
    def test_sql_insert_parser_returns_dataframe(self) -> None:
        df = dataset_manager._parse_sql(
            "INSERT INTO prices (date, close, headline) "
            "VALUES ('2026-01-01', 123.45, 'Strong earnings');"
        )

        self.assertEqual(df.shape, (1, 3))
        self.assertEqual(df.loc[0, "date"], "2026-01-01")
        self.assertEqual(df.loc[0, "close"], "123.45")
        self.assertEqual(df.loc[0, "headline"], "Strong earnings")

    def test_trainer_column_classifier_detects_text_price_and_date(self) -> None:
        df = pd.DataFrame({
            "Date": ["2026-01-01"],
            "Close": [100.0],
            "Headline": ["Company beats estimates"],
            "Ticker": ["TCS.NS"],
        })

        classified = _classify_columns(df)

        self.assertIn("Date", classified["date"])
        self.assertIn("Close", classified["price"])
        self.assertIn("Headline", classified["text"])
        self.assertIn("Ticker", classified["text"])

    def test_sanitize_replaces_nan_and_infinity_for_json(self) -> None:
        clean = _sanitize({"values": [1.0, float("nan"), float("inf"), -float("inf")]})

        self.assertEqual(clean, {"values": [1.0, None, None, None]})


if __name__ == "__main__":
    unittest.main()
