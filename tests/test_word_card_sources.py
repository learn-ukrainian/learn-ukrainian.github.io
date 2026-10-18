"""Source-side rules of pilot word-card assembly: stress readings, paradigm slots, identity matching, and the
authentication of derived ULIF forms against the held raw page.

Synthetic rows and pages only: placeholder Cyrillic tokens with combining acute and real grammatical-label terms,
so no dictionary content is committed. Raw pages are minimal ULIF-shaped HTML parsed by the existing parser.
"""

import hashlib
import json
import sqlite3

import pytest

from scripts.atlas import word_card_foundation as foundation
from scripts.atlas import word_card_sources as src
from scripts.lexicon import ulif_raw_cache
from scripts.lexicon.runner import ulif_dictua_parse
from scripts.wiki.sources_db import compute_ulif_entry_fingerprint

A = src.ACUTE
ENTRY_DDL = """CREATE TABLE ulif_dictua_entries (id INTEGER PRIMARY KEY, normalized_query TEXT, homonym_index INTEGER,
 canonical_headword TEXT, grammatical_label TEXT, sense_gloss TEXT, content_sha256 TEXT, register_position TEXT,
 homonym_checked INTEGER, raw_response_ref TEXT, retrieved_at TEXT, response_sha256 TEXT, parser_version TEXT,
 status TEXT)"""
SECTION_DDL = """CREATE TABLE ulif_dictua_sections (id INTEGER PRIMARY KEY, entry_id INTEGER, kind TEXT,
 source_order INTEGER, sense_or_group_id TEXT, payload_json TEXT)"""
FORMS_DDL = """CREATE TABLE ulif_forms (id INTEGER PRIMARY KEY, entry_id INTEGER, entry_key TEXT, form_unstressed TEXT,
 form_stressed TEXT, stress_vowel_indices TEXT, grammatical_tags TEXT, unmapped_labels TEXT, variant_order INTEGER,
 preposition TEXT, marked_asterisk INTEGER, is_lemma INTEGER, is_invariable INTEGER, dual_stress_flag INTEGER,
 pedagogical_stressed_form TEXT, source_page_sha256 TEXT, parser_version TEXT, source_entry_fingerprint TEXT)"""
FAILURES_DDL = "CREATE TABLE ulif_forms_failures (id INTEGER PRIMARY KEY, entry_id INTEGER, reason TEXT, locator TEXT)"
VESUM_DDL = (
    "CREATE TABLE forms_all (id INTEGER PRIMARY KEY, entry_id INTEGER, word_form TEXT, lemma TEXT, pos TEXT, "
    "tags TEXT, source_comment TEXT, word_form_folded TEXT, lemma_folded TEXT);"
    "CREATE TABLE form_markers (form_id INTEGER, marker TEXT, origin TEXT, marker_class TEXT);"
    "CREATE TABLE vesum_build_metadata (key TEXT PRIMARY KEY, value TEXT);"
)


# --- ULIF fixture pages and the raw cache -----------------------------------------------------------------

def paradigm_page(head, label, gloss="", rows=()):
    """A minimal ULIF entry page: header, label, gloss and a case table (rows: (case, singular, plural))."""
    table = ""
    if rows:
        body = "".join(f'<tr><td class="td_left_style">{case}</td><td class="td_inner_style">{sg}</td>'
                       f'<td class="td_inner_style">{pl}</td></tr>' for case, sg, pl in rows)
        table = (f'<table><tr class="td_style"><td>відмінок</td><td>однина</td><td>множина</td></tr>{body}'
                 "</table>")
    return (f'<td id="ContentPlaceHolder1_article"><div align="center"><span class="word_style">{head} </span>'
            f'<span class="gram_style">– {label}</span></div><div align="center" class="comment_style">{gloss}<hr>'
            f"</div>{table}</td>")


