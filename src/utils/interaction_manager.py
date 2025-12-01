"""
Interaction Manager - Handles recording user interactions and updating scores incrementally.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from src.database.models import CommunityUser, UserInteraction, UserTier
from src.utils.logger import logger

class InteractionManager:
    """
    Manages user interactions and real-time score updates.
    """
    
    # Weights for different interaction types
    INTERACTION_WEIGHTS = {
        "like": 1.0,
        "reply": 3.0,
        "retweet": 2.0,
        "quote": 4.0,
        "dm_open": 5.0,
        "dm_click": 10.0,
        "mention": 3.0,
        "click": 2.0,
        "view": 0.1
    }

    @classmethod
    def record_interaction(
        cls, 
        db: Session,
        user_id: int,
        platform: str,
        interaction_type: str,
        content_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> UserInteraction:
        """
        Record a new interaction and update user's score incrementally.
        
        Args:
            db: Database session
            user_id: ID of the user
            platform: 'twitter', 'discord', 'telegram'
            interaction_type: Type of interaction (like, reply, etc.)
            content_id: Optional ID of the content interacted with
            metadata: Optional additional data
            
        Returns:
            The created UserInteraction object
        """
        
        # 1. Determine weight
        weight = cls.INTERACTION_WEIGHTS.get(interaction_type, 1.0)
        
        # 2. Create Interaction Record
        interaction = UserInteraction(
            user_id=user_id,
            platform=platform,
            interaction_type=interaction_type,
            content_id=content_id,
            interaction_metadata=metadata,
            engagement_value=weight,
            timestamp=datetime.utcnow()
        )
        db.add(interaction)
        
        # 3. Update User Stats Immediately (Incremental Update)
        user = db.query(CommunityUser).filter(CommunityUser.id == user_id).first()
        if user:
            user.total_interactions += 1
            user.last_interaction = datetime.utcnow()
            
            # Update Score: Simple addition + clamping (optional normalization logic could go here)
            # Current simple logic: Score = Score + (Weight * 0.5)
            # We multiply by a factor to keep scores manageable or use a sigmoid function in future
            increment = weight * 0.5
            user.engagement_score = min(100.0, user.engagement_score + increment)
            
            logger.info(f"Recorded interaction for user {user_id}. Score updated to {user.engagement_score}")
        
        return interaction

    @classmethod
    def decay_scores(cls, db: Session, decay_factor: float = 0.95):
        """
        Apply decay to all users' engagement scores.
        Should be run periodically (e.g., daily).
        """
        # This executes a single SQL update for efficiency instead of looping
        db.query(CommunityUser).update(
            {CommunityUser.engagement_score: CommunityUser.engagement_score * decay_factor},
            synchronize_session=False
        )
        db.commit()
        logger.info(f"Applied engagement score decay (factor: {decay_factor})")
