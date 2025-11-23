"""ImageGenerationAgent - Generates visual content for posts."""

import json
from typing import Optional

from src.agents.base_agent import BaseAgent
from src.database.connection import get_db
from src.database.models import Insight


class ImageGenerationAgent(BaseAgent):
    """
    The Image Generation Agent creates visual content.

    Responsibilities:
    - Generate price chart images
    - Create infographic-style posts
    - Generate AI images for social media
    - Annotate charts with analysis
    """

    def __init__(self):
        """Initialize the ImageGenerationAgent."""
        super().__init__("ImageGenerationAgent")

        # Image generation settings
        self.chart_api_base = "https://quickchart.io/chart"
        self.output_dir = "data/images"

        # Ensure output directory exists
        import os
        os.makedirs(self.output_dir, exist_ok=True)

    async def execute(self) -> dict:
        """
        Execute image generation for insights that need visuals.

        Returns:
            Dictionary with generation results
        """
        self.log_info("Starting image generation...")

        results = {
            "images_generated": 0,
            "charts_created": 0,
            "errors": []
        }

        try:
            # Get insights that would benefit from images
            insights_needing_images = await self._get_insights_for_images()

            for insight in insights_needing_images:
                try:
                    image_url = await self._generate_image_for_insight(insight)

                    if image_url:
                        # Store image URL with the insight
                        await self._save_image_reference(insight.id, image_url)
                        results["images_generated"] += 1

                        if insight.type.value in ["breakout", "breakdown", "volume_spike"]:
                            results["charts_created"] += 1

                except Exception as e:
                    error_msg = f"Error generating image for insight {insight.id}: {e}"
                    self.log_error(error_msg)
                    results["errors"].append(error_msg)

            self.log_info(
                f"Image generation complete: {results['images_generated']} images created"
            )

        except Exception as e:
            self.log_error(f"Image generation error: {e}")
            raise

        return results

    async def _get_insights_for_images(self):
        """Get insights that would benefit from images."""
        with get_db() as db:
            # Get recent high-confidence insights that don't have images yet
            return db.query(Insight).filter(
                Insight.confidence >= 0.75,
                Insight.is_published.is_(False)
            ).limit(5).all()


    async def _generate_image_for_insight(self, insight: Insight) -> Optional[str]:
        """
        Generate an image for a specific insight.

        Args:
            insight: Insight to generate image for

        Returns:
            URL or path to generated image
        """
        insight_type = insight.type.value

        # Different image types based on insight type
        if insight_type in ["breakout", "breakdown", "volume_spike"]:
            return await self._generate_price_chart(insight)
        if insight_type == "sentiment_shift":
            return await self._generate_sentiment_visualization(insight)
        if insight_type == "news_impact":
            return await self._generate_news_infographic(insight)
        return await self._generate_generic_crypto_image(insight)

    async def _generate_price_chart(self, insight: Insight) -> Optional[str]:
        """
        Generate a price chart with annotations.

        Args:
            insight: Insight containing price data

        Returns:
            URL to chart image
        """
        try:
            asset = insight.asset
            # Note: insight.details could be used for additional chart customization

            # Get price data (would fetch from database in practice)
            # For now, create a sample chart

            chart_config = {
                "type": "line",
                "data": {
                    "labels": ["1h ago", "45m", "30m", "15m", "Now"],
                    "datasets": [{
                        "label": f"{asset} Price",
                        "data": [100, 102, 98, 105, 110],  # Sample data
                        "borderColor": "rgb(75, 192, 192)",
                        "backgroundColor": "rgba(75, 192, 192, 0.2)",
                        "tension": 0.4
                    }]
                },
                "options": {
                    "title": {
                        "display": True,
                        "text": f"{asset} - {insight.type.value.title()}"
                    },
                    "scales": {
                        "yAxes": [{
                            "ticks": {
                                "callback": "function(value) { return '$' + value; }"
                            }
                        }]
                    },
                    "annotation": {
                        "annotations": [{
                            "type": "line",
                            "mode": "vertical",
                            "scaleID": "x-axis-0",
                            "value": "Now",
                            "borderColor": "red",
                            "label": {
                                "content": f"Confidence: {insight.confidence:.0%}",
                                "enabled": True
                            }
                        }]
                    }
                }
            }

            # Generate chart URL
            return await self._create_chart(chart_config)


        except Exception as e:
            self.log_error(f"Error generating price chart: {e}")
            return None

    async def _create_chart(self, config: dict) -> str:
        """
        Create a chart using QuickChart API.

        Args:
            config: Chart.js configuration

        Returns:
            URL to chart image
        """
        try:
            # Encode config as JSON
            config_json = json.dumps(config)

            # Create QuickChart URL
            return f"{self.chart_api_base}?c={config_json}"

            # In practice, you might want to download and save locally
            # For now, return the URL


        except Exception as e:
            self.log_error(f"Error creating chart: {e}")
            return None

    async def _generate_sentiment_visualization(
        self,
        insight: Insight
    ) -> Optional[str]:
        """Generate a sentiment visualization."""
        try:
            # Create a simple gauge chart for sentiment
            chart_config = {
                "type": "radialGauge",
                "data": {
                    "datasets": [{
                        "data": [75],  # Sentiment score
                        "backgroundColor": "green"
                    }]
                },
                "options": {
                    "title": {
                        "display": True,
                        "text": f"{insight.asset} Sentiment Shift"
                    },
                    "trackColor": "lightgray",
                    "centerPercentage": 80,
                    "centerArea": {
                        "text": "75%",
                        "fontSize": 40
                    }
                }
            }

            return await self._create_chart(chart_config)

        except Exception as e:
            self.log_error(f"Error generating sentiment viz: {e}")
            return None

    async def _generate_news_infographic(self, insight: Insight) -> Optional[str]:
        """Generate a news impact infographic."""
        try:
            # Create a bar chart showing news volume over time
            chart_config = {
                "type": "bar",
                "data": {
                    "labels": ["Day 1", "Day 2", "Day 3", "Today"],
                    "datasets": [{
                        "label": "News Articles",
                        "data": [2, 1, 3, 5],
                        "backgroundColor": "rgba(54, 162, 235, 0.8)"
                    }]
                },
                "options": {
                    "title": {
                        "display": True,
                        "text": f"{insight.asset} News Impact"
                    }
                }
            }

            return await self._create_chart(chart_config)

        except Exception as e:
            self.log_error(f"Error generating news infographic: {e}")
            return None

    async def _generate_generic_crypto_image(
        self,
        insight: Insight
    ) -> Optional[str]:
        """Generate a generic crypto-themed image."""
        # For now, return a placeholder
        # In practice, you could use DALL-E, Stable Diffusion, etc.

        self.log_info(f"Would generate AI image for {insight.asset} {insight.type.value}")

        # Placeholder image URL
        return f"https://via.placeholder.com/800x400/4CAF50/FFFFFF?text={insight.asset}+{insight.type.value}"

    async def _save_image_reference(self, insight_id: int, image_url: str):
        """Save image URL reference to the insight."""
        with get_db() as db:
            insight = db.query(Insight).filter(Insight.id == insight_id).first()

            if insight:
                # Add image URL to insight details
                if not insight.details:
                    insight.details = {}

                insight.details["image_url"] = image_url
                db.commit()

                self.log_info(f"Saved image reference for insight {insight_id}")

    async def create_custom_chart(
        self,
        asset: str,
        chart_type: str = "line",
        time_period: str = "24h"
    ) -> Optional[str]:
        """
        Create a custom chart for a specific asset.

        Args:
            asset: Asset symbol
            chart_type: Type of chart (line, candlestick, bar)
            time_period: Time period for data

        Returns:
            URL to chart image
        """
        self.log_info(f"Creating custom {chart_type} chart for {asset} ({time_period})")

        # In practice, fetch real data from exchange API
        # For now, create a sample chart

        chart_config = {
            "type": chart_type,
            "data": {
                "labels": self._get_time_labels(time_period),
                "datasets": [{
                    "label": f"{asset} Price",
                    "data": self._get_sample_data(time_period),
                    "borderColor": "rgb(75, 192, 192)"
                }]
            },
            "options": {
                "title": {
                    "display": True,
                    "text": f"{asset} - {time_period}"
                }
            }
        }

        return await self._create_chart(chart_config)

    def _get_time_labels(self, period: str) -> list:
        """Generate time labels for a given period."""
        if period == "24h":
            return ["00:00", "04:00", "08:00", "12:00", "16:00", "20:00", "24:00"]
        if period == "7d":
            return ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        if period == "30d":
            return ["Week 1", "Week 2", "Week 3", "Week 4"]
        return ["Start", "Mid", "End"]

    def _get_sample_data(self, period: str) -> list:
        """Generate sample data for a given period."""
        # In practice, fetch real data
        if period == "24h":
            return [45000, 45200, 44800, 46000, 46500, 47000, 47200]
        if period == "7d":
            return [45000, 46000, 45500, 47000, 46800, 48000, 47500]
        if period == "30d":
            return [42000, 45000, 47000, 48000]
        return [100, 105, 103]
