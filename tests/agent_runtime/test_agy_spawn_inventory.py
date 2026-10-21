"""File-level AGY regression tripwire, not exhaustive start or enforcement proof."""

from __future__ import annotations

import ast
import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
STATUSES = frozenset({"gated", "management-exempt", "probe-exempt", "ungated-residual-10442", "generic-helper"})
GENERIC_HELPERS = frozenset({"scripts/agent_runtime/runner.py", "scripts/lib/launcher_core.sh"})

# One row per file; mixed files take the weakest applicable status.
SPAWN_INVENTORY = {
    "scripts/ops/host_stack_drift.py": (
        "probe-exempt",
        "Session-start drift report runs a literal AGY version probe without starting a model session.",
    ),
    "scripts/launchers/gemini.sh": ("gated", "Launcher validates guard registration before its model-session start."),
    "scripts/ai_agent_bridge/_model.py": ("gated", "Model check uses the guarded adapter before starting AGY."),
    "scripts/agent_runtime/runner.py": (
        "generic-helper",
        "Receives caller binaries; generic-helper rule: callers are classified by their own rows.",
    ),
    "scripts/lib/launcher_core.sh": (
        "generic-helper",
        "Executes caller argv; generic-helper rule: callers are classified by their own rows.",
    ),
    "scripts/agent_runtime/tool_config.py": ("management-exempt", "AGY MCP management permits only list and add."),
    "scripts/agent_runtime/review_mcp.py": ("management-exempt", "AGY catalog verification starts only mcp list."),
    "scripts/agent_runtime/attempt_boundary.py": (
        "probe-exempt",
        "Direct AGY start verifies the installed seat version.",
    ),
    "scripts/agent_runtime/adapters/acpx.py": (
        "ungated-residual-10442",
        "Mixed version/help probes and AGY text-agent model-session plan construction reaching the ungated ACP "
        "text agent; harness lane #10442.",
    ),
    "scripts/agent_runtime/telemetry.py": ("probe-exempt", "AGY subprocess probes the CLI version."),
    "scripts/ai_agent_bridge/_ui_agy.py": (
        "ungated-residual-10442",
        "UI sends start ungated model sessions; harness lane #10442.",
    ),
    "scripts/agent_runtime/acp_text_agent.mjs": (
        "ungated-residual-10442",
        "ACP text-agent model-session starts remain ungated; harness lane #10442.",
    ),
    "scripts/ai_agent_bridge/openai_proxy.py": (
        "ungated-residual-10442",
        "Mixed health probes and ungated proxy model sessions; weakest status, harness lane #10442.",
    ),
    "scripts/api/subscription_usage.py": (
        "ungated-residual-10442",
        "Usage command runs through an ungated prompt session; harness lane #10442.",
    ),
    "scripts/agent_runtime/adapters/agy.py": (
        "probe-exempt",
        "Mixed guarded model-session plans and an ungated version probe; probe-exempt is the weaker status.",
    ),
    "scripts/agent_runtime/env_sanitize.py": (
        "management-exempt",
        "Over-included provider metadata; direct subprocess only sanitizes Git configuration.",
    ),
    "scripts/agent_runtime/secret_print_hook.py": (
        "management-exempt",
        "Over-included harness token; starts the local command detector, not an AGY model session.",
    ),
    "scripts/ai_agent_bridge/_agy.py": (
        "ungated-residual-10442",
        "Mixed guarded shared-runtime sessions and background bridge asks that reach the ungated ACP text agent; "
        "harness lane #10442.",
    ),
    "scripts/ai_agent_bridge/_ask_lifecycle.py": (
        "ungated-residual-10442",
        "Background bridge process can request AGY through ACP; per-site session coverage remains with harness lane #10442.",
    ),
    "scripts/ai_agent_bridge/_channels_cli.py": (
        "ungated-residual-10442",
        "Mixed Git/editor tooling and ACP discussions admitting AGY sessions through the ungated ACP text agent; "
        "harness lane #10442.",
    ),
    "scripts/ai_agent_bridge/_cli.py": (
        "ungated-residual-10442",
        "Mixed CLI tooling and UI/ACP delegation; weakest status follows ungated UI/ACP sessions, harness lane #10442.",
    ),
    "scripts/ai_agent_bridge/_review_worktree.py": (
        "management-exempt",
        "Over-included review-engine metadata; direct subprocesses inspect Git blobs and diffs.",
    ),
    "scripts/audit/lint_agent_trailer.py": (
        "management-exempt",
        "Over-included agent-name metadata; subprocess reads Git history for trailer linting.",
    ),
    "scripts/build/fresh/writer.py": (
        "ungated-residual-10442",
        "AGY authoring delegation through subprocess wrappers; per-site session coverage remains with harness lane #10442.",
    ),
    "scripts/build/v7_build.py": (
        "ungated-residual-10442",
        "Mixed Git tooling and delegated writer processes; per-site AGY session coverage remains with harness lane #10442.",
    ),
    "scripts/curriculum/evidence/sense_bindings.py": (
        "management-exempt",
        "Over-included provider metadata; direct subprocess reads Git evidence.",
    ),
    "scripts/delegate.py": (
        "management-exempt",
        "Over-included agent token; direct subprocesses manage dispatch/Git tooling, while AGY plans use the guarded runtime.",
    ),
    "scripts/deploy_prompts.sh": (
        "management-exempt",
        "Over-included extension path ending in /agy; deploys configuration rather than starting a model session.",
    ),
    "scripts/entire/fleet_capture.py": (
        "management-exempt",
        "Over-included harness metadata; subprocesses read Git status and call context-capture hooks.",
    ),
    "scripts/hygiene/branch_sweep.py": (
        "management-exempt",
        "Over-included agent-name metadata; subprocesses inspect Git branches and patch IDs.",
    ),
    "scripts/ops/smoketest_bridge_stdout_only.sh": (
        "ungated-residual-10442",
        "AGY token in output-matching data plus ask-agy delegation; ACP per-site session coverage remains with harness lane #10442.",
    ),
    "scripts/orchestration/orchestrator_control.py": (
        "ungated-residual-10442",
        "Provider token plus delegate subprocess; downstream session coverage remains with harness lane #10442.",
    ),
    "scripts/orchestration/reap_worktrees.py": (
        "management-exempt",
        "Over-included provider metadata; direct subprocesses perform Git/GitHub cleanup operations.",
    ),
    "scripts/pipeline/dispatch.py": (
        "ungated-residual-10442",
        "AGY sessions delegate to ask-agy/ACP; per-site session coverage remains with harness lane #10442.",
    ),
    "scripts/projects/open_model_data/freeze_phase3_scope_circularity_firewall.py": (
        "management-exempt",
        "Over-included actor metadata; direct subprocess decompresses source objects.",
    ),
    "scripts/projects/open_model_data/phase3_cycle007_labeling_guardian.py": (
        "ungated-residual-10442",
        "Provider token plus controller subprocess; downstream session coverage remains with harness lane #10442.",
    ),
    "scripts/projects/open_model_data/phase3_rule_author_runner.py": (
        "ungated-residual-10442",
        "Author subprocess delegates to ask-agy/ACP; per-site session coverage remains with harness lane #10442.",
    ),
    "scripts/projects/open_model_data/phase3_source_production_transport.py": (
        "ungated-residual-10442",
        "Author transport delegates to ask-agy/ACP; per-site session coverage remains with harness lane #10442.",
    ),
    "scripts/review/isolation.py": (
        "probe-exempt",
        "Over-included engine metadata; process starts probe engine help/version and sandbox behavior.",
    ),
    "scripts/review/record_cf_verdict.py": (
        "management-exempt",
        "Over-included harness metadata; direct subprocess reads Git evidence for verdict publication.",
    ),
}
# The rule overrides the brief's starting exclusions: delegate.py and the hook
# import subprocess and contain literal "agy", so their rows above are required.
NON_CANDIDATES = frozenset({"scripts/agy_hooks/driver_state_inject.sh"})