def put_raw(raw, body: bytes) -> str:
    sha = hashlib.sha256(body).hexdigest()
    raw.execute("INSERT OR IGNORE INTO ulif_dictua_raw_responses (response_sha256, body) VALUES (?, ?)", (sha, body))
    return sha


def raw_cache():
    raw = sqlite3.connect(":memory:")
    raw.execute(ulif_raw_cache.RAW_SCHEMA)
    return raw


def add_entry(sources, raw, entry_id, query, head, label, gloss="", homonym=1, rows=(), sections=(), page=True):
    """Insert an entry whose `ulif_forms` rows are exactly the existing parser's output for its held raw page."""
    html = paradigm_page(head, label, gloss, rows)
    manifest = {"paradigm": "sha256:" + put_raw(raw, html.encode())} if page else {}
    manifest_sha = put_raw(raw, json.dumps(manifest, sort_keys=True).encode())
    entry = {"id": entry_id, "normalized_query": query, "homonym_index": homonym, "canonical_headword": head,
             "grammatical_label": label, "sense_gloss": gloss, "content_sha256": "c" * 64,
             "register_position": f"1:{entry_id}", "homonym_checked": 1, "raw_response_ref": "sha256:" + manifest_sha,
             "retrieved_at": "2026-01-01T00:00:00Z", "response_sha256": manifest_sha, "parser_version": "ulif-dictua-v2",
             "status": "ok"}
    insert(sources, "ulif_dictua_entries", entry)
    section_rows = []
    for number, (kind, payload) in enumerate(sections, start=1):
        row = {"id": entry_id * 100 + number, "entry_id": entry_id, "kind": kind, "source_order": number - 1,
               "sense_or_group_id": f"{kind}:{number}", "payload_json": json.dumps({"raw_html": payload})}
        insert(sources, "ulif_dictua_sections", row)
        section_rows.append(row)
    fingerprint = compute_ulif_entry_fingerprint(entry, sorted(section_rows, key=lambda r: (r["kind"], r["source_order"])))
    if page:
        parsed = ulif_dictua_parse.parse_ulif_entry(html, homonym_index=homonym)["forms"]
        page_sha = manifest["paradigm"].removeprefix("sha256:")
    else:
        parsed = [ulif_dictua_parse.base_lemma_row(head, label, homonym_index=homonym, is_invariable=False)]
        page_sha = ""
        insert(sources, "ulif_forms_failures", {"entry_id": entry_id, "reason": "raw_entry_page_absent",
                                               "locator": f"ulif:entry:{entry_id}"})
    for number, form in enumerate(parsed):
        insert(sources, "ulif_forms", {
            "id": entry_id * 100 + number, "entry_id": entry_id, "entry_key": form["entry_key"],
            "form_unstressed": form["form_unstressed"], "form_stressed": form["form_stressed"],
            "stress_vowel_indices": json.dumps(form["stress_vowel_indices"]),
            "grammatical_tags": json.dumps(form["grammatical_tags"], ensure_ascii=False),
            "unmapped_labels": json.dumps(form["unmapped_labels"], ensure_ascii=False),
            "variant_order": form["variant_order"], "preposition": form["preposition"],
            "marked_asterisk": int(form["marked_asterisk"]), "is_lemma": int(form["is_lemma"]),
            "is_invariable": int(form["is_invariable"]), "dual_stress_flag": int(form["dual_stress_flag"]),
            "pedagogical_stressed_form": form["pedagogical_stressed_form"], "source_page_sha256": page_sha,
            "parser_version": src.FORMS_PARSER_VERSION, "source_entry_fingerprint": fingerprint})
    return entry


def insert(conn, table, row):
    cols = ",".join(row)
    conn.execute(f"INSERT INTO {table} ({cols}) VALUES ({','.join('?' * len(row))})", list(row.values()))


def stores():
    sources = sqlite3.connect(":memory:")
    sources.executescript(";".join((ENTRY_DDL, SECTION_DDL, FORMS_DDL, FAILURES_DDL)) + ";")
    vesum = sqlite3.connect(":memory:")
    vesum.executescript(VESUM_DDL)
    return sources, vesum, raw_cache()


