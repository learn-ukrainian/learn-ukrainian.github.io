"""Read-only source access for pilot word-card assembly (#8981).

Everything here reads the frozen pilot inputs and the held `sources.db` / `vesum.db` / ULIF raw-response cache
without writing to them. Four jobs: row access that records the digest of every row and query result a build
consumes, authentication of the derived `ulif_forms` rows against the held raw paradigm page, the ULIF paradigm
model (slot keys, withholding classes) and the VESUM↔ULIF identity match of `docs/atlas/word-cards/identity.md` §4.

No Ukrainian text is produced here: every returned string is a verbatim source value.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import unicodedata
from collections import defaultdict
from contextlib import closing
from os import environ
from pathlib import Path

from scripts.atlas import word_card_foundation as foundation
from scripts.lexicon import sum20_store, ulif_raw_cache
from scripts.lexicon.runner import ulif_dictua_parse
from scripts.lib.readonly_sqlite import SQLiteConnection
from scripts.wiki.sources_db import compute_ulif_entry_fingerprint

ACUTE = "́"
CASES = ("v_naz", "v_rod", "v_dav", "v_zna", "v_oru", "v_mis", "v_kly")
GENDERS = ("m", "f", "n")
TENSES = ("inf", "pres", "futr", "past", "impr")
PERSONS = ("1", "2", "3")
# Canonical slot order: tense, case, number, gender, person.
SLOT_VOCABULARY = frozenset(CASES + GENDERS + TENSES + PERSONS + ("s", "p"))
HIDDEN_MARKERS = ("bad", "obsc", "subst")
# VESUM tag tokens that mark an entry flag (proper name, abbreviation, register/variant marking).
VARIANT_TAGS = frozenset({"var", "arch", "rare", "long", "short", "slang", "vulg", "bad", "obsc", "subst", "ranim", "rinanim"})
FORMS_PARSER_VERSION = ulif_dictua_parse.ULIF_FORMS_PARSER_VERSION
# `ulif_forms` columns the parser determines; compared with the parse of the held raw page (ulif_forms.py).
FORM_COLUMNS = ("entry_key", "form_unstressed", "form_stressed", "stress_vowel_indices", "grammatical_tags",
                "unmapped_labels", "variant_order", "preposition", "marked_asterisk", "is_lemma", "is_invariable",
                "dual_stress_flag", "pedagogical_stressed_form")
JSON_COLUMNS = frozenset({"stress_vowel_indices", "grammatical_tags", "unmapped_labels"})
FLAG_COLUMNS = frozenset({"marked_asterisk", "is_lemma", "is_invariable", "dual_stress_flag"})
EXTRACTION = {
    "ulif_entry": "ulif-dictua-v2",
    "ulif_forms": FORMS_PARSER_VERSION,
    "ulif_section": "ulif-dictua-v2",
    "vesum": "vesum-reingest-v2",
    "puls": "puls-cefr-v1",
    "frazeolohichnyi": "frazeolohichnyi-v1",
    "uws": "atlas0-migration",
}


class SourceAuthenticityError(foundation.Refusal):
    """A held authoritative object the build needs is missing or corrupt: the build stops (fixed diagnostics)."""


def nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text)


def unstressed(text: str) -> str:
    return nfc(text.replace(ACUTE, ""))


def norm_v1(value: str) -> str:
    """norm-v1: NFC, combining acute kept, lower-cased, whitespace collapsed, trailing punctuation cut."""
    text = nfc(value).lower().strip().rstrip(".,;:!?")
    return " ".join(text.split())


def stress_forms(head: str) -> list[str]:
    """Every single-stress reading of a headword: one mark per word part.

    A part printed with several marks (`по́ми́лка`) declares a doublet; a compound
    with one mark per part (`вряди́-годи́`) is one reading. Order is stable.
    """
    parts = re.split(r"([\s-]+)", nfc(head))
    options = []
    for part in parts:
        positions = [i for i, ch in enumerate(part) if ch == ACUTE]
        if len(positions) <= 1:
            options.append([part])
            continue
        plain = part.replace(ACUTE, "")
        variants = []
        for keep in positions:
            # Rebuild with only this mark: count the letters before it in the plain word.
            letters_before = sum(1 for ch in part[:keep] if ch != ACUTE)
            variants.append(plain[:letters_before] + ACUTE + plain[letters_before:])
        options.append(variants)
    forms = [""]
    for choices in options:
        forms = [prefix + choice for prefix in forms for choice in choices]
    seen = []
    for form in forms:
        if form not in seen:
            seen.append(form)
    return seen


def row_dict(row) -> dict:
    return {key: row[key] for key in row.keys()}  # noqa: SIM118 - sqlite3.Row iterates values, not keys


def _raw_sha(ref) -> str | None:
    """The digest of a `sha256:<hex>` raw-cache reference, or None when the reference is malformed."""
    if not isinstance(ref, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", ref):
        return None
    return ref.removeprefix("sha256:")


def _comparable(row: dict) -> tuple:
    """A form row as the parser determines it: JSON columns decoded, flags as booleans."""
    out = []
    for column in FORM_COLUMNS:
        value = row[column]
        if column in JSON_COLUMNS and isinstance(value, str):
            value = json.loads(value or "[]")
        elif column in FLAG_COLUMNS:
            value = bool(value)
        out.append(value)
    return tuple(out)


class PilotSources:
    """Read-only handles for the held sources plus per-entry caches and the consumed-input ledger.

    `consumed` maps every row lookup and query a build made to the digest of its result, empty results included,
    so the build identity covers candidate and absence evidence, not only the frozen anchor rows.
    """

    def __init__(self, sources: SQLiteConnection, vesum: SQLiteConnection, raw_cache: SQLiteConnection,
                 modern_root: Path | None = None, atlas: SQLiteConnection | None = None, frozen_records=()):
        self.sources = sources
        self.vesum = vesum
        self.raw_cache = raw_cache
        self.sources.row_factory = sqlite3.Row
        self.vesum.row_factory = sqlite3.Row
        self._forms: dict[int, dict] = {}
        self._homonyms: dict[str, list[dict]] = {}
        self._vesum: dict[str, list[dict]] = {}
        self.modern_root = modern_root
        self.atlas = atlas
        self.frozen_records = {(r["source_id"], r["locator"]): r for r in frozen_records}
        self._partitions: dict[tuple[str, str | None], list[dict]] = {}
        self._kaikki = None
        self.availability: dict[str, dict] = {}
        self._meanings: dict[str, dict] = {}
        self.consumed: dict[str, str] = {}

    def begin(self) -> None:
        """Start a build's consumed-input ledger (caches stay: the held sources are read in one transaction)."""
        self.consumed = {}

    def _use(self, key: str, value) -> None:
        self.consumed[key] = foundation.digest(value)

    def consumed_digest(self) -> str:
        return foundation.digest(dict(sorted(self.consumed.items())))

    # --- ULIF
    def homonyms(self, normalized_query: str) -> list[dict]:
        if normalized_query not in self._homonyms:
            rows = self.sources.execute(
                "SELECT * FROM ulif_dictua_entries WHERE normalized_query=? AND homonym_checked=1 AND status='ok' "
                "ORDER BY homonym_index, id",
                (normalized_query,),
            )
            self._homonyms[normalized_query] = [row_dict(r) for r in rows]
        rows = self._homonyms[normalized_query]
        self._use(f"ulif_homonyms:{normalized_query}", rows)
        return rows

    def forms(self, entry_id: int) -> list[dict] | None:
        """The entry's `ulif_forms` rows when they authenticate against the held raw page, else None.

        `forms_status` names why rows were refused; refused rows are never attached or compared.
        """
        evidence = self._forms_evidence(entry_id)
        return evidence["rows"] if evidence["status"] is None else None

    def forms_status(self, entry_id: int) -> str | None:
        return self._forms_evidence(entry_id)["status"]

    def forms_failed(self, entry_id: int) -> str | None:
        return self._forms_evidence(entry_id)["failure"]

    def _forms_evidence(self, entry_id: int) -> dict:
        if entry_id not in self._forms:
            self._forms[entry_id] = self._authenticate_forms(entry_id)
        evidence = self._forms[entry_id]
        self._use(f"ulif_forms:{entry_id}", evidence["record"])
        return evidence

    def _authenticate_forms(self, entry_id: int) -> dict:
        """Authenticate derived rows with the existing fingerprint, raw-cache and parser mechanisms (ulif_forms.py).

        A missing or corrupt raw object stops the build (the authority is unavailable). Rows that disagree with the
        authority are refused for this entry: stale parser version or entry fingerprint (the materializer's
        `stale_*` states), a page digest other than the manifest's paradigm reference, or content other than the
        parse of the held page. The derived table never authenticates itself.
        """
        locator = f"ulif:ulif_dictua_entries:id:{entry_id}"
        entry = self.sources.execute("SELECT * FROM ulif_dictua_entries WHERE id=?", (entry_id,)).fetchone()
        if entry is None:
            raise SourceAuthenticityError(f"ULIF entry row missing for {locator}")
        sections = self.sources.execute(
            "SELECT id, kind, source_order, sense_or_group_id, payload_json FROM ulif_dictua_sections "
            "WHERE entry_id=? ORDER BY kind, source_order, id", (entry_id,)).fetchall()
        fingerprint = compute_ulif_entry_fingerprint(entry, sections)
        rows = [row_dict(r) for r in self.sources.execute(
            "SELECT * FROM ulif_forms WHERE entry_id=? ORDER BY id", (entry_id,))]
        failure = self.sources.execute(
            "SELECT reason FROM ulif_forms_failures WHERE entry_id=?", (entry_id,)).fetchone()
        failure = failure[0] if failure else None
        manifest_sha = _raw_sha(entry["raw_response_ref"])
        if manifest_sha is None:
            raise SourceAuthenticityError(f"ULIF raw response reference is malformed for {locator}")
        manifest = self._raw(manifest_sha, locator)
        try:
            manifest = json.loads(manifest)
        except (UnicodeDecodeError, json.JSONDecodeError):
            manifest = None
        if not isinstance(manifest, dict):
            raise SourceAuthenticityError(f"ULIF raw manifest sha256:{manifest_sha} for {locator} is not a manifest")
        page_sha, status = "", None
        homonym_index = int(entry["homonym_index"] or 1)
        if "paradigm" in manifest:
            page_sha = _raw_sha(manifest["paradigm"])
            if page_sha is None:
                raise SourceAuthenticityError(f"ULIF paradigm reference is malformed in sha256:{manifest_sha}")
            page = self._raw(page_sha, locator)
            try:
                expected = ulif_dictua_parse.parse_ulif_entry(page.decode("utf-8", errors="replace"),
                                                              homonym_index=homonym_index)["forms"]
            except Exception:  # any parser failure refuses the derived rows, as the runner does
                expected, status = None, "parse_failed"
        else:
            # The runner's `raw_entry_page_absent` path: one base row from the stored header (ulif_forms.py).
            expected = [ulif_dictua_parse.base_lemma_row(
                entry["canonical_headword"] or "", entry["grammatical_label"] or "", homonym_index=homonym_index,
                is_invariable=False)] if entry["canonical_headword"] else []
        if status is None and rows:
            if any(r["parser_version"] != FORMS_PARSER_VERSION for r in rows):
                status = "stale_parser_version"
            elif any(r["source_entry_fingerprint"] != fingerprint for r in rows):
                status = "stale_source_snapshot"
            elif any((r["source_page_sha256"] or "") != page_sha for r in rows):
                status = "page_lineage_mismatch"
            elif [_comparable(r) for r in rows] != [_comparable(e) for e in expected]:
                status = "content_mismatch"
        elif status is None and not failure and expected:
            status = "content_mismatch"  # the authority prints forms the derived table does not hold
        record = {"rows": rows, "failure": failure, "fingerprint": fingerprint, "manifest": manifest_sha,
                  "page": page_sha, "parser": FORMS_PARSER_VERSION, "status": status}
        return {"rows": rows, "status": status, "failure": failure, "page": page_sha, "record": record}

    def _raw(self, sha: str, locator: str) -> bytes:
        try:
            body = ulif_raw_cache.get(sha, conn=self.raw_cache)
        except ValueError as error:
            raise SourceAuthenticityError(f"ULIF raw object sha256:{sha} for {locator} is corrupt") from error
        if body is None:
            raise SourceAuthenticityError(f"ULIF raw object sha256:{sha} for {locator} is missing from the raw cache")
        return body

    # --- VESUM
    def vesum_forms(self, lemma: str) -> list[dict]:
        """Visible forms (hidden markers excluded, the `forms` view's rule) of every entry with this lemma."""
        if lemma not in self._vesum:
            rows = self.vesum.execute(
                "SELECT f.id, f.entry_id, f.word_form, f.lemma, f.pos, f.tags, f.source_comment FROM forms_all AS f "
                "WHERE f.lemma=? AND NOT EXISTS (SELECT 1 FROM form_markers AS m WHERE m.form_id=f.id "
                f"AND m.marker IN ({','.join('?' * len(HIDDEN_MARKERS))})) ORDER BY f.entry_id, f.id",
                (lemma, *HIDDEN_MARKERS),
            )
            self._vesum[lemma] = [row_dict(r) for r in rows]
        rows = self._vesum[lemma]
        self._use(f"vesum_forms:{lemma}", rows)
        return rows

    def modern_meanings(self, lemma: str) -> dict:
        """Read admitted local articles, preserving whole source partitions for correspondence review.

        A synthetic/injected source without a modern-store binding reads only its injected official table.
        Production uses the canonical SUM-20 resolver, including its normalized staging lookup, and the
        version-gated generic VTS cache reader. Neither reader fetches or writes. An explicit cached miss
        is local absence; a missing current cache is unavailable. Neither proves dictionary-wide absence.
        """
        if lemma not in self._meanings:
            sources = {}
            try:
                articles = (sum20_store.lookup_sum20_cached(lemma, self.sources) if self.modern_root is None else
                            sum20_store.resolve_sum20_articles(lemma, repository_root=self.modern_root))
                sources["sum20"] = {"status": "present" if articles else "local_absent", "records": articles}
            except sum20_store.Sum20StoreError as error:
                sources["sum20"] = {"status": "unavailable", "reason": error.reason, "records": []}
            sources["vts_busel_slovnyk_me"] = {"status": "not_bound", "records": []}
            if self.modern_root is not None:
                from scripts.lexicon.enrich_manifest import _cache_lookup, _read_cached_slovnyk_rows

                cache = _read_cached_slovnyk_rows(lemma)
                row = _cache_lookup(cache, "vts")
                status = "present" if row else ("local_absent" if "vts" in cache.get("lookups", {}) else "unavailable")
                sources["vts_busel_slovnyk_me"] = {"status": status, "records": [row] if row else []}
                if status == "unavailable":
                    sources["vts_busel_slovnyk_me"]["reason"] = "no_current_cached_lookup"
            self._meanings[lemma] = sources
        result = self._meanings[lemma]
        self._use(f"modern_meanings:{lemma}", result)
        return result

    def vesum_canonical_sha(self) -> str:
        row = self.vesum.execute(
            "SELECT value FROM vesum_build_metadata WHERE key='canonical_jsonl_sha256'"
        ).fetchone()
        return row[0]

    def source_partitions(self, lemma: str, slug: str | None) -> list[dict]:
        """All held pilot values, with source-local fields and no inferred sense boundaries.

        Queries are per input. The SUM-20 adapter owns its normalized-title index; no
        other corpus is scanned. Optional stores stay absent in injected fixtures.
        Atlas compilations retain their original labels and raw payloads: they do
        not become independent witnesses for the dictionaries they copied.
        """
        key = (lemma, slug)
        # Replay dependency reads even when the assembled partitions are cached.
        self.modern_meanings(lemma)
        if key not in self._partitions:
            records = []

            def add(source, locator, raw, values, label=None):
                digest = foundation.digest(raw)
                frozen = self.frozen_records.get((source, locator))
                snapshot = (frozen["snapshot_id"] if frozen and frozen["content_sha256"] == digest
                            else f"{source}@sha256:{digest}")
                records.append({"source_id": source, "locator": locator, "record": raw,
                                "content_sha256": digest, "snapshot_id": snapshot,
                                "values": values, "source_label": label or source})

            if self.atlas is not None and slug:
                self.atlas.row_factory = sqlite3.Row
                for table in ("articles", "article_payloads", "enrichment"):
                    for row in self.atlas.execute(f'SELECT * FROM "{table}" WHERE slug=? ORDER BY rowid', (slug,)):
                        raw = row_dict(row)
                        payload = json.loads(raw["payload_json"]) if "payload_json" in raw else raw
                        locator = f"atlas0:{table}:{slug}"
                        if table == "enrichment":
                            locator += "/" + raw["section"]
                            values = {raw["section"]: payload}
                        elif table == "article_payloads":
                            # Keep the complete entry, including metadata and embedded
                            # sections that can differ from the enrichment side table.
                            values = dict(payload)
                        else:
                            values = {"atlas_metadata": raw}
                        label = raw.get("source") or "Atlas compilation"
                        add(source_label_id(label), locator, raw, values, label)
            for source, evidence in self.modern_meanings(lemma).items():
                for raw in evidence["records"]:
                    locator = raw.get("url") or raw.get("source_url") or f"{source}:article:{raw.get('id')}"
                    add(source, locator, raw, {"definition_uk": raw})

            if self.modern_root is not None:
                official = [r for r in self.modern_meanings(lemma)["sum20"]["records"] if r.get("id") is not None]
                if official:
                    with closing(sum20_store.open_sum20(repository_root=self.modern_root)) as store:
                        for article in official:
                            raw = {"article": row_dict(store.execute("SELECT * FROM sum20_articles WHERE id=?",
                                                                     (article["id"],)).fetchone())}
                            for table in ("sum20_senses", "sum20_citations"):
                                raw[table] = [row_dict(r) for r in store.execute(
                                    f'SELECT * FROM "{table}" WHERE article_id=? ORDER BY id', (article["id"],))]
                            add("sum20", f"sum20:structured:id:{article['id']}", raw, {"definition_uk": raw})
                # Reuse the adapter's exact normalized lookup, then read the complete
                # selected mirror row. The older compact adapter drops senses_json,
                # examples and register labels; none may be lost from the card.
                path = self.modern_root / "data" / "sum20_slovnyk_staging.db"
                if path.is_file():
                    with closing(sum20_store.open_sources(path, repository_root=self.modern_root)) as mirror:
                        signature = tuple((p.stat().st_ino, p.stat().st_size, p.stat().st_mtime_ns,
                                           p.stat().st_ctime_ns) if p.exists() else None
                                          for p in (path, Path(str(path) + "-wal")))
                        candidates = sum20_store._mirror_index(path, signature).get(
                            sum20_store.normalize_sum20_lookup(lemma), [])
                        for url in sorted({candidate[1] for candidate in candidates}):
                            row = mirror.execute("SELECT * FROM sum20_slovnyk_articles WHERE url=?", (url,)).fetchone()
                            raw = row_dict(row)
                            add("sum20", "sum20:mirror:" + url, raw, {"definition_uk": {
                                "article_text": raw["text"], "senses": json.loads(raw.get("senses_json") or "[]"),
                                "segmentation": "unadjudicated_source_parser_units", "source_record": raw}})
                for table, column, source, field in (
                    ("esum_etymology_meta", "lemma", "esum", "etymology"),
                    ("goroh_etymology", "requested_lemma", "goroh", "etymology"),
                    ("wiktionary_etymology", "requested_lemma", "wiktionary", "etymology"),
                    ("wiktionary", "word", "wiktionary", "definition_uk"),
                ):
                    if not self.sources.execute("SELECT 1 FROM sqlite_master WHERE name=?", (table,)).fetchone():
                        continue
                    for row in self.sources.execute(f'SELECT rowid AS _rowid, * FROM "{table}" WHERE "{column}"=? '
                                                    'ORDER BY rowid', (lemma,)):
                        raw = row_dict(row)
                        if table == "esum_etymology_meta":
                            cognates = self.sources.execute("SELECT * FROM esum_cognate_forms WHERE entry_id=?",
                                                           (raw["id"],)).fetchone()
                            raw["cognate_forms_record"] = row_dict(cognates) if cognates else None
                        add(source, f"sources:{table}:id:{raw['_rowid']}", raw, {field: raw})
                from scripts.lexicon.enrich_manifest import KAIKKI_SOURCE, _kaikki_row, _load_kaikki_lookup
                from scripts.storage.paths import MissingArtifactError, artifact_path

                if self._kaikki is None:
                    try:
                        path = (None if environ.get("LEXICON_KAIKKI_SIDE_DB", "").strip() else
                                artifact_path("lexicon_kaikki", "lexicon/kaikki_uk_lookup.json",
                                              repo=self.modern_root))
                        self._kaikki = _load_kaikki_lookup(path)
                        self.availability["kaikki_lookup"] = {"status": "available"}
                    except MissingArtifactError:
                        self._kaikki = {}
                        self.availability["kaikki_lookup"] = {"status": "unavailable", "reason": "missing_artifact"}
                raw = _kaikki_row(self._kaikki, lemma)
                if raw:
                    values = {"kaikki": raw}
                    for source_key, field in (("glosses", "english_gloss"), ("ipa", "pronunciation"),
                                              ("etymology_text", "etymology"), ("forms", "morphology")):
                        if raw.get(source_key):
                            values[field] = raw[source_key]
                    add("kaikki", "kaikki:lookup:" + lemma, raw, values,
                        KAIKKI_SOURCE)
            self._partitions[key] = records
        records = self._partitions[key]
        self._use(f"source_partitions:{lemma}:{slug}", records)
        self._use("source_availability", self.availability)
        return records


