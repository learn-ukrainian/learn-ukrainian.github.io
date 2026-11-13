"""Complete catalogue reconciliation and discovery regressions for #9409."""

from __future__ import annotations

import asyncio
import hashlib
import http.client
import importlib.util
import json
import os
import sqlite3
from collections import Counter
from contextlib import closing, contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

import pytest
import yaml

from scripts.curriculum.evidence import sources
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
    "ulp-alphabet.yaml": 40,
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
    conn.execute(
        "CREATE TABLE external_articles(id INTEGER PRIMARY KEY,chunk_id TEXT,url TEXT,title TEXT,text TEXT,source_file TEXT)"
    )
    conn.executemany(
        "INSERT INTO external_articles VALUES(?,?,?,?,?,?)",
        [
            (
                1,
                "ext-ulp_youtube-302",
                "https://www.youtube.com/watch?v=fixture2",
                "ULP 1-02 | Formal Greetings",
                "добрий день привіт дякую",
                "ulp_youtube",
            ),
            (
                2,
                "article-fixture",
                "https://www.ukrainianlessons.com/greetings/",
                "Greetings",
                "статтятест",
                "ulp_blogs",
            ),
        ],
    )
    conn.commit()
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
    assert hit["access"] == "mixed"
    assert hit["discovery_evidence"][0]["chunk_id"] == "ext-ulp_youtube-302"
    assert hit["discovery_evidence"][0]["relation"] == "episode_identity"


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


@pytest.mark.parametrize("url", ["relative", "file:///tmp/a", "https://user:password@example.org"])  # trufflehog:ignore
def test_reject_unsafe_url(url):
    with pytest.raises(ValueError):
        catalogue.normalise_url(url)


def test_atomic_idempotent_reingest_and_mutation_fts(database):
    before = catalogue.search_resources(database, "formal greetings")
    report = catalogue.ingest(database, ROOT / "docs/resources", no_network=True)
    assert report["entries_in"] == sum(COUNTS.values())
    assert report["rows_out"] == 1086
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


@contextmanager
def link_server(statuses):
    """Serve the given statuses in turn (the last repeats) on a loopback port."""
    seen = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            seen.append(self.headers.get("User-Agent", ""))
            self.send_response(statuses[min(len(seen) - 1, len(statuses) - 1)])
            self.send_header("Content-Type", "text/html")
            self.end_headers()

        def log_message(self, *args):
            pass

    with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
        thread = Thread(target=server.serve_forever)
        thread.start()
        try:
            yield f"http://127.0.0.1:{server.server_port}/page", seen
        finally:
            server.shutdown()
            thread.join()


@pytest.mark.parametrize(
    ("statuses", "outcome", "final_status", "requests_made"),
    [
        ([200], "live", 200, 1),
        ([403], "bot_blocked", 403, 1),
        ([429, 200], "live", 200, 2),
        ([503], "unverifiable", 503, 3),
        ([404], "dead_link", 404, 1),
    ],
)
def test_link_check_classifies_outcome_with_the_shared_honest_checker(
    monkeypatch, statuses, outcome, final_status, requests_made
):
    monkeypatch.setattr(sources.time, "sleep", lambda delay: None)
    with link_server(statuses) as (url, seen):
        check = catalogue.check_link(url, timeout=3)
    assert check["link_check"] == outcome
    assert check["http_status"] == final_status
    assert check["checked_at"]
    assert len(seen) == requests_made
    assert all(agent == sources.LINKCHECK_USER_AGENT for agent in seen)


def test_malformed_http_response_is_unverifiable_and_does_not_abort_ingest(monkeypatch):
    monkeypatch.setattr(sources.time, "sleep", lambda delay: None)

    def not_http(*args, **kwargs):
        raise http.client.BadStatusLine("NOT HTTP")

    monkeypatch.setattr(sources.urllib.request, "urlopen", not_http)
    check = catalogue.check_link("https://example.org/", timeout=1)
    assert (check["link_check"], check["http_status"]) == ("unverifiable", None)


