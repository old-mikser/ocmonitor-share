# Codebase Structure

**Analysis Date:** 2026-04-12

## Directory Layout

```
ocmonitor-share/
├── ocmonitor/              # Main package
│   ├── __init__.py        # Package init with version info
│   ├── cli.py             # CLI entry point (Click commands)
│   ├── config.py          # Configuration management
│   ├── config.toml        # Default config file
│   ├── models.json        # Default model pricing data
│   ├── version.py         # Version utilities
│   ├── models/            # Data models
│   ├── services/           # Business logic services
│   ├── ui/                # UI components
│   └── utils/             # Utility functions
├── tests/                 # Test suite
│   ├── unit/              # Unit tests
│   └── integration/       # Integration tests
├── .planning/             # Planning documents (this directory)
├── pyproject.toml         # Package configuration
├── requirements.txt       # Dependencies
├── Dockerfile            # Container definition
├── docker-compose.yml     # Docker composition
├── run_ocmonitor.py       # Alternative entry point
└── exports/               # Default export output directory
```

## Directory Purposes

**`ocmonitor/`:**
- Purpose: Main package containing all application code
- Contains: Python modules for CLI, config, models, services, UI, utils
- Key files: `cli.py` (entry point), `config.py` (configuration)

**`ocmonitor/models/`:**
- Purpose: Pydantic data models for validation and structure
- Contains:
  - `__init__.py`: Package marker
  - `session.py`: `SessionData`, `InteractionFile`, `TokenUsage`, `TimeData`
  - `analytics.py`: `DailyUsage`, `WeeklyUsage`, `MonthlyUsage`, `TimeframeAnalyzer`, stats models
  - `tool_usage.py`: `ToolUsageStats`, `ModelToolUsage`, `ToolUsageSummary`
  - `workflow.py`: `SessionWorkflow`

**`ocmonitor/services/`:**
- Purpose: Business logic service classes
- Contains:
  - `__init__.py`: Package marker
  - `session_analyzer.py`: `SessionAnalyzer` - core session analysis
  - `report_generator.py`: `ReportGenerator` - report formatting
  - `live_monitor.py`: `LiveMonitor` - real-time dashboard
  - `export_service.py`: `ExportService` - file export
  - `session_grouper.py`: `SessionGrouper` - workflow grouping
  - `agent_registry.py`: `AgentRegistry` - agent detection
  - `price_fetcher.py`: Remote pricing API
  - `rate_fetcher.py`: FX rate fetching
  - `metrics_server.py`: Prometheus endpoint

**`ocmonitor/ui/`:**
- Purpose: Terminal UI rendering components
- Contains:
  - `__init__.py`: Package marker
  - `dashboard.py`: `DashboardUI` - live dashboard panels
  - `tables.py`: `TableFormatter` - table formatting
  - `theme.py`: Rich theme definition

**`ocmonitor/utils/`:**
- Purpose: Shared utility functions
- Contains:
  - `__init__.py`: Package marker
  - `data_loader.py`: `DataLoader` - unified data loading (SQLite/files)
  - `sqlite_utils.py`: `SQLiteProcessor` - SQLite-specific queries
  - `file_utils.py`: `FileProcessor` - file-based session loading
  - `time_utils.py`: `TimeUtils` - date/time utilities
  - `currency.py`: `CurrencyConverter` - currency formatting
  - `formatting.py`: `ColorFormatter` - color utilities
  - `error_handling.py`: `ErrorHandler`, error utilities
  - `sqlite_utils.py`: SQLite operations

**`tests/`:**
- Purpose: Test suite
- Contains:
  - `__init__.py`: Test package markers
  - `unit/`: Unit tests
  - `integration/`: Integration tests

## Key File Locations

**Entry Points:**
- `ocmonitor/cli.py`: Main CLI entry via Click group
- `run_ocmonitor.py`: Alternative development entry point

**Configuration:**
- `ocmonitor/config.toml`: Default configuration
- `ocmonitor/config.py`: Configuration management classes
- `ocmonitor/models.json`: Default model pricing data

**Core Logic:**
- `ocmonitor/services/session_analyzer.py`: Session analysis logic
- `ocmonitor/services/report_generator.py`: Report generation
- `ocmonitor/services/live_monitor.py`: Live dashboard
- `ocmonitor/utils/data_loader.py`: Data loading abstraction

**Data Models:**
- `ocmonitor/models/session.py`: Core session models
- `ocmonitor/models/analytics.py`: Analytics models
- `ocmonitor/models/workflow.py`: Workflow model

**UI:**
- `ocmonitor/ui/dashboard.py`: Dashboard components
- `ocmonitor/ui/tables.py`: Table formatting
- `ocmonitor/ui/theme.py`: Theme definition

## Naming Conventions

**Files:**
- PascalCase: Model files (`SessionData`, `Analytics`)
- snake_case: Service and utility files (`session_analyzer`, `data_loader`)
- Single purpose per file

**Directories:**
- snake_case: All package directories
- Descriptive names indicating contained functionality

**Classes:**
- PascalCase: All class names (`SessionAnalyzer`, `DashboardUI`)
- Suffix pattern: `Analyzer` (analysis), `Generator` (generation), `Processor` (data ops), `Formatter` (formatting), `Converter` (conversion)

**Functions/Methods:**
- snake_case: All function and method names
- Verb pattern: `analyze_*`, `generate_*`, `create_*`, `calculate_*`, `format_*`, `load_*`, `get_*`

## Where to Add New Code

**New CLI Command:**
- Add command function to `ocmonitor/cli.py` using `@cli.command()` decorator
- Use `cli_error_context` for consistent error handling
- Access services from `ctx.obj` (initialized in `cli()`)

**New Service:**
- Create file in `ocmonitor/services/` (e.g., `new_service.py`)
- Define service class with clear responsibilities
- Add imports in `ocmonitor/services/__init__.py` if needed

**New Data Model:**
- Create file in `ocmonitor/models/` (e.g., `new_model.py`)
- Extend Pydantic `BaseModel` for validation
- Add computed properties with `@computed_field`
- Import in `ocmonitor/models/__init__.py`

**New UI Component:**
- Create file in `ocmonitor/ui/` (e.g., `new_component.py`)
- Use Rich components for terminal output
- Follow `DashboardUI` patterns for consistency

**New Utility:**
- Create file in `ocmonitor/utils/` (e.g., `new_util.py`)
- Keep functions pure and independent where possible
- Import in `ocmonitor/utils/__init__.py` if needed

## Special Directories

**`exports/`:**
- Purpose: Default directory for exported CSV/JSON files
- Generated: No (user-created or auto-created on export)
- Committed: Yes (in git, empty initially)

**`build/`:**
- Purpose: Python package build artifacts
- Generated: Yes (by build tools)
- Committed: No (in .gitignore)

**`ocmonitor.egg-info/`:**
- Purpose: Package metadata
- Generated: Yes (by setuptools)
- Committed: No (in .gitignore)

**`__pycache__/`:**
- Purpose: Python bytecode cache
- Generated: Yes (by Python interpreter)
- Committed: No (in .gitignore)

---

*Structure analysis: 2026-04-12*
