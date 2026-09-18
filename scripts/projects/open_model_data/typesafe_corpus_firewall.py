"""TypeSafe System One Semantic Firewall for Raw Ukrainian Corpus Ingestion.

Thin adapter over ``typesafe_cyrillic_gate`` — the single decision taxonomy for
curriculum / corpus dispositions. This module adds batch ingestion telemetry,
offline heuristic fallback, and quality scoring; it does **not** invent a
parallel action enum.

Disposition taxonomy (from ``typesafe_cyrillic_gate.CurriculumAction``):
  admit_standard          — clean modern standard literary Ukrainian
  admit_dialect_heritage  — authentic dialect OR historical / heritage text
  use_as_anti_calque      — Surzhyk / calque / soviet-jargon foil material
  reject_drop             — OCR noise, non-Ukrainian, unusable fragments

Firewall → gate mapping (heuristic / API route labels → CurriculumAction):
  keep_standard_corpus     → ADMIT_STANDARD
  keep_dialectal_corpus    → ADMIT_DIALECT_HERITAGE (+ LexicalVariety.AUTHENTIC_DIALECT)
  keep_historical_corpus   → ADMIT_DIALECT_HERITAGE (+ LexicalVariety.HISTORICAL_LITERARY)
  drop_ocr_or_noise        → REJECT_DROP
  drop_russian_or_surzhyk  → USE_AS_ANTI_CALQUE (Surzhyk/calques) or REJECT_DROP (pure RU)

Variety labels come from ``LexicalVariety`` (includes soviet_jargon).

Adopts TypeSafe System One triage:
https://docs.typesafe.ai/concepts/system-one.md
https://docs.typesafe.ai/patterns/confidence-routing.md
"""

from __future__ import annotations

import argparse
import json
import math
import re
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, ClassVar

from scripts.projects.open_model_data.typesafe_cyrillic_gate import (
    CurriculumAction,
    LexicalVariety,
    resolve_api_key,
)

# Back-compat alias: callers that imported CorpusAction still resolve to the gate enum.
CorpusAction = CurriculumAction

# API choice labels used only as TypeSafe route keys; always mapped onto CurriculumAction.
_ROUTE_TO_ACTION: dict[str, CurriculumAction] = {
    "keep_standard_corpus": CurriculumAction.ADMIT_STANDARD,
    "keep_dialectal_corpus": CurriculumAction.ADMIT_DIALECT_HERITAGE,
    "keep_historical_corpus": CurriculumAction.ADMIT_DIALECT_HERITAGE,
    "drop_ocr_or_noise": CurriculumAction.REJECT_DROP,
    "drop_russian_or_surzhyk": CurriculumAction.USE_AS_ANTI_CALQUE,
    # Direct gate labels also accepted from the API
    CurriculumAction.ADMIT_STANDARD.value: CurriculumAction.ADMIT_STANDARD,
    CurriculumAction.ADMIT_DIALECT_HERITAGE.value: CurriculumAction.ADMIT_DIALECT_HERITAGE,
    CurriculumAction.USE_AS_ANTI_CALQUE.value: CurriculumAction.USE_AS_ANTI_CALQUE,
    CurriculumAction.REJECT_DROP.value: CurriculumAction.REJECT_DROP,
}

_ROUTE_TO_VARIETY: dict[str, LexicalVariety] = {
    "keep_standard_corpus": LexicalVariety.STANDARD_MODERN,
    "keep_dialectal_corpus": LexicalVariety.AUTHENTIC_DIALECT,
    "keep_historical_corpus": LexicalVariety.HISTORICAL_LITERARY,
    "drop_ocr_or_noise": LexicalVariety.NON_UKRAINIAN,
    "drop_russian_or_surzhyk": LexicalVariety.COLONIAL_SURZHYK,
}


@dataclass
class FirewallDecision:
    """Ingestion gate decision for a single sentence candidate."""

    sentence: str
    action: CurriculumAction
    quality_score: float
    confidence: float
    needs_human_review: bool
    review_probability: float
    reason: str = ""
    lexical_variety: LexicalVariety = LexicalVariety.STANDARD_MODERN