def test_unreachable_host_is_unverifiable_and_internal_link_is_not_applicable(monkeypatch):
    monkeypatch.setattr(sources.time, "sleep", lambda delay: None)
    with link_server([200]) as (url, _):
        pass  # the server is closed: nothing listens on this port any more
    check = catalogue.check_link(url, timeout=1)
    assert (check["link_check"], check["http_status"]) == ("unverifiable", None)
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


def test_cli_help_and_storage_guards(tmp_path, publish_store, monkeypatch, capsys):
    with pytest.raises(SystemExit) as exit_info:
        catalogue.main(["--help"])
    assert exit_info.value.code == 0
    assert "Outputs:" in capsys.readouterr().out
    database = tmp_path / "copy.db"
    sqlite3.connect(database).close()
    args = ["--ingest", "--db", str(database), "--no-network", "--catalogue-root", str(ROOT / "docs/resources")]
    assert catalogue.main(args) == 0
    assert json.loads(capsys.readouterr().out)["rows_out"] == 1086
    with pytest.raises(SystemExit):
        catalogue.main([*args, "--workers", "0"])
    # --publish is a separate mode: never with --db, and every binding is required and well formed.
    selector, generation, root = publish_store
    publish = _publish_args(selector, generation, root)
    for invalid in (
        [*publish, "--db", str(database)],
        [*args, "--store", str(selector)],
        [*args[:3], "--publish"],
        [*publish[:5], "not-a-generation", *publish[6:]],
        [*publish[:7], "0" * 63, *publish[8:]],
    ):
        with pytest.raises(SystemExit) as exit_info:
            catalogue.main(invalid)
        assert exit_info.value.code == 2
    before = _store_files(selector)
    from scripts.storage import topology

    for reason, store, patch in (
        ("store_not_selector", selector.with_name("copy.db"), None),
        ("locality_network", selector, ("store_locality", lambda path: "network")),
        ("store_inside_live_data", selector, ("live_store_path", lambda: tmp_path / topology.SELECTOR_NAME)),
        ("insufficient_free_space", selector, None),
    ):
        with monkeypatch.context() as scoped:
            if patch:
                scoped.setattr(topology, *patch)
            if reason == "insufficient_free_space":
                scoped.setenv("LU_EVIDENCE_FREE_DISK_FLOOR_BYTES", str(1 << 62))
            assert catalogue.main([*publish[:3], str(store), *publish[4:]]) == 2
        assert _failed(capsys)["reason"] == reason
        assert _store_files(selector) == before
    # The primary store is admitted only from the primary checkout, through the importer's default target.
    from scripts.ingest import sum20_mirror_import as importer

    with monkeypatch.context() as scoped:
        scoped.setattr(topology, "live_store_path", lambda: selector)
        scoped.setattr(importer, "main_checkout_root", lambda root: root / "primary")
        assert catalogue.main(publish) == 2
    assert _failed(capsys)["reason"] == "linked_worktree"
    assert _store_files(selector) == before

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
    assert tool.input_schema["properties"]["mode"]["default"] == "text"
    assert "recorded free" in tool.input_schema["properties"]["free_only"]["description"]
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
    assert "Found 1 catalogue resources" in content[0].text
    assert outcome["hits"][0]["episode"] == 2
    _, empty = asyncio.run(server.handle_search_resources({"query": "NonexistentResourceTerm"}))
    assert empty["status"] == "empty" and empty["match_count"] == 0


@pytest.mark.parametrize("query", ["я", "і", "у", "в", "з", "о", "а", "й"])
def test_one_letter_word_and_mcp_default_use_full_text(database, monkeypatch, query):
    word_url = "https://www.ukrainianlessons.com/prepositions-u-na/"
    with database:
        # Isolate both FTS fields; letter titles can legitimately match text searches too.
        database.execute("UPDATE resource_catalogue SET title='Fixture',search_text=''")
        database.execute("UPDATE resource_catalogue SET search_text=? WHERE url=?", (query, word_url))
    hits = catalogue.search_resources(database, query)
    assert [hit["url"] for hit in hits] == [word_url]
    assert catalogue.search_resources(database, query, mode="text") == hits
    letter_hits = catalogue.search_resources(database, query, mode="letter")
    assert len(letter_hits) == 1
    assert letter_hits[0]["letters"] == [query.upper()]
    assert letter_hits[0]["url"] != word_url

    spec = importlib.util.spec_from_file_location("catalogue_sources_server", ROOT / ".mcp/servers/sources/server.py")
    server = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(server)
    from wiki import sources_db

    monkeypatch.setattr(sources_db, "_get_conn", lambda: database)
    _, default = asyncio.run(server.handle_search_resources({"query": query}))
    assert default["hits"] == hits
    _, explicit = asyncio.run(server.handle_search_resources({"query": query, "mode": "letter"}))
    assert explicit["hits"] == letter_hits