def ulif_row(row_id, entry_id, tags, form, stressed=None, **extra):
    row = {"id": row_id, "entry_id": entry_id, "entry_key": f"e#{entry_id}", "form_unstressed": form,
           "form_stressed": stressed or form, "stress_vowel_indices": "[]", "grammatical_tags": json.dumps(tags),
           "unmapped_labels": "[]", "variant_order": 1, "preposition": "", "marked_asterisk": 0, "is_lemma": 0,
           "is_invariable": 0, "dual_stress_flag": 0, "pedagogical_stressed_form": stressed or form,
           "source_page_sha256": "", "parser_version": "ulif-forms-v4", "source_entry_fingerprint": ""}
    row.update(extra)
    return row


def vesum_row(row_id, entry_id, lemma, form, tags, comment=None, pos="noun"):
    return {"id": row_id, "entry_id": entry_id, "word_form": form, "lemma": lemma, "pos": pos, "tags": tags,
            "source_comment": comment}


# --- text, slots and paradigms ---------------------------------------------------------------------------

def test_stress_forms_doublet_and_compound():
    assert src.stress_forms(f"по{A}ми{A}лка") == [f"по{A}милка", f"поми{A}лка"]
    assert src.stress_forms(f"вря{A}ди-году{A}") == [f"вря{A}ди-году{A}"]
    assert src.stress_forms("проста") == ["проста"]
    # Each hyphen part declares its own doublet; the readings are the product, in a stable order.
    assert len(src.stress_forms(f"по{A}ми{A}лка-по{A}ми{A}лка")) == 4


def test_norm_v1_keeps_stress_and_cuts_trailing_punctuation():
    assert src.norm_v1(f"  Фо{A}о  Бар. ") == f"фо{A}о бар"


def test_ulif_slot_ignores_header_rows_and_non_slot_tokens():
    assert src.ulif_slot(["v_naz", "s"]) == ("v_naz", "s")
    assert src.ulif_slot(["noun", "m"]) == ("m",)  # header tokens are filtered by is_lemma, not by vocabulary
    assert src.ulif_slot(["adv"]) is None
    assert src.slot_name(("pres", "s", "1")) == "pres.s.1"


def test_vesum_slot_adds_implicit_singular_and_drops_gender_for_nouns():
    assert src.vesum_slot(["noun", "inanim", "m", "v_naz"], keep_gender=False) == ("v_naz", "s")
    assert src.vesum_slot(["adj", "m", "v_naz"], keep_gender=True) == ("v_naz", "s", "m")
    assert src.vesum_slot(["verb", "imperf", "past", "m"], keep_gender=True) == ("past", "s", "m")
    assert src.vesum_slot(["adv"], keep_gender=False) is None


def test_ulif_paradigm_withholds_asterisk_preposition_and_unmapped_slots():
    forms = [
        ulif_row(1, 7, ["v_naz", "s"], "a"),
        ulif_row(2, 7, ["v_kly", "s"], "b", marked_asterisk=1),
        ulif_row(3, 7, ["v_mis", "s"], "c", preposition="na/u"),
        ulif_row(4, 7, ["v_oru", "s"], "d", unmapped_labels='["label"]'),
        ulif_row(5, 7, ["noun", "m"], "head", is_lemma=1),
    ]
    paradigm = src.ulif_paradigm(forms)
    slots = {src.slot_name(k): v for k, v in paradigm["slots"].items()}
    assert slots["v_naz.s"]["withheld"] == []
    assert slots["v_mis.s"]["withheld"] == ["preposition_bound"]
    assert slots["v_oru.s"]["withheld"] == ["unmapped_label"]
    # An asterisk-only slot has no certain form: it leaves the form sets and is reported separately.
    assert "v_kly.s" not in slots
    assert [src.slot_name(k) for k in paradigm["uncertain_only"]] == ["v_kly.s"]
    assert "head" not in {f for item in slots.values() for f in item["forms"]}