@dataclass
class FirewallBatchReport:
    """Telemetry and audit summary for a batch of candidate sentences."""

    total_processed: int
    kept_standard: int
    kept_dialectal: int
    kept_historical: int
    dropped_ocr_noise: int
    dropped_russian_surzhyk: int
    escalated_to_human: int
    average_quality: float
    decisions: list[FirewallDecision] = field(default_factory=list)

    @property
    def total_admitted(self) -> int:
        return self.kept_standard + self.kept_dialectal + self.kept_historical

    @property
    def admission_rate(self) -> float:
        if self.total_processed == 0:
            return 0.0
        return self.total_admitted / self.total_processed


def _resolve_typesafe_key() -> str:
    """Resolve TypeSafe API key (delegates to the shared gate resolver)."""
    return resolve_api_key() or ""


# Regex patterns for deterministic heuristic fallback
STRICT_RUSSIAN_CHARS_RE = re.compile(r"[эёЭЁ]")
ARCHAIC_CYRILLIC_RE = re.compile(r"[ѣѧѩѫѭѢѦѪ]")
HISTORICAL_SHARED_CHARS_RE = re.compile(r"[ыъЫЪ]")
MIXED_HOMOGLYPH_RE = re.compile(
    r"\b(?=[a-zA-Zа-яА-ЯіїєґІЇЄҐ]*[a-zA-Z])(?=[a-zA-Zа-яА-ЯіїєґІЇЄҐ]*[а-яА-ЯіїєґІЇЄҐ])[a-zA-Zа-яА-ЯіїєґІЇЄҐ]+\b"
)
OLD_EAST_SLAVIC_MARKERS_RE = re.compile(
    r"\b(половци|князь|бяше|рече|яко|се|вои|иже|свѧт|вѣд|лѣт|кнѧз|граде|володимер|русьск)\b",
    re.IGNORECASE,
)
DIALECTAL_MARKERS_RE = re.compile(
    r"\b(файний|файно|ґазда|ґаздиня|ватра|плай|полонина|батяр|кобіта|легінь|стріха|крисаня|гойний|бусько)\b",
    re.IGNORECASE,
)
SOVIET_JARGON_MARKERS_RE = re.compile(
    r"\b(колгоспниця|передовик|партком|п'ятирічка|п’ятирічка|соцзмагання|ударник)\b",
    re.IGNORECASE,
)


def _parse_curriculum_action(choice: Any) -> CurriculumAction | None:
    """Map an API choice label onto CurriculumAction; None if unknown."""
    if not isinstance(choice, str):
        return None
    mapped = _ROUTE_TO_ACTION.get(choice)
    if mapped is not None:
        return mapped
    try:
        return CurriculumAction(choice)
    except ValueError:
        return None


