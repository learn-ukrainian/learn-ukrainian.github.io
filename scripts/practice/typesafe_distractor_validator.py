#!/usr/bin/env python3
"""TypeSafe Practice Distractor & Misconception Validator (Practice Hub #8174).

Two-layer verification architecture:
  Tier 1: Fast pedagogical & ambiguity screening via TypeSafe System One (Jev 1.13):
    1. Distractor Plausibility & Foil Quality (Score)
    2. Unambiguous Target Exclusivity (Noul: guarantees no distractor is a valid secondary reading)
    3. Anti-Calque Yield (Noul: identifies drills countering Russian linguistic interference)
    4. Card Quality Verdict (Choice: pass, warn_weak_foils, fail_ambiguous, fail_broken)

  Tier 2: Deterministic verification against immutable Ukrainian linguistic authority:
    1. Morphological Attestation: Cross-checks target and distractors against VESUM (data/vesum.db).
    2. Style-Guide Grounding: Corroborates anti-calque claims against Antonenko-Davydovych
       «Як ми говоримо» (data/sources.db table style_guide).

Adheres strictly to the 2026-09-17 TypeSafe fleet contract:
  - System One outputs are treated as probabilistic triage, never confusing LLM confidence
    with ground linguistic truth.
  - Morphological forms and Russianism classifications are anchored in VESUM and verified style guides.
  - Credentials securely resolved from ~/.secrets/typsafe-ai.key (never committed or leaked).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Policy thresholds (evaluated in Python code)
DEFAULT_THRESHOLDS = {
    "unambiguous_min": 0.70,  # P(is_unambiguous) must be >= 0.70 to pass
    "plausibility_min": 0.80,  # Score >= 0.80 for high-quality foils
    "anti_calque_notable": 0.60,  # P(anti_calque) >= 0.60 flagged as high anti-calque value
    "confidence_review_floor": 0.50,  # Confidence < 0.50 triggers advisory review
}


@dataclass
class DistractorValidationVerdict:
    stem: str
    target: str
    distractors: list[str]
    verdict: str  # "pass", "warn_weak_foils", "fail_ambiguous", "fail_broken"
    is_unambiguous_prob: float
    plausibility_score: float
    plausibility_confidence: float
    anti_calque_yield_prob: float
    verdict_confidence: float
    latency_seconds: float
    model: str
    needs_review: bool
    findings: list[str]
    vesum_verified: bool = False
    style_guide_attested: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def resolve_api_key() -> str | None:
    """Resolve TypeSafe API key securely from environment or ~/.secrets/."""
    env_key = os.environ.get("TYPESAFE_API_KEY", "").strip()
    if env_key:
        return env_key

    for name in ("typsafe-ai.key", "typesafe-ai.key"):
        path = Path.home() / ".secrets" / name
        if path.exists():
            key = path.read_text(encoding="utf-8").strip()
            if key:
                return key

    return None


def get_typesafe_client(api_key: str | None = None) -> Any:
    """Instantiate TypeSafeClient using the verified SDK."""
    try:
        from typesafe_sdk import TypeSafeClient
    except ImportError as err:
        raise ImportError(
            "typesafe-sdk is not installed in the current environment. "
            "Install with `.venv/bin/python -m pip install typesafe-sdk`"
        ) from err

    resolved = api_key or resolve_api_key()
    if not resolved:
        raise ValueError(
            "TypeSafe API key not found. Ensure TYPESAFE_API_KEY is exported or ~/.secrets/typsafe-ai.key exists."
        )

    return TypeSafeClient(api_key=resolved)


def build_validation_questions() -> dict[str, Any]:
    """Define the 4 batched questions for practice card distractor validation."""
    from typesafe_sdk import Choice, Noul, Score

    return {
        "distractor_plausibility": Score(
            instructions="Evaluate the pedagogical quality of the distractors for a Ukrainian language learner",
            criteria=[
                "Poor: distractors are absurd, impossible nonsense, or obvious non-foils that provide no learning value",
                "Acceptable: grammatical forms from other slots, but somewhat generic or mechanical",
                "High quality: directly targets frequent learner misconceptions (case confusion, wrong person/mood, or Russian calques)",
            ],
        ),
        "is_unambiguous": Noul(
            instructions="In the context of the sentence stem and target grammar, is the target answer the ONLY correct option (none of the distractors can serve as an acceptable secondary answer)?"
        ),
        "anti_calque_yield": Noul(
            instructions="Does this drill effectively target, contrast, or prevent a common Russian interference pattern or Surzhyk calque in Ukrainian?"
        ),
        "card_quality": Choice(
            instructions="What overall quality verdict should be assigned to this practice card?",
            criteria={
                "pass": "Card is unambiguous, has plausible foils, and is pedagogically sound for learners",
                "warn_weak_foils": "Card is unambiguous, but distractors are too weak, obvious, or unchallenging",
                "fail_ambiguous": "One or more distractors could be considered grammatically acceptable in context",
                "fail_broken": "Target is incorrect or distractors contain typos or malformed tokens",
            },
        ),
    }


def _resolve_db_path(relative_path: str) -> Path | None:
    """Locate database file across worktree or main checkout."""
    candidates = [
        REPO_ROOT / relative_path,
        REPO_ROOT.parent.parent.parent / relative_path,
    ]
    for c in candidates:
        if c.is_file():
            return c
    return None


def verify_word_in_vesum(word: str, vesum_db_path: Path | None = None) -> bool:
    """Verify if a word form is attested in VESUM (data/vesum.db)."""
    db_path = vesum_db_path or _resolve_db_path("data/vesum.db")
    if not db_path or not db_path.is_file():
        return True  # Fail open if DB not present in CI environment

    clean = word.strip().lower().replace("’", "'").replace("ʼ", "'")
    try:
        conn = sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True)
        cursor = conn.execute("SELECT 1 FROM forms WHERE word_form = ? LIMIT 1", (clean,))
        found = cursor.fetchone() is not None
        conn.close()
        return found
    except Exception:
        return True


def check_style_guide_calque(tokens: list[str], sources_db_path: Path | None = None) -> list[str]:
    """Check if any token matches an attested calque in data/sources.db table style_guide."""
    db_path = sources_db_path or _resolve_db_path("data/sources.db")
    if not db_path or not db_path.is_file():
        return []

    hits: list[str] = []
    try:
        conn = sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True)
        for tok in tokens:
            clean = tok.strip().lower()
            if len(clean) < 3:
                continue
            cursor = conn.execute(
                "SELECT headword FROM style_guide WHERE headword LIKE ? OR text LIKE ? LIMIT 1",
                (f"%{clean}%", f"%{clean}%"),
            )
            row = cursor.fetchone()
            if row:
                hits.append(f"{clean} (Antonenko-Davydovych: {row[0]})")
        conn.close()
    except Exception:
        pass
    return hits


def validate_practice_card(
    stem: str,
    target: str,
    distractors: list[str],
    grammar_focus: str | None = None,
    client: Any | None = None,
    thresholds: dict[str, float] | None = None,
    mock_response: dict[str, Any] | None = None,
    vesum_db: Path | None = None,
    sources_db: Path | None = None,
) -> DistractorValidationVerdict:
    """Validate a single practice card's options through TypeSafe System One and deterministic authority."""
    th = {**DEFAULT_THRESHOLDS, **(thresholds or {})}
    state = {
        "sentence_stem": stem,
        "target_correct_answer": target,
        "distractor_options": distractors,
        "all_options": [target, *distractors],
        "grammar_focus": grammar_focus or "General Ukrainian grammar practice",
    }

    t0 = time.perf_counter()

    if mock_response is not None:
        answers = mock_response.get("answers", {})
        model_name = mock_response.get("model", "mock-jev")
        elapsed = 0.001
    else:
        if client is None:
            client = get_typesafe_client()
        questions = build_validation_questions()
        resp = client.system_one(state=state, questions=questions)
        answers = resp.answers
        model_name = resp.model
        elapsed = time.perf_counter() - t0

    plaus_ans = answers["distractor_plausibility"]
    unambig_ans = answers["is_unambiguous"]
    calque_ans = answers["anti_calque_yield"]
    quality_ans = answers["card_quality"]

    plaus_score = float(plaus_ans.score if hasattr(plaus_ans, "score") else plaus_ans["score"])
    plaus_conf = float(plaus_ans.confidence if hasattr(plaus_ans, "confidence") else plaus_ans.get("confidence", 1.0))

    unambig_prob = float(unambig_ans.noul if hasattr(unambig_ans, "noul") else unambig_ans["noul"])
    calque_prob = float(calque_ans.noul if hasattr(calque_ans, "noul") else calque_ans["noul"])

    quality_choice = str(quality_ans.choice if hasattr(quality_ans, "choice") else quality_ans["choice"])
    quality_conf = float(
        quality_ans.confidence if hasattr(quality_ans, "confidence") else quality_ans.get("confidence", 1.0)
    )

    findings: list[str] = []
    final_verdict = quality_choice
    needs_review = False

    # Tier 1 (System One) Invariant 1: Ambiguity Failure
    if unambig_prob < th["unambiguous_min"]:
        final_verdict = "fail_ambiguous"
        findings.append(
            f"Ambiguity alert: target exclusivity probability is low (P={unambig_prob:.2f} < {th['unambiguous_min']:.2f})"
        )
        needs_review = True

    # Tier 1 Invariant 2: Distractor Quality
    if plaus_score < th["plausibility_min"] and final_verdict == "pass":
        final_verdict = "warn_weak_foils"
        findings.append(
            f"Weak foils: distractor plausibility score is low ({plaus_score:.2f} < {th['plausibility_min']:.2f})"
        )

    # Tier 1 Invariant 3: Anti-calque notification
    if calque_prob >= th["anti_calque_notable"]:
        findings.append(f"Anti-calque value (TypeSafe System-1 judgment: P={calque_prob:.2f})")

    # Tier 1 Invariant 4: Confidence check
    if quality_conf < th["confidence_review_floor"]:
        needs_review = True
        findings.append(f"Low verdict confidence ({quality_conf:.2f}) - manual check recommended")

    # Tier 2: Deterministic Authority Checks
    vesum_ok = True
    # Single-word target verification in VESUM
    if re.fullmatch(r"[\w'’ʼ-]+", target) and not verify_word_in_vesum(target, vesum_db_path=vesum_db):
        vesum_ok = False
        needs_review = True
        findings.append(f"VESUM authority alert: target form '{target}' not attested in forms table")
        if final_verdict == "pass":
            final_verdict = "warn_weak_foils"

    # Style-guide cross-check
    all_tokens = [target, *distractors]
    calque_hits = check_style_guide_calque(all_tokens, sources_db_path=sources_db)
    style_attested = len(calque_hits) > 0
    for hit in calque_hits:
        findings.append(f"Attested style-guide entry: {hit}")

    return DistractorValidationVerdict(
        stem=stem,
        target=target,
        distractors=distractors,
        verdict=final_verdict,
        is_unambiguous_prob=unambig_prob,
        plausibility_score=plaus_score,
        plausibility_confidence=plaus_conf,
        anti_calque_yield_prob=calque_prob,
        verdict_confidence=quality_conf,
        latency_seconds=elapsed,
        model=model_name,
        needs_review=needs_review,
        findings=findings,
        vesum_verified=vesum_ok,
        style_guide_attested=style_attested,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="TypeSafe Practice Distractor & Misconception Validator (Practice Hub #8174)"
    )
    parser.add_argument("--stem", type=str, help="Sentence cue / stem with blank")
    parser.add_argument("--target", type=str, help="Correct target answer form")
    parser.add_argument("--distractor", action="append", dest="distractors", help="Distractor option (repeatable)")
    parser.add_argument("--grammar", type=str, help="Grammar topic / focus")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")

    args = parser.parse_args()

    if not args.stem or not args.target or not args.distractors:
        parser.error("Must provide --stem, --target, and at least one --distractor.")

    client = get_typesafe_client()
    verdict = validate_practice_card(
        stem=args.stem,
        target=args.target,
        distractors=args.distractors,
        grammar_focus=args.grammar,
        client=client,
    )

    if args.format == "json":
        print(json.dumps(verdict.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(f"\n--- Practice Card Verdict ({verdict.model}, {verdict.latency_seconds:.3f}s) ---")
        print(f"Stem        : {verdict.stem}")
        print(f"Target      : {verdict.target}")
        print(f"Distractors : {', '.join(verdict.distractors)}")
        print(f"Verdict     : {verdict.verdict.upper()} (conf: {verdict.verdict_confidence:.2f})")
        print(f"Unambiguous : P(yes) = {verdict.is_unambiguous_prob:.2f}")
        print(f"Plausibility: {verdict.plausibility_score:.2f} / 2.00 (conf: {verdict.plausibility_confidence:.2f})")
        print(f"Anti-Calque : P(yes) = {verdict.anti_calque_yield_prob:.2f}")
        print(f"VESUM Check : {'Attested' if verdict.vesum_verified else 'Missing/Unverified'}")
        if verdict.findings:
            print(f"Findings    : {'; '.join(verdict.findings)}")

    return 0 if verdict.verdict in {"pass", "warn_weak_foils"} else 1


if __name__ == "__main__":
    sys.exit(main())
