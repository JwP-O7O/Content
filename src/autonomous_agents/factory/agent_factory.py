"""AgentFactory - Creates and manages specialized agents dynamically."""

import importlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from loguru import logger

from ..base_autonomous_agent import BaseAutonomousAgent


class AgentFactory:
    """
    Factory for creating and managing specialized autonomous agents.

    Capabilities:
    - Create agents from templates
    - Register agents for reuse
    - Track agent performance
    - Generate new agents based on needs
    """

    def __init__(self):
        self.agents_dir = Path("src/autonomous_agents")
        self.registry_file = self.agents_dir / "agent_registry.json"
        self.templates_dir = self.agents_dir / "factory/templates"
        self.registry: dict[str, dict[str, Any]] = {}
        self._load_registry()

        logger.info(f"AgentFactory initialized with {len(self.registry)} registered agents")

    def _load_registry(self):
        """Load agent registry from file."""
        try:
            if self.registry_file.exists():
                with open(self.registry_file) as f:
                    self.registry = json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load registry: {e}")
            self.registry = {}

    def _save_registry(self):
        """Save agent registry to file."""
        try:
            with open(self.registry_file, "w") as f:
                json.dump(self.registry, f, indent=2, default=str)
        except Exception as e:
            logger.warning(f"Failed to save registry: {e}")

    def register_agent(
        self,
        name: str,
        module_path: str,
        layer: str,
        description: str,
        capabilities: Optional[list[str]] = None,
    ):
        """
        Register an agent in the factory registry.

        Args:
            name: Agent class name
            module_path: Python module path (e.g., "specialists.docstring_generator")
            layer: Which layer (monitoring, analysis, execution, etc.)
            description: What the agent does
            capabilities: List of agent capabilities
        """
        self.registry[name] = {
            "name": name,
            "module_path": module_path,
            "layer": layer,
            "description": description,
            "capabilities": capabilities or [],
            "registered_at": datetime.now().isoformat(),
            "usage_count": 0,
            "last_used": None,
        }
        self._save_registry()
        logger.info(f"Registered agent: {name}")

    def get_agent(self, name: str) -> Optional[BaseAutonomousAgent]:
        """
        Get an agent instance by name.

        Args:
            name: Agent name

        Returns:
            Agent instance or None
        """
        if name not in self.registry:
            logger.warning(f"Agent not found: {name}")
            return None

        try:
            info = self.registry[name]
            module_path = f"src.autonomous_agents.{info['module_path']}"

            module = importlib.import_module(module_path)
            agent_class = getattr(module, name)

            # Update usage stats
            self.registry[name]["usage_count"] += 1
            self.registry[name]["last_used"] = datetime.now().isoformat()
            self._save_registry()

            return agent_class()

        except Exception as e:
            logger.error(f"Failed to get agent {name}: {e}")
            return None

    def list_agents(self, layer: Optional[str] = None) -> list[dict[str, Any]]:
        """
        List all registered agents.

        Args:
            layer: Filter by layer (optional)

        Returns:
            List of agent info dictionaries
        """
        agents = list(self.registry.values())

        if layer:
            agents = [a for a in agents if a.get("layer") == layer]

        return agents

    def find_agent_for_task(self, task_type: str) -> Optional[str]:
        """
        Find the best agent for a specific task.

        Args:
            task_type: Type of task (e.g., "fix_docstrings", "run_tests")

        Returns:
            Agent name or None
        """
        task_mappings = {
            "fix_linting": "CodeFixerAgent",
            "fix_docstrings": "DocstringGeneratorAgent",
            "add_types": "TypeHintAgent",
            "generate_tests": "TestGeneratorAgent",
            "validate_agents": "AgentValidatorAgent",
            "analyze_quality": "CodeQualityAnalyzer",
            "check_security": "SecurityAuditor",
            "update_deps": "DependencyScanner",
        }

        return task_mappings.get(task_type)

    def create_agent_from_template(
        self, name: str, layer: str, description: str, template: str = "base"
    ) -> bool:
        """
        Create a new agent from a template.

        Args:
            name: New agent name
            layer: Agent layer
            description: What it does
            template: Template to use

        Returns:
            True if successful
        """
        from .generator import AgentGenerator

        generator = AgentGenerator()
        return generator.generate_agent(
            name=name, layer=layer, description=description, template=template
        )

    def get_available_agents_for_issue(self, issue_type: str) -> list[str]:
        """
        Get list of agents that can handle a specific issue type.

        Args:
            issue_type: Type of issue (e.g., "linting", "complexity")

        Returns:
            List of agent names
        """
        issue_handlers = {
            "linting": ["CodeFixerAgent"],
            "complexity": ["ComplexityRefactorAgent", "CodeQualityAnalyzer"],
            "docstrings": ["DocstringGeneratorAgent"],
            "types": ["TypeHintAgent"],
            "tests": ["TestGeneratorAgent", "IntegrationTestAgent"],
            "security": ["SecurityAuditor"],
            "performance": ["PerformanceMonitor", "QueryOptimizerAgent"],
            "architecture": ["ArchitectureAnalyzer", "AgentValidatorAgent"],
        }

        return issue_handlers.get(issue_type, [])

    def run_agent(self, name: str) -> dict[str, Any]:
        """
        Run an agent and return results.

        Args:
            name: Agent name

        Returns:
            Agent run results
        """
        import asyncio

        agent = self.get_agent(name)
        if not agent:
            return {"status": "error", "message": f"Agent not found: {name}"}

        try:
            return asyncio.run(agent.run_cycle())
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get_stats(self) -> dict[str, Any]:
        """Get factory statistics."""
        return {
            "total_agents": len(self.registry),
            "by_layer": self._count_by_layer(),
            "most_used": self._get_most_used(),
            "recently_used": self._get_recently_used(),
        }

    def _count_by_layer(self) -> dict[str, int]:
        """Count agents by layer."""
        counts = {}
        for agent in self.registry.values():
            layer = agent.get("layer", "unknown")
            counts[layer] = counts.get(layer, 0) + 1
        return counts

    def _get_most_used(self, limit: int = 5) -> list[dict[str, Any]]:
        """Get most used agents."""
        agents = sorted(self.registry.values(), key=lambda x: x.get("usage_count", 0), reverse=True)
        return agents[:limit]

    def _get_recently_used(self, limit: int = 5) -> list[dict[str, Any]]:
        """Get recently used agents."""
        agents = [a for a in self.registry.values() if a.get("last_used")]
        agents.sort(key=lambda x: x.get("last_used", ""), reverse=True)
        return agents[:limit]


# Singleton instance
_factory_instance = None


def get_factory() -> AgentFactory:
    """Get the singleton AgentFactory instance."""
    global _factory_instance
    if _factory_instance is None:
        _factory_instance = AgentFactory()
    return _factory_instance
