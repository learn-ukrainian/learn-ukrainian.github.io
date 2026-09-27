"""Tests for deploy-time Atlas tree vendoring (PR3 D1 / R1 / R7)."""

from __future__ import annotations

import hashlib
import json
import re
import zipfile
from pathlib import Path

import pytest

from scripts.deploy.vendor_atlas_tree import (
    SKIP_MESSAGE,
    TREE_MANIFEST_REL,
    VendorError,
    build_archive_from_tree,
    main,
    sha256_hex,
    vendor_atlas_tree,
    verify_archive_digest,
)


def _write(path: Path, data: bytes | str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, str):
        path.write_text(data, encoding="utf-8")
    else:
        path.write_bytes(data)


def _mini_generation(root: Path, data_version: str, *, payload: bytes) -> None:
    """Write a minimal versions/<dataVersion>/ tree (manifest + one shard)."""
    version_root = root / "atlas" / "versions" / data_version
    shard_rel = "entries/p00-0.json.gz"
    _write(version_root / shard_rel, payload)
    manifest = {
        "schema": "atlas-runtime-manifest",
        "schemaVersion": 1,
        "dataVersion": data_version,
        "generatedAt": "2026-07-17T00:00:00+00:00",
        "entries": {
            "tree": {"shardId": "p00-0"},
            "shards": {
                "p00-0": {
                    "id": "p00-0",
                    "url": shard_rel,
                    "count": 1,
                    "bytes": len(payload),
                    "uncompressedBytes": len(payload),
                    "sha256": sha256_hex(payload),
                    "jsonSha256": sha256_hex(payload),
                    "encoding": "gzip",
                }
            },
        },
        "search": {"articles": {"tree": {}, "shards": {}}, "aliases": {"tree": {}, "shards": {}}},
        "decks": {"levels": {}},
        "counts": {"entryShards": 1},
    }
    _write(
        version_root / "manifest.json",
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
    )


def _build_two_gen_tree(tmp: Path, *, current: str = "v-current", prior: str = "v-prior") -> Path:
    """Create tree_root with atlas/current.json + two version dirs."""
    tree_root = tmp / "tree"
    _mini_generation(tree_root, prior, payload=b"prior-shard-bytes")
    _mini_generation(tree_root, current, payload=b"current-shard-bytes")
    current_doc = {
        "schema": "atlas-current",
        "schemaVersion": 1,
        "dataVersion": current,
        "generatedAt": "2026-07-17T00:00:00+00:00",
        "manifestUrl": f"versions/{current}/manifest.json",
    }
    _write(
        tree_root / "atlas" / "current.json",
        json.dumps(current_doc, ensure_ascii=False, indent=2) + "\n",
    )
    return tree_root


def _archive_for(tree_root: Path, tmp: Path) -> tuple[Path, str]:
    archive = tmp / "atlas-tree.zip"
    digest = build_archive_from_tree(tree_root, archive)
    return archive, digest


def test_happy_path_vendors_current_and_prior(tmp_path: Path) -> None:
    tree_root = _build_two_gen_tree(tmp_path)
    archive, digest = _archive_for(tree_root, tmp_path)
    dist = tmp_path / "dist"
    metrics_path = tmp_path / "metrics.json"

    # Capture original bytes of a versioned shard for R10 byte-preservation.
    original_shard = (
        tree_root / "atlas" / "versions" / "v-current" / "entries" / "p00-0.json.gz"
    ).read_bytes()

    metrics = vendor_atlas_tree(
        dist,
        sha256=digest,
        archive_path=archive,
        metrics_path=metrics_path,
    )

    assert metrics.skipped is False
    assert metrics.data_version == "v-current"
    assert "v-prior" in metrics.prior_versions
    assert metrics.archive_bytes == archive.stat().st_size
    assert metrics.object_count >= 4
    assert metrics.extracted_bytes > 0
    assert metrics.archive_sha256 == digest

    installed_shard = dist / "atlas" / "versions" / "v-current" / "entries" / "p00-0.json.gz"
    assert installed_shard.read_bytes() == original_shard
    assert (dist / "atlas" / "versions" / "v-prior" / "manifest.json").is_file()
    assert (dist / "atlas" / "current.json").is_file()
    assert (dist / "atlas" / "tree-manifest.json").is_file()

    saved = json.loads(metrics_path.read_text(encoding="utf-8"))
    assert saved["data_version"] == "v-current"
    assert saved["archive_sha256"] == digest