def _qualified_name(node: ast.AST, aliases: dict[str, str]) -> str:
    if isinstance(node, ast.Name):
        return aliases.get(node.id, node.id)
    if isinstance(node, ast.Attribute):
        return f"{_qualified_name(node.value, aliases)}.{node.attr}"
    return ""


def _python_facts(source: str) -> tuple[bool, bool, bool]:
    """Return process capability, AGY token presence, and a process-start call."""
    tree = ast.parse(source)
    nodes = list(ast.walk(tree))
    docstrings = {
        id(node.body[0].value)
        for node in nodes
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
        and node.body
        and isinstance(node.body[0], ast.Expr)
        and isinstance(node.body[0].value, ast.Constant)
        and isinstance(node.body[0].value.value, str)
    }
    aliases = {}
    imports = set()
    for node in nodes:
        if isinstance(node, ast.Import):
            for alias in node.names:
                aliases[alias.asname or alias.name] = alias.name
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                name = f"{node.module}.{alias.name}"
                aliases[alias.asname or alias.name] = name
                imports.add(name)

    def process_api(name: str) -> bool:
        return (
            name == "subprocess"
            or name.startswith("subprocess.")
            or name == "pty"
            or name.startswith("pty.")
            or name.startswith(("os.exec", "os.spawn", "asyncio.create_subprocess"))
        )

    capable = any(process_api(name) for name in imports)
    has_agy = False
    starts = False
    for node in nodes:
        if isinstance(node, (ast.Name, ast.Attribute)):
            capable |= process_api(_qualified_name(node, aliases))
        if isinstance(node, ast.Constant) and id(node) not in docstrings and isinstance(node.value, str):
            has_agy |= node.value == "agy" or node.value.endswith("/agy")
        for field in ("id", "attr", "arg", "name", "asname"):
            identifier = getattr(node, field, None)
            if isinstance(identifier, str):
                has_agy |= any(token in identifier for token in ("agy_bin", "agy_binary", "AGY_BIN"))
        if isinstance(node, ast.Call):
            name = _qualified_name(node.func, aliases)
            starts |= name in {
                "subprocess.run",
                "subprocess.Popen",
                "subprocess.call",
                "subprocess.check_call",
                "subprocess.check_output",
                "subprocess.getoutput",
                "subprocess.getstatusoutput",
                "pty.spawn",
                "pty.fork",
            } or name.startswith(("os.exec", "os.spawn", "asyncio.create_subprocess"))
    return capable, has_agy, starts


