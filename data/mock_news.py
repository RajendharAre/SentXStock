"""
Mock news headlines for fallback / demo mode.
"""

from datetime import datetime


def get_mock_news() -> list[dict]:
    """Return a list of mock financial news headlines."""
    return [
        {
            "source": "Reuters",
            "headline": "Tech stocks surge as AI chip demand hits record highs",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "category": "technology",
        },
        {
            "source": "Bloomberg",
            "headline": "Federal Reserve signals potential rate cuts in upcoming quarter",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "category": "economy",
        },
        {
            "source": "CNBC",
            "headline": "Apple reports record quarterly revenue beating analyst expectations",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "category": "earnings",
        },
        {
            "source": "Financial Times",
            "headline": "Oil prices drop sharply amid global demand concerns",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "category": "commodities",
        },
        {
            "source": "Wall Street Journal",
            "headline": "Semiconductor shortage eases as new fabs come online",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "category": "technology",
        },
        {
            "source": "MarketWatch",
            "headline": "Consumer confidence index rises to 18-month high",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "category": "economy",
        },
        {
            "source": "Reuters",
            "headline": "Tesla deliveries miss expectations amid increasing competition",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "category": "automotive",
        },
        {
            "source": "Bloomberg",
            "headline": "Gold prices climb as investors seek safe-haven assets",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "category": "commodities",
        },
        {
            "source": "CNBC",
            "headline": "Microsoft Azure revenue growth accelerates cloud dominance",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "category": "technology",
        },
        {
            "source": "Financial Times",
            "headline": "Banking sector faces pressure from rising default rates",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "category": "finance",
        },
    ]
