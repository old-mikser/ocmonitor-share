import json
import sqlite3
import time
from pathlib import Path

from ocmonitor.utils.sqlite_utils import SQLiteProcessor


def _assistant_message(tokens: int = 10) -> str:
    return json.dumps(
        {
            "role": "assistant",
            "tokens": {"input": tokens, "output": 0, "cache": {"write": 0, "read": 0}},
            "time": {
                "created": int(time.time() * 1000),
                "completed": int(time.time() * 1000),
            },
        }
    )


def _create_base_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE project (
            id TEXT PRIMARY KEY,
            worktree TEXT,
            name TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE session (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            parent_id TEXT,
            title TEXT,
            time_created INTEGER NOT NULL,
            time_updated INTEGER NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE message (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            time_created INTEGER NOT NULL,
            time_updated INTEGER NOT NULL,
            data TEXT NOT NULL
        )
        """
    )


def test_get_all_active_workflows_orders_by_latest_parent_activity(tmp_path: Path):
    db_path = tmp_path / "opencode.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    _create_base_schema(conn)

    now_ms = int(time.time() * 1000)

    conn.execute(
        "INSERT INTO project (id, worktree, name) VALUES (?, ?, ?)",
        ("proj", "/tmp/project", "project"),
    )

    # This parent is created earlier, but has the newest parent message.
    conn.execute(
        "INSERT INTO session (id, project_id, parent_id, title, time_created, time_updated) VALUES (?, ?, ?, ?, ?, ?)",
        (
            "older-parent",
            "proj",
            None,
            "Older Parent",
            now_ms - 10_000,
            now_ms - 10_000,
        ),
    )
    conn.execute(
        "INSERT INTO message (id, session_id, time_created, time_updated, data) VALUES (?, ?, ?, ?, ?)",
        (
            "msg-older-new",
            "older-parent",
            now_ms - 1_000,
            now_ms - 1_000,
            _assistant_message(),
        ),
    )

    # This parent is created later, but has an older parent message.
    conn.execute(
        "INSERT INTO session (id, project_id, parent_id, title, time_created, time_updated) VALUES (?, ?, ?, ?, ?, ?)",
        ("newer-parent", "proj", None, "Newer Parent", now_ms - 2_000, now_ms - 2_000),
    )
    conn.execute(
        "INSERT INTO message (id, session_id, time_created, time_updated, data) VALUES (?, ?, ?, ?, ?)",
        (
            "msg-newer-old",
            "newer-parent",
            now_ms - 5_000,
            now_ms - 5_000,
            _assistant_message(),
        ),
    )

    conn.commit()
    conn.close()

    workflows = SQLiteProcessor.get_all_active_workflows(
        db_path=db_path,
        active_threshold_minutes=60,
    )

    assert [w["workflow_id"] for w in workflows[:2]] == ["older-parent", "newer-parent"]
