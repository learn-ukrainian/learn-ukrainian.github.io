"""Receipt admission proves source existence, independently of YAML/lock shape."""

import copy
import sqlite3

import pytest

from scripts.build.fresh.requires_confirm import record_answers
from scripts.build.fresh.runner import check_7_a1_choices
from scripts.curriculum.evidence import lock
from scripts.curriculum.evidence.sources import Sources, batch_digest
from scripts.curriculum.resolver import codes, receipts
from scripts.curriculum.resolver.inputs import ResolverError
from tests.curriculum.resolver.evidence_helpers import receipt_sources  # noqa: F401

IDS = {
    "vesum": "vesum:487702-487719",
    "pravopys": "pravopys:53",
    "textbook": "textbook:real-chunk",
    "grinchenko": "grinchenko:11367",
    "sum20": "sum20:2319",
    "vts": "vts:1",
    "ulif": "ulif:18",
}


@pytest.fixture(autouse=True)
def pravopys_fixture(monkeypatch):
    from scripts.rag import source_query

    def section(number, **kwargs):
        return {"section": number, "url": f"fixture/sections/{number}/", "text": "one two fixture rule"} if number == 53 else None

    monkeypatch.setattr(source_query, "pravopys_section", section)


def test_folded_lookup_columns_do_not_change_cited_source_rows_or_digests(request):
    _, db = request.getfixturevalue("receipt_sources")
    eid = IDS["vesum"]
    with Sources(vesum_db=db) as api:
        before = api.resolve_evidence_ids([eid])
    assert before.raw[eid]
    with sqlite3.connect(db) as conn:
        conn.execute("ALTER TABLE forms_all ADD COLUMN word_form_folded TEXT")
        conn.execute("ALTER TABLE forms_all ADD COLUMN lemma_folded TEXT")
        conn.execute("UPDATE forms_all SET word_form_folded = lower(word_form), lemma_folded = lower(lemma)")
    with Sources(vesum_db=db) as api:
        after = api.resolve_evidence_ids([eid])
    assert after.raw == before.raw
    assert after.content_hash == before.content_hash


def document(eid):
    return {
        "requirements_schema": 2,
        "lesson": {"level": "a1", "slug": "sample", "n": 1},
        "inputs": {"draft_sha256": "a" * 64},
        "items": [{
            "activity": "a1", "item": 0, "requires": {"Case": "Acc"},
            "payload_sha256": receipts.requirement_payload_sha256("___", ["one", "two"], 0, {"Case": "Acc"}),
            "decision": "confirm", "reason": "fixture source", "requires_forced": True,
            "options": [
                {"text": "one", "judgement": "valid", "evidence": [eid]},
                {"text": "two", "judgement": "invalid", "evidence": [eid]},
            ],
            "writer": {"seat": "codex@sol", "family": "openai"},
            "reviewer": {"seat": "claude@sonnet", "family": "anthropic", "lane": "language"},
        }],
    }


def status(doc, state, sources):
    row = doc["items"][0]
    return receipts.requirement_status(
        doc, lesson=doc["lesson"], state_dir=state, inputs=doc["inputs"], activity="a1", item=0,
        payload_sha256=row["payload_sha256"], options=["one", "two"], key_index=0, requires=row["requires"], sources=sources,
    )


def record(doc, state, sources):
    row = doc["items"][0]
    batch = {"lesson": doc["lesson"], "inputs": doc["inputs"], "questions": [{
        "activity": "a1", "item": 0, "requires": row["requires"], "payload_sha256": row["payload_sha256"],
        "options": [option["text"] for option in row["options"]], "key_index": 0,
    }]}
    answers = {"answers": [{k: row[k] for k in ("activity", "item", "decision", "reason", "requires_forced", "options")}]}
    return record_answers(
        batch, answers, seat="claude@sonnet", family="anthropic", writer_seat="codex@sol", writer_family="openai",
        state_dir=state, sources=sources,
    )


