"""Complete catalogue reconciliation and discovery regressions for #9409."""

from __future__ import annotations

import asyncio
import importlib.util
import json
import sqlite3
from collections import Counter
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import requests
import yaml

from scripts.ingest import resource_catalogue_ingest as catalogue

ROOT = Path(__file__).resolve().parents[1]
COUNTS = {
    "podcasts/podcast_db.json": 300,
    "podcasts/raw_lists/seasons_1_3.txt": 120,
    "podcasts/raw_lists/seasons_4_5.txt": 80,
    "podcasts/raw_lists/season_6_fmu.txt": 100,
    "podcasts/ulp_mapping.yaml": 602,
    "external_resources.yaml": 1739,
    "ulp-resources.yaml": 7,
    "ulp-articles-index.yaml": 77,
    "ulp-article-mappings.yaml": 152,
    "trusted_sources.yaml": 11,
    "dobraforma/dobraforma_db.json": 90,
    "talkukrainian/talkukrainian_db.json": 36,
    "verba/verba_db.json": 17,
}


@pytest.fixture
def database():
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    catalogue.ingest(conn, ROOT / "docs/resources", no_network=True)
    yield conn
    conn.close()


@pytest.mark.parametrize("relative,expected", COUNTS.items())
def test_every_file_reconciles(database, relative, expected):
    source = f"docs/resources/{relative}"
    stored = []
    for row in database.execute("SELECT source_entries FROM resource_catalogue"):
        stored.extend(e for e in json.loads(row[0]) if e["source_file"] == source)
    assert len(stored) == expected
    assert len({e["locator"] for e in stored}) == expected
    # Independently enumerate the complete file; no shared parser as oracle.
    path = ROOT / source
    if path.suffix == ".txt":
        original = [line.rsplit("URL: ", 1)[1].strip() for line in path.read_text().splitlines() if line.strip()]
    else:
        data = json.loads(path.read_text()) if path.suffix == ".json" else yaml.safe_load(path.read_text())
        original = []

        def collect(node):
            if isinstance(node, list):
                for item in node:
                    collect(item)
            elif isinstance(node, dict):
                if any(k in node for k in ("title", "name")):
                    if "url" in node or "youtube_url" in node:
                        original.append(node.get("url") or node["youtube_url"])
                        return
                    if "path" in node:
                        original.append("https://www.ukrainianlessons.com" + node["path"])
                        return
                    if node.get("type") == "rag":
                        original.append(f"sources://collection/{node['id']}")
                        return
                for value in node.values():
                    collect(value)

        collect(data)
    assert Counter(e["original_url"] for e in stored) == Counter(original)


@pytest.mark.parametrize("query", ["добрий день", "formal greetings", "ULP 1-02"])
def test_greeting_episode_found(database, query):
    hits = catalogue.search_resources(database, query, kind="podcast", free_only=True)
    hit = next(h for h in hits if h["url"] == "https://www.ukrainianlessons.com/episode2/")
    assert hit["season"] == 1 and hit["episode"] == 2
    assert hit["audio_access"] == "free"
    assert hit["notes_access"] == "premium"
    assert len(hit["source_files"]) == 6
    assert hit["discovery_evidence"][0]["source_url"] == "https://www.ukrainianlessons.com/greetings/"


def test_dedup_exact_filters_and_preserved_mappings(database):
    hits = catalogue.search_resources(database, "formal greetings", module="a1-who-am-i", level="a1", kind="podcast")
    greeting = next(hit for hit in hits if hit["episode"] == 2)
    assert "a2-21-numerals-and-nouns" in greeting["modules"]
    assert catalogue.search_resources(database, "formal greetings", module="a1-who") == []
    assert catalogue.search_resources(database, "formal greetings", level="C2") == []
    assert catalogue.search_resources(database, "", kind="video", limit=100)
    assert len(catalogue.search_resources(database, limit=100)) == 20
    assert catalogue.search_resources(database, '" ()') == []
    assert catalogue.search_resources(database, "добрий день", live_only=True) == []
    with pytest.raises(ValueError, match="kind"):
        catalogue.search_resources(database, kind="invalid")


