"""
Strategy Layer
==============
Translates a daily sentiment score into a position signal and size.

Fully configurable — no ticker-specific parameters.
Supports comparing multiple strategy variants side-by-side.

Strategies
----------
- **SentimentThreshold**  (default)
    BUY  if score ≥  buy_threshold
    SELL if score ≤  sell_threshold
    HOLD otherwise

- **MomentumSentimentBlend**
    Blends sentiment score with price momentum (equal weight).
    Threshold logic same as above.

- **AdaptiveRisk**
    Adjusts position size dynamically based on how strongly bullish/bearish
    the signal is (linear scale from 0→max_position_pct).

Position sizing
---------------
All strategies return a `position_pct` in [0, 1] representing the
fraction of available capital to allocate to this ticker.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal

import numpy as np
import pandas as pd


Signal = Literal["BUY", "SELL", "HOLD"]


@dataclass
class StrategyConfig:
    """All tunable parameters for the strategy layer."""

    # ── Signal thresholds ────────────────────────────────────────────────────
    buy_threshold:         float = 0.10   # sentiment ≥ this → BUY
    sell_threshold:        float = -0.10  # sentiment ≤ this → SELL

    # ── Position sizing ──────────────────────────────────────────────────────
    max_position_pct:      float = 0.05   # max 5% of portfolio per ticker
    min_position_pct:      float = 0.005  # min 0.5% (avoids rounding to zero)
    size_by_conviction:    bool  = True   # scale size with signal strength

    # ── Risk allocation (mirrors config.py) ──────────────────────────────────
    risk_level:            str   = "Medium"  # Low / Medium / High
    equity_pct: dict = field(default_factory=lambda: {
        "Low": 0.25, "Medium": 0.50, "High": 0.70
    })

    # ── Model variant ────────────────────────────────────────────────────────
    model_variant:         str   = "price_momentum"
    # Options: "price_momentum" | "finbert_only" | "finbert_gemini"

    # ── Blend weight (MomentumSentimentBlend only) ───────────────────────────
    momentum_weight:       float = 0.30   # weight of price momentum in blend
    sentiment_weight:      float = 0.70   # weight of sentiment score in blend

    # ── Cooldown ─────────────────────────────────────────────────────────────
    signal_cooldown_days:  int   = 3      # don't flip signal faster than N days


class SentimentStrategy:
    """
    Core strategy: pure sentiment threshold.

    Parameters
    ----------
    config : StrategyConfig
    """

    name = "SentimentThreshold"

    def __init__(self, config: StrategyConfig = None):
        self.cfg = config or StrategyConfig()

    # ── Main interface ───────────────────────────────────────────────────────

    def compute_signals(
        self,
        sentiment: pd.Series,
        prices: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Compute daily signals for a single ticker.

        Parameters
        ----------
        sentiment : pd.Series  daily sentiment score [-1, 1]
        prices    : pd.DataFrame  OHLCV, index=DatetimeIndex

        Returns
        -------
        pd.DataFrame with columns:
            signal        : "BUY" | "SELL" | "HOLD"
            position_pct  : float  fraction of capital to allocate
            sentiment     : float  raw input score
            blended_score : float  score after any blending
        """
        aligned = sentiment.reindex(prices.index).fillna(0.0)
        scores  = self._blend_signals(aligned, prices)
        signals = scores.apply(self._classify)
        sizes   = self._position_sizes(scores, signals)

        return pd.DataFrame({
            "signal":        signals,
            "position_pct":  sizes,
            "sentiment":     aligned,
            "blended_score": scores,
        }, index=prices.index)

    # ── Internal helpers ─────────────────────────────────────────────────────

    def _blend_signals(self, sentiment: pd.Series, prices: pd.DataFrame) -> pd.Series:
        """Default: identity (override in subclasses for blending)."""
        return sentiment

    def _classify(self, score: float) -> Signal:
        if score >= self.cfg.buy_threshold:
            return "BUY"
        if score <= self.cfg.sell_threshold:
            return "SELL"
        return "HOLD"

    def _position_sizes(self, scores: pd.Series, signals: pd.Series) -> pd.Series:
        """
        Map signal + score to position fraction.

        If size_by_conviction=True, position scales linearly with score magnitude
        between min_position_pct and max_position_pct.
        """
        if not self.cfg.size_by_conviction:
            # uniform size for all non-HOLD signals
            return signals.apply(
                lambda s: self.cfg.max_position_pct if s != "HOLD" else 0.0
            )

        buy_range  = self.cfg.buy_threshold
        sell_range = abs(self.cfg.sell_threshold)

        def sized(row):
            sig, score = row
            if sig == "HOLD":
                return 0.0
            if sig == "BUY":
                t = min((score - self.cfg.buy_threshold) / max(1 - self.cfg.buy_threshold, 1e-9), 1.0)
            else:  # SELL
                t = min((abs(score) - self.cfg.sell_threshold) / max(1 - self.cfg.sell_threshold, 1e-9), 1.0)
            size = self.cfg.min_position_pct + t * (self.cfg.max_position_pct - self.cfg.min_position_pct)
            return round(float(size), 6)

        return pd.Series(
            [sized(row) for row in zip(signals, scores)],
            index=scores.index,
        )

    def describe(self) -> dict:
        """Return a human-readable config summary."""
        return {
            "name":           self.name,
            "buy_threshold":  self.cfg.buy_threshold,
            "sell_threshold": self.cfg.sell_threshold,
            "max_position":   f"{self.cfg.max_position_pct*100:.1f}%",
            "risk_level":     self.cfg.risk_level,
            "model_variant":  self.cfg.model_variant,
        }


