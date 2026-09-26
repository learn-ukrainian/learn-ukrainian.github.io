"""Regression checks for lexicon paths after the P2 data split."""

from __future__ import annotations

import inspect
import json
import sys
from pathlib import Path

import pytest

from scripts.atlas import fill_local
from scripts.lexicon import curated_textbook_jsonl_repromote as textbook
from scripts.lexicon import reenrich_thin_manifest_entries as reenrich
from scripts.lexicon import repair_plural_noun_aliases as repair
from scripts.storage import paths


def test_textbook_default_inventory_is_tracked_registry_file() -> None:
    assert textbook.DEFAULT_INVENTORY.is_relative_to(textbook.PROJECT_ROOT / "registry/lexicon")
    assert textbook.DEFAULT_INVENTORY.is_file()


@pytest.mark.parametrize("module", [reenrich, repair], ids=["reenrich", "repair"])
def test_kaikki_readers_fail_closed_when_unhydrated(tmp_path: Path, monkeypatch, module) -> None:
    manifest = paths.manifest_path("lexicon_kaikki")
    destination = paths.manifest_path("lexicon_kaikki", tmp_path)
    destination.parent.mkdir(parents=True)
    destination.write_bytes(manifest.read_bytes())
    monkeypatch.setattr(
        module,
        "artifact_path",
        lambda group, rel: paths.artifact_path(group, rel, repo=tmp_path),
    )

    with pytest.raises(paths.MissingArtifactError, match="hydrate"):
        module._load_kaikki_lookup(None)
    with pytest.raises(FileNotFoundError):
        module._load_kaikki_lookup(tmp_path / "missing-explicit.json")


@pytest.mark.parametrize("module", [reenrich, repair], ids=["reenrich", "repair"])
def test_unhydrated_write_does_not_change_manifest(tmp_path: Path, monkeypatch, module) -> None:
    artifact_manifest = paths.manifest_path("lexicon_kaikki", tmp_path)
    artifact_manifest.parent.mkdir(parents=True)
    artifact_manifest.write_bytes(paths.manifest_path("lexicon_kaikki").read_bytes())
    manifest = tmp_path / "manifest.json"
    original = json.dumps({"entries": []}) + "\n"
    manifest.write_text(original, encoding="utf-8")
    monkeypatch.setattr(
        module,
        "artifact_path",
        lambda group, rel: paths.artifact_path(group, rel, repo=tmp_path),
    )
    if module is reenrich:
        monkeypatch.setattr(
            sys,
            "argv",
            ["reenrich_thin_manifest_entries.py", "--manifest", str(manifest), "--local", "--write"],
        )
        invoke = module.main
    else:

        def invoke():
            return module.main(["--manifest", str(manifest), "--write"])

    with pytest.raises(paths.MissingArtifactError):
        invoke()
    assert manifest.read_text(encoding="utf-8") == original


def test_fill_local_uses_verified_default_kaikki_artifact(monkeypatch) -> None:
    assert fill_local.DEFAULT_KAIKKI_LOOKUP is None
    assert inspect.signature(fill_local._fill_local).parameters["kaikki_lookup_path"].default is None
    seen = []
    monkeypatch.setattr(fill_local, "_fill_local", lambda *args, **kwargs: seen.append(args[2]))
    fill_local.fill_local()
    assert seen == [None]
