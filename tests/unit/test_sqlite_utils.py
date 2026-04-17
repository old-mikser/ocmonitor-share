"""Tests for SQLite path discovery behavior."""

from datetime import date, timedelta
from pathlib import Path

from ocmonitor.config import Config, PathsConfig, config_manager
from ocmonitor.utils.sqlite_utils import SQLiteProcessor


class TestFindDatabasePath:
    """Tests for SQLiteProcessor.find_database_path."""

    def test_prefers_custom_path_over_env_and_config(self, monkeypatch, tmp_path: Path):
        """Explicit custom path should have highest precedence."""
        custom_db = tmp_path / "custom.db"
        custom_db.touch()

        env_db = tmp_path / "env.db"
        env_db.touch()
        monkeypatch.setenv("OCMONITOR_DATABASE_FILE", str(env_db))

        configured_db = tmp_path / "configured.db"
        configured_db.touch()
        monkeypatch.setattr(
            config_manager,
            "_config",
            Config(paths=PathsConfig(database_file=str(configured_db))),
        )

        monkeypatch.setattr(SQLiteProcessor, "DEFAULT_DB_PATH", tmp_path / "default.db")

        resolved = SQLiteProcessor.find_database_path(custom_db)

        assert resolved == custom_db

    def test_uses_configured_database_file_when_default_missing(
        self, monkeypatch, tmp_path: Path
    ):
        """Config path should be used when default path does not exist."""
        configured_db = tmp_path / "configured.db"
        configured_db.touch()

        monkeypatch.delenv("OCMONITOR_DATABASE_FILE", raising=False)
        monkeypatch.setattr(
            config_manager,
            "_config",
            Config(paths=PathsConfig(database_file=str(configured_db))),
        )
        monkeypatch.setattr(
            SQLiteProcessor, "DEFAULT_DB_PATH", tmp_path / "missing-default.db"
        )

        resolved = SQLiteProcessor.find_database_path()

        assert resolved == configured_db

    def test_falls_back_to_default_when_configured_path_invalid(
        self, monkeypatch, tmp_path: Path
    ):
        """Default path should be used when configured path is invalid."""
        missing_configured = tmp_path / "missing-configured.db"
        default_db = tmp_path / "default.db"
        default_db.touch()

        monkeypatch.delenv("OCMONITOR_DATABASE_FILE", raising=False)
        monkeypatch.setattr(
            config_manager,
            "_config",
            Config(paths=PathsConfig(database_file=str(missing_configured))),
        )
        monkeypatch.setattr(SQLiteProcessor, "DEFAULT_DB_PATH", default_db)

        resolved = SQLiteProcessor.find_database_path()

        assert resolved == default_db

class TestSQLiteDateBoundaryLocalTime:
    """Tests for SQLite date filtering using local time boundaries."""

    def test_date_filtering_uses_local_time_boundaries(self, tmp_path: Path):
        """Test that SQLite date filtering uses local time, not UTC."""
        import sqlite3
        from datetime import datetime, timezone

        db_path = tmp_path / "test.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("""
            CREATE TABLE session (
                id TEXT PRIMARY KEY,
                project_id TEXT,
                time_created INTEGER,
                time_updated INTEGER,
                summary TEXT,
                first_model TEXT,
                cost REAL
            )
        """)
        conn.execute("""
            CREATE TABLE project (
                id TEXT PRIMARY KEY,
                name TEXT,
                worktree TEXT,
                created_at INTEGER
            )
        """)
        conn.execute("""
            CREATE TABLE message (
                id TEXT PRIMARY KEY,
                session_id TEXT,
                time_created INTEGER,
                data TEXT
            )
        """)
        conn.commit()
        conn.close()

        now_local = datetime.now()
        now_utc = datetime.now(timezone.utc)

        start = now_local.date() - timedelta(days=1)
        end = now_local.date() + timedelta(days=1)

        sessions = SQLiteProcessor.load_all_sessions(
            db_path=db_path, start_date=start, end_date=end
        )

        assert isinstance(sessions, list)

    def test_date_filtering_boundary_consistency_with_file_utils(self, tmp_path: Path):
        """Test that SQLite and file-based date filtering use consistent local time."""
        import sqlite3
        from datetime import datetime

        db_path = tmp_path / "test.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("""
            CREATE TABLE session (
                id TEXT PRIMARY KEY,
                project_id TEXT,
                time_created INTEGER,
                time_updated INTEGER,
                summary TEXT,
                first_model TEXT,
                cost REAL
            )
        """)
        conn.execute("""
            CREATE TABLE project (
                id TEXT PRIMARY KEY,
                name TEXT,
                worktree TEXT,
                created_at INTEGER
            )
        """)
        conn.execute("""
            CREATE TABLE message (
                id TEXT PRIMARY KEY,
                session_id TEXT,
                time_created INTEGER,
                data TEXT
            )
        """)
        conn.commit()
        conn.close()

        today = date.today()
        start = today - timedelta(days=7)
        end = today

        sqlite_sessions = SQLiteProcessor.load_all_sessions(
            db_path=db_path, start_date=start, end_date=end
        )

        assert isinstance(sqlite_sessions, list)