def test_corrupt_archive_sha256_fails_closed(tmp_path: Path) -> None:
    tree_root = _build_two_gen_tree(tmp_path)
    archive, digest = _archive_for(tree_root, tmp_path)
    # Flip one byte after digest pin — checksum gate must abort before install.
    blob = bytearray(archive.read_bytes())
    blob[0] = (blob[0] + 1) % 256
    corrupt = tmp_path / "corrupt.zip"
    corrupt.write_bytes(bytes(blob))
    dist = tmp_path / "dist"
    dist.mkdir()
    sentinel = dist / "keep-me.txt"
    sentinel.write_text("pre-existing", encoding="utf-8")

    with pytest.raises(VendorError, match="archive sha256 mismatch"):
        vendor_atlas_tree(dist, sha256=digest, archive_path=corrupt)

    assert not (dist / "atlas").exists()
    assert sentinel.read_text(encoding="utf-8") == "pre-existing"


def test_verify_archive_digest_direct() -> None:
    data = b"abc"
    digest = hashlib.sha256(data).hexdigest()
    assert verify_archive_digest(data, digest) == digest
    with pytest.raises(VendorError, match="sha256 mismatch"):
        verify_archive_digest(data, "0" * 64)


def test_manifest_inconsistency_fails_closed(tmp_path: Path) -> None:
    tree_root = _build_two_gen_tree(tmp_path)
    archive, _digest = _archive_for(tree_root, tmp_path)

    # Rebuild zip with a size lie in tree-manifest.
    with zipfile.ZipFile(archive, "r") as zf:
        members = {name: zf.read(name) for name in zf.namelist() if not name.endswith("/")}
    manifest = json.loads(members[TREE_MANIFEST_REL].decode("utf-8"))
    # Point at a real file but claim wrong size.
    for entry in manifest["files"]:
        if entry["path"].endswith("p00-0.json.gz"):
            entry["bytes"] = entry["bytes"] + 99
            break
    members[TREE_MANIFEST_REL] = (json.dumps(manifest, indent=2) + "\n").encode("utf-8")
    # Also fix the self-size entry for tree-manifest so only the shard size is wrong.
    for entry in manifest["files"]:
        if entry["path"] == TREE_MANIFEST_REL:
            entry["bytes"] = len(members[TREE_MANIFEST_REL])
    members[TREE_MANIFEST_REL] = (json.dumps(manifest, indent=2) + "\n").encode("utf-8")
    for entry in manifest["files"]:
        if entry["path"] == TREE_MANIFEST_REL:
            entry["bytes"] = len(members[TREE_MANIFEST_REL])
    members[TREE_MANIFEST_REL] = (json.dumps(manifest, indent=2) + "\n").encode("utf-8")

    bad = tmp_path / "bad-manifest.zip"
    with zipfile.ZipFile(bad, "w") as zf:
        for name, data in members.items():
            zf.writestr(name, data)
    bad_digest = sha256_hex(bad.read_bytes())

    with pytest.raises(VendorError, match="size mismatch"):
        vendor_atlas_tree(tmp_path / "dist", sha256=bad_digest, archive_path=bad)


def test_missing_file_in_manifest_fails_closed(tmp_path: Path) -> None:
    tree_root = _build_two_gen_tree(tmp_path)
    archive, _digest = _archive_for(tree_root, tmp_path)
    with zipfile.ZipFile(archive, "r") as zf:
        members = {name: zf.read(name) for name in zf.namelist() if not name.endswith("/")}
    manifest = json.loads(members[TREE_MANIFEST_REL].decode("utf-8"))
    manifest["files"].append({"path": "atlas/versions/v-current/missing.bin", "bytes": 1})
    members[TREE_MANIFEST_REL] = (json.dumps(manifest, indent=2) + "\n").encode("utf-8")
    for entry in manifest["files"]:
        if entry["path"] == TREE_MANIFEST_REL:
            entry["bytes"] = len(members[TREE_MANIFEST_REL])
    members[TREE_MANIFEST_REL] = (json.dumps(manifest, indent=2) + "\n").encode("utf-8")

    bad = tmp_path / "missing-file.zip"
    with zipfile.ZipFile(bad, "w") as zf:
        for name, data in members.items():
            zf.writestr(name, data)
    digest = sha256_hex(bad.read_bytes())

    with pytest.raises(VendorError, match="missing file"):
        vendor_atlas_tree(tmp_path / "dist", sha256=digest, archive_path=bad)


