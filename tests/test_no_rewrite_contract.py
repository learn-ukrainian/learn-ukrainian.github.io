"""
ADR-007 structural invariant: the rewrite mechanisms that were KILLed
do not reappear.

The reviewer-as-fixer policy (dec-001) is authoritative. This test is
the executable form of ADR-007's Validation §1 and §5 — see
`docs/decisions/2026-04-23-rewrite-strategies-kill-or-revert.md`.

Adding a symbol listed below to scripts/build/, or the <rewrite-block
prompt string to scripts/build/phases/, will fail CI. If you believe
a rewrite mechanism is justified, you need a new ADR that supersedes
ADR-007 — not an exception to this test.

Transitional state: PR-A (M1/M2/M3), PR-B (M4) and PR-C (M5) have
merged. PR-D (M6 rewrite-block infrastructure cleanup) has not, so
the M6 helper symbols are marked xfail(strict=True) below. When PR-D
lands, those entries will XPASS — strict mode then flips them to FAIL,
forcing the PR-D author to promote them into the active forbidden set.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

# Symbols KILLed by PR-A/PR-B/PR-C. Present in scripts/build/ → test fails.
FORBIDDEN_SYMBOLS_ACTIVE: tuple[str, ...] = (
    # PR-A (M1/M2/M3 convergence tiers)
    "section_rewrite",
    "full_rewrite",
    "writer_swap",
    "_section_rewrite_round",
    "_full_rewrite_round",
    "_writer_swap_round",
    "_build_section_rewrite_directive",
    "_build_full_rewrite_directive",
    "CONVERGENCE_MATRIX_ENFORCED",
    # PR-B (M4 reviewer <rewrite-block> protocol)
    "_parse_rewrite_blocks",
    "_apply_review_rewrite_blocks",
    # PR-C (M5 WORD_BUDGET auto-heal)
    "_apply_contract_word_budget_rewrites",
)

# M6 rewrite-block infrastructure symbols. Still live on main pending PR-D
# (ADR-007 Migration Plan §PR-D). Marked xfail(strict=True) so the test
# auto-reports when PR-D removes them.
FORBIDDEN_SYMBOLS_PENDING_PRD: tuple[str, ...] = (
    "_rewrite_block_section",
    "_dispatch_rewrite_prompt",
    "_rewrite_block_guardrails",
    "_rewrite_block_prompt_manifest",
    "_audit_rewrite_block_prompt",
    "_extract_rewrite_block_auxiliary_forbidden_literals",
)

_PRD_XFAIL = pytest.mark.xfail(
    strict=True,
    reason="ADR-007 PR-D (M6 infrastructure cleanup) not yet merged; "
    "symbol expected to be present until then.",
)

FORBIDDEN_SYMBOLS = [pytest.param(s, id=s) for s in FORBIDDEN_SYMBOLS_ACTIVE] + [
    pytest.param(s, id=s, marks=_PRD_XFAIL) for s in FORBIDDEN_SYMBOLS_PENDING_PRD
]

# Reviewer-prompt directive strings removed by PR-B. Reappearance in
# scripts/build/phases/ → test fails.
FORBIDDEN_PROMPT_STRINGS: tuple[str, ...] = (
    "<rewrite-block",
    "rewrite-block section=",
)

# Exempt lines that explicitly cite this ADR in a comment, so a future
# engineer can reference ADR-007 alongside a historical mention without
# tripping the guard.
_ADR_REF_RE = re.compile(r"ADR-?0?07|2026-04-23-rewrite-strategies")


def _scan_dir(root: Path, extensions: tuple[str, ...]) -> list[tuple[Path, int, str]]:
    hits: list[tuple[Path, int, str]] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix not in extensions:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            hits.append((path, lineno, line))
    return hits


@pytest.mark.parametrize("symbol", FORBIDDEN_SYMBOLS)
def test_rewrite_symbol_absent_from_build_code(symbol: str) -> None:
    """Every KILLed symbol is absent from scripts/build/ (except ADR refs)."""
    violations: list[str] = []
    for path, lineno, line in _scan_dir(REPO_ROOT / "scripts" / "build", (".py",)):
        if symbol not in line:
            continue
        if _ADR_REF_RE.search(line):
            continue
        violations.append(f"{path.relative_to(REPO_ROOT)}:{lineno}: {line.strip()}")

    assert not violations, (
        f"ADR-007 symbol `{symbol}` reappeared in scripts/build/:\n"
        + "\n".join(violations)
        + "\n\nSee docs/decisions/2026-04-23-rewrite-strategies-kill-or-revert.md."
        + "\nTo reintroduce, write a new ADR that supersedes ADR-007."
    )


@pytest.mark.parametrize(
    "forbidden", FORBIDDEN_PROMPT_STRINGS, ids=list(FORBIDDEN_PROMPT_STRINGS)
)
def test_rewrite_prompt_string_absent_from_phases(forbidden: str) -> None:
    """<rewrite-block> and friends are absent from phase prompts."""
    violations: list[str] = []
    for path, lineno, line in _scan_dir(
        REPO_ROOT / "scripts" / "build" / "phases", (".md", ".yaml", ".yml")
    ):
        if forbidden not in line:
            continue
        if _ADR_REF_RE.search(line):
            continue
        violations.append(f"{path.relative_to(REPO_ROOT)}:{lineno}: {line.strip()}")

    assert not violations, (
        f"ADR-007 forbidden prompt string `{forbidden}` reappeared in phases:\n"
        + "\n".join(violations)
    )


def test_convergence_loop_has_two_strategies_only() -> None:
    """ADR-007 Validation §2: select_strategy returns only "patch" or "plan_revision_request".

    Grep-based sanity check. Behavioural coverage lives in
    tests/test_convergence_loop.py.
    """
    conv_loop_path = REPO_ROOT / "scripts" / "build" / "convergence_loop.py"
    text = conv_loop_path.read_text(encoding="utf-8")
    forbidden_strategies = ("section_rewrite", "full_rewrite", "writer_swap")
    violations: list[str] = []
    for strategy in forbidden_strategies:
        idx = 0
        while True:
            pos = text.find(strategy, idx)
            if pos < 0:
                break
            window = text[max(0, pos - 80) : pos + 80]
            if not _ADR_REF_RE.search(window):
                violations.append(strategy)
                break
            idx = pos + len(strategy)

    assert not violations, (
        "convergence_loop.py references forbidden strategies: "
        + ", ".join(violations)
        + "\nSee docs/decisions/2026-04-23-rewrite-strategies-kill-or-revert.md."
    )
