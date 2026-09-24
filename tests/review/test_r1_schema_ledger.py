"""Part R1: review schema, receipt ledger, and the active validator.

Fixtures are written per case under tmp_path. Placeholder strings only.
No test calls the live sources database.
"""

from __future__ import annotations

import ast
import asyncio
import hashlib
import importlib.util
import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from scripts.curriculum.evidence.words import strip_combining_stress
from scripts.review.receipts.ledger import (
    ENV_KEYS,
    REVIEW_TOOLS,
    LedgerError,
    LedgerHashStaleLastLine,
    append,
    collect_snapshots,
    create_empty_ledger,
    dumps,
    lookup,
    records,
    session_from_environ,
)
from scripts.review.receipts.outcomes import classify_outcome
from scripts.review.validate import codes
from scripts.review.validate.validate import fold_quote, main, validate_review

REPO = Path(__file__).resolve().parents[2]
SERVER_PATH = REPO / ".mcp" / "servers" / "sources" / "server.py"
LEDGER_PATH = REPO / "scripts" / "review" / "receipts" / "ledger.py"
PLAN_CHECKS = (
    "closing_shape",
    "title_describes_job",
    "title_quantities",
    "quoted_forms",
    "sequencing",
    "sizing",
    "inventory",
    "activities",
    "evidence_fit",
    "standard_and_ulp",
)
LESSON_CHECKS = ("job", "language", "learner_fit", "activity", "evidence_use", "english", "fact")
SNAPSHOTS = {
    "sources_db": {
        "digest": "11" * 32,
        "metadata": {
            "scheme": "file-meta-v1",
            "size_bytes": 13,
            "mtime_ns": 1,
            "journal_mode": "wal",
            "wal_bytes": 0,
            "wal_mtime_ns": None,
        },
    },
    "vesum": {"digest": "22" * 32, "metadata": {"canonical_jsonl_sha256": "22" * 32}},
    "trie": {"digest": "33" * 32},
}


def _run(coro):
    return asyncio.run(coro)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_manifest(path: Path, *, recap: bool = False) -> str:
    path.write_text(f"recap: {'true' if recap else 'false'}\nlabel: fixture\n", encoding="utf-8")
    return _sha(path)


def _lesson() -> dict:
    return {
        "lesson": {"level": "a1", "slug": "fixture-module", "n": 1},
        "units": [
            {
                "tab": "urok",
                "activity": None,
                "item": None,
                "block": 0,
                "role": "narration",
                "text": "lesson prose alpha",
            },
            {
                "tab": "vpravy",
                "activity": "act-1",
                "item": 0,
                "block": 0,
                "role": "item_prompt",
                "text": "alpha-item-text",
            },
            {
                "tab": "vpravy",
                "activity": "act-2",
                "item": 0,
                "block": 0,
                "role": "item_prompt",
                "text": "other-item-text",
            },
        ],
    }


def _dump(path: Path, data: dict) -> None:
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _review(
    *,
    kind: str,
    manifest_hash: str,
    checks: dict,
    findings: list,
    attempt_id: str = "attempt-1",
    previous: str | None = None,
    review_id: str = "review-1",
) -> dict:
    return {
        "review_schema": 1,
        "taxonomy": 1,
        "kind": kind,
        "attempt": {
            "review_id": review_id,
            "attempt_id": attempt_id,
            "manifest_sha256": manifest_hash,
            "previous_attempt_id": previous,
        },
        "reviewer": {
            "resolved_model": "fixture-model",
            "harness": "fixture-harness",
            "family": "fixture-family",
            "prompt_sha256": "cd" * 32,
        },
        "checks": checks,
        "findings": findings,
    }


def _plan(manifest_hash: str) -> dict:
    return _review(
        kind="plan", manifest_hash=manifest_hash, checks={name: "clean" for name in PLAN_CHECKS}, findings=[]
    )


def _lesson_checks(language: str | list = "clean") -> dict:
    checks = {name: "clean" for name in LESSON_CHECKS}
    checks["language"] = language
    return checks


def _finding(**overrides) -> dict:
    finding = {
        "id": "F-01",
        "status": "active",
        "locations": [{"tab": "vpravy", "activity": "act-1", "item": 0, "quote": "alpha-item-text"}],
        "dimension": "language",
        "sub_dimension": "stress",
        "severity": "MINOR",
        "claim": "Placeholder claim.",
        "evidence": {"receipt": "pending"},
        "expected": "attested",
    }
    finding.update(overrides)
    return finding


def _record(
    path: Path,
    *,
    manifest: str,
    result: str,
    attempt_id: str = "attempt-1",
    review_id: str = "review-1",
    status: str = "ok",
    tool: str = "verify_words",
) -> str:
    return append(
        path,
        review_id=review_id,
        attempt_id=attempt_id,
        manifest_sha256=manifest,
        tool=tool,
        server_version="ef" * 32,
        arguments={"words": ["placeholder"]},
        snapshots=SNAPSHOTS,
        status=status,
        result=result,
    )


def _layout(tmp_path: Path, *, recap: bool = False) -> dict:
    tmp_path = Path(tmp_path)
    tmp_path.mkdir(parents=True, exist_ok=True)
    manifest = tmp_path / "manifest.yaml"
    lesson = tmp_path / "lesson.yaml"
    review = tmp_path / "review.yaml"
    ledger = tmp_path / "attempt-1.jsonl"
    digest = _write_manifest(manifest, recap=recap)
    _dump(lesson, _lesson())
    create_empty_ledger(ledger)
    return {"manifest": manifest, "lesson": lesson, "review": review, "ledger": ledger, "digest": digest}


def _validate(paths: dict) -> object:
    return validate_review(
        paths["review"],
        manifest_path=paths["manifest"],
        lesson_path=paths["lesson"],
        ledger_path=paths["ledger"],
    )


def _codes(result) -> set[str]:
    return {item.code for item in result.rejections}


