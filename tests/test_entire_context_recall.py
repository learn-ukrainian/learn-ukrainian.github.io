"""Acceptance coverage for the Phase-2 public recall workflows (#6183).

Proves: real Git, ACP, and rollover explicit-ID bootstrap/admission then
recall, provider-neutral byte equivalence (Codex/Kimi/GLM), deterministic
ranking and caps, scan/pagination behavior, idempotent retry, stale digest /
missing source / tombstone / partial ACP receipt / unsupported kind failure
closure, zero Entire CLI invocation, forbidden-field leakage sweeps over every
public result and capsule, typed provenance traversal, and the 8 KiB handoff
cap without invalid JSON.

The rollover resolver coverage builds a real registry fixture through
``rollover_registry.record_from_lease`` and exercises the full
bootstrap → search → explain/handoff recall pipeline, digest determinism,
lifecycle-field digest mismatch, missing/corrupt source failure closure,
body-free canary sweeps, and read-only state-root posture.
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
    MAX_SEARCH_OMISSIONS,
    rank_candidate,
)
from scripts.entire_context.resolvers import (
    REASON_DIGEST_MISMATCH,
    REASON_RESOLUTION_ERROR,
    REASON_SOURCE_MISSING,
    REASON_UNSUPPORTED_KIND,
    ResolutionError,
    resolve_acp_conversation,
    resolve_bootstrap,
    resolve_git_commit,
    resolve_rollover,
    rollover_projection,
    rollover_projection_digest,
)
from scripts.entire_context.store import AdmitOutcome, ContextLinkStore
from scripts.orchestration import task_identity
from scripts.orchestration.task_family import rollover, rollover_registry

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


def promote_link(store: ContextLinkStore, link: ContextLink) -> str:
    verification = VerificationEvidence(
        verifier="test",
        canonical_digest=link.canonical_digest,
        status=VerificationStatus.VERIFIED,
        evidence_locator="test:synthetic-link",
        checked_at=isoformat_z(utc_now()),
    )
    result = store.admit(link, verification, actor="test")
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


def test_git_projection_supports_merge_parents_and_rejects_tree(tmp_path: Path) -> None:
    repo = make_git_repo(tmp_path)
    base = commit_files(repo, {"base.txt": "base\n"}, "base")
    git(repo, "checkout", "-qb", "left")
    left = commit_files(repo, {"left.txt": "left\n"}, "left")
    git(repo, "checkout", "-qb", "right", base)
    right = commit_files(repo, {"right.txt": "right\n"}, "right")
    git(repo, "merge", "--no-ff", "-qm", "merge", "left")
    merge_sha = git(repo, "rev-parse", "HEAD")

    resolution = resolve_git_commit(merge_sha, repo=repo)
    assert resolution.excerpt["parents"] == sorted([left, right])
    assert resolution.excerpt["touched_paths"] == ["left.txt"]

    tree_sha = git(repo, "rev-parse", "HEAD^{tree}")
    with pytest.raises(ResolutionError) as excinfo:
        resolve_git_commit(tree_sha, repo=repo)
    assert excinfo.value.reason == REASON_SOURCE_MISSING


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


def test_search_omission_metadata_is_capped(tmp_path: Path, git_repo: dict[str, object]) -> None:
    store = make_store(tmp_path)
    for index in range(MAX_SEARCH_OMISSIONS + 1):
        sha = commit_files(
            git_repo["repo"],
            {f"stale-series/file-{index:02d}.txt": f"{index}\n"},
            "stale-series",
        )
        bootstrap_git(store, git_repo["repo"], sha)

    missing_repo = make_git_repo(tmp_path, name="missing")
    result = recall.search_past_work(
        store,
        "stale-series",
        repo=missing_repo,
        acp_root=None,
        limit=10,
    )
    assert result["results"] == []
    assert len(result["omitted"]) == MAX_SEARCH_OMISSIONS
    assert result["omissions_truncated"] is True


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
    assert payload["relation_scan"]["truncated"] is False
    assert payload["complete"] is True
    assert payload["truncation_reasons"] == []
    assert_body_free(out)

    code, out = run_cli(
        capsys,
        "explain-change",
        "--canonical-id",
        sha,
        "--repo",
        str(git_repo["repo"]),
        "--acp-root",
        str(acp_root),
        "--db",
        str(store.db_path),
    )
    assert code == 0
    assert json.loads(out)["found"] is True


def test_find_related_limit_zero_is_empty(tmp_path: Path, git_repo: dict[str, object]) -> None:
    sha = str(git_repo["sha2"])
    acp_root = make_acp_plane(tmp_path, correlation_id=sha)
    store = make_store(tmp_path)
    git_locator = bootstrap_git(store, git_repo["repo"], sha)
    bootstrap_acp(store, acp_root, git_sha=sha)
    seed = store.lookup(git_locator)
    assert seed is not None
    related = store.find_related(seed, limit=0)
    assert related.items == ()
    assert related.examined == 0
    assert related.truncated is True


def test_explain_change_reports_typed_join_truncation(tmp_path: Path, git_repo: dict[str, object]) -> None:
    sha = str(git_repo["sha2"])
    store = make_store(tmp_path)
    seed_locator = bootstrap_git(store, git_repo["repo"], sha)
    for index in range(51):
        promote_link(
            store,
            ContextLink(
                kind=LinkKind.GITHUB_ISSUE,
                canonical_namespace="github:test/repo",
                canonical_id=sha,
                canonical_digest="sha256:" + hashlib.sha256(f"related-{index}".encode()).hexdigest(),
            ),
        )

    result = recall.explain_change(
        store,
        locator_id=seed_locator,
        repo=git_repo["repo"],
        acp_root=None,
    )
    assert result["relation_scan"] == {"examined": 50, "truncated": True}
    assert result["complete"] is False
    assert "relation_scan_cap" in result["truncation_reasons"]


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


# ── rollover registry resolver (#6183) ───────────────────────────────────────

# Canary tokens deliberately placed in body-bearing fields that the strict
# body-free projection must never emit.
ROLLOVER_TITLE_CANARY = "zyx-title-canary-991"
ROLLOVER_THREAD_CANARY = "zyx-thread-canary-992"
ROLLOVER_PATH_CANARY = "zyx-path-canary"
ROLLOVER_NATIVE_CANARY = "zyx-native-canary-994"
ROLLOVER_CONFIRMED_BY_CANARY = "zyx-confirmed-by-canary-995"

ROLLOVER_CANARIES = (
    ROLLOVER_TITLE_CANARY,
    ROLLOVER_THREAD_CANARY,
    ROLLOVER_PATH_CANARY,
    ROLLOVER_NATIVE_CANARY,
    ROLLOVER_CONFIRMED_BY_CANARY,
)

ROLLOVER_AGENT = "codex"
ROLLOVER_LINEAGE = "lineage-entire-context"
ROLLOVER_ROLLOVER_ID = "rollover-entire-context"
ROLLOVER_CANONICAL_ID = f"{ROLLOVER_AGENT}/{ROLLOVER_LINEAGE}/{ROLLOVER_ROLLOVER_ID}"


def _build_rollover_lease(
    *,
    agent: str = ROLLOVER_AGENT,
    lineage: str = ROLLOVER_LINEAGE,
    rollover_id: str = ROLLOVER_ROLLOVER_ID,
) -> dict:
    """Build a confirmed lease with canaries in every body-bearing field."""
    source = ROLLOVER_THREAD_CANARY
    replacement_id = f"replacement-{ROLLOVER_THREAD_CANARY}"
    prepared_at = "2026-08-01T09:00:00Z"
    identity = task_identity.build_identity(
        repository=task_identity.DEFAULT_REPOSITORY,
        stream_epic=4707,
        stream_epic_url=None,
        github_issue_number=6183,
        github_issue_url=None,
        semantic_title=f"Rollover resolver {ROLLOVER_TITLE_CANARY}",
        task_family="thread-rollover",
        role=agent,
        predecessor_task_id=source,
        replacement_task_id=None,
        lineage_id=lineage,
        generation=1,
        terminal_goal="merge",
    )
    title_transition = task_identity.new_title_transition(
        harness=task_identity.default_harness(agent),
        visible_title_value=identity["visible_title"],
        prepared_at=prepared_at,
    )
    family_id, operation_id = rollover.transition_identity(
        lineage_id=lineage,
        generation=1,
        rollover_id=rollover_id,
    )
    packet_prefix = f".agent/thread-rollovers/{agent}/{lineage}/generation-0001/{rollover_id}"
    identity, title_transition = task_identity.bind_replacement(
        identity,
        title_transition,
        replacement_task_id=replacement_id,
        evidence=f"Exact replacement binding {ROLLOVER_NATIVE_CANARY}.",
        now=prepared_at,
    )
    if title_transition["native_title_supported"]:
        identity, title_transition = task_identity.record_title_acknowledgement(
            identity,
            title_transition,
            replacement_task_id=replacement_id,
            succeeded=True,
            evidence=f"Native ack {ROLLOVER_NATIVE_CANARY}.",
            error="",
            now=prepared_at,
        )
        identity, title_transition = task_identity.record_title_readback(
            identity,
            title_transition,
            replacement_task_id=replacement_id,
            observed_title=identity["visible_title"],
            succeeded=True,
            evidence=f"Native readback {ROLLOVER_NATIVE_CANARY}.",
            error="",
            now=prepared_at,
        )
    identity = task_identity.mark_confirmed(
        identity,
        title_transition,
        replacement_task_id=replacement_id,
    )
    return {
        "schema_version": 2,
        "agent": agent,
        "lineage_id": lineage,
        "rollover_id": rollover_id,
        "active": {
            "thread_id": source,
            "automation_id": "automation-1",
            "generation": 0,
            "lineage_id": lineage,
            "started_at": prepared_at,
            "last_seen_at": prepared_at,
        },
        "replacement": {
            "rollover_id": rollover_id,
            "lineage_id": lineage,
            "generation": 1,
            "status": "started",
            "prepared_at": prepared_at,
            "thread_id": replacement_id,
            "resumed_thread_id": None,
            "confirmed_at": prepared_at,
            "display": {"title": identity["visible_title"], "title_source": "task_identity_v1"},
            "identity": identity,
            "title_transition": title_transition,
            "tracking": {"stream_epic": 4707, "github_issue": 6183},
            "native_lifecycle": {
                "family_id": family_id,
                "operation_id": operation_id,
                "source_thread_id": source,
                "replacement_thread_id": replacement_id,
                "status": "replacement_created_bound",
            },
            "runtime_path": packet_prefix,
            "handoff_path": f"{packet_prefix}/handoff-{ROLLOVER_PATH_CANARY}.md",
            "bootstrap_prompt_path": f"{packet_prefix}/bootstrap.md",
            "semantic_snapshot_path": f"{packet_prefix}/semantic-snapshot.json",
            "strict_probe_path": f"{packet_prefix}/strict-probe.json",
            "strict_questions_path": f"{packet_prefix}/strict-questions.json",
            "strict_answers_path": f"{packet_prefix}/strict-answers.json",
            "strict_verdict_path": f"{packet_prefix}/strict-verdict-{ROLLOVER_PATH_CANARY}.json",
            "canary_proof_path": f"{packet_prefix}/canary-pass-{ROLLOVER_PATH_CANARY}.json",
            "strict_verdict": {"verdict": "PASS", "correct": 10, "k": 10},
            "canary_proof": {"status": "PASS"},
        },
        "cleanup": {
            "old_automation_ready_to_delete": True,
            "reason": "test",
            "confirmed_by": ROLLOVER_CONFIRMED_BY_CANARY,
        },
        "updated_at": prepared_at,
    }


def _persist_rollover_fixture(state_root: Path, lease: dict | None = None) -> Path:
    """Build a registry record through ``record_from_lease`` and persist it to the canonical path."""
    lease = lease or _build_rollover_lease()
    lease_path = state_root / ".agent" / "thread-rollovers" / lease["agent"] / lease["lineage_id"] / "lease.json"
    lease_path.parent.mkdir(parents=True, exist_ok=True)
    lease_path.write_text(json.dumps(lease, indent=2) + "\n", encoding="utf-8")
    record = rollover_registry.record_from_lease(state_root, lease_path, lease)
    canonical = rollover_registry.record_path(
        state_root,
        agent=lease["agent"],
        lineage_id=lease["lineage_id"],
        rollover_id=lease["rollover_id"],
    )
    canonical.parent.mkdir(parents=True, exist_ok=True)
    canonical.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return canonical


def _assert_no_rollover_canaries(output: str) -> None:
    for token in ROLLOVER_CANARIES:
        assert token not in output, f"rollover body canary leaked: {token!r}"


def _snapshot_files(root: Path) -> dict[str, int]:
    return {str(p.relative_to(root)): p.stat().st_mtime_ns for p in root.rglob("*") if p.is_file()}


def test_rollover_bootstrap_then_search_explain_and_handoff(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    """Full recall pipeline from a registry fixture built through ``record_from_lease``."""
    root = tmp_path / "state"
    root.mkdir()
    _persist_rollover_fixture(root)
    db = str(tmp_path / "db.sqlite3")

    # bootstrap-rollover CLI → promoted
    code, out = run_cli(
        capsys,
        "bootstrap-rollover",
        "--agent",
        ROLLOVER_AGENT,
        "--lineage-id",
        ROLLOVER_LINEAGE,
        "--rollover-id",
        ROLLOVER_ROLLOVER_ID,
        "--rollover-root",
        str(root),
        "--db",
        db,
    )
    assert code == 0
    payload = json.loads(out)
    assert payload["outcome"] == "promoted"
    assert payload["excerpt"]["state"] == "CONFIRMED"
    assert payload["excerpt"]["schema"] == "rollover-projection.v1"
    assert payload["excerpt"]["key"]["agent"] == ROLLOVER_AGENT
    assert_body_free(out)
    _assert_no_rollover_canaries(out)

    # search finds the verified rollover card
    code, out = run_cli(
        capsys,
        "search",
        "--query",
        ROLLOVER_LINEAGE,
        "--repo",
        str(tmp_path),
        "--rollover-root",
        str(root),
        "--db",
        db,
    )
    assert code == 0
    result = json.loads(out)
    assert len(result["results"]) == 1
    card = result["results"][0]
    assert card["kind"] == "rollover"
    assert card["canonical_id"] == ROLLOVER_CANONICAL_ID
    assert card["excerpt"]["state"] == "CONFIRMED"
    assert card["excerpt"]["lifecycle_state"] == "confirmed"
    assert card["excerpt"]["stream_epic"] == 4707
    assert card["excerpt"]["cleanup_authorized"] is True
    assert card["excerpt"]["strict_recall_state"] == "passed"
    assert card["excerpt"]["canary_state"] == "passed"
    assert card["excerpt"]["confirmation_state"] == "confirmed"
    assert_body_free(out)
    _assert_no_rollover_canaries(out)

    # explain-change traverses the single rollover node
    code, out = run_cli(
        capsys,
        "explain-change",
        "--canonical-id",
        ROLLOVER_CANONICAL_ID,
        "--repo",
        str(tmp_path),
        "--rollover-root",
        str(root),
        "--db",
        db,
    )
    assert code == 0
    payload = json.loads(out)
    assert payload["found"] is True
    assert len(payload["nodes"]) == 1
    assert payload["nodes"][0]["kind"] == "rollover"
    assert payload["omitted"] == []
    assert_body_free(out)
    _assert_no_rollover_canaries(out)

    # handoff capsule includes the verified rollover item
    code, out = run_cli(
        capsys,
        "handoff",
        "--locator-id",
        card["locator_id"],
        "--repo",
        str(tmp_path),
        "--rollover-root",
        str(root),
        "--db",
        db,
    )
    assert code == 0
    capsule = json.loads(out)
    assert len(capsule["items"]) == 1
    assert capsule["items"][0]["kind"] == "rollover"
    assert capsule["omitted"] == []
    assert_body_free(out)
    _assert_no_rollover_canaries(out)


def test_rollover_bootstrap_without_root_fails_closed(
    tmp_path: Path,
    capsys: pytest.CaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The public CLI returns a machine refusal instead of raising a NameError."""
    monkeypatch.delenv("ENTIRE_CONTEXT_ROLLOVER_ROOT", raising=False)
    code, out = run_cli(
        capsys,
        "bootstrap-rollover",
        "--agent",
        ROLLOVER_AGENT,
        "--lineage-id",
        ROLLOVER_LINEAGE,
        "--rollover-id",
        ROLLOVER_ROLLOVER_ID,
        "--db",
        str(tmp_path / "db.sqlite3"),
    )

    assert code == 2
    assert json.loads(out) == {"outcome": "refused", "reason": REASON_SOURCE_MISSING}
    assert not (tmp_path / "db.sqlite3").exists()


