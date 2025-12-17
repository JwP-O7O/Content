import asyncio
import sys
import os
from loguru import logger

# Add parent directory to path so 'src' module is resolvable
sys.path.append(os.path.abspath(".."))

from src.agents.system_architect_agent import SystemArchitectAgent

async def main():
    architect = SystemArchitectAgent()
    
    # Use absolute path to ensure it's found
    docs = [os.path.join(os.getcwd(), "PROJECT_PLAN.md")]
    
    print(f"Running Architect on {docs}...")
    result = await architect.run(action="execute", doc_paths=docs)
    
    import json
    print(json.dumps(result, indent=2, default=str))

if __name__ == "__main__":
    asyncio.run(main())
