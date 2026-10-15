"""Read-only source access for pilot word-card assembly (#8981).

Everything here reads the frozen pilot inputs and the held `sources.db` / `vesum.db`
without writing to them. Three jobs: row access with literal-row digests, the ULIF
paradigm model (slot keys, withholding classes) and the VESUM↔ULIF identity match of
`docs/atlas/word-cards/identity.md` §4 for the cases the pilot exercises.

No Ukrainian text is produced here: every returned string is a verbatim source value.
"""

from __future__ import annotations

import json
import re
import sqlite3
import unicodedata
from collections import defaultdict
from pathlib import Path

ACUTE = "́"
CASES = ("v_naz", "v_rod", "v_dav", "v_zna", "v_oru", "v_mis", "v_kly")
GENDERS = ("m", "f", "n")
TENSES = ("inf", "pres", "futr", "past", "impr")
PERSONS = ("1", "2", "3")
# Canonical slot order: tense, case, number, gender, person.
SLOT_VOCABULARY = frozenset(CASES + GENDERS + TENSES + PERSONS + ("s", "p"))
HIDDEN_MARKERS = ("bad", "obsc", "subst")
# VESUM tag tokens that mark a form as a variant rather than a different slot (never part of the slot key).
VARIANT_TAGS = frozenset({"var", "arch", "rare", "long", "short", "slang", "vulg", "bad", "obsc", "subst", "ranim", "rinanim"})
EXTRACTION = {
    "ulif_entry": "ulif-dictua-v2",
    "ulif_forms": "ulif-forms-v4",
    "ulif_section": "ulif-dictua-v2",
    "vesum": "vesum-reingest-v2",
    "puls": "puls-cefr-v1",
    "frazeolohichnyi": "frazeolohichnyi-v1",
    "uws": "atlas0-migration",
}


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


class PilotSources:
    """Read-only handles for the held sources plus per-entry caches."""

    def __init__(self, sources: sqlite3.Connection, vesum: sqlite3.Connection):
        self.sources = sources
        self.vesum = vesum
        self.sources.row_factory = sqlite3.Row
        self.vesum.row_factory = sqlite3.Row
        self._forms: dict[int, list[dict]] = {}
        self._vesum: dict[str, list[dict]] = {}

    # --- ULIF
    def entry(self, entry_id: int) -> dict | None:
        row = self.sources.execute("SELECT * FROM ulif_dictua_entries WHERE id=?", (entry_id,)).fetchone()
        return row_dict(row) if row else None

    def homonyms(self, normalized_query: str) -> list[dict]:
        rows = self.sources.execute(
            "SELECT * FROM ulif_dictua_entries WHERE normalized_query=? AND homonym_checked=1 AND status='ok' "
            "ORDER BY homonym_index, id",
            (normalized_query,),
        )
        return [row_dict(r) for r in rows]

    def sections(self, entry_id: int) -> list[dict]:
        rows = self.sources.execute(
            "SELECT * FROM ulif_dictua_sections WHERE entry_id=? ORDER BY kind, source_order, id", (entry_id,)
        )
        return [row_dict(r) for r in rows]

    def forms(self, entry_id: int) -> list[dict]:
        if entry_id not in self._forms:
            rows = self.sources.execute("SELECT * FROM ulif_forms WHERE entry_id=? ORDER BY id", (entry_id,))
            self._forms[entry_id] = [row_dict(r) for r in rows]
        return self._forms[entry_id]

    def forms_failed(self, entry_id: int) -> str | None:
        row = self.sources.execute("SELECT reason FROM ulif_forms_failures WHERE entry_id=?", (entry_id,)).fetchone()
        return row[0] if row else None

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
        return self._vesum[lemma]

    def sum20_articles(self) -> list[dict]:
        """Held СУМ-20 articles (crawl paused: a small sample). Headwords only; no definition text is read here."""
        if not hasattr(self, "_sum20"):
            rows = self.sources.execute(
                "SELECT id, wordid, headword, stressed_headword, quarantine_reason FROM sum20_articles ORDER BY id"
            )
            self._sum20 = [row_dict(r) for r in rows]
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
    """`v_naz.s`; a variant marker (`~arch`) is appended to the base slot name without a separator."""
    base = ".".join(t for t in slot if not t.startswith("~"))
    return base + "".join(t for t in slot if t.startswith("~"))


