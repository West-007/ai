import os
from dotenv import load_dotenv

# Load variables from .env
load_dotenv()

class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

    # X Credentials
    X_CLIENT_ID = os.getenv("X_CLIENT_ID", "")
    X_CLIENT_SECRET = os.getenv("X_CLIENT_SECRET", "")
    X_ACCESS_TOKEN = os.getenv("X_ACCESS_TOKEN", "")
    X_ACCESS_TOKEN_SECRET = os.getenv("X_ACCESS_TOKEN_SECRET", "")

    # Reddit Credentials
    REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "")
    REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "")
    REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "CalebReviewSocialBot/1.0")

    # Telegram Credentials
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_BOT_USERNAME = os.getenv("TELEGRAM_BOT_USERNAME", "@CalebReviewautomationbot")
    
    # Telegram Owner Config
    _owner_id_raw = os.getenv("TELEGRAM_OWNER_USER_ID", "991042904")
    try:
        TELEGRAM_OWNER_USER_ID = int(_owner_id_raw)
    except ValueError:
        TELEGRAM_OWNER_USER_ID = 991042904

    # Telegram Private Archive Channel Config
    TELEGRAM_PRIVATE_CHANNEL_NAME = os.getenv("TELEGRAM_PRIVATE_CHANNEL_NAME", "CalebReview AI Logs")
    _channel_id_raw = os.getenv("TELEGRAM_PRIVATE_CHANNEL_ID", "4371566619")
    
    # Normalizing private channel ID.
    # In Telegram API, Channel IDs are prefixed with -100 (e.g. -1004371566619)
    if _channel_id_raw:
        if not _channel_id_raw.startswith("-100") and _channel_id_raw.isdigit():
            TELEGRAM_PRIVATE_CHANNEL_ID = f"-100{_channel_id_raw}"
        else:
            TELEGRAM_PRIVATE_CHANNEL_ID = _channel_id_raw
    else:
        TELEGRAM_PRIVATE_CHANNEL_ID = "-1004371566619"

    # Scraping Config
    SUBREDDITS = ["entrepreneur", "saas", "solopreneur", "sidehustle", "artificial", "marketing", "webdev"]
    RSS_FEEDS = {
        "TechCrunch": "https://techcrunch.com/feed/",
        "HackerNews": "https://news.ycombinator.com/rss",
        "SearchEngineJournal": "https://www.searchenginejournal.com/feed/"
    }

    # Time window for scraping (e.g., look back at posts from the last 4 hours)
    SCRAPE_LOOKBACK_HOURS = 4

    @classmethod
    def validate(cls):
        """Validates configuration, returning a list of warnings or errors."""
        missing = []
        if not cls.OPENAI_API_KEY:
            missing.append("OPENAI_API_KEY")
        if not cls.TELEGRAM_BOT_TOKEN:
            missing.append("TELEGRAM_BOT_TOKEN")
        if not all([cls.X_CLIENT_ID, cls.X_CLIENT_SECRET, cls.X_ACCESS_TOKEN, cls.X_ACCESS_TOKEN_SECRET]):
            missing.append("X (Twitter) credentials")
        return missing
