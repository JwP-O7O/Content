"""ABTestingAgent - Automatically tests content variations for optimization."""

import json
import math
from datetime import datetime, timedelta, timezone
from typing import Optional

from anthropic import Anthropic

from config.config import settings
from src.agents.base_agent import BaseAgent
from src.database.connection import get_db
from src.database.models import (
    ABTest,
    ABTestVariant,
    Insight,
    PublishedContent,
    TestStatus,
)


class ABTestingAgent(BaseAgent):
    """
    The A/B Testing Agent automatically creates and analyzes content experiments.

    Responsibilities:
    - Identify opportunities for A/B testing
    - Generate test variants using AI
    - Monitor active tests
    - Calculate statistical significance
    - Declare winners and share learnings
    - Feed results to StrategyTuningAgent
    """

    def __init__(self):
        """Initialize the ABTestingAgent."""
        super().__init__("ABTestingAgent")

        # Initialize LLM for variant generation
        self.llm_client = Anthropic(api_key=settings.anthropic_api_key)

        # Testing parameters from config
        self.min_sample_size = settings.ab_testing_min_sample_size
        self.confidence_threshold = settings.ab_testing_confidence_threshold
        self.max_active_tests = settings.ab_testing_max_active_tests
        self.test_duration_days = settings.ab_testing_test_duration_days

        # Variables we can test
        self.testable_variables = [
            "headline",
            "format",
            "posting_time",
            "call_to_action",
            "emoji_usage",
            "hashtag_count"
        ]

    async def execute(self) -> dict:
        """
        Execute A/B testing workflow.

        Returns:
            Dictionary with testing results
        """
        self.log_info("Starting A/B testing workflow...")

        results = {
            "new_tests_created": 0,
            "tests_analyzed": 0,
            "tests_completed": 0,
            "winners_declared": 0,
            "learnings": []
        }

        try:
            # Step 1: Analyze active tests
            analysis_results = await self._analyze_active_tests()
            results["tests_analyzed"] = analysis_results["analyzed_count"]
            results["tests_completed"] = analysis_results["completed_count"]
            results["winners_declared"] = analysis_results["winners_count"]
            results["learnings"] = analysis_results["learnings"]

            # Step 2: Create new tests if we have capacity
            new_test_results = await self._create_new_tests()
            results["new_tests_created"] = new_test_results["created_count"]

            self.log_info(
                f"A/B testing complete: {results['new_tests_created']} new tests, "
                f"{results['tests_completed']} completed, {results['winners_declared']} winners"
            )

        except Exception as e:
            self.log_error(f"A/B testing error: {e}")
            raise

        return results

    async def _analyze_active_tests(self) -> dict:
        """
        Analyze all active A/B tests.

        Returns:
            Dictionary with analysis results
        """
        self.log_info("Analyzing active A/B tests...")

        with get_db() as db:
            active_tests = db.query(ABTest).filter(
                ABTest.status == TestStatus.ACTIVE
            ).all()

            analyzed_count = 0
            completed_count = 0
            winners_count = 0
            learnings = []

            for test in active_tests:
                analyzed_count += 1

                # Check if test has enough data
                variants = db.query(ABTestVariant).filter(
                    ABTestVariant.test_id == test.id
                ).all()

                # Update variant metrics from published content
                for variant in variants:
                    await self._update_variant_metrics(variant, db)

                # Check if we can determine a winner
                winner = await self._analyze_test_results(test, variants)

                if winner:
                    # Complete the test
                    test.status = TestStatus.COMPLETED
                    test.completed_at = datetime.now(tz=timezone.utc)
                    test.winning_variant_id = winner["variant_id"]
                    test.confidence_level = winner["confidence"]
                    test.improvement_percentage = winner["improvement"]

                    db.commit()

                    completed_count += 1
                    winners_count += 1

                    # Extract learning
                    learning = {
                        "test_name": test.test_name,
                        "variable": test.variable_being_tested,
                        "winner": winner["variant_name"],
                        "improvement": f"{winner['improvement']:.1f}%",
                        "confidence": f"{winner['confidence']:.0%}",
                        "insight": winner["insight"]
                    }

                    learnings.append(learning)

                    self.log_info(
                        f"Test '{test.test_name}' complete: "
                        f"{winner['variant_name']} won with {winner['improvement']:.1f}% improvement"
                    )

                # Check for stale tests (running too long)
                test_age = datetime.now(tz=timezone.utc) - test.started_at
                if test_age.days > self.test_duration_days:
                    # No clear winner after max duration
                    if not winner:
                        test.status = TestStatus.COMPLETED
                        test.completed_at = datetime.now(tz=timezone.utc)
                        db.commit()

                        completed_count += 1

                        self.log_info(
                            f"Test '{test.test_name}' completed without clear winner "
                            f"(duration exceeded {self.test_duration_days} days)"
                        )

            return {
                "analyzed_count": analyzed_count,
                "completed_count": completed_count,
                "winners_count": winners_count,
                "learnings": learnings
            }

    async def _update_variant_metrics(self, variant: ABTestVariant, db) -> None:
        """
        Update variant metrics from published content.

        Args:
            variant: The variant to update
            db: Database session
        """
        # Get all published content for this variant
        content_items = db.query(PublishedContent).filter(
            PublishedContent.ab_test_variant_id == variant.id
        ).all()

        if not content_items:
            return

        # Aggregate metrics
        total_views = sum(c.views or 0 for c in content_items)
        total_likes = sum(c.likes or 0 for c in content_items)
        total_comments = sum(c.comments or 0 for c in content_items)
        total_shares = sum(c.shares or 0 for c in content_items)

        variant.impressions = total_views
        variant.engagement_count = total_likes + total_comments + total_shares
        variant.sample_size = len(content_items)

        # Calculate rates
        if total_views > 0:
            variant.engagement_rate = variant.engagement_count / total_views
            variant.click_through_rate = (total_likes + total_shares) / total_views

        db.commit()

    async def _analyze_test_results(
        self,
        test: ABTest,
        variants: list[ABTestVariant]
    ) -> Optional[dict]:
        """
        Analyze test results to determine if there's a clear winner.

        Args:
            test: The A/B test
            variants: List of variants

        Returns:
            Winner details or None if no clear winner yet
        """
        if len(variants) < 2:
            return None

        # Find control variant
        control = next((v for v in variants if v.is_control), variants[0])

        # Check if control has enough data
        if control.sample_size < self.min_sample_size:
            return None

        # Compare each variant to control
        best_variant = None
        best_improvement = 0
        best_confidence = 0

        for variant in variants:
            if variant.id == control.id:
                continue

            if variant.sample_size < self.min_sample_size:
                continue

            # Calculate improvement
            if control.engagement_rate > 0:
                improvement = (
                    (variant.engagement_rate - control.engagement_rate)
                    / control.engagement_rate
                ) * 100
            else:
                improvement = 0

            # Calculate statistical significance
            confidence = self._calculate_statistical_significance(
                control.engagement_count,
                control.impressions,
                variant.engagement_count,
                variant.impressions
            )

            # Check if this is a winning variant
            if (confidence >= self.confidence_threshold and
                improvement > best_improvement):

                best_variant = variant
                best_improvement = improvement
                best_confidence = confidence

        if best_variant:
            # Generate insight using AI
            insight = await self._generate_test_insight(
                test,
                control,
                best_variant,
                best_improvement
            )

            return {
                "variant_id": best_variant.id,
                "variant_name": best_variant.variant_name,
                "improvement": best_improvement,
                "confidence": best_confidence,
                "insight": insight
            }

        return None

    def _calculate_statistical_significance(
        self,
        control_successes: int,
        control_total: int,
        variant_successes: int,
        variant_total: int
    ) -> float:
        """
        Calculate statistical significance using z-test for proportions.

        Args:
            control_successes: Number of engagements for control
            control_total: Total impressions for control
            variant_successes: Number of engagements for variant
            variant_total: Total impressions for variant

        Returns:
            Confidence level (0-1)
        """
        if control_total == 0 or variant_total == 0:
            return 0.0

        # Calculate proportions
        p1 = control_successes / control_total
        p2 = variant_successes / variant_total

        # Pooled proportion
        p_pool = (control_successes + variant_successes) / (control_total + variant_total)

        # Standard error
        se = math.sqrt(p_pool * (1 - p_pool) * (1/control_total + 1/variant_total))

        if se == 0:
            return 0.0

        # Z-score
        z = abs(p2 - p1) / se

        # Convert z-score to confidence level (simplified)
        # z=1.96 ≈ 95% confidence, z=2.58 ≈ 99% confidence
        if z >= 2.58:
            return 0.99
        if z >= 1.96:
            return 0.95
        if z >= 1.645:
            return 0.90
        return min(0.85, z / 1.96 * 0.95)

    async def _generate_test_insight(
        self,
        test: ABTest,
        control: ABTestVariant,
        winner: ABTestVariant,
        improvement: float
    ) -> str:
        """
        Generate insight about why a variant won using AI.

        Args:
            test: The A/B test
            control: Control variant
            winner: Winning variant
            improvement: Improvement percentage

        Returns:
            Insight text
        """
        try:
            prompt = f"""You are an A/B testing expert. Analyze these test results and provide a concise insight.

Test: {test.test_name}
Variable Tested: {test.variable_being_tested}

Control variant: {json.dumps(control.variant_config, indent=2)}
- Engagement rate: {control.engagement_rate:.2%}

Winning variant: {json.dumps(winner.variant_config, indent=2)}
- Engagement rate: {winner.engagement_rate:.2%}
- Improvement: {improvement:.1f}%

Provide a single-sentence insight explaining why the winning variant likely performed better."""

            message = self.llm_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}]
            )

            return message.content[0].text.strip()

        except Exception as e:
            self.log_error(f"Error generating test insight: {e}")
            return f"Variant {winner.variant_name} performed {improvement:.1f}% better than control"

    async def _create_new_tests(self) -> dict:
        """
        Create new A/B tests based on opportunities.

        Returns:
            Dictionary with creation results
        """
        self.log_info("Checking for A/B testing opportunities...")

        with get_db() as db:
            # Check how many active tests we have
            active_count = db.query(ABTest).filter(
                ABTest.status == TestStatus.ACTIVE
            ).count()

            if active_count >= self.max_active_tests:
                self.log_info(f"Already at max active tests ({self.max_active_tests})")
                return {"created_count": 0}

            # Find high-confidence insights that could benefit from testing
            cutoff = datetime.now(tz=timezone.utc) - timedelta(days=1)

            insights = db.query(Insight).filter(
                Insight.timestamp >= cutoff,
                Insight.confidence >= 0.85,
                Insight.is_published.is_(False)
            ).limit(3).all()

            created_count = 0

            for insight in insights:
                if active_count + created_count >= self.max_active_tests:
                    break

                # Create a test for this insight
                test = await self._create_test_for_insight(insight, db)

                if test:
                    created_count += 1
                    self.log_info(f"Created A/B test: {test.test_name}")

            return {"created_count": created_count}

    async def _create_test_for_insight(
        self,
        insight: Insight,
        db
    ) -> Optional[ABTest]:
        """
        Create an A/B test for a specific insight.

        Args:
            insight: The insight to test
            db: Database session

        Returns:
            Created ABTest or None
        """
        try:
            # Choose what to test (randomly pick a variable for now)
            import random
            variable = random.choice(self.testable_variables)

            # Create test
            test = ABTest(
                test_name=f"{insight.asset}_{insight.type.value}_{variable}_test",
                hypothesis=f"Testing different {variable} variations for {insight.asset} {insight.type.value}",
                variable_being_tested=variable,
                insight_id=insight.id,
                asset=insight.asset,
                platform="twitter",
                status=TestStatus.ACTIVE
            )

            db.add(test)
            db.flush()

            # Generate variants using AI
            variants = await self._generate_test_variants(
                insight,
                variable,
                test.id
            )

            for variant_data in variants:
                variant = ABTestVariant(
                    test_id=test.id,
                    variant_name=variant_data["name"],
                    is_control=variant_data["is_control"],
                    variant_config=variant_data["config"]
                )
                db.add(variant)

            db.commit()

            return test

        except Exception as e:
            self.log_error(f"Error creating test for insight {insight.id}: {e}")
            db.rollback()
            return None

    async def _generate_test_variants(
        self,
        insight: Insight,
        variable: str,
        test_id: int
    ) -> list[dict]:
        """
        Generate test variants using AI.

        Args:
            insight: The insight
            variable: Variable being tested
            test_id: Test ID

        Returns:
            List of variant configurations
        """
        try:
            prompt = f"""You are a content optimization expert. Generate 2 variations to A/B test.

Insight: {json.dumps(insight.details, indent=2)}
Asset: {insight.asset}
Type: {insight.type.value}

Variable to test: {variable}

Generate a control variant and one test variant. For each variant, specify the {variable} configuration.

Respond with JSON:
[
  {{
    "name": "control",
    "is_control": true,
    "config": {{"the config for control variant"}}
  }},
  {{
    "name": "variant_a",
    "is_control": false,
    "config": {{"the config for test variant"}}
  }}
]

Be creative and data-driven in your variations."""

            message = self.llm_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = message.content[0].text.strip()

            # Parse JSON
            start_idx = response_text.find("[")
            end_idx = response_text.rfind("]") + 1
            json_str = response_text[start_idx:end_idx]
            return json.loads(json_str)


        except Exception as e:
            self.log_error(f"Error generating variants: {e}")

            # Return default variants
            return [
                {
                    "name": "control",
                    "is_control": True,
                    "config": {variable: "standard"}
                },
                {
                    "name": "variant_a",
                    "is_control": False,
                    "config": {variable: "optimized"}
                }
            ]

    async def get_test_results(self, test_id: int) -> dict:
        """
        Get detailed results for a specific test.

        Args:
            test_id: Test ID

        Returns:
            Dictionary with test results
        """
        with get_db() as db:
            test = db.query(ABTest).filter(ABTest.id == test_id).first()

            if not test:
                return {"error": "Test not found"}

            variants = db.query(ABTestVariant).filter(
                ABTestVariant.test_id == test_id
            ).all()

            return {
                "test_name": test.test_name,
                "status": test.status.value,
                "variable": test.variable_being_tested,
                "started_at": test.started_at.isoformat() if test.started_at else None,
                "completed_at": test.completed_at.isoformat() if test.completed_at else None,
                "winning_variant_id": test.winning_variant_id,
                "confidence_level": test.confidence_level,
                "improvement_percentage": test.improvement_percentage,
                "variants": [
                    {
                        "id": v.id,
                        "name": v.variant_name,
                        "is_control": v.is_control,
                        "config": v.variant_config,
                        "impressions": v.impressions,
                        "engagement_count": v.engagement_count,
                        "engagement_rate": v.engagement_rate,
                        "sample_size": v.sample_size
                    }
                    for v in variants
                ]
            }

    async def get_all_learnings(self, days: int = 30) -> list[dict]:
        """
        Get all learnings from completed tests.

        Args:
            days: Number of days to look back

        Returns:
            List of learnings
        """
        cutoff = datetime.now(tz=timezone.utc) - timedelta(days=days)

        with get_db() as db:
            completed_tests = db.query(ABTest).filter(
                ABTest.status == TestStatus.COMPLETED,
                ABTest.completed_at >= cutoff
            ).all()

            learnings = []

            for test in completed_tests:
                if not test.winning_variant_id:
                    continue

                winner = db.query(ABTestVariant).filter(
                    ABTestVariant.id == test.winning_variant_id
                ).first()

                learnings.append({
                    "test_name": test.test_name,
                    "variable": test.variable_being_tested,
                    "winner_config": winner.variant_config if winner else {},
                    "improvement": test.improvement_percentage,
                    "confidence": test.confidence_level,
                    "completed_at": test.completed_at.isoformat()
                })

            return learnings
