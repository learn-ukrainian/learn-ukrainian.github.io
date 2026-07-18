"""Offline reduce: ULIF cache envelopes → structured candidate (#5230)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.lexicon.runner.network_cache import NetworkCache, compute_request_key
from scripts.lexicon.runner.offline_reduce import (
    PHASE,
    build_lemma_request_index,
    open_raw_cache_ro,
    reduce_offline_slice,
)
from scripts.lexicon.runner.ulif_dictua_parse import (
    ULIF_PARSER_VERSION,
    ULIF_STRUCTURED_SCHEMA_VERSION,
    parse_dictua_envelope,
    strip_raw_html,
    summarize_artifacts,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "ulif_dictua"
USER_AGENT = "learn-ukrainian-atlas/1.0 (noncommercial educational ULIF per-lemma fetch; issue #5230)"


def _html(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def _envelope(lemma: str, status: str, stages: list[tuple[str, str]]) -> dict:
    return {
        "lemma": lemma,
        "status": status,
        "responses": [
            {
                "stage": stage,
                "status_code": 200,
                "headers": {"content-type": "text/html"},
                "html": _html(html_name),
            }
            for stage, html_name in stages
        ],
    }


def _seed_network_cache(path: Path, items: list[tuple[str, dict]]) -> dict[str, str]:
    """Write fetch-shaped raw_cache rows; return lemma → request_key."""
    cache = NetworkCache(path, owner_id="test-reduce-seed")
    cache.open()
    keys: dict[str, str] = {}
    try:
        for lemma, envelope in items:
            body = (json.dumps(envelope, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
            request_body = json.dumps(
                {"adapter": "ulif-dictua-fetch-v1", "lemma": lemma},
                ensure_ascii=False,
                sort_keys=True,
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
            # Status stub only — mirrors production fetch-only parsed_cache.
            stub = {
                "lemma_id": lemma,
                "request_key": request_key,
                "status": envelope["status"],
                "response_count": len(envelope["responses"]),
            }
            cache.put_parsed(
                request_key=request_key,
                body_sha256=hashlib_sha256(body),
                parser_version="ulif-dictua-fetch-v1",
                normalizer_version="none",
                schema_version="ulif-raw-envelope-v1",
                parsed_payload=json.dumps(stub, ensure_ascii=False, sort_keys=True),
            )
            keys[lemma] = request_key
    finally:
        cache.close()
    return keys


def hashlib_sha256(body: bytes) -> str:
    import hashlib

    return hashlib.sha256(body).hexdigest()


@pytest.fixture
def sample_envelopes() -> list[tuple[str, dict]]:
    return [
        (
            "привіт",
            _envelope(
                "привіт",
                "ok",
                [
                    ("initial", "privit-paradigm.html"),
                    ("paradigm", "privit-paradigm.html"),
                    ("synonyms", "privit-synonyms.html"),
                    ("phraseology", "privit-phraseology.html"),
                ],
            ),
        ),
        (
            "говорити",
            _envelope(
                "говорити",
                "ok",
                [
                    ("initial", "hovoryty-paradigm.html"),
                    ("paradigm", "hovoryty-paradigm.html"),
                    ("synonyms", "hovoryty-synonyms.html"),
                ],
            ),
        ),
        (
            "привіточок",
            _envelope(
                "привіточок",
                "not_found",
                [
                    ("initial", "privit-paradigm.html"),
                    ("paradigm", "privit-paradigm.html"),
                ],
            ),
        ),
        (
            "добрий",
            # No paradigm stage: antonyms-only envelope still yields structured groups.
            _envelope(
                "добрий",
                "ok",
                [
                    ("initial", "privit-paradigm.html"),
                    ("antonyms", "dobryi-antonyms.html"),
                ],
            ),
        ),
    ]


def test_parse_dictua_envelope_ok_and_not_found(sample_envelopes):
    by_lemma = dict(sample_envelopes)
    ok = parse_dictua_envelope(by_lemma["привіт"], request_key="rk1")
    assert ok["status"] == "ok"
    assert ok["parser_version"] == ULIF_PARSER_VERSION
    assert ok["schema_version"] == ULIF_STRUCTURED_SCHEMA_VERSION
    assert "paradigm" in ok["sections"]
    assert len(ok["sections"]["synonyms"]) >= 3
    assert ok["sections"]["synonyms"][0]["terms"][0]["text"] == "ВІТА́ННЯ"
    assert "raw_html" not in ok["sections"]["paradigm"]
    assert "raw_html" not in ok["sections"]["synonyms"][0]

    nf = parse_dictua_envelope(by_lemma["привіточок"], request_key="rk2")
    assert nf["status"] == "not_found"
    assert nf["sections"] == {}

    ant = parse_dictua_envelope(by_lemma["добрий"], request_key="rk3")
    assert "antonyms" in ant["sections"]
    assert len(ant["sections"]["antonyms"]) >= 1


def test_strip_raw_html_removes_nested_keys():
    payload = {"rows": [[{"raw_html": "<b>x</b>", "text": "x"}]], "raw_html": "<table/>"}
    cleaned = strip_raw_html(payload)
    assert cleaned == {"rows": [[{"text": "x"}]]}


def test_reduce_offline_slice_resumable_after_kill(tmp_path, sample_envelopes):
    cache_path = tmp_path / "network-cache.sqlite"
    keys = _seed_network_cache(cache_path, sample_envelopes)
    assert len(keys) == 4

    work = tmp_path / "work"
    lemmas = [lemma for lemma, _ in sample_envelopes]
    cohort = tmp_path / "slice.txt"
    cohort.write_text("\n".join(lemmas) + "\n", encoding="utf-8")

    # First pass: stop after 2 lemmas (simulates kill mid-run).
    first = reduce_offline_slice(
        network_cache=cache_path,
        work_dir=work,
        cohort_path=cohort,
        max_lemmas=2,
    )
    assert first.get("error") is None
    assert first["processed_this_invocation"] == 2
    assert first["complete"] is False
    counts = first["counts"]
    assert counts.get("done", 0) == 2
    assert counts.get("pending", 0) == 2

    # Resume without force_new: finishes remaining units.
    second = reduce_offline_slice(
        network_cache=cache_path,
        work_dir=work,
        cohort_path=cohort,
    )
    assert second.get("error") is None
    assert second["complete"] is True
    assert second["counts"].get("done") == 4
    assert second["ulif_summary"]["status_counts"].get("not_found") == 1
    assert second["ulif_summary"]["status_counts"].get("ok", 0) >= 1
    assert second["ulif_summary"]["section_presence"]["synonyms"] >= 1

    candidate = Path(second["candidate"]["output_path"])
    assert candidate.is_file()
    data = json.loads(candidate.read_text(encoding="utf-8"))
    assert data["phase"] == PHASE
    assert len(data["entries"]) == 4
    statuses = {e["lemma"]: e["ulif_dictua"]["status"] for e in data["entries"]}
    assert statuses["привіточок"] == "not_found"
    assert statuses["привіт"] == "ok"
    assert "paradigm" in data["entries"][0]["ulif_dictua"]["sections"] or any(
        e["ulif_dictua"]["sections"].get("paradigm") for e in data["entries"] if e["lemma"] == "привіт"
    )

    div = Path(second["divergence"]["path"])
    assert div.is_file()
    report = json.loads(div.read_text(encoding="utf-8"))
    assert report["ulif"]["artifact_count"] == 4
    assert report["blocked_reason"]  # no baseline in this test


def test_raw_cache_ro_index_does_not_require_writer_lock(tmp_path, sample_envelopes):
    cache_path = tmp_path / "network-cache.sqlite"
    _seed_network_cache(cache_path, sample_envelopes[:1])
    # Hold exclusive writer lock in another handle — RO index should still work.
    writer = NetworkCache(cache_path, owner_id="writer-hold")
    writer.open()
    try:
        conn = open_raw_cache_ro(cache_path)
        try:
            index = build_lemma_request_index(conn)
            assert "привіт" in index
        finally:
            conn.close()
    finally:
        writer.close()


def test_summarize_artifacts_aggregate_only():
    arts = [
        {"status": "ok", "sections": {"paradigm": {}, "synonyms": [{}, {}]}},
        {"status": "not_found", "sections": {}},
        {"status": "ok", "sections": {"paradigm": {}, "antonyms": [{}]}},
    ]
    summary = summarize_artifacts(arts)
    assert summary["artifact_count"] == 3
    assert summary["status_counts"] == {"ok": 2, "not_found": 1}
    assert summary["section_presence"]["paradigm"] == 2
    assert summary["relation_group_totals"]["synonyms"] == 2
    assert summary["relation_group_totals"]["antonyms"] == 1
