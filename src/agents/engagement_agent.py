"""EngagementAgent - Monitors and engages with the audience."""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Optional

from anthropic import Anthropic

from config.config import settings
from src.agents.base_agent import BaseAgent
from src.api_integrations.twitter_api import TwitterAPI
from src.database.connection import get_db
from src.database.models import PublishedContent

import json
from src.agents.base_agent import BaseAgent
from src.utils.llm_client import llm_client
from loguru import logger

class EngagementAgent(BaseAgent):
    SYSTEM_PROMPT = '''
    As an advanced AI agent named "EngagementAgent" within the GEMINI Content Creator system, your primary directive is to serve as a specialized **Community Interaction and Relationship Builder**. Your persona is that of a knowledgeable, empathetic, and strategically-minded expert in crypto markets and community dynamics, dedicated to fostering a vibrant, loyal, and positively engaged audience.

    **Objective:**
    Your core objective is to actively monitor social media platforms for mentions, comments, and relevant discussions related to our crypto-market content. You are to generate contextually appropriate, high-quality replies, strategically like relevant posts, and initiate discussions that stimulate community growth and significantly enhance audience loyalty. The ultimate goal is to cultivate a strong, interactive community around our insights and content.

    **Theoretical Constraints & Frameworks:**
    Your operational model is rigorously grounded in a multi-disciplinary academic framework:

    1.  **Natural Language Understanding (NLU):** You must apply advanced NLU techniques to accurately parse, interpret, and contextualize all forms of social media text. This includes sentiment analysis (positive, neutral, negative), intent recognition (question, critique, compliment, discussion), topic modeling, entity extraction, and understanding the nuances of crypto-specific jargon, slang, and cultural references. This ensures responses are always highly relevant and appropriately toned.

    2.  **Social Network Analysis (SNA):** You are equipped to analyze the underlying structure of social interactions. This involves identifying key influencers, assessing user connectivity, understanding conversational hubs, and tracking information flow. Your decisions on whom to engage with, when, and how, are informed by SNA to maximize reach, foster network density, and amplify positive sentiment within the community.

    3.  **Dialog Systems:** You will employ principles of sophisticated dialog systems to craft coherent, context-aware, and natural-sounding conversational responses. This includes managing conversational state, maintaining topic continuity, employing appropriate turn-taking strategies, and ensuring that each interaction contributes to building rapport and guiding discussions effectively towards project goals.

    4.  **Behavioral Economics:** You are tasked with leveraging insights from behavioral economics to strategically design interactions that encourage desired user behaviors. This involves understanding cognitive biases and heuristics to:
        *   Promote reciprocity (by providing value).
        *   Utilize social proof (by highlighting popular content or influential users).
        *   Foster commitment (by encouraging participation and contribution).
        *   Strategically frame messages to maximize engagement, loyalty, and positive brand association.

    **Workflow & Decision Process (Think Step-by-Step, Verify Assumptions):**

    **Input:** A JSON object representing a social media event. This object will contain pertinent information such as the `post_content`, `platform`, `user_id`, `post_id`, and any additional `context` relevant to the current market or project status.

    **Steps:**

    1.  **Ingestion and Initial Analysis (NLU, SNA):**
        *   **Deconstruct Input:** Parse the provided JSON input. Extract `post_content`, `user_id`, `platform`, `post_id`, and `context`.
        *   **NLU Processing:** Perform detailed sentiment analysis (e.g., POSITIVE, NEUTRAL, NEGATIVE), identify the user's explicit and implicit intent (e.g., QUESTION, COMPLIMENT, CRITICISM, GENERAL_COMMENT, DISCUSSION_STARTER), and extract key topics or entities from the `post_content`.
        *   **SNA Assessment:** If `user_id` is available, query internal records or simulated external data (if applicable) to retrieve the user's historical interaction patterns, perceived influence within the network, and previous sentiment expressed towards our content. Evaluate the `context` for broader trending discussions or relevant events.

    2.  **Engagement Strategy Determination (Behavioral Economics, SNA, Dialog Systems):**
        *   **Action Type Selection:** Based on the comprehensive analysis from Step 1, determine the most optimal engagement action:
            *   `REPLY`: For direct questions, constructive criticism, compliments, or mentions requiring a tailored textual response.
            *   `LIKE`: For positive or neutral posts that acknowledge engagement without requiring a full textual reply, leveraging social proof.
            *   `INITIATE_DISCUSSION`: If the input presents a strategic opportunity to pivot into a broader community discussion that aligns with project goals (e.g., a general market observation that can be expanded).
            *   `IGNORE`: Only for spam, highly irrelevant content, or extreme toxicity (minimize this where possible, preferring de-escalation via REPLY).
        *   **Behavioral Goal Definition:** Clearly define the specific behavioral outcome desired from this interaction (e.g., inform the user, solicit further information, express gratitude, de-escalate tension, encourage peer interaction, reinforce loyalty).
        *   **Tone and Persona Consistency:** Ensure the chosen strategy and subsequent content align perfectly with the project's expert, helpful, and personable AI persona.

    3.  **Content Generation / Action Detailing (Dialog Systems, NLU):**
        *   **If REPLY:** Synthesize a concise, contextually accurate, and engaging textual response. It must directly address the user's point, provide value, maintain a positive tone (or appropriately neutralize negative tone), and encourage continued interaction.
        *   **If LIKE:** Confirm the `LIKE` action, indicating no textual content is needed.
        *   **If INITIATE_DISCUSSION:** Formulate a compelling discussion prompt or open-ended question that extends from the original input, designed to invite broader community participation and drive engagement.
        *   **Verify Assumptions:** Critically review the generated action/response. Does it accurately reflect the user's intent? Is the tone appropriate? Does it align with the defined behavioral goal and theoretical frameworks? Is it free of factual errors or misinterpretations? Correct any discrepancies before outputting.

    **Output Format:**
    Your final output MUST be a valid JSON object following this exact schema. Do not include any additional text or formatting outside the JSON.

    json
    {
        "action_type": "REPLY" | "LIKE" | "INITIATE_DISCUSSION" | "IGNORE",
        "details": {
            "platform": "Twitter" | "Discord" | "Reddit" | "Other",
            "post_id": "string_identifier_of_original_post",
            "user_id": "string_identifier_of_target_user",
            "response_text": "string_generated_text_if_REPLY_or_INITIATE_DISCUSSION_otherwise_empty",
            "discussion_prompt": "string_generated_prompt_if_INITIATE_DISCUSSION_otherwise_empty",
            "sentiment_analysis": "POSITIVE" | "NEUTRAL" | "NEGATIVE",
            "intent_analysis": "QUESTION" | "COMPLIMENT" | "CRITICISM" | "GENERAL_COMMENT" | "DISCUSSION_STARTER" | "UNKNOWN"
        },
        "reasoning": "A concise, academic explanation of the chosen action type and its details, explicitly referencing the applied theoretical frameworks (NLU, SNA, Dialog Systems, Behavioral Economics) and the steps taken."
    }
    
    '''

    def __init__(self):
        super().__init__("EngagementAgent")
        self.llm = llm_client

    async def execute(self, *args, **kwargs):
        logger.info(f"EngagementAgent received execute call. Args: {args}, Kwargs: {kwargs}")

        # Consolidate input from args and kwargs. kwargs are preferred for structured data.
        input_data = {}
        if args:
            # If the first positional argument is a dict, it's likely the primary input payload
            if isinstance(args[0], dict):
                input_data.update(args[0])
            # If it's a string, consider it the main post_content
            elif isinstance(args[0], str) and "post_content" not in kwargs:
                input_data["post_content"] = args[0]
        
        # kwargs always take precedence for specific fields, or provide additional structured input
        input_data.update(kwargs)

        if not input_data.get("post_content") and not input_data:
            logger.warning("EngagementAgent received no discernible input for execution. 'post_content' missing or input_data empty.")
            return {
                "action_type": "IGNORE",
                "details": {
                    "platform": "N/A",
                    "post_id": "N/A",
                    "user_id": "N/A",
                    "response_text": "No valid input (e.g., 'post_content') provided to the agent.",
                    "sentiment_analysis": "UNKNOWN",
                    "intent_analysis": "UNKNOWN"
                },
                "reasoning": "Agent requires specific social media input (e.g., 'post_content') to perform engagement. Input was either empty or lacked essential fields."
            }

        # Initialize APIs
        try:
            self.twitter_api = TwitterAPI(
                api_key=settings.twitter_api_key,
                api_secret=settings.twitter_api_secret,
                access_token=settings.twitter_access_token,
                access_token_secret=settings.twitter_access_token_secret,
                bearer_token=settings.twitter_bearer_token,
            )
        except Exception as e:
            self.log_warning(f"Twitter API not configured: {e}")
            self.twitter_api = None

        # Initialize LLM for generating replies
        self.llm_client = Anthropic(api_key=settings.anthropic_api_key)

        # Engagement parameters
        self.auto_like_threshold = 0.3  # Like posts with sentiment > 0.3
        self.auto_reply_enabled = True
        self.max_replies_per_run = 10
        self.max_likes_per_run = 50

        # Track engaged users for later conversion
        self.engaged_users = {}

    async def execute(self) -> dict:
        """
        Execute the engagement process.

        Returns:
            Dictionary with engagement results
        """
        self.log_info("Starting audience engagement...")

        results = {
            "mentions_processed": 0,
            "replies_sent": 0,
            "likes_given": 0,
            "retweets": 0,
            "engaged_users_tracked": 0,
            "errors": [],
        }

        if not self.twitter_api:
            self.log_warning("Twitter API not available, skipping engagement")
            return results

        try:
            # Get our recent published content
            recent_content = await self._get_recent_published_content()

            # Run engagement tasks in parallel
            tasks = [
                self._monitor_and_respond_to_mentions(),
                self._engage_with_replies(recent_content),
                self._find_and_retweet_influential_content(),
                self._update_engagement_metrics(recent_content),
            ]

            task_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            for i, result in enumerate(task_results):
                if isinstance(result, Exception):
                    results["errors"].append(str(result))
                elif i == 0:  # Mentions
                    results["mentions_processed"] = result.get("mentions", 0)
                    results["replies_sent"] += result.get("replies", 0)
                elif i == 1:  # Replies
                    results["likes_given"] = result.get("likes", 0)
                    results["replies_sent"] += result.get("replies", 0)
                elif i == 2:  # Retweets
                    results["retweets"] = result.get("retweets", 0)
                elif i == 3:  # Metrics
                    results["engaged_users_tracked"] = result.get("users_tracked", 0)

            self.log_info(
                f"Engagement complete: {results['replies_sent']} replies, "
                f"{results['likes_given']} likes, {results['retweets']} retweets"
            )

        except Exception as e:
            self.log_error(f"Engagement error: {e}")
            raise

        return results

    async def _get_recent_published_content(self) -> list[PublishedContent]:
        """Get recently published content from the last 24 hours."""
        cutoff_time = datetime.now(tz=timezone.utc) - timedelta(hours=24)

        with get_db() as db:
            return (
                db.query(PublishedContent)
                .filter(
                    PublishedContent.platform == "twitter",
                    PublishedContent.published_at >= cutoff_time,
                )
                .all()
            )

    async def _monitor_and_respond_to_mentions(self) -> dict:
        """Monitor mentions and respond to them."""
        self.log_info("Monitoring mentions...")

        results = {"mentions": 0, "replies": 0}

        try:
            # Search for mentions (simplified - would use Twitter API properly)
            # For now, we'll search for our typical hashtags
            mentions = self.twitter_api.search_tweets(
                query="to:our_handle OR @our_handle",  # Replace with actual handle
                max_results=50,
            )

            results["mentions"] = len(mentions)

            # Process each mention
            reply_count = 0
            for mention in mentions[: self.max_replies_per_run]:
                if await self._should_reply_to_tweet(mention):
                    reply = await self._generate_reply(mention)

                    if reply:
                        # Post reply (in practice)
                        self.log_info(f"Would reply to {mention['id']}: {reply}")
                        reply_count += 1

                        # Track this user as engaged
                        await self._track_engaged_user(mention.get("author_id"))

            results["replies"] = reply_count

        except Exception as e:
            self.log_error(f"Error monitoring mentions: {e}")
            raise

        return results

    async def _engage_with_replies(self, recent_content: list[PublishedContent]) -> dict:
        """Engage with replies to our content."""
        self.log_info("Engaging with replies...")

        results = {"likes": 0, "replies": 0}

        try:
            for content in recent_content:
                if not content.post_id:
                    continue

                # In practice, fetch replies to this tweet
                # For now, we'll simulate
                self.log_info(f"Processing replies to post {content.post_id}")

                # TODO: Implement actual reply fetching and processing:
                # 1. Fetch replies from Twitter API
                # 2. Analyze sentiment
                # 3. Like if positive
                # 4. Reply if it's a question
                # 5. Track engaged users

        except Exception as e:
            self.log_error(f"Error engaging with replies: {e}")

        return results

    async def _find_and_retweet_influential_content(self) -> dict:
        """Find and retweet relevant content from influential accounts."""
        self.log_info("Finding influential content to retweet...")

        results = {"retweets": 0}

        try:
            # Define crypto influencers to monitor
            influencers = [
                "VitalikButerin",
                "cz_binance",
                "elonmusk",
                "APompliano",
                "saylor",
                "CryptoCobain",
            ]

            # Search for relevant tweets from influencers
            for influencer in influencers[:3]:  # Limit to avoid rate limits
                query = f"from:{influencer} (crypto OR bitcoin OR ethereum)"

                tweets = self.twitter_api.search_tweets(query, max_results=10)

                # Analyze and potentially retweet
                for tweet in tweets[:1]:  # Max 1 retweet per influencer
                    if await self._should_retweet(tweet):
                        self.log_info(f"Would retweet from {influencer}: {tweet['text'][:50]}...")
                        results["retweets"] += 1

        except Exception as e:
            self.log_error(f"Error finding influential content: {e}")

        return results

    async def _update_engagement_metrics(self, recent_content: list[PublishedContent]) -> dict:
        """Update engagement metrics for recent content."""
        self.log_info("Updating engagement metrics...")

        results = {"users_tracked": 0}

        # Note: In practice, fetch actual metrics from Twitter API
        # This would update content.views, content.likes, etc.
        for content in recent_content:
            # - content.likes
            # - content.comments
            # - content.shares
            # - content.engagement_rate

            self.log_info(f"Would update metrics for post {content.post_id}")

        # Track highly engaged users
        results["users_tracked"] = len(self.engaged_users)

        return results

    async def _should_reply_to_tweet(self, tweet: dict) -> bool:
        """
        Determine if we should reply to a tweet.

        Args:
            tweet: Tweet data

        Returns:
            True if we should reply
        """
        # Don't reply to tweets we've already replied to
        # Check if it's a question
        # Check if it's positive/neutral sentiment

        text = tweet.get("text", "").lower()

        # Simple heuristics
        is_question = "?" in text or any(
            word in text for word in ["how", "what", "when", "where", "why", "which"]
        )

        has_negative_sentiment = any(
            word in text for word in ["scam", "fraud", "fake", "lie", "shit"]
        )

        return is_question and not has_negative_sentiment

    async def _generate_reply(self, tweet: dict) -> Optional[str]:
        """
        Generate an intelligent reply to a tweet using LLM.

        Args:
            tweet: Tweet data
        user_message_content = json.dumps(input_data)
        
        logger.debug(f"EngagementAgent sending request to LLM with input: {user_message_content}")

        try:
            prompt = f"""You are a helpful crypto analyst responding to a community member.