def test_extra_unlisted_file_fails_closed(tmp_path: Path) -> None:
    """Archive member not in tree-manifest must fail closed (object_count gate)."""
    tree_root = _build_two_gen_tree(tmp_path)
    archive, _digest = _archive_for(tree_root, tmp_path)
    with zipfile.ZipFile(archive, "r") as zf:
        members = {
            name: zf.read(name) for name in zf.namelist() if not name.endswith("/")
        }
    # Inject a payload under atlas/ that packaging manifest does not list.
    members["atlas/versions/v-current/sneaky-extra.bin"] = b"unlisted-payload"
    bad = tmp_path / "extra-unlisted.zip"
    with zipfile.ZipFile(bad, "w") as zf:
        for name, data in members.items():
            zf.writestr(name, data)
    digest = sha256_hex(bad.read_bytes())
    dist = tmp_path / "dist"
    dist.mkdir()
    sentinel = dist / "keep-me.txt"
    sentinel.write_text("pre-existing", encoding="utf-8")

    with pytest.raises(
        VendorError,
        match=r"files not listed in packaging manifest.*object_count=.*listed_file_count=",
    ):
        vendor_atlas_tree(dist, sha256=digest, archive_path=bad)

    assert not (dist / "atlas").exists()
    assert sentinel.read_text(encoding="utf-8") == "pre-existing"


def test_missing_prior_generation_fails(tmp_path: Path) -> None:
    tree_root = tmp_path / "tree"
    _mini_generation(tree_root, "v-only", payload=b"solo")
    current_doc = {
        "schema": "atlas-current",
        "schemaVersion": 1,
        "dataVersion": "v-only",
        "generatedAt": "2026-07-17T00:00:00+00:00",
        "manifestUrl": "versions/v-only/manifest.json",
    }
    _write(
        tree_root / "atlas" / "current.json",
        json.dumps(current_doc, indent=2) + "\n",
    )
    archive, digest = _archive_for(tree_root, tmp_path)

    with pytest.raises(VendorError, match="PRIOR generation"):
        vendor_atlas_tree(tmp_path / "dist", sha256=digest, archive_path=archive)


TRANSPORT_HEX = "ab" * 32


def _with_transport_current(
    tmp: Path,
    *,
    prior: str | None = "v-prior",
    current: str = "v-current",
    manifest_url: str | None = None,
    data_version: str | None = None,
) -> Path:
    """Tree whose current.json points at ``<current>-transport-<hex>`` beside canonical."""
    tree_root = tmp / "tree"
    if prior is not None:
        _mini_generation(tree_root, prior, payload=b"prior-shard-bytes")
    _mini_generation(tree_root, current, payload=b"canonical-shard-bytes")
    alternate = f"{current}-transport-{TRANSPORT_HEX}"
    _mini_generation(tree_root, alternate, payload=b"alternate-shard-bytes")
    # The exporter's alternate carries the canonical dataVersion inside its manifest.
    alt_manifest = tree_root / "atlas" / "versions" / alternate / "manifest.json"
    doc = json.loads(alt_manifest.read_text(encoding="utf-8"))
    doc["dataVersion"] = current
    _write(alt_manifest, json.dumps(doc, indent=2) + "\n")
    _write(
        tree_root / "atlas" / "current.json",
        json.dumps(
            {
                "schema": "atlas-current",
                "schemaVersion": 1,
                "dataVersion": data_version or current,
                "generatedAt": "2026-07-17T00:00:00+00:00",
                "manifestUrl": manifest_url or f"versions/{alternate}/manifest.json",
            }
        )
        + "\n",
    )
    return tree_root


