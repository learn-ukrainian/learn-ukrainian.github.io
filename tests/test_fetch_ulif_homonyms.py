"""Offline tests for the targeted ULIF homonym runner (#8400 step c)."""

from __future__ import annotations

import os
import shlex
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.lexicon.runner.fetch_ulif_20k import DictUAClient
from scripts.lexicon.runner.fetch_ulif_homonyms import (
    EXIT_FORBIDDEN,
    EXIT_INTERRUPTED,
    EXIT_OK,
    EXIT_RETRY_STORM,
    EXIT_USAGE,
    HomonymFetcher,
    HttpResult,
    SpellingLedger,
    _dedupe_register_rows,
    _write_group,
    build_a1_a2_spellings,
    declared_user_agent,
    main,
    parse_stored,
    run_fetch,
    status_text,
)
from scripts.lexicon.runner.ulif_dictua_parse import parse_ulif_entry

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "ulif_dictua"


def _html(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def _tokens(html: str) -> dict[str, str]:
    tokens = DictUAClient._tokens(html)
    assert tokens is not None
    return tokens


def _noop_sleep(_seconds: float) -> None:
    return None


def _write_spellings(path: Path, spellings: list[str]) -> Path:
    path.write_text("".join(f"{spelling}\n" for spelling in spellings), encoding="utf-8")
    return path


def _register(words: list[str], viewstate: str, *, paging: bool = True) -> str:
    rows = []
    for index, word in enumerate(words):
        rows.append(
            '<tr><td><a href="javascript:__doPostBack(&#39;ctl00$ContentPlaceHolder1$dgv&#39;,'
            f'&#39;Select${index}&#39;)">{word}</a></td></tr>'
        )
    paging_html = ""
    if paging:
        paging_html = (
            '<input type="image" name="ctl00$ContentPlaceHolder1$backpage" />'
            '<input type="image" name="ctl00$ContentPlaceHolder1$nextpage" />'
        )
    return (
        f'<input type="hidden" name="__VIEWSTATE" value="{viewstate}" />'
        '<input type="hidden" name="__VIEWSTATEGENERATOR" value="GEN" />'
        f'<input type="hidden" name="__EVENTVALIDATION" value="EV-{viewstate}" />'
        f"{paging_html}"
        f'<table id="ContentPlaceHolder1_dgv">{"".join(rows)}</table>'
        '<span id="ContentPlaceHolder1_rlength">Реєстрових слів - 262812</span>'
    )


def _entry(headword: str, gloss: str, viewstate: str, tabs: str) -> str:
    return (
        f'<input type="hidden" name="__VIEWSTATE" value="{viewstate}" />'
        '<input type="hidden" name="__VIEWSTATEGENERATOR" value="GEN" />'
        f'<input type="hidden" name="__EVENTVALIDATION" value="EV-{viewstate}" />'
        f"{tabs}"
        '<div id="ContentPlaceHolder1_article">'
        f'<span class="word_style">{headword}</span>'
        '<span class="gram_style">– іменник</span>'
        f'<div class="comment_style">{gloss}</div>'
        "</div>"
        '<span id="ContentPlaceHolder1_rlength">Реєстрових слів - 262812</span>'
    )


def _run(tmp_path: Path, spellings: list[str], transport, **kwargs) -> int:
    return run_fetch(
        spellings=spellings,
        state_dir=tmp_path / "state",
        db_path=tmp_path / "cache.db",
        delay_seconds=kwargs.pop("delay_seconds", 1.0),
        transport=transport,
        sleep=kwargs.pop("sleep", _noop_sleep),
        scanner=kwargs.pop("scanner", lambda: False),
        **kwargs,
    )


def _ledger(tmp_path: Path) -> SpellingLedger:
    return SpellingLedger(tmp_path / "state" / "ledger.sqlite")


class _Scripted:
    def __init__(self, handler) -> None:
        self.calls: list[tuple[str, dict[str, str] | None]] = []
        self.handler = handler

    def __call__(self, method: str, data: dict[str, str] | None) -> HttpResult:
        self.calls.append((method, data))
        return self.handler(method, data)


def test_declared_user_agent_is_the_20k_client():
    client = DictUAClient(delay_seconds=1.0, timeout_seconds=20)
    assert declared_user_agent() == client.headers["User-Agent"]


def test_zamok_group_stores_three_entries_and_tab_sets(tmp_path):
    entry = {
        "Select$4": _html("zamok-entry-1.html"),
        "Select$5": _html("zamok-entry-2.html"),
        "Select$6": _html("zamok-entry-3.html"),
    }
    entry_view = {key: _tokens(html)["__VIEWSTATE"] for key, html in entry.items()}
    tabs = {
        entry_view["Select$4"]: {"paradigm": _html("zamok-entry-1-par.html")},
        entry_view["Select$5"]: {
            "paradigm": _html("zamok-entry-2-par.html"),
            "synonyms": _html("zamok-entry-2-syn.html"),
            "phraseology": _html("zamok-entry-2-phras.html"),
        },
        entry_view["Select$6"]: {
            "paradigm": _html("zamok-entry-3.html"),
            "synonyms": _html("zamok-entry-3.html"),
            "phraseology": _html("zamok-entry-3.html"),
        },
    }

    def handler(method: str, data: dict[str, str] | None) -> HttpResult:
        if method == "GET":
            return HttpResult(200, _html("zamok-seed.html"), {})
        assert data is not None
        if f"{'ctl00$ContentPlaceHolder1$search'}.x" in data:
            return HttpResult(200, _html("zamok-tsearch.html"), {})
        argument = data.get("__EVENTARGUMENT", "")
        if argument in entry:
            return HttpResult(200, entry[argument], {})
        viewstate = data["__VIEWSTATE"]
        for kind, control in (
            ("paradigm", "ctl00$ContentPlaceHolder1$par"),
            ("synonyms", "ctl00$ContentPlaceHolder1$syn"),
            ("phraseology", "ctl00$ContentPlaceHolder1$phras"),
            ("antonyms", "ctl00$ContentPlaceHolder1$ant"),
        ):
            if f"{control}.x" in data:
                return HttpResult(200, tabs[viewstate][kind], {})
        raise AssertionError(data)

    scripted = _Scripted(handler)
    assert _run(tmp_path, ["замок"], scripted) == EXIT_OK
    ledger = _ledger(tmp_path)
    try:
        row = ledger.conn.execute("SELECT state, entry_count, straddled_boundary FROM spellings").fetchone()
        assert (row["state"], row["entry_count"], row["straddled_boundary"]) == ("stored", 3, 0)
        tab_rows = ledger.conn.execute(
            "SELECT homonym_index, tab_kind FROM responses WHERE role = 'tab' ORDER BY homonym_index, tab_kind"
        ).fetchall()
        assert [(row["homonym_index"], row["tab_kind"]) for row in tab_rows] == [
            (1, "paradigm"),
            (2, "paradigm"),
            (2, "phraseology"),
            (2, "synonyms"),
            (3, "paradigm"),
            (3, "phraseology"),
            (3, "synonyms"),
        ]
        request = ledger.conn.execute("SELECT request_sha256 FROM responses WHERE role = 'entry' LIMIT 1").fetchone()
        cache = sqlite3.connect(tmp_path / "cache.db")
        payload = cache.execute(
            "SELECT body FROM ulif_dictua_raw_responses WHERE response_sha256 = ?",
            (request["request_sha256"],),
        ).fetchone()[0]
        text = bytes(payload).decode("utf-8")
        assert "__VIEWSTATE" in text
        assert "/wEPDw" not in text
        differing = parse_stored(ledger, cache)
        rows = cache.execute(
            """
            SELECT homonym_index, canonical_headword, sense_gloss, homonym_checked
            FROM ulif_dictua_entries ORDER BY homonym_index
            """
        ).fetchall()
        cache.close()
    finally:
        ledger.close()
    assert differing == 0
    assert rows == [
        (1, "За́мок", "(населений пункт в Україні)", 1),
        (2, "за́мок", "(будівля)", 1),
        (3, "замо́к", "(пристрій для замикання тощо)", 1),
    ]


def test_invariable_duzhe_records_one_entry_and_its_tabs(tmp_path):
    page = _register(["інше", "ду́же", "ще"], "seed", paging=False)
    entry = _html("duzhe.html")

    def handler(method: str, data: dict[str, str] | None) -> HttpResult:
        if method == "GET" or (data and "search.x" in "".join(data)):
            return HttpResult(200, page, {})
        if data and data.get("__EVENTARGUMENT") == "Select$1":
            return HttpResult(200, entry, {})
        return HttpResult(200, entry, {})

    assert _run(tmp_path, ["дуже"], _Scripted(handler)) == EXIT_OK
    cache = sqlite3.connect(tmp_path / "cache.db")
    ledger = _ledger(tmp_path)
    try:
        digest = ledger.conn.execute("SELECT response_sha256 FROM responses WHERE role = 'entry'").fetchone()[
            "response_sha256"
        ]
        body = cache.execute(
            "SELECT body FROM ulif_dictua_raw_responses WHERE response_sha256 = ?",
            (digest,),
        ).fetchone()[0]
        parsed = parse_ulif_entry(bytes(body).decode("utf-8"), homonym_index=1)
        tabs = [
            row["tab_kind"]
            for row in ledger.conn.execute("SELECT tab_kind FROM responses WHERE role = 'tab' ORDER BY tab_kind")
        ]
        assert parsed["is_invariable"] is True
        assert tabs == ["paradigm", "synonyms"]
        assert ledger.conn.execute("SELECT entry_count FROM spellings").fetchone()["entry_count"] == 1
    finally:
        cache.close()
        ledger.close()


def test_boundary_group_fetches_the_next_page_from_the_pristine_viewstate(tmp_path):
    """Synthetic two-page register boundary built in test code (not an HTML fixture)."""
    fillers = [f"слово{index}" for index in range(24)]
    page = _register([*fillers, "Кра́й"], "page-a")
    nxt = _register(["край", "інше"], "page-b", paging=False)
    entry_a = _entry("Кра́й", "(перше)", "entry-a", '<input type="image" name="ctl00$ContentPlaceHolder1$par" />')
    entry_b = _entry("край", "(друге)", "entry-b", '<input type="image" name="ctl00$ContentPlaceHolder1$par" />')
    payloads: list[dict[str, str]] = []

    def handler(method: str, data: dict[str, str] | None) -> HttpResult:
        if method == "GET":
            return HttpResult(200, page, {})
        assert data is not None
        payloads.append(data)
        if any(key.endswith("search.x") for key in data):
            return HttpResult(200, page, {})
        if any(key.endswith("nextpage.x") for key in data):
            return HttpResult(200, nxt, {})
        if data.get("__EVENTARGUMENT") == "Select$24":
            return HttpResult(200, entry_a, {})
        if data.get("__EVENTARGUMENT") == "Select$0":
            return HttpResult(200, entry_b, {})
        return HttpResult(200, entry_a if data.get("__VIEWSTATE") == "entry-a" else entry_b, {})

    assert _run(tmp_path, ["край"], _Scripted(handler)) == EXIT_OK
    next_posts = [data for data in payloads if any(key.endswith("nextpage.x") for key in data)]
    assert len(next_posts) == 1
    assert next_posts[0]["__VIEWSTATE"] == "page-a"
    assert next_posts[0]["__EVENTTARGET"] == ""
    assert next_posts[0]["__EVENTARGUMENT"] == ""
    ledger = _ledger(tmp_path)
    try:
        row = ledger.conn.execute("SELECT state, entry_count, straddled_boundary FROM spellings").fetchone()
        positions = [
            row["register_position"]
            for row in ledger.conn.execute(
                "SELECT register_position FROM responses WHERE role = 'entry' ORDER BY homonym_index"
            )
        ]
    finally:
        ledger.close()
    assert (row["state"], row["entry_count"], row["straddled_boundary"]) == ("stored", 2, 1)
    assert positions == ["0:24", "1:0"]


def test_resume_after_injected_failure_mid_spelling(tmp_path):
    page = _register(["інше"], "seed", paging=False)
    phase = {"fail": True}

    def handler(method: str, data: dict[str, str] | None) -> HttpResult:
        if method == "GET" and phase["fail"] and data is None and phase.get("saw_post"):
            raise RuntimeError("injected failure")
        if method == "POST":
            phase["saw_post"] = True
        return HttpResult(200, page, {})

    scripted = _Scripted(handler)
    assert _run(tmp_path, ["нема", "теж"], scripted) == EXIT_INTERRUPTED
    ledger = _ledger(tmp_path)
    try:
        states = {row["spelling"]: row["state"] for row in ledger.conn.execute("SELECT spelling, state FROM spellings")}
    finally:
        ledger.close()
    assert states == {"нема": "absent_from_ulif", "теж": "pending"}
    phase["fail"] = False
    second = _Scripted(handler)
    assert _run(tmp_path, ["нема", "теж"], second) == EXIT_OK
    assert [data.get("ctl00$ContentPlaceHolder1$tsearch") for _method, data in second.calls if data] == ["теж"]
    ledger = _ledger(tmp_path)
    try:
        states = {
            row["spelling"]: row["state"]
            for row in ledger.conn.execute("SELECT spelling, state FROM spellings ORDER BY spelling")
        }
    finally:
        ledger.close()
    assert states == {"нема": "absent_from_ulif", "теж": "absent_from_ulif"}


def test_http_403_stops_the_run(tmp_path):
    seen: list[str | None] = []

    def handler(method: str, data: dict[str, str] | None) -> HttpResult:
        seen.append(None if data is None else data.get("ctl00$ContentPlaceHolder1$tsearch"))
        return HttpResult(403, "forbidden", {})

    assert _run(tmp_path, ["перше", "друге"], _Scripted(handler)) == EXIT_FORBIDDEN
    assert seen == [None]
    ledger = _ledger(tmp_path)
    try:
        rows = {
            row["spelling"]: (row["state"], row["error"])
            for row in ledger.conn.execute("SELECT spelling, state, error FROM spellings")
        }
    finally:
        ledger.close()
    assert rows == {"перше": ("error", "http_403"), "друге": ("pending", "")}


def test_lock_refuses_a_second_runner(tmp_path):
    state = tmp_path / "state"
    state.mkdir()
    lock = state / "runner.lock"
    lock.write_text(f"{os.getpid()}\n2026-09-21T00:00:00+00:00\n", encoding="utf-8")
    before = lock.read_bytes()
    with pytest.raises(SystemExit, match="live pid"):
        _run(tmp_path, ["замок"], _Scripted(lambda *_args: HttpResult(200, "", {})))
    assert lock.read_bytes() == before


def test_lock_file_mode_is_owner_only_after_acquire(tmp_path):
    from scripts.lexicon.runner.fetch_ulif_homonyms import RunnerLock

    old_umask = os.umask(0o022)
    try:
        held = RunnerLock(tmp_path / "state", break_stale=False, scanner=lambda: False)
        held.acquire()
        try:
            mode = (tmp_path / "state" / "runner.lock").stat().st_mode & 0o777
            assert mode == 0o600, f"expected 0o600, got {oct(mode)}"
        finally:
            held.release()
    finally:
        os.umask(old_umask)


def test_prepare_database_leaves_preexisting_db_and_parent_modes(tmp_path, capsys):
    from scripts.lexicon.runner.fetch_ulif_homonyms import prepare_database

    # umask 0o027 → mkdir 0o750 / file 0o640 (group-accessible, no world bits).
    # No chmod: CodeQL py/overly-permissive-file flags world *and* group r/w on chmod/open.
    old_umask = os.umask(0o027)
    try:
        parent = tmp_path / "data"
        parent.mkdir()
        db_path = parent / "sources.db"
        db_path.write_bytes(b"")
        parent_before = parent.stat().st_mode & 0o777
        db_before = db_path.stat().st_mode & 0o777
        assert parent_before == 0o750, f"expected 0o750, got {oct(parent_before)}"
        assert db_before == 0o640, f"expected 0o640, got {oct(db_before)}"
        assert parent_before & 0o077
        assert db_before & 0o077

        conn = prepare_database(db_path)
        try:
            assert parent.stat().st_mode & 0o777 == parent_before
            assert db_path.stat().st_mode & 0o777 == db_before
        finally:
            conn.close()
        assert "warning" not in capsys.readouterr().err
    finally:
        os.umask(old_umask)


def test_prepare_database_creates_new_db_owner_only(tmp_path):
    from scripts.lexicon.runner.fetch_ulif_homonyms import prepare_database

    old_umask = os.umask(0o022)
    try:
        db_path = tmp_path / "fresh" / "cache.db"
        conn = prepare_database(db_path)
        try:
            assert db_path.stat().st_mode & 0o777 == 0o600
            assert db_path.parent.stat().st_mode & 0o777 == 0o700
        finally:
            conn.close()
    finally:
        os.umask(old_umask)


def test_ensure_private_dir_warns_on_permissive_existing_keeps_mode(tmp_path, capsys):
    from scripts.lexicon.runner.fetch_ulif_homonyms import _ensure_private_dir

    # umask 0o027 → mkdir yields 0o750 (group r-x). Avoid chmod: CodeQL flags group r/w too.
    old_umask = os.umask(0o027)
    try:
        existing = tmp_path / "state"
        existing.mkdir()
        before = existing.stat().st_mode & 0o777
        assert before == 0o750, f"expected 0o750, got {oct(before)}"
        assert before & 0o077
        _ensure_private_dir(existing)
        assert existing.stat().st_mode & 0o777 == before
        err = capsys.readouterr().err
        assert "warning" in err
        assert str(existing) in err
        assert oct(before) in err

        fresh = tmp_path / "new-state"
        _ensure_private_dir(fresh)
        assert fresh.stat().st_mode & 0o777 == 0o700
    finally:
        os.umask(old_umask)


def test_stale_lock_is_reported_and_kept_until_break_stale_lock(tmp_path, capsys):
    state = tmp_path / "state"
    state.mkdir()
    lock = state / "runner.lock"
    dead = 2**22
    while True:
        try:
            os.kill(dead, 0)
        except ProcessLookupError:
            break
        except PermissionError:
            dead += 1
            continue
        dead += 1
    original = f"{dead}\n2026-09-21T00:00:00+00:00\n"
    lock.write_text(original, encoding="utf-8")
    with pytest.raises(SystemExit, match="stale lock"):
        _run(tmp_path, ["замок"], _Scripted(lambda *_args: HttpResult(200, "", {})))
    assert "stale lock" in capsys.readouterr().err
    assert lock.read_text(encoding="utf-8") == original
    assert _run(tmp_path, [], _Scripted(lambda *_args: HttpResult(200, "", {})), break_stale_lock=True) == EXIT_OK
    assert not lock.exists()


def test_legacy_crawler_and_uncertain_scan_refuse_to_start(tmp_path):
    with pytest.raises(SystemExit, match=r"dump_ulif\.py"):
        _run(tmp_path, [], _Scripted(lambda *_args: HttpResult(200, "", {})), scanner=lambda: True)
    with pytest.raises(SystemExit, match="could not scan"):
        _run(tmp_path, [], _Scripted(lambda *_args: HttpResult(200, "", {})), scanner=lambda: None)


def test_ledger_state_transitions_and_three_retry_scheduled_stop(tmp_path):
    page = _register(["інше"], "seed", paging=False)
    sleeps: list[float] = []

    def handler(method: str, data: dict[str, str] | None) -> HttpResult:
        spelling = "" if data is None else data.get("ctl00$ContentPlaceHolder1$tsearch", "")
        if spelling in {"блок", "ще", "далі"}:
            return HttpResult(429, "slow", {"Retry-After": "7"})
        return HttpResult(200, page, {})

    spellings = ["нема", "блок", "ще", "далі"]
    code = _run(tmp_path, spellings, _Scripted(handler), sleep=sleeps.append)
    assert code == EXIT_RETRY_STORM
    assert any(value >= 7 for value in sleeps)
    ledger = _ledger(tmp_path)
    try:
        states = {row["spelling"]: row["state"] for row in ledger.conn.execute("SELECT spelling, state FROM spellings")}
        text = status_text(ledger, delay_seconds=1.0)
    finally:
        ledger.close()
    assert states["нема"] == "absent_from_ulif"
    assert states["блок"] == "retry_scheduled"
    assert states["ще"] == "retry_scheduled"
    assert states["далі"] == "retry_scheduled"
    assert "retry_scheduled=3" in text


def test_five_attempts_then_retry_scheduled_and_third_stops(tmp_path):
    calls = {"n": 0}

    def handler(method: str, data: dict[str, str] | None) -> HttpResult:
        calls["n"] += 1
        return HttpResult(503, "down", {})

    code = _run(tmp_path, ["а", "б", "в", "г"], _Scripted(handler))
    assert code == EXIT_RETRY_STORM
    assert calls["n"] == 15
    ledger = _ledger(tmp_path)
    try:
        states = [row["state"] for row in ledger.conn.execute("SELECT state FROM spellings ORDER BY spelling")]
    finally:
        ledger.close()
    assert states == ["retry_scheduled", "retry_scheduled", "retry_scheduled", "pending"]


def test_session_reseed_then_absent(tmp_path):
    page = _register(["інше"], "seed", paging=False)
    gets = {"n": 0}

    def handler(method: str, data: dict[str, str] | None) -> HttpResult:
        if method == "GET":
            gets["n"] += 1
            if gets["n"] < 3:
                return HttpResult(500, "boom", {})
        return HttpResult(200, page, {})

    assert _run(tmp_path, ["нема"], _Scripted(handler)) == EXIT_OK
    ledger = _ledger(tmp_path)
    try:
        state = ledger.conn.execute("SELECT state FROM spellings").fetchone()["state"]
    finally:
        ledger.close()
    assert gets["n"] == 3
    assert state == "absent_from_ulif"


def test_unmigrated_database_stops_before_requests(tmp_path):
    from tests.test_ulif_dictua import _sqlite_master_bytes, _write_old_ulif_db

    db_path = _write_old_ulif_db(tmp_path / "old.db")
    before = _sqlite_master_bytes(db_path)
    calls = {"n": 0}

    def handler(method: str, data: dict[str, str] | None) -> HttpResult:
        calls["n"] += 1
        return HttpResult(200, "", {})

    code = run_fetch(
        spellings=["замок"],
        state_dir=tmp_path / "state",
        db_path=db_path,
        transport=handler,
        sleep=_noop_sleep,
        scanner=lambda: False,
    )
    assert code == EXIT_USAGE
    assert calls["n"] == 0
    assert _sqlite_master_bytes(db_path) == before


def test_delay_below_one_second_is_rejected():
    with pytest.raises(SystemExit):
        main(["run", "--spellings-file", "x", "--state-dir", "y", "--db", "z", "--delay", "0.5"])


def test_equal_content_hash_marks_checked_without_rewriting(tmp_path):
    page = _register(["ду́же"], "seed", paging=False)
    entry = _html("duzhe.html")

    def handler(method: str, data: dict[str, str] | None) -> HttpResult:
        if data and data.get("__EVENTARGUMENT"):
            return HttpResult(200, entry, {})
        return HttpResult(200, page, {})

    assert _run(tmp_path, ["дуже"], _Scripted(handler)) == EXIT_OK
    cache = sqlite3.connect(tmp_path / "cache.db")
    ledger = _ledger(tmp_path)
    try:
        parse_stored(ledger, cache)
        digest = cache.execute("SELECT content_sha256 FROM ulif_dictua_entries").fetchone()[0]
        cache.execute(
            "UPDATE ulif_dictua_entries SET canonical_headword = 'KEEP', homonym_checked = 0 WHERE normalized_query = 'дуже'"
        )
        cache.commit()
        assert parse_stored(ledger, cache) == 0
        row = cache.execute("SELECT canonical_headword, homonym_checked FROM ulif_dictua_entries").fetchone()
        assert row == ("KEEP", 1)
        cache.execute("UPDATE ulif_dictua_entries SET content_sha256 = 'different', homonym_checked = 0")
        cache.commit()
        assert parse_stored(ledger, cache) == 1
        rewritten = cache.execute("SELECT canonical_headword, homonym_checked FROM ulif_dictua_entries").fetchone()
        assert rewritten[1] == 1
        assert rewritten[0] != "KEEP"
        assert ledger.meta("differing_content_hashes") == "1"
    finally:
        cache.close()
        ledger.close()


def test_build_a1a2_lemmatises_and_skips_stored(tmp_path):
    sources = tmp_path / "sources.db"
    vesum = tmp_path / "vesum.db"
    src = sqlite3.connect(sources)
    src.execute("CREATE TABLE puls_cefr (word TEXT, level TEXT)")
    src.executemany(
        "INSERT INTO puls_cefr VALUES (?, ?)",
        [("яблуко", "A1"), ("яблука", "A2"), ("будинок", "B1"), ("вже", "A1"), ("Як справи?", "A1")],
    )
    src.commit()
    src.close()
    ves = sqlite3.connect(vesum)
    ves.execute("CREATE TABLE forms_all (word_form TEXT, lemma TEXT)")
    ves.executemany(
        "INSERT INTO forms_all VALUES (?, ?)",
        [("яблуко", "яблуко"), ("яблука", "яблуко"), ("вже", "вже")],
    )
    ves.commit()
    ves.close()
    assert build_a1_a2_spellings(sources_db=sources, vesum_db=vesum, stored={"вже"}) == ["яблуко"]


def test_homonym_runner_cli_subprocess_clean_env(tmp_path):
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.lexicon.runner.fetch_ulif_homonyms",
            "status",
            "--state-dir",
            str(tmp_path),
        ],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert proc.returncode == 0, proc.stderr
    assert "spellings_total=0" in proc.stdout
    assert "register_size=unknown" in proc.stdout


