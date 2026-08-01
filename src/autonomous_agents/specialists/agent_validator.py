"""AgentValidatorAgent - Validates all agents in the system work correctly."""

import ast
import importlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from loguru import logger

from ..base_autonomous_agent import BaseAutonomousAgent


class AgentValidatorAgent(BaseAutonomousAgent):
    """
    Validates that all 31+ agents in the system work correctly.

    Checks:
    - Agent files exist and are valid Python
    - Agents inherit from BaseAgent
    - Agents have required methods
    - Agent registry is consistent
    - Agents can be imported without errors
    """

    def __init__(self):
        super().__init__(
            name="AgentValidatorAgent",
            layer="specialists",
            interval_seconds=21600,  # 6 hours
        )
        self.agents_path = Path("src/agents")
        self.registry_path = Path("src/agent_registry.json")

    async def analyze(self) -> dict[str, Any]:
        """Validate all agents."""
        results = {
            "timestamp": datetime.now().isoformat(),
            "total_agents": 0,
            "valid": 0,
            "invalid": [],
            "registry_issues": [],
            "missing_methods": [],
            "import_errors": [],
        }

        # Load registry
        registry = self._load_registry()
        results["registry_count"] = len(registry)

        # Check each agent file
        for py_file in self.agents_path.glob("*.py"):
            if py_file.name.startswith("_"):
                continue

            results["total_agents"] += 1

            validation = self._validate_agent_file(py_file, registry)

            if validation["valid"]:
                results["valid"] += 1
            else:
                results["invalid"].append({"file": str(py_file), "issues": validation["issues"]})

            if validation.get("missing_methods"):
                results["missing_methods"].append(
                    {"file": str(py_file), "methods": validation["missing_methods"]}
                )

            if validation.get("import_error"):
                results["import_errors"].append(
                    {"file": str(py_file), "error": validation["import_error"]}
                )

        # Check registry consistency
        results["registry_issues"] = self._check_registry_consistency(registry)

        # Calculate score
        if results["total_agents"] > 0:
            results["validity_rate"] = (results["valid"] / results["total_agents"]) * 100
        else:
            results["validity_rate"] = 0

        self.metrics["validity_rate"] = results["validity_rate"]
        self.metrics["total_agents"] = results["total_agents"]
        self.metrics["invalid_count"] = len(results["invalid"])

        logger.info(
            f"[{self.name}] Validated {results['total_agents']} agents: "
            f"{results['valid']} valid, {len(results['invalid'])} invalid"
        )

        return results

    async def plan(self, analysis: dict[str, Any]) -> list[dict[str, Any]]:
        """Create plans to fix agent issues."""
        plans = []

        # Invalid agents
        if analysis.get("invalid"):
            plans.append(
                {
                    "type": "fix_invalid_agents",
                    "priority": 8,
                    "description": f"Fix {len(analysis['invalid'])} invalid agents",
                    "agents": analysis["invalid"],
                }
            )

        # Missing methods
        if analysis.get("missing_methods"):
            plans.append(
                {
                    "type": "add_missing_methods",
                    "priority": 7,
                    "description": f"{len(analysis['missing_methods'])} agents missing required methods",
                    "agents": analysis["missing_methods"],
                }
            )

        # Registry issues
        if analysis.get("registry_issues"):
            plans.append(
                {
                    "type": "fix_registry",
                    "priority": 6,
                    "description": f"Fix {len(analysis['registry_issues'])} registry issues",
                    "issues": analysis["registry_issues"],
                }
            )

        # Import errors
        if analysis.get("import_errors"):
            plans.append(
                {
                    "type": "fix_imports",
                    "priority": 9,
                    "description": f"Fix {len(analysis['import_errors'])} import errors",
                    "errors": analysis["import_errors"],
                }
            )

        return plans

    async def execute(self, plan: dict[str, Any]) -> dict[str, Any]:
        """Execute validation plan."""
        plan_type = plan.get("type", "")

        if plan_type == "fix_invalid_agents":
            agents = plan.get("agents", [])

            for agent in agents[:5]:
                logger.warning(f"[{self.name}] Invalid: {agent['file']}")
                for issue in agent.get("issues", []):
                    logger.warning(f"  - {issue}")

            self._save_improvement_suggestion(
                {
                    "category": "agents",
                    "priority": 8,
                    "title": "Fix Invalid Agents",
                    "description": f"{len(agents)} agents have issues",
                    "estimated_impact": 0.2,
                    "details": agents,
                }
            )

            return {
                "status": "logged",
                "message": f"Logged {len(agents)} invalid agents",
                "action": "fix_invalid_agents",
            }

        if plan_type == "fix_imports":
            errors = plan.get("errors", [])

            for error in errors[:5]:
                logger.error(f"[{self.name}] Import error: {error['file']}")
                logger.error(f"  {error['error']}")

            self._save_improvement_suggestion(
                {
                    "category": "agents",
                    "priority": 9,
                    "title": "Fix Agent Import Errors",
                    "description": f"{len(errors)} agents cannot be imported",
                    "estimated_impact": 0.3,
                    "details": errors,
                }
            )

            return {
                "status": "logged",
                "message": f"Logged {len(errors)} import errors",
                "action": "fix_imports",
            }

        if plan_type in ("add_missing_methods", "fix_registry"):
            self._save_improvement_suggestion(
                {
                    "category": "agents",
                    "priority": plan.get("priority", 6),
                    "title": plan.get("description", "Agent issues"),
                    "description": plan.get("description", ""),
                    "estimated_impact": 0.1,
                    "details": plan.get("agents", plan.get("issues", [])),
                }
            )

            return {
                "status": "logged",
                "message": plan.get("description", "Issues logged"),
                "action": plan_type,
            }

        return {"status": "skipped", "message": f"Unknown: {plan_type}", "action": plan_type}

    def _load_registry(self) -> list[dict[str, Any]]:
        """Load agent registry."""
        try:
            if self.registry_path.exists():
                return json.loads(self.registry_path.read_text())
        except Exception as e:
            logger.warning(f"[{self.name}] Failed to load registry: {e}")
        return []

    def _validate_agent_file(self, file_path: Path, registry: list[dict]) -> dict[str, Any]:
        """Validate a single agent file."""
        result = {"valid": True, "issues": [], "missing_methods": [], "import_error": None}

        try:
            content = file_path.read_text()
            tree = ast.parse(content)

            # Find agent classes
            agent_classes = []
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # Check if it inherits from BaseAgent or similar
                    bases = [
                        ast.unparse(base) if hasattr(ast, "unparse") else "base"
                        for base in node.bases
                    ]

                    is_agent = any("Agent" in b or "Base" in b for b in bases)

                    if is_agent or "Agent" in node.name:
                        agent_classes.append(node)

            if not agent_classes:
                result["issues"].append("No agent class found")
                result["valid"] = False

            # Check required methods
            for agent_class in agent_classes:
                methods = [
                    node.name
                    for node in ast.walk(agent_class)
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                ]

                required = ["execute", "__init__"]
                for req in required:
                    if req not in methods:
                        result["missing_methods"].append(req)

            if result["missing_methods"]:
                result["issues"].append(f"Missing methods: {', '.join(result['missing_methods'])}")

            # Try to import
            try:
                module_name = f"src.agents.{file_path.stem}"
                importlib.import_module(module_name)
            except Exception as e:
                result["import_error"] = str(e)[:200]
                result["issues"].append(f"Import error: {str(e)[:100]}")
                result["valid"] = False

        except SyntaxError as e:
            result["valid"] = False
            result["issues"].append(f"Syntax error: {e}")
        except Exception as e:
            result["valid"] = False
            result["issues"].append(f"Error: {str(e)[:100]}")

        return result

    def _check_registry_consistency(self, registry: list[dict]) -> list[dict[str, Any]]:
        """Check if registry matches actual files."""
        issues = []

        # Check all registry entries point to existing files
        for entry in registry:
            file_path = Path("src") / entry.get("file_path", "")
            if not file_path.exists():
                issues.append(
                    {
                        "type": "missing_file",
                        "agent": entry.get("name", "unknown"),
                        "path": str(file_path),
                    }
                )

        # Check for orphaned agent files (not in registry)
        registered_files = {entry.get("file_path", "") for entry in registry}

        for py_file in self.agents_path.glob("*.py"):
            if py_file.name.startswith("_"):
                continue

            relative_path = f"agents/{py_file.name}"
            if relative_path not in registered_files:
                issues.append(
                    {
                        "type": "orphaned_file",
                        "path": str(py_file),
                        "message": "File not in registry",
                    }
                )

        return issues


async def run_agent_validator():
    """Run the agent validator."""
    agent = AgentValidatorAgent()
    return await agent.run_cycle()
