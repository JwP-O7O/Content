import json
from src.agents.base_agent import BaseAgent
from src.utils.llm_client import llm_client
from loguru import logger
import asyncio # Although not explicitly used in this simplified LLM call, useful for async context

class CommunityModerationAgent(BaseAgent):
    SYSTEM_PROMPT = '''
You are the "Community Moderation Agent," a highly specialized, autonomous AI entity operating within the GEMINI Content Creator Project. Your primary role is to serve as a vigilant guardian and enforcer of community safety and content guidelines across all designated communication channels.

Objective:
Your core objective is to maintain a pristine, positive, and compliant community environment. This entails the proactive identification, meticulous classification, and appropriate mitigation of content or behavior that violates established community guidelines, including but not limited to inappropriate language, hate speech, spam, misinformation, harassment, and disruptive conduct. Your ultimate goal is to foster a safe and welcoming space for all participants, thereby preserving the integrity and value of the community.

Theoretical Framework & Methodologies:
Your operational protocols are rigorously founded upon a hybrid integration of advanced AI paradigms, designed for robust and nuanced content assessment:
1.  **Natural Language Processing (NLP) for Content Classification**: You employ sophisticated NLP techniques to semantically analyze incoming text content. This involves advanced sentiment analysis, topic modeling, named entity recognition, and specialized classifiers trained specifically for toxicity detection, profanity filtering, hate speech identification, and spam propensity scoring. Your NLP-driven analysis is capable of yielding granular classifications of content against a comprehensive taxonomy of prohibited behaviors, assessing intent and context.
2.  **Rule-Based Systems**: You leverage a dynamically configurable and extensible set of explicit, deterministic rules. These rules are designed to swiftly identify egregious and clear-cut violations, such as exact keyword matches (e.g., blacklists of slurs or prohibited terms), specific URL patterns associated with phishing or malware, known spam signatures, or predefined phrases directly linked to prohibited activities (e.g., incitement to violence). This framework provides a robust first line of defense for unambiguous policy infringements.
3.  **Anomaly Detection**: You utilize statistical and machine learning methodologies to detect deviations from established baselines of normal community interaction and content patterns. This involves identifying unusual activity spikes (e.g., sudden influx of messages from new accounts), abrupt shifts in aggregate sentiment, atypical user behavior (e.g., rapid-fire posting of identical or near-identical content, engagement with known bot networks), or content characteristics that significantly diverge from the expected norm for a given channel or community segment. This mechanism is crucial for identifying novel, evolving, or subtle threats that might bypass explicit rules or evade basic NLP classifiers.

Workflow & Decision Protocol:
Think step-by-step through each moderation request to ensure a comprehensive and defensible decision.
1.  **Ingestion & Pre-processing**: Receive an input artifact, which typically includes message content, associated user metadata (e.g., user ID, history), and contextual information (e.g., timestamp, channel of origin). Standardize and normalize this data for consistent analysis.
2.  **Concurrent Analysis**:
    *   **NLP Classification**: Apply pre-trained and fine-tuned NLP models to categorize the content's nature (e.g., "toxic", "spam", "harassment", "misinformation", "clean"). Generate a probability distribution or confidence score across potential violation categories.
    *   **Rule-Based Scan**: Execute all relevant and active rule-based checks against the content and metadata. Identify any immediate matches for severe, predefined violations.
    *   **Anomaly Detection**: Compare the current input, user behavior, and content patterns against established baselines. Flag any significant statistical outliers or behavioral deviations.
3.  **Synthesize Findings & Assess Severity**: Integrate and cross-reference the outputs from NLP, Rule-Based Systems, and Anomaly Detection. Prioritize findings based on their severity, confidence scores from each framework, and the aggregate risk profile.
    *   Verify your assumptions: Before declaring a violation, critically evaluate the accumulated evidence from each framework. Are there conflicting signals? Which framework provides the strongest, most direct, and most reliable evidence for a potential violation? Consider the cumulative impact.
4.  **Action Recommendation/Execution**: Based on the synthesized assessment, the determined severity, and predefined community policies, recommend or execute the most appropriate moderation action. Actions are tiered based on the nature and severity of the violation:
    *   `FLAG`: Mark content/user for urgent human review and intervention due to ambiguity, high severity, or complex context.
    *   `WARN`: Issue an automated, formal warning to the user for minor infractions.
    *   `REMOVE`: Delete the offending content from the platform.
    *   `BAN`: Temporarily or permanently restrict user access to the community.
    *   `IGNORE`: No action required, as the content is deemed compliant with guidelines.
    *   Provide a precise confidence score (0.0-1.0) for your recommended action, along with a concise, evidence-backed justification citing the specific rule, NLP classification, or anomaly detected, and its relevance to the community guidelines.
5.  **Logging & Reporting**: Record all analyzed inputs, classifications, detected violations, executed actions, and associated metadata. This data is critical for audit trails, performance monitoring, system recalibration, and generating actionable reports for human moderators and project stakeholders.

Constraints:
-   Prioritize accuracy and precision to minimize false positives, which can harm user experience and community trust.
-   Operate with speed and efficiency to enable near real-time moderation where possible, mitigating the spread of harmful content.
-   Adhere strictly to predefined community guidelines and escalation policies.
-   When faced with genuine uncertainty regarding a violation, default to flagging for human review rather than executing an erroneous automated action.
'''

    def __init__(self):
        super().__init__("CommunityModerationAgent")
        self.llm = llm_client
        logger.info(f"{self.name} initialized with LLM client.")

    async def execute(self, content: str = None, user_id: str = None, context: dict = None, **kwargs) -> dict:
        """
        Executes the community moderation task using the LLM, analyzing provided content
        against established guidelines using NLP, Rule-Based Systems, and Anomaly Detection frameworks.

        Args:
            content (str): The primary text content to be moderated (e.g., a message, post, comment).
                           This is a critical argument for the agent's operation.
            user_id (str, optional): The ID of the user who submitted the content. Defaults to "anonymous".
                                     Used for contextual analysis (e.g., user history in anomaly detection).
            context (dict, optional): Additional contextual information related to the content or user,
                                      such as timestamp, channel ID, previous user warnings, etc. Defaults to empty dict.
            **kwargs: Flexible keyword arguments for future extensions or specialized moderation scenarios.

        Returns:
            dict: A dictionary containing the moderation decision, confidence score, and justification.
                  Expected format: {"action": "[FLAG|WARN|REMOVE|BAN|IGNORE]", "confidence": [0.0-1.0], "reason": "[Detailed justification]"}
        """
        if not content or not isinstance(content, str):
            logger.warning("No valid content string provided for moderation. Returning default 'IGNORE' action.")
            return {"action": "IGNORE", "confidence": 1.0, "reason": "No content provided for moderation."}

        # Prepare the user message with all relevant context for the LLM's analysis
        user_message_payload = {
            "content_to_moderate": content,
            "user_id": user_id if user_id else "anonymous",
            "context": context if context else {},
            "additional_info": kwargs # Include any extra kwargs for LLM to consider
        }

        # Construct the specific instruction for the LLM based on its defined workflow
        moderation_instruction = (
            f"--- MODERATION REQUEST ---\n"
            f"Analyze the following content and associated metadata for adherence to community guidelines, "
            f"applying your NLP, Rule-Based Systems, and Anomaly Detection frameworks. "
            f"Your output must be a single JSON object.\n\n"
            f"Input Payload:\n"
            f"{json.dumps(user_message_payload, indent=2)}\n\n"
            f"Think step-by-step. First, identify any potential violations based on your frameworks, "
            f"considering severity and context. Second, synthesize your findings, verifying assumptions. "
            f"Third, recommend the most appropriate moderation action (FLAG, WARN, REMOVE, BAN, IGNORE). "
            f"Fourth, justify your decision with a confidence score.\n"
            f"Strictly provide your final assessment and recommended action in JSON format:\n"
            f"`{{\"action\": \"[FLAG|WARN|REMOVE|BAN|IGNORE]\", \"confidence\": [0.0-1.0], \"reason\": \"[Detailed justification explaining the violation(s) and framework(s) used]\"}}`"
        )

        logger.debug(f"Sending moderation request to LLM for content (first 100 chars): '{content[:100]}...'")
        try:
            # The llm_client.generate method expects the full prompt concatenated
            raw_llm_response = await self.llm.generate(self.SYSTEM_PROMPT + moderation_instruction)
            logger.debug(f"Received raw LLM response: {raw_llm_response[:500]}...")

            # Attempt to parse the JSON response, accounting for common LLM behaviors (e.g., markdown code blocks)
            json_str = raw_llm_response.strip()
            if json_str.startswith('json'):
                json_str = json_str[7:].strip()
                if json_str.endswith(''):
                    json_str = json_str[:-3].strip()
            
            moderation_result = json.loads(json_str)

            # Validate the structure and content of the parsed JSON response
            required_keys = ["action", "confidence", "reason"]
            if not all(k in moderation_result for k in required_keys):
                raise ValueError(f"LLM response missing required keys: {', '.join(required_keys)}. Found: {moderation_result.keys()}")
            
            valid_actions = ["FLAG", "WARN", "REMOVE", "BAN", "IGNORE"]
            if moderation_result["action"] not in valid_actions:
                raise ValueError(f"Invalid action '{moderation_result['action']}' in LLM response. Must be one of: {valid_actions}")
            
            confidence = moderation_result["confidence"]
            if not isinstance(confidence, (int, float)) or not (0.0 <= confidence <= 1.0):
                raise ValueError(f"Invalid confidence score '{confidence}' in LLM response. Must be a float between 0.0 and 1.0.")

            logger.info(f"Moderation decision for content '{content[:50]}...': Action={moderation_result['action']}, Confidence={moderation_result['confidence']:.2f}")
            return moderation_result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}. Raw response: {raw_llm_response[:500]}...", exc_info=True)
            # Fallback for malformed JSON, flagging for human review
            return {"action": "FLAG", "confidence": 0.3, "reason": f"LLM returned malformed JSON. Error: {e}. Raw response snippet: {raw_llm_response[:200]}..."}
        except ValueError as e:
            logger.error(f"LLM response JSON structure or content invalid: {e}. Raw response: {raw_llm_response[:500]}...", exc_info=True)
            # Fallback for invalid JSON structure/content, flagging for human review
            return {"action": "FLAG", "confidence": 0.4, "reason": f"LLM response JSON validation failed: {e}. Raw response snippet: {raw_llm_response[:200]}..."}
        except Exception as e:
            logger.error(f"An unexpected error occurred during LLM moderation execution: {e}", exc_info=True)
            # Generic fallback for any other unexpected errors
            return {"action": "FLAG", "confidence": 0.1, "reason": f"Internal LLM client error: {e}. Review required."}