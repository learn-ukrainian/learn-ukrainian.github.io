"""Recompute dependency staleness from all immutable lesson manifests."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

from scripts.build.fresh.manifest import changed_inputs
from scripts.build.fresh.path_guard import checked_existing_path
from scripts.curriculum.evidence import lock

SCHEMA = Path(__file__).resolve().parents[3] / "schemas" / "module-closure-v1.schema.json"


def compute_closure(level: str, slug: str, lessons: list[dict[str, Any]], *,
                    repo_root: Path, state_dir: Path, site_dir: Path | None = None) -> dict[str, Any]:
    page_dir = checked_existing_path(repo_root, site_dir or repo_root / "site/src/content/docs" / level / slug,
                                     "site/src/content/docs")
    state_dir = checked_existing_path(repo_root, state_dir, "curriculum/l2-uk-en/evidence")
    pages = {item["n"]: checked_existing_path(repo_root, page_dir / f"{item['n']}.mdx",
                                               "site/src/content/docs") for item in lessons}
    hashes = {n: hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
              for n, path in pages.items()}
    rows = []
    stale = []
    for item in lessons:
        n = item["n"]
        pointer = checked_existing_path(repo_root, state_dir / f"lesson-{n}.manifest.yaml",
                                        "curriculum/l2-uk-en/evidence")
        sidecar = checked_existing_path(repo_root, state_dir / f"lesson-{n}.manifest.sha256",
                                        "curriculum/l2-uk-en/evidence")
        current = None
        if pointer.is_file() and sidecar.is_file():
            digest = hashlib.sha256(pointer.read_bytes()).hexdigest()
            if sidecar.read_text(encoding="ascii").strip() == digest:
                current = digest
        rows.append({"n": n, "kind": "recap" if item.get("kind") == "recap" else "lesson", "lesson_sha256": hashes[n],
                     "current_manifest_sha256": current})
        for path in sorted((state_dir / "manifests" / f"lesson-{n}").glob("*.yaml")):
            path = checked_existing_path(repo_root, path, "curriculum/l2-uk-en/evidence")
            content = path.read_bytes()
            digest = hashlib.sha256(content).hexdigest()
            if path.stem != digest:
                raise ValueError(f"manifest history hash mismatch: {path}")
            manifest = yaml.safe_load(content)
            for change in changed_inputs(manifest, repo_root):
                entry = change["entry"]
                record = {"n": n, "manifest_sha256": digest, "input": change["input"], "path": entry["path"],
                          "recorded_sha256": entry["sha256"], "current_sha256": change["current_sha256"]}
                if change["input"] == "upstream_lessons":
                    record["upstream"] = entry["n"]
                stale.append(record)
    doc = {"closure_schema": 1, "level": level, "slug": slug, "lessons": rows, "stale": stale}
    Draft202012Validator(json.loads(checked_existing_path(SCHEMA.parents[1], SCHEMA, "schemas").read_text(
        encoding="utf-8"))).validate(doc)
    lock.atomic_write(checked_existing_path(repo_root, state_dir / "module.closure.yaml",
                                            "curriculum/l2-uk-en/evidence"), lock.yaml_bytes(doc))
    return doc
