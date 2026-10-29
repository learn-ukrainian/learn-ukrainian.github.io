"""Offline staging and CLI contracts; independent held-out proof belongs to the driver."""

from __future__ import annotations

import ast
import contextlib
import json
import os
import signal
import subprocess
import sys
import time
from itertools import pairwise
from pathlib import Path
from types import SimpleNamespace

import pytest
import requests

from scripts.hygiene import lint_source_db_writable_connects as sqlite_lint
from scripts.ingest import dictionary_acquisition as acquisition

SLOVNYK_HTML = '<html><section id="dictionary-article"><article><p>synthetic article</p></article></section></html>'
OFFICIAL_HTML = (
    '<article><div class="ENTRY"><span class="WORD">SAMPLE</span>'
    '<div class="INTF"><span class="FORMULA">Synthetic definition</span></div></div></article>'
)


@pytest.fixture
def acquisition_writer_entry():
    return next(
        entry for entry in sqlite_lint.load_allowlist() if entry.path == "scripts/ingest/dictionary_acquisition.py"
    )


@pytest.fixture
def acquisition_admission_scan(tmp_path, monkeypatch, acquisition_writer_entry):
    """Feed in-memory source controls through the unchanged repository lint API."""
    path = tmp_path / acquisition_writer_entry.path
    read_bytes = Path.read_bytes
    monkeypatch.setattr(sqlite_lint, "iter_scan_paths", lambda root: [path])

    def scan(source):
        monkeypatch.setattr(Path, "read_bytes", lambda self: source.encode() if self == path else read_bytes(self))
        return sqlite_lint.find_violations(tmp_path, (acquisition_writer_entry,))

    return scan


def test_acquisition_writer_source_pins(acquisition_writer_entry, acquisition_admission_scan):
    source = (sqlite_lint.REPO_ROOT / acquisition_writer_entry.path).read_text()
    assert len(sqlite_lint.classify_source(source, acquisition_writer_entry.path)) == 9
    calls = [
        ast.unparse(node)
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Call) and ast.unparse(node.func) == "sqlite3.connect"
    ]
    assert calls == list(acquisition_writer_entry.calls)
    assert sqlite_lint.writer_target_violations(source, acquisition_writer_entry) == []
    assert acquisition_admission_scan(source) == ([], [])


@pytest.mark.parametrize("mutation", ["retarget", "extra_annotation", "escape"])
def test_acquisition_writer_mutations_rejected(mutation, acquisition_writer_entry, acquisition_admission_scan):
    source = (sqlite_lint.REPO_ROOT / acquisition_writer_entry.path).read_text()
    if mutation == "retarget":
        changed = source.replace('directory / "staging.sqlite3"', 'directory / "other.sqlite3"')
        expected = "opens differ from declared target sites"
        assert len(sqlite_lint.classify_source(changed, acquisition_writer_entry.path)) == 9
    elif mutation == "extra_annotation":
        changed = source + "\nextra_annotation: sqlite3.Connection\n"
        expected = "pinned 9 references, found 10"
        assert len(sqlite_lint.classify_source(changed, acquisition_writer_entry.path)) == 10
        assert sqlite_lint.writer_target_violations(changed, acquisition_writer_entry) == []
    else:
        changed = source + "\nescaped = sqlite3.connect\n"
        expected = "constructor escapes the declared writer sites"
        assert sqlite_lint.writer_target_violations(changed, acquisition_writer_entry) == [
            f"{acquisition_writer_entry.path}: {expected}"
        ]
    assert changed != source
    violations, unreadable = acquisition_admission_scan(changed)
    assert not unreadable
    assert any(expected in violation for violation in violations), violations


def test_acquisition_writer_has_no_protected_store_eligibility(acquisition_writer_entry):
    protected = {
        entry.path
        for entry in sqlite_lint.load_allowlist()
        if entry.kind == "writer" and any(name in entry.target_db for name in ("sources.db", "vesum.db"))
    }
    assert acquisition_writer_entry.path not in protected


@pytest.mark.parametrize("path", ["scripts/ingest/dictionary_acquisition.py", "tests/test_dictionary_acquisition.py"])
def test_acquisition_admission_has_no_store_census_growth(path):
    source = (sqlite_lint.REPO_ROOT / path).read_text()
    assert sqlite_lint.classify_store_source(source, path) == []
    assert {entry for entry in sqlite_lint.baseline_entries() if entry.path == path} == set()


class Clock:
    def __init__(self):
        self.now = 1000.0
        self.sleeps = []

    def __call__(self):
        return self.now

    def sleep(self, seconds):
        assert seconds >= 0
        self.sleeps.append(seconds)
        self.now += seconds


class HTTP:
    def __init__(self, responses, clock):
        self.responses = iter(responses)
        self.clock = clock
        self.calls = []
        self.trust_env = True

    def get(self, url, **kwargs):
        self.calls.append((self.clock(), url, kwargs))
        response = next(self.responses)
        if isinstance(response, BaseException):
            raise response
        return response

    def __enter__(self):
        return self

    def __exit__(self, *_):
        pass


def response(code=200, text=SLOVNYK_HTML, headers=None):
    return SimpleNamespace(status_code=code, text=text, headers=headers or {})


def arguments(tmp_path, dictionary="vts", lemmas=("sample",), *extra):
    argv = [
        "--root",
        str(tmp_path / "staging"),
        "--dictionary",
        dictionary,
        "--delay",
        "2",
        "--timeout",
        "1",
        "--backoff",
        "2",
    ]
    if dictionary == acquisition.SUM20_SOURCE_ID:
        argv += ["--start-wordid", "5", "--end-wordid", "6"]
    else:
        manifest = tmp_path / "manifest.json"
        manifest.write_text(json.dumps({"entries": [{"lemma": lemma} for lemma in lemmas]}))
        argv += ["--manifest", str(manifest)]
    return argv + list(extra)


def status(tmp_path, dictionary="vts"):
    return json.loads((tmp_path / "staging" / dictionary / "status.json").read_text())


@contextlib.contextmanager
def database(tmp_path, dictionary="vts"):
    with contextlib.closing(acquisition.connect(tmp_path / "staging" / dictionary)) as conn:
        yield conn


def invoke(action, argv, http, clock, **kwargs):
    return acquisition.main([action, *argv], session_factory=lambda: http, clock=clock, sleep=clock.sleep, **kwargs)


def write_seed(directory, article=None, **overrides):
    directory.mkdir(exist_ok=True)
    cache = {
        "schema_version": acquisition._SLOVNYK_CACHE_SCHEMA_VERSION,
        "lemma": "sample",
        "lookup_word": "sample",
        "fetched_at": "2026-01-01T00:00:00+00:00",
        "lookups": {"vts": article},
    }
    cache.update(overrides)
    path = directory / acquisition._slovnyk_cache_path("sample").name
    path.write_text(json.dumps(cache))
    return path


