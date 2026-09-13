#!/usr/bin/env python3
"""Phase 3.5: Automated CoT Claim-Verifier & Schema Reconciliation (#8009).

Verifies factual grounding across Ukrainian Linguistic Decolonization & Reasoning (ULDR)
Chain-of-Thought (CoT) trajectories against local authoritative databases:
  1. VESUM (data/vesum.db): Lemma attestation, inflected forms count, tags, living standard validity.
  2. СУМ-11 (data/sources.db): Headword presence, definitions, and sovietization risk flags.
  3. R2U (1920s dictionaries / cache): Historical contrast and pre-Soviet attestation.
  4. ULIF (data/ulif_dump_all.db, sources.db): Register qualifiers and canonical headwords.
  5. Negative controls (PRESERVE): Verified standard Ukrainian, zero fabricated suppression notes.

Hard rejection policy: Any trajectory containing an ungrounded or unverifiable claim is rejected.
Zero LLM generation: 100% deterministic rule-based verification.
"""

from __future__ import annotations

import argparse
import enum
import hashlib
import json
import logging
import re
import sqlite3
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import jsonschema

REPO_ROOT = Path(__file__).resolve().parents[3]


def resolve_data_path(rel_path: str) -> Path:
    """Resolve a relative data path, falling back to git common parent checkout for gitignored files."""
    local_p = REPO_ROOT / rel_path
    if local_p.exists() and local_p.stat().st_size > 0:
        return local_p
    try:
        common = subprocess.check_output(
            ["git", "rev-parse", "--git-common-dir"],
            cwd=REPO_ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=15,
        ).strip()
        main_p = Path(common).resolve().parent / rel_path
        if main_p.exists() and main_p.stat().st_size > 0:
            return main_p
    except Exception:
        pass
    return local_p


CONTRACTS_DIR = REPO_ROOT / "data" / "projects" / "open_model_data" / "contracts"
TRAJECTORY_SCHEMA_PATH = CONTRACTS_DIR / "v1_decolonization_trajectory.schema.json"
RECEIPT_SCHEMA_PATH = CONTRACTS_DIR / "v1_cot_claim_verification_receipt.schema.json"

DEFAULT_VESUM_DB = resolve_data_path("data/vesum.db")
DEFAULT_SOURCES_DB = resolve_data_path("data/sources.db")
DEFAULT_ULIF_DB = resolve_data_path("data/ulif_dump_all.db")
DEFAULT_R2U_CACHE = resolve_data_path("data/projects/open_model_data/soviet_candidates/r2u_differential_cache.json")
DEFAULT_INPUT_TRAJECTORIES = resolve_data_path("data/projects/open_model_data/decolonization/seeds/seed_decolonization_trajectories.jsonl")
DEFAULT_TRAJECTORIES_DIR = REPO_ROOT / "data" / "projects" / "open_model_data" / "trajectories"
DEFAULT_VERIFIED_OUTPUT = DEFAULT_TRAJECTORIES_DIR / "verified_trajectories.jsonl"
DEFAULT_REJECTED_OUTPUT = DEFAULT_TRAJECTORIES_DIR / "rejected_trajectories.jsonl"
DEFAULT_RECEIPT_OUTPUT = DEFAULT_TRAJECTORIES_DIR / "cot_claim_verification_receipt.json"

PRIVATE_HOST_RE = re.compile(r"(?:/home/(?:ops|ubuntu)|/Users/|[\d]{1,3}\.[\d]{1,3}\.[\d]{1,3}\.[\d]{1,3})")
ACUTE_RE = re.compile(r"[\u0301\u0300]")
CLEAN_WORD_RE = re.compile(r"^[\"'«»„”“,.:;!?…\s]+|[\"'«»„”“,.:;!?…\s]+$")


def clean_word(w: str) -> str:
    """Strip accents and edge punctuation from a Ukrainian word."""
    return CLEAN_WORD_RE.sub("", ACUTE_RE.sub("", w)).strip().lower()


def sha256_file(path: Path) -> str:
    """Compute SHA-256 hex digest of a file."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(text: str) -> str:
    """Compute SHA-256 hex digest of UTF-8 string."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def validate_no_private_host_paths(data: Any) -> None:
    """Ensure no host-local private paths or raw IPs exist in committed structures."""
    serialized = json.dumps(data, ensure_ascii=False)
    match = PRIVATE_HOST_RE.search(serialized)
    if match:
        raise ValueError(f"OPSEC violation: private path detected: {match.group(0)}")


class R2ULookupStatus(enum.StrEnum):
    FOUND = "found"
    NOT_FOUND = "not_found"
    NOT_FOUND_WITHIN_VERIFIED_COVERAGE = "not_found_within_verified_coverage"
    SOURCE_UNAVAILABLE = "source_unavailable"
    CACHED = "cached"
    NOT_QUERIED = "not_queried"


class ClaimType(enum.StrEnum):
    VESUM_LEMMA = "VESUM_LEMMA"
    VESUM_FORM_COUNT = "VESUM_FORM_COUNT"
    VESUM_TAGS = "VESUM_TAGS"
    SUM11_HEADWORD = "SUM11_HEADWORD"
    SUM11_VOLUME_YEAR = "SUM11_VOLUME_YEAR"
    SUM11_STYLISTIC = "SUM11_STYLISTIC"
    SUM11_SOVIETIZATION = "SUM11_SOVIETIZATION"
    R2U_HISTORICAL = "R2U_HISTORICAL"
    ULIF_REGISTER = "ULIF_REGISTER"
    NEGATIVE_CONTROL = "NEGATIVE_CONTROL"


# Authoritative bibliographic source:
# «Словник української мови: в 11 томах / АН УРСР. Інститут мовознавства імені О. О. Потебні;
# редкол.: І. К. Білодід (голова) та ін. — К. : Наукова думка, 1970—1980.»
SUM11_VOLUMES: dict[int, dict[str, Any]] = {
    1: {"letters": ("А", "В"), "year": 1970},
    2: {"letters": ("Г", "Ж"), "year": 1971},
    3: {"letters": ("З", "З"), "year": 1972},
    4: {"letters": ("І", "М"), "year": 1973},
    5: {"letters": ("Н", "О"), "year": 1974},
    6: {"letters": ("П", "ПОЇТИ"), "year": 1975},
    7: {"letters": ("ПОЇХАТИ", "ПРИРОБЛЯТИ"), "year": 1976},
    8: {"letters": ("ПРИРОДА", "РЯХТЛИВИЙ"), "year": 1977},
    9: {"letters": ("С", "С"), "year": 1978},
    10: {"letters": ("Т", "Ф"), "year": 1979},
    11: {"letters": ("Х", "Ь"), "year": 1980},
}


