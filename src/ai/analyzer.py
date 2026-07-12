import json
import logging
from openai import OpenAI
from src.config import Config

logger = logging.getLogger(__name__)

class TopicAnalyzer:
    def __init__(self):
        self.enabled = bool(Config.OPENAI_API_KEY)
        self.client = None
        if self.enabled:
            self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        else:
            logger.warning("OpenAI API key not configured. Topic analysis is disabled.")

    def analyze_topic(self, topic_title, topic_content, source_name):
        """Analyzes a topic to see if it is relevant, evaluates the business angle,
        and determines if it is Core Niche (auto-publish) or Secondary Niche (needs approval).
        """
        if not self.enabled or not self.client:
            return {
                "is_niche_relevant": False,
                "is_core_niche": False,
                "reason_chosen": "OpenAI not configured",
                "business_opportunity": "",
                "business_lesson": "",
                "suggested_angle": "",
                "suggested_opening": ""
            }

        prompt = f"""
You are an experienced entrepreneur, marketing strategist, and business consultant. Your job is to analyze the following trend/topic and extract a valuable business lesson or opportunity for people interested in building online wealth.

Topic Source: {source_name}
Topic Title: {topic_title}
Topic Content:
{topic_content}

---

Determine if this topic fits the interest of CalebReview's audience:
- Core Niche (Automatically publish if relevant): Making money online, AI, AI Automation, Entrepreneurship, Business Growth, Online Business, Affiliate Marketing, SEO, Website Design, SaaS, Lead Generation, Freelancing, Productivity, Digital Marketing, Content Creation, Automation, Technology that creates business opportunities.
- Secondary Niche (Requires human approval, only post if there is a strong business lesson): Sports, Politics, Celebrity/Entertainment gossip, World news, Science, Finance, Lifestyle.
- Irrelevant Niche: Pure gossip, drama, crime, politics or sports with no business angle, clickbait with no value. Reject these completely.

You must respond in JSON format matching this schema:
{{
  "is_niche_relevant": true or false,
  "is_core_niche": true or false (true if core niche, false if secondary but contains a valuable business lesson),
  "niche": "e.g., AI Automation, SaaS, Business Growth",
  "reason_chosen": "Why this topic is valuable for the CalebReview audience",
  "business_opportunity": "How someone can make money, save time, build a service, or grow a business from this",
  "business_lesson": "The core takeaway or shift in perspective for entrepreneurs",
  "suggested_angle": "The specific perspective/angle we should take (e.g. Applying it first vs waiting)",
  "suggested_opening": "A strong, punchy first sentence for the social media post"
}}
"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a professional business analyst. Output only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.7
            )
            
            result_text = response.choices[0].message.content
            analysis = json.loads(result_text)
            logger.info(f"Topic analysis complete: is_relevant={analysis.get('is_niche_relevant')}, is_core={analysis.get('is_core_niche')}")
            return analysis
        except Exception as e:
            logger.error(f"Error during topic analysis: {e}")
            return {
                "is_niche_relevant": False,
                "is_core_niche": False,
                "reason_chosen": f"Error: {str(e)}",
                "business_opportunity": "",
                "business_lesson": "",
                "suggested_angle": "",
                "suggested_opening": ""
            }
