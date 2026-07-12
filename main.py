import logging
import sys
import asyncio
from telegram.ext import ApplicationBuilder
from src.config import Config
from src.bot.telegram_bot import setup_telegram_bot, TelegramControlCenter

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("main")

async def post_init(application) -> None:
    """Callback triggered after bot application initialization, before polling starts."""
    from src.manager import start_automation_loop
    
    # Run the background automation loop (check every 30 minutes / 1800 seconds)
    logger.info("Scheduling background automation loop...")
    asyncio.create_task(start_automation_loop(application, check_interval_seconds=1800))
    logger.info("Background automation loop scheduled successfully.")

async def post_shutdown(application) -> None:
    """Callback triggered during bot shutdown."""
    control_center = TelegramControlCenter(application)
    logger.info("System is shutting down...")
    await control_center.send_notification("🤖 <b>AI Social Media Manager is shutting down...</b>")

def main():
    logger.info("Initializing CalebReview AI Social Media Manager...")

    # Validate configuration
    warnings = Config.validate()
    if warnings:
        logger.warning(f"Configuration warning(s): Missing {', '.join(warnings)}")
        logger.warning("The application will start, but missing components will run in mock mode.")

    if not Config.TELEGRAM_BOT_TOKEN:
        logger.error("CRITICAL: TELEGRAM_BOT_TOKEN is required to run the control bot. Running mock manager execution instead...")
        # Fallback runner for headless/botless testing
        async def run_mock_standalone():
            from src.manager import AutomationManager
            manager = AutomationManager(application=None)
            logger.info("Starting standalone mock automation loop...")
            await manager.run_one_cycle()
            logger.info("Standalone mock automation cycle completed.")
        
        asyncio.run(run_mock_standalone())
        return

    # Build Telegram Bot Application
    application = (
        ApplicationBuilder()
        .token(Config.TELEGRAM_BOT_TOKEN)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )

    # Set up command and callback handlers
    setup_telegram_bot(application)

    # Start the bot. This starts the polling loop, blocks until Ctrl+C, and shuts down cleanly.
    logger.info("Starting Telegram Bot listener...")
    application.run_polling()

if __name__ == "__main__":
    main()
