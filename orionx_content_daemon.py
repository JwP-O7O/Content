#!/usr/bin/env python3
"""
OrionX Content Creation Empire - Autonomous 24/7 Daemon
======================================================
Coordinates autonomous agents across:
1. Live Market Scanning (Binance & Crypto feeds)
2. Quantitative Analysis & Trend Modeling
3. Multi-platform Content Planning
4. High-conversion Copy Generation (AI-driven)
5. Direct Telegram Dispatch to @AgentO7Obot
6. RSS / JSON Feed Syndication to OrionX Ecosystem
"""

import os
import sys
import time
import json
import signal
import asyncio
from pathlib import Path
from datetime import datetime, timezone
from xml.sax.saxutils import escape

# Ensure current directory is on python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from loguru import logger
from src.orchestrator import AgentOrchestrator
from src.database.connection import get_db
from src.database.models import PublishedContent, ContentPlan, Insight

# Configuration
INTERVAL_MINUTES = int(os.environ.get("ORIONX_CONTENT_INTERVAL_MINUTES", "60"))
FEED_LOCATIONS = [
    Path("/root/empire/hae_command_center"),
    Path("/root/hae_command_center"),
    BASE_DIR.parent / "hae_command_center",
    BASE_DIR / "data"
]

def syndicate_to_feeds():
    """Extract recent published content from SQLite and syndicate to JSON & RSS feeds."""
    try:
        with get_db() as db:
            recent_posts = (
                db.query(PublishedContent)
                .order_by(PublishedContent.published_at.desc())
                .limit(25)
                .all()
            )

            feed_items = []
            for p in recent_posts:
                feed_items.append({
                    "id": p.id,
                    "platform": p.platform,
                    "text": p.content_text,
                    "post_id": p.post_id,
                    "published_at": p.published_at.isoformat() if p.published_at else datetime.now(timezone.utc).isoformat(),
                    "link": "https://trade.orionx.nl"
                })

        # Find available feed directory
        target_dir = None
        for loc in FEED_LOCATIONS:
            if loc.exists():
                target_dir = loc
                break
        
        if not target_dir:
            target_dir = BASE_DIR / "data"
            target_dir.mkdir(parents=True, exist_ok=True)

        json_path = target_dir / "promotions_feed.json"
        rss_path = target_dir / "promotions_rss.xml"

        # Write JSON Feed
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump({
                "source": "OrionX Content Engine",
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "total_items": len(feed_items),
                "items": feed_items
            }, f, indent=2)

        # Write RSS Feed
        rss_items = []
        for item in feed_items:
            pub_date = item["published_at"]
            rss_items.append(f"""    <item>
      <title>{escape(item['platform'].upper())}: {escape(item['text'][:60])}...</title>
      <description>{escape(item['text'])}</description>
      <link>https://trade.orionx.nl</link>
      <guid isPermaLink="false">orionx-content-{item['id']}</guid>
      <pubDate>{pub_date}</pubDate>
    </item>""")

        rss_xml = f"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
  <channel>
    <title>OrionX Autonomous Content & Alpha Feed</title>
    <link>https://trade.orionx.nl</link>
    <description>Live autonomous crypto market intelligence, trading alpha and strategic updates from the OrionX Empire.</description>
    <lastBuildDate>{datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S GMT')}</lastBuildDate>
{chr(10).join(rss_items)}
  </channel>
</rss>"""

        with open(rss_path, "w", encoding="utf-8") as f:
            f.write(rss_xml)

        logger.info(f"Successfully syndicated {len(feed_items)} posts to {json_path} and {rss_path}")
    except Exception as e:
        logger.error(f"Feed syndication failed: {e}")

class OrionXContentDaemon:
    def __init__(self):
        self.orchestrator = AgentOrchestrator()
        self.running = True

    def stop(self):
        logger.info("Stopping OrionX Content Engine...")
        self.running = False

    async def run_cycle(self):
        logger.info("=" * 60)
        logger.info("Starting Autonomous Content Engine Cycle")
        logger.info("=" * 60)
        try:
            results = await self.orchestrator.run_full_pipeline()
            logger.info(f"Cycle completed successfully: {results.get('status')}")
            syndicate_to_feeds()
        except Exception as e:
            logger.error(f"Error executing content cycle: {e}")

    async def start(self):
        logger.info(f"OrionX Content Engine started (Cycle Interval: {INTERVAL_MINUTES} minutes)")
        # Run first cycle immediately
        await self.run_cycle()

        while self.running:
            logger.info(f"Sleeping for {INTERVAL_MINUTES} minutes until next cycle...")
            for _ in range(INTERVAL_MINUTES * 6):
                if not self.running:
                    break
                await asyncio.sleep(10)

            if self.running:
                await self.run_cycle()

def main():
    daemon = OrionXContentDaemon()

    def handle_signal(sig, frame):
        daemon.stop()

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    asyncio.run(daemon.start())

if __name__ == "__main__":
    main()
