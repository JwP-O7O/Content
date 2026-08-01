"""DocumentationAnalyzer - Analyzes docstring coverage and quality."""

import ast
import os
from typing import Any

from ..base_autonomous_agent import BaseAutonomousAgent


class DocumentationAnalyzer(BaseAutonomousAgent):
    """
    Analyzes Python files for docstring coverage.
    Checks modules, classes, and functions.
    """

    def __init__(self):
        super().__init__(
            name="DocumentationAnalyzer",
            layer="analysis",
            interval_seconds=3600,  # Every 1 hour
        )

    async def analyze(self) -> dict[str, Any]:
        """Run documentation analysis."""
        self.log_info("Running documentation analysis...")
        results = {
            "total_items": 0,
            "missing_docstrings": 0,
            "files_analyzed": 0,
            "missing_items": [],
        }

        try:
            for root, _, files in os.walk("src"):
                for file in files:
                    if file.endswith(".py"):
                        path = os.path.join(root, file)
                        self._analyze_file(path, results)

            if results["total_items"] > 0:
                coverage = (
                    (results["total_items"] - results["missing_docstrings"])
                    / results["total_items"]
                ) * 100
            else:
                coverage = 100.0

            results["documentation_score"] = coverage
            self.metrics["documentation_score"] = coverage

        except Exception as e:
            results["error"] = str(e)
            self.log_error(f"Documentation analysis failed: {e}")

        return results

    def _analyze_file(self, path: str, results: dict[str, Any]):
        """Analyze a single file for docstrings."""
        try:
            with open(path, encoding="utf-8") as f:
                tree = ast.parse(f.read())

            results["files_analyzed"] += 1

            # check module docstring
            results["total_items"] += 1
            if not ast.get_docstring(tree):
                results["missing_docstrings"] += 1
                results["missing_items"].append(
                    {"file": path, "type": "module", "name": "<module>"}
                )

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    # Skip private items (starting with _)
                    if node.name.startswith("_") and not node.name.startswith("__init__"):
                        continue

                    results["total_items"] += 1
                    if not ast.get_docstring(node):
                        results["missing_docstrings"] += 1
                        results["missing_items"].append(
                            {
                                "file": path,
                                "type": type(node).__name__,
                                "name": node.name,
                                "lineno": node.lineno,
                            }
                        )

        except Exception as e:
            self.log_warning(f"Failed to parse {path}: {e}")

    async def plan(self, analysis: dict[str, Any]) -> list[dict[str, Any]]:
        """Plan docstring generation for missing items."""
        plans = []

        missing_items = analysis.get("missing_items", [])

        # Group by file
        files_needing_docs = {}
        for item in missing_items:
            path = item["file"]
            if path not in files_needing_docs:
                files_needing_docs[path] = []
            files_needing_docs[path].append(item)

        # Create plans for top 10 files
        for path, items in list(files_needing_docs.items())[:10]:
            plans.append(
                {
                    "type": "generate_docstrings",
                    "priority": 5,
                    "file": path,
                    "missing_count": len(items),
                    "items": [i["name"] for i in items],
                    "description": f"Generate docstrings for {path} ({len(items)} missing)",
                }
            )

        return plans

    async def execute(self, plan: dict[str, Any]) -> dict[str, Any]:
        """
        Execution is handled by DocstringGeneratorAgent.
        """
        return {
            "status": "planned",
            "message": f"Docstring generation planned for {plan['file']}",
            "plan": plan,
        }