def source_label_id(label: str) -> str:
    """Registered source of an existing Atlas label; mixed compilations remain compilations."""
    for text, source in (("kaikki/", "kaikki"), ("Вікісловник", "wiktionary"), ("VESUM", "vesum"),
                         ("PULS", "puls"), ("ukrainian-word-stress", "ukrainian_word_stress"),
                         ("dmklinger", "dmklinger"), ("ЕСУМ", "esum"), ("Горох", "goroh"),
                         ("e2u", "r2u_e2u"), ("ВТС", "vts_busel_slovnyk_me")):
        if label.startswith(text) and " + " not in label:
            return source
    return "course_authored"


def partition_lexically_ambiguous(partition: dict, spelling: str) -> bool:
    """Recognize source-owned lexical divisions, never numbered article senses.

    SUM-20 prints superscript homonym numbers on repeated headwords. VTS uses
    Roman-numbered paragraph headings. The compact Kaikki reader retains a POS
    list when its lookup row combines entries. None establishes correspondence
    to the card merely because ULIF has a single homonym.
    """
    head = re.escape(unstressed(spelling).upper())
    heading = re.compile(r"(?<!\w)" + head + r"([¹²³⁴⁵⁶⁷⁸⁹⁰]+),")
    markers = set()
    positions = set()

    def visit(node):
        if isinstance(node, dict):
            if partition["source_id"] == "kaikki" and isinstance(node.get("pos"), list):
                positions.update(node["pos"])
            for key, value in node.items():
                # These columns retain structured source headings as JSON text.
                if key in {"paragraphs_json", "payload_json"} and isinstance(value, str):
                    value = json.loads(value)
                if key in {"paragraphs", "paragraphs_json"} and partition["source_id"] == "vts_busel_slovnyk_me":
                    for paragraph in value:
                        match = re.match(r"^([IVX]+)\s", paragraph["text"])
                        if paragraph.get("strong") and match:
                            markers.add("vts:" + match[1])
                else:
                    visit(value)
        elif isinstance(node, list):
            for value in node:
                visit(value)
        elif isinstance(node, str):
            markers.update(heading.findall(unstressed(node)))

    visit(partition["record"])
    return len(markers) > 1 or len(positions) > 1


