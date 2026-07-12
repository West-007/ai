import logging
from src.publishers.x import XPublisher

logger = logging.getLogger(__name__)

class PublisherManager:
    def __init__(self):
        # Register available publishers
        self.publishers = {
            "x": XPublisher(),
            # Future publishers can be added here easily:
            # "linkedin": LinkedInPublisher()
        }

    def publish(self, platform: str, text: str, **kwargs) -> dict:
        """Publishes content to the specified platform."""
        platform_lower = platform.lower()
        if platform_lower not in self.publishers:
            error_msg = f"Publisher for platform '{platform}' is not supported."
            logger.error(error_msg)
            return {
                "success": False,
                "post_id": None,
                "url": None,
                "error": error_msg
            }
        
        publisher = self.publishers[platform_lower]
        return publisher.publish(text, **kwargs)
