#!/usr/bin/env python3
"""TypeSafe Verb Valency & Prepositional Government Verifier (Practice Hub #8170).

Automated pedagogical verification of verb valency & prepositional government practice cards:
  1. Strict Government Case Requirement (Noul: does the verb strictly govern target case?)
  2. Authentic Russian Calque Foil Verification (Noul: does distractor represent real interference?)
  3. Syntactic Exclusivity (Noul: is target the only grammatically acceptable option in context?)
  4. Sentence Frame Naturalness (Score 1–5: natural, contemporary Ukrainian context)

Decolonization & Anti-Calque Moat:
  Explicitly targets Russian interference in Ukrainian verb syntax:
    - «дякувати» + Dat (not Acc «дякую вас» ❌)
    - «вчитися» + Gen (not Dat «вчитися музиці» ❌)
    - «хворіти на» + Acc (not Ins «хворіти грипом» ❌)
    - «одружитися з» + Ins (not Loc «одружитися на ній» ❌)
    - «сміятися з» + Gen (not Ins «сміятися над ним» ❌)
    - «зрадити» + Acc (not Dat «зрадити кому» ❌)

Adheres strictly to the 2026-09-17 TypeSafe fleet contract:
  - Credentials securely resolved from ~/.secrets/typesafe-ai.key
  - Multi-attribute evaluation batched in one System One call
  - Thresholds and business logic evaluated in Python code
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

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Decision policy thresholds
DEFAULT_THRESHOLDS = {
    "government_min": 0.80,       # P(strict_government) >= 0.80
    "exclusivity_min": 0.75,      # P(syntactic_exclusivity) >= 0.75
    "calque_foil_min": 0.60,      # P(authentic_calque_foil) >= 0.60 for anti-calque drills
    "naturalness_min": 2.5,       # Naturalness score >= 2.5 (learner context)
    "confidence_review_floor": 0.50,
}


@dataclass
class ValencyVerificationVerdict:
    verb: str
    sentence_stem: str
    target: str
    calque_distractor: str
    case_demanded: str
    verdict: str  # "admit", "warn_weak_foil", "fail_ambiguous", "fail_incorrect_gov", "needs_review"
    government_prob: float
    exclusivity_prob: float
    calque_foil_prob: float
    naturalness_score: float
    naturalness_confidence: float
    latency_seconds: float
    model: str
    needs_review: bool
    findings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


try:
    from typesafe_sdk import Noul, Score, TypeSafeClient
except ImportError:
    TypeSafeClient = None  # type: ignore

    class Score:  # type: ignore
        def __init__(self, instructions: str, criteria: list[str]):
            self.type = "score"
            self.instructions = instructions
            self.criteria = criteria

        def to_dict(self) -> dict[str, Any]:
            return {"type": self.type, "instructions": self.instructions, "criteria": self.criteria}

    class Noul:  # type: ignore
        def __init__(self, instructions: str):
            self.type = "noul"
            self.instructions = instructions

        def to_dict(self) -> dict[str, Any]:
            return {"type": self.type, "instructions": self.instructions}


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
    """Instantiate TypeSafeClient using the verified SDK, or None if unavailable."""
    if TypeSafeClient is None:
        return None
    resolved = api_key or resolve_api_key()
    if not resolved:
        raise ValueError(
            "TypeSafe API key not found. Ensure TYPESAFE_API_KEY is exported or ~/.secrets/typesafe-ai.key exists."
        )

    return TypeSafeClient(api_key=resolved)


def build_valency_questions() -> dict[str, Any]:
    """Define the 4 batched questions for verb valency drill verification."""
    return {
        "strict_government": Noul(
            instructions=(
                "In standard literary Ukrainian, does this verb strictly govern the specified grammatical case "
                "or prepositional construction in this syntactic context?"
            )
        ),
        "syntactic_exclusivity": Noul(
            instructions=(
                "In this sentence context, is the target option the ONLY grammatically acceptable choice "
                "(the distractor is strictly ungrammatical according to standard Ukrainian norms)?"
            )
        ),
        "is_calque_foil": Noul(
            instructions=(
                "Does the provided distractor reflect a common, attested Russian linguistic interference pattern "
                "(Surzhyk / Russian syntactic government calque) that Ukrainian learners frequently produce?"
            )
        ),
        "sentence_naturalness": Score(
            instructions="How natural, idiomatic, and appropriate is this sentence context for a language drill?",
            criteria=[
                "1 - Unnatural, bizarre, or grammatically broken context",
                "2 - Stilted, archaic, or overly artificial sentence",
                "3 - Clear, standard, and acceptable everyday context",
                "4 - Natural, lively, and highly realistic Ukrainian sentence",
                "5 - Outstanding authentic exemplar from contemporary Ukrainian usage",
            ],
        ),
    }


def verify_valency_card(
    verb: str,
    stem: str,
    target: str,
    calque_distractor: str,
    case_demanded: str,
    client: Any = None,
    thresholds: dict[str, float] | None = None,
    mock_response: dict[str, Any] | None = None,
) -> ValencyVerificationVerdict:
    """Verify a verb valency drill card using TypeSafe System One."""
    th = {**DEFAULT_THRESHOLDS, **(thresholds or {})}

    if mock_response is not None:
        latency = 0.0
        model = mock_response.get("model", "jev-mock")
        answers = mock_response["answers"]
    else:
        typesafe = client or get_typesafe_client()
        state = {
            "target_verb": verb,
            "case_demanded": case_demanded,
            "sentence_stem": stem,
            "target_correct_form": target,
            "calque_distractor_form": calque_distractor,
        }

        t0 = time.perf_counter()
        if typesafe is not None:
            response = typesafe.system_one(
                state=state,
                questions=build_valency_questions(),
                model="jev-latest",
            )
            latency = time.perf_counter() - t0
            answers = response.answers
            model = response.model
        else:
            import urllib.request

            api_key = resolve_api_key()
            if not api_key:
                raise ValueError("TypeSafe API key not found.")
            questions = {
                k: v.to_dict() if hasattr(v, "to_dict") else v
                for k, v in build_valency_questions().items()
            }
            body = json.dumps({"state": state, "model": "jev-latest", "questions": questions}).encode()
            req = urllib.request.Request(
                "https://api.typesafe.ai/v1/systemone",
                data=body,
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.load(resp)
            latency = time.perf_counter() - t0
            answers = data.get("answers", {})
            model = data.get("model", "jev-latest")
    gov_prob = float(answers["strict_government"].noul)
    excl_prob = float(answers["syntactic_exclusivity"].noul)
    calque_prob = float(answers["is_calque_foil"].noul)
    nat_score = float(answers["sentence_naturalness"].score)
    nat_conf = float(answers["sentence_naturalness"].confidence)

    findings: list[str] = []
    needs_review = False

    if nat_conf < th["confidence_review_floor"]:
        needs_review = True
        findings.append(f"Low naturalness confidence ({nat_conf:.2f})")

    if gov_prob < th["government_min"]:
        verdict = "fail_incorrect_gov"
        findings.append(f"Strict government not confirmed (P={gov_prob:.2f} < {th['government_min']})")
    elif excl_prob < th["exclusivity_min"]:
        verdict = "fail_ambiguous"
        findings.append(f"Target is not exclusively acceptable in context (P={excl_prob:.2f} < {th['exclusivity_min']})")
    elif calque_prob < th["calque_foil_min"]:
        verdict = "warn_weak_foil"
        findings.append(f"Distractor is not a strong calque foil (P={calque_prob:.2f} < {th['calque_foil_min']})")
    elif nat_score < th["naturalness_min"]:
        verdict = "needs_review"
        findings.append(f"Sentence naturalness below threshold ({nat_score:.1f} < {th['naturalness_min']})")
    elif needs_review:
        verdict = "needs_review"
    else:
        verdict = "admit"

    return ValencyVerificationVerdict(
        verb=verb,
        sentence_stem=stem,
        target=target,
        calque_distractor=calque_distractor,
        case_demanded=case_demanded,
        verdict=verdict,
        government_prob=gov_prob,
        exclusivity_prob=excl_prob,
        calque_foil_prob=calque_prob,
        naturalness_score=nat_score,
        naturalness_confidence=nat_conf,
        latency_seconds=latency,
        model=model,
        needs_review=needs_review,
        findings=findings,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify Verb Valency practice cards via TypeSafe.")
    parser.add_argument("--verb", required=True, help="Target verb (e.g. дякувати)")
    parser.add_argument("--stem", required=True, help="Sentence stem with blank (e.g. 'Я щиро дякую ___ за підтримку.')")
    parser.add_argument("--target", required=True, help="Target correct answer (e.g. 'вам')")
    parser.add_argument("--calque", required=True, help="Calque distractor (e.g. 'вас')")
    parser.add_argument("--case", required=True, help="Case demanded (e.g. 'Dative')")
    parser.add_argument("--json", action="store_true", help="Emit JSON output")
    args = parser.parse_args()

    verdict = verify_valency_card(
        verb=args.verb,
        stem=args.stem,
        target=args.target,
        calque_distractor=args.calque,
        case_demanded=args.case,
    )

    if args.json:
        print(json.dumps(verdict.to_dict(), ensure_ascii=False, indent=2))
        return

    print(f"=== TypeSafe Verb Valency Verifier: {verdict.verb} ===")
    print(f"Stem:           {verdict.sentence_stem}")
    print(f"Target:         {verdict.target} (Demanded: {verdict.case_demanded})")
    print(f"Calque Foil:    {verdict.calque_distractor}")
    print(f"Verdict:        {verdict.verdict.upper()} (latency: {verdict.latency_seconds:.2f}s, model: {verdict.model})")
    print(f"Government:     P(strict_gov) = {verdict.government_prob:.2f}")
    print(f"Exclusivity:    P(unambiguous) = {verdict.exclusivity_prob:.2f}")
    print(f"Calque Yield:   P(calque_foil) = {verdict.calque_foil_prob:.2f}")
    print(f"Naturalness:    Score {verdict.naturalness_score:.1f}/5 (conf={verdict.naturalness_confidence:.2f})")
    if verdict.findings:
        print("Findings:")
        for f in verdict.findings:
            print(f"  - {f}")


if __name__ == "__main__":
    main()