@pytest.mark.parametrize("kind", IDS)
def test_real_fixture_id_passes_record_publication_read_and_status(tmp_path, kind):
    doc = document(IDS[kind])
    (tmp_path / "lesson-1.writer.yaml").write_text("model: gpt-6.1-sol\n")
    path = receipts.requirement_receipt_path(tmp_path, 1)
    with Sources() as api:
        assert record(doc, tmp_path, api) == doc
        receipts.write_requirement_receipts(path, doc, sources=api)
    with Sources() as api:
        assert receipts.read_requirement_receipts(path, sources=api) == doc
        assert status(doc, tmp_path, api) == "confirmed"


@pytest.mark.parametrize("kind", IDS)
@pytest.mark.parametrize("suffix", ["anything", "999999999"])
def test_fabricated_id_refuses_at_every_entry_point(tmp_path, kind, suffix):
    doc = document(f"{kind}:{suffix}")
    path = receipts.requirement_receipt_path(tmp_path, 1)
    (tmp_path / "lesson-1.writer.yaml").write_text("model: gpt-6.1-sol\n")
    with Sources() as api:
        for action in (
            lambda: record(doc, tmp_path, api),
            lambda: receipts.write_requirement_receipts(path, doc, sources=api),
            lambda: status(doc, tmp_path, api),
        ):
            with pytest.raises(ResolverError) as caught:
                action()
            assert caught.value.code == codes.EVIDENCE_ID_UNRESOLVED
        assert not path.exists()
        # A valid lock proves publication bytes only; it cannot authorize a fake citation.
        lock.write(path, lock.yaml_bytes(doc))
        with pytest.raises(ResolverError) as caught:
            receipts.read_requirement_receipts(path, sources=api)
        assert caught.value.code == codes.EVIDENCE_ID_UNRESOLVED


@pytest.mark.parametrize("kind", IDS)
def test_store_outage_refuses_at_record_and_gate(tmp_path, kind, monkeypatch):
    from scripts.rag import source_query

    doc = document(IDS[kind])
    (tmp_path / "lesson-1.writer.yaml").write_text("model: gpt-6.1-sol\n")
    path = receipts.requirement_receipt_path(tmp_path, 1)
    lock.write(path, lock.yaml_bytes(doc))
    if kind == "pravopys":
        monkeypatch.setattr(source_query, "pravopys_section", lambda *a, **kw: {"status": "unavailable"})
    with Sources(sources_db=tmp_path / "missing-sources", vesum_db=tmp_path / "missing-vesum") as api:
        for action in (
            lambda: record(doc, tmp_path, api),
            lambda: receipts.write_requirement_receipts(path, doc, sources=api),
            lambda: receipts.read_requirement_receipts(path, sources=api),
            lambda: status(doc, tmp_path, api),
        ):
            with pytest.raises(ResolverError) as caught:
                action()
            assert caught.value.code == codes.SOURCE_UNAVAILABLE


@pytest.mark.parametrize("eid", ["vesum:487702", "vesum:1", "vesum:487702-487719"])
def test_existing_vesum_locator_grammars(eid):
    with Sources() as api:
        assert receipts.validate_requirement_receipts(document(eid), sources=api).raw[eid]


@pytest.mark.parametrize("eid", ["vesum:487702-487718", "vesum:487701-487719", "vts:2", "sum20:1", "vesum:0"])
def test_nearby_range_wrong_dictionary_and_wrong_key_do_not_resolve(eid):
    with Sources() as api, pytest.raises(ResolverError) as caught:
        receipts.validate_requirement_receipts(document(eid), sources=api)
    assert caught.value.code == codes.EVIDENCE_ID_UNRESOLVED


