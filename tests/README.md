# Content Creator - Test Suite

Unit tests voor het Content Creator systeem.

## Test Setup

```bash
# Installeer test dependencies
pip install -r requirements.txt

# Of alleen test packages
pip install pytest pytest-asyncio pytest-mock
```

## Running Tests

### Run All Tests

```bash
# Run alle tests
pytest

# Run met verbose output
pytest -v

# Run met coverage
pytest --cov=src --cov-report=html
```

### Run Specific Tests

```bash
# Run alleen agent tests
pytest tests/test_agents.py

# Run alleen database tests
pytest tests/test_database.py

# Run een specifieke test
pytest tests/test_agents.py::TestABTestingAgent::test_calculate_statistical_significance

# Run tests met een specifieke marker
pytest -m unit
pytest -m integration
```

### Run Tests in Watch Mode

```bash
# Install pytest-watch
pip install pytest-watch

# Run in watch mode
ptw
```

## Test Structure

```
tests/
├── __init__.py
├── README.md
├── test_agents.py          # Agent unit tests
├── test_database.py        # Database model tests
├── test_api_integrations.py (TODO)
└── test_orchestrator.py    (TODO)
```

## Test Coverage

Current test coverage:

- ✅ **Base Agent**: Initialization, run/execute flow
- ✅ **ABTestingAgent**: Statistical calculations, initialization
- ✅ **StrategyTuningAgent**: Initialization, execute structure
- ✅ **PerformanceAnalyticsAgent**: Trend calculation, anomaly detection
- ✅ **Database Models**: All Phase 1-4 models, relationships
- ✅ **Configuration**: Settings loading

### TODO - Additional Tests

- [ ] API Integration tests (Twitter, Telegram, Discord, Stripe)
- [ ] Orchestrator workflow tests
- [ ] Scheduler tests
- [ ] End-to-end pipeline tests
- [ ] Performance/load tests
- [ ] Error handling tests
- [ ] Mocking external API calls

## Writing New Tests

### Example Unit Test

```python
import pytest
from unittest.mock import Mock, patch

class TestMyAgent:
    """Test MyAgent functionality."""

    def test_agent_initialization(self):
        """Test that agent initializes correctly."""
        agent = MyAgent()
        assert agent.name == "MyAgent"

    @pytest.mark.asyncio
    async def test_agent_execute(self):
        """Test agent execute method."""
        agent = MyAgent()
        result = await agent.execute()
        assert "status" in result
```

### Example Database Test

```python
import pytest

@pytest.fixture
def in_memory_db():
    """Create in-memory test database."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_model_creation(in_memory_db):
    """Test creating a model."""
    obj = MyModel(field="value")
    in_memory_db.add(obj)
    in_memory_db.commit()
    assert obj.id is not None
```

## Test Best Practices

1. **Use descriptive test names**: `test_should_return_error_when_invalid_input`
2. **One assertion per test**: Keep tests focused
3. **Use fixtures**: Avoid code duplication
4. **Mock external dependencies**: Don't call real APIs in unit tests
5. **Test edge cases**: Empty inputs, None values, large numbers
6. **Test error handling**: Ensure exceptions are handled correctly

## Continuous Integration

For CI/CD pipelines:

```yaml
# .github/workflows/tests.yml example
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest --cov=src --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

## Debugging Tests

```bash
# Run with pdb on failure
pytest --pdb

# Run last failed tests only
pytest --lf

# Show local variables in tracebacks
pytest -l

# Stop on first failure
pytest -x
```

## Performance Testing

```bash
# Show slowest tests
pytest --durations=10

# Profile test execution
pytest --profile
```

## Test Markers

Available markers:
- `@pytest.mark.asyncio` - Async tests
- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.slow` - Slow running tests

Example:
```python
@pytest.mark.unit
@pytest.mark.asyncio
async def test_something():
    pass
```

---

**Status**: Basic test suite implemented ✅

Next steps:
- Add API integration tests
- Add end-to-end pipeline tests
- Setup CI/CD
- Increase coverage to 80%+
