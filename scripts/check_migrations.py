"""Zero-Downtime Migration CI Gate (scripts/check_migrations.py).

Enforces schema synchronization and zero-downtime Expand-Contract backward-compatible
DDL patterns across Alembic migrations:
1. Verifies that the active database matches the Alembic head revision.
2. Statically inspects migration scripts using AST parsing to flag unsafe operations:
   - op.add_column with nullable=False without a server_default.
   - op.drop_column unless explicitly approved/tagged for Expand-Contract phase.
   - op.drop_table (destructive DDL).
"""

import argparse
import ast
import sys
from pathlib import Path

import alembic.command
import alembic.config
import alembic.util


def _is_false_constant(val: ast.AST) -> bool:
    """Checks whether an AST node represents the literal False."""
    if isinstance(val, ast.Constant) and val.value is False:
        return True
    return isinstance(val, ast.Name) and val.id == "False"


def _is_none_constant(val: ast.AST) -> bool:
    """Checks whether an AST node represents the literal None."""
    if isinstance(val, ast.Constant) and val.value is None:
        return True
    return isinstance(val, ast.Name) and val.id == "None"


def _extract_revision_id(tree: ast.AST) -> str | None:
    """Extracts revision identifier from module-level assignment."""
    for node in getattr(tree, "body", []):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if (
                    isinstance(target, ast.Name)
                    and target.id == "revision"
                    and isinstance(node.value, ast.Constant)
                    and isinstance(node.value.value, str)
                ):
                    return node.value.value
        elif (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "revision"
            and node.value
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        ):
            return node.value.value
    return None


class MigrationSafetyVisitor(ast.NodeVisitor):
    """AST visitor detecting unsafe zero-downtime DDL calls in Alembic migrations."""

    def __init__(
        self,
        filename: str,
        source_lines: list[str],
        file_approved: bool,
        approved_tags: tuple[str, ...],
    ) -> None:
        self.filename = filename
        self.source_lines = source_lines
        self.file_approved = file_approved
        self.approved_tags = approved_tags
        self.errors: list[str] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        # Skip downgrade blocks; Expand-Contract safety applies to forward upgrade DDL
        if node.name == "downgrade":
            return
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        if node.name == "downgrade":
            return
        self.generic_visit(node)

    def _is_approved(self, lineno: int) -> bool:
        if self.file_approved:
            return True
        if 0 <= lineno - 1 < len(self.source_lines):
            line = self.source_lines[lineno - 1].lower()
            return any(tag in line for tag in self.approved_tags)
        return False

    def _get_func_name(self, node: ast.Call) -> str | None:
        if isinstance(node.func, ast.Attribute):
            return node.func.attr
        if isinstance(node.func, ast.Name):
            return node.func.id
        return None

    def visit_Call(self, node: ast.Call) -> None:
        func_name = self._get_func_name(node)

        if func_name == "add_column":
            self._check_add_column(node)
        elif func_name == "drop_column":
            self._check_drop_column(node)
        elif func_name == "drop_table":
            self._check_drop_table(node)

        self.generic_visit(node)

    def _check_add_column(self, node: ast.Call) -> None:
        has_nullable_false = False
        has_server_default = False

        calls_to_inspect: list[ast.Call] = [node]
        for arg in node.args:
            if isinstance(arg, ast.Call):
                calls_to_inspect.append(arg)
        for kw in node.keywords:
            if isinstance(kw.value, ast.Call):
                calls_to_inspect.append(kw.value)

        for call_node in calls_to_inspect:
            for kw in call_node.keywords:
                if kw.arg == "nullable" and _is_false_constant(kw.value):
                    has_nullable_false = True
                elif kw.arg == "server_default" and not _is_none_constant(kw.value):
                    has_server_default = True

        if has_nullable_false and not has_server_default and not self._is_approved(node.lineno):
            self.errors.append(
                f"{self.filename}:{node.lineno}: op.add_column with nullable=False requires server_default "
                "for zero-downtime Expand-Contract migration (avoids table locks and row insert failures)."
            )

    def _check_drop_column(self, node: ast.Call) -> None:
        if not self._is_approved(node.lineno):
            self.errors.append(
                f"{self.filename}:{node.lineno}: op.drop_column violates Expand-Contract backward compatibility "
                "unless explicitly approved/tagged (use '# allow-drop-column' or '# approved-contract-phase')."
            )

    def _check_drop_table(self, node: ast.Call) -> None:
        if not self._is_approved(node.lineno):
            self.errors.append(
                f"{self.filename}:{node.lineno}: op.drop_table is destructive DDL and not permitted in automated migrations "
                "(use '# allow-drop-table' or '# allow-destructive' if approved)."
            )