def test_transport_suffixed_current_vendors_both_trees_byte_for_byte(tmp_path: Path) -> None:
    tree_root = _with_transport_current(tmp_path)
    archive, digest = _archive_for(tree_root, tmp_path)
    dist = tmp_path / "dist"

    metrics = vendor_atlas_tree(dist, sha256=digest, archive_path=archive)

    alternate = f"v-current-transport-{TRANSPORT_HEX}"
    assert metrics.data_version == "v-current"
    # The canonical sibling is the same logical generation, never a PRIOR.
    assert "v-current" not in metrics.prior_versions
    assert "v-prior" in metrics.prior_versions
    for name in ("v-current", alternate, "v-prior"):
        src = tree_root / "atlas" / "versions" / name
        for path in src.rglob("*"):
            if path.is_file():
                installed = dist / "atlas" / "versions" / name / path.relative_to(src)
                assert installed.read_bytes() == path.read_bytes()


def test_transport_current_with_only_canonical_sibling_fails_retention(tmp_path: Path) -> None:
    tree_root = _with_transport_current(tmp_path, prior=None)
    archive, digest = _archive_for(tree_root, tmp_path)

    with pytest.raises(VendorError, match="PRIOR generation"):
        vendor_atlas_tree(tmp_path / "dist", sha256=digest, archive_path=archive)


def _add_generation(tree_root: Path, dir_name: str, *, data_version: str, payload: bytes) -> None:
    """A ``versions/<dir_name>`` tree whose manifest carries ``data_version`` (exporter shape)."""
    _mini_generation(tree_root, dir_name, payload=payload)
    manifest = tree_root / "atlas" / "versions" / dir_name / "manifest.json"
    doc = json.loads(manifest.read_text(encoding="utf-8"))
    doc["dataVersion"] = data_version
    _write(manifest, json.dumps(doc, indent=2) + "\n")


def test_prior_transport_sibling_does_not_count_as_extra_prior(tmp_path: Path) -> None:
    tree_root = _with_transport_current(tmp_path, prior=None)
    # Another transport sibling of the SAME current generation is still not a prior.
    _add_generation(
        tree_root, f"v-current-transport-{'cd' * 32}", data_version="v-current", payload=b"other-alternate"
    )
    archive, digest = _archive_for(tree_root, tmp_path)

    with pytest.raises(VendorError, match="PRIOR generation"):
        vendor_atlas_tree(tmp_path / "dist", sha256=digest, archive_path=archive)


def test_canonical_current_ignores_transport_sibling_as_prior(tmp_path: Path) -> None:
    tree_root = _with_transport_current(
        tmp_path, prior=None, manifest_url="versions/v-current/manifest.json"
    )
    archive, digest = _archive_for(tree_root, tmp_path)

    with pytest.raises(VendorError, match="PRIOR generation"):
        vendor_atlas_tree(tmp_path / "dist", sha256=digest, archive_path=archive)


@pytest.mark.parametrize(
    "manifest_url",
    [
        f"versions/v-current-transport-{'AB' * 32}/manifest.json",  # uppercase hex
        f"versions/v-current-transport-{'ab' * 31}/manifest.json",  # short digest
        f"versions/v-current-transport-{'ab' * 33}/manifest.json",  # long digest
        f"versions/v-current-transport-{'ab' * 32}x/manifest.json",  # trailing junk
        "versions/v-current-transport-/manifest.json",  # empty digest
        f"versions/v-current-{'ab' * 32}/manifest.json",  # missing marker
        f"versions/v-current-transport-{'ab' * 32}/../v-prior/manifest.json",
        f"versions/../versions/v-current-transport-{'ab' * 32}/manifest.json",
        f"versions//v-current-transport-{'ab' * 32}/manifest.json",
        f"versions/v-current-transport-{'ab' * 32}//manifest.json",
        f"versions/v-current-transport-{'ab' * 32}/manifest.json/",
        f"versions/v-current-transport-{'ab' * 32}/other.json",
        f"versions\\v-current-transport-{'ab' * 32}\\manifest.json",
        f"/versions/v-current-transport-{'ab' * 32}/manifest.json",
        "versions/v-prior/manifest.json",  # a different dataVersion's directory
        "versions/v-current/extra/manifest.json",
        "versions/v-current",
    ],
)
def test_malformed_transport_manifest_url_fails(tmp_path: Path, manifest_url: str) -> None:
    tree_root = _with_transport_current(tmp_path, manifest_url=manifest_url)
    archive, digest = _archive_for(tree_root, tmp_path)

    with pytest.raises(VendorError, match="manifestUrl"):
        vendor_atlas_tree(tmp_path / "dist", sha256=digest, archive_path=archive)


