#!/usr/bin/env python3
"""Build and verify the sealed inventory of old-plan trainable artifacts (#9607, plan v3.4.3 PA1).

The inventory lists every quarantined artifact with its repo-relative path, byte
count, SHA-256 and the reason it is sealed. The guard that refuses these paths
lives in ``paths.py`` (``refuse_quarantined``); this module only records and
re-checks what is sealed. Nothing here moves or deletes data.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from scripts.projects.open_model_data.paths import (
    LOGICAL_OPEN_MODEL_PREFIX,
    QUARANTINE_INVENTORY_PATH,
    QUARANTINE_INVENTORY_SCHEMA,
    REGISTRY_OPEN_MODEL_DATA_DIR,
    REGISTRY_OPEN_MODEL_PREFIX,
    REPO_ROOT,
    TOMBSTONE_NAME,
)

ARTIFACT_MANIFEST_GLOB = "registry/artifacts/open_model_*.manifest.json"


@dataclass(frozen=True)
class QuarantineSet:
    """One sealed set: open-model relative path prefixes and why they are sealed."""

    set_id: str
    prefixes: tuple[str, ...]
    reason: str


# Most specific prefix wins. Every inventoried artifact must match exactly one set.
QUARANTINE_SETS: tuple[QuarantineSet, ...] = (
    QuarantineSet(
        "archive-uldr-v1-production",
        ("archive/uldr_v1_production/",),
        "uldr_v1 decolonization release, archived before the restart; training on it dropped format validity "
        "from 100% to 2.8% because the model copied its templated reasoning (#8338).",
    ),
    QuarantineSet(
        "archive-historical",
        ("archive/quarantined_historical/",),
        "Kyivan Rus and Middle Ukrainian sets (uldr_v04a/v04b), quarantined before the restart; historical text "
        "is out of the plan's scope.",
    ),
    QuarantineSet(
        "decolonization-gold-seeds",
        ("decolonization/seeds/",),
        "Gold seeds of the v1 decolonization pipeline (150 DPO pairs, 150 trajectories) in the templated "
        "reasoning format that #8338 measured as harmful; plan principle P1 forbids written reasoning text.",
    ),
    QuarantineSet(
        "decolonization-v1-pipeline",
        ("decolonization/",),
        "Intermediates of the uldr_v1 decolonization pipeline (generated, mined, partitions, stem controls, "
        "consumer formats) carrying script-written reasoning (#8338); plan principle P1 forbids it.",
    ),
    QuarantineSet(
        "pilot-canary",
        ("canary/",),
        "Pilot canary data, adapter and log built from v1 decolonization data; withdrawn 2026-09-25 after "
        "failing the dataset acceptance check.",
    ),
    QuarantineSet(
        "component-decolonization",
        ("components/decolonization/",),
        "Decolonization component of the withdrawn plan (250 cases, reviews, review sample); plan v3.4.3 PA1 "
        "seals it before any component is rebuilt from human sources.",
    ),
    QuarantineSet(
        "component-grammar",
        ("components/grammar/",),
        "Grammar component of the withdrawn plan (17 case families, shards, review sample); plan v3.4.3 PA1 "
        "seals it and rebuilds C1 from aligned UA-GEC pairs.",
    ),
    QuarantineSet(
        "release-uldr-v03-dialect",
        ("release/uldr_v03_dialect/",),
        "Dialect-protection release; the dialect component is closed as out of scope (#8141).",
    ),
    QuarantineSet(
        "release-uldr-v05-grammar-valency",
        ("release/uldr_v05_grammar_valency/",),
        "Tombstoned 2026-09-23 (#8342): 93% controls, 13 templates for all rows, synthetic negatives.",
    ),
    QuarantineSet(
        "release-uldr-v06-general-assistant",
        ("release/uldr_v06_general_assistant/",),
        "School-subject assistant set (#8139) with script-synthesized explanations and reasoning; its redo "
        "(#8341) failed review on 2026-10-03.",
    ),
    QuarantineSet(
        "release-correction-protection-v1",
        ("release/correction_protection_v1/",),
        "Correction and protection release of the withdrawn plan; plan PA7 quarantines the old evaluator "
        "and suites rather than reusing them.",
    ),
    QuarantineSet(
        "study-8338",
        ("study/",),
        "#8338 learning study, acceptance-sample template and real-run outputs; plan PA7 quarantines the old "
        "evaluator and suites rather than reusing them.",
    ),
    QuarantineSet(
        "v4-pipeline-records",
        (
            "custody/",
            "dataset/",
            "detector/",
            "evidence/",
            "extraction/",
            "inventory/",
            "language/",
            "pilot/",
            "profiles/",
            "provenance/",
            "reference/",
            "soviet_candidates/",
            "splits/",
            "trajectories/",
        ),
        "Records and indexes of the withdrawn v4 and phase-3 dataset pipeline; their provenance under the "
        "restart plan is not established, so the PA1 residual policy quarantines them.",
    ),
)

# Tracked record files: every file under these registry directories, plus single files.
TRACKED_SEALED_DIRECTORIES: tuple[str, ...] = (
    "archive",
    "components/decolonization",
    "components/grammar",
    "decolonization/seeds",
    "release/correction_protection_v1",
    "release/uldr_v03_dialect",
    "release/uldr_v05_grammar_valency",
    "release/uldr_v06_general_assistant",
)
TRACKED_SEALED_FILES: tuple[str, ...] = ("study/uldr_v1_acceptance_sample.signoff_template.json",)
# Directories that carry a TOMBSTONE.md seal in the registry (archive/ is sealed by its base).
TOMBSTONED_DIRECTORIES: tuple[str, ...] = tuple(item for item in TRACKED_SEALED_DIRECTORIES if item != "archive")


class InventoryError(RuntimeError):
    """The sealed inventory cannot be built or does not match the artifacts."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1 << 20):
            digest.update(chunk)
    return digest.hexdigest()


