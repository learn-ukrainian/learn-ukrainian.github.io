"""Entry-point denominator for the hook runtime audit (#9807).

Every Python module and shell file under ``agents_extensions/*/hooks/`` and
``scripts/hooks/`` is classified once. A file that is not in this table fails
the audit. A skipped path is not a pass.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from tests.test_hook_single_parser import REPO_ROOT, analyze_repository

COMMAND_PROCESSING = "command-processing entry point"
LIBRARY = "library"
MAINTENANCE = "maintenance tool"
SESSION_HOOK = "session hook"
SHELL_WRAPPER = "shell wrapper"

# Explicit on purpose. A new hook file must be classified in this change.
CLASSIFICATION: dict[str, str] = {
    "agents_extensions/shared/hooks/guard-admin-merge.py": COMMAND_PROCESSING,
    "agents_extensions/shared/hooks/guard-branch-switch-in-main.py": COMMAND_PROCESSING,
    "agents_extensions/shared/hooks/guard-pr-merge.py": COMMAND_PROCESSING,
    "agents_extensions/shared/hooks/guard-primary-checkout-write.py": COMMAND_PROCESSING,
    "agents_extensions/shared/hooks/guard-public-github-text.py": COMMAND_PROCESSING,
    "agents_extensions/shared/hooks/guard-reviewer-publish.py": COMMAND_PROCESSING,
    "agents_extensions/shared/hooks/guard-secret-print.py": COMMAND_PROCESSING,
    "agents_extensions/shared/hooks/heal-core-bare.py": COMMAND_PROCESSING,
    "agents_extensions/shared/hooks/shell_redirects.py": LIBRARY,
    "agents_extensions/shared/hooks/shell_shlex.py": LIBRARY,
    "agents_extensions/shared/hooks/auto-audit.sh": SHELL_WRAPPER,
    "agents_extensions/shared/hooks/auto-deploy-agent-extensions.sh": SHELL_WRAPPER,
    "agents_extensions/shared/hooks/check-agent-inbox.sh": SHELL_WRAPPER,
    "agents_extensions/shared/hooks/context-monitor.sh": SHELL_WRAPPER,
    "agents_extensions/shared/hooks/context-rollover-guard.sh": SHELL_WRAPPER,
    "agents_extensions/shared/hooks/context-rollover-lib.sh": SHELL_WRAPPER,
    "agents_extensions/shared/hooks/enforce-venv.sh": SHELL_WRAPPER,
    "agents_extensions/shared/hooks/goal-driver-stop.sh": SHELL_WRAPPER,
    "agents_extensions/shared/hooks/post-compact.sh": SHELL_WRAPPER,
    "agents_extensions/shared/hooks/release-thread-lease.sh": SHELL_WRAPPER,
    "agents_extensions/shared/hooks/session-setup.sh": SHELL_WRAPPER,
    "agents_extensions/shared/hooks/stamp-pytest.sh": SHELL_WRAPPER,
    "agents_extensions/shared/hooks/tool-timing.sh": SHELL_WRAPPER,
    "scripts/hooks/__init__.py": LIBRARY,
    "scripts/hooks/apply_grok_hook_profile.py": MAINTENANCE,
    "scripts/hooks/hook_timing.py": MAINTENANCE,
    "scripts/hooks/measure_hook_stack.py": MAINTENANCE,
    "scripts/hooks/run_hook_timed.sh": SHELL_WRAPPER,
    "scripts/hooks/session_start_gate.py": SESSION_HOOK,
}

EXCLUSION_REASONS = {
    LIBRARY: "library imported by hooks; not an entry point",
    MAINTENANCE: "maintenance CLI; running it writes config or launches hooks",
    SESSION_HOOK: "session hook; running it can claim a lease",
    SHELL_WRAPPER: "shell script; the audit hook covers Python entry points",
}

_DEPLOY_SOURCES = (
    REPO_ROOT / "agents_extensions" / "shared" / "settings.json",
    REPO_ROOT / "agents_extensions" / "codex" / "hooks.json",
)


@dataclass(frozen=True)
class Surface:
    path: str
    category: str
    reason: str


def hook_root_files(root: Path = REPO_ROOT) -> tuple[str, ...]:
    """Every file under the hook roots. Unclassified files fail the audit."""
    found: list[str] = []
    agents = root / "agents_extensions"
    if agents.is_dir():
        for entry in sorted(agents.iterdir()):
            hooks = entry / "hooks"
            if not hooks.is_dir():
                continue
            for path in sorted(hooks.rglob("*")):
                if not path.is_file() or "__pycache__" in path.parts:
                    continue
                found.append(path.relative_to(root).as_posix())
    scripts_hooks = root / "scripts" / "hooks"
    if scripts_hooks.is_dir():
        for path in sorted(scripts_hooks.rglob("*")):
            if not path.is_file() or "__pycache__" in path.parts:
                continue
            found.append(path.relative_to(root).as_posix())
    return tuple(found)


def unclassified(root: Path = REPO_ROOT) -> tuple[str, ...]:
    return tuple(path for path in hook_root_files(root) if path not in CLASSIFICATION)


def command_processing_paths() -> tuple[str, ...]:
    return tuple(path for path, category in sorted(CLASSIFICATION.items()) if category == COMMAND_PROCESSING)


def _walk_commands(node: object, found: list[tuple[str, str]]) -> None:
    if isinstance(node, dict):
        command = node.get("command")
        matcher = node.get("matcher")
        if isinstance(command, str):
            found.append((command, matcher if isinstance(matcher, str) else ""))
        for value in node.values():
            _walk_commands(value, found)
    elif isinstance(node, list):
        for item in node:
            _walk_commands(item, found)


def deployment_commands() -> tuple[tuple[str, str], ...]:
    """``(command, matcher)`` pairs from the shared and Codex hook manifests."""
    found: list[tuple[str, str]] = []
    for path in _DEPLOY_SOURCES:
        payload = json.loads(path.read_text(encoding="utf-8"))
        _walk_commands(payload.get("hooks", {}), found)
    return tuple(found)


def _source_for_command(command: str) -> str | None:
    """Map a deployed hook path back to a classified source file, when one exists."""
    for path in CLASSIFICATION:
        name = path.rsplit("/", 1)[-1]
        if name and name in command:
            return path
    return None


def excluded_surfaces() -> tuple[Surface, ...]:
    """Surfaces the corpus does not execute. Each one is named, not skipped silently."""
    surfaces = [
        Surface(path, category, EXCLUSION_REASONS[category])
        for path, category in sorted(CLASSIFICATION.items())
        if category != COMMAND_PROCESSING
    ]
    helpers = analyze_repository().production_helpers
    for path in helpers:
        surfaces.append(
            Surface(path, "production-parsing-helper", "scanned by the static checker; not a hook entry point")
        )
    for command, matcher in deployment_commands():
        if "sh -c" in command or command.startswith("echo "):
            surfaces.append(Surface(command, "inline-shell", "deployment command is inline shell, not a Python entry"))
            continue
        source = _source_for_command(command)
        if source is None:
            surfaces.append(Surface(command, "deployment-outside-hook-roots", "not a file under the hook roots"))
            continue
        if "Write" in matcher or "Edit" in matcher or "MultiEdit" in matcher:
            surfaces.append(
                Surface(
                    f"{matcher} -> {source}",
                    "non-bash-contract",
                    "file-path contract; the module is driven through Bash stdin",
                )
            )
    return tuple(surfaces)


def denominator_text(*, rows: list[tuple[str, int, int, int, str]]) -> str:
    """Human-readable pair counts and excluded surfaces for the test output."""
    lines = ["hook runtime denominator"]
    lines.append(f"{'entry':<64} {'inputs':>7} {'done':>7} {'violations':>11}  status")
    for entry, inputs, done, violations, status in rows:
        name = entry.rsplit("/", 1)[-1]
        lines.append(f"{name:<64} {inputs:7d} {done:7d} {violations:11d}  {status}")
    lines.append("excluded surfaces:")
    for surface in excluded_surfaces():
        shown = surface.path if len(surface.path) < 160 else surface.path[:157] + "..."
        lines.append(f"  [{surface.category}] {shown} — {surface.reason}")
    return "\n".join(lines)
