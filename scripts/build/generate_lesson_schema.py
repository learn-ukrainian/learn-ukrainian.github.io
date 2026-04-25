#!/usr/bin/env python3
"""Generate docs/lesson-schema.yaml from Starlight component prop interfaces."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
COMPONENTS_DIR = PROJECT_ROOT / "starlight" / "src" / "components"
OUTPUT_PATH = PROJECT_ROOT / "docs" / "lesson-schema.yaml"
CONFIG_TABLES_PATH = PROJECT_ROOT / "scripts" / "pipeline" / "config_tables.py"
LESSON_CONTRACT_PATH = PROJECT_ROOT / "docs" / "lesson-contract.md"
EXTRACTOR_PATH = PROJECT_ROOT / "scripts" / "build" / "lesson_schema_extractor.mjs"
GENERATOR_VERSION = "1.0.0"

sys.path.insert(0, str(SCRIPTS_DIR))
from pipeline.config_tables import (
    ACTIVITY_CONFIGS,
    INLINE_ONLY_TYPES,
    WORKBOOK_ONLY_TYPES,
)

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

PUBLIC_LEVELS = [
    "a1",
    "a2",
    "b1",
    "b2",
    "c1",
    "c2",
    "hist",
    "bio",
    "istorio",
    "lit",
    "b2-pro",
    "c1-pro",
    "oes",
    "ruth",
]

LEVEL_KEY_MAP = {
    "a1": "a1",
    "a2": "a2",
    "b1-core": "b1",
    "b2": "b2",
    "c1-core": "c1",
    "c2": "c2",
    "hist": "hist",
    "bio": "bio",
    "istorio": "istorio",
    "lit": "lit",
    "b2-pro": "b2-pro",
    "c1-pro": "c1-pro",
    "oes": "oes",
    "ruth": "ruth",
}

TAB_BY_COMPONENT = {
    "RuleBox": "lesson",
    "DialogueBox": "lesson",
    "YouTubeVideo": "lesson",
    "AuthorialIntent": "activities",
    "MythBuster": "lesson",
    "ComparativeStudy": "activities",
    "CriticalAnalysis": "activities",
    "DialectComparison": "activities",
    "EtymologyTrace": "activities",
    "PaleographyAnalysis": "activities",
    "SourceEvaluation": "activities",
    "TranslationCritique": "activities",
    "FlashcardDeck": "vocabulary",
    "VocabCard": "vocabulary",
    "PhraseTable": "vocabulary",
    "SourceBox": "resources",
}

ACTIVITY_TYPE_BY_COMPONENT = {
    "Anagram": "anagram",
    "AuthorialIntent": "authorial-intent",
    "Classify": "classify",
    "Cloze": "cloze",
    "ComparativeStudy": "comparative-study",
    "CountSyllables": "count-syllables",
    "CriticalAnalysis": "critical-analysis",
    "Debate": "debate",
    "DialectComparison": "dialect-comparison",
    "DivideWords": "divide-words",
    "ErrorCorrection": "error-correction",
    "EssayResponse": "essay-response",
    "EtymologyTrace": "etymology-trace",
    "FillIn": "fill-in",
    "GrammarIdentify": "grammar-identify",
    "GroupSort": "group-sort",
    "HighlightMorphemes": "highlight-morphemes",
    "ImageToLetter": "image-to-letter",
    "LetterGrid": "letter-grid",
    "MarkTheWords": "mark-the-words",
    "MatchUp": "match-up",
    "Observe": "observe",
    "OddOneOut": "odd-one-out",
    "Order": "order",
    "PaleographyAnalysis": "paleography-analysis",
    "PickSyllables": "pick-syllables",
    "Quiz": "quiz",
    "ReadingActivity": "reading",
    "Select": "select",
    "SourceEvaluation": "source-evaluation",
    "Transcription": "transcription",
    "Translate": "translate",
    "TranslationCritique": "translation-critique",
    "TrueFalse": "true-false",
    "Unjumble": "unjumble",
    "WatchAndRepeat": "watch-and-repeat",
}

PROPS_INTERFACE_OVERRIDES = {
    "Observe": "ObserveBlockProps",
    "ReadingActivity": "ReadingProps",
}

DEPRECATED = {
    "Classify": "Deprecated; subsumed by group-sort.",
    "Select": "Deprecated; subsumed by mark-the-words.",
}


def _split_types(value: str) -> set[str]:
    return {item.strip() for item in value.split(",") if item.strip()}


def discover_components(components_dir: Path) -> list[Path]:
    files = [*components_dir.rglob("*.tsx"), *components_dir.rglob("*.astro")]
    return sorted(path for path in files if path.stem not in EXCLUSIONS)


def _hash_files(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths):
        digest.update(path.relative_to(PROJECT_ROOT).as_posix().encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def extract_interfaces(paths: list[Path]) -> dict[str, dict[str, Any]]:
    result = subprocess.run(
        ["node", str(EXTRACTOR_PATH), *[str(path) for path in paths]],
        check=True,
        capture_output=True,
        text=True,
    )
    return {item["component"]: item for item in json.loads(result.stdout)}


def choose_props_interface(component: str, interfaces: list[dict[str, Any]]) -> dict[str, Any]:
    by_name = {interface["name"]: interface for interface in interfaces}
    names = [
        PROPS_INTERFACE_OVERRIDES.get(component, ""),
        f"{component}Props",
        f"{component}BlockProps",
    ]
    for name in names:
        if name and name in by_name:
            return by_name[name]
    props_interfaces = [item for item in interfaces if item["name"].endswith("Props")]
    if len(props_interfaces) == 1:
        return props_interfaces[0]
    raise RuntimeError(f"Could not identify props interface for {component}")


def _type_name(type_text: str) -> str | None:
    cleaned = type_text.replace("Array<", "").replace("[]>", "").replace("[]", "")
    cleaned = cleaned.strip()
    if cleaned.startswith("{") or "|" in cleaned or "<" in cleaned:
        return None
    return cleaned if cleaned[:1].isupper() else None


def _normalize_type(type_text: str) -> str:
    replacements = {
        "React.ReactNode": "jsx",
        "string": "string",
        "number": "number",
        "boolean": "boolean",
    }
    if type_text in replacements:
        return replacements[type_text]
    if type_text == "string[]":
        return "string[]"
    if type_text.startswith("Array<"):
        inner = type_text.removeprefix("Array<").removesuffix(">")
        return f"{_normalize_type(inner)}[]"
    return type_text


def _prop_record(prop: dict[str, Any]) -> dict[str, Any]:
    tags = prop.get("tags", {})
    record = {
        "name": prop["name"],
        "type": _normalize_type(prop["type"]),
        "description": tags.get("schemaDescription") or f"{prop['name']} prop.",
        "ukrainian_text": tags.get("ukrainianText", "false"),
    }
    if prop["optional"]:
        default = _default_for(prop["name"])
        if default is not None:
            record["default"] = default
    if "deprecated" in tags:
        record["deprecated"] = True
        record["deprecation_reason"] = tags["deprecated"]
    return record


def _default_for(name: str) -> Any:
    if name == "isUkrainian":
        return False
    if name in {"children", "instruction", "title", "prompt", "explanation"}:
        return None
    return None


def _nested_types(
    main_interface: dict[str, Any],
    interfaces: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    by_name = {item["name"]: item for item in interfaces}
    names = set()
    for prop in main_interface["props"]:
        type_name = _type_name(prop["type"])
        if type_name and type_name in by_name:
            names.add(type_name)
    nested = {}
    for name in sorted(names):
        nested[name] = [_prop_record(prop) for prop in by_name[name]["props"]]
    return nested


def _levels_for_activity(activity_type: str) -> list[str]:
    levels: set[str] = set()
    for key, config in ACTIVITY_CONFIGS.items():
        public_key = LEVEL_KEY_MAP.get(key)
        if public_key is None:
            continue
        allowed = (
            _split_types(config.get("INLINE_ALLOWED_TYPES", ""))
            | _split_types(config.get("WORKBOOK_ALLOWED_TYPES", ""))
            | _split_types(config.get("ALLOWED_ACTIVITY_TYPES", ""))
        )
        if activity_type in allowed:
            levels.add(public_key)
    return [level for level in PUBLIC_LEVELS if level in levels]


def _placement_for_activity(activity_type: str) -> str:
    if activity_type in INLINE_ONLY_TYPES:
        return "inline"
    if activity_type in WORKBOOK_ONLY_TYPES:
        return "workbook"
    inline = False
    workbook = False
    for config in ACTIVITY_CONFIGS.values():
        inline = inline or activity_type in _split_types(config.get("INLINE_ALLOWED_TYPES", ""))
        workbook = workbook or activity_type in _split_types(config.get("WORKBOOK_ALLOWED_TYPES", ""))
    if inline and workbook:
        return "both"
    if inline:
        return "inline"
    if workbook:
        return "workbook"
    return "n/a"


def _example_value(type_text: str, prop_name: str) -> Any:
    if type_text == "jsx":
        return "<p>Приклад вмісту.</p>"
    if type_text == "string":
        return "Приклад"
    if type_text == "number":
        return 1
    if type_text == "boolean":
        return False
    if type_text.endswith("[]"):
        return [_example_value(type_text[:-2], prop_name)]
    if type_text.startswith("{"):
        return {}
    return f"<{type_text}>"


def _example(required: list[dict[str, Any]], optional: list[dict[str, Any]]) -> dict[str, Any]:
    sample_props = required + [prop for prop in optional if prop["name"] in {"instruction", "title"}]
    return {prop["name"]: _example_value(prop["type"], prop["name"]) for prop in sample_props}


def build_schema(components_dir: Path) -> dict[str, Any]:
    paths = discover_components(components_dir)
    extracted = extract_interfaces(paths)
    components: dict[str, Any] = {}
    for path in paths:
        component = path.stem
        item = extracted[component]
        main_interface = choose_props_interface(component, item["interfaces"])
        required = [_prop_record(prop) for prop in main_interface["props"] if not prop["optional"]]
        optional = [_prop_record(prop) for prop in main_interface["props"] if prop["optional"]]
        activity_type = ACTIVITY_TYPE_BY_COMPONENT.get(component)
        deprecated = component in DEPRECATED
        components[component] = {
            "tab": TAB_BY_COMPONENT.get(component, "activities" if activity_type else "lesson"),
            "level_scope": _levels_for_activity(activity_type) if activity_type else PUBLIC_LEVELS,
            "activity_type": activity_type,
            "placement": _placement_for_activity(activity_type) if activity_type else "n/a",
            "props": {
                "required": required,
                "optional": optional,
            },
            "nested_types": _nested_types(main_interface, item["interfaces"]),
            "example": _example(required, optional),
            "deprecated": deprecated,
            "deprecation_reason": DEPRECATED.get(component) if deprecated else None,
        }
    return {
        "schema_version": "1.0",
        "generator_version": GENERATOR_VERSION,
        "generated_from": {
            "components_dir": "starlight/src/components/{*.tsx, *.astro}",
            "components_sha256": _hash_files(paths),
            "config_tables_sha256": _hash_file(CONFIG_TABLES_PATH),
            "lesson_contract_sha256": _hash_file(LESSON_CONTRACT_PATH),
        },
        "components": dict(sorted(components.items())),
    }


def write_schema(schema: dict[str, Any], output: Path) -> None:
    text = yaml.safe_dump(schema, sort_keys=False, allow_unicode=True, width=1000)
    text = text.replace("schema_version: '1.0'\n", 'schema_version: "1.0"\n', 1)
    text = text.replace("generator_version: 1.0.0\n", 'generator_version: "1.0.0"\n', 1)
    output.write_text(text, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    epilog = textwrap.dedent(
        """\
        Examples:
          .venv/bin/python scripts/build/generate_lesson_schema.py
          .venv/bin/python scripts/build/generate_lesson_schema.py --output /tmp/lesson-schema.yaml

        Outputs:
          Writes deterministic lesson component schema YAML to docs/lesson-schema.yaml by default.

        Exit codes:
          0  schema generated successfully
          1  generation failed
          2  invalid CLI usage

        Related docs:
          docs/lesson-schema-design.md
          docs/lesson-contract.md
          docs/best-practices/activity-pedagogy.md
        """
    )
    parser = argparse.ArgumentParser(
        description="Generate the lesson component schema YAML from Starlight prop interfaces.",
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--components-dir",
        type=Path,
        default=COMPONENTS_DIR,
        help="Directory containing Starlight .tsx/.astro component files (default: starlight/src/components).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_PATH,
        help="YAML output path (default: docs/lesson-schema.yaml).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        schema = build_schema(args.components_dir)
        write_schema(schema, args.output)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
