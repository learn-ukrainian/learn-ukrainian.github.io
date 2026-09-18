"""TypeSafe (Jev) structured triage for curriculum build / upgrade.

Issues:
  - #8177 EC / Find-and-Fix activity fan-out
  - #8178 vocab keep/drop labeling
  - #8179 pre-QG / pre-CF readiness scoring
  - #8195 uncertain-band + confidence-gated routing (cookbook composition)
  - #8196 function-calling mesh: Jev tool Choice → local VESUM/Sources verify
  - #8208 pre-parsed stress / apostrophe / soft-sign span pick
  - #8209 writer/QG I/O guardrails
  - #8210 Choice parent-label collapse on low top-probability

Policy (operator 2026-09-17): use freely for Choice / Score / Noul labeling.
Label → verify for attested morphology (VESUM / Sources). Never rewrite human
source text. Not a CF / Monitor / merge substitute.

Cookbook policy (illustrative upstream numbers; code owns production thresholds):
  - Noul uncertain band ``[0.30, 0.70]`` (consistency_noul_cookbook)
  - Choice act iff **top probability** ≥ ``0.60`` — not the API confidence field
    (consistency_choice_cookbook)
  - Score escalate when API confidence < ``0.60`` (date_extraction / confidence pattern)
  - function calling: Jev picks a closed tool id; **Python** runs verify

Credentials: ``TYPESAFE_API_KEY`` or ``~/.secrets/typesafe-ai.key``
(also accepts ``~/.secrets/typesafe-ai.key``).
"""

from __future__ import annotations

import argparse
import json
import os
import unicodedata
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal, Protocol

# --- thresholds owned by code (tune here; model only supplies judgments) ---

NOUL_TRUE_THRESHOLD = 0.7  # legacy binary for NoulJudgment.is_true
# #8195 — cookbook self-consistency: nouls
NOUL_FALSE_AT = 0.30
NOUL_TRUE_AT = 0.70
# #8195 — cookbook self-consistency: choices (top probability, not confidence)
CHOICE_MIN_TOP_PROBABILITY = 0.60
# Score / date-extraction style review gate on API confidence
SCORE_MIN_CONFIDENCE = 0.60
EC_MIN_OPTIONS = 3
SCORE_BAND_LOW = 0.75  # below → lower band for 3-point scores
SCORE_BAND_HIGH = 1.75  # at/above → upper band

_UK_VOWELS = frozenset("аеєиіїоуюяАЕЄИІЇОУЮЯ")
_APOSTROPHES = ("'", "ʼ", "’", "`")

NoulDecision = Literal["true", "false", "uncertain"]
ConfidenceDecision = Literal["act", "escalate"]
GuardrailAction = Literal["pass", "review", "block"]
VerifyToolId = Literal["check_russian_shadow", "verify_stress", "none"]

VERIFY_TOOL_CRITERIA: dict[str, str] = {
    "check_russian_shadow": (
        "Run local Russian-shadow / calque morphology check "
        "(is_russian_pattern / check_ru_morph)."
    ),
    "verify_stress": "Run local VESUM-backed stress lookup (verify_stress).",
    "none": "No local verifier needed for this state.",
}

# #8210 — flat distractor taxonomy collapses to unclear when top-prob is weak
DISTRACTOR_FAMILY_PARENTS: dict[str, str] = {
    "stress": "unclear",
    "soft_sign": "unclear",
    "apostrophe": "unclear",
    "letter": "unclear",
    "other": "unclear",
    "unclear": "unclear",
}



def _question_primitives():
    """Return Choice/Noul/Score classes; stub when SDK absent (hermetic CI)."""
    try:
        from typesafe_sdk import Choice, Noul, Score

        return Choice, Noul, Score
    except ImportError:  # pragma: no cover - exercised in CI without extra-index
        class _Q:
            def __init__(self, **kwargs):
                self.kwargs = kwargs

        class Noul(_Q):
            def __init__(self, instructions="", **kwargs):
                super().__init__(instructions=instructions, **kwargs)

        class Choice(_Q):
            def __init__(self, instructions="", criteria=None, **kwargs):
                super().__init__(instructions=instructions, criteria=criteria or {}, **kwargs)

        class Score(_Q):
            def __init__(self, instructions="", criteria=None, **kwargs):
                super().__init__(instructions=instructions, criteria=criteria or [], **kwargs)

        return Choice, Noul, Score


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
    decision: NoulDecision = "uncertain"

    @property
    def routing(self) -> NoulDecision:
        return self.decision