@pytest.mark.parametrize(
    "data_version",
    ["..", ".", "a/b", "a\\b", "../v-current", "/abs", " v-current", f"v-current-transport-{'ab' * 32}"],
)
def test_unsafe_data_version_fails(tmp_path: Path, data_version: str) -> None:
    tree_root = _with_transport_current(tmp_path, data_version=data_version)
    archive, digest = _archive_for(tree_root, tmp_path)

    with pytest.raises(VendorError):
        vendor_atlas_tree(tmp_path / "dist", sha256=digest, archive_path=archive)


def test_transport_manifest_with_wrong_data_version_fails(tmp_path: Path) -> None:
    tree_root = _with_transport_current(tmp_path)
    alt_manifest = (
        tree_root / "atlas" / "versions" / f"v-current-transport-{TRANSPORT_HEX}" / "manifest.json"
    )
    doc = json.loads(alt_manifest.read_text(encoding="utf-8"))
    doc["dataVersion"] = "v-prior"
    _write(alt_manifest, json.dumps(doc, indent=2) + "\n")
    archive, digest = _archive_for(tree_root, tmp_path)

    with pytest.raises(VendorError, match="does not carry dataVersion"):
        vendor_atlas_tree(tmp_path / "dist", sha256=digest, archive_path=archive)


def test_transport_manifest_missing_from_archive_fails(tmp_path: Path) -> None:
    tree_root = _with_transport_current(tmp_path)
    (
        tree_root / "atlas" / "versions" / f"v-current-transport-{TRANSPORT_HEX}" / "manifest.json"
    ).unlink()
    archive, digest = _archive_for(tree_root, tmp_path)

    with pytest.raises(VendorError, match="manifestUrl missing on disk"):
        vendor_atlas_tree(tmp_path / "dist", sha256=digest, archive_path=archive)


# A generation directory is counted only once its name shape and manifest identity
# are proven; a malformed sibling can never pose as a distinct PRIOR (#8672 review).


@pytest.mark.parametrize(
    "current_dir", ["v-current", f"v-current-transport-{TRANSPORT_HEX}"], ids=["canonical", "transport"]
)
def test_reviewer_malformed_transport_sibling_is_not_a_prior(tmp_path: Path, current_dir: str) -> None:
    # Canonical current + valid alternate current + malformed 62-hex sibling, all v-current.
    tree_root = _with_transport_current(
        tmp_path, prior=None, manifest_url=f"versions/{current_dir}/manifest.json"
    )
    malformed = f"v-current-transport-{'ef' * 31}"
    _add_generation(tree_root, malformed, data_version="v-current", payload=b"malformed-sibling")
    archive, digest = _archive_for(tree_root, tmp_path)
    dist = tmp_path / "dist"

    with pytest.raises(VendorError, match="malformed generation directory") as excinfo:
        vendor_atlas_tree(dist, sha256=digest, archive_path=archive)
    assert malformed in str(excinfo.value)
    assert not (dist / "atlas").exists()