def test_asterisk_form_never_joins_the_slot_form_set():
    forms = [ulif_row(1, 7, ["v_naz", "s"], "a"), ulif_row(2, 7, ["v_naz", "s"], "z", marked_asterisk=1)]
    slot = src.ulif_paradigm(forms)["slots"][("v_naz", "s")]
    assert slot["forms"] == ["a"]
    assert slot["uncertain"] == ["z"]
    assert slot["withheld"] == ["asterisk_marked"]


def par(**slots):
    return {"slots": {("v_" + k, "s"): {"forms": sorted(v)} for k, v in slots.items()}}


def test_compare_paradigms_is_equal_subset_or_differs():
    assert src.compare_paradigms(par(), par())["relation"] == "equal"  # two invariable sides
    assert src.compare_paradigms(par(naz=["а"], rod=["б"]), par(naz=["а"], rod=["б"]))["relation"] == "equal"
    # ULIF gives fewer slots: a subset.
    subset = src.compare_paradigms(par(naz=["а"]), par(naz=["а"], rod=["б"]))
    assert subset["relation"] == "subset" and subset["slots"][("v_rod", "s")] == "vesum_only_slot"
    assert src.compare_paradigms(par(naz=["а"]), par(naz=["б"]))["relation"] == "differs"
    # A slot VESUM does not print is a slot with a different form; no shared slot is never a match.
    extra = src.compare_paradigms(par(naz=["а"], rod=["б"]), par(naz=["а"]))
    assert extra["relation"] == "differs" and extra["slots"][("v_rod", "s")] == "ulif_only_slot"
    assert src.compare_paradigms(par(naz=["а"]), par(rod=["а"]))["relation"] == "differs"
    assert src.compare_paradigms(par(), par(naz=["а"]))["relation"] == "differs"
    assert src.compare_paradigms(None, par(naz=["а"]))["relation"] == "unknown"


def test_overlapping_form_sets_never_match_by_intersection():
    # The retained rule compares whole form sets: an extra variant on either side is a different form set.
    for ulif, vesum in ((["а", "х"], ["а"]), (["а"], ["а", "х"]), (["а", "х"], ["а", "у"])):
        result = src.compare_paradigms(par(naz=ulif), par(naz=vesum))
        assert result["relation"] == "differs" and result["slots"][("v_naz", "s")] == "differs"


def test_vesum_paradigm_keeps_source_slots_forms_and_tags():
    rows = [
        vesum_row(1, 5, "ікс", "ікс", "noun:inanim:m:v_naz"),
        vesum_row(2, 5, "ікс", "іксікс", "noun:inanim:m:v_naz:arch"),
        vesum_row(3, 5, "ікс", "ґрець", "noun:inanim:m:v_zna:ranim"),
    ]
    entry = src.vesum_paradigm(rows, keep_gender=False)[5]
    slots = {src.slot_name(k): v for k, v in entry["slots"].items()}
    # A marked variant stays a member of its own slot, tagged as VESUM prints it; no `~tag` proposition is made.
    assert {k: v["forms"] for k, v in slots.items()} == {"v_naz.s": {"ікс", "іксікс"}, "v_zna.s": {"ґрець"}}
    assert slots["v_naz.s"]["tags"] == {"noun:inanim:m:v_naz", "noun:inanim:m:v_naz:arch"}
    assert entry["aspect"] is None


def test_vesum_comment_stress_is_read_only_for_the_lemma():
    rows = [vesum_row(1, 5, "альфа", "альфа", "noun:inanim:m:v_naz", comment=f"а{A}льфа (note)"),
            vesum_row(2, 5, "альфа", "альфу", "noun:inanim:m:v_rod", comment="xv2")]
    assert src.vesum_paradigm(rows, keep_gender=False)[5]["stress"] == {f"а{A}льфа"}


