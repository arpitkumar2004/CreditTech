"""CLI: back up the pilot SQLite DB.

Usage:
    python -m scripts.backup [SRC] [DST]

Defaults to `./credittech.db` -> `./backups/credittech-<utc-ts>.db`.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone

try:
    from datetime import UTC
except ImportError:
    UTC = timezone.utc
from pathlib import Path

from services.core.ops.dr import backup_sqlite, row_counts


def main(argv: list[str]) -> int:
    src = Path(argv[1]) if len(argv) > 1 else Path("credittech.db")
    if len(argv) > 2:
        dst = Path(argv[2])
    else:
        ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        dst = Path("backups") / f"credittech-{ts}.db"
    print(f"backup: {src} -> {dst}")
    backup_sqlite(src, dst)
    counts = row_counts(dst)
    print("row_counts:", counts)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
