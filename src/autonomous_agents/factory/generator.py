"""AgentGenerator - Generates new agents from templates."""

import re
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from loguru import logger


class AgentGenerator:
    """
    Generates new autonomous agents from templates.

    Can create agents for:
    - Analysis tasks
    - Fixing/execution tasks
    - Validation tasks
    - Domain-specific tasks
    """

    def __init__(self):
        self.agents_dir = Path("src/autonomous_agents")
        self.templates = self._load_templates()

    def _load_templates(self) -> dict[str, str]:
        """Load agent templates."""
        return {
            "base": self._get_base_template(),
            "analyzer": self._get_analyzer_template(),
            "fixer": self._get_fixer_template(),
            "validator": self._get_validator_template(),
        }

    def generate_agent(
        self,
        name: str,
        layer: str,
        description: str,
        template: str = "base",
        capabilities: Optional[dict[str, Any]] = None,
    ) -> bool:
        """
        Generate a new agent from template.

        Args:
            name: Agent class name (e.g., "MyCustomAgent")
            layer: Layer (monitoring, analysis, execution, validation, etc.)
            description: What the agent does
            template: Template to use (base, analyzer, fixer, validator)
            capabilities: Additional capabilities to add

        Returns:
            True if successful
        """
        if template not in self.templates:
            logger.error(f"Unknown template: {template}")
            return False

        # Generate file name from class name
        file_name = self._to_snake_case(name) + ".py"

        # Determine output directory
        layer_dir = self.agents_dir / layer
        if not layer_dir.exists():
            layer_dir = self.agents_dir / "specialists"

        output_path = layer_dir / file_name

        # Fill template
        code = self.templates[template]
        code = code.replace("{{name}}", name)
        code = code.replace("{{description}}", description)
        code = code.replace("{{layer}}", layer)
        code = code.replace("{{file_name}}", file_name)
        code = code.replace("{{date}}", datetime.now().strftime("%Y-%m-%d"))

        # Write file
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(code)
            logger.info(f"Generated agent: {output_path}")

            # Register in factory
            from .agent_factory import get_factory

            factory = get_factory()
            factory.register_agent(
                name=name,
                module_path=f"{layer}.{name.lower()}",
                layer=layer,
                description=description,
                capabilities=list(capabilities.keys()) if capabilities else [],
            )

            return True

        except Exception as e:
            logger.error(f"Failed to generate agent: {e}")
            return False

    def _to_snake_case(self, name: str) -> str:
        """Convert CamelCase to snake_case."""
        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()

    def _get_base_template(self) -> str:
        """Get base agent template."""
        return '''"""{{name}} - {{description}}"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from loguru import logger

from ..base_autonomous_agent import BaseAutonomousAgent


class {{name}}(BaseAutonomousAgent):
    """
    {{description}}

    Generated: {{date}}
    Layer: {{layer}}
    """

    def __init__(self):
        super().__init__(
            name="{{name}}",
            layer="{{layer}}",
            interval_seconds=3600
        )

    async def analyze(self) -> Dict[str, Any]:
        """Analyze current state."""
        results = {
            'timestamp': datetime.now().isoformat(),
            'status': 'analyzed'
        }

        # TODO: Implement analysis logic

        logger.info(f"[{self.name}] Analysis complete")
        return results

    async def plan(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create improvement plans."""
        plans = []

        # TODO: Implement planning logic

        return plans

    async def execute(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a plan."""
        plan_type = plan.get('type', '')

        # TODO: Implement execution logic

        return {
            'status': 'success',
            'message': f'Executed {plan_type}',
            'action': plan_type
        }
'''

    def _get_analyzer_template(self) -> str:
        """Get analyzer agent template."""
        return '''"""{{name}} - {{description}}"""

import ast
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from loguru import logger

from ..base_autonomous_agent import BaseAutonomousAgent


class {{name}}(BaseAutonomousAgent):
    """
    {{description}}

    Analyzer template - optimized for code analysis tasks.
    Generated: {{date}}
    """

    def __init__(self):
        super().__init__(
            name="{{name}}",
            layer="analysis",
            interval_seconds=3600
        )
        self.src_path = Path("src")
        self.analysis_results: List[Dict[str, Any]] = []

    async def analyze(self) -> Dict[str, Any]:
        """Perform deep analysis."""
        results = {
            'timestamp': datetime.now().isoformat(),
            'files_analyzed': 0,
            'findings': []
        }

        for py_file in self.src_path.rglob('*.py'):
            try:
                content = py_file.read_text()
                tree = ast.parse(content)

                # Analyze each file
                file_findings = self._analyze_file(py_file, tree)
                results['findings'].extend(file_findings)
                results['files_analyzed'] += 1

            except Exception as e:
                logger.debug(f"[{self.name}] Error analyzing {py_file}: {e}")

        results['score'] = self._calculate_score(results)
        self.metrics['score'] = results['score']

        logger.info(f"[{self.name}] Analyzed {results['files_analyzed']} files, score: {results['score']}")
        return results

    def _analyze_file(self, file_path: Path, tree: ast.AST) -> List[Dict[str, Any]]:
        """Analyze a single file."""
        findings = []

        # TODO: Implement file analysis

        return findings

    def _calculate_score(self, results: Dict[str, Any]) -> float:
        """Calculate analysis score (0-100)."""
        findings = len(results.get('findings', []))
        files = max(results.get('files_analyzed', 1), 1)

        # Score decreases with more findings per file
        score = 100 - (findings / files * 10)
        return max(0, min(100, score))

    async def plan(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create improvement plans from findings."""
        plans = []

        findings = analysis.get('findings', [])
        if findings:
            plans.append({
                'type': 'address_findings',
                'priority': 5,
                'description': f"Address {len(findings)} findings",
                'findings': findings[:20]
            })

        return plans

    async def execute(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Log findings for review."""
        findings = plan.get('findings', [])

        self._save_improvement_suggestion({
            'category': '{{layer}}',
            'priority': plan.get('priority', 5),
            'title': plan.get('description', 'Analysis findings'),
            'description': f"{len(findings)} items found",
            'estimated_impact': 0.1,
            'details': findings
        })

        return {
            'status': 'logged',
            'message': f'Logged {len(findings)} findings',
            'action': plan.get('type', 'unknown')
        }
'''

    def _get_fixer_template(self) -> str:
        """Get fixer/execution agent template."""
        return '''"""{{name}} - {{description}}"""

import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from loguru import logger

from ..base_autonomous_agent import BaseAutonomousAgent


class {{name}}(BaseAutonomousAgent):
    """
    {{description}}

    Fixer template - optimized for automated code fixes.
    Generated: {{date}}
    """

    def __init__(self):
        super().__init__(
            name="{{name}}",
            layer="execution",
            interval_seconds=0  # On-demand
        )
        self.src_path = Path("src")
        self.fixes_applied = 0

    async def analyze(self) -> Dict[str, Any]:
        """Identify issues to fix."""
        results = {
            'timestamp': datetime.now().isoformat(),
            'issues': [],
            'fixable': 0
        }

        # TODO: Implement issue detection

        results['total'] = len(results['issues'])
        logger.info(f"[{self.name}] Found {results['total']} issues, {results['fixable']} fixable")
        return results

    async def plan(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create fix plans."""
        plans = []

        if analysis.get('fixable', 0) > 0:
            plans.append({
                'type': 'auto_fix',
                'priority': 7,
                'description': f"Fix {analysis['fixable']} issues automatically"
            })

        return plans

    async def execute(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Apply fixes."""
        plan_type = plan.get('type', '')

        if plan_type == 'auto_fix':
            return self._apply_fixes()

        return {
            'status': 'skipped',
            'message': f'Unknown: {plan_type}',
            'action': plan_type
        }

    def _apply_fixes(self) -> Dict[str, Any]:
        """Apply automatic fixes."""
        try:
            # TODO: Implement fix logic
            self.fixes_applied += 1

            return {
                'status': 'success',
                'message': 'Fixes applied',
                'action': 'auto_fix'
            }

        except Exception as e:
            return {
                'status': 'error',
                'message': str(e),
                'action': 'auto_fix'
            }
'''

    def _get_validator_template(self) -> str:
        """Get validator agent template."""
        return '''"""{{name}} - {{description}}"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from loguru import logger

from ..base_autonomous_agent import BaseAutonomousAgent


class {{name}}(BaseAutonomousAgent):
    """
    {{description}}

    Validator template - optimized for validation tasks.
    Generated: {{date}}
    """

    def __init__(self):
        super().__init__(
            name="{{name}}",
            layer="validation",
            interval_seconds=3600
        )
        self.validation_history: List[Dict[str, Any]] = []

    async def analyze(self) -> Dict[str, Any]:
        """Run validation checks."""
        results = {
            'timestamp': datetime.now().isoformat(),
            'passed': 0,
            'failed': 0,
            'checks': []
        }

        # Run validation checks
        checks = self._run_checks()
        results['checks'] = checks
        results['passed'] = sum(1 for c in checks if c.get('passed'))
        results['failed'] = sum(1 for c in checks if not c.get('passed'))

        total = results['passed'] + results['failed']
        results['pass_rate'] = (results['passed'] / max(total, 1)) * 100

        self.metrics['pass_rate'] = results['pass_rate']

        logger.info(f"[{self.name}] Validation: {results['passed']}/{total} passed ({results['pass_rate']:.1f}%)")
        return results

    def _run_checks(self) -> List[Dict[str, Any]]:
        """Run all validation checks."""
        checks = []

        # TODO: Implement validation checks

        return checks

    async def plan(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create plans to address failed checks."""
        plans = []

        failed = [c for c in analysis.get('checks', []) if not c.get('passed')]

        if failed:
            plans.append({
                'type': 'report_failures',
                'priority': 8,
                'description': f"{len(failed)} validation checks failed",
                'failures': failed
            })

        return plans

    async def execute(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Report validation failures."""
        failures = plan.get('failures', [])

        for failure in failures[:5]:
            logger.warning(f"[{self.name}] {failure.get('name', 'Check')}: {failure.get('message', 'Failed')}")

        self._save_improvement_suggestion({
            'category': 'validation',
            'priority': 8,
            'title': plan.get('description', 'Validation failures'),
            'description': f"{len(failures)} checks failed",
            'estimated_impact': 0.2,
            'details': failures
        })

        return {
            'status': 'logged',
            'message': f'Reported {len(failures)} failures',
            'action': 'report_failures'
        }
'''
