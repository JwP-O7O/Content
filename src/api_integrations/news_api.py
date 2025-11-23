"""News API integration for crypto news."""

import aiohttp
import feedparser
from typing import List, Dict
from datetime import datetime, timedelta
from loguru import logger


class NewsAPI:
    """
    Fetch cryptocurrency news from various sources.

    Uses RSS feeds and public APIs to gather news articles.
    """

    def __init__(self):
        """Initialize the News API client."""
        self.rss_feeds = [
            "https://cointelegraph.com/rss",
            "https://www.coindesk.com/arc/outboundfeeds/rss/",
            "https://cryptonews.com/news/feed/",
            "https://decrypt.co/feed",
        ]

    async def fetch_latest_news(self, max_articles: int = 20) -> List[Dict]:
        """
        Fetch the latest crypto news from multiple sources.

        Args:
            max_articles: Maximum number of articles to return

        Returns:
            List of news article dictionaries
        """
        all_articles = []

        for feed_url in self.rss_feeds:
            try:
                feed = feedparser.parse(feed_url)

                for entry in feed.entries[:max_articles // len(self.rss_feeds)]:
                    article = {
                        "title": entry.get("title", ""),
                        "url": entry.get("link", ""),
                        "source": feed.feed.get("title", "Unknown"),
                        "published_at": self._parse_date(entry.get("published")),
                        "summary": entry.get("summary", ""),
                        "content": entry.get("content", [{}])[0].get("value", "")
                        if entry.get("content")
                        else entry.get("description", "")
                    }
                    all_articles.append(article)

            except Exception as e:
                logger.error(f"Error fetching from {feed_url}: {e}")
                continue

        # Sort by published date
        all_articles.sort(key=lambda x: x["published_at"], reverse=True)

        return all_articles[:max_articles]

    def _parse_date(self, date_string: str) -> datetime:
        """
        Parse various date formats to datetime.

        Args:
            date_string: Date string in various formats

        Returns:
            Datetime object
        """
        try:
            from dateutil import parser
            return parser.parse(date_string)
        except:
            return datetime.utcnow()

    async def search_news(self, keyword: str, days_back: int = 7) -> List[Dict]:
        """
        Search for news articles containing a specific keyword.

        Args:
            keyword: Keyword to search for
            days_back: How many days back to search

        Returns:
            List of matching articles
        """
        all_news = await self.fetch_latest_news(max_articles=50)
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)

        matching_articles = [
            article for article in all_news
            if keyword.lower() in article["title"].lower()
            or keyword.lower() in article["summary"].lower()
            and article["published_at"] >= cutoff_date
        ]

        return matching_articles