def test_one_readonly_database_snapshot_and_row_identity(request, monkeypatch):
    sources_db, _ = request.getfixturevalue("receipt_sources")
    with sqlite3.connect(sources_db) as writer:
        writer.execute("PRAGMA journal_mode=WAL")
    original_connect = sqlite3.connect
    opened = []

    def connect(path, **kwargs):
        opened.append((path, kwargs))
        return original_connect(path, **kwargs)

    monkeypatch.setattr(sqlite3, "connect", connect)
    with Sources() as api:
        first = api.resolve_evidence_ids(["grinchenko:11367"])
        assert first.content_hash == batch_digest(first.raw)
        assert first.metadata == {"sources_db": {"scheme": "rows-v2"}}
        with pytest.raises(sqlite3.OperationalError, match="readonly"):
            api._db().execute("DELETE FROM grinchenko")
        with original_connect(sources_db) as writer:
            writer.execute("INSERT INTO grinchenko (id, definition) VALUES (2, 'concurrent row')")
        assert not api.resolve_evidence_ids(["grinchenko:2"]).raw["grinchenko:2"]
        assert api.resolve_evidence_ids(["grinchenko:11367"]) == first
        assert len(opened) == 1
        assert opened[0] == (sources_db.resolve().as_uri() + "?mode=ro", {"uri": True, "isolation_level": None})
        api.close()
        assert api.resolve_evidence_ids(["grinchenko:2"]).raw["grinchenko:2"]
    assert api._conn is None


def test_vesum_change_is_a_named_refusal(request):
    _, vesum_db = request.getfixturevalue("receipt_sources")
    with Sources() as api:
        receipts.validate_requirement_receipts(document(IDS["vesum"]), sources=api)
        with sqlite3.connect(vesum_db) as writer:
            writer.execute("UPDATE forms_all SET entry_id=123 WHERE id=487702")
        with pytest.raises(ResolverError) as caught:
            receipts.validate_requirement_receipts(document(IDS["vesum"]), sources=api)
        assert caught.value.code == codes.SOURCE_UNAVAILABLE


def test_pravopys_section_is_read_once_per_session(monkeypatch):
    from scripts.rag import source_query

    calls = []

    def section(number, **kwargs):
        calls.append(number)
        return {"section": number, "text": "one two source bytes"}

    monkeypatch.setattr(source_query, "pravopys_section", section)
    with Sources() as api:
        first = receipts.validate_requirement_receipts(document(IDS["pravopys"]), sources=api)
        assert receipts.validate_requirement_receipts(document(IDS["pravopys"]), sources=api) == first
    assert calls == [53]


def test_choice_gate_resolves_even_a_locked_fabrication(tmp_path):
    from types import SimpleNamespace

    forged = document("vesum:anything")
    lock.write(receipts.requirement_receipt_path(tmp_path, 1), lock.yaml_bytes(forged))
    with Sources() as api, pytest.raises(ResolverError) as caught:
        check_7_a1_choices(
            {"activities": []}, {}, {"words": []}, SimpleNamespace(), state_dir=tmp_path, lesson_n=1, sources=api,
        )
    assert caught.value.code == codes.EVIDENCE_ID_UNRESOLVED


def test_schema_errors_remain_receipt_invalid():
    malformed = copy.deepcopy(document(IDS["vesum"]))
    malformed["items"][0]["options"][0]["evidence"] = ["vesum:no:colon"]
    with pytest.raises(ResolverError) as caught:
        receipts.validate_requirement_receipts(malformed)
    assert caught.value.code == codes.RECEIPT_INVALID


def test_missing_vts_table_is_source_unavailable(request):
    sources_db, _ = request.getfixturevalue("receipt_sources")
    with sqlite3.connect(sources_db) as writer:
        writer.execute("DROP TABLE slovnyk_me_entries")
    with Sources() as api, pytest.raises(ResolverError) as caught:
        receipts.validate_requirement_receipts(document(IDS["vts"]), sources=api)
    assert caught.value.code == codes.SOURCE_UNAVAILABLE


@pytest.mark.parametrize("kind", IDS)
def test_existing_id_cannot_support_unrelated_form_at_any_entry_point(tmp_path, kind):
    doc = document(IDS[kind])
    doc["items"][0]["options"][1]["text"] = "unrelated"
    path = receipts.requirement_receipt_path(tmp_path, 1)
    (tmp_path / "lesson-1.writer.yaml").write_text("model: gpt-6.1-sol\n")
    lock.write(path, lock.yaml_bytes(doc))
    with Sources() as api:
        for action in (
            lambda: record(doc, tmp_path, api),
            lambda: receipts.validate_requirement_receipts(doc, sources=api),
            lambda: receipts.write_requirement_receipts(path, doc, sources=api),
            lambda: receipts.read_requirement_receipts(path, sources=api),
            lambda: status(doc, tmp_path, api),
        ):
            with pytest.raises(ResolverError) as caught:
                action()
            assert caught.value.code == codes.EVIDENCE_FORM_MISMATCH


