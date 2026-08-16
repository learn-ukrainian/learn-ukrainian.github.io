"""Contract and deterministic unit tests for the Work projection foundation."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from scripts.work.attention import derive_health, derive_safe_next_action
from scripts.work.normalize import _match_dispatch, build_projection
from scripts.work.relations import (
    detect_dependency_cycles,
    extract_body_relations,
    issue_work_id,
    make_work_id,
)
from scripts.work.schema import (
    SCHEMA_VERSION,
    SchemaValidationError,
    load_schema,
    parse_saved_view_params,
    schema_digest_sha256,
    validate_projection,
)
from scripts.work.sources_public import SectionResult, fetch_fleet_reviews

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "work" / "projection_public_min.json"
REPO = "learn-ukrainian/learn-ukrainian.github.io"


def test_schema_loads_and_fixture_validates():
    schema = load_schema()
    assert schema["properties"]["schema_version"]["const"] == SCHEMA_VERSION
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    validate_projection(payload)
    assert payload["foundation_status"] == "FOUNDATION_COMPLETE"
    assert payload["foundation_status"] != "COMPLETE"
    assert payload["capabilities"]["mutation"] is False


def test_identity_serialization_is_collision_safe():
    a = make_work_id("public-monitor", REPO, "issue", "1")
    b = make_work_id("private-local-adapter", REPO, "issue", "1")
    assert a != b
    assert a.startswith("wp1:")
    assert a == issue_work_id(REPO, 1)


def test_saved_view_rejects_free_text_and_private_keys():
    with pytest.raises(SchemaValidationError):
        parse_saved_view_params({"q": "secret search"})
    with pytest.raises(SchemaValidationError):
        parse_saved_view_params({"private_endpoint": "http://127.0.0.1:9999"})
    with pytest.raises(SchemaValidationError):
        parse_saved_view_params({"health": "kinda-bad"})
    ok = parse_saved_view_params(
        {"health": "AT_RISK", "kind": "issue", "orphan": "true", "repository_id": REPO}
    )
    assert ok["health"] == ["AT_RISK"]
    assert ok["orphan"] is True


def test_saved_view_lifecycle_allowlist():
    ok = parse_saved_view_params({"lifecycle": "open"})
    assert ok["lifecycle"] == ["open"]
    with pytest.raises(SchemaValidationError, match="invalid lifecycle filter"):
        parse_saved_view_params({"lifecycle": "nonce-xyz-not-a-lifecycle"})


def test_saved_view_repository_id_allowlist():
    """Public P1 accepts only the closed public repository_id singleton."""
    from scripts.work.sources_public import public_repository_id

    configured = public_repository_id()
    assert configured == REPO
    ok = parse_saved_view_params({"repository_id": configured})
    assert ok["repository_id"] == [configured]
    with pytest.raises(SchemaValidationError, match="invalid repository_id"):
        parse_saved_view_params({"repository_id": "some-owner/random-repo-not-configured"})


def test_public_repository_identity_ignores_env_override(monkeypatch):
    """WORK_PUBLIC_REPOSITORY must not repoint source, query, cache, or projection."""
    from fastapi.testclient import TestClient

    from scripts.api.main import app
    from scripts.api.state_helpers import cache_invalidate
    from scripts.api.work_router import projection_cache_key
    from scripts.work.sources_public import (
        DEFAULT_PUBLIC_REPOSITORY,
        admit_public_repository_id,
        collect_public_sections,
        public_repository_id,
    )

    foreign = "evil-org/private-infra-must-not-project"
    monkeypatch.setenv("WORK_PUBLIC_REPOSITORY", foreign)

    assert public_repository_id() == DEFAULT_PUBLIC_REPOSITORY == REPO
    assert admit_public_repository_id() == REPO
    assert admit_public_repository_id(REPO) == REPO
    with pytest.raises(ValueError, match="public repository_id must be exactly"):
        admit_public_repository_id(foreign)

    # Saved-view allowlist still admits only the closed singleton, not the env value.
    ok = parse_saved_view_params({"repository_id": REPO})
    assert ok["repository_id"] == [REPO]
    with pytest.raises(SchemaValidationError, match="invalid repository_id"):
        parse_saved_view_params({"repository_id": foreign})
    assert projection_cache_key(ok) == projection_cache_key({"repository_id": [REPO]})
    assert foreign not in projection_cache_key(ok)

    # Collectors must query the closed public repo even when env names another.
    seen_repos: list[str] = []

    def gh_runner(args: list[str], timeout_s: float) -> tuple[int, str, str]:
        if "--repo" in args:
            seen_repos.append(args[args.index("--repo") + 1])
        return 0, "[]", ""

    def fleet_loader(limit: int, offset: int, repository: str) -> dict:
        # Pre-pagination repository filter (matches fleet_reviews SQL boundary).
        rows = [
            {
                "review_id": "rev-public",
                "repository": REPO,
                "pr_number": 1,
                "state": "running",
                "sealed_verdict_available": False,
            },
            {
                "review_id": "rev-foreign",
                "repository": foreign,
                "pr_number": 2,
                "state": "running",
                "sealed_verdict_available": True,
            },
        ]
        scoped = [r for r in rows if r["repository"] == repository]
        if offset:
            return {
                "total": len(scoped),
                "reviews": [],
                "filters": {"repository": repository},
            }
        return {
            "total": len(scoped),
            "reviews": scoped[offset : offset + limit],
            "filters": {"repository": repository},
        }

    sections = collect_public_sections(
        gh_runner=gh_runner,
        streams_loader=lambda: {
            "_status": "ok",
            "open_total": 0,
            "orphans": [],
            "multi_homed": [],
            "pending_native_link": [],
            "ok": True,
        },
        delegate_active_loader=lambda repository: {"total": 0, "tasks": []},
        delegate_tasks_loader=lambda repository: {"total": 0, "tasks": []},
        fleet_reviews_loader=fleet_loader,
    )
    assert set(seen_repos) == {REPO}
    assert foreign not in seen_repos
    assert sections["fleet_reviews"].count == 1
    assert sections["fleet_reviews"].payload["reviews"][0]["repository"] == REPO

    projection = build_projection(sections)
    validate_projection(projection)
    assert {item["repository_id"] for item in projection["items"]} <= {REPO}
    blob = json.dumps(projection)
    assert foreign not in blob

    # Explicit foreign repository_id parameter also fails closed.
    with pytest.raises(ValueError, match="public repository_id must be exactly"):
        collect_public_sections(repository_id=foreign, gh_runner=gh_runner)
    with pytest.raises(ValueError, match="public repository_id must be exactly"):
        build_projection(sections, repository_id=foreign)
    with pytest.raises(ValueError, match="public repository_id must be exactly"):
        fetch_fleet_reviews(loader=fleet_loader, repository_id=foreign)

    # Capabilities surface remains pinned to the closed identity under env poison.
    cache_invalidate("work:v1:projection")
    client = TestClient(app, raise_server_exceptions=False)
    caps = client.get("/api/work/v1/capabilities")
    assert caps.status_code == 200
    assert caps.json()["public_repository_id"] == REPO
    assert foreign not in caps.text


def test_collector_entry_points_fail_closed_before_runner():
    """Direct collector invocation must admit repo identity before any runner call.

    Foreign / cased / suffixed / whitespace-padded repository ids must raise and
    must not touch issues, PRs, reviews, normalization, cache keys, filters, or
    emitted projection payloads.
    """
    from scripts.api.work_router import projection_cache_key
    from scripts.work.normalize import build_projection, build_public_projection
    from scripts.work.sources_public import (
        admit_public_repository_id,
        collect_public_sections,
        fetch_fleet_reviews,
        fetch_open_issues,
        fetch_open_prs,
        public_repository_id,
    )

    foreign_exact = "evil-org/private-infra-must-not-project"
    # Forms that must fail closed at admit/collector boundaries (exact match only).
    adversarial_ids = [
        foreign_exact,
        "LEARN-UKRAINIAN/learn-ukrainian.github.io",  # casing
        "learn-ukrainian/learn-ukrainian.github.io-evil",  # suffix
        "learn-ukrainian/learn-ukrainian.github.io ",  # trailing whitespace
        " learn-ukrainian/learn-ukrainian.github.io",  # leading whitespace
        "other-owner/learn-ukrainian.github.io",  # same-name different owner
        "learn-ukrainian/learn-ukrainian.github.io/extra",  # path suffix
        "..",
        "not-a-repo",
        " ",
        "\t",
    ]
    # Saved-view parser strips then allowlists; whitespace-only becomes a no-op
    # (not a foreign filter). Non-canonical non-empty strings still reject.
    saved_view_rejected = [
        foreign_exact,
        "LEARN-UKRAINIAN/learn-ukrainian.github.io",
        "learn-ukrainian/learn-ukrainian.github.io-evil",
        "other-owner/learn-ukrainian.github.io",
        "learn-ukrainian/learn-ukrainian.github.io/extra",
        "..",
        "not-a-repo",
    ]

    runner_calls: list[list[str]] = []

    def tracking_runner(args: list[str], timeout_s: float) -> tuple[int, str, str]:
        runner_calls.append(list(args))
        return 0, "[]", ""

    def tracking_fleet(limit: int, offset: int, repository: str) -> dict:
        runner_calls.append(["fleet", str(limit), str(offset), repository])
        return {
            "total": 0,
            "reviews": [],
            "filters": {"repository": repository},
        }

    # Canonical / omitted ids still reach the runner with the closed identity.
    assert admit_public_repository_id() == REPO
    assert admit_public_repository_id(None) == REPO
    assert admit_public_repository_id("") == REPO
    assert admit_public_repository_id(REPO) == REPO
    assert public_repository_id() == REPO

    issues_ok = fetch_open_issues(REPO, runner=tracking_runner)
    prs_ok = fetch_open_prs(None, runner=tracking_runner)
    assert issues_ok.status == "ok"
    assert prs_ok.status == "ok"
    assert len(runner_calls) == 2
    for args in runner_calls:
        assert "--repo" in args
        assert args[args.index("--repo") + 1] == REPO
    runner_calls.clear()

    # Every non-canonical form fails closed with zero runner side effects.
    for bad in adversarial_ids:
        with pytest.raises(ValueError, match="public repository_id must be exactly"):
            admit_public_repository_id(bad)
        with pytest.raises(ValueError, match="public repository_id must be exactly"):
            fetch_open_issues(bad, runner=tracking_runner)
        with pytest.raises(ValueError, match="public repository_id must be exactly"):
            fetch_open_prs(bad, runner=tracking_runner)
        with pytest.raises(ValueError, match="public repository_id must be exactly"):
            fetch_fleet_reviews(loader=tracking_fleet, repository_id=bad)
        with pytest.raises(ValueError, match="public repository_id must be exactly"):
            collect_public_sections(repository_id=bad, gh_runner=tracking_runner)
        with pytest.raises(ValueError, match="public repository_id must be exactly"):
            build_public_projection(repository_id=bad, gh_runner=tracking_runner)

    for bad in saved_view_rejected:
        with pytest.raises(SchemaValidationError, match="invalid repository_id"):
            parse_saved_view_params({"repository_id": bad})
    # Whitespace-only / empty saved-view values cannot install a foreign filter.
    assert parse_saved_view_params({"repository_id": " "}) == {}
    assert parse_saved_view_params({"repository_id": "\t"}) == {}
    assert parse_saved_view_params({"repository_id": ""}) == {}

    assert runner_calls == [], "foreign repository_id must never invoke runners"

    # Normalize / filters / cache keys / projection emit stay pinned when sections
    # already exist; foreign repository_id cannot re-label or leak into output.
    clean_sections = {
        "issues": SectionResult(
            "issues",
            "ok",
            payload=[
                {
                    "number": 9,
                    "title": "public issue",
                    "labels": [],
                    "assignees": [],
                    "body": "blocked by #1",
                    "createdAt": "2026-08-01T00:00:00Z",
                    "updatedAt": "2026-08-01T00:00:00Z",
                    "url": f"https://github.com/{REPO}/issues/9",
                    "state": "OPEN",
                }
            ],
            count=1,
        ),
        "prs": SectionResult("prs", "ok", payload=[], count=0),
        "streams": SectionResult(
            "streams",
            "ok",
            payload={
                "orphans": [],
                "multi_homed": [],
                "pending_native_link": [],
                "open_total": 1,
                "open_issue_numbers": [9],
            },
            count=1,
        ),
        "delegate_active": SectionResult(
            "delegate_active", "ok", payload={"total": 0, "tasks": []}, count=0
        ),
        "delegate_tasks": SectionResult(
            "delegate_tasks", "ok", payload={"total": 0, "tasks": []}, count=0
        ),
        "fleet_reviews": SectionResult(
            "fleet_reviews",
            "ok",
            payload={
                "total": 1,
                "reviews": [
                    {
                        "review_id": "rev-foreign-try",
                        "repository": foreign_exact,
                        "pr_number": 9,
                        "state": "running",
                        "sealed_verdict_available": True,
                    }
                ],
            },
            count=1,
        ),
    }

    for bad in adversarial_ids:
        with pytest.raises(ValueError, match="public repository_id must be exactly"):
            build_projection(clean_sections, repository_id=bad)

    projection = build_projection(clean_sections, repository_id=REPO)
    validate_projection(projection)
    assert {item["repository_id"] for item in projection["items"]} == {REPO}
    blob = json.dumps(projection)
    cache_key = projection_cache_key(
        parse_saved_view_params({"repository_id": REPO})
    )
    for bad in adversarial_ids:
        if not bad.strip():
            # Whitespace-only forms are not embeddable repository ids; skip
            # substring checks that would false-positive on normal JSON.
            continue
        assert bad not in blob
        assert bad not in cache_key
    assert foreign_exact not in blob
    assert foreign_exact not in cache_key

    ok_filters = parse_saved_view_params({"repository_id": REPO})
    assert ok_filters["repository_id"] == [REPO]
    assert projection_cache_key(ok_filters) == projection_cache_key(
        {"repository_id": [REPO]}
    )
    # Foreign filter values never become cache-key material — including via
    # direct projection_cache_key calls (self-validating boundary).
    for bad in saved_view_rejected:
        with pytest.raises(SchemaValidationError, match="invalid repository_id"):
            projection_cache_key(parse_saved_view_params({"repository_id": bad}))
        with pytest.raises(SchemaValidationError, match="invalid repository_id"):
            projection_cache_key({"repository_id": bad})
    # Padded canonical forms: parser strips before admit, so exact public id
    # remains the only cache-key identity.
    padded = parse_saved_view_params(
        {"repository_id": f"  {REPO}  "}
    )
    assert padded["repository_id"] == [REPO]
    assert projection_cache_key(padded) == projection_cache_key(ok_filters)
    assert projection_cache_key({"repository_id": f"  {REPO}  "}) == projection_cache_key(
        ok_filters
    )


def test_saved_view_multivalue_filters_are_canonical():
    """Duplicate / reordered multivalue query forms share one canonical filter dict."""
    from scripts.work.sources_public import public_repository_id

    configured = public_repository_id()
    a = parse_saved_view_params(
        {
            "health": ["ON_TRACK", "AT_RISK", "AT_RISK"],
            "kind": ["pr", "issue"],
            "lifecycle": ["draft", "open", "open"],
            "source_id": ["private-local-adapter", "public-monitor"],
            "repository_id": configured,
        }
    )
    b = parse_saved_view_params(
        {
            "health": ["AT_RISK", "ON_TRACK"],
            "kind": ["issue", "pr"],
            "lifecycle": ["open", "draft"],
            "source_id": ["public-monitor", "private-local-adapter"],
            "repository_id": configured,
        }
    )
    assert a == b
    assert a["health"] == ["AT_RISK", "ON_TRACK"]
    assert a["resource_kind"] == ["issue", "pr"]
    assert a["lifecycle"] == ["draft", "open"]
    assert a["source_id"] == ["private-local-adapter", "public-monitor"]
    assert a["repository_id"] == [configured]

    from scripts.api.work_router import projection_cache_key

    assert projection_cache_key(a) == projection_cache_key(b)


def test_projection_cache_key_direct_call_rejects_and_canonicalizes():
    """Cache-key boundary self-validates; direct calls need no prevalidated caller."""
    from scripts.api.state_helpers import cache_invalidate, cache_set
    from scripts.api.work_router import CACHE_KEY, projection_cache_key

    # Unknown keys and foreign repositories fail closed at the key boundary.
    with pytest.raises(SchemaValidationError, match="saved-view key not allowed"):
        projection_cache_key({"q": "secret-search"})
    with pytest.raises(SchemaValidationError, match="saved-view key not allowed"):
        projection_cache_key({"private_endpoint": "http://127.0.0.1:9"})
    with pytest.raises(SchemaValidationError, match="invalid repository_id"):
        projection_cache_key({"repository_id": "evil-org/private-infra"})
    with pytest.raises(SchemaValidationError, match="invalid health filter"):
        projection_cache_key({"health": "not-a-health"})

    # Raw reordered/duplicate multivalues collide with already-parsed forms.
    # repository_id is a singleton domain (raw maxItems=1); health/kind allow
    # duplicates only within their finite domain bounds.
    raw_a = {
        "health": ["ON_TRACK", "AT_RISK", "AT_RISK"],
        "kind": ["pr", "issue"],
        "repository_id": REPO,
    }
    raw_b = {
        "health": ["AT_RISK", "ON_TRACK"],
        "kind": ["issue", "pr"],
        "repository_id": REPO,
    }
    parsed = parse_saved_view_params(raw_a)
    key_raw_a = projection_cache_key(raw_a)
    key_raw_b = projection_cache_key(raw_b)
    key_parsed = projection_cache_key(parsed)
    assert key_raw_a == key_raw_b == key_parsed
    assert key_raw_a.startswith(f"{CACHE_KEY}:")
    # Single encoding only — no nested repr of an already-encoded key string.
    assert key_raw_a.count(CACHE_KEY) == 1

    # Prefix invalidation still covers every permanent filter variant.
    cache_set(key_raw_a, {"ok": True})
    cache_set(projection_cache_key({}), {"empty": True})
    removed = cache_invalidate(CACHE_KEY)
    assert removed >= 2


def test_filters_applied_source_id_is_schema_backed():
    """Closed filters_applied object advertises enum-backed source_id."""
    schema = load_schema()
    props = schema["properties"]["filters_applied"]["properties"]
    assert "source_id" in props
    assert props["source_id"]["items"]["enum"] == [
        "public-monitor",
        "private-local-adapter",
    ]
    assert props["source_id"]["maxItems"] == 2
    assert props["source_id"]["uniqueItems"] is True
    # Digest is content-addressed; any filters_applied change must recompute.
    digest = schema_digest_sha256()
    assert len(digest) == 64
    assert all(ch in "0123456789abcdef" for ch in digest)

    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    payload["filters_applied"] = {"source_id": ["public-monitor"]}
    validate_projection(payload)
    with pytest.raises(SchemaValidationError):
        payload["filters_applied"] = {"source_id": ["not-a-source"]}
        validate_projection(payload)


def test_filters_applied_schema_enforces_cardinality_and_enums():
    """filters_applied schema mirrors parser bounds, enums, and uniqueItems."""
    from scripts.work.schema import FILTER_MAX_RAW_ITEMS

    schema = load_schema()
    props = schema["properties"]["filters_applied"]["properties"]
    assert props["health"]["maxItems"] == FILTER_MAX_RAW_ITEMS["health"]
    assert props["health"]["uniqueItems"] is True
    assert props["resource_kind"]["maxItems"] == FILTER_MAX_RAW_ITEMS["kind"]
    assert props["resource_kind"]["uniqueItems"] is True
    assert props["lifecycle"]["maxItems"] == FILTER_MAX_RAW_ITEMS["lifecycle"]
    assert props["lifecycle"]["uniqueItems"] is True
    assert set(props["lifecycle"]["items"]["enum"]) == {
        "open",
        "draft",
        "running",
        "failed",
    }
    assert props["repository_id"]["maxItems"] == 1
    assert props["repository_id"]["uniqueItems"] is True
    assert props["repository_id"]["items"]["const"] == REPO

    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    # Noncanonical (duplicate) arrays fail uniqueItems even when members are valid.
    with pytest.raises(SchemaValidationError):
        payload["filters_applied"] = {"health": ["AT_RISK", "AT_RISK"]}
        validate_projection(payload)
    with pytest.raises(SchemaValidationError):
        payload["filters_applied"] = {"resource_kind": ["issue", "issue"]}
        validate_projection(payload)
    with pytest.raises(SchemaValidationError):
        payload["filters_applied"] = {"lifecycle": ["open", "not-a-lifecycle"]}
        validate_projection(payload)
    with pytest.raises(SchemaValidationError):
        payload["filters_applied"] = {"repository_id": ["evil-org/private"]}
        validate_projection(payload)
    with pytest.raises(SchemaValidationError):
        payload["filters_applied"] = {"repository_id": [REPO, REPO]}
        validate_projection(payload)
    # Canonical forms still validate.
    payload["filters_applied"] = {
        "health": ["AT_RISK", "ON_TRACK"],
        "resource_kind": ["issue", "pr"],
        "lifecycle": ["draft", "open"],
        "repository_id": [REPO],
        "source_id": ["public-monitor"],
        "orphan": True,
    }
    validate_projection(payload)


def test_saved_view_rejects_oversized_raw_multivalue_before_canonicalize():
    """Raw repetitions beyond the finite domain bound fail before admit work."""
    from scripts.work.schema import ALLOWED_HEALTH, FILTER_MAX_RAW_ITEMS

    oversized_health = ["ON_TRACK"] * (FILTER_MAX_RAW_ITEMS["health"] + 1)
    with pytest.raises(SchemaValidationError, match="exceeds max"):
        parse_saved_view_params({"health": oversized_health})
    # Even when the unique set would fit, raw length is the bound.
    assert len(set(oversized_health)) == 1
    assert len(oversized_health) > len(ALLOWED_HEALTH)

    with pytest.raises(SchemaValidationError, match="exceeds max"):
        parse_saved_view_params(
            {"kind": ["issue"] * (FILTER_MAX_RAW_ITEMS["kind"] + 1)}
        )
    with pytest.raises(SchemaValidationError, match="exceeds max"):
        parse_saved_view_params({"repository_id": [REPO, REPO]})
    with pytest.raises(SchemaValidationError, match="exceeds max"):
        parse_saved_view_params({"orphan": ["true", "false"]})

    # Duplicates within the allowed raw bound still canonicalize.
    ok = parse_saved_view_params(
        {
            "health": ["ON_TRACK", "AT_RISK", "AT_RISK", "ON_TRACK"],
            "lifecycle": ["open", "open", "draft"],
        }
    )
    assert ok["health"] == ["AT_RISK", "ON_TRACK"]
    assert ok["lifecycle"] == ["draft", "open"]


def test_build_projection_admits_filters_directly():
    """Direct build_projection / build_public_projection re-enter saved-view admission."""
    from scripts.work.normalize import build_public_projection
    from scripts.work.schema import SchemaValidationError

    empty = {
        "issues": SectionResult("issues", "ok", payload=[], count=0),
        "prs": SectionResult("prs", "ok", payload=[], count=0),
        "streams": SectionResult(
            "streams",
            "ok",
            payload={
                "generated_at": 1,
                "open_total": 0,
                "orphans": [],
                "multi_homed": [],
                "pending_native_link": [],
                "ok": True,
            },
            count=0,
        ),
        "delegate_active": SectionResult(
            "delegate_active", "ok", payload={"total": 0, "tasks": []}, count=0
        ),
        "delegate_tasks": SectionResult(
            "delegate_tasks", "ok", payload={"total": 0, "tasks": []}, count=0
        ),
        "fleet_reviews": SectionResult(
            "fleet_reviews", "ok", payload={"total": 0, "reviews": []}, count=0
        ),
    }

    # Foreign repository_id never appears in filters_applied.
    with pytest.raises(SchemaValidationError, match="invalid repository_id"):
        build_projection(
            empty,
            repository_id=REPO,
            filters={"repository_id": ["other-org/foreign-repository"]},
        )
    with pytest.raises(SchemaValidationError, match="saved-view key not allowed"):
        build_projection(empty, repository_id=REPO, filters={"q": "secret"})
    with pytest.raises(SchemaValidationError, match="invalid health filter"):
        build_projection(empty, repository_id=REPO, filters={"health": ["NOPE"]})

    # kind alias and resource_kind both canonicalize; only canonical form is emitted.
    via_kind = build_projection(
        empty, repository_id=REPO, filters={"kind": ["pr", "issue", "issue"]}
    )
    via_resource = build_projection(
        empty, repository_id=REPO, filters={"resource_kind": ["issue", "pr"]}
    )
    assert via_kind["filters_applied"] == via_resource["filters_applied"]
    assert via_kind["filters_applied"]["resource_kind"] == ["issue", "pr"]
    assert "kind" not in via_kind["filters_applied"]

    # build_public_projection shares the same gate (before collect).
    def no_collect(**_kwargs):
        raise AssertionError("collect must not run after filter rejection")

    with pytest.raises(SchemaValidationError, match="invalid repository_id"):
        build_public_projection(
            repository_id=REPO,
            filters={"repository_id": "evil-org/private"},
            gh_runner=no_collect,
        )


def test_fleet_reviews_and_projection_reject_mixed_repositories():
    """Formal-review rows for non-public repositories never enter the projection."""
    private_repo = "other-org/other-private-repo"
    suffix_cousin = "evil-org/learn-ukrainian.github.io"

    def loader(limit: int, offset: int, repository: str) -> dict:
        rows = [
            {
                "review_id": "rev-public",
                "repository": REPO,
                "pr_number": 42,
                "state": "running",
                "sealed_verdict_available": False,
            },
            {
                "review_id": "rev-private",
                "repository": private_repo,
                "pr_number": 7,
                "state": "running",
                "sealed_verdict_available": True,
            },
            {
                "review_id": "rev-suffix",
                "repository": suffix_cousin,
                "pr_number": 99,
                "state": "running",
                "sealed_verdict_available": True,
            },
        ]
        scoped = [r for r in rows if r["repository"] == repository]
        if offset:
            return {
                "total": len(scoped),
                "reviews": [],
                "filters": {"repository": repository},
            }
        return {
            "total": len(scoped),
            "reviews": scoped[offset : offset + limit],
            "filters": {"repository": repository},
        }

    section = fetch_fleet_reviews(loader=loader, repository_id=REPO)
    assert section.status == "ok"
    assert section.truncated is False
    assert section.count == 1
    assert section.payload["reviews"][0]["review_id"] == "rev-public"
    assert section.payload["reviews"][0]["repository"] == REPO

    mixed_rows = [
        {
            "review_id": "rev-public-unlinked",
            "repository": REPO,
            "pr_number": 5001,
            "state": "pending",
            "sealed_verdict_available": False,
        },
        {
            "review_id": "rev-private-unlinked",
            "repository": private_repo,
            "pr_number": 5002,
            "state": "pending",
            "sealed_verdict_available": True,
        },
        {
            "review_id": "rev-suffix-unlinked",
            "repository": suffix_cousin,
            "pr_number": 5003,
            "state": "pending",
            "sealed_verdict_available": True,
        },
        {
            "review_id": "rev-missing-repo",
            "repository": None,
            "pr_number": 5004,
            "state": "pending",
            "sealed_verdict_available": True,
        },
        {
            # Same PR number as an open public PR but foreign repository: must not match.
            "review_id": "rev-foreign-linked",
            "repository": private_repo,
            "pr_number": 100,
            "state": "running",
            "sealed_verdict_available": True,
        },
        {
            "review_id": "rev-public-linked",
            "repository": REPO,
            "pr_number": 100,
            "state": "running",
            "sealed_verdict_available": False,
        },
    ]
    sections = {
        "issues": SectionResult("issues", "ok", payload=[], count=0),
        "prs": SectionResult(
            "prs",
            "ok",
            payload=[
                {
                    "number": 100,
                    "title": "Public PR",
                    "state": "OPEN",
                    "isDraft": False,
                    "reviewDecision": "REVIEW_REQUIRED",
                    "statusCheckRollup": [{"state": "SUCCESS"}],
                    "mergeStateStatus": "CLEAN",
                    "labels": [],
                    "assignees": [],
                    "url": f"https://github.com/{REPO}/pull/100",
                    "createdAt": "2026-08-01T00:00:00Z",
                    "updatedAt": "2026-08-02T00:00:00Z",
                    "headRefOid": "deadbeef",
                    "headRefName": "feat/work",
                }
            ],
            count=1,
        ),
        "streams": SectionResult(
            "streams",
            "ok",
            payload={
                "generated_at": 1,
                "open_total": 0,
                "orphans": [],
                "multi_homed": [],
                "pending_native_link": [],
                "ok": True,
            },
            count=0,
        ),
        "delegate_active": SectionResult(
            "delegate_active", "ok", payload={"total": 0, "tasks": []}, count=0
        ),
        "delegate_tasks": SectionResult(
            "delegate_tasks", "ok", payload={"total": 0, "tasks": []}, count=0
        ),
        "fleet_reviews": SectionResult(
            "fleet_reviews",
            "ok",
            payload={"total": len(mixed_rows), "reviews": mixed_rows},
            count=len(mixed_rows),
        ),
    }
    projection = build_projection(sections, repository_id=REPO)
    validate_projection(projection)
    repos = {item["repository_id"] for item in projection["items"]}
    assert repos == {REPO}
    review_ids = {
        rid
        for item in projection["items"]
        for rid in ((item.get("projections") or {}).get("review") or {}).get("review_ids")
        or []
    }
    assert "rev-public-linked" in review_ids
    assert "rev-public-unlinked" in review_ids
    assert "rev-private-unlinked" not in review_ids
    assert "rev-suffix-unlinked" not in review_ids
    assert "rev-missing-repo" not in review_ids
    assert "rev-foreign-linked" not in review_ids
    blob = json.dumps(projection)
    assert private_repo not in blob
    assert suffix_cousin not in blob


def test_delegate_requires_authoritative_public_repository():
    """Foreign/unclassified delegate rows never enter payload or link to public work.

    Authoritative attribution is only ``repository`` / ``repository_id``. Paths,
    branches, and task_id numbers must not admit a row or attach it to a
    same-number public issue/PR. Totals are public-admitted only.
    """
    from scripts.work.sources_public import (
        DELEGATE_TASK_LIMIT,
        fetch_delegate_active,
        fetch_delegate_tasks,
    )

    private_repo = "other-org/other-private-repo"
    suffix_cousin = "evil-org/learn-ukrainian.github.io"
    same_number = 42

    mixed = [
        {
            "task_id": f"codex-issue-{same_number}-public",
            "agent": "codex",
            "status": "running",
            "repository": REPO,
        },
        {
            "task_id": f"claude-pr-{same_number}-public",
            "agent": "claude",
            "status": "running",
            "repository_id": REPO,
        },
        # Same task_id shape as a public issue number, but foreign repository.
        {
            "task_id": f"codex-issue-{same_number}-foreign",
            "agent": "codex",
            "status": "running",
            "repository": private_repo,
        },
        {
            "task_id": f"codex-issue-{same_number}-suffix",
            "agent": "codex",
            "status": "running",
            "repository": suffix_cousin,
        },
        # Unclassified: no authoritative field (path/branch/task_id alone).
        {
            "task_id": f"codex-issue-{same_number}-unclassified",
            "agent": "codex",
            "status": "running",
            "worktree_path": f"/Users/private/.worktrees/dispatch/codex/issue-{same_number}",
            "worktree_branch": f"codex/issue-{same_number}",
            "cwd": f"/Users/private/projects/{private_repo}",
        },
        # Ambiguous: conflicting authoritative fields.
        {
            "task_id": f"codex-issue-{same_number}-ambiguous",
            "agent": "codex",
            "status": "running",
            "repository": REPO,
            "repository_id": private_repo,
        },
        # Empty / whitespace claim is unclassified.
        {
            "task_id": f"codex-issue-{same_number}-blank",
            "agent": "codex",
            "status": "running",
            "repository": "  ",
        },
    ]
    # Private-heavy volume must not inflate public totals or force truncation.
    private_pad = [
        {
            "task_id": f"private-pad-{i}",
            "agent": "codex",
            "status": "done",
            "repository": private_repo,
        }
        for i in range(DELEGATE_TASK_LIMIT + 50)
    ]
    universe = [*private_pad, *mixed]

    def _scoped_loader(repository: str) -> dict:
        # Production contract: filter before total/page so private volume never
        # consumes the public enumeration budget.
        assert repository == REPO
        scoped = [
            row
            for row in universe
            if row.get("repository") == repository
            or row.get("repository_id") == repository
        ]
        # Drop ambiguous/blank/unclassified the way the real loader does.
        cleaned = []
        for row in scoped:
            rid = row.get("repository")
            rid2 = row.get("repository_id")
            claims = {c for c in (rid, rid2) if c not in (None, "")}
            claims = {str(c).strip() for c in claims if str(c).strip()}
            if claims == {repository}:
                cleaned.append(row)
        return {"total": len(cleaned), "tasks": cleaned}

    active = fetch_delegate_active(loader=_scoped_loader)
    tasks = fetch_delegate_tasks(loader=_scoped_loader)
    assert active.status == "ok"
    assert active.truncated is False
    assert active.count == 2
    assert active.payload["total"] == 2
    assert {t["task_id"] for t in active.payload["tasks"]} == {
        f"codex-issue-{same_number}-public",
        f"claude-pr-{same_number}-public",
    }
    assert all(t["repository"] == REPO for t in active.payload["tasks"])
    assert tasks.status == "ok"
    assert tasks.truncated is False
    assert tasks.count == 2
    assert tasks.payload["total"] == 2
    blob = json.dumps({"active": active.payload, "tasks": tasks.payload})
    assert private_repo not in blob
    assert suffix_cousin not in blob
    assert f"codex-issue-{same_number}-foreign" not in blob
    assert f"codex-issue-{same_number}-unclassified" not in blob
    assert f"codex-issue-{same_number}-ambiguous" not in blob
    assert "/Users/private/" not in blob

    # Normalization: foreign/unclassified never link to same-number public issue/PR.
    sections = {
        "issues": SectionResult(
            "issues",
            "ok",
            payload=[
                {
                    "number": same_number,
                    "title": "Public issue",
                    "labels": [],
                    "assignees": [],
                    "body": "",
                    "createdAt": "2026-08-01T00:00:00Z",
                    "updatedAt": "2026-08-02T00:00:00Z",
                    "url": f"https://github.com/{REPO}/issues/{same_number}",
                    "state": "OPEN",
                }
            ],
            count=1,
        ),
        "prs": SectionResult(
            "prs",
            "ok",
            payload=[
                {
                    "number": same_number,
                    "title": "Public PR",
                    "state": "OPEN",
                    "isDraft": False,
                    "reviewDecision": "REVIEW_REQUIRED",
                    "statusCheckRollup": [{"state": "SUCCESS"}],
                    "mergeStateStatus": "CLEAN",
                    "labels": [],
                    "assignees": [],
                    "url": f"https://github.com/{REPO}/pull/{same_number}",
                    "createdAt": "2026-08-01T00:00:00Z",
                    "updatedAt": "2026-08-02T00:00:00Z",
                    "headRefOid": "deadbeef",
                    "headRefName": "feat/work",
                }
            ],
            count=1,
        ),
        "streams": SectionResult(
            "streams",
            "ok",
            payload={
                "generated_at": 1,
                "open_total": 1,
                "orphans": [],
                "multi_homed": [],
                "pending_native_link": [],
                "ok": True,
            },
            count=1,
        ),
        "delegate_active": active,
        "delegate_tasks": SectionResult(
            "delegate_tasks",
            "ok",
            # Inject the raw mixed universe to prove normalize re-admits.
            payload={"total": len(universe), "tasks": universe},
            count=len(universe),
        ),
        "fleet_reviews": SectionResult(
            "fleet_reviews", "ok", payload={"total": 0, "reviews": []}, count=0
        ),
    }
    projection = build_projection(sections, repository_id=REPO)
    validate_projection(projection)
    issue = next(i for i in projection["items"] if i["resource_kind"] == "issue")
    pr = next(i for i in projection["items"] if i["resource_kind"] == "pr")
    assert set(issue["projections"]["dispatch"]["task_ids"]) == {
        f"codex-issue-{same_number}-public"
    }
    assert set(pr["projections"]["dispatch"]["task_ids"]) == {
        f"claude-pr-{same_number}-public"
    }
    task_ids = {
        i["remote_id"]
        for i in projection["items"]
        if i["resource_kind"] == "task"
    }
    assert f"codex-issue-{same_number}-foreign" not in task_ids
    assert f"codex-issue-{same_number}-unclassified" not in task_ids
    assert f"codex-issue-{same_number}-ambiguous" not in task_ids
    # Public linked tasks are attached to issue/PR, not re-emitted unlinked.
    assert f"codex-issue-{same_number}-public" not in task_ids
    assert f"claude-pr-{same_number}-public" not in task_ids
    proj_blob = json.dumps(projection)
    assert private_repo not in proj_blob
    assert suffix_cousin not in proj_blob
    assert "/Users/private/" not in proj_blob


def test_delegate_repository_filter_before_pagination_starvation():
    """Foreign volume above the public task cap must not hide older public tasks.

    Repository filtering (and the filtered total) happens in the delegate
    loader before limit/total, so private/unclassified rows never consume
    DELEGATE_TASK_LIMIT and cannot starve older public rows out of the page.
    """
    from scripts.work.sources_public import DELEGATE_TASK_LIMIT, fetch_delegate_active, fetch_delegate_tasks

    private_repo = "other-org/other-private-repo"
    public_count = 7
    foreign_count = DELEGATE_TASK_LIMIT + 50
    assert foreign_count > DELEGATE_TASK_LIMIT

    # Newer foreign/unclassified first (higher started_at rank would win if
    # pagination ran before repository filter).
    foreign_newer = [
        {
            "task_id": f"private-new-{i:04d}",
            "agent": "codex",
            "status": "done",
            "started_at": f"2026-08-16T12:{i % 60:02d}:00Z",
            "repository": private_repo,
            "cwd": f"/Users/private/{private_repo}",
            "worktree_path": f"/Users/private/.worktrees/dispatch/codex/private-{i}",
        }
        for i in range(foreign_count)
    ]
    unclassified_newer = [
        {
            "task_id": f"unclassified-new-{i:04d}",
            "agent": "codex",
            "status": "done",
            "started_at": f"2026-08-16T11:{i % 60:02d}:00Z",
            "cwd": f"/Users/private/projects/{REPO}",
            "worktree_path": f"/Users/private/.worktrees/dispatch/codex/issue-{i}",
            "worktree_branch": f"codex/issue-{i}",
        }
        for i in range(30)
    ]
    public_older = [
        {
            "task_id": f"public-old-{i:04d}",
            "agent": "claude",
            "status": "done",
            "started_at": f"2026-08-01T0{i}:00:00Z",
            "repository": REPO,
        }
        for i in range(public_count)
    ]
    public_active = [
        {
            "task_id": "public-running",
            "agent": "codex",
            "status": "running",
            "started_at": "2026-08-01T00:00:00Z",
            "repository": REPO,
            "alive": True,
        },
        {
            "task_id": "public-spawning",
            "agent": "kimi",
            "status": "spawning",
            "started_at": "2026-08-01T00:01:00Z",
            "repository_id": REPO,
            "alive": False,
        },
    ]
    universe = [*foreign_newer, *unclassified_newer, *public_older, *public_active]
    seen_repos: list[str] = []

    def _scope(repository: str, *, active_only: bool) -> list[dict]:
        assert repository == REPO
        # Exact pre-pagination filter — private volume never enters the page.
        scoped = []
        for row in universe:
            if active_only and row.get("status") not in {"running", "spawning"}:
                continue
            claims = []
            for key in ("repository", "repository_id"):
                raw = row.get(key)
                if raw is None or raw == "":
                    continue
                text = str(raw).strip()
                if text:
                    claims.append(text)
            if not claims:
                continue
            if len(set(claims)) != 1:
                continue
            if claims[0] != repository:
                continue
            scoped.append(row)
        return scoped

    def active_loader(repository: str) -> dict:
        seen_repos.append(repository)
        scoped = _scope(repository, active_only=True)
        return {"total": len(scoped), "tasks": scoped}

    def tasks_loader(repository: str) -> dict:
        seen_repos.append(repository)
        scoped = _scope(repository, active_only=False)
        # Apply the same limit the production list path uses after filter.
        page = scoped[:DELEGATE_TASK_LIMIT]
        return {"total": len(scoped), "tasks": page}

    active = fetch_delegate_active(loader=active_loader, repository_id=REPO)
    tasks = fetch_delegate_tasks(loader=tasks_loader, repository_id=REPO)

    assert seen_repos == [REPO, REPO]
    assert active.status == "ok"
    assert active.truncated is False
    assert active.count == 2
    assert active.payload["total"] == 2
    assert {t["task_id"] for t in active.payload["tasks"]} == {
        "public-running",
        "public-spawning",
    }
    assert all(t["repository"] == REPO for t in active.payload["tasks"])

    assert tasks.status == "ok"
    assert tasks.truncated is False
    # Full public set is inside the page; foreign volume did not force truncation.
    assert tasks.payload["total"] == public_count + 2
    assert tasks.count == public_count + 2
    public_ids = {t["task_id"] for t in tasks.payload["tasks"]}
    assert public_ids == {
        *(f"public-old-{i:04d}" for i in range(public_count)),
        "public-running",
        "public-spawning",
    }
    assert all(t["repository"] == REPO for t in tasks.payload["tasks"])
    blob = json.dumps({"active": active.payload, "tasks": tasks.payload})
    assert private_repo not in blob
    assert "private-new-" not in blob
    assert "unclassified-new-" not in blob
    assert "/Users/private/" not in blob


def test_delegate_production_loader_scopes_before_page(tmp_path, monkeypatch):
    """End-to-end: production list/active loaders filter by public repo before limit."""
    import scripts.api.delegate_router as delegate_router
    from scripts.work.sources_public import (
        DELEGATE_TASK_LIMIT,
        fetch_delegate_active,
        fetch_delegate_tasks,
    )

    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    monkeypatch.setattr(delegate_router, "TASKS_DIR", tasks_dir)
    monkeypatch.setattr(delegate_router.os, "kill", lambda pid, sig: None)
    private_repo = "other-org/other-private-repo"
    now = datetime.now(UTC)

    def _write(task_id: str, **overrides):
        payload = {
            "task_id": task_id,
            "agent": "codex",
            "model": "gpt-5.5",
            "status": "done",
            "pid": 1,
            "started_at": now.isoformat().replace("+00:00", "Z"),
            "duration_s": 1.0,
        }
        payload.update(overrides)
        (tasks_dir / f"{task_id}.json").write_text(
            json.dumps(payload), encoding="utf-8"
        )

    for i in range(DELEGATE_TASK_LIMIT + 40):
        _write(
            f"foreign-{i:04d}",
            started_at=(now - timedelta(seconds=i)).isoformat().replace("+00:00", "Z"),
            repository=private_repo,
            cwd=f"/Users/private/{private_repo}",
        )
    for i in range(5):
        _write(
            f"public-old-{i:04d}",
            started_at=(now - timedelta(days=2, minutes=i))
            .isoformat()
            .replace("+00:00", "Z"),
            repository=REPO,
        )
    _write(
        "public-running",
        status="running",
        pid=111,
        started_at=(now - timedelta(days=3)).isoformat().replace("+00:00", "Z"),
        repository=REPO,
        duration_s=None,
    )
    _write(
        "public-spawning",
        status="spawning",
        pid=None,
        started_at=(now - timedelta(days=3, minutes=1))
        .isoformat()
        .replace("+00:00", "Z"),
        repository_id=REPO,
        duration_s=None,
    )

    # Production path: no injectable loader — uses scoped active/list helpers.
    active = fetch_delegate_active(repository_id=REPO)
    tasks = fetch_delegate_tasks(repository_id=REPO)

    assert active.status == "ok"
    assert active.payload["total"] == 2
    assert {t["task_id"] for t in active.payload["tasks"]} == {
        "public-running",
        "public-spawning",
    }
    assert tasks.status == "ok"
    assert tasks.truncated is False
    assert tasks.payload["total"] == 7
    assert {t["task_id"] for t in tasks.payload["tasks"]} == {
        *(f"public-old-{i:04d}" for i in range(5)),
        "public-running",
        "public-spawning",
    }
    blob = json.dumps({"active": active.payload, "tasks": tasks.payload})
    assert private_repo not in blob
    assert "/Users/private/" not in blob
    assert "foreign-" not in blob


def test_fleet_reviews_repository_filter_before_hard_cap():
    """Foreign volume above the public scan cap must not hide public reviews.

    Repository filtering (and the filtered total) happens in the loader before
    pagination/counting, so private rows never consume FLEET_REVIEW_HARD_CAP
    and cannot force truncation relative to the public filtered total.
    """
    from scripts.work.sources_public import FLEET_REVIEW_HARD_CAP, FLEET_REVIEW_PAGE

    private_repo = "other-org/other-private-repo"
    public_count = 7
    foreign_count = FLEET_REVIEW_HARD_CAP + 50
    assert foreign_count > FLEET_REVIEW_HARD_CAP

    public_rows = [
        {
            "review_id": f"rev-public-{i:04d}",
            "repository": REPO,
            "pr_number": 1000 + i,
            "state": "running",
            "sealed_verdict_available": False,
            "created_at": f"2026-08-01T00:{i:02d}:00Z",
        }
        for i in range(public_count)
    ]
    foreign_rows = [
        {
            "review_id": f"rev-foreign-{i:04d}",
            "repository": private_repo,
            "pr_number": 9000 + i,
            "state": "running",
            "sealed_verdict_available": True,
            "created_at": f"2026-07-01T00:00:{i % 60:02d}Z",
        }
        for i in range(foreign_count)
    ]
    # Foreign rows first would exhaust an unfiltered 2000-row scan.
    universe = [*foreign_rows, *public_rows]
    seen_repos: list[str] = []
    seen_offsets: list[int] = []

    def loader(limit: int, offset: int, repository: str) -> dict:
        seen_repos.append(repository)
        seen_offsets.append(offset)
        assert repository == REPO
        # Exact pre-pagination filter — private volume never enters the page.
        scoped = [r for r in universe if r["repository"] == repository]
        page = scoped[offset : offset + limit]
        return {
            "total": len(scoped),
            "reviews": page,
            "limit": limit,
            "offset": offset,
            "filters": {"repository": repository},
        }

    section = fetch_fleet_reviews(loader=loader, repository_id=REPO)
    assert seen_repos and all(r == REPO for r in seen_repos)
    assert section.status == "ok"
    assert section.truncated is False
    assert section.count == public_count
    assert section.payload["total"] == public_count
    assert len(section.payload["reviews"]) == public_count
    assert {r["review_id"] for r in section.payload["reviews"]} == {
        f"rev-public-{i:04d}" for i in range(public_count)
    }
    assert all(r["repository"] == REPO for r in section.payload["reviews"])
    # Loader was not forced through the full foreign-dominated universe.
    assert max(seen_offsets) < FLEET_REVIEW_HARD_CAP
    assert max(seen_offsets) <= public_count
    assert private_repo not in json.dumps(section.payload)
    # Page size stays the public collector constant.
    assert FLEET_REVIEW_PAGE == 100


def test_relations_and_cycle_detection():
    body = "This blocks #2 and is blocked by #3. Duplicate of #4. Superseded-by: #5"
    rels = extract_body_relations(body, repository_id=REPO, self_number=1)
    types = {r["type"] for r in rels}
    assert "blocks" in types
    assert "blocked_by" in types
    assert "duplicate_of" in types
    assert "superseded_by" in types

    items = [
        {
            "work_id": issue_work_id(REPO, 1),
            "relationships": [
                {"type": "blocks", "target_id": issue_work_id(REPO, 2), "evidence": "t"}
            ],
        },
        {
            "work_id": issue_work_id(REPO, 2),
            "relationships": [
                {"type": "blocks", "target_id": issue_work_id(REPO, 1), "evidence": "t"}
            ],
        },
    ]
    cycles = detect_dependency_cycles(items)
    assert cycles
    assert issue_work_id(REPO, 1) in cycles[0]


def test_match_dispatch_requires_boundary_safe_issue_and_pr_ids():
    """Substring prefixes must not attach unrelated dispatch state.

    Regression: unanchored ``#1`` matched ``#19``; ``pr-10`` matched ``pr-100``.
    """
    tasks = [
        {"task_id": "codex-#19-fix", "status": "running", "agent": "codex", "repository": REPO},
        {"task_id": "codex-issue-19", "status": "running", "agent": "codex", "repository": REPO},
        {"task_id": "codex-issue_19", "status": "running", "agent": "codex", "repository": REPO},
        {"task_id": "codex/19/work", "status": "running", "agent": "codex", "repository": REPO},
        {"task_id": "worker-19", "status": "running", "agent": "codex", "repository": REPO},
        {"task_id": "codex-#1-fix", "status": "running", "agent": "claude", "repository": REPO},
        {"task_id": "codex-issue-1", "status": "running", "agent": "claude", "repository": REPO},
        {"task_id": "codex-issue_1", "status": "running", "agent": "claude", "repository": REPO},
        {"task_id": "codex/1/work", "status": "running", "agent": "claude", "repository": REPO},
        {"task_id": "worker-1", "status": "running", "agent": "claude", "repository": REPO},
        {"task_id": "agy-pr-100", "status": "running", "agent": "agy", "repository": REPO},
        {"task_id": "agy-pr_100", "status": "running", "agent": "agy", "repository": REPO},
        {"task_id": "agy-pr/100", "status": "running", "agent": "agy", "repository": REPO},
        {"task_id": "review-pr100", "status": "running", "agent": "agy", "repository": REPO},
        {"task_id": "agy-pr-10", "status": "running", "agent": "kimi", "repository": REPO},
        {"task_id": "agy-pr_10", "status": "running", "agent": "kimi", "repository": REPO},
        {"task_id": "agy-pr/10", "status": "running", "agent": "kimi", "repository": REPO},
        {"task_id": "review-pr10", "status": "running", "agent": "kimi", "repository": REPO},
        # Unrelated numeric text must not become authority for a match.
        {"task_id": "retrycount1of19", "status": "running", "agent": "cursor", "repository": REPO},
        {"task_id": "shard10of100", "status": "running", "agent": "cursor", "repository": REPO},
        {"task_id": "build100timeout", "status": "running", "agent": "cursor", "repository": REPO},
        {"task_id": "page1", "status": "running", "agent": "cursor", "repository": REPO},
        {"task_id": "v10-release", "status": "running", "agent": "cursor", "repository": REPO},
    ]

    issue_1 = _match_dispatch(tasks, issue_number=1, pr_number=None)
    assert set(issue_1["task_ids"]) == {
        "codex-#1-fix",
        "codex-issue-1",
        "codex-issue_1",
        "codex/1/work",
        "worker-1",
    }
    assert "codex-#19-fix" not in issue_1["task_ids"]
    assert "codex-issue-19" not in issue_1["task_ids"]
    assert "retrycount1of19" not in issue_1["task_ids"]
    assert "page1" not in issue_1["task_ids"]

    issue_19 = _match_dispatch(tasks, issue_number=19, pr_number=None)
    assert set(issue_19["task_ids"]) == {
        "codex-#19-fix",
        "codex-issue-19",
        "codex-issue_19",
        "codex/19/work",
        "worker-19",
    }
    assert "codex-#1-fix" not in issue_19["task_ids"]
    assert "codex-issue-1" not in issue_19["task_ids"]
    assert "retrycount1of19" not in issue_19["task_ids"]

    pr_10 = _match_dispatch(tasks, issue_number=None, pr_number=10)
    assert set(pr_10["task_ids"]) == {
        "agy-pr-10",
        "agy-pr_10",
        "agy-pr/10",
        "review-pr10",
    }
    assert "agy-pr-100" not in pr_10["task_ids"]
    assert "review-pr100" not in pr_10["task_ids"]
    assert "shard10of100" not in pr_10["task_ids"]
    assert "v10-release" not in pr_10["task_ids"]

    pr_100 = _match_dispatch(tasks, issue_number=None, pr_number=100)
    assert set(pr_100["task_ids"]) == {
        "agy-pr-100",
        "agy-pr_100",
        "agy-pr/100",
        "review-pr100",
    }
    assert "agy-pr-10" not in pr_100["task_ids"]
    assert "review-pr10" not in pr_100["task_ids"]
    assert "build100timeout" not in pr_100["task_ids"]
    assert "shard10of100" not in pr_100["task_ids"]


def test_health_never_uses_activity_and_pr_rules():
    pr_fail = {
        "resource_kind": "pr",
        "lifecycle": "open",
        "flags": {},
        "projections": {
            "stream": {},
            "dispatch": {},
            "review": {"review_decision": "APPROVED"},
            "verification": {"ci_state": "failing"},
        },
    }
    assert derive_health(pr_fail, source_ok=True) == "OFF_TRACK"
    assert derive_safe_next_action(pr_fail)["code"] == "FIX_CI"

    orphan = {
        "resource_kind": "issue",
        "flags": {},
        "projections": {
            "stream": {"status": "orphan", "fresh": True},
            "dispatch": {"statuses": []},
            "review": {},
            "verification": {},
        },
    }
    assert derive_health(orphan, source_ok=True) == "AT_RISK"
    assert derive_safe_next_action(orphan)["code"] == "TRIAGE_ORPHAN"

    assert derive_health(orphan, source_ok=False) == "UNKNOWN"


def test_build_projection_joins_sources_deterministically():
    sections = {
        "issues": SectionResult(
            "issues",
            "ok",
            payload=[
                {
                    "number": 10,
                    "title": "Orphan issue",
                    "labels": [{"name": "agent"}],
                    "assignees": [],
                    "body": "blocked by #11",
                    "createdAt": "2026-08-01T00:00:00Z",
                    "updatedAt": "2026-08-02T00:00:00Z",
                    "url": "https://example.test/issues/10",
                    "state": "OPEN",
                },
                {
                    "number": 11,
                    "title": "Blocker",
                    "labels": [],
                    "assignees": [],
                    "body": "blocks #10",
                    "createdAt": "2026-08-01T00:00:00Z",
                    "updatedAt": "2026-08-02T00:00:00Z",
                    "url": "https://example.test/issues/11",
                    "state": "OPEN",
                },
            ],
            count=2,
        ),
        "prs": SectionResult(
            "prs",
            "ok",
            payload=[
                {
                    "number": 99,
                    "title": "Draft PR",
                    "state": "OPEN",
                    "isDraft": True,
                    "reviewDecision": "",
                    "statusCheckRollup": [{"state": "PENDING"}],
                    "mergeStateStatus": "BLOCKED",
                    "labels": [],
                    "assignees": [],
                    "url": "https://example.test/pull/99",
                    "createdAt": "2026-08-01T00:00:00Z",
                    "updatedAt": "2026-08-02T00:00:00Z",
                    "headRefOid": "abc",
                    "headRefName": "feat/x",
                }
            ],
            count=1,
        ),
        "streams": SectionResult(
            "streams",
            "ok",
            payload={
                "generated_at": 1,
                "open_total": 2,
                "orphans": [{"number": 10, "title": "Orphan issue"}],
                "multi_homed": [],
                "pending_native_link": [],
                "ok": False,
            },
            count=2,
        ),
        "delegate_active": SectionResult(
            "delegate_active",
            "ok",
            payload={"total": 0, "tasks": []},
            count=0,
        ),
        "delegate_tasks": SectionResult(
            "delegate_tasks",
            "ok",
            payload={
                "total": 1,
                "tasks": [
                    {
                        "task_id": "unlinked-task-1",
                        "agent": "codex",
                        "status": "running",
                        "started_at": "2026-08-16T00:00:00Z",
                        "repository": REPO,
                    }
                ],
            },
            count=1,
        ),
        "fleet_reviews": SectionResult(
            "fleet_reviews",
            "ok",
            payload={
                "total": 1,
                "reviews": [
                    {
                        "review_id": "rev-1",
                        "repository": REPO,
                        "pr_number": 99,
                        "head_sha": "abc",
                        "gate_kind": "code",
                        "state": "running",
                        "sealed_verdict_available": False,
                    }
                ],
            },
            count=1,
        ),
    }
    projection = build_projection(sections, repository_id=REPO)
    validate_projection(projection)
    assert projection["foundation_status"] == "FOUNDATION_COMPLETE"
    assert projection["capabilities"]["mutation"] is False
    assert projection["capabilities"]["private_source"]["available"] is False
    assert projection["denominator"]["issues_open"] == 2
    assert projection["denominator"]["prs_open"] == 1
    assert projection["denominator"]["class4"]["delegate_tasks"] is True

    ids = {item["work_id"] for item in projection["items"]}
    assert issue_work_id(REPO, 10) in ids
    assert any(i["resource_kind"] == "pr" for i in projection["items"])
    assert any(i["resource_kind"] == "task" for i in projection["items"])

    # Body text must not leak into the projection payload.
    blob = json.dumps(projection)
    assert "blocked by #11" not in blob
    assert "blocks #10" not in blob

    ranks = [a["attention_rank"] for a in projection["attention"]]
    assert ranks == sorted(ranks)
    # Deterministic: same inputs → same first attention id
    again = build_projection(sections, repository_id=REPO)
    assert again["attention"][0]["work_id"] == projection["attention"][0]["work_id"]