def partition_claims(partition: dict) -> list[tuple[str, object, str]]:
    """Typed, additive values plus the verbatim source record, without sense minting.

    The provenance field is retained alongside extracted fields so even unmapped
    Atlas metadata and source-parser structure remain inspectable. A dictionary
    article is a card-level source partition, never one invented card sense.
    """
    claims = [("source_records", {"source_label": partition["source_label"],
                                  "record": partition["record"]}, "record")]
    names = {"meaning": "definition_uk", "definition_cards": "definition_uk", "gloss": "english_gloss",
             "translation": "english_gloss", "literary_attestation": "examples", "lemma": "spelling",
             "pronunciation": "pronunciation", "morphology": "morphology", "etymology": "etymology",
             "stress": "stress", "cefr": "cefr", "examples": "examples", "synonyms": "synonyms",
             "antonyms": "antonyms", "definition_uk": "definition_uk", "kaikki": "kaikki",
             "heritage_status": "heritage_status", "frequency": "frequency", "sources": "sources",
             "idioms": "idioms", "proverbs": "proverbs", "form_notes": "form_notes",
             "wiki_reference": "wiki_reference", "ipa": "pronunciation", "english_gloss": "english_gloss",
             "primary_source": "sources", "source_provenance": "sources"}
    values = [(key, value, key) for key, value in partition["values"].items()]
    for key, value, origin in values:
        if key in {"enrichment", "sections", "atlas_metadata"} and isinstance(value, dict):
            values.extend((name, item, origin + "/" + name) for name, item in value.items())
            continue
        field = names.get(key)
        if field is None or value is None or value == "":
            continue
        if field == "stress" and isinstance(value, dict):
            value = value.get("form")
        elif field == "cefr" and isinstance(value, dict):
            value = value.get("level")
        if value is not None and value != "":
            claims.append((field, value, origin))
    def structured(node, path):
        if isinstance(node, dict):
            for key, value in node.items():
                location = path + "/" + key
                if key in {"examples", "sum20_citations", "register_labels", "labels"} and value:
                    field = "register" if key in {"register_labels", "labels"} else "examples"
                    claims.append((field, {"source_unit_path": location, "value": value}, location))
                elif key != "source_record":
                    structured(value, location)
        elif isinstance(node, list):
            for index, value in enumerate(node):
                structured(value, path + f"/{index}")
    if partition["source_id"] == "sum20":
        structured(partition["values"], "")
    return claims