@pytest.mark.parametrize("text", ["stone", "o ne", "\u0301", "оne"])
def test_word_comparison_preserves_letters_whitespace_and_boundaries(text):
    doc = document(IDS["vesum"])
    doc["items"][0]["options"][0]["text"] = text
    with Sources() as api, pytest.raises(ResolverError) as caught:
        receipts.validate_requirement_receipts(doc, sources=api)
    assert caught.value.code == codes.EVIDENCE_FORM_MISMATCH


@pytest.mark.parametrize("kind", IDS)
def test_stress_and_apostrophe_comparison_normalization(kind):
    from scripts.curriculum.evidence.sources import SourceResult

    with Sources() as api:
        eid = IDS[kind]
        field = {"vesum": "word_form", "grinchenko": "word", "sum20": "headword", "ulif": "canonical_headword"}.get(kind, "word" if kind == "vts" else "text")
        resolved = SourceResult({eid: [{field: "м'яч", "status": "ok"}]}, "a" * 64)
        result = api.bind_evidence_forms(resolved, [(eid, "м’я\u0301ч"), (eid, "мʼя\u0300ч")])
        assert all(result.raw.values())


@pytest.mark.parametrize("kind", IDS)
def test_lemma_binding_comes_from_vesum_lookup(kind, request):
    from scripts.curriculum.evidence.sources import SourceResult

    _, db = request.getfixturevalue("receipt_sources")
    with sqlite3.connect(db) as conn:
        conn.execute("INSERT INTO forms_all VALUES (999, 999, '999-1000', 'inflected', 'lemma', 'noun', 'noun')")
        conn.execute("INSERT INTO forms_all VALUES (1000, 999, '999-1000', 'lemma', 'lemma', 'noun', 'noun')")
    eid = IDS[kind]
    field = {"vesum": "lemma", "grinchenko": "word", "sum20": "headword", "ulif": "canonical_headword"}.get(kind, "word" if kind == "vts" else "text")
    with Sources() as api:
        result = api.bind_evidence_forms(SourceResult({eid: [{field: "lemma", "status": "ok"}]}, "a" * 64), [(eid, "inflected")])
        assert result.raw[eid, "inflected"] is True
        assert "analyses_sha256" in result.metadata


def test_pravopys_identity_names_live_origin():
    with Sources() as api:
        result = receipts.validate_requirement_receipts(document(IDS["pravopys"]), sources=api)
    assert result.metadata["pravopys"] == {
        "scheme": "pravopys-live-section-v1", "origin": "https://2019.pravopys.net",
    }


@pytest.mark.parametrize("source_text", ["stone", "one's", "one-two", "two-one", "two’one", "_one"])
def test_word_components_and_metadata_cannot_supply_form_support(source_text):
    from scripts.curriculum.evidence.sources import SourceResult

    eid = IDS["textbook"]
    resolved = SourceResult({eid: [{"text": source_text, "title": "one", "source_url": "one"}]}, "a" * 64)
    with Sources() as api:
        assert api.bind_evidence_forms(resolved, [(eid, "one")]).raw[eid, "one"] is False


@pytest.mark.parametrize("text", ["One", "ONE", "oNe"])
@pytest.mark.parametrize("kind", IDS)
def test_capitalised_option_binds_without_judging_case(text, kind):
    doc = document(IDS[kind])
    doc["items"][0]["options"][0]["text"] = text
    with Sources() as api:
        receipts.validate_requirement_receipts(doc, sources=api)


@pytest.mark.parametrize("kind", ["vesum", "grinchenko", "sum20", "ulif", "vts"])
def test_dictionary_definition_cannot_bind_another_headword(kind):
    from scripts.curriculum.evidence.sources import SourceResult

    eid = IDS[kind]
    row = {"word_form": "other", "word": "other", "headword": "other", "lemma": "other",
           "canonical_headword": "other", "stressed_headword": "other",
           "definition": "one", "definition_text": "one", "article_text": "one",
           "sense_gloss": "one", "snippet": "one", "text": "one"}
    with Sources() as api:
        assert api.bind_evidence_forms(SourceResult({eid: [row]}, "a" * 64), [(eid, "one")]).raw[eid, "one"] is False


