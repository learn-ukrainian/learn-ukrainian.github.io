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
from pathlib import Path

from scripts.atlas import word_card_foundation as foundation
from scripts.lexicon import ulif_raw_cache
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

    def __init__(self, sources: SQLiteConnection, vesum: SQLiteConnection, raw_cache: SQLiteConnection):
        self.sources = sources
        self.vesum = vesum
        self.raw_cache = raw_cache
        self.sources.row_factory = sqlite3.Row
        self.vesum.row_factory = sqlite3.Row
        self._forms: dict[int, dict] = {}
        self._homonyms: dict[str, list[dict]] = {}
        self._vesum: dict[str, list[dict]] = {}
        self._sum20: list[dict] | None = None
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

    def sum20_articles(self) -> list[dict]:
        """Held СУМ-20 articles (crawl paused: a small sample). Headwords only; no definition text is read here."""
        if self._sum20 is None:
            rows = self.sources.execute(
                "SELECT id, wordid, headword, stressed_headword, quarantine_reason FROM sum20_articles ORDER BY id"
            )
            self._sum20 = [row_dict(r) for r in rows]
        self._use("sum20_articles", self._sum20)
        return self._sum20

    def vesum_canonical_sha(self) -> str:
        row = self.vesum.execute(
            "SELECT value FROM vesum_build_metadata WHERE key='canonical_jsonl_sha256'"
        ).fetchone()
        return row[0]


# --- ULIF paradigm model --------------------------------------------------------------------------

def ulif_slot(tags: list[str]) -> tuple[str, ...] | None:
    """Slot key of a ULIF form row, or None when the row is not a grammatical slot."""
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
    for row in forms:
        if row["is_lemma"]:
            continue
        tags = json.loads(row["grammatical_tags"])
        slot = ulif_slot(tags)
        if slot is None:
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
            "uncertain_only": {slot: item for slot, item in slots.items() if not item["forms"]}}


def vesum_slot(tokens: list[str], keep_gender: bool) -> tuple[str, ...] | None:
    chosen = [t for t in tokens if t in SLOT_VOCABULARY]
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
        entry["aspect"] = vesum_aspect_of(entry.pop("tags"))
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
