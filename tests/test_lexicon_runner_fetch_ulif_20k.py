"""CLI driver for the ULIF 20k network fetch phase — #5230, sibling of #5786 (#5776)."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PYTHON = str(ROOT / ".venv" / "bin" / "python")
DRIVER = ROOT / "scripts" / "lexicon" / "runner" / "fetch_ulif_20k.py"


def test_help_exits_zero_without_side_effects(tmp_path: Path) -> None:
    work = tmp_path / "work"
    proc = subprocess.run(
        [PYTHON, str(DRIVER), "--help"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert proc.returncode == 0, proc.stderr
    help_text = (proc.stdout + proc.stderr).lower()
    assert "usage:" in help_text
    assert "--cohort" in help_text
    assert not work.exists()


def test_in_process_fetch_never_applies_worker_memory_limit_to_coordinator(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """#5776 sibling of #5786: the coordinator must defer memory enforcement, not self-apply.

    Fails (via the raising stub below) if ``_run`` ever goes back to calling
    ``apply_worker_memory_limit`` directly instead of the disposable-child
    self-test — that direct call would RLIMIT/cgroup-cap whatever process
    drives it, including pytest itself when a test drives this in-process.
    """
    from scripts.lexicon.runner import fetch_ulif_20k
    from scripts.lexicon.runner.fetch_ulif_20k import main as fetch_main
    from scripts.lexicon.runner.memory import EnforcementProof

    # Real cohort pin validation is out of scope here — this fixes the
    # in-process lemma list without exercising the (real, 20k-entry) cohort file.
    monkeypatch.setattr(fetch_ulif_20k, "_cohort", lambda _path: (["привіт"], "test-digest"))
    monkeypatch.setattr(
        fetch_ulif_20k.DictUAClient,
        "fetch_lookup",
        lambda self, lemma: {"lemma": lemma, "status": "not_found", "responses": []},
    )
    monkeypatch.setattr(
        "scripts.lexicon.runner.memory.run_startup_self_test",
        lambda **_kwargs: EnforcementProof(
            kind="rlimit_as",
            enforced=True,
            detail="test stub",
            max_bytes=64 * 1024 * 1024,
        ),
    )

    def _parent_memory_limit_must_not_be_applied(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("the coordinator must not apply a worker memory limit to pytest")

    monkeypatch.setattr(
        "scripts.lexicon.runner.memory.apply_worker_memory_limit",
        _parent_memory_limit_must_not_be_applied,
    )

    work = tmp_path / "fetch_work"
    code = fetch_main(
        [
            "--repo",
            str(ROOT),
            "--work-dir",
            str(work),
            "--cohort",
            str(tmp_path / "unused-cohort.txt"),
            "--max-lemmas",
            "1",
        ]
    )
    assert code == 0
    assert (work / "ledger.sqlite").is_file()
