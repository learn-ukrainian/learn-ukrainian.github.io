#!/usr/bin/env python3
"""Phase 3 Cycle 007 evidence-sidecar compiler.

Builds one immutable, text-free-in-public evidence sidecar per packet by
running the frozen query plan from
``batch_state/phase3-cycle007-source-grounded-amendment-v1.md`` (step "Frozen
Sources MCP evidence layer") against every row's source-bearing text, using
the project's ``sources`` MCP at the reviewed local endpoint.

The compiler never calls a network service. ``LocalMcpSourcesClient`` only
ever reaches cached/local data (VESUM SQLite, ``sources.db`` FTS tables, and
the bounded ULIF/slovnyk.me cache tables audited by
``scripts/projects/open_model_data/evidence_cache_canaries.py``); anything
that would require a live HTTP call is deliberately left unimplemented and
reported as ``unavailable`` rather than fetched. Tests inject
``SourcesClient`` implementations that never touch a socket either.

Only counts, hashes, tool names, source versions, and pass/fail facts belong
in a printed or logged receipt (``public_manifest``/``compile_receipt``);
row text, extracted forms, and raw tool output belong only in the private
per-packet sidecar file.
"""

from __future__ import annotations

import os
import re
import sqlite3
import stat
import tempfile
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Protocol

from scripts.projects.open_model_data import phase3_cycle007_evidence_contract as contract

ROOT = Path(__file__).resolve().parents[3]
SIDECAR_SCHEMA_VERSION = "phase3_cycle007_evidence_sidecar_v1"
MANIFEST_SCHEMA_VERSION = "phase3_cycle007_evidence_manifest_v1"
EVALUATION_CYCLE_ID = "phase3-v2-1-evaluation-cycle-007"

PRIVATE_DIR_MODE = 0o700
PRIVATE_FILE_MODE = 0o600

DEFAULT_SOURCES_DB = ROOT / "data" / "sources.db"
DEFAULT_VESUM_DB = ROOT / "data" / "vesum.db"
DEFAULT_SERVER_CODE = ROOT / ".mcp" / "servers" / "sources" / "server.py"

ANTONENKO_SOURCE_FILE = "antonenko-davydovych-yak-my-hovorymo"

# --------------------------------------------------------------------------
# Frozen, versioned tokenizer (amendment step 2).
# --------------------------------------------------------------------------

TOKENIZER_ID = "phase3-cycle007-cyrillic-tokenizer-v1"
TOKENIZER_VERSION = "1"
COMPOUND_PARSER_ID = "phase3-cycle007-compound-splitter-v1"
COMPOUND_PARSER_VERSION = "1"

_UKRAINIAN_LETTERS = "А-ЩЬЮЯЄІЇҐа-щьюяєіїґ"
_TOKEN_RE = re.compile(
    rf"[{_UKRAINIAN_LETTERS}]+(?:['’ʼ-][{_UKRAINIAN_LETTERS}]+)*",
    re.UNICODE,
)


def extract_forms(text: str) -> list[str]:
    """Extract, lowercase, and deduplicate Cyrillic surface forms from text.

    Frozen tokenizer: ``TOKENIZER_ID``/``TOKENIZER_VERSION``. Never silently
    drops candidate forms — every match is returned; ambiguous decomposition
    is a separate, explicit compound-splitting step, not a tokenizer
    responsibility.
    """
    return sorted({match.group(0).lower() for match in _TOKEN_RE.finditer(text)})


def split_compound(form: str) -> list[str] | None:
    """Split a hyphenated compound into parts (versioned parser operation).

    Returns ``None`` when the form is not a supported hyphenated compound
    (i.e. it is a single token, or an internal apostrophe form the tokenizer
    already normalized) — a caller must treat ``None`` as "no decomposition
    available", never as "invalid form".
    """
    if "-" not in form:
        return None
    parts = [part for part in form.split("-") if part]
    if len(parts) < 2 or any(not _TOKEN_RE.fullmatch(part) for part in parts):
        return None
    return parts


# --------------------------------------------------------------------------
# Injectable Sources client protocol.
# --------------------------------------------------------------------------


