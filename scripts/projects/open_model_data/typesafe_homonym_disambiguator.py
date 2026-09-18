"""TypeSafe System One Contextual Homonym & Syntactic Valency Disambiguation Engine.

Resolves syncretic homonyms (e.g. «мила», «пекла», «шила», «пили», «стала», «рило», «жало»)
and ambiguous syntactic roles in the 250,000+ Sovereign Ukrainian Model Dataset collection (#6321 / #8182).

Architecture:
1. Micro-Judgments via TypeSafe System One (Choice, Score, Noul):
   - Part-of-Speech & Form Disambiguation (Choice): finite_verb_past, noun_genitive, noun_nominative, noun_accusative, adjective
   - Syntactic Role Classification (Choice): predicate_verb, direct_object, subject_appositive, adnominal_attribute, adverbial_modifier
2. Confidence Routing:
   - High confidence (>= 0.85): auto-accepted as ground-truth disambiguation.
   - Borderline (< 0.85): routed to deterministic VESUM database attestation.
3. Offline Heuristic & Morphological Fallback:
   - Fully resilient using VESUM forms_all database when TypeSafe API is unavailable.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sqlite3
import urllib.request
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, ClassVar

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class SyntacticRole(StrEnum):
    PREDICATE_VERB = "predicate_verb"
    DIRECT_OBJECT = "direct_object"
    SUBJECT_APPOSITIVE = "subject_appositive"
    ADNOMINAL_ATTRIBUTE = "adnominal_attribute"
    ADVERBIAL_MODIFIER = "adverbial_modifier"
    UNKNOWN = "unknown"


class GrammaticalForm(StrEnum):
    FINITE_VERB_PAST = "finite_verb_past"
    NOUN_GENITIVE = "noun_genitive"
    NOUN_NOMINATIVE = "noun_nominative"
    NOUN_ACCUSATIVE = "noun_accusative"
    ADJECTIVE = "adjective"
    OTHER = "other"


@dataclass(frozen=True)
class HomonymDisambiguation:
    sentence: str
    target_token: str
    grammatical_form: GrammaticalForm
    syntactic_role: SyntacticRole
    lemma: str
    confidence: float
    needs_verification: bool
    reason: str


@dataclass
class HomonymBatchReport:
    total_processed: int
    finite_verbs: int
    genitive_nouns: int
    adjectives: int
    other_forms: int
    high_confidence: int
    needs_verification_count: int
    disambiguations: list[HomonymDisambiguation]


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


def _resolve_vesum_path(custom_path: Path | str | None = None) -> Path:
    """Resolve active VESUM database path across primary checkout and worktrees."""
    if custom_path is not None:
        return Path(custom_path)
    candidates = [
        PROJECT_ROOT / "data" / "vesum.db",
        Path("/home/ops/learn-ukrainian/data/vesum.db"),
    ]
    for c in candidates:
        if c.is_file() and c.stat().st_size > 1024:
            return c
    return PROJECT_ROOT / "data" / "vesum.db"


class TypeSafeHomonymDisambiguator:
    """Contextual homonym disambiguator backed by TypeSafe System One."""

    CRITERIA_ROLE: ClassVar[dict[str, str]] = {
        "predicate_verb": "Finite verb expressing the grammatical action or state of the clause.",
        "direct_object": "Direct or partitive nominal object governed by a transitive verb.",
        "subject_appositive": "Nominal apposition explaining or renaming a head subject or object.",
        "adnominal_attribute": "Genitive or attributive nominal dependent modifying another noun.",
        "adverbial_modifier": "Adverbial modifier of time, manner, place, or measure.",
    }

    CRITERIA_FORM: ClassVar[dict[str, str]] = {
        "finite_verb_past": "Past tense finite verb form (e.g., вона мила, вони пили, воно пекло).",
        "noun_genitive": "Genitive case noun dependent (e.g., шматок мила, дві пили заводу, гострого шила).",
        "noun_nominative": "Nominative case noun form functioning as subject or apposition.",
        "noun_accusative": "Accusative case noun form functioning as direct object.",
        "adjective": "Adjectival modifier or short predicative form (e.g., була мила).",
    }

    KNOWN_LEMMA_FALLBACKS: ClassVar[dict[tuple[str, GrammaticalForm], str]] = {
        ("мила", GrammaticalForm.FINITE_VERB_PAST): "мити",
        ("мила", GrammaticalForm.NOUN_GENITIVE): "мило",
        ("мила", GrammaticalForm.NOUN_NOMINATIVE): "мила",
        ("мила", GrammaticalForm.ADJECTIVE): "милий",
        ("пили", GrammaticalForm.FINITE_VERB_PAST): "пити",
        ("пили", GrammaticalForm.NOUN_GENITIVE): "пила",
        ("пили", GrammaticalForm.NOUN_NOMINATIVE): "пила",
        ("шило", GrammaticalForm.NOUN_NOMINATIVE): "шило",
        ("шила", GrammaticalForm.FINITE_VERB_PAST): "шити",
        ("шила", GrammaticalForm.NOUN_GENITIVE): "шило",
        ("пекла", GrammaticalForm.FINITE_VERB_PAST): "пекти",
        ("пекла", GrammaticalForm.NOUN_GENITIVE): "пекло",
    }

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "https://api.typesafe.ai",
        batch_size: int = 20,
        vesum_path: Path | str | None = None,
    ) -> None:
        self.api_key = api_key if api_key is not None else _resolve_typesafe_key()
        self.base_url = base_url.rstrip("/")
        self.batch_size = max(1, batch_size)
        self.vesum_path = _resolve_vesum_path(vesum_path)
        self._vesum_conn: sqlite3.Connection | None = None

    def _get_vesum_conn(self) -> sqlite3.Connection | None:
        if self._vesum_conn is None and self.vesum_path.is_file():
            try:
                self._vesum_conn = sqlite3.connect(str(self.vesum_path))
            except sqlite3.Error:
                self._vesum_conn = None
        return self._vesum_conn

    def disambiguate(self, sentence: str, target_token: str) -> HomonymDisambiguation:
        """Disambiguate a single token within its sentence context."""
        results = self.batch_disambiguate([(sentence, target_token)])
        return results[0]

    def batch_disambiguate(self, items: list[tuple[str, str]]) -> list[HomonymDisambiguation]:
        """Batch disambiguate multiple (sentence, target_token) pairs."""
        if not items:
            return []

        results: list[HomonymDisambiguation] = []

        if self.api_key:
            for offset in range(0, len(items), self.batch_size):
                batch = items[offset : offset + self.batch_size]
                try:
                    batch_results = self._call_batch_api(batch)
                    results.extend(batch_results)
                    continue
                except Exception:
                    pass
                for s, tok in batch:
                    results.append(self._heuristic_disambiguate(s, tok))
        else:
            for s, tok in items:
                results.append(self._heuristic_disambiguate(s, tok))

        return results

    def _call_batch_api(self, batch: list[tuple[str, str]]) -> list[HomonymDisambiguation]:
        """Batch call remote TypeSafe System One API."""
        questions: dict[str, Any] = {}
        for idx, (_sent, _tok) in enumerate(batch):
            questions[f"i{idx}_form"] = {
                "type": "choice",
                "instructions": f"In context state.items[{idx}].sentence, what is the grammatical form of target token state.items[{idx}].token?",
                "criteria": self.CRITERIA_FORM,
            }
            questions[f"i{idx}_role"] = {
                "type": "choice",
                "instructions": f"In context state.items[{idx}].sentence, what is the syntactic role of target token state.items[{idx}].token?",
                "criteria": self.CRITERIA_ROLE,
            }

        url = f"{self.base_url}/v1/systemone"
        payload = {
            "model": "jev-latest",
            "state": {"items": [{"sentence": s, "token": t} for s, t in batch]},
            "questions": questions,
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
                "User-Agent": "learn-ukrainian-homonym-disambiguator/1.0",
            },
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=30.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        answers = data.get("answers", {})
        results: list[HomonymDisambiguation] = []

        for idx, (sent, tok) in enumerate(batch):
            form_ans = answers.get(f"i{idx}_form")
            role_ans = answers.get(f"i{idx}_role")

            is_valid_structure = isinstance(form_ans, dict) and isinstance(role_ans, dict)
            form_choice = form_ans.get("choice") if is_valid_structure else None
            role_choice = role_ans.get("choice") if is_valid_structure else None

            valid_form = (
                is_valid_structure
                and form_choice in GrammaticalForm._value2member_map_
                and form_choice != GrammaticalForm.OTHER.value
            )
            valid_role = (
                is_valid_structure
                and role_choice in SyntacticRole._value2member_map_
                and role_choice != SyntacticRole.UNKNOWN.value
            )

            if not (valid_form and valid_role):
                g_form = (
                    GrammaticalForm(form_choice)
                    if (form_choice in GrammaticalForm._value2member_map_)
                    else GrammaticalForm.OTHER
                )
                s_role = (
                    SyntacticRole(role_choice)
                    if (role_choice in SyntacticRole._value2member_map_)
                    else SyntacticRole.UNKNOWN
                )
                lemma, _ = self._lookup_vesum_lemma(tok, g_form)
                results.append(
                    HomonymDisambiguation(
                        sentence=sent,
                        target_token=tok,
                        grammatical_form=g_form,
                        syntactic_role=s_role,
                        lemma=lemma,
                        confidence=0.0,
                        needs_verification=True,
                        reason=f"Unrecognized or invalid form/role choice from TypeSafe API (form={form_choice!r}, role={role_choice!r})",
                    )
                )
                continue

            g_form = GrammaticalForm(form_choice)
            s_role = SyntacticRole(role_choice)

            try:
                conf_form = float(form_ans.get("confidence", -1))
                conf_role = float(role_ans.get("confidence", -1))
                if not (
                    math.isfinite(conf_form)
                    and 0.0 <= conf_form <= 1.0
                    and math.isfinite(conf_role)
                    and 0.0 <= conf_role <= 1.0
                ):
                    raise ValueError("Confidence out of finite [0..1] range")
                confidence = min(conf_form, conf_role)
            except (TypeError, ValueError):
                lemma, _ = self._lookup_vesum_lemma(tok, g_form)
                results.append(
                    HomonymDisambiguation(
                        sentence=sent,
                        target_token=tok,
                        grammatical_form=g_form,
                        syntactic_role=s_role,
                        lemma=lemma,
                        confidence=0.0,
                        needs_verification=True,
                        reason="Malformed or non-numeric confidence in TypeSafe API response",
                    )
                )
                continue

            lemma, attested = self._lookup_vesum_lemma(tok, g_form)
            needs_ver = (confidence < 0.85) or not attested
            reason = (
                "Auto-accepted by TypeSafe System One"
                if not needs_ver
                else (f"Confidence {confidence:.2f} < 0.85" if confidence < 0.85 else "Lemma not attested in VESUM")
            )

            results.append(
                HomonymDisambiguation(
                    sentence=sent,
                    target_token=tok,
                    grammatical_form=g_form,
                    syntactic_role=s_role,
                    lemma=lemma,
                    confidence=round(confidence, 2),
                    needs_verification=needs_ver,
                    reason=reason,
                )
            )

        return results

    def _lookup_vesum_lemma(self, tok: str, form: GrammaticalForm) -> tuple[str, bool]:
        """Query VESUM to resolve canonical lemma for the disambiguated form.

        Returns (lemma, attested_in_morphology).
        """
        lower_t = tok.lower()
        ves_conn = self._get_vesum_conn()
        if not ves_conn:
            if (lower_t, form) in self.KNOWN_LEMMA_FALLBACKS:
                return (self.KNOWN_LEMMA_FALLBACKS[(lower_t, form)], True)
            return (lower_t, False)

        try:
            cur = ves_conn.cursor()
            if form == GrammaticalForm.FINITE_VERB_PAST:
                cur.execute(
                    "SELECT lemma FROM forms_all WHERE word_form = ? AND pos = 'verb' AND tags LIKE '%past%' LIMIT 1",
                    (lower_t,),
                )
            elif form == GrammaticalForm.NOUN_GENITIVE:
                cur.execute(
                    "SELECT lemma FROM forms_all WHERE word_form = ? AND pos = 'noun' AND tags LIKE '%v_rod%' LIMIT 1",
                    (lower_t,),
                )
            elif form == GrammaticalForm.NOUN_NOMINATIVE:
                cur.execute(
                    "SELECT lemma FROM forms_all WHERE word_form = ? AND pos = 'noun' AND tags LIKE '%v_naz%' LIMIT 1",
                    (lower_t,),
                )
            elif form == GrammaticalForm.NOUN_ACCUSATIVE:
                cur.execute(
                    "SELECT lemma FROM forms_all WHERE word_form = ? AND pos = 'noun' AND tags LIKE '%v_zna%' LIMIT 1",
                    (lower_t,),
                )
            elif form == GrammaticalForm.ADJECTIVE:
                cur.execute(
                    "SELECT lemma FROM forms_all WHERE word_form = ? AND pos = 'adj' LIMIT 1",
                    (lower_t,),
                )
            else:
                cur.execute("SELECT lemma FROM forms_all WHERE word_form = ? LIMIT 1", (lower_t,))
            row = cur.fetchone()
            if row:
                return (row[0], True)
        except sqlite3.Error:
            pass

        if (lower_t, form) in self.KNOWN_LEMMA_FALLBACKS:
            return (self.KNOWN_LEMMA_FALLBACKS[(lower_t, form)], True)
        return (lower_t, False)

    def _heuristic_disambiguate(self, sentence: str, target_token: str) -> HomonymDisambiguation:
        """Deterministic heuristic and VESUM-backed disambiguation."""
        # Validate that the target token occurs as a complete word in the sentence
        if not re.search(rf"\b{re.escape(target_token)}\b", sentence, re.IGNORECASE):
            return HomonymDisambiguation(
                sentence=sentence,
                target_token=target_token,
                grammatical_form=GrammaticalForm.OTHER,
                syntactic_role=SyntacticRole.UNKNOWN,
                lemma=target_token,
                confidence=0.0,
                needs_verification=True,
                reason=f"Target token {target_token!r} not found as a complete word token in sentence",
            )

        lower_t = target_token.lower()
        lower_s = sentence.lower()

        # Check surrounding syntactic environment
        # 1. Subject pronoun preceding target: «вона мила», «дівчина мила», «вони пили»
        verb_preceding_match = re.search(
            r"\b(я|ти|він|вона|воно|ми|ви|вони|дівчина|жінка|сестра|мати|хлопець)\s+" + re.escape(lower_t) + r"\b",
            lower_s,
        )
        has_direct_object_following = re.search(
            r"\b" + re.escape(lower_t) + r"\s+(руки|посуд|воду|чай|кефір|підлогу|обличчя)\b",
            lower_s,
        )

        if verb_preceding_match or has_direct_object_following:
            lemma, attested = self._lookup_vesum_lemma(target_token, GrammaticalForm.FINITE_VERB_PAST)
            return HomonymDisambiguation(
                sentence=sentence,
                target_token=target_token,
                grammatical_form=GrammaticalForm.FINITE_VERB_PAST,
                syntactic_role=SyntacticRole.PREDICATE_VERB,
                lemma=lemma,
                confidence=0.92 if attested else 0.50,
                needs_verification=not attested,
                reason=(
                    "Preceding subject or governed direct object confirms finite verb reading"
                    if attested
                    else f"Verb pattern matched but token {target_token!r} not attested in VESUM"
                ),
            )

        # 2. Genitive container / measure preceding target: «шматок мила», «брусок мила», «дві пили», «три пили»
        noun_preceding_match = re.search(
            r"\b(шматок|брусок|залишок|грам|кілограм|пачка|запах|виробництво|заводу|майстра)\s+"
            + re.escape(lower_t)
            + r"\b",
            lower_s,
        )
        numeral_saw_match = re.search(
            r"\b(дві|три|чотири|одна)\s+" + re.escape(lower_t) + r"\s+(заводу|лісгоспу|майстра)\b",
            lower_s,
        )

        if noun_preceding_match or numeral_saw_match:
            lemma, attested = self._lookup_vesum_lemma(target_token, GrammaticalForm.NOUN_GENITIVE)
            return HomonymDisambiguation(
                sentence=sentence,
                target_token=target_token,
                grammatical_form=GrammaticalForm.NOUN_GENITIVE,
                syntactic_role=SyntacticRole.ADNOMINAL_ATTRIBUTE,
                lemma=lemma,
                confidence=0.90 if attested else 0.50,
                needs_verification=not attested,
                reason=(
                    "Governed nominal attribute or measure dependent confirms noun reading"
                    if attested
                    else f"Noun pattern matched but token {target_token!r} not attested in VESUM"
                ),
            )

        # 3. Copula or predicative degree adverb preceding: «була мила», «напрочуд мила», «дуже мила»
        adj_preceding_match = re.search(
            r"\b(була|стала|напрочуд|дуже|надзвичайно|така)\s+" + re.escape(lower_t) + r"\b",
            lower_s,
        )
        if adj_preceding_match:
            lemma, attested = self._lookup_vesum_lemma(target_token, GrammaticalForm.ADJECTIVE)
            return HomonymDisambiguation(
                sentence=sentence,
                target_token=target_token,
                grammatical_form=GrammaticalForm.ADJECTIVE,
                syntactic_role=SyntacticRole.PREDICATE_VERB,
                lemma=lemma,
                confidence=0.88 if attested else 0.50,
                needs_verification=not attested,
                reason=(
                    "Preceding copula or degree adverb confirms adjectival reading"
                    if attested
                    else f"Adjective pattern matched but token {target_token!r} not attested in VESUM"
                ),
            )

        # Default VESUM fallback
        lemma, attested = self._lookup_vesum_lemma(target_token, GrammaticalForm.OTHER)
        return HomonymDisambiguation(
            sentence=sentence,
            target_token=target_token,
            grammatical_form=GrammaticalForm.OTHER,
            syntactic_role=SyntacticRole.UNKNOWN,
            lemma=lemma,
            confidence=0.60 if attested else 0.30,
            needs_verification=True,
            reason="Ambiguous context routed for manual linguistic evaluation",
        )


def main() -> None:
    """CLI test interface for homonym disambiguation."""
    parser = argparse.ArgumentParser(description="Disambiguate Ukrainian homonyms via TypeSafe System One")
    parser.add_argument("--sentence", required=True, help="Context sentence")
    parser.add_argument("--token", required=True, help="Homonym token to disambiguate")
    args = parser.parse_args()

    disambiguator = TypeSafeHomonymDisambiguator()
    result = disambiguator.disambiguate(args.sentence, args.token)

    out = {
        "sentence": result.sentence,
        "token": result.target_token,
        "grammatical_form": result.grammatical_form.value,
        "syntactic_role": result.syntactic_role.value,
        "lemma": result.lemma,
        "confidence": round(result.confidence, 2),
        "needs_verification": result.needs_verification,
        "reason": result.reason,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
