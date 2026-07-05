#!/usr/bin/env python3
"""Empirically probe which Codex edit paths fire project hooks.

The probe creates a temporary trusted Git repo under /private/tmp, installs a
minimal .codex/hooks.json, and runs nested `codex exec` prompts that ask Codex
to write through Bash and apply_patch. The hook records every payload it sees
and can exit 2 for selected tools to test whether Codex blocks the operation.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_PYTHON = REPO_ROOT / ".venv" / "bin" / "python"
DEFAULT_TIMEOUT_SECONDS = 180
TEMP_PARENT = Path("/private/tmp") if Path("/private/tmp").is_dir() else Path(tempfile.gettempdir())

HOOK_SCRIPT = """#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


def _payload() -> dict:
    try:
        return json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError as exc:
        return {"_decode_error": str(exc)}


def _tool_name(payload: dict) -> str:
    return str(payload.get("tool_name") or payload.get("tool") or payload.get("name") or "")


payload = _payload()
tool_name = _tool_name(payload)
event = str(payload.get("hook_event_name") or payload.get("event") or "")
log_path = Path(os.environ["CODEX_HOOK_PROBE_LOG"])
record = {
    "ts": datetime.now(timezone.utc).isoformat(),
    "event": event,
    "tool_name": tool_name,
    "cwd": os.getcwd(),
    "payload": payload,
}
with log_path.open("a", encoding="utf-8") as handle:
    handle.write(json.dumps(record, sort_keys=True) + "\\n")

deny_tools = {item for item in os.environ.get("CODEX_HOOK_PROBE_DENY_TOOLS", "").split(",") if item}
if tool_name in deny_tools:
    print(f"codex-hook-probe denying {tool_name}", file=sys.stderr)
    raise SystemExit(2)

