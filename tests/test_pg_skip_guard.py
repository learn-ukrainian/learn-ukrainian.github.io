"""The Postgres skip guard turns a silent skip into a red shard (#9062)."""

from pathlib import Path

from scripts.ci import junit_results
from scripts.ci.pg_skip_guard import DSN_ENV, check, main
from scripts.ci.pg_skip_guard import postgres_test_files as find_pg_files

_PG_FILE = "tests/fleet_comms/test_sample_pg.py"


def _junit(tmp_path: Path, *cases: str) -> Path:
    path = tmp_path / "junit.xml"
    path.write_text(f"<testsuites><testsuite name='pytest'>{''.join(cases)}</testsuite></testsuites>", encoding="utf-8")
    return path


def _case(name: str, body: str = "", file: str = _PG_FILE) -> str:
    module = file[:-3].replace("/", ".")
    return f"<testcase classname='{module}' name='{name}' file='{file}'>{body}</testcase>"


def _skip() -> str:
    return f"<skipped type='pytest.skip' message='{DSN_ENV} unset/empty'>skip</skipped>"


def test_main_reports_counts_and_exit_code(tmp_path: Path, capsys, monkeypatch):
    monkeypatch.setattr("scripts.ci.pg_skip_guard.postgres_test_files", lambda root: {_PG_FILE})
    clean = _junit(tmp_path, _case("test_a"), _case("test_b"))
    assert main([str(clean), "--title", "shard 1"]) == 0
    assert "passed=2 skipped=0" in capsys.readouterr().out

    skipped = tmp_path / "skipped.xml"
    skipped.write_text(_junit(tmp_path, _case("test_a"), _case("test_b", _skip())).read_text(), encoding="utf-8")
    assert main([str(skipped)]) == 1
    captured = capsys.readouterr()
    assert "passed=1 skipped=1" in captured.out and "test_b skipped" in captured.err


def test_dsn_skip_fails_even_when_other_tests_pass():
    results = [
        junit_results.TestResult(f"{_PG_FILE}::test_a", "passed", "", 0, Path("x")),
        junit_results.TestResult(f"{_PG_FILE}::test_b", "skipped", f"{DSN_ENV} unset/empty", 0, Path("x")),
    ]
    problems, counts = check(results, {_PG_FILE})
    assert len(problems) == 1 and "test_b skipped" in problems[0]
    assert (counts["passed"], counts["skipped"]) == (1, 1)


def test_file_with_no_passing_test_fails_and_unrelated_skips_do_not():
    only_failed = [junit_results.TestResult(f"{_PG_FILE}::test_a", "failed", "boom", 0, Path("x"))]
    problems, _ = check(only_failed, {_PG_FILE})
    assert problems and "none passed" in problems[0]

    unrelated = [
        junit_results.TestResult("tests/test_other.py::test_a", "skipped", "needs a GPU", 0, Path("x")),
        junit_results.TestResult(f"{_PG_FILE}::test_a", "passed", "", 0, Path("x")),
    ]
    assert check(unrelated, {_PG_FILE})[0] == []


def test_postgres_files_are_found_in_the_repo():
    found = find_pg_files(Path(__file__).resolve().parents[1])
    assert "tests/fleet_comms/test_pg_schema_ledger.py" in found
    assert "tests/fleet_comms/test_artifacts_pg_transactions.py" in found


def test_fstring_skip_message_alone_marks_a_file_as_postgres(tmp_path: Path):
    import subprocess

    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True, timeout=30)
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_fstring_only.py").write_text(
        'def test_x():\n    pytest.skip(f"{_PG_DSN_ENV} unset/empty - skipped")\n', encoding="utf-8"
    )
    (tmp_path / "tests" / "test_unrelated.py").write_text("def test_y():\n    pass\n", encoding="utf-8")
    subprocess.run(["git", "add", "tests"], cwd=tmp_path, check=True, timeout=30)
    assert find_pg_files(tmp_path) == {"tests/test_fstring_only.py"}
