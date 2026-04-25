from pathlib import Path

import yaml

from scripts.build.generate_lesson_schema import (
    ACTIVITY_TYPE_BY_COMPONENT,
    LEVEL_KEY_MAP,
    PUBLIC_LEVELS,
    _split_types,
)
from scripts.pipeline.config_tables import ACTIVITY_CONFIGS

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = PROJECT_ROOT / "docs" / "lesson-schema.yaml"
COMPONENTS_DIR = PROJECT_ROOT / "starlight" / "src" / "components"
PEDAGOGY_PATH = PROJECT_ROOT / "docs" / "best-practices" / "activity-pedagogy.md"

EXCLUSIONS = {
    "utils",
    "Footer",
    "Head",
    "Header",
    "PageTitle",
    "Sidebar",
    "Home",
    "LevelLanding",
    "LiveStatus",
    "ActivityHelp",
    "ActivityPlaceholder",
}


def _schema() -> dict:
    return yaml.safe_load(SCHEMA_PATH.read_text(encoding="utf-8"))


def test_every_lesson_scope_component_has_schema() -> None:
    schema = _schema()
    declared = set(schema["components"].keys())
    actual = set()
    for ext in ("*.tsx", "*.astro"):
        for path in COMPONENTS_DIR.rglob(ext):
            if path.stem not in EXCLUSIONS:
                actual.add(path.stem)
    assert declared == actual, (
        f"missing from schema: {actual - declared}; orphan in schema: {declared - actual}"
    )


def test_schema_loadable() -> None:
    yaml.safe_load(SCHEMA_PATH.read_text(encoding="utf-8"))


def test_activity_components_match_pedagogy_matrix() -> None:
    assert "## 3. Full Allowlist Matrix" in PEDAGOGY_PATH.read_text(encoding="utf-8")
    schema = _schema()
    expected = _expected_level_scopes()

    for component, activity_type in ACTIVITY_TYPE_BY_COMPONENT.items():
        if component not in schema["components"]:
            continue
        assert schema["components"][component]["level_scope"] == expected.get(activity_type, [])


def _expected_level_scopes() -> dict[str, list[str]]:
    scopes: dict[str, set[str]] = {}
    for config_key, config in ACTIVITY_CONFIGS.items():
        public_key = LEVEL_KEY_MAP.get(config_key)
        if public_key is None:
            continue
        allowed = (
            _split_types(config.get("INLINE_ALLOWED_TYPES", ""))
            | _split_types(config.get("WORKBOOK_ALLOWED_TYPES", ""))
            | _split_types(config.get("ALLOWED_ACTIVITY_TYPES", ""))
        )
        for activity_type in allowed:
            scopes.setdefault(activity_type, set()).add(public_key)
    return {
        activity_type: [level for level in PUBLIC_LEVELS if level in levels]
        for activity_type, levels in scopes.items()
    }
