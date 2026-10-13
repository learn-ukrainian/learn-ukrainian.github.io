"""Anti-rot guard for #5740 — every test subprocess call must be bounded.

Background: a timeout-less ``subprocess.*`` hang held a CI runner for 357 minutes
(run ``30109965086``) because three guards were missing at once: call-site
``timeout=``, job ``timeout-minutes``, and ``pytest-timeout``. Job caps landed in
PR #5735; ``pytest-timeout`` is pinned in ``requirements*.txt`` and enforced via
``pyproject.toml`` (``timeout = 120``, ``timeout_method = "thread"``) plus the
CI pytest invocation. This module keeps the *call-site* fence from regrowing and
proves a hang fails fast *and names the test*.

``subprocess.Popen`` cannot take ``timeout=`` at construction; callers must bound
``.wait()`` / ``.communicate()`` (or an equivalent deadline). The AST guard in
``scripts/ci/subprocess_timeout_guard.py`` covers ``run`` / ``check_output`` /
``call`` / ``check_call`` only. Scripts/ keys include a call-shape hash so a
different timeout-less call cannot rotate into a vacated qualname slot (#7213).
"""

from __future__ import annotations

import ast
import os
import re
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

import scripts.ci.subprocess_timeout_guard as timeout_guard
from scripts.ci.subprocess_timeout_guard import (
    ALLOWLIST_KEY_PARTS,
    SHAPE_HASH_HEX_LEN,
    SORT_ADVICE,
    STALE_PREAMBLE,
    TESTS_TIMEOUT_PREAMBLE,
    UNALLOWLISTED_PREAMBLE,
    compare_allowlist,
    format_stale_line,
    format_unallowlisted_line,
    load_allowlist,
    main,
    parse_allowlist_key,
    scan_scripts,
    sort_allowlist_entries,
    timeout_less_calls,
    timeout_less_calls_from_source,
    validate_allowlist_entry,
)

pytestmark = [pytest.mark.repo_invariant, pytest.mark.repo_wide]

_REPO_ROOT = Path(__file__).resolve().parents[1]
_TESTS_ROOT = _REPO_ROOT / "tests"
_SCRIPTS_ROOT = _REPO_ROOT / "scripts"
_ALLOWLIST_PATH = _SCRIPTS_ROOT / "ci" / "subprocess_timeout_allowlist.txt"

# Documented per-test budget (must stay aligned with pyproject + ci.yml).
_EXPECTED_PYTEST_TIMEOUT_SECONDS = 120
_EXPECTED_TIMEOUT_METHOD = "thread"


@pytest.mark.parametrize(
    ("source", "callee"),
    [
        ('import subprocess as sp\nsp.run(["probe"])\n', "run"),
        ('import os, subprocess as sp\nsp.check_call(["probe"])\n', "check_call"),
        ('import os, \\\n    subprocess as sp\nsp.call(["probe"])\n', "call"),
        ('from subprocess import (\n    check_output as launch,\n)\nlaunch(["probe"])\n', "check_output"),
        ('from subprocess \\\n    import run as launch\nlaunch(["probe"])\n', "run"),
        ('import subprocess; subprocess.run(["probe"])\n', "run"),
        ('if True: import subprocess as sp\nsp.run(["probe"])\n', "run"),
        ('import ｓｕｂｐｒｏｃｅｓｓ as sp\nsp.ｒｕｎ(["probe"])\n', "run"),
        ('from ｓｕｂｐｒｏｃｅｓｓ import ｃｈｅｃｋ＿ｃａｌｌ as launch\nlaunch(["probe"])\n', "check_call"),
        ("import subprocess as sp\nvalue = f\"{sp.run(['probe'])}\"\n", "run"),
    ],
)
def test_prefilter_preserves_real_calls(source: str, callee: str, tmp_path: Path) -> None:
    expected = timeout_guard.timeout_less_calls_from_tree(ast.parse(source))
    assert len(expected) == 1
    assert expected[0].name == f"subprocess.{callee}"
    assert expected[0].qualname == "<module>"
    assert timeout_less_calls_from_source(source) == expected
    path = tmp_path / "probe.py"
    path.write_text(source, encoding="utf-8")
    assert timeout_less_calls(path) == expected
    bounded = source.replace('["probe"]', '["probe"], timeout=30').replace("['probe']", "['probe'], timeout=30")
    path.write_text(bounded, encoding="utf-8")
    assert timeout_less_calls_from_source(bounded) == []
    assert timeout_less_calls(path) == []


