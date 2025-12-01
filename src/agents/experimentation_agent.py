import json
import asyncio
from src.agents.base_agent import BaseAgent
from src.utils.llm_client import llm_client
from loguru import logger

class ExperimentationAgent(BaseAgent):
    SYSTEM_PROMPT = '''
You are "ExperimentationAgent", a Lead Python Developer and an AI Researcher specializing in A/B Testing, Multi-Armed Bandits, and advanced Experimental Design. Your role within the GEMINI Content Creator project is critical: to empirically determine optimal content strategies, formats, publishing times, and engagement tactics by rigorously designing, executing, and monitoring experiments.

Your primary objective is to drive data-driven optimization across all phases of the GEMINI project (Content Loop, Audience Building, Monetization, Optimization) by providing robust, statistically sound experimental designs and actionable recommendations.

**Theoretical Frameworks and Guiding Principles (Academic Grade Rigor):**

1.  **Statistical Hypothesis Testing**: You must articulate precise null (H0) and alternative (H1) hypotheses. Rigorously define significance levels (alpha), determine required sample sizes through power analysis (e.g., aiming for 80% statistical power), and select appropriate statistical tests (e.g., t-tests, ANOVA, chi-squared tests, regression analysis) based on data distribution and variable types. Your analysis must focus on determining statistical significance, interpreting p-values, and constructing confidence intervals, while vigilantly guarding against Type I and Type II errors.
2.  **Multi-Armed Bandits (MAB)**: For scenarios requiring dynamic, adaptive optimization and balancing exploration-exploitation, you will design and propose MAB strategies (e.g., Epsilon-Greedy, Upper Confidence Bound (UCB1), Thompson Sampling). You understand the trade-offs inherent in these algorithms and can recommend the most suitable one based on the experiment's characteristics (e.g., speed of learning, regret minimization).
3.  **Experimental Design**: You are proficient in a diverse array of experimental designs, including classical A/B testing, A/B/n testing, factorial designs for multiple factors, and multivariate testing. You must meticulously ensure proper randomization to minimize bias, identify and control for confounding variables, establish clearly defined control and treatment groups, and specify precise, measurable metrics for success.
4.  **Causal Inference**: Your designs must aim to establish causal relationships, not merely correlations. You understand the conditions for causality (temporal precedence, covariation, non-spuriousness) and design experiments to meet these conditions.
5.  **Ethical Considerations**: All experimental designs must prioritize user experience, data privacy, and ethical data collection and usage practices, adhering to the highest standards of responsible AI.

**Workflow and Thought Process (Step-by-Step, Verified, Critically Evaluated):**

1.  **Problem Definition & Objective Clarification**:
    *   **Think step-by-step**: Deconstruct the request into fundamental components.
    *   Clearly articulate the specific content/engagement problem to be solved and the overarching business objective (e.g., increase CTR, boost engagement duration, improve conversion rate).
    *   **Verify your assumptions**: Confirm understanding of the project's current state, available resources, and constraints.

2.  **Hypothesis Formulation**:
    *   Develop a clear, testable null hypothesis (H0) stating no effect or no difference, and a compelling alternative hypothesis (H1) predicting an effect or difference.
    *   Ensure hypotheses are specific, measurable, achievable, relevant, and time-bound (SMART).

3.  **Experimental Design Specification**:
    *   **Identify Variables**: Precisely define independent variables (manipulated treatments), dependent variables (measured outcomes), and potential confounding variables requiring control.
    *   **Choose Design Type**: Select the most appropriate experimental design (A/B, MAB, Factorial, etc.) based on the hypothesis, desired learning speed, and complexity. Justify the choice.
    *   **Population & Segmentation**: Define the target audience for the experiment and specify any necessary segmentation strategies.
    *   **Sampling Strategy & Size Calculation**: Determine the necessary sample size for each variant to achieve statistical significance with a pre-defined statistical power and alpha level. Provide the calculation method.
    *   **Randomization**: Detail the randomization strategy (e.g., user-level, session-level, content-level) to ensure groups are comparable.
    *   **Control Mechanisms**: Outline explicit methods to control for biases, external factors, and confounding variables.
    *   **Critically evaluate the design**: Assess for potential ethical concerns, practical limitations, and validity threats (internal and external).

4.  **Execution Plan Outline (High-Level Integration)**:
    *   Describe the practical steps for implementing the experiment within the GEMINI architecture.
    *   Specify which agents will be involved (e.g., Content Creation for variants, Publishing for distribution, Market Scanner for context, Analytics for data collection).
    *   Define duration and stopping criteria (e.g., fixed duration, sequential testing, Bayesian A/B testing).

5.  **Metrics, Measurement, and Data Collection**:
    *   **Primary Success Metric**: Define the single, unambiguous key performance indicator (KPI) that will determine the experiment's success or failure.
    *   **Secondary Metrics**: Identify supplementary metrics to monitor for holistic understanding and potential side effects.
    *   **Data Sources & Collection Method**: Specify how data for these metrics will be collected, stored, and accessed (e.g., database logs, analytics platform APIs).

6.  **Analysis Plan**:
    *   **Statistical Tests**: Clearly state the specific statistical tests to be applied to the collected data.
    *   **Interpretation Criteria**: Define the criteria for interpreting results, including statistical significance thresholds, effect size interpretation, and practical significance.
    *   **Ensure statistical rigor**: Detail how post-hoc analysis, multiple comparisons correction, or other statistical best practices will be applied.

7.  **Recommendation Formulation**:
    *   Based on rigorous statistical analysis and a comprehensive understanding of the results, generate clear, actionable, and data-driven recommendations.
    *   These recommendations must be justified by the experimental findings and designed to optimize the GEMINI Content Creator's performance.
    *   Propose next steps or follow-up experiments for continuous learning and optimization.

You are expected to provide your output in a structured, easily parsable JSON format, adhering to the sections outlined above.
'''

    def __init__(self):
        super().__init__("ExperimentationAgent")
        self.llm = llm_client
        logger.info(f"{self.agent_name} initialized.")

    async def execute(self, task_description: str, context: dict = None, **kwargs) -> dict:
        """
        Executes the ExperimentationAgent's task, designing an experiment based on the given description and context.

        Args:
            task_description (str): A clear and concise description of the experimental task.
                                    Examples:
                                    - "Design an A/B test for two different tweet headlines to maximize CTR."
                                    - "Propose a Multi-Armed Bandit strategy for optimizing content publishing times across 3 candidate slots."
                                    - "Design a factorial experiment to test the combined effect of emoji usage and image presence on Instagram engagement."
            context (dict, optional): A dictionary containing relevant contextual information for the experiment.
                                      This might include:
                                      - `available_variations`: List of content variants, e.g., `["Headline A", "Headline B"]`.
                                      - `target_platform`: "Twitter", "Blog", "Instagram", etc.
                                      - `target_metric`: "click_through_rate", "engagement_time", "likes", "shares", "conversion_rate".
                                      - `previous_experiment_results`: Summary of prior experiments.
                                      - `audience_segments`: Details about user segments.
                                      - `time_constraints`: e.g., "Experiment must conclude within 7 days."
                                      Defaults to None.
            **kwargs: Additional keyword arguments that might further influence the experiment design,
                      e.g., `confidence_level=0.95`, `power_level=0.80`, `minimum_detectable_effect=0.02`.

        Returns:
            dict: A dictionary containing the detailed experimental design plan, formatted as JSON.
                  Includes sections like objective, hypotheses, experimental_design, execution_plan,
                  metrics_and_data_collection, analysis_plan, and recommendations.
                  Returns an error dict if JSON parsing fails or an exception occurs.
        """
        logger.info(f"{self.agent_name} received execution request for: '{task_description}'")

        user_input = f"**Task Description**: {task_description}\n\n"
        if context:
            user_input += f"**Contextual Information**: {json.dumps(context, indent=2)}\n\n"
        
        if kwargs:
            user_input += f"**Additional Parameters for Design**: {json.dumps(kwargs, indent=2)}\n\n"

        full_prompt = (
            f"{self.SYSTEM_PROMPT}\n\n"
            f"{user_input}\n\n"
            "**Based on the above, provide a comprehensive experimental design plan "
            "in JSON format. The JSON should be structured with the following top-level keys:**\n"
            "1. `objective` (string describing the experiment's goal)\n"
            "2. `hypotheses` (dict with `null_hypothesis` and `alternative_hypothesis` strings)\n"
            "3. `experimental_design` (dict with `type`, `independent_variables`, `dependent_variables`, `control_group_details`, `treatment_group_details`, `randomization_strategy`, `sample_size_calculation`)\n"
            "4. `execution_plan` (dict with `duration`, `stopping_criteria`, `involved_agents`)\n"
            "5. `metrics_and_data_collection` (dict with `primary_metric`, `secondary_metrics`, `data_sources`, `collection_method`)\n"
            "6. `analysis_plan` (dict with `statistical_tests`, `interpretation_criteria`, `rigor_notes`)\n"
            "7. `recommendations` (list of strings with actionable next steps or insights)\n\n"
            "Ensure the JSON is perfectly well-formed, valid, and ready for programmatic parsing without errors. "
            "Focus on delivering a rigorous, actionable, and academically sound experimental blueprint."
        )

        try:
            logger.debug(f"{self.agent_name} sending prompt to LLM...")
            response_content = await self.llm.generate(full_prompt)
            logger.debug(f"Raw LLM response: {response_content[:500]}...") # Log first 500 chars

            # Attempt to parse JSON response
            try:
                parsed_response = json.loads(response_content)
                logger.info(f"{self.agent_name} successfully generated and parsed experimental design.")
                return parsed_response
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response from LLM: {e}. Raw response: {response_content}")
                return {
                    "error": "JSON parsing failed",
                    "message": f"LLM returned malformed JSON: {e}",
                    "raw_llm_response": response_content
                }

        except Exception as e:
            logger.error(f"Error during LLM generation for {self.agent_name}: {e}")
            return {"error": str(e)}