# Testing Guide

Complete guide voor het testen van het Content Creator systeem.

## 📋 Test Overview

### Current Coverage

```bash
pytest --cov=src --cov-report=term-missing
```

**Current**: ~40% (Target: 80%+)

### Test Categories

1. **Unit Tests** - Individual components
2. **Integration Tests** - Component interaction
3. **API Tests** - External integrations
4. **E2E Tests** - Complete workflows
5. **Performance Tests** - Load & benchmarks

## 🚀 Quick Start

### Running Tests

```bash
# All tests
pytest -v

# Specific test file
pytest tests/test_agents.py -v

# Specific test
pytest tests/test_agents.py::test_base_agent_initialization -v

# With coverage
pytest --cov=src --cov-report=html

# Integration tests only
pytest -m integration

# Skip slow tests
pytest -m "not slow"
```

### Test Markers

```python
@pytest.mark.asyncio      # Async tests
@pytest.mark.integration  # Integration tests
@pytest.mark.slow         # Slow-running tests
@pytest.mark.unit         # Unit tests
```

## 📁 Test Structure

```
tests/
├── conftest.py                # Fixtures and configuration
├── test_agents.py             # Agent unit tests
├── test_database.py           # Database tests
├── test_api_integrations.py  # API integration tests
├── test_orchestrator.py       # Orchestrator tests
└── test_integration.py        # E2E integration tests
```

## 🧪 Writing Tests

### Basic Test Template

```python
"""Test module for MyAgent."""

import pytest
from unittest.mock import Mock, patch, AsyncMock


class TestMyAgent:
    """Tests for MyAgent."""

    def test_initialization(self):
        """Test agent initializes correctly."""
        from src.agents.my_agent import MyAgent
        
        agent = MyAgent()
        assert agent is not None
        assert agent.name == "MyAgent"

    @pytest.mark.asyncio
    async def test_execute(self):
        """Test agent execution."""
        from src.agents.my_agent import MyAgent
        
        agent = MyAgent()
        result = await agent.run()
        
        assert result is not None
        assert "status" in result

    @pytest.mark.asyncio
    async def test_execute_with_mock(self):
        """Test execution with mocked dependencies."""
        from src.agents.my_agent import MyAgent
        
        with patch('src.api_integrations.some_api.SomeAPI.method', 
                   AsyncMock(return_value={'data': 'test'})):
            agent = MyAgent()
            result = await agent.run()
            
            assert result['status'] == 'success'
```

### Testing Async Code

```python
import pytest
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_async_function():
    """Test async function."""
    result = await some_async_function()
    assert result is not None

@pytest.mark.asyncio
async def test_with_async_mock():
    """Test with async mock."""
    mock = AsyncMock(return_value={'key': 'value'})
    result = await mock()
    assert result['key'] == 'value'
```

### Testing Database Operations

```python
def test_database_operation(in_memory_db):
    """Test database operation."""
    from src.database.models import MarketData
    
    # Use fixture-provided in-memory database
    db = in_memory_db
    
    # Create test data
    data = MarketData(
        symbol='BTC',
        price=50000.0,
        volume=1000000,
        timestamp=datetime.now(tz=timezone.utc)
    )
    db.add(data)
    db.commit()
    
    # Query
    result = db.query(MarketData).filter_by(symbol='BTC').first()
    assert result is not None
    assert result.price == 50000.0
```

### Mocking External APIs

```python
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
async def test_api_call():
    """Test external API call."""
    mock_response = {'price': 50000, 'volume': 1000}
    
    with patch('src.api_integrations.exchange_api.ExchangeAPI.get_price_data',
               AsyncMock(return_value=mock_response)):
        from src.agents.market_scanner_agent import MarketScannerAgent
        
        agent = MarketScannerAgent()
        # Agent will use mocked API
        result = await agent.run()
        
        assert result is not None
```

## 🎯 Test Best Practices

### 1. Arrange-Act-Assert Pattern