# --- ULIF paradigm model --------------------------------------------------------------------------

def ulif_slot(tags: list[str]) -> tuple[str, ...] | None:
    """Slot key of a ULIF form row, or None when the row is not a grammatical slot."""
    if {"adjp", "advp", "impers"}.intersection(tags):
        return None
    tokens = [t for t in tags if t in SLOT_VOCABULARY]
    return slot_key(tokens) if tokens else None


def slot_key(tokens: list[str]) -> tuple[str, ...]:
    order = TENSES + CASES + ("s", "p") + GENDERS + PERSONS
    return tuple(sorted(set(tokens), key=order.index))


def slot_name(slot: tuple[str, ...]) -> str:
    """`v_naz.s`."""
    return ".".join(slot)


def ulif_paradigm(forms: list[dict]) -> dict:
    """Group an entry's ULIF form rows into slots.

    Returns {slots: {slot: {forms, stressed, rows, withheld[]}}, uncertain_only: {...}}. A slot is withheld
    when any of its rows is asterisk-marked, preposition-bound or carries unmapped labels (C2 spec,
    REVIEW_BUILD.md §5); withheld slots keep their reason codes and rows as evidence, never as accepted forms.
    """
    slots: dict[tuple[str, ...], dict] = {}
    related = []
    for row in forms:
        if row["is_lemma"]:
            continue
        tags = json.loads(row["grammatical_tags"])
        slot = ulif_slot(tags)
        if slot is None:
            if {"adjp", "advp", "impers"}.intersection(tags):
                related.append(row)
            continue
        item = slots.setdefault(slot, {"forms": [], "stressed": [], "rows": [], "withheld": [], "uncertain": []})
        plain = unstressed(row["form_unstressed"] or row["form_stressed"])
        item["rows"].append(row["id"])
        if row["marked_asterisk"]:
            # An asterisk marks a form ULIF itself flags as uncertain: evidence, never a member of the form set.
            item["withheld"].append("asterisk_marked")
            if plain not in item["uncertain"]:
                item["uncertain"].append(plain)
        else:
            if plain not in item["forms"]:
                item["forms"].append(plain)
            stressed = nfc(row["form_stressed"])
            if stressed not in item["stressed"]:
                item["stressed"].append(stressed)
        if row["preposition"]:
            item["withheld"].append("preposition_bound")
        if json.loads(row["unmapped_labels"] or "[]"):
            item["withheld"].append("unmapped_label")
    for item in slots.values():
        item["withheld"] = sorted(set(item["withheld"]))
        item["forms"].sort()
        item["uncertain"].sort()
    # A slot with no certain form takes no part in comparison or acceptance; its rows stay as withheld evidence.
    return {"slots": {slot: item for slot, item in slots.items() if item["forms"]},
            "uncertain_only": {slot: item for slot, item in slots.items() if not item["forms"]},
            "related": related}