class MomentumSentimentBlend(SentimentStrategy):
    """
    Blends sentiment score with short-term price momentum.
    Useful to compare against pure-sentiment strategy.
    """

    name = "MomentumSentimentBlend"

    def _blend_signals(self, sentiment: pd.Series, prices: pd.DataFrame) -> pd.Series:
        close   = prices["Close"].squeeze()
        momentum = close.pct_change(5).clip(-0.5, 0.5) * 2.0  # scale to [-1,1]
        momentum = momentum.reindex(sentiment.index).fillna(0.0)

        blended = (
            self.cfg.sentiment_weight * sentiment
            + self.cfg.momentum_weight * momentum
        ).clip(-1.0, 1.0)
        return blended


class AdaptiveRiskStrategy(SentimentStrategy):
    """
    Like SentimentThreshold but uses different thresholds
    depending on the configured risk level.

    High risk  → looser thresholds → more signals
    Low risk   → stricter thresholds → fewer, higher-conviction signals
    """

    name = "AdaptiveRisk"

    _THRESHOLDS = {
        "Low":    {"buy":  0.25, "sell": -0.25},
        "Medium": {"buy":  0.10, "sell": -0.10},
        "High":   {"buy":  0.05, "sell": -0.05},
    }

    def __init__(self, config: StrategyConfig = None):
        super().__init__(config)
        thresholds = self._THRESHOLDS.get(self.cfg.risk_level, self._THRESHOLDS["Medium"])
        self.cfg.buy_threshold  = thresholds["buy"]
        self.cfg.sell_threshold = thresholds["sell"]


# ─── Factory ─────────────────────────────────────────────────────────────────

def build_strategy(
    variant: str = "threshold",
    config: StrategyConfig = None,
) -> SentimentStrategy:
    """
    Factory function.

    variant : "threshold" | "blend" | "adaptive"
    """
    config = config or StrategyConfig()
    mapping = {
        "threshold": SentimentStrategy,
        "blend":     MomentumSentimentBlend,
        "adaptive":  AdaptiveRiskStrategy,
    }
    cls = mapping.get(variant, SentimentStrategy)
    return cls(config)
