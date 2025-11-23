"""Unit tests for database models and connections."""

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database.models import (
    ABTest,
    ABTestVariant,
    Base,
    CommunityUser,
    ContentFormat,
    ContentPlan,
    Insight,
    InsightType,
    MarketData,
    PerformanceSnapshot,
    PublishedContent,
    TestStatus,
    UserTier,
)


@pytest.fixture
def in_memory_db():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


class TestDatabaseModels:
    """Test database model creation and relationships."""

    def test_market_data_creation(self, in_memory_db):
        """Test creating market data."""
        market_data = MarketData(
            asset="BTC",
            price=50000.0,
            volume_24h=1000000000.0,
            price_change_24h=5.5,
            market_cap=900000000000.0
        )
        in_memory_db.add(market_data)
        in_memory_db.commit()

        assert market_data.id is not None
        assert market_data.asset == "BTC"
        assert market_data.price == 50000.0

    def test_insight_creation(self, in_memory_db):
        """Test creating an insight."""
        insight = Insight(
            type=InsightType.BREAKOUT,
            asset="ETH",
            confidence=0.85,
            details={"reason": "Price broke resistance"},
            is_published=False
        )
        in_memory_db.add(insight)
        in_memory_db.commit()

        assert insight.id is not None
        assert insight.type == InsightType.BREAKOUT
        assert insight.confidence == 0.85

    def test_content_plan_insight_relationship(self, in_memory_db):
        """Test relationship between content plan and insight."""
        # Create insight
        insight = Insight(
            type=InsightType.SENTIMENT_SHIFT,
            asset="BTC",
            confidence=0.9,
            details={"direction": "bullish"}
        )
        in_memory_db.add(insight)
        in_memory_db.commit()

        # Create content plan
        plan = ContentPlan(
            insight_id=insight.id,
            platform="twitter",
            format=ContentFormat.SINGLE_TWEET,
            priority="high",
            status="pending"
        )
        in_memory_db.add(plan)
        in_memory_db.commit()

        # Test relationship
        assert plan.insight is not None
        assert plan.insight.id == insight.id
        assert plan.insight.asset == "BTC"

    def test_published_content_creation(self, in_memory_db):
        """Test creating published content."""
        # Create insight and plan first
        insight = Insight(
            type=InsightType.VOLUME_SPIKE,
            asset="SOL",
            confidence=0.88,
            details={"volume_increase": "200%"}
        )
        in_memory_db.add(insight)
        in_memory_db.commit()

        plan = ContentPlan(
            insight_id=insight.id,
            platform="twitter",
            format=ContentFormat.THREAD,
            status="approved"
        )
        in_memory_db.add(plan)
        in_memory_db.commit()

        # Create published content
        content = PublishedContent(
            content_plan_id=plan.id,
            platform="twitter",
            content_text="Test tweet about SOL volume spike",
            post_url="https://twitter.com/test/123",
            post_id="123",
            views=1000,
            likes=50,
            comments=10,
            shares=5
        )
        in_memory_db.add(content)
        in_memory_db.commit()

        assert content.id is not None
        assert content.views == 1000
        assert content.content_plan.insight.asset == "SOL"


class TestPhase4Models:
    """Test Phase 4 database models."""

    def test_ab_test_creation(self, in_memory_db):
        """Test creating an A/B test."""
        test = ABTest(
            test_name="headline_test_BTC",
            hypothesis="Different headline will increase engagement",
            variable_being_tested="headline",
            asset="BTC",
            platform="twitter",
            status=TestStatus.ACTIVE
        )
        in_memory_db.add(test)
        in_memory_db.commit()

        assert test.id is not None
        assert test.status == TestStatus.ACTIVE
        assert test.variable_being_tested == "headline"

    def test_ab_test_variant_creation(self, in_memory_db):
        """Test creating A/B test variants."""
        # Create test
        test = ABTest(
            test_name="format_test",
            hypothesis="Thread format performs better",
            variable_being_tested="format",
            platform="twitter",
            status=TestStatus.ACTIVE
        )
        in_memory_db.add(test)
        in_memory_db.commit()

        # Create variants
        control = ABTestVariant(
            test_id=test.id,
            variant_name="control",
            is_control=True,
            variant_config={"format": "single_tweet"},
            impressions=1000,
            engagement_count=50,
            sample_size=10
        )
        variant_a = ABTestVariant(
            test_id=test.id,
            variant_name="variant_a",
            is_control=False,
            variant_config={"format": "thread"},
            impressions=1000,
            engagement_count=75,
            sample_size=10
        )

        in_memory_db.add_all([control, variant_a])
        in_memory_db.commit()

        # Test relationship
        assert len(test.variants) == 2
        assert test.variants[0].is_control or test.variants[1].is_control

    def test_performance_snapshot_creation(self, in_memory_db):
        """Test creating performance snapshot."""
        snapshot = PerformanceSnapshot(
            period_type="daily",
            content_published_count=10,
            avg_engagement_rate=0.05,
            total_impressions=10000,
            total_clicks=500,
            new_conversions=2,
            total_paying_members=50,
            revenue=500.0,
            conversion_rate=0.04
        )
        in_memory_db.add(snapshot)
        in_memory_db.commit()

        assert snapshot.id is not None
        assert snapshot.revenue == 500.0
        assert snapshot.period_type == "daily"


class TestPhase3Models:
    """Test Phase 3 database models."""

    def test_community_user_creation(self, in_memory_db):
        """Test creating a community user."""
        user = CommunityUser(
            twitter_id="123456",
            twitter_username="testuser",
            tier=UserTier.FREE,
            engagement_score=75.5,
            total_interactions=100
        )
        in_memory_db.add(user)
        in_memory_db.commit()

        assert user.id is not None
        assert user.tier == UserTier.FREE
        assert user.engagement_score == 75.5

    def test_user_tier_upgrade(self, in_memory_db):
        """Test upgrading user tier."""
        user = CommunityUser(
            twitter_id="123456",
            tier=UserTier.FREE,
            engagement_score=80.0
        )
        in_memory_db.add(user)
        in_memory_db.commit()

        # Upgrade to premium
        user.tier = UserTier.PREMIUM
        user.converted_at = datetime.now(tz=timezone.utc)
        in_memory_db.commit()

        assert user.tier == UserTier.PREMIUM
        assert user.converted_at is not None


def test_all_models_have_required_fields():
    """Test that all models have basic required fields."""
    models = [
        MarketData, Insight, ContentPlan, PublishedContent,
        ABTest, ABTestVariant, PerformanceSnapshot, CommunityUser
    ]

    for model in models:
        # Check that model has an id field
        assert hasattr(model, "id")

        # Check that model has __tablename__
        assert hasattr(model, "__tablename__")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
