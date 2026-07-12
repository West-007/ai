import logging
import tweepy
from src.config import Config
from src.publishers.base import BasePublisher

logger = logging.getLogger(__name__)

class XPublisher(BasePublisher):
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
                # Initialize Tweepy Client for v2 API
                self.client = tweepy.Client(
                    consumer_key=Config.X_CLIENT_ID,
                    consumer_secret=Config.X_CLIENT_SECRET,
                    access_token=Config.X_ACCESS_TOKEN,
                    access_token_secret=Config.X_ACCESS_TOKEN_SECRET
                )
            except Exception as e:
                logger.error(f"Failed to initialize X Publisher: {e}")
                self.enabled = False
        else:
            logger.warning("X API credentials not fully configured. X publishing is in MOCK mode.")

    def publish(self, text: str, **kwargs) -> dict:
        """Publishes a post (tweet) to X (Twitter)."""
        if not self.enabled or not self.client:
            logger.info(f"[MOCK PUBLISH TO X]:\n{text}")
            return {
                "success": True,
                "post_id": "mock_x_1234567890",
                "url": "https://x.com/mock_user/status/1234567890",
                "error": None
            }

        try:
            logger.info("Publishing post to X...")
            response = self.client.create_tweet(text=text)
            
            # Tweepy v2 response contains data as a dict or object
            tweet_id = response.data.get("id") if hasattr(response, "data") and isinstance(response.data, dict) else getattr(response.data, "id", None)
            
            if not tweet_id and response.data:
                # Backup access pattern
                tweet_id = response.data["id"]

            tweet_url = f"https://x.com/user/status/{tweet_id}"
            logger.info(f"Successfully published tweet. ID: {tweet_id}")
            
            return {
                "success": True,
                "post_id": str(tweet_id),
                "url": tweet_url,
                "error": None
            }
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to publish tweet to X: {error_msg}")
            return {
                "success": False,
                "post_id": None,
                "url": None,
                "error": error_msg
            }
        
    def test_connection(self) -> bool:
        """Simple verification method to test credentials."""
        if not self.enabled or not self.client:
            return False
        try:
            # Try fetching own bot details
            self.client.get_me()
            return True
        except Exception as e:
            logger.error(f"X Connection test failed: {e}")
            return False
