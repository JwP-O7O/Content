"""Twitter/X API integration."""

from typing import Optional

import tweepy
from loguru import logger


class TwitterAPI:
    """
    Twitter/X API client for posting content and monitoring sentiment.
    """

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        access_token: str,
        access_token_secret: str,
        bearer_token: str,
    ):
        """
        Initialize the Twitter API client.

        Args:
            api_key: Twitter API key
            api_secret: Twitter API secret
            access_token: Access token
            access_token_secret: Access token secret
            bearer_token: Bearer token for API v2
        """
        # Initialize v1.1 API (for posting)
        auth = tweepy.OAuthHandler(api_key, api_secret)
        auth.set_access_token(access_token, access_token_secret)
        self.api_v1 = tweepy.API(auth)

        # Initialize v2 API (for searching and advanced features)
        self.client = tweepy.Client(
            bearer_token=bearer_token,
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_token_secret,
        )

        logger.info("Twitter API initialized")

    def post_tweet(self, text: str) -> Optional[dict]:
        """
        Post a single tweet.

        Args:
            text: Tweet text (max 280 characters)

        Returns:
            Dictionary with tweet data or None if failed
        """
        try:
            response = self.client.create_tweet(text=text)
            logger.info(f"Tweet posted successfully: {response.data['id']}")
            return {
                "id": response.data["id"],
                "text": text,
                "url": f"https://twitter.com/i/status/{response.data['id']}",
            }
        except Exception as e:
            logger.error(f"Failed to post tweet: {e}")
            return None

    def post_thread(self, tweets: list[str]) -> Optional[list[dict]]:
        """
        Post a thread of tweets.

        Args:
            tweets: List of tweet texts

        Returns:
            List of tweet data dictionaries or None if failed
        """
        try:
            posted_tweets = []
            previous_tweet_id = None

            for i, text in enumerate(tweets):
                if previous_tweet_id:
                    response = self.client.create_tweet(
                        text=text, in_reply_to_tweet_id=previous_tweet_id
                    )
                else:
                    response = self.client.create_tweet(text=text)

                tweet_data = {
                    "id": response.data["id"],
                    "text": text,
                    "url": f"https://twitter.com/i/status/{response.data['id']}",
                    "position": i + 1,
                }
                posted_tweets.append(tweet_data)
                previous_tweet_id = response.data["id"]

                logger.info(f"Thread tweet {i+1}/{len(tweets)} posted")

            return posted_tweets

        except Exception as e:
            logger.error(f"Failed to post thread: {e}")
            return None

    def search_tweets(self, query: str, max_results: int = 100) -> list[dict]:
        """
        Search for tweets matching a query.

        Args:
            query: Search query
            max_results: Maximum number of tweets to return

        Returns:
            List of tweet dictionaries
        """
        try:
            tweets = self.client.search_recent_tweets(
                query=query,
                max_results=max_results,
                tweet_fields=["created_at", "public_metrics", "author_id"],
            )

            if not tweets.data:
                return []

            return [
                {
                    "id": tweet.id,
                    "text": tweet.text,
                    "created_at": tweet.created_at,
                    "likes": tweet.public_metrics["like_count"],
                    "retweets": tweet.public_metrics["retweet_count"],
                    "replies": tweet.public_metrics["reply_count"],
                }
                for tweet in tweets.data
            ]

        except Exception as e:
            logger.error(f"Failed to search tweets: {e}")
            return []

    def get_sentiment_for_asset(self, asset: str, max_results: int = 100) -> dict:
        """
        Get sentiment data for a specific cryptocurrency.

        Args:
            asset: Cryptocurrency symbol (e.g., BTC, ETH)
            max_results: Maximum tweets to analyze

        Returns:
            Dictionary with sentiment analysis
        """
        # Search for tweets mentioning the asset
        query = f"${asset} OR #{asset} -is:retweet lang:en"
        tweets = self.search_tweets(query, max_results)

        if not tweets:
            return {"asset": asset, "sentiment_score": 0, "volume": 0, "tweets": []}

        # Simple sentiment calculation based on engagement
        total_engagement = sum(t["likes"] + t["retweets"] * 2 + t["replies"] for t in tweets)

        return {
            "asset": asset,
            "volume": len(tweets),
            "total_engagement": total_engagement,
            "avg_engagement": total_engagement / len(tweets) if tweets else 0,
            "tweets": tweets[:10],  # Sample of top tweets
        }
