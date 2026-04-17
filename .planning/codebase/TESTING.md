# Testing Patterns

**Analysis Date:** 2026-04-12

## Test Framework

**Runner:**
- **pytest** [Version 7.0.0+]
- Configured in `pyproject.toml` under `[tool.pytest.ini_options]`

**Assertion Library:**
- pytest built-in assertions
- `pytest.raises()` for exception testing
- `pytest.warns()` for warning testing

**Optional Test Dependencies:**
- `pytest-click>=1.1.0` - For Click CLI testing
- `pytest-mock>=3.10.0` - For mocking
- `coverage>=7.0.0` - For coverage reporting

**Run Commands:**
```bash
pytest                          # Run all tests
pytest -v                      # Verbose output
pytest tests/unit/             # Run unit tests only
pytest tests/integration/      # Run integration tests only
pytest -m unit                 # Run by marker (unit)
pytest -m integration          # Run by marker (integration)
pytest --co                    # Collect tests without running
```

## Test File Organization

**Location:**
- `tests/unit/` - Unit tests
- `tests/integration/` - Integration tests
- `tests/conftest.py` - Shared fixtures

**Naming:**
- Pattern: `test_*.py`
- Examples: `test_currency.py`, `test_config.py`, `test_cli.py`

**Structure:**
```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures
├── unit/
│   ├── __init__.py
│   ├── test_currency.py
│   ├── test_config.py
│   ├── test_models.py
│   ├── test_time_utils.py
│   └── ...
└── integration/
    ├── __init__.py
    └── test_cli.py
```

## Test Structure

**Class-Based Organization:**
```python
class TestCurrencyConverter:
    """Tests for CurrencyConverter."""

    def test_default_format_matches_usd(self):
        converter = CurrencyConverter()
        assert converter.format(Decimal("1.23")) == "$1.23"
```

**Function-Based Organization:**
```python
def test_weekday_map_values(self):
    """Test that WEEKDAY_MAP has correct values."""
    assert WEEKDAY_MAP['monday'] == 0
```

## Pytest Configuration

**From `pyproject.toml`:**
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "-v --tb=short"
markers = [
    "unit: Unit tests",
    "integration: Integration tests",
    "slow: Slow tests",
]
```

## Fixtures

**Location:** `tests/conftest.py`

**Key Fixtures:**

```python
@pytest.fixture
def temp_directory():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_config_file(temp_directory):
    """Create a sample configuration file."""
    # Creates config.toml in temp directory

@pytest.fixture
def sample_models_file(temp_directory):
    """Create a sample models.json file."""
    # Creates models.json with test pricing data

@pytest.fixture
def sample_session_json():
    """Return sample session JSON data."""
    return {
        "modelID": "test-model",
        "tokens": {...},
        "timeData": {...},
        ...
    }

@pytest.fixture
def mock_session_directory(temp_directory):
    """Create a mock session directory structure."""
    # Creates session dirs with interaction JSON files
```

**Integration Test Fixtures** (in `tests/integration/test_cli.py`):
```python
@pytest.fixture
def mock_sessions_dir(tmp_path):
    """Create a mock sessions directory with test data."""
    sessions_dir = tmp_path / "message"
    sessions_dir.mkdir()
    # Creates session dirs and interaction files
    return sessions_dir
```

## Mocking

**Framework:** `unittest.mock` (standard library)

**Common Patterns:**

```python
# Patch a method
from unittest.mock import patch

with patch("ocmonitor.services.live_monitor.LiveMonitor.validate_monitoring_setup",
           return_value={"valid": True, "issues": [], "warnings": []}):
    result = runner.invoke(cli, ["live", str(mock_sessions_dir)])

# Mock with assert
with patch('ocmonitor.services.price_fetcher.get_remote_payload') as mock_get:
    mock_get.return_value = {"providers": {}}
    pricing = manager.load_pricing_data(no_remote=True)
    mock_get.assert_not_called()

