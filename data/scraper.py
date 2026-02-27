"""
BeautifulSoup web scraper for financial news headlines.
Scrapes publicly available financial news sites as a bonus data source.
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime


def scrape_headlines(url: str = "https://finance.yahoo.com/news/", max_headlines: int = 10) -> list[dict]:
    """
    Scrape news headlines from a financial news page using BeautifulSoup.
    
    Args:
        url: The URL to scrape headlines from
        max_headlines: Maximum number of headlines to return
    
    Returns:
        List of headline dicts
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        headlines = []

        # Try common headline selectors
        selectors = ["h3", "h2.title", "a[data-test-id='article-link']", ".news-title", "h3 a"]
        for selector in selectors:
            elements = soup.select(selector)
            for el in elements:
                text = el.get_text(strip=True)
                if text and len(text) > 15:  # Filter out short non-headline text
                    headlines.append({
                        "source": "Web Scrape",
                        "headline": text,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "category": "scraped",
                        "url": url,
                    })
                if len(headlines) >= max_headlines:
                    break
            if headlines:
                break

        return headlines[:max_headlines]

    except Exception as e:
        print(f"[WARNING] Scraping failed for {url}: {e}")
        return []


def scrape_reddit_titles(subreddit: str = "wallstreetbets", max_posts: int = 10) -> list[dict]:
    """
    Scrape post titles from a Reddit subreddit (using old.reddit.com for easier parsing).
    
    Args:
        subreddit: Subreddit name
        max_posts: Max posts to return
    
    Returns:
        List of post dicts
    """
    try:
        url = f"https://old.reddit.com/r/{subreddit}/hot/"
        headers = {"User-Agent": "SentimentAgent/1.0 (research project)"}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        posts = []

        for link in soup.select("a.title"):
            text = link.get_text(strip=True)
            if text and len(text) > 10:
                posts.append({
                    "platform": "Reddit",
                    "user": f"r/{subreddit}",
                    "post": text,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "ticker": "",
                })
            if len(posts) >= max_posts:
                break

        return posts

    except Exception as e:
        print(f"[WARNING] Reddit scraping failed for r/{subreddit}: {e}")
        return []
