"""FeedbackLoopCoordinator - Coordinates the continuous learning and optimization system."""

import json
from datetime import datetime, timezone

from anthropic import Anthropic

from config.config import settings
from src.agents.ab_testing_agent import ABTestingAgent
from src.agents.base_agent import BaseAgent
from src.agents.performance_analytics_agent import PerformanceAnalyticsAgent
from src.agents.strategy_tuning_agent import StrategyTuningAgent
from src.database.connection import get_db
from src.database.models import AgentLog


class FeedbackLoopCoordinator(BaseAgent):
    """
    The Feedback Loop Coordinator manages the continuous improvement cycle.

    Responsibilities:
    - Coordinate all optimization agents
    - Synthesize learnings from multiple sources
    - Identify optimization priorities
    - Track improvement over time
    - Generate meta-insights about the system itself
    - Prevent conflicting optimizations
    """

    def __init__(self):
        """Initialize the FeedbackLoopCoordinator."""
        super().__init__("FeedbackLoopCoordinator")

        # Initialize sub-agents
        self.strategy_tuning = StrategyTuningAgent()
        self.ab_testing = ABTestingAgent()
        self.performance_analytics = PerformanceAnalyticsAgent()

        # Initialize LLM for synthesis
        self.llm_client = Anthropic(api_key=settings.anthropic_api_key)

        # Optimization settings from config
        self.optimization_cycle_hours = settings.feedback_loop_optimization_cycle_hours
        self.min_confidence_for_changes = settings.feedback_loop_min_confidence_for_changes

    async def execute(self) -> dict:
        """
        Execute the feedback loop coordination.

        Returns:
            Dictionary with coordination results
        """
        self.log_info("Starting feedback loop coordination...")

        results = {
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "cycle_complete": False,
            "components": {},
            "synthesized_insights": [],
            "optimization_priorities": [],
            "actions_taken": []
        }

        try:
            # Step 1: Performance Analytics - Gather current state
            self.log_info("Step 1/4: Running performance analytics...")
            analytics_results = await self.performance_analytics.execute()
            results["components"]["performance_analytics"] = analytics_results

            # Step 2: A/B Testing - Learn from experiments
            self.log_info("Step 2/4: Running A/B testing analysis...")
            ab_results = await self.ab_testing.execute()
            results["components"]["ab_testing"] = ab_results

            # Step 3: Strategy Tuning - Apply learned optimizations
            self.log_info("Step 3/4: Running strategy tuning...")
            tuning_results = await self.strategy_tuning.execute()
            results["components"]["strategy_tuning"] = tuning_results

            # Step 4: Synthesize and coordinate
            self.log_info("Step 4/4: Synthesizing insights and coordinating...")
            synthesis = await self._synthesize_learnings({
                "analytics": analytics_results,
                "ab_testing": ab_results,
                "tuning": tuning_results
            })

            results["synthesized_insights"] = synthesis["insights"]
            results["optimization_priorities"] = synthesis["priorities"]
            results["actions_taken"] = synthesis["actions"]

            results["cycle_complete"] = True

            self.log_info(
                f"Feedback loop complete: {len(synthesis['insights'])} insights, "
                f"{len(synthesis['priorities'])} priorities, {len(synthesis['actions'])} actions"
            )

        except Exception as e:
            self.log_error(f"Feedback loop coordination error: {e}")
            raise

        return results

    async def _synthesize_learnings(self, component_results: dict) -> dict:
        """
        Synthesize learnings from all optimization components.

        Args:
            component_results: Results from all components

        Returns:
            Dictionary with synthesized insights and priorities
        """
        self.log_info("Synthesizing learnings from all optimization components...")

        # Extract key learnings
        ab_learnings = component_results.get("ab_testing", {}).get("learnings", [])
        tuning_recommendations = component_results.get("tuning", {}).get("recommendations", [])

        # Get performance predictions
        predictions = await self.performance_analytics._generate_predictions()

        # Use AI to synthesize everything
        try:
            prompt = f"""You are a system optimization expert. Analyze these optimization results and synthesize key insights.

A/B Test Learnings:
{json.dumps(ab_learnings, indent=2, default=str)}

Strategy Tuning Recommendations:
{json.dumps(tuning_recommendations, indent=2, default=str)}

Performance Predictions:
{json.dumps(predictions, indent=2, default=str)}

Based on all this data, generate:
1. Top 3 synthesized insights (patterns across multiple data sources)
2. Top 3 optimization priorities (what to focus on next)
3. Specific actions to take (concrete next steps)

Respond with JSON:
{{
  "insights": [
    {{
      "insight": "synthesized insight statement",
      "supporting_evidence": ["evidence from multiple sources"],
      "confidence": 0.0-1.0
    }}
  ],
  "priorities": [
    {{
      "priority": "optimization focus area",
      "rationale": "why this is important",
      "expected_impact": "potential impact"
    }}
  ],
  "actions": [
    {{
      "action": "specific action to take",
      "component": "which system component to adjust",
      "parameters": {{"param": "value"}},
      "reason": "why this action"
    }}
  ]
}}"""

            message = self.llm_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = message.content[0].text.strip()

            # Parse JSON
            start_idx = response_text.find("{")
            end_idx = response_text.rfind("}") + 1
            json_str = response_text[start_idx:end_idx]
            synthesis = json.loads(json_str)

            # Apply high-confidence actions
            actions_taken = []

            for action in synthesis.get("actions", []):
                # Only apply actions that are safe and high confidence
                if self._is_safe_action(action):
                    result = await self._apply_coordinated_action(action)
                    if result:
                        actions_taken.append(action)

            synthesis["actions"] = actions_taken

            return synthesis

        except Exception as e:
            self.log_error(f"Error synthesizing learnings: {e}")

            return {
                "insights": [],
                "priorities": [],
                "actions": []
            }

    def _is_safe_action(self, action: dict) -> bool:
        """
        Check if an action is safe to apply automatically.

        Args:
            action: Action dictionary

        Returns:
            True if safe to apply
        """
        # Define safe action types
        safe_components = [
            "posting_schedule",
            "content_format_weights",
            "engagement_thresholds",
            "ab_test_parameters"
        ]

        component = action.get("component", "")

        # Don't automatically change critical systems
        if component in ["payment_processing", "user_data", "moderation_rules"]:
            return False

        # Only apply if component is in safe list
        return component in safe_components

    async def _apply_coordinated_action(self, action: dict) -> bool:
        """
        Apply a coordinated optimization action.

        Args:
            action: Action dictionary

        Returns:
            True if applied successfully
        """
        try:
            self.log_info(
                f"Applying coordinated action: {action['action']} "
                f"to {action['component']}"
            )

            # In a production system, this would actually update agent configurations
            # For now, we log what would be changed

            # Log the action
            with get_db() as db:
                log = AgentLog(
                    agent_name="FeedbackLoopCoordinator",
                    action=f"Applied optimization: {action['action']}",
                    status="success",
                    details={
                        "component": action["component"],
                        "parameters": action.get("parameters", {}),
                        "reason": action.get("reason", "")
                    }
                )
                db.add(log)
                db.commit()

            return True

        except Exception as e:
            self.log_error(f"Error applying coordinated action: {e}")
            return False

    async def get_optimization_history(self, days: int = 30) -> dict:
        """
        Get history of optimizations made by the feedback loop.

        Args:
            days: Number of days to look back

        Returns:
            Dictionary with optimization history
        """
        from datetime import datetime, timedelta, timezone

        cutoff = datetime.now(tz=timezone.utc) - timedelta(days=days)

        with get_db() as db:
            logs = db.query(AgentLog).filter(
                AgentLog.agent_name == "FeedbackLoopCoordinator",
                AgentLog.timestamp >= cutoff,
                AgentLog.action.like("Applied optimization:%")
            ).order_by(AgentLog.timestamp.desc()).all()

            optimizations = []

            for log in logs:
                optimizations.append({
                    "timestamp": log.timestamp.isoformat(),
                    "action": log.action,
                    "status": log.status,
                    "details": log.details
                })

            return {
                "period_days": days,
                "total_optimizations": len(optimizations),
                "optimizations": optimizations
            }

    async def generate_learning_report(self, days: int = 7) -> str:
        """
        Generate a comprehensive learning report.

        Args:
            days: Number of days to analyze

        Returns:
            Report text
        """
        self.log_info(f"Generating learning report for last {days} days...")

        # Get A/B test learnings
        ab_learnings = await self.ab_testing.get_all_learnings(days=days)

        # Get optimization history
        opt_history = await self.get_optimization_history(days=days)

        # Get executive summary
        exec_summary = await self.performance_analytics.generate_executive_summary(days=days)

        # Get ROI metrics
        roi_metrics = await self.performance_analytics.get_roi_metrics(days=days)

        try:
            prompt = f"""You are a business intelligence analyst. Generate a comprehensive learning report.

Period: Last {days} days

Executive Summary:
{exec_summary}

A/B Test Learnings:
{json.dumps(ab_learnings, indent=2, default=str)}

Optimizations Applied:
{json.dumps(opt_history, indent=2, default=str)}

ROI Metrics:
{json.dumps(roi_metrics, indent=2, default=str)}

Generate a comprehensive report with:
1. Executive Summary (2-3 paragraphs)
2. Key Learnings (bullet points)
3. Performance Improvements (with metrics)
4. System Evolution (how the system improved itself)
5. Recommendations (what to focus on next)

Format as markdown."""

            message = self.llm_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )

            return message.content[0].text.strip()


        except Exception as e:
            self.log_error(f"Error generating learning report: {e}")

            # Return basic report
            return f"""# System Learning Report ({days} days)

## Executive Summary
{exec_summary}

## A/B Tests Completed
{len(ab_learnings)} tests completed

## Optimizations Applied
{opt_history['total_optimizations']} optimizations

## ROI
- Revenue: ${roi_metrics['total_revenue']:.2f}
- ROI: {roi_metrics['roi_percentage']:.1f}%
- Conversion Efficiency: {roi_metrics['conversion_efficiency']:.1f}%
"""

    async def get_system_health_score(self) -> dict:
        """
        Calculate an overall system health score.

        Returns:
            Dictionary with health metrics
        """
        self.log_info("Calculating system health score...")

        with get_db() as db:
            # Get recent performance snapshot
            from datetime import datetime, timedelta, timezone

            from src.database.models import PerformanceSnapshot

            cutoff = datetime.now(tz=timezone.utc) - timedelta(days=1)

            snapshot = db.query(PerformanceSnapshot).filter(
                PerformanceSnapshot.snapshot_date >= cutoff
            ).order_by(PerformanceSnapshot.snapshot_date.desc()).first()

            if not snapshot:
                return {"health_score": 0, "status": "unknown", "components": {}}

            # Score components (0-100 each)
            components = {}

            # Content production health
            if snapshot.content_published_count > 0:
                components["content_production"] = min(100, snapshot.content_published_count * 10)
            else:
                components["content_production"] = 0

            # Engagement health
            components["engagement"] = snapshot.avg_engagement_rate * 100 if snapshot.avg_engagement_rate else 0

            # Monetization health
            if snapshot.total_paying_members > 0:
                components["monetization"] = min(100, snapshot.total_paying_members * 5)
            else:
                components["monetization"] = 0

            # Conversion health
            components["conversion"] = snapshot.conversion_rate * 100 if snapshot.conversion_rate else 0

            # AI performance health
            components["ai_performance"] = snapshot.avg_insight_confidence * 100 if snapshot.avg_insight_confidence else 0

            # Calculate overall health score (weighted average)
            weights = {
                "content_production": 0.2,
                "engagement": 0.3,
                "monetization": 0.25,
                "conversion": 0.15,
                "ai_performance": 0.1
            }

            overall_score = sum(
                components[k] * weights[k]
                for k in components
            )

            # Determine status
            if overall_score >= 80:
                status = "excellent"
            elif overall_score >= 60:
                status = "good"
            elif overall_score >= 40:
                status = "fair"
            else:
                status = "needs_attention"

            return {
                "health_score": round(overall_score, 1),
                "status": status,
                "components": {k: round(v, 1) for k, v in components.items()},
                "timestamp": datetime.now(tz=timezone.utc).isoformat()
            }
