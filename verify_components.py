import sys
import logging
import asyncio
from src.config import Config
from src.scrapers.reddit import RedditScraper
from src.scrapers.rss import RssScraper
from src.scrapers.x_trends import XTrendsScraper
from src.ai.analyzer import TopicAnalyzer
from src.ai.writer import PostWriter
from src.publishers.manager import PublisherManager
from src.bot.telegram_bot import TelegramControlCenter

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
logger = logging.getLogger("verifier")

async def verify_components():
    logger.info("Checking configuration initialization...")
    logger.info(f"Owner ID: {Config.TELEGRAM_OWNER_USER_ID}")
    logger.info(f"Private Channel ID: {Config.TELEGRAM_PRIVATE_CHANNEL_ID}")
    
    warnings = Config.validate()
    if warnings:
        logger.warning(f"Note: Some credentials are not set up: {warnings}")
        logger.info("Testing will proceed using mock fallback logic where possible.")

    logger.info("\nInitializing Scrapers...")
    reddit = RedditScraper()
    logger.info(f"Reddit Scraper initialized (Enabled: {reddit.enabled})")
    
    rss = RssScraper()
    logger.info("RSS Scraper initialized (Always enabled)")
    
    x_trends = XTrendsScraper()
    logger.info(f"X Trends Scraper initialized (Enabled: {x_trends.enabled})")

    logger.info("\nInitializing AI Modules...")
    analyzer = TopicAnalyzer()
    writer = PostWriter()
    logger.info(f"AI Analyzer initialized (Enabled: {analyzer.enabled})")
    logger.info(f"AI Writer initialized (Enabled: {writer.enabled})")

    logger.info("\nInitializing Publishers...")
    publisher_manager = PublisherManager()
    logger.info("Publisher Manager initialized successfully.")

    logger.info("\nMocking Topic Analysis & Writing Process...")
    mock_title = "Google launches new AI Model with agentic capabilities"
    mock_content = "OpenAI competitors launch new features. The model performs complex reasoning and automates browser tasks."
    mock_source = "HackerNews"
    
    # 1. Run local test of analyzer/writer if OpenAI is configured
    if analyzer.enabled:
        logger.info("Running live OpenAI Topic Analysis test...")
        analysis = analyzer.analyze_topic(mock_title, mock_content, mock_source)
        logger.info(f"Analysis result: {analysis}")
        
        if analysis.get("is_niche_relevant"):
            logger.info("Running live OpenAI Post Writing test...")
            post = writer.generate_post(mock_title, analysis)
            logger.info(f"Generated Post:\n{post}")
    else:
        logger.info("OpenAI disabled. Skipping live AI tests.")
        analysis = {
            "is_niche_relevant": True,
            "is_core_niche": True,
            "niche": "AI Automation",
            "reason_chosen": "Mock explanation",
            "business_opportunity": "Mock opportunity",
            "business_lesson": "Mock lesson",
            "suggested_angle": "Mock angle",
            "suggested_opening": "Mock opening"
        }
        logger.info("Using mock analysis data.")

    # 2. Test mock publishing
    logger.info("\nTesting Mock Publication flow...")
    pub_result = publisher_manager.publish(platform="x", text="This is a verification tweet from CalebReview AI Manager.")
    logger.info(f"Publication Result: {pub_result}")
    
    logger.info("\nTesting Telegram control Center mock operations...")
    bot_control = TelegramControlCenter(application=None)
    await bot_control.send_notification("System verification running (MOCK)...")

    logger.info("\n🎉 Verification Completed Successfully! All components imported and initialized.")

if __name__ == "__main__":
    asyncio.run(verify_components())
