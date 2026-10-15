"""Frozen roster behavior and fresh-import parse counts for #10741."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.api import config

SOURCE_ROOT = Path(__file__).resolve().parents[2]
FALLBACK_ROWS = [
    ("a1", "A1 - Beginner"),
    ("a2", "A2 - Elementary"),
    ("b1", "B1 - Intermediate"),
    ("b2", "B2 - Upper Intermediate"),
    ("c1", "C1 - Advanced"),
    ("c2", "C2 - Mastery"),
    ("hist", "HIST - History Track"),
    ("istorio", "ISTORIO - History Track"),
    ("bio", "BIO - Biography Track"),
    ("lit", "LIT - Literature Track"),
    ("lit-essay", "LIT-ESSAY - Essays"),
    ("lit-hist-fic", "LIT-HIST-FIC - Historical Fiction"),
    ("lit-fantastika", "LIT-FANTASTIKA - Fantasy/Sci-Fi"),
    ("lit-war", "LIT-WAR - War Literature"),
    ("lit-humor", "LIT-HUMOR - Humor"),
    ("lit-youth", "LIT-YOUTH - Youth & YA"),
    ("lit-doc", "LIT-DOC - Fact & Testimony"),
    ("lit-drama", "LIT-DRAMA - Modern Stage"),
    ("lit-crimea", "LIT-CRIMEA - Voices of Crimea"),
    ("oes", "OES - Old East Slavic"),
    ("ruth", "RUTH - Ruthenian"),
    ("folk", "FOLK - Folk Culture"),
]
FALLBACK_LEVELS = [{"id": key, "name": name, "path": key} for key, name in FALLBACK_ROWS]
FALLBACK_SEMINARS = {
    "hist",
    "istorio",
    "bio",
    "lit",
    "lit-essay",
    "lit-hist-fic",
    "lit-fantastika",
    "lit-war",
    "lit-humor",
    "lit-youth",
    "lit-drama",
    "oes",
    "ruth",
    "folk",
}
# Captured from the unmodified config at 82c0f11d, independent of candidate helpers.
REAL_IDS = [
    "a1-v1",
    "a2",
    "b1",
    "b2",
    "c1",
    "hist",
    "bio",
    "lit",
    "istorio",
    "c2",
    "oes",
    "ruth",
    "lit-essay",
    "lit-hist-fic",
    "lit-fantastika",
    "lit-war",
    "lit-humor",
    "lit-youth",
    "lit-drama",
    "folk",
    "a1",
]
REAL_NAMES = dict(FALLBACK_ROWS) | {"a1-v1": "A1-V1 - a1-v1"}
REAL_LEVELS = [{"id": key, "name": REAL_NAMES[key], "path": key} for key in REAL_IDS]

IMPORT_PROBE = r"""
import json
import sys
from pathlib import Path
import yaml

root = Path(sys.argv[1])
manifest = root / "curriculum/l2-uk-en/curriculum.yaml"
text = manifest.read_text(encoding="utf-8")
reads = []
loaders = []
read_text = Path.read_text
load = yaml.load

def counted_read(self, *args, **kwargs):
    if self == manifest:
        reads.append(str(self))
    return read_text(self, *args, **kwargs)

def counted_load(stream, Loader):
    if stream == text:
        loaders.append(Loader.__name__)
    return load(stream, Loader=Loader)

class ForbiddenCLoader:
    def __init__(self, *args, **kwargs):
        raise AssertionError("C loader changes SafeLoader semantics")

if sys.argv[2] == "present":
    yaml.CSafeLoader = ForbiddenCLoader
elif hasattr(yaml, "CSafeLoader"):
    del yaml.CSafeLoader