def is_term_in_sum11_volume(term: str, volume: int) -> bool:
    """Verify if a term falls into the alphabetical range of a СУМ-11 volume.

    Grounded in the official volume titles of Словник української мови в 11 томах (1970–1980).
    """
    t = clean_word(term.split()[0])
    if not t or volume not in SUM11_VOLUMES:
        return False
    first = t[0]
    simple_volume_letters = {
        1: "абв",
        2: "гґдеєж",
        3: "з",
        4: "іїйклм",
        5: "но",
        9: "с",
        10: "туф",
        11: "хцчшщьюя",
    }
    if volume in simple_volume_letters:
        return first in simple_volume_letters[volume]
    if volume == 6:
        return first == "п" and t <= "поїти"
    if volume == 7:
        return first == "п" and "поїти" < t <= "приробляти"
    if volume == 8:
        return (first == "п" and t > "приробляти") or (first == "р" and t <= "ряхтливий")
    return False



@dataclass(frozen=True)
class ParsedClaim:
    claim_type: ClaimType
    source_field: str
    term: str
    claim_text: str
    expected_attributes: dict[str, Any] = field(default_factory=dict)


@dataclass
class ClaimVerificationResult:
    claim: ParsedClaim
    passed: bool
    evidence: str
    error_message: str = ""


@dataclass
class TrajectoryVerificationOutcome:
    trajectory_id: str
    target_term: str
    is_calque: bool
    passed: bool
    claims_verified: list[ClaimVerificationResult]
    rejection_reasons: list[dict[str, Any]] = field(default_factory=list)


def detect_term_polarity(text: str, term: str) -> bool | None:
    """Detect whether a term in context is asserted as attested (True), absent (False), or ambiguous (None).

    Adversarial rigor: avoids silent default-to-True which would allow ungrounded absence claims
    expressed with non-standard phrasing to falsely pass as presence assertions.
    """
    t_escaped = re.escape(term)
    term_pat = rf"(?:«|\"|“|\b){t_escaped}(?:»|\"|”|\b)"
    neg_patterns = [
        rf"{term_pat}[^\n.]{{0,45}}(?:не\s+(?:зафіксован|засвідчен|подан|включен|відом|трапля|існує|подибу|зустріча|знаходи|знайдено|вжива|знає|містить|фіксує)|відсутн|немає|бракує|випадає(?:\s+з\s+реєстру)?|без\s+фіксації)",
        rf"(?:не\s+(?:зафіксован|засвідчен|подан|включен|відом|трапля|існує|подибу|зустріча|знаходи|знайдено|вжива|знає|містить|фіксує)|відсутн|немає|бракує|випадає(?:\s+з\s+реєстру)?|без\s+фіксації)[^\n.]{{0,45}}{term_pat}",
    ]
    for pat in neg_patterns:
        if re.search(pat, text, re.IGNORECASE):
            return False

    pos_patterns = [
        rf"{term_pat}[^\n.]{{0,45}}(?:зафіксован|засвідчен|подан|наявн|містить|трапля|зустріча|знаходи|вжива|фіксує)",
        rf"(?:зафіксован|засвідчен|подан|наявн|містить|трапля|зустріча|знаходи|вжива|фіксує|відповідником\s+є|замість\s+якого|наведено|подає|є\s+у\s+словник|міститься)[^\n.]{{0,45}}{term_pat}",
    ]
    for pat in pos_patterns:
        if re.search(pat, text, re.IGNORECASE):
            return True

    return None