class SourcesClient(Protocol):
    """The exact frozen query surface the compiler is allowed to use.

    Every method is synchronous and returns a plain, JSON-serializable
    structure (never MCP ``TextContent``) so the compiler can hash and
    interpret it uniformly whether it came from the real local adapter or a
    synthetic test double.
    """

    def server_identity(self) -> Mapping[str, Any]:
        """Return the frozen server/source-database identity for the manifest."""
        ...

    def verify_words(self, words: Sequence[str]) -> Mapping[str, list[Mapping[str, str]]]:
        """Batch VESUM check. Word -> list of ``{lemma, pos, tags}``; ``[]`` = miss."""
        ...

    def check_modern_form(self, word: str) -> Mapping[str, Any]:
        """``{found, is_modern_codified, has_archaic_form, has_only_archaic_form}``."""
        ...

    def ulif_cached(self, word: str) -> Mapping[str, Any]:
        """Cache-only ULIF escalation lookup. ``{status, payload}``, never live HTTP."""
        ...

    def slovnyk_me_cached(self, word: str) -> Mapping[str, Any]:
        """Cache-only slovnyk.me escalation lookup. ``{status, payload}``."""
        ...

    def grac_cached(self, word: str) -> Mapping[str, Any]:
        """Cache-only GRAC corpus-occurrence lookup. ``{status, payload}``."""
        ...

    def search_style_guide(self, query: str) -> Mapping[str, Any]:
        """Антоненко-Давидович structured index lookup. ``{status, hits}``."""
        ...

    def search_antonenko_text(self, query: str) -> Mapping[str, Any]:
        """``search_text`` scoped to ``source_file=antonenko-davydovych-yak-my-hovorymo``."""
        ...

    def search_ua_gec_errors(self, query: str) -> Mapping[str, Any]:
        """UA-GEC human error/correction pair search. ``{status, hits}``."""
        ...

    def search_heritage_cached(self, query: str) -> Mapping[str, Any]:
        """Cache-only heritage search (no live slovnyk.me escalation). ``{status, hits}``."""
        ...

    def check_russian_shadow(self, word: str) -> Mapping[str, Any]:
        """``{matches_russian, russian_lemma, confidence}`` — suspicion only."""
        ...


# --------------------------------------------------------------------------
# Production local-MCP adapter.
# --------------------------------------------------------------------------


class LocalMcpSourcesClientError(RuntimeError):
    """The local Sources MCP endpoint is unavailable or drifted."""


