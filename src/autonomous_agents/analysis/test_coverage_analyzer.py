"""TestCoverageAnalyzer - Analyzes test coverage of the codebase."""

import json
import subprocess
from pathlib import Path
from typing import Any

from ..base_autonomous_agent import BaseAutonomousAgent


class TestCoverageAnalyzer(BaseAutonomousAgent):
    """
    Analyzes code coverage using pytest-cov.
    Identifies files with low coverage.
    """

    def __init__(self):
        super().__init__(
            name="TestCoverageAnalyzer",
            layer="analysis",
            interval_seconds=21600,  # Every 6 hours
        )
        self.min_coverage_threshold = 80.0

    async def analyze(self) -> dict[str, Any]:
        """Run coverage analysis."""
        self.log_info("Running test coverage analysis...")
        results = {}

        try:
            # Run pytest with coverage
            # We use --cov-report=json to get structured data
            # -p no:warnings to reduce noise
            cmd = ["pytest", "--cov=src", "--cov-report=json:coverage.json", "-p", "no:warnings"]

            process = subprocess.run(
                cmd, check=False, capture_output=True, text=True, cwd=Path.cwd()
            )

            # Check if coverage.json exists
            cov_file = Path("coverage.json")
            if cov_file.exists():
                with open(cov_file) as f:
                    cov_data = json.load(f)

                # Calculate overall coverage
                totals = cov_data.get("totals", {})
                overall_coverage = totals.get("percent_covered", 0.0)

                # Identify low coverage files
                low_coverage_files = []
                for filename, file_data in cov_data.get("files", {}).items():
                    # Skip __init__.py and empty files
                    if filename.endswith("__init__.py"):
                        continue

                    coverage = file_data.get("summary", {}).get("percent_covered", 0.0)
                    missing_lines = file_data.get("missing_lines", [])

                    if coverage < self.min_coverage_threshold:
                        low_coverage_files.append(
                            {
                                "file": filename,
                                "coverage": coverage,
                                "missing_lines": len(missing_lines),
                            }
                        )

                # Sort by lowest coverage first
                low_coverage_files.sort(key=lambda x: x["coverage"])

                results["overall_coverage"] = overall_coverage
                results["low_coverage_files"] = low_coverage_files
                results["files_analyzed"] = len(cov_data.get("files", {}))

                self.metrics["test_coverage"] = overall_coverage

                # Clean up
                cov_file.unlink()
            else:
                results["error"] = "coverage.json not generated"
                results["stderr"] = process.stderr

        except Exception as e:
            results["error"] = str(e)
            self.log_error(f"Coverage analysis failed: {e}")

        return results

    async def plan(self, analysis: dict[str, Any]) -> list[dict[str, Any]]:
        """Plan test generation for low coverage files."""
        plans = []

        low_coverage_files = analysis.get("low_coverage_files", [])

        # Prioritize top 5 files with lowest coverage
        for file_info in low_coverage_files[:5]:
            plans.append(
                {
                    "type": "generate_tests",
                    "priority": 8,
                    "file": file_info["file"],
                    "current_coverage": file_info["coverage"],
                    "target_coverage": self.min_coverage_threshold,
                    "description": f"Generate tests for {file_info['file']} (coverage: {file_info['coverage']:.1f}%)",
                }
            )

        return plans

    async def execute(self, plan: dict[str, Any]) -> dict[str, Any]:
        """
        Execution is handled by TestGeneratorAgent.
        This agent just creates the plans.
        """
        return {
            "status": "planned",
            "message": f"Test generation planned for {plan['file']}",
            "plan": plan,
        }