@pytest.fixture
def word_binding_rows(request):
    _, db = request.getfixturevalue("receipt_sources")
    # Structural doubles shaped after the task's examples, not source attestation.
    rows = [
        (10001, 101, "101-110", "жовта", "жовтий"),
        (10002, 102, "102-110", "Різдвом", "Різдво"),
        (10003, 102, "102-110", "Різдва", "Різдво"),
        (10004, 103, "103-110", "незалежність", "незалежність"),
        (10005, 103, "103-110", "Незалежності", "незалежність"),
        (10006, 104, "104-110", "кашу", "каша"),
        (10007, 105, "105-110", "способу", "спосіб"),
        (10008, 106, "106-110", "кордони", "кордон"),
        (3030583, 201, "201-210", "манну", "манний"),
        (3785464, 202, "202-210", "нового", "новий"),
        (5936922, 203, "203-210", "сухопутні", "сухопутний"),
        # Legacy collision: id 101 is unrelated; entry_id 101 is the right word.
        (101, 204, "204-210", "other", "other"),
    ]
    with sqlite3.connect(db) as writer:
        writer.executemany("INSERT INTO forms_all VALUES (?, ?, ?, ?, ?, 'noun', 'noun')", rows)


def test_capitalised_option_binds_legacy_entry_namespace(word_binding_rows):
    doc = document("vesum:101")
    doc["items"][0]["options"] = [
        {"text": "Жовта", "judgement": "valid", "evidence": ["vesum:101"]},
        {"text": "two", "judgement": "invalid", "evidence": [IDS["vesum"]]},
    ]
    with Sources() as api:
        receipts.validate_requirement_receipts(doc, sources=api)


@pytest.mark.parametrize("kind", ["pravopys", "textbook"])
@pytest.mark.parametrize("option,judgement,source_text", [
    ("різдвом", "invalid", "Rule example: Різдва."),
    ("незалежність", "valid", "Rule example: Незалежності."),
])
def test_text_kind_binds_attested_paradigm_without_option_text(
    kind, option, judgement, source_text, word_binding_rows, request, monkeypatch,
):
    from scripts.rag import source_query

    if kind == "pravopys":
        monkeypatch.setattr(source_query, "pravopys_section", lambda number, **kw: {"section": number, "text": source_text})
    else:
        db, _ = request.getfixturevalue("receipt_sources")
        with sqlite3.connect(db) as writer:
            writer.execute("UPDATE textbooks SET text=?", (source_text,))
    doc = document(IDS["vesum"])
    doc["items"][0]["options"][0 if judgement == "valid" else 1] = {"text": option, "judgement": judgement, "evidence": [IDS[kind]]}
    with Sources() as api:
        result = receipts.validate_requirement_receipts(doc, sources=api)
        assert "paradigms_sha256" in result.metadata["form_binding"]


@pytest.mark.parametrize("option,eid", [("кашу", "vesum:3030583"), ("способу", "vesum:3785464"), ("кордони", "vesum:5936922")])
@pytest.mark.parametrize("judgement", ["valid", "invalid"])
def test_neighbouring_adjective_citation_refuses(option, eid, judgement, word_binding_rows):
    doc = document(IDS["vesum"])
    doc["items"][0]["options"][0 if judgement == "valid" else 1] = {"text": option, "judgement": judgement, "evidence": [eid]}
    with Sources() as api, pytest.raises(ResolverError) as caught:
        receipts.validate_requirement_receipts(doc, sources=api)
    assert caught.value.code == codes.EVIDENCE_FORM_MISMATCH


def test_paradigm_binding_retains_whole_word_boundaries(word_binding_rows):
    from scripts.curriculum.evidence.sources import SourceResult

    eid = IDS["textbook"]
    with Sources() as api:
        for text in ["пронезалежності", "Незалежності-extra", "_Незалежності"]:
            result = api.bind_evidence_forms(SourceResult({eid: [{"text": text}]}, "a" * 64), [(eid, "незалежність")])
            assert result.raw[eid, "незалежність"] is False