def test_build_suspects_cli_delegates(tmp_path, monkeypatch):
    from scripts.lexicon.tools import report_ulif_homonym_suspects

    def fake_build(dump, vesum, out):
        out.write_text("замок\ttrie_stress\n", encoding="utf-8")
        return 1

    monkeypatch.setattr(report_ulif_homonym_suspects, "build_report", fake_build)
    out = tmp_path / "suspects.txt"
    code = main(
        ["build-suspects", "--dump", str(tmp_path / "dump"), "--vesum", str(tmp_path / "vesum"), "--out", str(out)]
    )
    assert code == EXIT_OK
    assert out.read_text(encoding="utf-8").startswith("замок")


def test_same_stress_homonyms_keep_two_indexes_and_glosses(tmp_path):
    """Ішим: two register rows, identical stressed text, distinct Select$N.

    Headword and sense glosses are copied from the real fixture HTML. The live
    one-spelling run for this word reported ``entries_stored=2``.
    """
    from bs4 import BeautifulSoup

    def _from_fixture(name: str) -> tuple[str, str]:
        article = BeautifulSoup(_html(name), "html.parser").find(id="ContentPlaceHolder1_article")
        assert article is not None
        word = article.select_one(".word_style")
        comment = article.select_one(".comment_style")
        assert word is not None and comment is not None
        return word.get_text(), comment.get_text(" ", strip=True)

    word1, gloss1 = _from_fixture("ishym-entry-1.html")
    word2, gloss2 = _from_fixture("ishym-entry-2.html")
    assert word1.strip().endswith("1")
    assert word2.strip().endswith("2")
    assert gloss1 == "(місто в Росії)"
    assert gloss2 == "(річка в Росії та Казахстані)"

    entry = {
        "Select$4": _html("ishym-entry-1.html"),
        "Select$5": _html("ishym-entry-2.html"),
    }

    def handler(method: str, data: dict[str, str] | None) -> HttpResult:
        if method == "GET":
            return HttpResult(200, _html("ishym-seed.html"), {})
        assert data is not None
        if any(key.endswith("search.x") for key in data):
            return HttpResult(200, _html("ishym-tsearch.html"), {})
        argument = data.get("__EVENTARGUMENT", "")
        if argument in entry:
            return HttpResult(200, entry[argument], {})
        # paradigm tab reuses the entry body (as on the wire for entry-1)
        return HttpResult(200, entry.get(data.get("__EVENTARGUMENT", ""), next(iter(entry.values()))), {})

    scripted = _Scripted(handler)
    assert _run(tmp_path, ["ішим"], scripted) == EXIT_OK
    select_args = [
        data.get("__EVENTARGUMENT")
        for _method, data in scripted.calls
        if data and data.get("__EVENTARGUMENT", "").startswith("Select$")
    ]
    assert select_args == ["Select$4", "Select$5"]
    ledger = _ledger(tmp_path)
    try:
        row = ledger.conn.execute("SELECT state, entry_count FROM spellings WHERE spelling = 'ішим'").fetchone()
        assert (row["state"], row["entry_count"]) == ("stored", 2)
        cache = sqlite3.connect(tmp_path / "cache.db")
        cache.row_factory = sqlite3.Row
        differing = parse_stored(ledger, cache)
        rows = cache.execute(
            """
            SELECT homonym_index, canonical_headword, sense_gloss, homonym_checked
            FROM ulif_dictua_entries WHERE normalized_query = 'ішим'
            ORDER BY homonym_index
            """
        ).fetchall()
        duplicate = ledger.conn.execute("SELECT duplicate_content FROM spellings WHERE spelling = 'ішим'").fetchone()[
            "duplicate_content"
        ]
        printed_meta = ledger.meta("printed_homonym_numbers:ішим")
        cache.close()
    finally:
        ledger.close()
    assert differing == 0
    assert duplicate == 0
    assert [(r["homonym_index"], r["canonical_headword"], r["sense_gloss"], r["homonym_checked"]) for r in rows] == [
        (1, "Іши́м", gloss1, 1),
        (2, "Іши́м", gloss2, 1),
    ]
    assert '"printed": ["1", "2"]' in printed_meta
    assert '"register": [1, 2]' in printed_meta


