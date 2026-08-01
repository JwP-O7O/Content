"""CodeFixerAgent - Automatically fixes code issues detected by monitoring."""

import builtins
import contextlib
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from loguru import logger

from ..base_autonomous_agent import BaseAutonomousAgent


class CodeFixerAgent(BaseAutonomousAgent):
    """
    Sub-agent that automatically fixes linting and code quality issues.

    Capabilities:
    - Run Ruff with --fix to auto-fix linting issues
    - Run Ruff format to standardize code style
    - Safe, non-breaking fixes only

    Interval: On-demand (triggered by monitoring)
    """

    def __init__(self):
        super().__init__(
            name="CodeFixerAgent",
            layer="execution",
            interval_seconds=0,  # On-demand only
        )
        self.src_path = Path("src")
        self.fixes_applied = 0

    async def analyze(self) -> dict[str, Any]:
        """Analyze current linting issues."""
        results = {
            "timestamp": datetime.now().isoformat(),
            "ruff_check": self._check_ruff_issues(),
            "format_check": self._check_format_issues(),
        }

        results["total_issues"] = results["ruff_check"].get("count", 0) + (
            1 if results["format_check"].get("needs_format", False) else 0
        )
        results["fixable"] = results["ruff_check"].get("fixable", 0)

        logger.info(
            f"[{self.name}] Found {results['total_issues']} issues, {results['fixable']} fixable"
        )

        return results

    async def plan(self, analysis: dict[str, Any]) -> list[dict[str, Any]]:
        """Create fix plans based on analysis."""
        plans = []

        # Plan 1: Ruff safe fixes
        if analysis.get("ruff_check", {}).get("fixable", 0) > 0:
            plans.append(
                {
                    "type": "ruff_safe_fix",
                    "priority": 8,
                    "description": f"Apply {analysis['ruff_check']['fixable']} safe Ruff fixes",
                    "count": analysis["ruff_check"]["fixable"],
                }
            )

        # Plan 2: Format code
        if analysis.get("format_check", {}).get("needs_format", False):
            plans.append(
                {"type": "ruff_format", "priority": 6, "description": "Format code with Ruff"}
            )

        # Plan 3: Organize imports
        plans.append(
            {"type": "organize_imports", "priority": 5, "description": "Organize and sort imports"}
        )

        return plans

    async def execute(self, plan: dict[str, Any]) -> dict[str, Any]:
        """Execute a fix plan."""
        plan_type = plan.get("type", "")

        if plan_type == "ruff_safe_fix":
            return self._apply_ruff_fixes()

        if plan_type == "ruff_format":
            return self._apply_ruff_format()

        if plan_type == "organize_imports":
            return self._organize_imports()

        return {
            "status": "skipped",
            "message": f"Unknown plan type: {plan_type}",
            "action": plan_type,
        }

    def _check_ruff_issues(self) -> dict[str, Any]:
        """Check for Ruff linting issues."""
        result = {"count": 0, "fixable": 0}

        try:
            output = subprocess.run(
                ["ruff", "check", str(self.src_path), "--output-format=json"],
                check=False,
                capture_output=True,
                text=True,
                timeout=120,
            )

            if output.stdout:
                import json

                try:
                    issues = json.loads(output.stdout)
                    result["count"] = len(issues)
                    result["fixable"] = sum(1 for i in issues if i.get("fix"))
                except:
                    pass

        except Exception as e:
            result["error"] = str(e)

        return result

    def _check_format_issues(self) -> dict[str, Any]:
        """Check if code needs formatting."""
        result = {"needs_format": False}

        try:
            output = subprocess.run(
                ["ruff", "format", "--check", str(self.src_path)],
                check=False,
                capture_output=True,
                text=True,
                timeout=60,
            )
            result["needs_format"] = output.returncode != 0
        except Exception as e:
            result["error"] = str(e)

        return result

    def _apply_ruff_fixes(self) -> dict[str, Any]:
        """Apply all safe Ruff auto-fixes."""
        try:
            # First pass: safe fixes
            subprocess.run(
                ["ruff", "check", str(self.src_path), "--fix", "--unsafe-fixes"],
                check=False,
                capture_output=True,
                text=True,
                timeout=120,
            )

            # Count remaining issues
            check = subprocess.run(
                ["ruff", "check", str(self.src_path), "--output-format=json"],
                check=False,
                capture_output=True,
                text=True,
                timeout=60,
            )

            remaining = 0
            if check.stdout:
                import json

                with contextlib.suppress(builtins.BaseException):
                    remaining = len(json.loads(check.stdout))

            self.fixes_applied += 1

            return {
                "status": "success",
                "message": f"Applied Ruff fixes, {remaining} issues remaining",
                "action": "ruff_safe_fix",
                "remaining_issues": remaining,
            }

        except Exception as e:
            return {"status": "error", "message": str(e), "action": "ruff_safe_fix"}

    def _apply_ruff_format(self) -> dict[str, Any]:
        """Apply Ruff formatting."""
        try:
            result = subprocess.run(
                ["ruff", "format", str(self.src_path)],
                check=False,
                capture_output=True,
                text=True,
                timeout=120,
            )

            return {
                "status": "success" if result.returncode == 0 else "partial",
                "message": "Applied code formatting",
                "action": "ruff_format",
            }

        except Exception as e:
            return {"status": "error", "message": str(e), "action": "ruff_format"}

    def _organize_imports(self) -> dict[str, Any]:
        """Organize imports using Ruff."""
        try:
            subprocess.run(
                ["ruff", "check", str(self.src_path), "--select=I", "--fix"],
                check=False,
                capture_output=True,
                text=True,
                timeout=60,
            )

            return {
                "status": "success",
                "message": "Organized imports",
                "action": "organize_imports",
            }

        except Exception as e:
            return {"status": "error", "message": str(e), "action": "organize_imports"}


async def run_code_fixer():
    """Convenience function to run the code fixer."""
    agent = CodeFixerAgent()
    return await agent.run_cycle()


if __name__ == "__main__":
    import asyncio

    asyncio.run(run_code_fixer())
