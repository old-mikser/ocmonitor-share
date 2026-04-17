# Phase Research: Performance Fix for `ocmonitor daily --week`

**Researched:** 2026-04-12
**Domain:** SQLite/File session loading with date filtering
**Confidence:** HIGH

## Summary

The `--week` flag (and `--month`/`--year`) uses `last_n_days` filtering which currently loads ALL sessions first via `analyzer.analyze_all_sessions()` in `report_generator.py:172`, then filters in-memory via `filter_sessions_by_date()`. For SQLite source, each session loads ALL messages before filtering (`sqlite_utils.py:214-215`), causing O(n) message loading for sessions that fall outside the date range.

**Primary recommendation:** Add optional `start_date`/`end_date` parameters to `load_all_sessions()` across all processors, pushing date filtering to the database/filesystem level.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python sqlite3 | stdlib | SQLite database access | OpenCode v1.2.0+ stores sessions in SQLite |
| JSON (std-lib) | stdlib | File-based message storage | Legacy OpenCode file format |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `ocmonitor.utils.data_loader.DataLoader` | N/A | Unified loading with SQLite preference | Primary entry point for loading sessions |
| `ocmonitor.utils.sqlite_utils.SQLiteProcessor` | N/A | SQLite-specific queries | When SQLite source is available |
| `ocmonitor.utils.file_utils.FileProcessor` | N/A | File-based session loading | Legacy fallback |

## Architecture Patterns

### Current Flow (Problematic)
```
report_generator.generate_daily_report(last_n_days=7)
  → analyzer.analyze_all_sessions(base_path)  [loads ALL sessions]
    → data_loader.load_all_sessions()
      → sqlite_processor.load_all_sessions()  [queries ALL sessions]
        → load_session_data() for each session  [loads ALL messages for EACH]
          → load_session_messages()  [O(messages) per session]
  → filter_sessions_by_date()  [filters AFTER loading everything]
```

### Target Flow (Optimized)
```
report_generator.generate_daily_report(last_n_days=7)
  → data_loader.load_all_sessions(start_date=7_days_ago, end_date=today)
    → sqlite_processor.load_all_sessions(start_date=..., end_date=...)
      → SQL WHERE clause filters at query level  [only relevant sessions]
```

### Key Methods to Modify

**SQLiteProcessor.load_all_sessions()** (line 248):
- Add optional `start_date` and `end_date` parameters
- Modify SQL query to add `WHERE s.time_created BETWEEN ? AND ?`
- Convert date objects to millisecond timestamps for comparison

**FileProcessor.load_all_sessions()** (line 350):
- Add optional `start_date` and `end_date` parameters
- Filter session directories by modification time before loading
- Use `session_path.stat().st_mtime` for quick pre-filtering

**DataLoader.load_all_sessions()** (line 138):
- Add optional `start_date` and `end_date` parameters
- Pass through to underlying processors

**SessionAnalyzer.analyze_all_sessions()** (line 51):
- Add optional `start_date` and `end_date` parameters
- Pass through to `data_loader.load_all_sessions()`

**ReportGenerator.generate_daily_report()** (line 156):
- Compute date range BEFORE calling `analyze_all_sessions()`
- Pass `start_date` and `end_date` to analyzer

## Backward Compatibility Assessment

**Non-breaking change — NO backward compatibility risk.**

| Aspect | Assessment |
|--------|------------|
| API signature | Adding optional parameters with default `None` preserves existing callers |
| Return type | Unchanged — `List[SessionData]` |
| Behavior without filters | Identical to current behavior |
| Test coverage | Tests only verify exit_code=0 and basic output, not exact loading behavior |

**Justification:**
1. All changes are additive (new optional parameters with default `None`)
2. When date range is `None`, behavior matches current "load all"
3. Existing tests will pass unchanged because they test file-based loading which will still work
4. No existing API contracts are modified — only extended with optional kwargs

## Test Coverage Status

| Test File | Coverage | Gap |
|-----------|----------|-----|
| `tests/integration/test_cli.py` | Basic `--week` flag usage (line 132) | Only tests error handling, not actual data filtering |
| `tests/unit/test_file_utils.py` | `load_all_sessions` (line 238) | No tests for date-filtered loading |
| `tests/unit/test_time_utils.py` | `get_last_n_days_range` | Only unit tests, not integration |

**Critical gaps identified:**
1. No integration test verifies that `--week` actually filters sessions by date
2. No unit test verifies SQLite processor with date range
3. No unit test verifies FileProcessor with date range
4. No test verifies that filtered loading returns correct session subset