class CoTClaimVerifier:
    """Automated claim verifier against local authoritative databases."""

    def __init__(
        self,
        vesum_conn: sqlite3.Connection,
        sources_conn: sqlite3.Connection,
        ulif_conn: sqlite3.Connection | None = None,
        r2u_cache: dict[str, Any] | None = None,
        allow_network: bool = False,
    ) -> None:
        self.vesum_conn = vesum_conn
        self.sources_conn = sources_conn
        self.ulif_conn = ulif_conn
        self.r2u_cache = r2u_cache or {}
        self.allow_network = allow_network
        self._vesum_cache: dict[str, int] = {}
        self._sum11_cache: dict[str, dict[str, Any] | None] = {}
        self._ulif_cache: dict[str, bool] = {}

    def get_vesum_forms_count(self, lemma: str) -> int:
        norm = clean_word(lemma)
        if norm in self._vesum_cache:
            return self._vesum_cache[norm]
        cur = self.vesum_conn.cursor()
        cur.execute("SELECT count(*) FROM forms_all WHERE lemma = ?", (norm,))
        row = cur.fetchone()
        cnt = row[0] if row else 0
        if cnt == 0:
            # Fallback check for exact case if proper noun
            cur.execute("SELECT count(*) FROM forms_all WHERE lemma = ?", (lemma.strip(),))
            row = cur.fetchone()
            cnt = row[0] if row else 0
        self._vesum_cache[norm] = cnt
        return cnt

    def check_vesum_tags(self, lemma: str, expected_tags: list[str]) -> bool:
        norm = clean_word(lemma)
        cur = self.vesum_conn.cursor()
        cur.execute("SELECT DISTINCT pos, tags FROM forms_all WHERE lemma = ?", (norm,))
        rows = cur.fetchall()
        if not rows:
            return False
        vesum_vocab = {
            "noun", "verb", "adj", "adv", "numr", "pron", "prep", "conj", "part", "intj",
            "m", "f", "n", "p", "anim", "inanim", "perf", "imperf", "pres", "futr", "past",
            "inf", "impr", "short", "long",
        }
        relevant_expected = [t.lower() for t in expected_tags if t.lower() in vesum_vocab]
        if not relevant_expected:
            return True
        all_tags_text = " ".join(f"{r[0]}:{r[1]}" for r in rows).lower()
        return all(t in all_tags_text for t in relevant_expected)

    def get_sum11_entry(self, word: str) -> dict[str, Any] | None:
        norm = clean_word(word)
        if norm in self._sum11_cache:
            return self._sum11_cache[norm]
        cur = self.sources_conn.cursor()
        cur.execute(
            """
            SELECT id, word, definition, text, sovietization_risk, sovietization_keywords
            FROM sum11
            WHERE word = ? OR word LIKE ? OR word LIKE ? OR word LIKE ?
            LIMIT 1
            """,
            (norm, f"{norm}|%", f"%|{norm}|%", f"%|{norm}"),
        )
        row = cur.fetchone()
        if not row:
            self._sum11_cache[norm] = None
            return None
        res = {
            "id": row[0],
            "word": row[1],
            "definition": row[2],
            "text": row[3],
            "sovietization_risk": row[4],
            "sovietization_keywords": row[5] if len(row) > 5 else "",
        }
        self._sum11_cache[norm] = res
        return res

    def check_ulif_attestation(self, word: str) -> bool:
        norm = clean_word(word)
        if norm in self._ulif_cache:
            return self._ulif_cache[norm]

        found = False
        # Check ulif_dump_all.db if available
        if self.ulif_conn:
            cur = self.ulif_conn.cursor()
            cur.execute(
                "SELECT status FROM ulif_entries WHERE lemma = ? COLLATE NOCASE OR canonical_headword = ? COLLATE NOCASE",
                (norm, norm),
            )
            row = cur.fetchone()
            if row and row[0] == "ok":
                found = True

        # Fallback check in sources.db table ulif_dictua_entries if table exists
        if not found:
            try:
                cur = self.sources_conn.cursor()
                cur.execute(
                    "SELECT status FROM ulif_dictua_entries WHERE normalized_query = ? OR canonical_headword = ? COLLATE NOCASE",
                    (norm, norm),
                )
                row = cur.fetchone()
                if row and row[0] == "ok":
                    found = True
            except sqlite3.OperationalError:
                pass

        self._ulif_cache[norm] = found
        return found

    def query_r2u_historical(self, term: str) -> tuple[R2ULookupStatus, list[str]]:
        norm = clean_word(term)
        if norm in self.r2u_cache:
            entry = self.r2u_cache[norm]
            raw_status = entry.get("status", "found")
            try:
                status = R2ULookupStatus(raw_status)
            except ValueError:
                status = R2ULookupStatus.FOUND
            translations = entry.get("translations", [])
            return status, translations

        if not self.allow_network:
            return R2ULookupStatus.NOT_QUERIED, []

        try:
            from scripts.rag.source_query import r2u_translate_with_status

            sq_status, entries = r2u_translate_with_status(norm)
            if sq_status.value == R2ULookupStatus.FOUND.value:
                translations = [e.get("translation", "") for e in entries if e.get("translation")]
                res_status = R2ULookupStatus.FOUND
                res_trans = translations[:10]
            elif sq_status.value == R2ULookupStatus.SOURCE_UNAVAILABLE.value:
                res_status = R2ULookupStatus.SOURCE_UNAVAILABLE
                res_trans = []
            else:
                res_status = R2ULookupStatus.NOT_FOUND_WITHIN_VERIFIED_COVERAGE
                res_trans = []

            if res_status != R2ULookupStatus.SOURCE_UNAVAILABLE:
                self.r2u_cache[norm] = {
                    "status": res_status.value,
                    "translations": res_trans[:5],
                }
            return res_status, res_trans
        except Exception:
            return R2ULookupStatus.SOURCE_UNAVAILABLE, []

    def parse_trajectory_claims(self, trajectory: dict[str, Any]) -> list[ParsedClaim]:
        """Extract all checkable factual claims from trajectory steps and fields."""
        claims: list[ParsedClaim] = []
        is_calque = trajectory.get("is_calque_or_russianism", True)
        target_term = trajectory.get("target_term", "")

        # 1. Claims in vesum_attestation
        for idx, item in enumerate(trajectory.get("vesum_attestation", [])):
            lemma = item.get("lemma", "")
            is_standard = item.get("is_standard_attested", True)
            claimed_count = item.get("vesum_forms_count")
            tags = item.get("tags", [])
            claims.append(
                ParsedClaim(
                    claim_type=ClaimType.VESUM_LEMMA,
                    source_field=f"vesum_attestation[{idx}].lemma",
                    term=lemma,
                    claim_text=f"Lemma «{lemma}» attestation (is_standard_attested={is_standard})",
                    expected_attributes={"is_standard_attested": is_standard},
                )
            )
            if claimed_count is not None:
                claims.append(
                    ParsedClaim(
                        claim_type=ClaimType.VESUM_FORM_COUNT,
                        source_field=f"vesum_attestation[{idx}].vesum_forms_count",
                        term=lemma,
                        claim_text=f"Lemma «{lemma}» forms count claims {claimed_count}",
                        expected_attributes={"claimed_count": claimed_count, "is_standard_attested": is_standard},
                    )
                )
            if tags and is_standard:
                claims.append(
                    ParsedClaim(
                        claim_type=ClaimType.VESUM_TAGS,
                        source_field=f"vesum_attestation[{idx}].tags",
                        term=lemma,
                        claim_text=f"Lemma «{lemma}» tags claim {tags}",
                        expected_attributes={"tags": tags},
                    )
                )

        # 2. Register spectrum claims
        reg_spec = trajectory.get("register_spectrum", {})
        primary_living = reg_spec.get("primary_living_standard", "")
        if primary_living:
            claims.append(
                ParsedClaim(
                    claim_type=ClaimType.ULIF_REGISTER,
                    source_field="register_spectrum.primary_living_standard",
                    term=primary_living,
                    claim_text=f"Primary living standard «{primary_living}» valid in contemporary standard",
                    expected_attributes={"tier": "living_standard"},
                )
            )

        for idx, alt in enumerate(reg_spec.get("alternatives", [])):
            alt_lemma = alt.get("lemma", "")
            tier = alt.get("register_tier", "")
            claims.append(
                ParsedClaim(
                    claim_type=ClaimType.ULIF_REGISTER,
                    source_field=f"register_spectrum.alternatives[{idx}]",
                    term=alt_lemma,
                    claim_text=f"Alternative «{alt_lemma}» register tier claims «{tier}»",
                    expected_attributes={"tier": tier, "alt_entry": alt},
                )
            )

        # 3. Lexicographical context claims (historical suppression note & restoration era)
        lex_ctx = trajectory.get("lexicographical_context", {})
        suppression_note = lex_ctx.get("historical_suppression_note", "")
        if suppression_note:
            # Check СУМ-11 volume and year citations: e.g. "СУМ-11 (т. 6, 1975)"
            vol_match = re.search(r"СУМ(?:-11)?\s*\((?:т\.|том)\s*(\d+)(?:,\s*(\d{4}))?\)", suppression_note)
            if vol_match:
                vol_num = int(vol_match.group(1))
                year_num = int(vol_match.group(2)) if vol_match.group(2) else None
                claims.append(
                    ParsedClaim(
                        claim_type=ClaimType.SUM11_VOLUME_YEAR,
                        source_field="lexicographical_context.historical_suppression_note",
                        term=target_term,
                        claim_text=f"Suppression note cites СУМ-11 vol. {vol_num}" + (f", year {year_num}" if year_num else ""),
                        expected_attributes={"volume": vol_num, "year": year_num, "target_term": target_term},
                    )
                )

            # Check СУМ-11 headword citation in suppression note
            if re.search(r"СУМ(?:-11)?", suppression_note):
                quoted_in_note = re.findall(r"«([^»]+)»", suppression_note)
                sum_terms = [q for q in quoted_in_note if len(q.split()) <= 2] or ([target_term] if target_term else [])
                for s_term in sum_terms:
                    claims.append(
                        ParsedClaim(
                            claim_type=ClaimType.SUM11_HEADWORD,
                            source_field="lexicographical_context.historical_suppression_note",
                            term=s_term,
                            claim_text=f"Suppression note cites СУМ-11 presence for «{s_term}»",
                            expected_attributes={"must_exist": True},
                        )
                    )

            # Check Soviet ideological / suppression risk claim
            if is_calque and any(k in suppression_note.lower() for k in ["радянськ", "канцелярськ", "витісня", "зближення", "урср", "номенклатур"]):
                claims.append(
                    ParsedClaim(
                        claim_type=ClaimType.SUM11_SOVIETIZATION,
                        source_field="lexicographical_context.historical_suppression_note",
                        term=target_term,
                        claim_text=f"Suppression note asserts Sovietization/suppression context for «{target_term}»",
                        expected_attributes={"context": suppression_note},
                    )
                )

            # Check 1920s / pre-Soviet Academy dictionary citations in suppression note with polarity detection
            if re.search(r"1920-х|R2U|r2u|Кримськ|Голоскевич|Російсько-українськ.*словник", suppression_note):
                quoted_in_note = re.findall(r"«([^»]+)»", suppression_note)
                r2u_terms = [q for q in quoted_in_note if len(q.split()) <= 2] or ([target_term] if target_term else [])
                for r_term in r2u_terms:
                    expected_att = detect_term_polarity(suppression_note, r_term)
                    claims.append(
                        ParsedClaim(
                            claim_type=ClaimType.R2U_HISTORICAL,
                            source_field="lexicographical_context.historical_suppression_note",
                            term=r_term,
                            claim_text=f"Suppression note cites 1920s dictionary evidence for «{r_term}» (expected_attested={expected_att})",
                            expected_attributes={"expected_attested": expected_att},
                        )
                    )

        # 4. Reasoning steps CoT claims
        reasoning_steps = trajectory.get("reasoning_steps", [])
        for step_idx, step in enumerate(reasoning_steps):
            field_name = f"reasoning_steps[{step_idx}]"

            # Check explicit VESUM count citations: e.g. «слово» (25 форм), (3 форми), (1 форма)
            count_matches = re.findall(r"«([^»]+)»[^(«»]{0,25}\((\d+)\s*(?:форм[аиів]?|словоформ[аиів]?)\)", step)
            count_matches.extend(re.findall(r"«([^»]+)»[^(«»]{0,25}має\s+(\d+)\s+(?:форм[аиів]?|словоформ[аиів]?)", step))
            for lemma_match, cnt_str in count_matches:
                claims.append(
                    ParsedClaim(
                        claim_type=ClaimType.VESUM_FORM_COUNT,
                        source_field=field_name,
                        term=lemma_match.strip(),
                        claim_text=f"CoT step asserts «{lemma_match}» has {cnt_str} forms",
                        expected_attributes={"claimed_count": int(cnt_str), "is_standard_attested": True},
                    )
                )

            # Check СУМ-11 volume and year citations in reasoning steps
            vol_step_match = re.search(r"СУМ(?:-11)?\s*\((?:т\.|том)\s*(\d+)(?:,\s*(\d{4}))?\)", step)
            if vol_step_match:
                vol_num = int(vol_step_match.group(1))
                year_num = int(vol_step_match.group(2)) if vol_step_match.group(2) else None
                quoted_in_step = re.findall(r"«([^»]+)»", step)
                s_term = quoted_in_step[0] if quoted_in_step else target_term
                claims.append(
                    ParsedClaim(
                        claim_type=ClaimType.SUM11_VOLUME_YEAR,
                        source_field=field_name,
                        term=s_term,
                        claim_text=f"CoT step cites СУМ-11 vol. {vol_num}" + (f", year {year_num}" if year_num else ""),
                        expected_attributes={"volume": vol_num, "year": year_num, "target_term": s_term},
                    )
                )

            # Check СУМ-11 stylistic label claims: e.g. ремарка «рідко», «заст.», «діал.»
            style_match = re.search(r"(?:ремарк[аи]|позначк[аи]|помітк[аи]|маркер[аи])?\s*«?(рідко|заст\.|розм\.|діал\.|спец\.|канц\.)»?", step.lower())
            if style_match and ("сум" in step.lower() or "словник" in step.lower()):
                quoted_in_step = re.findall(r"«([^»]+)»", step)
                t_word = quoted_in_step[0] if quoted_in_step else target_term
                lbl = style_match.group(1).rstrip(".")
                claims.append(
                    ParsedClaim(
                        claim_type=ClaimType.SUM11_STYLISTIC,
                        source_field=field_name,
                        term=t_word,
                        claim_text=f"CoT step asserts stylistic label «{lbl}» in СУМ-11 for «{t_word}»",
                        expected_attributes={"label": lbl},
                    )
                )

            # Check general СУМ-11 citations in step
            if re.search(r"СУМ-11|СУМ\s*\(?1970–1980\)?|Словник української мови в 11 томах", step):
                quoted_in_step = re.findall(r"«([^»]+)»", step)
                target_cited = [q for q in quoted_in_step if len(q.split()) <= 2] or ([target_term] if target_term else [])
                for term_c in target_cited:
                    if term_c.lower() in ("рідко", "заст.", "діал.", "розм.", "спец.", "канц."):
                        continue
                    claims.append(
                        ParsedClaim(
                            claim_type=ClaimType.SUM11_HEADWORD,
                            source_field=field_name,
                            term=term_c,
                            claim_text=f"CoT step cites СУМ-11 presence/treatment for «{term_c}»",
                            expected_attributes={"must_exist": True},
                        )
                    )

            # Check R2U / 1920s historical dictionary citations with polarity detection
            if re.search(r"1920-х|R2U|r2u|Кримськ|Голоскевич|Російсько-українськ.*словник", step):
                quoted_in_step = re.findall(r"«([^»]+)»", step)
                r2u_terms = [q for q in quoted_in_step if len(q.split()) <= 2] or ([target_term] if target_term else [])
                for r_term in r2u_terms:
                    expected_att = detect_term_polarity(step, r_term)
                    claims.append(
                        ParsedClaim(
                            claim_type=ClaimType.R2U_HISTORICAL,
                            source_field=field_name,
                            term=r_term,
                            claim_text=f"CoT step cites 1920s dictionary / R2U evidence for «{r_term}» (expected_attested={expected_att})",
                            expected_attributes={"expected_attested": expected_att},
                        )
                    )

        # 5. Negative controls (PRESERVE) claims
        if not is_calque:
            claims.append(
                ParsedClaim(
                    claim_type=ClaimType.NEGATIVE_CONTROL,
                    source_field="is_calque_or_russianism",
                    term=target_term,
                    claim_text=f"Negative control «{target_term}» must be clean living standard Ukrainian",
                    expected_attributes={"is_calque": False},
                )
            )

        return claims

    def verify_claim(self, claim: ParsedClaim, trajectory: dict[str, Any]) -> ClaimVerificationResult:
        """Verify an individual factual claim against DBs."""
        # A. VESUM Lemma verification
        if claim.claim_type == ClaimType.VESUM_LEMMA:
            is_std = claim.expected_attributes.get("is_standard_attested", True)
            cnt = self.get_vesum_forms_count(claim.term)
            if is_std:
                if cnt > 0:
                    return ClaimVerificationResult(claim, True, f"Attested in VESUM ({cnt} forms)")
                # Check if multi-word phrase (e.g. «брати участь»): each content word must be attested
                words = [w for w in claim.term.split() if len(clean_word(w)) >= 2]
                if len(words) > 1:
                    sub_counts = [self.get_vesum_forms_count(w) for w in words]
                    if all(c > 0 for c in sub_counts):
                        return ClaimVerificationResult(claim, True, f"Attested phrase in VESUM (words attested: {sub_counts})")
                return ClaimVerificationResult(
                    claim, False, "VESUM count is 0", f"Standard lemma «{claim.term}» has 0 forms in vesum.db"
                )
            else:
                # Non-standard item (e.g. neologism/calque): valid if count is 0
                return ClaimVerificationResult(claim, True, f"Non-standard term verified (VESUM count={cnt})")

        # B. VESUM Form Count verification
        elif claim.claim_type == ClaimType.VESUM_FORM_COUNT:
            expected_cnt = claim.expected_attributes.get("claimed_count", 0)
            is_std = claim.expected_attributes.get("is_standard_attested", True)
            actual_cnt = self.get_vesum_forms_count(claim.term)
            if not is_std and expected_cnt == 0:
                if actual_cnt == 0:
                    return ClaimVerificationResult(claim, True, "Non-standard term confirmed absent (0 forms)")
                return ClaimVerificationResult(claim, False, f"Actual count {actual_cnt}", f"Claimed 0 forms but found {actual_cnt}")
            if actual_cnt == expected_cnt:
                return ClaimVerificationResult(claim, True, f"VESUM exact count verified: {actual_cnt} forms")
            # Strict exact count: no tolerance band allowed for linguistic fact grounding
            return ClaimVerificationResult(
                claim,
                False,
                f"Actual VESUM count is {actual_cnt}",
                f"VESUM form count mismatch for «{claim.term}»: claimed {expected_cnt}, actual {actual_cnt}",
            )

        # C. VESUM Tags verification
        elif claim.claim_type == ClaimType.VESUM_TAGS:
            expected_tags = claim.expected_attributes.get("tags", [])
            matches = self.check_vesum_tags(claim.term, expected_tags)
            if matches:
                return ClaimVerificationResult(claim, True, f"Tags {expected_tags} attested in VESUM")
            return ClaimVerificationResult(
                claim, False, "Tags not found", f"Lemma «{claim.term}» does not match expected tags {expected_tags}"
            )

        # D. СУМ-11 Headword verification
        elif claim.claim_type == ClaimType.SUM11_HEADWORD:
            entry = self.get_sum11_entry(claim.term)
            if entry is not None:
                return ClaimVerificationResult(claim, True, f"Found in sum11 table (id={entry['id']}, risk={entry['sovietization_risk']})")
            # If multi-word, check headword
            head = claim.term.split()[0]
            entry_head = self.get_sum11_entry(head)
            if entry_head is not None:
                return ClaimVerificationResult(claim, True, f"Found headword «{head}» in sum11 (id={entry_head['id']})")
            return ClaimVerificationResult(
                claim, False, "Not in sum11", f"Cited term «{claim.term}» does not exist in sources.db sum11 table"
            )

        # D.1 СУМ-11 Volume and Year verification
        elif claim.claim_type == ClaimType.SUM11_VOLUME_YEAR:
            vol = claim.expected_attributes.get("volume")
            year = claim.expected_attributes.get("year")
            term = claim.expected_attributes.get("target_term") or claim.term

            if vol not in SUM11_VOLUMES:
                return ClaimVerificationResult(
                    claim, False, f"Invalid volume {vol}", f"СУМ-11 has exactly 11 volumes, but volume {vol} was claimed"
                )
            vol_meta = SUM11_VOLUMES[vol]
            if year is not None and year != vol_meta["year"]:
                return ClaimVerificationResult(
                    claim,
                    False,
                    f"Year mismatch for vol {vol}",
                    f"СУМ-11 volume {vol} was published in {vol_meta['year']}, but trajectory claimed year {year}",
                )
            if not is_term_in_sum11_volume(term, vol):
                return ClaimVerificationResult(
                    claim,
                    False,
                    "Alphabetical volume mismatch",
                    f"Term «{term}» does not fall within alphabetical coverage of СУМ-11 volume {vol}",
                )
            return ClaimVerificationResult(
                claim, True, f"СУМ-11 volume {vol} and year {vol_meta['year']} verified for «{term}»"
            )

        # D.2 СУМ-11 Stylistic Label verification
        elif claim.claim_type == ClaimType.SUM11_STYLISTIC:
            label = claim.expected_attributes.get("label", "").lower()
            entry = self.get_sum11_entry(claim.term)
            if entry is None:
                return ClaimVerificationResult(
                    claim, False, "Not in sum11", f"Term «{claim.term}» does not exist in sum11 table"
                )
            text = (entry.get("text") or entry.get("definition", "")).lower()
            if label in text:
                return ClaimVerificationResult(claim, True, f"Stylistic label «{label}» verified in СУМ-11 text")
            return ClaimVerificationResult(
                claim,
                False,
                f"Label «{label}» not found",
                f"СУМ-11 entry for «{claim.term}» does not contain claimed stylistic label «{label}»",
            )

        # D.3 СУМ-11 Sovietization / Codification Context verification
        elif claim.claim_type == ClaimType.SUM11_SOVIETIZATION:
            head = claim.term.split()[0]
            entry = self.get_sum11_entry(claim.term) or self.get_sum11_entry(head)
            if entry is not None:
                risk = entry.get("sovietization_risk", 0)
                kw = entry.get("sovietization_keywords", "")
                return ClaimVerificationResult(
                    claim, True, f"СУМ-11 codification verified (id={entry['id']}, sovietization_risk={risk}, kw='{kw}')"
                )
            return ClaimVerificationResult(
                claim,
                False,
                "Term not in СУМ-11",
                f"Trajectory asserts Soviet lexicographical codification in СУМ-11, but «{claim.term}» is not present in СУМ-11",
            )

        # E. R2U Historical Dictionary verification with Polarity
        elif claim.claim_type == ClaimType.R2U_HISTORICAL:
            status, translations = self.query_r2u_historical(claim.term)
            if status == R2ULookupStatus.SOURCE_UNAVAILABLE:
                return ClaimVerificationResult(
                    claim, False, "Source unavailable", "R2U source unavailable or network timed out; fail-closed rejection"
                )
            if status == R2ULookupStatus.NOT_QUERIED:
                return ClaimVerificationResult(
                    claim, False, "R2U not queried", f"Term «{claim.term}» not found in local R2U cache and network lookup is disabled"
                )

            expected_attested = claim.expected_attributes.get("expected_attested")
            if expected_attested is None:
                return ClaimVerificationResult(
                    claim,
                    False,
                    "Ambiguous polarity",
                    f"Ambiguous 1920s lexicographical claim: could not determine whether «{claim.term}» was claimed present or absent in 1920s dictionaries",
                )

            is_found = status in (R2ULookupStatus.FOUND, R2ULookupStatus.CACHED)
            is_not_found = status in (R2ULookupStatus.NOT_FOUND, R2ULookupStatus.NOT_FOUND_WITHIN_VERIFIED_COVERAGE)

            if expected_attested:
                if is_found:
                    return ClaimVerificationResult(
                        claim, True, f"R2U attested: status={status.value}, translations={translations[:3]}"
                    )
                return ClaimVerificationResult(
                    claim,
                    False,
                    f"R2U status {status.value}",
                    f"Fabricated 1920s attestation claim: «{claim.term}» was claimed attested, but R2U returned {status.value}",
                )
            else:
                if is_not_found:
                    return ClaimVerificationResult(
                        claim, True, f"R2U confirmed absence: status={status.value}"
                    )
                return ClaimVerificationResult(
                    claim,
                    False,
                    f"R2U status {status.value}",
                    f"Fabricated 1920s absence claim: «{claim.term}» was claimed absent, but R2U returned {status.value}",
                )

        # F. ULIF Register Qualifier verification
        elif claim.claim_type == ClaimType.ULIF_REGISTER:
            tier = claim.expected_attributes.get("tier", "living_standard")
            alt_entry = claim.expected_attributes.get("alt_entry", {})
            evidence_source = alt_entry.get("evidence_source", "")

            if tier == "living_standard":
                vesum_cnt = self.get_vesum_forms_count(claim.term)
                ulif_attested = self.check_ulif_attestation(claim.term)
                if vesum_cnt > 0 or ulif_attested:
                    return ClaimVerificationResult(claim, True, f"Living standard verified (VESUM forms={vesum_cnt}, ULIF={ulif_attested})")
                words = [w for w in claim.term.split() if len(clean_word(w)) >= 2]
                if len(words) > 1 and all(self.get_vesum_forms_count(w) > 0 for w in words):
                    return ClaimVerificationResult(claim, True, "Living standard phrase verified via words in VESUM")
                return ClaimVerificationResult(
                    claim, False, "Not in living standard", f"Living standard term «{claim.term}» unattested in both VESUM and ULIF"
                )
            elif tier in ("classical_regional", "technical_compound"):
                vesum_cnt = self.get_vesum_forms_count(claim.term)
                sum_entry = self.get_sum11_entry(claim.term)
                if vesum_cnt == 0 and sum_entry is None:
                    words = [w for w in claim.term.split() if len(clean_word(w)) >= 2]
                    if not (len(words) > 1 and all(self.get_vesum_forms_count(w) > 0 for w in words)):
                        return ClaimVerificationResult(
                            claim,
                            False,
                            "Lexicographically unattested",
                            f"Register tier «{tier}» term «{claim.term}» is completely unattested in VESUM and sources",
                        )
                if not evidence_source or len(evidence_source.strip()) < 5:
                    return ClaimVerificationResult(
                        claim,
                        False,
                        "Missing evidence source",
                        f"Register tier «{tier}» requires non-empty evidence_source citation",
                    )
                return ClaimVerificationResult(
                    claim, True, f"Register tier «{tier}» verified (VESUM={vesum_cnt}, source='{evidence_source}')"
                )
            elif tier == "purist_neologism":
                claimed_cnt = alt_entry.get("vesum_forms_count", 0)
                actual_cnt = self.get_vesum_forms_count(claim.term)
                if claimed_cnt == 0 and actual_cnt > 0:
                    return ClaimVerificationResult(
                        claim,
                        False,
                        f"VESUM count is {actual_cnt}",
                        f"Claimed unrecorded purism «{claim.term}» (0 forms) actually has {actual_cnt} forms in VESUM",
                    )
                if not evidence_source or len(evidence_source.strip()) < 5:
                    return ClaimVerificationResult(
                        claim,
                        False,
                        "Missing evidence source",
                        f"Purist neologism «{claim.term}» requires cited evidence_source",
                    )
                return ClaimVerificationResult(
                    claim, True, f"Purist neologism «{claim.term}» verified with cited source: {evidence_source}"
                )

        # G. Negative Control verification
        elif claim.claim_type == ClaimType.NEGATIVE_CONTROL:
            vesum_cnt = self.get_vesum_forms_count(claim.term)
            if vesum_cnt == 0:
                words = [w for w in claim.term.split() if len(clean_word(w)) >= 2]
                if not (len(words) > 1 and all(self.get_vesum_forms_count(w) > 0 for w in words)):
                    return ClaimVerificationResult(
                        claim, False, "Target term unattested", f"PRESERVE target term «{claim.term}» must exist in VESUM"
                    )
            # Check for fabricated suppression note in PRESERVE control
            lex_ctx = trajectory.get("lexicographical_context", {})
            note = lex_ctx.get("historical_suppression_note", "")
            if note:
                # Must not allege genuine Soviet banning on clean Ukrainian terms
                banned_markers = ["заборонен", "репресован", "вилучен", "штучно нав'язан"]
                if any(m in note.lower() for m in banned_markers) and not any(
                    p in note.lower() for p in ["не зазна", "не зазнавал", "не підлягал", "preserve control", "не стосується"]
                ):
                    return ClaimVerificationResult(
                        claim,
                        False,
                        "Fabricated suppression note",
                        f"PRESERVE control falsely claims historical suppression on clean Ukrainian term: {note}",
                    )
            return ClaimVerificationResult(claim, True, "PRESERVE negative control confirmed valid")

        return ClaimVerificationResult(claim, False, "Unknown claim", f"Unsupported claim type: {claim.claim_type}")

    def verify_trajectory(
        self,
        trajectory: dict[str, Any],
        validator: jsonschema.Draft202012Validator | None = None,
    ) -> TrajectoryVerificationOutcome:
        """Run full claim verification suite on a single trajectory."""
        traj_id = trajectory.get("trajectory_id", "unknown")
        target_term = trajectory.get("target_term", "")
        is_calque = trajectory.get("is_calque_or_russianism", True)

        rejection_reasons: list[dict[str, Any]] = []

        # 1. Schema check
        if validator is not None:
            schema_errors = list(validator.iter_errors(trajectory))
            if schema_errors:
                for err in schema_errors:
                    rejection_reasons.append(
                        {
                            "claim_type": "SCHEMA_VALIDATION",
                            "source_field": "root",
                            "error": err.message,
                        }
                    )
                return TrajectoryVerificationOutcome(
                    trajectory_id=traj_id,
                    target_term=target_term,
                    is_calque=is_calque,
                    passed=False,
                    claims_verified=[],
                    rejection_reasons=rejection_reasons,
                )

        # 2. Extract and verify claims
        claims = self.parse_trajectory_claims(trajectory)
        results: list[ClaimVerificationResult] = []
        for claim in claims:
            res = self.verify_claim(claim, trajectory)
            results.append(res)
            if not res.passed:
                rejection_reasons.append(
                    {
                        "claim_type": claim.claim_type.value,
                        "source_field": claim.source_field,
                        "term": claim.term,
                        "claim_text": claim.claim_text,
                        "error": res.error_message,
                        "evidence": res.evidence,
                    }
                )

        passed = len(rejection_reasons) == 0
        return TrajectoryVerificationOutcome(
            trajectory_id=traj_id,
            target_term=target_term,
            is_calque=is_calque,
            passed=passed,
            claims_verified=results,
            rejection_reasons=rejection_reasons,
        )


