"""SystemArchitectAgent - Analyzes documentation and builds specialized sub-agents."""

import os
import json
import re
import asyncio
from typing import List, Dict, Any
from datetime import datetime

from src.agents.base_agent import BaseAgent
from src.utils.llm_client import llm_client
from loguru import logger

class SystemArchitectAgent(BaseAgent):
    """
    The System Architect Agent reads project documentation (README, ROADMAP, Business Plans)
    and autonomously designs and generates specialized sub-agents with academic-grade
    system prompts to fulfill the project's goals.
    """

    def __init__(self):
        super().__init__("SystemArchitectAgent")
        self.llm = llm_client
        self.agents_dir = "agents" # Corrected path relative to where we run

    async def execute(self, doc_paths: List[str], **kwargs) -> Dict[str, Any]:
        """
        Analyze documents and generate agents.

        Args:
            doc_paths: List of file paths to read (e.g., ["README.md", "ROADMAP.md"])
        """
        self.log_info(f"Starting System Architecture analysis on: {doc_paths}")

        # 1. Read Documents
        context_content = ""
        for path in doc_paths:
            if os.path.exists(path):
                try:
                    with open(path, 'r') as f:
                        context_content += f"\n--- CONTENT OF {path} ---\n"
                        context_content += f.read()
                except Exception as e:
                    self.log_error(f"Could not read {path}: {e}")
            else:
                self.log_warning(f"File not found: {path}")

        if not context_content:
            return {"status": "error", "message": "No content found in provided paths."}

        # 2. Architect the Solution (Define Agents)
        architecture = await self._design_architecture(context_content)
        
        if not architecture:
             return {"status": "error", "message": "Failed to design architecture."}

        # 3. Generate Code for each Agent
        generated_agents = []
        for agent_def in architecture.get("agents", []):
            success = await self._generate_agent_code(agent_def, context_content)
            if success:
                generated_agents.append(agent_def["name"])

        # 4. Update Registry
        await self._update_registry()

        return {
            "status": "success",
            "architecture_plan": architecture,
            "generated_agents": generated_agents
        }

    async def _design_architecture(self, context: str) -> Dict:
        """Uses LLM to design the agent architecture based on docs."""
        self.log_info("Designing multi-agent architecture...")

        prompt = f"""
        You are a Distinguished Professor of Artificial Intelligence Engineering and System Architecture.
        
        Based on the following project documentation, design a Multi-Agent System (MAS) that perfectly executes the project goals.
        
        Analyze the specific domain (e.g., Trading, Content, Healthcare) and propose agents that are:
        1. Highly Specialized (separation of concerns).
        2. Theoretically Grounded (using specific academic frameworks suitable for the task).
        3. Necessary for the roadmap.

        DOCUMENTATION:
        {context[:25000]}  # Truncate if too long

        Output purely JSON with this structure (no markdown, no code blocks):
        {{
            "rationale": "Brief explanation of the architecture choice.",
            "agents": [
                {{
                    "name": "NameAgent", 
                    "role": "Specific Role",
                    "academic_framework": "e.g. Chain-of-Thought, ReAct, Game Theory, Bayesian Inference",
                    "responsibility": "Core task description"
                }}
            ]
        }}
        """
        
        try:
            response = self.llm.generate(prompt, model="gemini")
            # Clean cleanup json
            response = response.replace("```json", "").replace("```", "").strip()
            return json.loads(response)
        except Exception as e:
            self.log_error(f"Architecture design failed: {e}")
            return None

    async def _generate_agent_code(self, agent_def: Dict, context: str) -> bool:
        """Generates the Python code for a single agent."""
        name = agent_def['name']
        self.log_info(f"Generating code for {name}...")

        # We construct the prompt carefully to avoid syntax errors in the python code string
        prompt = f"""
        You are a Lead Python Developer and AI Researcher.
        
        Task: Write the complete Python code for a new Agent class named `{name}`.
        
        Context:
        - Project: {context[:2000]}
        - Role: {agent_def['role']}
        - Framework: {agent_def['academic_framework']}
        - Responsibility: {agent_def['responsibility']} 
        
        Requirements:
        1. Inherit from `src.agents.base_agent.BaseAgent`.
        2. Imports: `from src.agents.base_agent import BaseAgent`, `from loguru import logger`, etc.
        3. **CRITICAL**: Define a class constant string named `SYSTEM_PROMPT`.
           - This prompt must be "Academic Grade". 
           - It must define the Persona, Objective, Theoretical Constraints, and Workflow.
           - It must explicitly reference the assigned academic framework ({agent_def['academic_framework']}).
           - It should use advanced prompting techniques (e.g. "Think step-by-step", "Verify your assumptions").
        4. Implement the `async def execute(self, *args, **kwargs)` method.
           - It should use `llm_client` (assume it is imported from `src.utils.llm_client`) to perform its task using the `SYSTEM_PROMPT`.
           - The execute method should handle arguments gracefully.
        5. Return ONLY the python code. No markdown.

        Structure:
        ```python
        import json
        from src.agents.base_agent import BaseAgent
        from src.utils.llm_client import llm_client
        from loguru import logger
        
        class {name}(BaseAgent):
            SYSTEM_PROMPT = '''
            [Your high-quality prompt here]
            '''
            
            def __init__(self):
                super().__init__("{name}")
                self.llm = llm_client

            async def execute(self, *args, **kwargs):
                # Implementation using self.llm.generate(self.SYSTEM_PROMPT + ...)
                pass
        ```
        """

        try:
            code = self.llm.generate(prompt, model="gemini")
            code = code.replace("```python", "").replace("```", "").strip()
            
            # Sanity check: Does it look like python?
            if "class " not in code or "def execute" not in code:
                self.log_error(f"Generated code for {name} seems invalid.")
                return False

            # Convert camelCase to snake_case for filename
            filename = re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower() + ".py"
            filepath = os.path.join(self.agents_dir, filename)
            
            # Write file
            with open(filepath, "w") as f:
                f.write(code)
                
            self.log_info(f"Successfully wrote {filepath}")
            return True

        except Exception as e:
            self.log_error(f"Failed to generate code for {name}: {e}")
            return False

    async def _update_registry(self):
        """Runs the registry generation script."""
        self.log_info("Updating agent registry...")
        try:
            registry = []
            # We are in src/, so agents_dir="agents"
            if not os.path.exists(self.agents_dir):
                self.log_error(f"Agents dir not found at {self.agents_dir}")
                return

            for filename in os.listdir(self.agents_dir):
                if filename.endswith(".py") and filename not in ["__init__.py", "base_agent.py"]:
                    # Simple parse
                    with open(os.path.join(self.agents_dir, filename), 'r') as f:
                        content = f.read()
                        match = re.search(r'class (\w+)\(BaseAgent\):', content)
                        if match:
                            cls_name = match.group(1)
                            # Get docstring
                            doc_match = re.search(r'"""(.*?)"""', content, re.DOTALL)
                            desc = doc_match.group(1).strip().split('\n')[0] if doc_match else "No description."
                            
                            registry.append({
                                "name": cls_name,
                                "file_path": f"agents/{filename}",
                                "description": desc,
                                "module": f"agents.{filename[:-3]}"
                            })
            
            with open("agent_registry.json", "w") as f:
                json.dump(registry, f, indent=2)
                
        except Exception as e:
            self.log_error(f"Registry update failed: {e}")