def test_normalized_analysis_and_paradigm_reads_cache_and_detect_change(word_binding_rows, request):
    _, db = request.getfixturevalue("receipt_sources")
    with Sources() as api:
        first = api._receipt_vesum_rows(["різдвом"])
        assert {row["lemma"] for row in first.raw["різдвом"]} == {"Різдво"}
        assert api._receipt_vesum_rows(["різдвом"]) == first
        paradigm = api._receipt_vesum_rows(["різдво"], paradigm=True)
        assert {row["word_form"] for row in paradigm.raw["різдво"]} == {"Різдвом", "Різдва"}
        with sqlite3.connect(db) as writer:
            writer.execute("UPDATE forms_all SET lemma='changed' WHERE id=10002")
        with pytest.raises(ValueError, match="source_changed"):
            api._receipt_vesum_rows(["різдвом"])
        api.close()
        assert not api._receipt_words and not api._receipt_paradigms


@pytest.mark.parametrize("judgement", ["valid", "invalid"])
@pytest.mark.parametrize("ulif_status", ["not_found", "unavailable", None])
def test_ulif_only_ok_rows_are_witnesses_at_every_entry_point(tmp_path, request, judgement, ulif_status):
    sources_db, _ = request.getfixturevalue("receipt_sources")
    with sqlite3.connect(sources_db) as writer:
        writer.execute("UPDATE ulif_dictua_entries SET status=?", (ulif_status,))
    doc = document(IDS["vesum"])
    doc["items"][0]["options"][0 if judgement == "valid" else 1]["evidence"] = [IDS["ulif"]]
    path = receipts.requirement_receipt_path(tmp_path, 1)
    (tmp_path / "lesson-1.writer.yaml").write_text("model: gpt-6.1-sol\n")
    lock.write(path, lock.yaml_bytes(doc))
    with Sources() as api:
        assert api.resolve_evidence_ids([IDS["ulif"]]).raw[IDS["ulif"]]
        for action in (
            lambda: record(doc, tmp_path, api),
            lambda: receipts.validate_requirement_receipts(doc, sources=api),
            lambda: receipts.write_requirement_receipts(path, doc, sources=api),
            lambda: receipts.read_requirement_receipts(path, sources=api),
            lambda: status(doc, tmp_path, api),
        ):
            with pytest.raises(ResolverError) as caught:
                action()
            assert caught.value.code == codes.EVIDENCE_FORM_MISMATCH


@pytest.mark.parametrize("kind,field", [
    (kind, field)
    for kind, fields in {
        "grinchenko": ("headword", "lemma", "word_form"),
        "sum20": ("lemma", "word_form"),
        "vts": ("headword", "lemma", "word_form"),
        "ulif": ("headword", "lemma", "word_form"),
    }.items() for field in fields
])
def test_unrecognized_dictionary_fields_cannot_bind(kind, field):
    from scripts.curriculum.evidence.sources import SourceResult

    eid = IDS[kind]
    row = {field: "one", "status": "ok"}
    with Sources() as api:
        assert api.bind_evidence_forms(SourceResult({eid: [row]}, "a" * 64), [(eid, "one")]).raw[eid, "one"] is False


def test_sum20_stressed_headword_is_a_real_witness(request):
    sources_db, _ = request.getfixturevalue("receipt_sources")
    with sqlite3.connect(sources_db) as writer:
        writer.execute("UPDATE sum20_articles SET headword='other', stressed_headword='o\u0301ne'")
    with Sources() as api:
        receipts.validate_requirement_receipts(document(IDS["sum20"]), sources=api)