def test_vesum_aspect_and_compatibility():
    assert src.vesum_aspect_of(["verb:perf:inf", "verb:perf:futr:s:1"]) == "perf"
    assert src.vesum_aspect_of(["verb:imperf:inf", "verb:perf:inf"]) == "both"
    assert src.aspect_compatible("perf", "imperf") is False
    assert src.aspect_compatible("both", "imperf") and src.aspect_compatible("perf", "both")
    assert src.aspect_compatible(None, "perf") and src.aspect_compatible("perf", None)


# --- identity matching (identity.md §4) -------------------------------------------------------------------

def homonym(head, forms, aspect=None):
    return {"head": head, "paradigm": src.ulif_paradigm(forms), "aspect": aspect}


def vesum_entry(slots, stress=(), aspect=None):
    return {"slots": {tuple(k.split(".")): {"forms": set(v), "tags": set()} for k, v in slots.items()},
            "stress": set(stress), "pos": "noun", "flags": set(), "aspect": aspect}


def forms_for(entry_id, naz, rod):
    return [ulif_row(entry_id * 10 + 1, entry_id, ["v_naz", "s"], naz), ulif_row(entry_id * 10 + 2, entry_id,
                                                                                  ["v_rod", "s"], rod)]


def test_identity_unique_match_is_high():
    ulif = {1: homonym("альфа", forms_for(1, "альфа", "альфи"))}
    match = src.match_identity(1, ulif, {10: vesum_entry({"v_naz.s": ["альфа"], "v_rod.s": ["альфи"]})})
    assert (match["confidence"], match["method"], match["vesum_entry"]) == ("high", "unique_match", 10)


def test_identity_subset_paradigm_matches():
    ulif = {1: homonym("альфа", [ulif_row(11, 1, ["v_naz", "s"], "альфа")])}
    match = src.match_identity(1, ulif, {10: vesum_entry({"v_naz.s": ["альфа"], "v_rod.s": ["альфи"]})})
    assert (match["method"], match["evidence"]["10"]["paradigm"]) == ("unique_match", "subset")


def test_identity_paradigm_separates_homographs():
    ulif = {1: homonym("альфа", forms_for(1, "альфа", "альфи")), 2: homonym("альфа", forms_for(2, "альфа", "альфу"))}
    vesum = {10: vesum_entry({"v_naz.s": ["альфа"], "v_rod.s": ["альфи"]}),
             11: vesum_entry({"v_naz.s": ["альфа"], "v_rod.s": ["альфу"]})}
    first, second = src.match_identity(1, ulif, vesum), src.match_identity(2, ulif, vesum)
    assert (first["vesum_entry"], first["method"], first["confidence"]) == (10, "paradigm_only", "high")
    assert (second["vesum_entry"], second["confidence"]) == (11, "high")


def test_identity_stress_and_paradigm_when_both_separate():
    ulif = {1: homonym(f"а{A}льфа", forms_for(1, "альфа", "альфи")),
            2: homonym(f"альфа{A}", forms_for(2, "альфа", "альфу"))}
    vesum = {10: vesum_entry({"v_naz.s": ["альфа"], "v_rod.s": ["альфи"]}, stress=[f"а{A}льфа"]),
             11: vesum_entry({"v_naz.s": ["альфа"], "v_rod.s": ["альфу"]}, stress=[f"альфа{A}"])}
    match = src.match_identity(1, ulif, vesum)
    assert (match["method"], match["confidence"], match["vesum_entry"]) == ("stress_and_paradigm", "high", 10)


