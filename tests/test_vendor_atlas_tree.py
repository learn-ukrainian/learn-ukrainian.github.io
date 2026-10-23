"""Tests for deploy-time Atlas tree vendoring (PR3 D1 / R1 / R7)."""

from __future__ import annotations

import gzip
import json
import re
import zipfile
from pathlib import Path

import pytest

from scripts.deploy.vendor_atlas_tree import (
    TREE_MANIFEST_REL,
    VendorError,
    build_archive_from_tree,
    sha256_hex,
    vendor_atlas_tree,
)


def _write(path: Path, data: bytes | str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, str):
        path.write_text(data, encoding="utf-8")
    else:
        path.write_bytes(data)


def _replace_runtime_shard(version_root: Path, family: str, shard_id: str, rows: list[dict]) -> None:
    manifest_path = version_root / "manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    schemas = {
        "entries": "atlas-entry-shard",
        "articles": "atlas-search-article-shard",
        "aliases": "atlas-search-alias-shard",
    }
    rel = f"{family if family == 'entries' else 'search/' + family}/{shard_id}.json.gz"
    raw = json.dumps(
        {"schema": schemas[family], "schemaVersion": 1, "dataVersion": manifest["dataVersion"], "records": rows}
    ).encode()
    blob = gzip.compress(raw, mtime=0)
    _write(version_root / rel, blob)
    index = manifest["entries"] if family == "entries" else manifest["search"][family]
    index["shards"][shard_id] = {
        "id": shard_id,
        "url": rel,
        "count": len(rows),
        "bytes": len(blob),
        "uncompressedBytes": len(raw),
        "sha256": sha256_hex(blob),
        "jsonSha256": sha256_hex(raw),
        "encoding": "gzip",
    }
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")


def _mini_generation(root: Path, data_version: str, *, payload: bytes) -> None:
    """Write a minimal versions/<dataVersion>/ tree (manifest + one shard)."""
    version_root = root / "atlas" / "versions" / data_version
    logical_version = data_version.split("-transport-")[0]
    manifest = {
        "schema": "atlas-runtime-manifest",
        "schemaVersion": 1,
        "dataVersion": logical_version,
        "generatedAt": "2026-07-17T00:00:00+00:00",
        "entries": {"tree": {"shardId": "p00-0"}, "shards": {}},
        "search": {"articles": {"tree": {}, "shards": {}}, "aliases": {"tree": {}, "shards": {}}},
        "decks": {"levels": {}},
        "counts": {
            "articles": 1,
            "formRoutes": 0,
            "publicRoutes": 1,
            "searchArticles": 1,
            "searchAliases": 0,
            "entryShards": 1,
        },
    }
    _write(version_root / "manifest.json", json.dumps(manifest))
    _replace_runtime_shard(
        version_root,
        "entries",
        "p00-0",
        [
            {"slug": "unit-article", "kind": "article", "fixturePayload": payload.hex()},
        ],
    )
    _replace_runtime_shard(
        version_root,
        "articles",
        "unit",
        [
            {"s": "unit-article", "l": "Unit article", "g": "Unmodified gloss", "r": "Unit", "t": "lemma"},
        ],
    )
    manifest = json.loads((version_root / "manifest.json").read_bytes())
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