@pytest.mark.parametrize("query", ["", "()", "two words", "Те", "1"])
def test_letter_mode_rejects_non_letter_queries(database, query):
    assert catalogue.search_resources(database, query, mode="letter") == []


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
    "access_fields,expected",
    [
        ({}, "unknown"),
        ({"access": None}, "unknown"),
        ({"access": "premium"}, "premium"),
        ({"paid": True}, "paid"),
        ({"free": False}, "paid"),
        ({"free": True}, "free"),
        ({"paid": True, "free": True}, "paid"),
    ],
)
def test_explicit_access_metadata(access_fields, expected):
    entry = catalogue._resource_entry(
        {
            "title": "An article",
            "url": "https://example.org/article",
            **access_fields,
            "access_evidence": [
                {"source_url": "https://example.org/article", "source_sha256": "0" * 64, "locator": "body"}
            ]
            if expected == "free"
            else [],
        },
        "docs/resources/test.json",
        "/0",
        {},
    )
    assert entry["access"] == expected


@pytest.mark.parametrize("query", ["добрий день", "привіт", "дякую"])
def test_linked_transcript_words_not_aliases(database, query):
    hits = catalogue.search_resources(database, query, kind="podcast")
    assert {hit["episode"] for hit in hits} == {2}
    database.execute("UPDATE external_articles SET text='replacement' WHERE chunk_id='ext-ulp_youtube-302'")
    catalogue.ingest(database, ROOT / "docs/resources", no_network=True)
    assert catalogue.search_resources(database, query, kind="podcast") == []


def test_url_link_and_linked_count(database):
    hit = catalogue.search_resources(database, "статтятест")[0]
    assert hit["url"] == "https://www.ukrainianlessons.com/greetings/"
    assert hit["discovery_evidence"][0]["relation"] == "url"
    report = catalogue.ingest(database, ROOT / "docs/resources", no_network=True)
    assert report["linked_resources"] == 2


def test_linking_missing_table_bad_urls_and_series_separation():
    conn = sqlite3.connect(":memory:")
    rows = catalogue.deduplicate(catalogue.load_catalogues(ROOT / "docs/resources"))
    assert catalogue.link_existing_text(conn, rows) == 0
    assert catalogue._episode_identity("https://example.org/a", "ULP 1-02") is None
    assert catalogue._episode_identity("https://www.youtube.com/watch?v=a", "FMU 1-02") == ("FMU", 2)
    conn.execute(
        "CREATE TABLE external_articles(id INTEGER,chunk_id TEXT,url TEXT,title TEXT,text TEXT,source_file TEXT)"
    )
    conn.executemany(
        "INSERT INTO external_articles VALUES(?,?,?,?,?,?)",
        [
            (1, "bad", "invalid", "ULP 1-02", "unsupported", "fixture"),
            (2, "fmu", "https://youtu.be/fmu", "FMU 1-02", "fmuwitness", "fixture"),
        ],
    )
    catalogue.link_existing_text(conn, rows)
    ulp = next(r for r in rows if r["url"] == "https://www.ukrainianlessons.com/episode2/")
    assert "fmuwitness" not in ulp["search_text"]
    assert "unsupported" not in ulp["search_text"]
    assert any("fmuwitness" in r["search_text"] for r in rows)
    conn.close()


