# External Integrations

**Analysis Date:** 2026-04-12

## APIs & External Services

### Model Pricing API

**Service:** models.dev
- **Purpose:** Fetch remote model pricing data as fallback when local pricing is unavailable
- **Endpoint:** `https://models.dev/api.json`
- **Auth:** None required (public API)
- **Client:** Custom urllib-based HTTP client in `ocmonitor/services/price_fetcher.py`
  - Uses `urllib.request.urlopen` with `Request` objects
  - User-Agent: `ocmonitor/1.0`
- **Data Flow:** Response cached locally with TTL (default 24 hours), stale fallback on fetch failure

### Currency Exchange API

**Service:** frankfurter.dev
- **Purpose:** Fetch live exchange rates for non-USD currency display
- **Endpoint:** `https://api.frankfurter.dev/v1/latest?base=USD`
- **Auth:** None required (public API)
- **Client:** Custom urllib-based HTTP client in `ocmonitor/services/rate_fetcher.py`
  - Uses `urllib.request.urlopen` with `Request` objects
  - User-Agent: `ocmonitor/1.0`
- **Data Flow:** Response cached locally with TTL (default 24 hours), stale fallback on fetch failure

## Data Storage

### OpenCode SQLite Database

**Location:** `~/.local/share/opencode/opencode.db`
- **Format:** SQLite3 (accessed via `ocmonitor/utils/sqlite_utils.py`)
- **Purpose:** Primary session data storage for OpenCode v1.2.0+
- **Access Pattern:** 
  - Direct sqlite3 connection with `check_same_thread=False`
  - Row factory for dict-like access
  - Placeholder paths used in some session records

### OpenCode Message Files (Legacy)

**Location:** `~/.local/share/opencode/storage/message/`
- **Format:** JSON files per message
- **Purpose:** Legacy session data for OpenCode versions <1.2.0
- **Access Pattern:** File-based reading via `FileProcessor` in `ocmonitor/utils/file_utils.py`

## Prometheus Metrics

**Endpoint:** `http://{host}:{port}/metrics`
- **Default:** `0.0.0.0:9090`
- **Purpose:** Expose metrics for Prometheus scraping
- **Implementation:** `prometheus_client` library in `ocmonitor/services/metrics_server.py`
- **Metrics Exposed:**
  - `ocmonitor_tokens_input_total` (label: model)
  - `ocmonitor_tokens_output_total` (label: model)
  - `ocmonitor_tokens_cache_read_total` (label: model)
  - `ocmonitor_tokens_cache_write_total` (label: model)
  - `ocmonitor_cost_dollars_total` (label: model)
  - `ocmonitor_sessions_total` (label: model)
  - `ocmonitor_interactions_total` (label: model)
  - `ocmonitor_output_rate_tokens_per_second` (label: model)
  - `ocmonitor_session_duration_hours_total` (no label)
  - `ocmonitor_sessions_by_project` (label: project)

## File System Integrations

### OpenCode Storage Directory

**Purpose:** Read OpenCode session data (both SQLite and legacy files)
- **Configured via:** `paths.opencode_storage_dir` in config
- **Default:** `~/.local/share/opencode/storage/`

### ocmonitor Configuration Directory

**Purpose:** Read/write user configuration
- **Search order:** 
  1. `~/.config/ocmonitor/config.toml`
  2. `./config.toml`
  3. `./ocmonitor.toml`
  4. Package default (`ocmonitor/config.toml`)
- **User pricing override:** `~/.config/ocmonitor/models.json`

### Cache Directory

**Purpose:** Store cached API responses
- **Default:** `~/.cache/ocmonitor/`
- **Files:**
  - `models_dev_api.json` - Cached model pricing
  - `exchange_rates.json` - Cached currency rates

## Docker Integration

**Image:** `ocmonitor` (built from `Dockerfile`)
- **Base:** `python:3.11-slim`
- **Runtime:** `ocmonitor` CLI command as entrypoint
- **Volumes:**
  - OpenCode data: `${OPENCODE_DATA_DIR:-$HOME/.local/share/opencode}:/app/.local/share/opencode`
  - Config: `${OCMONITOR_CONFIG_DIR:-$HOME/.config/ocmonitor}:/app/.config/ocmonitor`
  - Cache: `${OCMONITOR_CACHE_DIR:-$HOME/.cache/ocmonitor}:/app/.cache/ocmonitor`

## Environment Configuration

**Required env vars:** None (all configuration via config files)
**Optional env vars:**
- `XDG_DATA_HOME` - Base for data directories
- `XDG_CACHE_HOME` - Base for cache directories
- `OPENCODE_DATA_DIR` - Override OpenCode data mount point
- `OCMONITOR_CONFIG_DIR` - Override config directory mount point
- `OCMONITOR_CACHE_DIR` - Override cache directory mount point

## Data Flow Summary

```
OpenCode Session Data (SQLite/JSON)
         │
         ▼
┌─────────────────────────────┐
│   DataLoader / SQLiteUtils  │
│   (detects source: sqlite   │
│    or files automatically)  │
└─────────────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│    SessionAnalyzer         │
│    (aggregates data)        │
└─────────────────────────────┘
         │
         ├──▶ MetricsServer ──▶ Prometheus scrape
         │
         ├──▶ LiveMonitor ──▶ Rich CLI dashboard
         │
         ├──▶ ReportGenerator ──▶ CSV/JSON export
         │
         └──▶ Price/Rate fetchers ──▶ models.dev/frankfurter.dev (cached)
```

---

*Integration audit: 2026-04-12*