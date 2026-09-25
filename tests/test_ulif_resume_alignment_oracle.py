"""Brute-force oracle for the one ULIF resume alignment decision (#8400).

The oracle enumerates consistent starts with its own nested loops. It does not
call the production function to decide what the answer should be.
"""

from __future__ import annotations

import itertools
from pathlib import Path

import pytest

from scripts.lexicon.runner import fetch_ulif_homonyms as ulif_walk
from scripts.lexicon.runner.fetch_ulif_homonyms import (
    HttpResult,
    PoliteClient,
    ResumeMismatchError,
    SpellingLedger,
    _reseed_to_page,
    _resume_window_offset,
    align_resume_window,
    parse_register_list,
)

_ALPHABET = ("A", "B", "C")


def _brute_consistent(
    window: tuple[str, ...],
    *,
    page_size: int,
    target_rows: dict[int, str],
    previous_rows: dict[int, str],
    page_row_count: int | None,
    end_headword: str | None,
    target_page: int,
) -> tuple[set[int], bool]:
    """Return (consistent starts, whether any fitting start overlaps a recorded row)."""
    known = page_row_count if page_row_count and page_row_count > 0 else None
    limit = known if known is not None else page_size
    short = len(window) < page_size
    end = end_headword or None
    consistent: set[int] = set()
    overlapped = False
    window_length = len(window)
    previous_get = previous_rows.get
    target_get = target_rows.get
    for origin in range(-page_size if target_page > 1 else 0, limit):
        last = origin + window_length - 1
        fits = True
        if short and known is not None and last != known - 1:
            fits = False
        if last >= limit and (short or (known is not None and known < page_size)):
            fits = False
        if not fits:
            continue
        matches = True
        overlaps = False
        for index, word in enumerate(window):
            coord = origin + index
            expected = None
            if coord < 0:
                expected = previous_get(page_size + coord)
            elif coord < limit:
                expected = target_get(coord)
            if expected is None:
                continue
            overlaps = True
            if expected != word:
                matches = False
        if end is not None and origin <= limit - 1 <= last and window[limit - 1 - origin] != end:
            matches = False
        if overlaps:
            overlapped = True
        if matches:
            consistent.add(origin)
    return consistent, overlapped


def _assert_matches_oracle(
    window: tuple[str, ...],
    *,
    true_start: int,
    page_size: int,
    target_rows: dict[int, str],
    previous_rows: dict[int, str] | None = None,
    page_row_count: int | None = None,
    end_headword: str | None = None,
    target_page: int = 2,
) -> None:
    previous = previous_rows or {}
    consistent, overlapped = _brute_consistent(
        window,
        page_size=page_size,
        target_rows=target_rows,
        previous_rows=previous,
        page_row_count=page_row_count,
        end_headword=end_headword,
        target_page=target_page,
    )
    try:
        got: int | str | None = align_resume_window(
            window,
            page_size=page_size,
            target_rows=target_rows,
            previous_rows=previous,
            page_row_count=page_row_count,
            end_headword=end_headword,
            target_page=target_page,
        )
    except ResumeMismatchError:
        got = "raise"
    if isinstance(got, int):
        assert got == true_start, (got, true_start, consistent, window)
    if consistent == {true_start}:
        assert got == true_start
    elif len(consistent) > 1:
        assert got is None
    elif overlapped:
        assert got == "raise"
    else:
        assert got is None


def test_repeated_pair_landing_inside_is_not_taken_as_page_start() -> None:
    """Review of 18c658e11c: A,A,B,B with only rows 0 and 2 recorded, landed at row 1.

    The later B matches recorded row 2 under the wrong start as well as the true
    one. Both pending and completed rows are listing data; neither start may win.
    """
    page = ("A", "A", "B", "B", "C", "D", "E", "F")
    window = (*page[1:], "Z")
    recorded = {0: "A", 2: "B"}
    _assert_matches_oracle(window, true_start=1, page_size=8, target_rows=recorded, page_row_count=8)
    assert align_resume_window(window, page_size=8, target_rows=recorded, page_row_count=8) is None


def test_pending_and_completed_rows_both_block_the_shifted_pair(tmp_path: Path) -> None:
    ledger = SpellingLedger(tmp_path / "ledger.sqlite")
    try:
        page = ["A", "A", "B", "B", *[f"X{index:02d}" for index in range(21)]]
        ledger.ensure_page(2, start_headword="A", row_count=25)
        ledger.ensure_row(2, 0, select_arg="Select$0", stressed_headword="A", normalized_spelling="a")
        ledger.ensure_row(2, 2, select_arg="Select$2", stressed_headword="B", normalized_spelling="b")
        ledger.mark_row(2, 2, "completed")
        window = [{"stressed": word, "unstressed": word.lower()} for word in (*page[1:], "Z")]
        assert (
            _resume_window_offset(ledger, window, target_page=2, anchor_headword="A", anchor_page=2, anchor_index=0)
            is None
        )
    finally:
        ledger.close()


