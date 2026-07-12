import logging
import asyncio
from datetime import datetime, timezone
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes
)
from src.config import Config

logger = logging.getLogger(__name__)

# State dictionary for storing owner interactions
# keys: owner_user_id, value: dict(candidate_id, state)
OWNER_STATES = {}

class TelegramControlCenter:
    def __init__(self, application: Application = None):
        self.application = application
        self.bot = application.bot if application else None
        self.enabled = bool(Config.TELEGRAM_BOT_TOKEN)
        
        if not self.enabled:
            logger.warning("Telegram Bot Token not configured. Telegram bot is in MOCK mode.")

    async def send_notification(self, message: str, to_channel: bool = False):
        """Sends a notification to the owner or the archive channel."""
        if not self.enabled or not self.bot:
            logger.info(f"[MOCK TELEGRAM NOTIFICATION] (to_channel={to_channel}):\n{message}")
            return

        try:
            chat_id = Config.TELEGRAM_PRIVATE_CHANNEL_ID if to_channel else Config.TELEGRAM_OWNER_USER_ID
            await self.bot.send_message(chat_id=chat_id, text=message, parse_mode="HTML")
        except Exception as e:
            logger.error(f"Error sending Telegram notification: {e}")

    async def send_approval_card(self, candidate_id: str, candidate_data: dict):
        """Sends an interactive approval card with inline buttons to the owner."""
        topic = candidate_data.get("title", "Untitled Topic")
        source = candidate_data.get("source", "Unknown Source")
        analysis = candidate_data.get("analysis", {})

        message = (
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🤖 <b>I found something interesting.</b>\n\n"
            f"<b>Topic:</b> {topic}\n"
            f"<b>Source:</b> {source}\n"
            f"<b>Why this matters:</b> {analysis.get('reason_chosen', 'N/A')}\n"
            f"<b>Possible business lesson:</b> {analysis.get('business_lesson', 'N/A')}\n"
            f"<b>Suggested angle:</b> {analysis.get('suggested_angle', 'N/A')}\n"
            f"<b>Suggested opening sentence:</b> <i>\"{analysis.get('suggested_opening', 'N/A')}\"</i>\n\n"
            f"No post has been published.\n"
            f"Waiting for your decision.\n"
            f"━━━━━━━━━━━━━━━━━━━━━━"
        )

        if not self.enabled or not self.bot:
            logger.info(f"[MOCK TELEGRAM APPROVAL CARD] (ID={candidate_id}):\n{message}")
            # In mock mode, we assume SKIP or AUTO-APPROVE if we were running a script.
            return

        keyboard = [
            [
                InlineKeyboardButton("✅ Approve", callback_data=f"approve_{candidate_id}"),
                InlineKeyboardButton("✍️ I'll Write It", callback_data=f"write_{candidate_id}"),
                InlineKeyboardButton("❌ Skip", callback_data=f"skip_{candidate_id}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        try:
            await self.bot.send_message(
                chat_id=Config.TELEGRAM_OWNER_USER_ID,
                text=message,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Error sending Telegram approval card: {e}")

    async def archive_post(self, topic: str, source: str, analysis: dict, post_text: str, published_url: str, tweet_id: str):
        """Archives a successfully published post inside the private Telegram channel."""
        now = datetime.now(timezone.utc)
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S UTC")

        archive_message = (
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🤖 <b>New X Post Published</b>\n\n"
            f"📰 <b>Topic:</b> {topic}\n\n"
            f"<b>Why I selected it:</b>\n{analysis.get('reason_chosen', 'N/A')}\n\n"
            f"<b>Business opportunity:</b>\n{analysis.get('business_opportunity', 'N/A')}\n\n"
            f"<b>Business lesson:</b>\n{analysis.get('business_lesson', 'N/A')}\n\n"
            f"<b>Generated post:</b>\n<pre>{post_text}</pre>\n\n"
            f"<b>Source:</b> {source}\n"
            f"<b>Published URL:</b> {published_url}\n"
            f"<b>Tweet ID:</b> {tweet_id}\n"
            f"<b>Date:</b> {date_str}\n"
            f"<b>Time:</b> {time_str}\n\n"
            f"<b>Status:</b>\nPublished Successfully\n"
            f"━━━━━━━━━━━━━━━━━━━━━━"
        )

        # 1. Send log update to owner channel
        await self.send_notification(archive_message, to_channel=True)


# Telegram Bot Command and Callback Handlers
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /start command."""
    if update.effective_user.id != Config.TELEGRAM_OWNER_USER_ID:
        await update.message.reply_text("Unauthorized access.")
        return
    await update.message.reply_text(
        "🤖 CalebReview Automation Bot is active.\n"
        "Commands:\n"
        "/status - Check system status\n"
        "/start_automation - Resume automated scanning\n"
        "/stop_automation - Pause automated scanning"
    )

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /status command."""
    if update.effective_user.id != Config.TELEGRAM_OWNER_USER_ID:
        return
    # Check if the manager loop is running
    is_paused = context.bot_data.get("automation_paused", False)
    status_text = "Paused ⏸️" if is_paused else "Running 🟢"
    
    await update.message.reply_text(
        f"🤖 <b>CalebReview System Status</b>\n"
        f"Automation Loop: {status_text}\n"
        f"Channel: {Config.TELEGRAM_PRIVATE_CHANNEL_NAME}\n"
        f"Owner ID: {Config.TELEGRAM_OWNER_USER_ID}",
        parse_mode="HTML"
    )

async def stop_automation_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Pauses the automation loop."""
    if update.effective_user.id != Config.TELEGRAM_OWNER_USER_ID:
        return
    context.bot_data["automation_paused"] = True
    await update.message.reply_text("Automation loop paused ⏸️.")
    logger.info("Automation loop paused by user command.")

async def start_automation_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Resumes the automation loop."""
    if update.effective_user.id != Config.TELEGRAM_OWNER_USER_ID:
        return
    context.bot_data["automation_paused"] = False
    await update.message.reply_text("Automation loop resumed 🟢.")
    logger.info("Automation loop resumed by user command.")

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles button interaction responses (Approve, Write, Skip)."""
    query = update.callback_query
    await query.answer()

    if update.effective_user.id != Config.TELEGRAM_OWNER_USER_ID:
        return

    data = query.data
    action, candidate_id = data.split("_", 1)

    # Fetch candidate details from application bot_data
    candidates = context.bot_data.get("candidates", {})
    candidate = candidates.get(candidate_id)

    if not candidate:
        await query.edit_message_text("❌ Error: Candidate data not found in memory (could be expired or cleared).")
        return

    if action == "approve":
        await query.edit_message_text("⚡ Generating post and publishing to X...")
        
        # We delegate the actual generation and publishing process to context task
        # so the bot interaction remains responsive.
        context.application.create_task(
            _process_approved_candidate(context.application, candidate_id, candidate, query)
        )

    elif action == "write":
        await query.edit_message_text(
            "✍️ <b>I'll Write It Selected</b>\n"
            "Please send the exact text you want to publish as your next message. "
            "I will publish it directly to X without any changes.",
            parse_mode="HTML"
        )
        # Set state for owner
        OWNER_STATES[update.effective_user.id] = {
            "action": "write",
            "candidate_id": candidate_id
        }

    elif action == "skip":
        # Remove from candidates
        candidates.pop(candidate_id, None)
        await query.edit_message_text("❌ Topic skipped permanently.")
        logger.info(f"Candidate {candidate_id} skipped by owner.")


async def handle_owner_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles messages from the owner, specifically for 'I'll Write It' flow."""
    user_id = update.effective_user.id
    if user_id != Config.TELEGRAM_OWNER_USER_ID:
        return

    state = OWNER_STATES.get(user_id)
    if not state or state.get("action") != "write":
        # Standard chat message (unrelated to state)
        await update.message.reply_text("I'm listening. Use /status to check automation.")
        return

    # Clear state
    OWNER_STATES.pop(user_id, None)

    candidate_id = state.get("candidate_id")
    candidates = context.bot_data.get("candidates", {})
    candidate = candidates.pop(candidate_id, None)

    if not candidate:
        await update.message.reply_text("❌ Error: Candidate data expired or not found.")
        return

    custom_post_text = update.message.text
    status_msg = await update.message.reply_text("⚡ Publishing your custom post to X...")

    # We delegate publishing
    context.application.create_task(
        _publish_custom_post(context.application, candidate, custom_post_text, status_msg)
    )


# Helper functions to run the background publishers asynchronously
async def _process_approved_candidate(application, candidate_id, candidate, query):
    try:
        from src.ai.writer import PostWriter
        from src.publishers.manager import PublisherManager

        # Remove candidate from cache
        application.bot_data.get("candidates", {}).pop(candidate_id, None)

        writer = PostWriter()
        publisher = PublisherManager()
        control_center = TelegramControlCenter(application)

        topic = candidate["title"]
        source = candidate["source"]
        analysis = candidate["analysis"]

        # Generate post copy
        post_text = writer.generate_post(topic, analysis)

        # Publish to X
        pub_result = publisher.publish(platform="x", text=post_text)

        if pub_result["success"]:
            tweet_id = pub_result["post_id"]
            tweet_url = pub_result["url"]

            # Archive the post
            await control_center.archive_post(
                topic=topic,
                source=source,
                analysis=analysis,
                post_text=post_text,
                published_url=tweet_url,
                tweet_id=tweet_id
            )

            await query.edit_message_text(
                f"✅ <b>Successfully Published to X!</b>\n\n"
                f"URL: {tweet_url}\n"
                f"Post text:\n<i>{post_text}</i>",
                parse_mode="HTML"
            )
        else:
            await query.edit_message_text(
                f"❌ <b>Publishing failed:</b>\n{pub_result.get('error')}"
            )
            # Notify owner of the API failure
            await control_center.send_notification(
                f"⚠️ <b>X API Failure:</b> Failed to publish approved post.\n"
                f"Error: {pub_result.get('error')}"
            )
    except Exception as e:
        logger.error(f"Error in approved candidate processing: {e}")
        await query.edit_message_text(f"❌ Error during execution: {e}")


async def _publish_custom_post(application, candidate, post_text, status_msg):
    try:
        from src.publishers.manager import PublisherManager
        publisher = PublisherManager()
        control_center = TelegramControlCenter(application)

        topic = candidate["title"]
        source = candidate["source"]
        analysis = candidate["analysis"]

        # Publish to X
        pub_result = publisher.publish(platform="x", text=post_text)

        if pub_result["success"]:
            tweet_id = pub_result["post_id"]
            tweet_url = pub_result["url"]

            # Archive the custom post
            await control_center.archive_post(
                topic=topic,
                source=source,
                analysis=analysis,
                post_text=post_text,
                published_url=tweet_url,
                tweet_id=tweet_id
            )

            await status_msg.edit_text(
                f"✅ <b>Custom post successfully published!</b>\n\n"
                f"URL: {tweet_url}",
                parse_mode="HTML"
            )
        else:
            await status_msg.edit_text(
                f"❌ <b>Publishing failed:</b>\n{pub_result.get('error')}"
            )
            # Notify owner of failure
            await control_center.send_notification(
                f"⚠️ <b>X API Failure:</b> Failed to publish custom post.\n"
                f"Error: {pub_result.get('error')}"
            )
    except Exception as e:
        logger.error(f"Error in custom post publishing: {e}")
        await status_msg.edit_text(f"❌ Error during execution: {e}")


def setup_telegram_bot(application: Application):
    """Registers handlers for the bot application."""
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("stop_automation", stop_automation_command))
    application.add_handler(CommandHandler("start_automation", start_automation_command))
    
    # Callback query handler for inline button actions
    application.add_handler(CallbackQueryHandler(handle_callback_query, pattern="^(approve|write|skip)_"))
    
    # Message handler for user inputs (custom posts)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_owner_message))
