"""ContentCreationAgent - Generates content based on insights and content plans."""

import json

from anthropic import Anthropic

from config.config import settings
from src.agents.base_agent import BaseAgent
from src.database.connection import get_db
from src.database.models import ContentFormat, ContentPlan


class ContentCreationAgent(BaseAgent):
    """
    The Content Creation Agent generates actual content text.

    Responsibilities:
    - Generate content based on content plans
    - Maintain consistent brand voice and personality
    - Format content for different platforms
    - Generate engaging headlines and hooks
    """

    def __init__(self):
        """Initialize the ContentCreationAgent."""
        super().__init__("ContentCreationAgent")

        # Initialize LLM client
        self.llm_client = Anthropic(api_key=settings.anthropic_api_key)

        # Content personality from config
        self.personality = settings.content_personality

        # Personality templates
        self.personality_prompts = {
            "hyper-analytical": (
                "You are a data-driven crypto analyst. Your tone is professional, "
                "analytical, and focused on facts. You use specific numbers and metrics. "
                "You avoid hype and stick to what the data shows."
            ),
            "bold": (
                "You are a bold crypto trader with strong opinions. Your tone is "
                "confident and direct. You're not afraid to make calls. You use "
                "casual language but back it up with data."
            ),
            "educational": (
                "You are a crypto educator. Your tone is helpful and informative. "
                "You explain concepts clearly and help people learn. You're patient "
                "and encouraging."
            )
        }

    async def execute(self) -> dict:
        """
        Execute content creation for pending content plans.

        Returns:
            Dictionary with creation results
        """
        self.log_info("Starting content creation...")

        results = {
            "content_created": 0,
            "tweets": 0,
            "threads": 0,
            "telegram_messages": 0,
            "errors": []
        }

        try:
            # Get pending content plans
            pending_plans = await self._get_pending_plans()

            with get_db() as db:
                for plan in pending_plans:
                    try:
                        # Generate content based on format
                        content = await self._generate_content(plan)

                        if content:
                            # Store generated content in the plan
                            # (We'll use a JSON field for now)
                            plan.status = "ready"  # Ready for publishing
                            results["content_created"] += 1

                            # Track by type
                            if plan.format == ContentFormat.SINGLE_TWEET:
                                results["tweets"] += 1
                            elif plan.format == ContentFormat.THREAD:
                                results["threads"] += 1
                            elif plan.format in [
                                ContentFormat.TELEGRAM_MESSAGE,
                                ContentFormat.IMAGE_POST
                            ]:
                                results["telegram_messages"] += 1

                            self.log_info(
                                f"Created {plan.format.value} for "
                                f"{plan.insight.asset} ({plan.insight.type.value})"
                            )

                    except Exception as e:
                        error_msg = f"Error creating content for plan {plan.id}: {e}"
                        self.log_error(error_msg)
                        results["errors"].append(error_msg)

                db.commit()

            self.log_info(
                f"Content creation complete: {results['content_created']} pieces created"
            )

        except Exception as e:
            self.log_error(f"Content creation error: {e}")
            raise

        return results

    async def _get_pending_plans(self) -> list[ContentPlan]:
        """
        Get content plans that are pending content creation.

        Returns:
            List of pending content plans
        """
        with get_db() as db:
            return db.query(ContentPlan).filter(
                ContentPlan.status == "pending"
            ).limit(10).all()  # Process 10 at a time


    async def _generate_content(self, plan: ContentPlan) -> dict:
        """
        Generate content for a content plan.

        Args:
            plan: ContentPlan object

        Returns:
            Dictionary with generated content
        """
        insight = plan.insight

        # Choose generation method based on format
        if plan.format == ContentFormat.SINGLE_TWEET:
            return await self._generate_tweet(insight, plan)
        if plan.format == ContentFormat.THREAD:
            return await self._generate_thread(insight, plan)
        if plan.format == ContentFormat.TELEGRAM_MESSAGE:
            return await self._generate_telegram_message(insight, plan)
        if plan.format == ContentFormat.BLOG_POST:
            return await self._generate_blog_post(insight, plan)
        return await self._generate_tweet(insight, plan)

    async def _generate_tweet(self, insight, plan: ContentPlan) -> dict:
        """Generate a single tweet."""
        personality = self.personality_prompts.get(
            self.personality,
            self.personality_prompts["hyper-analytical"]
        )

        prompt = f"""{personality}

Create a single tweet (max 280 characters) about this crypto insight:

Asset: {insight.asset}
Type: {insight.type.value}
Confidence: {insight.confidence:.0%}
Details: {json.dumps(insight.details, indent=2)}

Requirements:
- Max 280 characters
- Include ${insight.asset} ticker
- Use 1-2 relevant hashtags
- Make it engaging and informative
- Match the personality described above

Tweet:"""

        try:
            message = self.llm_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=150,
                messages=[{"role": "user", "content": prompt}]
            )

            tweet_text = message.content[0].text.strip()

            # Ensure it fits in 280 characters
            if len(tweet_text) > 280:
                tweet_text = tweet_text[:277] + "..."

            return {
                "text": tweet_text,
                "format": "tweet",
                "content_plan_id": plan.id
            }

        except Exception as e:
            self.log_error(f"Error generating tweet: {e}")
            return None

    async def _generate_thread(self, insight, plan: ContentPlan) -> dict:
        """Generate a Twitter thread."""
        personality = self.personality_prompts.get(
            self.personality,
            self.personality_prompts["hyper-analytical"]
        )

        # Determine thread length based on confidence and detail
        thread_length = 5 if insight.confidence >= 0.85 else 3

        prompt = f"""{personality}

Create a Twitter thread with {thread_length} tweets about this crypto insight:

Asset: {insight.asset}
Type: {insight.type.value}
Confidence: {insight.confidence:.0%}
Details: {json.dumps(insight.details, indent=2)}

Requirements:
- Exactly {thread_length} tweets
- Each tweet max 280 characters
- First tweet should hook the reader
- Include data and specific numbers
- Use ${insight.asset} ticker in first tweet
- Add relevant hashtags at the end
- Match the personality described above
- Number each tweet (1/X, 2/X, etc.)

Return as a JSON array of strings, e.g.:
["Tweet 1 text...", "Tweet 2 text...", "Tweet 3 text..."]

Thread:"""

        try:
            message = self.llm_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=800,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = message.content[0].text.strip()

            # Try to parse as JSON
            try:
                # Extract JSON array from the response
                start_idx = response_text.find("[")
                end_idx = response_text.rfind("]") + 1
                json_str = response_text[start_idx:end_idx]
                thread_tweets = json.loads(json_str)
            except:
                # Fallback: split by newlines
                thread_tweets = [
                    t.strip()
                    for t in response_text.split("\n")
                    if t.strip() and len(t.strip()) > 10
                ][:thread_length]

            # Ensure each tweet fits in 280 characters
            thread_tweets = [
                tweet[:277] + "..." if len(tweet) > 280 else tweet
                for tweet in thread_tweets
            ]

            return {
                "tweets": thread_tweets,
                "format": "thread",
                "content_plan_id": plan.id
            }

        except Exception as e:
            self.log_error(f"Error generating thread: {e}")
            return None

    async def _generate_telegram_message(self, insight, plan: ContentPlan) -> dict:
        """Generate a Telegram message."""
        personality = self.personality_prompts.get(
            self.personality,
            self.personality_prompts["hyper-analytical"]
        )

        # Telegram allows markdown formatting
        prompt = f"""{personality}

Create a Telegram message about this crypto insight:

Asset: {insight.asset}
Type: {insight.type.value}
Confidence: {insight.confidence:.0%}
Details: {json.dumps(insight.details, indent=2)}

Requirements:
- Use Telegram Markdown formatting (bold, italic, code)
- 2-4 paragraphs
- Include specific data and numbers
- Add a clear conclusion or takeaway
- Match the personality described above

Message:"""

        try:
            message = self.llm_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )

            telegram_text = message.content[0].text.strip()

            return {
                "text": telegram_text,
                "format": "telegram",
                "content_plan_id": plan.id
            }

        except Exception as e:
            self.log_error(f"Error generating Telegram message: {e}")
            return None

    async def _generate_blog_post(self, insight, plan: ContentPlan) -> dict:
        """Generate a blog post."""
        personality = self.personality_prompts.get(
            self.personality,
            self.personality_prompts["educational"]
        )

        prompt = f"""{personality}

Write a detailed blog post about this crypto insight:

Asset: {insight.asset}
Type: {insight.type.value}
Confidence: {insight.confidence:.0%}
Details: {json.dumps(insight.details, indent=2)}

Requirements:
- Include a catchy title
- 400-600 words
- Use headers and sections
- Include specific data and analysis
- Add a conclusion with key takeaways
- Write in Markdown format
- Match the personality described above

Blog Post:"""

        try:
            message = self.llm_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )

            blog_text = message.content[0].text.strip()

            # Extract title (first line starting with #)
            lines = blog_text.split("\n")
            title = lines[0].replace("#", "").strip() if lines else "Market Analysis"

            return {
                "title": title,
                "text": blog_text,
                "format": "blog",
                "content_plan_id": plan.id
            }

        except Exception as e:
            self.log_error(f"Error generating blog post: {e}")
            return None