def test_same_stress_homonym_indexes_stable_across_rerun(tmp_path):
    entry = {
        "Select$4": _html("ishym-entry-1.html"),
        "Select$5": _html("ishym-entry-2.html"),
    }

    def handler(method: str, data: dict[str, str] | None) -> HttpResult:
        if method == "GET":
            return HttpResult(200, _html("ishym-seed.html"), {})
        assert data is not None
        if any(key.endswith("search.x") for key in data):
            return HttpResult(200, _html("ishym-tsearch.html"), {})
        argument = data.get("__EVENTARGUMENT", "")
        if argument in entry:
            return HttpResult(200, entry[argument], {})
        return HttpResult(200, next(iter(entry.values())), {})

    assert _run(tmp_path, ["ішим"], _Scripted(handler)) == EXIT_OK
    ledger = _ledger(tmp_path)
    try:
        cache = sqlite3.connect(tmp_path / "cache.db")
        cache.row_factory = sqlite3.Row
        parse_stored(ledger, cache)
        first = {
            str(row["content_sha256"]): int(row["homonym_index"])
            for row in cache.execute(
                "SELECT content_sha256, homonym_index FROM ulif_dictua_entries WHERE normalized_query = 'ішим'"
            )
        }
        cache.close()
    finally:
        ledger.close()

    assert _run(tmp_path, ["ішим"], _Scripted(handler), refetch=True) == EXIT_OK
    ledger = _ledger(tmp_path)
    try:
        cache = sqlite3.connect(tmp_path / "cache.db")
        cache.row_factory = sqlite3.Row
        parse_stored(ledger, cache)
        second = {
            str(row["content_sha256"]): int(row["homonym_index"])
            for row in cache.execute(
                "SELECT content_sha256, homonym_index FROM ulif_dictua_entries WHERE normalized_query = 'ішим'"
            )
        }
        cache.close()
    finally:
        ledger.close()
    assert first == second
    assert set(first.values()) == {1, 2}