class LocalMcpSourcesClient:
    """Calls the exact reviewed local server's underlying library functions.

    This is "the local endpoint" in the same sense the MCP server itself
    is: it imports the identical ``scripts.verification.vesum`` and
    ``wiki.sources_db`` entry points ``.mcp/servers/sources/server.py``
    dispatches to, so a compiled evidence record is provably the same fact
    the live tool would have returned, without depending on the MCP stdio
    transport or the server's markdown text formatting (which is a display
    concern, not a fact). Every method that would otherwise require a live
    HTTP fetch (ULIF, slovnyk.me, GRAC) is instead answered from the local
    SQLite cache only; a cache miss is reported ``unavailable``, never
    fetched.
    """

    def __init__(
        self,
        *,
        sources_db: Path = DEFAULT_SOURCES_DB,
        vesum_db: Path = DEFAULT_VESUM_DB,
        server_code: Path = DEFAULT_SERVER_CODE,
    ) -> None:
        self._sources_db = sources_db
        self._vesum_db = vesum_db
        self._server_code = server_code
        for path, label in ((sources_db, "sources.db"), (vesum_db, "vesum.db"), (server_code, "server.py")):
            if not path.is_file():
                raise LocalMcpSourcesClientError(f"local sources endpoint unavailable: missing {label} at {path}")

    def _sources_conn(self) -> sqlite3.Connection:
        connection = sqlite3.connect(f"file:{self._sources_db}?mode=ro", uri=True)
        connection.row_factory = sqlite3.Row
        return connection

    def server_identity(self) -> Mapping[str, Any]:
        return {
            "server_code_sha256": contract.sha256_file(self._server_code),
            "sources_db_sha256": contract.sha256_file(self._sources_db),
            "sources_db_bytes": self._sources_db.stat().st_size,
            "vesum_db_sha256": contract.sha256_file(self._vesum_db),
            "vesum_db_bytes": self._vesum_db.stat().st_size,
        }

    def verify_words(self, words: Sequence[str]) -> Mapping[str, list[Mapping[str, str]]]:
        from scripts.verification.vesum import verify_words as _verify_words

        return _verify_words(list(words), db_path=self._vesum_db)

    def check_modern_form(self, word: str) -> Mapping[str, Any]:
        from scripts.verification.vesum import verify_word as _verify_word

        matches = _verify_word(word, db_path=self._vesum_db)
        if not matches:
            return {
                "found": False,
                "is_modern_codified": False,
                "has_archaic_form": False,
                "has_only_archaic_form": False,
            }
        has_archaic = any("arch" in str(match.get("tags") or "").split(":") for match in matches)
        has_modern = any("arch" not in str(match.get("tags") or "").split(":") for match in matches)
        return {
            "found": True,
            "is_modern_codified": has_modern,
            "has_archaic_form": has_archaic,
            "has_only_archaic_form": has_archaic and not has_modern,
        }

    def _cache_table_lookup(
        self,
        *,
        table: str,
        required_columns: Sequence[str],
        query_column: str,
        word: str,
    ) -> Mapping[str, Any]:
        try:
            with self._sources_conn() as connection:
                tables = {
                    str(row[0]) for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")
                }
                if table not in tables:
                    return {"status": "unavailable", "payload": None}
                columns = {str(row[1]) for row in connection.execute(f"PRAGMA table_info({table})")}
                if not set(required_columns) <= columns:
                    return {"status": "unavailable", "payload": None}
                # table/query_column are frozen constants passed by this module's own
                # callers, never user input.
                row = connection.execute(
                    f"SELECT * FROM {table} WHERE {query_column} = ? LIMIT 1",
                    (word,),
                ).fetchone()
        except sqlite3.Error:
            return {"status": "unavailable", "payload": None}
        if row is None:
            return {"status": "not_found", "payload": None}
        return {"status": "attested", "payload": dict(row)}

    def ulif_cached(self, word: str) -> Mapping[str, Any]:
        # ulif_dictua_entries schema per evidence_cache_canaries.py; a cache
        # miss (or absent table) is "unavailable" — never a live HTTP call.
        result = self._cache_table_lookup(
            table="ulif_dictua_entries",
            required_columns=("normalized_query", "canonical_headword", "status"),
            query_column="normalized_query",
            word=word,
        )
        if result["status"] == "attested" and str(result["payload"].get("status")) != "ok":
            return {"status": "not_found", "payload": result["payload"]}
        return result

    def slovnyk_me_cached(self, word: str) -> Mapping[str, Any]:
        result = self._cache_table_lookup(
            table="slovnyk_me_entries",
            required_columns=("dictionary_identity", "locator"),
            query_column="headword",
            word=word,
        )
        payload = result.get("payload")
        if result["status"] == "attested" and (not payload or not str(payload.get("dictionary_identity") or "")):
            # Aggregator-only rows (no named dictionary) cannot strengthen evidence.
            return {"status": "not_found", "payload": payload}
        return result

    def grac_cached(self, word: str) -> Mapping[str, Any]:
        # No corpus-frequency cache table is ingested into sources.db today;
        # GRAC is a live-only tool (scripts/rag/source_query.py). Fail closed
        # to "unavailable" rather than making the disallowed network call.
        return self._cache_table_lookup(
            table="grac_frequency_cache",
            required_columns=("word", "freq"),
            query_column="word",
            word=word,
        )

    def search_style_guide(self, query: str) -> Mapping[str, Any]:
        from wiki.sources_db import search_style_guide as _search

        hits = _search(query, db_path=self._sources_db)
        return {"status": "attested" if hits else "not_found", "hits": hits}

    def search_antonenko_text(self, query: str) -> Mapping[str, Any]:
        from wiki.sources_db import search_textbooks as _search

        keywords = {word for word in query.lower().split() if len(word) >= 3}
        hits = _search(keywords, 5, source_file=ANTONENKO_SOURCE_FILE)
        return {"status": "attested" if hits else "not_found", "hits": hits}

    def search_ua_gec_errors(self, query: str) -> Mapping[str, Any]:
        from wiki.sources_db import search_ua_gec_errors as _search

        hits = _search(query, db_path=self._sources_db)
        return {"status": "attested" if hits else "not_found", "hits": hits}

    def search_heritage_cached(self, query: str) -> Mapping[str, Any]:
        from wiki.sources_db import search_heritage as _search

        # include_live_slovnyk defaults to False; pass it explicitly so a
        # future default flip can never silently re-enable network fallback.
        hits = _search(query, 10, include_live_slovnyk=False, db_path=self._sources_db)
        return {"status": "attested" if hits else "not_found", "hits": hits}

    def check_russian_shadow(self, word: str) -> Mapping[str, Any]:
        from scripts.verification.check_ru_morph import is_russian_pattern

        return is_russian_pattern(word, vesum_db_path=self._vesum_db)


