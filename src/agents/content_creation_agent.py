"""ContentCreationAgent - Generates content based on insights and content plans."""

import json
from typing import Dict, List

from src.agents.base_agent import BaseAgent
from src.database.connection import get_db
from src.database.models import ContentPlan, ContentFormat
from src.utils.llm_client import llm_client
from config.config import settings


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

        # Use global LLM client (supports Gemini & Claude with failover)
        self.llm_client = llm_client

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

    async def execute(self, *args, **kwargs) -> Dict:
        """
        Execute content creation for pending content plans.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
                     - content_plan (list, optional): List of content items to process immediately.

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

        # Check for direct input via kwargs (e.g., from orchestrator or helper script)
        direct_content_plans = kwargs.get('content_plan') or kwargs.get('content_plans')

        if direct_content_plans:
            # Handle direct execution with provided plans (bypassing DB for immediate response)
            self.log_info(f"Processing {len(direct_content_plans)} provided content plans directly")

            for item in direct_content_plans:
                try:
                    # Map dictionary item to a mock plan/insight structure for generation
                    # This is a bit of a hack to reuse existing generation methods

                    # Determine format
                    fmt = item.get('format', 'tweet').lower()
                    if 'thread' in fmt:
                        item_format = ContentFormat.THREAD
                    elif 'telegram' in fmt:
                        item_format = ContentFormat.TELEGRAM_MESSAGE
                    elif 'blog' in fmt:
                        item_format = ContentFormat.BLOG_POST
                    else:
                        item_format = ContentFormat.SINGLE_TWEET

                    # Create a MockInsight-like object
                    class MockInsight:
                        def __init__(self, data):
                            self.asset = data.get('keywords', ['CRYPTO'])[0]
                            self.type = type('obj', (object,), {'value': data.get('main_topic', 'General Update')})
                            self.confidence = 0.9
                            self.details = data

                    class MockPlan:
                        def __init__(self, item, insight):
                            self.id = item.get('item_id', 'mock_id')
                            self.format = item_format
                            self.insight = insight

                    mock_insight = MockInsight(item)
                    mock_plan = MockPlan(item, mock_insight)

                    # Generate content
                    content = await self._generate_content(mock_plan)

                    if content:
                        results["content_created"] += 1
                        results["generated_content"] = results.get("generated_content", [])
                        results["generated_content"].append(content)

                        # Track by type
                        if item_format == ContentFormat.SINGLE_TWEET:
                            results["tweets"] += 1
                        elif item_format == ContentFormat.THREAD:
                            results["threads"] += 1
                        elif item_format == ContentFormat.TELEGRAM_MESSAGE:
                            results["telegram_messages"] += 1

                except Exception as e:
                    error_msg = f"Error creating content for item: {e}"
                    self.log_error(error_msg)
                    results["errors"].append(error_msg)

            return results

        try:
            # Query and process plans within same session
            from sqlalchemy.orm import joinedload

            with get_db() as db:
                # Query plans with insights eagerly loaded in same session
                pending_plans = db.query(ContentPlan).options(
                    joinedload(ContentPlan.insight)
                ).filter(
                    ContentPlan.status == "pending"
                ).limit(10).all()

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

    async def _get_pending_plans(self) -> List[ContentPlan]:
        """
        Get content plans that are pending content creation.

        Returns:
            List of pending content plans
        """
        from sqlalchemy.orm import joinedload

        with get_db() as db:
            plans = db.query(ContentPlan).options(
                joinedload(ContentPlan.insight)
            ).filter(
                ContentPlan.status == "pending"
            ).limit(10).all()  # Process 10 at a time

            # Expunge objects from session so they can be used outside
            for plan in plans:
                db.expunge(plan)

            return plans

    async def _generate_content(self, plan: ContentPlan) -> Dict:
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
        elif plan.format == ContentFormat.THREAD:
            return await self._generate_thread(insight, plan)
        elif plan.format == ContentFormat.TELEGRAM_MESSAGE:
            return await self._generate_telegram_message(insight, plan)
        elif plan.format == ContentFormat.BLOG_POST:
            return await self._generate_blog_post(insight, plan)
        else:
            return await self._generate_tweet(insight, plan)

    async def _generate_tweet(self, insight, plan: ContentPlan) -> Dict:
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
            # Use Gemini by default (Anthropic has no credits)
            tweet_text = await self.llm_client.generate(
                prompt=prompt,
                model="gemini",
                max_tokens=150
            )
            tweet_text = tweet_text.strip()

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

    async def _generate_thread(self, insight, plan: ContentPlan) -> Dict:
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
            # Use Gemini by default (Anthropic has no credits)
            response_text = await self.llm_client.generate(
                prompt=prompt,
                model="gemini",
                max_tokens=800
            )
            response_text = response_text.strip()

            # Try to parse as JSON
            try:
                # Extract JSON array from the response
                start_idx = response_text.find('[')
                end_idx = response_text.rfind(']') + 1
                json_str = response_text[start_idx:end_idx]
                thread_tweets = json.loads(json_str)
            except:
                # Fallback: split by newlines
                thread_tweets = [
                    t.strip()
                    for t in response_text.split('\n')
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

    async def _generate_telegram_message(self, insight, plan: ContentPlan) -> Dict:
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
            # Use Gemini by default (Anthropic has no credits)
            telegram_text = await self.llm_client.generate(
                prompt=prompt,
                model="gemini",
                max_tokens=500
            )
            telegram_text = telegram_text.strip()

            return {
                "text": telegram_text,
                "format": "telegram",
                "content_plan_id": plan.id
            }

        except Exception as e:
            self.log_error(f"Error generating Telegram message: {e}")
            return None

    async def _generate_blog_post(self, insight, plan: ContentPlan) -> Dict:
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
            # Use Gemini by default (Anthropic has no credits)
            blog_text = await self.llm_client.generate(
                prompt=prompt,
                model="gemini",
                max_tokens=1500
            )
            blog_text = blog_text.strip()

            # Extract title (first line starting with #)
            lines = blog_text.split('\n')
            title = lines[0].replace('#', '').strip() if lines else "Market Analysis"

            return {
                "title": title,
                "text": blog_text,
                "format": "blog",
                "content_plan_id": plan.id
            }

        except Exception as e:
            self.log_error(f"Error generating blog post: {e}")
            return None
