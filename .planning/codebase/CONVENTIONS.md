# Coding Conventions

**Analysis Date:** 2026-04-12

## Naming Patterns

**Files:**
- Python source files: `snake_case.py` (e.g., `currency.py`, `time_utils.py`)
- Test files: `test_<module_name>.py` (e.g., `test_currency.py`)
- Integration test files: `test_<feature>.py` in `tests/integration/`

**Classes:**
- PascalCase (e.g., `CurrencyConverter`, `ConfigManager`, `SessionData`)
- Test classes: `Test<ClassName>` (e.g., `TestCurrencyConverter`, `TestPathsConfig`)

**Functions/Methods:**
- snake_case (e.g., `get_exchange_rate`, `load_pricing_data`)
- Private methods: `_leading_underscore`

**Variables:**
- snake_case (e.g., `config_path`, `pricing_data`)
- Constants: SCREAMING_SNAKE_CASE (e.g., `WEEKDAY_MAP`, `WEEKDAY_NAMES`)

**Type Names:**
- PascalCase for Pydantic models (e.g., `ModelPricing`, `Config`)
- Type aliases use standard Python types

## Code Style

**Formatting:**
- No explicit formatter config found (ruff.toml, black config, .prettierrc all absent)
- Follow PEP 8 conventions observed in code
- 4-space indentation
- Maximum line length: not explicitly configured

**Change Discipline:**
- Automated reformatting tools (formatters, linters, AI assistants) may introduce unwanted syntax changes
- **Keep changes minimal** — never commit syntax-only changes (quote replacements, line endings, line widths, trailing whitespace, etc.)
- Before committing, review diffs and revert any non-functional formatting changes
- Exception: Explicit refactoring where formatting is the stated goal

**Linting:**
- No explicit linter config found
- `flake8` listed as dev dependency in `pyproject.toml`

**Import Organization:**
```
1. Standard library imports (os, json, pathlib, etc.)
2. Third-party imports (click, rich, pydantic, toml, etc.)
3. Local application imports (ocmonitor.*)
```

**Relative Imports:**
- Use `from ..module import ...` pattern for package-internal imports
- Example from `ocmonitor/services/report_generator.py`:
```python
from ..models.session import SessionData
from ..models.analytics import DailyUsage, WeeklyUsage, MonthlyUsage
from ..ui.tables import TableFormatter
from ..services.session_analyzer import SessionAnalyzer
```

**Module Imports in cli.py:**
```python
from .config import config_manager
from .services.export_service import ExportService
from .services.live_monitor import LiveMonitor
from .services.report_generator import ReportGenerator
from .services.session_analyzer import SessionAnalyzer
from .ui.theme import get_theme
from .utils.error_handling import (
    ErrorHandler,
    create_user_friendly_error,
    handle_errors,
)
from .version import get_version
```

## Error Handling

**Custom Exception Hierarchy** in `ocmonitor/utils/error_handling.py`:
```python
class OCMonitorError(Exception):
    """Base exception for OpenCode Monitor."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        ...

class ConfigurationError(OCMonitorError): ...
class DataProcessingError(OCMonitorError): ...
class FileSystemError(OCMonitorError): ...
class ValidationError(OCMonitorError): ...
class ExportError(OCMonitorError): ...
```

**ErrorHandler Class:**
- Centralized error handling via `ErrorHandler` class
- `handle_error()` returns structured error dict with `error_type`, `message`, `context`, `success`
- `safe_execute()` wraps function execution with error handling

**CLI Error Context Manager** in `ocmonitor/cli.py`:
```python
@contextmanager
def cli_error_context(ctx: click.Context, operation_name: str):
    """Context manager for consistent CLI error handling."""
    try:
        yield
    except click.exceptions.Exit:
        raise
    except Exception as e:
        error_msg = create_user_friendly_error(e)
        click.echo(f"Error {operation_name}: {error_msg}", err=True)
        if ctx.obj.get("verbose"):
            click.echo(f"Details: {str(e)}", err=True)
        ctx.exit(1)
```

**User-Friendly Error Messages:**
- `create_user_friendly_error()` converts exceptions to user-facing messages
- Wraps common exceptions (FileNotFoundError, PermissionError, etc.)

**Validation with Pydantic:**
- Configuration uses Pydantic models with `Field()` validators
- `field_validator` decorators for custom validation (e.g., path expansion)
- Pattern matching with regex for constrained strings (e.g., `pattern="^(rich|simple|minimal)$"`)

## Logging

**Framework:** Python standard `logging` module

**Pattern:**
```python
import logging
logger = logging.getLogger(__name__)
```

**Usage in `ocmonitor/services/metrics_server.py`:**
```python
logger = logging.getLogger(__name__)
...
logger.warning("Failed to collect metrics", exc_info=True)
```

**Usage in `ocmonitor/utils/error_handling.py`:**
```python
logger = logging.getLogger(__name__)
logger.error(f"Error in {context}: {error_info['error_type']}: {error_info['message']}")
if self.verbose:
    logger.debug(f"Traceback: {error_info.get('traceback', 'N/A')}")
```

**Test Logging:**
- Tests in `test_live_monitor.py` use `caplog` fixture with `caplog.set_level(logging.INFO)`

## Documentation

**Module Docstrings:**
- Triple quotes with module purpose description
- Example: `"""Configuration management for OpenCode Monitor."""`

**Class Docstrings:**
- Brief description of class purpose
- Args, Returns, Raises sections for complex methods

**Function Docstrings:**
- Args section for parameters
- Returns section for return values
- Used extensively in config.py and error_handling.py

**Test Docstrings:**
- Descriptive test purpose in docstrings
- Example: `"""Test that lowercase currency codes are normalized to uppercase."""`

## Function Design

**Parameters:**
- Use type hints throughout (e.g., `path: Optional[str]`, `config_path: str`)
- Default values for optional parameters
- Docstrings for complex parameter logic

**Return Values:**
- Return `None` for operations that may fail gracefully
- Return `Optional[T]` when result may be absent
- Return `Dict[str, Any]` for structured results
- Pydantic models for typed configuration returns

**Size Guidelines:**
- Functions typically under 100 lines
- Complex CLI commands use helper functions (e.g., `_determine_monitoring_source`, `_prompt_workflow_selection`)

---

*Convention analysis: 2026-04-12*