@pytest.mark.parametrize("endpoint", ["articles", "aliases"])
@pytest.mark.parametrize("reverse", [False, True])
def test_vendor_preserves_producer_order_instead_of_unicode_order(tmp_path: Path, endpoint: str, reverse: bool) -> None:
    """#11341: raw Unicode ordering misplaces ґ; comparator ties must stay deterministic."""
    tree = _build_two_gen_tree(tmp_path)
    version = tree / "atlas/versions/v-current"
    # Existing generator-test heads straddle Г/Ґ/Д and include stable article ties.
    heads = ["ґанок", "дім", "ґазда", "гетьман", "кава", "ґанок"]
    slugs = ["z-porch", "house", "host", "hetman", "coffee", "a-porch"]
    articles = [
        {"s": slug, "l": head, "g": "gloss", "r": f"row-{i}", "t": "lemma", "c": "A1"}
        for i, (slug, head) in enumerate(zip(slugs, heads, strict=True))
    ]
    aliases = [
        {"a": head, "s": slug, "h": head, "k": "variant"}
        for slug, head in zip(slugs, heads, strict=True)
    ]
    aliases[0]["k"] = "abbreviation"
    # Uppercase-equivalent synthetic aliases reach the kind tie while keeping
    # normalized alias+target pairs distinct, as the admission guard requires.
    aliases.extend([
        {"a": "ss", "s": "house", "h": "дім", "k": "variant"},
        {"a": "ß", "s": "house", "h": "дім", "k": "abbreviation"},
    ])
    _replace_runtime_shard(version, "entries", "p00-0", [
        {"slug": slug, "kind": "article"} for slug in slugs
    ])
    # Perturb both row order and shard insertion without changing the logical rows.
    ordered = list(reversed(articles)) if reverse else articles
    shards = [("unit", ordered[::2]), ("second", ordered[1::2])]
    if reverse:
        shards.reverse()
    for shard_id, rows in shards:
        _replace_runtime_shard(version, "articles", shard_id, rows)
    _replace_runtime_shard(version, "aliases", "alias", list(reversed(aliases)) if reverse else aliases)
    manifest_path = version / "manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    manifest["counts"].update(articles=6, publicRoutes=6, searchArticles=6, searchAliases=8)
    manifest_path.write_text(json.dumps(manifest))
    pinned = {p.relative_to(tree): p.read_bytes() for p in tree.rglob("*") if p.is_file()}
    archive, digest = _archive_for(tree, tmp_path)
    dist = tmp_path / "dist"
    metrics = vendor_atlas_tree(dist, sha256=digest, archive_path=archive)

    # Literal order from the established producer contract, never its sort helper.
    if endpoint == "articles":
        # generate_search_index.build_article_indexes queries display_head, slug,
        # then stably applies _uk_sort_key; equal heads therefore use slug order.
        expected = [articles[3], articles[2], articles[5], articles[0], articles[1], articles[4]]
        for path in ("lexicon/search-index.json", "api/lexicon/search-index.json"):
            assert json.loads((dist / path).read_bytes()) == expected
    else:
        expected = [aliases[3], aliases[2], aliases[5], aliases[0], aliases[1], aliases[4], aliases[7], aliases[6]]
        assert json.loads((dist / "lexicon/search-aliases.json").read_bytes()) == expected
    assert metrics.search_parity["articles"] == 6
    assert metrics.search_parity["aliases"] == 8
    for field in ("advertisedOnly", "runtimeOnly"):
        assert metrics.search_parity[field] == []
    for field in ("articleDuplicates", "runtimeDuplicates", "aliasDuplicates"):
        assert metrics.search_parity[field] == 0
    for rel, blob in pinned.items():
        assert (dist / rel).read_bytes() == blob


@pytest.mark.parametrize("gloss, expected", [
    ("avoid: наступний", "примітка Атласу: радять «наступний»; обсяг застереження не встановлено"),
    ("1. first meaning 2. second meaning", "first meaning"),
    ("first meaning… quoted fragment... later", "first meaning"),
    ("while reading", "while reading"),
])
@pytest.mark.parametrize("parent_case", ["vesum", "dictionary", "unsourced", "conflict", "unbound-label"])
@pytest.mark.parametrize("projected_runtime", [False, True])
def test_vendor_preserves_public_gloss_and_sourced_gerund_backlink(
    tmp_path: Path, gloss: str, expected: str, parent_case: str, projected_runtime: bool,
) -> None:
    """B1: raw pinned glosses and missing p must not regress public search semantics."""
    from scripts.audit.generate_search_index import build_index

    tree = _build_two_gen_tree(tmp_path)
    version = tree / "atlas/versions/v-current"
    entry = {
        "lemma": "читаючи", "url_slug": "unit-article", "gloss": gloss,
        "primary_source": "built_vocabulary",
        "enrichment": {"morphology": {"source": "VESUM", "pos": "advp", "paradigm": {"verb": "читати"}}},
    }
    if parent_case == "unsourced":
        entry["enrichment"]["morphology"]["source"] = "manual"
    if parent_case == "unbound-label":
        entry["enrichment"]["heritage"] = {"classification": "historical"}
    if parent_case in {"dictionary", "conflict"}:
        definition = "Дієприсл. до читати." if parent_case == "dictionary" else "Дієприсл. до працювати."
        if parent_case == "dictionary":
            entry["enrichment"] = {}
        entry["enrichment"]["meaning"] = {"source": "словник", "definitions": [definition]}
    parent = "читати" if parent_case in {"vesum", "dictionary", "unbound-label"} else None
    established = build_index([entry])[0]
    _replace_runtime_shard(version, "entries", "p00-0", [{"slug": "unit-article", "kind": "article", "entry": entry}])
    _replace_runtime_shard(version, "articles", "unit", [
        {"s": "unit-article", "l": "читаючи", "g": established["g"] if projected_runtime else gloss,
         "r": "chytaiuchy", "t": "lemma", "p": "unproven", "cls": "avoid"},
    ])
    frozen = {p.relative_to(tree): p.read_bytes() for p in tree.rglob("*") if p.is_file()}
    archive, digest = _archive_for(tree, tmp_path)
    dist = tmp_path / "dist"
    vendor_atlas_tree(dist, sha256=digest, archive_path=archive)
    for endpoint in ("lexicon/search-index.json", "api/lexicon/search-index.json"):
        row, = json.loads((dist / endpoint).read_bytes())
        assert row["g"] == established["g"] == expected
        assert row.get("p") == established.get("p") == parent
        assert row.get("cls") == established.get("cls") is None
        assert row["s"] == "unit-article"
    manifest = json.loads((dist / "lexicon/search-shards.json").read_bytes())
    for desc in manifest["shards"].values():
        row, = json.loads((dist / desc["path"].lstrip("/")).read_bytes())
        assert (row["g"], row.get("p")) == (expected, parent)
    for path, blob in frozen.items():
        assert (dist / path).read_bytes() == blob


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


