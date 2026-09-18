#!/usr/bin/env python3
"""TypeSafe Word Atlas Sense & Collocation Gate (Word Atlas #4387, #6460).

Automated lexical and pedagogical verification of candidate example sentences,
senses, and collocations for the Word Atlas:
  1. Sense Alignment (Choice: primary_sense, secondary_sense, metaphorical, wrong_sense)
  2. Authentic Ukrainian Quality (Noul: natural contemporary Ukrainian vs calqued)
  3. Calque Risk Detection (Choice: none_authentic, subtle_surzhyk, direct_russian_calque, awkward_translation)
  4. Pedagogical Clarity (Score 1–5: suitability as learner exemplar)
  5. Estimated CEFR Level (Choice: A1–C2)

Decolonization Moat (§6):
  Specifically catches polysemous Russian calques (e.g. «вірний» meaning "loyal" [authentic]
  vs "correct" [calque → «правильний»]) and active participle traps, ensuring Atlas
  examples reinforce standard, authentic Ukrainian.

Adheres strictly to the 2026-09-17 TypeSafe fleet contract:
  - Credentials securely resolved from ~/.secrets/typsafe-ai.key (never committed or leaked)
  - Thresholds and business logic evaluated in Python code, not prompt prose
  - Complements VESUM and sources.db; VESUM remains morphological SSOT
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

# Decision policy thresholds (evaluated in Python code)
DEFAULT_THRESHOLDS = {
    "authenticity_min": 0.75,          # P(is_authentic) must be >= 0.75 to auto-admit
    "pedagogical_score_min": 3.0,      # Score >= 3.0 required for learner examples
    "confidence_review_floor": 0.50,   # Confidence < 0.50 flags for advisory review
}


@dataclass
class AtlasSenseGateVerdict:
    lemma: str
    definition: str
    sentence: str
    verdict: str  # "admit", "reject_calque", "reject_off_sense", "warn_pedagogy", "needs_review"
    sense_match: str
    sense_match_prob: float
    is_authentic_prob: float
    calque_risk: str
    calque_risk_prob: float
    pedagogical_score: float
    pedagogical_confidence: float
    cefr_level: str
    cefr_confidence: float
    latency_seconds: float
    model: str
    needs_review: bool
    findings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


try:
    from typesafe_sdk import Choice, Noul, Score, TypeSafeClient
except ImportError:
    TypeSafeClient = None  # type: ignore

    class Choice:  # type: ignore
        def __init__(self, instructions: str, criteria: dict[str, str]):
            self.type = "choice"
            self.instructions = instructions
            self.criteria = criteria

        def to_dict(self) -> dict[str, Any]:
            return {"type": self.type, "instructions": self.instructions, "criteria": self.criteria}

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

    for name in ("typsafe-ai.key", "typesafe-ai.key"):
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
            "TypeSafe API key not found. Ensure TYPESAFE_API_KEY is exported or ~/.secrets/typsafe-ai.key exists."
        )
    return TypeSafeClient(api_key=resolved)


def build_atlas_questions() -> dict[str, Any]:
    """Define the 5 batched questions for Word Atlas example sentence gating."""
    return {
        "sense_match": Choice(
            instructions=(
                "Does the target word in this Ukrainian example sentence illustrate the "
                "given dictionary definition?"
            ),
            criteria={
                "primary_sense": "Directly and clearly illustrates this specific definition.",
                "secondary_sense": "Illustrates a related legitimate secondary sense of the lemma.",
                "metaphorical_or_figurative": "Illustrates a figurative, poetic, or idiom-bound use.",
                "unrelated_or_wrong_sense": "Illustrates a different homonym or an entirely unrelated meaning.",
            },
        ),
        "is_authentic_ukrainian": Noul(
            instructions=(
                "Is this example sentence authentic, natural contemporary standard Ukrainian, "
                "free from Soviet-era bureaucratic calques and unnatural literal translations?"
            )
        ),
        "calque_risk": Choice(
            instructions=(
                "Does this sentence exhibit Russian linguistic calquing, Russianized false-friend polysemy "
                "(e.g., using 'вірний' for 'правильний', 'відноситися' for 'ставитися'), or active-participle calques?"
            ),
            criteria={
                "none_authentic": "Authentic Ukrainian syntax and vocabulary.",
                "subtle_surzhyk": "Contains minor colloquial or dialectal interference.",
                "direct_russian_calque": "Direct Russian calque or false-friend polyseme violation.",
                "awkward_translation": "Awkward translationese or machine-translation artifact.",
            },
        ),
        "pedagogical_clarity": Score(
            instructions=(
                "How effective is this sentence as a textbook-quality exemplar for a learner dictionary entry?"
            ),
            criteria=[
                "1 - Obscure, fragmented, or confusing for language learners",
                "2 - Complex, heavy subordinate clauses or rare context",
                "3 - Adequate and comprehensible everyday sentence",
                "4 - Very clear context making the target word meaning evident",
                "5 - Exemplary, memorable textbook illustration",
            ],
        ),
        "cefr_level": Choice(
            instructions="What CEFR language proficiency level is required to comprehend this example sentence?",
            criteria={
                "A1": "Beginner: simple present, basic everyday vocabulary",
                "A2": "Elementary: routine expressions, simple past/future",
                "B1": "Intermediate: straightforward connected prose, standard topics",
                "B2": "Upper-intermediate: complex text, nuanced vocabulary",
                "C1": "Advanced: idiomatic, abstract, or literary Ukrainian",
                "C2": "Mastery: archaic, highly specialized, or complex literary syntax",
            },
        ),
    }


def evaluate_atlas_example(
    lemma: str,
    definition: str,
    sentence: str,
    pos: str | None = None,
    client: Any = None,
    thresholds: dict[str, float] | None = None,
    mock_response: dict[str, Any] | None = None,
) -> AtlasSenseGateVerdict:
    """Evaluate a candidate Word Atlas example sentence using TypeSafe System One."""
    th = {**DEFAULT_THRESHOLDS, **(thresholds or {})}

    if mock_response is not None:
        latency = 0.0
        model = mock_response.get("model", "jev-mock")
        answers = mock_response["answers"]
    else:
        typesafe = client or get_typesafe_client()
        state = {
            "lemma": lemma,
            "part_of_speech": pos or "unspecified",
            "dictionary_definition": definition,
            "example_sentence": sentence,
        }

        t0 = time.perf_counter()
        if typesafe is not None:
            response = typesafe.system_one(
                state=state,
                questions=build_atlas_questions(),
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
                for k, v in build_atlas_questions().items()
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
    sense_ans = answers["sense_match"]
    auth_ans = answers["is_authentic_ukrainian"]
    calque_ans = answers["calque_risk"]
    ped_ans = answers["pedagogical_clarity"]
    cefr_ans = answers["cefr_level"]

    sense_match = str(sense_ans.choice)
    sense_match_prob = float(sense_ans.probabilities.get(sense_match, 0.0))
    is_auth_prob = float(auth_ans.noul)
    calque_risk = str(calque_ans.choice)
    calque_risk_prob = float(calque_ans.probabilities.get(calque_risk, 0.0))
    ped_score = float(ped_ans.score)
    ped_conf = float(ped_ans.confidence)
    cefr_level = str(cefr_ans.choice)
    cefr_conf = float(cefr_ans.confidence)

    findings: list[str] = []
    needs_review = False

    # Check for low confidence
    if ped_conf < th["confidence_review_floor"] or cefr_conf < th["confidence_review_floor"]:
        needs_review = True
        findings.append(f"Low confidence (ped={ped_conf:.2f}, cefr={cefr_conf:.2f})")

    # Determine verdict based on business policy
    if calque_risk in ("direct_russian_calque", "awkward_translation") or is_auth_prob < 0.40:
        verdict = "reject_calque"
        findings.append(f"Calque or unauthentic Ukrainian detected ({calque_risk}, auth={is_auth_prob:.2f})")
    elif sense_match == "unrelated_or_wrong_sense":
        verdict = "reject_off_sense"
        findings.append(f"Sentence does not illustrate definition (sense_match={sense_match})")
    elif ped_score < th["pedagogical_score_min"]:
        verdict = "warn_pedagogy"
        findings.append(f"Pedagogical clarity below threshold ({ped_score:.1f} < {th['pedagogical_score_min']})")
    elif is_auth_prob < th["authenticity_min"]:
        verdict = "needs_review"
        findings.append(f"Authenticity borderline ({is_auth_prob:.2f} < {th['authenticity_min']})")
    elif needs_review:
        verdict = "needs_review"
    else:
        verdict = "admit"

    return AtlasSenseGateVerdict(
        lemma=lemma,
        definition=definition,
        sentence=sentence,
        verdict=verdict,
        sense_match=sense_match,
        sense_match_prob=sense_match_prob,
        is_authentic_prob=is_auth_prob,
        calque_risk=calque_risk,
        calque_risk_prob=calque_risk_prob,
        pedagogical_score=ped_score,
        pedagogical_confidence=ped_conf,
        cefr_level=cefr_level,
        cefr_confidence=cefr_conf,
        latency_seconds=latency,
        model=model,
        needs_review=needs_review,
        findings=findings,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate Word Atlas candidate sentences via TypeSafe.")
    parser.add_argument("--lemma", required=True, help="Atlas headword lemma (e.g. вірний)")
    parser.add_argument("--definition", required=True, help="Target dictionary definition")
    parser.add_argument("--sentence", required=True, help="Candidate example sentence")
    parser.add_argument("--pos", default=None, help="Part of speech")
    parser.add_argument("--json", action="store_true", help="Emit raw JSON verdict")
    args = parser.parse_args()

    verdict = evaluate_atlas_example(
        lemma=args.lemma,
        definition=args.definition,
        sentence=args.sentence,
        pos=args.pos,
    )

    if args.json:
        print(json.dumps(verdict.to_dict(), ensure_ascii=False, indent=2))
        return

    print(f"=== TypeSafe Atlas Sense Gate: {verdict.lemma} ===")
    print(f"Sentence:        {verdict.sentence}")
    print(f"Definition:      {verdict.definition}")
    print(f"Verdict:         {verdict.verdict.upper()} (latency: {verdict.latency_seconds:.2f}s, model: {verdict.model})")
    print(f"Sense Match:     {verdict.sense_match} (prob={verdict.sense_match_prob:.2f})")
    print(f"Authenticity:    P(authentic) = {verdict.is_authentic_prob:.2f}")
    print(f"Calque Risk:     {verdict.calque_risk} (prob={verdict.calque_risk_prob:.2f})")
    print(f"Pedagogical:     Score {verdict.pedagogical_score:.1f}/5 (conf={verdict.pedagogical_confidence:.2f})")
    print(f"CEFR Level:      {verdict.cefr_level} (conf={verdict.cefr_confidence:.2f})")
    if verdict.findings:
        print("Findings:")
        for f in verdict.findings:
            print(f"  - {f}")


if __name__ == "__main__":
    main()
