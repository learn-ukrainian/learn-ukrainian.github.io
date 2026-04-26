"""CI invariant — thresholds live in exactly one file.

Guards against drift by rejecting:
  1. Module-level re-declarations of any canonical threshold name.
  2. Float literals (8.0 / 9.0 / 8.5 / 6.0) used in threshold-adjacent
     contexts anywhere in ``scripts/`` outside the source-of-truth module.

Related incident: ISTORIO 3500 vs 4000 drift (Jan 2026), recorded in
``claude_extensions/rules/non-negotiable-rules.md`` §1. EPIC #1451 P2-A.
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from common.thresholds import (
    REVIEW_PASS_FLOOR,
    REVIEW_REJECT_FLOOR,
    STYLE_REVIEW_DIMENSION_FLOOR,
    STYLE_REVIEW_TARGET,
)

SCRIPTS_ROOT = Path(__file__).resolve().parent.parent / "scripts"
SOURCE_OF_TRUTH = SCRIPTS_ROOT / "common" / "thresholds.py"

# Canonical names that must never be redeclared outside the source-of-truth.
# The values are the source-of-truth values — any other file claiming to
# own these names (at module scope) is a regression.
_CANONICAL_NAMES: frozenset[str] = frozenset({
    "REVIEW_PASS_FLOOR",
    "REVIEW_REJECT_FLOOR",
    "STYLE_REVIEW_TARGET",
    "STYLE_REVIEW_DIMENSION_FLOOR",
    "LEVEL_THRESHOLDS",
})

# Float literals that are threshold-valued. 5.0 / 7.0 are common but not
# pipeline thresholds; we deliberately do not list them.
_THRESHOLD_VALUES: frozenset[float] = frozenset({
    REVIEW_PASS_FLOOR,
    REVIEW_REJECT_FLOOR,
    STYLE_REVIEW_TARGET,
    STYLE_REVIEW_DIMENSION_FLOOR,
})

# Words that make a nearby float literal "look like" a threshold. If none
# of these appear within 3 lines of the literal, we don't flag — an 8.0
# in a test-weight matrix is fine.
_THRESHOLD_CONTEXT_WORDS: tuple[str, ...] = (
    "threshold", "floor", "target", "min_score", "minscore",
    "pass_floor", "reject_floor", "revise", "review_score",
    "review_target", "review_pass", "style_review",
    "naturalness_min", "naturalness_threshold",
)

# Precise content-based allow-list for legitimate non-threshold float
# literals that happen to look like thresholds. Each entry is
# (relative_posix_path, compiled_regex) matched against ``line.strip()``.
# Keep this short; prefer migrating over extending.
_FLOAT_LITERAL_ALLOWLIST: tuple[tuple[str, re.Pattern[str]], ...] = (
    # scoring/report.py display heuristic: "show criteria below 9" —
    # not a pipeline pass/fail threshold, belongs to a separate scoring
    # domain. One regex covers both occurrences (lines 205 and 400 in
    # current main — content-based match is line-number-agnostic).
    ("scoring/report.py", re.compile(r"^if score < 9\.0:$")),
    # review_validation.py gaming-detection heuristic: if ALL dims scored
    # ≥9 without substantive issues → suspicious. Independent of
    # STYLE_REVIEW_TARGET (they share the number by coincidence).
    (
        "audit/checks/review_validation.py",
        re.compile(r"^if min_score >= 9\.0 and not has_real_issues:$"),
    ),
    # scoring/caps.py max_score= entries: these CAP a track's score at a
    # value when a content-quality metric fails (e.g., zero [!quote]
    # blocks → cap at 6.0). They are cap values, not pipeline
    # pass/fail gates, and the specific numbers encode per-criterion
    # penalties chosen for the scoring rubric. One regex covers both
    # caps-definition sites.
    ("scoring/caps.py", re.compile(r"^max_score=6\.0,$")),
    # v6_build.py docstring in a long help message — mentions the default
    # --review-threshold CLI default (9.0). The actual CLI default is
    # wired via argparse reading REVIEW_TARGET_SCORE, not this literal.
    # Content-based match (#1507) so future line shifts don't break CI.
    ("build/v6_build.py", re.compile(r"review_threshold \(default 9\.0\)")),
)

# REVIEW_PASS_FLOOR remains valid only for legacy V6, wiki single-score
# review, and dashboard surfaces that still consume legacy single scores.
_REVIEW_PASS_FLOOR_IMPORT_ALLOWLIST: frozenset[str] = frozenset({
    "audit/checks/review_gaming.py",
    "audit/checks/review_validation.py",
    "build/v6_build.py",
    "wiki/review.py",
    "api/dashboard_helpers.py",
    "api/dashboard_router.py",
    "api/state_compute.py",
})

# Files excluded from the scan entirely (archived / generated / legacy).
_EXCLUDED_DIRS: tuple[str, ...] = (
    "__pycache__",
    "oneoff",
    "legacy/",
    "agent_runtime/_archive",
)


def _iter_python_files() -> list[Path]:
    files: list[Path] = []
    for path in SCRIPTS_ROOT.rglob("*.py"):
        rel = path.relative_to(SCRIPTS_ROOT).as_posix()
        if any(excl in rel for excl in _EXCLUDED_DIRS):
            continue
        files.append(path)
    return files


def _module_level_name_assignments(tree: ast.Module) -> list[tuple[str, int]]:
    """Return (name, lineno) pairs for module-level ``NAME = ...`` assigns.

    Skips nested functions/classes — only top-level assignments count as
    "this module claims to own this constant."
    """
    results: list[tuple[str, int]] = []
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    results.append((target.id, node.lineno))
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            results.append((node.target.id, node.lineno))
    return results


def _matching_allowlist_patterns(
    rel_path: str,
    stripped_line: str,
) -> list[re.Pattern[str]]:
    """Return allowlist regexes that match this stripped line in this file."""
    return [
        pat
        for path, pat in _FLOAT_LITERAL_ALLOWLIST
        if rel_path == path and pat.search(stripped_line)
    ]


def test_no_canonical_name_redeclared_outside_thresholds() -> None:
    """No file other than thresholds.py defines the canonical names.

    An ``import`` of the name is fine (that's the whole point). Only
    local re-assignments at module scope are flagged.
    """
    offenders: list[str] = []
    for path in _iter_python_files():
        if path.resolve() == SOURCE_OF_TRUTH.resolve():
            continue
        try:
            tree = ast.parse(path.read_text("utf-8"))
        except SyntaxError:
            continue
        for name, lineno in _module_level_name_assignments(tree):
            if name in _CANONICAL_NAMES:
                rel = path.relative_to(SCRIPTS_ROOT).as_posix()
                offenders.append(f"{rel}:{lineno} redeclares {name!r}")

    assert not offenders, (
        "Canonical threshold names must live only in scripts/common/thresholds.py.\n"
        + "\n".join(offenders)
    )


def test_review_pass_floor_imports_are_legacy_allowlisted() -> None:
    """New module QG callers must use per-level per-dim review_floors.

    ``REVIEW_PASS_FLOOR`` is retained for legacy V6 and single-score wiki /
    dashboard review. A new import of the global floor is a schema regression.
    """
    offenders: list[str] = []
    for path in _iter_python_files():
        if path.resolve() == SOURCE_OF_TRUTH.resolve():
            continue
        rel = path.relative_to(SCRIPTS_ROOT).as_posix()
        try:
            tree = ast.parse(path.read_text("utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom):
                continue
            if node.module not in {"common.thresholds", "scripts.common.thresholds"}:
                continue
            if (
                any(alias.name == "REVIEW_PASS_FLOOR" for alias in node.names)
                and rel not in _REVIEW_PASS_FLOOR_IMPORT_ALLOWLIST
            ):
                offenders.append(f"{rel}:{node.lineno} imports REVIEW_PASS_FLOOR")

    assert not offenders, (
        "New callers must use LevelThresholds.review_floors or aggregate_review(); "
        "REVIEW_PASS_FLOOR imports are legacy-only.\n"
        + "\n".join(offenders)
    )


def test_no_duplicate_target_words_module_level() -> None:
    """No module-level ``target_words = <int>`` literal outside thresholds.py.

    Dict-entry ``'target_words': 1200`` inside ``LEVEL_CONFIG`` is fine —
    those are per-variant overrides, not module-level constants. This
    catches the ISTORIO-class drift: a bare ``target_words = 3500`` next
    to a separate ``target_words = 4000`` in another file.
    """
    pattern = re.compile(r"^(?:target_words|naturalness_threshold|word_floor)\s*=\s*\d", re.MULTILINE)
    offenders: list[str] = []
    for path in _iter_python_files():
        if path.resolve() == SOURCE_OF_TRUTH.resolve():
            continue
        for match in pattern.finditer(path.read_text("utf-8")):
            lineno = path.read_text("utf-8")[: match.start()].count("\n") + 1
            rel = path.relative_to(SCRIPTS_ROOT).as_posix()
            offenders.append(f"{rel}:{lineno} — {match.group(0).strip()}")

    assert not offenders, (
        "Module-level threshold names are reserved for scripts/common/thresholds.py.\n"
        + "\n".join(offenders)
    )


def test_no_threshold_float_literals_in_threshold_context() -> None:
    """Flag ``8.0 / 8.5 / 9.0 / 6.0`` near threshold-adjacent words.

    The ± 3-line window catches common patterns (``if score < 8.0:``,
    ``threshold = 8.0``) without false-positiving on unrelated uses
    (e.g., a version string or a percentage). Per-line allow-list
    carries the few legitimate exceptions.
    """
    offenders: list[str] = []
    for path in _iter_python_files():
        if path.resolve() == SOURCE_OF_TRUTH.resolve():
            continue
        rel = path.relative_to(SCRIPTS_ROOT).as_posix()
        lines = path.read_text("utf-8").splitlines()
        for idx, line in enumerate(lines, start=1):
            stripped_line = line.strip()
            if _matching_allowlist_patterns(rel, stripped_line):
                continue
            # Quick literal presence filter.
            stripped = line.split("#", 1)[0]  # strip line comments
            has_literal = any(
                re.search(rf"(?<!\d)\b{re.escape(f'{value:.1f}')}\b", stripped)
                for value in _THRESHOLD_VALUES
            )
            if not has_literal:
                continue
            # Context window: ± 3 lines. Include the line itself.
            lo, hi = max(0, idx - 4), min(len(lines), idx + 3)
            window = " ".join(lines[lo:hi]).lower()
            if any(word in window for word in _THRESHOLD_CONTEXT_WORDS):
                offenders.append(f"{rel}:{idx} — {line.strip()}")

    assert not offenders, (
        "Float literals that look like pipeline thresholds were found "
        "outside scripts/common/thresholds.py:\n"
        + "\n".join(offenders)
        + "\n\nFix: import REVIEW_PASS_FLOOR / STYLE_REVIEW_TARGET / etc. "
        "from scripts.common.thresholds, or — if the value is genuinely "
        "unrelated — add (path, regex_pattern) to "
        "_FLOAT_LITERAL_ALLOWLIST with a one-line justification."
    )


def test_allowlist_does_not_match_unrelated_lines(tmp_path: Path) -> None:
    """A ``9.0`` in an unrelated location must still trigger the gate.

    Regression for #1507: content-based allowlist must not swallow new
    occurrences just because they live in an allowlisted file.
    """
    del tmp_path  # test exercises the predicate directly

    fake_line = "CHECK_THRESHOLD = 9.0  # unrelated constant"
    allowlisted_paths = {path for path, _pat in _FLOAT_LITERAL_ALLOWLIST}
    matches = {
        path: _matching_allowlist_patterns(path, fake_line)
        for path in allowlisted_paths
    }
    matched = {
        path: [pat.pattern for pat in pats]
        for path, pats in matches.items()
        if pats
    }
    assert not matched, (
        "Allowlist regex is too permissive — matched an unrelated line: "
        f"{fake_line!r}. Tighten the pattern(s): {matched}"
    )


def test_audit_config_naturalness_matches_thresholds() -> None:
    """``AUDIT_THRESHOLDS['naturalness_min_score']`` stays in sync with
    ``LEVEL_THRESHOLDS`` — not because a test asserts equality once,
    but because the dict is built from LEVEL_THRESHOLDS at import time.
    Regression guard.
    """
    from audit.config import AUDIT_THRESHOLDS
    from common.thresholds import LEVEL_THRESHOLDS

    mins = AUDIT_THRESHOLDS["naturalness_min_score"]
    for level, thresholds in LEVEL_THRESHOLDS.items():
        assert mins[level] == thresholds.naturalness_min, (
            f"{level} audit naturalness drift: "
            f"AUDIT_THRESHOLDS={mins[level]} vs LEVEL_THRESHOLDS={thresholds.naturalness_min}"
        )
    assert "default" in mins, "AUDIT_THRESHOLDS must keep a 'default' fallback."


def test_level_config_family_target_words_match_thresholds() -> None:
    """Family entries (A1..C2) in ``LEVEL_CONFIG`` read from
    ``LEVEL_THRESHOLDS`` — guards against someone hardcoding a number
    back into the LEVEL_CONFIG dict literal.
    """
    from audit.config import LEVEL_CONFIG
    from common.thresholds import LEVEL_THRESHOLDS

    for level, thresholds in LEVEL_THRESHOLDS.items():
        cfg = LEVEL_CONFIG.get(level)
        assert cfg is not None, f"LEVEL_CONFIG missing family {level!r}"
        assert cfg["target_words"] == thresholds.target_words, (
            f"{level} LEVEL_CONFIG target_words={cfg['target_words']} "
            f"drifted from LEVEL_THRESHOLDS.target_words={thresholds.target_words}"
        )


def test_config_py_has_no_word_floor() -> None:
    """Legacy dead field — must stay removed. scripts/config.py
    TRACK_CONFIG used to carry ``word_floor`` that no caller read."""
    config_py = (SCRIPTS_ROOT / "config.py").read_text("utf-8")
    assert "word_floor" not in config_py, (
        "scripts/config.py TRACK_CONFIG.word_floor was removed as dead "
        "code that contradicted scripts/audit/config.py word targets. "
        "Do not revive it — use scripts.common.thresholds.LEVEL_THRESHOLDS."
    )
