"""TypeSafe (Jev) structured triage for curriculum build / upgrade.

Issues:
  - #8177 EC / Find-and-Fix activity fan-out
  - #8178 vocab keep/drop labeling
  - #8179 pre-QG / pre-CF readiness scoring

Policy (operator 2026-09-17): use freely for Choice / Score / Noul labeling.
Label → verify for attested morphology (VESUM / Sources). Never rewrite human
source text. Not a CF / Monitor / merge substitute.

Credentials: ``TYPESAFE_API_KEY`` or ``~/.secrets/typsafe-ai.key``
(also accepts ``~/.secrets/typesafe-ai.key``).
"""

from __future__ import annotations

import argparse
import json
import os
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Protocol

# --- thresholds owned by code (tune here; model only supplies judgments) ---

NOUL_TRUE_THRESHOLD = 0.7
EC_MIN_OPTIONS = 3
SCORE_BAND_LOW = 0.75  # below → lower band for 3-point scores
SCORE_BAND_HIGH = 1.75  # at/above → upper band


class _SystemOneClient(Protocol):
    def system_one(
        self,
        state: Any,
        questions: Mapping[str, Any],
        *,
        model: str | None = None,
    ) -> Any: ...


@dataclass(frozen=True)
class TypeSafeReceipt:
    """Usage + model id for spend / reproducibility logs."""

    model: str | None
    input_tokens: int | None
    output_tokens: int | None
    request_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class NoulJudgment:
    probability: float
    is_true: bool


