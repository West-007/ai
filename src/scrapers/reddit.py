import logging
import praw
from datetime import datetime, timezone, timedelta
from src.config import Config

logger = logging.getLogger(__name__)

class RedditScraper:
    def __init__(self):
        self.enabled = bool(Config.REDDIT_CLIENT_ID and Config.REDDIT_CLIENT_SECRET)
        self.reddit = None
        if self.enabled:
            try:
                self.reddit = praw.Reddit(
                    client_id=Config.REDDIT_CLIENT_ID,
                    client_secret=Config.REDDIT_CLIENT_SECRET,
                    user_agent=Config.REDDIT_USER_AGENT
                )
            except Exception as e:
                logger.error(f"Failed to initialize Reddit scraper: {e}")
                self.enabled = False
        else:
            logger.warning("Reddit API credentials not fully configured. Reddit scraping disabled.")

    def fetch_recent_posts(self, limit=10):
        """Fetches recent posts from configured subreddits.
        
        Only returns posts created within Config.SCRAPE_LOOKBACK_HOURS.
        """
        if not self.enabled or not self.reddit:
            return []

        posts = []
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=Config.SCRAPE_LOOKBACK_HOURS)

        for subreddit_name in Config.SUBREDDITS:
            try:
                logger.info(f"Scraping r/{subreddit_name}...")
                subreddit = self.reddit.subreddit(subreddit_name)
                
                # Fetch hot posts
                for submission in subreddit.hot(limit=limit):
                    created_at = datetime.fromtimestamp(submission.created_utc, timezone.utc)
                    if created_at < cutoff_time:
                        continue
                    
                    posts.append({
                        "id": f"reddit_{submission.id}",
                        "source": f"r/{subreddit_name}",
                        "title": submission.title,
                        "content": submission.selftext if submission.selftext else submission.url,
                        "url": f"https://reddit.com{submission.permalink}",
                        "score": submission.score,
                        "created_at": created_at.isoformat()
                    })
            except Exception as e:
                logger.error(f"Error scraping r/{subreddit_name}: {e}")

        logger.info(f"Reddit scraper found {len(posts)} recent posts.")
        return posts
