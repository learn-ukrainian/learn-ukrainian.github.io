"""Serialize the existing worker guards and reviewer grants for native dispatches."""

from __future__ import annotations

import argparse
import fnmatch
import importlib.util
import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.agent_runtime.adapters.claude import REVIEWER_PERMISSION_PROFILE, _worker_guard_settings
from scripts.agent_runtime.review_mcp import isolated_sources_mcp_config, sources_server_launch
from scripts.agent_runtime.sources_read_only import sources_tool_sets
from scripts.common.repo_root import project_interpreter
from scripts.dispatcher.types import TaskSpec
from scripts.lib import rules_core


def sources_config() -> dict:
    """Use the trusted dispatcher server, never the reviewed checkout's MCP config."""
    try:
        interpreter, server = sources_server_launch()
        if not interpreter.is_file() or not server.is_file() or "verify_word" not in sources_tool_sets()[0]:
            raise ValueError("Sources runtime unavailable")
        return isolated_sources_mcp_config(interpreter, server)
    except (OSError, ValueError, SyntaxError, StopIteration) as exc:
        raise ValueError("review_sources_unavailable: trusted Sources runtime cannot attach") from exc


def shell_denies() -> tuple[str, ...]:
    return tuple(rule[5:-1] for rule in REVIEWER_PERMISSION_PROFILE["deny"] if rule.startswith("Bash("))


def review_allow_csv(source_tools) -> str:
    return ",".join([*REVIEWER_PERMISSION_PROFILE["allow"], *(f"mcp__sources__{name}" for name in sorted(source_tools))])


def guard_runtime_reads() -> tuple[Path, ...]:
    """Trusted guard code and the project environment, mounted read-only in attempt sandboxes."""
    root = Path(__file__).resolve().parents[2]
    metadata = (root / ".git",) if (root / ".git").is_file() else ()
    return (*metadata, rules_core.source_path("scripts"), rules_core.source_path("agents_extensions/shared/hooks"),
            rules_core.source_path("agents_extensions/shared/settings.json"),
            rules_core.source_path(".mcp/servers/sources/server.py"),
            sources_server_launch()[1], project_interpreter().parent.parent)


def toml(value) -> str:
    if isinstance(value, dict):
        return "{" + ",".join(f"{json.dumps(key)}={toml(item)}" for key, item in value.items()) + "}"
    if isinstance(value, (list, tuple)):
        return "[" + ",".join(map(toml, value)) + "]"
    return json.dumps(value, ensure_ascii=False)


def hook_command(*, harness: str, review: bool) -> str:
    return shlex.join([str(project_interpreter()), "-I", str(Path(__file__).resolve()), harness,
                       "review" if review else "work"])


def hooks(*, harness: str, review: bool) -> dict:
    return {"PreToolUse": [{"matcher": "*", "hooks": [{
        "type": "command", "command": hook_command(harness=harness, review=review), "timeout": 180,
    }]}]}


def checkout_interpreter(worktree: Path) -> None:
    """Expose the project venv without replacing any checkout-provided interpreter."""
    target = project_interpreter().parent.parent
    local = worktree / ".venv"
    if os.path.lexists(local):
        if not local.is_symlink() or local.resolve(strict=True) != target.resolve(strict=True):
            raise ValueError("review_interpreter_conflict: checkout .venv is not the project interpreter")
    else:
        local.symlink_to(target, target_is_directory=True)


def stage_file(worktree: Path, relative: str, content: str | bytes) -> Path:
    """Stage native configuration only in the dispatcher's already validated checkout."""
    path = worktree / relative
    for directory in reversed(path.parent.relative_to(worktree).parents):
        candidate = worktree / directory
        if candidate.is_symlink():
            raise ValueError("review_config_symlink_refused")
    if path.parent.is_symlink():
        raise ValueError("review_config_symlink_refused")
    if os.path.lexists(path) and (path.is_symlink() or path.stat().st_nlink != 1):
        raise ValueError("review_config_link_refused")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(content.encode("utf-8") if isinstance(content, str) else content)
    return path


def write_config(worktree: Path, relative: str, value: dict) -> Path:
    return stage_file(worktree, relative, json.dumps(value, separators=(",", ":")))


def native_sources(route: str) -> dict:
    """Convert the same Sources definition to a native MCP entry."""
    source = sources_config()["mcpServers"]["sources"]
    if route == "opencode":
        return {"type": "local", "command": [source["command"], *source["args"]], "enabled": True}
    if route == "codex":
        source["required"] = True
    elif route == "muse":
        source["mode"] = "required"
    return source


