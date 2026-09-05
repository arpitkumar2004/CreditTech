"""Cross-dialect column types.

Production runs on PostgreSQL and uses JSONB / UUID / INET natively.
The in-memory SQLite test harness (see tests/conftest.py) needs
graceful fallbacks. These TypeDecorators emit the PG-native type on
PostgreSQL and portable equivalents on SQLite, so the same ORM
declaration works in both environments without weakening the
production schema.
"""

from __future__ import annotations

import uuid

from sqlalchemy import CHAR, JSON, String, TypeDecorator
from sqlalchemy.dialects.postgresql import INET as PG_INET
from sqlalchemy.dialects.postgresql import JSONB as PG_JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID


class GUID(TypeDecorator):
    """UUID column that is native on PostgreSQL, CHAR(36) elsewhere."""

    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))


class JSONB(TypeDecorator):
    """JSONB on PostgreSQL, JSON elsewhere."""

    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_JSONB())
        return dialect.type_descriptor(JSON())


class INET(TypeDecorator):
    """INET on PostgreSQL, VARCHAR(45) elsewhere (fits IPv6)."""

    impl = String
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_INET())
        return dialect.type_descriptor(String(45))