# --------------------------------------------------------------------------
# Per-row evidence compilation.
# --------------------------------------------------------------------------


def _evidence(
    *,
    client_result_status: str,
    channel: str,
    positive_supports: str,
    source_identity: str,
    source_version: str,
    locator: str,
    query: str,
    retrieval_payload: Any,
    parser_id: str,
    parser_version: str,
    row: Mapping[str, Any],
    phenomenon_id: str | None,
    negative_reason: str | None,
) -> dict[str, Any]:
    status = client_result_status
    supports = positive_supports if status == "attested" else "no_conclusion"
    return contract.build_evidence_record(
        channel=channel,
        source_identity=source_identity,
        source_version=source_version,
        locator=locator,
        query=query,
        query_sha256=contract.sha256_text(query),
        status=status,
        supports=supports,
        retrieval_sha256=contract.sha256_value(retrieval_payload),
        parser_id=parser_id,
        parser_version=parser_version,
        row=row,
        phenomenon_id=phenomenon_id,
        negative_reason=None if status == "attested" else (negative_reason or status),
    )


def _vesum_form_evidence(
    form: str,
    *,
    verify_result: list[Mapping[str, str]] | None,
    modern_result: Mapping[str, Any],
    row: Mapping[str, Any],
    source_version: str,
) -> dict[str, Any]:
    found = bool(verify_result) or bool(modern_result.get("found"))
    if not found:
        return _evidence(
            client_result_status="not_found",
            channel="vesum_attestation",
            positive_supports="attestation",
            source_identity="vesum",
            source_version=source_version,
            locator="data/vesum.db#forms",
            query=form,
            retrieval_payload={"verify_words": verify_result, "check_modern_form": modern_result},
            parser_id="vesum-forms-v1",
            parser_version="1",
            row=row,
            phenomenon_id=None,
            negative_reason="vesum_miss",
        )
    has_only_archaic = bool(modern_result.get("has_only_archaic_form"))
    return _evidence(
        client_result_status="attested",
        channel="vesum_attestation",
        positive_supports="archaic_attestation" if has_only_archaic else "attestation",
        source_identity="vesum",
        source_version=source_version,
        locator="data/vesum.db#forms",
        query=form,
        retrieval_payload={"verify_words": verify_result, "check_modern_form": modern_result},
        parser_id="vesum-forms-v1",
        parser_version="1",
        row=row,
        phenomenon_id=None,
        negative_reason=None,
    )


def _escalation_evidence(
    form: str,
    *,
    client: SourcesClient,
    row: Mapping[str, Any],
    source_version: str,
) -> list[dict[str, Any]]:
    """VESUM-miss escalation: ULIF, cached slovnyk.me, cached GRAC corpus attestation.

    A miss here is never condemnation — every result stays a distinct,
    explicit, negative-or-positive evidence record.
    """
    records = []
    ulif = client.ulif_cached(form)
    records.append(
        _evidence(
            client_result_status=ulif["status"],
            channel="vesum_attestation",
            positive_supports="attestation",
            source_identity="ulif",
            source_version=source_version,
            locator="https://lcorp.ulif.org.ua/dictua",
            query=form,
            retrieval_payload=ulif,
            parser_id="ulif-cache-v1",
            parser_version="1",
            row=row,
            phenomenon_id=None,
            negative_reason="ulif_cache_" + ulif["status"],
        )
    )
    slovnyk = client.slovnyk_me_cached(form)
    records.append(
        _evidence(
            client_result_status=slovnyk["status"],
            channel="vesum_attestation",
            positive_supports="attestation",
            source_identity="slovnyk_me",
            source_version=source_version,
            locator="https://slovnyk.me",
            query=form,
            retrieval_payload=slovnyk,
            parser_id="slovnyk-me-cache-v1",
            parser_version="1",
            row=row,
            phenomenon_id=None,
            negative_reason="slovnyk_me_cache_" + slovnyk["status"],
        )
    )
    grac = client.grac_cached(form)
    records.append(
        _evidence(
            client_result_status=grac["status"],
            channel="ukrainian_corpus_occurrence",
            positive_supports="occurrence",
            source_identity="grac",
            source_version=source_version,
            locator="https://sketch.uacorpus.org/bonito/run.cgi",
            query=form,
            retrieval_payload=grac,
            parser_id="grac-cache-v1",
            parser_version="1",
            row=row,
            phenomenon_id=None,
            negative_reason="grac_cache_" + grac["status"],
        )
    )
    return records