@dataclass(frozen=True)
class ChoiceJudgment:
    choice: str
    confidence: float
    probabilities: Mapping[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class ScoreJudgment:
    score: float
    confidence: float
    band: str
    legend: Mapping[int, str] = field(default_factory=dict)


@dataclass(frozen=True)
class EcItemEvaluation:
    """#8177 — Find-and-Fix / error-correction fan-out."""

    has_winning_chip: NoulJudgment
    too_few_options: NoulJudgment
    unaccented_copy_of_winner: NoulJudgment
    a1_en_scaffold_present: NoulJudgment
    distractor_family: ChoiceJudgment
    pedagogical_clarity: ScoreJudgment
    receipt: TypeSafeReceipt
    # Deterministic code checks (not model):
    option_count: int
    exact_winner_in_options: bool

    @property
    def needs_repair(self) -> bool:
        """Code-owned routing: hard mechanical defects or weak clarity."""
        if not self.exact_winner_in_options or self.option_count < EC_MIN_OPTIONS:
            return True
        if self.unaccented_copy_of_winner.is_true:
            return True
        if self.pedagogical_clarity.band == "unclear":
            return True
        return False


@dataclass(frozen=True)
class VocabRowEvaluation:
    """#8178 — vocab keep/drop (+ Russian-shadow *suspect*)."""

    keep_for_level: NoulJudgment
    ocr_junk: NoulJudgment
    russian_shadow_suspect: NoulJudgment
    proper_name: NoulJudgment
    dialect_bucket: ChoiceJudgment
    domain: ChoiceJudgment
    priority: ScoreJudgment
    receipt: TypeSafeReceipt

    @property
    def escalate_to_sources(self) -> bool:
        """Suspect flags that must not be treated as morphology fact."""
        return self.russian_shadow_suspect.is_true or self.ocr_junk.is_true


@dataclass(frozen=True)
class LessonReadinessEvaluation:
    """#8179 — pre-QG / pre-CF readiness."""

    preserve_expand_fidelity: ScoreJudgment
    immersion_fit: ScoreJudgment
    decolonize_risk: ScoreJudgment
    invented_upgrade_defect: NoulJudgment
    qg_budget: ChoiceJudgment
    cf_ready_likely: NoulJudgment
    receipt: TypeSafeReceipt

    @property
    def recommended_qg(self) -> str:
        """Map model Choice to a code-owned QG budget string."""
        return self.qg_budget.choice


def load_typesafe_api_key() -> str:
    """Load API key from env or host secrets dir. Never logs the value."""
    env = os.environ.get("TYPESAFE_API_KEY", "").strip()
    if env:
        return env
    home = Path.home() / ".secrets"
    for name in ("typsafe-ai.key", "typesafe-ai.key"):
        path = home / name
        if path.is_file():
            return path.read_text(encoding="utf-8").strip().replace("\r", "")
    raise FileNotFoundError(
        "TYPESAFE_API_KEY unset and neither ~/.secrets/typsafe-ai.key "
        "nor ~/.secrets/typesafe-ai.key found"
    )


def make_client(api_key: str | None = None) -> Any:
    """Construct a sync TypeSafeClient (lazy import)."""
    from typesafe_sdk import TypeSafeClient

    key = api_key if api_key is not None else load_typesafe_api_key()
    os.environ.setdefault("TYPESAFE_API_KEY", key)
    return TypeSafeClient()


def _receipt_from_response(response: Any) -> TypeSafeReceipt:
    usage = getattr(response, "usage", None)
    return TypeSafeReceipt(
        model=getattr(response, "model", None),
        input_tokens=getattr(usage, "input_tokens", None) if usage else None,
        output_tokens=getattr(usage, "output_tokens", None) if usage else None,
        request_id=getattr(response, "request_id", None),
    )


def _noul(response: Any, key: str, *, threshold: float = NOUL_TRUE_THRESHOLD) -> NoulJudgment:
    ans = response.nouls[key]
    prob = float(ans.noul)
    return NoulJudgment(probability=prob, is_true=prob >= threshold)


def _choice(response: Any, key: str) -> ChoiceJudgment:
    ans = response.choices[key]
    probs = dict(getattr(ans, "probabilities", {}) or {})
    return ChoiceJudgment(
        choice=str(ans.choice),
        confidence=float(getattr(ans, "confidence", 0.0) or 0.0),
        probabilities=probs,
    )


def _score(
    response: Any,
    key: str,
    *,
    bands: Sequence[str],
) -> ScoreJudgment:
    """Map continuous score onto named bands from the Score criteria order."""
    ans = response.scores[key]
    raw = float(ans.score)
    legend = {int(k): str(v) for k, v in dict(getattr(ans, "legend", {}) or {}).items()}
    if len(bands) != 3:
        raise ValueError("this helper expects 3-point Score criteria")
    if raw < SCORE_BAND_LOW:
        band = bands[0]
    elif raw < SCORE_BAND_HIGH:
        band = bands[1]
    else:
        band = bands[2]
    return ScoreJudgment(
        score=raw,
        confidence=float(getattr(ans, "confidence", 0.0) or 0.0),
        band=band,
        legend=legend,
    )


def _strip_combining(text: str) -> str:
    """Remove combining acute/grave for unaccented-duplicate heuristics."""
    import unicodedata

    return "".join(
        ch for ch in unicodedata.normalize("NFD", text) if unicodedata.category(ch) != "Mn"
    )


def exact_winner_present(options: Sequence[str], correct_form: str) -> bool:
    target = correct_form.strip()
    return any(opt.strip() == target for opt in options)


def has_unaccented_copy(options: Sequence[str], correct_form: str) -> bool:
    """True when an option matches winner with accents stripped but differs raw."""
    winner = correct_form.strip()
    winner_plain = _strip_combining(winner)
    if not winner_plain or winner_plain == winner:
        return False
    for opt in options:
        o = opt.strip()
        if o == winner:
            continue
        if _strip_combining(o) == winner_plain:
            return True
    return False


def evaluate_ec_item(
    *,
    sentence: str,
    error: str,
    correct_form: str,
    options: Sequence[str],
    level: str,
    prompt_en: str | None = None,
    client: _SystemOneClient | None = None,
    model: str | None = None,
) -> EcItemEvaluation:
    """#8177 — one batched system_one over a Find-and-Fix / EC item."""
    from typesafe_sdk import Choice, Noul, Score

    opts = [str(o) for o in options]
    level_l = (level or "").strip().lower()
    state = {
        "activity_type": "error_correction",
        "level": level_l,
        "sentence": sentence,
        "error": error,
        "correctForm": correct_form,
        "options": list(opts),
        "prompt_en": prompt_en or "",
        "option_count": len(opts),
        "exact_winner_in_options": exact_winner_present(opts, correct_form),
        "has_unaccented_duplicate_heuristic": has_unaccented_copy(opts, correct_form),
    }
    questions = {
        "has_winning_chip": Noul(
            instructions=(
                "Do the options include a chip that matches correctForm exactly "
                "(same characters, including stress marks)?"
            )
        ),
        "too_few_options": Noul(
            instructions="Are there fewer than three distinct option chips?"
        ),
        "unaccented_copy_of_winner": Noul(
            instructions=(
                "Is there an unaccented (or differently accented) duplicate of the "
                "accented winning form among the options?"
            )
        ),
        "a1_en_scaffold_present": Noul(
            instructions=(
                "If level is a1, is an English scaffold / prompt_en present and useful? "
                "If level is not a1, answer no."
            )
        ),
        "distractor_family": Choice(
            instructions="Primary learner-contrast family for this Find-and-Fix item.",
            criteria={
                "stress": "stress / accent contrast",
                "soft_sign": "soft sign ь presence or absence",
                "apostrophe": "apostrophe presence or absence",
                "letter": "letter substitution unrelated to soft sign / apostrophe / stress",
                "other": "another contrast type",
                "unclear": "cannot determine",
            },
        ),
        "pedagogical_clarity": Score(
            instructions="How clear and teachable is this Find-and-Fix item for the stated level?",
            criteria=["unclear", "usable", "strong"],
        ),
    }

    own_client = client is None
    c = client if client is not None else make_client()
    try:
        response = c.system_one(state=state, questions=questions, model=model)
    finally:
        if own_client and hasattr(c, "close"):
            c.close()

    return EcItemEvaluation(
        has_winning_chip=_noul(response, "has_winning_chip"),
        too_few_options=_noul(response, "too_few_options"),
        unaccented_copy_of_winner=_noul(response, "unaccented_copy_of_winner"),
        a1_en_scaffold_present=_noul(response, "a1_en_scaffold_present"),
        distractor_family=_choice(response, "distractor_family"),
        pedagogical_clarity=_score(
            response, "pedagogical_clarity", bands=("unclear", "usable", "strong")
        ),
        receipt=_receipt_from_response(response),
        option_count=len(opts),
        exact_winner_in_options=exact_winner_present(opts, correct_form),
    )


def evaluate_vocab_row(
    *,
    lemma: str,
    example: str = "",
    level: str,
    note: str = "",
    client: _SystemOneClient | None = None,
    model: str | None = None,
) -> VocabRowEvaluation:
    """#8178 — label one vocab candidate. Suspect ≠ VESUM fact."""
    from typesafe_sdk import Choice, Noul, Score

    state = {
        "lemma": lemma,
        "example": example,
        "level": (level or "").strip().lower(),
        "note": note,
        "language": "Ukrainian",
    }
    questions = {
        "keep_for_level": Noul(
            instructions=(
                "Is this lemma appropriate to teach at the stated CEFR level "
                "(not far too advanced or trivial junk)?"
            )
        ),
        "ocr_junk": Noul(
            instructions=(
                "Does the lemma look like OCR / encoding corruption "
                "(broken ligatures, Latin/Cyrillic homoglyphs, garbage)?"
            )
        ),
        "russian_shadow_suspect": Noul(
            instructions=(
                "Is this lemma a *suspect* Russianism, calque, or Surzhyk form "
                "that a Ukrainian curriculum should escalate for verification? "
                "Suspect only — not a dictionary ruling."
            )
        ),
        "proper_name": Noul(
            instructions="Is this primarily a proper name, toponym, or personal name?"
        ),
        "dialect_bucket": Choice(
            instructions="Dialect / register bucket for this lemma.",
            criteria={
                "standard": "standard modern Ukrainian",
                "regional": "authentic regional dialect",
                "historical": "historical literary form",
                "unclear": "cannot tell",
            },
        ),
        "domain": Choice(
            instructions="Domain for curriculum routing.",
            criteria={
                "everyday": "everyday / classroom",
                "academic": "academic / school subject",
                "folk": "folk / ethnographic",
                "technical": "technical / specialized",
                "other": "other",
            },
        ),
        "priority": Score(
            instructions="Curriculum priority if kept.",
            criteria=["drop", "optional", "core"],
        ),
    }

    own_client = client is None
    c = client if client is not None else make_client()
    try:
        response = c.system_one(state=state, questions=questions, model=model)
    finally:
        if own_client and hasattr(c, "close"):
            c.close()

    return VocabRowEvaluation(
        keep_for_level=_noul(response, "keep_for_level"),
        ocr_junk=_noul(response, "ocr_junk"),
        russian_shadow_suspect=_noul(response, "russian_shadow_suspect"),
        proper_name=_noul(response, "proper_name"),
        dialect_bucket=_choice(response, "dialect_bucket"),
        domain=_choice(response, "domain"),
        priority=_score(response, "priority", bands=("drop", "optional", "core")),
        receipt=_receipt_from_response(response),
    )


def evaluate_lesson_readiness(
    *,
    level: str,
    slug: str,
    lesson_excerpt: str,
    activities_excerpt: str = "",
    gate_summary: str = "",
    client: _SystemOneClient | None = None,
    model: str | None = None,
) -> LessonReadinessEvaluation:
    """#8179 — cheap readiness labels before paid QG / CF."""
    from typesafe_sdk import Choice, Noul, Score

    state = {
        "level": (level or "").strip().lower(),
        "slug": slug,
        "lesson_excerpt": lesson_excerpt[:6000],
        "activities_excerpt": activities_excerpt[:4000],
        "gate_summary": gate_summary[:2000],
        "note": (
            "A1 may use English scaffolding by design. From A2, maximize Ukrainian immersion. "
            "Upgrade must preserve-and-expand, not invent defects."
        ),
    }
    questions = {
        "preserve_expand_fidelity": Score(
            instructions=(
                "How faithful is this upgrade/build to preserve-and-expand "
                "(vs inventing a rewrite for no real archive defect)?"
            ),
            criteria=["invented_rewrite", "light_expand", "faithful_preserve_expand"],
        ),
        "immersion_fit": Score(
            instructions="Ukrainian immersion fit for the stated level.",
            criteria=["english_heavy", "mixed", "immersion_ok"],
        ),
        "decolonize_risk": Score(
            instructions="Decolonization / Russian-shadow risk in the excerpt.",
            criteria=["clear_risk", "mild", "clean"],
        ),
        "invented_upgrade_defect": Noul(
            instructions=(
                "Does this look like an invented upgrade defect — rewriting archive "
                "content without a real pedagogical defect?"
            )
        ),
        "qg_budget": Choice(
            instructions="Recommended quality-gate / QG budget before cross-family CF.",
            criteria={
                "full": "run full paid QG / writer repair loop",
                "light": "light local gates + targeted repair only",
                "skip_to_gates": "skip paid QG; local gates look sufficient before CF seating",
            },
        ),
        "cf_ready_likely": Noul(
            instructions=(
                "Does this snapshot look ready enough to seat independent cross-family CF "
                "(not a guarantee — mechanical gates still bind)?"
            )
        ),
    }

    own_client = client is None
    c = client if client is not None else make_client()
    try:
        response = c.system_one(state=state, questions=questions, model=model)
    finally:
        if own_client and hasattr(c, "close"):
            c.close()

    return LessonReadinessEvaluation(
        preserve_expand_fidelity=_score(
            response,
            "preserve_expand_fidelity",
            bands=("invented_rewrite", "light_expand", "faithful_preserve_expand"),
        ),
        immersion_fit=_score(
            response,
            "immersion_fit",
            bands=("english_heavy", "mixed", "immersion_ok"),
        ),
        decolonize_risk=_score(
            response,
            "decolonize_risk",
            bands=("clear_risk", "mild", "clean"),
        ),
        invented_upgrade_defect=_noul(response, "invented_upgrade_defect"),
        qg_budget=_choice(response, "qg_budget"),
        cf_ready_likely=_noul(response, "cf_ready_likely"),
        receipt=_receipt_from_response(response),
    )


def _ec_to_dict(ev: EcItemEvaluation) -> dict[str, Any]:
    return {
        "has_winning_chip": asdict(ev.has_winning_chip),
        "too_few_options": asdict(ev.too_few_options),
        "unaccented_copy_of_winner": asdict(ev.unaccented_copy_of_winner),
        "a1_en_scaffold_present": asdict(ev.a1_en_scaffold_present),
        "distractor_family": {
            "choice": ev.distractor_family.choice,
            "confidence": ev.distractor_family.confidence,
            "probabilities": dict(ev.distractor_family.probabilities),
        },
        "pedagogical_clarity": {
            "score": ev.pedagogical_clarity.score,
            "confidence": ev.pedagogical_clarity.confidence,
            "band": ev.pedagogical_clarity.band,
        },
        "option_count": ev.option_count,
        "exact_winner_in_options": ev.exact_winner_in_options,
        "needs_repair": ev.needs_repair,
        "receipt": ev.receipt.to_dict(),
    }


def _vocab_to_dict(ev: VocabRowEvaluation) -> dict[str, Any]:
    return {
        "keep_for_level": asdict(ev.keep_for_level),
        "ocr_junk": asdict(ev.ocr_junk),
        "russian_shadow_suspect": asdict(ev.russian_shadow_suspect),
        "proper_name": asdict(ev.proper_name),
        "dialect_bucket": {
            "choice": ev.dialect_bucket.choice,
            "confidence": ev.dialect_bucket.confidence,
        },
        "domain": {"choice": ev.domain.choice, "confidence": ev.domain.confidence},
        "priority": {
            "score": ev.priority.score,
            "band": ev.priority.band,
            "confidence": ev.priority.confidence,
        },
        "escalate_to_sources": ev.escalate_to_sources,
        "receipt": ev.receipt.to_dict(),
    }


def _readiness_to_dict(ev: LessonReadinessEvaluation) -> dict[str, Any]:
    return {
        "preserve_expand_fidelity": {
            "score": ev.preserve_expand_fidelity.score,
            "band": ev.preserve_expand_fidelity.band,
        },
        "immersion_fit": {
            "score": ev.immersion_fit.score,
            "band": ev.immersion_fit.band,
        },
        "decolonize_risk": {
            "score": ev.decolonize_risk.score,
            "band": ev.decolonize_risk.band,
        },
        "invented_upgrade_defect": asdict(ev.invented_upgrade_defect),
        "qg_budget": {
            "choice": ev.qg_budget.choice,
            "confidence": ev.qg_budget.confidence,
        },
        "cf_ready_likely": asdict(ev.cf_ready_likely),
        "recommended_qg": ev.recommended_qg,
        "receipt": ev.receipt.to_dict(),
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_ec = sub.add_parser("ec", help="#8177 evaluate one EC item")
    p_ec.add_argument("--sentence", required=True)
    p_ec.add_argument("--error", required=True)
    p_ec.add_argument("--correct-form", required=True)
    p_ec.add_argument("--options", required=True, help="JSON array of option strings")
    p_ec.add_argument("--level", default="a1")
    p_ec.add_argument("--prompt-en", default="")

    p_v = sub.add_parser("vocab", help="#8178 evaluate one vocab row")
    p_v.add_argument("--lemma", required=True)
    p_v.add_argument("--example", default="")
    p_v.add_argument("--level", default="a1")
    p_v.add_argument("--note", default="")

    p_r = sub.add_parser("readiness", help="#8179 evaluate lesson readiness")
    p_r.add_argument("--level", required=True)
    p_r.add_argument("--slug", required=True)
    p_r.add_argument("--lesson-excerpt", required=True)
    p_r.add_argument("--activities-excerpt", default="")
    p_r.add_argument("--gate-summary", default="")

    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.cmd == "ec":
        options = json.loads(args.options)
        ev = evaluate_ec_item(
            sentence=args.sentence,
            error=args.error,
            correct_form=args.correct_form,
            options=options,
            level=args.level,
            prompt_en=args.prompt_en or None,
        )
        print(json.dumps(_ec_to_dict(ev), ensure_ascii=False, indent=2))
        return 0
    if args.cmd == "vocab":
        ev = evaluate_vocab_row(
            lemma=args.lemma,
            example=args.example,
            level=args.level,
            note=args.note,
        )
        print(json.dumps(_vocab_to_dict(ev), ensure_ascii=False, indent=2))
        return 0
    if args.cmd == "readiness":
        ev = evaluate_lesson_readiness(
            level=args.level,
            slug=args.slug,
            lesson_excerpt=args.lesson_excerpt,
            activities_excerpt=args.activities_excerpt,
            gate_summary=args.gate_summary,
        )
        print(json.dumps(_readiness_to_dict(ev), ensure_ascii=False, indent=2))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
