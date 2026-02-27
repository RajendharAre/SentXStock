"""
Real-time social sentiment fetcher.
Uses Finnhub social sentiment API + Reddit JSON API.
"""

import requests
from datetime import datetime
from config.config import FINNHUB_API_KEY, FINNHUB_BASE_URL


def fetch_finnhub_social_sentiment(ticker: str) -> list[dict]:
    """
    Fetch social sentiment data for a ticker from Finnhub.
    Returns aggregated social media sentiment (Reddit + Twitter mentions).
    
    Args:
        ticker: Stock symbol (e.g., 'AAPL')
    
    Returns:
        List of social sentiment dicts
    """
    if not FINNHUB_API_KEY:
        return []

    try:
        url = f"{FINNHUB_BASE_URL}/stock/social-sentiment"
        params = {"symbol": ticker, "from": "2026-02-20", "to": "2026-02-28", "token": FINNHUB_API_KEY}
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        posts = []
        for source_key in ["reddit", "twitter"]:
            items = data.get(source_key, [])
            for item in items[:5]:
                mention = item.get("mention", 0)
                pos = item.get("positiveScore", 0)
                neg = item.get("negativeScore", 0)
                score_text = "positive" if pos > neg else "negative" if neg > pos else "neutral"
                posts.append({
                    "platform": source_key.capitalize(),
                    "user": f"{source_key}_aggregate",
                    "post": f"${ticker} social sentiment: {mention} mentions, trending {score_text} (pos:{pos:.0f} neg:{neg:.0f})",
                    "timestamp": item.get("atTime", datetime.now().isoformat()),
                    "ticker": ticker,
                })
        return posts

    except requests.RequestException as e:
        print(f"[WARNING] Finnhub social sentiment for {ticker} failed: {e}")
        return []


def fetch_reddit_posts(subreddit: str = "wallstreetbets", limit: int = 10) -> list[dict]:
    """
    Fetch posts from Reddit using the public JSON API (no auth needed).
    
    Args:
        subreddit: Subreddit name
        limit: Max posts to fetch
    
    Returns:
        List of social post dicts
    """
    try:
        url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit={limit}"
        headers = {"User-Agent": "SentimentAgent/1.0 (research project)"}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()

        posts = []
        for child in data.get("data", {}).get("children", []):
            post_data = child.get("data", {})
            title = post_data.get("title", "")
            if title and len(title) > 10:
                posts.append({
                    "platform": "Reddit",
                    "user": f"u/{post_data.get('author', 'unknown')}",
                    "post": title,
                    "timestamp": datetime.fromtimestamp(
                        post_data.get("created_utc", 0)
                    ).strftime("%Y-%m-%d %H:%M"),
                    "ticker": "",
                    "subreddit": subreddit,
                    "upvotes": post_data.get("ups", 0),
                })
        return posts

    except requests.RequestException as e:
        print(f"[WARNING] Reddit fetch for r/{subreddit} failed: {e}")
        return []


def fetch_social_multiple(tickers: list[str]) -> list[dict]:
    """
    Fetch social data from Reddit finance subreddits.
    
    Args:
        tickers: List of stock symbols (used for context)
    
    Returns:
        Combined list of social posts
    """
    all_posts = []

    # Reddit finance subreddits
    for sub in ["wallstreetbets", "stocks", "investing"]:
        posts = fetch_reddit_posts(sub, limit=8)
        all_posts.extend(posts)

    return all_posts
