"""SHA-256 pins of the freeze manifest: inherited assets, G3 code, rubric and private prompts.

``g3_bundle_sha256`` is the digest pinned in the
``private://uk-behaviour-v2/semantic-scorer-and-judge-template`` slot: canonical
JSON of the G3 code pins, the rubric digest and the private judge template's
digest. The template bytes stay private; the steward-owned path map supplies
their location when a pin is checked.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .contract import JUDGE_SLOT, PRIVATE_PROMPT_SLOTS, REPO_ROOT
from .rubric import rubric_sha256

PACKAGE = Path(__file__).resolve().parent
PACKAGE_REL = PACKAGE.relative_to(REPO_ROOT).as_posix()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def code_pins(root: Path = REPO_ROOT) -> list[dict[str, str]]:
    """Every Python file of this package, sorted by path."""
    package = root / PACKAGE_REL
    return [
        {"path": path.relative_to(root).as_posix(), "sha256": file_sha256(path)}
        for path in sorted(package.glob("*.py"))
    ]


def g3_bundle_sha256(code: list[dict[str, str]], rubric: str, judge_template: str) -> str:
    bundle = {"code": code, "rubric_sha256": rubric, "judge_template_sha256": judge_template}
    return hashlib.sha256(json.dumps(bundle, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def private_ref(manifest: dict[str, Any], ref: str) -> dict[str, Any]:
    for entry in manifest.get("private_references", []):
        if entry.get("ref") == ref:
            return entry
    raise KeyError(ref)


def problems(
    manifest: dict[str, Any], *, root: Path = REPO_ROOT, private_paths: dict[str, Path] | None = None
) -> list[str]:
    """Every pin that does not match the bytes it names (empty when all match).

    ``private_paths`` maps private slots (and ``JUDGE_SLOT + "#template"`` for the judge
    template) to their steward-held files; slots without a path are checked for a pin only.
    """
    found = []
    for asset in manifest.get("assets", []):
        path = root / asset["path"]
        if not path.is_file():
            found.append(f"asset {asset['path']} is missing")
        elif file_sha256(path) != asset["sha256"]:
            found.append(f"asset {asset['path']} differs from its pin")
    g3 = manifest.get("g3")
    if not isinstance(g3, dict):
        return [*found, "manifest has no g3 block"]
    if g3.get("code") != code_pins(root):
        found.append("G3 code differs from its pins (a changed, added or removed module)")
    if g3.get("rubric_sha256") != rubric_sha256():
        found.append("rubric differs from its pin")
    template = g3.get("judge_template_sha256")
    bundle = private_ref(manifest, JUDGE_SLOT)
    if bundle.get("sha256") != g3_bundle_sha256(g3.get("code", []), g3.get("rubric_sha256", ""), template or ""):
        found.append("semantic scorer and judge template slot does not pin the G3 bundle")
    paths = private_paths or {}
    template_path = paths.get(JUDGE_SLOT + "#template")
    if template_path is not None and file_sha256(template_path) != template:
        found.append("private judge template differs from its pin")
    for slot in PRIVATE_PROMPT_SLOTS.values():
        entry = private_ref(manifest, slot)
        if not entry.get("sha256"):
            found.append(f"{slot} is not pinned")
        elif slot in paths and file_sha256(paths[slot]) != entry["sha256"]:
            found.append(f"{slot} differs from its pin")
    return found
