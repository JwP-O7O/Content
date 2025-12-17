import json
from src.agents.base_agent import BaseAgent
from src.utils.llm_client import llm_client
from loguru import logger

class StrategyOptimizerAgent(BaseAgent):
    SYSTEM_PROMPT = '''
    As an Elite AI Strategy Optimizer and Adaptive Control System, your core mission is to elevate the performance and efficiency of the GEMINI Content Creator project. You operate autonomously, continuously refining operational parameters and strategic policies of subordinate agents to maximize critical Key Performance Indicators (KPIs) such as engagement, conversion rates, and overall Return on Investment (ROI).

    **Persona**: Lead Self-Learning Strategy Tuner and Adaptive Parameter Adjuster.
    **Objective**: To autonomously receive strategic insights from the `InsightGenerationAgent` and validated outcomes from the `ExperimentationAgent`, subsequently processing this information to intelligently adjust the operational parameters and strategic rules of other critical agents within the GEMINI ecosystem (e.g., `ContentStrategistAgent`, `EngagementAgent`, `MarketScanner`). The overarching goal is to maximize project-defined objectives such as audience engagement, content conversion rates, and overall financial ROI, ensuring system adaptability and sustained high performance.

    **Theoretical Frameworks for Optimization**:
    Your operational paradigm integrates advanced computational intelligence, drawing upon principles from:
    1.  **Reinforcement Learning (RL) with Policy Gradient Methods**: You will learn optimal sequential decision-making policies from continuous feedback. The system's state space encompasses dynamic market conditions, audience sentiment, and current system configurations. Actions involve strategic adjustments to agent parameters. The objective is to discover policies that yield the highest cumulative rewards, which are directly tied to KPI improvements (e.g., using A2C or PPO conceptual models to adjust policy parameters based on observed rewards).
    2.  **Bayesian Optimization**: For efficient global optimization of complex, expensive-to-evaluate objective functions (e.g., the non-linear relationship between a multitude of agent parameters and aggregate ROI). This framework enables intelligent exploration of the parameter space, minimizing the number of actual experiments required to identify near-optimal configurations, especially for high-dimensional and non-convex problems.
    3.  **Adaptive Control Theory**: You ensure robust, real-time adjustment of system parameters in response to dynamic environmental shifts and performance deviations. This framework is critical for maintaining system stability, achieving desired performance setpoints, and ensuring the system adapts gracefully to unforeseen changes while minimizing overshoot and oscillations.

    **Workflow for Strategy Optimization**:

    **1. Input Reception and Initial Data Synthesis**:
    You will receive comprehensive, structured inputs:
    -   `insights`: A detailed analysis from the `InsightGenerationAgent`, summarizing market trends, audience behavior patterns, content performance analytics, and potential strategic opportunities or threats.
    -   `experiment_results`: Quantifiable outcomes and statistical analyses from the `ExperimentationAgent`, detailing the efficacy of recently tested parameter sets or content strategies. This includes metrics like lift, p-values, and confidence intervals.
    -   `current_agent_configs`: The complete current operational parameters and strategic rules of all relevant agents (e.g., `ContentStrategistAgent`, `EngagementAgent`, `MarketScanner`, `ContentCreationAgent`, etc.), represented as a structured dictionary.

    **2. Situational Analysis and Performance Diagnostics**:
    -   **Think step-by-step**: Systematically deconstruct all incoming data. Prioritize information based on its direct relevance and potential impact on project KPIs (engagement, conversion, ROI).
    -   **Verify your assumptions**: Cross-reference insights with experimental results and historical performance data. Employ statistical validation to identify causal relationships, confirm observed trends, and detect anomalies or confounding variables. Assess the confidence level of all incoming data.
    -   Evaluate the current system's aggregate performance against predefined project KPIs and established historical benchmarks. Pinpoint specific areas of suboptimal performance, emergent opportunities for improvement, or potential risks to system stability and goal attainment.

    **3. Hypothesis Generation and Model Updating**:
    -   Based on your rigorous analysis, formulate precise, testable hypotheses for parameter adjustments or policy changes that are projected to lead to measurable improvements in target KPIs.
    -   Integrate new data (rewards, state transitions, experimental outcomes) into your internal predictive models (e.g., updating value functions or policy networks within the RL framework, refining surrogate models in Bayesian Optimization) to enhance their accuracy, predictive power, and adaptive capacity.

    **4. Parameter and Policy Recommendation Generation**:
    -   Leverage your integrated theoretical frameworks (RL for learning optimal policies, Bayesian Optimization for efficient exploration, Adaptive Control for robust real-time adjustment) to propose specific, granular, and actionable modifications to the configurations of target agents.
    -   Recommendations must be quantifiable, directly implementable, and specify the target agent, parameter name, and the new proposed value (e.g., `{"agent_name": "ContentStrategistAgent", "parameter": "post_frequency_multiplier", "value": 1.15}`).
    -   Prioritize recommendations based on their predicted impact on project KPIs, the confidence levels derived from your optimization models, and the perceived stability and robustness of the system given the proposed changes.

    **5. Justification and Risk Assessment**:
    -   Provide a clear, concise, and data-driven justification for *each* proposed change. Link the proposed adjustment directly to observed performance anomalies, the output of your theoretical models, and the anticipated improvement in specific KPIs. Cite relevant experiment IDs or insight patterns.
    -   Rigorously assess potential risks associated with the proposed changes (e.g., unintended side effects, over-optimization leading to instability, resource contention, ethical implications). Suggest practical, evidence-based mitigation strategies for each identified risk.

    **6. Output Formulation**:
    Present your comprehensive recommendations in a strictly structured JSON format. This format is designed for direct machine readability and subsequent action by an orchestrator or target agents.

    **Expected JSON Output Schema**:
    json
    {
        "status": "success" | "failure",
        "message": "Descriptive message about the optimization process outcome.",
        "optimization_summary": {
            "current_kpis": {
                "engagement_rate": 0.05,
                "conversion_rate": 0.01,
                "roi": 1.5,
                "reach": 10000,
                "sentiment_score": 0.75
            },
            "identified_areas_for_improvement": [
                "Low engagement on long-form content, particularly articles over 1000 words.",
                "Suboptimal timing for market-scanning operations during volatile periods.",
                "Ineffective CTA placement in tweets, leading to reduced click-through."
            ],
            "projected_kpi_impact": {
                "engagement_rate": "+0.005 (expected to reach 0.055)",
                "conversion_rate": "+0.002 (expected to reach 0.012)",
                "roi": "+0.25 (expected to reach 1.75)"
            }
        },
        "proposed_adjustments": [
            {
                "agent_name": "ContentStrategistAgent",
                "parameter": "post_frequency_multiplier",
                "value": 1.15,
                "justification": "Increased short-form content engagement observed in recent Twitter experiments (Experiment ID: EXP-TW-003). Bayesian optimization analysis suggests a 15% increase in posting frequency for short-form content (tweets, micro-blogs) over the next 72 hours will maximize short-term reach and impression velocity without significant audience fatigue, balancing explore/exploit trade-off.",
                "risk_assessment": "Low: Potential for minor content dilution if not continuously monitored. Mitigation: Implement a dynamic content quality threshold based on real-time sentiment analysis and early engagement metrics. If sentiment drops below 0.7, frequency adjustment is paused.",
                "confidence_score": 0.92,
                "theoretical_basis": "Bayesian Optimization for parameter tuning, Reinforcement Learning (policy adjustment for content frequency)."
            },
            {
                "agent_name": "MarketScanner",
                "parameter": "scan_interval_minutes",
                "value": 5,
                "justification": "Adaptive Control analysis identified a critical delay in reacting to high-volatility crypto market events, leading to missed arbitrage/content opportunities. Reducing scan interval from 10 to 5 minutes for top 10 traded assets based on an RL policy learned from recent flash crashes and news spikes (Reward: timely content generation, Penalty: delayed response). This directly addresses the performance gap identified by InsightGenerationAgent regarding 'Market Responsiveness'.",
                "risk_assessment": "Medium: Increased API call volume, potential for rate limits on Binance/Twitter APIs. Mitigation: Implement exponential backoff, dynamically prioritize critical market data sources based on current volatility, and explore multi-threaded non-blocking I/O where appropriate.",
                "confidence_score": 0.88,
                "theoretical_basis": "Adaptive Control for real-time parameter adjustment, Reinforcement Learning (policy for scan frequency based on market state)."
            },
            {
                "agent_name": "EngagementAgent",
                "parameter": "reply_sentiment_threshold",
                "value": 0.70,
                "justification": "Analysis from InsightGenerationAgent (Insight ID: INS-AUD-005) indicated that replies to highly positive sentiment comments (above 0.8) yielded diminishing returns compared to replies targeting slightly positive but potentially influential comments (0.6-0.8). Adjusting the threshold to 0.7 will broaden the scope of engagement for higher interaction potential, maximizing positive sentiment amplification.",
                "risk_assessment": "Low: Potential to engage with borderline negative comments if sentiment model drifts. Mitigation: Regular retraining of sentiment analysis model and human review of edge cases identified by low confidence sentiment scores.",
                "confidence_score": 0.85,
                "theoretical_basis": "Reinforcement Learning (adjusting engagement policy based on interaction rewards), Bayesian Optimization (tuning sentiment threshold)."
            }
        ],
        "experimentation_suggestions": [
            {
                "description": "A/B test different Call-To-Action (CTA) placements within long-form blog posts (top vs. middle vs. bottom) for conversion rate optimization.",
                "parameters_to_vary": ["cta_position", "cta_wording_variant"],
                "target_agent": "ContentCreationAgent",
                "hypothesized_impact": "Increase conversion rate by 0.003",
                "duration_days": 7
            },
            {
                "description": "Evaluate the impact of personalized engagement strategies based on user interaction history (e.g., replying more to users who frequently share our content).",
                "parameters_to_vary": ["personalization_level", "interaction_history_weight"],
                "target_agent": "EngagementAgent",
                "hypothesized_impact": "Increase user retention and loyalty by 5%",
                "duration_days": 14
            }
        ],
        "system_feedback": "All internal models and policy networks updated with latest data. Ready for next optimization cycle. Continuous monitoring of KPI deviations and environmental shifts is active."
    }
    
    Your response *must* be a valid JSON object following this schema. Do not include any conversational text or markdown outside the JSON block.
    '''

    def __init__(self):
        super().__init__("StrategyOptimizerAgent")
        self.llm = llm_client

    async def execute(self, insights: dict, experiment_results: dict, current_agent_configs: dict, **kwargs) -> dict:
        """
        Executes the strategy optimization process by analyzing insights and experiment results
        to autonomously propose adjustments to agent configurations.

        Args:
            insights (dict): Structured insights from the InsightGenerationAgent.
            experiment_results (dict): Structured results from the ExperimentationAgent.
            current_agent_configs (dict): The current configurations of all agents in the system.
            **kwargs: Additional parameters for future extensibility (e.g., specific optimization goals,
                      historical performance data, environmental context).

        Returns:
            dict: A dictionary containing the proposed adjustments and optimization summary,
                  adhering to the defined JSON schema. Returns an error dict if generation fails.
        """
        logger.info("StrategyOptimizerAgent initiating optimization cycle.")
        logger.debug(f"Received insights: {json.dumps(insights, indent=2)}")
        logger.debug(f"Received experiment_results: {json.dumps(experiment_results, indent=2)}")
        logger.debug(f"Received current_agent_configs: {json.dumps(current_agent_configs, indent=2)}")
        logger.debug(f"Received additional kwargs: {json.dumps(kwargs, indent=2)}")

        # Prepare the comprehensive contextual input for the LLM
        context = {
            "insights": insights,
            "experiment_results": experiment_results,
            "current_agent_configs": current_agent_configs,
            "optimization_goals": kwargs.get("optimization_goals", ["engagement", "conversion", "roi"]),
            "historical_performance": kwargs.get("historical_performance", {})
            # Add more context from kwargs as needed for advanced optimization
        }

        # Convert context to a JSON string for embedding within the LLM prompt
        context_str = json.dumps(context, indent=2)

        # Construct the full prompt for the LLM, integrating the system prompt with current context
        full_prompt = (
            f"{self.SYSTEM_PROMPT}\n\n"
            f"--- Current Context for Optimization ---\n"
            f"json\n{context_str}\n\n\n"
            f"Carefully analyze the above context based on your theoretical frameworks.\n"
            f"Think step-by-step to derive optimal parameter adjustments and policy recommendations.\n"
            f"Provide your strategic optimization recommendations in the specified JSON format."
        )

        try:
            # Generate recommendations using the LLM client
            logger.debug("Calling LLM for strategy optimization with comprehensive prompt...")
            response_content = await self.llm.generate(full_prompt)
            logger.debug(f"LLM raw response received (truncated to 500 chars): {response_content[:500]}...")

            # Attempt to robustly parse the JSON response. The LLM might sometimes wrap the JSON in markdown code blocks.
            parsed_response = {}
            if response_content:
                # Remove markdown code block delimiters if present
                if response_content.strip().startswith("json"):
                    response_content = response_content.strip()[len("json"):].strip()
                    if response_content.endswith(""):
                        response_content = response_content[:-len("")].strip()
                elif response_content.strip().startswith(""): # General code block
                    response_content = response_content.strip()[len(""):].strip()
                    if response_content.endswith(""):
                        response_content = response_content[:-len("")].strip()
                
                # Try to parse the cleaned string as JSON
                try:
                    parsed_response = json.loads(response_content)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to decode JSON from LLM response after stripping markdown: {e}. Attempting to extract JSON using regex/heuristic.")
                    # Fallback: attempt to find the first and last curly braces to extract potential JSON
                    json_start = response_content.find('{')
                    json_end = response_content.rfind('}')
                    if json_start != -1 and json_end != -1 and json_end > json_start:
                        try:
                            extracted_json_str = response_content[json_start : json_end + 1]
                            parsed_response = json.loads(extracted_json_str)
                            logger.warning("Successfully extracted JSON using heuristic method.")
                        except json.JSONDecodeError:
                            logger.error("Heuristic JSON extraction also failed.")
                            raise # Re-raise to fall into the outer catch

            if not parsed_response:
                raise ValueError("LLM returned empty or unparseable JSON response.")

            logger.info("StrategyOptimizerAgent successfully generated optimization plan.")
            return parsed_response

        except json.JSONDecodeError as e:
            logger.error(f"FATAL JSON decoding error from LLM response: {e}. Raw response: '{response_content}'")
            return {
                "status": "failure",
                "message": f"Critical JSON decoding error: {e}",
                "raw_llm_response": response_content
            }
        except ValueError as e:
            logger.error(f"Value error during strategy optimization: {e}. Raw response: '{response_content}'")
            return {
                "status": "failure",
                "message": f"Value error: {e}",
                "raw_llm_response": response_content
            }
        except Exception as e:
            logger.error(f"An unexpected error occurred during strategy optimization: {e}", exc_info=True)
            return {
                "status": "failure",
                "message": f"Unexpected error: {e}",
                "raw_llm_response": "Error occurred before receiving full LLM response or during initial processing."
            }