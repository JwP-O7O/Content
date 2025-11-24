"""Add performance indexes to the database."""

from sqlalchemy import Index, create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from config.config import settings
from src.database.models import Base, UserInteraction, PublishedContent, CommunityUser


def add_performance_indexes():
    """Add indexes to improve query performance."""
    
    engine = create_engine(settings.database_url)
    
    # Create indexes for frequently queried columns
    indexes = [
        # UserInteraction indexes for engagement score calculations
        Index('idx_user_interaction_user_timestamp', 
              UserInteraction.user_id, UserInteraction.timestamp),
        Index('idx_user_interaction_timestamp', 
              UserInteraction.timestamp),
        
        # PublishedContent indexes for analytics queries
        Index('idx_published_content_published_at', 
              PublishedContent.published_at),
        Index('idx_published_content_platform_published_at', 
              PublishedContent.platform, PublishedContent.published_at),
        
        # CommunityUser indexes for conversion queries
        Index('idx_community_user_tier_engagement', 
              CommunityUser.tier, CommunityUser.engagement_score),
        Index('idx_community_user_last_interaction', 
              CommunityUser.last_interaction),
    ]
    
    print("Creating performance indexes...")
    
    with engine.connect() as conn:
        for index in indexes:
            try:
                index.create(conn, checkfirst=True)
                print(f"✓ Created index: {index.name}")
            except Exception as e:
                # Check if it's an "already exists" error (can be ignored)
                error_msg = str(e).lower()
                if 'already exists' in error_msg or 'duplicate' in error_msg:
                    print(f"⚠ Index {index.name} already exists, skipping...")
                else:
                    print(f"✗ Error creating index {index.name}: {e}")
                    print(f"   Error type: {type(e).__name__}")
                    # Continue with other indexes even if one fails
    
    print("\nIndexes created successfully!")


if __name__ == "__main__":
    add_performance_indexes()
