"""
Mock social media posts for fallback / demo mode.
"""

from datetime import datetime


def get_mock_social_posts() -> list[dict]:
    """Return a list of mock social media posts about stocks."""
    return [
        {
            "platform": "Twitter",
            "user": "@bullTrader99",
            "post": "$AAPL just crushed earnings! Loading up more shares 🚀🚀",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "ticker": "AAPL",
        },
        {
            "platform": "Reddit",
            "user": "u/WallStreetAnalyst",
            "post": "GOOGL is undervalued at current levels. PE ratio looks attractive compared to peers.",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "ticker": "GOOGL",
        },
        {
            "platform": "StockTwits",
            "user": "TechBear2026",
            "post": "$TSLA overvalued, competition is crushing them. Selling my position.",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "ticker": "TSLA",
        },
        {
            "platform": "Reddit",
            "user": "u/DiamondHands420",
            "post": "Market crash incoming. Moving everything to cash and gold. The bubble is about to pop.",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "ticker": "SPY",
        },
        {
            "platform": "Twitter",
            "user": "@InvestorDaily",
            "post": "$MSFT AI integration is game-changing. This stock is going to $500 easily.",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "ticker": "MSFT",
        },
        {
            "platform": "StockTwits",
            "user": "NeutralNick",
            "post": "$SPY trading sideways. No clear direction. Staying on the sidelines for now.",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "ticker": "SPY",
        },
        {
            "platform": "Reddit",
            "user": "u/ValueInvestor101",
            "post": "AMZN AWS growth is slowing. Bearish short term but long term hold.",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "ticker": "AMZN",
        },
        {
            "platform": "Twitter",
            "user": "@ChipBull",
            "post": "$NVDA is the backbone of AI revolution. Not selling a single share 💎🙌",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "ticker": "NVDA",
        },
        {
            "platform": "StockTwits",
            "user": "BearishBob",
            "post": "Fed is going to wreck the market. Rates staying higher for longer. $TLT calls.",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "ticker": "TLT",
        },
        {
            "platform": "Reddit",
            "user": "u/TechOptimist",
            "post": "Incredible quarter for $META. Metaverse spending is finally paying off. Super bullish!",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "ticker": "META",
        },
    ]
