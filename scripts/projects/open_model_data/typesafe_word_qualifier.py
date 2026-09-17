"""TypeSafe System One Multi-Axis Lexicon Qualification & Labeling Engine.

Implements high-throughput, multi-axis qualification for candidate vocabulary in the
250,000+ Sovereign Ukrainian Model Dataset collection (#6321 / #8181).

Architecture:
1. Multi-Axis Batched Qualification (Choice, Score, Noul):
   - Stratum (Choice): standard literary, dialectal, archaism, slang, terminological, calque, pejorative
   - Russian Shadow (Noul): calibrated probability of Russian calque / Sovietism
   - Pedagogical Priority (Score 0..4): from stopwords (0) to cultural heritage gems (4)
   - OCR Junk (Noul): corrupted characters or Latin-Cyrillic homoglyph noise
2. Confidence Routing & Verification:
   - Decisions with confidence >= 0.85 and russian_shadow < 0.50 are auto-accepted.
   - Borderline decisions (< 0.85 or russian_shadow >= 0.50) automatically route to
     VESUM database verification or style guide review.
3. Offline Resilience:
   - Full deterministic heuristic and VESUM-backed fallback when API is unreachable.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import sys
import time
import urllib.request
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any, ClassVar

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class LexicalStratum(StrEnum):
    """Linguistic and stylistic strata for Ukrainian vocabulary."""

    STANDARD_LITERARY = "standard_literary"
    DIALECTAL = "dialectal"
    ARCHAISM = "archaism"
    SLANG_COLLOQUIAL = "slang_colloquial"
    TERMINOLOGICAL = "terminological"
    CALQUE_RUSSIANISM = "calque_russianism"
    PEJORATIVE_SLUR = "pejorative_slur"


@dataclass
class WordQualification:
    """Multi-axis qualification output for a single Ukrainian word."""

    word: str
    stratum: LexicalStratum
    confidence: float
    russian_shadow: float
    pedagogical_priority: float
    ocr_junk: float
    needs_verification: bool
    verification_route: str  # "none", "vesum_lookup", "style_guide_review", "ocr_filter"
    reason: str = ""


@dataclass
class BatchQualificationReport:
    """Summary metrics and decisions for a qualified batch of words."""

    total_processed: int
    standard_literary: int
    dialectal: int
    archaism: int
    slang_colloquial: int
    terminological: int
    calque_russianism: int
    pejorative_slur: int
    ocr_junk_count: int
    needs_verification_count: int
    average_priority: float
    elapsed_seconds: float = 0.0
    qualifications: list[WordQualification] = field(default_factory=list)

    @property
    def words_per_second(self) -> float:
        if self.elapsed_seconds <= 0:
            return 0.0
        return self.total_processed / self.elapsed_seconds


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


# Regex patterns for deterministic fallback
RUSSIAN_ONLY_CHARS_RE = re.compile(r"[ыэъёЫЭЪЁ]")
MIXED_HOMOGLYPH_RE = re.compile(
    r"\b(?=[a-zA-Zа-яА-ЯіїєґІЇЄҐ]*[a-zA-Z])(?=[a-zA-Zа-яА-ЯіїєґІЇЄҐ]*[а-яА-ЯіїєґІЇЄҐ])[a-zA-Zа-яА-ЯіїєґІЇЄҐ]+\b"
)
KNOWN_CALQUES = frozenset({
    "мероприємство",
    "празнувати",
    "слідуючий",
    "приймати участь",
    "влучний випадок",
    "бувший",
    "давнішній",
    "взнос",
    "заказ",
    "наложка",
    "підписка",
    "по крайній мірі",
    "палата представників",
})
KNOWN_DIALECTAL = frozenset({
    "файний",
    "файно",
    "ґазда",
    "ґаздиня",
    "ватра",
    "плай",
    "полонина",
    "батяр",
    "кобіта",
    "легінь",
    "крисаня",
    "бусько",
    "посіпака",
    "вуйко",
    "стрий",
})
KNOWN_ARCHAISMS = frozenset({
    "бяше",
    "рече",
    "яко",
    "се",
    "вои",
    "иже",
    "кнѧз",
    "віче",
    "ратник",
    "острог",
    "гридень",
    "дідич",
})
KNOWN_STOPWORDS = frozenset({
    "і",
    "й",
    "та",
    "але",
    "що",
    "як",
    "це",
    "в",
    "у",
    "на",
    "з",
    "із",
    "зі",
    "до",
    "по",
    "за",
    "про",
    "від",
    "для",
    "не",
    "чи",
    "бо",
    "так",
    "ми",
    "ви",
    "він",
    "вона",
    "вони",
    "я",
    "ти",
})
KNOWN_CULTURAL_GEMS = frozenset({
    "воля",
    "незалежність",
    "соборність",
    "гідність",
    "кобзар",
    "вишиванка",
    "писанка",
    "рушник",
    "калина",
    "козак",
    "січ",
    "майдан",
    "тризуб",
    "державність",
})


class TypeSafeWordQualifier:
    """Multi-axis qualification engine using TypeSafe System One."""

    CRITERIA_STRATUM: ClassVar[dict[str, str]] = {
        "standard_literary": "Normative, standard Ukrainian literary language vocabulary.",
        "dialectal": "Regional Ukrainian dialect word (e.g. Hutsul, Boyko, Lemko, Polissian, Podillian, Steppe).",
        "archaism": "Historic, archaic, or Old Ukrainian vocabulary (historicisms, Old East Slavic/Ruthenian).",
        "slang_colloquial": "Modern youth slang, colloquial speech, jargon, or non-standard street vernacular.",
        "terminological": "Specialized scientific, legal, engineering, medical, or academic terminology.",
        "calque_russianism": "Russian lexical calque, Sovietism, or unadapted Russian borrowing (e.g., мероприємство, празнувати).",
        "pejorative_slur": "Vulgarity, offensive ethnic slur, profanity, or abusive pejorative.",
    }

    CRITERIA_RUSSIAN_SHADOW: ClassVar[dict[str, str]] = {
        "true": "Word is a Russian borrowing, Sovietized bureaucratic calque, or phonologically Russianized form.",
        "false": "Word is an authentic Ukrainian lexical item with authentic Ukrainian phonology and morphology.",
    }

    CRITERIA_PRIORITY: ClassVar[list[str]] = [
        "Level 0: Stopword, grammatical particle, preposition, or non-content functional token.",
        "Level 1: Obscure, highly specialized, archaic, or peripheral vocabulary with low pedagogical utility.",
        "Level 2: Common intermediate general-purpose Ukrainian vocabulary.",
        "Level 3: High-frequency essential core vocabulary every Ukrainian speaker and learner needs.",
        "Level 4: Culturally salient Ukrainian identity term, folklore symbol, pro-sovereignty civic concept, or stylistic gem.",
    ]

    CRITERIA_OCR: ClassVar[dict[str, str]] = {
        "true": "Corrupted scan artifact, broken characters, or mixed Latin-Cyrillic homoglyph noise.",
        "false": "Clean, authentic word form.",
    }

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "https://api.typesafe.ai",
        batch_size: int = 25,
        vesum_path: Path | str | None = None,
    ) -> None:
        self.api_key = api_key if api_key is not None else _resolve_typesafe_key()
        self.base_url = base_url.rstrip("/")
        self.batch_size = max(1, batch_size)

        if vesum_path is None:
            vesum_path = PROJECT_ROOT / "data" / "vesum.db"
        self.vesum_path = Path(vesum_path)
        self._vesum_conn: sqlite3.Connection | None = None

    def _get_vesum_conn(self) -> sqlite3.Connection | None:
        if self._vesum_conn is None and self.vesum_path.is_file():
            try:
                self._vesum_conn = sqlite3.connect(str(self.vesum_path))
            except sqlite3.Error:
                self._vesum_conn = None
        return self._vesum_conn

    def qualify_words(self, words: list[str]) -> BatchQualificationReport:
        """Qualify a collection of candidate words across all dimensions."""
        start_time = time.monotonic()
        clean_words = [w.strip() for w in words if w.strip()]
        if not clean_words:
            return BatchQualificationReport(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.0, 0.0, [])

        qualifications: list[WordQualification] = []

        if self.api_key:
            for offset in range(0, len(clean_words), self.batch_size):
                batch = clean_words[offset : offset + self.batch_size]
                try:
                    batch_qualifications = self._call_batch_api(batch)
                    qualifications.extend(batch_qualifications)
                    continue
                except Exception:
                    pass
                # Fallback for this batch if remote API fails
                for w in batch:
                    qualifications.append(self._heuristic_qualify(w))
        else:
            for w in clean_words:
                qualifications.append(self._heuristic_qualify(w))

        elapsed = time.monotonic() - start_time

        # Compute summary metrics
        c_std = sum(1 for q in qualifications if q.stratum == LexicalStratum.STANDARD_LITERARY)
        c_dia = sum(1 for q in qualifications if q.stratum == LexicalStratum.DIALECTAL)
        c_arc = sum(1 for q in qualifications if q.stratum == LexicalStratum.ARCHAISM)
        c_slg = sum(1 for q in qualifications if q.stratum == LexicalStratum.SLANG_COLLOQUIAL)
        c_trm = sum(1 for q in qualifications if q.stratum == LexicalStratum.TERMINOLOGICAL)
        c_cal = sum(1 for q in qualifications if q.stratum == LexicalStratum.CALQUE_RUSSIANISM)
        c_pej = sum(1 for q in qualifications if q.stratum == LexicalStratum.PEJORATIVE_SLUR)
        c_ocr = sum(1 for q in qualifications if q.ocr_junk >= 0.50)
        c_ver = sum(1 for q in qualifications if q.needs_verification)
        avg_p = sum(q.pedagogical_priority for q in qualifications) / len(qualifications) if qualifications else 0.0

        return BatchQualificationReport(
            total_processed=len(qualifications),
            standard_literary=c_std,
            dialectal=c_dia,
            archaism=c_arc,
            slang_colloquial=c_slg,
            terminological=c_trm,
            calque_russianism=c_cal,
            pejorative_slur=c_pej,
            ocr_junk_count=c_ocr,
            needs_verification_count=c_ver,
            average_priority=avg_p,
            elapsed_seconds=elapsed,
            qualifications=qualifications,
        )

    def _call_batch_api(self, batch: list[str]) -> list[WordQualification]:
        """Batch call remote TypeSafe System One API for multiple words."""
        questions: dict[str, Any] = {}
        for idx in range(len(batch)):
            questions[f"w{idx}_stratum"] = {
                "type": "choice",
                "instructions": f"Classify the lexical stratum of Ukrainian word state.words[{idx}].",
                "criteria": self.CRITERIA_STRATUM,
            }
            questions[f"w{idx}_shadow"] = {
                "type": "noul",
                "instructions": f"Is state.words[{idx}] a Russian lexical borrowing, calque, or Sovietism?",
                "criteria": self.CRITERIA_RUSSIAN_SHADOW,
            }
            questions[f"w{idx}_priority"] = {
                "type": "score",
                "instructions": f"Rate the pedagogical importance of state.words[{idx}] for learning Ukrainian from 0 to 4.",
                "criteria": self.CRITERIA_PRIORITY,
            }
            questions[f"w{idx}_ocr"] = {
                "type": "noul",
                "instructions": f"Is state.words[{idx}] corrupted by OCR artifacts or mixed-script homoglyphs?",
                "criteria": self.CRITERIA_OCR,
            }

        url = f"{self.base_url}/v1/systemone"
        payload = {
            "model": "jev-latest",
            "state": {"words": batch},
            "questions": questions,
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
                "User-Agent": "learn-ukrainian-word-qualifier/1.0",
            },
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=30.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        answers = data.get("answers", {})
        results: list[WordQualification] = []

        for idx, word in enumerate(batch):
            stratum_ans = answers.get(f"w{idx}_stratum", {})
            shadow_ans = answers.get(f"w{idx}_shadow", {})
            prio_ans = answers.get(f"w{idx}_priority", {})
            ocr_ans = answers.get(f"w{idx}_ocr", {})

            choice_str = stratum_ans.get("choice", "standard_literary")
            try:
                stratum = LexicalStratum(choice_str)
            except ValueError:
                stratum = LexicalStratum.STANDARD_LITERARY

            confidence = float(stratum_ans.get("confidence", 0.5))
            shadow_prob = float(shadow_ans.get("noul", 0.0))
            priority = float(prio_ans.get("score", 2.0))
            ocr_prob = float(ocr_ans.get("noul", 0.0))

            # Routing determination
            needs_ver = False
            route = "none"
            reason = "Auto-accepted by TypeSafe System One"

            if ocr_prob >= 0.50:
                needs_ver = True
                route = "ocr_filter"
                reason = f"High probability of OCR/homoglyph corruption ({ocr_prob:.2f})"
            elif shadow_prob >= 0.50 or stratum == LexicalStratum.CALQUE_RUSSIANISM:
                needs_ver = True
                route = "style_guide_review"
                reason = f"Elevated Russian shadow ({shadow_prob:.2f}) or calque classification"
            elif confidence < 0.85:
                needs_ver = True
                route = "vesum_lookup"
                reason = f"Confidence {confidence:.2f} below auto-accept threshold 0.85"

            results.append(
                WordQualification(
                    word=word,
                    stratum=stratum,
                    confidence=confidence,
                    russian_shadow=shadow_prob,
                    pedagogical_priority=priority,
                    ocr_junk=ocr_prob,
                    needs_verification=needs_ver,
                    verification_route=route,
                    reason=reason,
                )
            )

        return results

    def _heuristic_qualify(self, word: str) -> WordQualification:
        """Deterministic heuristic fallback when remote API is unavailable."""
        lower_w = word.lower()

        # 1. OCR junk check
        if MIXED_HOMOGLYPH_RE.search(word):
            return WordQualification(
                word=word,
                stratum=LexicalStratum.STANDARD_LITERARY,
                confidence=0.99,
                russian_shadow=0.0,
                pedagogical_priority=0.0,
                ocr_junk=0.99,
                needs_verification=True,
                verification_route="ocr_filter",
                reason="Mixed Latin-Cyrillic homoglyph noise detected",
            )

        # 2. Russian character check
        if RUSSIAN_ONLY_CHARS_RE.search(word):
            return WordQualification(
                word=word,
                stratum=LexicalStratum.CALQUE_RUSSIANISM,
                confidence=0.99,
                russian_shadow=0.99,
                pedagogical_priority=0.0,
                ocr_junk=0.0,
                needs_verification=True,
                verification_route="style_guide_review",
                reason="Non-Ukrainian Cyrillic characters (ы, э, ъ, ё) detected",
            )

        # 3. Known calques
        if lower_w in KNOWN_CALQUES:
            return WordQualification(
                word=word,
                stratum=LexicalStratum.CALQUE_RUSSIANISM,
                confidence=0.95,
                russian_shadow=0.92,
                pedagogical_priority=0.5,
                ocr_junk=0.0,
                needs_verification=True,
                verification_route="style_guide_review",
                reason="Documented Russian calque / Sovietism",
            )

        # 4. Known dialectal
        if lower_w in KNOWN_DIALECTAL:
            return WordQualification(
                word=word,
                stratum=LexicalStratum.DIALECTAL,
                confidence=0.90,
                russian_shadow=0.05,
                pedagogical_priority=2.5,
                ocr_junk=0.0,
                needs_verification=False,
                verification_route="none",
                reason="Documented authentic regional dialect word",
            )

        # 5. Known archaisms
        if lower_w in KNOWN_ARCHAISMS:
            return WordQualification(
                word=word,
                stratum=LexicalStratum.ARCHAISM,
                confidence=0.92,
                russian_shadow=0.02,
                pedagogical_priority=1.5,
                ocr_junk=0.0,
                needs_verification=False,
                verification_route="none",
                reason="Documented historic / Old East Slavic vocabulary",
            )

        # 6. Stopwords
        if lower_w in KNOWN_STOPWORDS:
            return WordQualification(
                word=word,
                stratum=LexicalStratum.STANDARD_LITERARY,
                confidence=0.99,
                russian_shadow=0.0,
                pedagogical_priority=0.0,
                ocr_junk=0.0,
                needs_verification=False,
                verification_route="none",
                reason="Core grammatical function word / stopword",
            )

        # 7. Cultural gems
        if lower_w in KNOWN_CULTURAL_GEMS:
            return WordQualification(
                word=word,
                stratum=LexicalStratum.STANDARD_LITERARY,
                confidence=0.98,
                russian_shadow=0.01,
                pedagogical_priority=4.0,
                ocr_junk=0.0,
                needs_verification=False,
                verification_route="none",
                reason="Culturally salient identity term / sovereignty gem",
            )

        # 8. Check VESUM database
        ves_conn = self._get_vesum_conn()
        if ves_conn:
            try:
                cur = ves_conn.cursor()
                cur.execute("SELECT pos, tags FROM forms_all WHERE word_form = ? LIMIT 1", (lower_w,))
                row = cur.fetchone()
                if row:
                    tags = row[1] or ""
                    is_bad = "bad" in tags or "v-alt" in tags
                    is_rare = "rare" in tags or "obsc" in tags
                    if is_bad:
                        return WordQualification(
                            word=word,
                            stratum=LexicalStratum.CALQUE_RUSSIANISM,
                            confidence=0.82,
                            russian_shadow=0.60,
                            pedagogical_priority=1.0,
                            ocr_junk=0.0,
                            needs_verification=True,
                            verification_route="style_guide_review",
                            reason="VESUM flagged with bad/v-alt tag",
                        )
                    prio = 1.5 if is_rare else 3.0
                    return WordQualification(
                        word=word,
                        stratum=LexicalStratum.STANDARD_LITERARY,
                        confidence=0.90,
                        russian_shadow=0.05,
                        pedagogical_priority=prio,
                        ocr_junk=0.0,
                        needs_verification=False,
                        verification_route="none",
                        reason="Confirmed standard form in VESUM",
                    )
            except sqlite3.Error:
                pass

        # 9. Fallback unknown
        return WordQualification(
            word=word,
            stratum=LexicalStratum.STANDARD_LITERARY,
            confidence=0.75,
            russian_shadow=0.15,
            pedagogical_priority=2.0,
            ocr_junk=0.0,
            needs_verification=True,
            verification_route="vesum_lookup",
            reason="Unattested candidate routed for dictionary verification",
        )


def main() -> None:
    """CLI entrypoint for batch word qualification."""
    parser = argparse.ArgumentParser(description="Qualify Ukrainian words via TypeSafe System One")
    parser.add_argument("inputs", nargs="*", help="Words to qualify, or file paths if --file is set")
    parser.add_argument("--file", action="store_true", help="Treat input arguments as files")
    parser.add_argument("--batch-size", type=int, default=25, help="Batch size per TypeSafe API call")
    parser.add_argument("--json", action="store_true", help="Output JSON results")
    args = parser.parse_args()

    words_to_process: list[str] = []
    if args.file:
        for fpath in args.inputs:
            p = Path(fpath)
            if p.is_file():
                for line in p.read_text(encoding="utf-8").splitlines():
                    w = line.strip()
                    if w and not w.startswith("#"):
                        words_to_process.append(w)
    elif args.inputs:
        words_to_process.extend(args.inputs)
    else:
        # Read from stdin
        for line in sys.stdin:
            w = line.strip()
            if w and not w.startswith("#"):
                words_to_process.append(w)

    qualifier = TypeSafeWordQualifier(batch_size=args.batch_size)
    report = qualifier.qualify_words(words_to_process)

    if args.json:
        out = {
            "total_processed": report.total_processed,
            "standard_literary": report.standard_literary,
            "dialectal": report.dialectal,
            "archaism": report.archaism,
            "slang_colloquial": report.slang_colloquial,
            "terminological": report.terminological,
            "calque_russianism": report.calque_russianism,
            "pejorative_slur": report.pejorative_slur,
            "ocr_junk_count": report.ocr_junk_count,
            "needs_verification_count": report.needs_verification_count,
            "average_priority": round(report.average_priority, 2),
            "words_per_second": round(report.words_per_second, 1),
            "qualifications": [
                {
                    "word": q.word,
                    "stratum": q.stratum.value,
                    "confidence": round(q.confidence, 2),
                    "russian_shadow": round(q.russian_shadow, 2),
                    "pedagogical_priority": round(q.pedagogical_priority, 2),
                    "ocr_junk": round(q.ocr_junk, 2),
                    "needs_verification": q.needs_verification,
                    "verification_route": q.verification_route,
                    "reason": q.reason,
                }
                for q in report.qualifications
            ],
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print(f"Processed: {report.total_processed} words in {report.elapsed_seconds:.2f}s ({report.words_per_second:.1f} w/s)")
        print(f"  Standard Literary: {report.standard_literary}")
        print(f"  Dialectal:         {report.dialectal}")
        print(f"  Archaism:          {report.archaism}")
        print(f"  Calque/Russianism: {report.calque_russianism}")
        print(f"  OCR Junk:          {report.ocr_junk_count}")
        print(f"  Needs Review:      {report.needs_verification_count}")
        print(f"  Avg Priority:      {report.average_priority:.2f} / 4.0")


if __name__ == "__main__":
    main()
