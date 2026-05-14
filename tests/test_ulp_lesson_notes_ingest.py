"""Tests for scripts/ingest/ulp_lesson_notes_ingest.py.

Exercises the parser against synthetic fixtures that mirror the real
ULP lesson-notes book quirks identified during the 2026-05-14 ingest run:

- Lesson START anchor requires a SPACE between № and the number
  (``Lesson Notes № 1`` for seasons 1-3, ``Конспект уроку № 1`` for
  seasons 4-6). Page running heads use the no-space variant
  (``Конспект уроку №1``) and MUST be stripped, not promoted to lesson
  starts.
- Cover pages + Зміст (table of contents) before the first lesson start
  must be skipped entirely.
- Page footer + Back to Contents + UkrainianLessons.com + bare page
  numbers + season headers must be stripped from lesson bodies.
- ``Відповіді до вправ`` (Answers to exercises, season 1-3 appendix)
  and ``Key Phrases N-NNN`` (Season 4 appendix) terminate the last
  lesson's body.
- Verified output (chunk_id, title, char_count) lands in the textbooks
  table via the same code path as the live ingest.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from scripts.ingest import ulp_lesson_notes_ingest as ulp

# ---------------------------------------------------------------------------
# Fixtures — synthetic seasons 1 (English heading) and 4 (Ukrainian heading)
# ---------------------------------------------------------------------------

FIXTURE_S1 = """                          UkrainianLessons.com
                   Inspiring resources for learning Ukrainian — UkrainianLessons.com
Back to Contents                                                                       1
                              Ukrainian Lessons Podcast: Season 1




                                            Зміст
Lesson Notes №1: Informal Greetings in Ukrainian                                              5
Lesson Notes №2: Formal Greetings in Ukrainian                                                9



                          Inspiring resources for learning Ukrainian — UkrainianLessons.com
Back to Contents                                                                       2
                                  Ukrainian Lessons Podcast: Season 1


                                            Lesson Notes № 1

       Informal Greetings in Ukrainian
                                         Link to audio: ukrainianlessons.com/episode1




                       Приві́т! Мене́ зва́ти А́нна — Hi! My name is Anna.
                       In this lesson we learn basic informal greetings.

   Dialogue                                                       Привіт!
   Анна: Приві́т!                                The basic informal "Hi!"
   Інна: Приві́т!



                          Inspiring resources for learning Ukrainian — UkrainianLessons.com
Back to Contents                                                                       5
                                  Episode 1 — Informal Greetings in Ukrainian


   Анна: Як спра́ви?                            How are you?
   Інна: Чудо́во!


                                               Lesson Notes № 2

  Formal Greetings in Ukrainian
                                         Link to audio: ukrainianlessons.com/episode2




                          Приві́т! In the second episode of the Ukrainian Lessons Podcast,
                          we are continuing with greetings.

   Dialogue                                            Добрий день! — Hello!
   Анна: До́брий день!                          Formal greeting in Ukrainian.



                                  Відповіді до вправ 1-2

   Exercise 1 answers: ...
"""

FIXTURE_S4 = """                          UkrainianLessons.com
                   Inspiring resources for learning Ukrainian — UkrainianLessons.com
 Back to Contents                                                                       1
                                 Ukrainian Lessons Podcast: Season 4


                                            Зміст
Lesson Notes №121: 10 цікавих фактів про мене                                                5



                          Inspiring resources for learning Ukrainian — UkrainianLessons.com
 Back to Contents                                                                            4
                                 Ukrainian Lessons Podcast: Season 4


                                       Конспект уроку № 121


           10 цікавих фактів про мене
                                        Link to audio: ukrainianlessons.com/episode121




                                                     Вступ

Добрий день! Це Анна, і ви слухаєте Ukrainian Lessons Podcast.

Це — четвертий сезон!



                          Inspiring resources for learning Ukrainian — UkrainianLessons.com
 Back to Contents                                                                            5
                                        Конспект уроку №121
                                      10 цікавих фактів про мене


Я розповім вам 10 цікавих фактів про мене.

Перший факт. Я народилась у Радянському Союзі.



                                       Конспект уроку № 122


                            Друга лекція

                                        Link to audio: ukrainianlessons.com/episode122




                                                     Вступ