def test_search_before_ingest_is_typed(monkeypatch):
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    with pytest.raises(catalogue.ResourceCatalogueMissingError):
        catalogue.search_resources(conn, "привіт")
    spec = importlib.util.spec_from_file_location("missing_catalogue_server", ROOT / ".mcp/servers/sources/server.py")
    server = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(server)
    from wiki import sources_db

    monkeypatch.setattr(sources_db, "_get_conn", lambda: conn)
    wire = asyncio.run(
        server._on_call_tool(None, server.CallToolRequestParams(name="search_resources", arguments={"query": "привіт"}))
    )
    assert wire.structured_content["status"] == "error"
    assert wire.structured_content["error_code"] == "resource_catalogue_missing"
    assert wire.structured_content["hits"] == []
    assert "no such table" not in wire.content[0].text
    conn.close()


def test_browse_and_large_provenance_have_byte_caps(database, monkeypatch):
    url = catalogue.search_resources(database, limit=1)[0]["url"]
    huge = {"locator": "x" * 100000, "original_url": url}
    database.execute("UPDATE resource_catalogue SET source_entries=? WHERE url=?", (json.dumps([huge] * 20), url))
    spec = importlib.util.spec_from_file_location("bounded_catalogue_server", ROOT / ".mcp/servers/sources/server.py")
    server = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(server)
    from wiki import sources_db

    monkeypatch.setattr(sources_db, "_get_conn", lambda: database)
    content, envelope = asyncio.run(server.handle_search_resources({"limit": 100}))
    assert len(envelope["hits"]) == envelope["match_count"] == 20
    assert len(content[0].text.encode("utf-8")) < 1500
    for hit in envelope["hits"]:
        assert len(json.dumps(hit, ensure_ascii=False).encode("utf-8")) <= catalogue.MAX_HIT_BYTES
        for field, budget in catalogue.PROVENANCE_BUDGETS.items():
            assert len(json.dumps(hit[field], ensure_ascii=False).encode("utf-8")) <= budget
    hit = next(h for h in envelope["hits"] if h["url"] == url)
    assert hit["source_entries_count"] == 20 and hit["source_entries_truncated"]
    assert (
        database.execute("SELECT length(source_entries) FROM resource_catalogue WHERE url=?", (url,)).fetchone()[0]
        > 100000
    )
    assert len(json.dumps(envelope, ensure_ascii=False).encode("utf-8")) < 20 * catalogue.MAX_HIT_BYTES + 4096
    assert "original_url" not in content[0].text


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


def test_letter_index_excludes_stray_transcript_words(database):
    with database:
        database.execute("UPDATE resource_catalogue SET search_text=search_text || ' Т т Ь ь'")
    for query, letter in [
        ("Т", "Т"),
        ("т", "Т"),
        (" Т ", "Т"),
        ('"Т"', "Т"),
        ("т.", "Т"),
        ("т́", "Т"),
        ("Ь", "Ь"),
        ("ь", "Ь"),
    ]:
        hits = catalogue.search_resources(database, query, mode="letter", free_only=True)
        assert len(hits) == 1
        assert hits[0]["letters"] == [letter]
        assert hits[0]["letter_evidence"]
    assert catalogue.search_resources(database, "Q", mode="letter", free_only=True) == []
    assert catalogue.search_resources(database, "Т", mode="letter", kind="podcast") == []
    assert catalogue.search_resources(database, "Т", mode="letter", level="C2") == []


def test_old_schema_migrates_without_fts_fallback():
    conn = sqlite3.connect(":memory:")
    old_schema = "\n".join(
        line
        for line in catalogue.SCHEMA.splitlines()
        if not any(f"{field} TEXT" in line for field in ("letters", "letter_evidence", "access_evidence"))
    )
    conn.executescript(old_schema)
    with pytest.raises(catalogue.ResourceCatalogueMissingError, match="Letter index"):
        catalogue.search_resources(conn, "Т")
    with conn:
        catalogue.ensure_schema(conn)
    catalogue.ensure_schema(conn)
    assert catalogue.search_resources(conn, "Т") == []
    conn.close()


@pytest.mark.parametrize(
    "fields",
    [
        {"letters": ["AB"]},
        {"letters": ["Т"]},
        {"letters": ["Т"], "letter_evidence": [{"letters": ["А"]}]},
        {"letters": ["Т"], "letter_evidence": [{"letters": ["Т"], "locator": "h2", "source_sha256": "bad"}]},
        {"access_evidence": [{"locator": "h2", "source_sha256": "0" * 64}]},
    ],
)
def test_unevidenced_letter_metadata_fails_closed(fields):
    with pytest.raises(ValueError):
        catalogue._resource_entry({"title": "Fixture", "url": "https://example.org", **fields}, "test.yaml", "/0", {})


