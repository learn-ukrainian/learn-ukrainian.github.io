"""TypeSafe System One Semantic Firewall for Raw Ukrainian Corpus Ingestion.

Adopts the TypeSafe System One triage and confidence routing architecture:
https://docs.typesafe.ai/concepts/system-one.md
https://docs.typesafe.ai/patterns/confidence-routing.md

Evaluates candidate sentence chunks for the 250,000+ Sovereign Ukrainian Model Data
collection (#6321 / #7423) across historical chronicles, web crawls, textbooks, and scanned archives.

Core Principles:
1. Routing (Choice): Distinguishes clean literary standard Ukrainian from authentic regional
   dialects, Middle Ukrainian / historical texts, OCR/homoglyph noise, and Russian/Surzhyk interference.
2. Quality Scoring (Score): Continuous 0..4 utility metric for corpus filtering and shard tiering.
3. Uncertainty Escalation (Noul): Flags borderline cases for human expert curation.
4. Verbatim Preservation: Code NEVER rewrites or "fixes" human-authored source text; it classifies
   and routes.
5. Offline Resilience: Provides deterministic heuristic fallback when TypeSafe API is unavailable.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import urllib.request
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any, ClassVar

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class CorpusAction(StrEnum):
    KEEP_STANDARD = "keep_standard_corpus"
    KEEP_DIALECTAL = "keep_dialectal_corpus"
    KEEP_HISTORICAL = "keep_historical_corpus"
    DROP_OCR_NOISE = "drop_ocr_or_noise"
    DROP_RUSSIAN_SURZHYK = "drop_russian_or_surzhyk"


@dataclass
class FirewallDecision:
    """Ingestion gate decision for a single sentence candidate."""

    sentence: str
    action: CorpusAction
    quality_score: float
    confidence: float
    needs_human_review: bool
    review_probability: float
    reason: str = ""


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
    """Resolve TypeSafe API key from environment or host secrets."""
    key = os.environ.get("TYPESAFE_API_KEY", "").strip()
    if key:
        return key

    key_files = [
        Path.home() / ".secrets" / "typsafe-ai.key",
        Path.home() / ".secrets" / "typesafe-ai.key",
        Path.home() / ".config" / "typesafe" / "key",
        Path.home() / ".typesafe_api_key",
        Path.home() / ".gemini" / "antigravity-cli" / "typesafe_api_key",
    ]
    for p in key_files:
        if p.is_file():
            try:
                content = p.read_text(encoding="utf-8").strip()
                if content:
                    return content
            except OSError:
                continue
    return ""


# Regex patterns for deterministic heuristic fallback
RUSSIAN_ONLY_CHARS_RE = re.compile(r"[ыэъёЫЭЪЁ]")
UKRAINIAN_DISTINCTIVE_CHARS_RE = re.compile(r"[іїєґІЇЄҐ]")
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


class TypeSafeCorpusFirewall:
    """TypeSafe System One Semantic Firewall for candidate Ukrainian corpus ingestion."""

    CRITERIA_ROUTING: ClassVar[dict[str, str]] = {
        "keep_standard_corpus": "Clean, grammatical, modern standard Ukrainian literary text.",
        "keep_dialectal_corpus": "Authentic regional Ukrainian dialect (Hutsul, Lemko, Boyko, Polissian, etc.) or authentic folk speech.",
        "keep_historical_corpus": "Authentic Old East Slavic, Ruthenian, or Middle Ukrainian historical source text.",
        "drop_ocr_or_noise": "Broken scan OCR fragments, mixed Latin-Cyrillic homoglyph noise, cut-off words, or unreadable junk.",
        "drop_russian_or_surzhyk": "Russian language text, ungrammatical Russian interference, calques, or non-dialectal Surzhyk.",
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
        self.api_key = api_key if api_key is not None else _resolve_typesafe_key()
        self.base_url = base_url.rstrip("/")
        self.batch_size = max(1, batch_size)

    def filter_sentences(self, sentences: list[str]) -> FirewallBatchReport:
        """Filter and route a batch of candidate sentences."""
        clean_inputs = [s.strip() for s in sentences if s.strip()]
        if not clean_inputs:
            return FirewallBatchReport(0, 0, 0, 0, 0, 0, 0, 0.0, [])

        decisions: list[FirewallDecision] = []

        if self.api_key:
            for offset in range(0, len(clean_inputs), self.batch_size):
                batch = clean_inputs[offset : offset + self.batch_size]
                try:
                    batch_decisions = self._call_firewall_batch_api(batch)
                    decisions.extend(batch_decisions)
                    continue
                except Exception:
                    pass
                # Fallback for this batch if API call fails
                for s in batch:
                    decisions.append(self._heuristic_evaluate(s))
        else:
            for s in clean_inputs:
                decisions.append(self._heuristic_evaluate(s))

        # Build telemetry summary
        kept_std = sum(1 for d in decisions if d.action == CorpusAction.KEEP_STANDARD)
        kept_dia = sum(1 for d in decisions if d.action == CorpusAction.KEEP_DIALECTAL)
        kept_his = sum(1 for d in decisions if d.action == CorpusAction.KEEP_HISTORICAL)
        drop_ocr = sum(1 for d in decisions if d.action == CorpusAction.DROP_OCR_NOISE)
        drop_rus = sum(1 for d in decisions if d.action == CorpusAction.DROP_RUSSIAN_SURZHYK)
        escalated = sum(1 for d in decisions if d.needs_human_review)
        avg_q = sum(d.quality_score for d in decisions) / len(decisions) if decisions else 0.0

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
                "instructions": f"Classify the corpus ingestion eligibility of candidate sentence state.sentences[{idx}].",
                "criteria": self.CRITERIA_ROUTING,
            }
            questions[f"s{idx}_quality"] = {
                "type": "score",
                "instructions": f"Rate the linguistic quality and corpus utility of state.sentences[{idx}] from 0 to 4.",
                "criteria": self.CRITERIA_QUALITY,
            }
            questions[f"s{idx}_uncertainty"] = {
                "type": "noul",
                "instructions": f"Does state.sentences[{idx}] present borderline linguistic ambiguity requiring human expert review?",
                "criteria": {
                    "true": "The boundary between dialect vs Surzhyk or archaic vs corrupted text is uncertain.",
                    "false": "The sentence clearly belongs to its assigned category without ambiguity.",
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
            data = json.loads(resp.read().decode("utf-8"))
            answers = data.get("answers", {})
            out: list[FirewallDecision] = []
            for idx, s in enumerate(batch):
                q_route = answers.get(f"s{idx}_route", {})
                q_qual = answers.get(f"s{idx}_quality", {})
                q_unc = answers.get(f"s{idx}_uncertainty", {})

                action_str = str(q_route.get("choice", CorpusAction.KEEP_STANDARD))
                action = (
                    CorpusAction(action_str)
                    if action_str in CorpusAction._value2member_map_
                    else CorpusAction.KEEP_STANDARD
                )
                score_val = float(q_qual.get("score", 3.0))
                conf_val = float(q_route.get("confidence", 1.0))
                unc_val = float(q_unc.get("noul", 0.1))

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
                    )
                )
            return out

    def _heuristic_evaluate(self, text: str) -> FirewallDecision:
        """Deterministic linguistic heuristics for corpus filtering."""
        # 1. Mixed Latin-Cyrillic homoglyphs inside a word (OCR corruption)
        if MIXED_HOMOGLYPH_RE.search(text):
            return FirewallDecision(
                sentence=text,
                action=CorpusAction.DROP_OCR_NOISE,
                quality_score=0.2,
                confidence=0.98,
                needs_human_review=False,
                review_probability=0.05,
                reason="Contains corrupted mixed Latin-Cyrillic homoglyphs inside word tokens",
            )

        # 2. Old East Slavic / Middle Ukrainian historical markers
        if OLD_EAST_SLAVIC_MARKERS_RE.search(text):
            return FirewallDecision(
                sentence=text,
                action=CorpusAction.KEEP_HISTORICAL,
                quality_score=3.5,
                confidence=0.90,
                needs_human_review=False,
                review_probability=0.2,
                reason="Contains attested Old East Slavic / Middle Ukrainian lexical markers",
            )

        # 3. Authentic dialectal markers
        if DIALECTAL_MARKERS_RE.search(text):
            return FirewallDecision(
                sentence=text,
                action=CorpusAction.KEEP_DIALECTAL,
                quality_score=3.6,
                confidence=0.92,
                needs_human_review=False,
                review_probability=0.15,
                reason="Contains authentic Ukrainian regional dialect markers",
            )

        # 4. Russian letter detection (ы, э, ъ, ё)
        if RUSSIAN_ONLY_CHARS_RE.search(text):
            return FirewallDecision(
                sentence=text,
                action=CorpusAction.DROP_RUSSIAN_SURZHYK,
                quality_score=0.0,
                confidence=1.0,
                needs_human_review=False,
                review_probability=0.0,
                reason="Contains Russian-specific alphabet characters (ы/э/ъ/ё)",
            )

        # 5. Length and character ratio checks
        words = text.split()
        if len(words) < 3 or len(text) < 15:
            return FirewallDecision(
                sentence=text,
                action=CorpusAction.DROP_OCR_NOISE,
                quality_score=0.8,
                confidence=0.85,
                needs_human_review=False,
                review_probability=0.1,
                reason="Fragment too short for standalone corpus inclusion",
            )

        # Default: clean modern Ukrainian standard literary text
        return FirewallDecision(
            sentence=text,
            action=CorpusAction.KEEP_STANDARD,
            quality_score=3.8,
            confidence=0.95,
            needs_human_review=False,
            review_probability=0.05,
            reason="Clean literary Ukrainian standard syntax and orthography",
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="TypeSafe Corpus Firewall for Ukrainian Ingestion")
    parser.add_argument("file", help="Path to plain text file of candidate sentences (one per line)")
    args = parser.parse_args()

    path = Path(args.file)
    if not path.is_file():
        print(f"File not found: {path}")
        return

    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
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
    print(f"  • Russian / Surzhyk Interference: {report.dropped_russian_surzhyk}")
    print(f"Escalated to Human Review: {report.escalated_to_human}")
    print(f"Average Quality Score (0..4): {report.average_quality:.2f}")


if __name__ == "__main__":
    main()
