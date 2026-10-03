"""Pinned offline Stanza resources; no Stanza or Torch imports at module scope."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

MANIFEST_PATH = Path(__file__).with_name("stanza_uk_manifest.json")


def manifest() -> dict:
    """Read the repository-owned inventory, never caller-selected paths."""
    return json.loads(MANIFEST_PATH.read_text())


def model_root() -> Path:
    """Use the established Stanza installation root and a revision subdirectory."""
    default = Path.home() / "stanza_resources" / "protiah" / manifest()["revision"]
    return Path(os.environ.get("STANZA_RESOURCES_DIR", str(default)))


def valid_file(path: Path, entry: dict) -> bool:
    """Validate length and SHA-256 before deserialization or installation."""
    if not path.is_file() or path.stat().st_size != entry["size"]:
        return False
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest() == entry["sha256"]


def resources_bytes() -> bytes:
    """Minimal pinned configuration; all model/dependency paths are explicit."""
    processors = {"tokenize": "iu", "mwt": "iu", "pos": "iu_charlm", "lemma": "iu_charlm", "depparse": "iu_charlm"}
    uk = {"lang_name": "Ukrainian", "packages": {"default": processors}}
    for processor, package in processors.items():
        dependencies = []
        if processor in {"pos", "lemma", "depparse"}:
            dependencies = [
                {"model": name, "package": "conll17"} for name in ("pretrain", "forward_charlm", "backward_charlm")
            ]
        uk[processor] = {package: {"dependencies": dependencies}}
    for processor in ("pretrain", "forward_charlm", "backward_charlm"):
        uk[processor] = {"conll17": {}}
    return (json.dumps({"uk": uk}, sort_keys=True) + "\n").encode()


def pipeline_kwargs() -> dict:
    """Hash every required file once at load and constrain every loaded path."""
    inventory = manifest()
    root = model_root()
    paths = {}
    for entry in inventory["files"]:
        path = root / entry["install_path"]
        if not valid_file(path, entry):
            raise FileNotFoundError("missing_or_hash_mismatched_model")
        paths[entry["install_path"].split("/")[1]] = str(path)
    resource_path = root / "resources.json"
    if not resource_path.is_file() or resource_path.read_bytes() != resources_bytes():
        raise FileNotFoundError("missing_or_hash_mismatched_resources")
    processors = ("tokenize", "mwt", "pos", "lemma", "depparse")
    kwargs = dict(
        lang="uk",
        dir=str(root),
        processors={p: "iu" if p in {"tokenize", "mwt"} else "iu_charlm" for p in processors},
        package=None,
        download_method=None,
        use_gpu=False,
        verbose=False,
        allow_unknown_language=True,
        resources_filepath=str(resource_path),
    )
    for processor in processors:
        kwargs[f"{processor}_model_path"] = paths[processor]
    for processor in ("pos", "lemma", "depparse"):
        kwargs[f"{processor}_pretrain_path"] = paths["pretrain"]
        for direction in ("forward", "backward"):
            kwargs[f"{processor}_{direction}_charlm_path"] = paths[f"{direction}_charlm"]
    return kwargs
