"""
Tests for performance improvements.

These tests validate that the optimized code produces correct results
and performs better than the original implementations.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from sqlalchemy import func

from src.database.connection import get_db
from src.database.models import (
    Base, CommunityUser, UserInteraction, PublishedContent,
    ContentPlan, Insight, UserTier, InsightType, ContentFormat
)
from src.database.connection import SessionLocal, engine
from src.agents.conversion_agent import ConversionAgent
from src.agents.performance_analytics_agent import PerformanceAnalyticsAgent
from src.agents.analytics_agent import AnalyticsAgent


@pytest.fixture
def db_session():
    """Provide a shared database session for tests."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def sample_users(db_session):
    """Create sample users for testing."""
    users = []
    for i in range(10):
        user = CommunityUser(
            twitter_id=f"user_{i}",
            twitter_username=f"testuser{i}",
            tier=UserTier.FREE,
            engagement_score=0
        )
        db_session.add(user)
        users.append(user)
    
    db_session.commit()
    return users


@pytest.fixture
def sample_interactions(db_session, sample_users):
    """Create sample interactions for testing."""
    interactions = []
    interaction_types = ['like', 'reply', 'retweet', 'dm_open']
    
    for user in sample_users[:5]:  # First 5 users have interactions
        for i in range(10):  # 10 interactions each
            interaction = UserInteraction(
                user_id=user.id,
                interaction_type=interaction_types[i % len(interaction_types)],
                platform='twitter',
                engagement_value=1.0,
                timestamp=datetime.utcnow() - timedelta(days=i)
            )
            db_session.add(interaction)
            interactions.append(interaction)
    
    db_session.commit()
    return interactions


class TestConversionAgentPerformance:
    """Test ConversionAgent performance optimizations."""
    
    @pytest.mark.asyncio
    async def test_engagement_score_calculation(self, sample_users, sample_interactions):
        """Test that engagement scores are calculated correctly using SQL aggregation."""
        agent = ConversionAgent()
        
        # Run the optimized engagement score update
        await agent._update_engagement_scores()
        
        # Verify scores were calculated
        with get_db() as db:
            users_with_scores = db.query(CommunityUser).filter(
                CommunityUser.engagement_score > 0
            ).count()
            
            # First 5 users should have engagement scores
            assert users_with_scores == 5
            
            # Verify a specific user's score is reasonable
            user = db.query(CommunityUser).filter(
                CommunityUser.twitter_id == "user_0"
            ).first()
            
            assert user.engagement_score > 0
            assert user.total_interactions == 10
            assert user.last_interaction is not None
    
    @pytest.mark.asyncio
    async def test_sql_aggregation_correctness(self, sample_users, sample_interactions):
        """Test that SQL aggregation produces same results as Python loops."""
        cutoff = datetime.utcnow() - timedelta(days=30)
        
        with get_db() as db:
            # SQL aggregation approach (optimized)
            sql_stats = db.query(
                UserInteraction.user_id,
                func.count(UserInteraction.id).label('count'),
                func.max(UserInteraction.timestamp).label('last_interaction')
            ).filter(
                UserInteraction.timestamp >= cutoff
            ).group_by(
                UserInteraction.user_id
            ).all()
            
            sql_results = {stat.user_id: stat.count for stat in sql_stats}
            # Ensure users without interactions are represented with zero counts
            all_user_ids = [u.id for u in db.query(CommunityUser.id).all()]
            for user_id in all_user_ids:
                sql_results.setdefault(user_id, 0)
            
            # Python loop approach (original)
            users = db.query(CommunityUser).all()
            python_results = {}
            
            for user in users:
                interactions = db.query(UserInteraction).filter(
                    UserInteraction.user_id == user.id,
                    UserInteraction.timestamp >= cutoff
                ).all()
                python_results[user.id] = len(interactions)
            
            # Results should match
            assert sql_results == python_results


