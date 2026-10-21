"""The shared-reader child must not look successful if a reader is still alive or has raised (#11208).

Removing the join call fails the source guard. Removing the excepthook assignment
fails that guard too, and the injected-reader test exits 0 instead of 3.
"""

from __future__ import annotations

import ast

from tests.test_readonly_sqlite import SHARED_READER_LOAD, make_forms_database, run_shared_reader_child


def _forms(tmp_path):
    path = tmp_path / "forms.db"
    make_forms_database(path)
    return path


def _reader_joins(source: str) -> list[ast.Call]:
    """thread.join(...) calls. str.join is a different method and does not count."""
    calls = []
    for node in ast.walk(ast.parse(source)):
        func = getattr(node, "func", None)
        if (
            isinstance(node, ast.Call)
            and isinstance(func, ast.Attribute)
            and func.attr == "join"
            and isinstance(func.value, ast.Name)
        ):
            calls.append(node)
    return calls


def _assigns_reader_excepthook(source: str) -> bool:
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if (
                isinstance(target, ast.Attribute)
                and target.attr == "excepthook"
                and isinstance(target.value, ast.Name)
                and target.value.id == "threading"
            ):
                return True
    return False


def _strip_join_calls(source: str) -> str:
    class Strip(ast.NodeTransformer):
        def visit_Expr(self, node: ast.Expr) -> ast.Expr | None:
            call = node.value
            func = call.func if isinstance(call, ast.Call) else None
            if isinstance(func, ast.Attribute) and func.attr == "join" and isinstance(func.value, ast.Name):
                return None
            return node

    tree = Strip().visit(ast.parse(source))
    ast.fix_missing_locations(tree)
    return ast.unparse(tree)


def test_harness_source_joins_readers_and_captures_exceptions():
    assert _reader_joins(SHARED_READER_LOAD), "reader threads must be joined before the child exits"
    assert _assigns_reader_excepthook(SHARED_READER_LOAD), "reader exceptions must be captured"


def test_live_reader_threads_fail_the_child(tmp_path):
    result = run_shared_reader_child(
        _forms(tmp_path),
        env={"SHARED_READER_HOLD_READERS": "1", "SHARED_READER_WORK_S": "0.15", "SHARED_READER_JOIN_S": "0.4"},
        timeout=15,
    )
    assert result.returncode == 2, result.stderr[-2000:]
    assert "still alive" in result.stderr


def test_reader_exception_fails_the_child(tmp_path):
    result = run_shared_reader_child(
        _forms(tmp_path),
        env={"SHARED_READER_INJECT_ERROR": "1", "SHARED_READER_WORK_S": "0.25", "SHARED_READER_JOIN_S": "2"},
        timeout=15,
    )
    assert result.returncode == 3, result.stderr[-2000:]
    assert "FAIL reader thread exceptions:" in result.stderr
    assert "injected reader failure" in result.stderr


def test_removing_the_join_fails(tmp_path):
    """Mutation: delete every join call. Parked readers must not exit 0."""
    mutated = _strip_join_calls(SHARED_READER_LOAD)
    assert not _reader_joins(mutated)
    result = run_shared_reader_child(
        _forms(tmp_path),
        source=mutated,
        env={"SHARED_READER_HOLD_READERS": "1", "SHARED_READER_WORK_S": "0.15", "SHARED_READER_JOIN_S": "0.4"},
        timeout=15,
    )
    assert result.returncode != 0, result.stderr[-2000:]
    assert "still alive" in result.stderr or "unjoined" in result.stderr
