"""Tests for the СУМ-11 Sovietization scan (issue #1659).

Strategy: build a tiny in-memory sum11-shaped table seeded with hand-picked
entries that exercise each branch of the classify_entry logic, plus a
couple of real-content samples copied from the production DB at write
time. We do NOT depend on the 1.5 GB production DB at test time.
"""

from __future__ import annotations

import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCAN_SCRIPT = REPO_ROOT / "scripts" / "audit" / "sum11_sovietization_scan.py"
MIGRATION_SQL = (
    REPO_ROOT
    / "migrations"
    / "2026-05-04-1659-sum11-sovietization-flag.sql"
)
VENV_PYTHON = REPO_ROOT / ".venv" / "bin" / "python"


def _venv_python() -> Path:
    assert VENV_PYTHON.exists(), "Expected repo venv at .venv/bin/python"
    return VENV_PYTHON


# Real-content samples lifted from a production DB scan on 2026-05-04.
# Definitions truncated for test brevity; full text was 200+ chars per row.
SEED_ROWS = [
    # (id, word, definition, text, source) — see sum11 schema
    (
        1,
        "ленінізм",
        "Учення В. І. Леніна, що являє собою дальший розвиток і конкретизацію "
        "марксизму в умовах імперіалізму та пролетарських революцій. Ленінізм "
        "є ідеологією Комуністичної партії Радянського Союзу.",
        "",
        "sum11",
    ),
    (
        2,
        "більшовик",
        "Послідовник більшовизму, член більшовицької партії "
        "(первісне — належний до очолюваної В. І. Леніним більшості).",
        "",
        "sum11",
    ),
    (
        3,
        "національний",
        "Стос. до нації, національності, пов'язаний з їх суспільно-політичною "
        "діяльністю. Мудра ленінська національна політика возз'єднала нас у "
        "державу.",
        "",
        "sum11",
    ),
    (
        4,
        "москаль",
        "Вояк, солдат. Баба-повитуха в чистій сорочці.. командувала молодицями, "
        "неначе генерал москалями (Н.-Лев., III, 1956, 109).",
        "",
        "sum11",
    ),
    (
        5,
        "західний",
        "Прикм. до за́хід¹; протилежне східний. В обличчя віяв холодний західний "
        "вітер.",
        "",
        "sum11",
    ),
    (
        6,
        "піонер",
        # Ambiguous-only: "піонер" is in our keyword list but is the only stem
        # that hits, and the definition uses it in the explorer/pioneer sense
        # (no other Soviet stems present). Should classify as 0.
        "Той, хто перший виявляє ініціативу в чомусь; зачинатель.",
        "",
        "sum11",
    ),
    (
        7,
        "хххх",
        "Made-up word with no Soviet content whatsoever.",
        "",
        "sum11",
    ),
]


