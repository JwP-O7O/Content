"""Database models for the Content Creator system."""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean,
    Text, JSON, ForeignKey, Enum
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum


Base = declarative_base()


class MarketData(Base):
    """Raw market data from exchanges."""

    __tablename__ = "market_data"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    asset = Column(String(20), nullable=False, index=True)
    price = Column(Float, nullable=False)
    volume_24h = Column(Float)
    price_change_24h = Column(Float)
    market_cap = Column(Float)
    raw_data = Column(JSON)  # Store full API response
    created_at = Column(DateTime, default=datetime.utcnow)


class NewsArticle(Base):
    """News articles collected from various sources."""

    __tablename__ = "news_articles"

    id = Column(Integer, primary_key=True)
    title = Column(String(500), nullable=False)
    url = Column(String(1000), unique=True)
    source = Column(String(100))
    published_at = Column(DateTime, index=True)
    content = Column(Text)
    summary = Column(Text)
    sentiment_score = Column(Float)  # -1 to 1
    mentioned_assets = Column(JSON)  # List of assets mentioned
    created_at = Column(DateTime, default=datetime.utcnow)


class SentimentData(Base):
    """Social media sentiment data."""

    __tablename__ = "sentiment_data"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    platform = Column(String(50))  # twitter, stocktwits, etc.
    asset = Column(String(20), index=True)
    sentiment_score = Column(Float)  # -1 to 1
    volume = Column(Integer)  # Number of mentions
    influencer_sentiment = Column(Float)  # Weighted by follower count
    raw_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)


class InsightType(enum.Enum):
    """Types of insights the AnalysisAgent can generate."""
    BREAKOUT = "breakout"
    BREAKDOWN = "breakdown"
    SENTIMENT_SHIFT = "sentiment_shift"
    VOLUME_SPIKE = "volume_spike"
    NEWS_IMPACT = "news_impact"
    TECHNICAL_PATTERN = "technical_pattern"
    CORRELATION = "correlation"


class Insight(Base):
    """Analyzed insights from the AnalysisAgent."""

    __tablename__ = "insights"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    type = Column(Enum(InsightType), nullable=False, index=True)
    asset = Column(String(20), nullable=False, index=True)
    confidence = Column(Float, nullable=False)  # 0 to 1
    details = Column(JSON, nullable=False)
    supporting_data_ids = Column(JSON)  # References to market_data, news, etc.
    is_published = Column(Boolean, default=False)
    is_exclusive = Column(Boolean, default=False)  # For paid community
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship to content plans
    content_plans = relationship("ContentPlan", back_populates="insight")


class ContentFormat(enum.Enum):
    """Content format types."""
    SINGLE_TWEET = "single_tweet"
    THREAD = "thread"
    BLOG_POST = "blog_post"
    TELEGRAM_MESSAGE = "telegram_message"
    IMAGE_POST = "image_post"


class ContentPlan(Base):
    """Content planning decisions from ContentStrategistAgent."""

    __tablename__ = "content_plans"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    insight_id = Column(Integer, ForeignKey("insights.id"), nullable=False)
    platform = Column(String(50), nullable=False)  # X, Telegram, Blog
    format = Column(Enum(ContentFormat), nullable=False)
    priority = Column(String(20))  # high, medium, low
    scheduled_for = Column(DateTime)
    status = Column(String(20), default="pending")  # pending, approved, published, rejected
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    insight = relationship("Insight", back_populates="content_plans")
    published_content = relationship("PublishedContent", back_populates="content_plan", uselist=False)


class PublishedContent(Base):
    """Track all published content."""

    __tablename__ = "published_content"

    id = Column(Integer, primary_key=True)
    content_plan_id = Column(Integer, ForeignKey("content_plans.id"), nullable=False)
    platform = Column(String(50), nullable=False)
    content_text = Column(Text, nullable=False)
    media_urls = Column(JSON)  # URLs to images/videos
    post_url = Column(String(1000))
    post_id = Column(String(100))
    published_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Engagement metrics
    views = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    engagement_rate = Column(Float)

    # A/B Testing
    ab_test_variant_id = Column(Integer, ForeignKey("ab_test_variants.id"))

    # Relationships
    content_plan = relationship("ContentPlan", back_populates="published_content")
    ab_test_variant = relationship("ABTestVariant", back_populates="published_content")

    created_at = Column(DateTime, default=datetime.utcnow)


class AgentLog(Base):
    """Log all agent activities for debugging and optimization."""

    __tablename__ = "agent_logs"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    agent_name = Column(String(100), nullable=False, index=True)
    action = Column(String(200), nullable=False)
    status = Column(String(20))  # success, error, warning
    details = Column(JSON)
    error_message = Column(Text)
    execution_time = Column(Float)  # in seconds
    created_at = Column(DateTime, default=datetime.utcnow)