# Reset mock
mock_get.reset_mock()
```

**MagicMock for Objects:**
```python
from unittest.mock import MagicMock

instance = MockServer.return_value
instance.start.side_effect = KeyboardInterrupt
```

## Test Data Management

**Inline Test Data:**
- Small test data defined directly in test functions
- Example: `pricing_data` fixture with ModelPricing objects

**JSON Test Data:**
- Created as temp files with `tmp_path` fixture
- Written with `json.dumps()` and read with `json.loads()`

**Session Data Pattern:**
```python
session_dir = temp_directory / "ses_test123"
session_dir.mkdir()

interaction = session_dir / "inter_0001.json"
interaction.write_text(json.dumps({
    "modelID": "test-model",
    "tokens": {"input": 1000, "output": 500, ...},
    ...
}))
```

**Decimal Usage:**
```python
from decimal import Decimal

pricing = ModelPricing(
    input=Decimal("1.0"),
    output=Decimal("2.0"),
    ...
)
```

## Coverage

**Tool:** `coverage` (via `coverage>=7.0.0`)

**Measurement:**
- No explicit coverage target configured
- Coverage can be run with: `coverage run -m pytest`

## Test Types

**Unit Tests:**
- Test individual classes/functions in isolation
- Located in `tests/unit/`
- Use mocked dependencies
- Fast execution

**Integration Tests:**
- Test CLI commands end-to-end
- Located in `tests/integration/`
- Use `CliRunner` from `click`
- Example: `TestSessionsCommand`, `TestDailyCommand`

**CLI Testing Pattern:**
```python
from click.testing import CliRunner

def test_sessions_basic(self, mock_sessions_dir):
    """Test basic sessions command."""
    runner = CliRunner()
    result = runner.invoke(cli, ['sessions', str(mock_sessions_dir)])
    assert result.exit_code == 0
```

## Common Patterns

**Testing Exceptions:**
```python
def test_invalid_table_style(self):
    """Test that invalid table styles are rejected."""
    with pytest.raises(ValueError):
        UIConfig(table_style="invalid")
```

**Testing Warnings:**
```python
def test_invalid_remote_entries_are_skipped_not_fatal(self, tmp_path):
    """Test that invalid pricing entries are skipped with warning."""
    with pytest.warns(UserWarning, match="Skipping invalid pricing data"):
        pricing = manager.load_pricing_data()
```

**Testing Environment Variables:**
```python
def test_xdg_data_home_respected(self, monkeypatch):
    """Test that XDG_DATA_HOME environment variable is respected."""
    monkeypatch.setenv("XDG_DATA_HOME", "/custom/data")
    path = opencode_storage_path()
    assert path.startswith("/custom/data")
```

**Testing File Path Expansion:**
```python
def test_path_expansion(self):
    """Test that user paths are expanded."""
    config = PathsConfig(messages_dir="~/test/messages")
    assert not config.messages_dir.startswith("~")
    assert config.messages_dir.endswith("test/messages")
```

**Testing Pydantic Validation:**
```python
def test_live_refresh_interval_bounds(self):
    """Test live refresh interval boundary values."""
    config = UIConfig(live_refresh_interval=1)
    assert config.live_refresh_interval == 1
    
    with pytest.raises(ValueError):
        UIConfig(live_refresh_interval=0)
```

**Testing JSON Output:**
```python
def test_daily_json_includes_filter(self, mock_sessions_dir):
    """Test daily JSON output includes filter metadata."""
    runner = CliRunner()
    result = runner.invoke(cli, ['daily', str(mock_sessions_dir), '--format', 'json'])
    
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data['type'] == 'daily_breakdown'
    assert data['filter'] == {'year': 2024}
```

## Test Markers

**Defined Markers:**
- `unit` - Unit tests
- `integration` - Integration tests
- `slow` - Slow tests

**Usage:**
```bash
pytest -m unit              # Run only unit tests
pytest -m "not slow"        # Skip slow tests
```

---

*Testing analysis: 2026-04-12*