def test_printed_number_mismatch_refuses_group_write(tmp_path, monkeypatch):
    """Fail closed when every entry prints a number that disagrees with register order.

    The mismatch is built in test code by altering the parsed value — fixtures
    stay real captures.
    """
    import scripts.lexicon.runner.fetch_ulif_homonyms as runner

    entry = {
        "Select$4": _html("ishym-entry-1.html"),
        "Select$5": _html("ishym-entry-2.html"),
    }

    def handler(method: str, data: dict[str, str] | None) -> HttpResult:
        if method == "GET":
            return HttpResult(200, _html("ishym-seed.html"), {})
        assert data is not None
        if any(key.endswith("search.x") for key in data):
            return HttpResult(200, _html("ishym-tsearch.html"), {})
        argument = data.get("__EVENTARGUMENT", "")
        if argument in entry:
            return HttpResult(200, entry[argument], {})
        return HttpResult(200, next(iter(entry.values())), {})

    assert _run(tmp_path, ["ішим"], _Scripted(handler)) == EXIT_OK

    real_parse = runner.parse_ulif_entry

    def flipped(html: str, *, homonym_index: int, register_position: str = ""):
        parsed = real_parse(html, homonym_index=homonym_index, register_position=register_position)
        parsed["printed_homonym_number"] = "2" if homonym_index == 1 else "1"
        return parsed

    monkeypatch.setattr(runner, "parse_ulif_entry", flipped)

    ledger = _ledger(tmp_path)
    cache = sqlite3.connect(tmp_path / "cache.db")
    cache.row_factory = sqlite3.Row
    try:
        differing = parse_stored(ledger, cache)
        row = ledger.conn.execute("SELECT state, error FROM spellings WHERE spelling = 'ішим'").fetchone()
        entries = list(cache.execute("SELECT homonym_index FROM ulif_dictua_entries WHERE normalized_query = 'ішим'"))
        meta = ledger.meta("printed_homonym_numbers:ішим")
    finally:
        cache.close()
        ledger.close()

    assert differing == 0
    assert row["state"] == "error"
    assert row["error"] == "printed_number_mismatch register=[1, 2] printed=[2, 1]"
    assert entries == []
    assert '"printed": ["2", "1"]' in meta
    assert '"register": [1, 2]' in meta