# ============================================================================
# PHASE 3 MODELS - Community Management & Monetization
# ============================================================================


class UserTier(enum.Enum):
    """User membership tiers."""
    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    VIP = "vip"


class CommunityUser(Base):
    """Track users across all platforms and their engagement."""

    __tablename__ = "community_users"

    id = Column(Integer, primary_key=True)

    # Platform identifiers
    twitter_id = Column(String(100), unique=True, index=True)
    twitter_username = Column(String(100))
    telegram_id = Column(String(100), unique=True, index=True)
    telegram_username = Column(String(100))
    discord_id = Column(String(100), unique=True, index=True)
    discord_username = Column(String(100))
    email = Column(String(255), unique=True, index=True)

    # Membership info
    tier = Column(Enum(UserTier), default=UserTier.FREE, nullable=False)
    subscription_status = Column(String(20), default="inactive")  # active, inactive, cancelled

    # Engagement tracking
    total_interactions = Column(Integer, default=0)
    last_interaction = Column(DateTime)
    engagement_score = Column(Float, default=0)  # Calculated score 0-100

    # Conversion tracking
    conversion_dm_sent = Column(Boolean, default=False)
    conversion_dm_sent_at = Column(DateTime)
    conversion_dm_opened = Column(Boolean, default=False)
    conversion_dm_clicked = Column(Boolean, default=False)

    # Timestamps
    first_seen = Column(DateTime, default=datetime.utcnow)
    converted_at = Column(DateTime)  # When they became paying member
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    subscriptions = relationship("Subscription", back_populates="user")
    interactions = relationship("UserInteraction", back_populates="user")


class Subscription(Base):
    """Track user subscriptions and payments."""

    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("community_users.id"), nullable=False)

    # Stripe info
    stripe_customer_id = Column(String(100), unique=True)
    stripe_subscription_id = Column(String(100), unique=True)
    stripe_payment_intent_id = Column(String(100))

    # Subscription details
    tier = Column(Enum(UserTier), nullable=False)
    status = Column(String(20), default="active")  # active, cancelled, past_due, unpaid

    # Pricing
    amount = Column(Float, nullable=False)  # Monthly amount in USD
    currency = Column(String(3), default="USD")

    # Billing cycle
    current_period_start = Column(DateTime)
    current_period_end = Column(DateTime)
    trial_end = Column(DateTime)

    # Cancellation
    cancel_at_period_end = Column(Boolean, default=False)
    cancelled_at = Column(DateTime)
    cancellation_reason = Column(Text)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    user = relationship("CommunityUser", back_populates="subscriptions")


class UserInteraction(Base):
    """Log all user interactions for engagement scoring."""

    __tablename__ = "user_interactions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("community_users.id"), nullable=False)

    interaction_type = Column(String(50), nullable=False)  # like, reply, retweet, dm_open, etc.
    platform = Column(String(20), nullable=False)  # twitter, telegram, discord

    # Context
    content_id = Column(Integer, ForeignKey("published_content.id"))
    interaction_metadata = Column(JSON)  # Additional data about the interaction

    # Value scoring
    engagement_value = Column(Float, default=1.0)  # Weight of this interaction

    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationship
    user = relationship("CommunityUser", back_populates="interactions")


class ConversionAttempt(Base):
    """Track all conversion attempts (DMs sent to users)."""

    __tablename__ = "conversion_attempts"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("community_users.id"), nullable=False)

    # DM details
    platform = Column(String(20), nullable=False)  # twitter, telegram
    message_text = Column(Text, nullable=False)
    discount_code = Column(String(50))
    discount_percentage = Column(Integer)

    # Tracking
    sent_at = Column(DateTime, default=datetime.utcnow)
    opened_at = Column(DateTime)
    clicked_at = Column(DateTime)
    converted_at = Column(DateTime)  # If they subscribed

    # Outcome
    status = Column(String(20), default="sent")  # sent, opened, clicked, converted, ignored

    created_at = Column(DateTime, default=datetime.utcnow)


class ExclusiveContent(Base):
    """Track content that's exclusive to paying members."""

    __tablename__ = "exclusive_content"

    id = Column(Integer, primary_key=True)

    # Link to insight
    insight_id = Column(Integer, ForeignKey("insights.id"), nullable=False)

    # Content details
    content_text = Column(Text, nullable=False)
    platform = Column(String(20), nullable=False)  # discord, telegram_private

    # Exclusivity
    min_tier_required = Column(Enum(UserTier), default=UserTier.BASIC)

    # Publication
    published_at = Column(DateTime, default=datetime.utcnow)
    channel_id = Column(String(100))  # Discord/Telegram channel ID
    message_id = Column(String(100))  # Platform message ID

    # Engagement (from paying members)
    views = Column(Integer, default=0)
    reactions = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)


