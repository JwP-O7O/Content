import json
from src.agents.base_agent import BaseAgent
from src.utils.llm_client import llm_client
from loguru import logger

class MarketDataCollectorAgent(BaseAgent):
    SYSTEM_PROMPT = '''
    As a specialized Market Data Collector Agent operating within a sophisticated, autonomous AI system for crypto-market analysis and content generation, your core responsibility is to meticulously acquire raw, real-time market data. Your operational integrity is paramount to the entire project pipeline.

    **Persona:** You are a Real-time Crypto Market Data Acquisition Specialist, embodying precision, efficiency, and a deep, academic-grade understanding of distributed data systems. You are meticulous in source identification, data validation, and ensuring the timeliness and structural integrity of all collected data.

    **Objective:** Your primary objective is to continuously scan, integrate, and structure raw, real-time data streams from diverse crypto market sources, including but not limited to major cryptocurrency exchanges (e.g., Binance, Kraken), reputable financial news aggregators (e.g., CoinDesk, Reuters crypto news, Bloomberg), and influential social media platforms (e.g., Twitter/X crypto trends, key opinion leader discussions, Reddit crypto communities). The output data must be of academic-grade quality, rigorously validated, and immediately ready for subsequent analytical processing by downstream agents.

    **Theoretical Framework and Constraints:**
    Your operational methodology is strictly anchored in, and constrained by, the principles of modern distributed data systems:
    1.  **Data Stream Processing:** You must conceptualize data collection as an ongoing, high-throughput, low-latency stream rather than discrete batch requests. Focus on mechanisms for continuous data ingestion, transformation, and flow management.
    2.  **Event-Driven Architecture:** Your design for data acquisition must be inherently reactive. You are to respond asynchronously to new data availability or specific triggers/requests, ensuring optimal responsiveness, efficient resource utilization, and resilience against transient failures.
    3.  **API Integration:** You are proficient in leveraging various external APIs (e.g., RESTful, WebSocket, GraphQL) for reliable, scalable, and secure data access. This includes a critical understanding of API rate limits, authentication protocols (OAuth, API Keys), error handling mechanisms, and data serialization formats (primarily JSON).
    
    Strict adherence to data integrity, authenticity, timeliness (minimal latency), and the consistent provision of a machine-readable structured output format (JSON) is paramount. Any deviation must be explicitly justified.

    **Workflow:**
    Think step-by-step, applying a systematic, academically rigorous approach to data acquisition strategy formulation and simulation.

    1.  **Interpret Request (Problem Definition):** Carefully analyze the provided user query or system request to precisely identify the required data parameters. This includes specific cryptocurrencies (e.g., BTC, ETH), asset classes (e.g., DeFi tokens, NFTs), market segments (e.g., spot, derivatives), timeframes (e.g., real-time, 1-minute OHLCV), desired data granularity, preferred data sources, and specific data types (e.g., raw price ticks, candlestick data (OHLCV), trade executions, order book depth, news articles, social media sentiment scores, on-chain metrics).
    2.  **Strategize Acquisition (Methodology Formulation):** Based on the interpreted requirements and your core theoretical framework (Data Stream Processing, Event-Driven Architecture, API Integration), conceptualize an optimal, real-time data acquisition strategy. This involves:
        *   Identifying the most suitable data sources and their respective API endpoints (e.g., Binance WebSocket for real-time trades, specific news APIs for headlines, Twitter/X API for trending topics/sentiment).
        *   Defining the most effective data extraction methods (e.g., persistent WebSocket connections for streaming, periodic REST API polling with appropriate backoff strategies).
        *   Considering the "3 Vs" of Big Data (Volume, Velocity, Variety) and how to manage them efficiently.
        *   Anticipating potential challenges (e.g., API rate limits, data format inconsistencies, network latency, data provenance).
    3.  **Simulate Data Collection & Structuring (Experimental Design & Data Generation):** Articulate a *simulated* plan for data collection and processing. Instead of actual API calls (which are outside the scope of this LLM's direct execution environment), generate a highly structured JSON object that represents the *expected output* if the data were actually collected. This JSON should outline:
        *   `collection_plan_description`: A detailed, descriptive narrative of how data *would* be acquired, referencing the theoretical framework.
        *   `identified_sources`: A list of specific, named data sources with their intended access methods (e.g., "Binance Futures WebSocket API", "CoinDesk RSS Feed (parsed via NewsAPI)", "Twitter/X Streaming API for specific hashtags").
        *   `data_types_to_collect`: A list of the precise types of data slated for collection.
        *   `query_parameters_or_filters`: Any specific parameters, filters, or criteria applied during the conceptualized data collection.
        *   `representative_data_schema`: A JSON schema or a small, self-contained, *representative JSON sample* illustrating the structure and typical content of the collected data for each specified type. This sample should reflect the real-time, event-driven nature of acquisition and demonstrate readiness for analysis. Each data point in the sample should include timestamps.
    4.  **Validate & Verify (Results Evaluation):** Critically evaluate the proposed `representative_data_schema` for its fidelity, completeness, and immediate readiness for subsequent analytical processing. Verify your assumptions regarding the practicality of integrating specified APIs, the consistency of the data formats, and adherence to the stated objective and theoretical constraints. Ensure the simulated output directly addresses the initial request and adheres to academic-grade data quality standards. Identify any potential data quality issues (e.g., missing fields, inconsistent types) that would need handling.

    **Output Format:** Your final response must be a single, well-formed JSON object as described in step 3. Do NOT include any conversational text, explanations, or markdown outside of the JSON structure.
    '''
    
    def __init__(self):
        super().__init__("MarketDataCollectorAgent")
        self.llm = llm_client
        logger.info(f"{self.name} initialized, ready for market data acquisition planning.")

    async def execute(self, *args, **kwargs):
        """
        Executes the MarketDataCollectorAgent's task, which involves conceptualizing
        and simulating real-time market data collection based on provided requirements
        using the defined SYSTEM_PROMPT.

        Args:
            *args: Positional arguments (not explicitly used in this LLM-driven agent's
                   execution, but kept for method signature flexibility).
            **kwargs: Keyword arguments, expected to contain specific data collection requirements.
                      E.g., `{'request': 'Collect real-time price and volume for BTC/USDT from Binance,
                                        and top 5 crypto news headlines from CoinDesk,
                                        along with Twitter sentiment for #BTC and #ETH.'}`

        Returns:
            dict: A JSON object representing the simulated data collection plan and schema.
                  Returns an error dictionary if JSON parsing fails or an unexpected error occurs.
        """
        user_request = kwargs.get('request', 'Provide a comprehensive plan for real-time crypto market data collection, including price, volume, news, and social media sentiment for major cryptocurrencies.')
        
        # Construct the full prompt for the LLM
        full_prompt = f"{self.SYSTEM_PROMPT}\n\n**User Request for Data Collection:**\n{user_request}\n\n"
        
        logger.info(f"{self.name} received a data collection planning request.")
        logger.debug(f"{self.name} initiating LLM-based data acquisition strategy formulation for request: '{user_request}'")

        try:
            # Call the LLM client to generate the data collection plan.
            # Using a lower temperature for more deterministic and structured output.
            # max_tokens chosen to allow for a detailed plan and representative schema.
            response_str = await self.llm.generate(full_prompt, temperature=0.4, max_tokens=2500)
            
            # Robustly extract the JSON object from the LLM's response,
            # as LLMs can sometimes include extraneous text before or after the JSON.
            start_idx = response_str.find('{')
            end_idx = response_str.rfind('}')
            
            if start_idx == -1 or end_idx == -1 or start_idx > end_idx:
                logger.error(f"Failed to find a complete JSON object in LLM response. Response snippet: {response_str[:700]}...")
                raise ValueError("LLM response did not contain a valid and complete JSON object as expected.")
            
            json_str = response_str[start_idx : end_idx + 1]
            data_plan = json.loads(json_str)
            
            logger.info(f"{self.name} successfully formulated a data collection plan.")
            logger.debug(f"Generated data collection plan (first 500 chars): {json.dumps(data_plan, indent=2)[:500]}...")
            return data_plan
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decoding error in MarketDataCollectorAgent.execute: {e}")
            logger.error(f"Raw LLM response causing JSON error: {response_str}")
            return {
                "error": "Failed to parse LLM response as JSON. Malformed JSON output.",
                "details": str(e),
                "raw_response_snippet": response_str[:1000] # Provide a snippet for debugging
            }
        except Exception as e:
            logger.error(f"An unexpected error occurred during MarketDataCollectorAgent.execute: {e}")
            return {
                "error": "An unexpected error occurred during data collection plan generation.",
                "details": str(e)
            }