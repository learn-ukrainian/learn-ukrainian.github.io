"""Hermetic catalogue curation tests; synthetic tokens assert no language facts."""

import json
import sqlite3

import pytest
import yaml

from scripts.curriculum.evidence import catalogue, pack, sources
from scripts.ingest.resource_catalogue_ingest import SCHEMA


@pytest.fixture
def curation(tmp_path, synthetic_sources, synthetic_vesum, synthetic_standard):
    plan_path = tmp_path / "test-mod.yaml"
    words_path = tmp_path / "_words.yaml"
    plan = {
        "lessons": [
            {
                "n": 1,
                "slug": "first",
                "inventory": {
                    "phonetics": {"letters": ["X", "Y"]},
                    "vocabulary": {
                        "core": [{"lemma": "synthetic", "evidence": "W-001"}],
                        "incidental": [{"lemma": "unmatched", "evidence": "W-002"}],
                        "recycled": ["W-003"],
                    },
                },
            },
            {
                "n": 2,
                "slug": "second",
                "inventory": {
                    "phonetics": {"letters": ["X"]},
                    "vocabulary": {"recycled": ["W-001"]},
                },
            },
        ]
    }
    plan_path.write_text(yaml.safe_dump(plan))
    words_path.write_text(
        yaml.safe_dump(
            {
                "words": [
                    {"id": "W-001", "lemma": "synthetic"},
                    {"id": "W-003", "lemma": "reused"},
                ]
            }
        )
    )
    with sqlite3.connect(synthetic_sources) as conn:
        conn.executescript(SCHEMA)
        for resource_id, access, text in [(1, "free", "synthetic reused X"), (2, "premium", "Y unmatched")]:
            conn.execute(
                """INSERT INTO resource_catalogue
                (id,url,kind,title,channel,access,letters,levels,modules,topics,source_files,
                 source_entries,discovery_evidence,search_text,link_check)
                VALUES (?,?, 'podcast', 'Synthetic resource', 'Synthetic channel', ?,
                        ?, '[]','[]','[]','[]','[]','[]',?, 'not_checked')""",
                (
                    resource_id,
                    f"https://example.org/{resource_id}",
                    access,
                    json.dumps(["X"] if resource_id == 1 else ["Y"]),
                    text,
                ),
            )
    with sources.Sources(
        sources_db=synthetic_sources, vesum_db=synthetic_vesum, standard_path=synthetic_standard
    ) as src:
        yield plan_path, words_path, src


def test_queries_cover_each_lesson_word_and_letter(curation):
    plan, words, src = curation
    report = catalogue.request_report(plan, words, src)
    entries = report["queries"]
    assert [(q["lesson"], q["requirement_kind"], q["query"]) for q in entries] == [
        (1, "word", "synthetic"),
        (1, "word", "unmatched"),
        (1, "word", "reused"),
        (1, "letter", "X"),
        (1, "letter", "Y"),
        (2, "word", "synthetic"),
        (2, "letter", "X"),
    ]
    expected = {
        "id": 1,
        "title": "Synthetic resource",
        "url": "https://example.org/1",
        "access": "free",
        "kind": "podcast",
    }
    assert report["status"] == "ok"
    assert report["suggestions_only"] is True
    assert entries[0]["candidates"] == [expected]
    assert entries[2]["candidates"] == [expected]
    assert entries[3]["candidates"] == [expected]
    # Zero free candidates is a completed search, distinct from unavailability.
    for index in (1, 4):
        assert entries[index]["status"] == "ok"
        assert entries[index]["candidates"] == []


@pytest.mark.parametrize("missing_db", [False, True])
def test_absent_catalogue_is_typed_and_preserves_queries(curation, tmp_path, missing_db):
    plan, words, src = curation
    if missing_db:
        src.sources_db = tmp_path / "absent.db"
    else:
        with sqlite3.connect(src.sources_db) as conn:
            conn.execute("DROP TABLE resource_catalogue")
    report = catalogue.request_report(plan, words, src)
    assert report["status"] == "not_checked"
    assert report["notes"] == [{"code": "catalogue_unavailable"}]
    assert len(report["queries"]) == 7
    assert all(q["query"] and q["status"] == "not_checked" and q["candidates"] == [] for q in report["queries"])
    assert not (tmp_path / "absent.db").exists()


def test_missing_plan_and_unresolved_recycled_word_are_explicit(curation, tmp_path):
    plan, words, src = curation
    report = catalogue.request_report(tmp_path / "absent.yaml", words, src)
    assert report["notes"] == [{"code": "catalogue_plan_unavailable"}]
    assert report["status"] == "not_checked"
    report = catalogue.request_report(plan, tmp_path / "absent-words.yaml", src)
    unresolved = [q for q in report["queries"] if q["query"] is None]
    assert [q["evidence"] for q in unresolved] == ["W-003", "W-001"]
    assert all(q["note"] == {"code": "catalogue_word_unresolved"} for q in unresolved)
    assert report["status"] == "not_checked"


