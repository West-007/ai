from abc import ABC, abstractmethod

class BasePublisher(ABC):
    @abstractmethod
    def publish(self, text: str, **kwargs) -> dict:
        """Publishes content to the specific platform.
        
        Returns a dictionary containing details of the publication:
        {
            "success": True/False,
            "post_id": "platform_specific_id",
            "url": "published_post_url",
            "error": "error_message_if_failed"
        }
        """
        pass