def test_identity_identical_paradigms_separated_only_by_stress_are_stress_only_medium():
    # Two VESUM entries with the same paradigm; only the printed stress picks one: never high.
    ulif = {1: homonym(f"а{A}льфа", forms_for(1, "альфа", "альфи"))}
    vesum = {10: vesum_entry({"v_naz.s": ["альфа"], "v_rod.s": ["альфи"]}, stress=[f"а{A}льфа"]),
             11: vesum_entry({"v_naz.s": ["альфа"], "v_rod.s": ["альфи"]}, stress=[f"альфа{A}"])}
    match = src.match_identity(1, ulif, vesum)
    assert (match["method"], match["confidence"], match["basis"], match["vesum_entry"]) == (
        "stress_only", "medium", "stress", 10)
    # The same on the ULIF side: a homonym with the same paradigm whose stress VESUM contradicts.
    ulif = {1: homonym(f"а{A}льфа", forms_for(1, "альфа", "альфи")),
            2: homonym(f"альфа{A}", forms_for(2, "альфа", "альфи"))}
    only = src.match_identity(1, ulif, {10: vesum_entry({"v_naz.s": ["альфа"], "v_rod.s": ["альфи"]},
                                                        stress=[f"а{A}льфа"])})
    assert (only["method"], only["confidence"]) == ("stress_only", "medium")


def test_identity_dictionary_division_is_medium():
    ulif = {1: homonym("альфа", forms_for(1, "альфа", "альфи")), 2: homonym("альфа", forms_for(2, "альфа", "альфи"))}
    match = src.match_identity(1, ulif, {10: vesum_entry({"v_naz.s": ["альфа"], "v_rod.s": ["альфи"]})})
    assert (match["confidence"], match["method"], match["vesum_entry"]) == ("medium", "paradigm_only", 10)
    assert any("dictionary-division" in note for note in match["notes"])


def test_identity_stress_only_when_vesum_has_no_stress_and_ulif_heads_differ():
    ulif = {1: homonym(f"а{A}льфа", forms_for(1, "альфа", "альфи")),
            2: homonym(f"альфа{A}", forms_for(2, "альфа", "альфи"))}
    match = src.match_identity(1, ulif, {10: vesum_entry({"v_naz.s": ["альфа"], "v_rod.s": ["альфи"]})})
    assert (match["confidence"], match["method"]) == ("medium", "stress_only")


def test_identity_opposite_aspect_never_attaches():
    verb = [ulif_row(1, 1, ["inf"], "бігти")]
    ulif = {1: homonym("бігти", verb, aspect="perf")}
    imperf = {10: vesum_entry({"inf": ["бігти"]}, aspect="imperf")}
    match = src.match_identity(1, ulif, imperf)
    assert (match["vesum_entry"], match["confidence"]) == (None, "unresolved")
    assert match["evidence"]["10"] == {"paradigm": "equal", "aspect": False, "stress": None}
    # A biaspectual entry matches either aspect.
    both = src.match_identity(1, ulif, {10: vesum_entry({"inf": ["бігти"]}, aspect="both")})
    assert (both["vesum_entry"], both["method"]) == (10, "unique_match")
    # Aspect separates otherwise identical entries: the opposite-aspect candidate is excluded, not shared.
    pair = {10: vesum_entry({"inf": ["бігти"]}, aspect="imperf"), 11: vesum_entry({"inf": ["бігти"]}, aspect="perf")}
    assert src.match_identity(1, ulif, pair)["vesum_entry"] == 11


def test_identity_unresolved_when_paradigm_differs_or_vesum_is_ambiguous():
    ulif = {1: homonym("альфа", forms_for(1, "альфа", "альфи"))}
    differs = src.match_identity(1, ulif, {10: vesum_entry({"v_naz.s": ["альфа"], "v_rod.s": ["інше"]})})
    assert (differs["confidence"], differs["vesum_entry"]) == ("unresolved", None)
    assert differs["evidence"]["10"]["paradigm"] == "differs"
    both = {10: vesum_entry({"v_naz.s": ["альфа"], "v_rod.s": ["альфи"]}),
            11: vesum_entry({"v_naz.s": ["альфа"], "v_rod.s": ["альфи"]})}
    ambiguous = src.match_identity(1, ulif, both)
    assert ambiguous["confidence"] == "unresolved" and ambiguous["candidates"] == [10, 11]
    none = src.match_identity(1, ulif, {})
    assert (none["confidence"], none["method"]) == ("medium", "unresolved")


