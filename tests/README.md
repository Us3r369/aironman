# AIronman Testing Suite

This directory contains comprehensive unit tests and integration tests for the AIronman application.

## Test Structure

```
tests/
├── __init__.py
├── test_api.py              # API endpoint tests
├── test_database.py         # Database utility tests
├── test_preprocess.py       # Data preprocessing tests
├── test_profile_active.py   # Profile management tests
├── test_recovery_agent.py   # Recovery analysis agent tests
├── test_services.py         # Service layer tests
└── README.md               # This file
```

## Test Categories

### 1. Unit Tests (`test_*.py`)
- **Agent Tests** (`test_recovery_agent.py`): Test the CrewAI recovery analysis agent and its tools
- **API Tests** (`test_api.py`): Test FastAPI endpoints using TestClient
- **Database Tests** (`test_database.py`): Test database utilities and connection handling
- **Service Tests** (`test_services.py`): Test service layer functions (PMC, zones, sync, etc.)
- **Preprocess Tests** (`test_preprocess.py`): Test data preprocessing functions

### 2. Integration Tests
- End-to-end API testing
- Database integration testing
- Agent execution testing

## Running Tests

### Quick Start
```bash
# Run all tests
python run_tests.py

# Run specific test categories
python run_tests.py --mode unit
python run_tests.py --mode agent
python run_tests.py --mode api
python run_tests.py --mode database
python run_tests.py --mode coverage
```

### Using pytest directly
```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_recovery_agent.py

# Run with coverage
pytest --cov=api --cov=services --cov=utils --cov=agents tests/

# Run with verbose output
pytest -v tests/

# Run specific test class
pytest tests/test_recovery_agent.py::TestHealthMetricsTool
```

### Test Modes
- `--mode unit`: Run unit tests only
- `--mode integration`: Run integration tests only
- `--mode agent`: Run agent-specific tests
- `--mode api`: Run API endpoint tests
- `--mode database`: Run database tests
- `--mode coverage`: Run tests with coverage reporting
- `--mode lint`: Run code quality checks
- `--mode all`: Run all tests and checks (default)

## Test Coverage

The test suite aims for **80%+ coverage** across all modules:
- `api/`: FastAPI endpoints and request/response handling
- `services/`: Business logic and external service integration
- `utils/`: Utility functions and database connections
- `agents/`: CrewAI agent and tool implementations

## Pre-commit Hooks

### Setup
```bash
# Install pre-commit hooks
python run_tests.py --setup-pre-commit

# Or manually
pip install pre-commit
pre-commit install
```

### What runs on commit:
1. **Code formatting** (Black)
2. **Import sorting** (isort)
3. **Linting** (flake8)
4. **Security checks** (bandit)
5. **Unit tests** (pytest)

### What runs on push:
1. **Coverage tests** (pytest with coverage)
2. **Integration tests**

## Test Dependencies

Install test dependencies:
```bash
pip install -r requirements-test.txt
```

## Key Test Features

### 1. Mocking Strategy
- **Database connections**: Mocked to avoid real database calls
- **External APIs**: Mocked to avoid network dependencies
- **File operations**: Mocked for FIT file processing

### 2. Test Data
- **Mock workout data**: Realistic workout structures
- **Mock health metrics**: RHR, HRV, sleep data
- **Mock agent responses**: CrewAI output simulation

### 3. Error Handling
- **Database errors**: Connection failures, query errors
- **API errors**: Network timeouts, invalid responses
- **Validation errors**: Invalid input data

## Test Examples

### Agent Tests
```python
def test_health_metrics_tool_success(self):
    """Test successful health metrics extraction."""
    # Mock database connection
    # Mock health data
    # Verify tool output
```

### API Tests
```python
def test_get_health_analysis_success(self):
    """Test successful health analysis retrieval."""
    # Mock profile data
    # Mock database responses
    # Verify API response
```

### Database Tests
```python
def test_get_active_profile_success(self):
    """Test successful profile retrieval."""
    # Mock database connection
    # Mock profile data
    # Verify profile structure
```

## Continuous Integration

### GitHub Actions (Recommended)
```yaml
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
          python-version: 3.9
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-test.txt
      - name: Run tests
        run: python run_tests.py --mode all
```

### Local Development
```bash
# Run tests before committing
python run_tests.py --mode all

# Run specific tests during development
python run_tests.py --mode agent

# Check code quality
python run_tests.py --mode lint
```

## Troubleshooting

### Common Issues

1. **Import errors**: Ensure all dependencies are installed
   ```bash
   pip install -r requirements-test.txt
   ```

2. **Database connection errors**: Tests use mocked connections
   ```python
   @patch('utils.database.get_db_conn')
   def test_function(self, mock_get_db_conn):
       # Mock database responses
   ```

3. **Agent execution errors**: Agent tests are mocked
   ```python
   @patch('agents.recovery_analysis_agent.get_db_conn')
   def test_agent(self, mock_get_db_conn):
       # Mock agent data
   ```

### Debugging Tests
```bash
# Run with verbose output
pytest -v -s tests/

# Run specific test with debug
pytest -v -s tests/test_recovery_agent.py::TestHealthMetricsTool::test_health_metrics_tool_success

# Run with coverage and see missing lines
pytest --cov=agents --cov-report=term-missing tests/test_recovery_agent.py
```

## Best Practices

1. **Test isolation**: Each test should be independent
2. **Mock external dependencies**: Don't rely on real databases/APIs
3. **Comprehensive coverage**: Test success and failure cases
4. **Clear test names**: Use descriptive test method names
5. **Documentation**: Add docstrings to test classes and methods

## Adding New Tests

### For new API endpoints:
1. Add test to `test_api.py`
2. Mock database connections
3. Test success and error cases
4. Verify response structure

### For new services:
1. Add test to `test_services.py`
2. Mock external dependencies
3. Test business logic
4. Verify return values

### For new agents:
1. Add test to `test_recovery_agent.py`
2. Mock CrewAI components
3. Test tool functionality
4. Verify agent reasoning

## Coverage Reports

After running tests with coverage:
- **HTML report**: `htmlcov/index.html`
- **Terminal report**: Shows missing lines
- **XML report**: For CI integration

```bash
# Generate coverage report
pytest --cov=api --cov=services --cov=utils --cov=agents --cov-report=html tests/

# View HTML report
open htmlcov/index.html
``` 