def test_vendoring_replaces_equal_count_different_search_set_from_exact_pin(tmp_path: Path) -> None:
    """#11341: independent DB search survives a later runtime install on the old producer.

    Faithful minimal reproducer: stale search advertises an absent slug and omits
    a runtime article, while totals match. Actual captured input fingerprints:
    search 007b8c01bd91f32efcd72432dd91538d77af48b858e82d6df3e08ef4b29421d7;
    runtime manifest 626906d480dd33beeab29d64d2a76796d82a6a05f3ffee241182895d2b3ca1e0.
    That full replay has 340 advertised-only and 1 runtime-only articles. These
    synthetic English rows reproduce the producing sequence without lexical edits.
    """
    tree = _with_transport_current(tmp_path)
    version = tree / "atlas/versions" / f"v-current-transport-{TRANSPORT_HEX}"
    article = {"s": "runtime-only", "l": "Runtime only", "g": "Keep exactly.", "r": "Runtime", "t": "lemma"}
    _replace_runtime_shard(
        version,
        "entries",
        "p00-0",
        [
            {"slug": "runtime-only", "kind": "article"},
            {"slug": "separate-form", "kind": "form_route"},
        ],
    )
    _replace_runtime_shard(version, "articles", "unit", [article])
    # Article search legitimately replicates an identical row across prefix leaves.
    _replace_runtime_shard(version, "articles", "other-prefix", [article])
    alias = {"a": "Separate alias", "s": "runtime-only", "h": "Runtime only", "k": "variant"}
    frozen_input = {
        "advertised": [{"s": "advertised-only"}],
        "runtime_articles": [article],
        "form_routes": ["separate-form"],
        "aliases": [alias],
    }
    input_bytes = json.dumps(frozen_input, sort_keys=True, separators=(",", ":")).encode()
    assert sha256_hex(input_bytes) == "b576c4027df953807917460837eae79a423b554af5a75a78fa9f7c74f7919793"
    _replace_runtime_shard(version, "aliases", "alias", [alias])
    manifest_path = version / "manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    manifest["counts"].update(formRoutes=1, publicRoutes=2, searchAliases=1)
    manifest_path.write_text(json.dumps(manifest))
    pinned_files = {p.relative_to(tree): p.read_bytes() for p in tree.rglob("*") if p.is_file()}
    archive, digest = _archive_for(tree, tmp_path)
    dist = tmp_path / "dist"
    _write(dist / "lexicon/search-index.json", '[{"s":"advertised-only"}]')
    _write(dist / "api/lexicon/search-index.json", '[{"s":"advertised-only"}]')
    _write(dist / "lexicon/search-aliases.json", '[{"a":"Old alias","s":"advertised-only"}]')

    _write(dist / "lexicon/search/obsolete.json", '[{"s":"advertised-only"}]')
    metrics = vendor_atlas_tree(dist, sha256=digest, archive_path=archive)

    assert not (dist / "lexicon/search/obsolete.json").exists()
    rows = json.loads((dist / "lexicon/search-index.json").read_bytes())
    assert rows == [article]
    assert (dist / "api/lexicon/search-index.json").read_bytes() == (dist / "lexicon/search-index.json").read_bytes()
    assert json.loads((dist / "lexicon/search-aliases.json").read_bytes()) == [alias]
    shard_manifest = json.loads((dist / "lexicon/search-shards.json").read_bytes())
    assert shard_manifest["total"] == 1
    assert shard_manifest["fullIndex"]["sha256"] == sha256_hex((dist / "lexicon/search-index.json").read_bytes())
    for desc in shard_manifest["shards"].values():
        blob = (dist / desc["path"].lstrip("/")).read_bytes()
        assert sha256_hex(blob) == desc["sha256"]
        assert json.loads(blob) == [article]
    assert metrics.search_parity["advertisedOnly"] == []
    assert metrics.search_parity["runtimeOnly"] == []
    assert metrics.search_parity["articleDuplicates"] == 0
    assert metrics.search_parity["runtimeDuplicates"] == 0
    assert metrics.search_parity["formRoutes"] == 1
    assert metrics.search_parity["aliases"] == 1
    assert metrics.search_parity["replicatedArticleRows"] == 1
    assert metrics.search_parity["runtimeManifestSha256"] == sha256_hex(manifest_path.read_bytes())
    for rel, blob in pinned_files.items():
        assert (dist / rel).read_bytes() == blob