def compile_row_evidence(
    row: Mapping[str, Any],
    client: SourcesClient,
    *,
    source_version: str,
) -> dict[str, Any]:
    """Compile the complete evidence set for one row.

    Runs the always-on per-row channels (Antonenko style/text, UA-GEC,
    heritage, Russian-shadow) plus the per-extracted-form VESUM batch/
    escalation channels, and a single source_metadata record preserving the
    row's existing provenance without printing it.
    """
    source_text = str(row.get("source_text", ""))
    forms = extract_forms(source_text)
    evidence: list[dict[str, Any]] = []

    # source_metadata: preserve existing provenance, hashed, never printed.
    frozen_locator_sha256 = str(row.get("frozen_locator_sha256") or contract.sha256_text(""))
    source_text_sha256 = str(row.get("source_text_sha256") or contract.sha256_text(source_text))
    evidence.append(
        contract.build_evidence_record(
            channel="source_metadata",
            source_identity=str(row.get("family_id") or "unknown"),
            source_version=source_version,
            locator=f"phase3-cycle007-row:{row.get('unit_id')}",
            query=None,
            query_sha256=frozen_locator_sha256,
            status="attested",
            supports="metadata_only",
            retrieval_sha256=source_text_sha256,
            parser_id="phase3-cycle007-row-provenance-v1",
            parser_version="1",
            row=row,
            phenomenon_id=None,
        )
    )

    # VESUM batch + check_modern_form for every extracted form, regardless of
    # the batch result (amendment step 3).
    verify_batch = client.verify_words(forms) if forms else {}
    for form in forms:
        modern = client.check_modern_form(form)
        evidence.append(
            _vesum_form_evidence(
                form,
                verify_result=verify_batch.get(form, []),
                modern_result=modern,
                row=row,
                source_version=source_version,
            )
        )
        miss = not (verify_batch.get(form) or modern.get("found"))
        if miss:
            # Split supported compounds first; ambiguous/unresolved
            # decomposition never silently drops or invents evidence.
            parts = split_compound(form)
            if parts:
                part_batch = client.verify_words(parts)
                for part in parts:
                    part_modern = client.check_modern_form(part)
                    evidence.append(
                        _vesum_form_evidence(
                            part,
                            verify_result=part_batch.get(part, []),
                            modern_result=part_modern,
                            row=row,
                            source_version=source_version,
                        )
                    )
            evidence.extend(_escalation_evidence(form, client=client, row=row, source_version=source_version))

    # Always-on per-row parallel path (amendment step 5): style guide, the
    # structured Антоненко-Давидович index, its prose surface, UA-GEC, and
    # heritage. Runs even when the row has no extractable Cyrillic forms so
    # every row carries these channels.
    row_query = source_text if source_text.strip() else str(row.get("unit_id", ""))
    style = client.search_style_guide(row_query)
    evidence.append(
        _evidence(
            client_result_status=style["status"],
            channel="antonenko_style",
            positive_supports="style_guidance",
            source_identity="antonenko-davydovych-style-guide-index",
            source_version=source_version,
            locator="repo:data/sources.db#style_guide",
            query=row_query,
            retrieval_payload=style,
            parser_id="antonenko-style-index-v1",
            parser_version="1",
            row=row,
            phenomenon_id=None,
            negative_reason="style_guide_" + style["status"],
        )
    )
    antonenko_text = client.search_antonenko_text(row_query)
    evidence.append(
        _evidence(
            client_result_status=antonenko_text["status"],
            channel="antonenko_style",
            positive_supports="style_guidance",
            source_identity=ANTONENKO_SOURCE_FILE,
            source_version=source_version,
            locator=f"repo:data/sources.db#textbooks:{ANTONENKO_SOURCE_FILE}",
            query=row_query,
            retrieval_payload=antonenko_text,
            parser_id="antonenko-prose-search-v1",
            parser_version="1",
            row=row,
            phenomenon_id=None,
            negative_reason="antonenko_text_" + antonenko_text["status"],
        )
    )
    ua_gec = client.search_ua_gec_errors(row_query)
    evidence.append(
        _evidence(
            client_result_status=ua_gec["status"],
            channel="ua_gec_calque",
            positive_supports="calque_flag",
            source_identity="ua-gec",
            source_version=source_version,
            locator="repo:data/sources.db#ua_gec",
            query=row_query,
            retrieval_payload=ua_gec,
            parser_id="ua-gec-search-v1",
            parser_version="1",
            row=row,
            phenomenon_id=None,
            negative_reason="ua_gec_" + ua_gec["status"],
        )
    )
    heritage = client.search_heritage_cached(row_query)
    evidence.append(
        _evidence(
            client_result_status=heritage["status"],
            channel="heritage_attestation",
            positive_supports="attestation",
            source_identity="heritage-cache",
            source_version=source_version,
            locator="repo:data/sources.db#heritage",
            query=row_query,
            retrieval_payload=heritage,
            parser_id="heritage-cache-search-v1",
            parser_version="1",
            row=row,
            phenomenon_id=None,
            negative_reason="heritage_" + heritage["status"],
        )
    )

    # Russian-shadow suspicion: per extracted form (or the row identity when
    # there is nothing to tokenize), suspicion-only, never authoritative.
    shadow_targets = forms or [row_query]
    for target in shadow_targets:
        shadow = client.check_russian_shadow(target)
        matches = bool(shadow.get("matches_russian"))
        evidence.append(
            _evidence(
                client_result_status="attested" if matches else "not_found",
                channel="russian_shadow_suspicion",
                positive_supports="suspicion",
                source_identity="check_ru_morph",
                source_version=source_version,
                locator="repo:scripts/verification/check_ru_morph.py",
                query=target,
                retrieval_payload=shadow,
                parser_id="russian-shadow-heuristic-v1",
                parser_version="1",
                row=row,
                phenomenon_id=None,
                negative_reason="russian_shadow_not_suspected" if not matches else None,
            )
        )

    evidence_ids = sorted({str(record["evidence_id"]) for record in evidence})
    phenomenon_evidence_ids: dict[str, list[str]] = {}
    for record in evidence:
        phenomenon_id = record.get("phenomenon_id")
        if phenomenon_id:
            phenomenon_evidence_ids.setdefault(str(phenomenon_id), []).append(str(record["evidence_id"]))
    phenomenon_evidence_ids = {key: sorted(set(value)) for key, value in phenomenon_evidence_ids.items()}

    return {
        "unit_id": row["unit_id"],
        "unit_sha256": row["unit_sha256"],
        "tokenizer_id": TOKENIZER_ID,
        "tokenizer_version": TOKENIZER_VERSION,
        "extracted_forms": forms,
        "evidence": evidence,
        "evidence_ids": evidence_ids,
        "phenomenon_evidence_ids": phenomenon_evidence_ids,
        "sufficient_support": any(contract.is_sufficient_positive(record) for record in evidence),
        "archaic_only_risk": contract.is_archaic_only_risk(evidence),
        "russian_shadow_suspected": any(
            record["channel"] == "russian_shadow_suspicion" and record["status"] == "attested" for record in evidence
        ),
    }


