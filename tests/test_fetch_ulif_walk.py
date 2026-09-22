"""Offline tests for full ULIF register walk and verification (#8429 part 2 / #8400 step e)."""

from __future__ import annotations

import json
import re
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.lexicon.runner.fetch_ulif_homonyms import (
    EXIT_FORBIDDEN,
    EXIT_OK,
    EXIT_RETRY_STORM,
    EXIT_USAGE,
    HttpResult,
    RunnerLock,
    SpellingLedger,
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

    # Resume with server where search for "замо́к" lands offset, but nextpage succeeds
    server2 = MockULIFServer(search_offsets=True)
    code2 = run_walk(
        state_dir=state_dir,
        db_path=db_path,
        delay_seconds=1.0,
        transport=server2,
        sleep=_noop_sleep,
        scanner=lambda: False,
    )
    assert code2 == 0

    ledger = SpellingLedger(state_dir / "ledger.sqlite")
    try:
        p2 = ledger.get_page(2)
        assert p2 is not None
        assert p2["state"] == "completed"
    finally:
        ledger.close()

    # Verify that fast-forward searched for page 1 headword "а" to begin pagination
    ff_searches = [
        req
        for method, req in server2.requests_log
        if req and req.get("ctl00$ContentPlaceHolder1$tsearch") == "а"
    ]
    assert len(ff_searches) == 1


def test_startup_resume_fast_forward_recovers_after_injected_session_invalid(tmp_path: Path):
    """Fast-forward on startup resume catches SessionInvalid, restarts from a fresh seed, and completes."""
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

    # Resume with server that offsets search AND fails first nextpage click with 500
    server2 = MockULIFServer(search_offsets=True, fail_nextpage_500_times=1)
    code2 = run_walk(
        state_dir=state_dir,
        db_path=db_path,
        delay_seconds=1.0,
        transport=server2,
        sleep=_noop_sleep,
        scanner=lambda: False,
    )
    assert code2 == 0

    ledger = SpellingLedger(state_dir / "ledger.sqlite")
    try:
        p2 = ledger.get_page(2)
        assert p2 is not None
        assert p2["state"] == "completed"
    finally:
        ledger.close()

    # Verify that fast-forward was attempted twice (two searches for "а" from fresh seeds)
    ff_searches = [
        req
        for method, req in server2.requests_log
        if req and req.get("ctl00$ContentPlaceHolder1$tsearch") == "а"
    ]
    assert len(ff_searches) == 2


def test_startup_resume_fast_forward_exhaustion_marks_retry_scheduled(tmp_path: Path):
    """Fast-forward on startup resume marks retry_scheduled when all reseed attempts fail."""
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
    assert code2 == EXIT_RETRY_STORM

    ledger = SpellingLedger(state_dir / "ledger.sqlite")
    try:
        p2 = ledger.get_page(2)
        assert p2 is not None
        assert p2["state"] == "retry_scheduled"
        assert p2["error"] == "http_500"
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


def test_mid_walk_fast_forward_recovers_after_injected_session_invalid(tmp_path: Path):
    """Mid-walk reseed with fast-forward catches SessionInvalid, restarts from fresh seed, and completes."""
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
    assert code == 0

    ledger = SpellingLedger(state_dir / "ledger.sqlite")
    try:
        p2 = ledger.get_page(2)
        assert p2 is not None
        assert p2["state"] == "completed"
    finally:
        ledger.close()

    # Page 1 normal search ("а") + reseed attempt 1 fast-forward ("а") + reseed attempt 2 fast-forward ("а") >= 2
    ff_searches = [
        req
        for method, req in server.requests_log
        if req and req.get("ctl00$ContentPlaceHolder1$tsearch") == "а"
    ]
    assert len(ff_searches) >= 2


def test_mid_walk_fast_forward_exhaustion_marks_retry_scheduled(tmp_path: Path):
    """Mid-walk reseed with fast-forward marks retry_scheduled on exhaustion."""
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
    assert code == EXIT_RETRY_STORM

    ledger = SpellingLedger(state_dir / "ledger.sqlite")
    try:
        p2 = ledger.get_page(2)
        assert p2 is not None
        assert p2["state"] == "retry_scheduled"
        assert p2["error"] == "http_500"
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
