"""P6 — Disaster recovery: backup + restore + parity."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from services.core.ops.dr import (
    backup_sqlite,
    restore_sqlite,
    row_counts,
    verify_parity,
)


def _make_seed_db(path: Path, borrower_rows: int) -> None:
    conn = sqlite3.connect(str(path))
    conn.execute("CREATE TABLE borrowers (id INTEGER PRIMARY KEY, name TEXT)")
    conn.execute("CREATE TABLE scores (id INTEGER PRIMARY KEY)")
    for i in range(borrower_rows):
        conn.execute("INSERT INTO borrowers (name) VALUES (?)", (f"b{i}",))
    conn.commit()
    conn.close()


def test_backup_and_restore_preserves_row_counts(tmp_path: Path) -> None:
    src = tmp_path / "src.db"
    backup = tmp_path / "backup.db"
    restored = tmp_path / "restored.db"
    _make_seed_db(src, 42)

    backup_sqlite(src, backup)
    assert backup.exists() and backup.stat().st_size > 0

    restore_sqlite(backup, restored)
    src_counts = row_counts(src, tables=("borrowers", "scores"))
    restored_counts = row_counts(restored, tables=("borrowers", "scores"))
    ok, diffs = verify_parity(src_counts, restored_counts)
    assert ok, f"row-count drift: {diffs}"
    assert restored_counts == {"borrowers": 42, "scores": 0}


def test_verify_parity_detects_drift() -> None:
    ok, diffs = verify_parity({"a": 5}, {"a": 4})
    assert not ok and diffs == {"a": (5, 4)}
