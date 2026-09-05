"""CLI: restore the pilot SQLite DB from a backup.

Usage:
    python -m scripts.restore BACKUP [TARGET]
"""

from __future__ import annotations

import sys
from pathlib import Path

from services.core.ops.dr import restore_sqlite, row_counts, verify_parity


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    backup = Path(argv[1])
    target = Path(argv[2]) if len(argv) > 2 else Path("credittech.db")
    pre = row_counts(target) if target.exists() else {}
    print(f"restore: {backup} -> {target}")
    restore_sqlite(backup, target)
    post = row_counts(target)
    ok, diffs = verify_parity(row_counts(backup), post)
    print("row_counts:", post)
    print(f"parity_with_backup: {'OK' if ok else 'DIFF ' + str(diffs)}")
    if pre:
        print(f"pre_restore_target_counts: {pre}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