```python
def test_something():
    # Arrange - Setup test data
    agent = MyAgent()
    test_input = {'key': 'value'}
    
    # Act - Execute function
    result = agent.process(test_input)
    
    # Assert - Verify results
    assert result['status'] == 'success'
```

### 2. Use Fixtures

```python
@pytest.fixture
def sample_market_data():
    """Provide sample market data."""
    return {
        'symbol': 'BTC',
        'price': 50000.0,
        'volume': 1000000
    }

def test_with_fixture(sample_market_data):
    """Test using fixture."""
    assert sample_market_data['symbol'] == 'BTC'
```

### 3. Parametrize Tests

```python
@pytest.mark.parametrize('symbol,expected', [
    ('BTC', True),
    ('ETH', True),
    ('INVALID', False),
])
def test_validate_symbol(symbol, expected):
    """Test symbol validation."""
    result = validate_symbol(symbol)
    assert result == expected
```

### 4. Test Edge Cases

```python
def test_edge_cases():
    """Test edge cases."""
    # Empty input
    assert process([]) == []
    
    # None input
    assert process(None) is None
    
    # Large input
    assert len(process(range(10000))) == 10000
```

## 🔍 Coverage Analysis

### Generate Coverage Report

```bash
# Terminal report
pytest --cov=src --cov-report=term-missing

# HTML report
pytest --cov=src --cov-report=html
open htmlcov/index.html

# XML report (for CI)
pytest --cov=src --cov-report=xml
```

### Coverage Goals

| Module | Current | Target |
|--------|---------|--------|
| agents/ | ~20% | 80%+ |
| api_integrations/ | 0% | 70%+ |
| database/ | 80% | 90%+ |
| utils/ | 0% | 80%+ |
| **Overall** | **40%** | **80%+** |

### Improving Coverage

```bash
# Find uncovered lines
pytest --cov=src --cov-report=term-missing | grep "Missing"

# Focus on specific module
pytest --cov=src/agents --cov-report=term-missing

# Coverage threshold (fail if below)
pytest --cov=src --cov-fail-under=80
```

## 🏗️ Integration Testing

### Example Integration Test

```python
@pytest.mark.integration
class TestCompleteWorkflow:
    """Integration test for complete workflow."""

    @pytest.mark.asyncio
    async def test_market_to_content_flow(self):
        """Test data flows from market scan to content creation."""
        from src.orchestrator import AgentOrchestrator
        
        # Mock external dependencies
        with patch('src.api_integrations.exchange_api.ExchangeAPI.get_price_data',
                   AsyncMock(return_value={'price': 50000})):
            with patch('src.api_integrations.twitter_api.TwitterAPI.post_tweet',
                       AsyncMock(return_value={'id': '123'})):
                
                orchestrator = AgentOrchestrator()
                result = await orchestrator.run_phase_1_pipeline()
                
                # Verify complete flow
                assert result is not None
```

### Database Integration

```python
@pytest.mark.integration
def test_database_integration(in_memory_db):
    """Test database integration."""
    from src.database.models import MarketData, Insight
    
    db = in_memory_db
    
    # Insert market data
    data = MarketData(symbol='BTC', price=50000, volume=1000,
                      timestamp=datetime.now(tz=timezone.utc))
    db.add(data)
    db.commit()
    
    # Create insight from data
    insight = Insight(
        type='price_movement',
        content='BTC increased',
        confidence=0.8,
        market_data_id=data.id
    )
    db.add(insight)
    db.commit()
    
    # Verify relationship
    assert data.insights[0].content == 'BTC increased'
```

## ⚡ Performance Testing

### Benchmark Tests

