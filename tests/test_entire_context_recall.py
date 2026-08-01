"""Acceptance coverage for the Phase-2 public recall workflows (#6183).

Proves: real Git and ACP explicit-ID bootstrap/admission then recall,
provider-neutral byte equivalence (Codex/Kimi/GLM), deterministic ranking and
caps, scan/pagination behavior, idempotent retry, stale digest / missing
source / tombstone / partial ACP receipt / unsupported kind failure closure,
zero Entire CLI invocation, forbidden-field leakage sweeps over every public
result and capsule, typed provenance traversal, and the 8 KiB handoff cap
without invalid JSON.
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import subprocess
from pathlib import Path

import pytest

from scripts.entire_context import cli, recall
from scripts.entire_context.model import (
    ContextLink,
    LinkKind,
    VerificationEvidence,
    VerificationStatus,
    canonical_json,
    isoformat_z,
    utc_now,
)
from scripts.entire_context.recall import (
    MAX_CAPSULE_BYTES,
    MAX_HANDOFF_ITEMS,
    rank_candidate,
)
from scripts.entire_context.resolvers import (
    REASON_DIGEST_MISMATCH,
    REASON_SOURCE_MISSING,
    REASON_UNSUPPORTED_KIND,
    ResolutionError,
    resolve_acp_conversation,
    resolve_bootstrap,
    resolve_git_commit,
)
from scripts.entire_context.store import AdmitOutcome, ContextLinkStore

ORIGIN_URL = "https://github.com/learn-ukrainian/learn-ukrainian.github.io.git"
NAMESPACE = "git:learn-ukrainian/learn-ukrainian.github.io"
COMMIT_SUBJECT_CANARY = "zyxsubjcanary"
CONV_ID = "conversation_" + "1" * 32

FORBIDDEN_OUTPUT_TOKENS = (
    "prompt",
    "response",
    "transcript",
    "summar",
    "raw_capture",
    "message",
    "artifact",
    "secret",
    "password",
    "credential",
    "api_key",
    "refs/entire",
    "-----BEGIN",
    "ghp_",
    "sk-",
    COMMIT_SUBJECT_CANARY,
)


# ── fixtures: real local git repository ──────────────────────────────────────


def git(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def make_git_repo(tmp_path: Path, *, name: str = "repo") -> Path:
    repo = tmp_path / name
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "test@example.invalid")
    git(repo, "config", "user.name", "tester")
    git(repo, "remote", "add", "origin", ORIGIN_URL)
    return repo


def commit_files(repo: Path, files: dict[str, str], subject: str) -> str:
    for relative, content in files.items():
        path = repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", subject)
    return git(repo, "rev-parse", "HEAD")


@pytest.fixture
def git_repo(tmp_path: Path) -> dict[str, object]:
    repo = make_git_repo(tmp_path)
    sha1 = commit_files(
        repo,
        {"alpha.txt": "one\n", "src/beta.py": "two\n"},
        f"add alpha and beta {COMMIT_SUBJECT_CANARY}",
    )
    sha2 = commit_files(
        repo,
        {"alpha.txt": "one\ntwo\n", "gamma.md": "three\n"},
        f"extend alpha {COMMIT_SUBJECT_CANARY}",
    )
    return {"repo": repo, "sha1": sha1, "sha2": sha2}


# ── fixtures: synthetic ACP receipt plane ────────────────────────────────────

_ACP_DDL = """
CREATE TABLE acp_conversations (
    conversation_id TEXT PRIMARY KEY,
    task_digest TEXT NOT NULL,
    correlation_digest TEXT NOT NULL,
    idempotency_digest TEXT NOT NULL UNIQUE,
    rounds_requested INTEGER NOT NULL CHECK (rounds_requested BETWEEN 1 AND 3),
    participants_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    deadline_at TEXT NOT NULL,
    token_budget INTEGER NOT NULL CHECK (token_budget >= 0),
    content_budget_bytes INTEGER NOT NULL CHECK (content_budget_bytes >= 0)
);
CREATE TABLE acp_conversation_events (
    event_id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL,
    sequence INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    state TEXT NOT NULL,
    sender TEXT,
    recipient TEXT,
    round INTEGER,
    outcome TEXT,
    duration_ms INTEGER,
    token_count INTEGER,
    leg_key_digest TEXT,
    message_id TEXT,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    UNIQUE (conversation_id, sequence)
);
"""


def _insert_acp_event(
    connection: sqlite3.Connection,
    conversation_id: str,
    sequence: int,
    event_type: str,
    *,
    state: str = "IN_PROGRESS",
    sender: str | None = None,
    round_no: int | None = None,
    outcome: str | None = None,
    duration_ms: int | None = None,
    token_count: int | None = None,
    created_at: str,
) -> None:
    connection.execute(
        "INSERT INTO acp_conversation_events("
        "event_id, conversation_id, sequence, event_type, state, sender, recipient,"
        ' "round", outcome, duration_ms, token_count, leg_key_digest, message_id,'
        " metadata_json, created_at) VALUES (?, ?, ?, ?, ?, ?, NULL, ?, ?, ?, ?, NULL, NULL, '{}', ?)",
        (
            f"evt-{conversation_id[-4:]}-{sequence}",
            conversation_id,
            sequence,
            event_type,
            state,
            sender,
            round_no,
            outcome,
            duration_ms,
            token_count,
            created_at,
        ),
    )


def make_acp_plane(
    tmp_path: Path,
    *,
    conversation_id: str = CONV_ID,
    terminal: bool = True,
    name: str = "plane",
    correlation_id: str | None = None,
) -> Path:
    root = tmp_path / name
    root.mkdir()
    connection = sqlite3.connect(root / "comms.sqlite3")
    try:
        connection.executescript(_ACP_DDL)
        connection.execute(
            "INSERT INTO acp_conversations VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                conversation_id,
                "task-digest",
                hashlib.sha256(correlation_id.encode("utf-8")).hexdigest()
                if correlation_id is not None
                else "correlation-digest",
                f"idem-{conversation_id[-4:]}",
                1,
                json.dumps(["claude", "kimi"]),
                "2026-08-01T10:00:00Z",
                "2026-08-01T11:00:00Z",
                10_000,
                1_024,
            ),
        )
        _insert_acp_event(
            connection,
            conversation_id,
            1,
            "CALL_TERMINAL",
            sender="claude",
            round_no=1,
            outcome="ok",
            created_at="2026-08-01T10:00:01Z",
        )
        _insert_acp_event(
            connection,
            conversation_id,
            2,
            "CALL_TERMINAL",
            sender="kimi",
            round_no=1,
            outcome="ok",
            created_at="2026-08-01T10:00:02Z",
        )
        if terminal:
            _insert_acp_event(
                connection,
                conversation_id,
                3,
                "SYNTHESIS_TERMINAL",
                outcome="ok",
                created_at="2026-08-01T10:00:03Z",
            )
            _insert_acp_event(
                connection,
                conversation_id,
                4,
                "STATE",
                state="COMPLETE",
                duration_ms=25,
                token_count=150,
                created_at="2026-08-01T10:00:04Z",
            )
        connection.commit()
    finally:
        connection.close()
    return root


def append_acp_state_event(root: Path, conversation_id: str = CONV_ID) -> None:
    """Advance the terminal receipt so its canonical digest changes."""
    connection = sqlite3.connect(root / "comms.sqlite3")
    try:
        _insert_acp_event(
            connection,
            conversation_id,
            5,
            "STATE",
            state="COMPLETE",
            duration_ms=30,
            token_count=160,
            created_at="2026-08-01T10:05:00Z",
        )
        connection.commit()
    finally:
        connection.close()


# ── helpers ──────────────────────────────────────────────────────────────────


def make_store(tmp_path: Path) -> ContextLinkStore:
    return ContextLinkStore(tmp_path / "context-links.sqlite3")


def admit(store: ContextLinkStore, resolution) -> str:
    result = store.admit(resolution.link, resolution.verification, actor="test")
    assert result.outcome is AdmitOutcome.PROMOTED
    return result.locator_id


def bootstrap_git(store: ContextLinkStore, repo: Path, sha: str) -> str:
    return admit(store, resolve_git_commit(sha, repo=repo))


def bootstrap_acp(store: ContextLinkStore, acp_root: Path, conversation_id: str = CONV_ID, **kwargs) -> str:
    return admit(store, resolve_acp_conversation(conversation_id, acp_root=acp_root, **kwargs))


def run_cli(capsys: pytest.CaptureFixture, *args: str) -> tuple[int, str]:
    code = cli.main(list(args))
    return code, capsys.readouterr().out


def assert_body_free(output: str) -> None:
    lowered = output.lower()
    for token in FORBIDDEN_OUTPUT_TOKENS:
        assert token.lower() not in lowered, f"forbidden token leaked: {token!r}"


# ── real Git and ACP bootstrap/admission, then recall ────────────────────────


def test_git_bootstrap_then_search_recall(
    tmp_path: Path, git_repo: dict[str, object], capsys: pytest.CaptureFixture
) -> None:
    db = tmp_path / "db.sqlite3"
    repo = str(git_repo["repo"])
    sha2 = str(git_repo["sha2"])
    code, out = run_cli(capsys, "bootstrap-git", sha2, "--repo", repo, "--db", str(db))
    assert code == 0
    payload = json.loads(out)
    assert payload["outcome"] == "promoted"
    assert_body_free(out)

    # Exact SHA ranks first.
    code, out = run_cli(capsys, "search", "--query", sha2, "--repo", repo, "--db", str(db))
    assert code == 0
    result = json.loads(out)
    assert [card["canonical_id"] for card in result["results"]] == [sha2]
    card = result["results"][0]
    assert card["matched_fields"][0] == "exact_id"
    assert card["excerpt"]["touched_paths"] == ["alpha.txt", "gamma.md"]
    assert card["excerpt"]["parents"] == [git_repo["sha1"]]

    # Facet needle finds the same verified card.
    code, out = run_cli(capsys, "search", "--query", "gamma.md", "--repo", repo, "--db", str(db))
    assert code == 0
    result = json.loads(out)
    assert [entry["locator_id"] for entry in result["results"]] == [card["locator_id"]]
    assert result["omitted"] == []
    assert_body_free(out)


def test_acp_bootstrap_then_recall(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    acp_root = make_acp_plane(tmp_path)
    db = tmp_path / "db.sqlite3"
    code, out = run_cli(
        capsys,
        "bootstrap-acp",
        CONV_ID,
        "--acp-root",
        str(acp_root),
        "--db",
        str(db),
    )
    assert code == 0
    payload = json.loads(out)
    assert payload["outcome"] == "promoted"
    assert payload["excerpt"]["content_included"] is False
    assert_body_free(out)

    code, out = run_cli(
        capsys,
        "search",
        "--query",
        CONV_ID,
        "--acp-root",
        str(acp_root),
        "--db",
        str(db),
    )
    assert code == 0
    result = json.loads(out)
    assert len(result["results"]) == 1
    card = result["results"][0]
    assert card["kind"] == "acp_conversation"
    assert card["excerpt"]["state"] == "COMPLETE"
    assert card["excerpt"]["content_included"] is False

    # Participant facet needle finds the conversation.
    code, out = run_cli(
        capsys,
        "search",
        "--query",
        "kimi",
        "--acp-root",
        str(acp_root),
        "--db",
        str(db),
    )
    assert code == 0
    assert [c["canonical_id"] for c in json.loads(out)["results"]] == [CONV_ID]
    assert_body_free(out)


# ── provider neutrality ──────────────────────────────────────────────────────


def test_provider_consumer_labels_yield_identical_bytes(
    tmp_path: Path, git_repo: dict[str, object], capsys: pytest.CaptureFixture
) -> None:
    store = make_store(tmp_path)
    bootstrap_git(store, git_repo["repo"], str(git_repo["sha1"]))
    bootstrap_git(store, git_repo["repo"], str(git_repo["sha2"]))
    db = str(store.db_path)
    repo = str(git_repo["repo"])
    outputs = []
    for consumer in ("codex", "kimi", "glm"):
        code, out = run_cli(
            capsys,
            "search",
            "--query",
            "alpha",
            "--repo",
            repo,
            "--db",
            db,
            "--consumer",
            consumer,
        )
        assert code == 0
        outputs.append(out)
    assert outputs[0] == outputs[1] == outputs[2]

    handoff_outputs = []
    for consumer in ("codex", "kimi", "glm"):
        code, out = run_cli(
            capsys,
            "handoff",
            "--query",
            "alpha",
            "--repo",
            repo,
            "--db",
            db,
            "--consumer",
            consumer,
        )
        assert code == 0
        handoff_outputs.append(out)
    assert handoff_outputs[0] == handoff_outputs[1] == handoff_outputs[2]


def test_invalid_consumer_label_is_refused_without_echo(
    tmp_path: Path, git_repo: dict[str, object], capsys: pytest.CaptureFixture
) -> None:
    store = make_store(tmp_path)
    bootstrap_git(store, git_repo["repo"], str(git_repo["sha1"]))
    code, out = run_cli(
        capsys,
        "search",
        "--query",
        "alpha",
        "--repo",
        str(git_repo["repo"]),
        "--db",
        str(store.db_path),
        "--consumer",
        "not a valid consumer!",
    )
    assert code == 2
    assert "not a valid consumer!" not in out


# ── ranking, caps, scan behavior ─────────────────────────────────────────────


def _link_dict(locator_suffix: str, **overrides) -> dict[str, object]:
    link: dict[str, object] = {
        "locator_id": "clink_" + locator_suffix * 64,
        "kind": "git_commit",
        "canonical_namespace": NAMESPACE,
        "canonical_id": "0" * 40,
        "canonical_digest": "sha256:" + "a" * 64,
        "git_sha": "0" * 40,
        "entire_checkpoint_id": None,
        "facets": {},
    }
    link.update(overrides)
    return link


def test_ranking_exact_id_first_casefold_and_tiebreak() -> None:
    exact = rank_candidate(_link_dict("b"), "ab" * 20)
    facet = rank_candidate(_link_dict("a", facets={"title": "Matching Alpha Work"}), "matching alpha work")
    assert exact.score == 0  # no match against zero-sha candidate
    exact = rank_candidate(_link_dict("b", canonical_id="cd" * 20, git_sha="cd" * 20), "CD" * 20)
    assert exact.score >= 1000
    assert exact.matched_fields[0] == "exact_id"
    assert facet.score < 1000  # weighted facets cannot outrank an exact ID
    # Unicode casefold: uppercase needle matches lowercase title.
    folded = rank_candidate(_link_dict("c", facets={"title": "alpha work"}), "ALPHA")
    assert "title" in folded.matched_fields


def test_search_deterministic_limit_and_scan(
    tmp_path: Path, git_repo: dict[str, object], capsys: pytest.CaptureFixture
) -> None:
    store = make_store(tmp_path)
    ids = {
        bootstrap_git(store, git_repo["repo"], str(git_repo["sha1"])),
        bootstrap_git(store, git_repo["repo"], str(git_repo["sha2"])),
    }
    db = str(store.db_path)
    repo = str(git_repo["repo"])

    code, out = run_cli(capsys, "search", "--query", "learn-ukrainian", "--repo", repo, "--db", db)
    assert code == 0
    first = json.loads(out)
    code, out = run_cli(capsys, "search", "--query", "learn-ukrainian", "--repo", repo, "--db", db)
    assert json.loads(out) == first  # deterministic across calls
    assert first["scanned"] == 2
    assert {card["locator_id"] for card in first["results"]} == ids

    # Result cap: limit=1 keeps the deterministic top entry.
    code, out = run_cli(
        capsys,
        "search",
        "--query",
        "learn-ukrainian",
        "--repo",
        repo,
        "--db",
        db,
        "--limit",
        "1",
    )
    top = json.loads(out)
    assert len(top["results"]) == 1
    assert top["results"][0] == first["results"][0]

    # Scan cap: only the first promoted row (locator_id order) is a candidate.
    code, out = run_cli(
        capsys,
        "search",
        "--query",
        "learn-ukrainian",
        "--repo",
        repo,
        "--db",
        db,
        "--scan-limit",
        "1",
    )
    scanned = json.loads(out)
    assert scanned["scanned"] == 1
    expected_first = min(ids)
    assert [card["locator_id"] for card in scanned["results"]] == [expected_first]

    # Exact SHA outranks facet matches regardless of locator order.
    code, out = run_cli(capsys, "search", "--query", str(git_repo["sha2"]), "--repo", repo, "--db", db)
    exact = json.loads(out)
    assert exact["results"][0]["canonical_id"] == git_repo["sha2"]


def test_result_cap_of_ten(tmp_path: Path, git_repo: dict[str, object]) -> None:
    store = make_store(tmp_path)
    for index in range(12):
        sha = commit_files(git_repo["repo"], {f"series/file-{index:02d}.txt": f"{index}\n"}, "series")
        bootstrap_git(store, git_repo["repo"], sha)
    result = recall.search_past_work(store, "series", repo=git_repo["repo"], acp_root=None, limit=50)
    assert result["scanned"] == 12
    assert len(result["results"]) == 10  # hard cap, not the requested 50
    assert result["limit"] == 10


# ── idempotent retry ─────────────────────────────────────────────────────────


def test_bootstrap_retry_is_idempotent(
    tmp_path: Path, git_repo: dict[str, object], capsys: pytest.CaptureFixture
) -> None:
    db = tmp_path / "db.sqlite3"
    repo = str(git_repo["repo"])
    sha = str(git_repo["sha1"])
    code, out = run_cli(capsys, "bootstrap-git", sha, "--repo", repo, "--db", str(db))
    assert code == 0 and json.loads(out)["outcome"] == "promoted"
    code, out = run_cli(capsys, "bootstrap-git", sha, "--repo", repo, "--db", str(db))
    assert code == 0 and json.loads(out)["outcome"] == "already_promoted"
    status = ContextLinkStore(db).status()
    assert status["counts"] == {"promoted": 1}


# ── failure closure ──────────────────────────────────────────────────────────


def test_stale_digest_is_omitted(tmp_path: Path) -> None:
    acp_root = make_acp_plane(tmp_path)
    store = make_store(tmp_path)
    locator_id = bootstrap_acp(store, acp_root)
    append_acp_state_event(acp_root)  # receipt moves on; stored digest is stale

    result = recall.search_past_work(store, CONV_ID, repo=tmp_path, acp_root=acp_root)
    assert result["results"] == []
    assert result["omitted"] == [{"locator_id": locator_id, "reason": REASON_DIGEST_MISMATCH}]
    capsule = recall.prepare_handoff(store, [locator_id], repo=tmp_path, acp_root=acp_root)
    assert capsule["items"] == []
    assert capsule["omitted"] == [{"locator_id": locator_id, "reason": REASON_DIGEST_MISMATCH}]


def test_missing_source_is_omitted_and_bootstrap_refused(
    tmp_path: Path, git_repo: dict[str, object], capsys: pytest.CaptureFixture
) -> None:
    store = make_store(tmp_path)
    locator_id = bootstrap_git(store, git_repo["repo"], str(git_repo["sha1"]))
    other = make_git_repo(tmp_path, name="other")  # no such commit here

    result = recall.search_past_work(store, str(git_repo["sha1"]), repo=other, acp_root=None)
    assert result["results"] == []
    assert result["omitted"] == [{"locator_id": locator_id, "reason": REASON_SOURCE_MISSING}]

    code, out = run_cli(
        capsys,
        "bootstrap-git",
        "f" * 40,
        "--repo",
        str(other),
        "--db",
        str(tmp_path / "other-db.sqlite3"),
    )
    assert code == 2
    assert json.loads(out)["reason"] == REASON_SOURCE_MISSING


def test_acp_link_fails_closed_without_receipt_root(
    tmp_path: Path,
) -> None:
    acp_root = make_acp_plane(tmp_path)
    store = make_store(tmp_path)
    locator_id = bootstrap_acp(store, acp_root)
    result = recall.search_past_work(store, CONV_ID, repo=tmp_path, acp_root=None)
    assert result["results"] == []
    assert result["omitted"] == [{"locator_id": locator_id, "reason": REASON_SOURCE_MISSING}]


def test_tombstoned_claim_never_recalled(tmp_path: Path) -> None:
    store = make_store(tmp_path)
    link = ContextLink(
        kind=LinkKind.GIT_COMMIT,
        canonical_namespace=NAMESPACE,
        canonical_id="0" * 40,
        canonical_digest="sha256:" + "a" * 64,
        git_sha="0" * 40,
    )
    result = store.admit(link, None, actor="test")
    assert result.outcome is AdmitOutcome.REFUSED
    found = recall.search_past_work(store, "0" * 40, repo=tmp_path, acp_root=None)
    assert found["results"] == []
    assert found["scanned"] == 0  # tombstoned rows are not even candidates


def test_partial_acp_receipt_fails_closed(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    acp_root = make_acp_plane(tmp_path, terminal=False)
    db = tmp_path / "db.sqlite3"
    code, out = run_cli(capsys, "bootstrap-acp", CONV_ID, "--acp-root", str(acp_root), "--db", str(db))
    assert code == 2
    assert json.loads(out)["reason"] == "partial_terminal"
    assert not db.exists()  # nothing was admitted


def test_unknown_acp_conversation_fails_closed(tmp_path: Path) -> None:
    acp_root = make_acp_plane(tmp_path)
    with pytest.raises(ResolutionError) as excinfo:
        resolve_acp_conversation("conversation_" + "9" * 32, acp_root=acp_root)
    assert excinfo.value.reason == REASON_SOURCE_MISSING


def test_acp_commit_join_requires_canonical_correlation(tmp_path: Path, git_repo: dict[str, object]) -> None:
    acp_root = make_acp_plane(tmp_path)
    with pytest.raises(ResolutionError) as excinfo:
        resolve_acp_conversation(
            CONV_ID,
            acp_root=acp_root,
            git_sha=str(git_repo["sha1"]),
        )
    assert excinfo.value.reason == REASON_DIGEST_MISMATCH


def test_unsupported_kind_fails_closed(tmp_path: Path, git_repo: dict[str, object]) -> None:
    with pytest.raises(ResolutionError) as excinfo:
        resolve_bootstrap(
            LinkKind.GITHUB_ISSUE,
            "6183",
            repo=git_repo["repo"],
            acp_root=None,
        )
    assert excinfo.value.reason == REASON_UNSUPPORTED_KIND

    # A promoted link of an unsupported kind is omitted from recall, never emitted.
    store = make_store(tmp_path)
    link = ContextLink(
        kind=LinkKind.GITHUB_ISSUE,
        canonical_namespace="github:learn-ukrainian/learn-ukrainian.github.io",
        canonical_id="issue/6183",
        canonical_digest="sha256:" + "c" * 64,
    )
    verification = VerificationEvidence(
        verifier="test",
        canonical_digest=link.canonical_digest,
        status=VerificationStatus.VERIFIED,
        evidence_locator="github:issue/6183",
        checked_at=isoformat_z(utc_now()),
    )
    admitted = store.admit(link, verification, actor="test")
    assert admitted.outcome is AdmitOutcome.PROMOTED
    result = recall.search_past_work(store, "6183", repo=tmp_path, acp_root=None)
    assert result["results"] == []
    assert result["omitted"] == [{"locator_id": admitted.locator_id, "reason": REASON_UNSUPPORTED_KIND}]


def test_entire_cli_is_never_invoked(
    tmp_path: Path,
    git_repo: dict[str, object],
    capsys: pytest.CaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A failing stub `entire` on PATH changes nothing and is never executed."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    marker = tmp_path / "entire-was-called"
    stub = bin_dir / "entire"
    stub.write_text('#!/bin/sh\n/bin/touch "$ENTIRE_STUB_MARKER"\nexit 1\n', encoding="utf-8")
    stub.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("ENTIRE_STUB_MARKER", str(marker))

    store = make_store(tmp_path)
    bootstrap_git(store, git_repo["repo"], str(git_repo["sha1"]))
    code, out = run_cli(
        capsys,
        "search",
        "--query",
        "alpha",
        "--repo",
        str(git_repo["repo"]),
        "--db",
        str(store.db_path),
    )
    assert code == 0
    assert not marker.exists()
    assert len(json.loads(out)["results"]) == 1


# ── query bounds, echo, and persistence hygiene ──────────────────────────────


def test_query_over_256_bytes_refused_without_echo(
    tmp_path: Path, git_repo: dict[str, object], capsys: pytest.CaptureFixture
) -> None:
    store = make_store(tmp_path)
    bootstrap_git(store, git_repo["repo"], str(git_repo["sha1"]))
    needle = "q" * 257
    code, out = run_cli(
        capsys,
        "search",
        "--query",
        needle,
        "--repo",
        str(git_repo["repo"]),
        "--db",
        str(store.db_path),
    )
    assert code == 2
    assert needle not in out
    code, out = run_cli(
        capsys,
        "search",
        "--query",
        "   ",
        "--repo",
        str(git_repo["repo"]),
        "--db",
        str(store.db_path),
    )
    assert code == 2


def test_query_is_never_echoed_or_persisted(
    tmp_path: Path, git_repo: dict[str, object], capsys: pytest.CaptureFixture
) -> None:
    store = make_store(tmp_path)
    bootstrap_git(store, git_repo["repo"], str(git_repo["sha1"]))
    before = store.status()["events"]
    # Uppercase needle matches the casefolded facet but never appears raw.
    needle = "ALPHA.TXT"
    code, out = run_cli(
        capsys,
        "search",
        "--query",
        needle,
        "--repo",
        str(git_repo["repo"]),
        "--db",
        str(store.db_path),
    )
    assert code == 0
    assert needle not in out
    assert json.loads(out)["results"]  # it did match via casefold
    assert store.status()["events"] == before  # no writes
    assert needle.encode() not in store.db_path.read_bytes()


# ── explain-change provenance traversal ──────────────────────────────────────


def test_explain_change_traverses_typed_joins(
    tmp_path: Path, git_repo: dict[str, object], capsys: pytest.CaptureFixture
) -> None:
    sha = str(git_repo["sha2"])
    acp_root = make_acp_plane(tmp_path, correlation_id=sha)
    store = make_store(tmp_path)
    git_locator = bootstrap_git(store, git_repo["repo"], sha)
    acp_locator = bootstrap_acp(store, acp_root, git_sha=sha)

    code, out = run_cli(
        capsys,
        "explain-change",
        "--sha",
        sha,
        "--repo",
        str(git_repo["repo"]),
        "--acp-root",
        str(acp_root),
        "--db",
        str(store.db_path),
    )
    assert code == 0
    payload = json.loads(out)
    assert payload["found"] is True
    node_ids = {node["locator_id"] for node in payload["nodes"]}
    assert node_ids == {git_locator, acp_locator}
    joins = {(edge["from"], edge["to"], edge["join"]) for edge in payload["edges"]}
    assert (git_locator, acp_locator, "referenced_by_commit") in joins
    assert (acp_locator, git_locator, "references_commit") in joins
    # Every node was re-verified and carries a body-free excerpt.
    for node in payload["nodes"]:
        assert "excerpt" in node
        assert node["canonical_digest"].startswith("sha256:")
    assert payload["omitted"] == []
    assert_body_free(out)


def test_explain_change_omits_unverifiable_nodes(tmp_path: Path, git_repo: dict[str, object]) -> None:
    sha = str(git_repo["sha2"])
    acp_root = make_acp_plane(tmp_path, correlation_id=sha)
    store = make_store(tmp_path)
    bootstrap_git(store, git_repo["repo"], sha)
    acp_locator = bootstrap_acp(store, acp_root, git_sha=sha)
    append_acp_state_event(acp_root)  # ACP node goes stale

    result = recall.explain_change(store, git_sha=sha, repo=git_repo["repo"], acp_root=acp_root)
    assert result["found"] is True
    assert {node["kind"] for node in result["nodes"]} == {"git_commit"}
    assert result["edges"] == []  # edges to omitted nodes are dropped
    assert result["omitted"] == [{"locator_id": acp_locator, "reason": REASON_DIGEST_MISMATCH}]


def test_explain_change_unknown_seed_not_found(
    tmp_path: Path, git_repo: dict[str, object], capsys: pytest.CaptureFixture
) -> None:
    store = make_store(tmp_path)
    bootstrap_git(store, git_repo["repo"], str(git_repo["sha1"]))
    code, out = run_cli(
        capsys,
        "explain-change",
        "--locator-id",
        "clink_" + "f" * 64,
        "--repo",
        str(git_repo["repo"]),
        "--db",
        str(store.db_path),
    )
    assert code == 1
    assert json.loads(out)["found"] is False


# ── prepare-handoff capsule ──────────────────────────────────────────────────


def test_handoff_item_cap_and_deterministic_order(tmp_path: Path, git_repo: dict[str, object]) -> None:
    store = make_store(tmp_path)
    locators = []
    for index in range(MAX_HANDOFF_ITEMS + 1):
        sha = commit_files(git_repo["repo"], {f"cap/item-{index:02d}.txt": f"{index}\n"}, "cap")
        locators.append(bootstrap_git(store, git_repo["repo"], sha))
    capsule = recall.prepare_handoff(store, list(reversed(locators)), repo=git_repo["repo"], acp_root=None)
    assert len(capsule["items"]) == MAX_HANDOFF_ITEMS
    assert capsule["complete"] is False
    ordered = sorted(locators)
    assert [item["locator_id"] for item in capsule["items"]] == ordered[:MAX_HANDOFF_ITEMS]
    assert capsule["omitted"] == [{"locator_id": ordered[MAX_HANDOFF_ITEMS], "reason": "handoff_item_cap"}]


def test_handoff_byte_cap_never_emits_invalid_json(
    tmp_path: Path, git_repo: dict[str, object], capsys: pytest.CaptureFixture
) -> None:
    store = make_store(tmp_path)
    locators = []
    for commit_index in range(3):
        files = {
            (
                f"dir.{commit_index}/mod.{file_index:02d}.controller.component.extension.service.adapter.registry.txt"
            ): "x\n"
            for file_index in range(30)
        }
        sha = commit_files(git_repo["repo"], files, "bulk")
        locators.append(bootstrap_git(store, git_repo["repo"], sha))

    args = ["handoff", "--repo", str(git_repo["repo"]), "--db", str(store.db_path)]
    for locator_id in locators:
        args.extend(["--locator-id", locator_id])
    code, out = run_cli(capsys, *args)
    assert code == 0
    capsule = json.loads(out)  # always valid JSON, never a truncated stream
    assert len(out.encode("utf-8")) <= MAX_CAPSULE_BYTES + 1  # + newline
    assert len(canonical_json(capsule).encode("utf-8")) <= MAX_CAPSULE_BYTES
    assert capsule["complete"] is False
    assert 1 <= len(capsule["items"]) < 3
    reasons = [entry["reason"] for entry in capsule["omitted"]]
    assert "capsule_budget" in reasons
    assert_body_free(out)


def test_handoff_many_omissions_stays_under_byte_cap(tmp_path: Path) -> None:
    store = make_store(tmp_path)
    store.submit_claim(
        ContextLink(
            kind=LinkKind.GIT_COMMIT,
            canonical_namespace=NAMESPACE,
            canonical_id="f" * 40,
            canonical_digest="sha256:" + "f" * 64,
            git_sha="f" * 40,
        ),
        actor="test",
    )
    locator_ids = [f"clink_{index:064x}" for index in range(100)]
    capsule = recall.prepare_handoff(store, locator_ids, repo=tmp_path, acp_root=None)
    assert capsule["items"] == []
    assert capsule["complete"] is False
    assert capsule["omissions_truncated"] is True
    assert len(canonical_json(capsule).encode("utf-8")) <= MAX_CAPSULE_BYTES


def test_handoff_rejects_unbounded_seed_set(tmp_path: Path) -> None:
    store = make_store(tmp_path)
    locator_ids = [f"clink_{index:064x}" for index in range(501)]
    with pytest.raises(recall.RecallInputError, match="handoff_seed_limit"):
        recall.prepare_handoff(store, locator_ids, repo=tmp_path, acp_root=None)


def test_handoff_from_query_uses_only_verified_results(
    tmp_path: Path, git_repo: dict[str, object], capsys: pytest.CaptureFixture
) -> None:
    sha = str(git_repo["sha2"])
    acp_root = make_acp_plane(tmp_path, correlation_id=sha)
    store = make_store(tmp_path)
    bootstrap_git(store, git_repo["repo"], sha)
    stale_locator = bootstrap_acp(store, acp_root, git_sha=sha)
    append_acp_state_event(acp_root)

    code, out = run_cli(
        capsys,
        "handoff",
        "--locator-id",
        stale_locator,
        "--query",
        sha,
        "--repo",
        str(git_repo["repo"]),
        "--acp-root",
        str(acp_root),
        "--db",
        str(store.db_path),
    )
    assert code == 0
    capsule = json.loads(out)
    assert [item["kind"] for item in capsule["items"]] == ["git_commit"]
    assert {entry["reason"] for entry in capsule["omitted"]} == {REASON_DIGEST_MISMATCH}
    # The handoff is a capsule of verified locators/excerpts, never a summary.
    assert "summary" not in capsule
    assert [item["canonical_id"] for item in capsule["items"]] == [sha]


def test_handoff_requires_a_seed(tmp_path: Path, git_repo: dict[str, object], capsys: pytest.CaptureFixture) -> None:
    store = make_store(tmp_path)
    bootstrap_git(store, git_repo["repo"], str(git_repo["sha1"]))
    code, out = run_cli(capsys, "handoff", "--repo", str(git_repo["repo"]), "--db", str(store.db_path))
    assert code == 2
    assert "seed_invalid" in out


def test_handoff_rejects_malformed_locator_without_echo(
    tmp_path: Path, git_repo: dict[str, object], capsys: pytest.CaptureFixture
) -> None:
    store = make_store(tmp_path)
    bootstrap_git(store, git_repo["repo"], str(git_repo["sha1"]))
    code, out = run_cli(
        capsys,
        "handoff",
        "--locator-id",
        "not-a-locator",
        "--repo",
        str(git_repo["repo"]),
        "--db",
        str(store.db_path),
    )
    assert code == 2
    assert "not-a-locator" not in out


# ── projection availability posture ──────────────────────────────────────────


def test_search_missing_projection_is_clean(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    code, out = run_cli(capsys, "search", "--query", "alpha", "--db", str(tmp_path / "missing.sqlite3"))
    assert code == 0
    payload = json.loads(out)
    assert payload["available"] is False
    assert payload["reason"] == "projection_missing"
    assert not (tmp_path / "missing.sqlite3").exists()  # reads never create state


def test_handoff_missing_projection_is_clean(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    code, out = run_cli(
        capsys,
        "handoff",
        "--locator-id",
        "clink_" + "a" * 64,
        "--db",
        str(tmp_path / "missing.sqlite3"),
    )
    assert code == 0
    assert json.loads(out)["available"] is False


# ── forbidden-field leakage sweep over every public command ──────────────────


def test_all_public_outputs_are_body_free(
    tmp_path: Path, git_repo: dict[str, object], capsys: pytest.CaptureFixture
) -> None:
    acp_root = make_acp_plane(tmp_path)
    db = str(tmp_path / "db.sqlite3")
    repo = str(git_repo["repo"])
    sha = str(git_repo["sha2"])
    outputs = []
    for args in (
        ("bootstrap-git", sha, "--repo", repo, "--db", db),
        ("bootstrap-acp", CONV_ID, "--acp-root", str(acp_root), "--db", db),
        ("status", "--db", db),
        ("search", "--query", "alpha", "--repo", repo, "--acp-root", str(acp_root), "--db", db),
        ("search", "--query", "no-such-needle", "--repo", repo, "--db", db),
        ("explain-change", "--sha", sha, "--repo", repo, "--acp-root", str(acp_root), "--db", db),
        ("handoff", "--query", "alpha", "--repo", repo, "--acp-root", str(acp_root), "--db", db),
    ):
        code, out = run_cli(capsys, *args)
        assert code == 0, args
        outputs.append(out)
    combined = "".join(outputs)
    assert_body_free(combined)
    # The commit subject canary never reaches any public output.
    assert COMMIT_SUBJECT_CANARY not in combined
