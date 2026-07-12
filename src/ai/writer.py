import logging
from openai import OpenAI
from src.config import Config

logger = logging.getLogger(__name__)

class PostWriter:
    def __init__(self):
        self.enabled = bool(Config.OPENAI_API_KEY)
        self.client = None
        if self.enabled:
            self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        else:
            logger.warning("OpenAI API key not configured. Post writing is disabled.")

    def generate_post(self, topic_title, analysis_data):
        """Generates an X post based on topic analysis data using strict human-like rules."""
        if not self.enabled or not self.client:
            return "OpenAI API not configured. Cannot write post."

        prompt = f"""
You are an experienced entrepreneur, founder, and business mentor writing for CalebReview.
Your style is professional, confident, human, practical, and conversational.
You NEVER sound like standard AI, ChatGPT, or a journalist. You do not write filler or exaggerate.

Topic: {topic_title}
Niche: {analysis_data.get('niche')}
Business Opportunity: {analysis_data.get('business_opportunity')}
Business Lesson: {analysis_data.get('business_lesson')}
Suggested Angle: {analysis_data.get('suggested_angle')}
Suggested Opening: {analysis_data.get('suggested_opening')}

---

### WRITING RULES:
1. **Never use these AI phrases**: "In today's fast-paced world", "As we all know", "Game changer", "Revolutionary", "Leverage", "Unlock your potential", "Here's why".
2. **Avoid clichés** and generic motivational quotes.
3. **Minimize emoji use** — only use them if they genuinely improve readability (maximum 1-2, or none).
4. **Structure the post exactly like this flow**:
   - Section 1: Strong opening (hook the reader)
   - Section 2: Interesting insight (what's the shift in perspective?)
   - Section 3: Practical lesson (how can they use it?)
   - Section 4: Real-world implication (what happens next?)
   - Section 5: Thought-provoking ending (a closing thought or question)
5. **Formatting**: Use clean spacing and line breaks. Keep paragraphs short and punchy.
6. **Platform Limit**: The post must be written for X (Twitter), so keep the total length under 280 characters if possible, or up to 500 characters (assuming X Premium is supported, but aim for a punchy, clean post under 280 characters to be safe and effective, or slightly longer if necessary to deliver the lesson fully. Let's aim for a tight, high-impact post around 200-280 characters).

Write the post now:
"""
        try:
            # First draft
            response = self.client.chat.completions.create(
                model="gpt-4o", # We use gpt-4o for high-quality writing
                messages=[
                    {"role": "system", "content": "You are a professional social media ghostwriter for top entrepreneurs."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.75
            )
            draft = response.choices[0].message.content.strip()
            
            # Post Quality Check loop
            refined_post = self._quality_check_and_refine(draft, topic_title, analysis_data)
            return refined_post
        except Exception as e:
            logger.error(f"Error during post generation: {e}")
            return f"Error writing post: {str(e)}"

    def _quality_check_and_refine(self, draft, topic_title, analysis_data):
        """Performs a quality check on the generated post, rewriting if it sounds like AI."""
        check_prompt = f"""
Analyze the following draft social media post and determine if it sounds like a human entrepreneur wrote it, or if it sounds like a robotic AI:

Draft:
\"\"\"
{draft}
\"\"\"

### CRITERIA:
- Does it sound robotic or like ChatGPT?
- Does it contain forbidden words (e.g. leverage, game changer, revolutionary, in today's fast-paced, unlock your potential)?
- Is there a clear, practical lesson for entrepreneurs, freelancers, or business owners?
- Would an entrepreneur save this?

If it fails any criteria, rewrite it to make it sound completely human, direct, and valuable.
Otherwise, output the draft exactly as is.

Write the final post text below (do not include labels or formatting other than the post itself):
"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a perfectionist editor. Output ONLY the finalized tweet/post content, with no metadata or quotes."},
                    {"role": "user", "content": check_prompt}
                ],
                temperature=0.5
            )
            refined = response.choices[0].message.content.strip()
            # Remove enclosing quotes if the AI added them
            if refined.startswith('"') and refined.endswith('"'):
                refined = refined[1:-1]
            return refined
        except Exception as e:
            logger.error(f"Error during quality check: {e}")
            return draft