def vesum_slot(tokens: list[str], keep_gender: bool) -> tuple[str, ...] | None:
    chosen = [t for t in tokens if t in SLOT_VOCABULARY]
    if {"pron", "pers"} <= set(tokens):
        chosen = [t for t in chosen if t not in PERSONS]
    if not chosen:
        return None
    # VESUM leaves the singular implicit (`noun:inanim:m:v_naz`, `verb:imperf:past:m`).
    if any(c in CASES or c in GENDERS for c in chosen) and "p" not in chosen and "s" not in chosen:
        chosen.append("s")
    if not keep_gender:
        chosen = [t for t in chosen if t not in GENDERS]
    return slot_key(chosen) if chosen else None


def vesum_aspect_of(tags: list[str]) -> str | None:
    """`perf`, `imperf`, `both` (an entry printing both) or None, from the VESUM tags of one entry's rows."""
    tokens = {t for tag in tags for t in tag.split(":")}
    if {"perf", "imperf"} <= tokens:
        return "both"
    if "imperf" in tokens:
        return "imperf"
    if "perf" in tokens:
        return "perf"
    return None


def vesum_paradigm(rows: list[dict], keep_gender: bool) -> dict[int, dict]:
    """Per VESUM entry: {entry_id: {slots: {slot: {forms, tags}}, stress: set(), pos, flags, aspect}}.

    Every visible form of a slot is a member of its form set and every VESUM tag string stays with the slot: the
    source's own slots, forms and tags, never re-keyed by a variant marker.
    """
    entries: dict[int, dict] = {}
    for row in rows:
        entry = entries.setdefault(row["entry_id"], {"slots": {}, "stress": set(), "pos": row["pos"], "flags": set(),
                                                     "tags": []})
        tokens = row["tags"].split(":")
        entry["tags"].append(row["tags"])
        entry["flags"].update(t for t in tokens if t in {"prop", "abbr"} or t in VARIANT_TAGS)
        slot = vesum_slot(tokens, keep_gender)
        if slot is not None:
            item = entry["slots"].setdefault(slot, {"forms": set(), "tags": set()})
            item["forms"].add(nfc(row["word_form"]))
            item["tags"].add(row["tags"])
        comment = row["source_comment"] or ""
        for token in re.split(r"[\s;,()]+", comment):
            if ACUTE in token and unstressed(token) == row["lemma"]:
                entry["stress"].add(nfc(token))
    for entry in entries.values():
        tags = entry.pop("tags")
        entry["personal_pronoun"] = entry["pos"] == "noun" and all(
            {"pron", "pers"} <= set(tag.split(":")) for tag in tags)
        entry["aspect"] = vesum_aspect_of(tags)
    return entries


