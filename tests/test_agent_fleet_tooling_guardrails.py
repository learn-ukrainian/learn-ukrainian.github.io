from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

ACTIVE_GUIDANCE = [
    "AGENTS.md",
    "CLAUDE.md",
    "GEMINI.md",
    "docs/RUNBOOK-BUILD.md",
    "docs/SCRIPTS.md",
    "docs/agent-bridge-setup-guide.md",
    "docs/agent-channels/shared/context.md",
    "docs/agents/AGENT-CAPABILITY-MATRIX.md",
    "docs/architecture/ARCHITECTURE.md",
    "docs/architecture/system-topology.md",
    "docs/best-practices/agent-activity-matrix.md",
    "docs/best-practices/agent-bridge.md",
    "docs/best-practices/agent-cooperation.md",
    "docs/best-practices/api-ui-improvements-proposal.md",
    "docs/best-practices/harness-engineering.md",
    "docs/best-practices/issue-tracking.md",
    "docs/best-practices/wiki-plan-review-and-lock.md",
    "docs/design/agent-runtime.md",
    "docs/guardrails/agent-fleet-tooling.md",
]

ACTIVE_GUIDANCE_GLOBS = [
    "docs/prompts/orchestrators/**/*.md",
]

ACTIVE_RUNTIME_CALLERS = [
    "scripts/audit/naturalness_check.py",
    "scripts/audit/russianism_eval.py",
    "scripts/ops/smoketest_bridge_stdout_only.sh",
    "scripts/pipeline/dispatch.py",
    "scripts/tools/upgrade_activity_hints.py",
]

FORBIDDEN_PATTERNS = [
    re.compile(r"\bab ask-(?:gemini|agy)\b"),
    re.compile(r"\bab (?:post|p|discuss)\b"),
    re.compile(r"\bask-gemini\b"),
    re.compile(r"\bGemini CLI\b"),
    re.compile(r"\bGemini Code Assist\b"),
    re.compile(r"\bgemini-3\.(?:0-flash|1-pro)-preview\b"),
    re.compile(r"\bagy --model gemini-[\w.-]+"),
]

ALLOWED_WARNING_WORDS = (
    "unsupported",
    "not supported",
    "not a current route",
    "legacy",
    "retired",
    "avoid",
    "do not",
    "wrong binary",
    "apachebench",
    "brittle",
    "resolves to apachebench",
    "historical",
    "not gemini cli",
)


def _active_guidance_paths() -> list[Path]:
    paths = [REPO_ROOT / rel_path for rel_path in ACTIVE_GUIDANCE]
    for pattern in ACTIVE_GUIDANCE_GLOBS:
        paths.extend(REPO_ROOT.glob(pattern))
    return sorted(path for path in paths if path.exists())


def test_active_guidance_does_not_reintroduce_dead_gemini_routes() -> None:
    failures: list[str] = []

    for path in _active_guidance_paths():
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            for pattern in FORBIDDEN_PATTERNS:
                if not pattern.search(line):
                    continue
                normalized = line.lower()
                if any(word in normalized for word in ALLOWED_WARNING_WORDS):
                    continue
                rel_path = path.relative_to(REPO_ROOT)
                failures.append(f"{rel_path}:{line_no}: {line.strip()}")

    assert not failures, "Dead Gemini/ab route guidance found:\n" + "\n".join(failures)


def test_guardrail_documents_current_agy_model_names() -> None:
    guardrail = (REPO_ROOT / "docs/guardrails/agent-fleet-tooling.md").read_text(encoding="utf-8")

    assert "Gemini CLI and Gemini Code Assist are unsupported" in guardrail
    assert "Gemini 3.1 Pro (High)" in guardrail
    assert ("Gemini 3.6 Flash" in guardrail) or ("gemini-3.6-flash" in guardrail) or ("Gemini 3.5 Flash (High)" in guardrail)
    assert "gemini-3.1-pro-high" in guardrail


def test_active_runtime_callers_use_agy_not_retired_gemini_cli() -> None:
    forbidden = [
        re.compile(r"\bask-gemini\b"),
        re.compile(r"\bGemini CLI\b"),
    ]
    failures: list[str] = []
    for rel in ACTIVE_RUNTIME_CALLERS:
        text = (REPO_ROOT / rel).read_text(encoding="utf-8")
        for pattern in forbidden:
            if pattern.search(text):
                failures.append(f"{rel}: {pattern.pattern}")

    assert not failures, "Retired Gemini route in active runtime caller:\n" + "\n".join(failures)