def test_rollover_resolution_is_deterministic(tmp_path: Path) -> None:
    """Two resolutions yield byte-identical digest, excerpt, and identity."""
    root = tmp_path / "state"
    root.mkdir()
    _persist_rollover_fixture(root)

    first = resolve_rollover(
        ROLLOVER_AGENT,
        ROLLOVER_LINEAGE,
        ROLLOVER_ROLLOVER_ID,
        state_root=root,
        now=utc_now(),
    )
    second = resolve_rollover(
        ROLLOVER_AGENT,
        ROLLOVER_LINEAGE,
        ROLLOVER_ROLLOVER_ID,
        state_root=root,
        now=utc_now(),
    )
    assert first.link.canonical_digest == second.link.canonical_digest
    assert first.link.canonical_id == second.link.canonical_id == ROLLOVER_CANONICAL_ID
    assert first.link.locator_id == second.link.locator_id
    assert first.excerpt == second.excerpt
    assert first.verification.canonical_digest == second.verification.canonical_digest

    # The digest is independently reproducible from the projection function.
    record = rollover_registry.load_record(
        root,
        agent=ROLLOVER_AGENT,
        lineage_id=ROLLOVER_LINEAGE,
        rollover_id=ROLLOVER_ROLLOVER_ID,
    )
    assert rollover_projection_digest(rollover_projection(record)) == first.link.canonical_digest