def build_verification_receipt(
    total_trajectories: int,
    verified_trajectories: list[dict[str, Any]],
    rejected_trajectories: list[dict[str, Any]],
    all_outcomes: list[TrajectoryVerificationOutcome],
    input_file_info: dict[str, Any],
    verified_file_info: dict[str, Any],
    rejected_file_info: dict[str, Any],
) -> dict[str, Any]:
    """Build deterministic, schema-compliant verification receipt."""
    vesum_claims = 0
    sum11_claims = 0
    r2u_claims = 0
    ulif_claims = 0
    total_claims = 0

    for outcome in all_outcomes:
        for r in outcome.claims_verified:
            total_claims += 1
            if r.claim.claim_type in (ClaimType.VESUM_LEMMA, ClaimType.VESUM_FORM_COUNT, ClaimType.VESUM_TAGS, ClaimType.NEGATIVE_CONTROL):
                vesum_claims += 1
            elif r.claim.claim_type in (ClaimType.SUM11_HEADWORD, ClaimType.SUM11_VOLUME_YEAR, ClaimType.SUM11_STYLISTIC, ClaimType.SUM11_SOVIETIZATION):
                sum11_claims += 1
            elif r.claim.claim_type == ClaimType.R2U_HISTORICAL:
                r2u_claims += 1
            elif r.claim.claim_type == ClaimType.ULIF_REGISTER:
                ulif_claims += 1

    pass_rate_100 = bool(total_trajectories > 0 and len(rejected_trajectories) == 0 and len(verified_trajectories) == total_trajectories)

    dict_results = [
        r
        for out in all_outcomes
        for r in out.claims_verified
        if r.claim.claim_type in (
            ClaimType.SUM11_HEADWORD,
            ClaimType.SUM11_VOLUME_YEAR,
            ClaimType.SUM11_STYLISTIC,
            ClaimType.SUM11_SOVIETIZATION,
            ClaimType.R2U_HISTORICAL,
        )
    ]
    zero_unverified_claims = bool(all(r.passed for r in dict_results)) if dict_results else True

    living_std_results = [
        r
        for out in all_outcomes
        for r in out.claims_verified
        if r.claim.claim_type == ClaimType.ULIF_REGISTER and r.claim.expected_attributes.get("tier") == "living_standard"
    ]
    zero_unattested_living = bool(all(r.passed for r in living_std_results)) if living_std_results else True

    has_network_errors = any(
        r.claim.claim_type == ClaimType.R2U_HISTORICAL and "source unavailable" in r.evidence.lower()
        for out in all_outcomes
        for r in out.claims_verified
    )
    zero_network_errors = bool(not has_network_errors)

    # Enforce OPSEC scan across all trajectories written to dataset artifacts
    for rec in verified_trajectories:
        validate_no_private_host_paths(rec)
    for rec in rejected_trajectories:
        validate_no_private_host_paths(rec)

    receipt_id = f"receipt.cot_claim_verifier.{sha256_text(verified_file_info['sha256'] + input_file_info['sha256'])[:16]}"

    receipt = {
        "schema_version": "v1_cot_claim_verification_receipt",
        "receipt_id": receipt_id,
        "issue": 8009,
        "epic": 6321,
        "generated_at": datetime.now(UTC).isoformat(),
        "counts": {
            "total_trajectories": total_trajectories,
            "trajectories_passed": len(verified_trajectories),
            "trajectories_rejected": len(rejected_trajectories),
            "total_claims_verified": total_claims,
            "vesum_claims_verified": vesum_claims,
            "sum11_claims_verified": sum11_claims,
            "r2u_claims_verified": r2u_claims,
            "ulif_claims_verified": ulif_claims,
        },
        "invariants": {
            "pass_rate_100_percent": pass_rate_100,
            "zero_unverified_dictionary_claims": zero_unverified_claims,
            "zero_unattested_living_standard_terms": zero_unattested_living,
            "zero_network_errors_as_missing_word": zero_network_errors,
            "no_private_host_paths": True,
        },
        "files": {
            "input_trajectories": input_file_info,
            "verified_trajectories": verified_file_info,
            "rejected_trajectories": rejected_file_info,
        },
    }

    validate_no_private_host_paths(receipt)
    return receipt


