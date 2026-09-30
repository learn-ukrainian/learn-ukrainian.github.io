"""CI gate: BIO preparation capsules and active holds (#4431, #5766).

Fails when a BIO preparation file is deleted, when a changed BIO capsule is not
preparation-ready, when an active hold does not fail closed, or when the
promotion-evidence registry changes a slug that is not on the BIO manifest.

The change range is ``BASE_SHA..HEAD_SHA`` from the event; with no usable base
it is the merge base of ``origin/main`` and the head.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import yaml

from scripts.orchestration import curriculum_readiness as readiness
from scripts.orchestration.preparation_evidence import UniqueKeyLoader, load_manual_evidence

REGISTRY_REL = "curriculum/l2-uk-en/bio/promotion-evidence.yaml"


def is_bio_preparation_path(raw_path: str, manifest_set: set[str]) -> bool:
    path = Path(raw_path)
    parts = path.parts
    wiki_slug = path.name.removesuffix(".sources.yaml") if raw_path.endswith(".sources.yaml") else path.stem
    return (
        parts[:4] == ("curriculum", "l2-uk-en", "plans", "bio")
        or parts[:4] == ("curriculum", "l2-uk-en", "bio", "discovery")
        or raw_path == REGISTRY_REL
        or parts[:3] == ("docs", "research", "bio")
        or (parts[:2] == ("wiki", "figures") and wiki_slug in manifest_set)
    )


def _git_names(base_sha: str, head_sha: str, diff_filter: str) -> set[str]:
    return set(
        subprocess.check_output(
            ["git", "diff", "--no-renames", "--name-only", f"--diff-filter={diff_filter}", base_sha, head_sha],
            text=True,
            timeout=60,
        ).splitlines()
    )


def _show(ref: str, fallback: str) -> str:
    try:
        return subprocess.check_output(["git", "show", ref], text=True, stderr=subprocess.DEVNULL, timeout=60)
    except subprocess.CalledProcessError:
        return fallback


def main() -> None:
    root = Path.cwd()
    base_sha = os.environ.get("BASE_SHA", "")
    head_sha = os.environ.get("HEAD_SHA", "HEAD") or "HEAD"
    if not base_sha or set(base_sha) == {"0"}:
        base_sha = subprocess.check_output(
            ["git", "merge-base", "origin/main", head_sha], text=True, timeout=60
        ).strip()
    changed = _git_names(base_sha, head_sha, "AM")
    deleted = _git_names(base_sha, head_sha, "D")

    _, manifest_slugs = readiness.load_manifest_track(root, "bio")
    manifest_set = set(manifest_slugs)

    deleted_preparation = sorted(path for path in deleted if is_bio_preparation_path(path, manifest_set))
    if deleted_preparation:
        raise SystemExit(f"BIO preparation files may not be deleted: {deleted_preparation}")

    registry_path = root / REGISTRY_REL
    evidence = load_manual_evidence(registry_path, manifest_set)
    active_holds = {slug for slug, gates in evidence.items() if gates.get("hold", {}).get("active") is True}

    changed_slugs = set()
    for raw_path in changed:
        path = Path(raw_path)
        parts = path.parts
        slug = None
        if parts[:4] in (("curriculum", "l2-uk-en", "plans", "bio"), ("curriculum", "l2-uk-en", "bio", "discovery")):
            slug = path.stem
        elif parts[:3] == ("docs", "research", "bio"):
            slug = path.stem
            base_text = _show(f"{base_sha}:{raw_path}", "")
            try:
                head_text = (root / raw_path).read_text(encoding="utf-8")
            except OSError:
                head_text = ""
            if readiness.is_host_path_only_text_change(base_text, head_text):
                continue
        elif parts[:2] == ("wiki", "figures"):
            slug = path.name.removesuffix(".sources.yaml") if raw_path.endswith(".sources.yaml") else path.stem
        if slug in manifest_set:
            changed_slugs.add(slug)

    if REGISTRY_REL in changed:
        base_registry = yaml.load(
            _show(f"{base_sha}:{REGISTRY_REL}", "version: 1\nentries: {}\n"), Loader=UniqueKeyLoader
        )
        head_registry = yaml.load(registry_path.read_text(encoding="utf-8"), Loader=UniqueKeyLoader)
        base_entries = base_registry.get("entries", {})
        head_entries = head_registry.get("entries", {})
        registry_changed_slugs = {
            slug for slug in set(base_entries) | set(head_entries) if base_entries.get(slug) != head_entries.get(slug)
        }
        off_manifest_changes = registry_changed_slugs - manifest_set
        if off_manifest_changes:
            raise SystemExit(f"promotion evidence changed off-manifest slugs: {sorted(off_manifest_changes)}")
        changed_slugs.update(registry_changed_slugs)

    for slug in sorted(active_holds | changed_slugs, key=manifest_slugs.index):
        result = readiness.evaluate_preparation("bio", slug, repo_root=root)
        finding_ids = {finding["id"] for finding in result["findings"]}
        if slug in active_holds:
            if result["next_action"] != "stop" or "PREPARATION_HOLD_ACTIVE" not in finding_ids:
                raise SystemExit(f"active hold does not fail closed for {slug}")
            continue
        failed = [item["id"] for item in result["requirements"] if not item["passed"]]
        if failed:
            raise SystemExit(f"changed BIO capsule is not preparation-ready: {slug}: {failed}")

    print(
        f"BIO preparation PASS: entries={len(evidence)} "
        f"changed_slugs={len(changed_slugs)} active_holds={len(active_holds)}"
    )


if __name__ == "__main__":
    main()
