"""Tests for scripts/lint/lint_test_assertions.py (#6968)."""

from __future__ import annotations

from pathlib import Path

from scripts.lint import lint_test_assertions


def test_lint_detects_hardcoded_epic_in_assertion(tmp_path: Path) -> None:
    """Hard-coding a live epic ID in an assert statement must trip the linter."""
    test_file = tmp_path / "test_example.py"
    test_file.write_text(
        'def test_broken(out):\n    assert "epic:4707" in out\n',
        encoding="utf-8",
    )

    violations = lint_test_assertions.scan_file(test_file, repo_root=tmp_path)
    assert len(violations) == 1
    v = violations[0]
    assert v.line_number == 2
    assert v.epic_id == "epic:4707"  # allow-hardcoded-epic: test linter detection
    assert 'assert "epic:4707" in out' in v.snippet  # allow-hardcoded-epic: test linter detection


def test_lint_detects_hardcoded_epic_equality_assertion(tmp_path: Path) -> None:
    """Asserting equality with a hard-coded epic ID literal must trip the linter."""
    test_file = tmp_path / "test_example.py"
    test_file.write_text(
        'def test_stream_id(stream):\n    assert stream == "epic:6943"\n',
        encoding="utf-8",
    )

    violations = lint_test_assertions.scan_file(test_file, repo_root=tmp_path)
    assert len(violations) == 1
    v = violations[0]
    assert v.line_number == 2
    assert v.epic_id == "epic:6943"  # allow-hardcoded-epic: test linter detection


def test_lint_detects_mixed_boolean_assertion(tmp_path: Path) -> None:
    """Mixed boolean assertions containing hard-coded epic literals must trip the linter."""
    test_file = tmp_path / "test_example.py"
    test_file.write_text(
        'def test_mixed(out, is_valid):\n    assert is_valid and "epic:4707" in out\n',
        encoding="utf-8",
    )

    violations = lint_test_assertions.scan_file(test_file, repo_root=tmp_path)
    assert len(violations) == 1
    assert violations[0].epic_id == "epic:4707"  # allow-hardcoded-epic: test linter detection


def test_lint_detects_hardcoded_alias(tmp_path: Path) -> None:
    """Assigning an epic ID to an alias variable and asserting on it must trip the linter."""
    test_file = tmp_path / "test_example.py"
    test_file.write_text(
        'def test_alias(out):\n    alias = "epic:4707"\n    assert alias in out\n',
        encoding="utf-8",
    )

    violations = lint_test_assertions.scan_file(test_file, repo_root=tmp_path)
    assert len(violations) == 1
    assert violations[0].epic_id == "epic:4707"  # allow-hardcoded-epic: test linter detection


def test_lint_detects_string_concatenation(tmp_path: Path) -> None:
    """Concatenating string fragments to form an epic ID must trip the linter."""
    test_file = tmp_path / "test_example.py"
    test_file.write_text(
        'def test_concat(out):\n    assert "epic:" + "4707" in out\n    assert "epic:" + str(5703) in out\n',
        encoding="utf-8",
    )

    violations = lint_test_assertions.scan_file(test_file, repo_root=tmp_path)
    assert len(violations) == 2
    epic_ids = {v.epic_id for v in violations}
    assert "epic:4707" in epic_ids  # allow-hardcoded-epic: test linter detection
    assert "epic:5703" in epic_ids  # allow-hardcoded-epic: test linter detection


def test_lint_detects_fstring_assertion(tmp_path: Path) -> None:
    """Interpolating an epic ID in an f-string must trip the linter."""
    test_file = tmp_path / "test_example.py"
    test_file.write_text(
        'def test_fstring(out):\n    num = 4707\n    assert f"epic:{num}" in out\n    assert f"epic:{5703}" in out\n',
        encoding="utf-8",
    )

    violations = lint_test_assertions.scan_file(test_file, repo_root=tmp_path)
    assert len(violations) == 2
    epic_ids = {v.epic_id for v in violations}
    assert "epic:4707" in epic_ids  # allow-hardcoded-epic: test linter detection
    assert "epic:5703" in epic_ids  # allow-hardcoded-epic: test linter detection


