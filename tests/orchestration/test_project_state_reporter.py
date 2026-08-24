"""Tests for the project-state reporter bash wrapper (#7188)."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_run_project_state_reporter_resolves_repo_root(tmp_path: Path) -> None:
    tree = tmp_path / "fixture-repo"
    script_src = REPO_ROOT / "scripts" / "orchestration" / "run_project_state_reporter.sh"
    dest_script = tree / "scripts" / "orchestration" / "run_project_state_reporter.sh"
    dest_script.parent.mkdir(parents=True)
    dest_script.write_text(script_src.read_text(encoding="utf-8"), encoding="utf-8")
    dest_script.chmod(0o755)

    local_py = tree / "scripts" / "api" / "project_state_local.py"
    local_py.parent.mkdir(parents=True)
    local_py.write_text("# stub\n", encoding="utf-8")

    invoked = tmp_path / "invoked.txt"
    wrapper = tmp_path / "python.sh"
    wrapper.write_text(
        f"""#!/usr/bin/env bash
printf '%s' "$1" > {invoked}
exit 0
""",
        encoding="utf-8",
    )
    wrapper.chmod(0o755)

    env = {**os.environ, "LEARN_UKRAINIAN_PYTHON": str(wrapper)}
    result = subprocess.run(
        ["bash", str(dest_script)],
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert invoked.read_text(encoding="utf-8") == str(local_py)
