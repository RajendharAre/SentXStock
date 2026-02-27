"""
Portfolio Manager — manages mock portfolio state with real-time price support.
"""

import yfinance as yf
from config.config import EQUITY_ASSETS, BOND_ASSETS, DEFENSIVE_ASSETS


# Default portfolio for demo / initial state
DEFAULT_PORTFOLIO = {
    "cash": 50000.0,
    "holdings": {
        "AAPL": {"shares": 50, "avg_price": 180.0},
        "GOOGL": {"shares": 20, "avg_price": 140.0},
        "MSFT": {"shares": 30, "avg_price": 380.0},
        "SPY": {"shares": 40, "avg_price": 450.0},
        "TLT": {"shares": 60, "avg_price": 95.0},
    },
    "risk_level": "Medium",
}


class PortfolioManager:
    """Manages mock portfolio — holdings, cash, allocations, and live prices."""

    def __init__(self, portfolio: dict = None):
        """
        Initialize with a portfolio dict or use default.
        
        Args:
            portfolio: Dict with cash, holdings, and risk_level
        """
        if portfolio is None:
            portfolio = DEFAULT_PORTFOLIO.copy()
            portfolio["holdings"] = {
                k: v.copy() for k, v in DEFAULT_PORTFOLIO["holdings"].items()
            }

        self.cash = float(portfolio.get("cash", 50000.0))
        self.holdings = portfolio.get("holdings", {})
        self.risk_level = portfolio.get("risk_level", "Medium")
        self._live_prices = {}

    def fetch_live_prices(self) -> dict:
        """
        Fetch live stock prices using yfinance.
        Falls back to avg_price if fetch fails.
        
        Returns:
            Dict of ticker -> current price
        """
        tickers = list(self.holdings.keys())
        if not tickers:
            return {}

        try:
            data = yf.download(tickers, period="1d", progress=False)
            if "Close" in data.columns or len(tickers) == 1:
                for ticker in tickers:
                    try:
                        if len(tickers) == 1:
                            price = float(data["Close"].iloc[-1])
                        else:
                            price = float(data["Close"][ticker].iloc[-1])
                        self._live_prices[ticker] = round(price, 2)
                    except (KeyError, IndexError):
                        self._live_prices[ticker] = self.holdings[ticker]["avg_price"]
        except Exception as e:
            print(f"[WARNING] yfinance fetch failed: {e}. Using avg prices.")
            for ticker in tickers:
                self._live_prices[ticker] = self.holdings[ticker]["avg_price"]

        return self._live_prices

    def get_price(self, ticker: str) -> float:
        """Get current price for a ticker (live or avg fallback)."""
        if ticker in self._live_prices:
            return self._live_prices[ticker]
        if ticker in self.holdings:
            return self.holdings[ticker]["avg_price"]
        return 0.0

    def get_total_value(self) -> float:
        """Calculate total portfolio value (cash + holdings)."""
        holdings_value = sum(
            self.get_price(ticker) * info["shares"]
            for ticker, info in self.holdings.items()
        )
        return round(self.cash + holdings_value, 2)

    def get_allocation(self) -> dict:
        """
        Get current portfolio allocation breakdown.
        
        Returns:
            Dict with equity_pct, bonds_pct, cash_pct, and details
        """
        total = self.get_total_value()
        if total == 0:
            return {"equity_pct": 0, "bonds_pct": 0, "cash_pct": 100, "details": {}}

        equity_value = 0.0
        bonds_value = 0.0
        other_value = 0.0
        details = {}

        for ticker, info in self.holdings.items():
            value = self.get_price(ticker) * info["shares"]
            asset_type = self._classify_asset(ticker)
            details[ticker] = {
                "shares": info["shares"],
                "price": self.get_price(ticker),
                "value": round(value, 2),
                "type": asset_type,
                "pct": round((value / total) * 100, 2),
            }
            if asset_type == "equity":
                equity_value += value
            elif asset_type == "bonds":
                bonds_value += value
            else:
                other_value += value

        return {
            "equity_pct": round((equity_value / total) * 100, 2),
            "bonds_pct": round(((bonds_value + other_value) / total) * 100, 2),
            "cash_pct": round((self.cash / total) * 100, 2),
            "total_value": total,
            "cash": self.cash,
            "details": details,
        }

    def get_portfolio_summary(self) -> dict:
        """Get a full portfolio summary for display / agent input."""
        allocation = self.get_allocation()
        return {
            "risk_level": self.risk_level,
            "total_value": allocation["total_value"],
            "cash": self.cash,
            "equity_pct": allocation["equity_pct"],
            "bonds_pct": allocation["bonds_pct"],
            "cash_pct": allocation["cash_pct"],
            "holdings": allocation["details"],
        }

    def _classify_asset(self, ticker: str) -> str:
        """Classify a ticker as equity, bonds, or defensive."""
        if ticker in EQUITY_ASSETS or ticker == "SPY":
            return "equity"
        elif ticker in BOND_ASSETS:
            return "bonds"
        elif ticker in DEFENSIVE_ASSETS:
            return "defensive"
        else:
            return "equity"  # Default to equity
