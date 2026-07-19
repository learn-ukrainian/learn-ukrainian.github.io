"""start-grok.sh launcher: --epic env export + cold-start auto-continue prompt."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_LAUNCHER = _REPO_ROOT / "start-grok.sh"


def _write_executable(path: Path, body: str) -> None:
    path.write_text(body, encoding="utf-8")
    path.chmod(0o755)


def _run_launcher(
    tmp_path: Path,
    arguments: list[str],
) -> tuple[dict[str, str], str, subprocess.CompletedProcess[str]]:
    """Run start-grok.sh with a fake grok binary that captures env + argv."""
    home = tmp_path / "home"
    grok_bin_dir = home / ".grok" / "bin"
    grok_bin_dir.mkdir(parents=True)
    capture = tmp_path / "capture.txt"

    _write_executable(
        grok_bin_dir / "grok",
        f"""#!/usr/bin/env bash
if [[ "${{1:-}}" == "--version" ]]; then
  echo "test-grok 0.0.0"
  exit 0
fi
{{
  printf 'session_epic=%s\\n' "${{SESSION_EPIC-unset}}"
  printf 'session_stream=%s\\n' "${{SESSION_STREAM_ID-unset}}"
  printf 'handoff=%s\\n' "${{SESSION_HANDOFF_AGENT-unset}}"
  printf 'launch=%s\\n' "${{LEARN_UKRAINIAN_GROK_LAUNCH-unset}}"
  printf 'argv='
  printf '%s\\0' "$@"
  printf '\\n'
}} > "{capture}"
""",
    )

    env = os.environ.copy()
    for name in (
        "SESSION_EPIC",
        "SESSION_STREAM_ID",
        "SESSION_HANDOFF_AGENT",
        "LEARN_UKRAINIAN_GROK_LAUNCH",
    ):
        env.pop(name, None)
    env["HOME"] = os.fspath(home)
    env["PATH"] = f"{grok_bin_dir}:{env.get('PATH', '')}"

    result = subprocess.run(
        [os.fspath(_LAUNCHER), *arguments],
        cwd=_REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )
    raw = capture.read_text(encoding="utf-8") if capture.exists() else ""
    values: dict[str, str] = {}
    argv_blob = ""
    for line in raw.splitlines():
        if line.startswith("argv="):
            argv_blob = line[len("argv=") :]
            continue
        if "=" in line:
            k, _, v = line.partition("=")
            values[k] = v
    return values, argv_blob, result


def test_epic_atlas_exports_env_and_injects_cold_start_prompt(tmp_path: Path) -> None:
    values, argv_blob, result = _run_launcher(tmp_path, ["--epic", "atlas"])
    assert result.returncode == 0, result.stderr + result.stdout
    assert values["session_epic"] == "atlas"
    assert values["session_stream"] == "epic:4387"
    assert values["handoff"] == "grok-atlas"
    assert values["launch"] == "1"
    # Null-separated argv from fake grok; last non-empty token is the prompt.
    parts = [p for p in argv_blob.split("\0") if p]
    assert parts, "expected grok argv"
    prompt = parts[-1]
    assert "ATLAS" in prompt or "atlas" in prompt.lower()
    assert "TAKEOVER-PROMPT.md" in prompt
    assert "epic:4387" in prompt
    assert "--model" in parts
    assert "grok-4.5" in parts
    assert "--always-approve" in parts


def test_epic_equals_form_and_explicit_prompt_skips_inject(tmp_path: Path) -> None:
    values, argv_blob, result = _run_launcher(
        tmp_path,
        ["--epic=atlas", "only do the cloze batch"],
    )
    assert result.returncode == 0, result.stderr + result.stdout
    assert values["session_epic"] == "atlas"
    parts = [p for p in argv_blob.split("\0") if p]
    assert parts[-1] == "only do the cloze batch"
    assert "TAKEOVER-PROMPT.md" not in parts[-1]


def test_no_epic_no_cold_start_prompt(tmp_path: Path) -> None:
    values, argv_blob, result = _run_launcher(tmp_path, [])
    assert result.returncode == 0, result.stderr + result.stdout
    assert values["session_epic"] == "unset"
    parts = [p for p in argv_blob.split("\0") if p]
    # Flags only — no free-text cold-start prompt.
    assert all(p.startswith("-") or p in {"grok-4.5", "high"} or Path(p).is_absolute() for p in parts)