def test_missing_catalogue_fields_stop_instead_of_claiming_empty(curation):
    plan, words, src = curation
    with sqlite3.connect(src.sources_db) as conn:
        conn.execute("ALTER TABLE resource_catalogue RENAME COLUMN access TO old_access")
    with pytest.raises(sqlite3.OperationalError, match="access"):
        catalogue.request_report(plan, words, src)


def test_invalid_plan_is_not_a_no_source_claim(curation):
    plan, words, src = curation
    plan.write_text("[]")
    with pytest.raises(ValueError, match="catalogue_plan_invalid"):
        catalogue.request_report(plan, words, src)


def test_build_report_suggestions_never_bind_or_change_pack(curation, tmp_path):
    plan, words, src = curation
    request = tmp_path / "request.yaml"
    request.write_text(yaml.safe_dump({"request_schema": 1, "module": "a1/test-mod"}))
    report = pack.build_pack(
        "a1",
        "test-mod",
        request,
        plans_dir=plan.parent,
        evidence_dir=words.parent,
        sources_instance=src,
        dry_run=True,
        offline=True,
    )
    assert report["catalogue"]["queries"][0]["candidates"]
    assert "videos" not in report["pack"]
    assert "catalogue" not in report["pack"]
    assert "hosts" not in report["pack"]
    assert not (tmp_path / "test-mod.yaml.lock").exists()
    # A new snapshot observes the changed catalogue, while the pack stays byte-identical.
    src.close()
    with sqlite3.connect(src.sources_db) as conn:
        conn.execute("DELETE FROM resource_catalogue")
    empty = pack.build_pack(
        "a1",
        "test-mod",
        request,
        plans_dir=plan.parent,
        evidence_dir=words.parent,
        sources_instance=src,
        dry_run=True,
        offline=True,
    )
    assert all(q["candidates"] == [] for q in empty["catalogue"]["queries"])
    assert pack.lock.yaml_bytes(report["pack"]) == pack.lock.yaml_bytes(empty["pack"])


@pytest.mark.parametrize("missing_db", [False, True])
def test_build_fails_open_when_catalogue_is_absent(curation, tmp_path, missing_db):
    plan, words, src = curation
    if missing_db:
        src.sources_db = tmp_path / "absent.db"
    else:
        with sqlite3.connect(src.sources_db) as conn:
            conn.execute("DROP TABLE resource_catalogue")
    request = tmp_path / "request.yaml"
    request.write_text("request_schema: 1\nmodule: a1/test-mod\n")
    result = pack.build_pack(
        "a1",
        "test-mod",
        request,
        plans_dir=plan.parent,
        evidence_dir=words.parent,
        sources_instance=src,
        dry_run=True,
        offline=True,
    )
    assert result["status"] == "ok"
    assert result["catalogue"]["notes"] == [{"code": "catalogue_unavailable"}]


@pytest.mark.parametrize("json_output", [True, False])
def test_cli_exposes_catalogue_report(curation, tmp_path, capsys, json_output):
    plan, words, src = curation
    request = tmp_path / "request.yaml"
    request.write_text("request_schema: 1\nmodule: a1/test-mod\n")
    argv = [
        "a1",
        "test-mod",
        "--request",
        str(request),
        "--plans-dir",
        str(plan.parent),
        "--evidence-dir",
        str(words.parent),
        "--sources-db",
        str(src.sources_db),
        "--vesum-db",
        str(src.vesum_db),
        "--standard-path",
        str(src.standard_path),
        "--dry-run",
    ]
    if json_output:
        argv.append("--json")
    assert pack.main(argv) == 0
    output = capsys.readouterr().out
    if json_output:
        assert json.loads(output)["catalogue"]["queries"][0]["candidates"]
    else:
        assert "Catalogue suggestions (curator evidence required)" in output
        assert '"query": "synthetic"' in output
        assert '"url": "https://example.org/1"' in output


def test_letter_requirements_never_accept_unindexed_hits(curation, monkeypatch):
    plan, words, src = curation
    monkeypatch.setattr(
        src,
        "search_resources",
        lambda *args, **kwargs: [
            {"id": 999, "title": "Unrelated", "url": "https://example.org/999", "access": "free", "kind": "podcast"}
        ],
    )
    report = catalogue.request_report(plan, words, src)
    letters = [q for q in report["queries"] if q["requirement_kind"] == "letter"]
    assert letters and all(q["candidates"] == [] and q["query_mode"] == "letter_index" for q in letters)
    assert report["queries"][0]["candidates"]
