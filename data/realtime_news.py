"""
Real-time news fetcher using Finnhub API and NewsAPI.
Falls back to mock data if API keys are missing or requests fail.
"""

import requests
from datetime import datetime, timedelta
from config.config import FINNHUB_API_KEY, FINNHUB_BASE_URL, NEWSAPI_KEY, NEWSAPI_HEADLINES_URL, NEWSAPI_EVERYTHING_URL


def fetch_finnhub_news(category: str = "general") -> list[dict]:
    """
    Fetch real-time market news from Finnhub.
    
    Args:
        category: News category - 'general', 'forex', 'crypto', 'merger'
    
    Returns:
        List of news dicts with source, headline, timestamp, category
    """
    if not FINNHUB_API_KEY:
        print("[WARNING] FINNHUB_API_KEY not set. Use mock data or set key in .env")
        return []

    try:
        url = f"{FINNHUB_BASE_URL}/news"
        params = {
            "category": category,
            "token": FINNHUB_API_KEY,
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        raw_news = response.json()

        # Normalize to our standard format
        news = []
        for item in raw_news[:20]:  # Limit to 20 headlines
            news.append({
                "source": item.get("source", "Unknown"),
                "headline": item.get("headline", ""),
                "timestamp": datetime.fromtimestamp(
                    item.get("datetime", 0)
                ).strftime("%Y-%m-%d %H:%M"),
                "category": item.get("category", category),
                "url": item.get("url", ""),
            })
        return news

    except requests.RequestException as e:
        print(f"[ERROR] Finnhub news fetch failed: {e}")
        return []


def fetch_company_news(ticker: str, days_back: int = 7) -> list[dict]:
    """
    Fetch company-specific news from Finnhub.
    
    Args:
        ticker: Stock symbol (e.g., 'AAPL' or 'TCS.NS')
        days_back: How many days back to fetch news
    
    Returns:
        List of news dicts for the specific company
    """
    if not FINNHUB_API_KEY:
        return []

    # Finnhub uses NSE:TCS format for Indian stocks, not TCS.NS
    if ticker.endswith(".NS"):
        finnhub_symbol = "NSE:" + ticker[:-3]
    elif ticker.endswith(".BO") or ticker.endswith(".BSE"):
        finnhub_symbol = "BSE:" + ticker.split(".")[0]
    else:
        finnhub_symbol = ticker

    try:
        today = datetime.now()
        from_date = (today - timedelta(days=days_back)).strftime("%Y-%m-%d")
        to_date = today.strftime("%Y-%m-%d")

        url = f"{FINNHUB_BASE_URL}/company-news"
        params = {
            "symbol": finnhub_symbol,
            "from": from_date,
            "to": to_date,
            "token": FINNHUB_API_KEY,
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        raw_news = response.json()

        news = []
        for item in raw_news[:10]:
            news.append({
                "source": item.get("source", "Unknown"),
                "headline": item.get("headline", ""),
                "timestamp": datetime.fromtimestamp(
                    item.get("datetime", 0)
                ).strftime("%Y-%m-%d %H:%M"),
                "category": "company",
                "ticker": ticker,
                "url": item.get("url", ""),
            })
        return news

    except requests.RequestException as e:
        print(f"[ERROR] Finnhub company news fetch for {ticker} failed: {e}")
        return []


# ═══════════════════════════════════════════════════════════════
#  NewsAPI — Top Headlines & Keyword Search
# ═══════════════════════════════════════════════════════════════

def fetch_newsapi_headlines(country: str = "us", category: str = "business", max_items: int = 25) -> list[dict]:
    """
    Fetch top business headlines from NewsAPI.
    
    Args:
        country: 2-letter country code (default 'us')
        category: business, technology, general, science, health
        max_items: Max articles to return
    
    Returns:
        List of news dicts in standard format
    """
    if not NEWSAPI_KEY:
        print("[WARNING] NEWSAPI_KEY not set. Skipping NewsAPI headlines.")
        return []

    try:
        params = {
            "country": country,
            "category": category,
            "pageSize": max_items,
            "apiKey": NEWSAPI_KEY,
        }
        response = requests.get(NEWSAPI_HEADLINES_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get("status") != "ok":
            print(f"[WARNING] NewsAPI headlines returned: {data.get('message', 'unknown error')}")
            return []

        news = []
        for article in data.get("articles", []):
            title = article.get("title", "")
            # Skip removed/empty articles
            if not title or title == "[Removed]":
                continue
            news.append({
                "source": article.get("source", {}).get("name", "Unknown"),
                "headline": title,
                "timestamp": _parse_newsapi_date(article.get("publishedAt", "")),
                "category": category,
                "url": article.get("url", ""),
                "description": article.get("description", ""),
            })
        print(f"       [NewsAPI] Fetched {len(news)} headlines ({category})")
        return news

    except requests.RequestException as e:
        print(f"[ERROR] NewsAPI headlines fetch failed: {e}")
        return []


def fetch_newsapi_for_ticker(ticker: str, days_back: int = 3, max_items: int = 10, company_name: str = "") -> list[dict]:
    """
    Fetch news articles about a specific ticker/company from NewsAPI.
    
    Args:
        ticker: Stock symbol (e.g., 'AAPL' or 'TCS.NS')
        days_back: How many days back to search
        max_items: Max articles to return
        company_name: Full company name for better search (especially for NSE stocks)
    
    Returns:
        List of news dicts for the specific ticker
    """
    if not NEWSAPI_KEY:
        return []

    # Strip exchange suffixes for clean symbol
    base = ticker.replace(".NS", "").replace(".BO", "").replace(".BSE", "")

    # Map common tickers to company names for better search results
    us_ticker_map = {
        "AAPL": "Apple",
        "GOOGL": "Google OR Alphabet",
        "MSFT": "Microsoft",
        "AMZN": "Amazon",
        "TSLA": "Tesla",
        "NVDA": "NVIDIA",
        "META": "Meta Platforms OR Facebook",
        "SPY": "S&P 500",
        "TLT": "Treasury bonds",
    }

    if company_name:
        # Use the company name for NSE/BSE stocks — much better recall
        # e.g. "Tata Consultancy Services" stock NSE India
        query = f'"{company_name}" stock'
    elif base in us_ticker_map:
        query = us_ticker_map[base]
    else:
        # Generic fallback: try company name from universe if available
        try:
            from backtest.universe_india import IndiaUniverse
            name = IndiaUniverse().name(ticker)
            if name and name != ticker:
                query = f'"{name}" stock'
            else:
                query = f"{base} stock India"
        except Exception:
            query = f"{base} stock"

    try:
        from_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
        params = {
            "q": query,
            "from": from_date,
            "language": "en",
            "sortBy": "relevancy",
            "pageSize": max_items,
            "apiKey": NEWSAPI_KEY,
        }
        response = requests.get(NEWSAPI_EVERYTHING_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get("status") != "ok":
            return []

        news = []
        for article in data.get("articles", []):
            title = article.get("title", "")
            if not title or title == "[Removed]":
                continue
            news.append({
                "source": article.get("source", {}).get("name", "Unknown"),
                "headline": title,
                "timestamp": _parse_newsapi_date(article.get("publishedAt", "")),
                "category": "company",
                "ticker": ticker,
                "url": article.get("url", ""),
                "description": article.get("description", ""),
            })
        return news

    except requests.RequestException as e:
        print(f"[ERROR] NewsAPI search for {ticker} failed: {e}")
        return []


def _parse_newsapi_date(date_str: str) -> str:
    """Parse ISO 8601 date from NewsAPI to our standard format."""
    if not date_str:
        return datetime.now().strftime("%Y-%m-%d %H:%M")
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M")
    except (ValueError, TypeError):
        return datetime.now().strftime("%Y-%m-%d %H:%M")
