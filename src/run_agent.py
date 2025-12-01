import asyncio
import importlib
import sys
import os
import json
import argparse
from loguru import logger

# Add src to path if needed
sys.path.append(os.getcwd())

def load_registry():
    try:
        with open("agent_registry.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error("agent_registry.json not found. Run generate_registry.py first.")
        sys.exit(1)

async def run_specific_agent(agent_name, action="execute", **kwargs):
    registry = load_registry()
    agent_info = next((a for a in registry if a["name"] == agent_name), None)
    
    if not agent_info:
        logger.error(f"Agent '{agent_name}' not found in registry.")
        print("Available agents:")
        for a in registry:
            print(f"- {a['name']}")
        return

    module_path = agent_info["module"]
    
    try:
        # Dynamic import
        module = importlib.import_module(module_path)
        agent_class = getattr(module, agent_name)
        
        # Instantiate
        agent = agent_class()
        
        # Run
        logger.info(f"Running {agent_name}...")
        result = await agent.run(action=action, **kwargs)
        
        print(f"\n--- Result from {agent_name} ---\n")
        print(json.dumps(result, indent=2, default=str))
        
    except Exception as e:
        logger.error(f"Failed to run {agent_name}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a specific AI agent.")
    parser.add_argument("agent", help="Name of the agent class (e.g. MarketScannerAgent)")
    parser.add_argument("--action", default="execute", help="Action to perform (default: execute)")
    
    args = parser.parse_args()
    
    try:
        asyncio.run(run_specific_agent(args.agent, action=args.action))
    except KeyboardInterrupt:
        pass