def test_unknown_alias_preserves_evidenced_free_access_and_conflict_is_order_independent():
    import itertools

    base = catalogue._resource_entry({"title": "Fixture", "url": "https://example.org"}, "test.yaml", "/0", {})
    free = {**base, "access": "free", "access_evidence": [{"source_url": "https://example.org"}]}
    for entries in ([base, free], [free, base]):
        row = catalogue.deduplicate(entries)[0]
        assert row["access"] == "free"
        assert row["access_evidence"] == free["access_evidence"]
    paid = {**base, "access": "paid"}
    for entries in itertools.permutations([base, free, paid]):
        row = catalogue.deduplicate(list(entries))[0]
        assert row["access"] == "mixed"
        assert row["audio_access"] is None


def test_all_33_publisher_pairings_are_free_and_preserve_source_hash(database):
    expected = dict(
        zip(
            "АБВГҐДЕЄЖЗИІЇЙКЛМНОПРСТУФХЦЧШЩЬЮЯ",
            [
                "hvB3VpcR3ZE",
                "V1hxBE_JbGg",
                "aFcvYfvQ2X4",
                "gVnclpSI0DU",
                "gNjHqjTW9WQ",
                "g4Bh-lqzd48",
                "KFlsroBW0dk",
                "O0bwRyyBQSc",
                "dIrGVcqPwqM",
                "BhASNxitC1A",
                "W-1rCu0indE",
                "Z9TH0H4ShGo",
                "UcjdjQXhAY8",
                "aq0cjB90s3w",
                "J7sGEI4-xJo",
                "v6-3Xg52Buk",
                "Ez95H4ibuJo",
                "vNUfiKHPYaU",
                "gJFxRIPRZbI",
                "JksSjjxyW5Y",
                "fMGsQ5KPQgg",
                "7UsFBgSL91E",
                "m-jcLR_gK0k",
                "VB1O6PmtYRU",
                "haHRsFFZRQI",
                "vpr58zJSJKc",
                "u44eCjR2Oz8",
                "UsJkbdsY2RA",
                "1D-6MIw3OXY",
                "QmBLieIuf6Q",
                "cJlal8XKBxo",
                "9JdIBYCTWGw",
                "yhSAf41LX8I",
            ],
            strict=True,
        )
    )
    for letter, video in expected.items():
        hits = catalogue.search_resources(database, letter, mode="letter", free_only=True)
        assert hits[0]["url"] == f"https://www.youtube.com/watch?v={video}"
        assert hits[0]["letters"] == [letter]
        assert (
            hits[0]["access_evidence"][0]["source_sha256"]
            == "3d3e3a4cdb28fada42422fb70fd7ef9a1556b51dc4060c90c0165ae9fd79d795"
        )


@pytest.mark.parametrize("fields", [{"access": "free"}, {"free": True}])
def test_free_access_requires_evidence(fields):
    with pytest.raises(ValueError, match="Free catalogue access"):
        catalogue._resource_entry({"title": "Unknown", "url": "https://example.org", **fields}, "test.yaml", "/0", {})


# --- generation publication (#9471) ---------------------------------------------------------------------