@dataclass(frozen=True)
class ChoiceJudgment:
    choice: str
    confidence: float
    probabilities: Mapping[str, float] = field(default_factory=dict)
    top_probability: float = 0.0
    routing: ConfidenceDecision = "act"


@dataclass(frozen=True)
class ScoreJudgment:
    score: float
    confidence: float
    band: str
    legend: Mapping[int, str] = field(default_factory=dict)
    routing: ConfidenceDecision = "act"


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
    option_count: int
    exact_winner_in_options: bool

    @property
    def needs_repair(self) -> bool:
        """Code-owned routing: hard mechanical defects or weak/uncertain clarity."""
        if not self.exact_winner_in_options or self.option_count < EC_MIN_OPTIONS:
            return True
        if self.unaccented_copy_of_winner.decision == "true":
            return True
        if self.pedagogical_clarity.routing == "escalate":
            return True
        return self.pedagogical_clarity.band == "unclear"

    @property
    def family_trusted(self) -> bool:
        """#8195 — trust leaf family only when top probability clears gate."""
        return self.distractor_family.routing == "act"

    @property
    def effective_distractor_family(self) -> str:
        """#8210 — leaf label or parent (`unclear`) when top-prob is weak."""
        return collapse_choice(
            self.distractor_family.choice,
            self.distractor_family.probabilities,
            parent_map=DISTRACTOR_FAMILY_PARENTS,
            min_top_prob=CHOICE_MIN_TOP_PROBABILITY,
            confidence=self.distractor_family.confidence,
        )


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
        """Suspect flags / uncertain noul / weak buckets → verify."""
        if self.russian_shadow_suspect.decision in ("true", "uncertain"):
            return True
        if self.ocr_junk.decision in ("true", "uncertain"):
            return True
        if self.dialect_bucket.routing == "escalate":
            return True
        return self.priority.routing == "escalate" and self.priority.band == "drop"


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
        """Map model Choice to a code-owned QG budget; escalate → full."""
        if self.qg_budget.routing == "escalate":
            return "full"
        return self.qg_budget.choice

    @property
    def cf_ready(self) -> bool:
        """Only auto-seat CF when Noul clears the true band (not mid/uncertain)."""
        return self.cf_ready_likely.decision == "true"


@dataclass(frozen=True)
class VerifyToolProposal:
    """#8196 — Jev picks a closed tool; Python may run it."""

    tool: VerifyToolId
    confidence: float
    top_probability: float
    routing: ConfidenceDecision
    probabilities: Mapping[str, float]
    receipt: TypeSafeReceipt
    verify_result: Mapping[str, Any] | None = None
    ran: bool = False


@dataclass(frozen=True)
class PreparsedPick:
    """#8208 — verbatim candidate selected by Choice."""

    selected: str | None
    routing: ConfidenceDecision
    top_probability: float
    any_adequate: NoulJudgment
    receipt: TypeSafeReceipt
    candidates: tuple[str, ...]


@dataclass(frozen=True)
class GuardrailEvaluation:
    """#8209 — writer/QG I/O screen."""

    russian_calque_suspect: NoulJudgment
    invented_upgrade_defect: NoulJudgment
    immersion_leak: NoulJudgment
    hazard_severity: ScoreJudgment
    receipt: TypeSafeReceipt

    @property
    def action(self) -> GuardrailAction:
        if self.hazard_severity.band == "block":
            return "block"
        if self.russian_calque_suspect.decision == "true":
            return "block"
        if self.invented_upgrade_defect.decision == "true":
            return "block"
        if self.immersion_leak.decision == "true":
            return "block"
        if any(
            j.decision == "uncertain"
            for j in (
                self.russian_calque_suspect,
                self.invented_upgrade_defect,
                self.immersion_leak,
            )
        ):
            return "review"
        if self.hazard_severity.routing == "escalate" or self.hazard_severity.band == "mild":
            return "review"
        return "pass"