# --------------------------------------------------------------------------
# Pravopys 2026/2019 binding — explicit, phenomenon-scoped, never blanket.
# --------------------------------------------------------------------------

PRAVOPYS_2026_PDF_SHA256 = "e593956bfba6737d991a76fa86970db9c10a5cd7fd8895bae67f2b9a950c3a92"
PRAVOPYS_2026_CONTEXT_RECEIPT_SHA256 = "5da6f60e1cf5527fd98e44b4396472d871d359cd6b9dc76e3806c73a15c2b827"
DEFAULT_PRAVOPYS_CONTEXT_RECEIPT = (
    ROOT / "data/projects/open_model_data/inventory/phase3_pravopys_evaluation_context_receipt_v1.json"
)


def bind_pravopys_2026_evidence(
    row: Mapping[str, Any],
    phenomenon_id: str,
    *,
    context_receipt_path: Path = DEFAULT_PRAVOPYS_CONTEXT_RECEIPT,
) -> dict[str, Any]:
    """Bind the frozen Pravopys 2026 normative fact to one residual phenomenon.

    This is deliberately not a per-row/per-form query: within this frozen
    Phase 3 evaluation the 2026 edition is bound by explicit task-specific
    identity (PDF + context-receipt SHA-256), not fetched live — the general
    Sources MCP ``query_pravopys`` tool only exposes 2019 and is
    comparison-only here.
    """
    contract.require(bool(phenomenon_id), "pravopys_2026_normative evidence requires a phenomenon_id")
    receipt_sha256 = contract.sha256_file(context_receipt_path) if context_receipt_path.is_file() else None
    status = "attested" if receipt_sha256 == PRAVOPYS_2026_CONTEXT_RECEIPT_SHA256 else "unavailable"
    return contract.build_evidence_record(
        channel="pravopys_2026_normative",
        source_identity="pravopys-2026-official-edition",
        source_version=PRAVOPYS_2026_PDF_SHA256,
        locator=(
            str(context_receipt_path.relative_to(ROOT))
            if context_receipt_path.is_absolute() and context_receipt_path.is_relative_to(ROOT)
            else str(context_receipt_path)
        ),
        query=None,
        query_sha256=contract.sha256_text(PRAVOPYS_2026_PDF_SHA256),
        status=status,
        supports="normative_rule" if status == "attested" else "no_conclusion",
        retrieval_sha256=receipt_sha256 or contract.sha256_text("unavailable"),
        parser_id="pravopys-2026-frozen-binding-v1",
        parser_version="1",
        row=row,
        phenomenon_id=phenomenon_id,
        negative_reason=None if status == "attested" else "pravopys_2026_context_receipt_hash_mismatch",
    )


