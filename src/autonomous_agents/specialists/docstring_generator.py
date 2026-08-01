"""DocstringGeneratorAgent - Auto-generates docstrings for functions and classes."""

import ast
import builtins
import contextlib
from datetime import datetime
from pathlib import Path
from typing import Any

from loguru import logger

from ..base_autonomous_agent import BaseAutonomousAgent


class DocstringGeneratorAgent(BaseAutonomousAgent):
    """
    Automatically generates docstrings for functions and classes.

    Uses code analysis to understand function purpose and generate
    appropriate Google-style docstrings.

    Features:
    - Identifies functions/classes missing docstrings
    - Generates docstrings based on function signature
    - Follows Google docstring style
    - Can auto-insert docstrings
    """

    def __init__(self):
        super().__init__(
            name="DocstringGeneratorAgent",
            layer="specialists",
            interval_seconds=0,  # On-demand
        )
        self.src_path = Path("src")
        self.docstrings_added = 0

    async def analyze(self) -> dict[str, Any]:
        """Find all functions/classes missing docstrings."""
        results = {
            "timestamp": datetime.now().isoformat(),
            "missing": [],
            "total_items": 0,
            "with_docstrings": 0,
        }

        for py_file in self.src_path.rglob("*.py"):
            try:
                content = py_file.read_text()
                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        results["total_items"] += 1

                        docstring = ast.get_docstring(node)
                        if docstring:
                            results["with_docstrings"] += 1
                        # Skip private/dunder methods for now
                        elif not node.name.startswith("_"):
                            results["missing"].append(
                                {
                                    "file": str(py_file),
                                    "name": node.name,
                                    "type": "class"
                                    if isinstance(node, ast.ClassDef)
                                    else "function",
                                    "line": node.lineno,
                                    "signature": self._get_signature(node),
                                    "suggested_docstring": self._generate_docstring(node),
                                }
                            )
            except Exception as e:
                logger.debug(f"[{self.name}] Error parsing {py_file}: {e}")

        # Calculate coverage
        if results["total_items"] > 0:
            results["coverage"] = (results["with_docstrings"] / results["total_items"]) * 100
        else:
            results["coverage"] = 0

        self.metrics["coverage"] = results["coverage"]
        self.metrics["missing_count"] = len(results["missing"])

        logger.info(
            f"[{self.name}] Docstring coverage: {results['coverage']:.1f}% "
            f"({len(results['missing'])} missing)"
        )

        return results

    async def plan(self, analysis: dict[str, Any]) -> list[dict[str, Any]]:
        """Create plans to add docstrings."""
        plans = []

        missing = analysis.get("missing", [])

        if missing:
            # Group by file
            by_file: dict[str, list[dict]] = {}
            for item in missing:
                file_path = item["file"]
                if file_path not in by_file:
                    by_file[file_path] = []
                by_file[file_path].append(item)

            # Create plan for each file with missing docstrings
            for file_path, items in list(by_file.items())[:10]:  # Limit to 10 files
                plans.append(
                    {
                        "type": "add_docstrings",
                        "priority": 5,
                        "file": file_path,
                        "items": items,
                        "description": f"Add {len(items)} docstrings to {Path(file_path).name}",
                    }
                )

        return plans

    async def execute(self, plan: dict[str, Any]) -> dict[str, Any]:
        """Execute docstring addition plan."""
        plan_type = plan.get("type", "")

        if plan_type == "add_docstrings":
            items = plan.get("items", [])
            file_path = plan.get("file", "")

            # For now, just log suggestions
            # Full auto-insertion would require more careful handling
            for item in items[:5]:
                logger.info(
                    f"[{self.name}] Missing docstring: {item['name']} in {Path(file_path).name}"
                )

            self._save_improvement_suggestion(
                {
                    "category": "documentation",
                    "priority": 5,
                    "title": f"Add docstrings to {Path(file_path).name}",
                    "description": f"{len(items)} functions/classes need docstrings",
                    "estimated_impact": 0.05,
                    "file": file_path,
                    "items": items,
                }
            )

            return {
                "status": "logged",
                "message": f"Logged {len(items)} missing docstrings for {Path(file_path).name}",
                "action": "add_docstrings",
            }

        return {"status": "skipped", "message": f"Unknown: {plan_type}", "action": plan_type}

    def _get_signature(self, node: ast.AST) -> str:
        """Extract function/class signature."""
        if isinstance(node, ast.ClassDef):
            bases = ", ".join(
                ast.unparse(base) if hasattr(ast, "unparse") else "base" for base in node.bases
            )
            return f"class {node.name}({bases})"

        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = []
            for arg in node.args.args:
                arg_str = arg.arg
                if arg.annotation:
                    with contextlib.suppress(builtins.BaseException):
                        arg_str += f": {ast.unparse(arg.annotation)}"
                args.append(arg_str)

            prefix = "async " if isinstance(node, ast.AsyncFunctionDef) else ""
            return f"{prefix}def {node.name}({', '.join(args)})"

        return ""

    def _generate_docstring(self, node: ast.AST) -> str:
        """Generate a docstring suggestion for a function/class."""
        if isinstance(node, ast.ClassDef):
            return f'"""{node.name} class.\n\nTODO: Add description.\n"""'

        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Basic docstring
            lines = [f'"""{self._humanize_name(node.name)}.']

            # Add args section if there are parameters
            params = [arg.arg for arg in node.args.args if arg.arg != "self"]
            if params:
                lines.append("")
                lines.append("Args:")
                for param in params:
                    lines.append(f"    {param}: TODO")

            # Add returns section if there's a return annotation
            if node.returns:
                lines.append("")
                lines.append("Returns:")
                lines.append("    TODO")

            lines.append('"""')
            return "\n".join(lines)

        return '"""TODO: Add docstring."""'

    def _humanize_name(self, name: str) -> str:
        """Convert function name to human-readable description."""
        # Convert snake_case to sentence
        words = name.replace("_", " ").split()
        if words:
            words[0] = words[0].capitalize()
        return " ".join(words)


async def run_docstring_generator():
    """Run the docstring generator."""
    agent = DocstringGeneratorAgent()
    return await agent.run_cycle()