def route_noul(
    probability: float,
    *,
    true_at: float = NOUL_TRUE_AT,
    false_at: float = NOUL_FALSE_AT,
) -> NoulDecision:
    """#8195 — mid band is uncertain (consistency_noul_cookbook).

    Cookbook maps ``[false_at, true_at]`` inclusive to ``uncertain``.
    """
    p = float(probability)
    if p > true_at:
        return "true"
    if p < false_at:
        return "false"
    return "uncertain"


def choice_top_probability(
    probabilities: Mapping[str, float] | None,
    *,
    confidence: float | None = None,
) -> float:
    """Best available peakedness signal for Choice routing.

    Cookbook uses max(probabilities). If the distribution is missing (tests /
    truncated payloads), fall back to API confidence.
    """
    if probabilities:
        return float(max(float(v) for v in probabilities.values()))
    if confidence is not None:
        return float(confidence)
    return 0.0


def route_choice_top_prob(
    top_probability: float,
    *,
    min_top_prob: float = CHOICE_MIN_TOP_PROBABILITY,
) -> ConfidenceDecision:
    """#8195 — act iff top probability clears gate (consistency_choice_cookbook)."""
    return "act" if float(top_probability) >= min_top_prob else "escalate"


def route_score(
    confidence: float,
    *,
    min_confidence: float = SCORE_MIN_CONFIDENCE,
) -> ConfidenceDecision:
    return "act" if float(confidence) >= min_confidence else "escalate"


def collapse_choice(
    choice: str,
    probabilities: Mapping[str, float] | None,
    *,
    parent_map: Mapping[str, str],
    min_top_prob: float = CHOICE_MIN_TOP_PROBABILITY,
    confidence: float | None = None,
) -> str:
    """#8210 — low top-prob → broader parent label (classification_using_confidence)."""
    top = choice_top_probability(probabilities, confidence=confidence)
    if top >= min_top_prob:
        return choice
    return parent_map.get(choice, choice)