**Recommended Wave 0 tests:**
- Add `test_load_all_sessions_with_date_filter` to `tests/unit/test_file_utils.py`
- Add `test_daily_week_filters_correct_sessions` to `tests/integration/test_cli.py`
- Consider SQLite-specific tests if SQLite infrastructure is available

## Code Dependencies

### Direct Callers of `analyze_all_sessions()`
| File | Line | Context |
|------|------|---------|
| `report_generator.py` | 172, 242, 310, 367, 580 | Daily/Weekly/Monthly/Sessions/Models reports |
| `cli.py` | 356, 359 | `sessions` command |
| `metrics_server.py` | 31 | Prometheus metrics collection |

### Direct Callers of `load_all_sessions()` (DataLoader)
| File | Line | Context |
|------|------|---------|
| `session_analyzer.py` | 63 | `analyze_all_sessions()` |
| `data_loader.py` | 154, 156, 184 | Internal hierarchy loading |
| `live_monitor.py` | 191 | Live session monitoring |

### Files Using Date Filtering Flow
| File | Lines | Pattern |
|------|-------|---------|
| `report_generator.py` | 156-186, 223-294, 296-350 | `generate_daily_report()`, `generate_weekly_report()`, `generate_monthly_report()` |
| `session_analyzer.py` | 223-246 | `filter_sessions_by_date()` |
| `time_utils.py` | 191-205 | `get_last_n_days_range()` |

## Recommended Implementation Approach

### Phase 1: Core Database Filtering (SQLite)
1. Add `start_date: Optional[date]` and `end_date: Optional[date]` to `SQLiteProcessor.load_all_sessions()`
2. Modify SQL query to filter at database level when dates provided
3. Convert Python `date` objects to SQLite-compatible timestamps (milliseconds since epoch)

### Phase 2: File-Based Filtering
4. Add same parameters to `FileProcessor.load_all_sessions()`
5. Implement pre-filtering by session directory mtime before full loading
6. Fall back to full loading + in-memory filter if dates not provided

### Phase 3: DataLoader Propagation
7. Propagate date parameters through `DataLoader.load_all_sessions()`
8. Propagate through `SessionAnalyzer.analyze_all_sessions()`

### Phase 4: Report Generator Integration
9. In `generate_daily_report()`, compute date range BEFORE calling `analyze_all_sessions()`
10. Pass date range to `analyze_all_sessions()` instead of filtering post-load
11. Apply same pattern to `generate_weekly_report()` and `generate_monthly_report()`

### Phase 5: Cleanup
12. Keep `filter_sessions_by_date()` as fallback for edge cases
13. Add deprecation note to `filter_sessions_by_date()` for future removal

## Code Examples

### SQLiteProcessor.load_all_sessions() Modification

```python
# Source: sqlite_utils.py line 248 (proposed modification)
@classmethod
def load_all_sessions(
    cls, 
    db_path: Optional[Path] = None, 
    limit: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> List[SessionData]:
    """Load all sessions from the SQLite database.
    
    Args:
        db_path: Path to database (uses default if not provided)
        limit: Maximum number of sessions to load (None for all)
        start_date: Optional start date filter (inclusive)
        end_date: Optional end date filter (inclusive)
    
    Returns:
        List of SessionData objects sorted by creation time (newest first)
    """
    # ... existing path resolution ...
    
    # Build WHERE clause for date filtering
    where_clause = ""
    params = []
    if start_date or end_date:
        # Convert dates to milliseconds since epoch
        if start_date:
            start_ms = int(datetime.combine(start_date, datetime.min.time()).timestamp() * 1000)
            params.append(start_ms)
        if end_date:
            end_ms = int(datetime.combine(end_date, datetime.max.time()).timestamp() * 1000)
            params.append(end_ms)
        
        if start_date and end_date:
            where_clause = "WHERE s.time_created BETWEEN ? AND ?"
        elif start_date:
            where_clause = "WHERE s.time_created >= ?"
        else:
            where_clause = "WHERE s.time_created <= ?"
    
    # Query with optional date filter
    query = f"""
        SELECT s.*, p.worktree as project_path, p.name as project_name
        FROM session s
        LEFT JOIN project p ON s.project_id = p.id
        {where_clause}
        ORDER BY s.time_created DESC
    """
    # ... rest unchanged ...
```

### FileProcessor.load_all_sessions() Modification

