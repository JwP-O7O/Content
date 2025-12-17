"""Configuration management for the Content Creator system."""

from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str = "sqlite:///:memory:"

    # LLM API Keys
    anthropic_api_key: str = "test"
    google_api_key: Optional[str] = None
    google_api_key_backup: Optional[str] = None  # Backup Gemini key for failover
    openai_api_key: Optional[str] = None

    # Social Media
    twitter_api_key: str = "test"
    twitter_api_secret: str = "test"
    twitter_access_token: str = "test"
    twitter_access_token_secret: str = "test"
    twitter_bearer_token: str = "test"

    telegram_bot_token: str = "test"
    telegram_channel_id: str = "test"

    # Exchange APIs
    binance_api_key: Optional[str] = None
    binance_api_secret: Optional[str] = None

    # Configuration
    human_in_the_loop: bool = True
    content_personality: str = "hyper-analytical"
    log_level: str = "INFO"

    # Phase 3 - Monetization
    stripe_api_key: Optional[str] = None
    stripe_webhook_secret: Optional[str] = None
    stripe_price_id_basic: Optional[str] = None
    stripe_price_id_premium: Optional[str] = None
    stripe_price_id_vip: Optional[str] = None

    # Discord
    discord_bot_token: Optional[str] = None
    discord_guild_id: Optional[str] = None
    discord_role_id_basic: Optional[str] = None
    discord_role_id_premium: Optional[str] = None
    discord_role_id_vip: Optional[str] = None

    # Conversion Settings
    conversion_min_engagement_score: int = 60
    conversion_discount_percentage: int = 10
    conversion_dm_cooldown_days: int = 30

    # Phase 4 - Optimization & Self-Learning
    ab_testing_min_sample_size: int = 100
    ab_testing_confidence_threshold: float = 0.95
    ab_testing_max_active_tests: int = 5
    ab_testing_test_duration_days: int = 7

    strategy_tuning_min_data_points: int = 50
    strategy_tuning_confidence_level: float = 0.8
    strategy_tuning_max_adjustments_per_run: int = 5

    performance_analytics_snapshot_retention_days: int = 90

    feedback_loop_optimization_cycle_hours: int = 24
    feedback_loop_min_confidence_for_changes: float = 0.85

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