def test_overlapping_register_identity_opened_once(tmp_path):
    """Duplicate (page_delta, select) collapses; physical row opened once."""
    duplicated = _dedupe_register_rows(
        [
            {
                "row_index": 24,
                "select": "Select$24",
                "stressed": "Кра́й",
                "unstressed": "Край",
                "page_delta": 0,
            },
            {
                "row_index": 24,
                "select": "Select$24",
                "stressed": "Кра́й",
                "unstressed": "Край",
                "page_delta": 0,
            },
            {
                "row_index": 0,
                "select": "Select$0",
                "stressed": "край",
                "unstressed": "край",
                "page_delta": 1,
            },
        ]
    )
    assert [(row["page_delta"], row["select"]) for row in duplicated] == [
        (0, "Select$24"),
        (1, "Select$0"),
    ]

    fillers = [f"слово{index}" for index in range(24)]
    # Current page ends with Кра́й; a second link repeats Select$24 (overlapping identity).
    rows = []
    for index, word in enumerate([*fillers, "Кра́й"]):
        rows.append(
            '<tr><td><a href="javascript:__doPostBack(&#39;ctl00$ContentPlaceHolder1$dgv&#39;,'
            f'&#39;Select${index}&#39;)">{word}</a></td></tr>'
        )
    rows.append(
        '<tr><td><a href="javascript:__doPostBack(&#39;ctl00$ContentPlaceHolder1$dgv&#39;,'
        '&#39;Select$24&#39;)">Кра́й</a></td></tr>'
    )
    page = (
        '<input type="hidden" name="__VIEWSTATE" value="page-a" />'
        '<input type="hidden" name="__VIEWSTATEGENERATOR" value="GEN" />'
        '<input type="hidden" name="__EVENTVALIDATION" value="EV-page-a" />'
        '<input type="image" name="ctl00$ContentPlaceHolder1$backpage" />'
        '<input type="image" name="ctl00$ContentPlaceHolder1$nextpage" />'
        f'<table id="ContentPlaceHolder1_dgv">{"".join(rows)}</table>'
        '<span id="ContentPlaceHolder1_rlength">Реєстрових слів - 262812</span>'
    )
    entry = _entry("Кра́й", "(одне)", "entry-a", '<input type="image" name="ctl00$ContentPlaceHolder1$par" />')
    opens: list[str] = []

    def handler(method: str, data: dict[str, str] | None) -> HttpResult:
        if method == "GET":
            return HttpResult(200, page, {})
        assert data is not None
        if any(key.endswith("search.x") for key in data):
            return HttpResult(200, page, {})
        if any(key.endswith("nextpage.x") for key in data):
            return HttpResult(200, _register(["інше"], "page-b", paging=False), {})
        argument = data.get("__EVENTARGUMENT", "")
        if argument.startswith("Select$"):
            opens.append(argument)
            return HttpResult(200, entry, {})
        return HttpResult(200, entry, {})

    assert _run(tmp_path, ["край"], _Scripted(handler)) == EXIT_OK
    assert opens == ["Select$24"]


