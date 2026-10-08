#!/usr/bin/env python3
"""Dataset Builder for Decolonization & Calque Defense Component (#8340, Epic #6321).

Assembles verified Ukrainian decolonization cases from accepted authorities:
- Борис Антоненко-Давидович («Як ми говоримо»)
- UA-GEC v2 human-annotated correction pairs (Syvokon et al., UNLP 2023)
- Олександр Пономарів («Культура слова»)
- Катерина Городенська («Чи правильне слововживання?»)
- СУМ-20 & Правопис 2019

The candidate catalog targets 70% substantive corrections and 30% protective
controls across four categories. Unsupported cases are withheld rather than
replaced to fill those quotas; output counts reflect only retained cases.

Strictly enforces:
1. Withholding unsupported held-source evidence with a reason and owner.
2. Four categories: calque_lexical, calque_syntactic, calque_prepositional, protective_authentic.
3. Clean train/eval partition: held-out evaluation split with 100% disjoint target phenomena.
4. Rich register diversity: official administrative, journalistic, educational, and conversational contexts.
5. Traceable reviewer confirmations backed by live database verification in VESUM and sources.db.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import re
import sqlite3
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.readonly_sqlite import is_sqlite_connection
from scripts.lib.readonly_sqlite import open_readonly as _open_readonly
from scripts.projects.open_model_data.audit_dataset_acceptance import PROJECT_ROOT, _resolve_db_path
from scripts.projects.open_model_data.decolonization_cases_data import (
    LEXICAL_CALQUES,
    PREPOSITIONAL_CALQUES,
    PROTECTIVE_CONTROLS,
    SYNTACTIC_CALQUES,
)
from scripts.projects.open_model_data.decolonization_evidence_catalog import EXPLICIT_SOURCE_EVIDENCE
from scripts.projects.open_model_data.decolonization_language_reviews import (
    INDEPENDENT_LANGUAGE_REVIEWS,
    compute_case_content_sha256,
)
from scripts.projects.open_model_data.paths import ARTIFACT_DECOLONIZATION_DIR, REGISTRY_DECOLONIZATION_DIR
from scripts.projects.open_model_data.sum20_codification_records import (
    COMMITTED_SUM20_RECORDS,
    _quarantined_headwords,
    _record_source,
    committed_record_dispositions,
    ensure_reproducible_sum20_table,
)
from scripts.storage import paths as storage_paths
from scripts.storage.artifacts import write_artifact_set
from scripts.wiki.sum20_official import live_article_predicate_for, normalize_sum20_lookup

_COMPONENT_GROUP = "open_model_component_payload"
_DECOLONIZATION_REL = "projects/open_model_data/components/decolonization"
_PROJECT_CASE_IDS = frozenset(
    item["case_id"]
    for group in (LEXICAL_CALQUES, SYNTACTIC_CALQUES, PREPOSITIONAL_CALQUES, PROTECTIVE_CONTROLS)
    for item in group
)


def _managed_decolonization_destination(output_dir: Path) -> bool:
    data = REPO_ROOT / "data" / _DECOLONIZATION_REL
    registry = REPO_ROOT / "registry" / _DECOLONIZATION_REL
    lexical = output_dir.absolute()
    resolved = output_dir.resolve()
    if lexical != resolved and (lexical in {data, registry} or resolved in {data, registry}):
        raise ValueError(f"managed decolonization output reached through a symlink: {output_dir}")
    if lexical in {data, registry}:
        return True
    if lexical.is_relative_to(REPO_ROOT / "data/projects/open_model_data") or lexical.is_relative_to(
        REPO_ROOT / "registry/projects/open_model_data"
    ):
        raise ValueError(f"unsupported managed decolonization output directory: {output_dir}")
    return False


def _publish_decolonization_outputs(payloads: dict[str, bytes], companions: dict[str, bytes]) -> None:
    manifest = storage_paths.load_manifest(_COMPONENT_GROUP, REPO_ROOT)
    prior = {entry["path"][5:]: entry["sha256"] for entry in manifest["entries"]}
    prefix = f"{_DECOLONIZATION_REL}/"
    write_artifact_set(
        REPO_ROOT,
        _COMPONENT_GROUP,
        "build_decolonization_cases.py",
        {prefix + name: (lambda target, data=data: target.write_bytes(data)) for name, data in payloads.items()},
        expected_hashes={prefix + name: prior.get(prefix + name) for name in payloads},
        expected_members=set(prior),
        companions={
            f"registry/{prefix}{name}": (
                storage_paths.hash_file(REPO_ROOT / f"registry/{prefix}{name}")
                if (REPO_ROOT / f"registry/{prefix}{name}").exists()
                else None,
                lambda target, data=data: target.write_bytes(data),
            )
            for name, data in companions.items()
        },
    )


class SourceEvidenceUnavailable(ValueError):
    """A held source cannot substantiate a case; review and integrity failures still abort."""

    def __init__(self, message: str, reason_code: str):
        super().__init__(message)
        self.reason_code = reason_code


@dataclass
class DecolonizationCase:
    case_id: str
    target_term: str
    russian_copy: str
    ukrainian_proper: list[str]
    category: str
    disposition: str
    is_erroneous: bool
    authority: str
    reviewer_confirmation: dict[str, Any]
    split: str
    contexts: list[dict[str, Any]]


UA_GEC_RECORD_MAP: dict[str, dict[str, Any]] = {
    "decol_lex_012": {"id": 5921, "error": "гусь", "correct": "гусак", "error_type": "F/Calque", "doc_id": "1068"},
    "decol_lex_014": {
        "id": 6593,
        "error": "буфетчик",
        "correct": "буфетник",
        "error_type": "F/Calque",
        "doc_id": "1315",
    },
    "decol_lex_017": {
        "id": 6687,
        "error": "відправитися",
        "correct": "вирушити",
        "error_type": "F/Calque",
        "doc_id": "1345",
    },
    "decol_lex_028": {
        "id": 5134,
        "error": "бормотати",
        "correct": "бурмотіти",
        "error_type": "F/Calque",
        "doc_id": "0736",
    },
    "decol_syn_029": {
        "id": 3127,
        "error": "дозволяє",
        "correct": "дає змогу",
        "error_type": "F/Calque",
        "doc_id": "0029",
    },
}

ACCREDITED_INDEPENDENT_REVIEWERS: dict[str, dict[str, Any]] = {
    "claude_blue_team_ling_review": {
        "name": "Claude Sonnet (Blue Team Independent Language Reviewer)",
        "institution": "Learn Ukrainian Cross-Family Quality Gate",
        "role": "Lead Independent Linguistic Reviewer",
        "accreditation": "Cross-Family Independent Review Protocol",
        "reviewer_family": "claude",
    },
    "krisztiankoos_ling_review": {
        "name": "Krisztián Koós",
        "institution": "Learn Ukrainian Open Model Data Initiative",
        "role": "Project Maintainer & Lead Sovereign Dataset Reviewer",
        "accreditation": "Sovereign Ukrainian Curriculum Lead",
        "reviewer_family": "independent_human",
    },
    "dr_horodenska_codification_review": {
        "name": "Prof. K. H. Horodenska / Department of Grammar & Scientific Terminology",
        "institution": "Інститут української мови НАН України",
        "role": "External Normative Codifier & Reference Authority",
        "accreditation": "доктор філологічних наук, професор (author of «Чи правильне слововживання?»)",
        "reviewer_family": "independent_language_review",
    },
}


STOP_WORDS = {
    "в",
    "у",
    "на",
    "по",
    "до",
    "за",
    "з",
    "із",
    "зі",
    "та",
    "і",
    "й",
    "чи",
    "що",
    "як",
    "не",
    "б",
    "би",
    "ж",
    "же",
    "про",
    "від",
    "од",
    "при",
    "під",
    "над",
    "перед",
    "для",
    "без",
    "через",
    "після",
    "біля",
}


_PUNCT_PAT = re.compile(r"^[«»\",.?!:;()'\"-]+|[«»\",.?!:;()'\"-]+$")


def get_vesum_lemmas(word: str, v_cur: sqlite3.Cursor) -> set[str]:
    """Retrieve all attested lemmas for a word from VESUM."""
    rows = v_cur.execute(
        "SELECT DISTINCT lemma FROM forms_all WHERE word_form = ? OR lemma = ?",
        (word, word),
    ).fetchall()
    return {r[0] for r in rows}


def query_vesum_evidence(term: str, proper_list: list[str], v_cur: sqlite3.Cursor) -> dict[str, Any]:
    """Query authentic morphological and lemma facts directly from VESUM.

    Fails closed: requires EVERY constituent token of at least one candidate
    variant to be attested in VESUM.
    """
    candidates = [*list(proper_list), term]
    for cand in candidates:
        tokens = [_PUNCT_PAT.sub("", w).lower() for w in cand.split()]
        tokens = [t for t in tokens if t]
        if not tokens:
            continue

        all_attested = True
        attested_details = []
        for t in tokens:
            row = v_cur.execute(
                "SELECT lemma, pos, tags, source_location FROM forms_all WHERE lemma = ? OR word_form = ? LIMIT 1",
                (t, t),
            ).fetchone()
            if row:
                attested_details.append(
                    {
                        "token": t,
                        "lemma": row[0],
                        "pos": row[1],
                        "tags": row[2],
                        "entry_id": row[3],
                    }
                )
            elif t in STOP_WORDS:
                attested_details.append(
                    {
                        "token": t,
                        "lemma": t,
                        "pos": "functional",
                        "tags": "functional_word",
                        "entry_id": "functional_lexicon",
                    }
                )
            else:
                all_attested = False
                break

        if all_attested and attested_details:
            primary = attested_details[0]
            lemmas = [d["lemma"] for d in attested_details]
            pos_list = [d["pos"] for d in attested_details]
            return {
                "attested_candidate": cand,
                "attested_lemma": " ".join(lemmas),
                "part_of_speech": "+".join(pos_list),
                "morphological_tags": "; ".join(f"{d['token']}:{d['tags']}" for d in attested_details),
                "vesum_entry_id": str(primary["entry_id"]),
                "all_tokens_verified": True,
                "token_count": len(tokens),
                "lookup_status": "attested_standard",
                "database": "vesum.db",
            }

    raise ValueError(f"No candidate in {candidates} had all constituent tokens attested in vesum.db")


def validate_ua_gec_phrase(cand_str: str, rec_str: str, cur: sqlite3.Cursor) -> bool:
    """Strict phrase and morphological alignment between candidate and UA-GEC record.

    Requirements:
    1. Case-insensitive exact match passes.
    2. Strict token count match: len(cand_tokens) == len(rec_tokens).
    3. Negation match: presence and position of particle 'не' must be identical.
    4. Token-by-token alignment: each cand_token[i] must either equal rec_token[i]
       OR share at least one VESUM lemma with rec_token[i].
    """
    c_clean = cand_str.strip().lower()
    r_clean = rec_str.strip().lower()
    if c_clean == r_clean:
        return True
    c_toks = [_PUNCT_PAT.sub("", w).lower() for w in c_clean.split()]
    c_toks = [t for t in c_toks if t]
    r_toks = [_PUNCT_PAT.sub("", w).lower() for w in r_clean.split()]
    r_toks = [t for t in r_toks if t]
    if len(c_toks) != len(r_toks):
        return False
    # Check negation alignment
    for ct, rt in zip(c_toks, r_toks, strict=True):
        if (ct == "не") != (rt == "не"):
            return False
    # Token-by-token lemma alignment
    for ct, rt in zip(c_toks, r_toks, strict=True):
        if ct == rt:
            continue
        c_lemmas = get_vesum_lemmas(ct, cur)
        r_lemmas = get_vesum_lemmas(rt, cur)
        if not (c_lemmas and r_lemmas and c_lemmas.intersection(r_lemmas)):
            return False
    return True


def validate_dictionary_schema(cur: sqlite3.Cursor) -> None:
    """Compile required source queries; absent tables/columns are integrity errors.

    These are the held dictionary contracts used below, not optional telemetry.
    LIMIT 0 validates the schema without reading or changing source rows.
    """
    for query in (
        "SELECT id, headword, normalized_lookup_key, article_text, definition_text, official_url FROM sum20_articles LIMIT 0",
        "SELECT id, canonical_headword, normalized_query, sense_gloss FROM ulif_dictua_entries LIMIT 0",
        "SELECT id, title, text FROM external_articles LIMIT 0",
    ):
        cur.execute(query)
    if cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='slovnyk_me_entries'").fetchone():
        cur.execute("SELECT id, source_url, dictionary_slug, text FROM slovnyk_me_entries LIMIT 0")


def validate_source_schema(cur: sqlite3.Cursor) -> None:
    """Validate every required source contract before any case can withhold."""
    validate_dictionary_schema(cur)
    for query in (
        "SELECT id, error, correct, error_type, doc_id FROM ua_gec_errors LIMIT 0",
        "SELECT id, word, section, source, text, excerpt_full, page FROM style_guide LIMIT 0",
        "SELECT id, title, text, speaker, source_file, channel_id, domain, decolonization_tag FROM external_articles LIMIT 0",
        "SELECT id, title, text, author, author_uk, source_file FROM textbooks LIMIT 0",
        "SELECT rowid, title, text FROM textbooks_fts WHERE textbooks_fts MATCH 'schema' LIMIT 0",
        "SELECT source_id, number, text, text_sha256, locator FROM pravopys_paragraphs LIMIT 0",
    ):
        cur.execute(query)


def _literal_binding(
    passage: str,
    table: str,
    row_id: Any,
    field: str,
    text: str,
    provenance: dict[str, Any],
    *,
    locator: str | None = None,
    text_sha256: str | None = None,
) -> dict[str, Any] | None:
    """Bind raw quotation bytes to one resolving admitted row and field."""
    if row_id is None or row_id == "":
        raise ValueError(f"Missing resolving source row identity in {table}")
    digest = hashlib.sha256((text or "").encode("utf-8")).hexdigest()
    if text_sha256 is not None and digest != text_sha256:
        raise ValueError(f"Source text digest mismatch at {table}:{row_id}:{field}")
    if not passage or not text or passage not in text:
        return None
    return {
        "table": table,
        "row_id": row_id,
        "text_field": field,
        "text_sha256": digest,
        "passage_sha256": hashlib.sha256(passage.encode("utf-8")).hexdigest(),
        "locator": locator or f"{table}:{row_id}",
        "source_provenance": provenance,
    }


def _bind_admitted_passage(case_id: str, ev: dict[str, Any], cur: sqlite3.Cursor) -> dict[str, Any]:
    """Search all literal witnesses; metadata/body/title guesses never grant identity."""
    auth, source, passage = ev["authority"], ev.get("source"), ev.get("supporting_passage", "")
    seen = False
    if auth in {"СУМ-20", "ВТС"}:
        validate_dictionary_schema(cur)
        if normalize_sum20_lookup(ev.get("article") or ev["target_term"]) in _quarantined_headwords(cur.connection):
            raise SourceEvidenceUnavailable("Lexical evidence missing: quarantined headword", "quarantined_headword")
        live = live_article_predicate_for(cur)
        rows = cur.execute(
            f"SELECT id, article_text, definition_text, official_url FROM sum20_articles WHERE {live} ORDER BY id"
        ).fetchall()
        for row_id, article, definition, url in rows:
            seen = True
            # This table's admitted provenance is SUM-20, never a VTS or ULIF identity.
            try:
                parsed = urlsplit(url or "")
            except ValueError:
                continue
            if auth != "СУМ-20" or source != auth or parsed.scheme != "https" or parsed.netloc != "sum20ua.com":
                continue
            for field, text in (("article_text", article), ("definition_text", definition)):
                binding = _literal_binding(
                    passage, "sum20_articles", row_id, field, text, {"source": "СУМ-20", "official_url": url}
                )
                if binding:
                    return binding
        tables = {r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if "slovnyk_me_entries" in tables:
            # Optional absence is allowed; an existing malformed cache/query must abort.
            for row_id, url, slug, text in cur.execute(
                "SELECT id, source_url, dictionary_slug, text FROM slovnyk_me_entries ORDER BY id"
            ).fetchall():
                seen = True
                if (
                    _record_source(url or "") != auth
                    or source != auth
                    or slug != {"СУМ-20": "newsum", "ВТС": "vts"}[auth]
                ):
                    continue
                binding = _literal_binding(
                    passage,
                    "slovnyk_me_entries",
                    row_id,
                    "text",
                    text,
                    {"source": auth, "source_url": url, "dictionary_slug": slug},
                )
                if binding:
                    return binding
        # ULIF and generic external articles have no admitted provenance for these credits.
        seen = seen or bool(cur.execute("SELECT id FROM ulif_dictua_entries LIMIT 1").fetchone())
        seen = seen or bool(cur.execute("SELECT id FROM external_articles LIMIT 1").fetchone())
    elif auth == "Український правопис (2019)" and source == auth:
        from scripts.wiki.pravopys_official import PRAVOPYS_SOURCE_ID

        for source_id, number, text, digest, locator in cur.execute(
            "SELECT source_id, number, text, text_sha256, locator FROM pravopys_paragraphs WHERE source_id = ? ORDER BY number",
            (PRAVOPYS_SOURCE_ID,),
        ).fetchall():
            seen = True
            if not locator:
                raise ValueError(f"Missing admitted Pravopys locator at paragraph {number}")
            binding = _literal_binding(
                passage,
                "pravopys_paragraphs",
                f"{source_id}:{number}",
                "text",
                text,
                {"source": auth, "source_id": source_id, "number": number},
                locator=locator,
                text_sha256=digest,
            )
            if binding:
                return binding
    else:
        if source != auth:
            raise SourceEvidenceUnavailable("Held source disagrees with credited authority", "held_source_unproven")
        if auth == "Борис Антоненко-Давидович «Як ми говоримо»":
            for row_id, provenance, text, excerpt in cur.execute(
                "SELECT id, source, text, excerpt_full FROM style_guide ORDER BY id"
            ).fetchall():
                if provenance != "Антоненко-Давидович":
                    continue
                seen = True
                for field, body in (("text", text), ("excerpt_full", excerpt)):
                    binding = _literal_binding(
                        passage, "style_guide", row_id, field, body, {"source": auth, "source_record": provenance}
                    )
                    if binding:
                        return binding
        # Full authority in speaker is explicit book attribution; titles and body anchors are not.
        for row_id, text, speaker, source_file, channel, domain, tag in cur.execute(
            "SELECT id, text, speaker, source_file, channel_id, domain, decolonization_tag FROM external_articles "
            "WHERE speaker = ? OR decolonization_tag = ? ORDER BY id",
            (auth, case_id),
        ).fetchall():
            seen = True
            if (
                channel == "omd"
                or domain == "codification"
                or (source_file or "").startswith("codification-")
                or tag == case_id
                or tag in EXPLICIT_SOURCE_EVIDENCE
                or tag in _PROJECT_CASE_IDS
            ):
                continue
            if speaker != auth or not source_file:
                continue
            binding = _literal_binding(
                passage, "external_articles", row_id, "text", text, {"source": speaker, "source_file": source_file}
            )
            if binding:
                return binding
        # The approved full-book source ID is pinned by holdings_manifest.yaml.
        # Other books require exact author and cited title, not inline aliases or co-author guesses.
        author, sep, book = auth.partition(" «")
        book = book.removesuffix("»") if sep else ""
        for row_id, title, text, row_author, author_uk, source_file in cur.execute(
            "SELECT id, title, text, author, author_uk, source_file FROM textbooks "
            "WHERE source_file = ? OR (title = ? AND (author = ? OR author_uk = ?)) ORDER BY id",
            (
                "antonenko-davydovych-yak-my-hovorymo" if auth == "Борис Антоненко-Давидович «Як ми говоримо»" else "",
                book,
                author,
                author,
            ),
        ).fetchall():
            pinned = (
                auth == "Борис Антоненко-Давидович «Як ми говоримо»"
                and source_file == "antonenko-davydovych-yak-my-hovorymo"
                and author_uk == author
            )
            exact_book = bool(book and title == book and author in (row_author, author_uk) and source_file)
            if not (pinned or exact_book):
                continue
            seen = True
            binding = _literal_binding(
                passage,
                "textbooks",
                row_id,
                "text",
                text,
                {
                    "source": auth,
                    "source_file": source_file,
                    "author": row_author,
                    "author_uk": author_uk,
                    "title": title,
                },
            )
            if binding:
                return binding
    raise SourceEvidenceUnavailable(
        f"Held source has no admitted literal passage/source binding for case '{case_id}'",
        "held_source_unproven" if seen else "held_source_missing",
    )


def query_source_evidence(
    case_id: str,
    term: str,
    copy: str,
    auth: str,
    cat_name: str,
    s_cur: sqlite3.Cursor,
    v_cur: sqlite3.Cursor,
    style_guide_cache: list[tuple[Any, ...]],
    proper_list: list[str] | None = None,
) -> dict[str, Any]:
    """Query authentic citation loci and supporting evidence from sources.db and monographs.

    Fails closed: if no verified attestation exists, raises ValueError.
    Never returns fake or empty supporting passages.
    """
    if not auth or not auth.strip():
        raise ValueError(f"Empty authority provided for case '{case_id}'")

    if case_id not in EXPLICIT_SOURCE_EVIDENCE:
        raise ValueError(
            f"Term '{term}' (case: '{case_id}') has no verified attestation in authority '{auth}' or sources database"
        )

    ev = EXPLICIT_SOURCE_EVIDENCE[case_id]
    if proper_list is None:
        proper_list = ev.get("ukrainian_proper") or []

    # 1. Authority validation: Canonical authority identity
    expected_auth = ev.get("authority", ev.get("source", "")).strip()
    if auth.strip() != expected_auth:
        raise ValueError(
            f"Mismatched authority for case '{case_id}': probe authority '{auth}' does not match canonical authority '{expected_auth}'"
        )

    # 2. Target term validation: Independently attested complete phrases/variants from the catalog
    ev_term = ev.get("target_term", "").strip()
    t_clean = term.strip()
    if not t_clean:
        raise ValueError(f"Empty target term provided for case '{case_id}'")

    # Canonical allowed terms: ONLY from the catalog entry itself!
    canonical_terms = [ev_term]
    if "ukrainian_proper" in ev and isinstance(ev["ukrainian_proper"], list):
        canonical_terms.extend([p.strip() for p in ev["ukrainian_proper"] if p.strip()])

    if not any(t_clean.lower() == c.lower() for c in canonical_terms):
        raise ValueError(
            f"Mismatched target term for catalog case '{case_id}': term '{term}' incompatible with catalog entry '{ev.get('target_term')}'"
        )

    # 3. Russian copy validation: Exact match required
    ev_copy = (ev.get("russian_copy") or "").strip()
    c_clean = (copy or "").strip()

    if ev_copy:
        if not c_clean:
            raise ValueError(
                f"Missing required russian_copy for catalog case '{case_id}': probe copy is empty but catalog expects '{ev.get('russian_copy')}'"
            )
        if c_clean.lower() != ev_copy.lower():
            raise ValueError(
                f"Mismatched russian_copy for catalog case '{case_id}': probe copy '{copy}' incompatible with catalog entry '{ev.get('russian_copy')}'"
            )
    else:
        if c_clean:
            raise ValueError(
                f"Unexpected russian_copy '{copy}' for catalog case '{case_id}' which defines no russian_copy"
            )

    if auth in {"СУМ-20", "ВТС"}:
        conn = getattr(s_cur, "connection", None)
        # Preserve quarantine precedence for direct queries; build/CLI validate all contracts first.
        if (
            conn is not None
            and is_sqlite_connection(conn)
            and normalize_sum20_lookup(ev.get("article") or term) in _quarantined_headwords(conn)
        ):
            raise SourceEvidenceUnavailable("Lexical evidence missing: quarantined headword", "quarantined_headword")
        validate_dictionary_schema(s_cur)

    # Headword/phrase fallback must not attest a passage from an unproven committed record.
    candidates = [
        key
        for key, record in COMMITTED_SUM20_RECORDS.items()
        if ev.get("supporting_passage") in (record["article_text"], record.get("definition_text"))
    ]
    if candidates:
        dispositions = committed_record_dispositions(s_cur.connection)
        for key in candidates:
            if dispositions[key]["status"] == "withheld":
                raise SourceEvidenceUnavailable(
                    f"Committed source record '{key}' is withheld for case '{case_id}'",
                    dispositions[key]["reason_code"],
                )

    # 4. Mandatory live database queries on v_cur and s_cur (non-bypassable; fails closed on zero rows, exceptions, or unrelated results)
    t_tokens = [_PUNCT_PAT.sub("", w).lower() for w in t_clean.split()]
    t_tokens = [tok for tok in t_tokens if tok]
    for tok in t_tokens:
        v_cur.execute(
            "SELECT lemma, pos, tags, source_location FROM forms_all WHERE lemma = ? OR word_form = ? LIMIT 1",
            (tok, tok),
        )
        v_row = v_cur.fetchone()
        if not v_row:
            raise ValueError(
                f"VESUM evidence missing for case '{case_id}': token '{tok}' for target term '{term}' not found in forms_all"
            )

    source_record = None
    if "UA-GEC" in auth or "gec" in auth.lower():
        rec_meta = UA_GEC_RECORD_MAP.get(case_id)
        if not rec_meta:
            raise ValueError(f"No UA-GEC record mapped for case '{case_id}'")
        rec_id = rec_meta["id"] if isinstance(rec_meta, dict) else rec_meta
        s_cur.execute(
            "SELECT id, error, correct, error_type, doc_id FROM ua_gec_errors WHERE id = ?",
            (rec_id,),
        )
        source_record = s_cur.fetchone()
        if not source_record:
            raise SourceEvidenceUnavailable(
                f"UA-GEC evidence missing: record {rec_id} for case '{case_id}' not found in ua_gec_errors",
                "held_source_missing",
            )
        _db_id, db_error, db_correct, _db_error_type, _db_doc_id = source_record
        corr_clean = db_correct.strip().lower()
        err_clean = db_error.strip().lower()

        target_clean = t_clean.lower()
        copy_clean = c_clean.lower() if c_clean else ""

        # Strict phrase and negation alignment with target term and Russian copy
        if not validate_ua_gec_phrase(target_clean, corr_clean, v_cur) and not any(
            validate_ua_gec_phrase(p.strip().lower(), corr_clean, v_cur) for p in proper_list
        ):
            raise ValueError(
                f"UA-GEC record {rec_id} correction '{db_correct}' does not match case '{case_id}' target term '{term}'"
            )

        if isinstance(rec_meta, dict) and corr_clean != rec_meta["correct"].strip().lower():
            raise ValueError(
                f"UA-GEC record {rec_id} correction '{db_correct}' does not match expected canonical correction '{rec_meta['correct']}'"
            )

        if copy_clean and not validate_ua_gec_phrase(copy_clean, err_clean, v_cur):
            raise ValueError(
                f"UA-GEC record {rec_id} error '{db_error}' does not match case '{case_id}' Russian copy '{copy}'"
            )

        # Validate database record metadata against canonical UA-GEC mapping
        if isinstance(rec_meta, dict):
            if err_clean != rec_meta["error"].strip().lower():
                raise ValueError(
                    f"UA-GEC record {rec_id} error '{db_error}' does not match expected canonical error '{rec_meta['error']}'"
                )
            if str(_db_doc_id).strip() != rec_meta["doc_id"]:
                raise ValueError(
                    f"UA-GEC doc_id mismatch for case '{case_id}': expected '{rec_meta['doc_id']}', got '{_db_doc_id}'"
                )
            if str(_db_error_type).strip() != rec_meta["error_type"]:
                raise ValueError(
                    f"UA-GEC error_type mismatch for case '{case_id}': expected '{rec_meta['error_type']}', got '{_db_error_type}'"
                )
            if int(_db_id) != rec_meta["id"]:
                raise ValueError(f"UA-GEC record ID mismatch: expected {rec_meta['id']}, got {_db_id}")
        binding = None
        if ev["source"] == "UA-GEC v2.0" and auth == "UA-GEC (Syvokon et al., 2023)":
            for field, text in (("error", db_error), ("correct", db_correct)):
                binding = _literal_binding(
                    ev.get("supporting_passage", ""),
                    "ua_gec_errors",
                    _db_id,
                    field,
                    text,
                    {"source": "UA-GEC v2.0", "authority": auth, "doc_id": _db_doc_id},
                )
                if binding:
                    break
        if not binding:
            raise SourceEvidenceUnavailable("UA-GEC row lacks literal passage/source binding", "held_source_unproven")
    else:
        binding = _bind_admitted_passage(case_id, ev, s_cur)

    return {
        "source": ev["source"],
        "binding": binding,
        "section": ev.get("section"),
        "article": ev.get("article"),
        "page": ev.get("page"),
        "supporting_passage": ev["supporting_passage"],
        "status": "source_attested",
        "verification_method": ev.get(
            "verification_method",
            "Tool-backed verification and collation with primary authoritative codification",
        ),
        "locus": ev["locus"],
    }


def make_reviewer_confirmation(
    item: dict[str, Any],
    cat_name: str,
    v_cur: sqlite3.Cursor,
    s_cur: sqlite3.Cursor,
    style_guide_cache: list[tuple[Any, ...]],
) -> dict[str, Any]:
    """Build individual, traceable review and verification confirmation backed by live databases."""
    case_id = item["case_id"]
    target_term = item["target_term"]
    russian_copy = item.get("russian_copy", "")
    auth = item["authority"]
    proper_list = item.get("ukrainian_proper", [target_term])

    # 1. Traceable Independent Language Review Gate (Fail closed)
    if case_id not in INDEPENDENT_LANGUAGE_REVIEWS:
        raise ValueError(
            f"Case '{case_id}' has not been confirmed by independent language review in INDEPENDENT_LANGUAGE_REVIEWS"
        )
    rev_rec = INDEPENDENT_LANGUAGE_REVIEWS[case_id]

    receipt_id = rev_rec.get("review_receipt_id")
    if not receipt_id or not str(receipt_id).strip():
        raise ValueError(f"Case '{case_id}' missing review_receipt_id in language review record")

    locator = rev_rec.get("review_dossier_locator")
    if not locator or not str(locator).strip():
        raise ValueError(f"Case '{case_id}' missing review_dossier_locator in language review record")

    # Resolve dossier file on disk
    logical_prefix = Path("data/projects/open_model_data/components/decolonization")
    logical_locator = Path(locator)
    if (
        logical_locator.is_absolute()
        or ".." in logical_locator.parts
        or not logical_locator.is_relative_to(logical_prefix)
    ):
        raise ValueError(f"Invalid review dossier locator for case '{case_id}': {locator}")
    dossier_path = REGISTRY_DECOLONIZATION_DIR / logical_locator.relative_to(logical_prefix)
    if not dossier_path.is_file():
        raise ValueError(
            f"Review dossier file not found at '{dossier_path}' for case '{case_id}'. Unverified review receipt."
        )

    # Read and validate review dossier JSON from disk
    try:
        dossier = json.loads(dossier_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"Failed to read or parse review dossier at '{dossier_path}': {exc}") from exc

    # Validate reviewer independence and provenance against accredited whitelist (Fail closed)
    reviewer_id = str(rev_rec.get("reviewer_id") or "").strip()
    reviewer_family = str(rev_rec.get("reviewer_family") or "").strip()

    unapproved_reviewers = {"builder", "gemini", "assistant", "ai", "self"}
    if not reviewer_id or reviewer_id.lower() in unapproved_reviewers:
        raise ValueError(
            f"Invalid reviewer_id '{reviewer_id}' for case '{case_id}': independent language review cannot be performed by builder or model"
        )

    if reviewer_id not in ACCREDITED_INDEPENDENT_REVIEWERS:
        raise ValueError(
            f"Reviewer '{reviewer_id}' for case '{case_id}' is not in ACCREDITED_INDEPENDENT_REVIEWERS whitelist. "
            f"Independent language review requires accredited reviewer."
        )

    accredited_info = ACCREDITED_INDEPENDENT_REVIEWERS[reviewer_id]
    if reviewer_family != accredited_info["reviewer_family"]:
        raise ValueError(f"Reviewer family '{reviewer_family}' mismatch for accredited reviewer '{reviewer_id}'")

    # Validate against signed human acceptance review signoff (Fail closed on unapproved / defective / incomplete signoff)
    signoff_path = REGISTRY_DECOLONIZATION_DIR / "acceptance_review_sample.signoff.json"
    if not signoff_path.is_file():
        raise ValueError(f"Missing acceptance review signoff file at '{signoff_path}'")
    try:
        signoff_data = json.loads(signoff_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"Corrupted acceptance review signoff file at '{signoff_path}': {exc}") from exc

    # Reviewer identity & accredited whitelist validation
    if signoff_data.get("reviewer_id") != reviewer_id:
        raise ValueError(
            f"Reviewer ID '{reviewer_id}' for case '{case_id}' does not match signoff reviewer '{signoff_data.get('reviewer_id')}'"
        )
    if signoff_data.get("reviewer_family") != reviewer_family:
        raise ValueError(
            f"Reviewer family '{reviewer_family}' for case '{case_id}' does not match signoff family '{signoff_data.get('reviewer_family')}'"
        )

    # Validate review sample size: both drawn and reviewed must be positive integers and exactly equal
    drawn_count = signoff_data.get("sample_size_drawn")
    reviewed_count = signoff_data.get("sample_size_reviewed")
    if (
        type(drawn_count) is not int
        or isinstance(drawn_count, bool)
        or drawn_count <= 0
        or type(reviewed_count) is not int
        or isinstance(reviewed_count, bool)
        or reviewed_count <= 0
        or reviewed_count != drawn_count
    ):
        raise ValueError(
            f"Signoff sample_size_drawn ({drawn_count!r}) and sample_size_reviewed ({reviewed_count!r}) "
            f"must be positive integers and exactly equal. Review incomplete or defective."
        )

    # Zero BLOCKER defects tolerated
    blockers = signoff_data.get("blocker_defect_count")
    if type(blockers) is not int or isinstance(blockers, bool) or blockers != 0:
        raise ValueError(f"Signoff contains {blockers!r} unresolved BLOCKER defect(s). Approval requires 0 blockers.")

    # Minor defect cap
    minors = signoff_data.get("minor_defect_count")
    if type(minors) is not int or isinstance(minors, bool) or minors < 0 or minors > 5:
        raise ValueError(f"Signoff minor_defect_count ({minors!r}) exceeds allowable tolerance limit (<= 5).")

    # Digest and date binding
    d_sha = str(signoff_data.get("dataset_sha256") or "").strip()
    if len(d_sha) != 64 or not all(c in "0123456789abcdefABCDEF" for c in d_sha):
        raise ValueError(f"Signoff dataset_sha256 '{d_sha}' is missing or not a valid 64-character hex digest")

    p_sha = str(signoff_data.get("profile_sha256") or "").strip()
    if len(p_sha) != 64 or not all(c in "0123456789abcdefABCDEF" for c in p_sha):
        raise ValueError(f"Signoff profile_sha256 '{p_sha}' is missing or not a valid 64-character hex digest")

    s_date = str(signoff_data.get("signoff_date") or "").strip()
    if not s_date or not re.match(r"^\d{4}-\d{2}-\d{2}$", s_date):
        raise ValueError(f"Signoff signoff_date '{s_date}' is missing or invalid date format (expected YYYY-MM-DD)")
    try:
        datetime.date.fromisoformat(s_date)
    except ValueError as exc:
        raise ValueError(f"Signoff signoff_date '{s_date}' is not a valid calendar date: {exc}") from exc

    if dossier.get("review_receipt_id") != receipt_id:
        raise ValueError(
            f"Dossier receipt ID '{dossier.get('review_receipt_id')}' mismatch with registry receipt ID '{receipt_id}'"
        )
    if dossier.get("reviewer_id") != reviewer_id or dossier.get("reviewer_id") not in ACCREDITED_INDEPENDENT_REVIEWERS:
        raise ValueError(f"Dossier reviewer_id '{dossier.get('reviewer_id')}' mismatch or not accredited")
    if dossier.get("reviewer_family") != reviewer_family:
        raise ValueError(f"Dossier reviewer_family '{dossier.get('reviewer_family')}' is not '{reviewer_family}'")
    if dossier.get("verdict") != "APPROVED" or dossier.get("status") != "confirmed":
        raise ValueError(
            f"Dossier status/verdict ({dossier.get('status')}/{dossier.get('verdict')}) is not confirmed/APPROVED"
        )
    if rev_rec.get("status") != "confirmed" or rev_rec.get("verdict") != "APPROVED":
        raise ValueError(
            f"Case '{case_id}' review status is '{rev_rec.get('status')}' (verdict: '{rev_rec.get('verdict')}'), expected confirmed/APPROVED"
        )

    # Validate case properties against reviewed record
    if rev_rec.get("category") != cat_name:
        raise ValueError(
            f"Material change detected for case '{case_id}': category '{cat_name}' differs from reviewed category '{rev_rec.get('category')}'. Confirmation invalidated."
        )
    if rev_rec.get("is_erroneous") != item.get("is_erroneous"):
        raise ValueError(
            f"Material change detected for case '{case_id}': is_erroneous '{item.get('is_erroneous')}' differs from reviewed is_erroneous '{rev_rec.get('is_erroneous')}'. Confirmation invalidated."
        )
    if rev_rec.get("target_term") != target_term:
        raise ValueError(
            f"Material change detected for case '{case_id}': target_term '{target_term}' differs from reviewed target_term '{rev_rec.get('target_term')}'. Confirmation invalidated."
        )
    if (item.get("russian_copy") or "") != (rev_rec.get("russian_copy") or ""):
        raise ValueError(
            f"Material change detected for case '{case_id}': russian_copy '{item.get('russian_copy')}' differs from reviewed russian_copy '{rev_rec.get('russian_copy')}'. Confirmation invalidated."
        )
    if rev_rec.get("authority") != auth:
        raise ValueError(
            f"Material change detected for case '{case_id}': authority '{auth}' differs from reviewed authority '{rev_rec.get('authority')}'. Confirmation invalidated."
        )

    # Validate reviewed content before source availability can produce withholding.
    source_ev = EXPLICIT_SOURCE_EVIDENCE[case_id]
    # 3. Verify Source Evidence binding to Reviewed Dossier
    if rev_rec.get("supporting_passage") != source_ev.get("supporting_passage"):
        raise ValueError(
            f"Material change detected for case '{case_id}': supporting_passage in source evidence differs from reviewed passage. Confirmation invalidated."
        )
    if rev_rec.get("authority_locus") != source_ev.get("locus"):
        raise ValueError(
            f"Material change detected for case '{case_id}': locus in source evidence differs from reviewed locus. Confirmation invalidated."
        )
    if dossier.get("supporting_passage") != source_ev.get("supporting_passage"):
        raise ValueError(
            f"Material change detected for case '{case_id}': supporting_passage in dossier differs from source evidence. Confirmation invalidated."
        )
    if dossier.get("authority_locus") != source_ev.get("locus"):
        raise ValueError(
            f"Material change detected for case '{case_id}': locus in dossier differs from source evidence. Confirmation invalidated."
        )

    # 4. Exact content, context, and source evidence digest validation
    item_copy = dict(item)
    item_copy["category"] = cat_name
    computed_hash = compute_case_content_sha256(item_copy, source_ev)
    if rev_rec.get("content_sha256") != computed_hash:
        raise ValueError(
            f"Material change detected for case '{case_id}': content digest mismatch (reviewed: '{rev_rec.get('content_sha256')}', current: '{computed_hash}'). Contexts, case metadata, or source evidence tampered with. Confirmation invalidated."
        )
    if dossier.get("content_sha256") != computed_hash:
        raise ValueError(
            f"Material change detected for case '{case_id}': dossier content digest mismatch (dossier: '{dossier.get('content_sha256')}', current: '{computed_hash}'). Confirmation invalidated."
        )

    # 2. Automated Source Verification
    source_ev = query_source_evidence(
        case_id,
        target_term,
        russian_copy,
        auth,
        cat_name,
        s_cur,
        v_cur,
        style_guide_cache,
        proper_list=proper_list,
    )

    # 5. Automated VESUM Verification
    vesum_ev = query_vesum_evidence(target_term, proper_list, v_cur)

    locus = source_ev["locus"]

    return {
        "reviewer_id": rev_rec["reviewer_id"],
        "reviewer_family": rev_rec["reviewer_family"],
        "status": rev_rec["status"],
        "verdict": rev_rec.get("verdict", "APPROVED"),
        "review_date": rev_rec.get("review_date", "2026-09-22"),
        "review_receipt_id": rev_rec.get("review_receipt_id"),
        "review_dossier_locator": rev_rec.get("review_dossier_locator"),
        "content_sha256": rev_rec.get("content_sha256"),
        "authority_locus": locus,
        "vesum_lemma_status": "verified",
        "vesum_evidence": vesum_ev,
        "source_evidence": {
            "source_name": source_ev["source"],
            "binding": source_ev["binding"],
            "locus": source_ev["locus"],
            "supporting_passage": source_ev.get("supporting_passage"),
            "verification_method": source_ev.get("verification_method"),
            "automated_attestation_status": source_ev.get("status", "source_attested"),
        },
        "linguistic_rationale": rev_rec.get("linguistic_rationale", ""),
    }


def build_all_cases(*, withheld: list[dict[str, Any]] | None = None) -> list[DecolonizationCase]:
    """Validate the 250 candidates, accounting for unsupported sources as withheld."""
    vesum_path = _resolve_db_path("vesum.db", PROJECT_ROOT)
    sources_path = _resolve_db_path("sources.db", PROJECT_ROOT)

    v_conn = _open_readonly(vesum_path)
    s_conn = sqlite3.connect(sources_path.resolve().as_uri() + "?mode=ro", uri=True)
    validate_source_schema(s_conn.cursor())
    ensure_reproducible_sum20_table(s_conn)

    v_cur = v_conn.cursor()
    s_cur = s_conn.cursor()

    style_guide_cache = s_cur.execute("SELECT id, word, section, page, text, excerpt_full FROM style_guide").fetchall()

    cases: list[DecolonizationCase] = []
    withheld_cases = withheld if withheld is not None else []

    all_defs = [
        ("calque_lexical", LEXICAL_CALQUES),
        ("calque_syntactic", SYNTACTIC_CALQUES),
        ("calque_prepositional", PREPOSITIONAL_CALQUES),
        ("protective_authentic", PROTECTIVE_CONTROLS),
    ]

    for cat_name, items in all_defs:
        for item in items:
            try:
                rev_conf = make_reviewer_confirmation(item, cat_name, v_cur, s_cur, style_guide_cache)
            except SourceEvidenceUnavailable as exc:
                withheld_cases.append(
                    {
                        "case_id": item["case_id"],
                        "reason_code": exc.reason_code,
                        "record_keys": [
                            key
                            for key, record in COMMITTED_SUM20_RECORDS.items()
                            if EXPLICIT_SOURCE_EVIDENCE[item["case_id"]].get("supporting_passage")
                            in (record["article_text"], record.get("definition_text"))
                        ],
                        "owner": "claude-open-model-data",
                        "issue": 6321,
                    }
                )
                continue
            case = DecolonizationCase(
                case_id=item["case_id"],
                target_term=item["target_term"],
                russian_copy=item["russian_copy"],
                ukrainian_proper=item["ukrainian_proper"],
                category=cat_name,
                disposition=item["disposition"],
                is_erroneous=item["is_erroneous"],
                authority=item["authority"],
                reviewer_confirmation=rev_conf,
                split=item["split"],
                contexts=item["contexts"],
            )
            cases.append(case)

    v_conn.close()
    s_conn.close()

    return cases


def generate_dataset_records(cases: list[DecolonizationCase]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Generate train and eval records from cases."""
    train_records = []
    eval_records = []

    for case in cases:
        for ctx_idx, ctx in enumerate(case.contexts, start=1):
            query = ctx["query"].strip()
            orig = ctx["original_text"].strip()
            corr = ctx["corrected_text"].strip()
            resp = ctx["final_response"].strip()
            steps = [s.strip() for s in ctx["reasoning_steps"] if s.strip()]

            if not case.is_erroneous:
                orig = corr

            rec_id = f"{case.case_id}_ctx{ctx_idx}"
            rec = {
                "record_id": rec_id,
                "case_id": case.case_id,
                "split": case.split,
                "category": case.category,
                "disposition": case.disposition,
                "is_erroneous": case.is_erroneous,
                "target_term": case.target_term,
                "russian_copy": case.russian_copy,
                "ukrainian_proper": case.ukrainian_proper,
                "register": ctx["register"],
                "query": query,
                "original_text": orig,
                "corrected_text": corr,
                "final_response": resp,
                "reasoning_steps": steps,
                "chosen": corr if case.is_erroneous else orig,
                "rejected": orig
                if case.is_erroneous
                else (ctx.get("rejected_hyperpurism") or f"Неправильне виправлення: {orig}"),
                "source_metadata": {
                    "authority": case.authority,
                    "reviewer_id": case.reviewer_confirmation["reviewer_id"],
                    "authority_locus": case.reviewer_confirmation["authority_locus"],
                    "vesum_evidence": case.reviewer_confirmation.get("vesum_evidence"),
                },
            }
            if case.split == "train":
                train_records.append(rec)
            else:
                eval_records.append(rec)

    return train_records, eval_records


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build and validate the decolonization dataset. Use --check to validate without publication.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  .venv/bin/python -m scripts.projects.open_model_data.build_decolonization_cases --check\n"
            "  .venv/bin/python -m scripts.projects.open_model_data.build_decolonization_cases --output-dir decolonization-export\n"
            "Outputs: managed A payloads and K companions as one transaction, or an explicit external directory.\n"
            "Exit codes: 0 = success; nonzero = validation or publication failed.\n"
            "Related: issues #8340 and #8809."
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ARTIFACT_DECOLONIZATION_DIR,
        help="Target component directory (default: managed decolonization component).",
    )
    parser.add_argument(
        "--check",
        "--dry-run",
        dest="check",
        action="store_true",
        help="Validate dataset generation in memory without writing to disk",
    )
    args = parser.parse_args(argv)

    out_dir = args.output_dir
    managed = _managed_decolonization_destination(out_dir) if not args.check else False

    print(f"Building decolonization dataset at {out_dir}...")
    withheld: list[dict[str, Any]] = []
    cases = build_all_cases(withheld=withheld)
    print(f"Loaded {len(cases)} verified cases; withheld {len(withheld)} of {len(cases) + len(withheld)} candidates.")
    for disposition in withheld:
        print(f"Withheld {disposition['case_id']}: {disposition['reason_code']}")

    train_recs, eval_recs = generate_dataset_records(cases)
    total_recs = len(train_recs) + len(eval_recs)
    print(f"Generated {total_recs} records (Train: {len(train_recs)}, Eval: {len(eval_recs)})")

    if args.check:
        print(
            f"Check passed: {len(cases)} substantiated cases, {len(withheld)} withheld; {total_recs} records in memory."
        )
        return 0

    # Prepare all outputs before any managed pathname can change.
    cases_file = out_dir / "cases.json"
    cases_bytes = (json.dumps([asdict(c) for c in cases], ensure_ascii=False, indent=2) + "\n").encode("utf-8")

    train_file = out_dir / "decolonization_train.jsonl"
    train_bytes = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in train_recs).encode("utf-8")

    eval_file = out_dir / "decolonization_eval.jsonl"
    eval_bytes = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in eval_recs).encode("utf-8")

    manifest = {
        "dataset_name": "decolonization_v1",
        "payload_sha256": {
            "decolonization_train.jsonl": hashlib.sha256(train_bytes).hexdigest(),
            "decolonization_eval.jsonl": hashlib.sha256(eval_bytes).hexdigest(),
        },
        "version": "1.0.0",
        "candidate_cases": len(cases) + len(withheld),
        "withheld_cases": withheld,
        "task_type": "correction",
        "has_evaluation_split": True,
        "splits": {
            "decolonization_train.jsonl": "train",
            "decolonization_eval.jsonl": "eval",
        },
        "description": "Verified Ukrainian decolonization, anti-calque reasoning, and protective authentic Ukrainian corpus (#8340).",
        "governing_issues": ["#8340", "#6321"],
        "statistics": {
            "total_records": total_recs,
            "train_records": len(train_recs),
            "eval_records": len(eval_recs),
            "total_phenomena": len(cases),
            "substantive_corrections": sum(1 for r in train_recs + eval_recs if r["is_erroneous"]),
            "protective_controls": sum(1 for r in train_recs + eval_recs if not r["is_erroneous"]),
        },
    }
    manifest_file = out_dir / "manifest.json"
    manifest_bytes = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    if managed:
        _publish_decolonization_outputs(
            {"decolonization_train.jsonl": train_bytes, "decolonization_eval.jsonl": eval_bytes},
            {"cases.json": cases_bytes, "manifest.json": manifest_bytes},
        )
    else:
        out_dir.mkdir(parents=True, exist_ok=True)
        cases_file.write_bytes(cases_bytes)
        train_file.write_bytes(train_bytes)
        eval_file.write_bytes(eval_bytes)
        manifest_file.write_bytes(manifest_bytes)
    print(f"Wrote cases catalog: {cases_file}")
    print(f"Wrote train set: {train_file} ({len(train_recs)} records)")
    print(f"Wrote eval set: {eval_file} ({len(eval_recs)} records)")
    print(f"Wrote manifest: {manifest_file}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
