#!/usr/bin/env python3
"""Prepare or replay an Atlas release from separately hydrated committed inputs."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.deploy import runtime_source_report as report


class ReleaseError(ValueError):
    """A release cannot be reproduced or its source evidence is incomplete."""


def _fresh_directory(path: Path) -> None:
    resolved = path.resolve()
    if resolved == report.ROOT or report.ROOT in resolved.parents:
        raise ReleaseError("release scratch must be outside the worktree")
    if path.is_symlink() or any(parent.is_symlink() for parent in path.parents):
        raise ReleaseError("release scratch must not traverse symlinks")
    path.mkdir(parents=True, exist_ok=True)
    if any(path.iterdir()):
        raise ReleaseError("release scratch must be fresh and empty")


def prepare_release(*, work: Path, prior_archive: Path, prior_sha256: str, out: Path,
                    manifest_path: Path = report.MANIFEST,
                    deck_dir: Path = report.ROOT / "site/public/lexicon",
                    pointer_dir: Path = report.POINTER_DIR) -> dict[str, Any]:
    """Build one candidate without downloads, enrichment, pin changes or guard overrides."""
    from scripts.atlas.atlas_db import migrate_manifest, validate_alias_targets
    from scripts.atlas.export_runtime_shards import export_runtime_shards
    from scripts.audit import generate_search_index as search
    from scripts.deploy.vendor_atlas_tree import build_pinned_search, vendor_atlas_tree
    from scripts.lexicon.runner.finalize import build_publication_archive

    _fresh_directory(work)
    _fresh_directory(out)
    if work.resolve() == out.resolve() or work.resolve() in out.resolve().parents or out.resolve() in work.resolve().parents:
        raise ReleaseError("work and out must be separate fresh directories")
    binding = report.source_binding(manifest_path, pointer_dir=pointer_dir, deck_dir=deck_dir)
    holds = report.file_digest(report.HOLDS)
    source = work / "source"
    source.mkdir()
    manifest = source / "manifest.json"
    shutil.copyfile(manifest_path, manifest)
    decks = source / "public/lexicon"
    decks.mkdir(parents=True)
    for name in binding["deck_sha256"]:
        shutil.copyfile(deck_dir / name, decks / name)
    # No public/api/lexicon exists here, so the exporter's established lookup
    # cannot consume an ambient API deck instead of the validated public deck.
    if report.source_binding(manifest, pointer_dir=pointer_dir, deck_dir=decks) != binding:
        raise ReleaseError("source changed while copying")
    db = work / "atlas.db"
    migrate_manifest(manifest, db)
    validate_alias_targets(db)
    db_rows, _, _ = search.build_atlas_db_search_artifacts(db)

    prior_dist = work / "prior"
    prior_metrics = vendor_atlas_tree(prior_dist, archive_path=prior_archive, sha256=prior_sha256)
    if prior_metrics.skipped:
        raise ReleaseError("prior verification was skipped")
    prior_current = json.loads((prior_dist / "atlas/current.json").read_bytes())
    # vendor_atlas_tree has already validated this exact manifestUrl, including
    # its transport suffix. Keep the pointed directory's name and bytes.
    prior_directory = Path(prior_current["manifestUrl"]).parent.name
    tree = work / "tree"
    shutil.copytree(prior_dist / "atlas/versions" / prior_directory, tree / "atlas/versions" / prior_directory)
    prior = {"archive_sha256": prior_metrics.archive_sha256,
             "dataVersion": prior_current["dataVersion"],
             "runtimeManifestSha256": prior_metrics.search_parity["runtimeManifestSha256"],
             "manifestUrl": prior_current["manifestUrl"]}
    export_runtime_shards(db_path=db, out_dir=tree, base_path="atlas", deck_dir=decks, verify=True)
    candidate = work / "atlas-tree.zip"
    digest = build_publication_archive(tree, candidate)
    verified = work / "verified"
    metrics = vendor_atlas_tree(verified, archive_path=candidate, sha256=digest)
    if metrics.skipped:
        raise ReleaseError("candidate verification was skipped")
    rows, aliases, parity = build_pinned_search(verified)
    projected = report.membership([row["s"] for row in rows])
    raw = report.membership([*[row["s"] for row in rows], *parity["withheldArticles"]])
    if raw != report.membership([row["s"] for row in db_rows]) or raw["count"] != parity["articles"]:
        raise ReleaseError("runtime source membership mismatch")
    if projected["count"] != parity["projectedArticles"]:
        raise ReleaseError("runtime projection count mismatch")

    data_dir = work / "projection/data"
    browse_dir = work / "projection/public/lexicon/browse"
    meta, browse_shards, flagged = search.build_browse_outputs(rows)
    shards, shard_rows = search.build_search_shards(rows)
    search.write_index(rows, data_dir / search.DEFAULT_SEARCH_OUT.name)
    search.write_aliases(aliases, data_dir / search.DEFAULT_SEARCH_ALIASES_OUT.name)
    search.write_search_shards(shards, shard_rows, data_dir / search.DEFAULT_SEARCH_SHARDS_OUT.name,
                               work / "projection/public/lexicon/search")
    search.write_browse_outputs(meta, browse_shards, flagged, data_dir / search.DEFAULT_BROWSE_META_OUT.name,
                                data_dir / search.DEFAULT_BROWSE_FLAGGED_OUT.name, browse_dir)
    search.verify_browse_artifacts_written(data_dir / search.DEFAULT_BROWSE_META_OUT.name, browse_dir, meta["total"])
    # Reuse the canonical artifact digest contract; these on-disk outputs also
    # let independent release proof compare full files without a payload walk.
    search.pinned_set_digests(data_dir, browse_dir)
    receipt = report.validate_receipt({
        "schema": "atlas-runtime-release.v1", "source": binding, "holds_sha256": holds,
        "archive_sha256": digest, "prior": prior,
        "runtime": {key: parity[key] for key in ("dataVersion", "runtimeManifestSha256")},
        "raw": raw, "projected": projected,
    })
    if (binding != report.source_binding(manifest_path, pointer_dir=pointer_dir, deck_dir=deck_dir)
            or binding != report.source_binding(manifest, pointer_dir=pointer_dir, deck_dir=decks)
            or holds != report.file_digest(report.HOLDS)
            or prior_sha256 != report.file_digest(prior_archive)
            or digest != report.file_digest(candidate)):
        raise ReleaseError("input_drift")
    shutil.copyfile(candidate, out / "atlas-tree.zip")
    if report.file_digest(out / "atlas-tree.zip") != digest:
        raise ReleaseError("input_drift")
    (out / report.RECEIPT.name).write_bytes(report.canonical_bytes(receipt))
    return receipt


def verify_release(*, receipt_path: Path = report.RECEIPT, **kwargs: Any) -> dict[str, Any]:
    reference = report.read_receipt(receipt_path)
    reference_bytes = report.canonical_bytes(reference)
    if kwargs["prior_sha256"] != reference["prior"]["archive_sha256"]:
        raise ReleaseError("prior identity mismatch")
    actual = prepare_release(**kwargs)
    if actual["source"] != reference["source"] or actual["holds_sha256"] != reference["holds_sha256"]:
        raise ReleaseError("input_drift")
    if actual["prior"] != reference["prior"]:
        raise ReleaseError("prior identity mismatch")
    if actual["archive_sha256"] != reference["archive_sha256"]:
        raise ReleaseError("nondeterministic_export")
    if report.canonical_bytes(actual) != reference_bytes:
        raise ReleaseError("receipt replay mismatch")
    if receipt_path.read_bytes() != reference_bytes:
        raise ReleaseError("input_drift")
    return actual


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Prepare or replay a source-bound Atlas runtime release.\n"
                    "Use after hydrating the committed manifest/deck; this never downloads or publishes.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  .venv/bin/python scripts/deploy/prepare_atlas_runtime_release.py prepare --work ./scratch/work --prior-archive ./prior.zip --prior-sha256 <64hex> --out ./scratch/out
  .venv/bin/python scripts/deploy/prepare_atlas_runtime_release.py verify --work ./scratch/replay --prior-archive ./prior.zip --prior-sha256 <64hex> --out ./scratch/verified
Outputs: atlas-tree.zip and atlas-runtime-release.json in --out; fresh DB, verified trees and projection in --work.
Scratch directories must be fresh, outside the worktree. Hydration and prior acquisition are separate.
Exit codes: 0 verified; 1 source, certification, vendor or reproducibility refusal; 2 usage error.
Related: docs/runbooks/word-atlas-static-api.md; #12596.
""")
    parser.add_argument("command", choices=("prepare", "verify"), help="prepare a candidate, or replay the tracked receipt")
    parser.add_argument("--work", type=Path, required=True, help="Fresh scratch directory outside the worktree, e.g. ../scratch/work")
    parser.add_argument("--prior-archive", type=Path, required=True, help="Local immutable prior ZIP, e.g. ../prior.zip; never modified")
    parser.add_argument("--prior-sha256", required=True, help="Expected prior ZIP SHA-256, 64 lowercase hexadecimal characters")
    parser.add_argument("--out", type=Path, required=True, help="Separate fresh output directory outside the worktree, e.g. ../scratch/out")
    parser.add_argument("--manifest", type=Path, default=report.MANIFEST, help="Hydrated manifest JSON (default: site/src/data/lexicon-manifest.json)")
    parser.add_argument("--deck-dir", type=Path, default=report.ROOT / "site/public/lexicon", help="Hydrated practice decks (default: site/public/lexicon)")
    parser.add_argument("--receipt", type=Path, default=report.RECEIPT, help="Reference for verify (default: registry/lexicon/atlas-runtime-release.json)")
    args = parser.parse_args(argv)
    kwargs = {"work": args.work, "prior_archive": args.prior_archive, "prior_sha256": args.prior_sha256,
              "out": args.out, "manifest_path": args.manifest, "deck_dir": args.deck_dir}
    try:
        if args.command == "verify":
            result = verify_release(receipt_path=args.receipt, **kwargs)
        else:
            result = prepare_release(**kwargs)
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as exc:
        print(f"Atlas runtime release refused: {exc}", file=sys.stderr)
        return 1
    print(report.canonical_bytes(result).decode().rstrip("\n"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
