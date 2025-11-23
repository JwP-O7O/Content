# Development Setup Guide

Deze guide helpt developers om de Content Creator repository op te zetten voor development.

## Prerequisites

- Python 3.9 of hoger
- PostgreSQL database (voor productie/testing)
- Git
- (Optioneel) Pre-commit voor code quality hooks

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/JwP-O7O/Content.git
cd Content
```

### 2. Create Virtual Environment

```bash
# Maak virtual environment
python -m venv venv

# Activeer (Linux/Mac)
source venv/bin/activate

# Activeer (Windows)
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Production dependencies
pip install -r requirements.txt

# Development dependencies (aanbevolen)
pip install -r requirements-dev.txt
```

### 4. Setup Pre-commit Hooks (Aanbevolen)

```bash
# Install pre-commit hooks
pre-commit install

# Test de hooks
pre-commit run --all-files
```

Dit zorgt ervoor dat je code automatisch geformatteerd en gecontroleerd wordt voor elke commit.

### 5. Environment Configuration

```bash
# Kopieer .env example
cp .env.example .env

# Bewerk .env en voeg je API keys toe
nano .env  # of gebruik je favoriete editor
```

**Belangrijk**: Voor development/testing zijn dummy values OK, maar voor production heb je echte API keys nodig.

### 6. Database Setup (Optioneel voor tests)

Tests draaien zonder database, maar voor het volledige systeem:

```bash
# Initialize database
python init_db.py

# Of reset bestaande database
python init_db.py --reset
```

## Development Workflow

### Running Tests

```bash
# Run all tests
pytest

# Run met verbose output
pytest -v

# Run met coverage
pytest --cov=src --cov-report=html

# Run specifieke test
pytest tests/test_agents.py::TestBaseAgent -v
```

**Note**: Tests hebben GEEN .env bestand nodig - ze gebruiken test fixtures!

### Code Quality Checks

#### Linting

```bash
# Check code (zonder fixes)
ruff check .

# Check en auto-fix waar mogelijk
ruff check . --fix

# Check specifieke directory
ruff check src/agents/
```

#### Formatting

```bash
# Check formatting
ruff format --check .

# Format code
ruff format .
```

#### Type Checking (Optioneel)

```bash
# Run mypy type checker
mypy src/ --ignore-missing-imports
```

### Pre-commit Workflow

Als je pre-commit hebt geïnstalleerd:

```bash
# Pre-commit runs automatisch bij elke commit
git commit -m "Your message"

# Of run manually
pre-commit run --all-files
```

Pre-commit draait:
- Ruff linter & formatter
- Trailing whitespace check
- YAML/JSON validation
- Large files check
- Private key detection

## Project Structure

```
Content/
├── .github/
│   └── workflows/       # GitHub Actions CI/CD
├── config/
│   └── config.py        # Configuration management
├── src/
│   ├── agents/          # 16 AI agents (Phase 1-4)
│   ├── api_integrations/  # API clients
│   ├── database/        # Database models
│   └── utils/           # Utilities
├── tests/
│   ├── conftest.py      # Test fixtures
│   ├── test_agents.py   # Agent tests
│   └── test_database.py # Database tests
├── .env.example         # Environment template
├── requirements.txt     # Production deps
├── requirements-dev.txt # Development deps
├── ruff.toml           # Linter config
└── pytest.ini          # Test config
```

## Common Tasks

### Adding a New Agent

1. Create file in `src/agents/your_agent.py`
2. Inherit from `BaseAgent`
3. Implement `async def execute(self)`
4. Add to orchestrator
5. Write tests in `tests/test_agents.py`

Example:
```python
from src.agents.base_agent import BaseAgent

class YourAgent(BaseAgent):
    def __init__(self):
        super().__init__("YourAgent")
    
    async def execute(self):
        self.log_info("Starting execution")
        # Your logic here
        return {"status": "success"}
```

### Adding a New Database Model

1. Add model in `src/database/models.py`
2. Run `python init_db.py` to create table
3. Write tests in `tests/test_database.py`

### Running the System

```bash
# Interactive mode (met menu)
python main.py

# Scheduled mode (24/7 daemon)
python main.py --scheduled
```

## Troubleshooting

### Tests Fail with "ValidationError: Field required"

**Oorzaak**: Je probeert oude versie te draaien voor conftest.py was toegevoegd.

**Oplossing**: Pull laatste changes en run opnieuw.

### Ruff Not Found

**Oplossing**: 
```bash
pip install -r requirements-dev.txt
```

### Pre-commit Fails

**Oplossing**:
```bash
# Update pre-commit hooks
pre-commit autoupdate

# Clear cache
pre-commit clean
```

### Import Errors

**Oorzaak**: Virtual environment niet geactiveerd of dependencies niet geïnstalleerd.

**Oplossing**:
```bash
source venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
```

## Best Practices

### Before Committing

1. Run tests: `pytest`
2. Check linting: `ruff check .`
3. Format code: `ruff format .`
4. Review changes: `git diff`

(Of laat pre-commit dit automatisch doen!)

### Code Style

- Follow PEP 8 (enforced by ruff)
- Line length: 100 characters
- Use type hints waar mogelijk
- Write docstrings for public functions
- Use async/await consistently

### Testing

- Write tests voor nieuwe features
- Aim for >80% coverage
- Use mocks voor external APIs
- Keep tests fast

### Commits

- Write clear commit messages
- Use conventional commits format (optioneel):
  - `feat:` nieuwe feature
  - `fix:` bug fix
  - `docs:` documentatie
  - `style:` formatting
  - `refactor:` code refactoring
  - `test:` tests toevoegen
  - `chore:` onderhoud

## CI/CD Pipeline

GitHub Actions draait automatisch bij push/PR:

1. **Test Job** (Python 3.9-3.12)
   - Install dependencies
   - Run ruff linter
   - Run tests met coverage
   - Upload coverage

2. **Security Job**
   - Bandit security scanner
   - Safety vulnerability check

3. **Type Check Job**
   - MyPy type checking (informational)

Check `.github/workflows/ci.yml` voor details.

## Additional Resources

- [README.md](README.md) - Project overview
- [ROADMAP.md](ROADMAP.md) - Development roadmap
- [CLAUDE.md](CLAUDE.md) - AI agent guidance
- [CODE_QUALITY.md](CODE_QUALITY.md) - Quality improvements log
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [Pytest Documentation](https://docs.pytest.org/)

## Getting Help

Issues vinden? Vraag om hulp via:
- GitHub Issues
- Team chat
- Code reviews

Happy coding! 🚀