class ModerationAction(Base):
    """Log all moderation actions taken by CommunityModeratorAgent."""

    __tablename__ = "moderation_actions"

    id = Column(Integer, primary_key=True)

    # User being moderated
    user_id = Column(Integer, ForeignKey("community_users.id"))
    platform_user_id = Column(String(100), nullable=False)

    # Action details
    action_type = Column(String(50), nullable=False)  # warn, mute, kick, ban, delete_message
    reason = Column(String(200), nullable=False)
    platform = Column(String(20), nullable=False)

    # Context
    message_content = Column(Text)  # The offending message
    channel_id = Column(String(100))

    # Automated or manual
    automated = Column(Boolean, default=True)
    agent_confidence = Column(Float)  # If automated, confidence score

    # Duration (for temporary actions)
    duration_minutes = Column(Integer)  # For temporary mutes/bans
    expires_at = Column(DateTime)

    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ============================================================================
# PHASE 4 MODELS - Optimization & Self-Learning
# ============================================================================


class TestStatus(enum.Enum):
    """A/B test status."""
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class ABTest(Base):
    """A/B test experiments for content optimization."""

    __tablename__ = "ab_tests"

    id = Column(Integer, primary_key=True)

    # Test metadata
    test_name = Column(String(200), nullable=False)
    hypothesis = Column(Text)
    variable_being_tested = Column(String(100), nullable=False)  # headline, format, posting_time, cta, etc.

    # Test configuration
    insight_id = Column(Integer, ForeignKey("insights.id"))  # Optional - link to specific insight
    asset = Column(String(20))  # Which asset this test is for
    platform = Column(String(50))  # twitter, telegram, etc.

    # Status
    status = Column(Enum(TestStatus), default=TestStatus.ACTIVE)

    # Results
    winning_variant_id = Column(Integer, ForeignKey("ab_test_variants.id"))
    confidence_level = Column(Float)  # Statistical confidence 0-1
    improvement_percentage = Column(Float)  # % improvement of winner vs control

    # Timestamps
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    variants = relationship("ABTestVariant", back_populates="test", foreign_keys="ABTestVariant.test_id")


class ABTestVariant(Base):
    """Individual variants in an A/B test."""

    __tablename__ = "ab_test_variants"

    id = Column(Integer, primary_key=True)
    test_id = Column(Integer, ForeignKey("ab_tests.id"), nullable=False)

    # Variant details
    variant_name = Column(String(50), nullable=False)  # control, variant_a, variant_b, etc.
    is_control = Column(Boolean, default=False)

    # What's different in this variant
    variant_config = Column(JSON, nullable=False)  # Stores the specific changes

    # Performance metrics
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    engagement_count = Column(Integer, default=0)
    conversion_count = Column(Integer, default=0)

    # Calculated metrics
    click_through_rate = Column(Float, default=0.0)
    engagement_rate = Column(Float, default=0.0)
    conversion_rate = Column(Float, default=0.0)

    # Statistical
    sample_size = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    test = relationship("ABTest", back_populates="variants", foreign_keys=[test_id])
    published_content = relationship("PublishedContent", back_populates="ab_test_variant")


class PerformanceSnapshot(Base):
    """Periodic snapshots of system performance for trend analysis."""

    __tablename__ = "performance_snapshots"

    id = Column(Integer, primary_key=True)

    # Time period
    snapshot_date = Column(DateTime, default=datetime.utcnow, index=True)
    period_type = Column(String(20), default="daily")  # daily, weekly, monthly

    # Content metrics
    content_published_count = Column(Integer, default=0)
    avg_engagement_rate = Column(Float, default=0.0)
    total_impressions = Column(Integer, default=0)
    total_clicks = Column(Integer, default=0)

    # Audience metrics
    new_followers = Column(Integer, default=0)
    total_followers = Column(Integer, default=0)
    follower_growth_rate = Column(Float, default=0.0)

    # Monetization metrics
    new_conversions = Column(Integer, default=0)
    total_paying_members = Column(Integer, default=0)
    revenue = Column(Float, default=0.0)
    conversion_rate = Column(Float, default=0.0)

    # Best performing content
    top_performing_format = Column(String(50))
    top_performing_asset = Column(String(20))
    top_performing_insight_type = Column(String(50))

    # AI performance
    avg_insight_confidence = Column(Float, default=0.0)
    insight_accuracy_rate = Column(Float, default=0.0)  # How often high-confidence insights performed well

    created_at = Column(DateTime, default=datetime.utcnow)
