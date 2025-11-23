"""Unit tests for agents."""

from unittest.mock import Mock, patch

import pytest

from src.agents.ab_testing_agent import ABTestingAgent
from src.agents.base_agent import BaseAgent
from src.agents.strategy_tuning_agent import StrategyTuningAgent


class TestBaseAgent:
    """Test the base agent functionality."""

    def test_base_agent_initialization(self):
        """Test that base agent initializes correctly."""
        # Create a concrete implementation for testing
        class ConcreteAgent(BaseAgent):
            async def execute(self):
                return {"status": "success"}

        agent = ConcreteAgent("TestAgent")
        assert agent.name == "TestAgent"
        assert hasattr(agent, "log_info")
        assert hasattr(agent, "log_error")

    @pytest.mark.asyncio()
    async def test_base_agent_run_calls_execute(self):
        """Test that run() calls execute()."""
        # Create a concrete implementation for testing
        class ConcreteAgent(BaseAgent):
            def __init__(self, name):
                super().__init__(name)
                self.execute_called = False

            async def execute(self):
                self.execute_called = True
                return {"status": "success"}

        agent = ConcreteAgent("TestAgent")
        result = await agent.run()
        assert agent.execute_called
        assert result == {"status": "success"}


class TestABTestingAgent:
    """Test A/B testing agent."""

    def test_ab_testing_agent_initialization(self):
        """Test A/B testing agent initializes with correct settings."""
        with patch("src.agents.ab_testing_agent.Anthropic"):
            agent = ABTestingAgent()
            assert agent.min_sample_size == 100
            assert agent.confidence_threshold == 0.95
            assert agent.max_active_tests == 5
            assert agent.test_duration_days == 7

    def test_calculate_statistical_significance(self):
        """Test statistical significance calculation."""
        with patch("src.agents.ab_testing_agent.Anthropic"):
            agent = ABTestingAgent()

            # Test with clear winner (high significance)
            confidence = agent._calculate_statistical_significance(
                control_successes=100,
                control_total=1000,
                variant_successes=150,
                variant_total=1000
            )
            assert confidence > 0.95  # Should be highly significant

            # Test with no difference
            confidence = agent._calculate_statistical_significance(
                control_successes=100,
                control_total=1000,
                variant_successes=100,
                variant_total=1000
            )
            assert confidence < 0.9  # Should not be significant

    def test_calculate_statistical_significance_edge_cases(self):
        """Test edge cases in statistical calculation."""
        with patch("src.agents.ab_testing_agent.Anthropic"):
            agent = ABTestingAgent()

            # Zero total should return 0
            confidence = agent._calculate_statistical_significance(
                control_successes=0,
                control_total=0,
                variant_successes=10,
                variant_total=100
            )
            assert confidence == 0.0


class TestStrategyTuningAgent:
    """Test strategy tuning agent."""

    def test_strategy_tuning_agent_initialization(self):
        """Test strategy tuning agent initializes correctly."""
        with patch("src.agents.strategy_tuning_agent.Anthropic"):
            agent = StrategyTuningAgent()
            assert agent.min_data_points == 50
            assert agent.confidence_level == 0.8
            assert agent.max_adjustments_per_run == 5

    @pytest.mark.asyncio()
    async def test_execute_returns_structure(self):
        """Test that execute returns expected structure."""
        with patch("src.agents.strategy_tuning_agent.Anthropic"):
            agent = StrategyTuningAgent()

            # Create async mock functions
            async def mock_content_perf():
                return {"insufficient_data": False}

            async def mock_conversion_perf():
                return {"insufficient_data": False}

            async def mock_posting_times():
                return {"insufficient_data": False}

            async def mock_recommendations():
                return []

            async def mock_adjustments():
                return []

            # Mock the internal methods
            agent._analyze_content_performance = Mock(return_value=mock_content_perf())
            agent._analyze_conversion_performance = Mock(return_value=mock_conversion_perf())
            agent._analyze_optimal_posting_times = Mock(return_value=mock_posting_times())
            agent._generate_tuning_recommendations = Mock(return_value=mock_recommendations())
            agent._apply_strategy_adjustments = Mock(return_value=mock_adjustments())

            result = await agent.execute()

            assert "analyses_performed" in result
            assert "adjustments_made" in result
            assert "recommendations" in result
            assert "performance_improvements" in result


class TestPerformanceAnalytics:
    """Test performance analytics calculations."""

    def test_trend_calculation(self):
        """Test trend calculation logic."""
        from src.agents.performance_analytics_agent import PerformanceAnalyticsAgent

        with patch("src.agents.performance_analytics_agent.Anthropic"):
            agent = PerformanceAnalyticsAgent()

            # Increasing trend
            values = [1.0, 1.2, 1.4, 1.6, 1.8, 2.0]
            trend = agent._calculate_trend(values)
            assert trend is not None
            assert trend["direction"] == "increasing"
            assert trend["change_pct"] > 0

            # Decreasing trend
            values = [2.0, 1.8, 1.6, 1.4, 1.2, 1.0]
            trend = agent._calculate_trend(values)
            assert trend is not None
            assert trend["direction"] == "decreasing"
            assert trend["change_pct"] < 0

            # Stable (no significant trend)
            values = [1.0, 1.01, 1.02, 1.01, 1.0, 1.01]
            trend = agent._calculate_trend(values)
            assert trend is None  # Not significant

    def test_anomaly_detection(self):
        """Test anomaly detection logic."""
        from src.agents.performance_analytics_agent import PerformanceAnalyticsAgent

        with patch("src.agents.performance_analytics_agent.Anthropic"):
            agent = PerformanceAnalyticsAgent()

            # Clear anomaly (spike) - most recent value first
            values = [5.0, 1.0, 1.1, 1.0, 1.1, 1.0]  # First value is outlier
            anomaly = agent._detect_anomaly(values, "test_metric")
            assert anomaly is not None
            assert anomaly["direction"] == "spike"

            # No anomaly
            values = [1.0, 1.1, 1.0, 1.1, 1.0, 1.1]
            anomaly = agent._detect_anomaly(values, "test_metric")
            assert anomaly is None


def test_configuration_loading():
    """Test that configuration loads correctly."""
    from config.config import settings

    # Test that Phase 4 settings are available
    assert hasattr(settings, "ab_testing_min_sample_size")
    assert hasattr(settings, "strategy_tuning_confidence_level")
    assert hasattr(settings, "feedback_loop_optimization_cycle_hours")

    # Test default values
    assert settings.ab_testing_min_sample_size == 100
    assert settings.ab_testing_confidence_threshold == 0.95
    assert settings.strategy_tuning_confidence_level == 0.8


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
