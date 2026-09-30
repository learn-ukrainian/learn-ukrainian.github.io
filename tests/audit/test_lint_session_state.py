from __future__ import annotations

from pathlib import Path

import pytest

from scripts.audit import lint_session_state


def _write(path: Path, text: str) -> Path:
    path.write_text(text, "utf-8")
    return path


def _isolate_cli(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(lint_session_state, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(lint_session_state, "ALLOWLIST_FILE", tmp_path / "known_user_paths.yaml")
    monkeypatch.setattr(lint_session_state.Path, "home", staticmethod(lambda: tmp_path / "home"))


def test_missing_bash_secrets_exits_one_and_names_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _isolate_cli(monkeypatch, tmp_path)
    handoff = _write(tmp_path / "handoff.md", "Token was loaded from `~/.bash_secrets`.\n")

    exit_code = lint_session_state.main(["--file", str(handoff)])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert str(handoff) in output
    assert "~/.bash_secrets" in output


def test_existing_project_envrc_is_clean(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _isolate_cli(monkeypatch, tmp_path)
    handoff = _write(tmp_path / "handoff.md", "GH_TOKEN lives in `.envrc`.\n")
    _write(tmp_path / ".envrc", "export GH_TOKEN=test\n")

    assert lint_session_state.main(["--file", str(handoff)]) == 0


def test_allowlisted_codex_config_is_clean(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _isolate_cli(monkeypatch, tmp_path)
    handoff = _write(tmp_path / "handoff.md", "Codex config: `~/.codex/config.toml`.\n")
    _write(tmp_path / "known_user_paths.yaml", "paths:\n  - ~/.codex/config.toml\n")

    assert lint_session_state.main(["--file", str(handoff)]) == 0


def test_illustrative_code_block_is_not_flagged(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _isolate_cli(monkeypatch, tmp_path)
    handoff = _write(
        tmp_path / "handoff.md",
        """Example only:

```bash
# example
source ~/.bash_secrets
source ~/.notreal
```
""",
    )

    assert lint_session_state.main(["--file", str(handoff)]) == 0


@pytest.mark.parametrize(
    "typo_path",
    [
        "~/.bash_secret",
        "~/.totally_not_a_real_file_xyz",
        ".env.foofake",
        ".env.production",
        ".env.development",
        ".env.staging",
        ".env.example",
    ],
)
def test_closed_world_typos_and_variants_are_flagged(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    typo_path: str,
) -> None:
    _isolate_cli(monkeypatch, tmp_path)
    handoff = _write(tmp_path / "handoff.md", f"Check {typo_path} for secrets.\n")

    exit_code = lint_session_state.main(["--file", str(handoff)])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert typo_path in output


def test_positional_files_lint_only_the_named_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The pre-commit contract: only files handed to the hook are linted (#8354)."""
    _isolate_cli(monkeypatch, tmp_path)
    state_dir = tmp_path / "docs" / "session-state"
    state_dir.mkdir(parents=True)
    monkeypatch.setattr(lint_session_state, "SESSION_STATE_DIR", state_dir)
    stale = _write(state_dir / "stale.md", "Loaded from `~/.bash_secrets`.\n")
    touched = _write(state_dir / "touched.md", "Body-light pointer, no env refs.\n")

    assert lint_session_state.main([str(touched)]) == 0
    assert capsys.readouterr().out == ""
    # The untouched stale file still fails when linted explicitly or via --all.
    assert lint_session_state.main([str(stale)]) == 1
    assert lint_session_state.main(["--all"]) == 1


def test_committed_file_introducing_missing_env_path_still_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """AC-02: narrowing the hook keeps missing-path detection for the committed files."""
    _isolate_cli(monkeypatch, tmp_path)
    state_dir = tmp_path / "docs" / "session-state"
    state_dir.mkdir(parents=True)
    monkeypatch.setattr(lint_session_state, "SESSION_STATE_DIR", state_dir)
    clean = _write(state_dir / "clean.md", "No env references.\n")
    introduced = _write(state_dir / "new.md", "Token in `~/.brand_new_secrets`.\n")

    exit_code = lint_session_state.main([str(clean), str(introduced)])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert f"{introduced}:1:" in output
    assert "~/.brand_new_secrets" in output
    assert str(clean) not in output


def test_no_files_and_all_together_are_usage_errors(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _isolate_cli(monkeypatch, tmp_path)
    handoff = _write(tmp_path / "handoff.md", "Nothing here.\n")

    with pytest.raises(SystemExit) as no_args:
        lint_session_state.main([])
    with pytest.raises(SystemExit) as both:
        lint_session_state.main(["--all", str(handoff)])

    assert no_args.value.code == 2
    assert both.value.code == 2


def test_file_flag_is_still_accepted(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _isolate_cli(monkeypatch, tmp_path)
    handoff = _write(tmp_path / "handoff.md", "Nothing here.\n")

    assert lint_session_state.main(["--file", str(handoff)]) == 0
