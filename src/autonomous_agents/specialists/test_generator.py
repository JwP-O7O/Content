"""TestGeneratorAgent - Auto-generates unit tests for functions."""

import ast
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from loguru import logger

from ..base_autonomous_agent import BaseAutonomousAgent


class TestGeneratorAgent(BaseAutonomousAgent):
    """
    Automatically generates unit tests for functions and classes.

    Features:
    - Identifies untested functions
    - Generates pytest-style tests
    - Creates test files if needed
    - Tracks coverage improvements
    """

    def __init__(self):
        super().__init__(
            name="TestGeneratorAgent",
            layer="specialists",
            interval_seconds=0,  # On-demand
        )
        self.src_path = Path("src")
        self.tests_path = Path("tests")
        self.tests_generated = 0

    async def analyze(self) -> dict[str, Any]:
        """Analyze test coverage and find untested code."""
        results = {
            "timestamp": datetime.now().isoformat(),
            "coverage": self._get_coverage(),
            "untested_files": [],
            "untested_functions": [],
        }

        # Find files without corresponding test files
        tested_modules = self._get_tested_modules()

        for py_file in self.src_path.rglob("*.py"):
            if py_file.name.startswith("_"):
                continue

            module_name = py_file.stem

            # Check if test file exists
            has_test = any(
                module_name in test_name or test_name in module_name for test_name in tested_modules
            )

            if not has_test:
                # Get public functions
                try:
                    tree = ast.parse(py_file.read_text())
                    functions = [
                        {
                            "name": node.name,
                            "line": node.lineno,
                            "args": [arg.arg for arg in node.args.args if arg.arg != "self"],
                        }
                        for node in ast.walk(tree)
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                        and not node.name.startswith("_")
                    ]

                    if functions:
                        results["untested_files"].append(
                            {
                                "path": str(py_file),
                                "module": module_name,
                                "functions": functions[:10],
                            }
                        )
                        results["untested_functions"].extend(
                            [{"file": str(py_file), **f} for f in functions[:10]]
                        )
                except:
                    pass

        self.metrics["coverage"] = results["coverage"].get("percent", 0)
        self.metrics["untested_files"] = len(results["untested_files"])

        logger.info(
            f"[{self.name}] Coverage: {results['coverage'].get('percent', 0):.1f}% "
            f"({len(results['untested_files'])} files without tests)"
        )

        return results

    async def plan(self, analysis: dict[str, Any]) -> list[dict[str, Any]]:
        """Create plans to generate tests."""
        plans = []

        untested = analysis.get("untested_files", [])

        for file_info in untested[:5]:  # Limit to 5 files per cycle
            plans.append(
                {
                    "type": "generate_tests",
                    "priority": 6,
                    "file": file_info["path"],
                    "module": file_info["module"],
                    "functions": file_info["functions"],
                    "description": f"Generate tests for {file_info['module']}",
                }
            )

        return plans

    async def execute(self, plan: dict[str, Any]) -> dict[str, Any]:
        """Generate tests for a module."""
        plan_type = plan.get("type", "")

        if plan_type == "generate_tests":
            module = plan.get("module", "unknown")
            functions = plan.get("functions", [])

            # Generate test code
            test_code = self._generate_test_code(plan)

            # Save as suggestion (don't auto-create files without approval)
            self._save_improvement_suggestion(
                {
                    "category": "testing",
                    "priority": 6,
                    "title": f"Generate tests for {module}",
                    "description": f"Create tests for {len(functions)} functions",
                    "estimated_impact": 0.1,
                    "test_file": f"tests/test_{module}.py",
                    "test_code": test_code,
                    "functions": functions,
                }
            )

            logger.info(f"[{self.name}] Generated test suggestions for {module}")

            return {
                "status": "logged",
                "message": f"Generated test suggestions for {module}",
                "action": "generate_tests",
                "functions_count": len(functions),
            }

        return {"status": "skipped", "message": f"Unknown: {plan_type}", "action": plan_type}

    def _get_coverage(self) -> dict[str, Any]:
        """Get current test coverage."""
        result = {"percent": 0, "available": False}

        try:
            # Try to run coverage
            subprocess.run(
                ["python3", "-m", "pytest", "--cov=src", "--cov-report=json", "-q", "--no-header"],
                check=False,
                capture_output=True,
                text=True,
                timeout=120,
                cwd=str(Path.cwd()),
            )

            coverage_file = Path("coverage.json")
            if coverage_file.exists():
                import json

                data = json.loads(coverage_file.read_text())
                result["percent"] = data.get("totals", {}).get("percent_covered", 0)
                result["available"] = True
        except Exception as e:
            logger.debug(f"[{self.name}] Could not get coverage: {e}")

        return result

    def _get_tested_modules(self) -> list[str]:
        """Get list of modules that have test files."""
        tested = []

        if self.tests_path.exists():
            for test_file in self.tests_path.rglob("test_*.py"):
                # Extract module name from test file
                name = test_file.stem.replace("test_", "")
                tested.append(name)

        return tested

    def _generate_test_code(self, plan: dict[str, Any]) -> str:
        """Generate pytest test code for a module."""
        module = plan.get("module", "unknown")
        functions = plan.get("functions", [])
        file_path = plan.get("file", "")

        # Determine import path
        relative_path = Path(file_path).relative_to(Path.cwd()) if file_path else Path(module)
        import_path = str(relative_path).replace("/", ".").replace(".py", "")

        lines = [
            f'"""Tests for {module}."""',
            "",
            "import pytest",
            f"# from {import_path} import *  # Uncomment and adjust",
            "",
            "",
        ]

        for func in functions:
            func_name = func.get("name", "unknown")
            args = func.get("args", [])

            lines.extend(
                [
                    f"class Test{self._to_class_name(func_name)}:",
                    f'    """Tests for {func_name}."""',
                    "",
                    f"    def test_{func_name}_basic(self):",
                    f'        """Test basic functionality of {func_name}."""',
                    "        # Arrange",
                    "        # TODO: Set up test data",
                    "",
                    "        # Act",
                    f"        # result = {func_name}({', '.join(args)})",
                    "",
                    "        # Assert",
                    "        # assert result == expected",
                    "        pass  # TODO: Implement test",
                    "",
                    f"    def test_{func_name}_edge_cases(self):",
                    f'        """Test edge cases for {func_name}."""',
                    "        # TODO: Test edge cases",
                    "        pass",
                    "",
                    "",
                ]
            )

        return "\n".join(lines)

    def _to_class_name(self, name: str) -> str:
        """Convert function name to class name."""
        return "".join(word.capitalize() for word in name.split("_"))


async def run_test_generator():
    """Run the test generator."""
    agent = TestGeneratorAgent()
    return await agent.run_cycle()
