"""Test publishing agent directly."""

import asyncio
from src.agents.publishing_agent import PublishingAgent

async def test_publishing():
    """Test publishing agent."""

    print("="*60)
    print("Testing Publishing Agent")
    print("="*60)

    agent = PublishingAgent()

    print(f"\nHuman-in-the-loop: {agent.human_in_the_loop}")

    result = await agent.run()

    print(f"\n📊 Results:")
    print(f"   Awaiting approval: {result['awaiting_approval']}")
    print(f"   Published: {result['content_published']}")
    print(f"   Errors: {len(result['errors'])}")

    if result['errors']:
        for err in result['errors']:
            print(f"   ⚠️  {err}")

    print("\n" + "="*60)

if __name__ == "__main__":
    asyncio.run(test_publishing())
