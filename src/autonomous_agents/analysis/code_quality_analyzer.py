"""CodeQualityAnalyzer - Deep analysis of code quality and complexity."""

import ast
from datetime import datetime
from pathlib import Path
from typing import Any

from loguru import logger

from ..base_autonomous_agent import BaseAutonomousAgent


class CodeQualityAnalyzer(BaseAutonomousAgent):
    """
    Performs deep analysis of code quality beyond linting.

    Analyzes:
    - Cyclomatic complexity
    - Code duplication patterns
    - Function/class size metrics
    - Naming conventions
    - Docstring coverage
    - Quality trends over time

    Interval: 1 hour (3600 seconds)
    """

    def __init__(self):
        super().__init__(name="CodeQualityAnalyzer", layer="analysis", interval_seconds=3600)
        self.src_path = Path("src")
        self.quality_history: list[dict[str, Any]] = []

    async def analyze(self) -> dict[str, Any]:
        """Perform deep code quality analysis."""
        results = {
            "timestamp": datetime.now().isoformat(),
            "file_metrics": self._analyze_files(),
            "complexity": self._analyze_complexity(),
            "naming": self._analyze_naming(),
            "docstrings": self._analyze_docstrings(),
        }

        # Calculate overall quality score
        scores = [
            results["complexity"].get("score", 50),
            results["naming"].get("score", 50),
            results["docstrings"].get("score", 50),
        ]
        results["quality_score"] = sum(scores) / len(scores)

        # Update metrics
        self.metrics["quality_score"] = results["quality_score"]
        self.metrics["complexity_score"] = results["complexity"].get("score", 0)
        self.metrics["docstring_coverage"] = results["docstrings"].get("coverage", 0)

        logger.info(f"[{self.name}] Quality Score: {results['quality_score']:.1f}/100")

        return results

    async def plan(self, analysis: dict[str, Any]) -> list[dict[str, Any]]:
        """Create improvement plans based on analysis."""
        plans = []

        # Complex functions
        complex_funcs = analysis.get("complexity", {}).get("complex_functions", [])
        if complex_funcs:
            plans.append(
                {
                    "type": "refactor_complex",
                    "priority": 6,
                    "description": f"Found {len(complex_funcs)} complex functions to refactor",
                    "functions": complex_funcs[:10],
                }
            )

        # Missing docstrings
        missing_docs = analysis.get("docstrings", {}).get("missing", [])
        if missing_docs:
            plans.append(
                {
                    "type": "add_docstrings",
                    "priority": 5,
                    "description": f"Found {len(missing_docs)} items missing docstrings",
                    "items": missing_docs[:20],
                }
            )

        # Large files
        large_files = [
            f for f in analysis.get("file_metrics", {}).get("files", []) if f.get("lines", 0) > 500
        ]
        if large_files:
            plans.append(
                {
                    "type": "split_large_files",
                    "priority": 4,
                    "description": f"Found {len(large_files)} large files (>500 lines)",
                    "files": [f["path"] for f in large_files],
                }
            )

        # Save quality snapshot
        self._save_quality_snapshot(analysis)

        return plans

    async def execute(self, plan: dict[str, Any]) -> dict[str, Any]:
        """Execute analysis plan (mostly logging recommendations)."""
        plan_type = plan.get("type", "")

        if plan_type == "refactor_complex":
            # Log recommendations
            funcs = plan.get("functions", [])
            logger.info(f"[{self.name}] Complex functions to refactor:")
            for func in funcs[:5]:
                logger.info(
                    f"  - {func.get('name', 'unknown')} (complexity: {func.get('complexity', 0)})"
                )

            self._save_improvement_suggestion(
                {
                    "category": "complexity",
                    "priority": 6,
                    "title": "Refactor Complex Functions",
                    "description": f"{len(funcs)} functions have high complexity",
                    "estimated_impact": 0.15,
                    "details": funcs,
                }
            )

            return {
                "status": "logged",
                "message": f"Logged {len(funcs)} complex functions for refactoring",
                "action": "refactor_complex",
            }

        if plan_type == "add_docstrings":
            items = plan.get("items", [])

            self._save_improvement_suggestion(
                {
                    "category": "documentation",
                    "priority": 5,
                    "title": "Add Missing Docstrings",
                    "description": f"{len(items)} functions/classes missing docstrings",
                    "estimated_impact": 0.1,
                    "details": items,
                }
            )

            return {
                "status": "logged",
                "message": f"Logged {len(items)} items needing docstrings",
                "action": "add_docstrings",
            }

        if plan_type == "split_large_files":
            files = plan.get("files", [])

            self._save_improvement_suggestion(
                {
                    "category": "architecture",
                    "priority": 4,
                    "title": "Split Large Files",
                    "description": f"{len(files)} files exceed 500 lines",
                    "estimated_impact": 0.1,
                    "details": files,
                }
            )

            return {
                "status": "logged",
                "message": f"Logged {len(files)} large files to split",
                "action": "split_large_files",
            }

        return {
            "status": "skipped",
            "message": f"Unknown plan type: {plan_type}",
            "action": plan_type,
        }

    def _analyze_files(self) -> dict[str, Any]:
        """Analyze file-level metrics."""
        result = {"total_files": 0, "total_lines": 0, "avg_file_size": 0, "files": []}

        try:
            for py_file in self.src_path.rglob("*.py"):
                try:
                    lines = len(py_file.read_text().splitlines())
                    result["files"].append({"path": str(py_file), "lines": lines})
                    result["total_files"] += 1
                    result["total_lines"] += lines
                except:
                    pass

            if result["total_files"] > 0:
                result["avg_file_size"] = result["total_lines"] / result["total_files"]

            # Sort by size (largest first)
            result["files"].sort(key=lambda x: x.get("lines", 0), reverse=True)
            result["files"] = result["files"][:20]  # Keep top 20

        except Exception as e:
            result["error"] = str(e)

        return result

    def _analyze_complexity(self) -> dict[str, Any]:
        """Analyze cyclomatic complexity of functions."""
        result = {"score": 100, "complex_functions": [], "avg_complexity": 0}

        complexities = []

        try:
            for py_file in self.src_path.rglob("*.py"):
                try:
                    tree = ast.parse(py_file.read_text())

                    for node in ast.walk(tree):
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            complexity = self._calculate_complexity(node)
                            complexities.append(complexity)

                            if complexity > 10:  # High complexity threshold
                                result["complex_functions"].append(
                                    {
                                        "name": f"{py_file.name}:{node.name}",
                                        "complexity": complexity,
                                        "line": node.lineno,
                                    }
                                )
                except:
                    pass

            if complexities:
                result["avg_complexity"] = sum(complexities) / len(complexities)
                # Score: 100 if avg<=5, decreases as complexity increases
                result["score"] = max(0, 100 - (result["avg_complexity"] - 5) * 10)

            result["complex_functions"].sort(key=lambda x: x["complexity"], reverse=True)
            result["complex_functions"] = result["complex_functions"][:20]

        except Exception as e:
            result["error"] = str(e)

        return result

    def _calculate_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity of a function."""
        complexity = 1

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            elif isinstance(child, (ast.And, ast.Or)):
                complexity += 1

        return complexity

    def _analyze_naming(self) -> dict[str, Any]:
        """Analyze naming conventions."""
        result = {"score": 100, "issues": []}

        try:
            for py_file in self.src_path.rglob("*.py"):
                try:
                    tree = ast.parse(py_file.read_text())

                    for node in ast.walk(tree):
                        # Check class names (should be PascalCase)
                        if isinstance(node, ast.ClassDef):
                            if not node.name[0].isupper():
                                result["issues"].append(
                                    {
                                        "type": "class_naming",
                                        "name": node.name,
                                        "file": str(py_file),
                                    }
                                )

                        # Check function names (should be snake_case)
                        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            if (
                                not node.name.startswith("_")
                                and any(c.isupper() for c in node.name)
                                and node.name
                                not in [
                                    "setUp",
                                    "tearDown",
                                    "setUpClass",
                                    "tearDownClass",
                                ]
                            ):
                                result["issues"].append(
                                    {
                                        "type": "function_naming",
                                        "name": node.name,
                                        "file": str(py_file),
                                    }
                                )
                except:
                    pass

            # Score based on issues
            result["score"] = max(0, 100 - len(result["issues"]) * 2)
            result["issues"] = result["issues"][:20]

        except Exception as e:
            result["error"] = str(e)

        return result

    def _analyze_docstrings(self) -> dict[str, Any]:
        """Analyze docstring coverage."""
        result = {"score": 0, "coverage": 0, "total": 0, "with_docs": 0, "missing": []}

        try:
            for py_file in self.src_path.rglob("*.py"):
                try:
                    tree = ast.parse(py_file.read_text())

                    for node in ast.walk(tree):
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                            result["total"] += 1

                            docstring = ast.get_docstring(node)
                            if docstring:
                                result["with_docs"] += 1
                            # Skip private/dunder methods
                            elif not node.name.startswith("_"):
                                result["missing"].append(
                                    {
                                        "type": "class"
                                        if isinstance(node, ast.ClassDef)
                                        else "function",
                                        "name": node.name,
                                        "file": str(py_file),
                                        "line": node.lineno,
                                    }
                                )
                except:
                    pass

            if result["total"] > 0:
                result["coverage"] = (result["with_docs"] / result["total"]) * 100
                result["score"] = result["coverage"]

            result["missing"] = result["missing"][:30]

        except Exception as e:
            result["error"] = str(e)

        return result

    def _save_quality_snapshot(self, analysis: dict[str, Any]):
        """Save quality metrics snapshot for tracking over time."""
        snapshot = {
            "timestamp": analysis["timestamp"],
            "quality_score": analysis.get("quality_score", 0),
            "complexity_score": analysis.get("complexity", {}).get("score", 0),
            "naming_score": analysis.get("naming", {}).get("score", 0),
            "docstring_coverage": analysis.get("docstrings", {}).get("coverage", 0),
            "total_files": analysis.get("file_metrics", {}).get("total_files", 0),
            "total_lines": analysis.get("file_metrics", {}).get("total_lines", 0),
        }

        # Save to snapshot file
        snapshots_file = self.data_dir / "quality_snapshots.jsonl"
        try:
            import json

            with open(snapshots_file, "a") as f:
                f.write(json.dumps(snapshot) + "\n")
        except Exception as e:
            logger.warning(f"[{self.name}] Failed to save snapshot: {e}")
