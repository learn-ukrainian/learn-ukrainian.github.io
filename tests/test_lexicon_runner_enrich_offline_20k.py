"""CLI driver for offline enrich (20k ULIF path) — #5230 / #5331 post-reduce."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PYTHON = str(ROOT / ".venv" / "bin" / "python")
DRIVER = ROOT / "scripts" / "lexicon" / "runner" / "enrich_offline_20k.py"
FIXTURE = ROOT / "tests" / "fixtures" / "lexicon" / "runner_pr1"
MAX_FIXTURE_LEMMAS = 50


def _ensure_fixture() -> None:
    needed = (
        FIXTURE / "slice_input.json",
        FIXTURE / "sources_slice.sqlite",
        FIXTURE / "kaikki_slice.json",
        FIXTURE / "grac_frequency_slice.json",
    )
    if all(path.is_file() for path in needed):
        return
    from scripts.lexicon.runner.generate_pr1_fixture import main as gen

    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("LEXICON_SLOVNYK_OFFLINE", "1")
        assert gen() == 0
    assert all(path.is_file() for path in needed)


def _run_driver(*args: str, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [PYTHON, str(DRIVER), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout,
    )


def _events(stdout: str) -> list[dict]:
    out: list[dict] = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict) and "event" in obj:
            out.append(obj)
    return out


def test_help_exits_zero_without_side_effects(tmp_path: Path) -> None:
    """#5393 class: --help must not start enrich or write work artifacts."""
    work = tmp_path / "work"
    proc = _run_driver("--help")
    assert proc.returncode == 0, proc.stderr
    help_text = (proc.stdout + proc.stderr).lower()
    assert "usage:" in help_text
    assert "--candidate" in help_text or "--manifest" in help_text
    assert "--work-dir" in help_text
    assert "--dry-run" in help_text
    assert "--stop-after-chunks" in help_text
    assert not work.exists()


def test_bare_invocation_refuses_without_running() -> None:
    """#5393 class: bare argv must refuse (nonzero) and not open a long run."""
    proc = _run_driver()
    assert proc.returncode != 0
    combined = (proc.stdout + proc.stderr).lower()
    assert "refusing" in combined or "usage:" in combined
    assert "offline_enrich_start" not in proc.stdout