def test_short_final_page_does_not_accept_a_shifted_tail_as_the_start(tmp_path: Path) -> None:
    """Review of 18c658e11c: final page A,A,B,C, only row 0 recorded, landed at row 1.

    The tail A,B,C starts with the recorded start and ends with the recorded end.
    The page has 4 rows, so that tail starts at row 1, not row 0.
    """
    window = ("A", "B", "C")
    _assert_matches_oracle(
        window,
        true_start=1,
        page_size=25,
        target_rows={0: "A"},
        page_row_count=4,
        end_headword="C",
    )
    assert align_resume_window(window, page_size=25, target_rows={0: "A"}, page_row_count=4, end_headword="C") == 1
    ledger = SpellingLedger(tmp_path / "ledger.sqlite")
    try:
        ledger.ensure_page(2, start_headword="A", end_headword="C", row_count=4)
        ledger.ensure_row(2, 0, select_arg="Select$0", stressed_headword="A", normalized_spelling="a")
        rows = [{"stressed": word, "unstressed": word.lower()} for word in window]
        assert (
            _resume_window_offset(ledger, rows, target_page=2, anchor_headword="A", anchor_page=2, anchor_index=0) == -1
        )
    finally:
        ledger.close()


@pytest.mark.timeout(300)
def test_exhaustive_alignment_matches_the_brute_force_oracle() -> None:
    """Every page, recorded subset, landing, and fetch-sized window for page sizes 1..6.

    Full windows are ``page_size`` rows and may run off the end of the page.
    Short windows are the final-page tail from the landing through the last row.
    Page sizes 1..3 also vary the previous page the same way.
    """
    cases = 0
    for page_size in range(1, 7):
        pages = list(itertools.product(_ALPHABET, repeat=page_size))
        for page in pages:
            end = page[-1]
            for mask in range(1 << page_size):
                recorded = {index: page[index] for index in range(page_size) if mask & (1 << index)}
                for landing in range(page_size):
                    full = page[landing:] + ("Z",) * landing
                    _assert_matches_oracle(
                        full,
                        true_start=landing,
                        page_size=page_size,
                        target_rows=recorded,
                        page_row_count=page_size,
                        end_headword=end,
                    )
                    cases += 1
                    if landing:
                        tail = page[landing:]
                        _assert_matches_oracle(
                            tail,
                            true_start=landing,
                            page_size=page_size,
                            target_rows=recorded,
                            page_row_count=page_size,
                            end_headword=end,
                        )
                        cases += 1
        if page_size > 3:
            continue
        for previous in pages:
            for page in pages:
                end = page[-1]
                for prev_mask in range(1 << page_size):
                    previous_rows = {index: previous[index] for index in range(page_size) if prev_mask & (1 << index)}
                    for mask in range(1 << page_size):
                        recorded = {index: page[index] for index in range(page_size) if mask & (1 << index)}
                        for landing in range(-page_size, page_size):
                            if landing >= 0:
                                window = page[landing:] + ("Z",) * landing
                            else:
                                window = previous[landing:] + page[: page_size + landing]
                            _assert_matches_oracle(
                                window,
                                true_start=landing,
                                page_size=page_size,
                                target_rows=recorded,
                                previous_rows=previous_rows,
                                page_row_count=page_size,
                                end_headword=end,
                            )
                            cases += 1
                            if landing > 0:
                                _assert_matches_oracle(
                                    page[landing:],
                                    true_start=landing,
                                    page_size=page_size,
                                    target_rows=recorded,
                                    previous_rows=previous_rows,
                                    page_row_count=page_size,
                                    end_headword=end,
                                )
                                cases += 1
    # 593_466 target-only windows (sizes 1..6) plus 379_800 windows that also vary
    # the previous page (sizes 1..3).
    assert cases == 973_266, cases