def compare_paradigms(ulif: dict | None, vesum: dict) -> dict:
    """Paradigm signature of identity.md §4 step 2: ULIF's slot form sets against VESUM's for the same slots.

    relation: `equal` (the same slots with equal form sets; two invariable sides are equal), `subset` (every ULIF
    slot equals VESUM's and ULIF gives fewer slots) or `differs` (any ULIF slot whose form set is not VESUM's,
    a slot VESUM does not print included: `замка` vs `замку`). `unknown` when the ULIF forms did not authenticate.
    `slots` classifies every slot so a mismatch stays visible as evidence.
    """
    if ulif is None:
        return {"relation": "unknown", "slots": {}}
    u = {slot: set(item["forms"]) for slot, item in ulif["slots"].items()}
    v = {slot: set(item["forms"]) for slot, item in vesum["slots"].items()}
    # A one-column personal-pronoun table leaves number implicit. Supply it only when every
    # VESUM case slot explicitly agrees on one number; preserve the complete form sets.
    numbers = {token for slot in v for token in slot if token in {"s", "p"}}
    if (ulif.get("pronoun") and vesum.get("personal_pronoun") and len(numbers) == 1
            and u and all(len(slot) == 1 and slot[0] in CASES for slot in u)
            and all(any(case in slot for case in CASES) and numbers.intersection(slot) for slot in v)):
        number = next(iter(numbers))
        u = {slot_key([*slot, number]): forms for slot, forms in u.items()}
    detail = {}
    for slot in sorted(set(u) | set(v)):
        if slot not in v:
            detail[slot] = "ulif_only_slot"
        elif slot not in u:
            detail[slot] = "vesum_only_slot"
        else:
            detail[slot] = "equal" if u[slot] == v[slot] else "differs"
    if any(c in {"differs", "ulif_only_slot"} for c in detail.values()) or (v and not u):
        relation = "differs"
    elif set(u) == set(v):
        relation = "equal"
    else:
        relation = "subset"
    return {"relation": relation, "slots": detail}