def bind_pravopys_2019_comparison_evidence(
    row: Mapping[str, Any],
    phenomenon_id: str,
    client: SourcesClient,
    *,
    query: str,
) -> dict[str, Any]:
    """Bind a comparison-only 2019 Pravopys result to one residual phenomenon.

    ``query_pravopys`` is explicitly comparison-only in this evaluation: its
    result can never carry ``normative_rule`` support (enforced by the
    closed per-channel claim boundary in the contract module).
    """
    contract.require(bool(phenomenon_id), "pravopys_2019_comparison evidence requires a phenomenon_id")
    result = client.search_style_guide(query) if hasattr(client, "search_style_guide") else {"status": "unavailable"}
    return contract.build_evidence_record(
        channel="pravopys_2019_comparison",
        source_identity="pravopys-2019-comparison",
        source_version="2019.pravopys.net",
        locator="https://2019.pravopys.net",
        query=query,
        query_sha256=contract.sha256_text(query),
        status=result["status"],
        supports="comparison_only" if result["status"] == "attested" else "no_conclusion",
        retrieval_sha256=contract.sha256_value(result),
        parser_id="pravopys-2019-comparison-v1",
        parser_version="1",
        row=row,
        phenomenon_id=phenomenon_id,
        negative_reason=None if result["status"] == "attested" else "pravopys_2019_" + result["status"],
    )


# --------------------------------------------------------------------------
# Packet-level sidecar assembly and atomic private write.
# --------------------------------------------------------------------------


def compile_packet_sidecar(
    packet_index: int,
    rows: Sequence[Mapping[str, Any]],
    client: SourcesClient,
    *,
    source_version: str = "cycle007-foundation-v1",
) -> dict[str, Any]:
    row_records = [compile_row_evidence(row, client, source_version=source_version) for row in rows]
    identity = client.server_identity()
    body = {
        "schema_version": SIDECAR_SCHEMA_VERSION,
        "evaluation_cycle_id": EVALUATION_CYCLE_ID,
        "packet_index": packet_index,
        "row_count": len(rows),
        "tokenizer_id": TOKENIZER_ID,
        "tokenizer_version": TOKENIZER_VERSION,
        "server_code_sha256": identity["server_code_sha256"],
        "sources_db_sha256": identity["sources_db_sha256"],
        "vesum_db_sha256": identity["vesum_db_sha256"],
        "network_lookups_performed": 0,
        "rows": row_records,
    }
    body["sidecar_id"] = "cycle007_sidecar:" + contract.sha256_value(body)
    return body


