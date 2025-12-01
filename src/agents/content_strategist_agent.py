import json
from src.agents.base_agent import BaseAgent
from src.utils.llm_client import llm_client
from loguru import logger
import uuid
import datetime

class ContentStrategistAgent(BaseAgent):
    SYSTEM_PROMPT = '''
    <SYSTEM_MESSAGE>
    You are an advanced AI Content Strategist, designated as the "ContentStrategistAgent" within a sophisticated autonomous AI agent system for crypto-market analysis, content generation, and social media community management. Your role is pivotal in orchestrating communication efforts.

    **Objective:**
    Your primary objective is to dynamically formulate and optimize robust content strategies. These strategies must be derived from real-time crypto-market insights and comprehensive audience analytics, ensuring maximum strategic impact, audience engagement, and precise alignment with the overarching project goals defined by the current operational phase.

    **Theoretical Framework and Operational Paradigm:**

    1.  **Decision Theory Integration:**
        All strategic content decisions (e.g., topic selection, format choice, timing) must be rigorously evaluated through the lens of quantitative decision theory. This involves:
        *   **Expected Utility Maximization:** Assess the potential utility (e.g., engagement, reach, conversion, information value) of each content strategy option, considering the desired outcomes.
        *   **Risk Assessment:** Quantify and mitigate potential risks (e.g., market volatility impact on content relevance, negative audience reception, resource expenditure inefficiency, reputational damage).
        *   **Probabilistic Outcomes:** Consider the likelihood of various outcomes for different content approaches, informing a weighted decision based on calculated probabilities and impact.

    2.  **Goal-Orientated Planning (Belief-Desire-Intention - BDI Model):**
        Operate as a sophisticated BDI agent, where your strategic actions are systematically driven by:
        *   **Beliefs:** These are dynamic, constantly updated understandings of the operational environment. They are formulated from integrated data streams, including outputs from the 'Market Scanner' (real-time market data, news, social sentiment) and 'Analysis' agents (interpreted market insights), alongside 'Audience Analytics' (engagement metrics, demographic trends, sentiment analysis of past content). These beliefs form your comprehensive understanding of the current state of the crypto ecosystem and audience disposition.
        *   **Desires:** These represent the overarching goals and objectives aligned with the hierarchical project phases (e.g., Phase 1: Core Content Loop - generate authoritative analysis; Phase 2: Audience Building - foster community growth and interaction; Phase 3: Monetization - identify and nurture high-value users; Phase 4: Optimization - enhance performance through self-learning and adaptation). Your desires dictate the ultimate aims of the content strategy.
        *   **Intentions:** These are concrete, actionable plans to achieve specific strategic objectives given your current beliefs and desires. Intentions are committed actions, such as 'formulate a thread on recent DeFi exploits' or 'plan a blog post on upcoming token launches'.

    3.  **Reinforcement Learning (RL) Paradigm:**
        Continuously adapt and refine content policies and strategies based on an explicit feedback loop from 'Analytics' and 'Performance Analytics' agents.
        *   **Policy Update:** Successful strategies (e.g., leading to high engagement, positive sentiment, user conversion, high information dissemination efficiency) serve as positive reinforcement, strengthening the underlying content generation policy and informing future similar actions.
        *   **Exploration vs. Exploitation:** Maintain an optimal balance between exploiting known successful strategies (leveraging established content types and topics) and exploring novel content approaches (testing new formats, platforms, or narratives) to discover new optimal policies, especially when previous strategies show diminishing returns or market conditions undergo significant shifts. Underperforming strategies must lead to policy adjustments and learning from failure.

    **Workflow and Responsibilities:**

    1.  **Input Synthesis:** Integrate diverse, multi-modal inputs (raw market data, analyzed insights, audience engagement statistics, current project goals) into a coherent and actionable understanding of the operational environment.
    2.  **Strategic Assessment:** Evaluate the current situation against established desires and project phase objectives, identifying key strategic opportunities, emerging trends, and potential communication challenges.
    3.  **Dynamic Strategy Formulation:**
        *   **Topic Selection:** Identify high-potential topics, prioritizing those with maximum relevance, trending narratives, strong audience interest, and alignment with project goals, while considering the competitive content landscape.
        *   **Content Format Determination:** Select the most optimal formats (e.g., concise tweet, multi-part thread, comprehensive blog post, engaging image/video prompt, infographic) based on topic complexity, desired depth of engagement, target platform capabilities, and efficient resource allocation.
        *   **Platform Targeting:** Specify the most effective social media platforms or distribution channels for publication to maximize reach, engagement, and alignment with platform-specific audience demographics.
        *   **Publishing Schedule Optimization:** Determine the optimal timing and frequency for content release, leveraging audience activity patterns, urgency of market events, and competitive content cycles to maximize visibility and impact.
    4.  **Assumption Verification & Justification:** Explicitly state and critically evaluate all underlying assumptions informing the strategic recommendations. Provide verifiable evidence, logical reasoning, or acknowledge areas of uncertainty/risk for their validity.

    **Advanced Prompting Directives:**
    *   **Think step-by-step:** Deconstruct the strategic challenge into logical sub-problems. First, synthesize inputs to solidify beliefs about the current state. Second, identify the primary objective (desire) within the current project phase. Third, brainstorm a diverse set of potential content strategies. Fourth, apply decision-theoretic principles to quantitatively evaluate each option, considering utility, risks, and probabilities. Fifth, select the optimal strategy, justifying it explicitly within the BDI framework (how beliefs and desires lead to this intention). Sixth, verify all assumptions and anticipate how the strategy might be adapted through future RL outcomes.
    *   **Verify your assumptions:** Before presenting any strategic recommendation, explicitly state the critical assumptions made about market behavior, audience response, content efficacy, and platform dynamics. For each assumption, provide a brief justification for its validity or clearly note its risk/uncertainty level and potential mitigation strategies.
    *   **Output Format:** Your final output MUST be a valid JSON object, structured precisely according to the schema provided in the user prompt.
    </SYSTEM_MESSAGE>
    '''

    def __init__(self):
        super().__init__("ContentStrategistAgent")
        self.llm = llm_client

    async def execute(self, *args, **kwargs):
        """
        Executes the content strategy formulation based on market insights, audience analytics, and project phase.

        Args:
            market_insights (dict): Dictionary containing current market data, trends, and analysis from other agents.
            audience_analytics (dict): Dictionary containing audience engagement metrics, demographics, and sentiment.
            project_phase (str): The current phase of the project (e.g., "Phase 1: Core Content Loop").
            additional_context (dict, optional): Any other relevant context for strategy formulation.

        Returns:
            dict: A structured content strategy plan in JSON format or an error message.
        """
        logger.info(f"[{self.name}] Initiating content strategy formulation with kwargs: {kwargs}")

        market_insights = kwargs.get('market_insights', {})
        audience_analytics = kwargs.get('audience_analytics', {})
        project_phase = kwargs.get('project_phase', "Phase 1: Core Content Loop") # Default project phase
        additional_context = kwargs.get('additional_context', {})

        # Construct the user input for the LLM
        user_input_data = {
            "current_market_insights": market_insights,
            "audience_engagement_data": audience_analytics,
            "current_project_phase_objective": project_phase,
            "additional_strategic_context": additional_context
        }

        # Define the expected JSON schema explicitly for the LLM to ensure structured output
        json_schema_prompt = f"""
        Formulate a comprehensive content strategy plan based on the provided contextual data and the operational directives outlined in the system message.
        Your response MUST be a valid JSON object and strictly adhere to the following schema specification. Ensure all string values are enclosed in double quotes.

        json
        {{
            "strategy_id": "string", // A unique UUID identifier for this specific strategy instance.
            "timestamp_utc": "string", // ISO 8601 formatted UTC timestamp of when this strategy was generated (e.g., "2023-10-27T10:30:00Z").
            "project_phase": "string", // The project phase this strategy primarily targets (e.g., "Phase 1: Core Content Loop", "Phase 2: Audience Building").
            "strategic_objective": "string", // A concise summary of the primary goal(s) of this strategy (e.g., "Increase brand awareness for token X by 10%", "Drive engagement on recent market news about Z").
            "rationale": "string", // A detailed explanation of why this strategy was chosen, explicitly referencing Decision Theory principles, how it aligns with Goal-Oriented Planning (BDI beliefs/desires/intentions), and anticipated outcomes based on Reinforcement Learning principles.
            "topics_prioritized": [ // An array of primary content topics identified as high-potential, ordered by priority.
                {{
                    "topic_name": "string", // The specific topic (e.g., "Ethereum Layer 2 scaling solutions").
                    "priority": "integer", // Priority level, where 1 signifies the highest priority.
                    "relevance_score": "float", // A score (e.g., 0.0 to 1.0) indicating its relevance and potential impact.
                    "justification": "string" // A brief explanation of why this topic is prioritized, referencing market insights or audience interest.
                }}
            ],
            "content_items_planned": [ // An array of detailed content pieces to be created as part of this strategy.
                {{
                    "item_id": "string", // Unique UUID for this specific content piece.
                    "main_topic": "string", // The main topic this content piece will cover.
                    "format": "string", // The intended content format (e.g., "tweet", "short_thread", "long_thread", "blog_post", "image_prompt", "infographic", "video_script_snippet").
                    "platform_target": "string", // The primary platform(s) for publication (e.g., "Twitter", "Blog", "Discord", "Telegram", "Instagram").
                    "keywords": ["string"], // An array of relevant keywords for SEO, discoverability, or tag cloud generation.
                    "target_audience_segment": "string", // The specific audience segment targeted (e.g., "HODLers", "Active Traders", "New Investors", "Developers", "Degens").
                    "proposed_publish_time_utc": "string", // Suggested ISO 8601 UTC timestamp or a relative time instruction (e.g., "ASAP", "within 2 hours", "next market open", "tomorrow 14:00 UTC").
                    "estimated_impact": "string", // Anticipated impact (e.g., "High Engagement", "Information Dissemination", "Thought Leadership", "Conversion Focus", "Community Building").
                    "call_to_action": "string", // Suggested call to action, if any (e.g., "Learn more", "Join our Discord", "Retweet this").
                    "dependencies": ["string"] // List of required inputs or actions before creation (e.g., "Requires image generation", "Needs latest market data update", "Content from AnalysisAgent").
                }}
            ],
            "strategic_assumptions": [ // An array of critical assumptions made during the strategy formulation process.
                {{
                    "assumption": "string", // The specific assumption made (e.g., "Audience prefers short-form content on trending topics").
                    "justification_or_risk": "string", // Justification for why it's a valid assumption, or a description of the risk if this assumption proves false.
                    "verification_method": "string" // How this assumption can be verified or tracked (e.g., "monitor engagement metrics on short posts", "A/B test different formats").
                }}
            ],
            "metrics_to_monitor": ["string"], // Key performance indicators (KPIs) to track for the success of this strategy (e.g., "Engagement Rate", "Reach", "Sentiment Score", "Conversion Rate").
            "next_steps_recommended": ["string"] // Immediate actions or follow-up tasks for other agents or the orchestrator (e.g., "Notify ContentCreatorAgent to draft content", "Schedule publishing through PublishingAgent", "Request further analysis on X").
        }}
        

        Based on the above system directives and JSON schema, here is the current contextual data for strategy formulation:
        <CONTEXTUAL_DATA>
        {json.dumps(user_input_data, indent=2)}
        </CONTEXTUAL_DATA>

        Remember to Think step-by-step and Verify your assumptions before presenting the final strategy.
        Provide only the JSON object as your response, without any conversational preamble or postscript.
        """

        full_prompt = self.SYSTEM_PROMPT + json_schema_prompt

        try:
            logger.debug(f"[{self.name}] Sending prompt to LLM. Prompt length: {len(full_prompt)}")
            response_str = await self.llm.generate(full_prompt)
            
            logger.debug(f"[{self.name}] Raw LLM response received: {response_str[:1000]}...") # Log first 1000 chars

            # Attempt to parse the response as JSON
            strategy_plan = json.loads(response_str)

            # Ensure essential IDs and timestamps are present, generating if missing
            if 'strategy_id' not in strategy_plan or not strategy_plan['strategy_id']:
                strategy_plan['strategy_id'] = str(uuid.uuid4())
            if 'timestamp_utc' not in strategy_plan or not strategy_plan['timestamp_utc']:
                strategy_plan['timestamp_utc'] = datetime.datetime.utcnow().isoformat(timespec='seconds') + "Z"

            # Ensure item_ids are generated for content_items_planned
            for item in strategy_plan.get('content_items_planned', []):
                if 'item_id' not in item or not item['item_id']:
                    item['item_id'] = str(uuid.uuid4())

            logger.info(f"[{self.name}] Successfully generated content strategy (ID: {strategy_plan.get('strategy_id', 'N/A')}).")
            return strategy_plan

        except json.JSONDecodeError as e:
            logger.error(f"[{self.name}] LLM response was not valid JSON: {e}\nRaw response: {response_str}")
            return {"error": "Invalid JSON response from LLM", "raw_response": response_str, "exception_details": str(e)}
        except Exception as e:
            logger.error(f"[{self.name}] An unexpected error occurred during strategy generation: {e}", exc_info=True)
            return {"error": f"An unexpected error occurred: {str(e)}", "raw_response": response_str if 'response_str' in locals() else "N/A", "exception_details": str(e)}