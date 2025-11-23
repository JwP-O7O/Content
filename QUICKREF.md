# Quick Reference - Development Commands

Snelle referentie voor de meest gebruikte development commands.

## Setup

```bash
# Clone & setup
git clone https://github.com/JwP-O7O/Content.git
cd Content
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt -r requirements-dev.txt
pre-commit install
cp .env.example .env
```

## Testing

```bash
pytest                              # Run all tests
pytest -v                           # Verbose output
pytest tests/test_agents.py         # Specific file
pytest -k test_base_agent          # Specific test name
pytest --cov=src                    # With coverage
pytest --cov=src --cov-report=html  # HTML coverage report
```

## Code Quality

```bash
# Linting
ruff check .                   # Check all files
ruff check . --fix            # Auto-fix issues
ruff check src/agents/        # Specific directory

# Formatting
ruff format .                  # Format all files
ruff format --check .          # Check formatting only

# Type checking
mypy src/ --ignore-missing-imports
```

## Pre-commit

```bash
pre-commit install              # Install hooks
pre-commit run --all-files     # Run manually
pre-commit autoupdate          # Update hooks
```

## Git Workflow

```bash
# Create feature branch
git checkout -b feature/your-feature

# Make changes, then:
git add .
git commit -m "feat: your feature"  # Pre-commit runs automatically
git push origin feature/your-feature

# Create PR on GitHub
```

## Running the System

```bash
# Interactive mode
python main.py

# Scheduled daemon
python main.py --scheduled

# Verify system
python verify_system.py
```

## Database

```bash
# Initialize
python init_db.py

# Reset (WARNING: deletes data!)
python init_db.py --reset
```

## Common Fixes

```bash
# Linting errors
ruff check . --fix

# Import sorting
ruff check . --select I --fix

# Format code
ruff format .

# Clear pytest cache
rm -rf .pytest_cache

# Clear ruff cache
rm -rf .ruff_cache
```

## File Locations

```
tests/conftest.py           # Test fixtures
ruff.toml                   # Linter config
pytest.ini                  # Test config
.pre-commit-config.yaml     # Pre-commit hooks
.github/workflows/ci.yml    # CI pipeline
requirements.txt            # Production deps
requirements-dev.txt        # Dev deps
.env.example                # Env template
```

## Useful Aliases (Optional)

Add to `~/.bashrc` or `~/.zshrc`:

```bash
alias pt='pytest -v'
alias ptc='pytest --cov=src --cov-report=term'
alias lint='ruff check . --fix'
alias fmt='ruff format .'
alias check='ruff check . && ruff format --check . && pytest'
```

## CI/CD Status

Check pipeline: https://github.com/JwP-O7O/Content/actions

- ✅ Tests (Python 3.9-3.12)
- ✅ Security scan
- ✅ Type check

## Help

Full docs: [CONTRIBUTING.md](CONTRIBUTING.md)
