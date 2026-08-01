"""TypeHintAgent - Automatically adds type hints to functions."""

import ast
from datetime import datetime
from pathlib import Path
from typing import Any

from loguru import logger

from ..base_autonomous_agent import BaseAutonomousAgent


class TypeHintAgent(BaseAutonomousAgent):
    """
    Automatically adds type hints to untyped functions.

    Features:
    - Identifies functions without type hints
    - Infers types from usage patterns
    - Generates type hint suggestions
    - Tracks type coverage over time
    """

    def __init__(self):
        super().__init__(
            name="TypeHintAgent",
            layer="specialists",
            interval_seconds=0,  # On-demand
        )
        self.src_path = Path("src")

    async def analyze(self) -> dict[str, Any]:
        """Find functions without type hints."""
        results = {
            "timestamp": datetime.now().isoformat(),
            "untyped_functions": [],
            "total_functions": 0,
            "typed_functions": 0,
            "partially_typed": 0,
        }

        for py_file in self.src_path.rglob("*.py"):
            try:
                content = py_file.read_text()
                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        results["total_functions"] += 1

                        # Check type hints
                        has_return_hint = node.returns is not None
                        args_with_hints = sum(
                            1
                            for arg in node.args.args
                            if arg.annotation is not None and arg.arg != "self"
                        )
                        total_args = len([a for a in node.args.args if a.arg != "self"])

                        if has_return_hint and (total_args in (0, args_with_hints)):
                            results["typed_functions"] += 1
                        elif has_return_hint or args_with_hints > 0:
                            results["partially_typed"] += 1
                        # Skip private/dunder
                        elif not node.name.startswith("_"):
                            results["untyped_functions"].append(
                                {
                                    "file": str(py_file),
                                    "name": node.name,
                                    "line": node.lineno,
                                    "args": [a.arg for a in node.args.args if a.arg != "self"],
                                    "suggested_hints": self._suggest_types(node),
                                }
                            )
            except Exception as e:
                logger.debug(f"[{self.name}] Error parsing {py_file}: {e}")

        # Calculate coverage
        if results["total_functions"] > 0:
            results["type_coverage"] = (
                results["typed_functions"] / results["total_functions"]
            ) * 100
        else:
            results["type_coverage"] = 0

        self.metrics["type_coverage"] = results["type_coverage"]
        self.metrics["untyped_count"] = len(results["untyped_functions"])

        logger.info(
            f"[{self.name}] Type coverage: {results['type_coverage']:.1f}% "
            f"({len(results['untyped_functions'])} untyped functions)"
        )

        return results

    async def plan(self, analysis: dict[str, Any]) -> list[dict[str, Any]]:
        """Create plans to add type hints."""
        plans = []

        untyped = analysis.get("untyped_functions", [])

        # Group by file
        by_file: dict[str, list] = {}
        for func in untyped:
            file_path = func["file"]
            if file_path not in by_file:
                by_file[file_path] = []
            by_file[file_path].append(func)

        # Create plans for files with most untyped functions
        for file_path, funcs in sorted(by_file.items(), key=lambda x: -len(x[1]))[:10]:
            plans.append(
                {
                    "type": "add_type_hints",
                    "priority": 5,
                    "file": file_path,
                    "functions": funcs,
                    "description": f"Add type hints to {len(funcs)} functions in {Path(file_path).name}",
                }
            )

        return plans

    async def execute(self, plan: dict[str, Any]) -> dict[str, Any]:
        """Log type hint suggestions."""
        plan_type = plan.get("type", "")

        if plan_type == "add_type_hints":
            funcs = plan.get("functions", [])
            file_path = plan.get("file", "")

            # Log suggestions
            for func in funcs[:3]:
                logger.info(
                    f"[{self.name}] {func['name']}: "
                    f"suggested -> {func.get('suggested_hints', {}).get('return', 'None')}"
                )

            self._save_improvement_suggestion(
                {
                    "category": "type_hints",
                    "priority": 5,
                    "title": f"Add type hints to {Path(file_path).name}",
                    "description": f"{len(funcs)} functions need type hints",
                    "estimated_impact": 0.05,
                    "file": file_path,
                    "functions": funcs,
                }
            )

            return {
                "status": "logged",
                "message": f"Logged {len(funcs)} type hint suggestions",
                "action": "add_type_hints",
            }

        return {"status": "skipped", "message": f"Unknown: {plan_type}", "action": plan_type}

    def _suggest_types(self, node: ast.AST) -> dict[str, str]:
        """Suggest types based on function analysis."""
        suggestions = {"return": "None", "args": {}}

        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return suggestions

        # Analyze function name for hints
        name = node.name.lower()

        # Common patterns
        if name.startswith(("is_", "has_", "can_")):
            suggestions["return"] = "bool"
        elif name.startswith(("get_", "fetch_")):
            suggestions["return"] = "Optional[Any]"
        elif name.startswith(("count_", "num_")):
            suggestions["return"] = "int"
        elif name.startswith(("list_", "find_all")):
            suggestions["return"] = "List[Any]"
        elif "async" in str(type(node).__name__).lower():
            suggestions["return"] = "Coroutine"

        # Analyze args
        for arg in node.args.args:
            if arg.arg == "self":
                continue

            arg_name = arg.arg.lower()
            if "id" in arg_name:
                suggestions["args"][arg.arg] = "int"
            elif "name" in arg_name or "text" in arg_name or "message" in arg_name:
                suggestions["args"][arg.arg] = "str"
            elif "count" in arg_name or "num" in arg_name or "limit" in arg_name:
                suggestions["args"][arg.arg] = "int"
            elif "is_" in arg_name or "has_" in arg_name or "enable" in arg_name:
                suggestions["args"][arg.arg] = "bool"
            elif "list" in arg_name or "items" in arg_name:
                suggestions["args"][arg.arg] = "List[Any]"
            elif "dict" in arg_name or "data" in arg_name or "config" in arg_name:
                suggestions["args"][arg.arg] = "Dict[str, Any]"
            elif "path" in arg_name or "file" in arg_name:
                suggestions["args"][arg.arg] = "Path | str"

        return suggestions
