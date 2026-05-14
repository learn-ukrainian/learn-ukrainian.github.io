"""Tests for the static HTML etymology page generator."""

import json
import sqlite3

from scripts.etymology.extract_static_pages import generate_pages


def _make_db(path):
    conn = sqlite3.connect(path)
    conn.executescript(
        """
        CREATE TABLE esum_etymology_meta (
            id INTEGER PRIMARY KEY,
            lemma TEXT NOT NULL,
            vol INTEGER NOT NULL,
            page INTEGER NOT NULL,
            entry_hash TEXT NOT NULL DEFAULT '',
            etymology_text TEXT NOT NULL,
            cognates TEXT NOT NULL DEFAULT '[]',
            source TEXT NOT NULL DEFAULT 'ЕСУМ',
            UNIQUE(lemma, vol, page, entry_hash)
        );
        CREATE TABLE esum_cognate_forms (
            entry_id INTEGER PRIMARY KEY,
            cognate_forms TEXT NOT NULL DEFAULT '{}',
            proto_form TEXT,
            extracted_count INTEGER NOT NULL DEFAULT 0,
            expected_count INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY(entry_id) REFERENCES esum_etymology_meta(id)
        );
        """
    )
    entries = [
        (1, "дім", 2, 90, "hash-1", "дім; — р. дом, п. dom.", {"р.": "дом", "п.": "dom"}, None),
        (2, "мати", 2, 48, "hash-2", "мати більш загальне значення.", {}, None),
        (3, "мати", 3, 412, "hash-3", "мати 1 (іменник), {мать} <мати>.", {"р.": "мать"}, None),
        (4, "мати", 3, 413, "hash-4", "мати 2 (дієслово); — псл. *mati.", {"псл.": "*mati"}, "*mati"),
        (5, "п'ять", 1, 10, "hash-5", "п'ять | форма з [дужками] і {фігурними}.", {}, None),
    ]
    for entry_id, lemma, vol, page, entry_hash, text, forms, proto in entries:
        conn.execute(
            """
            INSERT INTO esum_etymology_meta (id, lemma, vol, page, entry_hash, etymology_text)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (entry_id, lemma, vol, page, entry_hash, text),
        )
        conn.execute(
            """
            INSERT INTO esum_cognate_forms (entry_id, cognate_forms, proto_form, extracted_count, expected_count)
            VALUES (?, ?, ?, ?, ?)
            """,
            (entry_id, json.dumps(forms, ensure_ascii=False), proto, len(forms), len(forms)),
        )
    conn.commit()
    conn.close()


def test_single_entry_page_output_structure(tmp_path):
    db_path = tmp_path / "sources.db"
    output_dir = tmp_path / "etymology"
    _make_db(db_path)

    summary = generate_pages(db_path, output_dir)
    page = output_dir / "dim.html"
    text = page.read_text(encoding="utf-8")

    # files_written = 6 (5 entry pages + 1 polysemy landing for "мати")
    # plus etymology.css is written separately as a shared asset.
    assert summary["files_written"] == 6
    assert (output_dir / "etymology.css").exists()
    assert page.exists()

    # HTML structure
    assert text.startswith("<!DOCTYPE html>")
    assert '<html lang="uk">' in text
    assert "<title>дім — Етимологія | Learn Ukrainian</title>" in text
    assert '<link rel="stylesheet" href="/etymology/etymology.css">' in text
    assert "<h1>дім</h1>" in text
    assert "Том 2, с. 90" in text
    # Cognate table includes Russian label
    assert "Російська (р.)" in text
    assert "<td>дом</td>" in text
    # Footer links to landing + explorer
    assert 'href="/etymology/"' in text
    assert 'href="/etymology/explore/"' in text


def test_polysemy_landing_and_subpages(tmp_path):
    db_path = tmp_path / "sources.db"
    output_dir = tmp_path / "etymology"
    _make_db(db_path)

    generate_pages(db_path, output_dir)

    landing = (output_dir / "maty.html").read_text(encoding="utf-8")
    assert "кілька статей в ЕСУМ" in landing
    assert 'href="maty-2-48/"' in landing
    assert 'href="maty-3-412/"' in landing
    assert 'href="maty-3-413/"' in landing
    assert (output_dir / "maty-2-48.html").exists()
    assert (output_dir / "maty-3-412.html").exists()
    assert (output_dir / "maty-3-413.html").exists()


def test_html_escaping_for_special_chars(tmp_path):
    db_path = tmp_path / "sources.db"
    output_dir = tmp_path / "etymology"
    _make_db(db_path)

    generate_pages(db_path, output_dir)
    page = output_dir / "piat.html"
    text = page.read_text(encoding="utf-8")

    # Title in <h1> contains the apostrophe-bearing lemma
    assert "<h1>п&#x27;ять</h1>" in text or "<h1>п'ять</h1>" in text
    # Curly-brace text in etymology body is escaped (HTML-safe — & < > " ' but { } pass through)
    assert "{фігурними}" in text  # curly braces are safe in HTML
    # Angle-bracket text in body is HTML-escaped
    body = (output_dir / "maty-3-412.html").read_text(encoding="utf-8")
    assert "&lt;мати&gt;" in body


def test_proto_form_block_when_present(tmp_path):
    db_path = tmp_path / "sources.db"
    output_dir = tmp_path / "etymology"
    _make_db(db_path)

    generate_pages(db_path, output_dir)
    page_with_proto = (output_dir / "maty-3-413.html").read_text(encoding="utf-8")
    assert 'class="proto"' in page_with_proto
    assert "Праслов'янське:" in page_with_proto
    assert "*mati" in page_with_proto

    page_without_proto = (output_dir / "dim.html").read_text(encoding="utf-8")
    assert 'class="proto"' not in page_without_proto


def test_css_file_is_emitted(tmp_path):
    db_path = tmp_path / "sources.db"
    output_dir = tmp_path / "etymology"
    _make_db(db_path)

    generate_pages(db_path, output_dir)
    css = (output_dir / "etymology.css").read_text(encoding="utf-8")
    assert "--bg" in css  # CSS custom property
    assert "prefers-color-scheme: dark" in css
    assert "@media (max-width: 600px)" in css