def ulif_paradigm(forms: list[dict]) -> dict:
    """Group an entry's ULIF form rows into slots.

    Returns {slots: {slot: {forms, stressed, rows, withheld[]}}, withheld_rows: [...]}. A slot is withheld
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


# VESUM tags that mark a form as an archaic, rare or contracted variant of its slot. Such forms are a separate
# proposition (`<slot>~<tag>`): mixing them into the base slot would report an archaic extra as a disagreement.
VARIANT_FORM_TAGS = frozenset({"var", "arch", "rare", "long", "short", "slang", "vulg"})


def vesum_paradigm(rows: list[dict], keep_gender: bool) -> dict[int, dict]:
    """Per VESUM entry: {entry_id: {slots: {slot: {forms, tags[]}}, stress: set(), pos, flags}}."""
    entries: dict[int, dict] = {}
    for row in rows:
        entry = entries.setdefault(row["entry_id"], {"slots": {}, "stress": set(), "pos": row["pos"], "flags": set()})
        tokens = row["tags"].split(":")
        entry["flags"].update(t for t in tokens if t in {"prop", "abbr"} or t in VARIANT_TAGS)
        slot = vesum_slot(tokens, keep_gender)
        if slot is not None:
            variant = sorted(t for t in tokens if t in VARIANT_FORM_TAGS)
            key = (*slot, "~" + "+".join(variant)) if variant else slot
            item = entry["slots"].setdefault(key, {"forms": set(), "tags": set()})
            item["forms"].add(nfc(row["word_form"]))
            item["tags"].add(row["tags"])
        comment = row["source_comment"] or ""
        for token in re.split(r"[\s;,()]+", comment):
            if ACUTE in token and unstressed(token) == row["lemma"]:
                entry["stress"].add(nfc(token))
    return entries


DIM_OF = {
    **{c: "case" for c in CASES}, **{g: "gender" for g in GENDERS}, **{t: "tense" for t in TENSES},
    **{p: "person" for p in PERSONS}, "s": "number", "p": "number",
}


def slot_dims(slot: tuple[str, ...]) -> set[str]:
    return {DIM_OF[t] for t in slot if t in DIM_OF}


def common_dims(*paradigms: dict) -> set[str]:
    """Dimensions that every given paradigm states on at least one slot.

    ULIF and VESUM print slots at different granularity (a numeral's ULIF slots carry no number, VESUM's do).
    A dimension one side never states is dropped from both before comparing; a dimension both sides state
    somewhere is kept, so a slot printed without it (a verb's participle row) stays its own slot.
    """
    dims = None
    for p in paradigms:
        stated = {d for slot in p["slots"] for d in slot_dims(slot)}
        dims = stated if dims is None else dims & stated
    return dims or set()


def project(paradigm: dict, dims: set[str]) -> dict:
    """Merge slots onto `dims`: union of forms, rows and withheld codes; an empty projection is the slot `*`."""
    out: dict[tuple[str, ...], dict] = {}
    for slot, item in paradigm["slots"].items():
        base = tuple(t for t in slot if t in DIM_OF and DIM_OF[t] in dims)
        key = (base or ("*",)) + tuple(t for t in slot if t not in DIM_OF)
        merged = out.setdefault(key, {})
        for field, value in item.items():
            if isinstance(value, (list, set)):
                current = merged.setdefault(field, set() if isinstance(value, set) else [])
                if isinstance(value, set):
                    current |= value
                else:
                    current += [v for v in value if v not in current]
            else:
                merged[field] = value
    for item in out.values():
        for field, value in item.items():
            if isinstance(value, list):
                item[field] = sorted(value) if field in {"forms", "withheld", "stressed"} else value
    return {"slots": out}


def compare_paradigms(ulif: dict, vesum: dict) -> dict:
    """Slot-level comparison of two paradigms (unstressed form sets per slot).

    relation: `equal`, `compatible` (common slots all intersect; either side may add variants or slots),
    `differs` (some common slot is disjoint, or the sides share no slot) or `empty` (neither side inflects).
    `slots` classifies every slot for the disagreement census.
    """
    if not ulif["slots"] and not vesum["slots"]:
        return {"relation": "empty", "slots": {}}
    dims = common_dims(ulif, vesum) if ulif["slots"] and vesum["slots"] else set()
    ulif, vesum = project(ulif, dims), project(vesum, dims)
    u = {slot: set(item["forms"]) for slot, item in ulif["slots"].items()}
    v = {slot: set(item["forms"]) for slot, item in vesum["slots"].items()}
    detail = {}
    for slot in sorted(set(u) | set(v)):
        if slot not in v:
            detail[slot] = "ulif_only_slot"
        elif slot not in u:
            detail[slot] = "vesum_only_slot"
        elif u[slot] == v[slot]:
            detail[slot] = "equal"
        elif not (u[slot] & v[slot]):
            detail[slot] = "disjoint"
        elif u[slot] < v[slot]:
            detail[slot] = "vesum_extra_variant"
        elif v[slot] < u[slot]:
            detail[slot] = "ulif_extra_variant"
        else:
            detail[slot] = "partial_overlap"
    common = [c for c in detail.values() if not c.endswith("_only_slot")]
    if not common or "disjoint" in common:
        relation = "differs"
    elif all(c == "equal" for c in detail.values()):
        relation = "equal"
    else:
        relation = "compatible"
    return {"relation": relation, "slots": detail}


def match_identity(target_id: int, ulif_homonyms: dict[int, dict], vesum_entries: dict[int, dict]) -> dict:
    """VESUM↔ULIF match for one ULIF entry (identity.md §4 decision table, the pilot-exercised rows).

    `ulif_homonyms` maps entry id -> {head: stressed headword, paradigm: ulif_paradigm()}; every entry is a checked
    ULIF homonym of the target's class. `vesum_entries` maps VESUM entry id -> vesum_paradigm() item.
    Returns {confidence, method, vesum_entry (id or None), candidates[], basis, notes[]}.
    """
    notes: list[str] = []
    if not vesum_entries:
        return {"confidence": "medium", "method": "unresolved", "vesum_entry": None, "candidates": [],
                "basis": "entry", "notes": ["no VESUM entry for the spelling and part of speech; the card follows "
                                            "the checked ULIF homonym division"]}

    def compat(ulif_id: int, vesum_id: int) -> bool:
        return compare_paradigms(ulif_homonyms[ulif_id]["paradigm"], vesum_entries[vesum_id])["relation"] in {
            "equal", "compatible", "empty"}

    def stress_ok(ulif_id: int, vesum_id: int):
        stresses = vesum_entries[vesum_id]["stress"]
        if not stresses:
            return None
        heads = {nfc(h) for h in stress_forms(ulif_homonyms[ulif_id]["head"])} | {nfc(ulif_homonyms[ulif_id]["head"])}
        return bool(heads & stresses)

    options = [v for v in sorted(vesum_entries) if compat(target_id, v) and stress_ok(target_id, v) is not False]
    if not options:
        return {"confidence": "unresolved", "method": "unresolved", "vesum_entry": None,
                "candidates": sorted(vesum_entries), "basis": "paradigm",
                "notes": ["no VESUM entry has a compatible paradigm and stress for this ULIF homonym; "
                          "the ULIF row stays unattached to VESUM evidence"]}
    if len(options) > 1:
        return {"confidence": "unresolved", "method": "unresolved", "vesum_entry": None, "candidates": options,
                "basis": "paradigm",
                "notes": ["several VESUM entries are compatible with this ULIF homonym; none is selected"]}
    partner = options[0]
    sharing = [u for u in sorted(ulif_homonyms) if u != target_id and compat(u, partner)
               and stress_ok(u, partner) is not False]
    if not sharing:
        if len(ulif_homonyms) == 1 and len(vesum_entries) == 1:
            return {"confidence": "high", "method": "unique_match", "vesum_entry": partner, "candidates": [partner],
                    "basis": "paradigm", "notes": notes}
        known = stress_ok(target_id, partner)
        method = "stress_and_paradigm" if known else "paradigm_only"
        return {"confidence": "high", "method": method, "vesum_entry": partner, "candidates": [partner],
                "basis": "paradigm", "notes": notes}
    heads = {nfc(ulif_homonyms[u]["head"]) for u in [target_id, *sharing]}
    if len(heads) == len(sharing) + 1:
        return {"confidence": "medium", "method": "stress_only", "vesum_entry": partner, "candidates": [partner],
                "basis": "stress", "notes": ["other ULIF homonyms share this VESUM entry; only stress separates them"]}
    return {"confidence": "medium", "method": "paradigm_only", "vesum_entry": partner, "candidates": [partner],
            "basis": "paradigm",
            "notes": ["dictionary-division split: several ULIF homonyms with identical stress and paradigm map to one "
                      "VESUM entry (identity.md §5 case D)"]}


# --- extraction of the held rows the WP3 ingestion modules read ---------------------------------------

WP3_TABLES = ("ulif_dictua_entries", "ulif_dictua_sections", "sum20_articles", "sum20_senses", "sum20_citations")


def write_extract(sources: sqlite3.Connection, entry_ids: list[int], destination: Path) -> dict:
    """Copy the rows the C3/C4 ingestion reads for the pilot entries into a standalone SQLite file.

    Rows are copied verbatim (same ids, same values), so citations and field digests computed on the extract
    equal those on the held snapshot. The ingestion iterates a whole table, which is far too slow on the full
    harvest; the extract bounds it to the pilot entries and their homonym siblings.
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
    counts = {}
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
        out.commit()
    finally:
        out.close()
    return counts


def group_by(items, key):
    grouped = defaultdict(list)
    for item in items:
        grouped[key(item)].append(item)
    return grouped