@pytest.fixture
def server_module():
    spec = importlib.util.spec_from_file_location("sources_server_review_r1", SERVER_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules["sources_server_review_r1"] = module
    spec.loader.exec_module(module)
    return module


def _quiet_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


def _arm(monkeypatch: pytest.MonkeyPatch, ledger: Path, *, manifest: str = "ab" * 32) -> None:
    ledger.parent.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("LU_REVIEW_ATTEMPT_ID", "attempt-1")
    monkeypatch.setenv("LU_REVIEW_MANIFEST_SHA256", manifest)
    monkeypatch.setenv("LU_REVIEW_LEDGER_PATH", str(ledger))
    monkeypatch.setattr(
        "scripts.review.receipts.ledger.collect_snapshots",
        lambda **_kwargs: SNAPSHOTS,
    )


def test_taxonomy_matches_schema_enums() -> None:
    schema = json.loads((REPO / "schemas" / "review-v1.schema.json").read_text(encoding="utf-8"))
    taxonomy = yaml.safe_load((REPO / "schemas" / "review-taxonomy-v1.yaml").read_text(encoding="utf-8"))
    finding = schema["$defs"]["finding"]
    assert finding["properties"]["dimension"]["enum"] == taxonomy["dimensions"]
    assert finding["properties"]["sub_dimension"]["enum"] == taxonomy["sub_dimensions"]["language"]
    schema_checks = set(schema["$defs"]["checks"]["properties"])
    named = {item["name"] for kind in taxonomy["kinds"].values() for item in kind["checks"]}
    assert named == schema_checks
    assert schema["additionalProperties"] is False
    assert [item["name"] for item in taxonomy["kinds"]["plan"]["checks"]] == list(PLAN_CHECKS)
    recap = [item for item in taxonomy["kinds"]["lesson"]["checks"] if item["name"] == "recap"]
    assert recap[0]["recap_only"] is True


def test_fold_quote_matches_word_store_stress_strip() -> None:
    text = "cafe\u0301 placeholder"
    assert fold_quote(text) == strip_combining_stress(text) == "cafe placeholder"


def test_ledger_source_does_not_import_network_modules() -> None:
    tree = ast.parse(LEDGER_PATH.read_text(encoding="utf-8"))
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.append(node.module.split(".")[0])
    assert not {"urllib", "requests", "socket", "http", "aiohttp", "httpx"} & set(modules)


def test_ledger_round_trip_same_bytes(tmp_path: Path) -> None:
    path = tmp_path / "review-1" / "attempt-1.jsonl"
    result = "stored-output-alpha\n" + ("x" * 600)
    receipt = _record(path, manifest="ab" * 32, result=result)
    loaded = lookup(path, receipt)
    line = path.read_bytes().splitlines()[0]
    assert loaded["result"] == result
    assert line == dumps(loaded).encode("utf-8")
    assert (path.stat().st_mode & 0o777) == 0o600
    sidecar = path.with_name(path.name + ".sha256")
    assert sidecar.read_text(encoding="ascii") == hashlib.sha256(path.read_bytes()).hexdigest() + "\n"
    assert (sidecar.stat().st_mode & 0o777) == 0o600


def test_ledger_and_sidecar_mode_0o600_after_append(tmp_path: Path) -> None:
    path = tmp_path / "review-1" / "attempt-1.jsonl"
    _record(path, manifest="ab" * 32, result="first-result")
    sidecar = path.with_name(path.name + ".sha256")
    lock_path = path.with_name(path.name + ".lock")
    assert (path.stat().st_mode & 0o777) == 0o600
    assert (sidecar.stat().st_mode & 0o777) == 0o600
    assert (lock_path.stat().st_mode & 0o777) == 0o600

    _record(path, manifest="ab" * 32, result="second-result")
    assert (path.stat().st_mode & 0o777) == 0o600
    assert (sidecar.stat().st_mode & 0o777) == 0o600
    assert (lock_path.stat().st_mode & 0o777) == 0o600


def test_ledger_atomic_write_sets_mode_0o600_before_replace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "review-1" / "attempt-1.jsonl"
    observed: list[tuple[str, int]] = []
    real_replace = os.replace

    def recording_replace(src: str | os.PathLike[str], dst: str | os.PathLike[str]) -> None:
        src_path = Path(src)
        observed.append((src_path.name, src_path.stat().st_mode & 0o777))
        real_replace(src, dst)

    monkeypatch.setattr(os, "replace", recording_replace)

    _record(path, manifest="ab" * 32, result="first-result")

    assert len(observed) == 2
    for name, mode in observed:
        assert mode == 0o600, f"Expected 0o600 at replace time for {name}, got {oct(mode)}"

    observed.clear()
    empty_path = tmp_path / "empty" / "attempt-2.jsonl"
    create_empty_ledger(empty_path)
    assert len(observed) == 2
    for name, mode in observed:
        assert mode == 0o600, f"Expected 0o600 at replace time for {name}, got {oct(mode)}"


def test_ledger_append_only_and_sidecar_mismatch(tmp_path: Path) -> None:
    path = tmp_path / "attempt-1.jsonl"
    first = _record(path, manifest="ab" * 32, result="first-result")
    before = path.read_bytes()
    second = _record(path, manifest="ab" * 32, result="second-result")
    after = path.read_bytes()
    assert first != second
    assert after.startswith(before)
    assert lookup(path, first)["result"] == "first-result"
    sidecar = path.with_name(path.name + ".sha256")
    sidecar.write_text("0" * 64 + "\n", encoding="ascii")
    with pytest.raises(LedgerError):
        lookup(path, first)


def _vesum_fixture(path: Path) -> None:
    connection = sqlite3.connect(path)
    connection.execute("CREATE TABLE vesum_build_metadata (key TEXT, value TEXT)")
    connection.execute(
        "INSERT INTO vesum_build_metadata VALUES ('canonical_jsonl_sha256', ?)",
        ("ab" * 32,),
    )
    connection.commit()
    connection.close()


def test_collect_snapshots_uses_file_metadata_identity_and_vesum_metadata(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """sources_db is a metadata identity (scheme file-meta-v1): 64-hex digest, no body read (#8527)."""
    sources_db = tmp_path / "sources.db"
    header = bytearray(b"SQLite format 3\x00" + b"\x10\x00" + b"\x02\x02" + bytes(80))
    sources_db.write_bytes(bytes(header))
    # Sparse: far larger than any read budget, so a whole-file hash could not finish in test time.
    # Probe sparse support with 64 MiB before extending, so a non-sparse filesystem never fills up.
    os.truncate(sources_db, 64 << 20)
    size = 64 << 20
    if sources_db.stat().st_blocks * 512 < (1 << 20):
        size = 1 << 34
        os.truncate(sources_db, size)
    (tmp_path / "sources.db-wal").write_bytes(b"w" * 7)
    vesum = tmp_path / "vesum.db"
    _vesum_fixture(vesum)
    from scripts.curriculum.evidence.sources import Sources

    bytes_read = {"total": 0}
    real_open = Path.open

    def counting_open(self, *args, **kwargs):
        stream = real_open(self, *args, **kwargs)
        if self == sources_db:
            real_read = stream.read

            def read(size=-1):
                data = real_read(size)
                bytes_read["total"] += len(data)
                return data

            stream.read = read
        return stream

    monkeypatch.setattr(Path, "open", counting_open)
    monkeypatch.setattr(hashlib, "file_digest", lambda *_a, **_k: pytest.fail("collect_snapshots hashed a file body"))
    sources = Sources(sources_db=sources_db, vesum_db=vesum)
    try:
        snapshot = collect_snapshots(sources=sources, trie_digest="cd" * 32)
    finally:
        sources.close()
    entry = snapshot["sources_db"]
    stat = sources_db.stat()
    wal_stat = (tmp_path / "sources.db-wal").stat()
    assert entry["metadata"] == {
        "scheme": "file-meta-v1",
        "size_bytes": size,
        "mtime_ns": stat.st_mtime_ns,
        "journal_mode": "wal",
        "wal_bytes": 7,
        "wal_mtime_ns": wal_stat.st_mtime_ns,
    }
    assert len(entry["digest"]) == 64 and all(ch in "0123456789abcdef" for ch in entry["digest"])
    expected = hashlib.sha256(
        json.dumps(entry["metadata"], sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()
    assert entry["digest"] == expected
    assert bytes_read["total"] <= 100, f"sources.db body was read: {bytes_read['total']} bytes"
    assert snapshot["vesum"]["digest"] == "ab" * 32
    assert snapshot["trie"]["digest"] == "cd" * 32


def test_sources_db_meta_identity_changes_with_size_or_mtime(tmp_path: Path) -> None:
    from scripts.curriculum.evidence.sources import Sources

    sources_db = tmp_path / "sources.db"
    sources_db.write_bytes(b"sources-bytes")
    vesum = tmp_path / "vesum.db"
    _vesum_fixture(vesum)
    sources = Sources(sources_db=sources_db, vesum_db=vesum)
    try:
        first = collect_snapshots(sources=sources, trie_digest="cd" * 32)["sources_db"]
        assert first["metadata"]["journal_mode"] is None  # not a SQLite header, no pinned session
        os.utime(sources_db, ns=(first["metadata"]["mtime_ns"] + 1_000_000_000,) * 2)
        after_mtime = collect_snapshots(sources=sources, trie_digest="cd" * 32)["sources_db"]
        assert after_mtime["metadata"]["size_bytes"] == first["metadata"]["size_bytes"]
        assert after_mtime["digest"] != first["digest"]
        with sources_db.open("ab") as stream:
            stream.write(b"!")
        os.utime(sources_db, ns=(after_mtime["metadata"]["mtime_ns"],) * 2)
        after_size = collect_snapshots(sources=sources, trie_digest="cd" * 32)["sources_db"]
        assert after_size["metadata"]["mtime_ns"] == after_mtime["metadata"]["mtime_ns"]
        assert after_size["digest"] not in {first["digest"], after_mtime["digest"]}
    finally:
        sources.close()


def test_session_from_environ_off_and_incomplete(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _quiet_env(monkeypatch)
    assert session_from_environ() is None
    monkeypatch.setenv("LU_REVIEW_ATTEMPT_ID", "attempt-1")
    session = session_from_environ()
    assert session is not None and session.mode == "incomplete"
    ledger = tmp_path / "review-1" / "attempt-1.jsonl"
    _arm(monkeypatch, ledger)
    armed = session_from_environ()
    assert armed is not None and armed.mode == "on"
    assert armed.review_id == "review-1"
    assert armed.attempt_id == "attempt-1"


def test_valid_plan_and_lesson_reviews(tmp_path: Path) -> None:
    paths = _layout(tmp_path)
    _dump(paths["review"], _plan(paths["digest"]))
    plan = _validate(paths)
    assert plan.ok and plan.verdict == "APPROVE"

    lesson_dir = tmp_path / "lesson-case"
    lesson_dir.mkdir()
    paths = _layout(lesson_dir)
    receipt = _record(paths["ledger"], manifest=paths["digest"], result="alpha-item-text is attested")
    _dump(
        paths["review"],
        _review(
            kind="lesson",
            manifest_hash=paths["digest"],
            checks=_lesson_checks(["F-01"]),
            findings=[_finding(evidence={"receipt": receipt})],
        ),
    )
    lesson = _validate(paths)
    assert lesson.ok and lesson.verdict == "APPROVE"
    assert lesson.active_blockers == 0 and lesson.active_majors == 0


def test_resolved_major_does_not_block(tmp_path: Path) -> None:
    paths = _layout(tmp_path)
    previous = tmp_path / "attempt-0.jsonl"
    receipt = _record(
        previous,
        manifest="11" * 32,
        result="alpha-item-text is attested",
        attempt_id="attempt-0",
    )
    finding = _finding(status="resolved", severity="MAJOR", evidence={"receipt": receipt})
    _dump(
        paths["review"],
        _review(
            kind="lesson",
            manifest_hash=paths["digest"],
            checks=_lesson_checks(["F-01"]),
            findings=[finding],
            previous="attempt-0",
        ),
    )
    result = _validate(paths)
    assert result.ok and result.verdict == "APPROVE"
    assert result.active_majors == 0

    active_dir = tmp_path / "active"
    active_dir.mkdir()
    active = _layout(active_dir)
    current = _record(active["ledger"], manifest=active["digest"], result="alpha-item-text is attested")
    _dump(
        active["review"],
        _review(
            kind="lesson",
            manifest_hash=active["digest"],
            checks=_lesson_checks(["F-01"]),
            findings=[_finding(severity="MAJOR", evidence={"receipt": current})],
        ),
    )
    blocked = _validate(active)
    assert blocked.ok and blocked.verdict == "REVISE" and blocked.active_majors == 1


@pytest.mark.parametrize(
    ("mutate", "code"),
    [
        ("manifest", codes.MANIFEST_HASH_MISMATCH),
        ("fabricated", codes.RECEIPT_NOT_IN_LEDGER),
        ("expected", codes.EXPECTED_NOT_IN_RESULT),
        ("other_activity", codes.QUOTE_NOT_IN_UNIT),
        ("empty_quote", codes.QUOTE_EMPTY),
        ("out_of_bounds", codes.LOCATION_NOT_IN_LESSON),
        ("incomplete", codes.LOCATION_INCOMPLETE),
        ("no_searches", codes.UNSUPPORTED_WITHOUT_SEARCHES),
        ("unsupported_cap", codes.UNSUPPORTED_SEVERITY_ABOVE_MINOR),
        ("outcome", codes.OUTCOME_NOT_IN_LEDGER),
        ("no_sub", codes.LANGUAGE_SUB_DIMENSION_MISSING),
        ("missing_check", codes.CHECK_MISSING),
        ("recap_check", codes.CHECK_NOT_APPLICABLE),
        ("duplicate", codes.DUPLICATE_FINDING_ID),
        ("two_branches", codes.EVIDENCE_BRANCH_COUNT),
        ("no_branch", codes.EVIDENCE_BRANCH_COUNT),
        ("scope", codes.SCOPE_MISSING),
        ("finding_not_referenced", codes.FINDING_NOT_REFERENCED),
        ("dangling_check_reference", codes.DANGLING_CHECK_REFERENCE),
        ("sub_dimension_invalid", codes.SUB_DIMENSION_INVALID),
    ],
)
def test_one_fixture_per_rejection(tmp_path: Path, mutate: str, code: str) -> None:
    paths = _layout(tmp_path)
    result_text = "alpha-item-text is attested" if mutate not in ("outcome", "unsupported_cap") else "No results found."
    if mutate == "expected":
        result_text = "stored-output-alpha"
    receipt = _record(paths["ledger"], manifest=paths["digest"], result=result_text, status="ok")
    finding = _finding(evidence={"receipt": receipt})
    checks = _lesson_checks(["F-01"])
    manifest_hash = paths["digest"]
    if mutate == "manifest":
        manifest_hash = "00" * 32
    elif mutate == "fabricated":
        finding["evidence"] = {"receipt": "not-a-receipt"}
    elif mutate == "expected":
        finding["expected"] = "missing-phrase"
    elif mutate == "other_activity":
        finding["locations"] = [{"tab": "vpravy", "activity": "act-2", "item": 0, "quote": "alpha-item-text"}]
    elif mutate == "empty_quote":
        finding["locations"] = [{"tab": "vpravy", "activity": "act-1", "item": 0, "quote": "   "}]
    elif mutate == "out_of_bounds":
        finding["locations"] = [{"tab": "vpravy", "activity": "act-1", "item": 9, "quote": "alpha-item-text"}]
    elif mutate == "incomplete":
        finding["locations"] = [{"tab": "vpravy", "quote": "alpha-item-text"}]
    elif mutate == "no_searches":
        finding.pop("evidence")
        finding["unsupported_by_source"] = {"searches": []}
    elif mutate == "unsupported_cap":
        finding.pop("evidence")
        finding.pop("expected")
        finding["severity"] = "MAJOR"
        finding["unsupported_by_source"] = {"searches": [{"receipt": receipt, "outcome": "no_hits"}]}
    elif mutate == "outcome":
        finding.pop("evidence")
        finding.pop("expected")
        finding["unsupported_by_source"] = {"searches": [{"receipt": receipt, "outcome": "hits_but_no_support"}]}

    elif mutate == "no_sub":
        finding.pop("sub_dimension")
    elif mutate == "missing_check":
        del checks["job"]
    elif mutate == "recap_check":
        checks["recap"] = "clean"
    elif mutate == "duplicate":
        finding = [finding, _finding()]
    elif mutate == "two_branches":
        finding["unsupported_by_source"] = {"searches": [{"receipt": receipt, "outcome": "no_hits"}]}
    elif mutate == "no_branch":
        finding.pop("evidence")
    elif mutate == "scope":
        finding["locations"] = []
        finding.pop("scope", None)
    elif mutate == "finding_not_referenced":
        checks = _lesson_checks()
    elif mutate == "dangling_check_reference":
        checks["job"] = ["F-99"]
    elif mutate == "sub_dimension_invalid":
        finding["sub_dimension"] = "invalid_sub_dim"
    findings = finding if isinstance(finding, list) else [finding]
    if mutate == "duplicate":
        findings[1]["evidence"] = {"receipt": receipt}
    _dump(
        paths["review"],
        _review(kind="lesson", manifest_hash=manifest_hash, checks=checks, findings=findings),
    )
    validated = _validate(paths)
    assert not validated.ok
    assert code in _codes(validated)

    schema_valid_mutations = {
        "manifest",
        "fabricated",
        "expected",
        "other_activity",
        "empty_quote",
        "out_of_bounds",
        "incomplete",
        "unsupported_cap",
        "outcome",
        "missing_check",
        "recap_check",
        "duplicate",
        "finding_not_referenced",
        "dangling_check_reference",
    }
    if mutate in schema_valid_mutations:
        assert codes.SCHEMA_INVALID not in _codes(validated), (
            f"mutation {mutate} unexpectedly triggered schema_invalid: "
            f"{[r.message for r in validated.rejections if r.code == codes.SCHEMA_INVALID]}"
        )


def test_recap_check_required_when_manifest_says_recap(tmp_path: Path) -> None:
    paths = _layout(tmp_path, recap=True)
    _dump(
        paths["review"],
        _review(kind="lesson", manifest_hash=paths["digest"], checks=_lesson_checks(), findings=[]),
    )
    missing = _validate(paths)
    assert codes.CHECK_MISSING in _codes(missing)
    checks = _lesson_checks()
    checks["recap"] = "clean"
    _dump(
        paths["review"],
        _review(kind="lesson", manifest_hash=paths["digest"], checks=checks, findings=[]),
    )
    assert _validate(paths).ok


def test_help_lists_the_code_registry() -> None:
    proc = subprocess.run(
        [sys.executable, "-m", "scripts.review.validate", "--help"],
        cwd=REPO,
        timeout=30,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    for code in codes.DESCRIPTIONS:
        assert code in proc.stdout
    assert "Do NOT use" in proc.stdout
    assert "Exit codes:" in proc.stdout


def test_cli_rejects_fabricated_receipt(tmp_path: Path) -> None:
    paths = _layout(tmp_path)
    _record(paths["ledger"], manifest=paths["digest"], result="alpha-item-text is attested")
    _dump(
        paths["review"],
        _review(
            kind="lesson",
            manifest_hash=paths["digest"],
            checks=_lesson_checks(["F-01"]),
            findings=[_finding(evidence={"receipt": "not-a-receipt"})],
        ),
    )
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.review.validate",
            str(paths["review"]),
            "--manifest",
            str(paths["manifest"]),
            "--lesson",
            str(paths["lesson"]),
            "--ledger",
            str(paths["ledger"]),
        ],
        cwd=REPO,
        timeout=30,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 1
    assert codes.RECEIPT_NOT_IN_LEDGER in proc.stdout
    assert (
        main(
            [
                str(paths["review"]),
                "--manifest",
                str(paths["manifest"]),
                "--lesson",
                str(paths["lesson"]),
                "--ledger",
                str(paths["ledger"]),
                "--json",
            ]
        )
        == 1
    )


def test_server_recording_off_is_byte_identical(server_module, monkeypatch: pytest.MonkeyPatch) -> None:
    _quiet_env(monkeypatch)

    async def fake(_arguments):
        from mcp.types import TextContent

        return [TextContent(type="text", text="plain-result")]

    monkeypatch.setattr(server_module, "handle_verify_words", fake)
    first = _run(server_module.call_tool("verify_words", {"words": ["placeholder"]}))
    second = _run(server_module.call_tool("verify_words", {"words": ["placeholder"]}))
    assert first[0].text == second[0].text == "plain-result"
    assert "receipt:" not in first[0].text
    unknown = _run(server_module.call_tool("nonexistent_tool", {}))
    assert unknown[0].text == "Unknown tool: nonexistent_tool"
    params = server_module.CallToolRequestParams(name="nonexistent_tool", arguments={})
    wire = _run(server_module._on_call_tool(None, params))
    assert wire.is_error is True
    assert wire.content[0].text == "Tool call failed: nonexistent_tool."


def test_check_text_outcome_classification() -> None:
    """A clean check is no hits; problems and suspicions count; errors are not hits."""
    error_facts = {"call_status": "ok", "hits": 0, "status": "error", "unavailable": False}
    clean = json.dumps(
        {"provenance": {}, "summary": {}, "problems": [], "suspicions": []},
        ensure_ascii=False,
    )
    clean_facts = classify_outcome("check_text", "ok", clean)
    assert clean_facts == {"call_status": "ok", "hits": 0, "status": "no_hits", "unavailable": False}

    problems = json.dumps(
        {
            "problems": [{"form": "написання постів", "check": "ua_gec"}],
            "suspicions": [],
        },
        ensure_ascii=False,
    )
    problem_facts = classify_outcome("check_text", "ok", problems)
    assert problem_facts == {"call_status": "ok", "hits": 1, "status": "hits_found", "unavailable": False}

    missing = json.dumps(
        {
            "status": "error",
            "error_code": "source_unavailable",
            "error": "source_unavailable: VESUM database not found at /nonexistent/vesum.db",
        },
        ensure_ascii=False,
    )
    missing_facts = classify_outcome("check_text", "ok", missing)
    assert missing_facts["unavailable"] is True
    assert missing_facts["status"] == "unavailable"
    assert missing_facts["hits"] == 0
    assert missing_facts["status"] != "no_hits"

    invalid_input = json.dumps(
        {
            "status": "error",
            "error_code": "invalid_input",
            "error": "invalid_input: provide either 'text' or 'items', not both",
        },
        ensure_ascii=False,
    )
    assert classify_outcome("check_text", "ok", invalid_input) == error_facts

    accent_in_input = json.dumps(
        {
            "status": "error",
            "error_code": "accent_in_input",
            "error": "accent_in_input: combining accent in input text",
        },
        ensure_ascii=False,
    )
    assert classify_outcome("check_text", "ok", accent_in_input) == error_facts

    # max_findings=1 can keep a suspicion and drop the problems the summary still counts.
    truncated = json.dumps(
        {
            "summary": {
                "truncated": True,
                "problems_per_check": {
                    "vesum": 0,
                    "stress": 2,
                    "russian_shadow": 0,
                    "ua_gec": 1,
                },
            },
            "problems": [],
            "suspicions": [{"form": "як", "check": "ua_gec"}],
        },
        ensure_ascii=False,
    )
    truncated_facts = classify_outcome("check_text", "ok", truncated)
    assert truncated_facts == {"call_status": "ok", "hits": 3, "status": "hits_found", "unavailable": False}
    assert truncated_facts["status"] != "no_hits"

    truncated_only = json.dumps(
        {
            "summary": {
                "truncated": True,
                "problems_per_check": {"vesum": 0, "stress": 0, "russian_shadow": 0, "ua_gec": 0},
            },
            "problems": [],
            "suspicions": [],
        },
        ensure_ascii=False,
    )
    assert classify_outcome("check_text", "ok", truncated_only)["status"] != "no_hits"

    suspicions_only = json.dumps(
        {
            "summary": {
                "truncated": False,
                "problems_per_check": {
                    "vesum": 0,
                    "stress": 0,
                    "russian_shadow": 0,
                    "ua_gec": 0,
                },
            },
            "problems": [],
            "suspicions": [{"form": "слово", "check": "russian_shadow"}],
        },
        ensure_ascii=False,
    )
    suspicions_facts = classify_outcome("check_text", "ok", suspicions_only)
    assert suspicions_facts == {"call_status": "ok", "hits": 1, "status": "hits_found", "unavailable": False}


def test_check_text_call_is_recorded_and_receipt_resolves(
    server_module, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from mcp.types import TextContent

    ledger = tmp_path / "review-1" / "attempt-1.jsonl"
    _arm(monkeypatch, ledger)
    payload = json.dumps(
        {"provenance": {}, "summary": {}, "problems": [], "suspicions": []},
        ensure_ascii=False,
    )

    async def fake(_arguments):
        return [TextContent(type="text", text=payload)]

    monkeypatch.setattr(server_module, "handle_check_text", fake)
    result = _run(server_module.call_tool("check_text", {"text": "Привіт."}))
    receipt = result[0].text.splitlines()[-1].removeprefix("receipt: ")
    assert result[0].text == payload + "\nreceipt: " + receipt
    stored = lookup(ledger, receipt)
    assert stored["tool"] == "check_text"
    assert stored["status"] == "ok"
    assert stored["result"] == payload
    assert "check_text" in REVIEW_TOOLS


def test_server_records_full_result_and_refuses_other_tools(
    server_module, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ledger = tmp_path / "review-1" / "attempt-1.jsonl"
    _arm(monkeypatch, ledger)
    payload = "Z" * 600

    async def fake(_arguments):
        from mcp.types import TextContent

        return [TextContent(type="text", text=payload)]

    monkeypatch.setattr(server_module, "handle_verify_words", fake)
    result = _run(server_module.call_tool("verify_words", {"words": ["placeholder"]}))
    receipt = result[0].text.splitlines()[-1].removeprefix("receipt: ")
    assert result[0].text == payload + "\nreceipt: " + receipt
    stored = lookup(ledger, receipt)
    assert stored["result"] == payload
    assert len(stored["result"]) == 600
    assert stored["status"] == "ok"
    assert stored["tool"] == "verify_words"
    assert stored["server_version"].startswith(server_module._sha256_of_file(SERVER_PATH))
    assert "+" in stored["server_version"]

    called = {"yes": False}

    async def should_not_run(_arguments):
        called["yes"] = True
        from mcp.types import TextContent

        return [TextContent(type="text", text="should-not-run")]

    monkeypatch.setattr(server_module, "handle_search_sources", should_not_run)
    refused = _run(server_module.call_tool("search_sources", {"query": "placeholder"}))
    assert called["yes"] is False
    assert "not in the review tool list" in refused[0].text
    refusal = records(ledger)[-1]
    assert refusal["status"] == "refused"
    assert refusal["tool"] == "search_sources"
    assert "search_sources" not in REVIEW_TOOLS


def test_v4_refusal_unchanged_when_review_recording_is_on(
    server_module, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ledger = tmp_path / "review-1" / "attempt-1.jsonl"
    _arm(monkeypatch, ledger)
    token = server_module._V4_ACTIVE_ATTEMPT.set(object())
    try:
        result = _run(server_module.call_tool("search_text", {"query": "placeholder"}))
    finally:
        server_module._V4_ACTIVE_ATTEMPT.reset(token)
    assert result[0].text == "V4 tool capability refused"
    assert not ledger.exists()


def test_review_tool_error_is_recorded(server_module, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    ledger = tmp_path / "review-1" / "attempt-1.jsonl"
    _arm(monkeypatch, ledger)

    async def boom(_arguments):
        raise RuntimeError("boom-marker")

    monkeypatch.setattr(server_module, "handle_verify_quote", boom)
    result = _run(server_module.call_tool("verify_quote", {"quote": "placeholder"}))
    assert "boom-marker" in result[0].text
    assert result[0].text.splitlines()[-1].startswith("receipt: ")
    stored = records(ledger)[0]
    assert stored["status"] == "error"
    assert "boom-marker" in stored["result"]
    assert len(stored["result"]) > len("boom-marker")


TOOL_NO_RESULT_FIXTURES: list[tuple[str, str]] = [
    (
        "check_russian_shadow",
        json.dumps({"matches_russian": False, "russian_lemma": None, "ukrainian_alternative": None, "confidence": 0.0}),
    ),
    (
        "verify_quote",
        json.dumps(
            {
                "matched": False,
                "best_confidence": 0.0,
                "matched_lines": [],
                "search_normalized": {"author_query": "author", "text_query": "text"},
            }
        ),
    ),
    ("search_text", "No results found."),
    ("search_ua_gec_errors", 'No UA-GEC results found for: "деякі речі"'),
    ("verify_words", "Batch verification: 1 words\nFound: 0/1\n\n- **неслово** — NOT FOUND"),
    (
        "inspect_word",
        '\'неслово\' — Status: NOT_FOUND\n- Effective markers: none\n- Clean analyses: 0\n- Marked analyses: 0\n- Raw payload: {"word": "неслово", "status": "NOT_FOUND"}',
    ),
    (
        "inspect_words",
        'Batch inspection: 1 words\n\n- **неслово** — NOT FOUND\n\nRaw payload:\n{"words": {"неслово": {"status": "NOT_FOUND"}}}',
    ),
    ("verify_stress", "неслово — not_found"),
    ("query_grac", "**неслово**: frequency = 0, relative = 0.00 per million"),
    ("query_ulif", "No ULIF paradigm found for: 'кицяневідома'"),
    ("query_r2u", "No r2u translation found for: 'неслово'"),
    (
        "query_sum20",
        "No official offline СУМ-20 entry is currently ingested for 'неслово'. This tool does not make a live request or use a fallback source.",
    ),
    ("query_pravopys", "No pravopys section found for: 'невідома_тема'"),
    ("search_style_guide", 'No results in Антоненко-Давидович for: "невідомо"'),
    ("query_cefr_level", 'No results in PULS CEFR for: "невідомо"'),
    ("search_heritage", 'No heritage evidence found for: "невідомо"'),
]


def test_all_16_tools_no_hits_and_mixed_case(tmp_path: Path) -> None:
    assert len(TOOL_NO_RESULT_FIXTURES) == 16
    for i, (tool_name, no_res_text) in enumerate(TOOL_NO_RESULT_FIXTURES):
        case_dir = tmp_path / f"tool_{i}_{tool_name}"
        case_dir.mkdir()
        paths = _layout(case_dir)
        receipt = _record(paths["ledger"], manifest=paths["digest"], result=no_res_text, tool=tool_name, status="ok")
        record = lookup(paths["ledger"], receipt)
        assert "outcome_facts" in record
        assert record["outcome_facts"]["hits"] == 0

        # Review claims no_hits -> PASS
        finding_no_hits = _finding(
            severity="MINOR",
            unsupported_by_source={"searches": [{"receipt": receipt, "outcome": "no_hits"}]},
        )
        finding_no_hits.pop("evidence", None)
        finding_no_hits.pop("expected", None)
        _dump(
            paths["review"],
            _review(
                kind="lesson",
                manifest_hash=paths["digest"],
                checks=_lesson_checks(["F-01"]),
                findings=[finding_no_hits],
            ),
        )
        validated = _validate(paths)
        assert validated.ok, f"tool {tool_name} failed no_hits check: {[r.message for r in validated.rejections]}"

        # Review claims hits_but_no_support -> REJECT with outcome_not_in_ledger
        finding_hits = _finding(
            severity="MINOR",
            unsupported_by_source={"searches": [{"receipt": receipt, "outcome": "hits_but_no_support"}]},
        )
        finding_hits.pop("evidence", None)
        finding_hits.pop("expected", None)
        _dump(
            paths["review"],
            _review(
                kind="lesson", manifest_hash=paths["digest"], checks=_lesson_checks(["F-01"]), findings=[finding_hits]
            ),
        )
        rejected = _validate(paths)
        assert not rejected.ok and codes.OUTCOME_NOT_IN_LEDGER in _codes(rejected)

    # Mixed verify_words case (1 found, 1 not found) -> hits > 0
    mixed_dir = tmp_path / "mixed_verify_words"
    mixed_dir.mkdir()
    mixed_paths = _layout(mixed_dir)
    mixed_text = (
        "Batch verification: 2 words\nFound: 1/2\n\n"
        "- **слово** — FOUND (clean=1, marked=0): слово(noun)\n"
        "- **неслово** — NOT FOUND"
    )
    mixed_receipt = _record(
        mixed_paths["ledger"], manifest=mixed_paths["digest"], result=mixed_text, tool="verify_words", status="ok"
    )
    mixed_record = lookup(mixed_paths["ledger"], mixed_receipt)
    assert mixed_record["outcome_facts"]["hits"] == 1

    # Mixed case with hits_but_no_support -> PASS
    finding_mixed_support = _finding(
        severity="MINOR",
        unsupported_by_source={"searches": [{"receipt": mixed_receipt, "outcome": "hits_but_no_support"}]},
    )
    finding_mixed_support.pop("evidence", None)
    finding_mixed_support.pop("expected", None)
    _dump(
        mixed_paths["review"],
        _review(
            kind="lesson",
            manifest_hash=mixed_paths["digest"],
            checks=_lesson_checks(["F-01"]),
            findings=[finding_mixed_support],
        ),
    )
    mixed_val = _validate(mixed_paths)
    assert mixed_val.ok

    # Mixed case with no_hits -> REJECT with outcome_not_in_ledger
    finding_mixed_no_hits = _finding(
        severity="MINOR",
        unsupported_by_source={"searches": [{"receipt": mixed_receipt, "outcome": "no_hits"}]},
    )
    finding_mixed_no_hits.pop("evidence", None)
    finding_mixed_no_hits.pop("expected", None)
    _dump(
        mixed_paths["review"],
        _review(
            kind="lesson",
            manifest_hash=mixed_paths["digest"],
            checks=_lesson_checks(["F-01"]),
            findings=[finding_mixed_no_hits],
        ),
    )
    mixed_rej = _validate(mixed_paths)
    assert not mixed_rej.ok and codes.OUTCOME_NOT_IN_LEDGER in _codes(mixed_rej)


def test_missing_ledger_is_ledger_unreadable(tmp_path: Path) -> None:
    paths = _layout(tmp_path)
    # Remove the created ledger
    paths["ledger"].unlink()
    paths["ledger"].with_name(paths["ledger"].name + ".sha256").unlink(missing_ok=True)
    _dump(paths["review"], _plan(paths["digest"]))
    validated = _validate(paths)
    assert not validated.ok
    assert codes.LEDGER_UNREADABLE in _codes(validated)


def test_create_empty_ledger_helper(tmp_path: Path) -> None:
    target = tmp_path / "empty" / "attempt-1.jsonl"
    created = create_empty_ledger(target)
    assert created == target
    assert target.is_file() and target.stat().st_size == 0
    sidecar = target.with_name(target.name + ".sha256")
    assert sidecar.is_file()
    assert (target.stat().st_mode & 0o777) == 0o600
    assert (sidecar.stat().st_mode & 0o777) == 0o600
    assert records(target) == []


def test_ledger_stale_last_line_recovery(tmp_path: Path) -> None:
    paths = _layout(tmp_path)
    r1 = _record(paths["ledger"], manifest=paths["digest"], result="result-one")
    # Capture hash of ledger with 1 line
    sidecar = paths["ledger"].with_name(paths["ledger"].name + ".sha256")
    sidecar_1 = sidecar.read_text()
    # Now append a second line
    r2 = _record(paths["ledger"], manifest=paths["digest"], result="result-two")
    assert r1 != r2
    # Simulate crash before sidecar update: overwrite sidecar with sidecar_1
    sidecar.write_text(sidecar_1)

    _dump(paths["review"], _plan(paths["digest"]))
    with pytest.raises(LedgerHashStaleLastLine):
        records(paths["ledger"])
    validated = _validate(paths)
    assert not validated.ok
    assert codes.LEDGER_HASH_STALE_LAST_LINE in _codes(validated)
    assert codes.LEDGER_UNREADABLE not in _codes(validated)


def test_positive_evidence_requires_ok_status_and_review_tool(tmp_path: Path) -> None:
    # 1. Error status receipt cited as positive evidence
    err_paths = _layout(tmp_path / "case_err")
    err_receipt = _record(
        err_paths["ledger"],
        manifest=err_paths["digest"],
        result="some error message",
        status="error",
        tool="search_text",
    )
    _dump(
        err_paths["review"],
        _review(
            kind="lesson",
            manifest_hash=err_paths["digest"],
            checks=_lesson_checks(["F-01"]),
            findings=[_finding(evidence={"receipt": err_receipt})],
        ),
    )
    err_val = _validate(err_paths)
    assert not err_val.ok
    assert codes.EVIDENCE_RECEIPT_INVALID in _codes(err_val)

    # 2. Refused status receipt cited as positive evidence
    ref_paths = _layout(tmp_path / "case_ref")
    ref_receipt = _record(
        ref_paths["ledger"],
        manifest=ref_paths["digest"],
        result="refused",
        status="refused",
        tool="search_sources",
    )
    _dump(
        ref_paths["review"],
        _review(
            kind="lesson",
            manifest_hash=ref_paths["digest"],
            checks=_lesson_checks(["F-01"]),
            findings=[_finding(evidence={"receipt": ref_receipt})],
        ),
    )
    ref_val = _validate(ref_paths)
    assert not ref_val.ok
    assert codes.EVIDENCE_RECEIPT_INVALID in _codes(ref_val)

    # 3. Tool not in REVIEW_TOOLS (e.g. search_sources) even with status: ok
    bad_tool_paths = _layout(tmp_path / "case_bad_tool")
    bad_receipt = _record(
        bad_tool_paths["ledger"],
        manifest=bad_tool_paths["digest"],
        result="some result",
        status="ok",
        tool="search_sources",
    )
    _dump(
        bad_tool_paths["review"],
        _review(
            kind="lesson",
            manifest_hash=bad_tool_paths["digest"],
            checks=_lesson_checks(["F-01"]),
            findings=[_finding(evidence={"receipt": bad_receipt})],
        ),
    )
    bad_tool_val = _validate(bad_tool_paths)
    assert not bad_tool_val.ok
    assert codes.EVIDENCE_RECEIPT_INVALID in _codes(bad_tool_val)

    # 4. Valid status: ok from a review tool -> PASS
    good_paths = _layout(tmp_path / "case_good")
    good_receipt = _record(
        good_paths["ledger"],
        manifest=good_paths["digest"],
        result="alpha-item-text is attested",
        status="ok",
        tool="search_text",
    )
    _dump(
        good_paths["review"],
        _review(
            kind="lesson",
            manifest_hash=good_paths["digest"],
            checks=_lesson_checks(["F-01"]),
            findings=[_finding(evidence={"receipt": good_receipt})],
        ),
    )
    good_val = _validate(good_paths)
    assert good_val.ok


def test_recording_failure_returns_error_and_drops_typed_result(
    server_module, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from mcp.types import CallToolRequestParams, TextContent

    ledger = tmp_path / "review-1" / "attempt-1.jsonl"
    _arm(monkeypatch, ledger)

    async def fake_verify_words(_arguments):
        content = [TextContent(type="text", text="Batch verification: 1 words\nFound: 1/1\n- слово — FOUND")]
        typed_outcome = {"disposition": "found", "hits": 1}
        return content, typed_outcome

    monkeypatch.setattr(server_module, "handle_verify_words", fake_verify_words)

    def boom(*_a, **_kw):
        raise OSError("simulated disk failure")

    monkeypatch.setattr(
        "scripts.review.receipts.ledger.ReviewSession.record",
        boom,
    )

    params = CallToolRequestParams(name="verify_words", arguments={"words": ["слово"]})
    res = _run(server_module._on_call_tool(None, params))
    assert res.is_error is True
    assert res.structured_content is None
    assert "Review receipt recording failed: OSError" in res.content[0].text


def test_http_mode_refuses_recording(
    server_module, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    import logging

    ledger = tmp_path / "review-1" / "attempt-1.jsonl"
    _arm(monkeypatch, ledger)
    server_module._set_http_mode(True)
    try:
        with caplog.at_level(logging.ERROR, logger="sources_server"):
            # Review env should be reported as not engaged
            assert server_module._review_env_engaged() is False
            # Verify the error was logged
            assert any(
                "Review recording is disabled in standalone/HTTP mode" in record.message for record in caplog.records
            )
            # Second call should not log another error (logged once)
            record_count = len(caplog.records)
            assert server_module._review_env_engaged() is False
            assert len(caplog.records) == record_count

            # Running a review tool behaves as with recording off (no receipt appended)
            res = _run(server_module.call_tool("verify_words", {"words": ["слово"]}))
            assert not any("receipt: " in t.text for t in res)
            assert not ledger.exists()
    finally:
        server_module._set_http_mode(False)


def test_review_server_version_format(server_module) -> None:
    version = server_module._review_server_version()
    assert "+" in version
    sha, commit = version.split("+", 1)
    assert len(sha) == 64
    assert len(commit) >= 7 or commit == "unknown"


def test_detect_git_commit_fallback(server_module, monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(*_a, **_kw):
        raise OSError("no git")

    monkeypatch.setattr(subprocess, "run", fake_run)
    assert server_module._detect_git_commit() == "unknown"


def test_plan_review_findings_with_locations_rejected(tmp_path: Path) -> None:
    import scripts.review.validate.validate as val_mod
    from scripts.review.validate.validate import build_parser

    # Verify docstring and help text
    help_text = build_parser().format_help()
    assert "Plan-review findings with locations are rejected (location_not_in_lesson)" in help_text
    assert "until a plan document locator is defined" in help_text
    assert "Plan-review findings with locations are rejected (location_not_in_lesson)" in (val_mod.__doc__ or "")
    assert "until a plan document locator is defined" in (val_mod.__doc__ or "")

    # Validate plan review with locations
    paths = _layout(tmp_path)
    receipt = _record(paths["ledger"], manifest=paths["digest"], result="attested result")
    plan_checks = {name: "clean" for name in PLAN_CHECKS}
    plan_checks["closing_shape"] = ["F-01"]
    finding = {
        "id": "F-01",
        "status": "active",
        "locations": [{"tab": "plan", "quote": "some quote"}],
        "dimension": "plan_defect",
        "severity": "MINOR",
        "claim": "Plan defect claim.",
        "evidence": {"receipt": receipt},
        "expected": "attested",
    }
    _dump(
        paths["review"],
        _review(
            kind="plan",
            manifest_hash=paths["digest"],
            checks=plan_checks,
            findings=[finding],
        ),
    )
    res = _validate(paths)
    assert not res.ok
    assert codes.LOCATION_NOT_IN_LESSON in _codes(res)
    assert any("plan-review findings with locations are rejected" in r.message for r in res.rejections)


def test_sub_dimension_invalid_isolated_from_schema(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import copy

    import scripts.review.validate.validate as val_mod

    paths = _layout(tmp_path)
    receipt = _record(paths["ledger"], manifest=paths["digest"], result="alpha-item-text is attested", status="ok")
    finding = _finding(evidence={"receipt": receipt}, sub_dimension="stress")
    checks = _lesson_checks(["F-01"])
    _dump(paths["review"], _review(kind="lesson", manifest_hash=paths["digest"], checks=checks, findings=[finding]))

    # Valid under default taxonomy
    val_default = _validate(paths)
    assert val_default.ok

    # Omit 'stress' from taxonomy only
    custom_tax = copy.deepcopy(val_mod._taxonomy())
    custom_tax["sub_dimensions"]["language"] = ["russianism", "surzhyk"]
    monkeypatch.setattr(val_mod, "_taxonomy", lambda: custom_tax)

    val_custom = _validate(paths)
    assert not val_custom.ok
    assert codes.SUB_DIMENSION_INVALID in _codes(val_custom)
    assert codes.SCHEMA_INVALID not in _codes(val_custom)


def test_active_finding_cites_previous_receipt_rejected(tmp_path: Path) -> None:
    paths = _layout(tmp_path)
    prev_ledger = paths["ledger"].parent / "attempt-0.jsonl"
    create_empty_ledger(prev_ledger)
    r_prev = _record(
        prev_ledger,
        manifest="11" * 32,
        result="alpha-item-text is attested",
        attempt_id="attempt-0",
        review_id="review-1",
        status="ok",
    )

    # 1. Finding with status: active citing previous attempt receipt is rejected
    finding_active = _finding(status="active", evidence={"receipt": r_prev})
    checks = _lesson_checks(["F-01"])
    rev_data = _review(kind="lesson", manifest_hash=paths["digest"], checks=checks, findings=[finding_active])
    rev_data["attempt"]["previous_attempt_id"] = "attempt-0"
    _dump(paths["review"], rev_data)

    val_active = _validate(paths)
    assert not val_active.ok
    assert codes.RECEIPT_NOT_IN_LEDGER in _codes(val_active)

    # 2. Finding with status: persisting citing previous attempt receipt is accepted
    finding_persisting = _finding(status="persisting", evidence={"receipt": r_prev})
    rev_data_persisting = _review(
        kind="lesson", manifest_hash=paths["digest"], checks=checks, findings=[finding_persisting]
    )
    rev_data_persisting["attempt"]["previous_attempt_id"] = "attempt-0"
    _dump(paths["review"], rev_data_persisting)

    val_persisting = _validate(paths)
    assert val_persisting.ok


def test_v4_and_review_both_record(server_module, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from mcp.types import TextContent

    ledger = tmp_path / "review-1" / "attempt-1.jsonl"
    _arm(monkeypatch, ledger)

    v4_invocations: list[tuple[str, dict]] = []

    def fake_v4_record(*, name: str, typed_outcome: dict) -> None:
        v4_invocations.append((name, typed_outcome))

    monkeypatch.setattr(server_module, "_record_v4_typed_invocation", fake_v4_record)

    async def fake_verify_words(_arguments):
        content = [TextContent(type="text", text="Batch verification: 1 words\nFound: 1/1\n- слово — FOUND")]
        typed_outcome = {"disposition": "found", "hits": 1}
        return content, typed_outcome

    monkeypatch.setattr(server_module, "handle_verify_words", fake_verify_words)

    result = _run(server_module.call_tool("verify_words", {"words": ["слово"]}))
    assert any("receipt: " in t.text for t in result)
    receipt = result[0].text.splitlines()[-1].removeprefix("receipt: ")

    stored = lookup(ledger, receipt)
    assert stored["tool"] == "verify_words"
    assert stored["status"] == "ok"

    assert len(v4_invocations) == 1
    assert v4_invocations[0][0] == "verify_words"
    assert v4_invocations[0][1] == {"disposition": "found", "hits": 1}


def test_server_recording_off_preserves_typed_structured_content(
    server_module, monkeypatch: pytest.MonkeyPatch
) -> None:
    from mcp.types import CallToolRequestParams, TextContent

    _quiet_env(monkeypatch)

    async def fake_verify_words(_arguments):
        content = [TextContent(type="text", text="Batch verification: 1 words\nFound: 1/1\n- слово — FOUND")]
        typed_outcome = {"disposition": "found", "hits": 1}
        return content, typed_outcome

    monkeypatch.setattr(server_module, "handle_verify_words", fake_verify_words)

    params = CallToolRequestParams(name="verify_words", arguments={"words": ["слово"]})
    res = _run(server_module._on_call_tool(None, params))
    assert res.is_error is False
    assert not any("receipt:" in t.text for t in res.content)
    assert res.structured_content == {"disposition": "found", "hits": 1}


def test_review_mode_receipt_in_both_wire_channels(
    server_module, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from mcp.types import CallToolRequestParams, TextContent

    ledger = tmp_path / "review-1" / "attempt-1.jsonl"
    _arm(monkeypatch, ledger)
    original = {"disposition": "found", "hits": 1, "evidence_identifiers": []}

    async def fake_verify_words(_arguments):
        content = [TextContent(type="text", text="Batch verification: 1 words\nFound: 1/1")]
        return content, dict(original)

    monkeypatch.setattr(server_module, "handle_verify_words", fake_verify_words)

    params = CallToolRequestParams(name="verify_words", arguments={"words": ["слово"]})
    res = _run(server_module._on_call_tool(None, params))
    assert res.is_error is False
    receipt = records(ledger)[-1]["receipt_id"]
    assert res.structured_content == {**original, "receipt": receipt}
    assert res.content[-1].text.endswith("\nreceipt: " + receipt)
    assert lookup(ledger, receipt)["tool"] == "verify_words"


def test_review_mode_without_typed_outcome_keeps_structured_content_empty(
    server_module, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from mcp.types import CallToolRequestParams, TextContent

    ledger = tmp_path / "review-1" / "attempt-1.jsonl"
    _arm(monkeypatch, ledger)

    async def fake(_arguments):
        return [TextContent(type="text", text="plain-result")]

    monkeypatch.setattr(server_module, "handle_verify_words", fake)
    params = CallToolRequestParams(name="verify_words", arguments={"words": ["слово"]})
    res = _run(server_module._on_call_tool(None, params))
    receipt = records(ledger)[-1]["receipt_id"]
    assert res.structured_content is None
    assert res.content[-1].text == "plain-result\nreceipt: " + receipt


def test_review_receipt_does_not_leak_into_recorded_result_or_v4(
    server_module, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from mcp.types import TextContent

    ledger = tmp_path / "review-1" / "attempt-1.jsonl"
    _arm(monkeypatch, ledger)
    seen: list[dict] = []
    monkeypatch.setattr(
        server_module, "_record_v4_typed_invocation", lambda *, name, typed_outcome: seen.append(typed_outcome)
    )

    async def fake_verify_words(_arguments):
        return [TextContent(type="text", text="body")], {"disposition": "found", "hits": 1}

    monkeypatch.setattr(server_module, "handle_verify_words", fake_verify_words)
    _content, _is_error, typed = _run(server_module._dispatch_tool_call("verify_words", {"words": ["слово"]}))
    assert typed["receipt"] == records(ledger)[-1]["receipt_id"]
    assert seen == [{"disposition": "found", "hits": 1}]
    assert records(ledger)[-1]["result"] == "body"