def cursor_config(spec: TaskSpec) -> None:
    review = spec.mode == "read-only"
    readers, writers = sources_tool_sets()
    denies = [f"Mcp(sources:{name})" for name in writers]
    if review:
        denies += ["Write(**)", *("Shell(" + pattern.replace(" ", ":", 1) + ")" for pattern in shell_denies())]
    write_config(spec.worktree, ".cursor/mcp.json", sources_config())
    write_config(spec.worktree, ".cursor/sandbox.json", {"networkPolicy": {"default": "allow"}})
    write_config(spec.worktree, ".cursor/cli.json", {"permissions": {
        "allow": ["Shell(*)", "Read(**)", "WebFetch(*)", *(f"Mcp(sources:{name})" for name in readers)],
        "deny": denies,
    }})
    write_config(spec.worktree, ".cursor/hooks.json", {"version": 1, "hooks": {
        "beforeShellExecution": [{"command": hook_command(harness="cursor", review=review)}],
    }})


def _publish_guard():
    path = rules_core.source_path("agents_extensions/shared/hooks/guard-reviewer-publish.py")
    spec = importlib.util.spec_from_file_location("dispatch_publish_guard", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def shell_blocked(command: str, depth: int = 0) -> str | None:
    """Reuse the worker parser so git -C and shell wrappers keep the same deny set."""
    if depth > 8:
        return "nested shell inspection limit"
    guard = _publish_guard()
    parser = guard._shell_parser()
    if reason := guard.blocked(command, parser):
        return reason
    for segment in parser._expanded_segments(command):
        segment = parser._without_redirects(segment)
        binary, index = parser._command_word(segment)
        args = [str(word) for word in segment[index + 1:]]
        if binary == "git":
            _, _, args = parser._git_global_prefix(args)
        elif binary in {"bash", "sh"}:
            for index, arg in enumerate(args[:-1]):
                if arg.startswith("-") and "c" in arg[1:] and (reason := shell_blocked(args[index + 1], depth + 1)):
                    return reason
        normalized = " ".join([binary or "", *args])
        if any(fnmatch.fnmatchcase(normalized, pattern) or normalized == pattern.removesuffix(" *")
               for pattern in shell_denies()):
            return "review mutation command"
    return None


def prepare(spec: TaskSpec) -> dict[Path, bytes | None]:
    """Prepare native files before spawn, never during a dry-run invocation build."""
    _ignore_runtime(spec.worktree)
    originals = {}
    if not os.path.lexists(spec.worktree / ".venv"):
        originals[spec.worktree / ".venv"] = None
    try:
        checkout_interpreter(spec.worktree)
        _prepare_native(spec, originals)
    except BaseException:
        restore(spec.worktree, originals)
        raise
    return originals


def _ignore_runtime(worktree: Path) -> None:
    """Keep provisioned runtime artifacts out of delivery, using only this worktree's config."""
    if not (worktree / ".git").is_file():
        return

    def git(*args: str) -> subprocess.CompletedProcess:
        return subprocess.run(["git", "-C", str(worktree), *args], capture_output=True, text=True, timeout=10)

    paths = (".venv", ".agent/dispatch-tools/")
    if all(git("check-ignore", "--quiet", path).returncode == 0 for path in paths):
        return
    metadata = git("rev-parse", "--absolute-git-dir")
    if metadata.returncode:
        raise ValueError("review_runtime_git_context_unavailable")
    existing = git("config", "--path", "--get", "core.excludesFile")
    default = Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))) / "git/ignore"
    source = Path(existing.stdout.strip()) if existing.returncode == 0 else default
    content = source.read_bytes() if source.is_file() else b""
    root = Path(metadata.stdout.strip())
    target = stage_file(root, "dispatch-runtime-excludes", content + b"\n/.venv\n/.agent/dispatch-tools/\n")
    result = git("config", "--worktree", "core.excludesFile", str(target))
    if result.returncode:
        raise ValueError("review_runtime_git_excludes_unavailable")


