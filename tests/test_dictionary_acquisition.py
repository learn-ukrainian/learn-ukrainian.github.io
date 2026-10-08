"""Offline staging and CLI contracts; independent held-out proof belongs to the driver."""

from __future__ import annotations

import contextlib
import json
import subprocess
import sys
from itertools import pairwise
from types import SimpleNamespace

import pytest
import requests

from scripts.ingest import dictionary_acquisition as acquisition

SLOVNYK_HTML = '<html><section id="dictionary-article"><article><p>synthetic article</p></article></section></html>'
OFFICIAL_HTML = (
    '<article><div class="ENTRY"><span class="WORD">SAMPLE</span>'
    '<div class="INTF"><span class="FORMULA">Synthetic definition</span></div></div></article>'
)


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
    with database(tmp_path, "sum20_official") as conn:
        payload = json.loads(conn.execute("SELECT payload FROM results WHERE position=0").fetchone()[0])
        assert payload["article"]["wordid"] == 5
        assert payload["parser_version"] == acquisition.PARSER_VERSION
        assert payload["content_sha256"]


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


@pytest.mark.parametrize("code", [408, 425, 429, 500, 599])
def test_http_retryable_statuses_are_errors(tmp_path, code):
    clock = Clock()
    assert invoke("run", arguments(tmp_path), HTTP([response(code)], clock), clock) == 75
    result = status(tmp_path)
    assert result["counts"]["error"] == 1
    assert result["counts"]["miss"] == 0


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
        {"source_url": "https://user:secret@slovnyk.me/dict/vts/sample"},
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


def test_missing_and_malformed_seed_are_safe(tmp_path):
    assert acquisition.seed_row(tmp_path, "sample", "sample", "vts") is None
    path = write_seed(tmp_path, positive_row())
    path.write_text("[1]")
    assert acquisition.seed_row(tmp_path, "sample", "sample", "vts") is None
    path.write_text("{")
    assert acquisition.seed_row(tmp_path, "sample", "sample", "vts") is None


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
    with pytest.raises(KeyboardInterrupt):
        invoke("run", argv, http, clock)
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
        invoke("run", command[4:], http, clock)

    with pytest.raises(KeyboardInterrupt):
        invoke("supervise", argv, http, clock, launch=progress_then_interrupt)
    assert status(tmp_path)["checkpoint"] == 1
    assert status(tmp_path)["retry"]["supervisor_launches"] == 1
    assert status(tmp_path)["retry"]["no_progress_launches"] == 0

    # Separate supervisor invocations die after reserving each next child.
    def interrupt(*_args, **_kwargs):
        raise KeyboardInterrupt

    for used in (1, 2):
        with pytest.raises(KeyboardInterrupt):
            invoke("supervise", argv, HTTP([], clock), clock, launch=interrupt)
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


def test_supervisor_restart_after_own_crash_does_not_reset_budget(tmp_path):
    clock = Clock()
    argv = arguments(tmp_path, "vts", ("sample",), "--max-restarts", "0")

    def interrupted(*_a, **_k):
        raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        invoke("supervise", argv, HTTP([], clock), clock, launch=interrupted)
    assert invoke("supervise", argv, HTTP([], clock), clock, launch=lambda *_a, **_k: pytest.fail("budget reset")) == 5


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


@pytest.mark.parametrize("manifest", ["[]", "{", '{"entries": 1}'])
def test_bad_manifest_schema_and_json_refusal(tmp_path, manifest):
    clock = Clock()
    argv = arguments(tmp_path)
    (tmp_path / "manifest.json").write_text(manifest)
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


def test_packing_is_stable_and_digest_matches():
    assert acquisition.packed({"b": 2, "a": 1}) == '{"a":1,"b":2}'
    assert acquisition.digest(b"") == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