@pytest.mark.parametrize("directory", ["scripts", "tests"])
def test_prefilter_matches_full_ast_on_tracked_corpus(directory: str, monkeypatch: pytest.MonkeyPatch) -> None:
    tracked = subprocess.run(
        ["git", "ls-files", "-z", "--", f"{directory}/*.py"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    ).stdout
    paths = [_REPO_ROOT / name for name in tracked.split("\0") if name]
    assert paths
    parsed: list[Path] = []
    original_parse = timeout_guard.parse_test_source

    def track_parse(path: Path) -> ast.Module:
        parsed.append(path)
        return original_parse(path)

    monkeypatch.setattr(timeout_guard, "parse_test_source", track_parse)
    for path in paths:
        source = path.read_text(encoding="utf-8")
        expected = timeout_guard.timeout_less_calls_from_tree(ast.parse(source, filename=str(path)))
        assert timeout_less_calls(path) == expected, path.relative_to(_REPO_ROOT)
    assert len(parsed) < len(paths), "The filter must avoid parsing irrelevant files"


@pytest.mark.parametrize(
    "source",
    [
        'value = "unrelated"\n',
        'import subprocess\nsubprocess.Popen(["probe"])\n',
        'source = """import subprocess\nsubprocess.run(["probe"])\n"""\n',
        '# import subprocess\n# subprocess.run(["probe"])\n',
    ],
)
def test_prefilter_skips_irrelevant_ast(source: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "probe.py"
    path.write_text(source, encoding="utf-8")

    def unexpected_parse(*args: object, **kwargs: object) -> ast.Module:
        pytest.fail("Irrelevant source must not be AST-parsed")

    monkeypatch.setattr(timeout_guard, "parse_test_source", unexpected_parse)
    monkeypatch.setattr(timeout_guard.ast, "parse", unexpected_parse)
    assert timeout_less_calls_from_source(source) == []
    assert timeout_less_calls(path) == []


def test_prefilter_preserves_cache_refresh_and_reuse(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "probe.py"
    source = 'import subprocess\nsubprocess.run(["probe"])\n'
    path.write_text(source, encoding="utf-8")
    expected = timeout_less_calls_from_source(source)
    assert timeout_less_calls(path) == expected
    original_read = Path.read_text
    reads: list[Path] = []

    def track_read(self: Path, *args: object, **kwargs: object) -> str:
        reads.append(self)
        return original_read(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", track_read)
    assert timeout_less_calls(path) == expected
    assert reads == []
    replacement = tmp_path / "replacement.py"
    replacement.write_text('import subprocess\nsubprocess.run(["probe"], timeout=30)\n', encoding="utf-8")
    replacement.replace(path)
    assert timeout_less_calls(path) == []
    assert reads == [path.resolve()]


def test_prefilter_propagates_read_and_candidate_syntax_errors(tmp_path: Path) -> None:
    path = tmp_path / "probe.py"
    with pytest.raises(FileNotFoundError):
        timeout_less_calls(path)
    path.write_bytes(b"\xff")
    with pytest.raises(UnicodeDecodeError):
        timeout_less_calls(path)
    source = "import subprocess\nsubprocess.run(\n"
    path.write_text(source, encoding="utf-8")
    with pytest.raises(SyntaxError):
        timeout_less_calls(path)
    with pytest.raises(SyntaxError):
        timeout_less_calls_from_source(source)


@pytest.mark.parametrize(
    "source",
    [
        "import subprocess\nsubprocess.Popen(\n",
        "import subprocess\nif:\n    pass\n",
        'source = """\nimport subprocess\nsubprocess.run([])\n"""\nif:\n    pass\n',
        'import subprocess\n"unterminated run\n',
        'import subprocess\n"""unterminated run\n',
    ],
)
def test_prefilter_retains_rejected_source_syntax_errors(source: str, tmp_path: Path) -> None:
    path = tmp_path / "probe.py"
    path.write_text(source, encoding="utf-8")
    with pytest.raises(SyntaxError):
        timeout_less_calls_from_source(source)
    with pytest.raises(SyntaxError):
        timeout_less_calls(path)


def test_prefilter_compilation_scope_error_is_not_a_syntax_error(tmp_path: Path) -> None:
    source = "import subprocess\nreturn\n"
    path = tmp_path / "probe.py"
    path.write_text(source, encoding="utf-8")
    assert timeout_less_calls_from_source(source) == []
    assert timeout_less_calls(path) == []


def test_pytest_timeout_budget_is_documented_in_pyproject() -> None:
    """The 120s per-test budget must stay explicit in tool.pytest.ini_options."""
    # Avoid importing tomllib only for this — pyproject is small; parse lightly.
    text = (_REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "timeout = 120" in text
    assert 'timeout_method = "thread"' in text or "timeout_method = 'thread'" in text
    assert "pytest-timeout" in (_REPO_ROOT / "requirements.txt").read_text(encoding="utf-8")
    lock = (_REPO_ROOT / "requirements-lock.txt").read_text(encoding="utf-8")
    assert "pytest-timeout==" in lock


def test_ci_pytest_invokes_timeout_flags() -> None:
    ci = (_REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert "--timeout=120" in ci
    assert "--timeout-method=thread" in ci


def test_no_timeout_less_subprocess_calls_under_tests() -> None:
    """Fail CI when a new ``subprocess.run``/``check_*``/``call`` lacks ``timeout=``."""
    offenders: list[str] = []
    for path in sorted(_TESTS_ROOT.rglob("*.py")):
        try:
            hits = timeout_less_calls(path)
        except SyntaxError as exc:
            offenders.append(f"{path}: syntax error while scanning ({exc})")
            continue
        for hit in hits:
            offenders.append(f"{path.relative_to(_REPO_ROOT)}:{hit.lineno} {hit.name}")

    assert not offenders, (
        "Timeout-less subprocess calls under tests/ (issue #5740). "
        "Pass an explicit timeout= (typically 30 for git fixtures, 60–120 for "
        "heavier scripts). Popen must bound wait()/communicate() instead.\n" + "\n".join(offenders)
    )


def test_subprocess_timeout_allowlist_is_sorted_and_valid() -> None:
    """Allowlist may be empty (endgame). Non-empty rows must be shaped and C-sorted (#7213)."""
    assert _ALLOWLIST_PATH.is_file(), f"allowlist not found at {_ALLOWLIST_PATH}"
    entries = load_allowlist(_ALLOWLIST_PATH)
    assert entries == sort_allowlist_entries(entries), SORT_ADVICE
    for entry in entries:
        validate_allowlist_entry(entry, _REPO_ROOT)


def test_no_unallowlisted_timeout_less_subprocess_calls_under_scripts() -> None:
    """Fail CI on unallowlisted timeout-less subprocess calls in scripts/ and reject stale allowlist entries (#7176)."""
    allowlist_entries = load_allowlist(_ALLOWLIST_PATH)
    actual_hits, scan_errors = scan_scripts(_SCRIPTS_ROOT, _REPO_ROOT)
    if scan_errors:
        pytest.fail("Syntax errors encountered while scanning scripts/:\n" + "\n".join(scan_errors))

    unallowlisted, stale_entries = compare_allowlist(allowlist_entries, actual_hits)
    errors: list[str] = []
    if unallowlisted:
        errors.append(UNALLOWLISTED_PREAMBLE + "\n".join(unallowlisted))
    if stale_entries:
        errors.append(STALE_PREAMBLE + "\n".join(stale_entries))

    assert not errors, "\n\n".join(errors)


_ROTATION_BEFORE = textwrap.dedent(
    """\
    import subprocess

    def helper():
        subprocess.run(["git", "status"], check=False)
        subprocess.run(["sleep", "999"], check=False)
    """
)

_ROTATION_AFTER = textwrap.dedent(
    """\
    import subprocess

    def helper():
        subprocess.run(["git", "status"], check=False, timeout=30)
        subprocess.run(["other", "cmd"], check=False)
    """
)


def test_call_shape_hash_is_location_independent_and_argument_sensitive() -> None:
    """F4: same call text keeps its hash after a line shift; a different argv does not."""
    moved = textwrap.dedent(
        """\
        import subprocess

        def helper():
            x = 1
            subprocess.run(["git", "status"], check=False)
        """
    )
    original = timeout_less_calls_from_source(_ROTATION_BEFORE)
    shifted = timeout_less_calls_from_source(moved)
    assert len(original) == 2
    assert len(shifted) == 1
    # First original call is the git-status site; moving it must keep the shape.
    assert shifted[0].shape_hash == original[0].shape_hash
    assert shifted[0].lineno != original[0].lineno
    assert original[0].shape_hash != original[1].shape_hash
    assert original[0].qualname == "helper"
    assert len(original[0].shape_hash) == SHAPE_HASH_HEX_LEN


def test_rotated_call_under_same_qualname_cannot_reuse_old_key() -> None:
    """F4: bounding one site and adding a different timeout-less call fails both ways."""
    before = timeout_less_calls_from_source(_ROTATION_BEFORE)
    after = timeout_less_calls_from_source(_ROTATION_AFTER)
    rel = "scripts/demo.py"
    before_keys = [hit.allowlist_key(rel) for hit in before]
    after_keys = [hit.allowlist_key(rel) for hit in after]
    assert len(before_keys) == 2
    assert len(after_keys) == 1
    # Old count-only key would have been path::helper::subprocess.run with count 2→1.
    # The remaining after-call must not share a shape with either before-call.
    assert after_keys[0] not in before_keys

    unallowlisted, stale = compare_allowlist(before_keys, {after_keys[0]: after})
    assert len(unallowlisted) == 1
    assert after_keys[0] in unallowlisted[0]
    assert unallowlisted[0].startswith(after_keys[0])
    stale_keys = {line.split(" ", 1)[0] for line in stale}
    assert set(before_keys) == stale_keys


def test_unallowlisted_line_is_paste_ready_key() -> None:
    """F3: the unallowlisted line starts with path::qualname::callee::shape."""
    hits = timeout_less_calls_from_source(_ROTATION_BEFORE)
    key = hits[0].allowlist_key("scripts/demo.py")
    path, qualname, callee, shape = parse_allowlist_key(key)
    assert (path, qualname, callee) == ("scripts/demo.py", "helper", "subprocess.run")
    assert len(shape) == SHAPE_HASH_HEX_LEN
    line = format_unallowlisted_line(key, lineno=hits[0].lineno, actual_count=1, allowed_count=0)
    assert line.startswith(key)
    assert line.split("  #", 1)[0] == key
    assert key.count("::") == ALLOWLIST_KEY_PARTS - 1
    assert "path::qualname::callee::shape" in UNALLOWLISTED_PREAMBLE
    with pytest.raises(ValueError, match="path::qualname::callee::shape"):
        parse_allowlist_key("scripts/demo.py::helper::subprocess.run")


def test_stale_message_mentions_rename_case() -> None:
    """F3: stale-entry copy names the rename / qualname-move case."""
    assert "renamed" in STALE_PREAMBLE
    assert "qualname" in STALE_PREAMBLE
    line = format_stale_line(
        "scripts/old.py::gone::subprocess.run::0123456789abcdef",
        allowed_count=1,
        actual_count=0,
    )
    assert line.startswith("scripts/old.py::gone::subprocess.run::0123456789abcdef")


def test_empty_allowlist_is_valid_endgame() -> None:
    """F7: burning down to zero keys must not fail CI."""
    unallowlisted, stale = compare_allowlist([], {})
    assert unallowlisted == []
    assert stale == []
    entries = load_allowlist(_ALLOWLIST_PATH)
    # File may still hold SKIP rows today; empty is legal once they go.
    assert entries == sort_allowlist_entries(entries)


def test_allowlist_sort_advice_is_c_locale() -> None:
    """F7: sort advice must not depend on the operator's libc locale."""
    assert "LC_ALL=C" in SORT_ADVICE
    # Byte order, not locale-aware str collation.
    assert sort_allowlist_entries(["b::x", "a::x", "A::x"]) == ["A::x", "a::x", "b::x"]


def test_deliberately_hanging_test_is_named_by_pytest_timeout(tmp_path: Path) -> None:
    """Prove pytest-timeout fails fast and names the hanging nodeid (#5740 AC).

    Runs an isolated child pytest so the hang cannot stall this suite. The child
    uses a 0.25-second budget; we allow a generous outer bound so flake from
    process startup does not become another hang.
    """
    hang_dir = tmp_path / "hang_suite"
    hang_dir.mkdir()
    hang_test = hang_dir / "test_intentional_hang.py"
    hang_test.write_text(
        textwrap.dedent(
            """\
            import time

            def test_intentional_forever_sleep():
                time.sleep(3600)
            """
        ),
        encoding="utf-8",
    )

    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("PYTEST_") and key not in {"PYTEST_CURRENT_TEST", "PYTEST_ADDOPTS"}
    }

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            str(hang_test),
            "-p",
            "no:xdist",
            "-p",
            "timeout",
            "--timeout=0.25",
            f"--timeout-method={_EXPECTED_TIMEOUT_METHOD}",
            "-o",
            "addopts=",
            "-q",
            "--tb=line",
        ],
        cwd=str(_REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=60,
        env=env,
    )

    combined = f"{completed.stdout}\n{completed.stderr}"
    assert completed.returncode != 0, "hanging test must fail under pytest-timeout, not pass/skip:\n" + combined
    assert "test_intentional_forever_sleep" in combined, (
        "pytest-timeout must name the hanging test in its output "
        f"(budget={_EXPECTED_PYTEST_TIMEOUT_SECONDS}s documented; child used 0.25s):\n" + combined
    )
    # Either Failed: Timeout / +++ Timeout / Failed: Timeout >… depending on version.
    assert "timeout" in combined.lower(), "expected a timeout failure signal in child pytest output:\n" + combined


def test_cli_fails_on_timeout_less_test_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """CLI fails on a temp tests/ file with a timeout-less subprocess.run (#8750)."""
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir(parents=True)
    test_file = tests_dir / "test_unbounded.py"
    test_file.write_text(
        textwrap.dedent(
            """\
            import subprocess

            def test_unbounded():
                subprocess.run(["echo", "hi"])
            """
        ),
        encoding="utf-8",
    )

    exit_code = main([str(test_file), "--root", str(tmp_path)])
    assert exit_code == 1
    err = capsys.readouterr().err
    assert TESTS_TIMEOUT_PREAMBLE.strip() in err
    assert "tests/test_unbounded.py:4 subprocess.run" in err


def test_cli_passes_on_bounded_test_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """CLI passes on a temp tests/ file when timeout= is specified (#8750)."""
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir(parents=True)
    test_file = tests_dir / "test_bounded.py"
    test_file.write_text(
        textwrap.dedent(
            """\
            import subprocess

            def test_bounded():
                subprocess.run(["echo", "hi"], timeout=30)
            """
        ),
        encoding="utf-8",
    )

    exit_code = main([str(test_file), "--root", str(tmp_path)])
    assert exit_code == 0
    err = capsys.readouterr().err
    assert err == ""


def test_cli_fails_on_unallowlisted_scripts_call_and_passes_when_allowlisted(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """CLI fails on unallowlisted scripts/ call and passes on allowlisted one (#8750)."""
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir(parents=True)
    script_file = scripts_dir / "tool.py"
    script_file.write_text(
        textwrap.dedent(
            """\
            import subprocess

            def do_work():
                subprocess.run(["echo", "hi"])
            """
        ),
        encoding="utf-8",
    )

    # 1. Unallowlisted call fails with exit code 1 and paste-ready key
    exit_code = main([str(script_file), "--root", str(tmp_path)])
    assert exit_code == 1
    err = capsys.readouterr().err
    assert UNALLOWLISTED_PREAMBLE.strip() in err
    assert "scripts/tool.py::do_work::subprocess.run::" in err

    # Extract the paste-ready key printed in stderr
    match = re.search(r"(scripts/tool\.py::do_work::subprocess\.run::[0-9a-f]{16})", err)
    assert match is not None, f"Expected paste-ready key in stderr: {err}"
    allowlist_key = match.group(1)

    # 2. Allowlisted call passes with exit code 0
    allowlist_file = tmp_path / "scripts" / "ci" / "subprocess_timeout_allowlist.txt"
    allowlist_file.parent.mkdir(parents=True, exist_ok=True)
    allowlist_file.write_text(f"{allowlist_key}\n", encoding="utf-8")

    exit_code = main([str(script_file), "--root", str(tmp_path)])
    assert exit_code == 0
    assert capsys.readouterr().err == ""


def test_cli_without_paths_agrees_with_repo_tests_on_main(capsys: pytest.CaptureFixture[str]) -> None:
    """CLI without paths agrees with repo tests on current main (both clean) (#8750)."""
    exit_code = main([])
    assert exit_code == 0
    assert capsys.readouterr().err == ""


def test_cli_help_standard(capsys: pytest.CaptureFixture[str]) -> None:
    """CLI meets the --help standard (cli-help-standard.md) (#8750)."""
    with pytest.raises(SystemExit) as exc_info:
        main(["--help"])
    assert exc_info.value.code == 0
    out = capsys.readouterr().out
    assert "Check Python files under tests/ and scripts/ for timeout-less subprocess calls." in out
    assert "Examples:" in out
    assert "Outputs:" in out
    assert "Exit codes:" in out
    assert "Related:" in out


def test_cli_syntax_error_exits_2(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """CLI exits 2 on Python syntax errors in checked files (#8750)."""
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir(parents=True)
    bad_file = tests_dir / "test_syntax.py"
    bad_file.write_text("def broken(: pass\n", encoding="utf-8")

    exit_code = main([str(bad_file), "--root", str(tmp_path)])
    assert exit_code == 2
    err = capsys.readouterr().err
    assert "syntax error while scanning" in err


def test_cli_missing_path_exits_2(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """CLI exits 2 on non-existent file paths (#8750)."""
    missing = tmp_path / "tests" / "missing.py"
    exit_code = main([str(missing), "--root", str(tmp_path)])
    assert exit_code == 2
    err = capsys.readouterr().err
    assert "path does not exist" in err