def test_dry_run_plan_fixture_slice(tmp_path: Path) -> None:
    _ensure_fixture()
    work = tmp_path / "enrich_work"
    proc = _run_driver(
        "--dry-run",
        "--work-dir",
        str(work),
        "--candidate",
        str(FIXTURE / "slice_input.json"),
        "--sources-db",
        str(FIXTURE / "sources_slice.sqlite"),
        "--kaikki-json",
        str(FIXTURE / "kaikki_slice.json"),
        "--max-lemmas",
        str(MAX_FIXTURE_LEMMAS),
        "--chunk-size",
        "25",
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    events = _events(proc.stdout)
    assert any(e.get("event") == "offline_enrich_dry_run" for e in events)
    plan = next(e for e in events if e.get("event") == "offline_enrich_dry_run")
    assert plan["ok"] is True
    assert plan["entry_count"] == 500
    assert plan["effective_entry_count"] == MAX_FIXTURE_LEMMAS
    assert plan["planned_chunks"] == 2  # 50 / 25
    assert "finalize" in plan["stops_before"]
    assert "publish" in plan["stops_before"]
    # Dry-run must not create ledger / seals under work-dir.
    assert not (work / "ledger.sqlite").exists()
    assert not (work / "seals").exists()


def test_dry_run_missing_candidate_reports_not_ok(tmp_path: Path) -> None:
    work = tmp_path / "enrich_work"
    proc = _run_driver(
        "--dry-run",
        "--work-dir",
        str(work),
        "--candidate",
        str(tmp_path / "missing-candidate.json"),
        "--sources-db",
        str(FIXTURE / "sources_slice.sqlite") if (FIXTURE / "sources_slice.sqlite").is_file() else str(tmp_path / "no-sources"),
        "--kaikki-json",
        str(tmp_path / "no-kaikki.json"),
    )
    assert proc.returncode != 0
    events = _events(proc.stdout)
    plan = next(e for e in events if e.get("event") == "offline_enrich_dry_run")
    assert plan["ok"] is False
    assert plan["missing"]


def test_in_process_slice_stop_after_chunks(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """≤50-lemma fixture dry-run of the full driver path (resumable, no finalize)."""
    _ensure_fixture()
    from scripts.lexicon import enrich_manifest as em
    from scripts.lexicon.runner.enrich_offline_20k import main as enrich_main
    from scripts.lexicon.runner.memory import EnforcementProof

    monkeypatch.setattr(em, "_vesum_valid_synonym", lambda term: bool(term))
    monkeypatch.setattr(
        "scripts.lexicon.runner.offline_engine.run_startup_self_test",
        lambda **_kwargs: EnforcementProof(
            kind="rlimit_as",
            enforced=True,
            detail="test stub",
            max_bytes=64 * 1024 * 1024,
        ),
    )

    def _fake_enrich(payload: dict) -> dict[str, str]:
        import hashlib

        entries = json.loads(Path(payload["entries_path"]).read_text(encoding="utf-8"))
        artifact_dir = Path(payload["artifact_dir"])
        artifact_dir.mkdir(parents=True, exist_ok=True)
        arts: dict[str, str] = {}
        for entry in entries:
            lemma_id = str(entry.get("url_slug") or entry.get("lemma") or "")
            body = {
                "lemma": entry.get("lemma"),
                "url_slug": lemma_id,
                "enriched": True,
                "offline_enrich_driver": True,
            }
            raw = json.dumps(body, ensure_ascii=False, sort_keys=True)
            (artifact_dir / f"{lemma_id}.json").write_text(raw + "\n", encoding="utf-8")
            arts[lemma_id] = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        return arts

    monkeypatch.setattr(
        "scripts.lexicon.runner.worker_enrich.enrich_chunk_payload",
        _fake_enrich,
    )

    work = tmp_path / "enrich_work"
    out = work / "candidate-enriched.json"
    code = enrich_main(
        [
            "--repo",
            str(ROOT),
            "--work-dir",
            str(work),
            "--candidate",
            str(FIXTURE / "slice_input.json"),
            "--sources-db",
            str(FIXTURE / "sources_slice.sqlite"),
            "--kaikki-json",
            str(FIXTURE / "kaikki_slice.json"),
            "--grac-cache",
            str(FIXTURE / "grac_frequency_slice.json"),
            "--output",
            str(out),
            "--max-lemmas",
            str(MAX_FIXTURE_LEMMAS),
            "--chunk-size",
            "25",
            "--stop-after-chunks",
            "1",
            "--in-process",
        ]
    )
    assert code == 0
    assert out.is_file()
    candidate = json.loads(out.read_text(encoding="utf-8"))
    assert candidate.get("enrichment_generated") is True
    assert candidate.get("interrupted") is True
    assert len(candidate["entries"]) == MAX_FIXTURE_LEMMAS
    # First chunk only enriched under the stub; rest passthrough.
    enriched = [e for e in candidate["entries"] if e.get("enriched") is True]
    assert len(enriched) == 25
    assert (work / "ledger.sqlite").is_file()
    # Must not have invoked finalize / publication tree.
    assert not (work / "tree").exists()
    assert not list(work.glob("**/atlas-tree.zip"))


def test_resume_after_stop_after_chunks(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _ensure_fixture()
    from scripts.lexicon import enrich_manifest as em
    from scripts.lexicon.runner.enrich_offline_20k import main as enrich_main
    from scripts.lexicon.runner.memory import EnforcementProof

    monkeypatch.setattr(em, "_vesum_valid_synonym", lambda term: bool(term))
    monkeypatch.setattr(
        "scripts.lexicon.runner.offline_engine.run_startup_self_test",
        lambda **_kwargs: EnforcementProof(
            kind="rlimit_as",
            enforced=True,
            detail="test stub",
            max_bytes=64 * 1024 * 1024,
        ),
    )

    def _fake_enrich(payload: dict) -> dict[str, str]:
        import hashlib

        entries = json.loads(Path(payload["entries_path"]).read_text(encoding="utf-8"))
        artifact_dir = Path(payload["artifact_dir"])
        artifact_dir.mkdir(parents=True, exist_ok=True)
        arts: dict[str, str] = {}
        for entry in entries:
            lemma_id = str(entry.get("url_slug") or entry.get("lemma") or "")
            body = {"lemma": entry.get("lemma"), "url_slug": lemma_id, "enriched": True}
            raw = json.dumps(body, ensure_ascii=False, sort_keys=True)
            (artifact_dir / f"{lemma_id}.json").write_text(raw + "\n", encoding="utf-8")
            arts[lemma_id] = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        return arts

    monkeypatch.setattr(
        "scripts.lexicon.runner.worker_enrich.enrich_chunk_payload",
        _fake_enrich,
    )

    work = tmp_path / "enrich_work"
    out1 = work / "out1.json"
    common = [
        "--repo",
        str(ROOT),
        "--work-dir",
        str(work),
        "--candidate",
        str(FIXTURE / "slice_input.json"),
        "--sources-db",
        str(FIXTURE / "sources_slice.sqlite"),
        "--kaikki-json",
        str(FIXTURE / "kaikki_slice.json"),
        "--grac-cache",
        str(FIXTURE / "grac_frequency_slice.json"),
        "--max-lemmas",
        str(MAX_FIXTURE_LEMMAS),
        "--chunk-size",
        "25",
        "--in-process",
        "--owner-id",
        "enrich-driver-test",
    ]
    code1 = enrich_main([*common, "--output", str(out1), "--stop-after-chunks", "1"])
    assert code1 == 0
    first = json.loads(out1.read_text(encoding="utf-8"))
    run_id = first["ledger_run_id"]
    assert first.get("interrupted") is True

    out2 = work / "out2.json"
    code2 = enrich_main([*common, "--output", str(out2), "--run-id", run_id])
    assert code2 == 0
    second = json.loads(out2.read_text(encoding="utf-8"))
    assert second["ledger_run_id"] == run_id
    assert second.get("interrupted") is False
    assert sum(1 for e in second["entries"] if e.get("enriched") is True) == MAX_FIXTURE_LEMMAS


def test_launch_enrich_sh_is_executable_and_documents_caps() -> None:
    path = ROOT / "scripts" / "lexicon" / "runner" / "launch_enrich.sh"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "MemoryHigh=1536M" in text
    assert "MemoryMax=2048M" in text
    assert "enrich_offline_20k.py" in text
    assert "candidate-ulif-reduce.json" in text
    assert "finalize" in text.lower() or "pin-flip" in text.lower()
    # Shell syntax check
    proc = subprocess.run(["bash", "-n", str(path)], capture_output=True, text=True, check=False)
    assert proc.returncode == 0, proc.stderr