def test_quarantined_sum20_row_is_never_evidence(request):
    sources_db, _ = request.getfixturevalue("receipt_sources")
    with sqlite3.connect(sources_db) as writer:
        writer.execute("ALTER TABLE sum20_articles ADD COLUMN quarantine_reason TEXT NOT NULL DEFAULT ''")
    with Sources() as api:
        receipts.validate_requirement_receipts(document(IDS["sum20"]), sources=api)
    with sqlite3.connect(sources_db) as writer:
        writer.execute("UPDATE sum20_articles SET quarantine_reason = 'unverified provenance' WHERE wordid = 2319")
    with Sources() as api, pytest.raises(ResolverError) as caught:
        receipts.validate_requirement_receipts(document(IDS["sum20"]), sources=api)
    assert caught.value.code == codes.EVIDENCE_ID_UNRESOLVED


@pytest.mark.parametrize("paradigm", [False, True])
def test_indexed_vesum_lookup_filters_candidates_and_fails_closed_on_mixed_case(request, monkeypatch, paradigm):
    from scripts.curriculum.evidence import sources as module

    _, db = request.getfixturevalue("receipt_sources")
    # Uppercasing dotless ı produces I; normalized filtering must discard
    # FIXTURE as a witness for fıxture, even though it is an SQL candidate.
    with sqlite3.connect(db) as writer:
        writer.executemany("INSERT INTO forms_all VALUES (?, ?, '999-1000', ?, ?, 'noun', 'noun')", [
            (999, 999, "fıxture", "fıxture"), (1000, 1000, "FIXTURE", "FIXTURE"),
            (1001, 1001, "MixedCase", "MixedCase"),
        ])
    queries = []
    original = module.open_readonly

    def traced(path):
        conn = original(path)
        conn.set_trace_callback(queries.append)
        return conn

    monkeypatch.setattr(module, "open_readonly", traced)
    monkeypatch.setattr(module, "BATCH_SIZE", 1)
    with Sources() as api:
        rows = api._receipt_vesum_rows(["fıxture", "mixedcase"], paradigm=paradigm).raw
        assert {row["word_form"] for row in rows["fıxture"]} == {"fıxture"}
        assert rows["mixedcase"] == []
        assert api._receipt_vesum_rows([], paradigm=paradigm).raw == {}
    selects = [query for query in queries if query.startswith("SELECT word_form")]
    assert len(selects) == 2
    column = "lemma" if paradigm else "word_form"
    assert all(f"WHERE {column} IN (" in query and "receipt_word" not in query for query in selects)


@pytest.mark.parametrize("paradigm", [False, True])
def test_legacy_hyphen_apostrophe_candidates_reach_each_capitalised_part(request, paradigm):
    _, db = request.getfixturevalue("receipt_sources")
    value = "Кам'янець-Подільський" if paradigm else "Кам'янці-Подільському"
    with sqlite3.connect(db) as writer:
        writer.execute(
            "INSERT INTO forms_all VALUES (999, 999, '999-1000', ?, ?, 'noun', 'noun')",
            ("Кам'янці-Подільському", "Кам'янець-Подільський"),
        )
        writer.execute(
            "INSERT INTO forms_all VALUES (1000, 999, '999-1000', ?, ?, 'noun', 'noun')",
            ("Кам'янець-Подільський", "Кам'янець-Подільський"),
        )
    with Sources() as api:
        assert len(api._receipt_vesum_rows([value.casefold()], paradigm=paradigm).raw[value.casefold()]) == (2 if paradigm else 1)
        from scripts.curriculum.evidence.sources import SourceResult

        eid = IDS["textbook"]
        result = api.bind_evidence_forms(
            SourceResult({eid: [{"text": "Кам'янець-Подільський"}]}, "a" * 64),
            [(eid, "Кам’янці-Подільському")],
        )
        assert result.raw[eid, "Кам’янці-Подільському"] is True


