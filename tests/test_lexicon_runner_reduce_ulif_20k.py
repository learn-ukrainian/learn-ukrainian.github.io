"""CLI driver for offline reduce (20k ULIF path) — #5230, sibling of #5786 (#5776)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.lexicon.runner.network_cache import NetworkCache, compute_request_key

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "ulif_dictua"
USER_AGENT = "learn-ukrainian-atlas/1.0 (noncommercial educational ULIF per-lemma fetch; issue #5230)"


def _seed_network_cache(path: Path, lemma: str) -> None:
    """Write one fetch-shaped raw_cache row so offline reduce has something to parse."""
    envelope = {
        "lemma": lemma,
        "status": "ok",
        "responses": [
            {
                "stage": "initial",
                "status_code": 200,
                "headers": {"content-type": "text/html"},
                "html": (FIXTURES / "privit-paradigm.html").read_text(encoding="utf-8"),
            }
        ],
    }
    cache = NetworkCache(path, owner_id="test-reduce-driver-seed")
    cache.open()
    try:
        body = (json.dumps(envelope, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
        request_body = json.dumps(
            {"adapter": "ulif-dictua-fetch-v1", "lemma": lemma}, ensure_ascii=False, sort_keys=True
        ).encode("utf-8")
        headers = {"user-agent": USER_AGENT}
        request_key = compute_request_key(
            method="POST",
            url="https://lcorp.ulif.org.ua/dictua/",
            request_body=request_body,
            response_affecting_headers=headers,
        )
        cache.ensure_claim_row(request_key)
        claim = cache.claim_request(request_key, cache.owner_id)
        assert claim.ok and claim.lease_generation is not None
        result = cache.commit_raw(
            request_key,
            cache.owner_id,
            claim.lease_generation,
            method="POST",
            url="https://lcorp.ulif.org.ua/dictua/",
            request_body=request_body,
            response_affecting_headers=headers,
            adapter_version="ulif-dictua-fetch-v1",
            status_code=200,
            response_headers={"content-type": "application/json; charset=utf-8"},
            body=body,
            meta={"logical_request": "ulif_dictua_lookup", "lemma": lemma},
        )
        assert result.ok, result
    finally:
        cache.close()


def test_in_process_reduce_never_applies_worker_memory_limit_to_coordinator(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """#5776 sibling of #5786: the coordinator must defer memory enforcement, not self-apply.

    Fails (via the raising stub below) if ``_run`` ever goes back to calling
    ``apply_worker_memory_limit`` directly instead of the disposable-child
    self-test — that direct call would RLIMIT/cgroup-cap whatever process
    drives it, including pytest itself when a test drives this in-process.
    """
    from scripts.lexicon.runner.memory import EnforcementProof
    from scripts.lexicon.runner.reduce_ulif_20k import main as reduce_main

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

    network_cache = tmp_path / "network-cache.sqlite"
    _seed_network_cache(network_cache, "привіт")

    slice_file = tmp_path / "slice.txt"
    slice_file.write_text("привіт\n", encoding="utf-8")

    work = tmp_path / "reduce_work"
    code = reduce_main(
        [
            "--repo",
            str(ROOT),
            "--work-dir",
            str(work),
            "--network-cache",
            str(network_cache),
            "--slice-file",
            str(slice_file),
            "--require-memory-cap",
        ]
    )
    assert code == 0
    candidate = json.loads((work / "candidate-ulif-reduce.json").read_text(encoding="utf-8"))
    assert candidate["entries"][0]["lemma"] == "привіт"


def test_help_exits_zero_without_side_effects(tmp_path: Path) -> None:
    """Sanity companion: --help must not start a reduce run or write work artifacts."""
    import subprocess

    work = tmp_path / "work"
    proc = subprocess.run(
        [str(ROOT / ".venv" / "bin" / "python"), str(ROOT / "scripts" / "lexicon" / "runner" / "reduce_ulif_20k.py"), "--help"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert proc.returncode == 0, proc.stderr
    help_text = (proc.stdout + proc.stderr).lower()
    assert "usage:" in help_text
    assert "--require-memory-cap" in help_text
    assert not work.exists()
