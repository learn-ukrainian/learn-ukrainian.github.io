"""Brute-force oracle for the one ULIF resume alignment decision (#8400).

The oracle enumerates consistent starts with its own nested loops. It does not
call the production function to decide what the answer should be.
"""

from __future__ import annotations

import itertools
from pathlib import Path

import pytest

from scripts.lexicon.runner.fetch_ulif_homonyms import (
    ResumeMismatchError,
    SpellingLedger,
    _resume_window_offset,
    align_resume_window,
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
) -> tuple[set[int], bool]:
    """Return (consistent starts, whether any fitting start overlaps a recorded row)."""
    known = page_row_count if page_row_count and page_row_count > 0 else None
    limit = known if known is not None else page_size
    short = len(window) < page_size
    end = end_headword or None
    consistent: set[int] = set()
    overlapped = False
    for origin in range(-page_size, limit):
        last = origin + len(window) - 1
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
                expected = previous_rows.get(page_size + coord)
            elif coord < limit:
                expected = target_rows.get(coord)
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


def _ask(window: tuple[str, ...], **kwargs: object) -> int | str | None:
    try:
        return align_resume_window(window, **kwargs)  # type: ignore[arg-type]
    except ResumeMismatchError:
        return "raise"


def _assert_matches_oracle(
    window: tuple[str, ...],
    *,
    true_start: int,
    page_size: int,
    target_rows: dict[int, str],
    previous_rows: dict[int, str] | None = None,
    page_row_count: int | None = None,
    end_headword: str | None = None,
) -> None:
    previous = previous_rows or {}
    consistent, overlapped = _brute_consistent(
        window,
        page_size=page_size,
        target_rows=target_rows,
        previous_rows=previous,
        page_row_count=page_row_count,
        end_headword=end_headword,
    )
    got = _ask(
        window,
        page_size=page_size,
        target_rows=target_rows,
        previous_rows=previous,
        page_row_count=page_row_count,
        end_headword=end_headword,
    )
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
