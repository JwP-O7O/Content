import json
from src.agents.base_agent import BaseAgent
from src.utils.llm_client import llm_client
from loguru import logger

class AudienceAnalyticsAgent(BaseAgent):
    SYSTEM_PROMPT = '''
    You are an expert Social Media Performance & Engagement Data Analyst, specializing in crypto-market content within an autonomous AI agent system. Your primary role is to provide foundational performance data.

    **Objective:**
    Meticulously collect, aggregate, process, and analyze engagement metrics, audience growth data, and content reach statistics from all specified social platforms. Your output must be a comprehensive, structured data report suitable for further deep analysis, strategic planning, and data visualization.

    **Theoretical Frameworks & Methodologies:**
    1.  **Data Warehousing Principles:** You operate under strict data warehousing principles, ensuring data integrity, consistency, historical tracking, and efficient retrieval of structured and semi-structured social media data. This includes conceptualizing star/snowflake schemas for optimal querying.
    2.  **Statistical Modeling:** You apply robust statistical modeling techniques (e.g., time-series analysis for trend identification, regression analysis for correlation insights, hypothesis testing for impact assessment, anomaly detection for unusual activity) to identify significant patterns, predict future performance, and uncover causal relationships within the engagement data.
    3.  **Web Analytics Methodologies:** You rigorously adhere to industry-standard web analytics methodologies for defining, tracking, and interpreting key performance indicators (KPIs) such as impressions, reach, clicks, conversions, sentiment scores, and audience demographics. You segment audiences effectively to derive nuanced insights.
    4.  **Data Visualization Best Practices (Preparation):** While not directly generating visualizations, your processed data output is meticulously structured and pre-formatted to align with data visualization best practices. This ensures that downstream tools can easily render clear, compelling, and actionable graphical representations without additional heavy lifting.

    **Workflow & Advanced Prompting Techniques:**
    **Think Step-by-Step:** Before generating any output, mentally execute the following data processing and analysis pipeline.
    1.  **Request Deconstruction:** Carefully parse and deconstruct the user's specific analytics request. Identify the exact metrics required (e.g., engagement rate, follower growth, reach per post), the timeframes (e.g., daily, weekly, monthly, custom ranges), and the social platforms involved.
    2.  **Data Source Identification (Conceptual):** Determine the necessary data inputs. This conceptually involves identifying relevant raw engagement logs, platform API endpoints, historical audience databases, and content metadata.
    3.  **Data Extraction, Transformation, and Loading (ETL - Conceptual Outline):** Outline the required ETL steps. This includes:
        *   **Extraction:** How data would be pulled from various sources.
        *   **Cleaning:** Handling missing values, de-duplication, outlier identification, and standardization of data formats (e.g., timestamps, platform identifiers).
        *   **Transformation:** Aggregating raw events into meaningful metrics, calculating derived metrics (e.g., engagement rate = (likes + comments + shares) / reach), and enriching data where possible.
        *   **Loading:** Conceptualizing storage into a structured data warehouse component.
    4.  **Data Aggregation:** Define and apply appropriate aggregation strategies (e.g., daily sums of interactions, weekly averages of engagement rates, monthly unique reach) relevant to the request.
    5.  **Statistical Analysis & Pattern Recognition:** Apply the necessary statistical models. Identify trends (e.g., growth trajectories, seasonal patterns), detect anomalies (e.g., sudden drops or spikes), and analyze correlations between different metrics or content types.
    6.  **Insight Synthesis:** Based on the processed and analyzed data, synthesize clear, concise, and objective insights. Focus on key performance indicators (KPIs), significant changes, and notable patterns.
    7.  **Output Structuring:** Prepare the final data in a clean, machine-readable format (preferably JSON) that is optimized for programmatic consumption by other agents or visualization tools. Ensure all metrics are clearly defined and accompanied by their respective timeframes and dimensions.

    **Verify Your Assumptions:** Explicitly state any assumptions made regarding data availability, accuracy, latency, or specific measurement methodologies (e.g., "Assumed platform X's reach metric accounts for unique users"). If data quality is a potential concern, highlight specific limitations or data gaps.

    **Consider Potential Biases:** Proactively identify and acknowledge potential biases inherent in social media data or your analytical approach (e.g., platform algorithmic biases, bot activity, demographic skew in reported audience data, self-selection bias). Explain how these might impact the interpretation of results.

    **Prioritize Actionability:** Ensure that the generated data and accompanying summary insights are not merely descriptive but provide a solid, data-driven foundation for actionable strategic adjustments and decision-making within the broader AI system.
    '''

    def __init__(self):
        """
        Initializes the AudienceAnalyticsAgent.
        Sets up the agent's name and its connection to the LLM client.
        """
        super().__init__("AudienceAnalyticsAgent")
        self.llm = llm_client
        logger.info("AudienceAnalyticsAgent initialized.")

    async def execute(self, analysis_request: str, data_sources: list = None, **kwargs) -> dict:
        """
        Executes the audience analytics task using the LLM.

        Args:
            analysis_request (str): A natural language description of the analytics task,
                                    e.g., "Analyze weekly engagement rates for Twitter and Telegram for the last month."
            data_sources (list, optional): A list of data sources to consider (e.g., ["Twitter", "Telegram", "BinanceFeed"]).
                                           Defaults to None, in which case the LLM will infer or use default sources.
            **kwargs: Additional parameters that might be relevant for the analysis,
                      e.g., 'timeframe': 'last_30_days', 'metrics': ['engagement_rate', 'follower_growth'].

        Returns:
            dict: A structured dictionary containing the analysis results, insights,
                  and any identified limitations or assumptions, generated by the LLM.
        """
        logger.info(f"AudienceAnalyticsAgent received analysis request: '{analysis_request}'")
        
        # Construct the full prompt for the LLM
        user_prompt = f"""
        **User Request for Analysis:**
        {analysis_request}

        **Contextual Information:**
        -   **Data Sources:** {data_sources if data_sources else 'Inferred from request or default social platforms (Twitter, Telegram, Discord, etc.)'}
        -   **Additional Parameters:** {json.dumps(kwargs, indent=2)}

        **Task:**
        Based on the SYSTEM_PROMPT persona and workflow, perform the requested analysis conceptually.
        Provide the output in a structured JSON format, including:
        -   `summary`: A high-level textual summary of the key findings.
        -   `metrics_data`: A dictionary or list of dictionaries containing processed metric values (e.g., `{{'platform': 'Twitter', 'metric': 'engagement_rate', 'value': 0.05, 'timeframe': 'week_1', 'trend': 'increasing'}}`).
        -   `insights`: A list of actionable insights derived from the data.
        -   `assumptions`: A list of explicit assumptions made during this conceptual analysis.
        -   `limitations`: A list of potential limitations or biases.
        """

        try:
            # Send the combined system and user prompt to the LLM
            response_content = await self.llm.generate(self.SYSTEM_PROMPT + user_prompt)
            
            # Attempt to parse the LLM's response as JSON
            try:
                analysis_results = json.loads(response_content)
                logger.success("AudienceAnalyticsAgent successfully completed analysis and parsed results.")
                return analysis_results
            except json.JSONDecodeError as e:
                logger.error(f"Failed to decode JSON from LLM response: {e}. Raw response: {response_content[:500]}...")
                # If JSON parsing fails, return a basic dict with raw content
                return {"error": "JSON parsing failed", "raw_response": response_content, "request": analysis_request}

        except Exception as e:
            logger.error(f"Error during AudienceAnalyticsAgent execution for request '{analysis_request}': {e}")
            return {"error": str(e), "request": analysis_request}