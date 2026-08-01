"""ArchitectureAnalyzer - Analyzes system architecture and dependencies."""

import ast
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from loguru import logger

from ..base_autonomous_agent import BaseAutonomousAgent


class ArchitectureAnalyzer(BaseAutonomousAgent):
    """
    Analyzes system architecture, module dependencies, and code organization.

    Analyzes:
    - Module dependency graph
    - Circular dependencies
    - Layer violations
    - Package structure
    - Import patterns

    Interval: 6 hours (21600 seconds)
    """

    def __init__(self):
        super().__init__(name="ArchitectureAnalyzer", layer="analysis", interval_seconds=21600)
        self.src_path = Path("src")

    async def analyze(self) -> dict[str, Any]:
        """Analyze system architecture."""
        results = {
            "timestamp": datetime.now().isoformat(),
            "modules": self._analyze_modules(),
            "dependencies": self._analyze_dependencies(),
            "circular_deps": self._find_circular_dependencies(),
            "layer_violations": self._check_layer_violations(),
        }

        # Calculate architecture score
        circular_count = len(results["circular_deps"].get("cycles", []))
        violation_count = len(results["layer_violations"].get("violations", []))

        score = 100
        score -= circular_count * 15  # Heavy penalty for circular deps
        score -= violation_count * 5

        results["architecture_score"] = max(0, min(100, score))

        self.metrics["architecture_score"] = results["architecture_score"]
        self.metrics["module_count"] = results["modules"].get("count", 0)
        self.metrics["circular_deps"] = circular_count

        logger.info(f"[{self.name}] Architecture Score: {results['architecture_score']:.1f}/100")

        return results

    async def plan(self, analysis: dict[str, Any]) -> list[dict[str, Any]]:
        """Create improvement plans."""
        plans = []

        # Circular dependencies
        cycles = analysis.get("circular_deps", {}).get("cycles", [])
        if cycles:
            plans.append(
                {
                    "type": "fix_circular_deps",
                    "priority": 9,
                    "description": f"Found {len(cycles)} circular dependency chains",
                    "cycles": cycles,
                }
            )

        # Layer violations
        violations = analysis.get("layer_violations", {}).get("violations", [])
        if violations:
            plans.append(
                {
                    "type": "fix_layer_violations",
                    "priority": 7,
                    "description": f"Found {len(violations)} layer violations",
                    "violations": violations,
                }
            )

        # Large modules
        modules = analysis.get("modules", {}).get("details", [])
        large_modules = [m for m in modules if m.get("file_count", 0) > 15]
        if large_modules:
            plans.append(
                {
                    "type": "split_large_modules",
                    "priority": 5,
                    "description": f"Found {len(large_modules)} large modules (>15 files)",
                    "modules": large_modules,
                }
            )

        return plans

    async def execute(self, plan: dict[str, Any]) -> dict[str, Any]:
        """Execute plan (log recommendations)."""
        plan_type = plan.get("type", "")

        if plan_type == "fix_circular_deps":
            cycles = plan.get("cycles", [])

            logger.warning(f"[{self.name}] Circular dependencies detected:")
            for cycle in cycles[:5]:
                logger.warning(f"  - {' -> '.join(cycle)}")

            self._save_improvement_suggestion(
                {
                    "category": "architecture",
                    "priority": 9,
                    "title": "Fix Circular Dependencies",
                    "description": f"{len(cycles)} circular dependency chains found",
                    "estimated_impact": 0.25,
                    "details": cycles,
                }
            )

            return {
                "status": "logged",
                "message": f"Logged {len(cycles)} circular dependencies",
                "action": "fix_circular_deps",
            }

        if plan_type == "fix_layer_violations":
            violations = plan.get("violations", [])

            self._save_improvement_suggestion(
                {
                    "category": "architecture",
                    "priority": 7,
                    "title": "Fix Layer Violations",
                    "description": f"{len(violations)} layer violations found",
                    "estimated_impact": 0.15,
                    "details": violations,
                }
            )

            return {
                "status": "logged",
                "message": f"Logged {len(violations)} layer violations",
                "action": "fix_layer_violations",
            }

        if plan_type == "split_large_modules":
            modules = plan.get("modules", [])

            self._save_improvement_suggestion(
                {
                    "category": "architecture",
                    "priority": 5,
                    "title": "Split Large Modules",
                    "description": f"{len(modules)} modules are too large",
                    "estimated_impact": 0.1,
                    "details": modules,
                }
            )

            return {
                "status": "logged",
                "message": f"Logged {len(modules)} large modules",
                "action": "split_large_modules",
            }

        return {"status": "skipped", "message": f"Unknown: {plan_type}", "action": plan_type}

    def _analyze_modules(self) -> dict[str, Any]:
        """Analyze module structure."""
        result = {"count": 0, "details": []}

        try:
            for module_dir in self.src_path.iterdir():
                if module_dir.is_dir() and not module_dir.name.startswith("_"):
                    py_files = list(module_dir.rglob("*.py"))
                    result["details"].append(
                        {
                            "name": module_dir.name,
                            "file_count": len(py_files),
                            "has_init": (module_dir / "__init__.py").exists(),
                        }
                    )
                    result["count"] += 1

            result["details"].sort(key=lambda x: x["file_count"], reverse=True)

        except Exception as e:
            result["error"] = str(e)

        return result

    def _analyze_dependencies(self) -> dict[str, Any]:
        """Build dependency graph from imports."""
        result = {"graph": defaultdict(set), "external": set()}

        try:
            for py_file in self.src_path.rglob("*.py"):
                try:
                    tree = ast.parse(py_file.read_text())
                    module_name = str(py_file.relative_to(self.src_path.parent))

                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                if alias.name.startswith("src."):
                                    result["graph"][module_name].add(alias.name)
                                else:
                                    result["external"].add(alias.name.split(".")[0])

                        elif isinstance(node, ast.ImportFrom):
                            if node.module and node.module.startswith("src."):
                                result["graph"][module_name].add(node.module)
                            elif node.module:
                                result["external"].add(node.module.split(".")[0])
                except:
                    pass

            # Convert sets to lists for JSON
            result["graph"] = {k: list(v) for k, v in result["graph"].items()}
            result["external"] = list(result["external"])[:30]
            result["internal_deps"] = sum(len(v) for v in result["graph"].values())

        except Exception as e:
            result["error"] = str(e)

        return result

    def _find_circular_dependencies(self) -> dict[str, Any]:
        """Find circular dependency chains."""
        result = {"has_cycles": False, "cycles": []}

        # Build simple dependency graph
        graph = defaultdict(set)

        try:
            for py_file in self.src_path.rglob("*.py"):
                try:
                    tree = ast.parse(py_file.read_text())
                    module = py_file.stem

                    for node in ast.walk(tree):
                        if isinstance(node, ast.ImportFrom):
                            if node.module and "src." in (node.module or ""):
                                imported = node.module.split(".")[-1]
                                if imported != module:
                                    graph[module].add(imported)
                except:
                    pass

            # Simple cycle detection (DFS)
            visited = set()
            rec_stack = set()
            cycles = []

            def dfs(node, path):
                visited.add(node)
                rec_stack.add(node)
                path.append(node)

                for neighbor in graph.get(node, []):
                    if neighbor not in visited:
                        dfs(neighbor, path.copy())
                    elif neighbor in rec_stack:
                        # Found cycle
                        cycle_start = path.index(neighbor) if neighbor in path else -1
                        if cycle_start >= 0:
                            cycle = [*path[cycle_start:], neighbor]
                            if len(cycle) <= 10:  # Limit cycle size
                                cycles.append(cycle)

                rec_stack.discard(node)

            for node in list(graph.keys())[:50]:  # Limit nodes checked
                if node not in visited:
                    dfs(node, [])

            result["cycles"] = cycles[:10]
            result["has_cycles"] = len(cycles) > 0

        except Exception as e:
            result["error"] = str(e)

        return result

    def _check_layer_violations(self) -> dict[str, Any]:
        """Check for architectural layer violations."""
        result = {"violations": []}

        # Define layer hierarchy (higher layers should not be imported by lower layers)
        layer_order = {"database": 1, "models": 2, "agents": 3, "services": 3, "api": 4, "web": 4}

        try:
            for py_file in self.src_path.rglob("*.py"):
                try:
                    # Determine file's layer
                    parts = py_file.parts
                    file_layer = None
                    file_layer_num = 0

                    for part in parts:
                        if part in layer_order:
                            file_layer = part
                            file_layer_num = layer_order[part]
                            break

                    if not file_layer:
                        continue

                    # Check imports
                    tree = ast.parse(py_file.read_text())

                    for node in ast.walk(tree):
                        if isinstance(node, ast.ImportFrom) and node.module:
                            for layer, num in layer_order.items():
                                if layer in node.module and num > file_layer_num:
                                    result["violations"].append(
                                        {
                                            "file": str(py_file),
                                            "layer": file_layer,
                                            "imports": layer,
                                            "module": node.module,
                                        }
                                    )
                                    break
                except:
                    pass

            result["violations"] = result["violations"][:20]

        except Exception as e:
            result["error"] = str(e)

        return result