def set_for(tail: str) -> QuarantineSet:
    """Return the most specific set whose prefix matches an open-model relative path."""
    matches = [(len(prefix), item) for item in QUARANTINE_SETS for prefix in item.prefixes if tail.startswith(prefix)]
    if not matches:
        raise InventoryError(f"no quarantine set covers {tail}; add one with its reason")
    return max(matches, key=lambda match: match[0])[1]


def ignored_manifest_entries(repo: Path = REPO_ROOT) -> list[dict[str, Any]]:
    """Return the git-ignored open-model artifacts recorded by the verified artifact store."""
    entries: list[dict[str, Any]] = []
    for manifest in sorted(repo.glob(ARTIFACT_MANIFEST_GLOB)):
        entries.extend(json.loads(manifest.read_text(encoding="utf-8"))["entries"])
    if not entries:
        raise InventoryError(f"no open-model artifact manifests under {repo}")
    return entries


def tracked_record_paths(repo: Path = REPO_ROOT) -> list[str]:
    """Return tracked registry record files that the quarantine seals."""
    pathspecs = [f"{REGISTRY_OPEN_MODEL_PREFIX}/{item}" for item in TRACKED_SEALED_DIRECTORIES]
    pathspecs += [f"{REGISTRY_OPEN_MODEL_PREFIX}/{item}" for item in TRACKED_SEALED_FILES]
    output = subprocess.run(
        ["git", "ls-files", "-z", "--", *pathspecs],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
        timeout=60,
    ).stdout
    paths = sorted(item for item in output.split("\0") if item)
    # The seals are not artifacts; they are written by this step and are excluded from the inventory.
    return [path for path in paths if Path(path).name != TOMBSTONE_NAME]


def build_inventory(*, data_root: Path, repo: Path = REPO_ROOT) -> dict[str, Any]:
    """Hash every quarantined artifact; the ignored files are read from ``data_root`` read-only."""
    artifacts: list[dict[str, Any]] = []
    on_disk = {
        path.relative_to(data_root).as_posix()
        for path in (data_root / LOGICAL_OPEN_MODEL_PREFIX).rglob("*")
        if path.is_file()
    }
    manifest_entries = ignored_manifest_entries(repo)
    recorded = {entry["path"] for entry in manifest_entries}
    if on_disk != recorded:
        raise InventoryError(
            f"ignored files differ from the artifact manifests: {len(on_disk - recorded)} unrecorded, "
            f"{len(recorded - on_disk)} missing"
        )
    for entry in sorted(manifest_entries, key=lambda item: item["path"]):
        path = data_root / entry["path"]
        digest = sha256_file(path)
        size = path.stat().st_size
        if digest != entry["sha256"] or size != entry["size"]:
            raise InventoryError(f"{entry['path']} differs from its artifact manifest")
        artifacts.append(_artifact(entry["path"], "ignored", size, digest))
    for relative in tracked_record_paths(repo):
        path = repo / relative
        artifacts.append(_artifact(relative, "tracked", path.stat().st_size, sha256_file(path)))
    return {
        "schema": QUARANTINE_INVENTORY_SCHEMA,
        "issue": 9607,
        "plan": "docs/projects/open-model-data/PLAN.md v3.4.3, gate PA1",
        "policy": "Sealed and kept. No loader, packager or uploader may open these artifacts; nothing is deleted.",
        "totals": _totals(artifacts),
        "sets": [
            {"id": item.set_id, "prefixes": list(item.prefixes), "reason": item.reason} for item in QUARANTINE_SETS
        ],
        "tombstoned_directories": [f"{REGISTRY_OPEN_MODEL_PREFIX}/{item}" for item in TOMBSTONED_DIRECTORIES],
        "artifacts": artifacts,
    }


def _artifact(path: str, storage: str, size: int, digest: str) -> dict[str, Any]:
    tail = path.split("/open_model_data/", 1)[1]
    sealed = set_for(tail)
    return {
        "path": path,
        "storage": storage,
        "bytes": size,
        "sha256": digest,
        "set": sealed.set_id,
        "reason": sealed.reason,
    }


