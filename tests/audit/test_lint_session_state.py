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
