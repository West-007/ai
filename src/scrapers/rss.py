import logging
import feedparser
import time
from datetime import datetime, timezone, timedelta
from src.config import Config

logger = logging.getLogger(__name__)

class RssScraper:
    def fetch_recent_articles(self):
        """Fetches recent articles from configured RSS feeds.
        
        Only returns articles published within Config.SCRAPE_LOOKBACK_HOURS.
        """
        articles = []
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=Config.SCRAPE_LOOKBACK_HOURS)

        for source_name, feed_url in Config.RSS_FEEDS.items():
            try:
                logger.info(f"Parsing RSS feed: {source_name} ({feed_url})...")
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries:
                    # Get publication time
                    pub_time = None
                    if hasattr(entry, "published_parsed") and entry.published_parsed:
                        pub_time = datetime.fromtimestamp(time.mktime(entry.published_parsed), timezone.utc)
                    elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                        pub_time = datetime.fromtimestamp(time.mktime(entry.updated_parsed), timezone.utc)
                    
                    if not pub_time:
                        continue
                    
                    # Filter by lookback window
                    if pub_time < cutoff_time:
                        continue
                    
                    description = entry.summary if hasattr(entry, "summary") else ""
                    # strip html if present
                    if "<" in description and ">" in description:
                        # Simple HTML stripping
                        import re
                        description = re.sub(r'<[^>]+>', '', description)

                    articles.append({
                        "id": f"rss_{entry.get('id', entry.link)}",
                        "source": source_name,
                        "title": entry.title,
                        "content": description,
                        "url": entry.link,
                        "score": 0, # RSS feeds don't have scores
                        "created_at": pub_time.isoformat()
                    })
            except Exception as e:
                logger.error(f"Error parsing RSS feed {source_name}: {e}")

        logger.info(f"RSS scraper found {len(articles)} recent articles.")
        return articles
