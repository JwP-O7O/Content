"""Exchange API integration for market data."""

from datetime import datetime, timezone
from typing import Optional

import aiohttp
from loguru import logger


class ExchangeAPI:
    """
    Interface for fetching cryptocurrency market data.

    Currently supports Binance, but can be extended for other exchanges.
    """

    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        """
        Initialize the Exchange API client.

        Args:
            api_key: Optional API key for authenticated endpoints
            api_secret: Optional API secret for authenticated endpoints
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://api.binance.com/api/v3"

    async def get_ticker_24h(self, symbol: str = "BTCUSDT") -> dict:
        """
        Get 24-hour price change statistics.

        Args:
            symbol: Trading pair symbol (e.g., BTCUSDT)

        Returns:
            Dictionary with price, volume, and change data
        """
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/ticker/24hr"
                params = {"symbol": symbol}

                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "symbol": symbol,
                            "price": float(data["lastPrice"]),
                            "volume_24h": float(data["volume"]),
                            "price_change_24h": float(data["priceChangePercent"]),
                            "high_24h": float(data["highPrice"]),
                            "low_24h": float(data["lowPrice"]),
                            "timestamp": datetime.now(tz=timezone.utc),
                            "raw_data": data
                        }
                    logger.error(f"Failed to fetch ticker for {symbol}: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching ticker data: {e}")
            return None

    async def get_top_gainers_losers(self, limit: int = 10) -> dict[str, list[dict]]:
        """
        Get top gainers and losers in the last 24 hours.

        Args:
            limit: Number of top gainers/losers to return

        Returns:
            Dictionary with 'gainers' and 'losers' lists
        """
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/ticker/24hr"

                async with session.get(url) as response:
                    if response.status == 200:
                        all_tickers = await response.json()

                        # Filter for USDT pairs and valid data
                        usdt_pairs = [
                            t for t in all_tickers
                            if t["symbol"].endswith("USDT")
                            and float(t["volume"]) > 1000000  # Min volume filter
                        ]

                        # Sort by price change percentage
                        sorted_tickers = sorted(
                            usdt_pairs,
                            key=lambda x: float(x["priceChangePercent"]),
                            reverse=True
                        )

                        gainers = [
                            {
                                "symbol": t["symbol"],
                                "price": float(t["lastPrice"]),
                                "change_percent": float(t["priceChangePercent"]),
                                "volume": float(t["volume"])
                            }
                            for t in sorted_tickers[:limit]
                        ]

                        losers = [
                            {
                                "symbol": t["symbol"],
                                "price": float(t["lastPrice"]),
                                "change_percent": float(t["priceChangePercent"]),
                                "volume": float(t["volume"])
                            }
                            for t in sorted_tickers[-limit:]
                        ]

                        return {
                            "gainers": gainers,
                            "losers": losers,
                            "timestamp": datetime.now(tz=timezone.utc)
                        }
                    logger.error(f"Failed to fetch all tickers: {response.status}")
                    return {"gainers": [], "losers": []}
        except Exception as e:
            logger.error(f"Error fetching gainers/losers: {e}")
            return {"gainers": [], "losers": []}

    async def get_klines(
        self,
        symbol: str = "BTCUSDT",
        interval: str = "1h",
        limit: int = 100
    ) -> list[dict]:
        """
        Get candlestick/kline data for technical analysis.

        Args:
            symbol: Trading pair symbol
            interval: Kline interval (1m, 5m, 1h, 1d, etc.)
            limit: Number of klines to return

        Returns:
            List of kline data dictionaries
        """
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/klines"
                params = {
                    "symbol": symbol,
                    "interval": interval,
                    "limit": limit
                }

                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        klines = await response.json()
                        return [
                            {
                                "timestamp": datetime.fromtimestamp(k[0] / 1000, tz=timezone.utc),
                                "open": float(k[1]),
                                "high": float(k[2]),
                                "low": float(k[3]),
                                "close": float(k[4]),
                                "volume": float(k[5])
                            }
                            for k in klines
                        ]
                    logger.error(f"Failed to fetch klines: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error fetching klines: {e}")
            return []
