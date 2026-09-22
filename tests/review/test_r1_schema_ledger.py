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
    append,
    collect_snapshots,
    dumps,
    lookup,
    records,
    session_from_environ,
)
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
    "sources_db": {"digest": "11" * 32, "metadata": {"db_sha256": "11" * 32}},
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
    manifest = tmp_path / "manifest.yaml"
    lesson = tmp_path / "lesson.yaml"
    review = tmp_path / "review.yaml"
    ledger = tmp_path / "attempt-1.jsonl"
    digest = _write_manifest(manifest, recap=recap)
    _dump(lesson, _lesson())
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
    assert (path.stat().st_mode & 0o777) == 0o644
    sidecar = path.with_name(path.name + ".sha256")
    assert sidecar.read_text(encoding="ascii") == hashlib.sha256(path.read_bytes()).hexdigest() + "\n"
    assert (sidecar.stat().st_mode & 0o777) == 0o644


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


def test_collect_snapshots_uses_fingerprint_and_vesum_metadata(tmp_path: Path) -> None:
    sources_db = tmp_path / "sources.db"
    sources_db.write_bytes(b"sources-bytes")
    vesum = tmp_path / "vesum.db"
    connection = sqlite3.connect(vesum)
    connection.execute("CREATE TABLE vesum_build_metadata (key TEXT, value TEXT)")
    connection.execute(
        "INSERT INTO vesum_build_metadata VALUES ('canonical_jsonl_sha256', ?)",
        ("ab" * 32,),
    )
    connection.commit()
    connection.close()
    from scripts.curriculum.evidence.sources import Sources

    sources = Sources(sources_db=sources_db, vesum_db=vesum)
    try:
        snapshot = collect_snapshots(sources=sources, trie_digest="cd" * 32)
    finally:
        sources.close()
    assert snapshot["sources_db"]["digest"] == hashlib.sha256(b"sources-bytes").hexdigest()
    assert snapshot["vesum"]["digest"] == "ab" * 32
    assert snapshot["trie"]["digest"] == "cd" * 32


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
        ("outcome", codes.OUTCOME_NOT_IN_LEDGER),
        ("no_sub", codes.LANGUAGE_SUB_DIMENSION_MISSING),
        ("missing_check", codes.CHECK_MISSING),
        ("recap_check", codes.CHECK_NOT_APPLICABLE),
        ("duplicate", codes.DUPLICATE_FINDING_ID),
        ("two_branches", codes.EVIDENCE_BRANCH_COUNT),
        ("no_branch", codes.EVIDENCE_BRANCH_COUNT),
        ("scope", codes.SCOPE_MISSING),
    ],
)
def test_one_fixture_per_rejection(tmp_path: Path, mutate: str, code: str) -> None:
    paths = _layout(tmp_path)
    result_text = "alpha-item-text is attested" if mutate != "outcome" else "No results found."
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
    assert stored["arguments"] == {"words": ["placeholder"]}
    assert len(stored["server_version"]) == 64

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
    ("check_russian_shadow", json.dumps({"matches_russian": False, "russian_lemma": None, "ukrainian_alternative": None, "confidence": 0.0})),
    ("verify_quote", json.dumps({"matched": False, "best_confidence": 0.0, "matched_lines": [], "search_normalized": {"author_query": "author", "text_query": "text"}})),
    ("search_text", "No results found."),
    ("search_ua_gec_errors", 'No UA-GEC results found for: "деякі речі"'),
    ("verify_words", "Batch verification: 1 words\nFound: 0/1\n\n- **неслово** — NOT FOUND"),
    ("inspect_word", "'неслово' — Status: NOT_FOUND\n- Effective markers: none\n- Clean analyses: 0\n- Marked analyses: 0\n- Raw payload: {\"word\": \"неслово\", \"status\": \"NOT_FOUND\"}"),
    ("inspect_words", "Batch inspection: 1 words\n\n- **неслово** — NOT FOUND\n\nRaw payload:\n{\"words\": {\"неслово\": {\"status\": \"NOT_FOUND\"}}}"),
    ("verify_stress", "неслово — not_found"),
    ("query_grac", "**неслово**: frequency = 0, relative = 0.00 per million"),
    ("query_ulif", "No ULIF paradigm found for: 'кицяневідома'"),
    ("query_r2u", "No r2u translation found for: 'неслово'"),
    ("query_sum20", "No official offline СУМ-20 entry is currently ingested for 'неслово'. This tool does not make a live request or use a fallback source."),
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
            _review(kind="lesson", manifest_hash=paths["digest"], checks=_lesson_checks(["F-01"]), findings=[finding_no_hits]),
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
            _review(kind="lesson", manifest_hash=paths["digest"], checks=_lesson_checks(["F-01"]), findings=[finding_hits]),
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
        _review(kind="lesson", manifest_hash=mixed_paths["digest"], checks=_lesson_checks(["F-01"]), findings=[finding_mixed_support]),
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
        _review(kind="lesson", manifest_hash=mixed_paths["digest"], checks=_lesson_checks(["F-01"]), findings=[finding_mixed_no_hits]),
    )
    mixed_rej = _validate(mixed_paths)
    assert not mixed_rej.ok and codes.OUTCOME_NOT_IN_LEDGER in _codes(mixed_rej)
