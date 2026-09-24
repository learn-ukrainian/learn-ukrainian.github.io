"""Tests for curriculum evidence CLI commands."""

import json
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from scripts.curriculum.evidence import __main__, words

REPO_ROOT = Path(__file__).resolve().parents[3]
PYTHON = sys.executable


def _real_sources_db() -> Path:
    path = REPO_ROOT / "data/sources.db"
    if path.is_file():
        return path
    from scripts.guardrails.worktree_containment import resolve_main_root

    return resolve_main_root(REPO_ROOT) / "data/sources.db"


HAS_REAL_SOURCES_DB = _real_sources_db().is_file()


def _db_flags(sources_db: Path, vesum_db: Path) -> list[str]:
    return ["--sources-db", str(sources_db), "--vesum-db", str(vesum_db)]


def test_cli_help(capsys):
    rc = __main__.main(["--help"])
    assert rc == 0
    captured = capsys.readouterr()
    assert "build-words" in captured.out
    assert "words-verify" in captured.out
    assert "build-pack" in captured.out
    assert "pack-verify" in captured.out
    assert "invalid_request" in captured.out


def test_cli_build_and_verify_subprocess(synthetic_sources, synthetic_vesum, tmp_path):
    req_path = tmp_path / "req.yaml"
    req_path.write_text(
        yaml.safe_dump(
            {
                "request_schema": 1,
                "level": "a1",
                "words": [
                    {
                        "lemma": "synthetic",
                        "pos": "noun",
                        "want": "new",
                        "entry": {"source": "vesum", "entry_id": 10},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    ev_dir = tmp_path / "evidence"
    db_flags = _db_flags(synthetic_sources, synthetic_vesum)

    # Run build-words via subprocess against the synthetic databases
    cmd_build = [
        PYTHON,
        "-m",
        "scripts.curriculum.evidence",
        "build-words",
        "a1",
        "--request",
        str(req_path),
        "--evidence-dir",
        str(ev_dir),
        "--json",
        *db_flags,
    ]
    proc_build = subprocess.run(
        cmd_build,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        timeout=30,
    )
    assert proc_build.returncode == 0, f"build failed: {proc_build.stderr}\n{proc_build.stdout}"
    data_build = json.loads(proc_build.stdout)
    assert data_build["status"] == "ok"
    assert data_build["words_count"] == 1
    assert data_build["store"]["built_with"]["sources_db_scheme"] == "rows-v2"
    # Progress output names the journal mode, the WAL size at start and end, and the snapshot duration.
    assert "progress: snapshot: pinned; journal_mode: delete; wal_bytes: 0;" in proc_build.stderr
    assert "progress: snapshot: released after " in proc_build.stderr
    assert "wal_bytes: 0 -> 0" in proc_build.stderr

    # Run words-verify via subprocess against the same synthetic databases
    cmd_verify = [
        PYTHON,
        "-m",
        "scripts.curriculum.evidence",
        "words-verify",
        "a1",
        "--evidence-dir",
        str(ev_dir),
        "--json",
        *db_flags,
    ]
    proc_verify = subprocess.run(
        cmd_verify,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        timeout=30,
    )
    assert proc_verify.returncode == 0, f"verify failed: {proc_verify.stderr}"
    data_verify = json.loads(proc_verify.stdout)
    assert data_verify["status"] == "ok"


def test_cli_dry_run_does_not_write_files(synthetic_sources, synthetic_vesum, tmp_path):
    # Monosyllabic form: the build must not need the stress oracle.
    with sqlite3.connect(synthetic_vesum) as conn:
        conn.execute("DELETE FROM forms_all")
        conn.execute("INSERT INTO forms_all VALUES (1, 100, 'ма', 'мама', 'noun', 'noun:f:v_kly:short', '', '')")

    req_path = tmp_path / "req.yaml"
    req_path.write_text(
        yaml.safe_dump(
            {
                "request_schema": 1,
                "level": "a1",
                "words": [
                    {
                        "lemma": "мама",
                        "pos": "noun",
                        "want": "new",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    ev_dir = tmp_path / "evidence"

    ret = words.main(
        [
            "a1",
            "--request",
            str(req_path),
            "--evidence-dir",
            str(ev_dir),
            "--dry-run",
            *_db_flags(synthetic_sources, synthetic_vesum),
        ]
    )
    assert ret == 0
    assert not (ev_dir / "_words.yaml").exists()
    assert not (ev_dir / "_words.registry.yaml").exists()


@pytest.mark.skipif(not HAS_REAL_SOURCES_DB, reason="requires the real data/sources.db dictionary")
def test_cli_dry_run_committed_five_lemmas_request(tmp_path):
    req_path = REPO_ROOT / "tests/fixtures/a1_five_lemmas_request.yaml"
    assert req_path.is_file()

    # An isolated evidence dir: a store already built under curriculum/ would otherwise be
    # carried into the dry-run and change the counts.
    proc = subprocess.run(
        [
            PYTHON,
            "-m",
            "scripts.curriculum.evidence",
            "build-words",
            "a1",
            "--request",
            str(req_path),
            "--evidence-dir",
            str(tmp_path / "evidence"),
            "--plans-dir",
            str(tmp_path / "plans"),
            "--dry-run",
            "--json",
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        timeout=30,
    )
    assert proc.returncode == 0, f"dry-run failed: {proc.stderr}\n{proc.stdout}"
    data = json.loads(proc.stdout)
    assert data["status"] == "ok"
    assert data["dry_run"] is True
    assert data["words_count"] == 5
    assert data["forms_count"] == 97
    assert data["store"]["built_with"]["sources_db_scheme"] == "rows-v2"
    assert data["snapshot"]["journal_mode"] in {"wal", "delete"}
    assert "progress: snapshot: pinned; journal_mode: " in proc.stderr


def test_cli_build_and_verify_pack_subprocess(synthetic_sources, synthetic_standard, tmp_path):
    req_path = tmp_path / "pack_req.yaml"
    req_path.write_text(
        yaml.safe_dump(
            {
                "request_schema": 1,
                "module": "a1/alphabet",
                "texts": [
                    {
                        "id": "T-001",
                        "source": {"table": "textbooks", "chunk_id": "chunk-1"},
                        "span": {"first_words": "synthetic-first", "last_words": "synthetic-last"},
                        "supports": "Grounds alphabet letter recognition.",
                    }
                ],
                "standard": [{"id": "S-001", "lines": "1-2"}],
            }
        ),
        encoding="utf-8",
    )

    ev_dir = tmp_path / "evidence" / "a1"
    ev_dir.mkdir(parents=True, exist_ok=True)

    cmd_build = [
        PYTHON,
        "-m",
        "scripts.curriculum.evidence",
        "build-pack",
        "a1",
        "alphabet",
        "--request",
        str(req_path),
        "--evidence-dir",
        str(ev_dir),
        "--sources-db",
        str(synthetic_sources),
        "--standard-path",
        str(synthetic_standard),
        "--offline",
        "--json",
    ]
    proc_build = subprocess.run(
        cmd_build,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        timeout=30,
    )
    assert proc_build.returncode == 0, f"build-pack failed: {proc_build.stderr}\n{proc_build.stdout}"
    data_build = json.loads(proc_build.stdout)
    assert data_build["status"] == "ok"
    assert data_build["texts_count"] == 1
    assert data_build["standard_count"] == 1
    assert (ev_dir / "alphabet.yaml").exists()
    assert (ev_dir / "alphabet.yaml.lock").exists()

    cmd_verify = [
        PYTHON,
        "-m",
        "scripts.curriculum.evidence",
        "pack-verify",
        "a1",
        "alphabet",
        "--evidence-dir",
        str(ev_dir),
        "--sources-db",
        str(synthetic_sources),
        "--standard-path",
        str(synthetic_standard),
        "--offline",
        "--json",
    ]
    proc_verify = subprocess.run(
        cmd_verify,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        timeout=30,
    )
    assert proc_verify.returncode == 0, f"pack-verify failed: {proc_verify.stderr}\n{proc_verify.stdout}"
    data_verify = json.loads(proc_verify.stdout)
    assert data_verify["status"] == "ok"


def test_cli_pack_dry_run_does_not_write_files(synthetic_sources, synthetic_standard, tmp_path):
    req_path = tmp_path / "pack_req.yaml"
    req_path.write_text(
        yaml.safe_dump(
            {
                "request_schema": 1,
                "module": "a1/alphabet",
                "texts": [
                    {
                        "id": "T-001",
                        "source": {"table": "textbooks", "chunk_id": "chunk-1"},
                        "span": {"first_words": "synthetic-first", "last_words": "synthetic-last"},
                        "supports": "Grounds alphabet letter recognition.",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    ev_dir = tmp_path / "evidence" / "a1"
    cmd_build = [
        PYTHON,
        "-m",
        "scripts.curriculum.evidence",
        "build-pack",
        "a1",
        "alphabet",
        "--request",
        str(req_path),
        "--evidence-dir",
        str(ev_dir),
        "--sources-db",
        str(synthetic_sources),
        "--standard-path",
        str(synthetic_standard),
        "--dry-run",
        "--offline",
        "--json",
    ]
    proc_build = subprocess.run(
        cmd_build,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        timeout=30,
    )
    assert proc_build.returncode == 0, f"dry-run failed: {proc_build.stderr}\n{proc_build.stdout}"
    data_build = json.loads(proc_build.stdout)
    assert data_build["status"] == "ok"
    assert data_build["dry_run"] is True
    assert not (ev_dir / "alphabet.yaml").exists()
    assert not (ev_dir / "alphabet.yaml.lock").exists()
