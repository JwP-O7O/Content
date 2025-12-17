"""Quick test script for API keys."""

import asyncio
from loguru import logger
from src.utils.llm_client import llm_client

async def test_keys():
    """Test all configured API keys."""
    
    print("="*60)
    print("Testing API Keys")
    print("="*60)
    
    # Test Gemini
    print("\n1. Testing Gemini (primary key)...")
    try:
        response = llm_client.generate_with_gemini(
            "Say 'Gemini API works!' in exactly 3 words."
        )
        print(f"✅ Gemini primary: {response[:100]}")
    except Exception as e:
        print(f"❌ Gemini primary failed: {e}")
    
    # Test Claude
    print("\n2. Testing Claude (Anthropic)...")
    try:
        response = llm_client.generate_with_claude(
            "Say 'Claude API works!' in exactly 3 words.",
            max_tokens=50
        )
        print(f"✅ Claude: {response[:100]}")
    except Exception as e:
        print(f"❌ Claude failed: {e}")
    
    # Test generic generate method
    print("\n3. Testing generic generate() with Gemini...")
    try:
        response = llm_client.generate(
            "What is 2+2? Answer in one word.",
            model="gemini"
        )
        print(f"✅ Generic (Gemini): {response[:100]}")
    except Exception as e:
        print(f"❌ Generic failed: {e}")
    
    print("\n" + "="*60)
    print("API Key Test Complete!")
    print("="*60)
    print(f"\nActive Gemini key: {llm_client.get_active_gemini_key()}")

if __name__ == "__main__":
    asyncio.run(test_keys())
