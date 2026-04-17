# Technology Stack

**Analysis Date:** 2026-04-12

## Languages

**Primary:**
- Python 3.8+ (minimum), 3.11 (primary target for Docker)

## Runtime

**Environment:**
- Python standard library with pip for package management
- Docker container using `python:3.11-slim`

**Package Manager:**
- pip (via requirements.txt/pyproject.toml)
- Lockfile: `requirements.txt` present

## Frameworks & CLI

**CLI Framework:**
- Click >=8.0.0 - Command-line interface framework

**UI Rendering:**
- Rich >=13.0.0 - Rich text and beautiful formatting in terminal

**Data Validation:**
- Pydantic >=2.0.0 - Data validation using Python type hints

## Data Handling

**Configuration:**
- toml >=0.10.0 - TOML configuration file parsing
- PyYAML >=6.0 - YAML file parsing (for OpenCode message files)

**Database:**
- sqlite3 (stdlib) - Local SQLite database for OpenCode session data
- JSON files for message storage and pricing data

**Charting (optional):**
- plotly >=5.18.0 - Interactive visualizations
- plotly-calplot >=0.1.20 - Calendar heatmaps for plotly

**Export (optional):**
- jinja2 >=3.1.0 - Template engine for report generation
- pandas >=2.0.0 - Data manipulation for exports

## Monitoring & Metrics

**Prometheus:**
- prometheus_client >=0.17.0 - Prometheus metrics exposition

## Testing

**Test Framework:**
- pytest >=7.0.0 - Testing framework
- pytest-click >=1.1.0 - Click CLI testing utilities
- pytest-mock >=3.10.0 - Mocking utilities
- coverage >=7.0.0 - Code coverage measurement

**Code Quality:**
- black >=22.0.0 - Code formatting
- isort >=5.10.0 - Import sorting
- flake8 >=4.0.0 - Linting

## Configuration Files

- `pyproject.toml` - Project metadata and dependencies
- `setup.py` - Legacy setup script (reads version from `__init__.py`)
- `requirements.txt` - Pinned dependency versions
- `Dockerfile` - Python 3.11 slim container
- `docker-compose.yml` - Service orchestration with volume mounts

## Key Application Structure

```
ocmonitor/
├── cli.py              # Main CLI entry point
├── config.py           # Configuration management via ConfigManager
├── models/
│   ├── analytics.py    # Analytics data models
│   ├── session.py      # Session data models
│   └── workflow.py     # Workflow models
├── services/
│   ├── live_monitor.py      # Live monitoring with progress tracking
│   ├── metrics_server.py    # Prometheus metrics HTTP server
│   ├── price_fetcher.py     # models.dev API client
│   ├── rate_fetcher.py      # frankfurter.dev API client
│   ├── report_generator.py  # Report generation
│   ├── session_analyzer.py  # Session analysis
│   └── export_service.py     # CSV/JSON export
├── ui/
│   ├── dashboard.py   # Rich-based dashboard rendering
│   ├── tables.py      # Rich table rendering
│   └── theme.py       # UI theme configuration
└── utils/
    ├── sqlite_utils.py    # SQLite database operations
    ├── data_loader.py    # Data loading with source detection
    ├── file_utils.py      # File system utilities
    └── time_utils.py      # Time/date utilities
```

## Environment Variables (Configuration-Driven)

- `XDG_DATA_HOME` - Base for OpenCode storage path (default: `~/.local/share`)
- `XDG_CACHE_HOME` - Base for cache files (default: `~/.cache`)
- OpenCode data directory: `~/.local/share/opencode/storage/`
- OpenCode database: `~/.local/share/opencode/opencode.db`

---

*Stack analysis: 2026-04-12*