def load_typesafe_api_key() -> str:
    """Load API key from env or host secrets dir. Never logs the value."""
    env = os.environ.get("TYPESAFE_API_KEY", "").strip()
    if env:
        return env
    home = Path.home() / ".secrets"
    for name in ("typesafe-ai.key", "typsafe-ai.key"):
        path = home / name
        if path.is_file():
            return path.read_text(encoding="utf-8").strip().replace("\r", "")
    raise FileNotFoundError(
        "TYPESAFE_API_KEY unset and neither ~/.secrets/typesafe-ai.key "
        "nor legacy ~/.secrets/typsafe-ai.key found"
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
    return NoulJudgment(
        probability=prob,
        is_true=prob >= threshold,
        decision=route_noul(prob),
    )


def _choice(response: Any, key: str) -> ChoiceJudgment:
    ans = response.choices[key]
    probs = {str(k): float(v) for k, v in dict(getattr(ans, "probabilities", {}) or {}).items()}
    confidence = float(getattr(ans, "confidence", 0.0) or 0.0)
    top = choice_top_probability(probs, confidence=confidence)
    return ChoiceJudgment(
        choice=str(ans.choice),
        confidence=confidence,
        probabilities=probs,
        top_probability=top,
        routing=route_choice_top_prob(top),
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
    confidence = float(getattr(ans, "confidence", 0.0) or 0.0)
    return ScoreJudgment(
        score=raw,
        confidence=confidence,
        band=band,
        legend=legend,
        routing=route_score(confidence),
    )


def _strip_combining(text: str) -> str:
    """Remove combining acute/grave for unaccented-duplicate heuristics."""
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


def stress_candidates(token: str, *, max_candidates: int = 12) -> list[str]:
    """#8208 — place combining acute after each vowel (verbatim variants)."""
    base = _strip_combining(token.strip())
    if not base:
        return []
    out: list[str] = [base]
    for i, ch in enumerate(base):
        if ch not in _UK_VOWELS:
            continue
        marked = base[: i + 1] + "\u0301" + base[i + 1 :]
        if marked not in out:
            out.append(marked)
        if len(out) >= max_candidates:
            break
    return out


def apostrophe_candidates(token: str) -> list[str]:
    """#8208 — swap among common apostrophe codepoints; keep verbatim otherwise."""
    t = token.strip()
    if not t:
        return []
    found = [a for a in _APOSTROPHES if a in t]
    if not found:
        return [t]
    out: list[str] = []
    for src in found:
        for dst in _APOSTROPHES:
            cand = t.replace(src, dst)
            if cand not in out:
                out.append(cand)
    if t not in out:
        out.insert(0, t)
    return out


def soft_sign_candidates(token: str) -> list[str]:
    """#8208 — with / without soft sign ь (simple presence toggle)."""
    t = token.strip()
    if not t:
        return []
    out = [t]
    if "ь" in t or "Ь" in t:
        stripped = t.replace("ь", "").replace("Ь", "")
        if stripped and stripped not in out:
            out.append(stripped)
    else:
        # insert ь before final letter if stem looks plausible
        if len(t) >= 2:
            inserted = t[:-1] + "ь" + t[-1]
            if inserted not in out:
                out.append(inserted)
        with_final = t + "ь"
        if with_final not in out:
            out.append(with_final)
    return out


def _default_russian_shadow(word: str) -> Mapping[str, Any]:
    from scripts.verification.check_ru_morph import is_russian_pattern

    return is_russian_pattern(word)


def _default_verify_stress(word: str) -> Mapping[str, Any]:
    from scripts.verification.stress import verify_stress

    return verify_stress(word)


def run_verify_tool(
    tool: VerifyToolId,
    word: str,
    *,
    russian_shadow_fn: Callable[[str], Mapping[str, Any]] | None = None,
    verify_stress_fn: Callable[[str], Mapping[str, Any]] | None = None,
) -> Mapping[str, Any] | None:
    """#8196 — execute a closed local verifier (never invent morphology in-model)."""
    if tool == "none":
        return None
    if tool == "check_russian_shadow":
        fn = russian_shadow_fn or _default_russian_shadow
        return dict(fn(word))
    if tool == "verify_stress":
        fn = verify_stress_fn or _default_verify_stress
        return dict(fn(word))
    raise ValueError(f"unknown verify tool: {tool}")


def propose_and_run_verify(
    *,
    word: str,
    context: str = "",
    level: str = "",
    client: _SystemOneClient | None = None,
    model: str | None = None,
    run: bool = True,
    russian_shadow_fn: Callable[[str], Mapping[str, Any]] | None = None,
    verify_stress_fn: Callable[[str], Mapping[str, Any]] | None = None,
) -> VerifyToolProposal:
    """#8196 — Choice over closed tools, then optional local execution."""
    Choice, _Noul, _Score = _question_primitives()

    state = {
        "word": word,
        "context": context,
        "level": (level or "").strip().lower(),
        "tools": list(VERIFY_TOOL_CRITERIA),
        "note": (
            "Pick at most one local verifier. Morphology facts come from the tool, "
            "never from this Choice alone."
        ),
    }
    questions = {
        "verify_tool": Choice(
            instructions=(
                "Which local verification tool should code run for this Ukrainian word "
                "in curriculum triage?"
            ),
            criteria=dict(VERIFY_TOOL_CRITERIA),
        ),
    }

    own_client = client is None
    c = client if client is not None else make_client()
    try:
        response = c.system_one(state=state, questions=questions, model=model)
    finally:
        if own_client and hasattr(c, "close"):
            c.close()

    judgment = _choice(response, "verify_tool")
    tool_raw = judgment.choice
    tool: VerifyToolId = (
        tool_raw if tool_raw in VERIFY_TOOL_CRITERIA else "none"  # type: ignore[assignment]
    )
    verify_result: Mapping[str, Any] | None = None
    ran = False
    if run and judgment.routing == "act" and tool != "none":
        verify_result = run_verify_tool(
            tool,
            word,
            russian_shadow_fn=russian_shadow_fn,
            verify_stress_fn=verify_stress_fn,
        )
        ran = True

    return VerifyToolProposal(
        tool=tool,
        confidence=judgment.confidence,
        top_probability=judgment.top_probability,
        routing=judgment.routing,
        probabilities=judgment.probabilities,
        receipt=_receipt_from_response(response),
        verify_result=verify_result,
        ran=ran,
    )


def pick_preparsed_value(
    *,
    question: str,
    candidates: Sequence[str],
    client: _SystemOneClient | None = None,
    model: str | None = None,
) -> PreparsedPick:
    """#8208 — Choice picks a verbatim regex/heuristic candidate."""
    Choice, Noul, _Score = _question_primitives()

    cands = [str(c) for c in candidates if str(c).strip()]
    # Cap criteria size; TypeSafe Choice needs a closed set
    cands = cands[:24]
    if not cands:
        empty = NoulJudgment(probability=0.0, is_true=False, decision="false")
        return PreparsedPick(
            selected=None,
            routing="escalate",
            top_probability=0.0,
            any_adequate=empty,
            receipt=TypeSafeReceipt(None, None, None),
            candidates=(),
        )

    criteria = {c: f"verbatim candidate: {c}" for c in cands}
    state = {
        "question": question,
        "candidates": cands,
        "note": "Select the exact string to copy. Do not invent a new spelling.",
    }
    questions = {
        "pick": Choice(
            instructions=(
                "Which candidate is the correct verbatim value for the question? "
                "Copy the option text exactly."
            ),
            criteria=criteria,
        ),
        "any_adequate": Noul(
            instructions="Is at least one candidate an adequate correct form?"
        ),
    }

    own_client = client is None
    c = client if client is not None else make_client()
    try:
        response = c.system_one(state=state, questions=questions, model=model)
    finally:
        if own_client and hasattr(c, "close"):
            c.close()

    pick = _choice(response, "pick")
    adequate = _noul(response, "any_adequate")
    selected = pick.choice if pick.routing == "act" and pick.choice in cands else None
    return PreparsedPick(
        selected=selected,
        routing=pick.routing,
        top_probability=pick.top_probability,
        any_adequate=adequate,
        receipt=_receipt_from_response(response),
        candidates=tuple(cands),
    )


def evaluate_upgrade_io_guardrails(
    *,
    level: str,
    excerpt: str,
    role: str = "writer_output",
    client: _SystemOneClient | None = None,
    model: str | None = None,
) -> GuardrailEvaluation:
    """#8209 — screen writer/QG I/O (complement to #8184 tone gates)."""
    _Choice, Noul, Score = _question_primitives()

    level_l = (level or "").strip().lower()
    state = {
        "level": level_l,
        "role": role,
        "excerpt": excerpt[:8000],
        "policy": (
            "A1 may use English scaffolding by design. From A2, flag immersion leaks. "
            "Never treat calque suspects as VESUM facts."
        ),
    }
    questions = {
        "russian_calque_suspect": Noul(
            instructions=(
                "Does this excerpt show a likely Russianism / calque / Surzhyk leak "
                "that should block auto-publish?"
            )
        ),
        "invented_upgrade_defect": Noul(
            instructions=(
                "Does this look like an invented upgrade defect — rewriting archive "
                "content without a real pedagogical defect?"
            )
        ),
        "immersion_leak": Noul(
            instructions=(
                "If level is a2 or higher, is there unwarranted English scaffolding "
                "in learner-facing prose? If level is a1, answer no."
            )
        ),
        "hazard_severity": Score(
            instructions="Overall hazard severity for auto-shipping this excerpt.",
            criteria=["none", "mild", "block"],
        ),
    }

    own_client = client is None
    c = client if client is not None else make_client()
    try:
        response = c.system_one(state=state, questions=questions, model=model)
    finally:
        if own_client and hasattr(c, "close"):
            c.close()

    return GuardrailEvaluation(
        russian_calque_suspect=_noul(response, "russian_calque_suspect"),
        invented_upgrade_defect=_noul(response, "invented_upgrade_defect"),
        immersion_leak=_noul(response, "immersion_leak"),
        hazard_severity=_score(
            response, "hazard_severity", bands=("none", "mild", "block")
        ),
        receipt=_receipt_from_response(response),
    )


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
    Choice, Noul, Score = _question_primitives()

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
    Choice, Noul, Score = _question_primitives()

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
    Choice, Noul, Score = _question_primitives()

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
            "top_probability": ev.distractor_family.top_probability,
            "routing": ev.distractor_family.routing,
            "probabilities": dict(ev.distractor_family.probabilities),
        },
        "effective_distractor_family": ev.effective_distractor_family,
        "pedagogical_clarity": {
            "score": ev.pedagogical_clarity.score,
            "confidence": ev.pedagogical_clarity.confidence,
            "band": ev.pedagogical_clarity.band,
            "routing": ev.pedagogical_clarity.routing,
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
            "top_probability": ev.dialect_bucket.top_probability,
            "routing": ev.dialect_bucket.routing,
        },
        "domain": {
            "choice": ev.domain.choice,
            "confidence": ev.domain.confidence,
            "routing": ev.domain.routing,
        },
        "priority": {
            "score": ev.priority.score,
            "band": ev.priority.band,
            "confidence": ev.priority.confidence,
            "routing": ev.priority.routing,
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
            "top_probability": ev.qg_budget.top_probability,
            "routing": ev.qg_budget.routing,
        },
        "cf_ready_likely": asdict(ev.cf_ready_likely),
        "cf_ready": ev.cf_ready,
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

    p_ver = sub.add_parser("verify", help="#8196 propose+run local verify tool")
    p_ver.add_argument("--word", required=True)
    p_ver.add_argument("--context", default="")
    p_ver.add_argument("--level", default="")
    p_ver.add_argument("--no-run", action="store_true")

    p_pre = sub.add_parser("preparse", help="#8208 pick verbatim candidate")
    p_pre.add_argument("--question", required=True)
    p_pre.add_argument("--candidates", required=True, help="JSON array of strings")

    p_g = sub.add_parser("guardrails", help="#8209 I/O guardrails")
    p_g.add_argument("--level", required=True)
    p_g.add_argument("--excerpt", required=True)
    p_g.add_argument("--role", default="writer_output")

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
    if args.cmd == "verify":
        prop = propose_and_run_verify(
            word=args.word,
            context=args.context,
            level=args.level,
            run=not args.no_run,
        )
        print(
            json.dumps(
                {
                    "tool": prop.tool,
                    "top_probability": prop.top_probability,
                    "routing": prop.routing,
                    "ran": prop.ran,
                    "verify_result": prop.verify_result,
                    "receipt": prop.receipt.to_dict(),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    if args.cmd == "preparse":
        cands = json.loads(args.candidates)
        pick = pick_preparsed_value(question=args.question, candidates=cands)
        print(
            json.dumps(
                {
                    "selected": pick.selected,
                    "routing": pick.routing,
                    "top_probability": pick.top_probability,
                    "any_adequate": asdict(pick.any_adequate),
                    "candidates": list(pick.candidates),
                    "receipt": pick.receipt.to_dict(),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    if args.cmd == "guardrails":
        ev = evaluate_upgrade_io_guardrails(
            level=args.level, excerpt=args.excerpt, role=args.role
        )
        print(
            json.dumps(
                {
                    "action": ev.action,
                    "russian_calque_suspect": asdict(ev.russian_calque_suspect),
                    "invented_upgrade_defect": asdict(ev.invented_upgrade_defect),
                    "immersion_leak": asdict(ev.immersion_leak),
                    "hazard_severity": {
                        "score": ev.hazard_severity.score,
                        "band": ev.hazard_severity.band,
                        "confidence": ev.hazard_severity.confidence,
                    },
                    "receipt": ev.receipt.to_dict(),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