def test_write_group_failure_rolls_back_leaving_legacy_unchecked(tmp_path):
    from scripts.lexicon.runner.fetch_ulif_homonyms import ULIF_PARSER_VERSION, prepare_database
    from scripts.wiki import sources_db

    db_path = tmp_path / "cache.db"
    cache = prepare_database(db_path)
    sources_db.store_ulif_dictua_entry(
        word="замок",
        canonical_headword="замок",
        sections={},
        raw_responses={},
        retrieved_at="2026-01-01T00:00:00+00:00",
        parser_version=ULIF_PARSER_VERSION,
        status="ok",
        homonym_index=1,
        sense_gloss="(legacy)",
        register_position="0:0",
        homonym_checked=0,
        content_sha256="legacy-hash",
        db_path=db_path,
        conn=cache,
    )
    cache.commit()
    ledger = SpellingLedger(tmp_path / "state" / "ledger.sqlite")
    ledger.ensure("замок")
    assert ledger.state_of("замок") == "pending"

    calls = {"n": 0}

    def store(**kwargs):
        calls["n"] += 1
        if calls["n"] > 1:
            raise RuntimeError("injected failure after first entry")
        return sources_db.store_ulif_dictua_entry(**kwargs)

    parsed_rows = [
        {
            "canonical_headword": f"замок-{index}",
            "grammatical_label": "іменник",
            "sense_gloss": f"(sense {index})",
            "register_position": f"0:{index}",
            "homonym_index": index,
            "content_sha256": f"hash-{index}",
        }
        for index in (1, 2, 3)
    ]
    with pytest.raises(RuntimeError, match="injected failure"):
        _write_group(
            cache,
            "замок",
            parsed_rows,
            [{}, {}, {}],
            [{}, {}, {}],
            store,
        )
    after = [
        (int(row[0]), str(row[1]), int(row[2]), str(row[3]))
        for row in cache.execute(
            "SELECT homonym_index, sense_gloss, homonym_checked, content_sha256 FROM ulif_dictua_entries"
        )
    ]
    state = ledger.state_of("замок")
    cache.close()
    ledger.close()
    assert after == [(1, "(legacy)", 0, "legacy-hash")]
    assert state != "stored"


def test_transport_exception_retries_then_succeeds(tmp_path):
    import requests

    page = _register(["інше"], "seed", paging=False)
    hits = {"n": 0}

    def handler(method: str, data: dict[str, str] | None) -> HttpResult:
        hits["n"] += 1
        if hits["n"] <= 2:
            raise requests.ConnectionError("reset")
        return HttpResult(200, page, {})

    sleeps: list[float] = []
    assert _run(tmp_path, ["нема"], _Scripted(handler), sleep=sleeps.append) == EXIT_OK
    # Two ConnectionError on the seed GET, then GET + tsearch POST succeed.
    assert hits["n"] == 4
    assert sleeps  # back-off and/or inter-request delay
    ledger = _ledger(tmp_path)
    try:
        assert ledger.state_of("нема") == "absent_from_ulif"
    finally:
        ledger.close()


def test_transport_exception_exhausts_to_retry_scheduled(tmp_path):
    import requests

    def handler(method: str, data: dict[str, str] | None) -> HttpResult:
        raise requests.Timeout("slow")

    code = _run(tmp_path, ["а", "б", "в", "г"], _Scripted(handler))
    assert code == EXIT_RETRY_STORM
    ledger = _ledger(tmp_path)
    try:
        states = {
            row["spelling"]: (row["state"], row["error"])
            for row in ledger.conn.execute("SELECT spelling, state, error FROM spellings")
        }
    finally:
        ledger.close()
    assert states["а"] == ("retry_scheduled", "transport_error")
    assert states["б"] == ("retry_scheduled", "transport_error")
    assert states["в"] == ("retry_scheduled", "transport_error")
    assert states["г"] == ("pending", "")


def test_start_banner_reports_counts_and_case_duplicates(tmp_path, capsys):
    page = _register(["інше"], "seed", paging=False)

    def handler(method: str, data: dict[str, str] | None) -> HttpResult:
        return HttpResult(200, page, {})

    code = _run(tmp_path, ["Замок", "замок", "будинок"], _Scripted(handler))
    assert code == EXIT_OK
    captured = capsys.readouterr()
    err = captured.err
    assert "=== ULIF Homonym Fetch Runner ===" in err
    assert "Spellings in file:             3" in err
    assert "Distinct after normalisation:  2 (1 duplicates)" in err
    assert "Already finished (skipped):    0" in err
    assert "To do in this run:             2" in err
    assert "Delay between requests:        1.0s" in err
    assert f"State directory:               {tmp_path / 'state'}" in err
    assert f"Database path:                 {tmp_path / 'cache.db'}" in err
    assert "Register size:                 unknown" in err
    assert "=================================" in err


def test_progress_lines_for_all_four_outcomes(tmp_path, capsys):
    page_zamok = _register(["за́мок"], "seed", paging=False)
    page_other = _register(["інше"], "seed", paging=False)
    entry_zamok = _entry("за́мок", "(будівля)", "entry_vs", "")

    def handler(method: str, data: dict[str, str] | None) -> HttpResult:
        if method == "GET":
            return HttpResult(200, page_zamok, {})
        assert data is not None
        query = data.get("ctl00$ContentPlaceHolder1$tsearch", "")
        if query == "замок":
            if data.get("__EVENTARGUMENT") == "Select$0":
                return HttpResult(200, entry_zamok, {})
            return HttpResult(200, page_zamok, {})
        if query == "нема":
            return HttpResult(200, page_other, {})
        if query == "помилка":
            return HttpResult(500, "internal server error", {})
        if query == "заборонено":
            return HttpResult(403, "forbidden", {})
        return HttpResult(200, page_other, {})

    code = _run(
        tmp_path,
        ["замок", "нема", "помилка", "заборонено"],
        _Scripted(handler),
    )
    assert code == EXIT_FORBIDDEN
    captured = capsys.readouterr()
    err = captured.err

    assert "stored       entries=1 req=" in err
    assert "absent_from_ulif entries=0 req=" in err
    assert "retry_scheduled entries=0 req=" in err
    assert "error        entries=0 req=" in err
    assert "total_req=" in err
    assert "замок" in err
    assert "нема" in err
    assert "помилка" in err
    assert "заборонено" in err


def test_progress_numbering_continues_across_resume(tmp_path, capsys):
    page = _register(["інше"], "seed", paging=False)

    def handler(method: str, data: dict[str, str] | None) -> HttpResult:
        return HttpResult(200, page, {})

    code1 = _run(tmp_path, ["а", "б"], _Scripted(handler), max_spellings=1)
    assert code1 == EXIT_OK
    err1 = capsys.readouterr().err
    assert "[    1/2      50.0%]" in err1
    assert "Already finished (skipped):    0" in err1
    assert "To do in this run:             1" in err1

    code2 = _run(tmp_path, ["а", "б"], _Scripted(handler))
    assert code2 == EXIT_OK
    err2 = capsys.readouterr().err
    assert "Already finished (skipped):    1" in err2
    assert "To do in this run:             1" in err2
    assert "[    2/2     100.0%]" in err2


