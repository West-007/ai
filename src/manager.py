import logging
import asyncio
import uuid
from datetime import datetime, timezone
from src.config import Config
from src.scrapers.reddit import RedditScraper
from src.scrapers.rss import RssScraper
from src.scrapers.x_trends import XTrendsScraper
from src.ai.analyzer import TopicAnalyzer
from src.ai.writer import PostWriter
from src.publishers.manager import PublisherManager
from src.bot.telegram_bot import TelegramControlCenter

logger = logging.getLogger(__name__)

# Keep track of processed item IDs to avoid duplicates in-memory
PROCESSED_IDS = set()

class AutomationManager:
    def __init__(self, application=None):
        self.application = application
        self.control_center = TelegramControlCenter(application)
        
        # Scrapers
        self.reddit_scraper = RedditScraper()
        self.rss_scraper = RssScraper()
        self.x_scraper = XTrendsScraper()
        
        # AI Engine
        self.analyzer = TopicAnalyzer()
        self.writer = PostWriter()
        
        # Publishers
        self.publisher = PublisherManager()

    async def run_one_cycle(self):
        """Runs a single cycle of scraping, analyzing, and publishing/routing."""
        logger.info("Starting automation scan cycle...")
        
        # 1. Discover trends
        candidates = []
        candidates.extend(self.rss_scraper.fetch_recent_articles())
        candidates.extend(self.reddit_scraper.fetch_recent_posts())
        candidates.extend(self.x_scraper.fetch_recent_trends())

        if not candidates:
            logger.info("No new trends discovered in this cycle.")
            return

        new_candidates_count = 0
        for item in candidates:
            item_id = item["id"]
            if item_id in PROCESSED_IDS:
                continue
            
            # Mark as processed immediately so we don't look at it again
            PROCESSED_IDS.add(item_id)
            new_candidates_count += 1
            
            logger.info(f"Processing candidate trend: {item['title']} (Source: {item['source']})")
            
            # Notify trend discovered
            await self.control_center.send_notification(
                f"🔍 <b>New Trend Discovered</b>\n"
                f"Source: {item['source']}\n"
                f"Title: {item['title']}"
            )

            # 2. Analyze the topic
            analysis = self.analyzer.analyze_topic(
                topic_title=item["title"],
                topic_content=item["content"],
                source_name=item["source"]
            )

            if not analysis.get("is_niche_relevant"):
                logger.info(f"Topic is not relevant to CalebReview niche. Skipping.")
                continue

            item["analysis"] = analysis
            await self.control_center.send_notification(
                f"🧠 <b>AI Finished Researching</b>\n"
                f"Topic: {item['title']}\n"
                f"Niche: {analysis.get('niche')}\n"
                f"Opportunity: {analysis.get('business_opportunity')[:150]}..."
            )

            # 3. Route based on Core vs Secondary
            if analysis.get("is_core_niche"):
                # Core Niche -> AUTOMATIC MODE
                logger.info("Topic is Core Niche. Running automatic publication flow.")
                
                await self.control_center.send_notification(
                    f"✍️ <b>AI writing post automatically...</b>"
                )
                
                # Generate post
                post_text = self.writer.generate_post(item["title"], analysis)
                
                await self.control_center.send_notification(
                    f"🤖 <b>AI generated post draft:</b>\n<pre>{post_text}</pre>"
                )
                
                # Publish
                pub_result = self.publisher.publish(platform="x", text=post_text)
                
                if pub_result["success"]:
                    tweet_id = pub_result["post_id"]
                    tweet_url = pub_result["url"]
                    
                    # Archive
                    await self.control_center.archive_post(
                        topic=item["title"],
                        source=item["source"],
                        analysis=analysis,
                        post_text=post_text,
                        published_url=tweet_url,
                        tweet_id=tweet_id
                    )
                    
                    # Notify owner
                    await self.control_center.send_notification(
                        f"🤖 <b>A new post has been published.</b>\n\n"
                        f"<b>Topic:</b> {item['title']}\n"
                        f"<b>Niche:</b> {analysis.get('niche')}\n"
                        f"<b>URL:</b> {tweet_url}"
                    )
                else:
                    # Notify owner of failure
                    await self.control_center.send_notification(
                        f"⚠️ <b>X API Failure:</b> Failed to publish automatic post.\n"
                        f"Error: {pub_result.get('error')}"
                    )
            else:
                # Secondary Niche -> APPROVAL MODE
                logger.info("Topic is Secondary Niche. Sending approval card to owner.")
                
                if self.application:
                    # Register candidate in-memory
                    candidate_id = str(uuid.uuid4())[:8]
                    if "candidates" not in self.application.bot_data:
                        self.application.bot_data["candidates"] = {}
                    
                    self.application.bot_data["candidates"][candidate_id] = item
                    
                    # Send approval card
                    await self.control_center.send_approval_card(candidate_id, item)
                else:
                    logger.warning("Bot application not registered. Cannot send approval card.")

        logger.info(f"Scan cycle complete. Processed {new_candidates_count} new trends.")

async def start_automation_loop(application, check_interval_seconds=1800):
    """Loop runner that runs cycles periodically."""
    manager = AutomationManager(application)
    control_center = TelegramControlCenter(application)

    # Allow application to finish starting up
    await asyncio.sleep(5)
    
    await control_center.send_notification("🤖 <b>AI Social Media Manager is starting up...</b>")
    
    while True:
        # Check if paused via command
        is_paused = application.bot_data.get("automation_paused", False)
        if not is_paused:
            try:
                await manager.run_one_cycle()
            except Exception as e:
                logger.error(f"Error in automation loop execution: {e}")
                await control_center.send_notification(
                    f"⚠️ <b>Automation Loop Error:</b>\n{str(e)}"
                )
        else:
            logger.info("Automation loop is currently paused. Skipping cycle.")

        await asyncio.sleep(check_interval_seconds)