Привіт. Це друга лекція.



                                     Key Phrases 4-122

Bonus vocabulary follows...
"""


def _write_fixture(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# Parser-level tests
# ---------------------------------------------------------------------------


def test_parse_book_skips_cover_and_toc(tmp_path: Path) -> None:
    """Cover pages, Зміст (ToC), and pre-first-lesson content must NOT
    enter the lesson list."""
    txt = _write_fixture(tmp_path, "s1.txt", FIXTURE_S1)
    lessons = ulp.parse_book(txt)
    nums = [l.number for l in lessons]
    assert nums == [1, 2], f"expected lessons [1, 2], got {nums}"
    # ToC entries ``Lesson Notes №1:`` (no space) must not have been
    # mistaken for lesson starts.


def test_parse_book_with_space_anchor_seasons_1_3(tmp_path: Path) -> None:
    """Season 1-3 anchor is ``Lesson Notes № N`` with space."""
    txt = _write_fixture(tmp_path, "s1.txt", FIXTURE_S1)
    lessons = ulp.parse_book(txt)
    assert lessons[0].title == "Informal Greetings in Ukrainian"
    assert lessons[1].title == "Formal Greetings in Ukrainian"


def test_parse_book_with_space_anchor_seasons_4_6(tmp_path: Path) -> None:
    """Season 4-6 anchor is ``Конспект уроку № N`` with space — the
    no-space variant ``Конспект уроку №N`` is a page running head and
    must NOT open a new lesson."""
    txt = _write_fixture(tmp_path, "s4.txt", FIXTURE_S4)
    lessons = ulp.parse_book(txt)
    nums = [l.number for l in lessons]
    assert nums == [121, 122], f"expected lessons [121, 122], got {nums}"
    # The running-head ``Конспект уроку №121`` on the second page of
    # lesson 121 must NOT have opened a duplicate lesson — and must not
    # appear in the body either.
    body = lessons[0].render()
    # Be strict: any occurrence in body is a bug.
    assert "Конспект уроку №121" not in body, "running-head leaked into lesson body — page-furniture strip failed"
    assert "Конспект уроку № 121" not in body  # also not the start marker


def test_parse_book_strips_page_furniture(tmp_path: Path) -> None:
    """Footers, Back-to-Contents, season headers, and bare page numbers
    must NOT appear in lesson bodies."""
    txt = _write_fixture(tmp_path, "s1.txt", FIXTURE_S1)
    lessons = ulp.parse_book(txt)
    for lesson in lessons:
        blob = lesson.render()
        assert "Inspiring resources for learning Ukrainian" not in blob
        assert "Back to Contents" not in blob
        assert "Ukrainian Lessons Podcast: Season" not in blob
        # Bare page numbers (single line of digits) — none should land
        for line in blob.split("\n"):
            assert not line.strip().isdigit() or len(line.strip()) > 4


def test_parse_book_strips_episode_running_head(tmp_path: Path) -> None:
    """Season 1-3 running head ``Episode N — Title`` must be stripped."""
    txt = _write_fixture(tmp_path, "s1.txt", FIXTURE_S1)
    lessons = ulp.parse_book(txt)
    body_l1 = lessons[0].render()
    assert "Episode 1 — Informal Greetings" not in body_l1


def test_parse_book_terminates_at_vidpovidi(tmp_path: Path) -> None:
    """``Відповіді до вправ`` (Season 1-3 appendix) finalizes the last
    lesson without absorbing the appendix."""
    txt = _write_fixture(tmp_path, "s1.txt", FIXTURE_S1)
    lessons = ulp.parse_book(txt)
    last_blob = lessons[-1].render()
    assert "Відповіді до вправ" not in last_blob
    assert "Exercise 1 answers" not in last_blob
    # But the real lesson 2 content stays:
    assert "До́брий день" in last_blob


def test_parse_book_terminates_at_key_phrases(tmp_path: Path) -> None:
    """``Key Phrases N-NNN`` (Season 4 appendix) finalizes the last
    lesson without absorbing the appendix."""
    txt = _write_fixture(tmp_path, "s4.txt", FIXTURE_S4)
    lessons = ulp.parse_book(txt)
    last_blob = lessons[-1].render()
    assert "Key Phrases 4-122" not in last_blob
    assert "Bonus vocabulary follows" not in last_blob


def test_parse_book_captures_title_after_marker(tmp_path: Path) -> None:
    """The first non-furniture line after a lesson marker is the title,
    and it does NOT also appear at the head of the rendered body."""
    txt = _write_fixture(tmp_path, "s4.txt", FIXTURE_S4)
    lessons = ulp.parse_book(txt)
    l121 = lessons[0]
    assert l121.title == "10 цікавих фактів про мене"
    # The renderer prepends the title via the header; it should not also
    # appear as a duplicate body line at offset 0.
    rendered = l121.render()
    header_first_line = rendered.split("\n", 1)[0]
    assert header_first_line == "Lesson 121: 10 цікавих фактів про мене"
    # And the next non-empty line is genuine body content, NOT the
    # title repeated.
    body_lines = [ln for ln in rendered.split("\n")[1:] if ln.strip()]
    # First body line should not be the title.
    assert body_lines[0] != l121.title


def test_parse_book_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        ulp.parse_book(tmp_path / "does-not-exist.txt")


def test_parse_book_joins_multiline_title(tmp_path: Path) -> None:
    """PDFs broke long lesson titles across two lines. The parser must
    join them via single space and strip the trailing comma fragment
    (mirrors real lesson #160 in ULP 4-00: ``Василь Стус,\nшістдесятники
    та дисиденти``)."""
    fixture = """                                       Конспект уроку № 160


              Василь Стус,
       шістдесятники та дисиденти
                                         Link to audio: ukrainianlessons.com/episode160