@pytest.mark.parametrize(
    "url,expected",
    [
        ("http://ukrainianlessons.com/lesson/2/?utm_source=foo#bar", "https://www.ukrainianlessons.com/episode2/"),
        ("https://www.ukrainianlessons.com/lesson-123/", "https://www.ukrainianlessons.com/episode123/"),
        ("https://youtu.be/abc?t=2", "https://www.youtube.com/watch?v=abc"),
        ("https://www.youtube.com/shorts/abc?si=test", "https://www.youtube.com/watch?v=abc"),
        ("https://www.youtube.com/watch?v=abc&t=20", "https://www.youtube.com/watch?v=abc"),
        ("https://example.org/a/?z=2&a=1#fragment", "https://example.org/a?a=1&z=2"),
        ("sources://collection/textbooks", "sources://collection/textbooks"),
    ],
)
def test_normalise_url(url, expected):
    assert catalogue.normalise_url(url) == expected


@pytest.mark.parametrize("url", ["relative", "file:///tmp/a", "https://user:password@example.org"])
def test_reject_unsafe_url(url):
    with pytest.raises(ValueError):
        catalogue.normalise_url(url)


def test_atomic_idempotent_reingest_and_mutation_fts(database):
    before = catalogue.search_resources(database, "formal greetings")
    report = catalogue.ingest(database, ROOT / "docs/resources", no_network=True)
    assert report["entries_in"] == sum(COUNTS.values())
    assert report["rows_out"] == 1053
    assert catalogue.search_resources(database, "formal greetings") == before
    with database:
        database.execute(
            "UPDATE resource_catalogue SET title='UniqueReplacementWord',search_text='' WHERE url=?",
            (before[0]["url"],),
        )
    assert catalogue.search_resources(database, "UniqueReplacementWord")
    with database:
        database.execute("DELETE FROM resource_catalogue WHERE title='UniqueReplacementWord'")
    assert catalogue.search_resources(database, "UniqueReplacementWord") == []


def test_access_conflict_excludes_free_filter(database):
    with database:
        database.execute(
            "UPDATE resource_catalogue SET access='paid' WHERE url='https://www.ukrainianlessons.com/episode2/'"
        )
    assert not catalogue.search_resources(database, "добрий день", free_only=True)
    entries = catalogue.load_catalogues(ROOT / "docs/resources")
    first = next(e for e in entries if "episode2/" in e["url"])
    merged = catalogue.deduplicate([first, {**first, "access": "paid"}])[0]
    assert merged["access"] == "mixed"


def test_all_podcast_audio_free_notes_premium(database):
    rows = list(database.execute("SELECT audio_access,notes_access FROM resource_catalogue WHERE kind='podcast'"))
    assert len(rows) == 313  # includes separately catalogued episode-page aliases
    assert all(tuple(row) == ("free", "premium") for row in rows)


@pytest.mark.parametrize("status", [200, 404, 403, 405, 501])
def test_link_check_records_status_and_date(monkeypatch, status):
    response = MagicMock(status_code=status)
    response.__enter__.return_value = response
    monkeypatch.setattr(catalogue.requests, "head", lambda *a, **kw: response)
    fallback = MagicMock(status_code=200)
    fallback.__enter__.return_value = fallback
    get = MagicMock(return_value=fallback)
    monkeypatch.setattr(catalogue.requests, "get", get)
    check = catalogue.check_link("https://example.org", timeout=3)
    assert check["http_status"] == (200 if status in {405, 501} else status)
    assert check["checked_at"]
    assert check["link_check"] == ("live" if status in {200, 405, 501} else "http_error")
    if status in {405, 501}:
        assert get.call_args.kwargs["stream"] is True


def test_network_failure_and_internal_link(monkeypatch):
    monkeypatch.setattr(catalogue.requests, "head", MagicMock(side_effect=requests.Timeout))
    assert catalogue.check_link("https://example.org")["link_check"] == "network_error"
    assert catalogue.check_link("sources://collection/textbooks")["link_check"] == "not_applicable"


def test_offline_preserves_previous_checks(database, monkeypatch):
    monkeypatch.setattr(
        catalogue, "check_link", lambda *a: {"http_status": 200, "checked_at": "2026-10-01", "link_check": "live"}
    )
    catalogue.ingest(database, ROOT / "docs/resources", workers=2)
    catalogue.ingest(database, ROOT / "docs/resources", no_network=True)
    hit = catalogue.search_resources(database, "добрий день", live_only=True)[0]
    assert hit["checked_at"] == "2026-10-01"
    assert hit["http_status"] == 200


def test_missing_catalogue_does_not_change_existing_rows(database, tmp_path):
    before = database.execute("SELECT count(*) FROM resource_catalogue").fetchone()[0]
    with pytest.raises(FileNotFoundError):
        catalogue.ingest(database, tmp_path, no_network=True)
    assert database.execute("SELECT count(*) FROM resource_catalogue").fetchone()[0] == before