def check_schema_sync(config_path: str | Path = "alembic.ini") -> bool:
    """Verifies that the database schema is synchronized with Alembic head.

    Uses alembic.command.check(alembic_cfg). Returns True if in sync, False if diffs or errors.
    """
    config_file = Path(config_path)
    if not config_file.exists():
        sys.stderr.write(f"ERROR: Alembic configuration file not found at {config_file}\n")
        return False

    try:
        alembic_cfg = alembic.config.Config(str(config_file))
        alembic.command.check(alembic_cfg)
        return True
    except alembic.util.AutogenerateDiffsDetected as e:
        sys.stderr.write(f"ERROR: Alembic detected uncommitted schema diffs: {e}\n")
        return False
    except Exception as e:
        sys.stderr.write(f"ERROR: Alembic schema sync check failed: {e}\n")
        return False


def check_migration_safety(
    versions_dir: str | Path = "alembic/versions",
    baseline_revisions: tuple[str, ...] | list[str] = ("14323a45982d",),
    approved_tags: tuple[str, ...] | list[str] = (
        "allow-drop-column",
        "allow-drop-table",
        "allow-destructive",
        "approved-contract-phase",
        "approved-contract",
        "expand-contract-approved",
    ),
) -> list[str]:
    """Inspects migration files for unsafe DDL operations violating zero-downtime Expand-Contract rules.

    Returns a list of error strings. If empty, all migrations pass safety checks.
    """
    vpath = Path(versions_dir)
    if not vpath.exists():
        return []

    files = [vpath] if vpath.is_file() else sorted(vpath.glob("*.py"))
    all_errors: list[str] = []
    baseline_set = set(baseline_revisions)

    for file_path in files:
        if file_path.name.startswith("__"):
            continue

        # Check if filename contains any baseline revision
        if any(base_rev in file_path.name for base_rev in baseline_set):
            continue

        try:
            source = file_path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(file_path))
        except Exception as e:
            all_errors.append(f"{file_path.name}: Failed to parse AST: {e}")
            continue

        # Check revision ID in module AST
        rev_id = _extract_revision_id(tree)
        if rev_id and rev_id in baseline_set:
            continue

        # Check for file-level approval tags
        file_approved = any(tag in source.lower() for tag in approved_tags)

        visitor = MigrationSafetyVisitor(
            filename=file_path.name,
            source_lines=source.splitlines(),
            file_approved=file_approved,
            approved_tags=tuple(approved_tags),
        )
        visitor.visit(tree)
        all_errors.extend(visitor.errors)

    return all_errors


def main(argv: list[str] | None = None) -> int:
    """Main CLI entrypoint for zero-downtime migration checks."""
    parser = argparse.ArgumentParser(
        description="Zero-Downtime Migration CI Gate (Schema Sync & AST Safety Check)",
    )
    parser.add_argument(
        "--check-schema-only",
        action="store_true",
        help="Only verify database schema matches Alembic head revision",
    )
    parser.add_argument(
        "--check-safety-only",
        action="store_true",
        help="Only verify migration files for zero-downtime safety",
    )
    parser.add_argument(
        "--config",
        default="alembic.ini",
        help="Path to alembic.ini (default: alembic.ini)",
    )
    parser.add_argument(
        "--versions-dir",
        default="alembic/versions",
        help="Path to alembic versions directory (default: alembic/versions)",
    )

    args = parser.parse_args(argv)

    run_schema = True
    run_safety = True

    if args.check_schema_only and not args.check_safety_only:
        run_safety = False
    elif args.check_safety_only and not args.check_schema_only:
        run_schema = False

    success = True

    if run_schema:
        print("[CI Gate] Checking database schema synchronization against Alembic head...")
        if not check_schema_sync(config_path=args.config):
            print("FAILED: Schema is not in sync with Alembic models or check error occurred.")
            success = False
        else:
            print("PASSED: Database schema is synchronized with Alembic head.")

    if run_safety:
        print("[CI Gate] Checking migration files for Expand-Contract zero-downtime safety...")
        safety_errors = check_migration_safety(versions_dir=args.versions_dir)
        if safety_errors:
            print("FAILED: Migration safety violations detected:")
            for err in safety_errors:
                print(f"  - {err}")
            success = False
        else:
            print("PASSED: All migration files adhere to zero-downtime Expand-Contract safety rules.")

    if success:
        print("[CI Gate] All migration checks passed successfully.")
        return 0
    else:
        print("[CI Gate] Migration checks failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