def test_rollover_lifecycle_field_change_yields_digest_mismatch(tmp_path: Path) -> None:
    """A lifecycle-field change in the record produces a digest mismatch on recall."""
    root = tmp_path / "state"
    root.mkdir()
    _persist_rollover_fixture(root)
    store = make_store(tmp_path)
    locator_id = admit(
        store,
        resolve_rollover(
            ROLLOVER_AGENT,
            ROLLOVER_LINEAGE,
            ROLLOVER_ROLLOVER_ID,
            state_root=root,
        ),
    )

    canonical = rollover_registry.record_path(
        root,
        agent=ROLLOVER_AGENT,
        lineage_id=ROLLOVER_LINEAGE,
        rollover_id=ROLLOVER_ROLLOVER_ID,
    )
    record = json.loads(canonical.read_text(encoding="utf-8"))
    record["last_successful_boundary"] = "PREDECESSOR_ARCHIVED"
    record["predecessor_archival"]["state"] = "archived"
    rollover_registry.validate_record(record)
    canonical.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")

    result = recall.search_past_work(
        store,
        ROLLOVER_LINEAGE,
        repo=tmp_path,
        acp_root=None,
        rollover_root=root,
    )
    assert result["results"] == []
    assert result["omitted"] == [{"locator_id": locator_id, "reason": REASON_DIGEST_MISMATCH}]


