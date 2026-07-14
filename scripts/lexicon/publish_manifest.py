#!/usr/bin/env python3
"""Publish the hydrated Word Atlas manifest release asset.

This is intentionally separate from ``make atlas``: the atlas target builds and
verifies the DB-backed manifest, then this script packages that exact output,
uploads it to the GitHub Release asset, and rewrites the small pointer committed
to git.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import subprocess
import tempfile
from contextlib import nullcontext
from pathlib import Path
from typing import Any
from urllib.parse import quote

from scripts.lexicon.manifest_fingerprint import DEFAULT_FINGERPRINT

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = ROOT / "site" / "src" / "data" / "lexicon-manifest.json"
DEFAULT_POINTER = ROOT / "site" / "src" / "data" / "lexicon-manifest.pointer.json"
DEFAULT_GZIP = ROOT / "site" / "src" / "data" / "lexicon-manifest.json.gz"
DEFAULT_RELEASE_TAG = "atlas-manifest"
DEFAULT_REPO = "learn-ukrainian/learn-ukrainian.github.io"
ASSET_NAME = "lexicon-manifest.json.gz"
VERSIONED_ASSET_PREFIX = "lexicon-manifest-"
VERSIONED_ASSET_SUFFIX = ".json.gz"
REQUIRED_POINTER_KEYS = (
    "asset_url",
    "release_tag",
    "manifest_version",
    "manifest_fingerprint",
    "fingerprint_schema_version",
    "gz_sha256",
    "json_sha256",
    "gz_bytes",
    "json_bytes",
)
RICHNESS_REGRESSION_KEYS = (
    "poc_thin_pages",
    "search_no_visible_gloss",
    "old_gate_no_english_anchor",
)


class ManifestPublishError(RuntimeError):
    """Raised when the manifest and pointer metadata cannot be made consistent."""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ManifestPublishError(f"{path} must contain a JSON object")
    return payload


def _asset_url(repo: str, release_tag: str, asset_name: str = ASSET_NAME) -> str:
    return f"https://github.com/{repo}/releases/download/{release_tag}/{quote(asset_name)}"


def versioned_asset_name(json_sha256: str) -> str:
    return f"{VERSIONED_ASSET_PREFIX}{json_sha256[:12]}{VERSIONED_ASSET_SUFFIX}"


def validate_manifest_fingerprint(
    manifest: dict[str, Any],
    fingerprint: dict[str, Any],
    *,
    manifest_path: Path = DEFAULT_MANIFEST,
) -> None:
    """Require the built manifest to embed the sidecar fingerprint."""
    embedded = manifest.get("manifest_fingerprint")
    if not isinstance(embedded, dict):
        raise ManifestPublishError(
            f"{manifest_path} lacks manifest_fingerprint; run `make atlas` before publishing."
        )

    expected_schema = fingerprint.get("schema_version")
    expected_fingerprint = fingerprint.get("fingerprint")
    if embedded.get("schema_version") != expected_schema:
        raise ManifestPublishError(
            "manifest_fingerprint.schema_version does not match "
            "site/src/data/lexicon-manifest.fingerprint.json"
        )
    if embedded.get("fingerprint") != expected_fingerprint:
        raise ManifestPublishError(
            "manifest_fingerprint.fingerprint does not match "
            "site/src/data/lexicon-manifest.fingerprint.json"
        )


def validate_pointer_freshness(
    pointer: dict[str, Any],
    fingerprint: dict[str, Any],
    *,
    manifest: dict[str, Any] | None = None,
) -> None:
    """Mirror the build-time guard for DB-free pytest coverage."""
    missing = [key for key in REQUIRED_POINTER_KEYS if pointer.get(key) in (None, "")]
    if missing:
        raise ManifestPublishError(f"Atlas manifest pointer missing freshness keys: {', '.join(missing)}")

    if pointer.get("fingerprint_schema_version") != fingerprint.get("schema_version"):
        raise ManifestPublishError("Atlas manifest pointer fingerprint schema is stale")
    if pointer.get("manifest_fingerprint") != fingerprint.get("fingerprint"):
        raise ManifestPublishError("Atlas manifest pointer fingerprint is stale")

    if manifest is None:
        return

    if manifest.get("version") != pointer.get("manifest_version"):
        raise ManifestPublishError("Atlas manifest pointer version is stale")
    embedded = manifest.get("manifest_fingerprint")
    if not isinstance(embedded, dict):
        raise ManifestPublishError("Atlas manifest lacks manifest_fingerprint")
    if embedded.get("schema_version") != pointer.get("fingerprint_schema_version"):
        raise ManifestPublishError("Atlas manifest fingerprint schema does not match pointer")
    if embedded.get("fingerprint") != pointer.get("manifest_fingerprint"):
        raise ManifestPublishError("Atlas manifest fingerprint does not match pointer")


def gzip_manifest(manifest_path: Path = DEFAULT_MANIFEST, gzip_path: Path = DEFAULT_GZIP) -> bytes:
    """Write a deterministic gzip for the manifest and return its bytes."""
    manifest_bytes = manifest_path.read_bytes()
    gzip_bytes = gzip.compress(manifest_bytes, compresslevel=9, mtime=0)
    gzip_path.write_bytes(gzip_bytes)
    return gzip_bytes


def build_pointer_payload(
    *,
    manifest_path: Path = DEFAULT_MANIFEST,
    gzip_path: Path = DEFAULT_GZIP,
    fingerprint_path: Path = DEFAULT_FINGERPRINT,
    release_tag: str = DEFAULT_RELEASE_TAG,
    repo: str = DEFAULT_REPO,
    richness_gate: dict[str, Any],
) -> dict[str, Any]:
    """Build a pointer only after the shared release-richness gate has run."""
    validate_richness_gate_record(richness_gate)
    manifest_bytes = manifest_path.read_bytes()
    gzip_bytes = gzip_path.read_bytes()
    manifest = json.loads(manifest_bytes.decode("utf-8"))
    if not isinstance(manifest, dict):
        raise ManifestPublishError(f"{manifest_path} must contain a JSON object")
    fingerprint = _read_json(fingerprint_path)
    validate_manifest_fingerprint(manifest, fingerprint, manifest_path=manifest_path)

    manifest_version = manifest.get("version")
    if not isinstance(manifest_version, str) or not manifest_version:
        raise ManifestPublishError(f"{manifest_path} must contain a non-empty version")

    json_sha256 = _sha256(manifest_bytes)
    gz_sha256 = _sha256(gzip_bytes)

    pointer = {
        "asset_url": _asset_url(repo, release_tag, versioned_asset_name(json_sha256)),
        "release_tag": release_tag,
        "manifest_version": manifest_version,
        "manifest_fingerprint": fingerprint["fingerprint"],
        "fingerprint_schema_version": fingerprint["schema_version"],
        "generated_at": manifest.get("generated_at"),
        "gz_sha256": gz_sha256,
        "json_sha256": json_sha256,
        "gz_bytes": len(gzip_bytes),
        "json_bytes": len(manifest_bytes),
        "richness_gate": richness_gate,
        "note": "Pins GitHub Release asset manifest for #3659; hydrate it build time instead committing raw JSON.",
    }
    validate_pointer_freshness(pointer, fingerprint, manifest=manifest)
    return pointer


def write_pointer(pointer_path: Path, payload: dict[str, Any]) -> None:
    """Persist only a pointer built with a recorded richness-gate decision."""
    gate_record = payload.get("richness_gate")
    if not isinstance(gate_record, dict):
        raise ManifestPublishError("Atlas manifest pointer requires a richness_gate record")
    validate_richness_gate_record(gate_record)
    pointer_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = pointer_path.with_suffix(f"{pointer_path.suffix}.tmp")
    temp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp_path.replace(pointer_path)


def upload_release_asset(
    gzip_path: Path = DEFAULT_GZIP,
    *,
    asset_name: str = ASSET_NAME,
    release_tag: str = DEFAULT_RELEASE_TAG,
    repo: str = DEFAULT_REPO,
    clobber: bool = True,
) -> None:
    upload_path = gzip_path
    with tempfile.TemporaryDirectory() if gzip_path.name != asset_name else nullcontext(None) as temp_dir:
        if temp_dir is not None:
            upload_path = Path(temp_dir) / asset_name
            upload_path.write_bytes(gzip_path.read_bytes())

        command = [
            "gh",
            "release",
            "upload",
            release_tag,
            str(upload_path),
            "--repo",
            repo,
        ]
        if clobber:
            command.append("--clobber")
        subprocess.run(command, check=True)


def _release_asset_names(*, release_tag: str = DEFAULT_RELEASE_TAG, repo: str = DEFAULT_REPO) -> set[str]:
    result = subprocess.run(
        ["gh", "release", "view", release_tag, "--repo", repo, "--json", "assets"],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assets = payload.get("assets", [])
    if not isinstance(assets, list):
        raise ManifestPublishError("gh release view returned malformed assets payload")
    return {asset["name"] for asset in assets if isinstance(asset, dict) and isinstance(asset.get("name"), str)}


def _download_release_asset(
    asset_name: str,
    *,
    release_tag: str = DEFAULT_RELEASE_TAG,
    repo: str = DEFAULT_REPO,
) -> bytes:
    result = subprocess.run(
        ["gh", "release", "download", release_tag, "-p", asset_name, "-O", "-", "--repo", repo],
        check=True,
        capture_output=True,
    )
    return result.stdout


def _stderr_excerpt(error: subprocess.CalledProcessError, *, limit: int = 400) -> str:
    """Return bounded command stderr without inspecting the process environment."""
    stderr = error.stderr
    if isinstance(stderr, bytes):
        text = stderr.decode("utf-8", errors="replace")
    elif isinstance(stderr, str):
        text = stderr
    else:
        text = ""
    normalized = " ".join(text.split())
    return normalized[:limit]


def download_published_manifest(
    *,
    release_tag: str = DEFAULT_RELEASE_TAG,
    repo: str = DEFAULT_REPO,
) -> dict[str, Any]:
    """Return the canonical live Atlas manifest used as the publish baseline."""
    try:
        manifest_bytes = gzip.decompress(
            _download_release_asset(ASSET_NAME, release_tag=release_tag, repo=repo)
        )
        manifest = json.loads(manifest_bytes.decode("utf-8"))
    except (subprocess.CalledProcessError, OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        excerpt = _stderr_excerpt(exc) if isinstance(exc, subprocess.CalledProcessError) else ""
        detail = f" (gh stderr: {excerpt})" if excerpt else ""
        raise ManifestPublishError(
            "could not read the canonical published Atlas manifest for the richness baseline" + detail
        ) from exc
    if not isinstance(manifest, dict):
        raise ManifestPublishError("canonical published Atlas manifest must contain a JSON object")
    return manifest


def verify_existing_release_asset(
    asset_name: str,
    *,
    expected_gz_bytes: bytes,
    release_tag: str = DEFAULT_RELEASE_TAG,
    repo: str = DEFAULT_REPO,
) -> None:
    existing = _download_release_asset(asset_name, release_tag=release_tag, repo=repo)
    if existing != expected_gz_bytes:
        raise ManifestPublishError(
            f"Existing Atlas manifest release asset {asset_name} does not match local gzip bytes"
        )


def upload_manifest_assets(
    gzip_path: Path,
    pointer: dict[str, Any],
    *,
    release_tag: str = DEFAULT_RELEASE_TAG,
    repo: str = DEFAULT_REPO,
) -> None:
    """Upload immutable + canonical assets; prune old versioned assets manually when the release gets heavy."""
    versioned_name = versioned_asset_name(pointer["json_sha256"])
    gzip_bytes = gzip_path.read_bytes()
    if versioned_name in _release_asset_names(release_tag=release_tag, repo=repo):
        verify_existing_release_asset(
            versioned_name,
            expected_gz_bytes=gzip_bytes,
            release_tag=release_tag,
            repo=repo,
        )
    else:
        upload_release_asset(
            gzip_path,
            asset_name=versioned_name,
            release_tag=release_tag,
            repo=repo,
            clobber=False,
        )
    upload_release_asset(gzip_path, asset_name=ASSET_NAME, release_tag=release_tag, repo=repo, clobber=True)


def assert_manifest_richness_publishable(
    manifest_path: Path,
    *,
    baseline_manifest: dict[str, Any],
    allow_richness_regression_reason: str | None = None,
) -> dict[str, Any]:
    """Block publish-time richness regressions relative to the live asset.

    Per-PR CI deliberately audits the live asset only as an advisory signal.
    This mutation chokepoint compares the manifest about to be published with
    the canonical live Release asset, including on dry runs.
    """
    from scripts.audit.audit_atlas_poc_richness import audit_manifest

    reason = allow_richness_regression_reason.strip() if allow_richness_regression_reason else None
    if allow_richness_regression_reason is not None and not reason:
        raise ManifestPublishError("--allow-richness-regression requires a non-empty reason")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    candidate_summary = audit_manifest(manifest)
    baseline_summary = audit_manifest(baseline_manifest)
    broken_stubs = int(candidate_summary.get("form_stub_broken", 0))
    if broken_stubs > 0:
        raise ManifestPublishError(
            f"publish blocked (#4220): manifest at {manifest_path} has {broken_stubs} "
            f"broken form_of stub page(s). Each stub must point at an existing manifest "
            f"entry and expose a gloss or form_of lemma label. Repair the broken stubs "
            f"(samples: scripts/audit/audit_atlas_poc_richness.py --format json "
            f"--limit 2000, bucket form_stub_broken) before publishing. There is no "
            f"publish-time override by design."
        )
    regressions = {
        key: {
            "baseline": int(baseline_summary[key]),
            "candidate": int(candidate_summary[key]),
        }
        for key in RICHNESS_REGRESSION_KEYS
        if int(candidate_summary[key]) > int(baseline_summary[key])
    }
    record = {
        "baseline": {key: int(baseline_summary[key]) for key in RICHNESS_REGRESSION_KEYS},
        "candidate": {key: int(candidate_summary[key]) for key in RICHNESS_REGRESSION_KEYS},
        "regressions": regressions,
        "override_reason": reason,
    }
    if regressions and reason is None:
        details = ", ".join(
            f"{key} {values['baseline']}→{values['candidate']}"
            for key, values in regressions.items()
        )
        raise ManifestPublishError(
            f"publish blocked (#4515): Atlas POC richness regressed versus the canonical "
            f"published manifest ({details}). Enrich the affected entries before publishing "
            "or use --allow-richness-regression with an operator decision reason."
        )
    return record


def assert_manifest_richness_bootstrap_publishable(manifest_path: Path) -> dict[str, Any]:
    """Validate a first publish that deliberately has no canonical baseline yet."""
    from scripts.audit.audit_atlas_poc_richness import audit_manifest

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    candidate_summary = audit_manifest(manifest)
    broken_stubs = int(candidate_summary.get("form_stub_broken", 0))
    if broken_stubs > 0:
        raise ManifestPublishError(
            f"publish blocked (#4220): manifest at {manifest_path} has {broken_stubs} "
            "broken form_of stub page(s). Each stub must point at an existing manifest "
            "entry and expose a gloss or form_of lemma label. Repair the broken stubs "
            "(samples: scripts/audit/audit_atlas_poc_richness.py --format json "
            "--limit 2000, bucket form_stub_broken) before publishing. There is no "
            "publish-time override by design."
        )
    return {
        "bootstrap": True,
        "baseline": None,
        "candidate": {key: int(candidate_summary[key]) for key in RICHNESS_REGRESSION_KEYS},
        "regressions": {},
        "override_reason": None,
    }


def canonical_published_manifest_exists(
    *,
    release_tag: str = DEFAULT_RELEASE_TAG,
    repo: str = DEFAULT_REPO,
) -> bool:
    """Return whether the canonical baseline asset exists on the configured release."""
    try:
        return ASSET_NAME in _release_asset_names(release_tag=release_tag, repo=repo)
    except subprocess.CalledProcessError as exc:
        excerpt = _stderr_excerpt(exc)
        raise ManifestPublishError(
            "could not determine whether the canonical published Atlas manifest exists"
            + (f" (gh stderr: {excerpt})" if excerpt else "")
        ) from exc


def evaluate_manifest_pointer_write_gate(
    manifest_path: Path,
    *,
    release_tag: str = DEFAULT_RELEASE_TAG,
    repo: str = DEFAULT_REPO,
    allow_richness_regression_reason: str | None = None,
    bootstrap_no_baseline: bool = False,
) -> dict[str, Any]:
    """Run the one required richness decision before any Atlas pointer packaging."""
    if bootstrap_no_baseline:
        if allow_richness_regression_reason is not None:
            raise ManifestPublishError(
                "--bootstrap-no-baseline cannot be combined with --allow-richness-regression"
            )
        if canonical_published_manifest_exists(release_tag=release_tag, repo=repo):
            raise ManifestPublishError(
                "--bootstrap-no-baseline is only valid when the canonical published Atlas manifest "
                "does not exist"
            )
        return assert_manifest_richness_bootstrap_publishable(manifest_path)

    baseline_manifest = download_published_manifest(release_tag=release_tag, repo=repo)
    record = assert_manifest_richness_publishable(
        manifest_path,
        baseline_manifest=baseline_manifest,
        allow_richness_regression_reason=allow_richness_regression_reason,
    )
    record["bootstrap"] = False
    return record


def validate_richness_gate_record(record: dict[str, Any]) -> None:
    """Reject pointer payloads that did not carry a complete gate decision."""
    bootstrap = record.get("bootstrap")
    if not isinstance(bootstrap, bool):
        raise ManifestPublishError("Atlas manifest richness_gate must record boolean bootstrap")

    candidate = record.get("candidate")
    if not isinstance(candidate, dict) or any(key not in candidate for key in RICHNESS_REGRESSION_KEYS):
        raise ManifestPublishError("Atlas manifest richness_gate must record all candidate richness metrics")

    baseline = record.get("baseline")
    if bootstrap:
        if baseline is not None:
            raise ManifestPublishError("bootstrap richness_gate must not contain a baseline")
    elif not isinstance(baseline, dict) or any(key not in baseline for key in RICHNESS_REGRESSION_KEYS):
        raise ManifestPublishError("Atlas manifest richness_gate must record all baseline richness metrics")

    regressions = record.get("regressions")
    if not isinstance(regressions, dict):
        raise ManifestPublishError("Atlas manifest richness_gate must record regressions")
    if "override_reason" not in record:
        raise ManifestPublishError("Atlas manifest richness_gate must record override_reason")


def publish_manifest(
    *,
    manifest_path: Path = DEFAULT_MANIFEST,
    gzip_path: Path = DEFAULT_GZIP,
    pointer_path: Path = DEFAULT_POINTER,
    fingerprint_path: Path = DEFAULT_FINGERPRINT,
    release_tag: str = DEFAULT_RELEASE_TAG,
    repo: str = DEFAULT_REPO,
    dry_run: bool = False,
    allow_richness_regression_reason: str | None = None,
    bootstrap_no_baseline: bool = False,
) -> dict[str, Any]:
    richness_record = evaluate_manifest_pointer_write_gate(
        manifest_path,
        release_tag=release_tag,
        repo=repo,
        allow_richness_regression_reason=allow_richness_regression_reason,
        bootstrap_no_baseline=bootstrap_no_baseline,
    )
    gzip_manifest(manifest_path, gzip_path)
    pointer = build_pointer_payload(
        manifest_path=manifest_path,
        gzip_path=gzip_path,
        fingerprint_path=fingerprint_path,
        release_tag=release_tag,
        repo=repo,
        richness_gate=richness_record,
    )

    if dry_run:
        return pointer

    upload_manifest_assets(gzip_path, pointer, release_tag=release_tag, repo=repo)
    write_pointer(pointer_path, pointer)
    return pointer


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish the Word Atlas manifest release asset.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--gzip", type=Path, default=DEFAULT_GZIP)
    parser.add_argument("--pointer", type=Path, default=DEFAULT_POINTER)
    parser.add_argument("--fingerprint", type=Path, default=DEFAULT_FINGERPRINT)
    parser.add_argument("--release-tag", default=DEFAULT_RELEASE_TAG)
    parser.add_argument("--repo", default=DEFAULT_REPO)
    parser.add_argument("--dry-run", action="store_true", help="Build metadata without uploading or writing pointer")
    parser.add_argument(
        "--allow-richness-regression",
        metavar="REASON",
        help="Publish despite a richness regression, recording this required operator decision reason.",
    )
    parser.add_argument(
        "--bootstrap-no-baseline",
        action="store_true",
        help=(
            "Allow the first publish only when the canonical release asset does not exist; "
            "records bootstrap=true in the pointer."
        ),
    )
    args = parser.parse_args()

    pointer = publish_manifest(
        manifest_path=args.manifest,
        gzip_path=args.gzip,
        pointer_path=args.pointer,
        fingerprint_path=args.fingerprint,
        release_tag=args.release_tag,
        repo=args.repo,
        dry_run=args.dry_run,
        allow_richness_regression_reason=args.allow_richness_regression,
        bootstrap_no_baseline=args.bootstrap_no_baseline,
    )
    print(
        "Atlas manifest pointer "
        f"{'would publish' if args.dry_run else 'published'}: "
        f"{pointer['manifest_version']} {pointer['manifest_fingerprint']}"
    )
    print(f"asset_url: {pointer['asset_url']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
