"""Test content creation pipeline directly."""

import asyncio
from loguru import logger
from src.orchestrator import AgentOrchestrator

async def test_content_creation():
    """Test the content creation pipeline."""

    print("="*60)
    print("Testing Content Creation Pipeline")
    print("="*60)

    # Initialize orchestrator
    orchestrator = AgentOrchestrator()

    # Run content creation pipeline
    print("\n1. Running content creation pipeline...")
    result = await orchestrator.run_content_creation_pipeline()

    print(f"\n✅ Content creation completed!")
    print(f"Result: {result}")

    print("\n" + "="*60)
    print("Content Creation Test Complete!")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(test_content_creation())