@pytest.mark.parametrize(
    "dir_name",
    [
        f"v-current-transport-{'ef' * 31}",  # reviewer: 62 hex
        f"v-current-transport-{'ef' * 31}e",  # 63 hex
        f"v-current-transport-{'ef' * 32}0",  # 65 hex
        f"v-current-transport-{'EF' * 32}",  # uppercase hex
        f"v-current-transport-{'ef' * 32}x",  # trailing junk
        "v-current-transport-",  # empty digest
        f"v-current-transport-{'eg' * 32}",  # non-hex
        f"v-current-transport-{'ab' * 32}-transport-{'cd' * 32}",  # double suffix
        "v-transport-prior",  # marker inside a would-be canonical name
        f"v-prior-transport-{'ef' * 31}",  # malformed suffix on a different dataVersion
        " v-prior",  # not a safe path component
    ],
)
def test_malformed_generation_directory_fails_closed(tmp_path: Path, dir_name: str) -> None:
    tree_root = _with_transport_current(tmp_path)  # valid canonical, alternate and prior
    match = TRANSPORT_DIR_NAME.fullmatch(dir_name)
    _add_generation(
        tree_root, dir_name, data_version=match.group(1) if match else dir_name.strip(), payload=b"odd"
    )
    archive, digest = _archive_for(tree_root, tmp_path)

    with pytest.raises(VendorError, match="malformed generation directory"):
        vendor_atlas_tree(tmp_path / "dist", sha256=digest, archive_path=archive)


TRANSPORT_DIR_NAME = re.compile(r"(.+?)-transport-")


@pytest.mark.parametrize(
    ("dir_name", "manifest_data_version"),
    [
        ("v-prior", "v-current"),  # a current copy posing under a prior's name
        ("v-prior", "v-other"),
        (f"v-prior-transport-{'ef' * 32}", "v-current"),
        (f"v-prior-transport-{'ef' * 32}", f"v-prior-transport-{'ef' * 32}"),
        (f"v-current-transport-{'ef' * 32}", f"v-current-transport-{'ef' * 32}"),
    ],
)
def test_generation_manifest_must_carry_its_directory_data_version(
    tmp_path: Path, dir_name: str, manifest_data_version: str
) -> None:
    tree_root = _with_transport_current(tmp_path, prior=None)
    _add_generation(tree_root, dir_name, data_version=manifest_data_version, payload=b"posing")
    archive, digest = _archive_for(tree_root, tmp_path)

    with pytest.raises(VendorError, match="manifest carries dataVersion"):
        vendor_atlas_tree(tmp_path / "dist", sha256=digest, archive_path=archive)


@pytest.mark.parametrize("manifest_body", [None, "{not json", "[]", '{"dataVersion": 7}'])
def test_prior_generation_without_valid_manifest_fails_closed(
    tmp_path: Path, manifest_body: str | None
) -> None:
    tree_root = _with_transport_current(tmp_path)
    manifest = tree_root / "atlas" / "versions" / "v-prior" / "manifest.json"
    if manifest_body is None:
        manifest.unlink()
    else:
        _write(manifest, manifest_body)
    archive, digest = _archive_for(tree_root, tmp_path)

    with pytest.raises(VendorError, match="generation atlas/versions/v-prior"):
        vendor_atlas_tree(tmp_path / "dist", sha256=digest, archive_path=archive)


@pytest.mark.parametrize("current_dir", ["v-current", f"v-current-transport-{TRANSPORT_HEX}"])
@pytest.mark.parametrize("canonical_prior", [True, False])
def test_valid_transport_prior_counts_as_distinct_generation(
    tmp_path: Path, current_dir: str, canonical_prior: bool
) -> None:
    tree_root = _with_transport_current(
        tmp_path, prior="v-prior" if canonical_prior else None,
        manifest_url=f"versions/{current_dir}/manifest.json",
    )
    alternate_prior = f"v-prior-transport-{'ef' * 32}"
    _add_generation(tree_root, alternate_prior, data_version="v-prior", payload=b"prior-alternate")
    archive, digest = _archive_for(tree_root, tmp_path)

    metrics = vendor_atlas_tree(tmp_path / "dist", sha256=digest, archive_path=archive)

    assert metrics.data_version == "v-current"
    expected = ["v-prior", alternate_prior] if canonical_prior else [alternate_prior]
    assert metrics.prior_versions == expected


def test_canonical_and_alternate_current_with_prior_report_only_the_prior(tmp_path: Path) -> None:
    tree_root = _with_transport_current(tmp_path, manifest_url="versions/v-current/manifest.json")
    archive, digest = _archive_for(tree_root, tmp_path)

    metrics = vendor_atlas_tree(tmp_path / "dist", sha256=digest, archive_path=archive)

    assert metrics.data_version == "v-current"
    assert metrics.prior_versions == ["v-prior"]