```python
import time

@pytest.mark.slow
def test_agent_performance():
    """Test agent execution performance."""
    agent = MyAgent()
    
    start = time.time()
    result = agent.execute()
    duration = time.time() - start
    
    # Should complete in under 1 second
    assert duration < 1.0
    assert result is not None

@pytest.mark.slow
def test_database_query_performance(in_memory_db):
    """Test database query performance."""
    db = in_memory_db
    
    # Insert 1000 records
    for i in range(1000):
        db.add(MarketData(symbol=f'TEST{i}', price=float(i),
                          volume=1000, timestamp=datetime.now(tz=timezone.utc)))
    db.commit()
    
    # Measure query time
    start = time.time()
    results = db.query(MarketData).limit(100).all()
    duration = time.time() - start
    
    # Should be fast
    assert duration < 0.1
    assert len(results) == 100
```

### Load Testing

```python
import asyncio

@pytest.mark.slow
@pytest.mark.asyncio
async def test_concurrent_execution():
    """Test concurrent agent execution."""
    agents = [MyAgent() for _ in range(10)]
    
    start = time.time()
    results = await asyncio.gather(*[agent.run() for agent in agents])
    duration = time.time() - start
    
    # All should succeed
    assert len(results) == 10
    assert all(r is not None for r in results)
    
    # Should be faster than sequential (but not 10x faster due to I/O)
    print(f"Concurrent execution: {duration:.2f}s")
```

## 🐛 Debugging Tests

### Using pdb

```python
def test_with_debugger():
    """Test with debugger."""
    import pdb; pdb.set_trace()
    
    result = some_function()
    assert result is not None
```

### Print Debugging

```python
def test_with_prints(capsys):
    """Test with captured output."""
    print("Debug message")
    result = some_function()
    
    captured = capsys.readouterr()
    assert "Debug message" in captured.out
```

### Verbose Output

```bash
# Show print statements
pytest -v -s

# Show detailed error traces
pytest -vv --tb=long

# Stop on first failure
pytest -x

# Drop into debugger on failure
pytest --pdb
```

## 📊 CI/CD Testing

### GitHub Actions

```yaml
# .github/workflows/ci.yml
test:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v3
    - name: Run tests
      run: |
        pip install -r requirements-dev.txt
        pytest --cov=src --cov-report=xml
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
- repo: local
  hooks:
    - id: pytest
      name: pytest
      entry: pytest
      language: system
      pass_filenames: false
      always_run: true
```

## 🎓 Testing Cheat Sheet

### Common Commands

```bash
# Basic
pytest -v                          # Verbose output
pytest -q                          # Quiet output
pytest -x                          # Stop on first failure
pytest --lf                        # Run last failed tests
pytest --ff                        # Failed first, then others

# Coverage
pytest --cov=src                   # Coverage report
pytest --cov-report=html           # HTML coverage
pytest --cov-fail-under=80         # Fail if < 80%

# Markers
pytest -m asyncio                  # Async tests only
pytest -m "not slow"               # Skip slow tests
pytest -k "test_market"            # Run tests matching pattern

# Output
pytest -s                          # Show print statements
pytest --tb=short                  # Short traceback
pytest --tb=no                     # No traceback
pytest -vv                         # Very verbose

# Debugging
pytest --pdb                       # Debug on failure
pytest --pdb-trace                 # Debug all tests
pytest --maxfail=2                 # Stop after 2 failures
```

### Useful Fixtures

```python
# Database
in_memory_db                       # SQLite in-memory database

# Mocking
mocker                            # pytest-mock mocker
mock_settings                     # Mocked settings

# Custom
@pytest.fixture
def my_fixture():
    """Custom fixture."""
    return {"key": "value"}
```

## 📚 Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
- [unittest.mock](https://docs.python.org/3/library/unittest.mock.html)

## 🎯 Next Steps

1. **Increase coverage to 80%+**
   - Add tests for all agents
   - Test API integrations
   - Test orchestrator flows

2. **Add performance benchmarks**
   - Agent execution times
   - Database query performance
   - API response times

3. **Implement E2E tests**
   - Complete workflows
   - User journeys
   - Error scenarios

4. **Setup continuous testing**
   - Pre-commit hooks
   - GitHub Actions
   - Coverage tracking
