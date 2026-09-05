"""Build the fixed resource closure from actual Git source; never executed at runtime."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent
REPOSITORY = PACKAGE.parents[1]
NAMESPACE = "learn_ukrainian_v4_runtime"
VERSION = "1.0.0"
RELATIONSHIP = "runtime_successor_validating_frozen_receipt"


def canonical(value):
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode() + b"\n"
    )


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def collect_assets(destination: Path) -> None:
    """Copy only reviewed allowlisted bytes; receipts never select more assets."""
    assets = json.loads((PACKAGE / "asset_allowlist.json").read_bytes())
    for relative, expected in assets.items():
        path = Path(relative)
        if (
            path.is_absolute()
            or ".." in path.parts
            or not (relative == "LICENSE-CONTENT.md" or relative.startswith("data/projects/open_model_data/"))
        ):
            raise ValueError("invalid explicit asset")
        raw = (REPOSITORY / path).read_bytes()
        if digest(raw) != expected:
            raise ValueError("explicit asset digest mismatch: " + relative)
        target = destination / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    # Preserve the historical generated v1 bytes. The reviewed v2 profile is
    # copied exclusively through the digest allowlist above, never generated.
    profile = destination / "data/projects/open_model_data/trust/v4_child_profile_v1.json"
    profile.write_bytes(
        canonical(
            {
                "schema": "hramatka-v4-child-profile.v1",
                "bwrap": "/usr/bin/bwrap",
                "bwrap_sha256": None,
                "sources_url": None,
                "adapters": {},
            }
        )
    )


def write_manifest(destination: Path, *, development: bool = False) -> None:
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPOSITORY, text=True).strip()
    # The build command is bound to real committed inputs, including assets,
    # package code, build hooks, license and frozen relationship specification.
    inputs = ["packages/v4-runtime", *json.loads((PACKAGE / "asset_allowlist.json").read_bytes())]
    dirty = subprocess.check_output(
        ["git", "status", "--porcelain", "--untracked-files=all", "--", *inputs], cwd=REPOSITORY
    )
    if dirty and not development:
        raise ValueError("release requires committed package and asset inputs")
    commit = None if dirty else sha
    spec = json.loads((destination / "provenance/v1/bindings.json").read_bytes())
    receipts = []
    for item in spec["receipts"]:
        record = dict(item)
        if digest((destination / item["resource"]).read_bytes()) != item["sha256"]:
            raise ValueError("frozen receipt digest mismatch")
        record["occurrences"] = {}
        for name, binding in item["bindings"].items():
            logical = binding["path"]
            if logical.startswith("scripts/"):
                blob = "provenance/v1/blobs/sha256/" + binding["sha256"] + ".blob"
                successor = Path(logical).name
                if digest((destination / blob).read_bytes()) != binding["sha256"]:
                    raise ValueError("historical implementation digest mismatch")
                record["occurrences"][name] = {
                    "binding": binding,
                    "historical_resource": blob,
                    "historical_sha256": binding["sha256"],
                    "successor_resource": successor,
                    "successor_sha256": digest((destination / successor).read_bytes()),
                    "relationship": RELATIONSHIP,
                    "package_version": VERSION,
                    "public_commit": commit,
                }
            else:
                record["occurrences"][name] = {
                    "binding": binding,
                    "resource": logical,
                    "sha256": binding["sha256"],
                    "relationship": "frozen_data_resource",
                    "package_version": VERSION,
                    "public_commit": commit,
                }
        receipts.append(record)
    manifest = {
        "schema": "v4-sealed-provenance.v1",
        "package_version": VERSION,
        "public_commit": commit,
        "historical_source_commit": spec["source_commit"],
        "receipts": receipts,
        "a3": {
            "seal_sha256": "d3147b0201d0f358677825ea6700e3e3e81b7e2fad551fe6c4e7b174d402f860",
            "receipt_binding_sha256": "1c0d736aa729ba7836ce3b5732a1ef7b3a9fdba71455a30185b76f1c24e3dd0a",
            "algorithm_descriptor_sha256": "b2abbb8e45f60abb098b8976dec7e7f2b4668137f55bfab8eee3999bd65a1928",
        },
    }
    provenance = canonical(manifest)
    (destination / "provenance/v1/manifest.json").write_bytes(provenance)
    tracked = subprocess.check_output(
        ["git", "ls-files", "packages/v4-runtime/src/" + NAMESPACE], cwd=REPOSITORY, text=True
    ).splitlines()
    prefix = "packages/v4-runtime/src/" + NAMESPACE + "/"
    source_files = {name.removeprefix(prefix) for name in tracked}
    allowed = (
        source_files
        | set(json.loads((PACKAGE / "asset_allowlist.json").read_bytes()))
        | {
            "data/projects/open_model_data/trust/v4_child_profile_v1.json",
            "provenance/v1/manifest.json",
            "release_manifest.json",
            "_build_identity.py",
        }
    )
    for path in destination.rglob("*"):
        if path.is_file() and "__pycache__" not in path.parts:
            relative = str(path.relative_to(destination))
            if relative not in allowed:
                raise ValueError("unreviewed file in build output: " + relative)
            if relative in source_files and not development:
                committed = subprocess.check_output(["git", "show", sha + ":" + prefix + relative], cwd=REPOSITORY)
                if path.read_bytes() != committed:
                    raise ValueError("build file differs from actual source commit: " + relative)
    installed = {
        str(p.relative_to(destination)): digest(p.read_bytes())
        for p in sorted(destination.rglob("*"))
        if p.is_file()
        and p.name not in ("release_manifest.json", "_build_identity.py")
        and "__pycache__" not in p.parts
    }
    release = canonical(
        {
            "schema": "v4-runtime-release.v1",
            "public_commit": commit,
            "package_version": VERSION,
            "provenance_sha256": digest(provenance),
            "files": installed,
        }
    )
    (destination / "release_manifest.json").write_bytes(release)
    # Acyclic: external vendor manifest hashes wheel, release AND identity file.
    # Identity hashes release; release hashes provenance + all other runtime files.
    (destination / "_build_identity.py").write_text(
        '"""Reproducible build identity; externally anchored by private vendor verification."""\n'
        + f"PUBLIC_COMMIT = {commit!r}\nPACKAGE_VERSION = {VERSION!r}\n"
        + f"RELEASE_MANIFEST_SHA256 = {digest(release)!r}\nPROVENANCE_MANIFEST_SHA256 = {digest(provenance)!r}\n"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Prepare fixed package resources for local tests. Release builds require committed source.",
        epilog="Example: .venv/bin/python packages/v4-runtime/build_assets.py --development\n"
        "Outputs: ignored local resource copies and identity. Exit codes: 0 success; 1 invalid source. Related: PR #7662.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--development",
        action="store_true",
        help="Allow dirty source with public commit explicitly absent; never release-ready (default: false).",
    )
    args = parser.parse_args()
    collect_assets(PACKAGE / "src" / NAMESPACE)
    write_manifest(PACKAGE / "src" / NAMESPACE, development=args.development)
