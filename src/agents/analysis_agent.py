"""AnalysisAgent - Analyzes market data and generates insights."""

import asyncio
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import pandas as pd
from anthropic import Anthropic

from src.agents.base_agent import BaseAgent
from src.database.connection import get_db
from src.database.models import (
    MarketData, NewsArticle, SentimentData,
    Insight, InsightType
)
from src.api_integrations.exchange_api import ExchangeAPI
from config.config import settings
from src.utils.llm_client import llm_client


class AnalysisAgent(BaseAgent):
    """
    The Analysis Agent interprets market data and generates actionable insights.

    Responsibilities:
    - Perform technical analysis on price data
    - Analyze news sentiment and impact
    - Use LLMs to generate high-quality insights
    - Assign confidence scores to insights
    """

    def __init__(self):
        """Initialize the AnalysisAgent."""
        super().__init__("AnalysisAgent")

        # Initialize LLM client (Use the shared client with failover)
        self.llm_client = llm_client
        self.exchange_api = ExchangeAPI()

        # Analysis parameters
        self.min_confidence = 0.5  # Minimum confidence to save insight
        self.lookback_hours = 24  # How far back to look for data

    async def execute(self) -> Dict:
        """
        Execute the analysis process.

        Returns:
            Dictionary with analysis results
        """
        self.log_info("Starting market analysis...")

        results = {
            "insights_generated": 0,
            "high_confidence_insights": 0,
            "assets_analyzed": 0,
            "errors": []
        }

        try:
            # Get list of assets to analyze from recent market data
            assets = await self._get_active_assets()
            results["assets_analyzed"] = len(assets)

            # Analyze each asset
            for asset in assets:
                try:
                    insights = await self._analyze_asset(asset)
                    results["insights_generated"] += len(insights)
                    results["high_confidence_insights"] += sum(
                        1 for i in insights if i.confidence >= 0.8
                    )
                except Exception as e:
                    self.log_error(f"Error analyzing {asset}: {e}")
                    results["errors"].append(f"{asset}: {str(e)}")

            self.log_info(
                f"Analysis complete: {results['insights_generated']} insights generated, "
                f"{results['high_confidence_insights']} high confidence"
            )

        except Exception as e:
            self.log_error(f"Analysis execution error: {e}")
            results["errors"].append(str(e))

        return results

    async def _get_active_assets(self) -> List[str]:
        """
        Get list of assets that have recent market data.

        Returns:
            List of asset symbols
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=self.lookback_hours)

        with get_db() as db:
            assets = db.query(MarketData.asset).filter(
                MarketData.timestamp >= cutoff_time
            ).distinct().all()

            return [a[0] for a in assets]

    async def _analyze_asset(self, asset: str) -> List[Insight]:
        """
        Perform comprehensive analysis on a specific asset.

        Args:
            asset: Asset symbol (e.g., BTC)

        Returns:
            List of generated insights
        """
        self.log_info(f"Analyzing {asset}...")

        insights = []

        # Gather data for analysis
        market_data = await self._get_market_data(asset)
        news_data = await self._get_news_data(asset)
        sentiment_data = await self._get_sentiment_data(asset)

        # Perform different types of analysis
        analysis_tasks = [
            self._technical_analysis(asset, market_data),
            self._news_impact_analysis(asset, news_data),
            self._sentiment_analysis(asset, sentiment_data)
        ]

        analysis_results = await asyncio.gather(*analysis_tasks, return_exceptions=True)

        # Save insights to database
        with get_db() as db:
            for result in analysis_results:
                if isinstance(result, list):
                    for insight in result:
                        if insight.confidence >= self.min_confidence:
                            db.add(insight)
                            insights.append(insight)

            db.commit()

        return insights

    async def _get_market_data(self, asset: str) -> pd.DataFrame:
        """Get recent market data for an asset as a DataFrame."""
        cutoff_time = datetime.utcnow() - timedelta(hours=self.lookback_hours)

        with get_db() as db:
            data = db.query(MarketData).filter(
                MarketData.asset == asset,
                MarketData.timestamp >= cutoff_time
            ).order_by(MarketData.timestamp).all()

            if not data:
                return pd.DataFrame()

            return pd.DataFrame([
                {
                    "timestamp": d.timestamp,
                    "price": d.price,
                    "volume": d.volume_24h,
                    "change": d.price_change_24h
                }
                for d in data
            ])

    async def _get_news_data(self, asset: str) -> List[NewsArticle]:
        """Get recent news mentioning the asset."""
        cutoff_time = datetime.utcnow() - timedelta(hours=self.lookback_hours)

        with get_db() as db:
            news = db.query(NewsArticle).filter(
                NewsArticle.published_at >= cutoff_time
            ).all()

            # Filter for articles mentioning the asset
            relevant_news = [
                n for n in news
                if asset.lower() in n.title.lower()
                or asset.lower() in n.summary.lower()
            ]

            return relevant_news

    async def _get_sentiment_data(self, asset: str) -> List[SentimentData]:
        """Get recent sentiment data for the asset."""
        cutoff_time = datetime.utcnow() - timedelta(hours=self.lookback_hours)

        with get_db() as db:
            sentiment = db.query(SentimentData).filter(
                SentimentData.asset == asset,
                SentimentData.timestamp >= cutoff_time
            ).all()

            return sentiment

    async def _technical_analysis(
        self,
        asset: str,
        market_data: pd.DataFrame
    ) -> List[Insight]:
        """
        Perform technical analysis and generate insights.

        Args:
            asset: Asset symbol
            market_data: DataFrame with market data

        Returns:
            List of insights from technical analysis
        """
        insights = []

        if market_data.empty or len(market_data) < 10:
            return insights

        # Get latest data point
        latest = market_data.iloc[-1]
        price = latest["price"]
        change = latest["change"]
        volume = latest["volume"]

        # Calculate simple indicators
        avg_volume = market_data["volume"].mean()
        volume_ratio = volume / avg_volume if avg_volume > 0 else 1

        # Check for breakout (significant price change + high volume)
        if abs(change) > 5 and volume_ratio > 1.5:
            insight_type = InsightType.BREAKOUT if change > 0 else InsightType.BREAKDOWN

            # Use LLM to generate detailed analysis
            llm_analysis = await self._get_llm_analysis(
                asset=asset,
                insight_type=insight_type.value,
                data={
                    "price": price,
                    "change_24h": change,
                    "volume_ratio": volume_ratio,
                    "market_data": market_data.tail(20).to_dict('records')
                }
            )

            confidence = min(0.95, 0.6 + (abs(change) / 100) + (volume_ratio / 10))

            insight = Insight(
                type=insight_type,
                asset=asset,
                confidence=confidence,
                details={
                    "price": price,
                    "change_24h": change,
                    "volume_ratio": volume_ratio,
                    "llm_analysis": llm_analysis
                }
            )
            insights.append(insight)

        # Check for volume spike
        elif volume_ratio > 2:
            llm_analysis = await self._get_llm_analysis(
                asset=asset,
                insight_type="volume_spike",
                data={
                    "price": price,
                    "volume_ratio": volume_ratio,
                    "change_24h": change
                }
            )

            insight = Insight(
                type=InsightType.VOLUME_SPIKE,
                asset=asset,
                confidence=0.65 + min(0.3, volume_ratio / 20),
                details={
                    "volume_ratio": volume_ratio,
                    "price": price,
                    "llm_analysis": llm_analysis
                }
            )
            insights.append(insight)

        return insights

    async def _news_impact_analysis(
        self,
        asset: str,
        news_data: List[NewsArticle]
    ) -> List[Insight]:
        """
        Analyze news impact on the asset.

        Args:
            asset: Asset symbol
            news_data: List of relevant news articles

        Returns:
            List of insights from news analysis
        """
        insights = []

        if not news_data:
            return insights

        # If there are multiple news articles about the asset, it might be significant
        if len(news_data) >= 3:
            # Use LLM to analyze the news collectively
            news_summaries = [
                {"title": n.title, "summary": n.summary, "source": n.source}
                for n in news_data[:5]
            ]

            llm_analysis = await self._get_llm_analysis(
                asset=asset,
                insight_type="news_impact",
                data={"news_articles": news_summaries}
            )

            insight = Insight(
                type=InsightType.NEWS_IMPACT,
                asset=asset,
                confidence=0.7,
                details={
                    "news_count": len(news_data),
                    "articles": news_summaries,
                    "llm_analysis": llm_analysis
                }
            )
            insights.append(insight)

        return insights

    async def _sentiment_analysis(
        self,
        asset: str,
        sentiment_data: List[SentimentData]
    ) -> List[Insight]:
        """
        Analyze sentiment shifts for the asset.

        Args:
            asset: Asset symbol
            sentiment_data: List of sentiment data points

        Returns:
            List of insights from sentiment analysis
        """
        insights = []

        if len(sentiment_data) < 2:
            return insights

        # Compare latest sentiment to previous
        latest_volume = sentiment_data[-1].volume
        avg_volume = sum(s.volume for s in sentiment_data) / len(sentiment_data)

        # Significant increase in social media activity
        if latest_volume > avg_volume * 1.5:
            llm_analysis = await self._get_llm_analysis(
                asset=asset,
                insight_type="sentiment_shift",
                data={
                    "volume": latest_volume,
                    "avg_volume": avg_volume,
                    "platform": sentiment_data[-1].platform
                }
            )

            insight = Insight(
                type=InsightType.SENTIMENT_SHIFT,
                asset=asset,
                confidence=0.6,
                details={
                    "volume": latest_volume,
                    "volume_increase": (latest_volume / avg_volume - 1) * 100,
                    "platform": sentiment_data[-1].platform,
                    "llm_analysis": llm_analysis
                }
            )
            insights.append(insight)

        return insights

    async def _get_llm_analysis(
        self,
        asset: str,
        insight_type: str,
        data: Dict
    ) -> str:
        """
        Use LLM to generate detailed analysis.

        Args:
            asset: Asset symbol
            insight_type: Type of insight being analyzed
            data: Data to analyze

        Returns:
            LLM-generated analysis text
        """
        try:
            prompt = f"""You are a crypto market analyst. Analyze the following {insight_type} for {asset}.

Data:
{json.dumps(data, indent=2, default=str)}

Provide a concise, professional analysis (2-3 sentences) explaining:
1. What this means for the asset
2. Why this is significant
3. Potential implications

Be factual and avoid speculation. Focus on what the data shows."""

            return await self.llm_client.generate(
                prompt=prompt,
                model="gemini", # Default to Gemini but client handles fallback
                max_tokens=300
            )

        except Exception as e:
            self.log_error(f"LLM analysis error: {e}")
            return f"Detected {insight_type} for {asset} based on market data."