Path.read_text = counted_read
yaml.load = counted_load
from scripts.api import config
print(json.dumps({
    "reads": len(reads), "loaders": loaders,
    "levels": config.LEVELS, "seminars": sorted(config.SEMINAR_TRACK_IDS),
    "types": [type(config.LEVELS).__name__, type(config.SEMINAR_TRACK_IDS).__name__],
}))
"""


def _fresh_import(root: Path, c_support: str) -> dict:
    result = subprocess.run(
        [sys.executable, "-c", IMPORT_PROBE, str(root), c_support],
        cwd=SOURCE_ROOT,
        env=os.environ | {"LEARN_UK_REPO_ROOT": str(root)},
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )
    return json.loads(result.stdout)


def _write_manifest(root: Path, text: str) -> Path:
    manifest = root / "curriculum/l2-uk-en/curriculum.yaml"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(text, encoding="utf-8")
    return manifest


@pytest.mark.parametrize("c_support", ["present", "absent"])
def test_fresh_import_reads_and_parses_real_manifest_once(c_support: str) -> None:
    result = _fresh_import(SOURCE_ROOT, c_support)
    assert result == {
        "reads": 1,
        "loaders": ["SafeLoader"],
        "levels": REAL_LEVELS,
        "seminars": sorted(FALLBACK_SEMINARS),
        "types": ["list", "set"],
    }


@pytest.mark.parametrize("c_support", ["present", "absent"])
def test_fresh_import_tab_after_type_preserves_fallback(tmp_path: Path, c_support: str) -> None:
    (tmp_path / ".git").mkdir()
    _write_manifest(tmp_path, "levels:\n  custom:\n    type:\ttrack\n")
    result = _fresh_import(tmp_path, c_support)
    assert result == {
        "reads": 1,
        "loaders": ["SafeLoader"],
        "levels": FALLBACK_LEVELS,
        "seminars": sorted(FALLBACK_SEMINARS),
        "types": ["list", "set"],
    }


@pytest.mark.parametrize("explicit_root", [True, False])
def test_helpers_observe_updates_and_keep_roots_isolated(tmp_path, monkeypatch, explicit_root):
    first, second = tmp_path / "first", tmp_path / "second"
    manifest = _write_manifest(first, "levels:\n  custom: {type: track}\n  a1: {type: core}\n")
    _write_manifest(second, "levels:\n  b2: {type: core}\n")
    monkeypatch.setattr(config, "LIVE_REPO_ROOT", first)
    args = (first,) if explicit_root else ()
    levels = config.load_levels(*args)
    seminars = config.load_seminar_track_ids(*args)
    assert levels == [
        {"id": "custom", "name": "CUSTOM - custom", "path": "custom"},
        {"id": "a1", "name": "A1 - Beginner", "path": "a1"},
    ]
    assert seminars == {"custom"}
    assert config.load_levels(second) == [{"id": "b2", "name": "B2 - Upper Intermediate", "path": "b2"}]
    assert config.load_seminar_track_ids(second) == set()
    levels.clear()
    seminars.clear()
    assert config.load_seminar_track_ids(*args) == {"custom"}
    manifest.write_text("levels:\n  a2: {type: track}\n", encoding="utf-8")
    assert config.load_levels(*args) == [{"id": "a2", "name": "A2 - Elementary", "path": "a2"}]
    assert config.load_seminar_track_ids(*args) == {"a2"}
    assert config.LEVELS == REAL_LEVELS
    assert config.SEMINAR_TRACK_IDS == FALLBACK_SEMINARS


@pytest.mark.parametrize(
    "text",
    [
        None,
        "",
        "[broken",
        "[]",
        "plain scalar",
        "{}",
        "levels: null",
        "levels: []",
        "levels: invalid",
        "levels: 42",
        "levels:\n  custom:\n    type:\ttrack\n",
        "!!python/object:builtins.object {}",
    ],
)
def test_invalid_or_missing_manifest_preserves_fallback(tmp_path, monkeypatch, text):
    monkeypatch.setattr(config, "PROJECT_ROOT", tmp_path / "missing-project")
    if text is not None:
        _write_manifest(tmp_path, text)
    assert config.load_levels(tmp_path) == FALLBACK_LEVELS
    assert config.load_seminar_track_ids(tmp_path) == FALLBACK_SEMINARS


def test_missing_explicit_root_uses_project_manifest(tmp_path, monkeypatch):
    project = tmp_path / "project"
    _write_manifest(project, "levels:\n  a1: {type: track}\n")
    monkeypatch.setattr(config, "PROJECT_ROOT", project)
    assert config.load_levels(tmp_path / "missing") == [{"id": "a1", "name": "A1 - Beginner", "path": "a1"}]
    assert config.load_seminar_track_ids(tmp_path / "missing") == {"a1"}


def test_unreadable_manifest_preserves_fallback(tmp_path, monkeypatch):
    manifest = _write_manifest(tmp_path, "levels: {}")
    read_text = Path.read_text

    def denied(self, *args, **kwargs):
        if self == manifest:
            raise PermissionError("manifest denied")
        return read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", denied)
    assert config.load_levels(tmp_path) == FALLBACK_LEVELS
    assert config.load_seminar_track_ids(tmp_path) == FALLBACK_SEMINARS


def test_empty_levels_is_valid(tmp_path):
    _write_manifest(tmp_path, "levels: {}")
    assert config.load_levels(tmp_path) == []
    assert config.load_seminar_track_ids(tmp_path) == set()


def test_nonmapping_track_configs_keep_order_but_are_not_seminars(tmp_path):
    _write_manifest(tmp_path, "levels:\n  plain: null\n  a1: []\n  custom: {type: track}\n")
    assert config.load_levels(tmp_path) == [
        {"id": "plain", "name": "PLAIN - plain", "path": "plain"},
        {"id": "a1", "name": "A1 - Beginner", "path": "a1"},
        {"id": "custom", "name": "CUSTOM - custom", "path": "custom"},
    ]
    assert config.load_seminar_track_ids(tmp_path) == {"custom"}


def test_invalid_level_key_keeps_original_error(tmp_path):
    _write_manifest(tmp_path, "levels:\n  42: {type: track}\n")
    with pytest.raises(AttributeError, match="'int' object has no attribute 'upper'"):
        config.load_levels(tmp_path)
    assert config.load_seminar_track_ids(tmp_path) == {42}