def test_release_asset_entrypoint_projects_search_and_emits_pin_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The release-download entrypoint must obey the same pinned search gate as local archives."""
    from scripts.deploy import vendor_atlas_tree as vendor

    archive, digest = _archive_for(_build_two_gen_tree(tmp_path), tmp_path)

    def download(asset_id: str, *, repo: str, token: str | None) -> bytes:
        assert asset_id == "42"
        assert repo == "fixture/runtime"
        assert token is None
        return archive.read_bytes()

    monkeypatch.setattr(vendor, "download_release_asset", download)
    dist = tmp_path / "dist"
    metrics = vendor.vendor_atlas_tree(dist, sha256=digest, asset_id="42", repo="fixture/runtime")
    rows = json.loads((dist / "lexicon/search-index.json").read_bytes())
    assert [row["s"] for row in rows] == ["unit-article"]
    assert metrics.archive_sha256 == digest
    assert metrics.search_parity["articles"] == 1
    receipt = capsys.readouterr().out
    assert f"archive_sha256={digest}" in receipt
    assert "asset_id=42" in receipt
    assert "search_parity=" + json.dumps(metrics.search_parity, sort_keys=True) in receipt


@pytest.mark.parametrize(
    "defect",
    [
        "equal-count-different-set",
        "missing-search",
        "extra-search",
        "duplicate-entry",
        "duplicate-search",
        "conflicting-replica",
        "alias-targets-form",
        "duplicate-alias",
        "unknown-kind",
    ],
)
def test_incoherent_pin_is_rejected_before_dist_mutation(tmp_path: Path, defect: str) -> None:
    """Bad membership, duplicates and aliases cannot be hidden by matching totals."""
    tree = _build_two_gen_tree(tmp_path)
    version = tree / "atlas/versions/v-current"
    row = {"s": "unit-article", "l": "Unit", "g": None, "r": "Unit", "t": "lemma"}
    if defect == "equal-count-different-set":
        _replace_runtime_shard(version, "articles", "unit", [{**row, "s": "absent"}])
    elif defect == "missing-search":
        _replace_runtime_shard(version, "articles", "unit", [])
    elif defect == "extra-search":
        _replace_runtime_shard(version, "articles", "unit", [row, {**row, "s": "absent"}])
    elif defect == "duplicate-entry":
        _replace_runtime_shard(version, "entries", "extra", [{"slug": "unit-article", "kind": "article"}])
    elif defect == "duplicate-search":
        _replace_runtime_shard(version, "articles", "unit", [row, row])
    elif defect == "conflicting-replica":
        _replace_runtime_shard(version, "articles", "extra", [{**row, "g": "conflict"}])
    elif defect == "alias-targets-form":
        _replace_runtime_shard(version, "entries", "extra", [{"slug": "form", "kind": "form_route"}])
        _replace_runtime_shard(version, "aliases", "alias", [{"a": "Alias", "s": "form", "h": "Form", "k": "variant"}])
    elif defect == "duplicate-alias":
        alias = {"a": "Alias", "s": "unit-article", "h": "Unit", "k": "variant"}
        _replace_runtime_shard(version, "aliases", "alias", [alias, alias])
    else:
        _replace_runtime_shard(version, "entries", "p00-0", [{"slug": "unit-article", "kind": "unknown"}])
    archive, digest = _archive_for(tree, tmp_path)
    dist = tmp_path / "dist"
    _write(dist / "atlas/sentinel", "old runtime")
    _write(dist / "lexicon/search-index.json", "old search")
    with pytest.raises(VendorError):
        vendor_atlas_tree(dist, sha256=digest, archive_path=archive)
    assert (dist / "atlas/sentinel").read_text() == "old runtime"
    assert (dist / "lexicon/search-index.json").read_text() == "old search"


@pytest.mark.parametrize(
    "field,value",
    [
        ("url", "../../../../outside.json.gz"),
        ("url", "/outside.json.gz"),
        ("sha256", "0" * 64),
        ("jsonSha256", "0" * 64),
        ("bytes", 1),
        ("uncompressedBytes", 1),
        ("count", 99),
        ("encoding", "plain"),
    ],
)
def test_runtime_descriptor_fault_fails_before_install(tmp_path: Path, field: str, value: object) -> None:
    """Runtime-derived search cannot follow escaping paths or unchecked descriptors."""
    tree = _build_two_gen_tree(tmp_path)
    path = tree / "atlas/versions/v-current/manifest.json"
    manifest = json.loads(path.read_bytes())
    manifest["search"]["articles"]["shards"]["unit"][field] = value
    path.write_text(json.dumps(manifest))
    archive, digest = _archive_for(tree, tmp_path)
    dist = tmp_path / "dist"
    with pytest.raises(VendorError):
        vendor_atlas_tree(dist, sha256=digest, archive_path=archive)
    assert not dist.exists()


@pytest.mark.parametrize(
    "defect",
    [
        "foreign-version",
        "foreign-schema",
        "unsupported-schema-version",
        "non-array-records",
        "non-object-row",
        "invalid-search-row",
        "invalid-slug",
        "truncated-gzip",
        "invalid-json",
        "manifest-schema",
        "manifest-count",
        "negative-inflated-size",
    ],
)
def test_pinned_runtime_protocol_fault_is_not_published(tmp_path: Path, defect: str) -> None:
    """A valid outer pin does not excuse a malformed runtime protocol or row."""
    tree = _build_two_gen_tree(tmp_path)
    version = tree / "atlas/versions/v-current"
    manifest_path = version / "manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    desc = manifest["search"]["articles"]["shards"]["unit"]
    shard_path = version / desc["url"]
    raw = gzip.decompress(shard_path.read_bytes())
    payload = json.loads(raw)
    if defect == "foreign-version":
        payload["dataVersion"] = "another-runtime"
    elif defect == "foreign-schema":
        payload["schema"] = "atlas-search-alias-shard"
    elif defect == "unsupported-schema-version":
        payload["schemaVersion"] = 2
    elif defect == "non-array-records":
        payload["records"] = {}
    elif defect == "non-object-row":
        payload["records"] = [None]
    elif defect == "invalid-search-row":
        payload["records"][0]["l"] = None
    elif defect == "invalid-slug":
        payload["records"][0]["s"] = ""
    elif defect == "manifest-schema":
        manifest["schema"] = "other"
    elif defect == "manifest-count":
        manifest["counts"]["searchArticles"] = 99
    elif defect == "negative-inflated-size":
        desc["uncompressedBytes"] = -1
    raw = b"not-json" if defect == "invalid-json" else json.dumps(payload).encode()
    blob = gzip.compress(raw, mtime=0)
    if defect == "truncated-gzip":
        blob = blob[:-5]
    shard_path.write_bytes(blob)
    desc.update(bytes=len(blob), sha256=sha256_hex(blob), jsonSha256=sha256_hex(raw))
    if defect != "negative-inflated-size":
        desc["uncompressedBytes"] = len(raw)
    manifest_path.write_text(json.dumps(manifest))
    archive, digest = _archive_for(tree, tmp_path)
    dist = tmp_path / "dist"
    with pytest.raises(VendorError):
        vendor_atlas_tree(dist, sha256=digest, archive_path=archive)
    assert not dist.exists()