def test_rollover_missing_and_corrupt_records_fail_closed(tmp_path: Path) -> None:
    """Missing records fail as source_missing; corrupt records fail as resolution_error."""
    # No fixture persisted → source_missing
    with pytest.raises(ResolutionError) as excinfo:
        resolve_rollover(
            ROLLOVER_AGENT,
            ROLLOVER_LINEAGE,
            ROLLOVER_ROLLOVER_ID,
            state_root=tmp_path,
        )
    assert excinfo.value.reason == REASON_SOURCE_MISSING

    # Bootstrap without a rollover root → source_missing
    with pytest.raises(ResolutionError) as excinfo:
        resolve_bootstrap(
            LinkKind.ROLLOVER,
            ROLLOVER_CANONICAL_ID,
            repo=tmp_path,
            acp_root=None,
            rollover_root=None,
        )
    assert excinfo.value.reason == REASON_SOURCE_MISSING

    # Corrupt JSON at the canonical path → resolution_error
    canonical = rollover_registry.record_path(
        tmp_path,
        agent=ROLLOVER_AGENT,
        lineage_id=ROLLOVER_LINEAGE,
        rollover_id=ROLLOVER_ROLLOVER_ID,
    )
    canonical.parent.mkdir(parents=True, exist_ok=True)
    canonical.write_text("{not-valid-json\n", encoding="utf-8")
    with pytest.raises(ResolutionError) as excinfo:
        resolve_rollover(
            ROLLOVER_AGENT,
            ROLLOVER_LINEAGE,
            ROLLOVER_ROLLOVER_ID,
            state_root=tmp_path,
        )
    assert excinfo.value.reason == REASON_RESOLUTION_ERROR