@pytest.mark.parametrize("data_version", [f"v-current-transport-{'ab' * 31}", "v-transport-current"])
def test_current_data_version_with_transport_marker_fails(tmp_path: Path, data_version: str) -> None:
    tree_root = _with_transport_current(tmp_path, data_version=data_version)
    archive, digest = _archive_for(tree_root, tmp_path)

    with pytest.raises(VendorError, match="transport suffix"):
        vendor_atlas_tree(tmp_path / "dist", sha256=digest, archive_path=archive)


def test_current_json_pointing_outside_vendored_set_fails(tmp_path: Path) -> None:
    tree_root = _build_two_gen_tree(tmp_path)
    # Point current at a generation that is not present under versions/.
    current_doc = {
        "schema": "atlas-current",
        "schemaVersion": 1,
        "dataVersion": "v-ghost",
        "generatedAt": "2026-07-17T00:00:00+00:00",
        "manifestUrl": "versions/v-ghost/manifest.json",
    }
    _write(
        tree_root / "atlas" / "current.json",
        json.dumps(current_doc, indent=2) + "\n",
    )
    archive, digest = _archive_for(tree_root, tmp_path)

    with pytest.raises(VendorError, match="non-vendored generation"):
        vendor_atlas_tree(tmp_path / "dist", sha256=digest, archive_path=archive)


def test_scale_threshold_extracted_fails(tmp_path: Path) -> None:
    tree_root = _build_two_gen_tree(tmp_path)
    archive, digest = _archive_for(tree_root, tmp_path)
    # Fail threshold of 1 byte forces gate trip on any real extract.
    with pytest.raises(VendorError, match="scale gate: extracted size"):
        vendor_atlas_tree(
            tmp_path / "dist",
            sha256=digest,
            archive_path=archive,
            thresholds={
                "warn_extracted_bytes": 0,
                "fail_extracted_bytes": 1,
                "fail_archive_bytes": 10**12,
                "fail_object_count": 10**9,
            },
        )


def test_scale_threshold_object_count_fails(tmp_path: Path) -> None:
    tree_root = _build_two_gen_tree(tmp_path)
    archive, digest = _archive_for(tree_root, tmp_path)
    with pytest.raises(VendorError, match="scale gate: object count"):
        vendor_atlas_tree(
            tmp_path / "dist",
            sha256=digest,
            archive_path=archive,
            thresholds={
                "warn_extracted_bytes": 10**12,
                "fail_extracted_bytes": 10**12,
                "fail_archive_bytes": 10**12,
                "fail_object_count": 1,
            },
        )


def test_skip_when_no_pin_configured(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    dist = tmp_path / "dist"
    metrics = vendor_atlas_tree(dist, asset_id=None, sha256=None, archive_path=None)
    assert metrics.skipped is True
    assert not (dist / "atlas").exists()
    captured = capsys.readouterr()
    assert SKIP_MESSAGE in captured.out


def test_main_skip_exit_zero(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ATLAS_TREE_ASSET_ID", raising=False)
    monkeypatch.delenv("ATLAS_TREE_SHA256", raising=False)
    monkeypatch.delenv("ATLAS_TREE_ARCHIVE_PATH", raising=False)
    assert main([str(tmp_path / "dist")]) == 0


def test_main_bad_sha_exit_one(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    tree_root = _build_two_gen_tree(tmp_path)
    archive, _digest = _archive_for(tree_root, tmp_path)
    monkeypatch.delenv("ATLAS_TREE_ASSET_ID", raising=False)
    assert main([str(tmp_path / "dist"), "--archive", str(archive), "--sha256", "0" * 64]) == 1


def test_partial_pin_without_source_skips(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # Digest alone without asset id / archive is incomplete → skip (feature flag off).
    metrics = vendor_atlas_tree(tmp_path / "dist", sha256="ab" * 32, archive_path=None, asset_id=None)
    assert metrics.skipped is True
    assert SKIP_MESSAGE in capsys.readouterr().out
