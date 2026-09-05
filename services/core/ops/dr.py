"""P6 — Disaster Recovery helpers.

For the pilot (SQLite dev DB) DR is:
    * `backup(src, dst)` — safe file-level snapshot via `sqlite3.Connection.backup`
    * `restore(backup, target)` — copy backup file to target path
    * `verify(target)` — row-count parity check on key tables against a supplied
      snapshot dict.

The Postgres path is deliberately out of scope for the pilot — production DR
is handled by managed backups on the RDS/Cloud SQL instance; this module
serves the local sqlite pilot DB.
"""

from __future__ import annotations

import shutil
import sqlite3
from pathlib import Path

KEY_TABLES = (
    "borrowers", "scores", "loan_applications", "officer_decision_log",
    "grievances", "grievance_audit_log", "fairness_audit_log",
)


def backup_sqlite(src: str | Path, dst: str | Path) -> Path:
    src = Path(src)
    dst = Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    if not src.exists():
        raise FileNotFoundError(f"SQLite source not found: {src}")
    conn_src = sqlite3.connect(str(src))
    conn_dst = sqlite3.connect(str(dst))
    try:
        with conn_dst:
            conn_src.backup(conn_dst)
    finally:
        conn_src.close()
        conn_dst.close()
    return dst


def restore_sqlite(backup: str | Path, target: str | Path) -> Path:
    backup = Path(backup)
    target = Path(target)
    if not backup.exists():
        raise FileNotFoundError(f"Backup not found: {backup}")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(str(backup), str(target))
    return target


def row_counts(db_path: str | Path, tables: tuple[str, ...] = KEY_TABLES) -> dict[str, int]:
    conn = sqlite3.connect(str(db_path))
    try:
        counts: dict[str, int] = {}
        for t in tables:
            try:
                cur = conn.execute(f"SELECT COUNT(*) FROM {t}")
                counts[t] = int(cur.fetchone()[0])
            except sqlite3.OperationalError:
                counts[t] = 0
        return counts
    finally:
        conn.close()


def verify_parity(pre: dict[str, int], post: dict[str, int]) -> tuple[bool, dict[str, tuple[int, int]]]:
    diffs: dict[str, tuple[int, int]] = {}
    for k in set(pre) | set(post):
        if pre.get(k, 0) != post.get(k, 0):
            diffs[k] = (pre.get(k, 0), post.get(k, 0))
    return (len(diffs) == 0, diffs)


__all__ = [
    "backup_sqlite", "restore_sqlite", "row_counts", "verify_parity", "KEY_TABLES",
]