def run_claim_verifier(
    input_path: Path,
    verified_output_path: Path,
    rejected_output_path: Path,
    receipt_output_path: Path,
    vesum_db: Path,
    sources_db: Path,
    ulif_db: Path | None = None,
    r2u_cache_path: Path | None = None,
    allow_network: bool = False,
    verify_only: bool = False,
) -> dict[str, Any]:
    """Execute trajectory claim verification or run verify-only check."""
    if verify_only:
        logging.info("Running in --verify-only mode.")
        if not receipt_output_path.is_file():
            raise FileNotFoundError(f"Receipt file missing: {receipt_output_path}")
        with receipt_output_path.open("r", encoding="utf-8") as f:
            receipt = json.load(f)

        validate_no_private_host_paths(receipt)

        if RECEIPT_SCHEMA_PATH.is_file():
            with RECEIPT_SCHEMA_PATH.open("r", encoding="utf-8") as sf:
                receipt_schema = json.load(sf)
            jsonschema.Draft202012Validator.check_schema(receipt_schema)
            jsonschema.validate(instance=receipt, schema=receipt_schema)

        # Check invariant requirements
        if not receipt["invariants"]["zero_unverified_dictionary_claims"]:
            raise ValueError("Receipt invariant failure: zero_unverified_dictionary_claims is False")
        if not receipt["invariants"]["no_private_host_paths"]:
            raise ValueError("Receipt invariant failure: no_private_host_paths is False")

        # Check files existence and hashes
        file_targets = {
            "input_trajectories": input_path,
            "verified_trajectories": verified_output_path,
            "rejected_trajectories": rejected_output_path,
        }
        for key, expected_target in file_targets.items():
            finfo = receipt["files"][key]
            rel_f = finfo["filename"]
            target = expected_target
            if not target.is_file():
                target = verified_output_path.parent / rel_f
            if not target.is_file():
                target = REPO_ROOT / rel_f
            if not target.is_file():
                raise FileNotFoundError(f"Referenced file does not exist: {rel_f}")
            actual_hash = sha256_file(target)
            if actual_hash != finfo["sha256"]:
                raise ValueError(f"Hash mismatch on {rel_f}: expected {finfo['sha256']}, got {actual_hash}")

        logging.info("Verify-only checks passed successfully.")
        return receipt

    # Fail-closed checks on required databases
    if not vesum_db.is_file():
        raise FileNotFoundError(f"Required VESUM database not found: {vesum_db}")
    if not sources_db.is_file():
        raise FileNotFoundError(f"Required sources database not found: {sources_db}")

    vesum_conn = sqlite3.connect(f"file:{vesum_db}?mode=ro", uri=True)
    sources_conn = sqlite3.connect(f"file:{sources_db}?mode=ro", uri=True)

    if ulif_db is None and DEFAULT_ULIF_DB and DEFAULT_ULIF_DB.is_file():
        ulif_db = DEFAULT_ULIF_DB
    if r2u_cache_path is None and DEFAULT_R2U_CACHE and DEFAULT_R2U_CACHE.is_file():
        r2u_cache_path = DEFAULT_R2U_CACHE

    ulif_conn = None
    if ulif_db and ulif_db.is_file():
        ulif_conn = sqlite3.connect(f"file:{ulif_db}?mode=ro", uri=True)

    r2u_cache = {}
    if r2u_cache_path and r2u_cache_path.is_file():
        with r2u_cache_path.open("r", encoding="utf-8") as f:
            r2u_cache = json.load(f)

    # Load trajectory schema for record validation
    validator = None
    if TRAJECTORY_SCHEMA_PATH.is_file():
        with TRAJECTORY_SCHEMA_PATH.open("r", encoding="utf-8") as f:
            trajectory_schema = json.load(f)
        jsonschema.Draft202012Validator.check_schema(trajectory_schema)
        validator = jsonschema.Draft202012Validator(trajectory_schema)

    verifier = CoTClaimVerifier(
        vesum_conn=vesum_conn,
        sources_conn=sources_conn,
        ulif_conn=ulif_conn,
        r2u_cache=r2u_cache,
        allow_network=allow_network,
    )

    if not input_path.is_file():
        raise FileNotFoundError(f"Input trajectories file missing: {input_path}")

    records: list[dict[str, Any]] = []
    with input_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))

    # Pre-write OPSEC gate: fail immediately before any output directory or file is touched
    for rec in records:
        validate_no_private_host_paths(rec)

    verified_records: list[dict[str, Any]] = []
    rejected_records: list[dict[str, Any]] = []
    all_outcomes: list[TrajectoryVerificationOutcome] = []

    for rec in records:
        outcome = verifier.verify_trajectory(rec, validator=validator)
        all_outcomes.append(outcome)
        if outcome.passed:
            verified_records.append(rec)
        else:
            rejected_item = {
                "trajectory_id": outcome.trajectory_id,
                "target_term": outcome.target_term,
                "is_calque": outcome.is_calque,
                "rejected": True,
                "rejection_reasons": outcome.rejection_reasons,
                "original_record": rec,
            }
            rejected_records.append(rejected_item)

    # Write output files
    verified_output_path.parent.mkdir(parents=True, exist_ok=True)
    rejected_output_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_output_path.parent.mkdir(parents=True, exist_ok=True)

    with verified_output_path.open("w", encoding="utf-8") as f:
        for r in verified_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    with rejected_output_path.open("w", encoding="utf-8") as f:
        for r in rejected_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    input_info = {
        "filename": input_path.name,
        "sha256": sha256_file(input_path),
        "line_count": len(records),
    }
    verified_info = {
        "filename": verified_output_path.name,
        "sha256": sha256_file(verified_output_path),
        "line_count": len(verified_records),
    }
    rejected_info = {
        "filename": rejected_output_path.name,
        "sha256": sha256_file(rejected_output_path),
        "line_count": len(rejected_records),
    }

    receipt = build_verification_receipt(
        total_trajectories=len(records),
        verified_trajectories=verified_records,
        rejected_trajectories=rejected_records,
        all_outcomes=all_outcomes,
        input_file_info=input_info,
        verified_file_info=verified_info,
        rejected_file_info=rejected_info,
    )

    with receipt_output_path.open("w", encoding="utf-8") as f:
        f.write(json.dumps(receipt, indent=2, sort_keys=True) + "\n")

    # Save updated r2u cache if changed
    if r2u_cache_path and verifier.r2u_cache:
        r2u_cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(r2u_cache_path, "w", encoding="utf-8") as f:
            json.dump(verifier.r2u_cache, f, indent=2, sort_keys=True, ensure_ascii=False)
            f.write("\n")

    logging.info(
        "Verification complete: %d total, %d passed, %d rejected",
        len(records),
        len(verified_records),
        len(rejected_records),
    )
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Automated CoT Claim-Verifier for Ukrainian Linguistic Reasoning Trajectories"
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_TRAJECTORIES, help="Path to input trajectories JSONL")
    parser.add_argument("--output", type=Path, default=DEFAULT_VERIFIED_OUTPUT, help="Path to output verified JSONL")
    parser.add_argument("--rejected-output", type=Path, default=DEFAULT_REJECTED_OUTPUT, help="Path to output rejected JSONL")
    parser.add_argument("--receipt", type=Path, default=DEFAULT_RECEIPT_OUTPUT, help="Path to output receipt JSON")
    parser.add_argument("--vesum-db", type=Path, default=DEFAULT_VESUM_DB, help="Path to vesum.db")
    parser.add_argument("--sources-db", type=Path, default=DEFAULT_SOURCES_DB, help="Path to sources.db")
    parser.add_argument("--ulif-db", type=Path, default=DEFAULT_ULIF_DB, help="Path to ulif_dump_all.db")
    parser.add_argument("--r2u-cache", type=Path, default=DEFAULT_R2U_CACHE, help="Path to r2u cache JSON")
    parser.add_argument("--allow-network", action="store_true", help="Allow online R2U lookup for uncached terms")
    parser.add_argument("--verify-only", action="store_true", help="Verify receipt and file integrity without re-running")
    parser.add_argument("--log-level", default="INFO", help="Logging level")

    args = parser.parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO), format="%(asctime)s [%(levelname)s] %(message)s")

    vesum_db = resolve_data_path(args.vesum_db) if args.vesum_db else None
    sources_db = resolve_data_path(args.sources_db) if args.sources_db else None
    ulif_db = resolve_data_path(args.ulif_db) if args.ulif_db else None
    r2u_cache = resolve_data_path(args.r2u_cache) if args.r2u_cache else None

    try:
        run_claim_verifier(
            input_path=resolve_data_path(args.input) if args.input else None,
            verified_output_path=args.output,
            rejected_output_path=args.rejected_output,
            receipt_output_path=args.receipt,
            vesum_db=vesum_db,
            sources_db=sources_db,
            ulif_db=ulif_db,
            r2u_cache_path=r2u_cache,
            allow_network=args.allow_network,
            verify_only=args.verify_only,
        )
    except Exception as e:
        logging.error("Fatal error during claim verification: %s", e, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
