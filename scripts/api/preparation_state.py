"""Deterministic agent-facing projections of canonical curriculum preparation."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from scripts.orchestration import curriculum_readiness

CONTRACT_VERSION = "agent-preparation-state.v1"
BUNDLE_STATES = ("unbuilt", "partial", "built")
PUBLICATION_STATES = ("absent", "generated", "published")
PUBLICATION_SURFACES = {
    "absent": "none",
    "generated": "legacy_md",
    "published": "mdx",
}


class PreparationStateError(RuntimeError):
    """Raised when the preparation projection cannot establish authority."""


class UnknownTrackError(PreparationStateError):
    """Raised when a selector is neither active nor a plans diagnostic."""


class InactiveTrackError(PreparationStateError):
    """Raised when a plans-only track is selected as active authority."""


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _relative(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError as exc:
        raise PreparationStateError("preparation source escaped the configured repository") from exc


def _source(path: Path, repo_root: Path) -> dict[str, str | None]:
    return {
        "path": _relative(path, repo_root),
        "sha256": _sha256_bytes(path.read_bytes()) if path.is_file() else None,
    }


def _source_identity(sources: Sequence[Mapping[str, Any]]) -> str:
    return _sha256_bytes(_canonical_json(list(sources)).encode("utf-8"))


def _with_freshness(payload: dict[str, Any]) -> dict[str, Any]:
    result = dict(payload)
    result["freshness"] = {
        "mode": "recompute",
        "cache": "none",
        "stale": False,
        "source_identity": _sha256_bytes(_canonical_json(payload).encode("utf-8")),
    }
    return result


def response_document(payload: Mapping[str, Any]) -> tuple[bytes, str]:
    """Serialize stable response bytes and their strong content ETag digest."""
    body = _canonical_json(payload).encode("utf-8")
    return body, _sha256_bytes(body)


def _publication_paths(repo_root: Path, track: str, slug: str) -> tuple[Path, Path]:
    mdx_path = repo_root / "site" / "src" / "content" / "docs" / track / f"{slug}.mdx"
    legacy_path = repo_root / "curriculum" / "l2-uk-en" / track / f"{slug}.md"
    return mdx_path, legacy_path


def publication_state(repo_root: Path, track: str, slug: str) -> str:
    """Classify publication with existence checks only (the roster hot path)."""
    mdx_path, legacy_path = _publication_paths(repo_root, track, slug)
    if mdx_path.is_file():
        return "published"
    if legacy_path.is_file():
        return "generated"
    return "absent"


def publication_evidence(repo_root: Path, track: str, slug: str) -> dict[str, Any]:
    """Classify and hash fixed learner publication surfaces for one target."""
    mdx_path, legacy_path = _publication_paths(repo_root, track, slug)
    sources = [_source(mdx_path, repo_root), _source(legacy_path, repo_root)]
    state = publication_state(repo_root, track, slug)
    selected = sources[0] if state == "published" else sources[1] if state == "generated" else None
    return {
        "state": state,
        "surface": PUBLICATION_SURFACES[state],
        "source": selected,
        "sources": sources,
        "source_identity": _source_identity(sources),
    }


def bundle_evidence(repo_root: Path, track: str, slug: str) -> dict[str, Any]:
    directory = repo_root / "curriculum" / "l2-uk-en" / track / slug
    sources = [
        _source(directory / filename, repo_root)
        for filename in curriculum_readiness.MODULE_BUNDLE_FILES
    ]
    return {
        "state": curriculum_readiness.module_bundle_state(repo_root, track, slug),
        "sources": sources,
        "source_identity": _source_identity(sources),
    }


def _inactive_plan_tracks(repo_root: Path, active_tracks: set[str]) -> list[dict[str, Any]]:
    plans_root = repo_root / "curriculum" / "l2-uk-en" / "plans"
    diagnostics: list[dict[str, Any]] = []
    if not plans_root.is_dir():
        return diagnostics
    for path in sorted(plans_root.iterdir()):
        if not path.is_dir() or path.name in active_tracks:
            continue
        count = sum(candidate.is_file() for candidate in path.glob("*.yaml"))
        if count:
            diagnostics.append(
                {
                    "track": path.name,
                    "module_count": count,
                    "manifest_authority": "fallback-diagnostic-only",
                    "source": "plans-fallback",
                }
            )
    return diagnostics


def build_roster(
    *,
    repo_root: Path,
    authority: Mapping[str, Any],
    track: str | None = None,
) -> dict[str, Any]:
    """Build active-manifest bundle/publication counts without readiness sweeps."""
    try:
        manifest = curriculum_readiness.load_active_manifest(repo_root)
    except (curriculum_readiness.ReadinessError, OSError) as exc:
        raise PreparationStateError(str(exc)) from exc
    all_tracks = manifest["tracks"]
    if track is not None and track not in all_tracks:
        inactive = {item["track"] for item in _inactive_plan_tracks(repo_root, set(all_tracks))}
        if track in inactive:
            raise InactiveTrackError(f"inactive plans-fallback track: {track}")
        raise UnknownTrackError(f"unknown track: {track}")

    selected_tracks = [track] if track is not None else list(all_tracks)
    tracks: list[dict[str, Any]] = []
    findings: list[dict[str, str]] = []
    total_bundle = {state: 0 for state in BUNDLE_STATES}
    total_publication = {state: 0 for state in PUBLICATION_STATES}
    total_modules = 0

    for track_id in selected_tracks:
        record = all_tracks[track_id]
        modules = record["modules"]
        bundle_counts = {state: 0 for state in BUNDLE_STATES}
        publication_counts = {state: 0 for state in PUBLICATION_STATES}
        for slug in modules:
            bundle_state = curriculum_readiness.module_bundle_state(repo_root, track_id, slug)
            if bundle_state in bundle_counts:
                bundle_counts[bundle_state] += 1
            else:
                findings.append(
                    {
                        "id": "BUNDLE_STATE_COUNT_MISMATCH",
                        "track": track_id,
                        "detail": f"unexpected bundle state for {slug}: {bundle_state}",
                    }
                )
            published_state = publication_state(repo_root, track_id, slug)
            if published_state in publication_counts:
                publication_counts[published_state] += 1
            else:
                findings.append(
                    {
                        "id": "PUBLICATION_STATE_COUNT_MISMATCH",
                        "track": track_id,
                        "detail": f"unexpected publication state for {slug}: {published_state}",
                    }
                )

        module_count = len(modules)
        if sum(bundle_counts.values()) != module_count or sum(publication_counts.values()) != module_count:
            findings.append(
                {
                    "id": "TRACK_COUNT_INVARIANT_FAILED",
                    "track": track_id,
                    "detail": "component state counts do not equal the active manifest module count",
                }
            )
        tracks.append(
            {
                "track": track_id,
                "type": record["type"],
                "manifest_authority": "active",
                "module_count": module_count,
                "module_state_counts": bundle_counts,
                "publication_state_counts": publication_counts,
            }
        )
        total_modules += module_count
        for state in BUNDLE_STATES:
            total_bundle[state] += bundle_counts[state]
        for state in PUBLICATION_STATES:
            total_publication[state] += publication_counts[state]

    manifest_path = Path(manifest["path"])
    payload = {
        "contract_version": CONTRACT_VERSION,
        "kind": "roster",
        "authority_kind": "active-manifest-roster",
        "authority": {
            **dict(authority),
            "manifest": {
                "path": _relative(manifest_path, repo_root),
                "sha256": manifest["sha256"],
            },
        },
        "field_authority": {
            "tracks": "curriculum-manifest",
            "module_state_counts": "canonical-learner-bundle-files",
            "publication_state_counts": "learner-publication-files",
            "diagnostics": "informational-only",
        },
        "tracks": tracks,
        "totals": {
            "manifest_active_tracks": len(all_tracks),
            "manifest_active_modules": sum(len(record["modules"]) for record in all_tracks.values()),
            "returned_tracks": len(selected_tracks),
            "returned_modules": total_modules,
            "module_state_counts": total_bundle,
            "publication_state_counts": total_publication,
        },
        "diagnostics": {
            "authority": "diagnostic-only",
            "inactive_plan_tracks": _inactive_plan_tracks(repo_root, set(all_tracks)),
        },
        "findings": findings,
    }
    return _with_freshness(payload)


def build_module_state(
    *,
    repo_root: Path,
    authority: Mapping[str, Any],
    track: str,
    slug: str,
    expanded: bool,
) -> dict[str, Any]:
    """Project one canonical preparation result without changing its decisions."""
    try:
        manifest = curriculum_readiness.load_active_manifest(repo_root)
        if track not in manifest["tracks"]:
            inactive = {item["track"] for item in _inactive_plan_tracks(repo_root, set(manifest["tracks"]))}
            if track in inactive:
                raise InactiveTrackError(f"inactive plans-fallback track: {track}")
            raise UnknownTrackError(f"unknown track: {track}")
        canonical = curriculum_readiness.evaluate_preparation(
            track,
            slug,
            repo_root=repo_root,
            active_manifest=manifest,
        )
    except (InactiveTrackError, UnknownTrackError):
        raise
    except (curriculum_readiness.ReadinessError, OSError) as exc:
        raise PreparationStateError(str(exc)) from exc

    bundle = bundle_evidence(repo_root, track, slug)
    publication = publication_evidence(repo_root, track, slug)
    findings = canonical.get("findings") or []
    canonical_sources = canonical.get("sources") or []
    manifest = canonical["manifest"]
    payload: dict[str, Any] = {
        "contract_version": CONTRACT_VERSION,
        "kind": "module",
        "authority_kind": "canonical-preparation",
        "authority": {
            **dict(authority),
            "manifest": {
                "path": manifest["path"],
                "sha256": manifest["sha256"],
                "index": manifest["index"],
            },
            "readiness": {
                "profile_id": canonical["profile_id"],
                "profile_version": canonical["profile_version"],
                "family": canonical["family"],
            },
        },
        "field_authority": {
            "manifest_module_preparation_next_action": "curriculum-preparation-result.v1",
            "publication": "learner-publication-files",
            "orchestration_telemetry": "not-included",
        },
        "track": canonical["track"],
        "slug": canonical["slug"],
        "manifest_authority": "off-manifest" if canonical["module_state"] == "off-manifest" else "active",
        "module_state": canonical["module_state"],
        "preparation_state": canonical["preparation_state"],
        "state": canonical["state"],
        "next_action": canonical["next_action"],
        "publication": {
            "state": publication["state"],
            "surface": publication["surface"],
            "source": publication["source"],
        },
        "reason_codes": [item["id"] for item in findings],
        "owners": sorted({item["owner"] for item in findings}),
        "preparation_identity": canonical["preparation_identity"],
        "source_identities": {
            "preparation": _source_identity(canonical_sources),
            "learner_bundle": bundle["source_identity"],
            "publication": publication["source_identity"],
        },
        "evidence": "expanded" if expanded else "summary",
    }
    if expanded:
        payload["bundle_sources"] = bundle["sources"]
        payload["publication_sources"] = publication["sources"]
        payload["canonical"] = canonical
    return _with_freshness(payload)