def test_eta_question_mark_then_clock_calculation(tmp_path, capsys):
    page = _register(["інше"], "seed", paging=False)
    sim_time = [1000.0]

    def fake_clock() -> float:
        return sim_time[0]

    def fake_sleep(sec: float) -> None:
        sim_time[0] += sec

    def handler(method: str, data: dict[str, str] | None) -> HttpResult:
        sim_time[0] += 10.0
        return HttpResult(200, page, {})

    spellings = ["а", "б", "в", "г", "д", "е"]
    code = _run(
        tmp_path,
        spellings,
        _Scripted(handler),
        clock=fake_clock,
        sleep=fake_sleep,
    )
    assert code == EXIT_OK
    err = capsys.readouterr().err

    lines = [line for line in err.splitlines() if line.startswith("[")]
    assert len(lines) == 6
    assert "eta=?" in lines[0]
    assert "eta=?" in lines[1]
    assert "eta=?" in lines[2]
    assert "eta=?" in lines[3]
    assert "eta=?" not in lines[4]
    assert "eta=" in lines[4]
    assert "eta=0:00:00" in lines[5]


def test_heartbeat_during_long_backoff(tmp_path, capsys):
    page = _register(["інше"], "seed", paging=False)
    sim_time = [1000.0]

    def fake_clock() -> float:
        return sim_time[0]

    def fake_sleep(sec: float) -> None:
        sim_time[0] += sec

    attempts = {"n": 0}

    def handler(method: str, data: dict[str, str] | None) -> HttpResult:
        attempts["n"] += 1
        if attempts["n"] == 1:
            return HttpResult(429, "Too Many Requests", {"Retry-After": "150"})
        return HttpResult(200, page, {})

    code = _run(
        tmp_path,
        ["тест"],
        _Scripted(handler),
        clock=fake_clock,
        sleep=fake_sleep,
    )
    assert code == EXIT_OK
    err = capsys.readouterr().err
    assert "heartbeat: waiting for back-off: 90s remaining (attempt 1)" in err
    assert "heartbeat: waiting for back-off: 30s remaining (attempt 1)" in err


def test_stop_summary_on_keyboard_interrupt(tmp_path, capsys):
    page = _register(["інше"], "seed", paging=False)
    calls = {"n": 0}

    def handler(method: str, data: dict[str, str] | None) -> HttpResult:
        calls["n"] += 1
        if calls["n"] > 2:
            raise KeyboardInterrupt()
        return HttpResult(200, page, {})

    code = _run(
        tmp_path,
        ["перше", "друге"],
        _Scripted(handler),
    )
    assert code == EXIT_INTERRUPTED
    captured = capsys.readouterr()
    err = captured.err

    assert "=== ULIF Fetch Stop Summary ===" in err
    assert "Reason:               interrupted by operator" in err
    assert "Spellings total:      2" in err
    assert "Pending:              1" in err
    assert f"Resume command:       {shlex.quote(sys.executable)}" in err
    assert "===============================" in err

    ledger = _ledger(tmp_path)
    try:
        assert ledger.state_of("перше") == "absent_from_ulif"
        assert ledger.state_of("друге") == "pending"
    finally:
        ledger.close()

    assert not (tmp_path / "state" / "runner.lock").exists()


def test_truthful_requests_made_mid_run_and_no_double_counting(tmp_path):
    page = _register(["інше"], "seed", paging=False)
    mid_requests: list[str] = []

    def handler(method: str, data: dict[str, str] | None) -> HttpResult:
        ledger = _ledger(tmp_path)
        try:
            mid_requests.append(ledger.meta("requests_made", "0") or "0")
        finally:
            ledger.close()
        return HttpResult(200, page, {})

    code = _run(tmp_path, ["перше", "друге"], _Scripted(handler))
    assert code == EXIT_OK
    ledger = _ledger(tmp_path)
    try:
        final_requests = int(ledger.meta("requests_made", "0") or "0")
    finally:
        ledger.close()

    assert mid_requests[0] == "0"
    assert any(int(val) > 0 for val in mid_requests[2:])
    assert final_requests == 4


def test_status_text_empty_ledger_and_lock_states(tmp_path):
    state_dir = tmp_path / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    ledger_path = state_dir / "ledger.sqlite"
    ledger = SpellingLedger(ledger_path)
    try:
        text = status_text(ledger, delay_seconds=1.0, state_dir=state_dir)
        assert "complete=not_started" in text
        assert "runner=not_running" in text
        assert "last_update=none" in text
        assert "seconds_since_last_update=unknown" in text
        assert "estimated_time_remaining_seconds=0" in text

        lock_path = state_dir / "runner.lock"
        pid = os.getpid()
        iso = "2026-09-21T12:00:00+00:00"
        lock_path.write_text(f"{pid}\n{iso}\n", encoding="utf-8")
        orig_bytes = lock_path.read_bytes()
        orig_stat = lock_path.stat().st_mode

        text_running = status_text(ledger, delay_seconds=1.0, state_dir=state_dir)
        assert f"runner=running pid={pid} since={iso}" in text_running
        assert lock_path.read_bytes() == orig_bytes
        assert lock_path.stat().st_mode == orig_stat

        lock_path.write_text(f"99999999\n{iso}\n", encoding="utf-8")
        text_stale = status_text(ledger, delay_seconds=1.0, state_dir=state_dir)
        assert "runner=stale_lock pid=99999999" in text_stale
        assert lock_path.read_text(encoding="utf-8") == f"99999999\n{iso}\n"
    finally:
        ledger.close()


def test_quiet_flag_suppresses_progress_lines(tmp_path, capsys):
    page = _register(["інше"], "seed", paging=False)

    def handler(method: str, data: dict[str, str] | None) -> HttpResult:
        return HttpResult(200, page, {})

    code = _run(tmp_path, ["тихо"], _Scripted(handler), quiet=True)
    assert code == EXIT_OK
    err = capsys.readouterr().err
    assert "=== ULIF Homonym Fetch Runner ===" in err
    assert "=== ULIF Fetch Stop Summary ===" in err
    assert "[    1/1" not in err


def test_parse_stored_progress_logging(tmp_path, capsys):
    page = _register(["ду́же"], "seed", paging=False)
    entry = _html("duzhe.html")

    def handler(method: str, data: dict[str, str] | None) -> HttpResult:
        if data and data.get("__EVENTARGUMENT"):
            return HttpResult(200, entry, {})
        return HttpResult(200, page, {})

    assert _run(tmp_path, ["дуже"], _Scripted(handler)) == EXIT_OK
    cache = sqlite3.connect(tmp_path / "cache.db")
    ledger = _ledger(tmp_path)
    try:
        capsys.readouterr()
        differing = parse_stored(ledger, cache)
        assert differing == 0
        err = capsys.readouterr().err
        assert (
            "parse complete: 1 spellings parsed, 1 entries written, 0 groups differed, 0 printed_number_mismatch errors"
        ) in err
    finally:
        cache.close()
        ledger.close()


