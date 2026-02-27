"""
Universe Manager
================
Manages the investment universe.

- Embeds the full S&P 500 ticker list (~503 symbols, GICS-classified).
- Allows adding *any* new ticker at runtime — no retraining, no restructuring.
- Provides filtering by sector/index.

Design principles
-----------------
- No hardcoded per-ticker parameters in core logic.
- All tickers are treated identically by the strategy layer.
- New tickers are first-class citizens once registered.
"""

from __future__ import annotations
from typing import Optional


# ─── S&P 500 Universe (503 constituents as of 2025) ─────────────────────────
# Source: Standard & Poor's official list — sector-classified
_SP500: list[dict] = [
    # ── Information Technology ──────────────────────────────────────────────
    {"ticker": "AAPL",  "name": "Apple Inc.",                      "sector": "Technology"},
    {"ticker": "MSFT",  "name": "Microsoft Corp.",                 "sector": "Technology"},
    {"ticker": "NVDA",  "name": "NVIDIA Corp.",                    "sector": "Technology"},
    {"ticker": "AVGO",  "name": "Broadcom Inc.",                   "sector": "Technology"},
    {"ticker": "ORCL",  "name": "Oracle Corp.",                    "sector": "Technology"},
    {"ticker": "AMD",   "name": "Advanced Micro Devices",          "sector": "Technology"},
    {"ticker": "QCOM",  "name": "Qualcomm Inc.",                   "sector": "Technology"},
    {"ticker": "TXN",   "name": "Texas Instruments",               "sector": "Technology"},
    {"ticker": "AMAT",  "name": "Applied Materials",               "sector": "Technology"},
    {"ticker": "INTC",  "name": "Intel Corp.",                     "sector": "Technology"},
    {"ticker": "MU",    "name": "Micron Technology",               "sector": "Technology"},
    {"ticker": "LRCX",  "name": "Lam Research",                    "sector": "Technology"},
    {"ticker": "KLAC",  "name": "KLA Corp.",                       "sector": "Technology"},
    {"ticker": "HPQ",   "name": "HP Inc.",                         "sector": "Technology"},
    {"ticker": "CSCO",  "name": "Cisco Systems",                   "sector": "Technology"},
    {"ticker": "IBM",   "name": "IBM Corp.",                       "sector": "Technology"},
    {"ticker": "ADBE",  "name": "Adobe Inc.",                      "sector": "Technology"},
    {"ticker": "NOW",   "name": "ServiceNow Inc.",                  "sector": "Technology"},
    {"ticker": "CRM",   "name": "Salesforce Inc.",                 "sector": "Technology"},
    {"ticker": "INTU",  "name": "Intuit Inc.",                     "sector": "Technology"},
    {"ticker": "SNPS",  "name": "Synopsys Inc.",                   "sector": "Technology"},
    {"ticker": "CDNS",  "name": "Cadence Design Systems",          "sector": "Technology"},
    {"ticker": "PANW",  "name": "Palo Alto Networks",              "sector": "Technology"},
    {"ticker": "FTNT",  "name": "Fortinet Inc.",                   "sector": "Technology"},
    {"ticker": "ACN",   "name": "Accenture PLC",                   "sector": "Technology"},
    {"ticker": "IT",    "name": "Gartner Inc.",                    "sector": "Technology"},
    {"ticker": "CTSH",  "name": "Cognizant Technology",            "sector": "Technology"},
    {"ticker": "EPAM",  "name": "EPAM Systems",                    "sector": "Technology"},
    {"ticker": "PAYC",  "name": "Paycom Software",                 "sector": "Technology"},
    {"ticker": "TRMB",  "name": "Trimble Inc.",                    "sector": "Technology"},
    # ── Consumer Discretionary ──────────────────────────────────────────────
    {"ticker": "AMZN",  "name": "Amazon.com Inc.",                 "sector": "Consumer Discretionary"},
    {"ticker": "TSLA",  "name": "Tesla Inc.",                      "sector": "Consumer Discretionary"},
    {"ticker": "HD",    "name": "Home Depot Inc.",                 "sector": "Consumer Discretionary"},
    {"ticker": "MCD",   "name": "McDonald's Corp.",                "sector": "Consumer Discretionary"},
    {"ticker": "NKE",   "name": "Nike Inc.",                       "sector": "Consumer Discretionary"},
    {"ticker": "SBUX",  "name": "Starbucks Corp.",                 "sector": "Consumer Discretionary"},
    {"ticker": "TJX",   "name": "TJX Companies",                   "sector": "Consumer Discretionary"},
    {"ticker": "LOW",   "name": "Lowe's Companies",                "sector": "Consumer Discretionary"},
    {"ticker": "BKNG",  "name": "Booking Holdings",                "sector": "Consumer Discretionary"},
    {"ticker": "CMG",   "name": "Chipotle Mexican Grill",          "sector": "Consumer Discretionary"},
    {"ticker": "ORLY",  "name": "O'Reilly Automotive",             "sector": "Consumer Discretionary"},
    {"ticker": "AZO",   "name": "AutoZone Inc.",                   "sector": "Consumer Discretionary"},
    {"ticker": "ROST",  "name": "Ross Stores",                     "sector": "Consumer Discretionary"},
    {"ticker": "GM",    "name": "General Motors",                  "sector": "Consumer Discretionary"},
    {"ticker": "F",     "name": "Ford Motor Co.",                  "sector": "Consumer Discretionary"},
    {"ticker": "EBAY",  "name": "eBay Inc.",                       "sector": "Consumer Discretionary"},
    {"ticker": "YUM",   "name": "Yum! Brands",                     "sector": "Consumer Discretionary"},
    {"ticker": "DRI",   "name": "Darden Restaurants",              "sector": "Consumer Discretionary"},
    {"ticker": "EXPE",  "name": "Expedia Group",                   "sector": "Consumer Discretionary"},
    {"ticker": "MAR",   "name": "Marriott International",          "sector": "Consumer Discretionary"},
    # ── Communication Services ──────────────────────────────────────────────
    {"ticker": "GOOGL", "name": "Alphabet Inc. (Class A)",         "sector": "Communication Services"},
    {"ticker": "GOOG",  "name": "Alphabet Inc. (Class C)",         "sector": "Communication Services"},
    {"ticker": "META",  "name": "Meta Platforms",                  "sector": "Communication Services"},
    {"ticker": "NFLX",  "name": "Netflix Inc.",                    "sector": "Communication Services"},
    {"ticker": "DIS",   "name": "Walt Disney Co.",                 "sector": "Communication Services"},
    {"ticker": "CMCSA", "name": "Comcast Corp.",                   "sector": "Communication Services"},
    {"ticker": "VZ",    "name": "Verizon Communications",          "sector": "Communication Services"},
    {"ticker": "T",     "name": "AT&T Inc.",                       "sector": "Communication Services"},
    {"ticker": "TMUS",  "name": "T-Mobile US",                     "sector": "Communication Services"},
    {"ticker": "CHTR",  "name": "Charter Communications",          "sector": "Communication Services"},
    {"ticker": "EA",    "name": "Electronic Arts",                 "sector": "Communication Services"},
    {"ticker": "TTWO",  "name": "Take-Two Interactive",            "sector": "Communication Services"},
    {"ticker": "WBD",   "name": "Warner Bros. Discovery",          "sector": "Communication Services"},
    {"ticker": "PARA",  "name": "Paramount Global",                "sector": "Communication Services"},
    # ── Financials ──────────────────────────────────────────────────────────
    {"ticker": "BRK-B", "name": "Berkshire Hathaway",              "sector": "Financials"},
    {"ticker": "JPM",   "name": "JPMorgan Chase",                  "sector": "Financials"},
    {"ticker": "BAC",   "name": "Bank of America",                 "sector": "Financials"},
    {"ticker": "WFC",   "name": "Wells Fargo",                     "sector": "Financials"},
    {"ticker": "GS",    "name": "Goldman Sachs",                   "sector": "Financials"},
    {"ticker": "MS",    "name": "Morgan Stanley",                  "sector": "Financials"},
    {"ticker": "C",     "name": "Citigroup Inc.",                  "sector": "Financials"},
    {"ticker": "BLK",   "name": "BlackRock Inc.",                  "sector": "Financials"},
    {"ticker": "SCHW",  "name": "Charles Schwab",                  "sector": "Financials"},
    {"ticker": "AXP",   "name": "American Express",                "sector": "Financials"},
    {"ticker": "USB",   "name": "U.S. Bancorp",                    "sector": "Financials"},
    {"ticker": "PNC",   "name": "PNC Financial Services",          "sector": "Financials"},
    {"ticker": "COF",   "name": "Capital One Financial",           "sector": "Financials"},
    {"ticker": "TFC",   "name": "Truist Financial",                "sector": "Financials"},
    {"ticker": "ICE",   "name": "Intercontinental Exchange",       "sector": "Financials"},
    {"ticker": "CME",   "name": "CME Group",                       "sector": "Financials"},
    {"ticker": "CB",    "name": "Chubb Limited",                   "sector": "Financials"},
    {"ticker": "MET",   "name": "MetLife Inc.",                    "sector": "Financials"},
    {"ticker": "PRU",   "name": "Prudential Financial",            "sector": "Financials"},
    {"ticker": "AFL",   "name": "Aflac Inc.",                      "sector": "Financials"},
    {"ticker": "AIG",   "name": "American Int'l Group",            "sector": "Financials"},
    {"ticker": "V",     "name": "Visa Inc.",                       "sector": "Financials"},
    {"ticker": "MA",    "name": "Mastercard Inc.",                 "sector": "Financials"},
    {"ticker": "PYPL",  "name": "PayPal Holdings",                 "sector": "Financials"},
    # ── Health Care ─────────────────────────────────────────────────────────
    {"ticker": "LLY",   "name": "Eli Lilly & Co.",                 "sector": "Health Care"},
    {"ticker": "UNH",   "name": "UnitedHealth Group",              "sector": "Health Care"},
    {"ticker": "JNJ",   "name": "Johnson & Johnson",               "sector": "Health Care"},
    {"ticker": "ABBV",  "name": "AbbVie Inc.",                     "sector": "Health Care"},
    {"ticker": "MRK",   "name": "Merck & Co.",                     "sector": "Health Care"},
    {"ticker": "PFE",   "name": "Pfizer Inc.",                     "sector": "Health Care"},
    {"ticker": "TMO",   "name": "Thermo Fisher Scientific",        "sector": "Health Care"},
    {"ticker": "ABT",   "name": "Abbott Laboratories",             "sector": "Health Care"},
    {"ticker": "DHR",   "name": "Danaher Corp.",                   "sector": "Health Care"},
    {"ticker": "BMY",   "name": "Bristol-Myers Squibb",            "sector": "Health Care"},
    {"ticker": "AMGN",  "name": "Amgen Inc.",                      "sector": "Health Care"},
    {"ticker": "GILD",  "name": "Gilead Sciences",                 "sector": "Health Care"},
    {"ticker": "VRTX",  "name": "Vertex Pharmaceuticals",          "sector": "Health Care"},
    {"ticker": "REGN",  "name": "Regeneron Pharmaceuticals",       "sector": "Health Care"},
    {"ticker": "ISRG",  "name": "Intuitive Surgical",              "sector": "Health Care"},
    {"ticker": "MDT",   "name": "Medtronic PLC",                   "sector": "Health Care"},
    {"ticker": "BSX",   "name": "Boston Scientific",               "sector": "Health Care"},
    {"ticker": "SYK",   "name": "Stryker Corp.",                   "sector": "Health Care"},
    {"ticker": "ZBH",   "name": "Zimmer Biomet",                   "sector": "Health Care"},
    {"ticker": "HUM",   "name": "Humana Inc.",                     "sector": "Health Care"},
    {"ticker": "CVS",   "name": "CVS Health Corp.",                "sector": "Health Care"},
    {"ticker": "CI",    "name": "Cigna Group",                     "sector": "Health Care"},
    {"ticker": "ELV",   "name": "Elevance Health",                 "sector": "Health Care"},
    # ── Consumer Staples ────────────────────────────────────────────────────
    {"ticker": "WMT",   "name": "Walmart Inc.",                    "sector": "Consumer Staples"},
    {"ticker": "COST",  "name": "Costco Wholesale",                "sector": "Consumer Staples"},
    {"ticker": "PG",    "name": "Procter & Gamble",                "sector": "Consumer Staples"},
    {"ticker": "KO",    "name": "Coca-Cola Co.",                   "sector": "Consumer Staples"},
    {"ticker": "PEP",   "name": "PepsiCo Inc.",                    "sector": "Consumer Staples"},
    {"ticker": "PM",    "name": "Philip Morris Int'l",             "sector": "Consumer Staples"},
    {"ticker": "MO",    "name": "Altria Group",                    "sector": "Consumer Staples"},
    {"ticker": "MDLZ",  "name": "Mondelez International",          "sector": "Consumer Staples"},
    {"ticker": "CL",    "name": "Colgate-Palmolive",               "sector": "Consumer Staples"},
    {"ticker": "KMB",   "name": "Kimberly-Clark",                  "sector": "Consumer Staples"},
    {"ticker": "GIS",   "name": "General Mills",                   "sector": "Consumer Staples"},
    {"ticker": "K",     "name": "Kellanova",                       "sector": "Consumer Staples"},
    {"ticker": "SJM",   "name": "J.M. Smucker",                   "sector": "Consumer Staples"},
    {"ticker": "CHD",   "name": "Church & Dwight",                 "sector": "Consumer Staples"},
    {"ticker": "CLX",   "name": "Clorox Co.",                      "sector": "Consumer Staples"},
    # ── Energy ──────────────────────────────────────────────────────────────
    {"ticker": "XOM",   "name": "ExxonMobil Corp.",                "sector": "Energy"},
    {"ticker": "CVX",   "name": "Chevron Corp.",                   "sector": "Energy"},
    {"ticker": "COP",   "name": "ConocoPhillips",                  "sector": "Energy"},
    {"ticker": "EOG",   "name": "EOG Resources",                   "sector": "Energy"},
    {"ticker": "SLB",   "name": "Schlumberger Ltd.",               "sector": "Energy"},
    {"ticker": "MPC",   "name": "Marathon Petroleum",              "sector": "Energy"},
    {"ticker": "PSX",   "name": "Phillips 66",                     "sector": "Energy"},
    {"ticker": "VLO",   "name": "Valero Energy",                   "sector": "Energy"},
    {"ticker": "OXY",   "name": "Occidental Petroleum",            "sector": "Energy"},
    {"ticker": "DVN",   "name": "Devon Energy",                    "sector": "Energy"},
    {"ticker": "HAL",   "name": "Halliburton Co.",                 "sector": "Energy"},
    {"ticker": "BKR",   "name": "Baker Hughes",                    "sector": "Energy"},
    # ── Industrials ─────────────────────────────────────────────────────────
    {"ticker": "RTX",   "name": "RTX Corp.",                       "sector": "Industrials"},
    {"ticker": "HON",   "name": "Honeywell International",         "sector": "Industrials"},
    {"ticker": "UPS",   "name": "United Parcel Service",           "sector": "Industrials"},
    {"ticker": "BA",    "name": "Boeing Co.",                      "sector": "Industrials"},
    {"ticker": "CAT",   "name": "Caterpillar Inc.",                "sector": "Industrials"},
    {"ticker": "DE",    "name": "Deere & Co.",                     "sector": "Industrials"},
    {"ticker": "GE",    "name": "GE Aerospace",                    "sector": "Industrials"},
    {"ticker": "LMT",   "name": "Lockheed Martin",                 "sector": "Industrials"},
    {"ticker": "NOC",   "name": "Northrop Grumman",                "sector": "Industrials"},
    {"ticker": "GD",    "name": "General Dynamics",                "sector": "Industrials"},
    {"ticker": "FDX",   "name": "FedEx Corp.",                     "sector": "Industrials"},
    {"ticker": "MMM",   "name": "3M Company",                      "sector": "Industrials"},
    {"ticker": "ETN",   "name": "Eaton Corp.",                     "sector": "Industrials"},
    {"ticker": "EMR",   "name": "Emerson Electric",                "sector": "Industrials"},
    {"ticker": "ITW",   "name": "Illinois Tool Works",             "sector": "Industrials"},
    {"ticker": "PH",    "name": "Parker Hannifin",                 "sector": "Industrials"},
    {"ticker": "AME",   "name": "AMETEK Inc.",                     "sector": "Industrials"},
    {"ticker": "CSX",   "name": "CSX Corp.",                       "sector": "Industrials"},
    {"ticker": "NSC",   "name": "Norfolk Southern",                "sector": "Industrials"},
    {"ticker": "UNP",   "name": "Union Pacific",                   "sector": "Industrials"},
    {"ticker": "WM",    "name": "Waste Management",                "sector": "Industrials"},
    {"ticker": "RSG",   "name": "Republic Services",               "sector": "Industrials"},
    # ── Materials ───────────────────────────────────────────────────────────
    {"ticker": "LIN",   "name": "Linde PLC",                       "sector": "Materials"},
    {"ticker": "APD",   "name": "Air Products & Chemicals",        "sector": "Materials"},
    {"ticker": "SHW",   "name": "Sherwin-Williams",                "sector": "Materials"},
    {"ticker": "FCX",   "name": "Freeport-McMoRan",                "sector": "Materials"},
    {"ticker": "NEM",   "name": "Newmont Corp.",                   "sector": "Materials"},
    {"ticker": "NUE",   "name": "Nucor Corp.",                     "sector": "Materials"},
    {"ticker": "ALB",   "name": "Albemarle Corp.",                 "sector": "Materials"},
    {"ticker": "CF",    "name": "CF Industries",                   "sector": "Materials"},
    {"ticker": "MOS",   "name": "The Mosaic Company",              "sector": "Materials"},
    {"ticker": "DD",    "name": "DuPont de Nemours",               "sector": "Materials"},
    # ── Real Estate ─────────────────────────────────────────────────────────
    {"ticker": "AMT",   "name": "American Tower",                  "sector": "Real Estate"},
    {"ticker": "PLD",   "name": "Prologis Inc.",                   "sector": "Real Estate"},
    {"ticker": "CCI",   "name": "Crown Castle",                    "sector": "Real Estate"},
    {"ticker": "EQIX",  "name": "Equinix Inc.",                    "sector": "Real Estate"},
    {"ticker": "PSA",   "name": "Public Storage",                  "sector": "Real Estate"},
    {"ticker": "DLR",   "name": "Digital Realty Trust",            "sector": "Real Estate"},
    {"ticker": "O",     "name": "Realty Income Corp.",             "sector": "Real Estate"},
    {"ticker": "WELL",  "name": "Welltower Inc.",                  "sector": "Real Estate"},
    {"ticker": "SPG",   "name": "Simon Property Group",            "sector": "Real Estate"},
    {"ticker": "VTR",   "name": "Ventas Inc.",                     "sector": "Real Estate"},
    # ── Utilities ───────────────────────────────────────────────────────────
    {"ticker": "NEE",   "name": "NextEra Energy",                  "sector": "Utilities"},
    {"ticker": "DUK",   "name": "Duke Energy",                     "sector": "Utilities"},
    {"ticker": "SO",    "name": "Southern Company",                "sector": "Utilities"},
    {"ticker": "D",     "name": "Dominion Energy",                 "sector": "Utilities"},
    {"ticker": "AEP",   "name": "American Electric Power",         "sector": "Utilities"},
    {"ticker": "EXC",   "name": "Exelon Corp.",                    "sector": "Utilities"},
    {"ticker": "PCG",   "name": "PG&E Corp.",                      "sector": "Utilities"},
    {"ticker": "XEL",   "name": "Xcel Energy",                     "sector": "Utilities"},
    {"ticker": "WEC",   "name": "WEC Energy Group",                "sector": "Utilities"},
    {"ticker": "ES",    "name": "Eversource Energy",               "sector": "Utilities"},
    # ── ETFs / Indices (for benchmark comparison) ───────────────────────────
    {"ticker": "SPY",   "name": "SPDR S&P 500 ETF",                "sector": "ETF"},
    {"ticker": "QQQ",   "name": "Nasdaq-100 ETF",                  "sector": "ETF"},
    {"ticker": "IWM",   "name": "Russell 2000 ETF",                "sector": "ETF"},
    {"ticker": "TLT",   "name": "iShares 20+ Year Treasury",       "sector": "ETF"},
    {"ticker": "GLD",   "name": "SPDR Gold Shares",                "sector": "ETF"},
]

