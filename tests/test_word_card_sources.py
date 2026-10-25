"""Source-side rules of pilot word-card assembly: stress readings, paradigm slots, identity matching, and the
authentication of derived ULIF forms against the held raw page.

Most cases use placeholder rows and minimal ULIF-shaped HTML parsed by the existing parser. The four
#11627 cases retain complete visible primary-source paradigms, with source IDs and snapshot receipts.
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


# --- #11627: exactly four granted primary-source cases ---


def test_verb_derived_slot_contamination_keeps_related_forms_separate():
    """ULIF derived rows must not become main-verb tense slots; visible variants still block identity."""
    # ULIF 258655; authenticated page cefc47dd1d1edba008612f181b28328da90cb84a5fa96fee2b799993939c3900.
    u258655 = src.ulif_paradigm([
        ulif_row(4542925, 258655, ['verb', 'imperf'], 'читати', 'чита́ти', is_lemma=1),
        ulif_row(4542926, 258655, ['inf'], 'читати', 'чита́ти'),
        ulif_row(4542927, 258655, ['impr', 'p', '1'], 'читаймо', 'чита́ймо'),
        ulif_row(4542928, 258655, ['impr', 's', '2'], 'читай', 'чита́й'),
        ulif_row(4542929, 258655, ['impr', 'p', '2'], 'читайте', 'чита́йте'),
        ulif_row(4542930, 258655, ['futr', 's', '1'], 'читатиму', 'чита́тиму'),
        ulif_row(4542931, 258655, ['futr', 'p', '1'], 'читатимемо', 'чита́тимемо'),
        ulif_row(4542932, 258655, ['futr', 'p', '1'], 'читатимем', 'чита́тимем'),
        ulif_row(4542933, 258655, ['futr', 's', '2'], 'читатимеш', 'чита́тимеш'),
        ulif_row(4542934, 258655, ['futr', 'p', '2'], 'читатимете', 'чита́тимете'),
        ulif_row(4542935, 258655, ['futr', 's', '3'], 'читатиме', 'чита́тиме'),
        ulif_row(4542936, 258655, ['futr', 'p', '3'], 'читатимуть', 'чита́тимуть'),
        ulif_row(4542937, 258655, ['pres', 's', '1'], 'читаю', 'чита́ю'),
        ulif_row(4542938, 258655, ['pres', 'p', '1'], 'читаємо', 'чита́ємо'),
        ulif_row(4542939, 258655, ['pres', 'p', '1'], 'читаєм', 'чита́єм'),
        ulif_row(4542940, 258655, ['pres', 's', '2'], 'читаєш', 'чита́єш'),
        ulif_row(4542941, 258655, ['pres', 'p', '2'], 'читаєте', 'чита́єте'),
        ulif_row(4542942, 258655, ['pres', 's', '3'], 'читає', 'чита́є'),
        ulif_row(4542943, 258655, ['pres', 'p', '3'], 'читають', 'чита́ють'),
        ulif_row(4542944, 258655, ['pres', 'advp'], 'читаючи', 'чита́ючи'),
        ulif_row(4542945, 258655, ['past', 'm', 's'], 'читав', 'чита́в'),
        ulif_row(4542946, 258655, ['past', 'p'], 'читали', 'чита́ли'),
        ulif_row(4542947, 258655, ['past', 'f', 's'], 'читала', 'чита́ла'),
        ulif_row(4542948, 258655, ['past', 'n', 's'], 'читало', 'чита́ло'),
        ulif_row(4542949, 258655, ['past', 'adjp', 'pasv'], 'читаний', 'чи́таний'),
        ulif_row(4542950, 258655, ['past', 'impers'], 'читано', 'чи́тано'),
        ulif_row(4542951, 258655, ['past', 'advp'], 'читавши', 'чита́вши'),
    ])
    # Complete visible VESUM rows; canonical snapshot 53923150073b4fc7bee419fe7b071acbe17b6a9aba76cfb2d0336c95f5188680.
    v = src.vesum_paradigm([
        vesum_row(6561736, 420694, 'читати', 'читати', 'verb:imperf:inf', 'rv_zna:rv_oru:rv_dav', pos='verb'),
        vesum_row(6561737, 420694, 'читати', 'читать', 'verb:imperf:inf:short', 'rv_zna:rv_oru:rv_dav', pos='verb'),
        vesum_row(6561738, 420694, 'читати', 'читай', 'verb:imperf:impr:s:2', 'rv_zna:rv_oru:rv_dav', pos='verb'),
        vesum_row(6561739, 420694, 'читати', 'читаймо', 'verb:imperf:impr:p:1', 'rv_zna:rv_oru:rv_dav', pos='verb'),
        vesum_row(6561740, 420694, 'читати', 'читайте', 'verb:imperf:impr:p:2', 'rv_zna:rv_oru:rv_dav', pos='verb'),
        vesum_row(6561741, 420694, 'читати', 'читаю', 'verb:imperf:pres:s:1', 'rv_zna:rv_oru:rv_dav', pos='verb'),
        vesum_row(6561742, 420694, 'читати', 'читаєш', 'verb:imperf:pres:s:2', 'rv_zna:rv_oru:rv_dav', pos='verb'),
        vesum_row(6561743, 420694, 'читати', 'читає', 'verb:imperf:pres:s:3', 'rv_zna:rv_oru:rv_dav', pos='verb'),
        vesum_row(6561744, 420694, 'читати', 'чита', 'verb:imperf:pres:s:3:short', 'rv_zna:rv_oru:rv_dav', pos='verb'),
        vesum_row(6561745, 420694, 'читати', 'читаємо', 'verb:imperf:pres:p:1', 'rv_zna:rv_oru:rv_dav', pos='verb'),
        vesum_row(6561747, 420694, 'читати', 'читаєте', 'verb:imperf:pres:p:2', 'rv_zna:rv_oru:rv_dav', pos='verb'),
        vesum_row(6561748, 420694, 'читати', 'читають', 'verb:imperf:pres:p:3', 'rv_zna:rv_oru:rv_dav', pos='verb'),
        vesum_row(6561749, 420694, 'читати', 'читатиму', 'verb:imperf:futr:s:1', 'rv_zna:rv_oru:rv_dav', pos='verb'),
        vesum_row(6561750, 420694, 'читати', 'читатимеш', 'verb:imperf:futr:s:2', 'rv_zna:rv_oru:rv_dav', pos='verb'),
        vesum_row(6561751, 420694, 'читати', 'читатиме', 'verb:imperf:futr:s:3', 'rv_zna:rv_oru:rv_dav', pos='verb'),
        vesum_row(6561752, 420694, 'читати', 'читатимем', 'verb:imperf:futr:p:1', 'rv_zna:rv_oru:rv_dav', pos='verb'),
        vesum_row(6561753, 420694, 'читати', 'читатимемо', 'verb:imperf:futr:p:1', 'rv_zna:rv_oru:rv_dav', pos='verb'),
        vesum_row(6561754, 420694, 'читати', 'читатимете', 'verb:imperf:futr:p:2', 'rv_zna:rv_oru:rv_dav', pos='verb'),
        vesum_row(6561755, 420694, 'читати', 'читатимуть', 'verb:imperf:futr:p:3', 'rv_zna:rv_oru:rv_dav', pos='verb'),
        vesum_row(6561756, 420694, 'читати', 'читав', 'verb:imperf:past:m', 'rv_zna:rv_oru:rv_dav', pos='verb'),
        vesum_row(6561757, 420694, 'читати', 'читала', 'verb:imperf:past:f', 'rv_zna:rv_oru:rv_dav', pos='verb'),
        vesum_row(6561758, 420694, 'читати', 'читало', 'verb:imperf:past:n', 'rv_zna:rv_oru:rv_dav', pos='verb'),
        vesum_row(6561759, 420694, 'читати', 'читали', 'verb:imperf:past:p', 'rv_zna:rv_oru:rv_dav', pos='verb'),
        vesum_row(6561760, 420694, 'читати', 'читано', 'verb:imperf:impers', 'rv_zna:rv_oru:rv_dav', pos='verb'),
    ], keep_gender=True)
    assert ('pres',) not in u258655['slots'] and ('past',) not in u258655['slots']
    assert {row['id'] for row in u258655['related']} == {4542944, 4542949, 4542950, 4542951}
    assert {row['form_unstressed'] for row in u258655['related']} == {'читаючи', 'читаний', 'читано', 'читавши'}
    compared = src.compare_paradigms(u258655, v[420694])
    assert 'ulif_only_slot' not in compared['slots'].values()
    assert compared['relation'] == 'differs'
    assert compared['slots'][('inf',)] == 'differs'
    assert compared['slots'][('pres', 'p', '1')] == 'differs'


def test_comparative_degree_control_preserves_complete_variant_sets():
    """The captured comparative already shares slots; its long variants remain incompatible."""
    # ULIF 268912; authenticated page e655c4bde46c2f2682cec18297071637b02baf58da1cc4dc31a464aea0936c7d.
    u268912 = src.ulif_paradigm([
        ulif_row(4735647, 268912, [], 'яскравіший', 'яскра́віший', is_lemma=1, unmapped_labels='["прикметник, вищий ступінь"]'),
        ulif_row(4735648, 268912, ['v_naz', 's', 'm'], 'яскравіший', 'яскра́віший'),
        ulif_row(4735649, 268912, ['v_naz', 's', 'f'], 'яскравіша', 'яскра́віша'),
        ulif_row(4735650, 268912, ['v_naz', 's', 'n'], 'яскравіше', 'яскра́віше'),
        ulif_row(4735651, 268912, ['v_naz', 'p'], 'яскравіші', 'яскра́віші'),
        ulif_row(4735652, 268912, ['v_rod', 's', 'm'], 'яскравішого', 'яскра́вішого'),
        ulif_row(4735653, 268912, ['v_rod', 's', 'f'], 'яскравішої', 'яскра́вішої'),
        ulif_row(4735654, 268912, ['v_rod', 's', 'n'], 'яскравішого', 'яскра́вішого'),
        ulif_row(4735655, 268912, ['v_rod', 'p'], 'яскравіших', 'яскра́віших'),
        ulif_row(4735656, 268912, ['v_dav', 's', 'm'], 'яскравішому', 'яскра́вішому'),
        ulif_row(4735657, 268912, ['v_dav', 's', 'f'], 'яскравішій', 'яскра́вішій'),
        ulif_row(4735658, 268912, ['v_dav', 's', 'n'], 'яскравішому', 'яскра́вішому'),
        ulif_row(4735659, 268912, ['v_dav', 'p'], 'яскравішим', 'яскра́вішим'),
        ulif_row(4735660, 268912, ['v_zna', 's', 'm'], 'яскравіший', 'яскра́віший'),
        ulif_row(4735661, 268912, ['v_zna', 's', 'm'], 'яскравішого', 'яскра́вішого'),
        ulif_row(4735662, 268912, ['v_zna', 's', 'f'], 'яскравішу', 'яскра́вішу'),
        ulif_row(4735663, 268912, ['v_zna', 's', 'n'], 'яскравіше', 'яскра́віше'),
        ulif_row(4735664, 268912, ['v_zna', 'p'], 'яскравіші', 'яскра́віші'),
        ulif_row(4735665, 268912, ['v_zna', 'p'], 'яскравіших', 'яскра́віших'),
        ulif_row(4735666, 268912, ['v_oru', 's', 'm'], 'яскравішим', 'яскра́вішим'),
        ulif_row(4735667, 268912, ['v_oru', 's', 'f'], 'яскравішою', 'яскра́вішою'),
        ulif_row(4735668, 268912, ['v_oru', 's', 'n'], 'яскравішим', 'яскра́вішим'),
        ulif_row(4735669, 268912, ['v_oru', 'p'], 'яскравішими', 'яскра́вішими'),
        ulif_row(4735670, 268912, ['v_mis', 's', 'm'], 'яскравішому', 'яскра́вішому', preposition='на/у'),
        ulif_row(4735671, 268912, ['v_mis', 's', 'm'], 'яскравішім', 'яскра́вішім', preposition='на/у'),
        ulif_row(4735672, 268912, ['v_mis', 's', 'f'], 'яскравішій', 'яскра́вішій', preposition='на/у'),
        ulif_row(4735673, 268912, ['v_mis', 's', 'n'], 'яскравішому', 'яскра́вішому', preposition='на/у'),
        ulif_row(4735674, 268912, ['v_mis', 's', 'n'], 'яскравішім', 'яскра́вішім', preposition='на/у'),
        ulif_row(4735675, 268912, ['v_mis', 'p'], 'яскравіших', 'яскра́віших', preposition='на/у'),
    ])
    # Complete visible VESUM rows; canonical snapshot 53923150073b4fc7bee419fe7b071acbe17b6a9aba76cfb2d0336c95f5188680.
    v = src.vesum_paradigm([
        vesum_row(6964175, 442056, 'яскравіший', 'яскравіший', 'adj:m:v_naz:compc', None, pos='adj'),
        vesum_row(6964176, 442056, 'яскравіший', 'яскравішого', 'adj:m:v_rod:compc', None, pos='adj'),
        vesum_row(6964177, 442056, 'яскравіший', 'яскравішому', 'adj:m:v_dav:compc', None, pos='adj'),
        vesum_row(6964178, 442056, 'яскравіший', 'яскравішого', 'adj:m:v_zna:ranim:compc', None, pos='adj'),
        vesum_row(6964179, 442056, 'яскравіший', 'яскравіший', 'adj:m:v_zna:rinanim:compc', None, pos='adj'),
        vesum_row(6964180, 442056, 'яскравіший', 'яскравішим', 'adj:m:v_oru:compc', None, pos='adj'),
        vesum_row(6964181, 442056, 'яскравіший', 'яскравішім', 'adj:m:v_mis:compc', None, pos='adj'),
        vesum_row(6964182, 442056, 'яскравіший', 'яскравішому', 'adj:m:v_mis:compc', None, pos='adj'),
        vesum_row(6964183, 442056, 'яскравіший', 'яскравіший', 'adj:m:v_kly:compc', None, pos='adj'),
        vesum_row(6964184, 442056, 'яскравіший', 'яскравіша', 'adj:f:v_naz:compc', None, pos='adj'),
        vesum_row(6964185, 442056, 'яскравіший', 'яскравішая', 'adj:f:v_naz:compc:long', None, pos='adj'),
        vesum_row(6964186, 442056, 'яскравіший', 'яскравішої', 'adj:f:v_rod:compc', None, pos='adj'),
        vesum_row(6964187, 442056, 'яскравіший', 'яскравішій', 'adj:f:v_dav:compc', None, pos='adj'),
        vesum_row(6964188, 442056, 'яскравіший', 'яскравішу', 'adj:f:v_zna:compc', None, pos='adj'),
        vesum_row(6964189, 442056, 'яскравіший', 'яскравішую', 'adj:f:v_zna:compc:long', None, pos='adj'),
        vesum_row(6964190, 442056, 'яскравіший', 'яскравішою', 'adj:f:v_oru:compc', None, pos='adj'),
        vesum_row(6964191, 442056, 'яскравіший', 'яскравішій', 'adj:f:v_mis:compc', None, pos='adj'),
        vesum_row(6964192, 442056, 'яскравіший', 'яскравіша', 'adj:f:v_kly:compc', None, pos='adj'),
        vesum_row(6964193, 442056, 'яскравіший', 'яскравішая', 'adj:f:v_kly:compc:long', None, pos='adj'),
        vesum_row(6964194, 442056, 'яскравіший', 'яскравіше', 'adj:n:v_naz:compc', None, pos='adj'),
        vesum_row(6964195, 442056, 'яскравіший', 'яскравішеє', 'adj:n:v_naz:compc:long', None, pos='adj'),
        vesum_row(6964196, 442056, 'яскравіший', 'яскравішого', 'adj:n:v_rod:compc', None, pos='adj'),
        vesum_row(6964197, 442056, 'яскравіший', 'яскравішому', 'adj:n:v_dav:compc', None, pos='adj'),
        vesum_row(6964198, 442056, 'яскравіший', 'яскравіше', 'adj:n:v_zna:compc', None, pos='adj'),
        vesum_row(6964199, 442056, 'яскравіший', 'яскравішеє', 'adj:n:v_zna:compc:long', None, pos='adj'),
        vesum_row(6964200, 442056, 'яскравіший', 'яскравішим', 'adj:n:v_oru:compc', None, pos='adj'),
        vesum_row(6964201, 442056, 'яскравіший', 'яскравішім', 'adj:n:v_mis:compc', None, pos='adj'),
        vesum_row(6964202, 442056, 'яскравіший', 'яскравішому', 'adj:n:v_mis:compc', None, pos='adj'),
        vesum_row(6964203, 442056, 'яскравіший', 'яскравіше', 'adj:n:v_kly:compc', None, pos='adj'),
        vesum_row(6964204, 442056, 'яскравіший', 'яскравішеє', 'adj:n:v_kly:compc:long', None, pos='adj'),
        vesum_row(6964205, 442056, 'яскравіший', 'яскравіші', 'adj:p:v_naz:compc', None, pos='adj'),
        vesum_row(6964206, 442056, 'яскравіший', 'яскравішії', 'adj:p:v_naz:compc:long', None, pos='adj'),
        vesum_row(6964207, 442056, 'яскравіший', 'яскравіших', 'adj:p:v_rod:compc', None, pos='adj'),
        vesum_row(6964208, 442056, 'яскравіший', 'яскравішим', 'adj:p:v_dav:compc', None, pos='adj'),
        vesum_row(6964209, 442056, 'яскравіший', 'яскравіших', 'adj:p:v_zna:ranim:compc', None, pos='adj'),
        vesum_row(6964210, 442056, 'яскравіший', 'яскравіші', 'adj:p:v_zna:rinanim:compc', None, pos='adj'),
        vesum_row(6964211, 442056, 'яскравіший', 'яскравішії', 'adj:p:v_zna:rinanim:compc:long', None, pos='adj'),
        vesum_row(6964212, 442056, 'яскравіший', 'яскравішими', 'adj:p:v_oru:compc', None, pos='adj'),
        vesum_row(6964213, 442056, 'яскравіший', 'яскравіших', 'adj:p:v_mis:compc', None, pos='adj'),
        vesum_row(6964214, 442056, 'яскравіший', 'яскравіші', 'adj:p:v_kly:compc', None, pos='adj'),
        vesum_row(6964215, 442056, 'яскравіший', 'яскравішії', 'adj:p:v_kly:compc:long', None, pos='adj'),
    ], keep_gender=True)
    assert ('v_naz', 's', 'm') in u268912['slots'] and ('v_naz', 's', 'm') in v[442056]['slots']
    compared = src.compare_paradigms(u268912, v[442056])
    assert compared['slots'][('v_naz', 's', 'm')] == 'equal'
    assert compared['slots'][('v_naz', 's', 'f')] == 'differs'
    assert compared['relation'] == 'differs'
    assert v[442056]['slots'][('v_naz', 's', 'f')]['forms'] == {'яскравіша', 'яскравішая'}


def test_personal_pronoun_person_is_not_a_case_slot_dimension():
    """Person and an implicit single number must correspond without erasing archaic or bound forms."""
    # ULIF 247362; authenticated page 79fd8538128cffffacf5851d81a7c7814e3a5a2c93071ca4b95d18333d505e9c.
    u247362 = src.ulif_paradigm([
        ulif_row(4351970, 247362, [], 'я', 'я', is_lemma=1, unmapped_labels='["займенник"]'),
        ulif_row(4351971, 247362, ['v_naz'], 'я', 'я'),
        ulif_row(4351972, 247362, ['v_rod'], 'мене', 'мене́'),
        ulif_row(4351973, 247362, ['v_rod'], 'до мене', 'до ме́не'),
        ulif_row(4351974, 247362, ['v_dav'], 'мені', 'мені́'),
        ulif_row(4351975, 247362, ['v_zna'], 'мене', 'мене́'),
        ulif_row(4351976, 247362, ['v_oru'], 'мною', 'мно́ю'),
        ulif_row(4351977, 247362, ['v_mis'], 'мені', 'мені́', preposition='на/у'),
    ])
    # Complete visible VESUM rows; canonical snapshot 53923150073b4fc7bee419fe7b071acbe17b6a9aba76cfb2d0336c95f5188680.
    v = src.vesum_paradigm([
        vesum_row(6863508, 436573, 'я', 'я', 'noun:anim:s:v_naz:pron:pers:1', None, pos='noun'),
        vesum_row(6863509, 436573, 'я', 'мене', 'noun:anim:s:v_rod:pron:pers:1', None, pos='noun'),
        vesum_row(6863510, 436573, 'я', 'мя', 'noun:anim:s:v_rod:pron:pers:1:arch', None, pos='noun'),
        vesum_row(6863511, 436573, 'я', 'мені', 'noun:anim:s:v_dav:pron:pers:1', None, pos='noun'),
        vesum_row(6863512, 436573, 'я', 'мене', 'noun:anim:s:v_zna:pron:pers:1', None, pos='noun'),
        vesum_row(6863513, 436573, 'я', 'мя', 'noun:anim:s:v_zna:pron:pers:1:arch', None, pos='noun'),
        vesum_row(6863514, 436573, 'я', 'мною', 'noun:anim:s:v_oru:pron:pers:1', None, pos='noun'),
        vesum_row(6863515, 436573, 'я', 'мені', 'noun:anim:s:v_mis:pron:pers:1', None, pos='noun'),
    ], keep_gender=False)
    u247362['pronoun'] = True  # the checked ULIF label is займенник
    assert all('1' not in slot for slot in v[436573]['slots'])
    compared = src.compare_paradigms(u247362, v[436573])
    assert compared['slots'][('v_naz', 's')] == 'equal'
    assert 'ulif_only_slot' not in compared['slots'].values()
    assert compared['relation'] == 'differs'
    assert compared['slots'][('v_rod', 's')] == 'differs'
    assert compared['slots'][('v_zna', 's')] == 'differs'
    assert u247362['slots'][('v_rod',)]['forms'] == ['до мене', 'мене']
    assert v[436573]['slots'][('v_rod', 's')]['forms'] == {'мене', 'мя'}


def test_animate_noun_control_keeps_inanimate_homonym_incompatible():
    """Animacy already differs in the accusative; an extra locative still blocks the animate match."""
    # ULIF 22123; authenticated page faf408c1729b80c6341fb98b50738cb6078214b4f9398974caa62b401c24c269.
    u22123 = src.ulif_paradigm([
        ulif_row(241241, 22123, [], 'баран', 'бара́н', is_lemma=1, unmapped_labels='["іменник чоловічого роду, істота"]'),
        ulif_row(241242, 22123, ['v_naz', 's'], 'баран', 'бара́н'),
        ulif_row(241243, 22123, ['v_naz', 'p'], 'барани', 'барани́'),
        ulif_row(241244, 22123, ['v_rod', 's'], 'барана', 'барана́'),
        ulif_row(241245, 22123, ['v_rod', 'p'], 'баранів', 'барані́в'),
        ulif_row(241246, 22123, ['v_dav', 's'], 'баранові', 'барано́ві'),
        ulif_row(241247, 22123, ['v_dav', 's'], 'барану', 'барану́'),
        ulif_row(241248, 22123, ['v_dav', 'p'], 'баранам', 'барана́м'),
        ulif_row(241249, 22123, ['v_zna', 's'], 'барана', 'барана́'),
        ulif_row(241250, 22123, ['v_zna', 'p'], 'барани', 'барани́'),
        ulif_row(241251, 22123, ['v_zna', 'p'], 'баранів', 'барані́в'),
        ulif_row(241252, 22123, ['v_oru', 's'], 'бараном', 'барано́м'),
        ulif_row(241253, 22123, ['v_oru', 'p'], 'баранами', 'барана́ми'),
        ulif_row(241254, 22123, ['v_mis', 's'], 'баранові', 'барано́ві', preposition='на/у'),
        ulif_row(241255, 22123, ['v_mis', 's'], 'барані', 'барані́', preposition='на/у'),
        ulif_row(241256, 22123, ['v_mis', 'p'], 'баранах', 'барана́х', preposition='на/у'),
        ulif_row(241257, 22123, ['v_kly', 's'], 'баране', 'бара́не'),
        ulif_row(241258, 22123, ['v_kly', 'p'], 'барани', 'барани́'),
    ])
    # ULIF 22124; authenticated page 4183d30b8d48d31e26c59c34acbf183a3668eef8943b0b4759c93b5145c82c27.
    u22124 = src.ulif_paradigm([
        ulif_row(241259, 22124, [], 'баран', 'бара́н', is_lemma=1, unmapped_labels='["іменник чоловічого роду, істота"]'),
        ulif_row(241260, 22124, ['v_naz', 's'], 'баран', 'бара́н'),
        ulif_row(241261, 22124, ['v_naz', 'p'], 'барани', 'барани́'),
        ulif_row(241262, 22124, ['v_rod', 's'], 'барана', 'барана́'),
        ulif_row(241263, 22124, ['v_rod', 'p'], 'баранів', 'барані́в'),
        ulif_row(241264, 22124, ['v_dav', 's'], 'баранові', 'барано́ві'),
        ulif_row(241265, 22124, ['v_dav', 's'], 'барану', 'барану́'),
        ulif_row(241266, 22124, ['v_dav', 'p'], 'баранам', 'барана́м'),
        ulif_row(241267, 22124, ['v_zna', 's'], 'барана', 'барана́'),
        ulif_row(241268, 22124, ['v_zna', 'p'], 'баранів', 'барані́в'),
        ulif_row(241269, 22124, ['v_oru', 's'], 'бараном', 'барано́м'),
        ulif_row(241270, 22124, ['v_oru', 'p'], 'баранами', 'барана́ми'),
        ulif_row(241271, 22124, ['v_mis', 's'], 'баранові', 'барано́ві', preposition='на/у'),
        ulif_row(241272, 22124, ['v_mis', 's'], 'барані', 'барані́', preposition='на/у'),
        ulif_row(241273, 22124, ['v_mis', 'p'], 'баранах', 'барана́х', preposition='на/у'),
        ulif_row(241274, 22124, ['v_kly', 's'], 'баране', 'бара́не'),
        ulif_row(241275, 22124, ['v_kly', 'p'], 'барани', 'барани́'),
    ])
    # ULIF 22125; authenticated page d0cec30c83c0505c51144f459c0222db80df644913a8c7e8f6d59877f4026673.
    u22125 = src.ulif_paradigm([
        ulif_row(241276, 22125, ['noun', 'm'], 'баран', 'бара́н', is_lemma=1),
        ulif_row(241277, 22125, ['v_naz', 's'], 'баран', 'бара́н'),
        ulif_row(241278, 22125, ['v_naz', 'p'], 'барани', 'барани́'),
        ulif_row(241279, 22125, ['v_rod', 's'], 'барана', 'барана́'),
        ulif_row(241280, 22125, ['v_rod', 'p'], 'баранів', 'барані́в'),
        ulif_row(241281, 22125, ['v_dav', 's'], 'барану', 'барану́'),
        ulif_row(241282, 22125, ['v_dav', 's'], 'баранові', 'барано́ві'),
        ulif_row(241283, 22125, ['v_dav', 'p'], 'баранам', 'барана́м'),
        ulif_row(241284, 22125, ['v_zna', 's'], 'баран', 'бара́н'),
        ulif_row(241285, 22125, ['v_zna', 'p'], 'барани', 'барани́'),
        ulif_row(241286, 22125, ['v_oru', 's'], 'бараном', 'барано́м'),
        ulif_row(241287, 22125, ['v_oru', 'p'], 'баранами', 'барана́ми'),
        ulif_row(241288, 22125, ['v_mis', 's'], 'барані', 'барані́', preposition='на/у'),
        ulif_row(241289, 22125, ['v_mis', 'p'], 'баранах', 'барана́х', preposition='на/у'),
        ulif_row(241290, 22125, ['v_kly', 's'], 'баране', 'бара́не', marked_asterisk=1),
        ulif_row(241291, 22125, ['v_kly', 'p'], 'барани', 'барани́', marked_asterisk=1),
    ])
    # Complete visible VESUM rows; canonical snapshot 53923150073b4fc7bee419fe7b071acbe17b6a9aba76cfb2d0336c95f5188680.
    v = src.vesum_paradigm([
        vesum_row(293437, 17249, 'баран', 'баран', 'noun:anim:m:v_naz', ':xp1 xv2 самець вівці, про нерозумну людину', pos='noun'),
        vesum_row(293438, 17249, 'баран', 'барана', 'noun:anim:m:v_rod', ':xp1 xv2 самець вівці, про нерозумну людину', pos='noun'),
        vesum_row(293439, 17249, 'баран', 'баранові', 'noun:anim:m:v_dav', ':xp1 xv2 самець вівці, про нерозумну людину', pos='noun'),
        vesum_row(293440, 17249, 'баран', 'барану', 'noun:anim:m:v_dav', ':xp1 xv2 самець вівці, про нерозумну людину', pos='noun'),
        vesum_row(293441, 17249, 'баран', 'барана', 'noun:anim:m:v_zna', ':xp1 xv2 самець вівці, про нерозумну людину', pos='noun'),
        vesum_row(293442, 17249, 'баран', 'бараном', 'noun:anim:m:v_oru', ':xp1 xv2 самець вівці, про нерозумну людину', pos='noun'),
        vesum_row(293443, 17249, 'баран', 'барані', 'noun:anim:m:v_mis', ':xp1 xv2 самець вівці, про нерозумну людину', pos='noun'),
        vesum_row(293444, 17249, 'баран', 'баранові', 'noun:anim:m:v_mis', ':xp1 xv2 самець вівці, про нерозумну людину', pos='noun'),
        vesum_row(293445, 17249, 'баран', 'барану', 'noun:anim:m:v_mis', ':xp1 xv2 самець вівці, про нерозумну людину', pos='noun'),
        vesum_row(293446, 17249, 'баран', 'баране', 'noun:anim:m:v_kly', ':xp1 xv2 самець вівці, про нерозумну людину', pos='noun'),
        vesum_row(293447, 17249, 'баран', 'барани', 'noun:anim:p:v_naz', ':xp1 xv2 самець вівці, про нерозумну людину', pos='noun'),
        vesum_row(293448, 17249, 'баран', 'баранів', 'noun:anim:p:v_rod', ':xp1 xv2 самець вівці, про нерозумну людину', pos='noun'),
        vesum_row(293449, 17249, 'баран', 'баранам', 'noun:anim:p:v_dav', ':xp1 xv2 самець вівці, про нерозумну людину', pos='noun'),
        vesum_row(293450, 17249, 'баран', 'барани', 'noun:anim:p:v_zna', ':xp1 xv2 самець вівці, про нерозумну людину', pos='noun'),
        vesum_row(293451, 17249, 'баран', 'баранів', 'noun:anim:p:v_zna', ':xp1 xv2 самець вівці, про нерозумну людину', pos='noun'),
        vesum_row(293452, 17249, 'баран', 'баранами', 'noun:anim:p:v_oru', ':xp1 xv2 самець вівці, про нерозумну людину', pos='noun'),
        vesum_row(293453, 17249, 'баран', 'баранах', 'noun:anim:p:v_mis', ':xp1 xv2 самець вівці, про нерозумну людину', pos='noun'),
        vesum_row(293454, 17249, 'баран', 'барани', 'noun:anim:p:v_kly', ':xp1 xv2 самець вівці, про нерозумну людину', pos='noun'),
        vesum_row(293455, 17250, 'баран', 'баран', 'noun:inanim:m:v_naz', ':xp2 гребінь замету', pos='noun'),
        vesum_row(293456, 17250, 'баран', 'барана', 'noun:inanim:m:v_rod', ':xp2 гребінь замету', pos='noun'),
        vesum_row(293457, 17250, 'баран', 'баранові', 'noun:inanim:m:v_dav', ':xp2 гребінь замету', pos='noun'),
        vesum_row(293458, 17250, 'баран', 'барану', 'noun:inanim:m:v_dav', ':xp2 гребінь замету', pos='noun'),
        vesum_row(293459, 17250, 'баран', 'баран', 'noun:inanim:m:v_zna', ':xp2 гребінь замету', pos='noun'),
        vesum_row(293460, 17250, 'баран', 'бараном', 'noun:inanim:m:v_oru', ':xp2 гребінь замету', pos='noun'),
        vesum_row(293461, 17250, 'баран', 'барані', 'noun:inanim:m:v_mis', ':xp2 гребінь замету', pos='noun'),
        vesum_row(293462, 17250, 'баран', 'баранові', 'noun:inanim:m:v_mis', ':xp2 гребінь замету', pos='noun'),
        vesum_row(293463, 17250, 'баран', 'барану', 'noun:inanim:m:v_mis', ':xp2 гребінь замету', pos='noun'),
        vesum_row(293464, 17250, 'баран', 'баране', 'noun:inanim:m:v_kly', ':xp2 гребінь замету', pos='noun'),
        vesum_row(293465, 17250, 'баран', 'барани', 'noun:inanim:p:v_naz', ':xp2 гребінь замету', pos='noun'),
        vesum_row(293466, 17250, 'баран', 'баранів', 'noun:inanim:p:v_rod', ':xp2 гребінь замету', pos='noun'),
        vesum_row(293467, 17250, 'баран', 'баранам', 'noun:inanim:p:v_dav', ':xp2 гребінь замету', pos='noun'),
        vesum_row(293468, 17250, 'баран', 'барани', 'noun:inanim:p:v_zna', ':xp2 гребінь замету', pos='noun'),
        vesum_row(293469, 17250, 'баран', 'баранами', 'noun:inanim:p:v_oru', ':xp2 гребінь замету', pos='noun'),
        vesum_row(293470, 17250, 'баран', 'баранах', 'noun:inanim:p:v_mis', ':xp2 гребінь замету', pos='noun'),
        vesum_row(293471, 17250, 'баран', 'барани', 'noun:inanim:p:v_kly', ':xp2 гребінь замету', pos='noun'),
    ], keep_gender=False)
    animate = src.compare_paradigms(u22123, v[17249])
    inanimate = src.compare_paradigms(u22123, v[17250])
    assert animate['slots'][('v_zna', 's')] == 'equal'
    assert inanimate['slots'][('v_zna', 's')] == 'differs'
    assert animate['slots'][('v_mis', 's')] == 'differs'
    assert animate['relation'] == inanimate['relation'] == 'differs'
    assert src.compare_paradigms(u22124, v[17250])['slots'][('v_zna', 's')] == 'differs'
    assert src.compare_paradigms(u22125, v[17249])['slots'][('v_zna', 's')] == 'differs'