@pytest.fixture
def publish_store(tmp_path, monkeypatch):
    """A held fixture store behind its selector, with unrelated tables, and a private catalogue copy."""
    from scripts.storage import generations

    for name in ("LU_SOURCES_DB", "SOURCES_DB_PATH"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.delenv(generations.ENV_WRITER_FD, raising=False)
    monkeypatch.delenv(generations.ENV_WRITER_SELECTOR, raising=False)
    # The publisher's real margin is tested with the generations; these fixtures are tiny.
    monkeypatch.setenv("LU_EVIDENCE_FREE_DISK_FLOOR_BYTES", "0")
    monkeypatch.setenv("LU_EVIDENCE_WAL_CEILING_BYTES", "0")
    data = tmp_path / "data"
    data.mkdir()
    seed = data / "seed.db"
    with closing(sqlite3.connect(seed)) as conn:
        conn.execute(
            "CREATE TABLE external_articles(id INTEGER PRIMARY KEY,chunk_id TEXT,url TEXT,title TEXT,text TEXT,"
            "source_file TEXT)"
        )
        conn.execute(
            "INSERT INTO external_articles VALUES(1,'ext-ulp_youtube-302','https://www.youtube.com/watch?v=fixture2',"
            "'ULP 1-02 | Formal Greetings','добрий день привіт дякую','ulp_youtube')"
        )
        conn.execute("CREATE TABLE textbooks(id INTEGER PRIMARY KEY, text TEXT, blob BLOB)")
        conn.executemany("INSERT INTO textbooks(text, blob) VALUES(?, ?)", [("fixture chunk", b"\x00\x01")] * 3)
        conn.execute("CREATE INDEX textbooks_text ON textbooks(text)")
        conn.execute("CREATE VIRTUAL TABLE textbooks_fts USING fts5(text, content='textbooks', content_rowid='id')")
        conn.execute("INSERT INTO textbooks_fts(textbooks_fts) VALUES('rebuild')")
        conn.commit()
        conn.execute("PRAGMA journal_mode=WAL")
    selector = data / generations.SELECTOR_NAME
    seed.rename(selector)
    selector.chmod(0o444)
    with generations.writer_lock(selector) as held:
        generations.checkpoint_legacy_store(held)
        generation = generations.publish_generation(selector, held, mode="bootstrap").generation
    # A reader's open leaves read-only -wal/-shm companions beside the generation, as on the live store.
    with closing(catalogue.open_readonly(generation)) as conn:
        conn.execute("SELECT count(*) FROM textbooks").fetchone()
    root = tmp_path / "resources"
    for relative in catalogue.CATALOGUES:
        (root / relative).parent.mkdir(parents=True, exist_ok=True)
        (root / relative).write_bytes((ROOT / "docs/resources" / relative).read_bytes())
    return selector, generation, root


def _publish_args(selector, generation, root, digest=None):
    digest = digest or catalogue.input_digest(catalogue.read_catalogue_inputs(root))
    return [
        "--ingest",
        "--publish",
        "--store",
        str(selector),
        "--expect-generation",
        generation.name,
        "--expect-input-sha256",
        digest,
        "--catalogue-root",
        str(root),
        "--no-network",
    ]


def _store_files(selector):
    """Every file beside the selector and in its generation directory, with the selected name."""
    from scripts.storage import generations

    names = sorted(p.relative_to(selector.parent).as_posix() for p in selector.parent.rglob("*"))
    return generations.inspect_selector(selector).generation.name, names


def _failed(capsys):
    return json.loads(capsys.readouterr().out)


def test_publish_refuses_input_manifest_drift(publish_store, monkeypatch, capsys):
    """Defect class: a catalogue changed after its digest was frozen is published, or later bytes are parsed."""
    selector, generation, root = publish_store
    frozen = catalogue.input_digest(catalogue.read_catalogue_inputs(root))
    before = _store_files(selector)
    drifted = root / "podcasts/raw_lists/seasons_1_3.txt"
    original = drifted.read_bytes()
    drifted.write_bytes(original + b"\n")
    assert catalogue.main(_publish_args(selector, generation, root, frozen)) == 2
    refusal = _failed(capsys)
    actual = catalogue.input_digest(catalogue.read_catalogue_inputs(root))
    assert refusal == {
        "status": "refused",
        "reason": "input_digest_mismatch",
        "input_sha256": actual,
        "selected": generation.name,
    }
    assert actual != frozen and _store_files(selector) == before
    # The digest is the documented sha256sum listing of the files in CATALOGUES order.
    drifted.write_bytes(original)
    listing = "".join(
        f"{hashlib.sha256((root / r).read_bytes()).hexdigest()}  docs/resources/{r}\n" for r in catalogue.CATALOGUES
    )
    assert hashlib.sha256(listing.encode()).hexdigest() == frozen
    # A file changed after the digest was taken is not reread: the published rows are the digested bytes.
    real_ingest = catalogue.ingest

    def change_after_digest(*args, **kwargs):
        drifted.write_bytes(b"not a catalogue line\n")
        return real_ingest(*args, **kwargs)

    monkeypatch.setattr(catalogue, "ingest", change_after_digest)
    assert catalogue.main(_publish_args(selector, generation, root, frozen)) == 0
    published = json.loads(capsys.readouterr().out)
    assert published["input_sha256"] == frozen and published["report"]["rows_out"] == 1086
    assert published["report"]["per_file"]["docs/resources/podcasts/raw_lists/seasons_1_3.txt"]["entries_in"] == 120


def test_publish_refuses_changed_source_generation(publish_store, monkeypatch, capsys):
    """Defect class: publishing over a selection other than the expected, held, unchanged one."""
    from scripts.storage import generations
    from scripts.storage.wal_permissions import hold_database, lift_database

    selector, generation, root = publish_store
    before = _store_files(selector)
    other = generation.with_name("sources.20000101T000000Z-000000000000.db").name
    args = _publish_args(selector, generation, root)
    assert catalogue.main([*args[:5], other, *args[6:]]) == 2
    assert _failed(capsys) == {
        "status": "refused",
        "reason": "selected_generation_mismatch",
        "selected": generation.name,
    }
    with generations.writer_lock(selector):
        assert catalogue.main(args) == 2
    assert _failed(capsys)["reason"] == "writer_lock_busy"
    lift_database(generation)
    try:
        assert catalogue.main(args) == 2
        assert _failed(capsys)["reason"] == "current_generation_writable"
    finally:
        hold_database(generation)
    real_ingest = catalogue.ingest

    def change_selected_generation(*a, **kw):
        report = real_ingest(*a, **kw)
        stamp = generation.stat().st_mtime_ns + 10**9
        os.utime(generation, ns=(stamp, stamp))
        return report

    monkeypatch.setattr(catalogue, "ingest", change_selected_generation)
    assert catalogue.main(args) == 2
    assert _failed(capsys) == {"status": "refused", "reason": "current_generation_changed", "selected": generation.name}
    assert _store_files(selector) == before


def test_publish_preserves_selected_generation_on_ingest_failure(publish_store, monkeypatch, capsys):
    """Defect class: a failed ingest, verification or late space check changes the selection or leaves a candidate."""
    from scripts.storage import generations

    selector, generation, root = publish_store
    before = _store_files(selector)
    args = _publish_args(selector, generation, root)
    real_deduplicate = catalogue.deduplicate

    def invalid_rows(items):
        rows = real_deduplicate(items)
        rows[-1]["title"] = None
        return rows

    monkeypatch.setattr(catalogue, "deduplicate", invalid_rows)
    assert catalogue.main(args) == 1
    assert _failed(capsys) == {"status": "failed", "reason": "IntegrityError", "selected": generation.name}
    assert _store_files(selector) == before
    monkeypatch.setattr(catalogue, "deduplicate", real_deduplicate)
    real_inventory = catalogue.preserved_inventory
    calls = []

    def changed_after_ingest(conn):
        calls.append(conn)
        inventory = real_inventory(conn)
        return {**inventory, "external_articles_sha256": "changed"} if len(calls) > 1 else inventory

    monkeypatch.setattr(catalogue, "preserved_inventory", changed_after_ingest)
    assert catalogue.main(args) == 1
    assert _failed(capsys) == {
        "status": "verification_failed",
        "reason": "external_articles_sha256_changed",
        "selected": generation.name,
    }
    assert _store_files(selector) == before
    monkeypatch.setattr(catalogue, "preserved_inventory", real_inventory)
    real_space = generations.require_free_space
    checks = []

    def refuse_restore_room(directory, size):
        checks.append(size)
        if len(checks) == 2:  # the refresh with actual sizes, after the candidate exists
            raise generations.GenerationError("insufficient_free_space")
        real_space(directory, size)

    monkeypatch.setattr(generations, "require_free_space", refuse_restore_room)
    assert catalogue.main(args) == 2
    assert _failed(capsys)["reason"] == "insufficient_free_space"
    assert checks[0] == 2 * generation.stat().st_size and _store_files(selector) == before


def test_publish_records_post_switch_failure_without_retry(publish_store, monkeypatch, capsys):
    """Defect class: an error after the selector switch reported as unchanged, or the ingest retried."""
    from scripts.storage import generations

    selector, generation, root = publish_store
    real_complete = generations._complete_receipt
    real_ingest = catalogue.ingest
    receipts, ingests = [], []

    def fail_after_the_switch(path):
        receipts.append(path)
        if len(receipts) > 1:  # the first call completes the previous receipt, before the switch
            raise generations.GenerationError("receipt_write_failed")
        real_complete(path)

    def counted(*args, **kwargs):
        ingests.append(args)
        return real_ingest(*args, **kwargs)

    monkeypatch.setattr(generations, "_complete_receipt", fail_after_the_switch)
    monkeypatch.setattr(catalogue, "ingest", counted)
    assert catalogue.main(_publish_args(selector, generation, root)) == 3
    selected, files = _store_files(selector)
    assert selected != generation.name and len(ingests) == 1
    assert _failed(capsys) == {
        "status": "published_post_switch_failed",
        "reason": "receipt_write_failed",
        "generation": selected,
        "previous": generation.name,
    }
    assert not [name for name in files if name.endswith(catalogue.CANDIDATE_SUFFIX)]
    assert generation.exists() and generations.is_held(generation)
    # An error raised while the writer lock is released, after a complete publication, is post-switch too.
    monkeypatch.setattr(generations, "_complete_receipt", real_complete)
    real_lock = generations.writer_lock

    @contextmanager
    def failing_release(*args, **kwargs):
        with real_lock(*args, **kwargs) as held:
            yield held
        raise OSError("writer lock release failed")

    monkeypatch.setattr(generations, "writer_lock", failing_release)
    previous = generations.inspect_selector(selector).generation
    assert catalogue.main(_publish_args(selector, previous, root)) == 3
    released, _ = _store_files(selector)
    assert released != previous.name and len(ingests) == 2
    assert _failed(capsys) == {
        "status": "published_post_switch_failed",
        "reason": "OSError",
        "generation": released,
        "previous": previous.name,
    }


def test_publish_scratch_round_trip_preserves_non_catalogue_tables(publish_store, capsys):
    """Defect class: publication loses non-catalogue data or the previous generation cannot be restored."""
    from scripts.storage import cli as storage_cli
    from scripts.storage import generations

    selector, generation, root = publish_store
    with closing(catalogue.open_readonly(generation)) as conn:
        before = catalogue.preserved_inventory(conn)
    assert catalogue.main(_publish_args(selector, generation, root)) == 0
    published = json.loads(capsys.readouterr().out)
    new = generations.inspect_selector(selector).generation
    assert published["generation"] == new.name != generation.name and published["previous"] == generation.name
    assert published["verification"]["external_articles_sha256"] == before["external_articles_sha256"]
    assert published["verification"]["preserved_tables"] == len(before["table_counts"])
    assert {"external_articles", "textbooks", "textbooks_fts_data"} <= before["table_counts"].keys()
    assert generations.is_held(new) and generations.is_held(generation)
    assert [g["receipt_state"] for g in generations.generation_status(selector)["generations"]] == ["published"] * 2
    with closing(catalogue.open_readonly(new)) as conn:
        assert catalogue.preserved_inventory(conn) == before
        assert catalogue.reconcile(conn, catalogue.load_catalogues(root))["rows_out"] == 1086
        hits = catalogue.search_resources(conn, "добрий день", kind="podcast")
        assert hits[0]["discovery_evidence"][0]["chunk_id"] == "ext-ulp_youtube-302"
    with closing(catalogue.open_readonly(generation)) as conn:
        assert catalogue.preserved_inventory(conn) == before
        with pytest.raises(catalogue.ResourceCatalogueMissingError):
            catalogue.search_resources(conn, "привіт")
    assert storage_cli.main(["restore-generation", "--store", str(selector), str(generation)]) == 0
    assert generations.inspect_selector(selector).generation == generation
    retained = {g["name"]: g["selected"] for g in generations.generation_status(selector)["generations"]}
    assert retained == {generation.name: True, new.name: False}