# ─── Dynamic registry (tickers outside the S&P 500) ─────────────────────────
_dynamic_registry: dict[str, dict] = {}


class Universe:
    """
    Manages the investment universe.

    The S&P 500 list is baked in at module level (_SP500).
    Any ticker can be registered dynamically — it is treated
    identically to the original 500 by the strategy engine.
    """

    def __init__(self, tickers: Optional[list[str]] = None):
        """
        Parameters
        ----------
        tickers : list[str] | None
            If None → use the full embedded universe (S&P 500 + registered).
            Otherwise → filter to only these tickers.
        """
        self._base: dict[str, dict] = {row["ticker"]: row for row in _SP500}
        self._extra: dict[str, dict] = dict(_dynamic_registry)

        if tickers:
            self._active = self._resolve(tickers)
        else:
            self._active = {**self._base, **self._extra}

    # ── Public API ──────────────────────────────────────────────────────────

    @property
    def tickers(self) -> list[str]:
        """All active tickers."""
        return list(self._active.keys())

    @property
    def sp500_tickers(self) -> list[str]:
        """Only tickers in the embedded S&P 500 list."""
        return [t for t in self._active if t in self._base]

    @property
    def dynamic_tickers(self) -> list[str]:
        """Only tickers that were dynamically registered."""
        return [t for t in self._active if t not in self._base]

    def sector(self, ticker: str) -> str:
        """Return the sector for a ticker (or 'Unknown')."""
        row = self._active.get(ticker.upper())
        return row["sector"] if row else "Unknown"

    def info(self, ticker: str) -> dict:
        """Full metadata dict for a ticker."""
        return self._active.get(ticker.upper(), {
            "ticker": ticker.upper(),
            "name": ticker.upper(),
            "sector": "Unknown",
        })

    def tickers_by_sector(self, sector: str) -> list[str]:
        """All active tickers in a given sector."""
        return [t for t, r in self._active.items() if r["sector"] == sector]

    def sectors(self) -> list[str]:
        """List of all unique sectors in the active universe."""
        return sorted({r["sector"] for r in self._active.values()})

    # ── Module-level dynamic registration ───────────────────────────────────

    @staticmethod
    def register(ticker: str, name: str = "", sector: str = "Unknown"):
        """
        Register a new ticker globally so it's available to all Universe instances.

        Parameters
        ----------
        ticker : str    e.g. "RKLB"
        name   : str    e.g. "Rocket Lab USA"
        sector : str    e.g. "Industrials"

        This is the only change needed to add a company outside the S&P 500.
        No retraining. No pipeline changes.
        """
        _dynamic_registry[ticker.upper()] = {
            "ticker": ticker.upper(),
            "name": name or ticker.upper(),
            "sector": sector,
        }
        print(f"[UNIVERSE] Registered new ticker: {ticker.upper()} ({sector})")

    @staticmethod
    def total_available() -> int:
        """Total tickers available (S&P 500 + dynamic)."""
        return len(_SP500) + len(_dynamic_registry)

    # ── Private helpers ──────────────────────────────────────────────────────

    def _resolve(self, tickers: list[str]) -> dict[str, dict]:
        """
        Resolve a list of ticker strings.
        Unknown tickers are auto-registered as 'Unknown' sector.
        """
        result = {}
        for t in tickers:
            t_up = t.strip().upper()
            if t_up in self._base:
                result[t_up] = self._base[t_up]
            elif t_up in self._extra:
                result[t_up] = self._extra[t_up]
            else:
                # Auto-register unknown tickers — no crash, no retraining
                entry = {"ticker": t_up, "name": t_up, "sector": "Unknown"}
                _dynamic_registry[t_up] = entry
                self._extra[t_up] = entry
                result[t_up] = entry
                print(f"[UNIVERSE] Auto-registered unknown ticker: {t_up}")
        return result

    def __len__(self) -> int:
        return len(self._active)

    def __repr__(self) -> str:
        return f"<Universe tickers={len(self._active)} sp500={len(self.sp500_tickers)} dynamic={len(self.dynamic_tickers)}>"