Tweet: "{tweet['text']}"

Generate a helpful, concise reply (max 280 characters) that:
1. Answers their question if there is one
2. Is friendly and professional
3. Encourages them to check our content for more info
4. Ends with a relevant emoji

Reply:"""

            message = self.llm_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=150,
                messages=[{"role": "user", "content": prompt}],
            )

            reply = message.content[0].text.strip()

            # Ensure it fits Twitter limits
            if len(reply) > 280:
                reply = reply[:277] + "..."

            return reply

        except Exception as e:
            self.log_error(f"Error generating reply: {e}")
            return None

    async def _should_retweet(self, tweet: dict) -> bool:
        """
        Determine if we should retweet content.

        Args:
            tweet: Tweet data

        Returns:
            True if we should retweet
        """
        # Check engagement levels
        likes = tweet.get("likes", 0)
        retweets = tweet.get("retweets", 0)

        # High engagement threshold
        min_engagement = 100

        # Check content relevance
        text = tweet.get("text", "").lower()
        relevant_keywords = [
            "bitcoin",
            "ethereum",
            "crypto",
            "blockchain",
            "defi",
            "nft",
            "web3",
            "altcoin",
        ]

        is_relevant = any(keyword in text for keyword in relevant_keywords)
        has_good_engagement = (likes + retweets * 2) >= min_engagement

        return is_relevant and has_good_engagement

    async def _track_engaged_user(self, user_id: str):
        """
        Track a user who has engaged with our content.

        Args:
            user_id: Twitter user ID
        """
        if user_id not in self.engaged_users:
            self.engaged_users[user_id] = {
                "first_interaction": datetime.now(tz=timezone.utc),
                "interaction_count": 1,
                "last_interaction": datetime.now(tz=timezone.utc),
            }
        else:
            self.engaged_users[user_id]["interaction_count"] += 1
            self.engaged_users[user_id]["last_interaction"] = datetime.now(tz=timezone.utc)

        # Note: Would save to an engaged_users table for later use by ConversionAgent (Fase 3)
        # Database implementation pending

    async def get_highly_engaged_users(self, min_interactions: int = 3) -> list[dict]:
        """
        Get users who have engaged multiple times.

        Args:
            min_interactions: Minimum number of interactions

        Returns:
            List of highly engaged users
        """
        highly_engaged = [
            {"user_id": user_id, **data}
            for user_id, data in self.engaged_users.items()
            if data["interaction_count"] >= min_interactions
        ]

        # Sort by interaction count
        highly_engaged.sort(key=lambda x: x["interaction_count"], reverse=True)

        return highly_engaged

    async def send_custom_reply(self, tweet_id: str, reply_text: str) -> bool:
        """
        Send a custom reply to a specific tweet.

        Args:
            tweet_id: ID of the tweet to reply to
            reply_text: Text of the reply

        Returns:
            True if successful
        """
        if not self.twitter_api:
            return False

        try:
            # Create reply
            _ = self.twitter_api.client.create_tweet(text=reply_text, in_reply_to_tweet_id=tweet_id)

            self.log_info(f"Custom reply sent to tweet {tweet_id}")
            return True

            # Assume self.llm.generate expects system_prompt and user_message
            response_json_str = await self.llm.generate(
                system_prompt=self.SYSTEM_PROMPT,
                user_message=user_message_content
            )
            
            logger.debug(f"LLM raw response from EngagementAgent: {response_json_str}")

            # Attempt to parse the JSON response
            parsed_response = json.loads(response_json_str)
            
            # Basic validation of the response structure as per SYSTEM_PROMPT
            if not isinstance(parsed_response, dict) or "action_type" not in parsed_response or "details" not in parsed_response:
                raise ValueError("LLM response did not return a valid JSON object with 'action_type' and 'details' keys.")

            logger.info(f"EngagementAgent executed successfully. Action: {parsed_response.get('action_type', 'UNKNOWN')}")
            return parsed_response

        except json.JSONDecodeError as e:
            logger.error(f"EngagementAgent failed to parse LLM response as JSON: {e}. Raw response: '{response_json_str}'")
            return {
                "action_type": "ERROR",
                "details": {
                    "error_message": f"Failed to parse LLM response as JSON: {e}",
                    "raw_response": response_json_str
                },
                "reasoning": "JSON parsing error from LLM output. Ensure LLM returns strictly JSON."
            }
        except ValueError as e:
            logger.error(f"EngagementAgent received invalid LLM response structure: {e}. Raw response: '{response_json_str}'")
            return {
                "action_type": "ERROR",
                "details": {
                    "error_message": f"Invalid LLM response structure: {e}",
                    "raw_response": response_json_str
                },
                "reasoning": "LLM output did not conform to the expected JSON schema (e.g., missing 'action_type' or 'details')."
            }
        except Exception as e:
            logger.error(f"An unexpected error occurred during EngagementAgent execution: {e}", exc_info=True)
            return {
                "action_type": "ERROR",
                "details": {
                    "error_message": str(e),
                    "input_received": input_data
                },
                "reasoning": "An unhandled exception occurred during agent execution."
            }