def _atomic_write_private(path: Path, payload: bytes) -> str:
    path.parent.mkdir(parents=True, exist_ok=True, mode=PRIVATE_DIR_MODE)
    os.chmod(path.parent, PRIVATE_DIR_MODE)
    if path.exists() or path.is_symlink():
        raise contract.EvidenceContractError(f"refusing to overwrite existing sidecar: {path}")
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            os.fchmod(handle.fileno(), PRIVATE_FILE_MODE)
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    return contract.sha256_bytes(payload)


def compile_sidecar_bundle(
    packets: Sequence[Sequence[Mapping[str, Any]]],
    client: SourcesClient,
    output_dir: Path,
    *,
    source_version: str = "cycle007-foundation-v1",
) -> dict[str, Any]:
    """Compile and atomically write one sidecar per packet, plus a public manifest."""
    output_dir.mkdir(parents=True, exist_ok=True, mode=PRIVATE_DIR_MODE)
    os.chmod(output_dir, PRIVATE_DIR_MODE)
    identity = client.server_identity()
    channel_counts: Counter[str] = Counter()
    status_counts: Counter[str] = Counter()
    supports_counts: Counter[str] = Counter()
    sufficient_support_rows = 0
    archaic_only_risk_rows = 0
    russian_shadow_suspected_rows = 0
    row_count = 0
    sidecar_index: list[dict[str, Any]] = []
    for packet_index, rows in enumerate(packets, start=1):
        sidecar = compile_packet_sidecar(packet_index, rows, client, source_version=source_version)
        payload = (contract.canonical_json(sidecar) + "\n").encode("utf-8")
        sidecar_path = output_dir / f"sidecar-{packet_index:04d}.json"
        sidecar_sha256 = _atomic_write_private(sidecar_path, payload)
        for row_record in sidecar["rows"]:
            row_count += 1
            sufficient_support_rows += int(row_record["sufficient_support"])
            archaic_only_risk_rows += int(row_record["archaic_only_risk"])
            russian_shadow_suspected_rows += int(row_record["russian_shadow_suspected"])
            for evidence_record in row_record["evidence"]:
                channel_counts[evidence_record["channel"]] += 1
                status_counts[evidence_record["status"]] += 1
                supports_counts[evidence_record["supports"]] += 1
        sidecar_index.append(
            {
                "packet_index": packet_index,
                "row_count": len(rows),
                "sidecar_sha256": sidecar_sha256,
            }
        )
    manifest = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "text_free": True,
        "evaluation_cycle_id": EVALUATION_CYCLE_ID,
        "tokenizer_id": TOKENIZER_ID,
        "tokenizer_version": TOKENIZER_VERSION,
        "server_code_sha256": identity["server_code_sha256"],
        "sources_db_sha256": identity["sources_db_sha256"],
        "vesum_db_sha256": identity["vesum_db_sha256"],
        "packet_count": len(packets),
        "row_count": row_count,
        "network_lookups_performed": 0,
        "counts_by_channel": dict(sorted(channel_counts.items())),
        "counts_by_status": dict(sorted(status_counts.items())),
        "counts_by_supports": dict(sorted(supports_counts.items())),
        "sufficient_support_rows": sufficient_support_rows,
        "archaic_only_risk_rows": archaic_only_risk_rows,
        "russian_shadow_suspected_rows": russian_shadow_suspected_rows,
        "sidecars": sidecar_index,
    }
    manifest["manifest_sha256"] = contract.sha256_value(manifest)
    manifest_bytes = (contract.canonical_json(manifest) + "\n").encode("utf-8")
    _atomic_write_private(output_dir / "manifest.json", manifest_bytes)
    for path in (output_dir, *output_dir.iterdir()):
        mode = stat.S_IMODE(path.stat().st_mode)
        expected = PRIVATE_DIR_MODE if path.is_dir() else PRIVATE_FILE_MODE
        contract.require(mode == expected, f"sidecar output permission drift: {path}")
    return manifest
