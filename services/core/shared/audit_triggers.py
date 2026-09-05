"""P6 — DB-level append-only enforcement for audit tables.

Application code already avoids updating/deleting OfficerDecisionLog and
GrievanceAuditLog rows, but the P6 hardening goal is defense-in-depth: any
attempted mutation must fail at the database, not just the app layer.

We install dialect-specific triggers:
    * SQLite: `BEFORE UPDATE/DELETE ... FOR EACH ROW BEGIN SELECT RAISE(ABORT, ...) END`
    * PostgreSQL: `BEFORE UPDATE OR DELETE ... EXECUTE FUNCTION raise_append_only()`

Called from application startup and from the test setup fixture so both
production and CI enforce the invariant.
"""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

APPEND_ONLY_TABLES = ("officer_decision_log", "grievance_audit_log")


SQLITE_TEMPLATE = """
CREATE TRIGGER IF NOT EXISTS {table}_no_update
BEFORE UPDATE ON {table}
BEGIN
    SELECT RAISE(ABORT, '{table} is append-only (P6 audit invariant)');
END;
"""

SQLITE_DELETE_TEMPLATE = """
CREATE TRIGGER IF NOT EXISTS {table}_no_delete
BEFORE DELETE ON {table}
BEGIN
    SELECT RAISE(ABORT, '{table} is append-only (P6 audit invariant)');
END;
"""

POSTGRES_FN = """
CREATE OR REPLACE FUNCTION raise_append_only() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'Append-only table (%): mutation blocked by P6 audit invariant',
        TG_TABLE_NAME USING ERRCODE = 'insufficient_privilege';
END;
$$ LANGUAGE plpgsql;
"""

POSTGRES_TRIGGER = """
DROP TRIGGER IF EXISTS {table}_append_only ON {table};
CREATE TRIGGER {table}_append_only
BEFORE UPDATE OR DELETE ON {table}
FOR EACH ROW EXECUTE FUNCTION raise_append_only();
"""


async def install_append_only_triggers(conn: AsyncConnection) -> None:
    """Idempotent — safe to call on every startup."""
    dialect = conn.engine.dialect.name
    if dialect == "sqlite":
        for tbl in APPEND_ONLY_TABLES:
            await conn.exec_driver_sql(SQLITE_TEMPLATE.format(table=tbl))
            await conn.exec_driver_sql(SQLITE_DELETE_TEMPLATE.format(table=tbl))
    elif dialect in ("postgresql", "postgres"):
        await conn.execute(text(POSTGRES_FN))
        for tbl in APPEND_ONLY_TABLES:
            for stmt in POSTGRES_TRIGGER.format(table=tbl).strip().split(";"):
                s = stmt.strip()
                if s:
                    await conn.execute(text(s))
    else:
        # Unknown dialect — do not silently swallow.
        raise NotImplementedError(
            f"Append-only triggers not implemented for dialect: {dialect}"
        )


__all__ = ["install_append_only_triggers", "APPEND_ONLY_TABLES"]