def _prepare_native(spec: TaskSpec, originals: dict[Path, bytes | None]) -> None:
    if spec.agent == "cursor":
        for name in ("mcp.json", "sandbox.json", "cli.json", "hooks.json"):
            path = spec.worktree / ".cursor" / name
            if path.is_symlink() or path.parent.is_symlink():
                raise ValueError("review_config_link_refused")
            originals[path] = path.read_bytes() if path.exists() else None
        cursor_config(spec)
    if spec.agent == "opencode" and spec.mode == "read-only":
        command = shlex.split(hook_command(harness="opencode", review=True))
        script = '''import { spawnSync } from 'node:child_process';
export const ReviewGuards = async () => ({
  'tool.execute.before': async (input, output) => {
    if (input.tool !== 'bash') return;
    const result = spawnSync(COMMAND[0], COMMAND.slice(1), {
      input: JSON.stringify({tool_name: 'Bash', tool_input: output.args, cwd: process.cwd()}),
      encoding: 'utf8', timeout: 170000
    });
    if (result.error || result.status !== 0) throw new Error('review_mutation_denied');
  }
});
'''.replace("COMMAND", json.dumps(command))
        stage_file(spec.worktree, ".agent/dispatch-tools/review-guards.mjs", script)
    if spec.agent == "agy" and spec.mode == "workspace-write":
        from scripts.agent_runtime.agy_hook_config import GUARD_NAME, guard_registration
        from scripts.agent_runtime.review_mcp import _real_agy_token

        write_config(spec.worktree, ".agent/dispatch-tools/agy-home/.gemini/config/mcp_config.json", sources_config())
        write_config(spec.worktree, ".agent/dispatch-tools/agy-home/.gemini/config/hooks.json", {
            GUARD_NAME: guard_registration(), "dispatch-worker-guards": hooks(harness="agy", review=False),
        })
        app = ".agent/dispatch-tools/agy-home/.gemini/antigravity-cli"
        write_config(spec.worktree, app + "/settings.json", {"permissions": {
            "deny": [f"mcp(sources/{name})" for name in sources_tool_sets()[1]],
        }})
        token = spec.worktree / app / "antigravity-oauth-token"
        source = _real_agy_token()
        if not os.path.lexists(token):
            token.symlink_to(source)
        elif not token.is_symlink() or token.resolve(strict=True) != source.resolve(strict=True):
            raise ValueError("agy_dispatch_auth_link_refused")


def restore(worktree: Path, originals: dict[Path, bytes | None]) -> None:
    for path, content in originals.items():
        if content is None:
            path.unlink(missing_ok=True)
        else:
            stage_file(worktree, path.relative_to(worktree).as_posix(), content)


def check(payload: dict, *, review: bool) -> str | None:
    name = payload.get("tool_name", "")
    if name in {f"mcp__sources__{writer}" for writer in sources_tool_sets()[1]}:
        return "Sources writer unavailable"
    if review and name in REVIEWER_PERMISSION_PROFILE["deny"]:
        return "review write tool"
    if name == "Bash" and review and (reason := shell_blocked(payload.get("tool_input", {}).get("command", ""))):
        return reason
    groups = json.loads(_worker_guard_settings(publish_guard=review))["hooks"]["PreToolUse"]
    for group in groups:
        if not re.search(group.get("matcher", ""), name):
            continue
        for hook in group["hooks"]:
            result = subprocess.run(shlex.split(hook["command"]), input=json.dumps(payload), text=True,
                                    capture_output=True, timeout=hook.get("timeout", 30))
            if result.returncode:
                return "worker guard refused " + Path(shlex.split(hook["command"])[-1]).name
    return None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Apply the shared worker guards to one native tool event.\n"
                    "Internal dispatch hook; do not use it to execute a command.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Example: .venv/bin/python scripts/dispatcher/review_tools.py claude review < event.json\n"
               "Outputs: native allow/deny decision; no command execution or persistent writes.\n"
               "Exit codes: 0 allowed or a native JSON decision; 2 denied or invalid arguments.\n"
               "Related: shared worker guards; review-loop; #12378.",
    )
    parser.add_argument("harness", choices=("claude", "codex", "agy", "cursor", "muse", "opencode"),
                        help="Native event dialect, for example cursor.")
    parser.add_argument("mode", choices=("review", "work"), help="Task authority, for example review.")
    args = parser.parse_args()
    harness, mode = args.harness, args.mode
    try:
        payload = json.load(sys.stdin)
        if harness == "muse" and payload.get("tool_name") in {"shell", "run_shell"}:
            payload["tool_name"] = "Bash"
        if harness == "cursor":
            payload = {"tool_name": "Bash", "tool_input": {"command": payload["command"]},
                       "cwd": payload["cwd"]}
        elif harness == "agy":
            from scripts.agent_runtime.secret_print_hook import extract_command

            command = extract_command("agy", payload)
            call = payload.get("toolCall")
            inputs = call.get("args") if isinstance(call, dict) else payload.get("tool_input")
            inputs = dict(inputs) if isinstance(inputs, dict) else {}
            if "Cwd" in inputs:
                inputs["cwd"] = inputs.pop("Cwd")
            inputs["command"] = command
            payload = {"tool_name": "Bash" if command is not None else "", "tool_input": inputs,
                       "cwd": payload.get("cwd", os.getcwd())}
        reason = check(payload, review=mode == "review")
    except Exception:
        reason = "worker guard inspection failed"
    if harness == "cursor":
        print(json.dumps({"permission": "deny" if reason else "allow",
                          "user_message": reason or "", "agent_message": reason or ""}))
        return 0
    if harness == "agy":
        print(json.dumps({"permission": "deny" if reason else "allow", "reason": reason or ""}))
        return 0
    if reason:
        print("review_mutation_denied: " + reason, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
