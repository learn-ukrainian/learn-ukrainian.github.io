"""Recompute dependency staleness from all immutable lesson manifests."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

from scripts.curriculum.evidence import lock

SCHEMA = Path(__file__).resolve().parents[3] / "schemas" / "module-closure-v1.schema.json"


def compute_closure(level: str, slug: str, lessons: list[dict[str, Any]], *,
                    repo_root: Path, state_dir: Path, site_dir: Path | None = None) -> dict[str, Any]:
    page_dir = site_dir or repo_root / "site/src/content/docs" / level / slug
    pages = {item["n"]: page_dir / f"{item['n']}.mdx" for item in lessons}
    hashes = {n: hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
              for n, path in pages.items()}
    rows = []
    stale = []
    for item in lessons:
        n = item["n"]
        pointer = state_dir / f"lesson-{n}.manifest.yaml"
        sidecar = state_dir / f"lesson-{n}.manifest.sha256"
        current = None
        if pointer.is_file() and sidecar.is_file():
            digest = hashlib.sha256(pointer.read_bytes()).hexdigest()
            if sidecar.read_text(encoding="ascii").strip() == digest:
                current = digest
        rows.append({"n": n, "kind": "recap" if item.get("kind") == "recap" else "lesson", "lesson_sha256": hashes[n],
                     "current_manifest_sha256": current})
        for path in sorted((state_dir / "manifests" / f"lesson-{n}").glob("*.yaml")):
            content = path.read_bytes()
            digest = hashlib.sha256(content).hexdigest()
            if path.stem != digest:
                raise ValueError(f"manifest history hash mismatch: {path}")
            manifest = yaml.safe_load(content)
            for prior in manifest.get("upstream_lessons", []):
                k = prior["n"]
                if prior["sha256"] != hashes.get(k):
                    stale.append({"n": n, "manifest_sha256": digest, "upstream": k,
                                  "recorded_sha256": prior["sha256"], "current_sha256": hashes.get(k)})
    doc = {"closure_schema": 1, "level": level, "slug": slug, "lessons": rows, "stale": stale}
    Draft202012Validator(json.loads(SCHEMA.read_text(encoding="utf-8"))).validate(doc)
    lock.atomic_write(state_dir / "module.closure.yaml", lock.yaml_bytes(doc))
    return doc