def _totals(artifacts: list[dict[str, Any]]) -> dict[str, int]:
    totals: dict[str, int] = {}
    for storage in ("ignored", "tracked"):
        selected = [item for item in artifacts if item["storage"] == storage]
        totals[f"{storage}_files"] = len(selected)
        totals[f"{storage}_bytes"] = sum(item["bytes"] for item in selected)
    return totals


def verify_inventory(
    inventory: dict[str, Any], *, repo: Path = REPO_ROOT, data_root: Path | None = None
) -> dict[str, int]:
    """Re-hash tracked artifacts (and ignored ones under ``data_root``); raise on any drift."""
    problems: list[str] = []
    if inventory.get("schema") != QUARANTINE_INVENTORY_SCHEMA:
        problems.append("unexpected inventory schema")
    artifacts = inventory["artifacts"]
    if inventory["totals"] != _totals(artifacts):
        problems.append("inventory totals do not match its artifacts")
    sets = {item.set_id: item.reason for item in QUARANTINE_SETS}
    checked = {"tracked": 0, "ignored": 0, "ignored_absent": 0}
    for entry in artifacts:
        tail = entry["path"].split("/open_model_data/", 1)[1]
        if set_for(tail).set_id != entry["set"] or sets.get(entry["set"]) != entry["reason"]:
            problems.append(f"{entry['path']}: set or reason drift")
        if entry["storage"] == "tracked":
            path = repo / entry["path"]
        elif data_root is not None:
            path = data_root / entry["path"]
        else:
            checked["ignored_absent"] += 1
            continue
        if not path.is_file():
            if entry["storage"] == "tracked":
                problems.append(f"{entry['path']}: tracked artifact missing")
            else:
                checked["ignored_absent"] += 1
            continue
        if path.stat().st_size != entry["bytes"] or sha256_file(path) != entry["sha256"]:
            problems.append(f"{entry['path']}: hash drift")
            continue
        checked[entry["storage"]] += 1
    tracked = {entry["path"] for entry in artifacts if entry["storage"] == "tracked"}
    if tracked != set(tracked_record_paths(repo)):
        problems.append("tracked sealed files differ from the inventory")
    ignored = {entry["path"] for entry in artifacts if entry["storage"] == "ignored"}
    if ignored != {entry["path"] for entry in ignored_manifest_entries(repo)}:
        problems.append("ignored artifacts differ from the artifact manifests")
    for directory in TOMBSTONED_DIRECTORIES:
        if not (REGISTRY_OPEN_MODEL_DATA_DIR / directory / TOMBSTONE_NAME).is_file():
            problems.append(f"{REGISTRY_OPEN_MODEL_PREFIX}/{directory}: tombstone missing")
    if problems:
        raise InventoryError(
            "; ".join(problems[:20]) + (f" (+{len(problems) - 20} more)" if len(problems) > 20 else "")
        )
    return checked


def write_inventory(inventory: dict[str, Any], path: Path = QUARANTINE_INVENTORY_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(inventory, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build or verify the sealed inventory of old-plan open-model artifacts (#9607).\n"
            "Use `verify` to prove nothing drifted; use `build` only to regenerate the inventory after a reviewed change."
        ),
        epilog=(
            "Examples:\n"
            "  .venv/bin/python scripts/projects/open_model_data/quarantine.py verify\n"
            "  .venv/bin/python scripts/projects/open_model_data/quarantine.py verify --data-root <checkout-with-data>\n"
            "  .venv/bin/python scripts/projects/open_model_data/quarantine.py build --data-root <checkout-with-data>\n"
            "Outputs: `build` writes registry/projects/open_model_data/quarantine/inventory_v1.json; `verify` writes nothing.\n"
            "Exit codes: 0 when the inventory matches; 1 on drift or a missing artifact.\n"
            "Related: scripts/projects/open_model_data/paths.py (refuse_quarantined), issue #9607, "
            "docs/projects/open-model-data/PLAN.md (PA1)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="action", required=True)
    build = sub.add_parser("build", help="Hash every quarantined artifact and write the inventory.")
    build.add_argument(
        "--data-root",
        type=Path,
        required=True,
        help="Checkout whose data/projects/open_model_data holds the git-ignored artifacts (read only).",
    )
    verify = sub.add_parser("verify", help="Re-hash the inventory against the artifacts; read only.")
    verify.add_argument(
        "--data-root",
        type=Path,
        default=None,
        help="Checkout holding the git-ignored artifacts; default: check tracked files and manifests only.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.action == "build":
            inventory = build_inventory(data_root=args.data_root.resolve())
            write_inventory(inventory)
            print(json.dumps(inventory["totals"], sort_keys=True))
            return 0
        inventory = json.loads(QUARANTINE_INVENTORY_PATH.read_text(encoding="utf-8"))
        data_root = args.data_root.resolve() if args.data_root is not None else None
        checked = verify_inventory(inventory, data_root=data_root)
    except InventoryError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({"totals": inventory["totals"], "checked": checked}, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