def _text_words(source: str, suffix: str) -> set[str]:
    """Tokenize words, retaining quoted words and dropping shell/JS comments."""
    comments = r"\#[^\n]*" if suffix == ".sh" else r"//[^\n]*|/\*[\s\S]*?\*/"
    word = r"[\w./-]+"
    tokens = re.finditer(
        rf"(?P<quoted>'(?:\\.|[^'\\])*'|\"(?:\\.|[^\"\\])*\"|`(?:\\.|[^`\\])*`)"
        rf"|(?P<comment>{comments})|(?P<word>{word})",
        source,
    )
    return {value for token in tokens if token.lastgroup != "comment" for value in re.findall(word, token.group())}


def _file_facts(path: Path) -> tuple[bool, bool, bool]:
    source = path.read_text(encoding="utf-8")
    if path.suffix == ".py":
        return _python_facts(source)
    words = _text_words(source, path.suffix)
    capable = path.suffix == ".sh" or any(
        word == "child_process" or word.startswith("child_process.") for word in words
    )
    has_agy = any(word == "agy" or word.endswith("/agy") for word in words)
    starts = (
        bool(re.search(r"(?m)^\s*exec\s+(?!\d*[<>])\S+", source))
        if path.suffix == ".sh"
        else capable and bool(words & {"spawn", "exec", "execFile", "fork"})
    )
    return capable, has_agy, starts


def _candidate_files(root: Path, paths: list[str]) -> set[str]:
    candidates = set()
    for relative in paths:
        path = root / relative
        if not relative.startswith("scripts/") or path.suffix not in {".py", ".sh", ".mjs", ".js"}:
            continue
        capable, has_agy, _ = _file_facts(path)
        if capable and has_agy:
            candidates.add(relative)
    return candidates


def _assert_inventory(
    root: Path, candidates: set[str], inventory: dict[str, tuple[str, str]], helpers: frozenset[str]
) -> None:
    for relative in helpers:
        path = root / relative
        assert path.is_file(), f"disappeared generic helper: {relative}"
        assert _file_facts(path)[2], f"generic helper no longer defines a process start: {relative}"
    for relative, (status, reason) in inventory.items():
        assert status in STATUSES, f"unknown status: {relative}: {status}"
        assert reason.strip(), f"empty reason: {relative}"
        assert (status == "generic-helper") == (relative in helpers), f"generic-helper row mismatch: {relative}"
    expected = candidates | helpers
    assert set(inventory) == expected, (
        f"unclassified candidates: {sorted(expected - set(inventory))}; "
        f"no longer candidates: {sorted(set(inventory) - expected)}"
    )


@pytest.mark.repo_wide
def test_every_agy_start_has_a_current_inventory_row():
    tracked = subprocess.run(
        ["git", "ls-files", "-z", "--", "scripts/"], cwd=ROOT, capture_output=True, text=True, check=True, timeout=30
    ).stdout.split("\0")
    candidates = _candidate_files(ROOT, [path for path in tracked if path])
    assert not candidates & NON_CANDIDATES
    assert {status for status, _ in SPAWN_INVENTORY.values()} == STATUSES
    _assert_inventory(ROOT, candidates, SPAWN_INVENTORY, GENERIC_HELPERS)