def aspect_compatible(ulif_aspect: str | None, vesum_aspect: str | None) -> bool:
    """identity.md §4 step 4: aspects must be equal; biaspectual matches either; an unstated aspect never excludes."""
    if ulif_aspect is None or vesum_aspect is None:
        return True
    return ulif_aspect == vesum_aspect or "both" in (ulif_aspect, vesum_aspect)


def match_identity(target_id: int, ulif_homonyms: dict[int, dict], vesum_entries: dict[int, dict]) -> dict:
    """VESUM↔ULIF match for one ULIF entry (identity.md §4 decision table).

    `ulif_homonyms` maps entry id -> {head: stressed headword, paradigm: ulif_paradigm() or None when the forms
    did not authenticate, aspect}; every entry is a checked ULIF homonym of the target's POS and proper/common
    class. `vesum_entries` maps VESUM entry id -> vesum_paradigm() item of the same POS and class. Paradigm and
    aspect compatibility are applied before stress; the method names what actually separated the candidates.
    Returns {confidence, method, vesum_entry (id or None), candidates[], basis, notes[], evidence{}}.
    """
    notes: list[str] = []
    if not vesum_entries:
        return {"confidence": "medium", "method": "unresolved", "vesum_entry": None, "candidates": [],
                "basis": "entry", "evidence": {},
                "notes": ["no VESUM entry for the spelling, part of speech and proper/common class; the card "
                          "follows the checked ULIF homonym division"]}

    def relation(ulif_id: int, vesum_id: int) -> str:
        return compare_paradigms(ulif_homonyms[ulif_id]["paradigm"], vesum_entries[vesum_id])["relation"]

    def grammar_ok(ulif_id: int, vesum_id: int) -> bool:
        return (relation(ulif_id, vesum_id) in {"equal", "subset"}
                and aspect_compatible(ulif_homonyms[ulif_id].get("aspect"), vesum_entries[vesum_id]["aspect"]))

    def stress_ok(ulif_id: int, vesum_id: int):
        stresses = vesum_entries[vesum_id]["stress"]
        if not stresses or not ulif_homonyms[ulif_id]["head"]:
            return None
        head = ulif_homonyms[ulif_id]["head"]
        return bool(({nfc(h) for h in stress_forms(head)} | {nfc(head)}) & stresses)

    evidence = {str(v): {"paradigm": relation(target_id, v),
                         "aspect": aspect_compatible(ulif_homonyms[target_id].get("aspect"),
                                                     vesum_entries[v]["aspect"]),
                         "stress": stress_ok(target_id, v)} for v in sorted(vesum_entries)}
    unknown = sorted(u for u, h in ulif_homonyms.items() if h["paradigm"] is None)
    if unknown:
        return {"confidence": "unresolved", "method": "unresolved", "vesum_entry": None,
                "candidates": sorted(vesum_entries), "basis": "paradigm", "evidence": evidence,
                "notes": ["the ULIF forms of this entry or of a homonym it competes with did not authenticate "
                          "against the held raw page; the ULIF row stays unattached to VESUM evidence"]}
    grammatical = [v for v in sorted(vesum_entries) if grammar_ok(target_id, v)]
    options = [v for v in grammatical if stress_ok(target_id, v) is not False]
    if not options:
        return {"confidence": "unresolved", "method": "unresolved", "vesum_entry": None,
                "candidates": sorted(vesum_entries), "basis": "paradigm", "evidence": evidence,
                "notes": ["no VESUM entry has an equal or subset paradigm, a compatible aspect and the stress of "
                          "this ULIF homonym; the ULIF row stays unattached to VESUM evidence"]}
    if len(options) > 1:
        return {"confidence": "unresolved", "method": "unresolved", "vesum_entry": None, "candidates": options,
                "basis": "paradigm", "evidence": evidence,
                "notes": ["several VESUM entries are compatible with this ULIF homonym; none is selected"]}
    partner = options[0]
    # Competitors excluded by stress alone: grammatically compatible, contradicted only by the stress evidence.
    stress_only = [v for v in grammatical if v != partner] + [
        u for u in sorted(ulif_homonyms) if u != target_id and grammar_ok(u, partner)
        and stress_ok(u, partner) is False]
    sharing = [u for u in sorted(ulif_homonyms) if u != target_id and grammar_ok(u, partner)
               and stress_ok(u, partner) is not False]
    if not sharing:
        if stress_only:
            return {"confidence": "medium", "method": "stress_only", "vesum_entry": partner, "candidates": [partner],
                    "basis": "stress", "evidence": evidence,
                    "notes": ["another candidate has an identical or compatible paradigm; only stress separates them"]}
        if len(ulif_homonyms) == 1 and len(vesum_entries) == 1:
            return {"confidence": "high", "method": "unique_match", "vesum_entry": partner, "candidates": [partner],
                    "basis": "paradigm", "evidence": evidence, "notes": notes}
        method = "stress_and_paradigm" if stress_ok(target_id, partner) else "paradigm_only"
        return {"confidence": "high", "method": method, "vesum_entry": partner, "candidates": [partner],
                "basis": "paradigm", "evidence": evidence, "notes": notes}
    heads = {nfc(ulif_homonyms[u]["head"]) for u in [target_id, *sharing]}
    if len(heads) == len(sharing) + 1:
        return {"confidence": "medium", "method": "stress_only", "vesum_entry": partner, "candidates": [partner],
                "basis": "stress", "evidence": evidence,
                "notes": ["other ULIF homonyms share this VESUM entry; only stress separates them"]}
    return {"confidence": "medium", "method": "paradigm_only", "vesum_entry": partner, "candidates": [partner],
            "basis": "paradigm", "evidence": evidence,
            "notes": ["dictionary-division split: several ULIF homonyms with identical stress and paradigm map to one "
                      "VESUM entry (identity.md §5 case D)"]}


