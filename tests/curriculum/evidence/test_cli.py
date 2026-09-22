"""Tests for curriculum evidence CLI commands."""

import json
import subprocess
import sys
from pathlib import Path

import yaml

from scripts.curriculum.evidence import __main__, words

REPO_ROOT = Path(__file__).resolve().parents[3]
PYTHON = sys.executable


def test_cli_help(capsys):
    rc = __main__.main(["--help"])
    assert rc == 0
    captured = capsys.readouterr()
    assert "build-words" in captured.out
    assert "words-verify" in captured.out
    assert "invalid_request" in captured.out


def test_cli_build_and_verify_subprocess(tmp_path):
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

    # Run build-words via subprocess
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

    # Run words-verify via subprocess
    cmd_verify = [
        PYTHON,
        "-m",
        "scripts.curriculum.evidence",
        "words-verify",
        "a1",
        "--evidence-dir",
        str(ev_dir),
        "--json",
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


def test_cli_dry_run_does_not_write_files(tmp_path):
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
        ]
    )
    assert ret == 0
    assert not (ev_dir / "_words.yaml").exists()
    assert not (ev_dir / "_words.registry.yaml").exists()