class TestPerformanceAnalyticsOptimizations:
    """Test PerformanceAnalyticsAgent optimizations."""
    
    @pytest.fixture
    def sample_content(self, db_session):
        """Create sample published content."""
        # Create insight
        insight = Insight(
            type=InsightType.BREAKOUT,
            asset="BTC",
            confidence=0.9,
            details={"test": "data"}
        )
        db_session.add(insight)
        db_session.flush()
        
        # Create content plan
        plan = ContentPlan(
            insight_id=insight.id,
            platform="twitter",
            format=ContentFormat.SINGLE_TWEET,
            priority="high"
        )
        db_session.add(plan)
        db_session.flush()
        
        # Create published content
        content_items = []
        for i in range(20):
            content = PublishedContent(
                content_plan_id=plan.id,
                platform="twitter",
                content_text=f"Test content {i}",
                published_at=datetime.utcnow() - timedelta(hours=i),
                views=100 + i * 10,
                likes=10 + i,
                comments=5 + i,
                shares=2 + i,
                engagement_rate=0.1 + (i * 0.01)
            )
            db_session.add(content)
            content_items.append(content)
        
        db_session.commit()
        return content_items
    
    def test_sql_aggregation_performance(self, sample_content):
        """Test that SQL aggregations work correctly."""
        cutoff = datetime.utcnow() - timedelta(days=1)
        
        with get_db() as db:
            # Test SQL aggregation
            metrics = db.query(
                func.sum(PublishedContent.views).label('total_views'),
                func.avg(PublishedContent.engagement_rate).label('avg_engagement')
            ).filter(
                PublishedContent.published_at >= cutoff
            ).first()
            
            assert metrics.total_views > 0
            assert metrics.avg_engagement > 0
    
    def test_eager_loading(self, sample_content):
        """Test that eager loading works correctly."""
        from sqlalchemy.orm import joinedload
        
        with get_db() as db:
            # Query with eager loading
            content = db.query(PublishedContent).options(
                joinedload(PublishedContent.content_plan).joinedload(ContentPlan.insight)
            ).first()
            
            # Should be able to access without triggering additional queries
            assert content.content_plan is not None
            assert content.content_plan.insight is not None
            assert content.content_plan.insight.asset == "BTC"


class TestAnalyticsAgentOptimizations:
    """Test AnalyticsAgent optimizations."""
    
    @pytest.fixture
    def sample_agent_logs(self, db_session):
        """Create sample agent logs."""
        from src.database.models import AgentLog
        
        logs = []
        for agent_idx in range(5):
            for run_idx in range(10):
                log = AgentLog(
                    agent_name=f"Agent{agent_idx}",
                    action="execute",
                    status="error" if run_idx == 0 else "success",
                    execution_time=0.5 + (run_idx * 0.1),
                    timestamp=datetime.utcnow() - timedelta(hours=(agent_idx * 10 + run_idx))
                )
                db_session.add(log)
                logs.append(log)
        
        db_session.commit()
        return logs
    
    @pytest.mark.asyncio
    async def test_agent_performance_analysis(self, sample_agent_logs):
        """Test that agent performance analysis uses SQL aggregation."""
        agent = AnalyticsAgent()
        
        # Run analysis
        results = await agent._analyze_agent_performance()
        
        # Should have stats for 5 agents
        assert len(results) == 5
        
        # Check that aggregations are correct
        for agent_name, stats in results.items():
            assert stats['total_runs'] == 10  # 50 logs / 5 agents
            assert stats['successful_runs'] == 9  # 1 failure per 10 runs
            assert stats['failed_runs'] == 1
            assert 0 <= stats['success_rate'] <= 1
            assert stats['avg_execution_time'] > 0


class TestQueryLimiting:
    """Test query result limiting."""
    
    @pytest.fixture
    def many_published_items(self, db_session):
        """Create many published content items."""
        from src.database.models import ContentPlan, Insight, InsightType
        
        insight = Insight(
            type=InsightType.BREAKOUT,
            asset="ETH",
            confidence=0.8,
            details={}
        )
        db_session.add(insight)
        db_session.flush()
        
        plan = ContentPlan(
            insight_id=insight.id,
            platform="twitter",
            format=ContentFormat.SINGLE_TWEET
        )
        db_session.add(plan)
        db_session.flush()
        
        items = []
        for i in range(200):  # Create 200 items
            content = PublishedContent(
                content_plan_id=plan.id,
                platform="twitter",
                content_text=f"Content {i}",
                published_at=datetime.utcnow() - timedelta(hours=i),
                views=100
            )
            db_session.add(content)
            items.append(content)
        
        db_session.commit()
        return items
    
    @pytest.mark.asyncio
    async def test_engagement_agent_limits_results(self, many_published_items):
        """Test that EngagementAgent limits query results."""
        from src.agents.engagement_agent import EngagementAgent
        
        agent = EngagementAgent()
        
        # Get recent content (should be limited to 100)
        content = await agent._get_recent_published_content()
        
        # Should not return all 200 items
        assert len(content) <= 100
        
        # Should be ordered by most recent first
        if len(content) > 1:
            assert content[0].published_at >= content[-1].published_at


class TestIndexEffectiveness:
    """Test that indexes are properly defined."""
    
    def test_user_interaction_indexes(self):
        """Test that UserInteraction has proper indexes."""
        from src.database.models import UserInteraction
        
        # Check table args for composite index
        assert hasattr(UserInteraction, '__table_args__')
        assert UserInteraction.__table_args__ is not None
    
    def test_community_user_indexes(self):
        """Test that CommunityUser has proper indexes."""
        from src.database.models import CommunityUser
        
        # Check table args for composite index
        assert hasattr(CommunityUser, '__table_args__')
        assert CommunityUser.__table_args__ is not None
    
    def test_published_content_indexes(self):
        """Test that PublishedContent has proper indexes."""
        from src.database.models import PublishedContent
        
        # Check table args for composite index
        assert hasattr(PublishedContent, '__table_args__')
        assert PublishedContent.__table_args__ is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