# --- extraction of the held rows the WP3 ingestion modules read ---------------------------------------

WP3_TABLES = ("ulif_dictua_entries", "ulif_dictua_sections", "sum20_articles", "sum20_senses", "sum20_citations")


def write_extract(sources: SQLiteConnection, entry_ids: list[int], destination: Path) -> dict:
    """Copy the rows the C3/C4 ingestion reads for the pilot entries into a standalone SQLite file.

    Rows are copied verbatim (same ids, same values), so citations and field digests computed on the extract
    equal those on the held snapshot. The ingestion iterates a whole table, which is far too slow on the full
    harvest; the extract bounds it to the pilot entries and their homonym siblings. Returns the row count per table
    and `content_sha256`, the digest of every copied row: the extract is a consumed build input.
    """
    ids = sorted(set(entry_ids))
    queries = [
        r[0] for r in sources.execute(
            f"SELECT normalized_query FROM ulif_dictua_entries WHERE id IN ({','.join('?' * len(ids))})", ids)
    ]
    sibling_ids = [
        r[0] for r in sources.execute(
            f"SELECT id FROM ulif_dictua_entries WHERE normalized_query IN ({','.join('?' * len(set(queries)))})",
            sorted(set(queries)))
    ]
    out = sqlite3.connect(destination)
    counts, content = {}, hashlib.sha256()
    try:
        for table in WP3_TABLES:
            ddl = sources.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone()
            out.execute(ddl[0])
            columns = [r[1] for r in sources.execute(f'PRAGMA table_info("{table}")')]
            listed = ",".join(f'"{c}"' for c in columns)
            where, params = "1=1", []
            if table == "ulif_dictua_entries":
                where, params = f"id IN ({','.join('?' * len(sibling_ids))})", sibling_ids
            elif table == "ulif_dictua_sections":
                where, params = f"entry_id IN ({','.join('?' * len(sibling_ids))})", sibling_ids
            rows = sources.execute(f'SELECT {listed} FROM "{table}" WHERE {where} ORDER BY id', params).fetchall()
            out.executemany(
                f'INSERT INTO "{table}" ({listed}) VALUES ({",".join("?" * len(columns))})', [tuple(r) for r in rows]
            )
            counts[table] = len(rows)
            content.update(foundation.canonical({"table": table, "columns": columns,
                                                 "rows": [list(r) for r in rows]}))
        out.commit()
    finally:
        out.close()
    return {"tables": counts, "content_sha256": content.hexdigest()}


def group_by(items, key):
    grouped = defaultdict(list)
    for item in items:
        grouped[key(item)].append(item)
    return grouped