@pytest.mark.parametrize("kind", ["textbook", "pravopys"])
@pytest.mark.parametrize("text,option,expected", [
    ("червиво-\nго", "червивого", True),
    # Pin the existing dual interpretation: binding is string identity, not a
    # linguistic judgement of whether this is a lexical hyphen.
    ("червиво-\nго", "червиво-го", True),
    ("червиво-\nго", "го", False),
    ("червиво- \r\n  го", "ЧЕРВИВОГО", True),
    ("червиво\u0301-\nго", "червивого", True),
    ("Фор\u00adмат файлу", "мат", False),
    ("Фор\u00ad мат", "формат", False),
    ("Фор\u00ad\tмат", "формат", False),
    ("Фор\u00ad \r\n мат", "формат", True),
    ("Формат файлу", "Фор\u00adмат", True),
    ("Формат файлу", "Фор\u00ad \r\n мат", True),
    ("Формат файлу", "Фор\u00ad мат", False),
    ("доб\u00adрий", "добрий", True),
    ("доб\u00ad\nрий", "добрий", True),
    ("доб\u00ad \r\n  рий", "добрий", True),
    ("будь-\nякий", "будь-який", True),
    ("жовто-\nблакитний", "жовто-блакитний", True),
    ("жовто- \r\n  блакитний", "жовто-блакитний", True),
    ("будь\u2011який", "будь-який", True),
    ("будь-який", "будь\u2011який", True),
    ("жовто\u2011\nблакитний", "жовто-блакитний", True),
    ("жовто-\nблакитний", "блакитний", False),
    ("one-\ntwo", "onetwo", True),
    ("one-\ntwo", "two", False),
    ("one-two", "onetwo", False),
    ("one -\ntwo", "onetwo", False),
    ("one -\ntwo", "two", True),
    ("і", "і", False),
    ("a", "a", False),
    ("'a'", "a", False),
    ("123", "123", False),
    ("на", "на", True),
    ("one на two", "НА", True),
    ("напис", "на", False),
    ("one two", "one two", True),
    ("ONE TWO", "One Two", True),
    ("one і two", "one і two", True),
    ("one unrelated two", "one two", False),
    ("one  two", "one two", True),
    ("one\ntwo", "one two", True),
    ("Добрий\nдень, Оксано!", "добрий день", True),
    ("Добрий  день!", "добрий день", True),
    ("Добрий день!", "добрий  день", True),
    ("Добрий день!", "добрий\nдень", True),
    ("Добрий\t\r\nдень!", "добрий\u00a0день", True),
    ("someone two", "one two", False),
    ("one twosome", "one two", False),
    ("one two's", "one two", False),
])
def test_text_binding_dehyphenation_short_words_and_exact_phrases(kind, text, option, expected):
    from scripts.curriculum.evidence.sources import SourceResult

    eid = IDS[kind]
    with Sources() as api:
        result = api.bind_evidence_forms(SourceResult({eid: [{"text": text}]}, "a" * 64), [(eid, option)])
        assert result.raw[eid, option] is expected


@pytest.mark.parametrize("kind", ["textbook", "pravopys"])
@pytest.mark.parametrize("option", ["t\u00adwo", "t\u00ad \r\n wo", "synth\u2011etic"])
def test_text_option_typesetting_is_normalized_before_paradigm_lookup(request, kind, option):
    from scripts.curriculum.evidence.sources import SourceResult

    _, db = request.getfixturevalue("receipt_sources")
    if "\u2011" in option:
        with sqlite3.connect(db) as conn:
            conn.execute("INSERT INTO forms_all VALUES (999, 999, '999-1000', 'synth-etic', 'one', 'noun', 'noun')")
    eid = IDS[kind]
    with Sources(vesum_db=db) as api:
        result = api.bind_evidence_forms(SourceResult({eid: [{"text": "one"}]}, "a" * 64), [(eid, option)])
        assert result.raw[eid, option] is True


@pytest.mark.parametrize("kind", ["textbook", "pravopys"])
@pytest.mark.parametrize("option,variant", [("a", "longer"), ("longer", "a"), ("one two", "longer")])
def test_text_limits_cannot_be_bypassed_by_paradigm(request, kind, option, variant):
    from scripts.curriculum.evidence.sources import SourceResult

    _, db = request.getfixturevalue("receipt_sources")
    with sqlite3.connect(db) as writer:
        writer.executemany("INSERT INTO forms_all VALUES (?, 999, '999-1000', ?, 'short-lemma', 'noun', 'noun')", [
            (999, option), (1000, variant),
        ])
    eid = IDS[kind]
    with Sources() as api:
        result = api.bind_evidence_forms(SourceResult({eid: [{"text": variant}]}, "a" * 64), [(eid, option)])
        assert result.raw[eid, option] is False
