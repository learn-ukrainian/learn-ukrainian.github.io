"""Contract, correctness, economy, and security tests for preparation state."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient
from jsonschema import Draft202012Validator

from scripts.api import preparation_state, state_router
from scripts.api.main import app
from scripts.api.repository_authority import build_repository_authority, preparation_data_root
from scripts.orchestration import curriculum_readiness

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / "schemas/agent-preparation-state.v1.schema.json").read_text(encoding="utf-8"))
VALIDATOR = Draft202012Validator(SCHEMA)
CLIENT = TestClient(app, raise_server_exceptions=False)
AUTHORITY = {
    "repository": "learn-ukrainian/learn-ukrainian.github.io",
    "data_checkout": {
        "role": "live_primary",
        "root": "/fixed/repository",
        "branch": "main",
        "head_sha": "a" * 40,
    },
    "service_code": {
        "mode": "release",
        "commit_sha": "b" * 40,
        "tree_sha256": "c" * 64,
    },
}


def _git_env() -> dict[str, str]:
    return {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
        env=_git_env(),
    )
    return result.stdout.strip()


def _repo(path: Path, *, remote: str) -> Path:
    path.mkdir(parents=True)
    subprocess.run(
        ["git", "init", "-q", "-b", "main", str(path)],
        check=True,
        capture_output=True,
        text=True,
        env=_git_env(),
    )
    _git(path, "config", "user.email", "test@example.com")
    _git(path, "config", "user.name", "Test")
    _git(path, "remote", "add", "origin", remote)
    (path / "tracked.txt").write_text(path.name, encoding="utf-8")
    _git(path, "add", "tracked.txt")
    _git(path, "commit", "-q", "-m", "init")
    return path


def _write_manifest(repo_root: Path, *, track: str = "a1", slug: str = "demo") -> None:
    path = repo_root / curriculum_readiness.MANIFEST_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"version: '1.0'\nlevels:\n  {track}:\n    type: core\n    modules:\n      - {slug}\n",
        encoding="utf-8",
    )


def _canonical(repo_root: Path, track: str, slug: str) -> dict[str, Any]:
    manifest_path = repo_root / curriculum_readiness.MANIFEST_PATH
    manifest_sha = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    module_state = curriculum_readiness.module_bundle_state(repo_root, track, slug)
    if module_state == "partial":
        state, next_action, preparation_state = "partial-bundle", "stop", "missing"
        findings = [
            {
                "id": "PARTIAL_LEARNER_BUNDLE",
                "category": "built_artifact",
                "severity": "blocker",
                "summary": "partial",
                "owner": "built_artifact",
            }
        ]
    else:
        state, next_action, preparation_state = "preparation-required", "prepare", "missing"
        findings = [
            {
                "id": "PREPARATION_PLAN",
                "category": "preparation",
                "severity": "high",
                "summary": "missing",
                "owner": "plan",
            }
        ]
    return {
        "contract_version": "curriculum-preparation-result.v1",
        "track": track,
        "slug": slug,
        "profile_id": "core",
        "profile_version": "1",
        "family": "core",
        "manifest": {
            "path": curriculum_readiness.MANIFEST_PATH.as_posix(),
            "sha256": manifest_sha,
            "index": 0,
        },
        "module_state": module_state,
        "preparation_state": preparation_state,
        "state": state,
        "next_action": next_action,
        "requirements": [],
        "findings": findings,
        "sources": [
            {
                "kind": "manifest",
                "path": curriculum_readiness.MANIFEST_PATH.as_posix(),
                "sha256": manifest_sha,
            }
        ],
        "preparation_identity": "d" * 64,
        "consumed_preparation_identity": None,
    }


def _all_keys(value: Any) -> set[str]:
    if isinstance(value, dict):
        return set(value) | set().union(*(_all_keys(item) for item in value.values()), set())
    if isinstance(value, list):
        return set().union(*(_all_keys(item) for item in value), set())
    return set()


def test_roster_uses_only_active_manifest_and_matches_required_fixture_counts() -> None:
    Draft202012Validator.check_schema(SCHEMA)
    response = CLIENT.get("/api/state/preparation")

    assert response.status_code == 200
    data = response.json()
    VALIDATOR.validate(data)
    assert data["totals"]["manifest_active_tracks"] == 20
    assert data["totals"]["manifest_active_modules"] == 1932
    tracks = {item["track"]: item for item in data["tracks"]}
    assert set(tracks).isdisjoint({"lit-doc", "lit-crimea"})
    assert tracks["a1"]["module_state_counts"] == {"unbuilt": 0, "partial": 0, "built": 55}
    assert tracks["a1"]["publication_state_counts"]["published"] == 55
    assert tracks["a2"]["publication_state_counts"]["published"] == 69
    assert tracks["b1"]["publication_state_counts"]["published"] == 94
    assert tracks["b2"]["publication_state_counts"]["published"] == 93
    assert tracks["folk"]["publication_state_counts"]["published"] == 40
    assert tracks["c1"]["publication_state_counts"]["published"] == 0
    assert tracks["c1"]["publication_state_counts"]["absent"] == 133
    assert tracks["hist"]["publication_state_counts"]["published"] == 0
    assert tracks["hist"]["publication_state_counts"]["absent"] == 140
    diagnostics = {item["track"]: item for item in data["diagnostics"]["inactive_plan_tracks"]}
    assert diagnostics["lit-doc"]["module_count"] == 13
    assert diagnostics["lit-crimea"]["module_count"] == 12
    assert all(item["manifest_authority"] == "fallback-diagnostic-only" for item in diagnostics.values())


def test_one_track_roster_meets_budget_and_keeps_distinct_telemetry_semantics() -> None:
    response = CLIENT.get("/api/state/preparation?track=a1")

    assert response.status_code == 200
    assert len(response.content) < 5_000
    data = response.json()
    VALIDATOR.validate(data)
    assert data["totals"]["returned_tracks"] == 1
    assert data["totals"]["returned_modules"] == 55
    legacy = CLIENT.get("/api/state/summary").json()["tracks"]["a1"]
    assert legacy["content_done"] == 0
    assert legacy["published_mdx"] == 55
    assert data["tracks"][0]["module_state_counts"]["built"] == 55


def test_module_projection_is_compact_canonical_and_has_no_ready_boolean() -> None:
    response = CLIENT.get("/api/state/preparation/a1/sounds-letters-and-hello")

    assert response.status_code == 200
    assert len(response.content) < 3_000
    data = response.json()
    VALIDATOR.validate(data)
    assert data["module_state"] == "built"
    assert data["publication"] == {
        "state": "published",
        "surface": "mdx",
        "source": data["publication"]["source"],
    }
    assert data["preparation_state"] == "stale"
    assert data["next_action"] == "prepare"
    assert data["authority"]["readiness"]["profile_id"] == "core"
    assert data["field_authority"]["orchestration_telemetry"] == "not-included"
    assert "ready" not in _all_keys(data)
    assert response.headers["etag"].startswith('"')
    assert response.headers["x-source-identity"] == data["freshness"]["source_identity"]

    expanded = CLIENT.get(
        "/api/state/preparation/a1/sounds-letters-and-hello?evidence=expanded"
    )
    assert expanded.status_code == 200
    VALIDATOR.validate(expanded.json())
    assert expanded.json()["canonical"]["contract_version"] == "curriculum-preparation-result.v1"


def test_bio_uses_bio_profile_and_dossier_alone_never_means_build(monkeypatch) -> None:
    # This test isolates the dossier-only preparation state. Source-controlled
    # holds are an independent terminal override covered by the readiness tests.
    monkeypatch.setattr(curriculum_readiness, "_active_preparation_hold", lambda _context: None)
    response = CLIENT.get("/api/state/preparation/bio/knyahynia-olha")

    assert response.status_code == 200
    data = response.json()
    VALIDATOR.validate(data)
    assert data["authority"]["readiness"]["profile_id"] == "bio"
    assert data["module_state"] == "unbuilt"
    assert data["preparation_state"] == "missing"
    assert data["next_action"] == "prepare"
    assert data["next_action"] != "build"
    assert data["reason_codes"]


def test_one_module_parses_the_active_manifest_once(monkeypatch) -> None:
    original = curriculum_readiness.load_active_manifest
    calls = 0

    def counted(*args, **kwargs):
        nonlocal calls
        calls += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(curriculum_readiness, "load_active_manifest", counted)

    data = preparation_state.build_module_state(
        repo_root=ROOT,
        authority=AUTHORITY,
        track="bio",
        slug="knyahynia-olha",
        expanded=False,
    )

    assert data["authority"]["readiness"]["profile_id"] == "bio"
    assert calls == 1


def test_strong_etag_returns_bodyless_304_for_unchanged_sources() -> None:
    first = CLIENT.get("/api/state/preparation?track=a1")
    second = CLIENT.get(
        "/api/state/preparation?track=a1",
        headers={"If-None-Match": first.headers["etag"]},
    )

    assert first.status_code == 200
    assert second.status_code == 304
    assert second.content == b""
    assert second.headers["etag"] == first.headers["etag"]


def test_recompute_identity_changes_on_bundle_and_publication_sources(tmp_path: Path, monkeypatch) -> None:
    repo_root = tmp_path / "repo"
    _write_manifest(repo_root)
    monkeypatch.setattr(
        preparation_state.curriculum_readiness,
        "evaluate_preparation",
        lambda track, slug, **_kwargs: _canonical(repo_root, track, slug),
    )

    before = preparation_state.build_module_state(
        repo_root=repo_root,
        authority=AUTHORITY,
        track="a1",
        slug="demo",
        expanded=True,
    )
    module_dir = repo_root / "curriculum/l2-uk-en/a1/demo"
    module_dir.mkdir(parents=True)
    (module_dir / "module.md").write_text("# partial\n", encoding="utf-8")
    partial = preparation_state.build_module_state(
        repo_root=repo_root,
        authority=AUTHORITY,
        track="a1",
        slug="demo",
        expanded=True,
    )
    assert partial["module_state"] == "partial"
    assert partial["next_action"] == "stop"
    assert partial["freshness"]["source_identity"] != before["freshness"]["source_identity"]

    for filename in curriculum_readiness.MODULE_BUNDLE_FILES[1:]:
        (module_dir / filename).write_text(filename, encoding="utf-8")
    mdx = repo_root / "site/src/content/docs/a1/demo.mdx"
    mdx.parent.mkdir(parents=True)
    mdx.write_text("published", encoding="utf-8")
    after = preparation_state.build_module_state(
        repo_root=repo_root,
        authority=AUTHORITY,
        track="a1",
        slug="demo",
        expanded=True,
    )
    assert after["module_state"] == "built"
    assert after["publication"]["state"] == "published"
    assert after["freshness"]["source_identity"] != partial["freshness"]["source_identity"]
    assert preparation_state.response_document(after)[1] != preparation_state.response_document(partial)[1]


def test_etag_changes_when_canonical_manifest_or_profile_sources_change(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo_root = tmp_path / "repo"
    _write_manifest(repo_root)
    profile_sha = ["1" * 64]

    def canonical(track: str, slug: str, **_kwargs) -> dict[str, Any]:
        result = _canonical(repo_root, track, slug)
        result["sources"].append(
            {
                "kind": "readiness-config",
                "path": "agents_extensions/shared/curriculum-lifecycle/config/readiness-profiles.v1.yaml",
                "sha256": profile_sha[0],
            }
        )
        return result

    monkeypatch.setattr(
        preparation_state.curriculum_readiness,
        "evaluate_preparation",
        canonical,
    )
    before = preparation_state.build_module_state(
        repo_root=repo_root,
        authority=AUTHORITY,
        track="a1",
        slug="demo",
        expanded=False,
    )

    profile_sha[0] = "2" * 64
    profile_changed = preparation_state.build_module_state(
        repo_root=repo_root,
        authority=AUTHORITY,
        track="a1",
        slug="demo",
        expanded=False,
    )
    assert preparation_state.response_document(profile_changed)[1] != preparation_state.response_document(before)[1]

    manifest_path = repo_root / curriculum_readiness.MANIFEST_PATH
    manifest_path.write_text(manifest_path.read_text(encoding="utf-8") + "# identity change\n", encoding="utf-8")
    manifest_changed = preparation_state.build_module_state(
        repo_root=repo_root,
        authority=AUTHORITY,
        track="a1",
        slug="demo",
        expanded=False,
    )
    assert preparation_state.response_document(manifest_changed)[1] != preparation_state.response_document(
        profile_changed
    )[1]


def test_count_disagreement_emits_finding(tmp_path: Path, monkeypatch) -> None:
    repo_root = tmp_path / "repo"
    _write_manifest(repo_root)
    monkeypatch.setattr(preparation_state.curriculum_readiness, "module_bundle_state", lambda *_args: "invalid")

    data = preparation_state.build_roster(repo_root=repo_root, authority=AUTHORITY)

    assert {item["id"] for item in data["findings"]} == {
        "BUNDLE_STATE_COUNT_MISMATCH",
        "TRACK_COUNT_INVARIANT_FAILED",
    }


def test_off_manifest_inactive_unknown_and_unsafe_selectors_fail_closed() -> None:
    off_manifest = CLIENT.get("/api/state/preparation/a1/not-in-curriculum")
    assert off_manifest.status_code == 404
    assert off_manifest.json()["manifest_authority"] == "off-manifest"
    assert off_manifest.json()["next_action"] == "stop"

    assert CLIENT.get("/api/state/preparation?track=lit-doc").status_code == 422
    assert CLIENT.get("/api/state/preparation?track=not-a-track").status_code == 404
    assert CLIENT.get("/api/state/preparation?track=../a1").status_code == 422
    assert CLIENT.get("/api/state/preparation?slug=demo").status_code == 422
    assert CLIENT.get("/api/state/preparation?track=a1&track=a2").status_code == 422
    assert CLIENT.get("/api/state/preparation/a1/sounds-letters-and-hello?evidence=unknown").status_code == 422
    assert CLIENT.get("/api/state/preparation/a1/sounds-letters-and-hello?field=state").status_code == 422


def test_readiness_contract_error_is_a_fail_closed_503(monkeypatch) -> None:
    def invalid_profile(*_args, **_kwargs):
        raise curriculum_readiness.ReadinessError("invalid readiness profile")

    monkeypatch.setattr(preparation_state.curriculum_readiness, "evaluate_preparation", invalid_profile)
    response = CLIENT.get("/api/state/preparation/a1/sounds-letters-and-hello")

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "PREPARATION_AUTHORITY_UNAVAILABLE"


def test_ready_to_build_is_additively_deprecated_and_session_start_migrated() -> None:
    response = CLIENT.get("/api/state/ready-to-build?track=not-a-track")

    assert response.status_code == 200
    assert response.json() == {
        "count": 0,
        "modules": [],
        "authority": "informational-only",
        "semantics": "research-complete-candidates-not-generation-readiness",
        "deprecated": True,
        "replacement": "/api/state/preparation",
    }
    operation = CLIENT.get("/openapi.json").json()["paths"]["/api/state/ready-to-build"]["get"]
    assert operation["deprecated"] is True
    script = (ROOT / "scripts/session_start.sh").read_text(encoding="utf-8")
    assert "/api/state/ready-to-build" not in script
    assert "/api/state/preparation" in script


def test_repository_authority_distinguishes_data_checkout_from_development_code(tmp_path: Path) -> None:
    data = _repo(
        tmp_path / "data",
        remote="https://secret-token@github.com/learn-ukrainian/learn-ukrainian.github.io.git",
    )
    code = _repo(
        tmp_path / "code",
        remote="https://github.com/learn-ukrainian/learn-ukrainian.github.io.git",
    )

    authority = build_repository_authority(project_root=code, live_repo_root=data)

    assert authority["repository"] == "learn-ukrainian/learn-ukrainian.github.io"
    assert "secret-token" not in json.dumps(authority)
    assert authority["data_checkout"] == {
        "role": "live_primary",
        "root": str(data),
        "branch": "main",
        "head_sha": _git(data, "rev-parse", "HEAD"),
    }
    assert authority["service_code"]["mode"] == "development"
    assert authority["service_code"]["commit_sha"] == _git(code, "rev-parse", "HEAD")


def test_repository_authority_reads_immutable_release_manifest(tmp_path: Path) -> None:
    data = _repo(
        tmp_path / "data",
        remote="git@github.com:learn-ukrainian/learn-ukrainian.github.io.git",
    )
    release_sha = "e" * 40
    release = tmp_path / ".runtime/api/releases" / release_sha
    release.mkdir(parents=True)
    (release / ".release-manifest.json").write_text(
        json.dumps({"sha": release_sha, "file_count": 1, "tree_sha256": "f" * 64}),
        encoding="utf-8",
    )

    authority = build_repository_authority(project_root=release, live_repo_root=data)

    assert authority["service_code"] == {
        "mode": "release",
        "commit_sha": release_sha,
        "tree_sha256": "f" * 64,
    }


def test_release_route_reads_from_the_reported_live_data_checkout(
    tmp_path: Path,
    monkeypatch,
) -> None:
    release_sha = "e" * 40
    release = tmp_path / ".runtime/api/releases" / release_sha
    release.mkdir(parents=True)
    (release / ".release-manifest.json").write_text(
        json.dumps({"sha": release_sha, "file_count": 1, "tree_sha256": "f" * 64}),
        encoding="utf-8",
    )
    monkeypatch.setattr(state_router, "PROJECT_ROOT", release)
    monkeypatch.setattr(state_router, "LIVE_REPO_ROOT", ROOT)

    response = CLIENT.get("/api/state/preparation?track=a1")

    assert response.status_code == 200
    data = response.json()
    VALIDATOR.validate(data)
    assert data["authority"]["data_checkout"]["root"] == str(ROOT)
    assert data["authority"]["service_code"] == {
        "mode": "release",
        "commit_sha": release_sha,
        "tree_sha256": "f" * 64,
    }
    assert data["tracks"][0]["module_state_counts"]["built"] == 55


def test_development_dispatch_worktree_is_reported_as_the_data_checkout(tmp_path: Path) -> None:
    primary = _repo(
        tmp_path / "primary",
        remote="https://github.com/learn-ukrainian/learn-ukrainian.github.io.git",
    )
    dispatch = tmp_path / ".worktrees/dispatch/codex/example"
    dispatch.parent.mkdir(parents=True)
    _git(primary, "worktree", "add", "-q", "-b", "codex/example", str(dispatch))

    data_root = preparation_data_root(project_root=dispatch, live_repo_root=primary)
    authority = build_repository_authority(project_root=dispatch, live_repo_root=data_root)

    assert data_root == dispatch
    assert authority["data_checkout"]["role"] == "dispatch_worktree"
    assert authority["data_checkout"]["root"] == str(dispatch)
