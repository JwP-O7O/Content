"""Pytest configuration and fixtures for Content Creator tests."""

import os
from unittest.mock import Mock, patch

import pytest

# Set test environment variables BEFORE any imports
# This is critical because config.py imports at module level
test_env = {
        # Database
        "DATABASE_URL": "postgresql://test:test@localhost:5432/test_db",

        # LLM API Keys
        "ANTHROPIC_API_KEY": "test_anthropic_key",
        "GOOGLE_API_KEY": "test_google_key",
        "OPENAI_API_KEY": "test_openai_key",

        # Social Media
        "TWITTER_API_KEY": "test_twitter_key",
        "TWITTER_API_SECRET": "test_twitter_secret",
        "TWITTER_ACCESS_TOKEN": "test_twitter_token",
        "TWITTER_ACCESS_TOKEN_SECRET": "test_twitter_token_secret",
        "TWITTER_BEARER_TOKEN": "test_twitter_bearer",

        "TELEGRAM_BOT_TOKEN": "test_telegram_token",
        "TELEGRAM_CHANNEL_ID": "@test_channel",

        # Exchange APIs
        "BINANCE_API_KEY": "test_binance_key",
        "BINANCE_API_SECRET": "test_binance_secret",

        # Configuration
        "HUMAN_IN_THE_LOOP": "true",
        "CONTENT_PERSONALITY": "hyper-analytical",
        "LOG_LEVEL": "INFO",

        # Phase 3 - Monetization
        "STRIPE_API_KEY": "sk_test_test",
        "STRIPE_WEBHOOK_SECRET": "whsec_test",
        "STRIPE_PRICE_ID_BASIC": "price_test_basic",
        "STRIPE_PRICE_ID_PREMIUM": "price_test_premium",
        "STRIPE_PRICE_ID_VIP": "price_test_vip",

        # Discord
        "DISCORD_BOT_TOKEN": "test_discord_token",
        "DISCORD_GUILD_ID": "123456789",
        "DISCORD_ROLE_ID_BASIC": "111111111",
        "DISCORD_ROLE_ID_PREMIUM": "222222222",
        "DISCORD_ROLE_ID_VIP": "333333333",

        # Conversion Settings
        "CONVERSION_MIN_ENGAGEMENT_SCORE": "60",
        "CONVERSION_DISCOUNT_PERCENTAGE": "10",
        "CONVERSION_DM_COOLDOWN_DAYS": "30",

        # Phase 4 - Optimization & Self-Learning
        "AB_TESTING_MIN_SAMPLE_SIZE": "100",
        "AB_TESTING_CONFIDENCE_THRESHOLD": "0.95",
        "AB_TESTING_MAX_ACTIVE_TESTS": "5",
        "AB_TESTING_TEST_DURATION_DAYS": "7",

        "STRATEGY_TUNING_MIN_DATA_POINTS": "50",
        "STRATEGY_TUNING_CONFIDENCE_LEVEL": "0.8",
        "STRATEGY_TUNING_MAX_ADJUSTMENTS_PER_RUN": "5",

        "PERFORMANCE_ANALYTICS_SNAPSHOT_RETENTION_DAYS": "90",

        "FEEDBACK_LOOP_OPTIMIZATION_CYCLE_HOURS": "24",
        "FEEDBACK_LOOP_MIN_CONFIDENCE_FOR_CHANGES": "0.85",
}

# Apply test environment immediately, before pytest starts collecting tests
os.environ.update(test_env)


@pytest.fixture(scope="session", autouse=True)
def mock_environment_variables() -> None:
    """Fixture to manage test environment variables.

    Environment is already set at module level, this just ensures cleanup.
    Note: We don't restore the original environment as tests should be isolated.
    """
    yield


@pytest.fixture()
def mock_db_session():
    """Mock database session for tests that need database access."""
    session = Mock()
    session.query = Mock()
    session.add = Mock()
    session.commit = Mock()
    session.rollback = Mock()
    session.close = Mock()
    return session


@pytest.fixture()
def mock_anthropic_client():
    """Mock Anthropic API client."""
    with patch("anthropic.Anthropic") as mock:
        client = Mock()
        mock.return_value = client
        yield client
