# Architecture

**Analysis Date:** 2026-04-12

## Pattern Overview

**Overall:** Service-oriented CLI architecture with layered separation of concerns

**Key Characteristics:**
- CLI commands delegate to service classes that encapsulate business logic
- Data access abstracted through loader classes (SQLite preferred, files fallback)
- Pydantic models provide validation and computed properties throughout
- Rich library used for terminal UI rendering with themed components
- Currency conversion layer allows multi-currency cost display

## Layers

**CLI Layer:**
- Purpose: Command-line interface entry point and command registration
- Location: `ocmonitor/cli.py`
- Contains: Click command group, subcommands (`session`, `sessions`, `live`, `daily`, `weekly`, `monthly`, `model`, `models`, `projects`, `export`, `config`, `metrics`, `agents`), context management
- Depends on: All services, config, Rich console
- Used by: User via terminal

**Configuration Layer:**
- Purpose: Centralized configuration management with TOML file loading
- Location: `ocmonitor/config.py`
- Contains: `ConfigManager` singleton, Pydantic config models (`Config`, `PathsConfig`, `UIConfig`, `ExportConfig`, `ModelsConfig`, `AnalyticsConfig`, `MetricsConfig`, `CurrencyConfig`)
- Depends on: TOML files, environment variables
- Used by: CLI initialization, all services

**Service Layer:**
- Purpose: Business logic encapsulation
- Location: `ocmonitor/services/`
- Contains:
  - `SessionAnalyzer`: Session analysis, filtering, statistics calculation
  - `ReportGenerator`: Report generation in multiple formats (table/JSON/CSV)
  - `LiveMonitor`: Real-time dashboard with Rich Live widgets
  - `ExportService`: File export handling
  - `AgentRegistry`: Agent type detection
  - `SessionGrouper`: Groups sessions by workflow
  - `PriceFetcher`: Remote pricing API fetching
  - `RateFetcher`: FX rate fetching
  - `MetricsServer`: Prometheus metrics endpoint
- Depends on: Models, utils, pricing data
- Used by: CLI commands

**Data Access Layer:**
- Purpose: Data loading abstraction with dual-source support
- Location: `ocmonitor/utils/data_loader.py`, `ocmonitor/utils/sqlite_utils.py`, `ocmonitor/utils/file_utils.py`
- Contains: `DataLoader` class (SQLite preferred, files fallback), `SQLiteProcessor`, `FileProcessor`
- Depends on: OpenCode storage (SQLite DB or message files)
- Used by: SessionAnalyzer, LiveMonitor

**Model Layer:**
- Purpose: Data structures with validation and computed properties
- Location: `ocmonitor/models/`
- Contains:
  - `session.py`: `SessionData`, `InteractionFile`, `TokenUsage`, `TimeData`
  - `analytics.py`: `DailyUsage`, `WeeklyUsage`, `MonthlyUsage`, `ModelUsageStats`, `ModelBreakdownReport`, `ModelDetailStats`, `ProjectUsageStats`, `ProjectBreakdownReport`, `TimeframeAnalyzer`
  - `tool_usage.py`: `ToolUsageStats`, `ModelToolUsage`, `ToolUsageSummary`
  - `workflow.py`: `SessionWorkflow`
- Depends on: Pydantic
- Used by: All layers

**UI Layer:**
- Purpose: Terminal rendering components
- Location: `ocmonitor/ui/`
- Contains: `DashboardUI` (live dashboard panels), `TableFormatter` (table generation), `Theme` (Rich theme definition)
- Depends on: Rich library
- Used by: ReportGenerator, LiveMonitor

**Utility Layer:**
- Purpose: Shared helper functions
- Location: `ocmonitor/utils/`
- Contains: `data_loader.py`, `sqlite_utils.py`, `file_utils.py`, `time_utils.py`, `currency.py`, `formatting.py`, `error_handling.py`
- Depends on: Various external libraries
- Used by: All layers

## Data Flow

**Typical CLI Command Flow:**

1. CLI command invoked with arguments
2. `cli_error_context` wraps execution for consistent error handling
3. Context object contains initialized services from `cli()` group handler
4. Command delegates to `SessionAnalyzer` for data loading
5. `SessionAnalyzer` uses `DataLoader` to fetch sessions (SQLite or files)
6. Analysis methods filter/group sessions and compute statistics
7. `ReportGenerator` formats results (table/JSON/CSV)
8. Rich console outputs formatted result

**Live Monitoring Flow:**

1. `live` command initializes `LiveMonitor` with pricing data and config
2. `DataLoader` detects available data source
3. Active workflows loaded and most recent selected
4. Rich `Live` widget starts with dashboard layout
5. Polling loop refreshes workflow data at configured interval
6. Dashboard layout regenerated on each refresh
7. Interactive workflow switching via keyboard input

**Configuration Loading Flow:**

1. `ConfigManager` singleton initialized
2. Searches for config in standard locations (user config → project config → package fallback)
3. TOML file parsed into Pydantic models
4. Pricing data loaded from multiple sources with merge precedence: user file > local file > remote fallback
5. Currency converter initialized with configured rate

## Key Abstractions

**DataLoader:**
- Purpose: Unified interface for session data regardless of storage backend
- Examples: `ocmonitor/utils/data_loader.py`
- Pattern: Strategy pattern with SQLite-first preference and file-based fallback

**SessionAnalyzer:**
- Purpose: Core business logic for session analysis
- Examples: `ocmonitor/services/session_analyzer.py`
- Pattern: Service class encapsulating all analysis operations

**ReportGenerator:**
- Purpose: Format-agnostic report generation
- Examples: `ocmonitor/services/report_generator.py`
- Pattern: Template method pattern - same data rendered differently per format

**DashboardUI:**
- Purpose: Reusable dashboard components
- Examples: `ocmonitor/ui/dashboard.py`
- Pattern: Builder pattern for constructing Rich layouts

**SessionWorkflow:**
- Purpose: Groups main session with sub-agent sessions
- Examples: `ocmonitor/models/workflow.py`
- Pattern: Composite pattern - single interface for workflow/session

**ConfigManager:**
- Purpose: Singleton managing application configuration
- Examples: `ocmonitor/config.py`
- Pattern: Singleton pattern with lazy loading

## Entry Points

**CLI Entry Point:**
- Location: `ocmonitor/cli.py::main()`
- Triggers: User runs `ocmonitor` command
- Responsibilities: Initialize Click group, load config, setup context, route commands

**Alternative Entry Point:**
- Location: `run_ocmonitor.py`
- Triggers: Python script execution
- Responsibilities: Development/debugging entry point

## Error Handling

**Strategy:** Centralized error handling with user-friendly messages

**Patterns:**
- `cli_error_context`: Context manager for consistent CLI error formatting
- `create_user_friendly_error`: Transforms exceptions into readable messages
- `ErrorHandler`: Class for error tracking and reporting
- Graceful degradation: Remote fetch failures don't crash, use cached/local-only data

## Cross-Cutting Concerns

**Logging:** Uses Rich console with styled output tags instead of traditional logging

**Validation:** Pydantic models enforce types and constraints at all data boundaries

**Authentication:** Not applicable (local-only data access)

**Currency:** `CurrencyConverter` class handles multi-currency display with configured rates and symbols

---

*Architecture analysis: 2026-04-12*