@pytest.fixture
def seeded_db(tmp_path):
    """Create a small sum11-shaped DB and apply the migration."""
    db_path = tmp_path / "sum11_test.db"
    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        CREATE TABLE sum11 (
            id INTEGER PRIMARY KEY,
            word TEXT NOT NULL,
            definition TEXT NOT NULL DEFAULT '',
            text TEXT NOT NULL DEFAULT '',
            source TEXT DEFAULT ''
        );
        CREATE INDEX idx_sum11_word ON sum11(word COLLATE NOCASE);
        """
    )
    conn.executemany(
        "INSERT INTO sum11 (id, word, definition, text, source) "
        "VALUES (?, ?, ?, ?, ?)",
        SEED_ROWS,
    )
    conn.commit()

    # Apply the production migration so column shape matches.
    conn.executescript(MIGRATION_SQL.read_text())
    conn.commit()
    conn.close()
    return db_path


def test_migration_adds_required_columns(seeded_db):
    conn = sqlite3.connect(seeded_db)
    cols = {row[1] for row in conn.execute("PRAGMA table_info(sum11)").fetchall()}
    conn.close()
    assert "sovietization_risk" in cols
    assert "sovietization_keywords" in cols


def test_classify_entry_branches():
    sys.path.insert(0, str(REPO_ROOT / "scripts" / "audit"))
    from sum11_sovietization_scan import classify_entry

    # Clean — no Soviet markers.
    risk, kws = classify_entry("Прикм. до за́хід.", "")
    assert risk == 0
    assert kws == []

    # Framing opener escalates to risk=2.
    risk, kws = classify_entry(
        "Учення В. І. Леніна, що являє собою розвиток марксизму. "
        "Ідеологія Комуністичної партії Радянського Союзу.",
        "",
    )
    assert risk == 2
    assert "ленін" in kws

    # ≥3 distinct keyword stems → risk=2 even without framing opener.
    risk, kws = classify_entry(
        "Стос. до більшовицької партії радянського періоду, керованої "
        "комуністичною ідеологією.",
        "",
    )
    assert risk == 2
    assert {"більшов", "радянськ", "комуністичн"}.issubset(set(kws))

    # Single-keyword match → risk=1.
    risk, kws = classify_entry(
        "Послідовник більшовизму, член відповідної партії.",
        "",
    )
    assert risk == 1
    assert kws == ["більшов"]

    # Ambiguous-only (just піонер, no other Soviet stems) → risk=0.
    risk, kws = classify_entry(
        "Той, хто перший виявляє ініціативу в чомусь; зачинатель.",
        "",
    )
    assert risk == 0
    assert kws == []


def test_scan_produces_expected_distribution(seeded_db, tmp_path):
    report_path = tmp_path / "report.md"

    result = subprocess.run(
        [
            str(_venv_python()),
            str(SCAN_SCRIPT),
            "--db",
            str(seeded_db),
            "--report",
            str(report_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        f"scan failed: stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert report_path.exists()

    conn = sqlite3.connect(seeded_db)

    # Real content checks. ленінізм should be high (framing opener +
    # multiple stems). більшовик and національний should be ≥1.
    rows = {
        row[0]: row[1:]
        for row in conn.execute(
            "SELECT word, sovietization_risk, sovietization_keywords FROM sum11"
        ).fetchall()
    }
    conn.close()

    assert rows["ленінізм"][0] == 2
    assert "ленін" in rows["ленінізм"][1]

    assert rows["більшовик"][0] >= 1
    assert "більшов" in rows["більшовик"][1]

    assert rows["національний"][0] >= 1
    assert "ленін" in rows["національний"][1]

    # Москаль's stub definition has only literary citations, no Soviet
    # ideological keywords — should be clean.
    assert rows["москаль"][0] == 0

    # Західний is purely directional/geographical — clean.
    assert rows["західний"][0] == 0

    # Піонер is ambiguous-only — clean.
    assert rows["піонер"][0] == 0

    # Made-up word — clean.
    assert rows["хххх"][0] == 0


def test_dry_run_does_not_modify_db(seeded_db, tmp_path):
    report_path = tmp_path / "dry_report.md"

    result = subprocess.run(
        [
            str(_venv_python()),
            str(SCAN_SCRIPT),
            "--db",
            str(seeded_db),
            "--report",
            str(report_path),
            "--dry-run",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "[dry-run]" in result.stdout

    # No rows should have been updated.
    conn = sqlite3.connect(seeded_db)
    flagged = conn.execute(
        "SELECT COUNT(*) FROM sum11 WHERE sovietization_risk > 0"
    ).fetchone()[0]
    conn.close()
    assert flagged == 0


def test_scan_is_idempotent(seeded_db, tmp_path):
    """Re-running the scan twice yields identical flag values."""
    report_path = tmp_path / "report.md"

    cmd = [
        str(_venv_python()),
        str(SCAN_SCRIPT),
        "--db",
        str(seeded_db),
        "--report",
        str(report_path),
    ]
    subprocess.run(cmd, check=True)
    conn = sqlite3.connect(seeded_db)
    first = conn.execute(
        "SELECT word, sovietization_risk, sovietization_keywords "
        "FROM sum11 ORDER BY id"
    ).fetchall()
    conn.close()

    subprocess.run(cmd, check=True)
    conn = sqlite3.connect(seeded_db)
    second = conn.execute(
        "SELECT word, sovietization_risk, sovietization_keywords "
        "FROM sum11 ORDER BY id"
    ).fetchall()
    conn.close()

    assert first == second
