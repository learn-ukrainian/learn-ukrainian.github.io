"""Coverage report counts distinct PULS/Atlas words per dictionary from fixtures only."""

import sqlite3

from scripts.ingest import slovnyk_me_coverage as coverage
from scripts.wiki.slovnyk_me import ensure_slovnyk_me_schema


def test_coverage_counts_found_and_recorded_404_per_dictionary(tmp_path):
    sources = tmp_path / "sources.db"
    with sqlite3.connect(sources) as conn:
        conn.execute("CREATE TABLE puls_cefr (word TEXT, level TEXT)")
        conn.executemany(
            "INSERT INTO puls_cefr VALUES (?, ?)",
            [("шуба", "A1"), ("Шуба", "A2"), ("хата", "B1"), ("кіт", "B2"), ("лис", "A1")],
        )
        ensure_slovnyk_me_schema(conn)
        conn.executemany(
            "INSERT INTO slovnyk_me_entries (word, normalized_word, dictionary_slug) VALUES (?, ?, ?)",
            [("шуба", "шуба", "vts"), ("шуба", "шуба", "newsum"), ("кіт", "кіт", "vts")],
        )
        conn.execute(
            "INSERT INTO slovnyk_me_lookup_misses (lookup_word, normalized_word, dictionary_slug) VALUES ('хата', 'хата', 'newsum')"
        )
    atlas = tmp_path / "atlas.db"
    with sqlite3.connect(atlas) as conn:
        conn.execute("CREATE TABLE articles (lemma TEXT)")
        conn.executemany("INSERT INTO articles VALUES (?)", [("шуба",), ("хата",), ("",)])

    report = coverage.coverage(sources, atlas)

    assert report["targets"] == {"puls_a1_b1": 3, "puls_a1": 2, "puls_a2": 1, "puls_b1": 1, "atlas": 2}
    assert report["slovnyk_me_entries"] == 3
    assert report["dictionaries"]["vts"]["puls_a1_b1"] == {"found": 1, "not_found": 0}
    assert report["dictionaries"]["newsum"]["puls_a1_b1"] == {"found": 1, "not_found": 1}
    assert report["dictionaries"]["newsum"]["atlas"] == {"found": 1, "not_found": 1}
    assert "| newsum | 1 / 1 |" in coverage.render(report)


def test_cli_writes_json_report(tmp_path, capsys):
    sources = tmp_path / "sources.db"
    with sqlite3.connect(sources) as conn:
        conn.execute("CREATE TABLE puls_cefr (word TEXT, level TEXT)")
    atlas = tmp_path / "atlas.db"
    with sqlite3.connect(atlas) as conn:
        conn.execute("CREATE TABLE articles (lemma TEXT)")
    out = tmp_path / "out" / "report.json"
    assert coverage.main(["--sources-db", str(sources), "--atlas-db", str(atlas), "--out", str(out)]) == 0
    assert '"slovnyk_me_entries": 0' in out.read_text()
    assert "slovnyk_me_entries rows: 0" in capsys.readouterr().out