def test_reconciliation_detects_missing_locator(database):
    with database:
        database.execute(
            "UPDATE resource_catalogue SET source_entries='[]' WHERE url='https://www.ukrainianlessons.com/episode2/'"
        )
    with pytest.raises(ValueError, match="reconciliation"):
        catalogue.reconcile(database, catalogue.load_catalogues(ROOT / "docs/resources"))


def test_cli_help_and_storage_guards(tmp_path, monkeypatch, capsys):
    with pytest.raises(SystemExit) as exit_info:
        catalogue.main(["--help"])
    assert exit_info.value.code == 0
    assert "Outputs:" in capsys.readouterr().out
    database = tmp_path / "copy.db"
    sqlite3.connect(database).close()
    args = ["--ingest", "--db", str(database), "--no-network", "--catalogue-root", str(ROOT / "docs/resources")]
    assert catalogue.main(args) == 0
    assert json.loads(capsys.readouterr().out)["rows_out"] == 1053
    with pytest.raises(SystemExit):
        catalogue.main([*args, "--workers", "0"])
    from scripts.storage import topology

    monkeypatch.setattr(topology, "is_network_filesystem_path", lambda path: True)
    with pytest.raises(SystemExit):
        catalogue.main(args)


def test_mcp_search_wire_shape(database, monkeypatch):
    spec = importlib.util.spec_from_file_location("catalogue_sources_server", ROOT / ".mcp/servers/sources/server.py")
    server = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(server)
    from wiki import sources_db

    monkeypatch.setattr(sources_db, "_get_conn", lambda: database)
    tools = asyncio.run(server.list_tools())
    tool = next(t for t in tools if t.name == "search_resources")
    assert tool.annotations.read_only_hint
    assert {"query", "kind", "level", "module", "free_only", "live_only"} <= tool.input_schema["properties"].keys()
    content, is_error, outcome = asyncio.run(
        server._dispatch_tool_call("search_resources", {"query": "добрий день", "free_only": True})
    )
    assert not is_error
    wire = asyncio.run(
        server._on_call_tool(
            None, server.CallToolRequestParams(name="search_resources", arguments={"query": "добрий день"})
        )
    )
    assert not wire.is_error
    assert wire.structured_content["schema"] == "sources.tool-result.v1"
    assert wire.structured_content["match_count"] == 1
    assert outcome["schema"] == "sources.tool-result.v1"
    assert outcome["status"] == "ok"
    assert outcome["match_count"] == len(outcome["hits"]) == 1
    assert json.loads(content[0].text)[0]["episode"] == 2
    _, empty = asyncio.run(server.handle_search_resources({"query": "NonexistentResourceTerm"}))
    assert empty["status"] == "empty" and empty["match_count"] == 0


def test_invalid_catalogues_fail_closed(tmp_path, monkeypatch):
    monkeypatch.setattr(catalogue, "CATALOGUES", ("broken.txt",))
    (tmp_path / "broken.txt").write_text("unexpected row\n")
    with pytest.raises(ValueError, match="Malformed"):
        catalogue.load_catalogues(tmp_path)
    monkeypatch.setattr(catalogue, "CATALOGUES", ("empty.json",))
    (tmp_path / "empty.json").write_text("[]")
    with pytest.raises(ValueError, match="Empty"):
        catalogue.load_catalogues(tmp_path)


@pytest.mark.parametrize(
    "access_fields,expected", [({"paid": True}, "paid"), ({"free": False}, "paid"), ({"free": True}, "free")]
)
def test_explicit_access_metadata(access_fields, expected):
    entry = catalogue._resource_entry(
        {"title": "An article", "url": "https://example.org/article", **access_fields},
        "docs/resources/test.json",
        "/0",
        {},
    )
    assert entry["access"] == expected


def test_database_failure_rolls_back_catalogue(database, monkeypatch):
    entries = catalogue.load_catalogues(ROOT / "docs/resources")
    before = database.execute("SELECT count(*) FROM resource_catalogue").fetchone()[0]
    original = catalogue.deduplicate

    def invalid_rows(items):
        rows = original(items)
        rows[-1]["title"] = None
        return rows

    monkeypatch.setattr(catalogue, "deduplicate", invalid_rows)
    with pytest.raises(sqlite3.IntegrityError):
        catalogue.ingest(database, ROOT / "docs/resources", no_network=True)
    assert database.execute("SELECT count(*) FROM resource_catalogue").fetchone()[0] == before
    assert catalogue.reconcile(database, entries)["entries_in"] == sum(COUNTS.values())
