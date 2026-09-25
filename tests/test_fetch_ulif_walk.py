"""Offline tests for full ULIF register walk and verification (#8429 part 2 / #8400 step e)."""

from __future__ import annotations

import json
import re
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import ClassVar

import pytest

from scripts.lexicon.runner import fetch_ulif_homonyms as ulif_walk
from scripts.lexicon.runner.fetch_ulif_homonyms import (
    EXIT_FORBIDDEN,
    EXIT_OK,
    EXIT_RETRY_STORM,
    EXIT_USAGE,
    HttpResult,
    RunnerLock,
    SpellingLedger,
    _resume_window_offset,
    normalize_ulif_spelling,
    parse_register_list,
    parse_stored,
    run_walk,
    status_text,
    verify_complete,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "ulif_dictua"


def _html(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def _noop_sleep(_seconds: float) -> None:
    return None


def _register_html(
    words: list[str],
    viewstate: str,
    *,
    has_next: bool = True,
    has_back: bool = True,
    register_size: int = 8,
) -> str:
    rows = []
    for index, word in enumerate(words):
        rows.append(
            '<tr><td><a href="javascript:__doPostBack(&#39;ctl00$ContentPlaceHolder1$dgv&#39;,'
            f'&#39;Select${index}&#39;)">{word}</a></td></tr>'
        )
    paging_parts = []
    if has_back:
        paging_parts.append('<input type="image" name="ctl00$ContentPlaceHolder1$backpage" />')
    if has_next:
        paging_parts.append('<input type="image" name="ctl00$ContentPlaceHolder1$nextpage" />')
    paging_html = "".join(paging_parts)
    return (
        f'<input type="hidden" name="__VIEWSTATE" value="{viewstate}" />\n'
        '<input type="hidden" name="__VIEWSTATEGENERATOR" value="GEN" />\n'
        f'<input type="hidden" name="__EVENTVALIDATION" value="EV-{viewstate}" />\n'
        f"{paging_html}\n"
        f'<table id="ContentPlaceHolder1_dgv">{"".join(rows)}</table>\n'
        f'<span id="ContentPlaceHolder1_rlength">Реєстрових слів - {register_size}</span>\n'
    )


def _entry_html(headword: str, gloss: str, viewstate: str, tabs: str = "", register_size: int = 8) -> str:
    return (
        f'<input type="hidden" name="__VIEWSTATE" value="{viewstate}" />\n'
        '<input type="hidden" name="__VIEWSTATEGENERATOR" value="GEN" />\n'
        f'<input type="hidden" name="__EVENTVALIDATION" value="EV-{viewstate}" />\n'
        f"{tabs}\n"
        '<div id="ContentPlaceHolder1_article">\n'
        f'<span class="word_style">{headword}</span>\n'
        '<span class="gram_style">– іменник</span>\n'
        f'<div class="comment_style">{gloss}</div>\n'
        "</div>\n"
        f'<span id="ContentPlaceHolder1_rlength">Реєстрових слів - {register_size}</span>\n'
    )


class MockULIFServer:
    def __init__(
        self,
        *,
        page1_size: int = 8,
        page2_size: int = 8,
        page3_size: int = 8,
        fail_on_page2_row1: bool = False,
        fail_with_403: bool = False,
        resume_mismatch: bool = False,
        search_offsets: bool = False,
        inject_unknown_control: bool = False,
        fail_nextpage_500_times: int = 0,
        fail_page2_row1_500_times: int = 0,
    ) -> None:
        self.page1_size = page1_size
        self.page2_size = page2_size
        self.page3_size = page3_size
        self.current_page = 1
        self.fail_on_page2_row1 = fail_on_page2_row1
        self.fail_with_403 = fail_with_403
        self.resume_mismatch = resume_mismatch
        self.search_offsets = search_offsets
        self.inject_unknown_control = inject_unknown_control
        self.fail_nextpage_500_times = fail_nextpage_500_times
        self.fail_page2_row1_500_times = fail_page2_row1_500_times
        self.requests_log: list[tuple[str, dict[str, str] | None]] = []

    def _fix_html(self, html: str, size: int | None = None) -> str:
        s = getattr(self, f"page{self.current_page}_size") if size is None else size
        return re.sub(r"Реєстрових слів - \d+", f"Реєстрових слів - {s}", html)

    def __call__(self, method: str, data: dict[str, str] | None) -> HttpResult:
        self.requests_log.append((method, data))
        if self.fail_with_403:
            return HttpResult(403, "Forbidden", {})

        if method == "GET":
            seed_html = (
                '<input type="hidden" name="__VIEWSTATE" value="VS-seed" />\n'
                '<input type="hidden" name="__VIEWSTATEGENERATOR" value="GEN" />\n'
                '<input type="hidden" name="__EVENTVALIDATION" value="EV-VS-seed" />\n'
                '<input type="image" name="ctl00$ContentPlaceHolder1$search" />\n'
                f'<span id="ContentPlaceHolder1_rlength">Реєстрових слів - {self.page1_size}</span>\n'
            )
            return HttpResult(200, seed_html, {})

        assert data is not None
        vs = data.get("__VIEWSTATE", "")

        # Initial search from seed or tsearch
        if "ctl00$ContentPlaceHolder1$search.x" in data or "ctl00$ContentPlaceHolder1$search" in data:
            search_word = data.get("ctl00$ContentPlaceHolder1$tsearch", "")
            if search_word in ("а", "ду́же"):
                if search_word == "а" and self.current_page >= 2:
                    self.is_fast_forwarding = True
                else:
                    self.is_fast_forwarding = False
                p1_html = _register_html(
                    ["ду́же", "за́мок", "замо́к"],
                    "VS-p1",
                    has_next=True,
                    has_back=False,
                    register_size=self.page1_size,
                )
                return HttpResult(200, p1_html, {})
            if search_word == "замо́к":
                self.current_page = 2
                if self.resume_mismatch:
                    mismatch_html = _register_html(
                        ["а", "б"],
                        "VS-p-mismatch",
                        has_next=True,
                        has_back=False,
                        register_size=self.page2_size,
                    )
                    return HttpResult(200, mismatch_html, {})
                if self.search_offsets:
                    offset_html = _register_html(
                        ["ду́же", "за́мок", "замо́к"],
                        "VS-p1",
                        has_next=True,
                        has_back=False,
                        register_size=self.page1_size,
                    )
                    return HttpResult(200, offset_html, {})
                p2_html = _register_html(
                    ["замо́к", "Іши́м", "Іши́м"],
                    "VS-p2",
                    has_next=True,
                    has_back=True,
                    register_size=self.page2_size,
                )
                return HttpResult(200, p2_html, {})
            if search_word == "до́брий":
                self.current_page = 3
                p3_html = _register_html(
                    ["до́брий", "приві́т"],
                    "VS-p3",
                    has_next=False,
                    has_back=True,
                    register_size=self.page3_size,
                )
                return HttpResult(200, p3_html, {})

        # Paging via nextpage
        if "ctl00$ContentPlaceHolder1$nextpage.x" in data or "ctl00$ContentPlaceHolder1$nextpage" in data:
            if getattr(self, "is_fast_forwarding", False) and self.fail_nextpage_500_times > 0:
                self.fail_nextpage_500_times -= 1
                return HttpResult(500, "Injected nextpage 500", {})
            if self.resume_mismatch:
                mismatch_html = _register_html(
                    ["а", "б"],
                    "VS-p-mismatch",
                    has_next=True,
                    has_back=False,
                    register_size=self.page2_size,
                )
                return HttpResult(200, mismatch_html, {})
            if vs == "VS-p1":
                self.current_page = 2
                self.is_fast_forwarding = False
                p2_html = _register_html(
                    ["замо́к", "Іши́м", "Іши́м"],
                    "VS-p2",
                    has_next=True,
                    has_back=True,
                    register_size=self.page2_size,
                )
                return HttpResult(200, p2_html, {})
            if vs == "VS-p2":
                self.current_page = 3
                p3_html = _register_html(
                    ["до́брий", "приві́т"],
                    "VS-p3",
                    has_next=False,
                    has_back=True,
                    register_size=self.page3_size,
                )
                return HttpResult(200, p3_html, {})

        # Entry selections on Page 1
        if vs == "VS-p1" and data.get("__EVENTTARGET") == "ctl00$ContentPlaceHolder1$dgv":
            self.current_page = 1
            arg = data.get("__EVENTARGUMENT", "")
            if arg == "Select$0":
                # дуже: adverb entry
                return HttpResult(200, self._fix_html(_html("duzhe.html")), {})
            if arg == "Select$1":
                # за́мок (homonym 1, paradigm in entry)
                html = self._fix_html(_html("zamok-entry-1.html"))
                if self.inject_unknown_control:
                    html += '<input type="image" name="ctl00$ContentPlaceHolder1$custom_submit" />\n'
                return HttpResult(200, html, {})
            if arg == "Select$2":
                # замо́к (homonym 2)
                return HttpResult(200, self._fix_html(_html("zamok-entry-2.html")), {})

        # Tab selections for Page 1 entries
        if "ctl00$ContentPlaceHolder1$par.x" in data:
            if "zamok" in vs or "1" in vs:
                return HttpResult(200, self._fix_html(_html("zamok-entry-1-par.html")), {})
            return HttpResult(200, self._fix_html(_html("zamok-entry-2-par.html")), {})
        if "ctl00$ContentPlaceHolder1$syn.x" in data:
            return HttpResult(200, self._fix_html(_html("zamok-entry-2-syn.html")), {})
        if "ctl00$ContentPlaceHolder1$phras.x" in data:
            return HttpResult(200, self._fix_html(_html("zamok-entry-2-phras.html")), {})

        # Entry selections on Page 2
        if vs == "VS-p2" and data.get("__EVENTTARGET") == "ctl00$ContentPlaceHolder1$dgv":
            self.current_page = 2
            arg = data.get("__EVENTARGUMENT", "")
            if arg == "Select$0":
                # замо́к (homonym 3, straddled from Page 1)
                return HttpResult(200, self._fix_html(_html("zamok-entry-3.html")), {})
            if arg == "Select$1":
                if self.fail_page2_row1_500_times > 0:
                    self.fail_page2_row1_500_times -= 1
                    return HttpResult(500, "Injected page2 row1 500", {})
                if self.fail_on_page2_row1:
                    raise RuntimeError("Injected mid-page failure on page 2 row 1")
                # Іши́м (homonym 1)
                return HttpResult(200, self._fix_html(_html("ishym-entry-1.html")), {})
            if arg == "Select$2":
                # Іши́м (homonym 2)
                return HttpResult(200, self._fix_html(_html("ishym-entry-2.html")), {})

        # Entry selections on Page 3
        if vs == "VS-p3" and data.get("__EVENTTARGET") == "ctl00$ContentPlaceHolder1$dgv":
            self.current_page = 3
            arg = data.get("__EVENTARGUMENT", "")
            if arg == "Select$0":
                dobryi_html = _entry_html(
                    "до́брий",
                    "який має позитивні моральні якості",
                    "VS-entry-dobryi",
                    tabs='<input type="image" name="ctl00$ContentPlaceHolder1$par" />',
                    register_size=self.page3_size,
                )
                return HttpResult(200, dobryi_html, {})
            if arg == "Select$1":
                privit_html = _entry_html(
                    "приві́т",
                    "вітання, поклін",
                    "VS-entry-privit",
                    tabs='<input type="image" name="ctl00$ContentPlaceHolder1$par" />',
                    register_size=self.page3_size,
                )
                return HttpResult(200, privit_html, {})

        # Tabs for Page 3
        if vs == "VS-entry-dobryi" and "ctl00$ContentPlaceHolder1$par.x" in data:
            return HttpResult(200, self._fix_html(_html("dobryi-paradigm.html"), self.page3_size), {})
        if vs == "VS-entry-privit" and "ctl00$ContentPlaceHolder1$par.x" in data:
            return HttpResult(200, self._fix_html(_html("privit-paradigm.html"), self.page3_size), {})

        return HttpResult(200, "<html></html>", {})


def test_full_walk_stores_every_row_exactly_once(tmp_path: Path):
    server = MockULIFServer()
    state_dir = tmp_path / "state"
    db_path = tmp_path / "cache.db"

    code = run_walk(
        state_dir=state_dir,
        db_path=db_path,
        delay_seconds=1.0,
        transport=server,
        sleep=_noop_sleep,
        scanner=lambda: False,
    )
    assert code == EXIT_OK

    ledger = SpellingLedger(state_dir / "ledger.sqlite")
    try:
        pages = list(ledger.conn.execute("SELECT * FROM register_pages ORDER BY page_num"))
        assert len(pages) == 3
        for p in pages:
            assert p["state"] == "completed"
            assert p["row_count"] in (2, 3)

        rows = list(ledger.conn.execute("SELECT * FROM register_rows ORDER BY page_num, row_index"))
        assert len(rows) == 8
        for r in rows:
            assert r["state"] == "completed"
            assert r["entry_sha256"] != ""

        # Check DB entries
        conn = sqlite3.connect(db_path)
        try:
            entries = list(
                conn.execute(
                    "SELECT normalized_query, homonym_index, canonical_headword, homonym_checked FROM ulif_dictua_entries ORDER BY id"
                )
            )
            assert len(entries) == 8
            for e in entries:
                assert e[3] == 1  # homonym_checked
        finally:
            conn.close()
    finally:
        ledger.close()


def test_homonym_group_straddling_pages_gets_indexes_in_order_and_one_transaction(tmp_path: Path):
    server = MockULIFServer()
    state_dir = tmp_path / "state"
    db_path = tmp_path / "cache.db"

    run_walk(
        state_dir=state_dir,
        db_path=db_path,
        delay_seconds=1.0,
        transport=server,
        sleep=_noop_sleep,
        scanner=lambda: False,
    )

    ledger = SpellingLedger(state_dir / "ledger.sqlite")
    try:
        zamok_rows = list(
            ledger.conn.execute(
                "SELECT page_num, row_index, stressed_headword, homonym_index FROM register_rows WHERE normalized_spelling = 'замок' ORDER BY page_num, row_index"
            )
        )
        assert len(zamok_rows) == 3
        # Page 1 has row 1 and row 2 (zamok), Page 2 has row 0 (zamok)
        assert zamok_rows[0]["page_num"] == 1
        assert zamok_rows[0]["homonym_index"] == 1
        assert zamok_rows[1]["page_num"] == 1
        assert zamok_rows[1]["homonym_index"] == 2
        assert zamok_rows[2]["page_num"] == 2
        assert zamok_rows[2]["homonym_index"] == 3

        # Spelling record in spellings table is straddled
        sp_row = ledger.conn.execute(
            "SELECT straddled_boundary, entry_count, state FROM spellings WHERE spelling = 'замок'"
        ).fetchone()
        assert sp_row is not None
        assert sp_row["straddled_boundary"] == 1
        assert sp_row["entry_count"] == 3
        assert sp_row["state"] == "stored"
    finally:
        ledger.close()


def test_same_stress_pair_becomes_two_entries(tmp_path: Path):
    server = MockULIFServer()
    state_dir = tmp_path / "state"
    db_path = tmp_path / "cache.db"

    run_walk(
        state_dir=state_dir,
        db_path=db_path,
        delay_seconds=1.0,
        transport=server,
        sleep=_noop_sleep,
        scanner=lambda: False,
    )

    ledger = SpellingLedger(state_dir / "ledger.sqlite")
    try:
        ishym_rows = list(
            ledger.conn.execute(
                "SELECT page_num, row_index, stressed_headword, homonym_index FROM register_rows WHERE normalized_spelling = 'ішим' ORDER BY page_num, row_index"
            )
        )
        assert len(ishym_rows) == 2
        assert ishym_rows[0]["stressed_headword"] == "Іши́м"
        assert ishym_rows[1]["stressed_headword"] == "Іши́м"
        assert ishym_rows[0]["homonym_index"] == 1
        assert ishym_rows[1]["homonym_index"] == 2
    finally:
        ledger.close()


def test_paradigm_from_entry_makes_zero_par_requests_vs_one_when_absent(tmp_path: Path):
    server = MockULIFServer()
    state_dir = tmp_path / "state"
    db_path = tmp_path / "cache.db"

    run_walk(
        state_dir=state_dir,
        db_path=db_path,
        delay_seconds=1.0,
        transport=server,
        sleep=_noop_sleep,
        scanner=lambda: False,
    )

    ledger = SpellingLedger(state_dir / "ledger.sqlite")
    try:
        # замок on page 1 row 1 had paradigm table directly in entry HTML
        zamok_1 = ledger.conn.execute(
            "SELECT paradigm_source FROM register_rows WHERE normalized_spelling = 'замок' AND row_index = 1"
        ).fetchone()
        assert zamok_1 is not None
        assert zamok_1["paradigm_source"] == "entry"

        # Response recorded for tab/paradigm points to entry response
        zamok_tab = ledger.conn.execute(
            "SELECT response_sha256 FROM responses WHERE spelling = 'замок' AND role = 'tab' AND tab_kind = 'paradigm' AND register_position = '1:1'"
        ).fetchone()
        zamok_entry = ledger.conn.execute(
            "SELECT response_sha256 FROM responses WHERE spelling = 'замок' AND role = 'entry' AND register_position = '1:1'"
        ).fetchone()
        assert zamok_tab is not None and zamok_entry is not None
        assert zamok_tab[0] == zamok_entry[0]

        # добрий on page 3 row 0 did NOT have paradigm in entry, so paradigm_source is tab
        dobryi = ledger.conn.execute(
            "SELECT paradigm_source FROM register_rows WHERE normalized_spelling = 'добрий'"
        ).fetchone()
        assert dobryi is not None
        assert dobryi["paradigm_source"] == "tab"
    finally:
        ledger.close()


def test_parse_stored_gives_identical_rows_for_both_paradigm_sources(tmp_path: Path):
    server = MockULIFServer()
    state_dir = tmp_path / "state"
    db_path = tmp_path / "cache.db"

    run_walk(
        state_dir=state_dir,
        db_path=db_path,
        delay_seconds=1.0,
        transport=server,
        sleep=_noop_sleep,
        scanner=lambda: False,
    )

    ledger = SpellingLedger(state_dir / "ledger.sqlite")
    conn = sqlite3.connect(db_path)
    try:
        differing = parse_stored(ledger, conn)
        assert differing == 0

        sec_kinds = {row[0] for row in conn.execute("SELECT kind FROM ulif_dictua_sections")}
        assert "paradigm" in sec_kinds
    finally:
        conn.close()
        ledger.close()


def test_parse_stored_uses_completed_entry_after_interrupted_retry(tmp_path: Path, monkeypatch, capsys):
    state_dir = tmp_path / "state"
    db_path = tmp_path / "cache.db"
    real_keep = ulif_walk._keep_walk
    first_server = MockULIFServer()

    def first_transport(method: str, data: dict[str, str] | None) -> HttpResult:
        result = first_server(method, data)
        if data and data.get("__VIEWSTATE") == "VS-p2" and data.get("__EVENTARGUMENT") == "Select$1":
            return HttpResult(
                result.status_code, result.text.replace("(місто в Росії)", "(STALE RETRY BODY)"), result.headers
            )
        return result

    def interrupt_after_entry(*args, **kwargs):
        result = real_keep(*args, **kwargs)
        if args[3] == "entry" and kwargs.get("register_position") == "2:1":
            raise KeyboardInterrupt
        return result

    monkeypatch.setattr(ulif_walk, "_keep_walk", interrupt_after_entry)
    assert (
        run_walk(
            state_dir=state_dir,
            db_path=db_path,
            delay_seconds=1.0,
            transport=first_transport,
            sleep=_noop_sleep,
            scanner=lambda: False,
        )
        == ulif_walk.EXIT_INTERRUPTED
    )
    monkeypatch.setattr(ulif_walk, "_keep_walk", real_keep)

    assert (
        run_walk(
            state_dir=state_dir,
            db_path=db_path,
            delay_seconds=1.0,
            transport=MockULIFServer(),
            sleep=_noop_sleep,
            scanner=lambda: False,
        )
        == EXIT_OK
    )

    ledger = SpellingLedger(state_dir / "ledger.sqlite")
    cache = sqlite3.connect(db_path)
    try:
        responses = list(
            ledger.conn.execute(
                "SELECT response_sha256, homonym_index FROM responses "
                "WHERE spelling = 'ішим' AND role = 'entry' ORDER BY id"
            )
        )
        completed = ledger.completed_rows_for_spelling("ішим")
        assert len(responses) == 3
        assert [row[1] for row in responses] == [1, 1, 2]
        assert responses[0][0] != responses[1][0]
        assert len(completed) == 2
        assert completed[0]["entry_sha256"] == responses[1][0]

        cache.execute(
            "UPDATE ulif_dictua_entries SET canonical_headword = 'KEEP' "
            "WHERE normalized_query = 'ішим' AND homonym_index = 1"
        )
        cache.commit()
        capsys.readouterr()
        assert parse_stored(ledger, cache) == 0
        err = capsys.readouterr().err
        rows = list(
            cache.execute(
                "SELECT homonym_index, canonical_headword FROM ulif_dictua_entries "
                "WHERE normalized_query = 'ішим' ORDER BY homonym_index"
            )
        )
        duplicate = ledger.conn.execute("SELECT duplicate_content FROM spellings WHERE spelling = 'ішим'").fetchone()[0]
        assert rows[0] == (1, "KEEP")
        assert len(rows) == 2
        assert [row[0] for row in rows] == [1, 2]
        assert duplicate == 0
        assert ledger.meta("differing_content_hashes") == "0"
        assert (
            "parse complete: 5 spellings parsed, 8 entries written, 0 groups differed, "
            "0 printed_number_mismatch errors, positions skipped: 0"
        ) in err

        ledger.record_response(
            spelling="ішим",
            role="entry",
            response_sha256="orphan-response",
            request_sha256="orphan-request",
            homonym_index=None,
            register_position="2:99",
        )
        assert parse_stored(ledger, cache) == 0
        err = capsys.readouterr().err
        assert (
            "parse complete: 5 spellings parsed, 8 entries written, 0 groups differed, "
            "0 printed_number_mismatch errors, positions skipped: 1"
        ) in err
    finally:
        cache.close()
        ledger.close()


def test_completed_attempt_is_the_only_source_of_tabs_in_offline_and_live_paths(tmp_path: Path):
    from scripts.lexicon.runner.fetch_ulif_homonyms import prepare_database

    spelling = "ішим"
    position = "1:0"
    ledger = SpellingLedger(tmp_path / "state" / "ledger.sqlite")
    cache = prepare_database(tmp_path / "cache.db")
    try:
        entry_html = _html("ishym-entry-1.html")
        entry_sha = ulif_walk._sha256(entry_html.encode("utf-8"))
        tab_bodies = {
            "synonyms": _html("zamok-entry-2-syn.html"),
            "phraseology": _html("zamok-entry-2-phras.html"),
        }
        for digest, body in [
            (entry_sha, entry_html),
            *[(ulif_walk._sha256(v.encode()), v) for v in tab_bodies.values()],
        ]:
            ulif_walk._store_blob(cache, digest, body.encode("utf-8"), "text/html; charset=utf-8")
        cache.commit()

        ledger.ensure_row(1, 0, select_arg="Select$0", stressed_headword="Іши́м", normalized_spelling=spelling)
        # An interrupted attempt saved X; the completed attempt saved Y from the same entry body.
        for kind in ("synonyms", "phraseology"):
            ledger.record_response(
                spelling=spelling,
                role="entry",
                response_sha256=entry_sha,
                request_sha256="request",
                homonym_index=1,
                register_position=position,
            )
            ledger.record_response(
                spelling=spelling,
                role="tab",
                response_sha256=ulif_walk._sha256(tab_bodies[kind].encode()),
                request_sha256="request",
                homonym_index=1,
                tab_kind=kind,
                register_position=position,
            )
        ledger.mark_row(1, 0, "completed", entry_sha256=entry_sha)
        ledger.ensure(spelling)
        ledger.mark(spelling, "stored", entry_count=1)

        def stored_raw_kinds() -> set[str]:
            ref = cache.execute(
                "SELECT raw_response_ref FROM ulif_dictua_entries WHERE normalized_query = ?", (spelling,)
            ).fetchone()[0]
            from scripts.lexicon import ulif_raw_cache

            manifest = ulif_raw_cache.resolve_ref(ref, path=ulif_raw_cache.cache_path(tmp_path / "cache.db"))
            assert manifest is not None
            return set(json.loads(manifest))

        assert parse_stored(ledger, cache) == 0
        assert stored_raw_kinds() == {"phraseology"}

        cache.execute("DELETE FROM ulif_dictua_sections")
        cache.execute("DELETE FROM ulif_dictua_entries")
        cache.commit()
        ledger.mark(spelling, "pending")
        assert ulif_walk._commit_spelling_group(ledger, cache, spelling) == 0
        assert stored_raw_kinds() == {"phraseology"}
    finally:
        cache.close()
        ledger.close()


def test_parse_refuses_mixed_targeted_and_walk_ledger(tmp_path: Path, capsys):
    from scripts.lexicon.runner.fetch_ulif_homonyms import prepare_database

    state_dir = tmp_path / "state"
    db_path = tmp_path / "cache.db"
    cache = prepare_database(db_path)
    cache.close()
    ledger = SpellingLedger(state_dir / "ledger.sqlite")
    try:
        ledger.ensure_row(1, 0, select_arg="Select$0", stressed_headword="Іши́м", normalized_spelling="ішим")
        ledger.record_response(spelling="ішим", role="seed", response_sha256="seed", request_sha256="request")
        cache = prepare_database(db_path)
        try:
            with pytest.raises(ValueError, match="mixed targeted run and walk data"):
                parse_stored(ledger, cache)
        finally:
            cache.close()
    finally:
        ledger.close()
    assert ulif_walk.main(["parse", "--state-dir", str(state_dir), "--db", str(db_path)]) == EXIT_USAGE
    assert "mixed targeted run and walk data" in capsys.readouterr().err


def test_fetch_modes_refuse_reusing_the_opposite_state_dir(tmp_path: Path, capsys):
    from scripts.lexicon.runner.fetch_ulif_homonyms import prepare_database, run_fetch

    db_path = tmp_path / "cache.db"
    prepare_database(db_path).close()

    run_state = tmp_path / "run-state"
    run_ledger = SpellingLedger(run_state / "ledger.sqlite")
    run_ledger.set_meta("mode", "run")
    run_ledger.close()
    assert (
        run_walk(
            state_dir=run_state,
            db_path=db_path,
            transport=lambda *_: pytest.fail("mixed-mode walk made a request"),
            sleep=_noop_sleep,
            scanner=lambda: False,
        )
        == EXIT_USAGE
    )
    assert "targeted run data in --state-dir" in capsys.readouterr().err

    walk_state = tmp_path / "walk-state"
    walk_ledger = SpellingLedger(walk_state / "ledger.sqlite")
    walk_ledger.set_meta("mode", "walk")
    walk_ledger.close()
    assert (
        run_fetch(
            spellings=["ішим"],
            state_dir=walk_state,
            db_path=db_path,
            transport=lambda *_: pytest.fail("mixed-mode run made a request"),
            sleep=_noop_sleep,
            scanner=lambda: False,
        )
        == EXIT_USAGE
    )
    assert "walk data in --state-dir" in capsys.readouterr().err


def test_resume_after_injected_mid_page_failure_refetches_nothing_already_stored(tmp_path: Path):
    server1 = MockULIFServer(fail_on_page2_row1=True)
    state_dir = tmp_path / "state"
    db_path = tmp_path / "cache.db"

    # First run fails on page 2 row 1
    code1 = run_walk(
        state_dir=state_dir,
        db_path=db_path,
        delay_seconds=1.0,
        transport=server1,
        sleep=_noop_sleep,
        scanner=lambda: False,
    )
    assert code1 != EXIT_OK

    ledger = SpellingLedger(state_dir / "ledger.sqlite")
    try:
        p1 = ledger.get_page(1)
        assert p1 is not None and p1["state"] == "completed"

        p2 = ledger.get_page(2)
        assert p2 is not None and p2["state"] == "in_progress"

        p2_r0 = ledger.conn.execute("SELECT state FROM register_rows WHERE page_num = 2 AND row_index = 0").fetchone()
        assert p2_r0["state"] == "completed"
    finally:
        ledger.close()

    # Second run resumes
    server2 = MockULIFServer(fail_on_page2_row1=False)
    code2 = run_walk(
        state_dir=state_dir,
        db_path=db_path,
        delay_seconds=1.0,
        transport=server2,
        sleep=_noop_sleep,
        scanner=lambda: False,
    )
    assert code2 == EXIT_OK

    # Check that server2 verified resume via tsearch and did NOT re-request row 0 on Page 2
    p2_r0_reqs = [
        req
        for method, req in server2.requests_log
        if req
        and req.get("__EVENTTARGET") == "ctl00$ContentPlaceHolder1$dgv"
        and req.get("__EVENTARGUMENT") == "Select$0"
        and req.get("__VIEWSTATE") == "VS-p2"
    ]
    assert len(p2_r0_reqs) == 0  # 0 requests made for already completed row!


def test_resume_mismatch_stops_cleanly_with_resume_mismatch(tmp_path: Path):
    server1 = MockULIFServer(fail_on_page2_row1=True)
    state_dir = tmp_path / "state"
    db_path = tmp_path / "cache.db"

    run_walk(
        state_dir=state_dir,
        db_path=db_path,
        delay_seconds=1.0,
        transport=server1,
        sleep=_noop_sleep,
        scanner=lambda: False,
    )

    # Resume with server that returns mismatching landing page
    server2 = MockULIFServer(resume_mismatch=True)
    code2 = run_walk(
        state_dir=state_dir,
        db_path=db_path,
        delay_seconds=1.0,
        transport=server2,
        sleep=_noop_sleep,
        scanner=lambda: False,
    )
    assert code2 == EXIT_USAGE

    ledger = SpellingLedger(state_dir / "ledger.sqlite")
    try:
        p2 = ledger.get_page(2)
        assert p2 is not None
        assert p2["state"] == "error"
        assert p2["error"] == "resume_mismatch"
    finally:
        ledger.close()


def test_resume_fast_forward_when_search_offsets(tmp_path: Path):
    server1 = MockULIFServer(fail_on_page2_row1=True)
    state_dir = tmp_path / "state"
    db_path = tmp_path / "cache.db"

    run_walk(
        state_dir=state_dir,
        db_path=db_path,
        delay_seconds=1.0,
        transport=server1,
        sleep=_noop_sleep,
        scanner=lambda: False,
    )

    # The offset search returns page 1's rows. They match no placement on page 2.
    server2 = MockULIFServer(search_offsets=True)
    code2 = run_walk(
        state_dir=state_dir,
        db_path=db_path,
        delay_seconds=1.0,
        transport=server2,
        sleep=_noop_sleep,
        scanner=lambda: False,
    )
    assert code2 == EXIT_USAGE

    ledger = SpellingLedger(state_dir / "ledger.sqlite")
    try:
        p2 = ledger.get_page(2)
        assert p2 is not None
        assert p2["error"] == "resume_mismatch"
    finally:
        ledger.close()


@pytest.mark.parametrize(
    ("page", "fixture", "offset"),
    [
        (3136, "register-page-3136-offset-4.html", 4),
        (248, "register-page-248-offset-2.html", 2),
    ],
)
def test_recorded_ulif_search_windows_map_to_canonical_rows(tmp_path: Path, page: int, fixture: str, offset: int):
    rows = parse_register_list(_html(fixture))
    assert len(rows) == 25
    ledger = SpellingLedger(tmp_path / "ledger.sqlite")
    try:
        for i, row in enumerate(rows):
            canonical_page, index = divmod((page - 1) * 25 - offset + i, 25)
            ledger.ensure_row(
                canonical_page + 1,
                index,
                select_arg=str(row["select"]),
                stressed_headword=str(row["stressed"]),
                normalized_spelling=normalize_ulif_spelling(str(row["unstressed"])),
            )
        anchor = rows[offset]["stressed"]
        ledger.ensure_page(page, start_headword=anchor, row_count=25)
        # Only the rows inside this window are recorded. A later start that misses
        # those rows is also consistent, so the alignment does not guess an offset.
        assert (
            _resume_window_offset(
                ledger, rows, target_page=page, anchor_headword=anchor, anchor_page=page, anchor_index=0
            )
            is None
        )
        assert rows[offset]["stressed"] == ("зі" if page == 3136 else "Арка́нза́с")
    finally:
        ledger.close()


class ShiftedWindowServer:
    words: ClassVar[list[str]] = [f"w{i:03d}" for i in range(100)]

    def __init__(self, offset: int, *, mode: str = "direct", fail_nextpage_500_times: int = 0) -> None:
        self.offset = offset
        self.mode = mode
        self.fail_nextpage_500_times = fail_nextpage_500_times
        self.requests: list[tuple[str, dict[str, str] | None]] = []

    def _window(self, start: int, *, mutate: str = "") -> str:
        words = self.words[start : start + 25].copy()
        if mutate == "duplicate":
            words[0] = self.words[25]
        elif mutate == "duplicate_aligned":
            words[1] = self.words[25]
        elif mutate == "mismatch":
            words[1] = "wrong"
        elif mutate == "absent":
            words = self.words[:25]
        return _register_html(words, f"VS-{start}", has_next=start + 25 < len(self.words), register_size=100)

    def __call__(self, method: str, data: dict[str, str] | None) -> HttpResult:
        self.requests.append((method, data))
        if method == "GET":
            return HttpResult(
                200,
                '<input name="__VIEWSTATE" value="SEED" />'
                '<input name="__VIEWSTATEGENERATOR" value="GEN" />'
                '<input name="__EVENTVALIDATION" value="EV-SEED" />',
                {},
            )
        assert data is not None
        if "ctl00$ContentPlaceHolder1$search.x" in data:
            word = data.get("ctl00$ContentPlaceHolder1$tsearch")
            if word in ("а", self.words[0]):
                return HttpResult(200, self._window(0), {})
            if word in (self.words[24], self.words[25], self.words[49], self.words[50]):
                target_start = 50 if word in (self.words[49], self.words[50]) else 25
                start = target_start if self.mode == "duplicate_aligned" else target_start - self.offset
                return HttpResult(200, self._window(start, mutate=self.mode), {})
        if "ctl00$ContentPlaceHolder1$nextpage.x" in data:
            if self.fail_nextpage_500_times > 0:
                self.fail_nextpage_500_times -= 1
                return HttpResult(500, "Injected nextpage 500", {})
            start = int(data["__VIEWSTATE"].split("-")[1]) + 25
            if self.mode == "reset":
                start = 0
            elif self.mode == "overlap":
                start -= 2
            return HttpResult(200, self._window(start), {})
        if data.get("__EVENTTARGET") == "ctl00$ContentPlaceHolder1$dgv":
            start = int(data["__VIEWSTATE"].split("-")[1])
            index = int(data["__EVENTARGUMENT"].split("$")[1])
            word = self.words[start + index]
            return HttpResult(200, _entry_html(word, "synthetic", f"ENTRY-{start + index}", register_size=100), {})
        return HttpResult(200, "<html></html>", {})


def _seed_shifted_ledger(state_dir: Path) -> None:
    ledger = SpellingLedger(state_dir / "ledger.sqlite")
    try:
        for page in (1, 2):
            words = ShiftedWindowServer.words[(page - 1) * 25 : page * 25]
            ledger.ensure_page(page, start_headword=words[0], end_headword=words[-1], row_count=25, register_size=100)
            for index, word in enumerate(words):
                ledger.ensure_row(
                    page,
                    index,
                    select_arg=f"Select${index}",
                    stressed_headword=word,
                    normalized_spelling=word,
                )
                if page == 1:
                    ledger.mark_row(page, index, "completed")
            if page == 1:
                ledger.mark_page(page, "completed")
    finally:
        ledger.close()


@pytest.mark.parametrize("offset", [0, 2, 4, 24])
def test_shifted_resume_completes_canonical_pages_across_windows(tmp_path: Path, offset: int, capsys):
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    _seed_shifted_ledger(state_dir)
    server = ShiftedWindowServer(offset)
    code = run_walk(
        state_dir=state_dir,
        db_path=tmp_path / "cache.db",
        delay_seconds=1,
        max_pages=2,
        transport=server,
        sleep=_noop_sleep,
        scanner=lambda: False,
    )
    assert code == EXIT_OK
    assert f"k={offset}" in capsys.readouterr().err
    ledger = SpellingLedger(state_dir / "ledger.sqlite")
    try:
        assert [ledger.get_page(page)["state"] for page in (1, 2, 3)] == ["completed"] * 3
        assert [row["stressed_headword"] for row in ledger.page_rows(2)] == server.words[25:50]
        assert [row["stressed_headword"] for row in ledger.page_rows(3)] == server.words[50:75]
        assert all(row["state"] == "completed" for page in (2, 3) for row in ledger.page_rows(page))
        entry_positions = [
            row["register_position"]
            for row in ledger.conn.execute("SELECT register_position FROM responses WHERE role = 'entry' ORDER BY id")
        ]
        assert entry_positions == [f"{page}:{index}" for page in (2, 3) for index in range(25)]
    finally:
        ledger.close()
    searches = [
        data["ctl00$ContentPlaceHolder1$tsearch"]
        for method, data in server.requests
        if data and "ctl00$ContentPlaceHolder1$search.x" in data
    ]
    assert searches == ["w025"]


@pytest.mark.parametrize("mode", ["reset", "overlap"])
def test_shifted_resume_rejects_next_window_drift_before_writing_rows(tmp_path: Path, mode: str):
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    _seed_shifted_ledger(state_dir)
    server = ShiftedWindowServer(4, mode=mode)
    code = run_walk(
        state_dir=state_dir,
        db_path=tmp_path / "cache.db",
        delay_seconds=1,
        max_pages=2,
        transport=server,
        sleep=_noop_sleep,
        scanner=lambda: False,
    )
    assert code == (EXIT_USAGE if mode == "reset" else EXIT_RETRY_STORM)
    ledger = SpellingLedger(state_dir / "ledger.sqlite")
    try:
        assert ledger.page_rows(3) == []
        assert ledger.get_page(2)["state"] == ("error" if mode == "reset" else "retry_scheduled")
    finally:
        ledger.close()


def test_first_unrecorded_page_uses_previous_ledger_boundary(tmp_path: Path):
    ledger = SpellingLedger(tmp_path / "ledger.sqlite")
    try:
        ledger.ensure_row(
            1, 24, select_arg="Select$24", stressed_headword="абазинський", normalized_spelling="абазинський"
        )
        ulif_walk._verify_first_unrecorded_page(
            ledger,
            [{"stressed": "Аба́зівка"}, {"stressed": "абазія"}],
            25,
        )
        # A local alphabet cannot reject a page ULIF supplies; there is no
        # stored entry at the new position yet to contradict this window.
        ulif_walk._verify_first_unrecorded_page(
            ledger,
            [{"stressed": "а"}, {"stressed": "абазія"}],
            25,
        )
    finally:
        ledger.close()


def test_resume_without_target_start_searches_last_completed_page(tmp_path: Path):
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    _seed_shifted_ledger(state_dir)
    ledger = SpellingLedger(state_dir / "ledger.sqlite")
    try:
        ledger.conn.execute(
            "UPDATE register_pages SET start_headword = '', end_headword = '', row_count = 0 WHERE page_num = 2"
        )
        ledger.conn.execute("DELETE FROM register_rows WHERE page_num = 2")
        ledger.conn.commit()
    finally:
        ledger.close()
    server = ShiftedWindowServer(4)
    assert (
        run_walk(
            state_dir=state_dir,
            db_path=tmp_path / "cache.db",
            delay_seconds=1,
            max_pages=1,
            transport=server,
            sleep=_noop_sleep,
            scanner=lambda: False,
        )
        == EXIT_OK
    )
    searches = [
        data["ctl00$ContentPlaceHolder1$tsearch"]
        for _, data in server.requests
        if data and "ctl00$ContentPlaceHolder1$search.x" in data
    ]
    assert searches == ["w024"]


def test_page_one_reseed_after_transient_failure_uses_direct_search(tmp_path: Path, capsys):
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    ledger = SpellingLedger(state_dir / "ledger.sqlite")
    try:
        words = ShiftedWindowServer.words[:25]
        ledger.ensure_page(1, start_headword=words[0], end_headword=words[-1], row_count=25)
        for index, word in enumerate(words):
            ledger.ensure_row(
                1,
                index,
                select_arg=f"Select${index}",
                stressed_headword=word,
                normalized_spelling=normalize_ulif_spelling(word),
            )
        ledger.mark_page(1, "retry_scheduled", error="transient_error")
    finally:
        ledger.close()
    server = ShiftedWindowServer(0)
    assert (
        run_walk(
            state_dir=state_dir,
            db_path=tmp_path / "cache.db",
            delay_seconds=1,
            max_pages=1,
            transport=server,
            sleep=_noop_sleep,
            scanner=lambda: False,
        )
        == EXIT_OK
    )
    err = capsys.readouterr().err
    assert "direct search page 1, k=0" in err
    assert "resume_mismatch" not in err


def test_mid_page_prefix_resumes_from_completed_page_without_fast_forward(tmp_path: Path, capsys):
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    _seed_shifted_ledger(state_dir)
    ledger = SpellingLedger(state_dir / "ledger.sqlite")
    try:
        ledger.conn.execute("DELETE FROM register_rows WHERE page_num = 2 AND row_index >= 22")
        ledger.conn.execute("UPDATE register_pages SET end_headword = '', row_count = 0 WHERE page_num = 2")
        ledger.conn.commit()
    finally:
        ledger.close()
    server = ShiftedWindowServer(3)
    assert (
        run_walk(
            state_dir=state_dir,
            db_path=tmp_path / "cache.db",
            delay_seconds=1,
            max_pages=1,
            transport=server,
            sleep=_noop_sleep,
            scanner=lambda: False,
        )
        == EXIT_OK
    )
    assert "direct search page 2, k=3" in capsys.readouterr().err
    searches = [
        data["ctl00$ContentPlaceHolder1$tsearch"]
        for _, data in server.requests
        if data and "ctl00$ContentPlaceHolder1$search.x" in data
    ]
    assert searches == ["w024"]


def test_chunked_walk_resumes_next_unrecorded_page_without_fast_forward(tmp_path: Path, capsys):
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    _seed_shifted_ledger(state_dir)
    first = ShiftedWindowServer(3)
    assert (
        run_walk(
            state_dir=state_dir,
            db_path=tmp_path / "cache.db",
            delay_seconds=1,
            max_pages=1,
            transport=first,
            sleep=_noop_sleep,
            scanner=lambda: False,
        )
        == EXIT_OK
    )
    capsys.readouterr()
    second = ShiftedWindowServer(3)
    assert (
        run_walk(
            state_dir=state_dir,
            db_path=tmp_path / "cache.db",
            delay_seconds=1,
            max_pages=1,
            transport=second,
            sleep=_noop_sleep,
            scanner=lambda: False,
        )
        == EXIT_OK
    )
    assert "direct search page 3" in capsys.readouterr().err
    searches = [
        data["ctl00$ContentPlaceHolder1$tsearch"]
        for _, data in second.requests
        if data and "ctl00$ContentPlaceHolder1$search.x" in data
    ]
    assert searches == ["w049"]


@pytest.mark.parametrize("damage", ["gap", "start", "end", "count"])
def test_verify_ledger_flag_is_read_only_and_names_bad_page(tmp_path: Path, capsys, damage: str):
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    ledger = SpellingLedger(state_dir / "ledger.sqlite")
    try:
        ledger.ensure_page(1, start_headword="а", end_headword="в", row_count=3)
        for index, word in enumerate(("а", "б", "в")):
            ledger.ensure_row(1, index, select_arg=f"Select${index}", stressed_headword=word, normalized_spelling=word)
        ledger.mark_page(1, "completed")
        changes = {
            "gap": "UPDATE register_rows SET row_index = 4 WHERE page_num = 1 AND row_index = 1",
            "start": "UPDATE register_pages SET start_headword = 'х' WHERE page_num = 1",
            "end": "UPDATE register_pages SET end_headword = 'х' WHERE page_num = 1",
            "count": "UPDATE register_pages SET row_count = 2 WHERE page_num = 1",
        }
        ledger.conn.execute(changes[damage])
        ledger.conn.commit()
    finally:
        ledger.close()
    ledger_path = state_dir / "ledger.sqlite"
    before = ledger_path.stat().st_mtime_ns
    code = ulif_walk.main(["walk", "--state-dir", str(state_dir), "--verify-ledger"])
    assert code == EXIT_USAGE
    assert "page 1" in capsys.readouterr().err
    assert ledger_path.stat().st_mtime_ns == before


# Source order from the live ULIF register, page 4098, rows 16–24. The
# capitalized proper name at row 19 precedes lower-case ледь at row 20.
ULIF_PAGE_4098_TAIL = (
    "ле́ді",
    "Ле́дісмі́т",
    "Ле́дне",
    "Лель",
    "ледь",
    "ледь",
    "ледь-ле́дь",
    "ледь-не-ле́дь",
    "Ледяне́ць",
)


def _record_page_4098_tail(ledger: SpellingLedger) -> None:
    words = ("ле́две",) * 16 + ULIF_PAGE_4098_TAIL
    ledger.ensure_page(1, start_headword=words[0], end_headword=words[-1], row_count=len(words))
    for index, word in enumerate(words):
        spelling = normalize_ulif_spelling(word)
        ledger.ensure_row(1, index, select_arg=f"Select${index}", stressed_headword=word, normalized_spelling=spelling)
        ledger.record_response(
            spelling=spelling,
            role="entry",
            response_sha256="a" * 64,
            request_sha256="b" * 64,
            register_position=f"1:{index}",
        )
    ledger.mark_page(1, "completed")


def test_verify_ledger_accepts_ulif_page_4098_source_order(tmp_path: Path):
    ledger = SpellingLedger(tmp_path / "ledger.sqlite")
    try:
        _record_page_4098_tail(ledger)
    finally:
        ledger.close()
    assert ulif_walk.verify_ledger_continuity(tmp_path / "ledger.sqlite") == 1


def test_verify_ledger_rejects_row_shift_against_recorded_entry_position(tmp_path: Path):
    ledger = SpellingLedger(tmp_path / "ledger.sqlite")
    try:
        _record_page_4098_tail(ledger)
        # Keep indexes contiguous and boundaries correct, but shift one row's
        # spelling away from the entry response stored at the same position.
        ledger.conn.execute(
            "UPDATE register_rows SET stressed_headword = 'ле́две', normalized_spelling = 'ледве' "
            "WHERE page_num = 1 AND row_index = 20"
        )
        ledger.conn.commit()
    finally:
        ledger.close()
    with pytest.raises(ulif_walk.ResumeMismatchError, match=r"row 20.*entry response"):
        ulif_walk.verify_ledger_continuity(tmp_path / "ledger.sqlite")


def test_entry_retry_after_tab_interruption_never_bricks_startup(tmp_path: Path, capsys):
    state_dir = tmp_path / "state"
    db_path = tmp_path / "cache.db"
    state_dir.mkdir()

    for attempt in range(2):
        server = MockULIFServer()
        clicked = False

        def interrupted_transport(method: str, data: dict[str, str] | None, server=server) -> HttpResult:
            nonlocal clicked
            if clicked:
                raise KeyboardInterrupt
            result = server(method, data)
            if data and data.get("__EVENTARGUMENT") == "Select$2" and server.current_page == 1:
                clicked = True
            return result

        assert (
            run_walk(
                state_dir=state_dir,
                db_path=db_path,
                delay_seconds=1,
                transport=interrupted_transport,
                sleep=_noop_sleep,
                scanner=lambda: False,
            )
            == ulif_walk.EXIT_INTERRUPTED
        )
        ledger = SpellingLedger(state_dir / "ledger.sqlite")
        try:
            assert (
                ledger.conn.execute(
                    "SELECT COUNT(*) FROM responses WHERE role = 'entry' AND register_position = '1:2'"
                ).fetchone()[0]
                == attempt + 1
            )
            assert (
                ledger.conn.execute("SELECT state FROM register_rows WHERE page_num = 1 AND row_index = 2").fetchone()[
                    0
                ]
                == "pending"
            )
        finally:
            ledger.close()
        assert ulif_walk.main(["walk", "--state-dir", str(state_dir), "--verify-ledger"]) == EXIT_OK
        assert "ledger continuity OK" in capsys.readouterr().out

    assert (
        run_walk(
            state_dir=state_dir,
            db_path=db_path,
            delay_seconds=1,
            max_pages=1,
            transport=MockULIFServer(),
            sleep=_noop_sleep,
            scanner=lambda: False,
        )
        == EXIT_OK
    )
    assert ulif_walk.main(["walk", "--state-dir", str(state_dir), "--verify-ledger"]) == EXIT_OK
    ledger = SpellingLedger(state_dir / "ledger.sqlite")
    try:
        assert (
            ledger.conn.execute(
                "SELECT COUNT(*) FROM responses WHERE role = 'entry' AND register_position = '1:2'"
            ).fetchone()[0]
            == 3
        )
        ledger.conn.execute(
            "UPDATE responses SET spelling = 'wrong' WHERE role = 'entry' AND register_position = '1:2' "
            "AND id = (SELECT MIN(id) FROM responses WHERE role = 'entry' AND register_position = '1:2')"
        )
        ledger.conn.commit()
    finally:
        ledger.close()
    with pytest.raises(ulif_walk.ResumeMismatchError, match=r"page 1 row 2: spelling differs from entry response"):
        ulif_walk.verify_ledger_continuity(state_dir / "ledger.sqlite")


def test_verify_ledger_accepts_interrupted_page_write(tmp_path: Path):
    ledger = SpellingLedger(tmp_path / "ledger.sqlite")
    try:
        # The walk commits page geometry before it writes the listing rows.
        ledger.ensure_page(1, start_headword="w00", end_headword="w24", row_count=25)
        for index in range(3):
            word = f"w{index:02d}"
            ledger.ensure_row(1, index, select_arg=f"Select${index}", stressed_headword=word, normalized_spelling=word)
    finally:
        ledger.close()
    assert ulif_walk.verify_ledger_continuity(tmp_path / "ledger.sqlite") == 1


def test_verify_ledger_reports_suspect_overlap_while_walk_startup_warns(tmp_path: Path, capsys):
    ledger = SpellingLedger(tmp_path / "ledger.sqlite")
    try:
        first = [f"w{index:02d}" for index in range(25)]
        second = ["w22", "w23", *[f"x{index:02d}" for index in range(23)]]
        for page_num, words in ((1, first), (2, second)):
            ledger.ensure_page(page_num, start_headword=words[0], end_headword=words[-1], row_count=25)
            for index, word in enumerate(words):
                ledger.ensure_row(
                    page_num, index, select_arg=f"Select${index}", stressed_headword=word, normalized_spelling=word
                )
            ledger.mark_page(page_num, "completed")
    finally:
        ledger.close()
    with pytest.raises(
        ulif_walk.ResumeMismatchError, match=r"pages 1 and 2: suspect cross-page overlap .*verify manually"
    ):
        ulif_walk.verify_ledger_continuity(tmp_path / "ledger.sqlite")

    def forbidden_transport(method: str, data: dict[str, str] | None) -> HttpResult:
        pytest.fail("request cap should prevent network calls")

    assert (
        run_walk(
            state_dir=tmp_path,
            db_path=tmp_path / "cache.db",
            delay_seconds=1,
            max_requests=0,
            transport=forbidden_transport,
            sleep=_noop_sleep,
            scanner=lambda: False,
        )
        == EXIT_OK
    )
    assert "ledger continuity warning: pages 1 and 2: suspect cross-page overlap" in capsys.readouterr().err


@pytest.mark.parametrize(
    ("sizes", "initial_search", "expected_failure"),
    [
        ((22, 25), True, None),
        ((22, 25), False, "page 1: short page"),
        ((25, 22, 25), True, "page 2: short page"),
        ((25, 26), True, "page 2: row count exceeds"),
    ],
)
def test_verify_ledger_short_search_page_and_page_size(
    tmp_path: Path, sizes: tuple[int, ...], initial_search: bool, expected_failure: str | None
):
    ledger = SpellingLedger(tmp_path / "ledger.sqlite")
    try:
        if initial_search:
            ledger.record_response(
                spelling="",
                role="tsearch:start",
                response_sha256="a" * 64,
                request_sha256="b" * 64,
            )
        for page_num, size in enumerate(sizes, start=1):
            words = [f"w{page_num:02d}-{index:02d}" for index in range(size)]
            ledger.ensure_page(page_num, start_headword=words[0], end_headword=words[-1], row_count=size)
            for index, word in enumerate(words):
                ledger.ensure_row(
                    page_num,
                    index,
                    select_arg=f"Select${index}",
                    stressed_headword=word,
                    normalized_spelling=word,
                )
            ledger.mark_page(page_num, "completed")
    finally:
        ledger.close()
    if expected_failure is None:
        assert ulif_walk.verify_ledger_continuity(tmp_path / "ledger.sqlite") == len(sizes)
    else:
        with pytest.raises(ulif_walk.ResumeMismatchError, match=expected_failure):
            ulif_walk.verify_ledger_continuity(tmp_path / "ledger.sqlite")


def test_verify_ledger_flag_reports_success_without_cache_or_requests(tmp_path: Path, capsys):
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    ledger = SpellingLedger(state_dir / "ledger.sqlite")
    try:
        ledger.ensure_page(1, start_headword="а", end_headword="б", row_count=2)
        for index, word in enumerate(("а", "б")):
            ledger.ensure_row(1, index, select_arg=f"Select${index}", stressed_headword=word, normalized_spelling=word)
        ledger.mark_page(1, "completed")
    finally:
        ledger.close()
    assert ulif_walk.main(["walk", "--state-dir", str(state_dir), "--verify-ledger"]) == EXIT_OK
    assert "ledger continuity OK: 1 pages checked" in capsys.readouterr().out


def test_walk_rejects_broken_ledger_before_network_or_cache(tmp_path: Path, capsys):
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    ledger = SpellingLedger(state_dir / "ledger.sqlite")
    try:
        ledger.ensure_page(1, start_headword="а", end_headword="б", row_count=2)
        ledger.ensure_row(1, 0, select_arg="Select$0", stressed_headword="а", normalized_spelling="а")
        ledger.ensure_row(1, 2, select_arg="Select$1", stressed_headword="б", normalized_spelling="б")
    finally:
        ledger.close()

    def forbidden_transport(method: str, data: dict[str, str] | None) -> HttpResult:
        pytest.fail("network reached before ledger verification")

    cache_path = tmp_path / "cache.db"
    assert (
        run_walk(
            state_dir=state_dir,
            db_path=cache_path,
            delay_seconds=1,
            transport=forbidden_transport,
            sleep=_noop_sleep,
            scanner=lambda: False,
        )
        == EXIT_USAGE
    )
    assert "page 1" in capsys.readouterr().err
    assert not cache_path.exists()


def test_shifted_page_requires_all_recorded_rows_before_completion(tmp_path: Path, monkeypatch):
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    _seed_shifted_ledger(state_dir)
    server = ShiftedWindowServer(4)
    original = SpellingLedger.page_rows

    def omit_one_row(self, page_num: int):
        rows = original(self, page_num)
        return [row for row in rows if page_num != 2 or row["row_index"] != 10]

    monkeypatch.setattr(SpellingLedger, "page_rows", omit_one_row)
    code = run_walk(
        state_dir=state_dir,
        db_path=tmp_path / "cache.db",
        delay_seconds=1,
        max_pages=1,
        transport=server,
        sleep=_noop_sleep,
        scanner=lambda: False,
    )
    assert code == EXIT_RETRY_STORM
    ledger = SpellingLedger(state_dir / "ledger.sqlite")
    try:
        assert ledger.get_page(2)["state"] == "retry_scheduled"
    finally:
        ledger.close()


def test_failed_reseed_never_reuses_stale_window(tmp_path: Path):
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    _seed_shifted_ledger(state_dir)
    server = ShiftedWindowServer(4, fail_nextpage_500_times=1)

    def failing_reseed(method: str, data: dict[str, str] | None) -> HttpResult:
        if method == "GET" and server.requests:
            server.requests.append((method, data))
            return HttpResult(500, "Injected reseed GET 500", {})
        return server(method, data)

    code = run_walk(
        state_dir=state_dir,
        db_path=tmp_path / "cache.db",
        delay_seconds=1,
        transport=failing_reseed,
        sleep=_noop_sleep,
        scanner=lambda: False,
    )
    assert code == EXIT_RETRY_STORM
    assert sum(bool(data and "ctl00$ContentPlaceHolder1$nextpage.x" in data) for _, data in server.requests) == 1


def test_resume_absent_direct_search_fast_forwards(tmp_path: Path, capsys):
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    _seed_shifted_ledger(state_dir)
    server = ShiftedWindowServer(4, mode="absent")
    code = run_walk(
        state_dir=state_dir,
        db_path=tmp_path / "cache.db",
        delay_seconds=1,
        max_pages=1,
        transport=server,
        sleep=_noop_sleep,
        scanner=lambda: False,
    )
    assert code == EXIT_OK
    output = capsys.readouterr().err
    assert "fast-forwarding" in output
    assert "previous-page" not in output
    searches = [
        data["ctl00$ContentPlaceHolder1$tsearch"]
        for method, data in server.requests
        if data and "ctl00$ContentPlaceHolder1$search.x" in data
    ]
    assert searches == ["w025", "а"]


@pytest.mark.parametrize("mode", ["duplicate", "duplicate_aligned"])
def test_resume_contradictory_direct_search_stops(tmp_path: Path, mode: str):
    """A window that matches no placement overlapping the target page is drift."""
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    _seed_shifted_ledger(state_dir)
    server = ShiftedWindowServer(4, mode=mode)
    code = run_walk(
        state_dir=state_dir,
        db_path=tmp_path / "cache.db",
        delay_seconds=1,
        max_pages=1,
        transport=server,
        sleep=_noop_sleep,
        scanner=lambda: False,
    )
    assert code == EXIT_USAGE
    ledger = SpellingLedger(state_dir / "ledger.sqlite")
    try:
        assert ledger.get_page(2)["error"] == "resume_mismatch"
    finally:
        ledger.close()


def test_shifted_resume_mapped_row_mismatch_stops_before_entry_click(tmp_path: Path):
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    _seed_shifted_ledger(state_dir)
    server = ShiftedWindowServer(4, mode="mismatch")
    code = run_walk(
        state_dir=state_dir,
        db_path=tmp_path / "cache.db",
        delay_seconds=1,
        transport=server,
        sleep=_noop_sleep,
        scanner=lambda: False,
    )
    assert code == EXIT_USAGE
    assert not any(data and data.get("__EVENTTARGET") == "ctl00$ContentPlaceHolder1$dgv" for _, data in server.requests)
    ledger = SpellingLedger(state_dir / "ledger.sqlite")
    try:
        assert ledger.get_page(2)["error"] == "resume_mismatch"
    finally:
        ledger.close()


def test_shifted_resume_persistent_nextpage_failure_exhausts_retries(tmp_path: Path):
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    _seed_shifted_ledger(state_dir)
    server = ShiftedWindowServer(4, fail_nextpage_500_times=10)
    code = run_walk(
        state_dir=state_dir,
        db_path=tmp_path / "cache.db",
        delay_seconds=1,
        transport=server,
        sleep=_noop_sleep,
        scanner=lambda: False,
    )
    assert code == EXIT_RETRY_STORM
    assert sum(bool(data and "ctl00$ContentPlaceHolder1$nextpage.x" in data) for _, data in server.requests) == 3
    ledger = SpellingLedger(state_dir / "ledger.sqlite")
    try:
        assert ledger.get_page(2)["state"] == "retry_scheduled"
    finally:
        ledger.close()


def test_startup_resume_offset_search_stops_for_drift(tmp_path: Path):
    """A startup search that matches no page placement stops before pagination."""
    server1 = MockULIFServer(fail_on_page2_row1=True)
    state_dir = tmp_path / "state"
    db_path = tmp_path / "cache.db"

    # Run 1 fails on page 2 row 1, leaving page 2 in_progress
    run_walk(
        state_dir=state_dir,
        db_path=db_path,
        delay_seconds=1.0,
        transport=server1,
        sleep=_noop_sleep,
        scanner=lambda: False,
    )

    server2 = MockULIFServer(search_offsets=True, fail_nextpage_500_times=1)
    code2 = run_walk(
        state_dir=state_dir,
        db_path=db_path,
        delay_seconds=1.0,
        transport=server2,
        sleep=_noop_sleep,
        scanner=lambda: False,
    )
    assert code2 == EXIT_USAGE

    ledger = SpellingLedger(state_dir / "ledger.sqlite")
    try:
        p2 = ledger.get_page(2)
        assert p2 is not None
        assert p2["error"] == "resume_mismatch"
    finally:
        ledger.close()


def test_startup_resume_contradictory_search_stops_before_pagination(tmp_path: Path):
    """A contradictory resume search stops. It does not paginate into HTTP retries."""
    server1 = MockULIFServer(fail_on_page2_row1=True)
    state_dir = tmp_path / "state"
    db_path = tmp_path / "cache.db"

    # Run 1 fails on page 2 row 1, leaving page 2 in_progress
    run_walk(
        state_dir=state_dir,
        db_path=db_path,
        delay_seconds=1.0,
        transport=server1,
        sleep=_noop_sleep,
        scanner=lambda: False,
    )

    # Resume with server that offsets search AND fails all nextpage clicks with 500
    server2 = MockULIFServer(search_offsets=True, fail_nextpage_500_times=10)
    code2 = run_walk(
        state_dir=state_dir,
        db_path=db_path,
        delay_seconds=1.0,
        transport=server2,
        sleep=_noop_sleep,
        scanner=lambda: False,
    )
    assert code2 == EXIT_USAGE

    ledger = SpellingLedger(state_dir / "ledger.sqlite")
    try:
        p2 = ledger.get_page(2)
        assert p2 is not None
        assert p2["error"] == "resume_mismatch"
    finally:
        ledger.close()


def test_startup_retry_exhaustion_followed_by_healthy_invocation_recovers(tmp_path: Path):
    """Startup failure leaves uninitialized page 1 with empty boundaries; restart on healthy server recovers."""
    server1 = MockULIFServer()
    orig_call = server1.__call__

    def failing_call(method: str, data: dict[str, str] | None) -> HttpResult:
        if method == "GET":
            return HttpResult(500, "Injected initial GET 500", {})
        return orig_call(method, data)

    state_dir = tmp_path / "state"
    db_path = tmp_path / "cache.db"

    # Run 1: initial seed GETs fail repeatedly, exhausting retries
    code1 = run_walk(
        state_dir=state_dir,
        db_path=db_path,
        delay_seconds=1.0,
        transport=failing_call,
        sleep=_noop_sleep,
        scanner=lambda: False,
    )
    assert code1 == EXIT_RETRY_STORM

    # Page 1 is marked retry_scheduled, with empty (unknown) boundaries and row_count=0
    ledger = SpellingLedger(state_dir / "ledger.sqlite")
    try:
        p1 = ledger.get_page(1)
        assert p1 is not None
        assert p1["state"] == "retry_scheduled"
        assert p1["start_headword"] == ""
        assert p1["end_headword"] == ""
        assert p1["row_count"] == 0
    finally:
        ledger.close()

    # Run 2: restart with healthy server; must navigate fresh start, avoid resume_mismatch, and succeed
    server2 = MockULIFServer()
    code2 = run_walk(
        state_dir=state_dir,
        db_path=db_path,
        delay_seconds=1.0,
        transport=server2,
        sleep=_noop_sleep,
        scanner=lambda: False,
    )
    assert code2 == EXIT_OK

    ledger = SpellingLedger(state_dir / "ledger.sqlite")
    try:
        p1_after = ledger.get_page(1)
        assert p1_after is not None
        assert p1_after["state"] == "completed"
        assert p1_after["start_headword"] == "ду́же"
        assert p1_after["end_headword"] == "замо́к"
        assert p1_after["row_count"] == 3
    finally:
        ledger.close()


def test_mid_walk_offset_reseed_stops_for_drift(tmp_path: Path):
    """A mid-walk reseed whose search matches no placement stops before pagination."""
    state_dir = tmp_path / "state"
    db_path = tmp_path / "cache.db"

    # Server fails page 2 row 1 with 500 (triggering reseed), offsets search, and fails first reseed nextpage with 500
    server = MockULIFServer(
        search_offsets=True,
        fail_page2_row1_500_times=1,
        fail_nextpage_500_times=1,
    )
    code = run_walk(
        state_dir=state_dir,
        db_path=db_path,
        delay_seconds=1.0,
        transport=server,
        sleep=_noop_sleep,
        scanner=lambda: False,
    )
    assert code == EXIT_USAGE

    ledger = SpellingLedger(state_dir / "ledger.sqlite")
    try:
        p2 = ledger.get_page(2)
        assert p2 is not None
        assert p2["error"] == "resume_mismatch"
    finally:
        ledger.close()


def test_mid_walk_contradictory_reseed_stops_before_pagination(tmp_path: Path):
    """A contradictory mid-walk reseed stops. It does not burn next-page retries."""
    state_dir = tmp_path / "state"
    db_path = tmp_path / "cache.db"

    # Server fails page 2 row 1 with 500, offsets search, and fails all reseed nextpage attempts with 500
    server = MockULIFServer(
        search_offsets=True,
        fail_page2_row1_500_times=1,
        fail_nextpage_500_times=10,
    )
    code = run_walk(
        state_dir=state_dir,
        db_path=db_path,
        delay_seconds=1.0,
        transport=server,
        sleep=_noop_sleep,
        scanner=lambda: False,
    )
    assert code == EXIT_USAGE

    ledger = SpellingLedger(state_dir / "ledger.sqlite")
    try:
        p2 = ledger.get_page(2)
        assert p2 is not None
        assert p2["error"] == "resume_mismatch"
    finally:
        ledger.close()


def test_unknown_control_is_recorded_and_counted(tmp_path: Path):
    server = MockULIFServer(inject_unknown_control=True)
    state_dir = tmp_path / "state"
    db_path = tmp_path / "cache.db"

    code = run_walk(
        state_dir=state_dir,
        db_path=db_path,
        delay_seconds=1.0,
        transport=server,
        sleep=_noop_sleep,
        scanner=lambda: False,
    )
    assert code == EXIT_OK

    ledger = SpellingLedger(state_dir / "ledger.sqlite")
    try:
        row = ledger.conn.execute(
            "SELECT unknown_controls FROM register_rows WHERE page_num = 1 AND row_index = 1"
        ).fetchone()
        assert row is not None
        assert "custom_submit" in row["unknown_controls"]

        st = status_text(ledger, delay_seconds=1.0, state_dir=state_dir, mode="walk")
        assert "unknown_control_entries=1" in st
    finally:
        ledger.close()


def test_register_size_change_mid_walk_is_reported_in_status(tmp_path: Path):
    # Page 1 has 8, Page 2 changes to 9
    server = MockULIFServer(page1_size=8, page2_size=9, page3_size=9)
    state_dir = tmp_path / "state"
    db_path = tmp_path / "cache.db"

    code = run_walk(
        state_dir=state_dir,
        db_path=db_path,
        delay_seconds=1.0,
        transport=server,
        sleep=_noop_sleep,
        scanner=lambda: False,
    )
    assert code == EXIT_OK

    ledger = SpellingLedger(state_dir / "ledger.sqlite")
    try:
        st = status_text(ledger, delay_seconds=1.0, state_dir=state_dir, mode="walk")
        assert "register_size_changes=1" in st
        assert "register_size=9" in st

        changes = json.loads(ledger.meta("register_size_changes", "[]"))
        assert len(changes) == 1
        assert changes[0]["old"] == 8
        assert changes[0]["new"] == 9
    finally:
        ledger.close()


def test_http_403_stops_with_exit_forbidden(tmp_path: Path):
    server = MockULIFServer(fail_with_403=True)
    state_dir = tmp_path / "state"
    db_path = tmp_path / "cache.db"

    code = run_walk(
        state_dir=state_dir,
        db_path=db_path,
        delay_seconds=1.0,
        transport=server,
        sleep=_noop_sleep,
        scanner=lambda: False,
    )
    assert code == EXIT_FORBIDDEN


def test_lock_refuses_second_runner(tmp_path: Path):
    state_dir = tmp_path / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    lock = RunnerLock(state_dir, break_stale=False, scanner=lambda: False)
    lock.acquire()
    try:
        server = MockULIFServer()
        db_path = tmp_path / "cache.db"

        with pytest.raises(SystemExit) as excinfo:
            run_walk(
                state_dir=state_dir,
                db_path=db_path,
                delay_seconds=1.0,
                transport=server,
                sleep=_noop_sleep,
                scanner=lambda: False,
            )
        assert "runner lock held by live pid" in str(excinfo.value)
    finally:
        lock.release()


def test_identical_hash_group_not_rewritten_differing_hash_replaced(tmp_path: Path):
    server = MockULIFServer()
    state_dir = tmp_path / "state"
    db_path = tmp_path / "cache.db"

    # Run 1
    run_walk(
        state_dir=state_dir,
        db_path=db_path,
        delay_seconds=1.0,
        transport=server,
        sleep=_noop_sleep,
        scanner=lambda: False,
    )

    ledger1 = SpellingLedger(state_dir / "ledger.sqlite")
    try:
        st1 = status_text(ledger1, delay_seconds=1.0, state_dir=state_dir, mode="walk")
        assert "differing_groups=0" in st1
    finally:
        ledger1.close()

    # Modify one content_sha256 in db to simulate a difference
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("UPDATE ulif_dictua_entries SET content_sha256 = 'fake_hash' WHERE normalized_query = 'дуже'")
        conn.commit()
    finally:
        conn.close()

    # Create fresh ledger to re-walk against modified DB
    state_dir2 = tmp_path / "state2"
    server2 = MockULIFServer()
    run_walk(
        state_dir=state_dir2,
        db_path=db_path,
        delay_seconds=1.0,
        transport=server2,
        sleep=_noop_sleep,
        scanner=lambda: False,
    )

    ledger2 = SpellingLedger(state_dir2 / "ledger.sqlite")
    try:
        st2 = status_text(ledger2, delay_seconds=1.0, state_dir=state_dir2, mode="walk")
        # 'дуже' differed and was counted in differing_groups
        assert "differing_groups=1" in st2
    finally:
        ledger2.close()


def test_verify_complete_itemises_deliberately_skipped_row_and_exits_nonzero(tmp_path: Path):
    server = MockULIFServer()
    state_dir = tmp_path / "state"
    db_path = tmp_path / "cache.db"

    run_walk(
        state_dir=state_dir,
        db_path=db_path,
        delay_seconds=1.0,
        transport=server,
        sleep=_noop_sleep,
        scanner=lambda: False,
    )

    ledger = SpellingLedger(state_dir / "ledger.sqlite")
    try:
        # Deliberately set one row to in_progress
        ledger.conn.execute("UPDATE register_rows SET state = 'in_progress' WHERE page_num = 2 AND row_index = 1")
        ledger.conn.commit()
    finally:
        ledger.close()

    code = verify_complete(state_dir=state_dir, db_path=db_path, expected_size=8)
    assert code == EXIT_USAGE


def test_verify_complete_exits_zero_on_complete(tmp_path: Path):
    server = MockULIFServer()
    state_dir = tmp_path / "state"
    db_path = tmp_path / "cache.db"

    run_walk(
        state_dir=state_dir,
        db_path=db_path,
        delay_seconds=1.0,
        transport=server,
        sleep=_noop_sleep,
        scanner=lambda: False,
    )

    code = verify_complete(state_dir=state_dir, db_path=db_path, expected_size=8)
    assert code == EXIT_OK


def test_status_on_empty_walk_ledger_prints_complete_not_started(tmp_path: Path):
    state_dir = tmp_path / "empty_state"
    state_dir.mkdir(parents=True)
    ledger = SpellingLedger(state_dir / "ledger.sqlite")
    try:
        ledger.set_meta("mode", "walk")
        st = status_text(ledger, delay_seconds=1.0, state_dir=state_dir, mode="walk")
        assert "complete=not_started" in st
        assert "pages_done=0" in st
    finally:
        ledger.close()


def test_stderr_progress_line_contains_no_ukrainian_characters(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    server = MockULIFServer()
    state_dir = tmp_path / "state"
    db_path = tmp_path / "cache.db"

    run_walk(
        state_dir=state_dir,
        db_path=db_path,
        delay_seconds=1.0,
        transport=server,
        sleep=_noop_sleep,
        scanner=lambda: False,
        quiet=False,
    )

    captured = capsys.readouterr()
    progress_lines = [line for line in captured.err.splitlines() if "page_completed" in line]
    assert len(progress_lines) >= 3
    for line in progress_lines:
        assert line.isascii(), f"Progress line contains non-ASCII characters: {line}"


def test_cli_walk_and_verify_complete_subcommands(tmp_path: Path):
    state_dir = tmp_path / "cli_state"

    res_status = subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.lexicon.runner.fetch_ulif_homonyms",
            "status",
            "--state-dir",
            str(state_dir),
            "--mode",
            "walk",
        ],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert res_status.returncode == 0
    assert "complete=not_started" in res_status.stdout


def test_verify_complete_fails_when_db_entries_deleted(tmp_path: Path):
    server = MockULIFServer()
    state_dir = tmp_path / "state"
    db_path = tmp_path / "cache.db"

    run_walk(
        state_dir=state_dir,
        db_path=db_path,
        delay_seconds=1.0,
        transport=server,
        sleep=_noop_sleep,
        scanner=lambda: False,
    )

    # Verifies complete when intact
    assert verify_complete(state_dir=state_dir, db_path=db_path, expected_size=8) == EXIT_OK

    # Delete entries from ulif_dictua_entries in database
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("DELETE FROM ulif_dictua_entries")
        conn.commit()
    finally:
        conn.close()

    # verify_complete must fail and report missing entries
    code = verify_complete(state_dir=state_dir, db_path=db_path, expected_size=8)
    assert code == EXIT_USAGE


def test_verify_complete_fails_on_page_continuity_gap(tmp_path: Path):
    server = MockULIFServer()
    state_dir = tmp_path / "state"
    db_path = tmp_path / "cache.db"

    run_walk(
        state_dir=state_dir,
        db_path=db_path,
        delay_seconds=1.0,
        transport=server,
        sleep=_noop_sleep,
        scanner=lambda: False,
    )

    # Delete page 2 from register_pages, creating a gap: pages 1, 3
    ledger = SpellingLedger(state_dir / "ledger.sqlite")
    try:
        ledger.conn.execute("DELETE FROM register_pages WHERE page_num = 2")
        ledger.conn.commit()
    finally:
        ledger.close()

    code = verify_complete(state_dir=state_dir, db_path=db_path, expected_size=8)
    assert code == EXIT_USAGE


def test_verify_complete_fails_when_final_page_record_deleted(tmp_path: Path):
    server = MockULIFServer()
    state_dir = tmp_path / "state"
    db_path = tmp_path / "cache.db"

    run_walk(
        state_dir=state_dir,
        db_path=db_path,
        delay_seconds=1.0,
        transport=server,
        sleep=_noop_sleep,
        scanner=lambda: False,
    )

    # Delete page 3 from register_pages (final page)
    ledger = SpellingLedger(state_dir / "ledger.sqlite")
    try:
        ledger.conn.execute("DELETE FROM register_pages WHERE page_num = 3")
        ledger.conn.commit()
    finally:
        ledger.close()

    # verify_complete must fail because page 3 rows have no completed page record
    code = verify_complete(state_dir=state_dir, db_path=db_path, expected_size=8)
    assert code == EXIT_USAGE


def test_exhausted_retries_does_not_corrupt_page_numbering(tmp_path: Path):
    server = MockULIFServer()
    orig_call = server.__call__

    def failing_call(method: str, data: dict[str, str] | None) -> HttpResult:
        if (
            data
            and data.get("__EVENTTARGET") == "ctl00$ContentPlaceHolder1$dgv"
            and data.get("__EVENTARGUMENT") == "Select$0"
        ):
            return HttpResult(500, "Internal Server Error", {})
        return orig_call(method, data)

    state_dir = tmp_path / "state"
    db_path = tmp_path / "cache.db"

    code = run_walk(
        state_dir=state_dir,
        db_path=db_path,
        delay_seconds=1.0,
        transport=failing_call,
        sleep=_noop_sleep,
        scanner=lambda: False,
    )
    # Must exit non-zero due to exhausted retries
    assert code != EXIT_OK

    ledger = SpellingLedger(state_dir / "ledger.sqlite")
    try:
        pages = list(ledger.conn.execute("SELECT page_num, state FROM register_pages").fetchall())
        # Exactly 1 page must be recorded, not 4 pages!
        assert len(pages) == 1
        assert pages[0][0] == 1
        assert pages[0][1] == "retry_scheduled"

        rows = list(ledger.conn.execute("SELECT page_num, row_index FROM register_rows").fetchall())
        # Only page 1 rows (3 rows), not 11 rows!
        assert len(rows) == 3
        for r in rows:
            assert r[0] == 1
    finally:
        ledger.close()


def test_invalid_next_page_html_does_not_finish_with_exit_zero(tmp_path: Path):
    server = MockULIFServer()
    orig_call = server.__call__

    def invalid_next_call(method: str, data: dict[str, str] | None) -> HttpResult:
        if data and ("ctl00$ContentPlaceHolder1$nextpage.x" in data or "ctl00$ContentPlaceHolder1$nextpage" in data):
            # Return HTTP 200 with temporary unavailability page (no register table)
            return HttpResult(200, "<html><body>Service Temporarily Unavailable</body></html>", {})
        return orig_call(method, data)

    state_dir = tmp_path / "state"
    db_path = tmp_path / "cache.db"

    code = run_walk(
        state_dir=state_dir,
        db_path=db_path,
        delay_seconds=1.0,
        transport=invalid_next_call,
        sleep=_noop_sleep,
        scanner=lambda: False,
    )
    # Must exit non-zero (EXIT_USAGE)
    assert code == EXIT_USAGE

    ledger = SpellingLedger(state_dir / "ledger.sqlite")
    try:
        # Page 1 must NOT be marked completed
        p1 = ledger.get_page(1)
        assert p1 is not None
        assert p1["state"] == "retry_scheduled"
        assert p1["error"] == "invalid_next_page"

        # Straddling homonym group on rows[-1] (замо́к) must NOT be committed yet
        conn = sqlite3.connect(db_path)
        try:
            entries = conn.execute("SELECT normalized_query FROM ulif_dictua_entries").fetchall()
            entry_words = {e[0] for e in entries}
            # 'дуже' was committed because next word was 'замок' (spelling changed)
            assert "дуже" in entry_words
            # 'замок' should NOT have been committed yet because it was the trailing group!
            assert "замок" not in entry_words
        finally:
            conn.close()
    finally:
        ledger.close()


# Live ledger rows at the 2026-09-25 interruption (#8400): the homonym
# ``порива́ння`` ends page 6931 and starts page 6932.
_BOUNDARY_PAGE_6931 = [
    ("порекомендува́тися", "порекомендуватися"),
    ("по-ремісни́цьки", "по-ремісницьки"),
    ("по-ремісни́цькому", "по-ремісницькому"),
    ("поре́мствувати", "поремствувати"),
    ("по́рений", "порений"),
    ("по́рений", "порений"),
    ("поренча́та", "поренчата"),
    ("поре́п", "пореп"),
    ("поре́паний", "порепаний"),
    ("поре́патися", "порепатися"),
    ("порепетува́ти", "порепетувати"),
    ("порефо́рмений", "пореформений"),
    ("по-реформі́стськи", "по-реформістськи"),
    ("по-реформі́стському", "по-реформістському"),
    ("порешети́ти", "порешетити"),
    ("порешети́тися", "порешетитися"),
    ("пореше́чений", "порешечений"),
    ("поржаві́лий", "поржавілий"),
    ("поржаві́ти", "поржавіти"),
    ("поржа́влений", "поржавлений"),
    ("пориба́лити", "порибалити"),
    ("по-ри́б'ячому", "по-риб'ячому"),
    ("пори́в", "порив"),
    ("пори́в", "порив"),
    ("порива́ння", "поривання"),
]
_BOUNDARY_PAGE_6932 = [
    ("порива́ння", "поривання"),
    ("порива́ти", "поривати"),
    ("порива́ти", "поривати"),
    ("порива́ти", "поривати"),
    ("порива́тися", "пориватися"),
    ("порива́тися", "пориватися"),
    ("порива́ч", "поривач"),
    ("пори́вний", "поривний"),
    ("поривни́й", "поривний"),
    ("пори́вність", "поривність"),
    ("пори́вно", "поривно"),
    ("пори́вчастий", "поривчастий"),
    ("пори́вчастість", "поривчастість"),
    ("пори́вчасто", "поривчасто"),
    ("пори́вчатий", "поривчатий"),
    ("пори́вчатість", "поривчатість"),
    ("пори́вчато", "поривчато"),
    ("порида́ти", "поридати"),
    ("порижі́лий", "порижілий"),
    ("порижі́ти", "порижіти"),
    ("по́риз", "пориз"),
    ("по-ри́зьки", "по-ризьки"),
    ("по-ри́зькому", "по-ризькому"),
    ("По́рик", "порик"),
    ("пори́кувати", "порикувати"),
]
_BOUNDARY_WORDS = [stressed for stressed, _ in _BOUNDARY_PAGE_6931 + _BOUNDARY_PAGE_6932]
_BOUNDARY_GLOBAL = 6931 * 25  # canonical index of page 6932 row 0


def _seed_boundary_ledger(path: Path, *, target_rows: bool = True) -> SpellingLedger:
    ledger = SpellingLedger(path)
    ledger.ensure_page(6931, start_headword="порекомендува́тися", end_headword="порива́ння", row_count=25)
    ledger.mark_page(6931, "completed")
    ledger.ensure_page(
        6932,
        start_headword="порива́ння",
        end_headword="пори́кувати" if target_rows else "",
        row_count=25 if target_rows else 0,
    )
    pages = [(6931, _BOUNDARY_PAGE_6931)] + ([(6932, _BOUNDARY_PAGE_6932)] if target_rows else [])
    for page, rows in pages:
        for index, (stressed, normalized) in enumerate(rows):
            ledger.ensure_row(
                page, index, select_arg=f"Select${index}", stressed_headword=stressed, normalized_spelling=normalized
            )
            if page == 6931 or index < 10:
                ledger.mark_row(page, index, "completed")
    return ledger


def _boundary_window(offset: int) -> list[dict[str, str]]:
    start = len(_BOUNDARY_PAGE_6931) - offset
    return parse_register_list(_register_html(_BOUNDARY_WORDS[start : start + 25], "VS-W", register_size=262812))


@pytest.mark.parametrize("offset", [0, 1, 3, 4, 20])
def test_resume_offset_aligns_homonym_across_page_boundary(tmp_path: Path, offset: int):
    ledger = _seed_boundary_ledger(tmp_path / "ledger.sqlite")
    try:
        rows = _boundary_window(offset)
        assert len(rows) == 25
        # At k=0 the window holds only page 6932's homonym, not page 6931's.
        anchors = ((6932, 0), (6931, 24)) if offset else ((6932, 0),)
        for anchor_page, anchor_index in anchors:
            assert (
                _resume_window_offset(
                    ledger,
                    rows,
                    target_page=6932,
                    anchor_headword="порива́ння",
                    anchor_page=anchor_page,
                    anchor_index=anchor_index,
                )
                == offset
            )
    finally:
        ledger.close()


def test_resume_offset_stays_none_when_two_homonym_alignments_agree(tmp_path: Path):
    # Without page 6932 rows, the window starting at the first homonym is
    # consistent both at k=0 and k=1, so neither may be chosen.
    ledger = _seed_boundary_ledger(tmp_path / "ledger.sqlite", target_rows=False)
    try:
        rows = _boundary_window(1)
        assert [row["stressed"] for row in rows[:2]] == ["порива́ння", "порива́ння"]
        assert (
            _resume_window_offset(
                ledger, rows, target_page=6932, anchor_headword="порива́ння", anchor_page=6932, anchor_index=0
            )
            is None
        )
    finally:
        ledger.close()


def test_resume_offset_homonym_window_with_drift_is_rejected(tmp_path: Path):
    ledger = _seed_boundary_ledger(tmp_path / "ledger.sqlite")
    try:
        drifted = _boundary_window(3)
        drifted[10] = {**drifted[10], "stressed": "поривни́ця", "unstressed": "поривниця"}
        with pytest.raises(ulif_walk.ResumeMismatchError):
            _resume_window_offset(
                ledger, drifted, target_page=6932, anchor_headword="порива́ння", anchor_page=6932, anchor_index=0
            )
        single = _boundary_window(0)
        single[5] = {**single[5], "stressed": "поривни́ця", "unstressed": "поривниця"}
        with pytest.raises(ulif_walk.ResumeMismatchError, match="page 6932 row 5"):
            _resume_window_offset(
                ledger, single, target_page=6932, anchor_headword="порива́ння", anchor_page=6932, anchor_index=0
            )
    finally:
        ledger.close()


@pytest.mark.parametrize("offset", [0, 3, 20])
def test_reseed_at_homonym_page_boundary_skips_fast_forward(tmp_path: Path, capsys, offset: int):
    # The operator's live case: page 6932 has its 25 rows recorded, so the
    # direct search settles the homonym alignment (k=3) without pagination.
    ledger = _seed_boundary_ledger(tmp_path / "ledger.sqlite")
    cache = ulif_walk.prepare_database(tmp_path / "cache.db")
    requests: list[tuple[str, dict[str, str] | None]] = []

    def transport(method: str, data: dict[str, str] | None) -> HttpResult:
        requests.append((method, data))
        if method == "GET":
            return HttpResult(200, _register_html([], "SEED", register_size=262812), {})
        assert data is not None
        assert "ctl00$ContentPlaceHolder1$search.x" in data, "only direct searches are allowed"
        assert data["ctl00$ContentPlaceHolder1$tsearch"] == "порива́ння"
        start = len(_BOUNDARY_PAGE_6931) - offset
        return HttpResult(200, _register_html(_BOUNDARY_WORDS[start : start + 25], "VS-W", register_size=262812), {})

    client = ulif_walk.PoliteClient(transport, delay_seconds=1, sleep=_noop_sleep)
    try:
        _, rows, landed_offset = ulif_walk._reseed_to_page(client, ledger, cache, target_page=6932, start_headword="а")
    finally:
        cache.close()
        ledger.close()
    assert landed_offset == offset
    assert [row["stressed"] for row in rows[max(offset - 1, 0) : offset + 1]] == ["порива́ння"] * (2 if offset else 1)
    assert [method for method, _ in requests] == ["GET", "POST"]
    err = capsys.readouterr().err
    assert f"direct search page 6932, k={offset}" in err
    assert "fast-forward" not in err


_RUN_HEAD = "порива́ння"


def _run_pages(run: int) -> tuple[list[str], list[str], list[str]]:
    """Previous, target and next pages; the target opens with ``run`` identical headwords."""
    previous = [f"a{i:02d}" for i in range(25)]
    target = [_RUN_HEAD] * run + [f"t{i:02d}" for i in range(25 - run)]
    following = [f"n{i:02d}" for i in range(25)]
    return previous, target, following


def _seed_run_ledger(path: Path, *, run: int, recorded: int, pin: bool) -> SpellingLedger:
    """Page 2 is the target. ``recorded`` leading run rows exist; ``pin`` also records every other row."""
    previous, target, _ = _run_pages(run)
    ledger = SpellingLedger(path)
    ledger.ensure_page(1, start_headword=previous[0], end_headword=previous[-1], row_count=25)
    ledger.ensure_page(2, start_headword=_RUN_HEAD)
    for page, words in ((1, previous), (2, target)):
        for index, word in enumerate(words):
            if page == 2 and index >= recorded and not (pin and index >= run):
                continue
            ledger.ensure_row(
                page,
                index,
                select_arg=f"Select${index}",
                stressed_headword=word,
                normalized_spelling=normalize_ulif_spelling(word),
            )
    return ledger


def _run_window(run: int, landing: int) -> list[dict[str, str]]:
    """The 25-row window that starts at target row ``landing`` (the search lands inside the homonym run)."""
    _, target, following = _run_pages(run)
    return parse_register_list(_register_html((target + following)[landing : landing + 25], "VS-R", register_size=100))


_RUN_CASES = [(run, landing) for run in (2, 3) for landing in range(run)]


@pytest.mark.parametrize(("run", "landing"), _RUN_CASES)
@pytest.mark.parametrize("recorded", [0, 1, 2])
def test_resume_offset_needs_a_distinct_recorded_row_in_a_homonym_run(
    tmp_path: Path, run: int, landing: int, recorded: int
):
    # #8400 review: with rows 0 and 1 both the anchor and only row 0 recorded, a search that
    # lands at row 1 showed one anchor and was accepted as k=0, shifting every later row.
    ledger = _seed_run_ledger(tmp_path / "ledger.sqlite", run=run, recorded=recorded, pin=False)
    try:
        assert (
            _resume_window_offset(
                ledger,
                _run_window(run, landing),
                target_page=2,
                anchor_headword=_RUN_HEAD,
                anchor_page=2,
                anchor_index=0,
            )
            is None
        )
    finally:
        ledger.close()


@pytest.mark.parametrize(("run", "landing"), _RUN_CASES)
def test_resume_offset_pinned_by_distinct_row_only_at_the_true_start(tmp_path: Path, run: int, landing: int):
    ledger = _seed_run_ledger(tmp_path / "ledger.sqlite", run=run, recorded=run, pin=True)
    try:
        offset = _resume_window_offset(
            ledger,
            _run_window(run, landing),
            target_page=2,
            anchor_headword=_RUN_HEAD,
            anchor_page=2,
            anchor_index=0,
        )
    finally:
        ledger.close()
    # Every row is recorded, so the landing is the only consistent start.
    # A positive landing is inside the page: the walker offset is negative.
    assert offset == -landing


def test_resume_offset_previous_page_rows_pin_a_shifted_window(tmp_path: Path):
    ledger = _seed_run_ledger(tmp_path / "ledger.sqlite", run=2, recorded=0, pin=False)
    try:
        previous, target, following = _run_pages(2)
        window = parse_register_list(_register_html((previous + target + following)[22:47], "VS-R", register_size=100))
        # Previous-page rows rule out the other previous-page starts, but an inside-page
        # landing overlaps none of the unrecorded target rows, so the start is not unique.
        assert (
            _resume_window_offset(
                ledger, window, target_page=2, anchor_headword=_RUN_HEAD, anchor_page=2, anchor_index=0
            )
            is None
        )
        for index, word in enumerate(target):
            ledger.ensure_row(
                2,
                index,
                select_arg=f"Select${index}",
                stressed_headword=word,
                normalized_spelling=normalize_ulif_spelling(word),
            )
        assert (
            _resume_window_offset(
                ledger, window, target_page=2, anchor_headword=_RUN_HEAD, anchor_page=2, anchor_index=0
            )
            == 3
        )
    finally:
        ledger.close()


def test_resume_offset_raises_for_clear_drift_but_not_inside_a_run(tmp_path: Path):
    # A lone anchor followed by a recorded, different row 1 is the target's first row: drift is real.
    ledger = _seed_run_ledger(tmp_path / "ledger.sqlite", run=1, recorded=1, pin=True)
    try:
        drifted = _run_window(1, 0)
        drifted[7] = {**drifted[7], "stressed": "zz", "unstressed": "zz"}
        with pytest.raises(ulif_walk.ResumeMismatchError, match="page 2 row 7"):
            _resume_window_offset(
                ledger, drifted, target_page=2, anchor_headword=_RUN_HEAD, anchor_page=2, anchor_index=0
            )
    finally:
        ledger.close()
    # The same disagreement inside a repeated run is still drift when every row is recorded:
    # no placement matches, and the window overlaps those rows.
    ledger = _seed_run_ledger(tmp_path / "ledger2.sqlite", run=2, recorded=2, pin=True)
    try:
        inside = _run_window(2, 1)
        inside[7] = {**inside[7], "stressed": "zz", "unstressed": "zz"}
        with pytest.raises(ulif_walk.ResumeMismatchError):
            _resume_window_offset(
                ledger, inside, target_page=2, anchor_headword=_RUN_HEAD, anchor_page=2, anchor_index=0
            )
    finally:
        ledger.close()


def _ambiguous_boundary_window(kind: str) -> list[str]:
    """Windows whose first two rows are the boundary homonym; page 6932 rows are unrecorded.

    ``target_start``: the window really starts at page 6932 row 0 and page 6932
    itself opens with two ``порива́ння`` rows (review of 40a2172c47).
    ``previous_end``: the window really starts at page 6931 row 24 (k=1).
    Both are the same 25 headwords apart from the tail, and no ledger row tells them apart.
    """
    if kind == "target_start":
        return ["порива́ння", "порива́ння", *(stressed for stressed, _ in _BOUNDARY_PAGE_6932[1:24])]
    return [stressed for stressed, _ in _BOUNDARY_PAGE_6931[-1:] + _BOUNDARY_PAGE_6932[:24]]


@pytest.mark.parametrize("kind", ["target_start", "previous_end"])
def test_reseed_ambiguous_homonym_boundary_fast_forwards_instead_of_guessing(tmp_path: Path, monkeypatch, kind: str):
    ledger = _seed_boundary_ledger(tmp_path / "ledger.sqlite", target_rows=False)
    cache = ulif_walk.prepare_database(tmp_path / "cache.db")
    words = _ambiguous_boundary_window(kind)
    assert words[:2] == ["порива́ння", "порива́ння"]
    requests: list[tuple[str, dict[str, str] | None]] = []

    def transport(method: str, data: dict[str, str] | None) -> HttpResult:
        requests.append((method, data))
        if method == "GET":
            return HttpResult(200, _register_html([], "SEED", register_size=262812), {})
        assert data is not None
        assert data["ctl00$ContentPlaceHolder1$tsearch"] == "порива́ння", "no previous-page anchor search"
        return HttpResult(200, _register_html(words, "VS-W", register_size=262812), {})

    fast_forwarded: list[int] = []

    def fake_fast_forward(client, ledger, cache, seed_tokens, start_headword, target_page, *, quiet=False):
        fast_forwarded.append(target_page)
        html = _register_html(_BOUNDARY_WORDS[25 : 25 + 25], "VS-FF", register_size=262812)
        return html, parse_register_list(html)

    monkeypatch.setattr(ulif_walk, "_fast_forward_to_page", fake_fast_forward)
    client = ulif_walk.PoliteClient(transport, delay_seconds=1, sleep=_noop_sleep)
    try:
        _, rows, landed_offset = ulif_walk._reseed_to_page(client, ledger, cache, target_page=6932, start_headword="а")
    finally:
        cache.close()
        ledger.close()
    assert fast_forwarded == [6932]
    assert landed_offset == 0
    assert rows[0]["stressed"] == "порива́ння"
    assert [method for method, _ in requests] == ["GET", "POST"]