```python
# Source: file_utils.py line 350 (proposed modification)
@staticmethod
def load_all_sessions(
    base_path: str, 
    limit: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> List[SessionData]:
    """Load all sessions from the base path.
    
    Args:
        base_path: Path to search for sessions
        limit: Maximum number of sessions to load (None for all)
        start_date: Optional start date filter
        end_date: Optional end date filter
    
    Returns:
        List of SessionData objects
    """
    session_dirs = FileProcessor.find_session_directories(base_path)
    
    # Pre-filter by modification time if date range provided
    if start_date or end_date:
        start_ts = start_date.timestamp() if start_date else 0
        end_ts = end_date.timestamp() if end_date else float('inf')
        session_dirs = [
            d for d in session_dirs 
            if start_ts <= d.stat().st_mtime <= end_ts
        ]
    
    if limit:
        session_dirs = session_dirs[:limit]

    sessions = []
    for session_dir in session_dirs:
        session_data = FileProcessor.load_session_data(session_dir)
        if session_data:
            # Secondary filter: check actual session date in message files
            if start_date or end_date:
                if session_data.start_time:
                    session_date = session_data.start_time.date()
                    if not TimeUtils.date_in_range(session_date, start_date, end_date):
                        continue
            sessions.append(session_data)

    return sessions
```

## Common Pitfalls

### Pitfall 1: Timestamp Conversion
**What goes wrong:** Date filtering returns wrong results due to timestamp mismatches
**Why it happens:** SQLite stores timestamps in milliseconds, Python `date` objects need conversion
**How to avoid:** Use `datetime.combine(date, datetime.min.time()).timestamp() * 1000` for start, and `datetime.combine(date, datetime.max.time()).timestamp() * 1000` for end

### Pitfall 2: File Modification Time vs. Session Time
**What goes wrong:** Files filtered by directory mtime, but session content may be from different date
**Why it happens:** Directory mtime reflects last write, not session creation time
**How to avoid:** Always apply secondary in-memory filter checking actual session `start_time` after loading

### Pitfall 3: Empty Result Sets
**What goes wrong:** No sessions returned when date range is valid but too restrictive
**Why it happens:** Date filtering at query level with no fallback
**How to avoid:** Return empty list gracefully (existing behavior handles this)

### Pitfall 4: Breaking Generator Pattern
**What goes wrong:** `session_generator()` doesn't support date filtering, creating inconsistency
**Why it happens:** Generator yields sessions one-by-one, can't filter at query level
**How to avoid:** Keep generators as-is; date filtering only on batch `load_all_sessions()`

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Date range calculation | Custom week/month range logic | `TimeUtils.get_last_n_days_range()` | Already handles edge cases |
| Timestamp conversion | Manual millisecond calculations | `datetime.combine().timestamp()` | Avoids off-by-one errors |
| Session filtering | Custom in-memory filter | `filter_sessions_by_date()` | Already tested, handles edge cases |

## Open Questions

1. **Should `session_generator()` also support date filtering?**
   - Current generators yield sessions one-by-one without any filtering
   - Adding date filtering to generators would require refactoring to batch filtering
   - **Recommendation:** Keep generators simple, date filtering only on batch loads

2. **Should we deprecate `filter_sessions_by_date()` after this change?**
   - It would become unused for the primary use case (date-filtered reports)
   - May still be needed for other custom filtering scenarios
   - **Recommendation:** Mark as potentially deprecated, keep for now

3. **SQLite timestamp column verification:**
   - We ASSUME `s.time_created` is the correct column for SQLite sessions
   - **Verification needed:** Check actual SQLite schema in `opencode.db`
   - Risk: Wrong column could silently return wrong results

4. **How should we handle `--week` when the SQLite database has no sessions in range?**
   - Currently loads all, then filters to empty
   - With this fix: query returns empty, report shows "no data"
   - **Recommendation:** Ensure empty result handling in report generator is graceful

## Sources

### Primary (HIGH confidence)
- `ocmonitor/services/report_generator.py` - Confirmed the problematic flow at line 172
- `ocmonitor/utils/sqlite_utils.py` - Confirmed `load_all_sessions()` loads all messages per session at lines 214-215
- `ocmonitor/utils/file_utils.py` - Confirmed file-based loading pattern at line 350
- `ocmonitor/utils/data_loader.py` - Confirmed DataLoader as unified entry point at line 138

### Secondary (MEDIUM confidence)
- `ocmonitor/services/session_analyzer.py` - Confirmed `filter_sessions_by_date()` at line 223
- `ocmonitor/cli.py` - Confirmed `--week` flag handling at line 598
- `tests/integration/test_cli.py` - Confirmed test coverage gap for `--week` flag

### Tertiary (LOW confidence)
- SQLite schema details (column names, timestamp format) - Need verification against actual database

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All components verified from source files
- Architecture: HIGH - Flow traced through code paths
- Pitfalls: MEDIUM - Based on patterns observed, not testing
- Backward compatibility: HIGH - All changes are additive

**Research date:** 2026-04-12
**Valid until:** 2026-05-12 (30 days - stack is stable)