def test_lint_rejects_bogus_comment_bypass(tmp_path: Path) -> None:
    """Unrelated comments like '# fixtures' do NOT suppress the hard-coded epic check."""
    test_file = tmp_path / "test_example.py"
    test_file.write_text(
        'def test_bogus_comment(out):\n    # fixtures\n    assert "epic:4707" in out\n',
        encoding="utf-8",
    )

    violations = lint_test_assertions.scan_file(test_file, repo_root=tmp_path)
    assert len(violations) == 1
    assert violations[0].epic_id == "epic:4707"  # allow-hardcoded-epic: test linter detection


def test_lint_allows_real_registry_derived_constant(tmp_path: Path) -> None:
    """Deriving the expected epic ID from config or registry passes cleanly."""
    test_file = tmp_path / "test_example.py"
    test_file.write_text(
        "from scripts.config.issue_streams import load_issue_streams\n"
        "\n"
        "def test_clean(out):\n"
        "    streams = load_issue_streams()\n"
        "    infra_stream = streams['infra'].id\n"
        "    assert infra_stream in out\n",
        encoding="utf-8",
    )

    violations = lint_test_assertions.scan_file(test_file, repo_root=tmp_path)
    assert violations == []


def test_lint_allows_synthetic_epic_ids(tmp_path: Path) -> None:
    """Synthetic/mock test epic IDs (e.g. epic:9999, epic:1001) are permitted."""
    test_file = tmp_path / "test_example.py"
    test_file.write_text(
        "def test_synthetic():\n"
        '    assert "epic:9999" in {"epic:9999"}\n'
        '    assert "epic:1001" in {"epic:1001", "epic:1002"}\n'
        '    assert "epic:888001" in {"epic:888001"}\n',
        encoding="utf-8",
    )

    violations = lint_test_assertions.scan_file(test_file, repo_root=tmp_path)
    assert violations == []


def test_lint_allows_negative_assertions(tmp_path: Path) -> None:
    """Negative assertions ensuring deprecated epics are NOT emitted pass cleanly."""
    test_file = tmp_path / "test_example.py"
    test_file.write_text(
        "def test_regression_guard(text):\n"
        '    assert "epic:4707" not in text\n'
        '    assert text != "epic:5703"\n'
        '    assert not ("epic:6943" in text)\n',
        encoding="utf-8",
    )

    violations = lint_test_assertions.scan_file(test_file, repo_root=tmp_path)
    assert violations == []


def test_lint_respects_inline_directives(tmp_path: Path) -> None:
    """Explicit line-scoped directives allow designated fixture assertions."""
    test_file = tmp_path / "test_example.py"
    test_file.write_text(
        "def test_fixture_setup(db):\n"
        '    assert db.get() == "epic:4707"  # allow-hardcoded-epic: historical test\n'
        '    assert db.other() == "epic:5703"  # allow-hardcoded-epic: historical test\n'
        "    # designated-fixture: mock db fixture\n"
        '    assert db.third() == "epic:6943"\n',
        encoding="utf-8",
    )

    violations = lint_test_assertions.scan_file(test_file, repo_root=tmp_path)
    assert violations == []


def test_lint_cli_main_exit_codes(tmp_path: Path, capsys) -> None:
    """CLI returns 0 on clean scan and 1 on violations."""
    clean_file = tmp_path / "test_clean.py"
    clean_file.write_text("def test_ok():\n    assert 1 == 1\n", encoding="utf-8")

    assert lint_test_assertions.main([str(clean_file), "--root", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "OK: no forbidden hard-coded epic/stream assertions" in out

    dirty_file = tmp_path / "test_dirty.py"
    dirty_file.write_text('def test_bad():\n    assert "epic:6943" in "epic:6943"\n', encoding="utf-8")

    assert lint_test_assertions.main([str(dirty_file), "--root", str(tmp_path)]) == 1
    err = capsys.readouterr().err
    assert "Forbidden hard-coded epic assertions found in tests:" in err
    assert "epic:6943" in err  # allow-hardcoded-epic: test linter detection


def test_repo_test_suite_is_clean() -> None:
    """The repository test suite must have zero forbidden hard-coded epic assertions."""
    violations = lint_test_assertions.find_stale_pinned_assertions()
    assert violations == [], f"Found stale pinned epic assertions in tests: {violations}"
