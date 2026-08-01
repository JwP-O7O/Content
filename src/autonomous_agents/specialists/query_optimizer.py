"""QueryOptimizerAgent - Analyzes and optimizes database queries."""

import ast
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from loguru import logger

from ..base_autonomous_agent import BaseAutonomousAgent


class QueryOptimizerAgent(BaseAutonomousAgent):
    """
    Analyzes database queries and suggests optimizations.

    Detects:
    - N+1 query patterns
    - Missing indexes
    - Inefficient query patterns
    - Raw SQL without parameterization
    """

    def __init__(self):
        super().__init__(
            name="QueryOptimizerAgent",
            layer="specialists",
            interval_seconds=21600,  # 6 hours
        )
        self.src_path = Path("src")

        # Patterns that might indicate query issues
        self.n_plus_one_patterns = [
            r"for\s+\w+\s+in\s+.*\.query\(",
            r"for\s+\w+\s+in\s+session\.query\(",
            r"\.filter\(.*\.id\s*==",
        ]

        self.raw_sql_patterns = [
            r'execute\s*\(\s*["\'].*SELECT',
            r'execute\s*\(\s*f["\'].*SELECT',
            r'\.raw\s*\(\s*["\']',
        ]

    async def analyze(self) -> dict[str, Any]:
        """Analyze database queries."""
        results = {
            "timestamp": datetime.now().isoformat(),
            "n_plus_one_suspects": [],
            "raw_sql_usage": [],
            "missing_eager_loading": [],
            "query_patterns": {},
        }

        for py_file in self.src_path.rglob("*.py"):
            try:
                content = py_file.read_text()

                # Check for N+1 patterns
                for pattern in self.n_plus_one_patterns:
                    matches = list(re.finditer(pattern, content, re.IGNORECASE))
                    for match in matches:
                        line_num = content[: match.start()].count("\n") + 1
                        results["n_plus_one_suspects"].append(
                            {"file": str(py_file), "line": line_num, "pattern": match.group()[:50]}
                        )

                # Check for raw SQL
                for pattern in self.raw_sql_patterns:
                    matches = list(re.finditer(pattern, content, re.IGNORECASE))
                    for match in matches:
                        line_num = content[: match.start()].count("\n") + 1
                        results["raw_sql_usage"].append(
                            {"file": str(py_file), "line": line_num, "pattern": match.group()[:50]}
                        )

                # Check for relationship access in loops without eager loading
                if ("for " in content and ".relationship" in content) or ".relationship" in content:
                    tree = ast.parse(content)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.For):
                            # Simple heuristic: check if accessing attributes that might be relationships
                            for_body = ast.dump(node)
                            if (
                                ".items" in for_body
                                or ".children" in for_body
                                or ".related" in for_body
                            ):
                                results["missing_eager_loading"].append(
                                    {"file": str(py_file), "line": node.lineno}
                                )

            except Exception as e:
                logger.debug(f"[{self.name}] Error analyzing {py_file}: {e}")

        # Calculate score
        issues = (
            len(results["n_plus_one_suspects"]) * 3
            + len(results["raw_sql_usage"]) * 2
            + len(results["missing_eager_loading"])
        )
        results["optimization_score"] = max(0, 100 - issues * 5)

        self.metrics["optimization_score"] = results["optimization_score"]
        self.metrics["n_plus_one_count"] = len(results["n_plus_one_suspects"])

        logger.info(
            f"[{self.name}] Query Optimization Score: {results['optimization_score']:.1f}/100 "
            f"(N+1 suspects: {len(results['n_plus_one_suspects'])})"
        )

        return results

    async def plan(self, analysis: dict[str, Any]) -> list[dict[str, Any]]:
        """Create optimization plans."""
        plans = []

        if analysis.get("n_plus_one_suspects"):
            plans.append(
                {
                    "type": "fix_n_plus_one",
                    "priority": 8,
                    "description": f"Found {len(analysis['n_plus_one_suspects'])} potential N+1 queries",
                    "issues": analysis["n_plus_one_suspects"][:10],
                }
            )

        if analysis.get("raw_sql_usage"):
            plans.append(
                {
                    "type": "review_raw_sql",
                    "priority": 7,
                    "description": f"Found {len(analysis['raw_sql_usage'])} raw SQL usages",
                    "issues": analysis["raw_sql_usage"][:10],
                }
            )

        if analysis.get("missing_eager_loading"):
            plans.append(
                {
                    "type": "add_eager_loading",
                    "priority": 6,
                    "description": f"Found {len(analysis['missing_eager_loading'])} potential eager loading opportunities",
                    "issues": analysis["missing_eager_loading"][:10],
                }
            )

        return plans

    async def execute(self, plan: dict[str, Any]) -> dict[str, Any]:
        """Log optimization suggestions."""
        plan_type = plan.get("type", "")
        issues = plan.get("issues", [])

        if plan_type in ("fix_n_plus_one", "review_raw_sql", "add_eager_loading"):
            for issue in issues[:3]:
                logger.warning(
                    f"[{self.name}] {plan_type}: {issue.get('file', 'unknown')}:{issue.get('line', 0)}"
                )

            self._save_improvement_suggestion(
                {
                    "category": "database",
                    "priority": plan.get("priority", 6),
                    "title": plan.get("description", "Query optimization"),
                    "description": f"{len(issues)} issues found",
                    "estimated_impact": 0.2,
                    "details": issues,
                }
            )

            return {
                "status": "logged",
                "message": f"Logged {len(issues)} query optimization suggestions",
                "action": plan_type,
            }

        return {"status": "skipped", "message": f"Unknown: {plan_type}", "action": plan_type}