def test_cli_help_options(capsys):
    for subcmd in ["run", "parse", "status", "build-suspects", "build-a1a2"]:
        with pytest.raises(SystemExit) as exc:
            main([subcmd, "--help"])
        assert exc.value.code == 0
        out = capsys.readouterr().out
        assert "Examples:" in out
        assert "Outputs:" in out
        assert "Exit codes:" in out
        assert "Related:" in out


def test_start_banner_reports_counts_and_case_duplicates_via_cli(tmp_path, capsys, monkeypatch):
    page = _register(["інше"], "seed", paging=False)

    def handler(m: str, d: dict[str, str] | None) -> HttpResult:
        return HttpResult(200, page, {})

    monkeypatch.setattr("scripts.lexicon.runner.fetch_ulif_homonyms._requests_transport", lambda ua: handler)

    spellings_file = _write_spellings(tmp_path / "spellings.txt", ["Замок", "замок", "будинок"])
    code = main(
        [
            "run",
            "--spellings-file",
            str(spellings_file),
            "--state-dir",
            str(tmp_path / "state"),
            "--db",
            str(tmp_path / "cache.db"),
            "--delay",
            "1.0",
        ]
    )
    assert code == EXIT_OK
    err = capsys.readouterr().err
    assert "Spellings in file:             3" in err
    assert "Distinct after normalisation:  2 (1 duplicates)" in err
    assert "To do in this run:             2" in err


def test_resume_command_faithful_options_and_quoting(tmp_path, capsys, monkeypatch):
    page = _register(["інше"], "seed", paging=False)
    calls = {"n": 0}

    def handler(method: str, data: dict[str, str] | None) -> HttpResult:
        calls["n"] += 1
        if calls["n"] > 1:
            raise KeyboardInterrupt()
        return HttpResult(200, page, {})

    monkeypatch.setattr("scripts.lexicon.runner.fetch_ulif_homonyms._requests_transport", lambda ua: handler)
    spellings_file = _write_spellings(tmp_path / "my spellings.txt", ["перше", "друге"])
    state_dir = tmp_path / "state with space"
    db_file = tmp_path / "cache with space.db"

    code = main(
        [
            "run",
            "--spellings-file",
            str(spellings_file),
            "--state-dir",
            str(state_dir),
            "--db",
            str(db_file),
            "--delay",
            "1.25",
            "--max-spellings",
            "5",
            "--quiet",
        ]
    )
    assert code == EXIT_INTERRUPTED
    err = capsys.readouterr().err
    assert "=== ULIF Fetch Stop Summary ===" in err
    assert "Reason:               interrupted by operator" in err
    assert shlex.quote(str(spellings_file)) in err
    assert shlex.quote(str(state_dir)) in err
    assert shlex.quote(str(db_file)) in err
    assert "--delay 1.25" in err
    assert "--max-spellings 5" in err
    assert "--quiet" in err


def test_discovered_register_size_emitted_to_stderr(tmp_path, capsys):
    page = _register(["інше"], "seed", paging=False)

    def handler(m: str, d: dict[str, str] | None) -> HttpResult:
        return HttpResult(200, page, {})

    code = _run(tmp_path, ["тест"], _Scripted(handler))
    assert code == EXIT_OK
    err = capsys.readouterr().err
    assert "discovered register size: 262812" in err


def test_operator_interrupt_during_setup_returns_exit_interrupted(tmp_path, capsys, monkeypatch):
    def fake_prepare(db_path):
        raise KeyboardInterrupt()

    monkeypatch.setattr("scripts.lexicon.runner.fetch_ulif_homonyms.prepare_database", fake_prepare)
    code = _run(tmp_path, ["тест"], lambda m, d: HttpResult(200, "", {}))
    assert code == EXIT_INTERRUPTED
    err = capsys.readouterr().err
    assert "Reason:               interrupted by operator" in err


def test_operator_interrupt_during_lock_acquire_cleans_up_and_returns_exit_interrupted(tmp_path, capsys, monkeypatch):
    lock_file = tmp_path / "state" / "runner.lock"

    def fake_fdopen(fd, *args, **kwargs):
        os.close(fd)
        raise KeyboardInterrupt()

    monkeypatch.setattr(os, "fdopen", fake_fdopen)
    code = _run(tmp_path, ["тест"], lambda m, d: HttpResult(200, "", {}))
    assert code == EXIT_INTERRUPTED
    err = capsys.readouterr().err
    assert "Reason:               interrupted by operator" in err
    assert not lock_file.exists()


def test_operator_interrupt_during_final_accounting_prints_summary_and_returns_exit_interrupted(
    tmp_path, capsys, monkeypatch
):
    page = _register(["інше"], "seed", paging=False)
    orig_set_requests = SpellingLedger.set_requests_made
    calls = [0]

    def flaky_set_requests(self, count):
        calls[0] += 1
        # Call 1: mid-run after spelling fetch succeeds
        # Call 2: final accounting -> raise KeyboardInterrupt
        if calls[0] >= 2:
            raise KeyboardInterrupt()
        orig_set_requests(self, count)

    monkeypatch.setattr(SpellingLedger, "set_requests_made", flaky_set_requests)
    code = _run(tmp_path, ["тест"], lambda m, d: HttpResult(200, page, {}))
    assert code == EXIT_INTERRUPTED
    err = capsys.readouterr().err
    assert "Reason:               interrupted by operator" in err
    assert "Resume command:" in err
    assert not (tmp_path / "state" / "runner.lock").exists()


def test_requests_made_idempotent_no_double_counting_across_interruption(tmp_path):
    page = _register(["інше"], "seed", paging=False)
    handler = _Scripted(lambda m, d: HttpResult(200, page, {}))

    # Run 1 spelling and interrupt during the second spelling
    orig_fetch = HomonymFetcher.fetch
    fetch_count = [0]

    def interrupted_fetch(self, spelling):
        fetch_count[0] += 1
        if fetch_count[0] > 1:
            raise KeyboardInterrupt()
        return orig_fetch(self, spelling)

    code = run_fetch(
        spellings=["перше", "друге"],
        state_dir=tmp_path / "state",
        db_path=tmp_path / "cache.db",
        transport=handler,
        sleep=_noop_sleep,
        scanner=lambda: False,
    )
    # The first run without mock runs both to completion (2 spellings * 2 requests = 4)
    assert code == EXIT_OK
    ledger = _ledger(tmp_path)
    try:
        assert int(ledger.meta("requests_made", "0") or "0") == 4
    finally:
        ledger.close()

    # Now simulate a resumed run where 1 spelling is fetched, then interrupted
    fetch_count[0] = 0
    from unittest.mock import patch

    with patch.object(HomonymFetcher, "fetch", interrupted_fetch):
        code2 = run_fetch(
            spellings=["перше", "третє", "четверте"],
            state_dir=tmp_path / "state",
            db_path=tmp_path / "cache.db",
            transport=handler,
            sleep=_noop_sleep,
            scanner=lambda: False,
        )
    assert code2 == EXIT_INTERRUPTED

    # "перше" was already stored (skipped). "третє" made 2 requests and was stored.
    # "четверте" raised KeyboardInterrupt before any requests.
    # Total requests across all runs should be exactly 4 (from run 1) + 2 (from run 2) = 6.
    ledger = _ledger(tmp_path)
    try:
        assert int(ledger.meta("requests_made", "0") or "0") == 6
    finally:
        ledger.close()
