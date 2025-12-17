"""
Utility script to create API keys for the Content Creator system.
"""

import sys
import os
import secrets
import hashlib
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.database.connection import get_db, init_db
from src.database.models import APIKey, Base

def create_key(owner_name: str, owner_email: str = None):
    """Generate and store a new API key."""
    
    # Generate a secure random key
    # Format: pk_ (public key) + 32 random hex chars
    raw_key = f"pk_{secrets.token_hex(16)}"
    
    # Hash the key for storage (SHA-256)
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    
    with get_db() as db:
        # Create DB record
        new_key = APIKey(
            key_hash=key_hash,
            owner_name=owner_name,
            owner_email=owner_email,
            is_active=True
        )
        db.add(new_key)
        db.commit()
        
        print(f"\n✅ API Key Created Successfully!")
        print(f"Owner: {owner_name}")
        print(f"Key: {raw_key}")
        print(f"⚠️  SAVE THIS KEY NOW. You won't be able to see it again.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python create_api_key.py <owner_name> [owner_email]")
        sys.exit(1)
        
    name = sys.argv[1]
    email = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Ensure tables exist (specifically api_keys)
    init_db()
    
    create_key(name, email)
