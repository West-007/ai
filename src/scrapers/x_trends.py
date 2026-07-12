import logging
import tweepy
from datetime import datetime, timezone, timedelta
from src.config import Config

logger = logging.getLogger(__name__)

class XTrendsScraper:
    def __init__(self):
        self.enabled = bool(
            Config.X_CLIENT_ID and 
            Config.X_CLIENT_SECRET and 
            Config.X_ACCESS_TOKEN and 
            Config.X_ACCESS_TOKEN_SECRET
        )
        self.client = None
        if self.enabled:
            try:
                # We initialize Tweepy Client for v2 API
                self.client = tweepy.Client(
                    consumer_key=Config.X_CLIENT_ID,
                    consumer_secret=Config.X_CLIENT_SECRET,
                    access_token=Config.X_ACCESS_TOKEN,
                    access_token_secret=Config.X_ACCESS_TOKEN_SECRET
                )
            except Exception as e:
                logger.error(f"Failed to initialize X Client: {e}")
                self.enabled = False
        else:
            logger.warning("X API credentials not fully configured. X trend scraping disabled.")

    def fetch_recent_trends(self):
        """Fetches trending tweets/topics from X in our target niches.
        
        Using search_recent_tweets as it is supported in all standard developer plans.
        """
        if not self.enabled or not self.client:
            return []

        posts = []
        # Target terms reflecting CalebReview target audience
        search_queries = [
            "AI automation lang:en min_retweets:10",
            "solopreneur SaaS lang:en min_retweets:10",
            "online business sidehustle lang:en min_retweets:10"
        ]

        for query in search_queries:
            try:
                logger.info(f"Searching X with query: '{query}'...")
                # Search for recent tweets
                response = self.client.search_recent_tweets(
                    query=query,
                    max_results=10,
                    tweet_fields=["created_at", "public_metrics", "text", "id"]
                )
                
                if response.data:
                    for tweet in response.data:
                        # Extract creation time
                        created_at = tweet.created_at
                        if created_at:
                            # Normalize offset-naive vs aware
                            if created_at.tzinfo is None:
                                created_at = created_at.replace(tzinfo=timezone.utc)
                        else:
                            created_at = datetime.now(timezone.utc)
                            
                        # Calculate engagement score
                        metrics = tweet.public_metrics or {}
                        retweet_count = metrics.get("retweet_count", 0)
                        like_count = metrics.get("like_count", 0)
                        score = retweet_count * 2 + like_count

                        posts.append({
                            "id": f"x_{tweet.id}",
                            "source": "X (Twitter) Trend",
                            "title": tweet.text[:80] + "...",
                            "content": tweet.text,
                            "url": f"https://x.com/user/status/{tweet.id}",
                            "score": score,
                            "created_at": created_at.isoformat()
                        })
            except Exception as e:
                logger.error(f"Error scraping X trend for query '{query}': {e}")

        logger.info(f"X trend scraper found {len(posts)} recent tweets.")
        return posts
