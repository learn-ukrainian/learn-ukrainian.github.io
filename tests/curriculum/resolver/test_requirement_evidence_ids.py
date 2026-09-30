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
        return {"section": number, "url": f"fixture/sections/{number}/", "text": "fixture rule"} if number == 53 else None

    monkeypatch.setattr(source_query, "pravopys_section", section)


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
        "options": ["one", "two"], "key_index": 0,
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
            writer.execute("INSERT INTO grinchenko VALUES (2, 'concurrent row')")
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
        return {"section": number, "text": "source bytes"}

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