def positive_row():
    return {
        "dictionary_slug": "vts",
        "word": "sample",
        "text": "synthetic article",
        "lookup_word": "sample",
        "source_url": "https://slovnyk.me/dict/vts/sample",
    }


def test_positive_miss_and_unique_frozen_denominator(tmp_path):
    clock = Clock()
    http = HTTP([response(), response(404)], clock)
    argv = arguments(tmp_path, "vts", ("sample", "sample", "other"))
    assert invoke("run", argv, http, clock) == 0
    result = status(tmp_path)
    assert result["denominator"] == 2
    assert result["counts"] == {"positive": 1, "miss": 1, "pending": 0, "error": 0, "reused": 0}
    assert result["checkpoint"] == 2
    assert result["state"] == "complete"
    assert result["eta_seconds"] == 0
    assert len(http.calls) == 2
    assert http.calls[1][0] - http.calls[0][0] >= 2
    assert http.trust_env is False
    assert http.calls[0][2]["allow_redirects"] is False
    assert http.calls[0][2]["headers"]["User-Agent"] == acquisition._SLOVNYK_USER_AGENT
    with database(tmp_path) as conn:
        payload = json.loads(conn.execute("SELECT payload FROM results WHERE position=0").fetchone()[0])
        assert payload["article"]["text"] == "synthetic article"
        assert payload["http_status"] == 200
        assert payload["source_url"] == "https://slovnyk.me/dict/vts/sample"
        assert payload["provenance"] == "observed_http"
        assert conn.execute("SELECT http_status FROM results WHERE position=1").fetchone()[0] == 404
    assert invoke("run", argv, HTTP([], clock), clock) == 0


@pytest.mark.parametrize("dictionary", ["vts", "sum20_official"])
@pytest.mark.parametrize("code", [401, 403, 302, 400])
def test_first_access_failure_stops_one_request_and_latches(tmp_path, dictionary, code):
    clock = Clock()
    http = HTTP([response(code), response()], clock)
    argv = arguments(tmp_path, dictionary)
    assert invoke("run", argv, http, clock) == 3
    assert len(http.calls) == 1
    result = status(tmp_path, dictionary)
    assert result["state"] == "blocked"
    assert result["checkpoint"] == 0
    assert result["counts"]["error"] == 1
    assert result["counts"]["miss"] == 0
    assert result["eta_seconds"] is None
    assert invoke("run", argv, HTTP([], clock), clock) == 3
    assert (
        invoke("supervise", argv, HTTP([], clock), clock, launch=lambda *_a, **_k: pytest.fail("latched job launched"))
        == 3
    )
    if dictionary == "sum20_official":
        headers = http.calls[0][2]["headers"]
        assert headers["User-Agent"] == acquisition.DEFAULT_USER_AGENT
        assert headers["Accept"] == "text/html,application/xhtml+xml"


@pytest.mark.parametrize("dictionary", ["vts", "sum20_official"])
def test_parse_error_never_advances_or_becomes_miss(tmp_path, dictionary):
    clock = Clock()
    http = HTTP([response(200, "<article></article>")], clock)
    argv = arguments(tmp_path, dictionary)
    assert invoke("run", argv, http, clock) == 4
    assert status(tmp_path, dictionary)["checkpoint"] == 0
    assert status(tmp_path, dictionary)["counts"]["miss"] == 0
    assert invoke("run", argv, HTTP([], clock), clock) == 4
    with database(tmp_path, dictionary) as conn:
        assert conn.execute("SELECT status,http_status,attempts FROM results WHERE position=0").fetchone()[:] == (
            "parse_error",
            200,
            1,
        )


def test_official_parser_recursion_stops_one_request_and_latches(tmp_path):
    # Keep the real parser: this is a valid entry beyond its recursive walk limit.
    entry = OFFICIAL_HTML.removeprefix("<article>").removesuffix("</article>")
    source = "<article>" + "<div>" * 1200 + entry + "</div>" * 1200 + "</article>"
    assert acquisition.parse_sum20_article(OFFICIAL_HTML, 5).headword == "SAMPLE"
    with pytest.raises(RecursionError):
        acquisition.parse_sum20_article(source, 5)
    clock = Clock()
    http = HTTP([response(200, source), response(200, OFFICIAL_HTML)], clock)
    argv = arguments(tmp_path, "sum20_official")
    assert invoke("run", argv, http, clock) == 4
    result = status(tmp_path, "sum20_official")
    assert result["state"] == "parse_error"
    assert result["terminal_reason"] == "unusable_article"
    assert result["checkpoint"] == 0
    assert result["next_wordid"] == 5
    assert result["counts"]["error"] == result["counts"]["pending"] == 1
    assert result["counts"]["positive"] == result["counts"]["miss"] == 0
    with database(tmp_path, "sum20_official") as conn:
        assert conn.execute("SELECT status,http_status,attempts FROM results WHERE position=0").fetchone()[:] == (
            "parse_error",
            200,
            1,
        )
    assert invoke("run", argv, http, clock) == 4
    assert invoke("supervise", argv, http, clock, launch=lambda *_a, **_k: pytest.fail("latched job launched")) == 4
    assert len(http.calls) == 1
    assert status(tmp_path, "sum20_official") == result


def test_official_positive_payload_and_bounded_range(tmp_path):
    clock = Clock()
    http = HTTP([response(200, OFFICIAL_HTML), response(404)], clock)
    assert invoke("run", arguments(tmp_path, "sum20_official"), http, clock) == 0
    result = status(tmp_path, "sum20_official")
    assert result["range"] == [5, 6]
    assert result["coverage_scope"] == "bounded_wordid_range"
    assert result["next_wordid"] is None
    assert result["counts"]["positive"] == result["counts"]["miss"] == 1
    assert http.calls[0][2]["params"] == {"page": 0}
    assert [call[0] for call in http.calls] == [1000, 1010]
    with database(tmp_path, "sum20_official") as conn:
        payload = json.loads(conn.execute("SELECT payload FROM results WHERE position=0").fetchone()[0])
        assert payload["article"]["wordid"] == 5
        assert payload["parser_version"] == acquisition.PARSER_VERSION
        assert payload["content_sha256"]


@pytest.mark.parametrize("retry_after,expected", [("1", 10), ("25", 25)])
def test_official_retry_spacing_survives_process_restart(tmp_path, retry_after, expected):
    clock = Clock()
    argv = arguments(tmp_path, "sum20_official")
    http = HTTP([response(503, headers={"Retry-After": retry_after}), response(404), response(404)], clock)
    assert invoke("run", argv, http, clock) == 75
    assert invoke("run", argv, http, clock) == 0
    assert [call[0] for call in http.calls] == [1000, 1000 + expected, 1010 + expected]


