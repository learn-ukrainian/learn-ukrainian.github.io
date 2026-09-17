#!/usr/bin/env python3
"""TypeSafe System One Cyrillic Gate (ULDR #8173).

High-throughput, calibrated triage for Ukrainian & Cyrillic text chunks:
  1. OCR Noise & Homoglyph Detection (Score)
  2. Lexical & Regional Variety Classification (Choice: standard vs authentic dialect vs colonial Surzhyk)
  3. Colonial / Russian Shadow Assessment (Noul)
  4. Tri-State Admissibility & Routing (admit_standard, admit_dialect_heritage, anti_calque_foil, reject_drop)

Adheres strictly to the 2026-09-17 TypeSafe fleet contract:
  - Credentials securely loaded from ~/.secrets/typsafe-ai.key (never logged or committed)
  - Thresholds and policy maintained in Python code
  - Does NOT replace VESUM as morphological authority; acts as fast semantic front-line gate
  - Never rewrites human source Ukrainian
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Policy thresholds (evaluated strictly in code, not model prompt)
DEFAULT_THRESHOLDS = {
    "ocr_clean_max": 0.40,           # Score <= 0.40 considered clean of OCR noise
    "ocr_garbage_min": 1.40,         # Score >= 1.40 considered irrecoverable OCR junk
    "colonial_shadow_flag": 0.50,    # P(colonial_shadow) >= 0.50 triggers anti-calque or review
    "confidence_auto_accept": 0.75,  # Confidence >= 0.75 permits automated pipeline decisions
    "confidence_review_floor": 0.45, # Confidence < 0.45 escalates to human or dictionary check
}


@dataclass
class CyrillicGateVerdict:
    text: str
    decision: str  # "admit_standard", "admit_heritage", "anti_calque", "reject", "escalate_review"
    lexical_variety: str
    variety_confidence: float
    ocr_corruption_score: float
    ocr_confidence: float
    colonial_shadow_prob: float
    curriculum_action: str
    action_confidence: float
    latency_seconds: float
    model: str
    needs_review: bool
    review_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def resolve_api_key() -> str | None:
    """Resolve TypeSafe API key securely from environment or ~/.secrets/."""
    env_key = os.environ.get("TYPESAFE_API_KEY", "").strip()
    if env_key:
        return env_key

    # Check host secret locations outside the repository
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
            "TypeSafe API key not found. Ensure TYPESAFE_API_KEY is exported "
            "or ~/.secrets/typsafe-ai.key exists."
        )

    return TypeSafeClient(api_key=resolved)


def build_system_one_questions() -> dict[str, Any]:
    """Define the 4 batched questions for the Cyrillic gate."""
    from typesafe_sdk import Choice, Noul, Score

    return {
        "ocr_corruption": Score(
            instructions="Rate the extent of OCR noise, typos, digit substitutions, or mixed Latin/Cyrillic homoglyphs in this text",
            criteria=[
                "Clean text, no perceptible OCR corruption, broken characters, or homoglyphs",
                "Minor typos or archaic orthography, but readable and mechanically sound",
                "Severe OCR garbage, broken ligatures, digit substitutions, or mixed Latin/Cyrillic homoglyphs"
            ]
        ),
        "lexical_variety": Choice(
            instructions="Classify the linguistic variety and origin of this Ukrainian/Cyrillic text",
            criteria={
                "standard_modern": "Contemporary standard literary Ukrainian (post-1990 standard norm)",
                "authentic_dialect": "Authentic regional Ukrainian dialect (Hutsul, Galician, Boyko, Polissian, etc. - e.g. ґазда, файно, бараболя)",
                "historical_literary": "Historical Ukrainian literary or 1928 Kharkiv orthography",
                "colonial_surzhyk": "Colonial Surzhyk, Russian calques, unidiomatic interference (e.g. случайно, получилося, вибачаюся, на протязі року, міроприємство)",
                "soviet_jargon": "Soviet bureaucratic, ideological, or kolkhoz era terminology (e.g. колгоспниця, передовик, партком)",
                "non_ukrainian": "Russian, Polish, or other non-Ukrainian text"
            }
        ),
        "colonial_shadow": Noul(
            instructions="Does this text exhibit Russian lexical calques, Surzhyk, or grammatical interference (such as случайно, получилося, вибачаюся, на протязі)?"
        ),
        "curriculum_action": Choice(
            instructions="What pipeline action is most appropriate for this text?",
            criteria={
                "admit_standard": "Admit into standard core Ukrainian corpus / curriculum",
                "admit_dialect_heritage": "Admit into regional dialect / cultural heritage archive",
                "use_as_anti_calque": "Use as anti-calque or error-correction drill foil",
                "reject_drop": "Reject and exclude (OCR corruption, non-Ukrainian, or unacceptable quality)"
            }
        )
    }


def evaluate_cyrillic_text(
    text: str,
    context: str | None = None,
    client: Any | None = None,
    thresholds: dict[str, float] | None = None,
    mock_response: dict[str, Any] | None = None
) -> CyrillicGateVerdict:
    """Evaluate a candidate Cyrillic text chunk through TypeSafe System One."""
    th = {**DEFAULT_THRESHOLDS, **(thresholds or {})}
    state: dict[str, Any] = {"text": text}
    if context:
        state["context"] = context

    t0 = time.perf_counter()

    if mock_response is not None:
        answers = mock_response.get("answers", {})
        model_name = mock_response.get("model", "mock-jev")
        elapsed = 0.001
    else:
        if client is None:
            client = get_typesafe_client()
        questions = build_system_one_questions()
        resp = client.system_one(state=state, questions=questions)
        answers = resp.answers
        model_name = resp.model
        elapsed = time.perf_counter() - t0

    # Extract answers
    ocr_ans = answers["ocr_corruption"]
    variety_ans = answers["lexical_variety"]
    shadow_ans = answers["colonial_shadow"]
    action_ans = answers["curriculum_action"]

    ocr_score = float(ocr_ans.score if hasattr(ocr_ans, "score") else ocr_ans["score"])
    ocr_conf = float(ocr_ans.confidence if hasattr(ocr_ans, "confidence") else ocr_ans.get("confidence", 1.0))

    variety = str(variety_ans.choice if hasattr(variety_ans, "choice") else variety_ans["choice"])
    variety_conf = float(variety_ans.confidence if hasattr(variety_ans, "confidence") else variety_ans.get("confidence", 1.0))

    shadow_prob = float(shadow_ans.noul if hasattr(shadow_ans, "noul") else shadow_ans["noul"])

    action = str(action_ans.choice if hasattr(action_ans, "choice") else action_ans["choice"])
    action_conf = float(action_ans.confidence if hasattr(action_ans, "confidence") else action_ans.get("confidence", 1.0))

    # Python policy logic: decide final disposition
    needs_review = False
    review_reason = None
    final_decision = action

    # 1. OCR Junk Gate: severe corruption drops regardless of lexical variety
    if ocr_score >= th["ocr_garbage_min"]:
        final_decision = "reject"
        if ocr_conf < th["confidence_review_floor"]:
            needs_review = True
            review_reason = f"Borderline OCR corruption ({ocr_score:.2f}) with low confidence ({ocr_conf:.2f})"

    # 2. Colonial Surzhyk Invariant: Surzhyk is never admitted to standard corpus
    elif variety == "colonial_surzhyk" or shadow_prob >= th["colonial_shadow_flag"]:
        if action == "admit_standard":
            # Override model's curriculum action if colonial shadow is flagged
            final_decision = "use_as_anti_calque"
            needs_review = True
            review_reason = f"Colonial Surzhyk flagged (P={shadow_prob:.2f}) - redirected from admit_standard to anti_calque"
        else:
            final_decision = "use_as_anti_calque"

    # 3. Non-Ukrainian text
    elif variety == "non_ukrainian":
        final_decision = "reject"

    # 4. Dialect Heritage Protection
    elif variety == "authentic_dialect":
        final_decision = "admit_heritage"

    # 5. Low confidence escalation
    if variety_conf < th["confidence_review_floor"] or action_conf < th["confidence_review_floor"]:
        needs_review = True
        reason_parts = []
        if variety_conf < th["confidence_review_floor"]:
            reason_parts.append(f"low variety confidence ({variety_conf:.2f})")
        if action_conf < th["confidence_review_floor"]:
            reason_parts.append(f"low action confidence ({action_conf:.2f})")
        review_reason = review_reason or (", ".join(reason_parts))

    return CyrillicGateVerdict(
        text=text,
        decision=final_decision,
        lexical_variety=variety,
        variety_confidence=variety_conf,
        ocr_corruption_score=ocr_score,
        ocr_confidence=ocr_conf,
        colonial_shadow_prob=shadow_prob,
        curriculum_action=action,
        action_confidence=action_conf,
        latency_seconds=elapsed,
        model=model_name,
        needs_review=needs_review,
        review_reason=review_reason
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="TypeSafe System One Cyrillic Gate (ULDR #8173)"
    )
    parser.add_argument("--text", type=str, help="Single text snippet to evaluate")
    parser.add_argument("--context", type=str, help="Optional text context or metadata")
    parser.add_argument("--input-jsonl", type=Path, help="Input JSONL file of candidate items")
    parser.add_argument("--output-jsonl", type=Path, help="Output JSONL file to store verdicts")
    parser.add_argument("--text-key", type=str, default="text", help="Key in input JSONL containing text")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format for single-text mode")

    args = parser.parse_args()

    if not args.text and not args.input_jsonl:
        parser.error("Either --text or --input-jsonl must be provided.")

    client = get_typesafe_client()

    if args.text:
        verdict = evaluate_cyrillic_text(args.text, context=args.context, client=client)
        if args.format == "json":
            print(json.dumps(verdict.to_dict(), ensure_ascii=False, indent=2))
        else:
            print(f"\n--- Cyrillic Gate Verdict ({verdict.model}, {verdict.latency_seconds:.3f}s) ---")
            print(f"Text: «{verdict.text}»")
            print(f"Decision         : {verdict.decision}")
            print(f"Lexical Variety  : {verdict.lexical_variety} (conf: {verdict.variety_confidence:.2f})")
            print(f"OCR Corruption   : {verdict.ocr_corruption_score:.2f} / 2.00 (conf: {verdict.ocr_confidence:.2f})")
            print(f"Colonial Shadow  : P(yes) = {verdict.colonial_shadow_prob:.2f}")
            print(f"Curriculum Action: {verdict.curriculum_action} (conf: {verdict.action_confidence:.2f})")
            if verdict.needs_review:
                print(f"ATTENTION        : Flagged for Review! ({verdict.review_reason})")
        return 0

    if args.input_jsonl:
        if not args.output_jsonl:
            parser.error("--output-jsonl required when --input-jsonl is specified.")

        input_path = args.input_jsonl
        output_path = args.output_jsonl
        rows: list[dict[str, Any]] = []

        with input_path.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    rows.append(json.loads(line))

        print(f"Processing {len(rows)} rows from {input_path}...")
        t_start = time.perf_counter()
        verdicts: list[dict[str, Any]] = []

        for idx, row in enumerate(rows, 1):
            text_val = row.get(args.text_key, "")
            context_val = row.get("context")
            v = evaluate_cyrillic_text(text_val, context=context_val, client=client)
            verdicts.append(v.to_dict())
            if idx % 10 == 0 or idx == len(rows):
                print(f"  [{idx}/{len(rows)}] processed in {time.perf_counter() - t_start:.1f}s")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as out_f:
            for item in verdicts:
                out_f.write(json.dumps(item, ensure_ascii=False) + "\n")

        print(f"Wrote {len(verdicts)} verdicts to {output_path}")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
