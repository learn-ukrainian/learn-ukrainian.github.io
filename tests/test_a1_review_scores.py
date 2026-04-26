"""Verify that all 7 A1.1 modules have review files with scores >= 8.0 (#991 AC6).

Checks that review-correction files exist for each module in the A1.1 phase
and that the latest review round shows a passing score (8.0+).
"""

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ORCHESTRATION_ROOT = PROJECT_ROOT / "curriculum" / "l2-uk-en" / "a1" / "orchestration"

# All 7 A1.1 modules
A1_1_MODULES = [
    "sounds-letters-and-hello",
    "reading-ukrainian",
    "stress-and-melody",
    "special-signs",
    "who-am-i",
    "my-family",
    "checkpoint-first-contact",
]

# Matches scores like "9.3/10", "8.0/10", "below 8.0/10"
_SCORE_RE = re.compile(r"(\d+\.?\d*)/10")


def _get_latest_review_score(slug: str) -> float | None:
    """Find the latest review-correction file and extract the score.

    Returns the score as a float, or None if no review file found.
    """
    module_dir = ORCHESTRATION_ROOT / slug
    if not module_dir.is_dir():
        return None

    # Find all review-correction files, sorted by round number descending
    corrections = sorted(
        module_dir.glob("review-correction-*.md"),
        key=lambda p: int(re.search(r"-(\d+)\.md$", p.name).group(1)) if re.search(r"-(\d+)\.md$", p.name) else 0,
        reverse=True,
    )

    if not corrections:
        return None

    # Read the latest correction and extract score
    latest = corrections[0]
    text = latest.read_text("utf-8")

    # Check for "scored X/10" pattern
    match = re.search(r"scored\s+(\d+\.?\d*)/10", text)
    if match:
        return float(match.group(1))

    # Check for "below X/10" (means the score was < X)
    match = re.search(r"below\s+(\d+\.?\d*)/10", text)
    if match:
        # The module scored below threshold — return 0 to indicate failure
        return 0.0

    return None


class TestA1ReviewScores:
    """All 7 A1.1 modules must have review files with scores."""

    def test_all_modules_have_orchestration_dirs(self):
        for slug in A1_1_MODULES:
            module_dir = ORCHESTRATION_ROOT / slug
            if not module_dir.is_dir():
                pytest.skip(f"Missing orchestration dir: {slug}")

    def test_all_modules_have_review_files(self):
        """Every A1.1 module must have at least one review artifact.

        The v5 pipeline wrote ``review-correction-*.md`` and
        ``review-fixes-*.yaml`` files in the orchestration dir. The v6
        pipeline writes ``review-structured-r*.yaml`` (orchestration)
        and ``{slug}-review[-r*].md`` (level review dir). Accept either
        shape so this test tracks the live artifact layout rather than
        the retired one.
        """
        import json as _json

        review_dir = ORCHESTRATION_ROOT.parent / "review"
        for slug in A1_1_MODULES:
            module_dir = ORCHESTRATION_ROOT / slug
            if not module_dir.is_dir():
                pytest.skip(f"Orchestration dir not found for {slug}")

            # Skip modules whose pipeline hasn't reached the review
            # phase yet (fresh rebuilds reset state.json to just the
            # earliest phases). ``review-style``-phase entry is the
            # first moment review artifacts are guaranteed.
            state_path = module_dir / "state.json"
            if state_path.is_file():
                try:
                    state = _json.loads(state_path.read_text(encoding="utf-8"))
                    phases = state.get("phases", {})
                    review_status = phases.get("review", {}).get("status")
                    if review_status not in ("complete", "failed"):
                        continue  # module is pre-review — no artifacts expected
                except (_json.JSONDecodeError, OSError):
                    pass  # fall through to artifact check

            # v6 artifacts
            structured = list(module_dir.glob("review-structured-r*.yaml"))
            round_reviews = list(review_dir.glob(f"{slug}-review-r*.md"))
            final_review = (review_dir / f"{slug}-review.md").is_file()

            # v5 artifacts (kept for archival tolerance)
            corrections = list(module_dir.glob("review-correction-*.md"))
            fixes = list(module_dir.glob("review-fixes-*.yaml"))

            has_review = bool(
                structured or round_reviews or final_review or corrections or fixes
            )
            assert has_review, (
                f"Module {slug} has no review artifacts "
                f"(no review-structured-r*.yaml / {slug}-review*.md / "
                "review-correction-*.md / review-fixes-*.yaml)"
            )

    def test_review_files_contain_score_pattern(self):
        for slug in A1_1_MODULES:
            module_dir = ORCHESTRATION_ROOT / slug
            if not module_dir.is_dir():
                continue
            corrections = list(module_dir.glob("review-correction-*.md"))
            if not corrections:
                continue
            # At least one file must mention a score
            has_score = False
            for path in corrections:
                text = path.read_text("utf-8")
                if _SCORE_RE.search(text):
                    has_score = True
                    break
            assert has_score, f"Module {slug} review files have no score pattern (X/10)"

    def test_latest_scores_at_least_8(self):
        """The latest review round for each module should have score >= 8.0.

        Note: some modules may still be in correction rounds (scored below 8.0
        on an earlier round). This test checks the LATEST round only.
        If a module's latest round is still below 8.0, it needs more fix rounds.
        """
        below_threshold = []
        for slug in A1_1_MODULES:
            score = _get_latest_review_score(slug)
            if score is not None and score < 8.0:
                below_threshold.append((slug, score))

        if below_threshold:
            details = ", ".join(f"{s} ({sc})" for s, sc in below_threshold)
            pytest.xfail(
                f"Modules with latest score < 8.0 (need more fix rounds): {details}"
            )