class TypeSafeCorpusFirewall:
    """Corpus-ingestion adapter over the shared Cyrillic gate taxonomy."""

    CRITERIA_ROUTING: ClassVar[dict[str, str]] = {
        "keep_standard_corpus": "Clean, grammatical, modern standard Ukrainian literary text.",
        "keep_dialectal_corpus": (
            "Authentic regional Ukrainian dialect (Hutsul, Lemko, Boyko, Polissian, etc.) "
            "or authentic folk speech."
        ),
        "keep_historical_corpus": (
            "Authentic Old East Slavic, Ruthenian, or Middle Ukrainian historical source text."
        ),
        "drop_ocr_or_noise": (
            "Broken scan OCR fragments, mixed Latin-Cyrillic homoglyph noise, cut-off words, "
            "or unreadable junk."
        ),
        "drop_russian_or_surzhyk": (
            "Russian language text, ungrammatical Russian interference, calques, "
            "non-dialectal Surzhyk, or soviet jargon suitable as anti-calque foil."
        ),
    }

    CRITERIA_QUALITY: ClassVar[list[str]] = [
        "Level 0: Unusable corrupted noise, scan debris, or pure foreign non-Ukrainian text.",
        "Level 1: Severely damaged or distorted text with heavy OCR or interference errors.",
        "Level 2: Acceptable informational text with minor typographic or colloquial blemishes.",
        "Level 3: High quality standard literary prose or verified authentic historical/dialectal text.",
        "Level 4: Exemplary gold-standard textbook, academic, or published literary Ukrainian.",
    ]

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "https://api.typesafe.ai",
        batch_size: int = 20,
    ) -> None:
        # Explicit empty string forces offline heuristics (do not resolve host secrets).
        if api_key is None:
            self.api_key = _resolve_typesafe_key()
        else:
            self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.batch_size = max(1, batch_size)

    def filter_sentences(self, sentences: list[str]) -> FirewallBatchReport:
        """Filter and route a batch of candidate sentences."""
        if not sentences:
            return FirewallBatchReport(0, 0, 0, 0, 0, 0, 0, 0.0, [])

        decisions: list[FirewallDecision] = []

        if self.api_key:
            for offset in range(0, len(sentences), self.batch_size):
                batch = sentences[offset : offset + self.batch_size]
                try:
                    batch_decisions = self._call_firewall_batch_api(batch)
                    decisions.extend(batch_decisions)
                    continue
                except Exception:
                    # API transport failure: escalate each item for human review rather
                    # than silently admitting via heuristics as high-confidence standard.
                    for s in batch:
                        decisions.append(
                            FirewallDecision(
                                sentence=s,
                                action=CurriculumAction.REJECT_DROP,
                                quality_score=0.0,
                                confidence=0.0,
                                needs_human_review=True,
                                review_probability=1.0,
                                reason="TypeSafe API call failed; escalated for human review",
                                lexical_variety=LexicalVariety.NON_UKRAINIAN,
                            )
                        )
        else:
            for s in sentences:
                decisions.append(self._heuristic_evaluate(s))

        return self._build_report(decisions)

    @staticmethod
    def _is_russian_or_surzhyk_drop(d: FirewallDecision) -> bool:
        """Telemetry: reject/anti-calque items that are RU/Surzhyk/soviet interference."""
        if d.action == CurriculumAction.USE_AS_ANTI_CALQUE:
            return True
        if d.action != CurriculumAction.REJECT_DROP:
            return False
        if d.lexical_variety in (
            LexicalVariety.COLONIAL_SURZHYK,
            LexicalVariety.SOVIET_JARGON,
        ):
            return True
        reason = d.reason
        return (
            "Russian" in reason
            or "Surzhyk" in reason
            or "alphabet" in reason
            or "soviet" in reason.lower()
        )

    @classmethod
    def _build_report(cls, decisions: list[FirewallDecision]) -> FirewallBatchReport:
        kept_std = sum(1 for d in decisions if d.action == CurriculumAction.ADMIT_STANDARD)
        kept_his = sum(
            1
            for d in decisions
            if d.action == CurriculumAction.ADMIT_DIALECT_HERITAGE
            and d.lexical_variety == LexicalVariety.HISTORICAL_LITERARY
        )
        kept_dia = sum(
            1
            for d in decisions
            if d.action == CurriculumAction.ADMIT_DIALECT_HERITAGE
            and d.lexical_variety != LexicalVariety.HISTORICAL_LITERARY
        )
        drop_rus = sum(1 for d in decisions if cls._is_russian_or_surzhyk_drop(d))
        drop_ocr = sum(
            1
            for d in decisions
            if d.action == CurriculumAction.REJECT_DROP
            and not cls._is_russian_or_surzhyk_drop(d)
        )
        escalated = sum(1 for d in decisions if d.needs_human_review)
        avg_q = (
            sum(d.quality_score for d in decisions) / len(decisions) if decisions else 0.0
        )

        return FirewallBatchReport(
            total_processed=len(decisions),
            kept_standard=kept_std,
            kept_dialectal=kept_dia,
            kept_historical=kept_his,
            dropped_ocr_noise=drop_ocr,
            dropped_russian_surzhyk=drop_rus,
            escalated_to_human=escalated,
            average_quality=avg_q,
            decisions=decisions,
        )

    def _call_firewall_batch_api(self, batch: list[str]) -> list[FirewallDecision]:
        """Batch call remote TypeSafe System One API for multiple sentences."""
        questions: dict[str, Any] = {}
        for idx in range(len(batch)):
            questions[f"s{idx}_route"] = {
                "type": "choice",
                "instructions": (
                    f"Classify the corpus ingestion eligibility of candidate sentence "
                    f"state.sentences[{idx}]."
                ),
                "criteria": self.CRITERIA_ROUTING,
            }
            questions[f"s{idx}_quality"] = {
                "type": "score",
                "instructions": (
                    f"Rate the linguistic quality and corpus utility of "
                    f"state.sentences[{idx}] from 0 to 4."
                ),
                "criteria": self.CRITERIA_QUALITY,
            }
            questions[f"s{idx}_uncertainty"] = {
                "type": "noul",
                "instructions": (
                    f"Does state.sentences[{idx}] present borderline linguistic ambiguity "
                    f"requiring human expert review?"
                ),
                "criteria": {
                    "true": (
                        "The boundary between dialect vs Surzhyk or archaic vs corrupted "
                        "text is uncertain."
                    ),
                    "false": (
                        "The sentence clearly belongs to its assigned category without ambiguity."
                    ),
                },
            }

        url = f"{self.base_url}/v1/systemone"
        payload = {
            "model": "jev-latest",
            "state": {"sentences": batch},
            "questions": questions,
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
                "User-Agent": "learn-ukrainian-firewall/1.0",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read().decode("utf-8")
            try:
                data = json.loads(raw)
            except json.JSONDecodeError as err:
                raise ValueError(f"Non-JSON TypeSafe API response: {err}") from err
            if not isinstance(data, dict):
                raise ValueError("TypeSafe API response root must be an object")
            answers = data.get("answers")
            if not isinstance(answers, dict):
                raise ValueError("TypeSafe API response missing object 'answers'")
            out: list[FirewallDecision] = []
            for idx, s in enumerate(batch):
                q_route = answers.get(f"s{idx}_route")
                q_qual = answers.get(f"s{idx}_quality")
                q_unc = answers.get(f"s{idx}_uncertainty")

                if (
                    not isinstance(q_route, dict)
                    or not isinstance(q_qual, dict)
                    or not isinstance(q_unc, dict)
                ):
                    out.append(
                        FirewallDecision(
                            sentence=s,
                            action=CurriculumAction.REJECT_DROP,
                            quality_score=0.0,
                            confidence=0.0,
                            needs_human_review=True,
                            review_probability=1.0,
                            reason="Malformed or missing response from TypeSafe API",
                            lexical_variety=LexicalVariety.NON_UKRAINIAN,
                        )
                    )
                    continue

                choice = q_route.get("choice")
                action = _parse_curriculum_action(choice)
                if action is None:
                    out.append(
                        FirewallDecision(
                            sentence=s,
                            action=CurriculumAction.REJECT_DROP,
                            quality_score=0.0,
                            confidence=0.0,
                            needs_human_review=True,
                            review_probability=1.0,
                            reason=f"Unknown choice label from TypeSafe API: {choice!r}",
                            lexical_variety=LexicalVariety.NON_UKRAINIAN,
                        )
                    )
                    continue

                variety = _ROUTE_TO_VARIETY.get(
                    choice if isinstance(choice, str) else "",
                    LexicalVariety.STANDARD_MODERN,
                )
                if action == CurriculumAction.ADMIT_STANDARD:
                    variety = LexicalVariety.STANDARD_MODERN
                elif action == CurriculumAction.ADMIT_DIALECT_HERITAGE:
                    if variety not in (
                        LexicalVariety.AUTHENTIC_DIALECT,
                        LexicalVariety.HISTORICAL_LITERARY,
                    ):
                        variety = LexicalVariety.AUTHENTIC_DIALECT
                elif action == CurriculumAction.USE_AS_ANTI_CALQUE:
                    variety = LexicalVariety.COLONIAL_SURZHYK
                elif action == CurriculumAction.REJECT_DROP:
                    variety = LexicalVariety.NON_UKRAINIAN

                try:
                    score_val = float(q_qual.get("score"))
                    conf_val = float(q_route.get("confidence"))
                    unc_val = float(q_unc.get("noul"))
                    if not (
                        math.isfinite(score_val)
                        and 0.0 <= score_val <= 4.0
                        and math.isfinite(conf_val)
                        and 0.0 <= conf_val <= 1.0
                        and math.isfinite(unc_val)
                        and 0.0 <= unc_val <= 1.0
                    ):
                        raise ValueError("Score or confidence out of bounds")
                except (TypeError, ValueError):
                    out.append(
                        FirewallDecision(
                            sentence=s,
                            action=CurriculumAction.REJECT_DROP,
                            quality_score=0.0,
                            confidence=0.0,
                            needs_human_review=True,
                            review_probability=1.0,
                            reason="Out of bounds or non-numeric score from TypeSafe API",
                            lexical_variety=LexicalVariety.NON_UKRAINIAN,
                        )
                    )
                    continue

                needs_review = unc_val >= 0.60 or conf_val < 0.70
                out.append(
                    FirewallDecision(
                        sentence=s,
                        action=action,
                        quality_score=round(score_val, 2),
                        confidence=round(conf_val, 2),
                        needs_human_review=needs_review,
                        review_probability=round(unc_val, 2),
                        reason=f"TypeSafe System One ({action.value})",
                        lexical_variety=variety,
                    )
                )
            return out

    def _heuristic_evaluate(self, text: str) -> FirewallDecision:
        """Deterministic linguistic heuristics for corpus filtering."""
        # 1. Strict Russian letter detection (э, ё)
        if STRICT_RUSSIAN_CHARS_RE.search(text):
            return FirewallDecision(
                sentence=text,
                action=CurriculumAction.REJECT_DROP,
                quality_score=0.0,
                confidence=1.0,
                needs_human_review=False,
                review_probability=0.0,
                reason="Contains Russian-specific alphabet characters (э/ё)",
                lexical_variety=LexicalVariety.NON_UKRAINIAN,
            )

        # 2. Mixed Latin-Cyrillic homoglyphs inside a word (OCR corruption)
        if MIXED_HOMOGLYPH_RE.search(text):
            return FirewallDecision(
                sentence=text,
                action=CurriculumAction.REJECT_DROP,
                quality_score=0.2,
                confidence=0.98,
                needs_human_review=False,
                review_probability=0.05,
                reason="Contains corrupted mixed Latin-Cyrillic homoglyphs inside word tokens",
                lexical_variety=LexicalVariety.NON_UKRAINIAN,
            )

        # 3. Cyrillic letter presence — count all Unicode letters in the denominator
        cyrillic_letters = len(re.findall(r"[а-яА-ЯіїєґІЇЄҐѣѧѩѫѭѢѦѪ]", text))
        total_letters = sum(1 for c in text if c.isalpha())

        if total_letters < 3 or cyrillic_letters / max(1, total_letters) < 0.60:
            return FirewallDecision(
                sentence=text,
                action=CurriculumAction.REJECT_DROP,
                quality_score=0.0,
                confidence=0.95,
                needs_human_review=False,
                review_probability=0.05,
                reason="Non-Ukrainian or non-language text (lacks required Cyrillic content)",
                lexical_variety=LexicalVariety.NON_UKRAINIAN,
            )

        # 4. Soviet jargon → anti-calque foil (gate LexicalVariety.SOVIET_JARGON)
        if SOVIET_JARGON_MARKERS_RE.search(text):
            return FirewallDecision(
                sentence=text,
                action=CurriculumAction.USE_AS_ANTI_CALQUE,
                quality_score=1.5,
                confidence=0.90,
                needs_human_review=False,
                review_probability=0.2,
                reason="Contains soviet jargon markers; route as anti-calque foil",
                lexical_variety=LexicalVariety.SOVIET_JARGON,
            )

        # 5. Historical / dialect markers
        historical_matches = {m.lower() for m in OLD_EAST_SLAVIC_MARKERS_RE.findall(text)}
        dialect_matches = {m.lower() for m in DIALECTAL_MARKERS_RE.findall(text)}
        has_archaic_letters = bool(ARCHAIC_CYRILLIC_RE.search(text))
        has_shared_historical_chars = bool(HISTORICAL_SHARED_CHARS_RE.search(text))

        if has_shared_historical_chars:
            if dialect_matches:
                return FirewallDecision(
                    sentence=text,
                    action=CurriculumAction.USE_AS_ANTI_CALQUE,
                    quality_score=0.0,
                    confidence=0.95,
                    needs_human_review=False,
                    review_probability=0.05,
                    reason="Conflicting dialect markers with Russian alphabet characters",
                    lexical_variety=LexicalVariety.COLONIAL_SURZHYK,
                )
            if has_archaic_letters or len(historical_matches) >= 2:
                return FirewallDecision(
                    sentence=text,
                    action=CurriculumAction.ADMIT_DIALECT_HERITAGE,
                    quality_score=3.5,
                    confidence=0.92,
                    needs_human_review=False,
                    review_probability=0.15,
                    reason=(
                        "Contains attested Old East Slavic / Middle Ukrainian lexical "
                        "and orthographic markers"
                    ),
                    lexical_variety=LexicalVariety.HISTORICAL_LITERARY,
                )
            return FirewallDecision(
                sentence=text,
                action=CurriculumAction.REJECT_DROP,
                quality_score=0.0,
                confidence=1.0,
                needs_human_review=False,
                review_probability=0.0,
                reason=(
                    "Contains Russian-specific alphabet characters (ы/ъ) without "
                    "sufficient historical provenance"
                ),
                lexical_variety=LexicalVariety.NON_UKRAINIAN,
            )

        if dialect_matches:
            return FirewallDecision(
                sentence=text,
                action=CurriculumAction.ADMIT_DIALECT_HERITAGE,
                quality_score=3.6,
                confidence=0.92,
                needs_human_review=False,
                review_probability=0.15,
                reason="Contains authentic Ukrainian regional dialect markers",
                lexical_variety=LexicalVariety.AUTHENTIC_DIALECT,
            )

        if has_archaic_letters or historical_matches:
            return FirewallDecision(
                sentence=text,
                action=CurriculumAction.ADMIT_DIALECT_HERITAGE,
                quality_score=3.5,
                confidence=0.90,
                needs_human_review=False,
                review_probability=0.2,
                reason="Contains attested Old East Slavic / Middle Ukrainian lexical markers",
                lexical_variety=LexicalVariety.HISTORICAL_LITERARY,
            )

        words = text.split()
        if len(words) < 3 or len(text.strip()) < 15:
            return FirewallDecision(
                sentence=text,
                action=CurriculumAction.REJECT_DROP,
                quality_score=0.8,
                confidence=0.85,
                needs_human_review=False,
                review_probability=0.1,
                reason="Fragment too short for standalone corpus inclusion",
                lexical_variety=LexicalVariety.NON_UKRAINIAN,
            )

        return FirewallDecision(
            sentence=text,
            action=CurriculumAction.ADMIT_STANDARD,
            quality_score=3.8,
            confidence=0.95,
            needs_human_review=False,
            review_probability=0.05,
            reason="Clean literary Ukrainian standard syntax and orthography",
            lexical_variety=LexicalVariety.STANDARD_MODERN,
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="TypeSafe Corpus Firewall for Ukrainian Ingestion")
    parser.add_argument("file", help="Path to plain text file of candidate sentences (one per line)")
    args = parser.parse_args()

    path = Path(args.file)
    if not path.is_file():
        print(f"File not found: {path}")
        return

    lines = [
        line.rstrip("\r\n")
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    firewall = TypeSafeCorpusFirewall()
    report = firewall.filter_sentences(lines)

    print("--- TypeSafe Corpus Firewall Report ---")
    print(f"Total Sentences Processed: {report.total_processed}")
    print(f"Admitted Sentences: {report.total_admitted} ({report.admission_rate:.2%})")
    print(f"  • Standard Literary Corpus: {report.kept_standard}")
    print(f"  • Dialectal Corpus: {report.kept_dialectal}")
    print(f"  • Historical / Middle Ukrainian: {report.kept_historical}")
    print(f"Dropped Sentences: {report.dropped_ocr_noise + report.dropped_russian_surzhyk}")
    print(f"  • OCR / Homoglyph Noise: {report.dropped_ocr_noise}")
    print(f"  • Russian / Surzhyk / Anti-calque: {report.dropped_russian_surzhyk}")
    print(f"Escalated to Human Review: {report.escalated_to_human}")
    print(f"Average Quality Score (0..4): {report.average_quality:.2f}")


if __name__ == "__main__":
    main()
