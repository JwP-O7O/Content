import json
import asyncio
import importlib
from typing import List, Dict, Any
from datetime import datetime

from agents.base_agent import BaseAgent
from utils.llm_client import llm_client
from loguru import logger

class SystemOrchestratorAgent(BaseAgent):
    """
    The COO of the system. 
    Receives high-level objectives from the CEO (Gemini), architectures a dynamic plan,
    selects the optimal sub-agents, and orchestrates execution.
    """
    
    SYSTEM_PROMPT = """
    You are the Chief Operating Officer (COO) and System Orchestrator of an autonomous AI agency.
    Your goal is to execute the CEO's (User/Gemini) requests by effectively utilizing your workforce of specialized AI agents.
    
    Your Responsibilities:
    1. **Analyze**: Deconstruct the User's request into logical steps.
    2. **Select**: Choose the *absolute best* agent for each step from the provided registry.
    3. **Instruct**: Write highly optimized, academic-grade instructions (prompts) for each agent to ensure maximum effectiveness.
    4. **Synthesize**: Combine all outputs into a structured, machine-readable JSON report.
    
    You operate on a strict "Think, Plan, Execute" cycle.
    """

    def __init__(self):
        super().__init__("SystemOrchestratorAgent")
        self.llm = llm_client
        self.registry = self._load_registry()

    def _load_registry(self) -> List[Dict]:
        """Loads the available agents from the registry."""
        try:
            with open("agent_registry.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error("Registry not found!")
            return []

    async def execute(self, request: str, **kwargs) -> Dict[str, Any]:
        """
        Main execution flow: Plan -> Delegate -> Aggregate.
        """
        self.log_info(f"Received Mission from CEO: {request}")
        
        # 1. Architect the Plan
        plan = await self._create_mission_plan(request)
        if not plan:
            return {"status": "error", "message": "Failed to create mission plan."}
        
        self.log_info(f"Mission Plan Created: {len(plan['steps'])} steps.")
        
        # 2. Execute Steps
        mission_log = []
        context = {"original_request": request}
        
        for step in plan['steps']:
            step_result = await self._execute_step(step, context)
            mission_log.append(step_result)
            
            # Update context with result for next agents to see
            context[f"step_{step['id']}_output"] = step_result['output']
            
            # Real-time feedback/check (Simulated for now, could use a critic agent)
            if step_result['status'] == 'error':
                self.log_error(f"Step {step['id']} failed. Stopping mission.")
                break

        # 3. Final Report
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "mission_status": "success" if all(s['status'] == 'success' for s in mission_log) else "partial_failure",
            "plan_execution": mission_log,
            "final_output": context.get(f"step_{plan['steps'][-1]['id']}_output") if plan['steps'] else None
        }

    async def _create_mission_plan(self, request: str) -> Dict:
        """Uses LLM to select agents and define steps."""
        
        agents_list = "\n".join([f"- {a['name']}: {a['description']}" for a in self.registry])
        
        prompt = f"""
        {self.SYSTEM_PROMPT}

        **Available Agents:**
        {agents_list}

        **CEO Request:** "{request}"

        **Task:**
        Create a JSON execution plan. 
        - Break the request down into sequential steps.
        - Assign exactly one agent per step.
        - Provide a "refined_instruction" for that agent. This instruction must be self-contained and include any necessary context from previous steps.
        
        **Output Format (JSON Only):**
        {{
            "rationale": "Why you chose this approach",
            "steps": [
                {{
                    "id": 1,
                    "agent_name": "NameOfAgent",
                    "objective": "Short description",
                    "refined_instruction": "Detailed, optimized prompt for the agent..."
                }}
            ]
        }}
        """
        
        try:
            response = self.llm.generate(prompt, model="gemini")
            cleaned = response.replace("```json", "").replace("```", "").strip()
            return json.loads(cleaned)
        except Exception as e:
            self.log_error(f"Planning failed: {e}")
            return None

    async def _execute_step(self, step: Dict, context: Dict) -> Dict:
        """Instantiates and runs a specific agent."""
        agent_name = step['agent_name']
        instruction = step['refined_instruction']
        
        self.log_info(f"Executing Step {step['id']} with {agent_name}...")
        
        # Find agent info
        agent_info = next((a for a in self.registry if a['name'] == agent_name), None)
        if not agent_info:
            return {"id": step['id'], "status": "error", "error": f"Agent {agent_name} not found"}

        try:
            # Dynamic Import
            # Note: agent_info['module'] is like 'agents.market_scanner_agent'
            # We need to ensure sys.path is correct in the main runner
            module = importlib.import_module(agent_info['module'])
            agent_class = getattr(module, agent_name)
            agent_instance = agent_class()
            
            # Inject context into instruction if needed (basic string formatting)
            # real implementation would be more robust
            
            # Run Agent
            # We pass the instruction as a specialized kwarg or 'action'
            result = await agent_instance.run(action="execute_task", instruction=instruction, context=context)
            
            return {
                "id": step['id'],
                "agent": agent_name,
                "status": "success",
                "output": result
            }
            
        except Exception as e:
            self.log_error(f"Step {step['id']} execution error: {e}")
            return {
                "id": step['id'],
                "agent": agent_name,
                "status": "error",
                "error": str(e)
            }