raise SystemExit(0)
"""


def _hooks_json() -> dict[str, Any]:
    hook_command = (
        '"$(git rev-parse --show-toplevel)/.venv/bin/python" '
        '"$(git rev-parse --show-toplevel)/.codex/hooks/probe-hook.py"'
    )
    return {
        "hooks": {
            "PreToolUse": [
                {
                    "matcher": "^(Bash|apply_patch|Edit|Write)$",
                    "hooks": [
                        {
                            "type": "command",
                            "command": hook_command,
                            "timeout": 5,
                            "statusMessage": "Codex hook probe",
                        }
                    ],
                }
            ],
            "PostToolUse": [
                {
                    "matcher": "^(Bash|apply_patch|Edit|Write)$",
                    "hooks": [
                        {
                            "type": "command",
                            "command": hook_command,
                            "timeout": 5,
                            "statusMessage": "Codex hook probe",
                        }
                    ],
                }
            ],
        }
    }


@dataclass(frozen=True)
class ProbeCase:
    name: str
    prompt: str
    expected_file: str
    deny_tools: tuple[str, ...] = ()


PROBE_CASES = (
    ProbeCase(
        name="bash-write-allow",
        prompt=(
            "Use the Bash tool exactly once to run this command, then stop: "
            "printf 'codex shell hook probe\\n' > shell-write.txt"
        ),
        expected_file="shell-write.txt",
    ),
    ProbeCase(
        name="bash-write-deny",
        prompt=(
            "Use the Bash tool exactly once to run this command, then stop: "
            "printf 'codex shell hook deny probe\\n' > shell-denied.txt"
        ),
        expected_file="shell-denied.txt",
        deny_tools=("Bash",),
    ),
    ProbeCase(
        name="apply-patch-allow",
        prompt=(
            "Use the apply_patch tool, not a shell command, to create "
            "apply-patch-write.txt containing exactly: codex apply_patch hook probe"
        ),
        expected_file="apply-patch-write.txt",
    ),
    ProbeCase(
        name="apply-patch-deny",
        prompt=(
            "Use the apply_patch tool, not a shell command, to create "
            "apply-patch-denied.txt containing exactly: codex apply_patch denied"
        ),
        expected_file="apply-patch-denied.txt",
        deny_tools=("apply_patch", "Edit", "Write"),
    ),
)


def _run(command: list[str], cwd: Path, env: dict[str, str] | None = None, timeout: int = 30) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        env=env,
        capture_output=True,
        check=False,
        text=True,
        timeout=timeout,
    )


def _prepare_probe_repo(parent: Path) -> Path:
    repo = parent / "codex-hook-probe-repo"
    repo.mkdir()
    git_init = _run(["git", "init"], cwd=repo)
    if git_init.returncode != 0:
        raise RuntimeError(f"git init failed:\n{git_init.stderr}")

    venv_bin = repo / ".venv" / "bin"
    venv_bin.mkdir(parents=True)
    python_wrapper = venv_bin / "python"
    python_wrapper.write_text(
        "#!/usr/bin/env bash\n"
        f"exec {shlex.quote(str(PROJECT_PYTHON))} \"$@\"\n",
        encoding="utf-8",
    )
    python_wrapper.chmod(0o755)

    hook_dir = repo / ".codex" / "hooks"
    hook_dir.mkdir(parents=True)
    hook_script = hook_dir / "probe-hook.py"
    hook_script.write_text(HOOK_SCRIPT, encoding="utf-8")
    hook_script.chmod(0o755)
    (repo / ".codex" / "hooks.json").write_text(
        json.dumps(_hooks_json(), indent=2) + "\n",
        encoding="utf-8",
    )
    (repo / "README.md").write_text("# Codex hook probe\n", encoding="utf-8")
    commit = _run(["git", "add", "README.md", ".codex/hooks.json", ".codex/hooks/probe-hook.py"], cwd=repo)
    if commit.returncode != 0:
        raise RuntimeError(f"git add failed:\n{commit.stderr}")
    commit = _run(
        [
            "git",
            "-c",
            "user.name=Codex Hook Probe",
            "-c",
            "user.email=codex-hook-probe@example.invalid",
            "commit",
            "-m",
            "init probe repo",
        ],
        cwd=repo,
    )
    if commit.returncode != 0:
        raise RuntimeError(f"git commit failed:\n{commit.stderr}")
    return repo


def _load_events(log_path: Path) -> list[dict[str, Any]]:
    if not log_path.exists():
        return []
    return [
        json.loads(line)
        for line in log_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _tool_names(events: list[dict[str, Any]]) -> list[str]:
    return [
        str(event.get("tool_name") or "")
        for event in events
        if event.get("tool_name")
    ]


def _run_case(repo: Path, case: ProbeCase, model: str | None, timeout: int) -> dict[str, Any]:
    log_path = repo / f"{case.name}.jsonl"
    env = os.environ.copy()
    env["CODEX_HOOK_PROBE_LOG"] = str(log_path)
    env["CODEX_HOOK_PROBE_DENY_TOOLS"] = ",".join(case.deny_tools)

    output_file = repo / f"{case.name}-last-message.txt"
    command = [
        "codex",
        "exec",
        "--dangerously-bypass-hook-trust",
        "--dangerously-bypass-approvals-and-sandbox",
        "--cd",
        str(repo),
        "--json",
        "--output-last-message",
        str(output_file),
    ]
    if model:
        command.extend(["--model", model])
    command.append(case.prompt)

    result = _run(command, cwd=repo, env=env, timeout=timeout)
    events = _load_events(log_path)
    expected_path = repo / case.expected_file
    return {
        "case": case.name,
        "command": command,
        "returncode": result.returncode,
        "stdout_tail": "\n".join(result.stdout.splitlines()[-20:]),
        "stderr_tail": "\n".join(result.stderr.splitlines()[-40:]),
        "expected_file": case.expected_file,
        "expected_file_exists": expected_path.exists(),
        "denied_tools": list(case.deny_tools),
        "hook_event_count": len(events),
        "hook_tool_names": _tool_names(events),
        "hook_log": str(log_path),
    }


def _summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "codex_cli_version": _run(["codex", "--version"], cwd=REPO_ROOT).stdout.strip(),
        "repo_root": str(REPO_ROOT),
        "manual_source": "Codex manual Hooks section fetched via openai-docs skill",
        "results": results,
        "interpretation": {
            "bash_write_intercepted": any(
                "Bash" in result["hook_tool_names"] for result in results if result["case"].startswith("bash-write")
            ),
            "apply_patch_intercepted": any(
                any(tool in {"apply_patch", "Edit", "Write"} for tool in result["hook_tool_names"])
                for result in results
                if result["case"].startswith("apply-patch")
            ),
            "direct_edit_desktop": "Not runnable from this CLI harness; verify with the manual Desktop steps in docs/runbooks/codex-hooks.md.",
        },
    }


def _self_test() -> int:
    with tempfile.TemporaryDirectory(prefix="codex-hook-probe-selftest-", dir=TEMP_PARENT) as tmp:
        repo = _prepare_probe_repo(Path(tmp))
        hooks = json.loads((repo / ".codex" / "hooks.json").read_text(encoding="utf-8"))
        command = hooks["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
        assert ".venv/bin/python" in command
        assert "probe-hook.py" in command
        assert (repo / ".codex" / "hooks" / "probe-hook.py").exists()
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=os.environ.get("CODEX_HOOK_PROBE_MODEL"))
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument(
        "--keep-workdir",
        action="store_true",
        help="Keep the temporary probe repo and include its path in the JSON output.",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Validate probe repo generation without invoking Codex.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.self_test:
        return _self_test()

    if not PROJECT_PYTHON.exists():
        raise SystemExit(f"missing project interpreter: {PROJECT_PYTHON}")
    if not shutil.which("codex"):
        raise SystemExit("codex CLI not found on PATH")

    tmp_path = Path(tempfile.mkdtemp(prefix="codex-hook-probe-", dir=TEMP_PARENT))
    try:
        repo = _prepare_probe_repo(tmp_path)
        results = [_run_case(repo, case, args.model, args.timeout) for case in PROBE_CASES]
        summary = _summarize(results)
        if args.keep_workdir:
            summary["probe_repo"] = str(repo)
        print(json.dumps(summary, indent=2, sort_keys=True))
    finally:
        if not args.keep_workdir:
            shutil.rmtree(tmp_path, ignore_errors=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
