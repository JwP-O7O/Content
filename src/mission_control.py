import argparse
import asyncio
import json
import os
import sys

# Add src to path
sys.path.append(os.getcwd())

# Ensure agents can import from src
sys.path.append(os.path.join(os.getcwd(), "src"))

from agents.system_orchestrator_agent import SystemOrchestratorAgent


async def main():
    parser = argparse.ArgumentParser(
        description="Mission Control: Execute a request via the System Orchestrator."
    )
    parser.add_argument("request", help="The mission/request for the system.")
    args = parser.parse_args()

    print("🚀 Mission Control Initialized")
    print(f"👑 CEO (User): {args.request}")
    print("-" * 50)

    orchestrator = SystemOrchestratorAgent()

    # Run the mission
    result = await orchestrator.run(action="execute_mission", request=args.request)

    print("-" * 50)
    print("🏁 Mission Report:")
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    asyncio.run(main())