Це лекція про Василя Стуса.
"""
    txt = _write_fixture(tmp_path, "multiline.txt", fixture)
    lessons = ulp.parse_book(txt)
    assert len(lessons) == 1
    assert lessons[0].title == "Василь Стус, шістдесятники та дисиденти", f"got title: {lessons[0].title!r}"
    # Body should still contain real content, not the Link line.
    body = lessons[0].render()
    assert "Це лекція" in body
    assert "Link to audio" not in body


def test_parse_book_link_to_audio_acts_as_title_terminator(
    tmp_path: Path,
) -> None:
    """The Link to audio line MUST NOT be promoted into the title or
    the body."""
    fixture = """                                            Lesson Notes № 1

       Informal Greetings in Ukrainian
                                         Link to audio: ukrainianlessons.com/episode1



Привіт!
"""
    txt = _write_fixture(tmp_path, "link.txt", fixture)
    lessons = ulp.parse_book(txt)
    assert len(lessons) == 1
    assert lessons[0].title == "Informal Greetings in Ukrainian"
    body = lessons[0].render()
    assert "Link to audio" not in body
    assert "ukrainianlessons.com/episode1" not in body
    assert "Привіт!" in body


# ---------------------------------------------------------------------------
# DB round-trip tests
# ---------------------------------------------------------------------------


def _make_textbooks_db(path: Path) -> sqlite3.Connection:
    """Minimal textbooks schema for round-trip tests (no FTS triggers
    needed — we exercise the INSERT layer, not retrieval)."""
    conn = sqlite3.connect(str(path))
    conn.executescript(
        """
        CREATE TABLE textbooks (
            id INTEGER PRIMARY KEY,
            chunk_id TEXT NOT NULL DEFAULT '',
            title TEXT NOT NULL DEFAULT '',
            text TEXT NOT NULL DEFAULT '',
            source_file TEXT NOT NULL DEFAULT '',
            grade TEXT DEFAULT '',
            author TEXT DEFAULT '',
            char_count INTEGER DEFAULT 0
        );
        """
    )
    return conn


def test_ingest_lessons_round_trip(tmp_path: Path) -> None:
    """End-to-end: parse → ingest → SELECT confirms rows are written
    with correct metadata."""
    txt = _write_fixture(tmp_path, "s4.txt", FIXTURE_S4)
    lessons = ulp.parse_book(txt)
    assert len(lessons) == 2

    db_path = tmp_path / "sources.db"
    conn = _make_textbooks_db(db_path)
    book = ulp.BookConfig(
        slug="test",
        source_file="test-ulp-fixture",
        txt_filename="s4.txt",
        season=4,
    )
    inserted, skipped = ulp.ingest_lessons(conn, book, lessons)
    conn.commit()
    assert inserted == 2
    assert skipped == 0

    rows = list(
        conn.execute(
            """SELECT chunk_id, title, source_file, author, char_count
             FROM textbooks WHERE source_file = ? ORDER BY chunk_id""",
            (book.source_file,),
        )
    )
    assert len(rows) == 2
    assert rows[0][0] == "test-ulp-fixture_l0121"
    assert rows[1][0] == "test-ulp-fixture_l0122"
    assert rows[0][1] == "Lesson 121: 10 цікавих фактів про мене"
    assert rows[1][1] == "Lesson 122: Друга лекція"
    assert all(r[2] == "test-ulp-fixture" for r in rows)
    assert all(r[3] == ulp.AUTHOR for r in rows)
    assert all(r[4] > 0 for r in rows)
    conn.close()


def test_ingest_lessons_idempotent(tmp_path: Path) -> None:
    """Running the ingest twice on the same source should NOT duplicate
    rows; the second call returns (0 inserted, N skipped)."""
    txt = _write_fixture(tmp_path, "s1.txt", FIXTURE_S1)
    lessons = ulp.parse_book(txt)

    db_path = tmp_path / "sources.db"
    conn = _make_textbooks_db(db_path)
    book = ulp.BookConfig(
        slug="t",
        source_file="t-ulp",
        txt_filename="s1.txt",
        season=1,
    )

    first = ulp.ingest_lessons(conn, book, lessons)
    conn.commit()
    second = ulp.ingest_lessons(conn, book, lessons)
    conn.commit()
    assert first == (2, 0)
    assert second == (0, 2)
    total = conn.execute("SELECT COUNT(*) FROM textbooks").fetchone()[0]
    assert total == 2
    conn.close()


def test_ingest_lessons_force_overwrites(tmp_path: Path) -> None:
    """With force=True, existing rows are deleted before re-insert."""
    txt = _write_fixture(tmp_path, "s1.txt", FIXTURE_S1)
    lessons = ulp.parse_book(txt)

    db_path = tmp_path / "sources.db"
    conn = _make_textbooks_db(db_path)
    book = ulp.BookConfig(
        slug="t",
        source_file="t-ulp",
        txt_filename="s1.txt",
        season=1,
    )
    ulp.ingest_lessons(conn, book, lessons)
    conn.commit()
    inserted, skipped = ulp.ingest_lessons(conn, book, lessons, force=True)
    conn.commit()
    assert inserted == 2
    assert skipped == 0
    total = conn.execute("SELECT COUNT(*) FROM textbooks").fetchone()[0]
    assert total == 2
    conn.close()


# ---------------------------------------------------------------------------
# Furniture-recognizer parametric tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "line,expected",
    [
        # Page footer
        ("                          Inspiring resources for learning Ukrainian — UkrainianLessons.com", True),
        # Back to Contents
        ("Back to Contents                                                                       1", True),
        ("Back to Contents 5", True),
        # Bare page numbers
        ("5", True),
        ("190", True),
        ("                    7", True),
        # Season header
        ("                              Ukrainian Lessons Podcast: Season 1", True),
        ("                                 Ukrainian Lessons Podcast: Season 4", True),
        # Bare UkrainianLessons.com
        ("                          UkrainianLessons.com", True),
        # Season 4-6 running head (no space between № and number)
        ("                                        Конспект уроку №121", True),
        ("Конспект уроку №240", True),
        # Season 1-3 running head
        ("                                  Episode 1 — Informal Greetings in Ukrainian", True),
        # NOT furniture
        ("Я люблю українську мову.", False),
        ("Анна: Приві́т!", False),
        ("", False),  # blank line — handled separately by parser
        # The WITH-space lesson-start markers must NOT be classified as
        # furniture (they're handled by the parser's marker detection).
        ("                                            Lesson Notes № 1", False),
        ("                                       Конспект уроку № 121", False),
    ],
)
def test_is_page_furniture(line: str, expected: bool) -> None:
    assert ulp._is_page_furniture(line) is expected
