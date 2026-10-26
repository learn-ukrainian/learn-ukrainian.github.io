"""CLI driver for the ULIF 20k network fetch phase — #5230, sibling of #5786 (#5776)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from tests._host_path_guard import assert_no_host_paths

ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
DRIVER = ROOT / "scripts" / "lexicon" / "runner" / "fetch_ulif_20k.py"


def test_default_requests_include_project_identity_and_public_contact(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject missing collector contact on actual outgoing session requests (#8999)."""
    from scripts.lexicon.runner import fetch_ulif_20k

    outgoing = []
    response = SimpleNamespace(status_code=200)
    fake_session = SimpleNamespace(headers={"User-Agent": "python-requests/fake"})

    def request(method, url, **kwargs):
        outgoing.append((method, url, dict(fake_session.headers), kwargs))
        return response

    fake_session.request = request
    session_factory = Mock(return_value=fake_session)
    requests_loader = Mock(return_value=SimpleNamespace(Session=session_factory, RequestException=RuntimeError))
    monkeypatch.setattr(fetch_ulif_20k, "_requests", requests_loader)

    client = fetch_ulif_20k.DictUAClient(delay_seconds=0, timeout_seconds=17)
    requests_loader.assert_not_called()
    assert client._request("GET") is response
    assert client._request("POST", data={"lookup": "fixture"}) is response
    session_factory.assert_called_once_with()

    expected_headers = {
        "User-Agent": (
            "learn-ukrainian-atlas/1.0 (noncommercial educational ULIF per-lemma fetch; issue #5230; "
            "+https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues)"
        )
    }
    assert outgoing == [
        ("GET", "https://lcorp.ulif.org.ua/dictua/", expected_headers, {"timeout": 17}),
        ("POST", "https://lcorp.ulif.org.ua/dictua/", expected_headers, {"timeout": 17, "data": {"lookup": "fixture"}}),
    ]


def test_source_has_no_baked_home_defaults() -> None:
    assert_no_host_paths(DRIVER.read_text(encoding="utf-8"))


def test_work_dir_flag_is_required() -> None:
    from scripts.lexicon.runner.fetch_ulif_20k import main as fetch_main

    with pytest.raises(SystemExit) as exc:
        fetch_main([])
    assert exc.value.code == 2


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
