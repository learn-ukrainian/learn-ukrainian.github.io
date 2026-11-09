"""Formal attempts validate the exact launched server, not worktree declarations."""

from pathlib import Path

import pytest

from scripts.agent_runtime import review_mcp
from scripts.agent_runtime.sources_read_only import SERVER_PATH, sources_tool_sets
from scripts.review.receipts import ledger


@pytest.mark.parametrize("access", ["isolated", "full"])
def test_identical_launched_server_contract(tmp_path, access):
    server = tmp_path / "primary/server.py"
    server.parent.mkdir()
    server.write_bytes(SERVER_PATH.read_bytes())
    expected = ledger.REVIEW_TOOLS if access == "isolated" else ledger.FULL_REVIEW_TOOLS
    assert ledger.review_tools(access, server_path=server) == expected


@pytest.mark.parametrize("changed", ["primary", "dispatch"])
def test_dispatch_and_launched_server_must_match(tmp_path, monkeypatch, changed):
    primary = tmp_path / "primary/server.py"
    dispatch = tmp_path / "dispatch/server.py"
    for path in (primary, dispatch):
        path.parent.mkdir()
        path.write_bytes(SERVER_PATH.read_bytes())
    target = primary if changed == "primary" else dispatch
    target.write_text(target.read_text() + "\n# changed server\n")
    monkeypatch.setattr(ledger, "SERVER_PATH", dispatch)
    with pytest.raises(ValueError, match="review_launched_sources_server_mismatch"):
        ledger.review_tools(server_path=primary)


def test_unreadable_launched_server_refuses_even_with_cached_declarations(tmp_path):
    server = tmp_path / "server.py"
    server.write_bytes(SERVER_PATH.read_bytes())
    sources_tool_sets(server)
    server.unlink()
    with pytest.raises(ValueError, match="review_launched_sources_server_unreadable"):
        ledger.review_tools(server_path=server)


def test_launched_writer_refuses_with_matching_imported_server(tmp_path, monkeypatch):
    server = tmp_path / "server.py"
    server.write_text(
        SERVER_PATH.read_text().replace(
            'name="verify_words",', 'name="verify_words", annotations=_PERSISTING_LOOKUP_TOOL,'
        )
    )
    monkeypatch.setattr(ledger, "SERVER_PATH", server)
    with pytest.raises(ValueError, match="review_contract_contains_non_read_only_sources_tool"):
        ledger.review_tools(server_path=server)


def test_attempt_validates_launch_before_creating_receipts(tmp_path, monkeypatch):
    server = tmp_path / "missing-server.py"
    monkeypatch.setattr(review_mcp, "sources_server_launch", lambda: (Path("/unused/python"), server))
    receipts = tmp_path / "receipts"
    manifest = tmp_path / "manifest.yaml"
    manifest.write_text("review_id: rev-9628\nattempt_id: att-9628\n")
    with pytest.raises(ValueError, match="review_launched_sources_server_unreadable"):
        review_mcp.prepare_review_attempt(
            review_id="rev-9628",
            attempt_id="att-9628",
            manifest_path=manifest,
            harness="claude",
            receipts_root=receipts,
        )
    assert not receipts.exists()


def test_attempt_launch_resolution_is_shared_by_validation_and_config(tmp_path, monkeypatch):
    server = tmp_path / "server.py"
    server.write_bytes(SERVER_PATH.read_bytes())
    manifest = tmp_path / "manifest.yaml"
    manifest.write_text("review_id: rev-9628\nattempt_id: att-9628\n")
    launches = []

    def launch():
        launches.append(server)
        return Path("/unused/python"), server

    monkeypatch.setattr(review_mcp, "sources_server_launch", launch)
    monkeypatch.setattr(review_mcp, "check_launch_contract", lambda *_args: None)
    plan = review_mcp.prepare_review_attempt(
        review_id="rev-9628",
        attempt_id="att-9628",
        manifest_path=manifest,
        harness="claude",
        receipts_root=tmp_path / "receipts",
    )
    import json

    assert launches == [server]
    assert json.loads(plan.config_path.read_text())["mcpServers"]["sources"]["args"] == [str(server)]


@pytest.mark.parametrize("problem", ["unreadable", "mismatch"])
def test_invalid_launch_creates_no_files_in_existing_attempt_directory(tmp_path, monkeypatch, problem):
    server = tmp_path / "server.py"
    if problem == "mismatch":
        server.write_text("# a different server\n")
    monkeypatch.setattr(review_mcp, "sources_server_launch", lambda: (Path("/unused/python"), server))
    receipts = tmp_path / "receipts"
    attempt = receipts / "rev-9628"
    attempt.mkdir(parents=True)
    manifest = tmp_path / "manifest.yaml"
    manifest.write_text("review_id: rev-9628\nattempt_id: att-9628\n")
    with pytest.raises(ValueError, match=f"review_launched_sources_server_{problem}"):
        review_mcp.prepare_review_attempt(
            review_id="rev-9628",
            attempt_id="att-9628",
            manifest_path=manifest,
            harness="claude",
            receipts_root=receipts,
        )
    assert list(attempt.iterdir()) == []


def test_attempt_created_during_server_validation_is_still_refused(tmp_path, monkeypatch):
    server = tmp_path / "server.py"
    server.write_bytes(SERVER_PATH.read_bytes())
    monkeypatch.setattr(review_mcp, "sources_server_launch", lambda: (Path("/unused/python"), server))
    receipts = tmp_path / "receipts"
    attempt = receipts / "rev-9628"
    manifest = tmp_path / "manifest.yaml"
    manifest.write_text("review_id: rev-9628\nattempt_id: att-9628\n")
    original = review_mcp.review_tools

    def concurrent_attempt(*args, **kwargs):
        attempt.mkdir(parents=True)
        (attempt / "att-9628.jsonl").write_bytes(b"prior-receipts\n")
        return original(*args, **kwargs)

    monkeypatch.setattr(review_mcp, "review_tools", concurrent_attempt)
    with pytest.raises(FileExistsError, match="review attempt 'att-9628' already exists for review 'rev-9628'"):
        review_mcp.prepare_review_attempt(
            review_id="rev-9628",
            attempt_id="att-9628",
            manifest_path=manifest,
            harness="claude",
            receipts_root=receipts,
        )
    assert sorted(path.name for path in attempt.iterdir()) == ["att-9628.jsonl"]
    assert (attempt / "att-9628.jsonl").read_bytes() == b"prior-receipts\n"