@pytest.mark.timeout(20)
def test_short_pages_unknown_end_and_matching_next_page_oracle() -> None:
    """Enumerate final-page tails and full windows whose next rows can repeat."""
    cases = 0
    for page_size in range(1, 4):
        for count in range(1, page_size + 1):
            for page in itertools.product(_ALPHABET, repeat=count):
                for mask in range(1 << count):
                    recorded = {index: page[index] for index in range(count) if mask & (1 << index)}
                    for end in (None, "", page[-1]):
                        for landing in range(count):
                            tail = page[landing:]
                            for target_page in (1, 2):
                                _assert_matches_oracle(
                                    tail,
                                    true_start=landing,
                                    page_size=page_size,
                                    target_rows=recorded,
                                    page_row_count=count,
                                    end_headword=end,
                                    target_page=target_page,
                                )
                                cases += 1
                            if count != page_size:
                                continue
                            for next_page in itertools.product(_ALPHABET, repeat=landing):
                                _assert_matches_oracle(
                                    tail + next_page,
                                    true_start=landing,
                                    page_size=page_size,
                                    target_rows=recorded,
                                    page_row_count=count,
                                    end_headword=end,
                                )
                                cases += 1
    assert cases > 8_000


def _register_html(words: tuple[str, ...], *, size: int) -> str:
    rows = "".join(
        '<tr><td><a href="javascript:__doPostBack(&#39;ctl00$ContentPlaceHolder1$dgv&#39;,'
        f'&#39;Select${index}&#39;)">{word}</a></td></tr>'
        for index, word in enumerate(words)
    )
    return (
        '<input type="hidden" name="__VIEWSTATE" value="VS" />'
        '<input type="hidden" name="__VIEWSTATEGENERATOR" value="GEN" />'
        '<input type="hidden" name="__EVENTVALIDATION" value="EV" />'
        f'<table id="ContentPlaceHolder1_dgv">{rows}</table>'
        f'<span id="ContentPlaceHolder1_rlength">Реєстрових слів - {size}</span>'
    )


@pytest.mark.parametrize("terminal_size", [1, 3, 7])
@pytest.mark.parametrize(("previous_suffix", "direct"), [(3, True), (1, False), (0, False)])
def test_previous_page_anchor_handles_short_terminal_page(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, terminal_size: int, previous_suffix: int, direct: bool
) -> None:
    """Exercise anchor choice, +25 conversion, and suffix guard on a short terminal page."""
    previous = tuple(f"p{index:02d}" for index in range(25))
    terminal = tuple(f"t{index:02d}" for index in range(terminal_size))
    window = previous[25 - previous_suffix :] + terminal
    size = 25 + terminal_size  # Not a multiple of the register page size.
    ledger = SpellingLedger(tmp_path / "ledger.sqlite")
    cache = ulif_walk.prepare_database(tmp_path / "cache.db")
    try:
        ledger.ensure_page(1, start_headword=previous[0], end_headword=previous[-1], row_count=25)
        for index, word in enumerate(previous):
            ledger.ensure_row(1, index, select_arg=f"Select${index}", stressed_headword=word, normalized_spelling=word)
        ledger.mark_page(1, "completed")

        searches: list[str] = []

        def transport(method: str, data: dict[str, str] | None) -> HttpResult:
            if method == "GET":
                return HttpResult(200, _register_html((), size=size), {})
            assert data is not None
            searches.append(data["ctl00$ContentPlaceHolder1$tsearch"])
            return HttpResult(200, _register_html(window, size=size), {})

        fast_forwarded: list[int] = []

        def fast_forward(client, ledger, cache, seed_tokens, start_headword, target_page, *, quiet=False):
            fast_forwarded.append(target_page)
            html = _register_html(terminal, size=size)
            return html, parse_register_list(html)

        monkeypatch.setattr(ulif_walk, "_fast_forward_to_page", fast_forward)
        client = PoliteClient(transport, delay_seconds=1, sleep=lambda _seconds: None)
        _, rows, offset = _reseed_to_page(client, ledger, cache, target_page=2, start_headword="p00", quiet=True)
        assert searches == [previous[-1]]
        assert [row["stressed"] for row in rows] == list(window if direct else terminal)
        assert offset == (previous_suffix if direct else 0)
        assert fast_forwarded == ([] if direct else [2])

        if previous_suffix:
            # The oracle's known previous listing locates the raw search start.
            matching = [
                start
                for start in range(25)
                if all(previous[start + i] == word for i, word in enumerate(window) if start + i < 25)
            ]
            assert matching == [25 - previous_suffix]
            assert (
                _resume_window_offset(
                    ledger,
                    [{"stressed": word} for word in window],
                    target_page=1,
                    anchor_headword=previous[-1],
                    anchor_page=1,
                    anchor_index=0,
                    nonterminal_page=True,
                )
                == previous_suffix - 25
            )
    finally:
        cache.close()
        ledger.close()