def test_transient_backoff_exhaustion_survives_process_invocations(tmp_path):
    clock = Clock()
    argv = arguments(tmp_path, "vts", ("sample",), "--max-attempts", "2")
    http = HTTP([response(503, headers={"Retry-After": "9"}), requests.Timeout("private secret")], clock)
    assert invoke("run", argv, http, clock) == 75
    assert status(tmp_path)["retry"]["attempts"] == 1
    assert invoke("run", argv, http, clock) == 5
    assert len(http.calls) == 2
    assert http.calls[1][0] - http.calls[0][0] >= 9
    assert status(tmp_path)["state"] == "exhausted"
    assert status(tmp_path)["counts"]["miss"] == 0
    assert invoke("run", argv, HTTP([], clock), clock) == 5
    assert "private secret" not in (tmp_path / "staging" / "vts" / "job.log").read_text()
    assert invoke("resume", argv, HTTP([], clock), clock) == 0
    assert status(tmp_path)["retry"]["attempts"] == 0
    assert invoke("run", argv, HTTP([response()], clock), clock) == 0
    with database(tmp_path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM events WHERE kind='operator_resume'").fetchone()[0] == 1


@pytest.mark.parametrize(
    "value,expected", [("5", 5), ("-3", 0), ("NaN", 0), ("bad", 0), (None, 0), ("Thu, 01 Jan 1970 00:16:45 GMT", 5)]
)
def test_retry_after_closed_safe_parsing(value, expected):
    assert acquisition.retry_after({"Retry-After": value}, 1000) == expected


def test_validated_positive_seed_is_separate_and_read_only(tmp_path):
    clock = Clock()
    seed = tmp_path / "seed"
    path = write_seed(seed, positive_row())
    original = path.read_bytes()
    argv = arguments(tmp_path, "vts", ("sample",), "--seed-cache", str(seed))
    assert invoke("run", argv, HTTP([], clock), clock) == 0
    result = status(tmp_path)
    assert result["counts"]["reused"] == 1
    assert result["counts"]["positive"] == result["counts"]["miss"] == 0
    assert result["eta_seconds"] is None
    assert result["request_attempts"] == 0
    assert path.read_bytes() == original
    with database(tmp_path) as conn:
        payload = json.loads(conn.execute("SELECT payload FROM results").fetchone()[0])
        assert payload["cache_sha256"] == acquisition.digest(original)
        assert payload["provenance"] == "legacy_positive"
        assert payload["fetched_at"] == "2026-01-01T00:00:00+00:00"
        assert payload["http_status"] is None


@pytest.mark.parametrize(
    "changes",
    [
        {"schema_version": -1},
        {"lookup_word": "other"},
        {"lemma": "other"},
        {"lookups": []},
        {"fetched_at": "invalid"},
        {"fetched_at": "2026-01-01T00:00:00"},
        {"fetched_at": None},
    ],
)
def test_bad_seed_is_not_reused(tmp_path, changes):
    seed = tmp_path / "seed"
    write_seed(seed, positive_row(), **changes)
    assert acquisition.seed_row(seed, "sample", "sample", "vts") is None


@pytest.mark.parametrize(
    "changes",
    [
        {"dictionary_slug": "newsum"},
        {"text": ""},
        {"lookup_word": "other"},
        {"source_url": "https://slovnyk.me/dict/vts/other"},
        {"source_url": "https://" + "user" + ":" + "secret" + "@" + "slovnyk.me" + "/dict/vts/sample"},
        {"source_url": "https://slovnyk.me/dict/vts/sample?secret=x"},
        {"source_url": "https://slovnyk.me/dict/newsum/sample"},
    ],
)
def test_seed_article_identity_and_url(changes):
    row = positive_row() | changes
    assert acquisition.valid_slovnyk(row, "vts", "sample") is False
    assert acquisition.valid_slovnyk(None, "vts", "sample") is False


def test_legacy_null_is_unattested_and_empty_200_is_parse_error(tmp_path):
    clock = Clock()
    seed = tmp_path / "seed"
    path = write_seed(seed)
    original = path.read_bytes()
    argv = arguments(tmp_path, "vts", ("sample",), "--seed-cache", str(seed))
    http = HTTP([response(200, "<article></article>")], clock)
    assert invoke("run", argv, http, clock) == 4
    assert len(http.calls) == 1
    assert status(tmp_path)["counts"]["miss"] == status(tmp_path)["counts"]["reused"] == 0
    assert path.read_bytes() == original


def test_manifest_configuration_and_durable_target_drift_refused(tmp_path, capsys):
    clock = Clock()
    argv = arguments(tmp_path)
    assert invoke("run", argv, HTTP([response(503)], clock), clock) == 75
    before = status(tmp_path)
    manifest = tmp_path / "manifest.json"
    original = manifest.read_text()
    manifest.write_text(original + " ")
    assert invoke("run", argv, HTTP([], clock), clock) == 2
    assert "frozen_input_mismatch" in capsys.readouterr().out
    assert status(tmp_path) == before
    manifest.write_text(original)
    assert invoke("run", [*argv, "--delay", "4"], HTTP([], clock), clock) == 2
    with database(tmp_path) as conn, conn:
        conn.execute("UPDATE results SET target='other'")
    assert invoke("run", argv, HTTP([], clock), clock) == 2
    refusal = json.loads((tmp_path / "staging" / "refusal.json").read_text())
    assert refusal["terminal_reason"] == "durable_targets_mismatch"


def test_dictionary_isolation_and_aggregate_host_spacing(tmp_path):
    clock = Clock()
    argv = arguments(tmp_path)
    http1 = HTTP([response()], clock)
    http2 = HTTP([response()], clock)
    assert invoke("run", argv, http1, clock) == 0
    argv2 = ["newsum" if item == "vts" else item for item in argv]
    assert invoke("run", argv2, http2, clock) == 0
    assert http2.calls[0][0] - http1.calls[0][0] >= 2
    assert status(tmp_path)["dictionary"] == "vts"
    assert status(tmp_path, "newsum")["dictionary"] == "newsum"
    assert (tmp_path / "staging" / "vts" / "staging.sqlite3").is_file()
    assert (tmp_path / "staging" / "newsum" / "staging.sqlite3").is_file()


def test_writer_conflict_then_release_and_resume_guard(tmp_path):
    clock = Clock()
    argv = arguments(tmp_path)
    directory = tmp_path / "staging" / "vts"
    directory.mkdir(parents=True)
    with acquisition.lock(directory / "writer.lock"):
        assert invoke("run", argv, HTTP([], clock), clock) == 6
    assert invoke("run", argv, HTTP([response(403)], clock), clock) == 3
    with acquisition.lock(directory / "supervisor.lock"):
        assert invoke("resume", argv, HTTP([], clock), clock) == 6
        assert invoke("supervise", argv, HTTP([], clock), clock) == 6
    assert status(tmp_path)["state"] == "blocked"
    assert invoke("resume", argv, HTTP([], clock), clock) == 0


def test_status_reconciles_durable_commit_after_projection_failure(tmp_path):
    clock = Clock()
    argv = arguments(tmp_path)
    assert invoke("run", argv, HTTP([response(503)], clock), clock) == 75
    with database(tmp_path) as conn, conn:
        conn.execute("UPDATE results SET status='not_found',http_status=404,reason='',next_attempt_at=0")
        conn.execute("UPDATE job SET state='complete',reason='target_resolved'")
    assert status(tmp_path)["state"] == "transient"
    assert invoke("status", argv, HTTP([], clock), clock) == 0
    result = status(tmp_path)
    assert result["checkpoint"] == 1
    assert result["counts"] == {"positive": 0, "miss": 1, "pending": 0, "error": 0, "reused": 0}
    assert result["state"] == "complete"


def test_interrupted_attempt_counts_and_event_budget(tmp_path):
    clock = Clock()
    argv = arguments(tmp_path, "vts", ("sample",), "--max-attempts", "1")
    http = HTTP([KeyboardInterrupt()], clock)
    assert invoke("run", argv, http, clock) == 130
    assert status(tmp_path)["retry"]["attempts"] == 1
    assert status(tmp_path)["terminal_reason"] == ""
    assert invoke("run", argv, HTTP([], clock), clock) == 5
    assert status(tmp_path)["terminal_reason"] == "attempt_budget"


@pytest.mark.parametrize("final_code,expected", [(403, 3), (200, 4), (503, 5), (404, 0)])
def test_documented_supervise_cli_stops_without_further_launches(tmp_path, final_code, expected):
    clock = Clock()
    argv = arguments(tmp_path, "vts", ("sample",), "--max-attempts", "3")
    http = HTTP([response(503), response(503), response(final_code, "<article></article>")], clock)
    commands = []

    def launch(command, **kwargs):
        assert kwargs == {"check": False}
        assert command[1:3] == ["-m", "scripts.ingest.dictionary_acquisition"]
        commands.append(command)
        return SimpleNamespace(
            returncode=acquisition.main(command[3:], session_factory=lambda: http, clock=clock, sleep=clock.sleep)
        )

    assert invoke("supervise", argv, http, clock, launch=launch) == expected
    assert len(commands) == len(http.calls) == 3
    assert invoke("supervise", argv, HTTP([], clock), clock, launch=launch) == expected
    assert len(commands) == 3
    assert all(later[0] - earlier[0] >= 2 for earlier, later in zip(http.calls, http.calls[1:], strict=False))
    assert status(tmp_path)["retry"]["supervisor_restarts"] == 2


def test_supervisor_crash_launch_budget_persists(tmp_path):
    clock = Clock()
    argv = arguments(tmp_path, "vts", ("sample",), "--max-restarts", "1")
    launches = []

    def crash(command, **_kwargs):
        launches.append(command)
        return SimpleNamespace(returncode=-9)

    assert invoke("supervise", argv, HTTP([], clock), clock, launch=crash) == 5
    assert len(launches) == 2
    result = status(tmp_path)
    assert result["state"] == "exhausted"
    assert result["terminal_reason"] == "supervisor_budget"
    assert result["request_attempts"] == 0
    assert result["retry"]["supervisor_launches"] == 2
    assert result["retry"]["no_progress_launches"] == 2
    assert result["retry"]["max_no_progress_launches"] == 2
    assert clock.sleeps == [2, 2]
    assert invoke("supervise", argv, HTTP([], clock), clock, launch=crash) == 5
    assert len(launches) == 2


@pytest.mark.parametrize("dictionary", ["vts", "sum20_official"])
def test_scattered_recovered_errors_outlive_launch_cap(tmp_path, dictionary):
    clock = Clock()
    argv = arguments(tmp_path, dictionary, tuple(f"sample{i}" for i in range(6)), "--max-restarts", "1")
    if dictionary == "sum20_official":
        argv += ["--end-wordid", "10"]
    article = OFFICIAL_HTML if dictionary == "sum20_official" else SLOVNYK_HTML
    # Every target first fails, then resolves; a miss is progress too.
    http = HTTP([item for i in range(6) for item in (response(503), response(404 if i % 2 else 200, article))], clock)
    launches = []

    def launch(command, **_kwargs):
        launches.append(command)
        return SimpleNamespace(returncode=invoke("run", command[4:], http, clock))

    assert invoke("supervise", argv, http, clock, launch=launch) == 0
    result = status(tmp_path, dictionary)
    assert result["state"] == "complete"
    assert result["denominator"] == result["checkpoint"] == 6
    assert result["counts"] == {"positive": 3, "miss": 3, "pending": 0, "error": 0, "reused": 0}
    assert result["request_attempts"] == result["current_attempt_budget_used"] == 12
    assert result["retry"]["supervisor_launches"] == len(launches) == 7
    assert result["retry"]["supervisor_restarts"] == 6
    assert result["retry"]["no_progress_launches"] == 0
    assert result["retry"]["max_no_progress_launches"] == 2
    assert all(b[0] - a[0] >= 2 for a, b in pairwise(http.calls))
    with database(tmp_path, dictionary) as conn:
        assert [row[0] for row in conn.execute("SELECT attempts FROM results")] == [2] * 6
        assert conn.execute("SELECT COUNT(*) FROM events WHERE kind='supervisor_launch'").fetchone()[0] == 7
    log = json.loads((tmp_path / "staging" / dictionary / "job.log").read_text().splitlines()[-1])
    assert log["retry"] == result["retry"]
    assert log["request_attempts"] == 12


def test_repeated_503_on_one_target_consumes_no_progress_cap(tmp_path):
    clock = Clock()
    argv = arguments(tmp_path, "vts", ("sample",), "--max-attempts", "10", "--max-restarts", "1")
    http = HTTP([response(503, headers={"Retry-After": "9"}), response(503)], clock)

    def launch(command, **_kwargs):
        return SimpleNamespace(returncode=invoke("run", command[4:], http, clock))

    assert invoke("supervise", argv, http, clock, launch=launch) == 5
    result = status(tmp_path)
    assert result["terminal_reason"] == "supervisor_budget"
    assert result["checkpoint"] == 0
    assert result["counts"]["miss"] == 0
    assert result["retry"]["attempts"] == result["retry"]["no_progress_launches"] == 2
    assert result["request_attempts"] == 2
    assert http.calls[1][0] - http.calls[0][0] >= 9
    assert invoke("supervise", argv, http, clock, launch=lambda *_a, **_k: pytest.fail("exhausted launched")) == 5
    # Only explicit operator resume resets current budgets; lifetime history survives it.
    assert invoke("resume", argv, HTTP([], clock), clock) == 0
    resumed = status(tmp_path)
    assert resumed["retry"]["no_progress_launches"] == resumed["retry"]["attempts"] == 0
    assert resumed["retry"]["supervisor_launches"] == resumed["request_attempts"] == 2
    assert resumed["current_attempt_budget_used"] == 0
    http = HTTP([response()], clock)
    assert invoke("supervise", argv, http, clock, launch=launch) == 0
    assert status(tmp_path)["retry"]["supervisor_launches"] == 3
    assert status(tmp_path)["request_attempts"] == 3


def test_restart_after_progress_then_crashes_retains_no_progress_cap(tmp_path):
    clock = Clock()
    argv = arguments(tmp_path, "vts", ("sample", "other"), "--max-restarts", "1")
    http = HTTP([response(), KeyboardInterrupt()], clock)

    def progress_then_interrupt(command, **_kwargs):
        assert invoke("run", command[4:], http, clock) == 130
        raise KeyboardInterrupt

    assert invoke("supervise", argv, http, clock, launch=progress_then_interrupt) == 130
    assert status(tmp_path)["checkpoint"] == 1
    assert status(tmp_path)["retry"]["supervisor_launches"] == 1
    assert status(tmp_path)["retry"]["no_progress_launches"] == 0

    # Separate supervisor invocations die after reserving each next child.
    def interrupt(*_args, **_kwargs):
        raise KeyboardInterrupt

    for used in (1, 2):
        assert invoke("supervise", argv, HTTP([], clock), clock, launch=interrupt) == 130
        assert status(tmp_path)["retry"]["no_progress_launches"] == used
        assert status(tmp_path)["retry"]["supervisor_launches"] == used + 1
    assert invoke("supervise", argv, HTTP([], clock), clock, launch=lambda *_a, **_k: pytest.fail("cap reset")) == 5
    assert status(tmp_path)["checkpoint"] == 1
    assert status(tmp_path)["request_attempts"] == 2
    assert status(tmp_path)["retry"]["attempts"] == 1


@pytest.mark.parametrize("last_code,expected", [(401, 3), (403, 3), (200, 4), (503, 5), (404, 0)])
def test_terminal_state_after_progress_and_child_crash_stays_latched(tmp_path, last_code, expected):
    clock = Clock()
    argv = arguments(tmp_path, "vts", ("sample", "other"), "--max-attempts", "1", "--max-restarts", "0")
    http = HTTP([response(), response(last_code, "<article></article>")], clock)
    launches = []

    def terminal_then_crash(command, **_kwargs):
        launches.append(command)
        assert invoke("run", command[4:], http, clock) == expected
        return SimpleNamespace(returncode=-9)

    assert invoke("supervise", argv, http, clock, launch=terminal_then_crash) == expected
    assert len(launches) == 1
    assert status(tmp_path)["checkpoint"] == (2 if expected == 0 else 1)
    assert status(tmp_path)["retry"]["no_progress_launches"] == 0
    assert invoke("supervise", argv, http, clock, launch=lambda *_a, **_k: pytest.fail("terminal launched")) == expected
    assert status(tmp_path)["request_attempts"] == 2


@pytest.mark.parametrize("scenario", ["blocked", "scattered"])
def test_supervise_command_with_real_children_and_fake_http(tmp_path, scenario):
    """Exercise the actual CLI supervisor offline, not a shell-loop model."""
    argv = arguments(tmp_path, "vts", tuple(f"sample{i}" for i in range(6)) if scenario == "scattered" else ("sample",))
    runner = tmp_path / "offline_cli.py"
    runner.write_text(
        f"scenario = {scenario!r}\n"
        + """
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path.cwd()))
from scripts.ingest.dictionary_acquisition import main

root = Path(sys.argv[sys.argv.index("--root") + 1])
root.mkdir(parents=True, exist_ok=True)
timer = [1000.0]
def sleep(seconds):
    timer[0] += seconds
class HTTP:
    def __enter__(self):
        return self
    def __exit__(self, *_):
        pass
    def get(self, *args, **kwargs):
        counter = root / "fake_requests.json"
        requests = json.loads(counter.read_text()) if counter.exists() else []
        code = (503 if len(requests) % 2 == 0 else 404) if scenario == "scattered" else (503 if len(requests) < 2 else 403)
        requests.append({"time": timer[0], "status": code})
        counter.write_text(json.dumps(requests))
        return SimpleNamespace(status_code=code, text="unused private body", headers={})
def launch(command, **kwargs):
    counter = root / "fake_launches.json"
    count = json.loads(counter.read_text()) if counter.exists() else 0
    counter.write_text(json.dumps(count + 1))
    return subprocess.run([sys.executable, __file__, *command[3:]], **kwargs)
raise SystemExit(main(sys.argv[1:], session_factory=HTTP,
                     launch=launch, clock=lambda: timer[0], sleep=sleep))
"""
    )
    command = [sys.executable, str(runner), "supervise", *argv]
    first = subprocess.run(command, capture_output=True, text=True, timeout=30)
    expected = 0 if scenario == "scattered" else 3
    assert first.returncode == expected, first.stderr
    root = tmp_path / "staging"
    attempts = json.loads((root / "fake_requests.json").read_text())
    assert [row["status"] for row in attempts] == ([503, 404] * 6 if scenario == "scattered" else [503, 503, 403])
    assert all(b["time"] - a["time"] >= 2 for a, b in pairwise(attempts))
    launches = 7 if scenario == "scattered" else 3
    assert json.loads((root / "fake_launches.json").read_text()) == launches
    assert status(tmp_path)["state"] == ("complete" if scenario == "scattered" else "blocked")
    if scenario == "scattered":
        assert status(tmp_path)["checkpoint"] == status(tmp_path)["denominator"] == 6
        assert status(tmp_path)["retry"]["no_progress_launches"] == 0
    second = subprocess.run(command, capture_output=True, text=True, timeout=30)
    assert second.returncode == expected
    assert json.loads((root / "fake_requests.json").read_text()) == attempts
    assert json.loads((root / "fake_launches.json").read_text()) == launches
    assert "unused private body" not in first.stdout + first.stderr + (root / "vts" / "job.log").read_text()


@pytest.mark.parametrize(
    "override",
    [
        ["--dictionary", "invalid/private"],
        ["--delay", "1"],
        ["--delay", "NaN"],
        ["--timeout", "0"],
        ["--backoff", "-1"],
        ["--max-attempts", "0"],
        ["--max-restarts", "11"],
        ["--start-wordid", "2"],
    ],
)
def test_cli_admission_refuses_without_network_and_journals(tmp_path, override, capsys):
    clock = Clock()
    argv = arguments(tmp_path)
    assert invoke("run", argv + override, HTTP([], clock), clock) == 2
    output = capsys.readouterr().out
    assert str(tmp_path) not in output
    assert "invalid/private" not in output
    refusal = json.loads((tmp_path / "staging" / "refusal.json").read_text())
    assert refusal["state"] == "invalid"
    assert (tmp_path / "staging" / "refusals.log").is_file()


@pytest.mark.parametrize("entries", [[], [{}], [{"lemma": 42}], [{"lemma": " "}], [{"lemma": "/"}]])
def test_bad_manifest_refusal(tmp_path, entries):
    clock = Clock()
    argv = arguments(tmp_path)
    (tmp_path / "manifest.json").write_text(json.dumps({"entries": entries}))
    assert invoke("run", argv, HTTP([], clock), clock) == 2


def test_official_range_admission_and_aliases(tmp_path):
    clock = Clock()
    argv = arguments(tmp_path, "sum20_official")
    assert invoke("run", [*argv, "--end-wordid", "4"], HTTP([], clock), clock) == 2
    assert invoke("run", [*argv, "--manifest", "manifest.json"], HTTP([], clock), clock) == 2
    assert acquisition.dictionary_name("karavansky") == "synonyms_karavansky"


@pytest.mark.parametrize("action", ["status", "resume"])
def test_missing_job_refuses(tmp_path, action):
    clock = Clock()
    assert invoke(action, arguments(tmp_path), HTTP([], clock), clock) == 2


def test_cli_help_and_argparse_error(capsys):
    with pytest.raises(SystemExit) as help_exit:
        acquisition.main(["--help"])
    assert help_exit.value.code == 0
    output = capsys.readouterr().out
    assert all(section in output for section in ("Examples:", "Outputs:", "Exit codes:", "Related:"))
    for option in ("--root", "--dictionary", "--max-attempts", "--max-restarts", "resume", "supervise"):
        assert option in output
    with pytest.raises(SystemExit) as invalid:
        acquisition.main(["run"])
    assert invalid.value.code == 2
    with pytest.raises(SystemExit) as secret_input:
        acquisition.main(["run", "--root", "private_location", "--dictionary", "vts", "--timeout", "secret"])
    assert secret_input.value.code == 2
    error = capsys.readouterr().err
    assert "private_location" not in error and "secret" not in error
    assert "invalid_arguments" in error


def test_atomic_json_replaces_projection_and_refusal_storage_failure(tmp_path, capsys):
    destination = tmp_path / "status.json"
    acquisition.atomic_json(destination, {"counts": {"positive": 1}})
    acquisition.atomic_json(destination, {"counts": {"positive": 2}})
    assert json.loads(destination.read_text())["counts"]["positive"] == 2
    assert not (tmp_path / "status.json.tmp").exists()
    root = tmp_path / "not_a_directory"
    root.write_text("occupied")
    assert acquisition.refusal(root, "invalid", "input_or_storage_error") == 2
    assert json.loads(capsys.readouterr().out)["evidence_error"] == "refusal_storage_unavailable"


@pytest.mark.parametrize("dictionary", ["vts", "sum20_official"])
@pytest.mark.parametrize(
    "code,expected",
    [
        (200, "positive"),
        (404, "not_found"),
        (401, "blocked"),
        (403, "blocked"),
        (408, "transient_error"),
        (425, "transient_error"),
        (429, "transient_error"),
        (500, "transient_error"),
        (599, "transient_error"),
        (201, "blocked"),
        (204, "blocked"),
        (301, "blocked"),
        (400, "blocked"),
        (407, "blocked"),
        (499, "blocked"),
        (600, "blocked"),
    ],
)
def test_transport_semantics_match_legacy_strict_paths(monkeypatch, dictionary, code, expected):
    from scripts.lexicon import enrich_manifest as em
    from scripts.wiki import sum20_official as official

    clock = Clock()
    document = OFFICIAL_HTML if dictionary == "sum20_official" else SLOVNYK_HTML
    http = HTTP([response(code, document)], clock)
    spec = {"dictionary": dictionary, "timeout": 1}
    row = {"target": "5" if dictionary == "sum20_official" else "sample", "lookup": "sample"}
    status, numeric, _payload, _retry = acquisition.fetch_once(http, spec, row, clock())
    assert (status, numeric) == (expected, code)
    if dictionary == "sum20_official":
        legacy_http = HTTP([response(code, document)], clock)
        legacy_http.headers = {}
        result = official.fetch_sum20_wordid(5, session=legacy_http, retries=0)
        semantic = (
            "blocked"
            if result.terminal and result.status != "parse_error"
            else ("positive" if result.status == "ok" else result.status)
        )
        assert semantic == expected
    else:
        monkeypatch.delenv("LEXICON_SLOVNYK_OFFLINE", raising=False)
        monkeypatch.setattr(em, "_polite_slovnyk_delay", lambda: None)
        monkeypatch.setattr(em, "_SLOVNYK_MAX_RETRIES", 0)
        monkeypatch.setattr(em.requests, "get", lambda *_args, **_kwargs: response(code, document))
        result = em._fetch_slovnyk_outcome("sample", "sample", dictionary)
        assert result.status == expected
    assert result.http_status == numeric


@pytest.mark.parametrize("dictionary", ["vts", "sum20_official"])
@pytest.mark.parametrize("bad", ["empty", "network"])
def test_transport_ambiguity_and_network_semantics_match(monkeypatch, dictionary, bad):
    from scripts.lexicon import enrich_manifest as em
    from scripts.wiki import sum20_official as official

    clock = Clock()

    def reply():
        if bad == "network":
            raise requests.ConnectionError("private request detail")
        return response(200, "<article></article>")

    http = HTTP([], clock)
    http.get = lambda *_args, **_kwargs: reply()
    expected = "parse_error" if bad == "empty" else "transient_error"
    status, numeric, *_ = acquisition.fetch_once(
        http, {"dictionary": dictionary, "timeout": 1}, {"target": "5", "lookup": "sample"}, clock()
    )
    assert status == expected
    if dictionary == "sum20_official":
        http.headers = {}
        result = official.fetch_sum20_wordid(5, session=http, retries=0)
    else:
        monkeypatch.delenv("LEXICON_SLOVNYK_OFFLINE", raising=False)
        monkeypatch.setattr(em, "_polite_slovnyk_delay", lambda: None)
        monkeypatch.setattr(em, "_SLOVNYK_MAX_RETRIES", 0)
        monkeypatch.setattr(em.requests, "get", http.get)
        result = em._fetch_slovnyk_outcome("sample", "sample", "vts")
    assert result.status == expected
    assert result.http_status == numeric


# --- operator progress lines, frozen transport identity and kill-and-rerun resume ---


def progress_lines(tmp_path, dictionary="vts"):
    return (tmp_path / "staging" / dictionary / "progress.log").read_text().splitlines()


def test_console_and_progress_file_carry_the_same_readable_lines(tmp_path, capsys):
    clock = Clock()
    argv = arguments(tmp_path, "vts", ("a", "b", "c", "d"), "--progress-interval", "1")
    secret = response(200, SLOVNYK_HTML.replace("synthetic", "private secret"))
    assert invoke("run", argv, HTTP([secret, response(503)], clock), clock) == 75
    first = capsys.readouterr().err.splitlines()
    assert progress_lines(tmp_path) == first
    assert "run: starting at 0/4 (0.0%)" in first[0]
    assert any("1/4  25.0%  positive  a http=200" in line for line in first)
    assert any("retry b attempt 1/4 http=503; next attempt in" in line for line in first)
    assert any("progress 1/4 (25.0%) rate=" in line and "eta=unknown" in line and "last=a" in line for line in first)
    assert "job state transient (retryable_request), exit 75" in first[-1]

    assert invoke("run", argv, HTTP([response(), response(404), response()], clock), clock) == 0
    second = capsys.readouterr().err.splitlines()
    assert progress_lines(tmp_path) == first + second
    assert "run: resuming at 1/4 (25.0%), job state transient, attempts used on next target 1" in second[0]
    assert any("not_found c http=404" in line for line in second)
    assert any(line.endswith("4/4 100.0%  positive  d http=200") for line in second)
    assert any(" eta=" in line and "eta=unknown" not in line for line in second)
    assert "job state complete (target_resolved), exit 0" in second[-1]
    assert "private secret" not in "\n".join(first + second)
    # The machine projections keep their shape for existing readers.
    assert json.loads((tmp_path / "staging" / "vts" / "job.log").read_text().splitlines()[-1])["state"] == "complete"
    assert status(tmp_path)["checkpoint"] == 4


def test_unwritable_progress_file_never_stops_the_job(tmp_path, capsys):
    clock = Clock()
    argv = arguments(tmp_path)
    (tmp_path / "staging" / "vts").mkdir(parents=True)
    (tmp_path / "staging" / "vts" / "progress.log").mkdir()
    assert invoke("run", argv, HTTP([response()], clock), clock) == 0
    err = capsys.readouterr().err
    assert err.count("warning: progress file unwritable") == 1
    assert "positive  sample" in err


def test_progress_interval_must_be_positive_and_finite(capsys):
    for bad in ("0", "-1", "nan", "inf"):
        with pytest.raises(SystemExit) as exc:
            acquisition.main(["status", "--root", "r", "--dictionary", "vts", "--progress-interval", bad])
        assert exc.value.code == 2
    assert "invalid_arguments" in capsys.readouterr().err


def test_transport_identity_binds_only_fetch_and_parse_code():
    source = Path(acquisition.__file__).read_text(encoding="utf-8")
    base = acquisition.transport_identity(source)
    # Logging, status projection, retry plumbing, CLI text and unrelated code are not identity.
    for unbound in (
        source + "\n\ndef added():\n    return 1\n",
        source.replace('"job.log"', '"other.log"'),
        source.replace("def report(", "# note\ndef report(").replace("def acquire(", "# note\ndef acquire("),
        source.replace("run once, supervise", "run one pass, supervise"),
        source.replace("progress.tick()", "progress.summary()"),
    ):
        assert unbound != source
        assert acquisition.transport_identity(unbound) == base
    # What is requested, reused and parsed is identity.
    for bound in (
        source.replace("allow_redirects=False", "allow_redirects=True"),
        source.replace('"Accept": "text/html,application/xhtml+xml"', '"Accept": "*/*"'),
        source.replace('"invalid_budget"', '"invalid_limits"'),
        source.replace('provenance="observed_http"', 'provenance="observed"'),
        source.replace('"legacy_positive"', '"legacy"'),
        source.replace("max(0, seconds) if math.isfinite(seconds) else 0", "max(0, seconds)"),
    ):
        assert bound != source
        assert acquisition.transport_identity(bound) != base
    with pytest.raises(RuntimeError, match="transport_functions_missing"):
        acquisition.transport_identity(source.replace("def fetch_once(", "def fetch_other("))


def freeze_previous_transport(tmp_path, dictionary="vts"):
    """Rewrite the stored identity to a different transport hash, as an older checkout would have frozen."""
    with database(tmp_path, dictionary) as conn, conn:
        spec = json.loads(conn.execute("SELECT spec FROM job").fetchone()["spec"])
        spec["transport_sha256"] = acquisition.digest(b"whole file of the earlier checkout")
        text = acquisition.packed(spec)
        conn.execute("UPDATE job SET spec=?, fingerprint=?", (text, acquisition.digest(text.encode())))
    return spec["transport_sha256"]


def durable_progress(tmp_path):
    with database(tmp_path) as conn:
        return (
            [tuple(row) for row in conn.execute("SELECT * FROM results ORDER BY position")],
            [tuple(row) for row in conn.execute("SELECT * FROM events ORDER BY id")],
            tuple(conn.execute("SELECT restarts, state, reason, started FROM job").fetchone()),
        )


def test_changed_transport_is_refused_until_an_explicit_recorded_rebind(tmp_path):
    clock = Clock()
    argv = arguments(tmp_path, "vts", ("a", "b", "c"))
    assert invoke("run", argv, HTTP([response(), response(503)], clock), clock) == 75
    previous = freeze_previous_transport(tmp_path)
    results, events, job = durable_progress(tmp_path)
    before = status(tmp_path)

    for action in ("run", "supervise", "resume"):
        no_http = HTTP([], clock)
        launch = lambda *_a, **_k: pytest.fail("launched against drifted transport")  # noqa: E731
        assert invoke(action, argv, no_http, clock, launch=launch) == 2
        assert json.loads((tmp_path / "staging" / "refusal.json").read_text())["terminal_reason"] == "transport_changed"
    assert durable_progress(tmp_path) == (results, events, job)

    assert invoke("rebind", argv, HTTP([], clock), clock) == 0
    after_results, after_events, after_job = durable_progress(tmp_path)
    assert after_results == results
    assert after_job == job  # launches, state and start time untouched
    assert after_events[:-1] == events
    assert after_events[-1][3] == "transport_rebind"
    with database(tmp_path) as conn:
        rebinds = [tuple(r) for r in conn.execute("SELECT * FROM transport_rebinds")]
    current = acquisition.transport_identity(Path(acquisition.__file__).read_text(encoding="utf-8"))
    assert rebinds == [(after_events[-1][0], previous, current)]
    now = status(tmp_path)
    assert now["retry"] == before["retry"]  # no budget reset
    assert now["counts"] == before["counts"]
    assert now["checkpoint"] == before["checkpoint"] == 1

    assert invoke("rebind", argv, HTTP([], clock), clock) == 0  # idempotent, records nothing
    assert durable_progress(tmp_path)[1] == after_events
    assert "rebind: already bound" in progress_lines(tmp_path)[-1]

    assert invoke("run", argv, HTTP([response(), response()], clock), clock) == 0
    assert status(tmp_path)["state"] == "complete"
    assert status(tmp_path)["retry"]["attempts"] == 0


def test_rebind_never_hides_other_drift_or_a_busy_job(tmp_path):
    clock = Clock()
    argv = arguments(tmp_path, "vts", ("a", "b"))
    assert invoke("rebind", argv, HTTP([], clock), clock) == 2  # no job yet
    assert invoke("run", argv, HTTP([response(503)], clock), clock) == 75
    freeze_previous_transport(tmp_path)
    frozen = durable_progress(tmp_path)

    manifest = tmp_path / "manifest.json"
    original = manifest.read_text()
    manifest.write_text(original + " ")
    assert invoke("rebind", argv, HTTP([], clock), clock) == 2
    assert json.loads((tmp_path / "staging" / "refusal.json").read_text())["terminal_reason"] == "frozen_input_mismatch"
    manifest.write_text(original)
    assert invoke("rebind", [*argv, "--max-attempts", "9"], HTTP([], clock), clock) == 2

    directory = tmp_path / "staging" / "vts"
    for held in ("writer.lock", "supervisor.lock"):
        with acquisition.lock(directory / held):
            assert invoke("rebind", argv, HTTP([], clock), clock) == 6
    with database(tmp_path) as conn, conn:
        conn.execute("UPDATE results SET target='other' WHERE position=0")
    assert invoke("rebind", argv, HTTP([], clock), clock) == 2
    assert (
        json.loads((tmp_path / "staging" / "refusal.json").read_text())["terminal_reason"] == "durable_targets_mismatch"
    )
    with database(tmp_path) as conn, conn:
        conn.execute("UPDATE results SET target='a' WHERE position=0")
    assert durable_progress(tmp_path) == frozen
    with database(tmp_path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE name='transport_rebinds'").fetchone()[0] == 0


KILL_RUNNER = """
import subprocess, sys, time
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path.cwd()))
from scripts.ingest.dictionary_acquisition import main

root = Path(sys.argv[sys.argv.index("--root") + 1])
root.mkdir(parents=True, exist_ok=True)
timer = [1000.0]
def sleep(seconds):
    timer[0] += seconds
class HTTP:
    def __enter__(self):
        return self
    def __exit__(self, *_):
        pass
    def get(self, url, **kwargs):
        with (root / "fake_requests.log").open("a") as handle:
            handle.write(url.rsplit("/", 1)[-1] + "\\n")
        if len((root / "fake_requests.log").read_text().split()) == 3 and not (root / "unblocked").exists():
            (root / "blocked").write_text("x")
            time.sleep(120)
        return SimpleNamespace(status_code=200, text=HTML, headers={})
def launch(command, **kwargs):
    return subprocess.run([sys.executable, __file__, *command[3:]], **kwargs)
raise SystemExit(main(sys.argv[1:], session_factory=HTTP, launch=launch, clock=lambda: timer[0], sleep=sleep))
"""


@pytest.mark.parametrize(
    "action,signum,code,handled",
    [
        ("run", signal.SIGINT, 130, True),
        ("run", signal.SIGTERM, 143, True),
        ("run", signal.SIGHUP, 129, True),
        ("run", signal.SIGKILL, -9, False),
        ("supervise", signal.SIGTERM, 143, True),
        ("supervise", signal.SIGKILL, -9, False),
    ],
)
def test_kill_during_a_request_then_rerun_resumes_from_the_durable_checkpoint(tmp_path, action, signum, code, handled):
    lemmas = ("one", "two", "three", "four", "five")
    argv = arguments(tmp_path, "vts", lemmas)
    root = tmp_path / "staging"
    runner = tmp_path / "kill_runner.py"
    runner.write_text(f"HTML = {SLOVNYK_HTML!r}\n" + KILL_RUNNER)
    command = [sys.executable, str(runner), action, *argv]
    repo = Path(__file__).resolve().parents[1]

    # Own session so a hard kill takes the supervisor's child with it, as a reboot or tmux kill does.
    first = subprocess.Popen(command, cwd=repo, stderr=subprocess.PIPE, text=True, start_new_session=True)
    deadline = time.monotonic() + 30
    while not (root / "blocked").exists():
        assert first.poll() is None and time.monotonic() < deadline, "runner never reached the third request"
        time.sleep(0.05)
    if handled:
        first.send_signal(signum)
    else:
        os.killpg(first.pid, signum)
    err = first.communicate(timeout=30)[1]
    assert first.returncode == code
    interrupted = [line for line in progress_lines(tmp_path) if "interrupted by" in line]
    if handled:
        name = signal.Signals(signum).name
        assert len(interrupted) == 1 and f"interrupted by {name}" in interrupted[0]
        assert ("at 2/5 (40.0%)" in interrupted[0]) == (action == "run")
        assert "progress is saved. Rerun the same command" in interrupted[0]
        assert interrupted[0] in err
    else:
        assert interrupted == []
    # Two targets are durable; the killed request is an unresolved, already-counted attempt.
    with database(tmp_path) as conn:
        assert [tuple(r) for r in conn.execute("SELECT target,status,attempts FROM results ORDER BY position")] == [
            ("one", "positive", 1),
            ("two", "positive", 1),
            ("three", "transient_error", 1),
            ("four", "pending", 0),
            ("five", "pending", 0),
        ]

    (root / "unblocked").write_text("x")
    second = subprocess.run(command, cwd=repo, capture_output=True, text=True, timeout=60)
    assert second.returncode == 0, second.stderr
    assert "run: resuming at 2/5 (40.0%)" in second.stderr
    assert "job state complete (target_resolved), exit 0" in second.stderr
    # Resolved targets are never refetched; only the interrupted one is requested again.
    assert (root / "fake_requests.log").read_text().split() == ["one", "two", "three", "three", "four", "five"]
    final = status(tmp_path)
    assert (final["state"], final["checkpoint"], final["denominator"]) == ("complete", 5, 5)
    assert final["counts"]["positive"] == 5
    assert final["request_attempts"] == 6
