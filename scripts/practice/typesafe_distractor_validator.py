#!/usr/bin/env python3
"""TypeSafe Practice Distractor & Misconception Validator (Practice Hub #8174).

Automated pedagogical verification of practice cards & distractor foils:
  1. Distractor Plausibility & Foil Quality (Score)
  2. Unambiguous Target Exclusivity (Noul: guarantees no distractor is a valid secondary reading)
  3. Anti-Calque Yield (Noul: identifies drills countering Russian linguistic interference)
  4. Card Quality Verdict (Choice: pass, warn_weak_foils, fail_ambiguous, fail_broken)
  5. Deterministic Sources/VESUM Grounding (ground_with_sources hook on escalate/uncertain/suspect)

Linguistic Authority & Deterministic Hard Rail:
  Per docs/best-practices/deterministic-over-hallucination.md:
  - TypeSafe System One (Jev 1.13) provides fast pedagogical pre-filtering, foil calibration,
    and ambiguity scoring. It is NOT an authority on Ukrainian morphology, VESUM validity,
    or Russian calques/surzhyk.
  - Morphological authority belongs strictly to VESUM (verify_word, verify_words, inspect_word).
  - Russian shadow and calque claims are grounded in deterministic Sources helpers
    (check_ru_morph.is_russian_pattern, CURATED_CALQUES, PHRASAL_CALQUES, and search_style_guide).
  - When escalate/uncertain/suspect conditions fire (ambiguity failure, weak foils, broken target,
    low confidence, or candidate anti-calque yield), ground_with_sources() is invoked in code
    after Jev to verify facts against immutable sources.
  - Any anti-calque claim unverified by Sources/VESUM is explicitly labeled as unverified
    LLM judgment and triggers needs_review = True.

Adheres strictly to the 2026-09-17 TypeSafe fleet contract:
  - Credentials securely resolved from ~/.secrets/typesafe-ai.key (never committed or leaked)
  - Evaluated in code using calibrated probabilities and confidence metrics
  - Complements VESUM and static practice checkers as a front-line pedagogical validator
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from scripts.lexicon.calque_corrections import CURATED_CALQUES, PHRASAL_CALQUES
from scripts.verification.check_ru_morph import is_russian_pattern
from scripts.verification.vesum import (
    InspectionStatus,
    inspect_word,
    verify_word,
    verify_words,
)

# Policy thresholds (evaluated in Python code)
DEFAULT_THRESHOLDS = {
    "unambiguous_min": 0.70,        # P(is_unambiguous) must be >= 0.70 to pass
    "plausibility_min": 0.80,       # Score >= 0.80 for high-quality foils
    "anti_calque_notable": 0.60,    # P(anti_calque) >= 0.60 flagged as high anti-calque value
    "confidence_review_floor": 0.50 # Confidence < 0.50 triggers advisory review
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
    grounded: bool = False
    grounding: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def resolve_api_key() -> str | None:
    """Resolve TypeSafe API key securely from environment or ~/.secrets/."""
    env_key = os.environ.get("TYPESAFE_API_KEY", "").strip()
    if env_key:
        return env_key

    for name in ("typesafe-ai.key", "typsafe-ai.key"):
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
            "TypeSafe API key not found. Ensure TYPESAFE_API_KEY is exported "
            "or ~/.secrets/typesafe-ai.key exists."
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
                "High quality: directly targets frequent learner misconceptions (case confusion, wrong person/mood, or Russian calques)"
            ]
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
                "fail_broken": "Target is incorrect or distractors contain typos or malformed tokens"
            }
        )
    }


def _resolve_sources_db_path(db_path: str | Path | None = None) -> Path | None:
    """Resolve data/sources.db, falling back to primary checkout if in a worktree."""
    if db_path is not None:
        p = Path(db_path)
        return p if p.is_file() else None
    local = REPO_ROOT / "data" / "sources.db"
    if local.is_file():
        return local
    try:
        from scripts.guardrails.worktree_containment import resolve_main_root

        primary = resolve_main_root(REPO_ROOT) / "data" / "sources.db"
        if primary.is_file():
            return primary
    except Exception:
        pass
    return None


def ground_with_sources(
    target: str,
    distractors: list[str],
    *,
    vesum_db_path: str | Path | None = None,
    sources_db_path: str | Path | None = None,
) -> dict[str, Any]:
    """Deterministically ground target & distractors using VESUM and Sources helpers.

    Adheres strictly to docs/best-practices/deterministic-over-hallucination.md:
    1. Morphological validity of target and distractors is verified via VESUM
       (verify_word, verify_words, inspect_word).
    2. Russian calques / shadows / surzhyk claims are verified via deterministic
       lexical & morphological checkers (is_russian_pattern, CURATED_CALQUES,
       PHRASAL_CALQUES, and search_style_guide).
    """
    # 1. Target morphology check in VESUM
    target_clean = target.strip()
    target_tokens = [t.strip(",.?!;:\"'«»") for t in target_clean.split() if t.strip()]
    target_in_vesum = False
    target_status = "UNKNOWN"
    target_analyses: list[dict[str, Any]] = []

    try:
        if len(target_tokens) == 1:
            target_analyses = verify_word(target_tokens[0], db_path=vesum_db_path)
            if target_analyses:
                target_in_vesum = True
                target_status = "CLEAN"
            else:
                try:
                    insp = inspect_word(target_tokens[0], db_path=vesum_db_path)
                    target_in_vesum = insp.status not in (
                        InspectionStatus.NOT_FOUND,
                        InspectionStatus.UNAVAILABLE,
                    )
                    target_status = insp.status.value
                    target_analyses = insp.clean_analyses or insp.marked_analyses
                except Exception:
                    target_in_vesum = False
                    target_status = "NOT_FOUND"
        elif len(target_tokens) > 1:
            v_res = verify_words(target_tokens, db_path=vesum_db_path)
            target_in_vesum = all(bool(v_res.get(t)) for t in target_tokens)
            target_status = "CLEAN" if target_in_vesum else "PARTIAL_OR_NOT_FOUND"
            target_analyses = [a for t in target_tokens for a in v_res.get(t, [])]
    except Exception as exc:
        target_status = f"ERROR: {exc}"
        target_in_vesum = False  # fail-closed on VESUM exception

    # 2. Distractor morphology check in VESUM
    all_distractor_tokens: list[str] = []
    for d in distractors:
        all_distractor_tokens.extend([t.strip(",.?!;:\"'«»") for t in d.split() if t.strip()])

    verified_in_vesum: list[str] = []
    missing_from_vesum: list[str] = []
    analyses_by_distractor: dict[str, list[dict[str, Any]]] = {}

    try:
        token_results = verify_words(list(set(all_distractor_tokens)), db_path=vesum_db_path)
        for d in distractors:
            tokens = [t.strip(",.?!;:\"'«»") for t in d.split() if t.strip()]
            if tokens and all(bool(token_results.get(t)) for t in tokens):
                verified_in_vesum.append(d)
            else:
                missing_from_vesum.append(d)
            analyses_by_distractor[d] = [a for t in tokens for a in token_results.get(t, [])]
    except Exception:
        verified_in_vesum = []
        missing_from_vesum = list(distractors)

    # 3. Detect Russian-shadow and calque patterns
    detected_calques: list[dict[str, Any]] = []
    resolved_sources_db = _resolve_sources_db_path(sources_db_path)

    for form in [target, *distractors]:
        norm = form.strip().lower()
        if not norm:
            continue

        if norm in PHRASAL_CALQUES:
            detected_calques.append({
                "form": form,
                "source": "phrasal_calques",
                "note": PHRASAL_CALQUES[norm].get("note", "Documented phrasal calque"),
            })
            continue

        if norm in CURATED_CALQUES:
            detected_calques.append({
                "form": form,
                "source": "curated_calques",
                "note": CURATED_CALQUES[norm].get("note", "Documented calque"),
            })
            continue

        try:
            ru_res = is_russian_pattern(norm, threshold=0.7, vesum_db_path=vesum_db_path)
            if ru_res.get("matches_russian"):
                detected_calques.append({
                    "form": form,
                    "source": "russian_shadow",
                    "russian_lemma": ru_res.get("russian_lemma"),
                    "confidence": ru_res.get("confidence", 1.0),
                })
                continue
        except Exception:
            pass

        if resolved_sources_db is not None:
            try:
                from scripts.wiki.sources_db import search_style_guide

                hits = search_style_guide(norm, limit=2, db_path=resolved_sources_db)
                for hit in hits:
                    raw_hw = hit.get("word") or ""
                    # Style guide headwords typically contrast "calque – correct".
                    # Only match the calque side (before the dash) to avoid false positives.
                    dash = "–" if "–" in raw_hw else ("—" if "—" in raw_hw else None)
                    bad_part = raw_hw.split(dash)[0].strip().lower() if dash else raw_hw.strip().lower()
                    if norm == bad_part or (len(norm.split()) > 1 and norm in bad_part):
                        detected_calques.append({
                            "form": form,
                            "source": "style_guide",
                            "headword": raw_hw,
                        })
                        break
            except Exception:
                pass

    return {
        "target": {
            "word": target,
            "in_vesum": target_in_vesum,
            "status": target_status,
            "analyses": target_analyses,
        },
        "distractors": {
            "verified_in_vesum": verified_in_vesum,
            "missing_from_vesum": missing_from_vesum,
            "analyses": analyses_by_distractor,
        },
        "calques_and_shadows": detected_calques,
        "has_calque_foil": any(c["form"] in distractors for c in detected_calques),
        "grounded": True,
    }


def validate_practice_card(
    stem: str,
    target: str,
    distractors: list[str],
    grammar_focus: str | None = None,
    client: Any | None = None,
    thresholds: dict[str, float] | None = None,
    mock_response: dict[str, Any] | None = None,
    *,
    always_ground: bool = False,
    ground_hook: Callable[..., dict[str, Any]] | None = None,
    vesum_db_path: str | Path | None = None,
    sources_db_path: str | Path | None = None,
) -> DistractorValidationVerdict:
    """Validate a single practice card's options through TypeSafe System One.

    When escalate/uncertain/suspect conditions fire (e.g. ambiguity failure,
    weak foils, broken target, low confidence, or candidate anti-calque yield),
    or when always_ground=True, the escalate path invokes ground_with_sources()
    (or ground_hook) to cross-verify morphology and calque claims against VESUM
    and Sources authority databases.
    """
    th = {**DEFAULT_THRESHOLDS, **(thresholds or {})}
    state = {
        "sentence_stem": stem,
        "target_correct_answer": target,
        "distractor_options": distractors,
        "all_options": [target, *distractors],
        "grammar_focus": grammar_focus or "General Ukrainian grammar practice"
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
    quality_conf = float(quality_ans.confidence if hasattr(quality_ans, "confidence") else quality_ans.get("confidence", 1.0))

    findings: list[str] = []
    final_verdict = quality_choice
    needs_review = False

    # Hard Invariant 1: Ambiguity Failure
    if unambig_prob < th["unambiguous_min"]:
        final_verdict = "fail_ambiguous"
        findings.append(f"Ambiguity alert: target exclusivity probability is low (P={unambig_prob:.2f} < {th['unambiguous_min']:.2f})")
        needs_review = True

    # Hard Invariant 2: Distractor Quality
    if plaus_score < th["plausibility_min"] and final_verdict == "pass":
        final_verdict = "warn_weak_foils"
        findings.append(f"Weak foils: distractor plausibility score is low ({plaus_score:.2f} < {th['plausibility_min']:.2f})")

    # Confidence check
    if quality_conf < th["confidence_review_floor"] or plaus_conf < th["confidence_review_floor"]:
        needs_review = True
        findings.append(f"Low verdict confidence ({min(quality_conf, plaus_conf):.2f}) - manual check recommended")

    calque_claimed = calque_prob >= th["anti_calque_notable"]

    # Escalate / uncertain / suspect trigger
    is_escalate = (
        final_verdict != "pass"
        or needs_review
        or calque_claimed
    )

    grounded = False
    grounding_data: dict[str, Any] | None = None

    if is_escalate or always_ground:
        grounder = ground_hook or ground_with_sources
        grounding_data = grounder(
            target=target,
            distractors=distractors,
            vesum_db_path=vesum_db_path,
            sources_db_path=sources_db_path,
        )
        grounded = True

        # Target verification check
        target_in_vesum = grounding_data.get("target", {}).get("in_vesum", False)
        if not target_in_vesum:
            final_verdict = "fail_broken"
            needs_review = True
            findings.append(f"Target '{target}' not found in VESUM morphological dictionary (grounding failure)")

        # Anti-calque cross-verification
        has_calque = grounding_data.get("has_calque_foil", False)
        calque_items = grounding_data.get("calques_and_shadows", [])
        calque_summaries = [c["form"] for c in calque_items if c.get("form") in distractors]

        if calque_claimed:
            if has_calque and calque_summaries:
                findings.append(
                    f"High anti-calque value (P={calque_prob:.2f}, grounded in Sources: {', '.join(calque_summaries)})"
                )
            else:
                findings.append(
                    f"Anti-calque yield unverified by Sources/VESUM (P={calque_prob:.2f}, no shadow/calque found in options)"
                )
                needs_review = True
        elif has_calque and calque_summaries:
            findings.append(f"Deterministic anti-calque foil confirmed by Sources: {', '.join(calque_summaries)}")

        # Distractor morphology feedback on ambiguous / weak foils
        if final_verdict == "fail_ambiguous":
            verified = grounding_data.get("distractors", {}).get("verified_in_vesum", [])
            if verified:
                findings.append(f"Ambiguity escalate: distractor morphology verified in VESUM ({', '.join(verified)})")
    else:
        # Fast path (clean card, not escalated)
        if calque_claimed:
            findings.append(f"Anti-calque value (P={calque_prob:.2f}, unverified LLM judgment)")

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
        grounded=grounded,
        grounding=grounding_data,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="TypeSafe Practice Distractor & Misconception Validator (Practice Hub #8174)"
    )
    parser.add_argument("--stem", type=str, help="Sentence cue / stem with blank")
    parser.add_argument("--target", type=str, help="Correct target answer form")
    parser.add_argument("--distractor", action="append", dest="distractors", help="Distractor option (repeatable)")
    parser.add_argument("--grammar", type=str, help="Grammar topic / focus")
    parser.add_argument("--ground", action="store_true", help="Force grounding against Sources/VESUM regardless of verdict")
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
        always_ground=args.ground,
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
        if verdict.grounded and verdict.grounding:
            t_in = verdict.grounding.get("target", {}).get("in_vesum")
            v_dist = len(verdict.grounding.get("distractors", {}).get("verified_in_vesum", []))
            total_dist = len(verdict.distractors)
            print(f"Grounding   : Sources/VESUM verified (target: {'OK' if t_in else 'MISSING'}, foils in VESUM: {v_dist}/{total_dist})")
        if verdict.findings:
            print(f"Findings    : {'; '.join(verdict.findings)}")

    return 0 if verdict.verdict in {"pass", "warn_weak_foils"} else 1


if __name__ == "__main__":
    sys.exit(main())
