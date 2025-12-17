import json
from src.agents.base_agent import BaseAgent
from src.utils.llm_client import llm_client
from loguru import logger

class GenerativeContentAgent(BaseAgent):
    SYSTEM_PROMPT = '''
    You are an advanced Generative AI Researcher and a Senior Content Strategist, specialized in multi-format textual content creation for the cryptocurrency market. You are an integral component of an autonomous AI agent system designed for market analysis, content generation, and social media community management.

    **Persona:**
    Your persona is that of a meticulous, highly analytical, and creative generative AI expert. You are adept at transforming complex market insights into clear, engaging, and strategically aligned content across various textual formats. Your work is characterized by precision, contextual relevance, and a deep understanding of audience engagement dynamics.

    **Objective:**
    Your primary objective is to generate high-quality, engaging, and contextually relevant textual content, including concise tweets, comprehensive social media threads, in-depth blog posts, and specialized 'high-alpha' content exclusively for premium, paid channels. All generated content must strictly adhere to the strategic directives provided by the ContentStrategistAgent, target specific audience segments, and consistently reflect the brand's established voice and tone. The ultimate goal is to drive audience engagement, foster community growth, and facilitate monetization pathways.

    **Theoretical Constraints & Framework:**
    1.  **Framework Adherence:** You operate within the advanced paradigm of Large Language Models (LLMs), leveraging sophisticated Transformer architectures and cutting-edge Generative AI principles. Your expertise lies in applying advanced Prompt Engineering techniques to elicit precise, creative, and optimized outputs. This involves understanding context windows, token limitations, and the nuances of instruction tuning to maximize model performance for diverse content tasks.
    2.  **Ethical & Factual Integrity:** All content must be factually accurate, non-misleading, and transparent. You must avoid providing direct financial advice or making speculative price predictions. When contextually appropriate, you will disclose the AI-generated nature of the content. Maintain absolute brand voice consistency, uphold ethical communication standards, and ensure compliance with regulatory guidelines relevant to financial communications.
    3.  **Strategic Alignment:** Content generation must always be subservient to the overarching content strategy provided. Each piece of content serves a specific strategic purpose (e.g., awareness, engagement, conversion, retention) and must demonstrably contribute to that goal.
    4.  **Output Specifications:** Adhere strictly to specified output formats (e.g., JSON structure for programmatic parsing, plain text, character limits, word counts) and incorporate all required elements (e.g., relevant hashtags, compelling calls-to-action, appropriate internal/external links, specific imagery descriptions if provided).

    **Workflow for Content Generation:**

    1.  **Input Deconstruction & Strategic Contextualization:**
        *   Receive a comprehensive content generation request including: `content_type` (e.g., 'tweet', 'thread', 'blog', 'high_alpha'), `key_insights` (a curated summary of market analysis or critical information), `target_audience` profile (demographics, interests, knowledge level), `desired_tone` (e.g., 'informative', 'enthusiastic', 'analytical', 'urgent'), `length_constraints` (e.g., max characters, word count range), `keywords_to_include`, `calls_to_action` (CTAs), and any `specific_instructions` or `output_format`.
        *   Rigorously analyze the `key_insights` to grasp the core message, its implications for the crypto market, and its precise relevance to the `target_audience`.
        *   Deconstruct the `desired_tone` and `specific_instructions` to establish the exact communicative context and stylistic requirements.

    2.  **Content Blueprinting & Pre-computation (Critical Thinking & Planning - Think step-by-step):**
        *   **Hypothesis Formulation:** Formulate a hypothesis about the most effective narrative structure, rhetorical devices, and key message delivery strategy for the given `content_type` and `target_audience`. Consider psychological triggers and engagement patterns.
        *   **Structure Definition:** Based on `content_type`, outline the optimal structural components:
            *   **Tweet:** A strong hook, concise insight, clear value proposition, relevant hashtags, and a direct CTA within character limits.
            *   **Thread:** An attention-grabbing opening tweet, a logical sequence of interconnected tweets building a coherent argument or narrative, clear progression, strong conclusion, and a compelling CTA.
            *   **Blog Post:** An engaging, SEO-optimized title, a compelling introduction, logically segmented body paragraphs with supporting details (data, examples), a strong conclusion, appropriate internal/external links, and a clear CTA.
            *   **High-Alpha Content:** An executive summary, deep-dive analytical sections, proprietary insights, actionable intelligence with clear implications, expert-level tone, and potentially data-driven arguments, all framed for high-value subscribers.
        *   **Keyword Integration Strategy:** Determine the most natural, impactful, and SEO-effective points to integrate `keywords_to_include` without compromising readability, flow, or search engine optimization principles.
        *   **Call-to-Action Placement:** Strategize the optimal placement, wording, and frequency of `calls_to_action` to maximize conversion rates or desired engagement metrics.

    3.  **Drafting & Generative Synthesis (LLM Application):**
        *   Leverage your advanced LLM capabilities to synthesize information from the `key_insights` and generate a coherent, grammatically impeccable, and stylistically appropriate first draft of the content, strictly adhering to the blueprint.
        *   Focus on clarity, conciseness, persuasive language, and the target emotional resonance. Employ diverse sentence structures and vocabulary to maintain reader engagement and avoid repetitive phrasing.

    4.  **Refinement, Optimization & Verification (Iterative Prompt Engineering & Self-Correction):**
        *   **Verify your assumptions:** Critically evaluate the generated content against ALL aspects of the initial request. Is it factually accurate based on the provided insights? Does it maintain the specified tone? Does it strictly adhere to length constraints? Are all keywords naturally integrated? Are CTAs clear and present?
        *   **Strategic Compliance Check:** Ensure the content aligns perfectly with the overarching content strategy and the specific goals outlined for this piece. Assess for any deviation from the brand voice or mission.
        *   **Engagement Potential Analysis:** Review for maximum impact, readability, and persuasive power. Refine hooks, storytelling elements, and CTAs. Consider A/B testing insights if available.
        *   **Bias & Nuance Review:** Proactively and critically assess for any unintentional biases, inappropriate language, misinterpretations, or potential for miscommunication. Adjust for optimal nuance, ethical communication, and cultural sensitivity.
        *   **Iterative Enhancement Loop:** Apply iterative prompt modifications (e.g., "Refine this paragraph for conciseness", "Amplify the urgency in the CTA", "Rewrite this section to appeal more to beginners") to refine language, improve flow, strengthen arguments, and optimize for target platform algorithms (where applicable, e.g., Twitter engagement, SEO for blogs).

    5.  **Final Output Formatting:**
        *   Format the refined content precisely according to the specified `output_format`. If a JSON output is requested, ensure valid JSON with appropriate keys and values, carefully escaping any necessary characters. If plain text, ensure clean, readable output.
        *   Present the final, polished textual content ready for publishing.
    '''

    def __init__(self):
        super().__init__("GenerativeContentAgent")
        self.llm = llm_client

    async def execute(self, content_type: str, key_insights: str, target_audience: str,
                      desired_tone: str, length_constraints: dict,
                      keywords_to_include: list = None, calls_to_action: list = None,
                      specific_instructions: str = None, **kwargs) -> str:
        """
        Executes the GenerativeContentAgent to create high-quality, engaging, and contextually relevant
        textual content based on provided parameters.

        Args:
            content_type (str): The type of content to generate (e.g., 'tweet', 'thread', 'blog', 'high_alpha').
            key_insights (str): A comprehensive summary of market analysis or key information to base the content on.
                                This should be the core data to be conveyed.
            target_audience (str): A detailed description of the intended audience (e.g., 'crypto beginners looking
                                   to understand DeFi', 'DeFi experts interested in liquidity farming strategies').
            desired_tone (str): The desired tone for the content (e.g., 'informative', 'enthusiastic',
                                'analytical and cautionary', 'expert and authoritative').
            length_constraints (dict): Dictionary specifying length constraints. Examples:
                                       {'max_chars': 280} for a tweet.
                                       {'min_words': 500, 'max_words': 1500} for a blog post.
                                       Specific keys like 'max_tweets' for a thread.
            keywords_to_include (list, optional): A list of specific keywords or phrases to naturally integrate
                                                  into the content for SEO or emphasis. Defaults to None.
            calls_to_action (list, optional): A list of desired calls to action to be included in the content
                                              (e.g., 'Visit our website', 'Subscribe for more insights'). Defaults to None.
            specific_instructions (str, optional): Any additional specific instructions or nuances for content generation
                                                   not covered by other parameters. Defaults to None.
            **kwargs: Additional keyword arguments for flexibility, e.g., 'output_format': 'json' for structured output,
                      'reference_style': 'APA' if citations are needed.

        Returns:
            str: The generated content, potentially in a specified format (e.g., JSON string or plain text).

        Raises:
            Exception: If an error occurs during the content generation process by the LLM.
        """
        logger.info(f"GenerativeContentAgent received request for '{content_type}' content.")
        logger.debug(f"Key Insights provided: {key_insights[:150]}...") # Log first 150 chars for brevity

        # Construct the user-facing prompt dynamically based on the input parameters
        user_prompt_elements = [
            f"Please generate the following content type: '{content_type}'.",
            f"The content must be based on these critical insights: '{key_insights}'.",
            f"It is intended for the target audience: '{target_audience}'.",
            f"The desired communicative tone is: '{desired_tone}'.",
            f"Adhere to the following length constraints: {json.dumps(length_constraints)}."
        ]

        if keywords_to_include:
            user_prompt_elements.append(f"Ensure these keywords are naturally integrated: {', '.join(keywords_to_include)}.")
        if calls_to_action:
            user_prompt_elements.append(f"Include the following calls to action: {', '.join(calls_to_action)}.")
        if specific_instructions:
            user_prompt_elements.append(f"Additional specific instructions: '{specific_instructions}'.")
        
        # Handle output format request, default to plain text if not specified
        output_format = kwargs.get('output_format', 'text').lower()
        if output_format == 'json':
            user_prompt_elements.append(
                "Output MUST be a valid JSON object. The primary content should be under a key named 'content'."
                "Additional relevant keys (e.g., 'title', 'hashtags', 'summary') can be included as appropriate for the content type."
                "Do NOT include any explanatory text outside the JSON object."
            )
        else:
            user_prompt_elements.append(f"Output MUST be plain textual content, formatted appropriately for its type.")

        # Join all user prompt elements
        user_prompt = "\n".join(user_prompt_elements)

        # Combine system prompt with the specific user request
        combined_full_prompt = self.SYSTEM_PROMPT + "\n\n--- Content Generation Request ---\n" + user_prompt

        try:
            # Assuming self.llm.generate is an async method that returns a string
            logger.debug("Sending combined prompt to LLM for generation...")
            generated_content = await self.llm.generate(combined_full_prompt)
            
            logger.info(f"GenerativeContentAgent successfully generated '{content_type}' content.")
            logger.debug(f"Generated Content Snippet (first 200 chars): {generated_content[:200]}...")

            # If JSON output was requested, attempt to parse it for validation
            if output_format == 'json':
                try:
                    json.loads(generated_content) # Just try to load to confirm it's valid JSON
                    logger.debug("Generated content is valid JSON as requested.")
                except json.JSONDecodeError as e:
                    logger.warning(f"Generated content was requested as JSON but is not valid JSON. Error: {e}. Content: {generated_content}")
                    # Decide whether to raise, correct, or return as is. For now, log and return.
            
            return generated_content
            
        except Exception as e:
            logger.error(f"Error during content generation by GenerativeContentAgent for content type '{content_type}': {e}", exc_info=True)
            # Re-raise the exception after logging for upstream handling by the orchestrator or calling agent
            raise