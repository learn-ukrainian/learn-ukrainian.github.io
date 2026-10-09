"""Exact recovery transactions, divergence and interrupted atomic replacement."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from scripts.lexicon import dispose_published_records as command
from scripts.lexicon import manifest_io
from scripts.lexicon import published_record_dispositions as dispositions
from tests.test_published_record_dispositions import add_release, make_authority


def prepare(tmp_path, monkeypatch):
    ledger, preserved, before = make_authority(tmp_path)
    monkeypatch.setattr(dispositions, "PROJECT_ROOT", tmp_path)
    path = tmp_path / "prospective.json"
    manifest_io.write_manifest(path, before)
    return ledger, preserved, before, path


def release_all(root, ledger):
    for hold in list(ledger["decisions"]):
        add_release(root, ledger, hold)


def test_dry_run_exact_withdraw_retry_and_reviewed_byte_restore(tmp_path, monkeypatch):
    ledger, preserved, before, path = prepare(tmp_path, monkeypatch)
    original = path.read_bytes()
    recovery = (tmp_path / dispositions.PRESERVATION_PATH).read_bytes()
    dry = command.dispose(path, "withdraw")
    assert dry["state"] == "dry_run" and not dry["written"]
    assert path.read_bytes() == original
    written = command.dispose(path, "withdraw", write=True)
    assert written["sha256"] == preserved["transaction"]["after_sha256"]
    after = json.loads(path.read_bytes())
    assert after["stats"] == {
        "lemmas_total": 2,
        "from_built": 1,
        "form_of_count": 1,
        "entries": 19203,
        "entry_count": 20111,
    }
    assert after["generated_at"] == before["generated_at"] and after["unknown"] == before["unknown"]
    assert command.dispose(path, "withdraw", write=True)["state"] == "already_applied"
    with pytest.raises(dispositions.DispositionError, match="reviewed releases"):
        command.dispose(path, "restore", write=True)
    release_all(tmp_path, ledger)
    assert command.dispose(path, "restore")["state"] == "dry_run"
    assert command.dispose(path, "restore", write=True)["sha256"] == preserved["transaction"]["before_sha256"]
    assert path.read_bytes() == original
    assert command.dispose(path, "restore", write=True)["state"] == "already_applied"
    assert (tmp_path / dispositions.PRESERVATION_PATH).read_bytes() == recovery
    with pytest.raises(dispositions.DispositionError, match="active holds"):
        command.dispose(path, "withdraw", write=True)


@pytest.mark.parametrize("fault", ["survivor", "metadata", "position", "payload", "missing", "formatting"])
def test_divergent_retry_refuses_without_changing_input(tmp_path, monkeypatch, fault):
    _, _, before, path = prepare(tmp_path, monkeypatch)
    if fault == "survivor":
        before["entries"][0]["gloss"] = "changed"
    elif fault == "metadata":
        before["unknown"]["opaque"] = False
    elif fault == "position":
        before["entries"][0], before["entries"][1] = before["entries"][1], before["entries"][0]
    elif fault == "payload":
        before["entries"][1]["gloss"] = "changed"
    elif fault == "missing":
        before["entries"].pop()
    manifest_io.write_manifest(path, before)
    if fault == "formatting":
        path.write_bytes(path.read_bytes() + b"\n")
    raw = path.read_bytes()
    assert command.main(["--manifest", str(path), "--action", "withdraw", "--write"]) == 2
    assert path.read_bytes() == raw


def test_interrupted_replace_preserves_before_and_exact_retry(tmp_path, monkeypatch):
    _, _, _, path = prepare(tmp_path, monkeypatch)
    raw = path.read_bytes()
    real_replace = os.replace

    def fail_replace(source, destination):
        if Path(destination) == path:
            raise OSError("interrupted replacement")
        real_replace(source, destination)

    with monkeypatch.context() as patch:
        patch.setattr(os, "replace", fail_replace)
        assert command.main(["--manifest", str(path), "--action", "withdraw", "--write"]) == 2
    assert path.read_bytes() == raw
    assert command.dispose(path, "withdraw", write=True)["written"]
    assert command.dispose(path, "withdraw", write=True)["state"] == "already_applied"


def test_authority_is_re_read_before_write(tmp_path, monkeypatch):
    _, _, _, path = prepare(tmp_path, monkeypatch)
    real_load = command.load_dispositions
    calls = 0
    raw = path.read_bytes()

    def changed_load():
        nonlocal calls
        authority = real_load()
        calls += 1
        if calls == 2:
            authority.ledger["batch_id"] = "changed"
        return authority

    monkeypatch.setattr(command, "load_dispositions", changed_load)
    with pytest.raises(dispositions.DispositionError, match="authority changed"):
        command.dispose(path, "withdraw", write=True)
    assert path.read_bytes() == raw


def test_concurrent_manifest_change_refuses_replace(tmp_path, monkeypatch):
    _, _, _, path = prepare(tmp_path, monkeypatch)
    real_load = command.load_dispositions
    calls = 0

    def changed_load():
        nonlocal calls
        authority = real_load()
        calls += 1
        if calls == 2:
            path.write_bytes(path.read_bytes() + b"\n")
        return authority

    monkeypatch.setattr(command, "load_dispositions", changed_load)
    with pytest.raises(dispositions.DispositionError, match="manifest changed"):
        command.dispose(path, "withdraw", write=True)
    assert path.read_bytes().endswith(b"\n\n")


@pytest.mark.parametrize(
    "fault",
    [
        "entries",
        "count",
        "payload",
        "envelope",
        "survivor",
        "digest",
        "route",
        "restore_count",
        "restore_holds",
        "action",
    ],
)
def test_prospective_contract_errors(tmp_path, fault):
    ledger, _preserved, before = make_authority(tmp_path)
    authority = dispositions.load_dispositions(tmp_path)
    action = "withdraw"
    if fault == "entries":
        before["entries"] = None
    elif fault == "count":
        before["entries"].pop()
    elif fault == "payload":
        before["entries"][1]["gloss"] = "changed"
    elif fault == "envelope":
        before["unknown"] = "changed"
    elif fault == "survivor":
        before["entries"][0]["gloss"] = "changed"
    elif fault == "digest":
        authority.preservation["transaction"]["after_sha256"] = "0" * 64
    elif fault == "route":
        before["entries"][0]["related_slug"] = before["entries"][1]["url_slug"]
    elif fault == "restore_count":
        release_all(tmp_path, ledger)
        authority = dispositions.load_dispositions(tmp_path)
        action = "restore"
    elif fault == "restore_holds":
        action = "restore"
    elif fault == "action":
        action = "invalid"
    with pytest.raises(dispositions.DispositionError):
        command.prospective_manifest(before, authority, action)


def test_partial_release_cannot_withdraw_or_restore(tmp_path, monkeypatch):
    ledger, _, before, path = prepare(tmp_path, monkeypatch)
    add_release(tmp_path, ledger, ledger["decisions"][0])
    for action in ("withdraw", "restore"):
        with pytest.raises(dispositions.DispositionError):
            command.dispose(path, action, write=True)
    assert json.loads(path.read_bytes()) == before


def test_missing_recovery_after_withdraw_still_refuses_retry(tmp_path, monkeypatch):
    _, _, _, path = prepare(tmp_path, monkeypatch)
    command.dispose(path, "withdraw", write=True)
    original = path.read_bytes()
    (tmp_path / dispositions.PRESERVATION_PATH).unlink()
    assert command.main(["--manifest", str(path), "--action", "withdraw", "--write"]) == 2
    assert path.read_bytes() == original


def test_present_metadata_aliases_only_and_cli_contract(tmp_path, monkeypatch, capsys):
    _, _, _, path = prepare(tmp_path, monkeypatch)
    assert command.main(["--manifest", str(path), "--action", "withdraw"]) == 0
    assert json.loads(capsys.readouterr().out)["state"] == "dry_run"
    with pytest.raises(SystemExit) as exit_info:
        command.main(["--action", "withdraw"])
    assert exit_info.value.code == 2
    with pytest.raises(dispositions.DispositionError):
        command.dispose(path, "invalid")
    manifest = {"entries": []}
    command._refresh_present_counts(manifest)
    assert manifest == {"entries": []}
