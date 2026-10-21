"""CI invariant — thresholds live in exactly one file.

Guards against drift by rejecting:
  1. Module-level re-declarations of any canonical threshold name.
  2. Float literals (8.0 / 9.0 / 8.5 / 6.0) used in threshold-adjacent
     contexts anywhere in ``scripts/`` outside the source-of-truth module.

Related incident: ISTORIO 3500 vs 4000 drift (Jan 2026), recorded in
``agents_extensions/shared/rules/non-negotiable-rules.md`` §1. EPIC #1451 P2-A.
"""

from __future__ import annotations

import re
import sys
from functools import cache
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))


SCRIPTS_ROOT = Path(__file__).resolve().parent.parent / "scripts"
SOURCE_OF_TRUTH = SCRIPTS_ROOT / "common" / "thresholds.py"
pytestmark = [pytest.mark.repo_invariant, pytest.mark.reads_content, pytest.mark.repo_wide]

# Precise content-based allow-list for legitimate non-threshold float
# literals that happen to look like thresholds. Each entry is
# (relative_posix_path, compiled_regex) matched against ``line.strip()``.
# Keep this short; prefer migrating over extending.
_FLOAT_LITERAL_ALLOWLIST: tuple[tuple[str, re.Pattern[str]], ...] = (
    # Host dispatch memory floor, not a pipeline quality threshold (#8860).
    ("config.py", re.compile(r"^DISPATCH_MIN_MEM_AVAILABLE_GIB = 8\.5$")),
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

# Files excluded from the scan entirely (archived / generated / legacy).
_EXCLUDED_DIRS: tuple[str, ...] = (
    "__pycache__",
    "oneoff",
    "legacy/",
    "agent_runtime/_archive",
)


@cache
def _iter_python_files() -> tuple[Path, ...]:
    files: list[Path] = []
    for path in SCRIPTS_ROOT.rglob("*.py"):
        rel = path.relative_to(SCRIPTS_ROOT).as_posix()
        if any(excl in rel for excl in _EXCLUDED_DIRS):
            continue
        files.append(path)
    return tuple(files)


@cache
def _read_script_text(path: Path) -> str:
    """Read each scanned script once for the module's repeated invariants."""
    return path.read_text("utf-8")


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
        source = _read_script_text(path)
        for match in pattern.finditer(source):
            lineno = source[: match.start()].count("\n") + 1
            rel = path.relative_to(SCRIPTS_ROOT).as_posix()
            offenders.append(f"{rel}:{lineno} — {match.group(0).strip()}")

    assert not offenders, (
        "Module-level threshold names are reserved for scripts/common/thresholds.py.\n"
        + "\n".join(offenders)
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