def test_identity_unknown_competitor_forms_never_make_a_match_unique():
    ulif = {1: homonym("альфа", forms_for(1, "альфа", "альфи")), 2: {"head": "альфа", "paradigm": None, "aspect": None}}
    match = src.match_identity(1, ulif, {10: vesum_entry({"v_naz.s": ["альфа"], "v_rod.s": ["альфи"]})})
    assert (match["confidence"], match["vesum_entry"]) == ("unresolved", None)


def test_identity_vesum_stress_contradiction_excludes_the_entry():
    ulif = {1: homonym(f"а{A}льфа", forms_for(1, "альфа", "альфи"))}
    vesum = {10: vesum_entry({"v_naz.s": ["альфа"], "v_rod.s": ["альфи"]}, stress=[f"альфа{A}"])}
    assert src.match_identity(1, ulif, vesum)["confidence"] == "unresolved"


# --- derived-form authentication (AC-P01) ----------------------------------------------------------------

@pytest.fixture
def held():
    sources, vesum, raw = stores()
    rows = [("називний", f"а{A}льфа", f"а{A}льфи"), ("родовий", f"а{A}льфи", f"а{A}льф")]
    add_entry(sources, raw, 1, "альфа", f"а{A}льфа", "іменник жіночого роду", rows=rows,
              sections=[("synonyms", "<p><b>а</b></p>")])
    add_entry(sources, raw, 2, "бета", f"бе{A}та", "прислівник", page=False)
    return sources, vesum, raw


def test_derived_forms_authenticate_against_the_held_page(held):
    sources = src.PilotSources(*held)
    rows = sources.forms(1)
    assert rows and sources.forms_status(1) is None
    assert {json.loads(r["grammatical_tags"])[0] for r in rows if not r["is_lemma"]} == {"v_naz", "v_rod"}
    # The runner's no-page path: one base row, a failure row, and still authenticated against the stored header.
    assert sources.forms_status(2) is None and sources.forms_failed(2) == "raw_entry_page_absent"


@pytest.mark.parametrize(("mutation", "status"), [
    ("UPDATE ulif_forms SET form_unstressed='SYNTHETIC', source_entry_fingerprint=? WHERE id=101",
     "stale_source_snapshot"),
    ("UPDATE ulif_forms SET form_unstressed='SYNTHETIC' WHERE id=101 AND ? IS NOT NULL", "content_mismatch"),
    ("UPDATE ulif_forms SET parser_version='ulif-forms-v3' WHERE id=101 AND ? IS NOT NULL", "stale_parser_version"),
    ("UPDATE ulif_forms SET source_page_sha256=? WHERE id=101", "page_lineage_mismatch"),
    ("UPDATE ulif_dictua_sections SET payload_json='{}' WHERE entry_id=1 AND ? IS NOT NULL", "stale_source_snapshot"),
    ("DELETE FROM ulif_forms WHERE id=101 AND ? IS NOT NULL", "content_mismatch"),
])
def test_inconsistent_derived_forms_are_refused(held, mutation, status):
    sources_db = held[0]
    sources_db.execute(mutation, ("0" * 64,))
    sources = src.PilotSources(*held)
    assert sources.forms(1) is None and sources.forms_status(1) == status