def test_rollover_canaries_never_leak(tmp_path: Path) -> None:
    """Title, thread-ID, path, native-payload, and confirmed-by canaries never appear in output."""
    root = tmp_path / "state"
    root.mkdir()
    _persist_rollover_fixture(root)
    resolution = resolve_rollover(
        ROLLOVER_AGENT,
        ROLLOVER_LINEAGE,
        ROLLOVER_ROLLOVER_ID,
        state_root=root,
    )
    combined = canonical_json(resolution.link.to_dict()) + canonical_json(resolution.excerpt)
    combined += canonical_json(resolution.verification.to_dict())
    assert_body_free(combined)
    _assert_no_rollover_canaries(combined)


def test_remaining_unsupported_kinds_still_fail_closed(tmp_path: Path) -> None:
    """Every kind except git/acp/rollover fails closed with unsupported_kind."""
    for kind in (
        LinkKind.GITHUB_ISSUE,
        LinkKind.GITHUB_PR,
        LinkKind.FLEET_RECEIPT,
        LinkKind.FORMAL_REVIEW,
        LinkKind.MONITOR_RUN,
    ):
        with pytest.raises(ResolutionError) as excinfo:
            resolve_bootstrap(
                kind,
                "test-identifier",
                repo=tmp_path,
                acp_root=None,
                rollover_root=None,
            )
        assert excinfo.value.reason == REASON_UNSUPPORTED_KIND


def test_rollover_resolution_never_invokes_entire_or_writes_state_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No ``entire`` invocation and no writes under the rollover state root."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    marker = tmp_path / "entire-was-called"
    stub = bin_dir / "entire"
    stub.write_text('#!/bin/sh\n/bin/touch "$ENTIRE_STUB_MARKER"\nexit 1\n', encoding="utf-8")
    stub.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("ENTIRE_STUB_MARKER", str(marker))

    root = tmp_path / "state"
    root.mkdir()
    _persist_rollover_fixture(root)

    before = _snapshot_files(root)
    resolution = resolve_rollover(
        ROLLOVER_AGENT,
        ROLLOVER_LINEAGE,
        ROLLOVER_ROLLOVER_ID,
        state_root=root,
    )
    assert _snapshot_files(root) == before  # resolution is read-only

    store = make_store(tmp_path)
    locator_id = admit(store, resolution)
    result = recall.search_past_work(
        store,
        ROLLOVER_LINEAGE,
        repo=tmp_path,
        acp_root=None,
        rollover_root=root,
    )
    assert len(result["results"]) == 1
    assert _snapshot_files(root) == before  # recall is also read-only
    assert not marker.exists()  # entire was never invoked