def test_missing_or_corrupt_raw_authority_stops_the_build(held):
    sources_db, vesum, raw = held
    manifest_sha = sources_db.execute("SELECT response_sha256 FROM ulif_dictua_entries WHERE id=1").fetchone()[0]
    page_ref = json.loads(raw.execute("SELECT body FROM ulif_dictua_raw_responses WHERE response_sha256=?",
                                      (manifest_sha,)).fetchone()[0])["paradigm"]
    raw.execute("UPDATE ulif_dictua_raw_responses SET body=? WHERE response_sha256=?", (b"tampered", page_ref[7:]))
    with pytest.raises(src.SourceAuthenticityError, match="corrupt"):
        src.PilotSources(sources_db, vesum, raw).forms(1)
    raw.execute("DELETE FROM ulif_dictua_raw_responses WHERE response_sha256=?", (page_ref[7:],))
    with pytest.raises(src.SourceAuthenticityError, match=page_ref[7:]):
        src.PilotSources(sources_db, vesum, raw).forms(1)


def test_consumed_ledger_records_rows_queries_and_absence(held):
    sources_db, vesum, raw = held
    vesum.execute("INSERT INTO vesum_build_metadata VALUES ('canonical_jsonl_sha256', ?)", ("5" * 64,))
    sources = src.PilotSources(sources_db, vesum, raw)
    sources.begin()
    sources.forms(1)
    sources.vesum_forms("альфа")  # an empty result is evidence of absence and is recorded
    first = sources.consumed_digest()
    assert set(sources.consumed) == {"ulif_forms:1", "vesum_forms:альфа"}
    vesum.execute("INSERT INTO forms_all VALUES (1, 9, 'альфа', 'альфа', 'noun', 'noun:inanim:f:v_naz', NULL, "
                  "'альфа', 'альфа')")
    changed = src.PilotSources(sources_db, vesum, raw)
    changed.begin()
    changed.forms(1)
    changed.vesum_forms("альфа")
    assert changed.consumed_digest() != first


def test_write_extract_copies_rows_verbatim_for_entries_and_siblings(tmp_path):
    source = sqlite3.connect(":memory:")
    source.executescript("""
CREATE TABLE ulif_dictua_entries (id INTEGER PRIMARY KEY, normalized_query TEXT, canonical_headword TEXT);
CREATE TABLE ulif_dictua_sections (id INTEGER PRIMARY KEY, entry_id INTEGER, kind TEXT, payload_json TEXT);
CREATE TABLE sum20_articles (id INTEGER PRIMARY KEY, headword TEXT);
CREATE TABLE sum20_senses (id INTEGER PRIMARY KEY, article_id INTEGER);
CREATE TABLE sum20_citations (id INTEGER PRIMARY KEY, article_id INTEGER);
INSERT INTO ulif_dictua_entries VALUES (1,'q','h1'),(2,'q','h2'),(3,'інше','h3');
INSERT INTO ulif_dictua_sections VALUES (10,1,'synonyms','{}'),(11,2,'synonyms','{}'),(12,3,'synonyms','{}');
INSERT INTO sum20_articles VALUES (1,'x');
""")
    out = tmp_path / "extract.sqlite"
    extracted = src.write_extract(source, [1], out)
    counts = extracted["tables"]
    assert counts["ulif_dictua_entries"] == 2  # the sibling homonym travels with the pilot entry
    assert counts["ulif_dictua_sections"] == 2
    assert counts["sum20_articles"] == 1
    copy = sqlite3.connect(out)
    assert [r[0] for r in copy.execute("SELECT id FROM ulif_dictua_entries ORDER BY id")] == [1, 2]
    # The extract is a consumed input: a changed sibling row changes its content digest.
    source.execute("UPDATE ulif_dictua_entries SET canonical_headword='h9' WHERE id=2")
    again = src.write_extract(source, [1], tmp_path / "again.sqlite")
    assert again["content_sha256"] != extracted["content_sha256"]
    assert foundation.digest(again["tables"]) == foundation.digest(counts)


@pytest.mark.parametrize("value,expected", [("Fóo", "Fóo"), ("é", "é")])
def test_nfc_is_idempotent_for_combining_marks(value, expected):
    assert src.nfc(src.nfc(value)) == src.nfc(expected)
