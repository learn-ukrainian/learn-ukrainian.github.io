#!/usr/bin/env python3
"""generate_mdx_direct.py -- Convert l2-uk-direct YAML modules to MDX pages.

Usage:
    .venv/bin/python scripts/generate_mdx_direct.py --module curriculum/l2-uk-direct/a1/abetka.yaml
    .venv/bin/python scripts/generate_mdx_direct.py --all --level a1
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

from generate_mdx_direct_content import (
    render_checkpoint,
    render_communicative,
    render_grammar,
    render_script_foundation,
    render_vocabulary_module,
)
from generate_mdx_direct_renderers import (
    dump_json_for_jsx,
    escape_jsx_string,
    render_activity,
)

# ──────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────

CURRICULUM_ROOT = Path("curriculum/l2-uk-direct")
OUTPUT_ROOT = Path("starlight/src/content/docs/direct")

# Activity type -> React component name
ACTIVITY_COMPONENT_MAP: dict[str, str] = {
    "watch_and_repeat": "WatchAndRepeat",
    "classify": "Classify",
    "image_to_letter": "ImageToLetter",
    "true_false": "TrueFalse",
    "build_sentence": "Unjumble",
    "match_sound": "MatchUp",
    "pattern_drill": "FillIn",
    "riddle": "Quiz",
    "tongue_twister": "WatchAndRepeat",
    "reading": "ReadingActivity",
    "proverb_drill": "Quiz",
}

# Module type -> renderer function name
MODULE_RENDERERS = {
    "script_foundation",
    "communicative",
    "vocabulary",
    "grammar",
    "checkpoint",
}

# Pre-literacy gate: modules 1-2 can only use these activity types
PRE_LITERACY_ACTIVITIES = {"watch_and_repeat", "classify", "image_to_letter"}


# ──────────────────────────────────────────────
# Module Loaders
# ──────────────────────────────────────────────


def load_module(path: Path) -> dict:
    """Load and validate a l2-uk-direct module YAML."""
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise ValueError(f"Expected dict at root of {path}, got {type(data).__name__}")

    required = {"module", "track", "level", "type", "title"}
    missing = required - set(data.keys())
    if missing:
        raise ValueError(f"Missing required keys in {path}: {missing}")

    if data["type"] not in MODULE_RENDERERS:
        raise ValueError(
            f"Unknown module type '{data['type']}' in {path}. "
            f"Must be one of: {MODULE_RENDERERS}"
        )

    return data


# ──────────────────────────────────────────────
# Import Collector
# ──────────────────────────────────────────────


def collect_imports(module_data: dict) -> list[str]:
    """Determine which React components to import based on module content."""
    imports: set[str] = set()

    if module_data.get("letters"):
        imports.add("LetterGrid")
    if module_data.get("vocabulary"):
        imports.add("VocabCard")
    if module_data.get("phrases"):
        imports.add("PhraseTable")
    if module_data.get("dialogues"):
        imports.add("DialogueBox")

    for activity in module_data.get("activities", []):
        act_type = activity.get("type", "")
        component = ACTIVITY_COMPONENT_MAP.get(act_type)
        if component:
            imports.add(component)

    return [
        f"import {comp} from '../../../../components/{comp}';"
        for comp in sorted(imports)
    ]


# ──────────────────────────────────────────────
# Main MDX Generator
# ──────────────────────────────────────────────


def _render_body(data: dict) -> str:
    """Render the main body content based on module type."""
    module_type = data["type"]
    renderers = {
        "script_foundation": render_script_foundation,
        "communicative": render_communicative,
        "vocabulary": render_vocabulary_module,
        "grammar": render_grammar,
        "checkpoint": render_checkpoint,
    }
    renderer = renderers.get(module_type)
    if renderer:
        return renderer(data)
    return f"{{/* Module type '{module_type}' not yet implemented */}}"


def _render_overview_section(data: dict) -> str:
    """Render the overview video section if present."""
    overview = data.get("overview_video")
    if not overview:
        return ""

    vid_id_match = re.search(
        r"(?:v=|/embed/|youtu\.be/)([A-Za-z0-9_-]{11})", overview
    )
    if not vid_id_match:
        return ""

    vid_id = vid_id_match.group(1)
    overview_credit = data.get("overview_credit", "")

    section = (
        f"\n## Огляд\n\n"
        f'<a href="{overview}" target="_blank" rel="noopener noreferrer" '
        f'style={{{{ display: "block", maxWidth: "640px", margin: "0 auto", position: "relative" }}}}>\n'
        f'  <img\n'
        f'    src="https://img.youtube.com/vi/{vid_id}/hqdefault.jpg"\n'
        f'    alt="Overview video"\n'
        f'    style={{{{ width: "100%", borderRadius: "8px", display: "block" }}}}\n'
        f"  />\n"
        f'  <span style={{{{ position: "absolute", top: "50%", left: "50%", transform: "translate(-50%, -50%)", '
        f'fontSize: "2rem", color: "#fff", background: "rgba(255,0,0,0.8)", '
        f'width: "64px", height: "44px", display: "flex", alignItems: "center", '
        f'justifyContent: "center", borderRadius: "12px" }}}}>&#9654;</span>\n'
        f"</a>\n"
    )
    if overview_credit:
        section += f"\n*{overview_credit}*\n"
    return section


def _render_activities_section(data: dict) -> str:
    """Render the activities section if activities are present."""
    activities = data.get("activities", [])
    if not activities:
        return ""
    section = "\n## Вправи\n\n"
    for act in activities:
        section += render_activity(act) + "\n"
    return section


def generate_mdx(data: dict, order: int = 1) -> str:
    """Generate a complete MDX string from a module data dict."""
    title = data["title"]
    data["module"]

    import_lines = collect_imports(data)

    frontmatter = [
        "---",
        f'title: "{escape_jsx_string(title)}"',
        "sidebar:",
        f"  order: {order}",
    ]
    if data.get("standard_ref"):
        frontmatter.append('  badge:')
        frontmatter.append(f'    text: "{data["level"].upper()}"')
    frontmatter.append("---")

    body = _render_body(data)
    overview_section = _render_overview_section(data)
    activities_section = _render_activities_section(data)

    playlist_credit = ""
    if data.get("playlist_credit"):
        playlist_credit = (
            f"\n---\n\n"
            f"*Відео: [{data['playlist_credit']}]({data.get('playlist', '')})*\n"
        )

    mdx_parts = [
        "\n".join(frontmatter),
        "",
        "\n".join(import_lines),
        "",
        f"# {title}",
        "",
    ]

    if overview_section:
        mdx_parts.append(overview_section)
    mdx_parts.append(body)
    if activities_section:
        mdx_parts.append(activities_section)
    if playlist_credit:
        mdx_parts.append(playlist_credit)

    return "\n".join(mdx_parts) + "\n"


# ──────────────────────────────────────────────
# Manifest & File Discovery
# ──────────────────────────────────────────────


def load_manifest(level: str) -> list[str]:
    """Load module ordering from manifest.yaml."""
    manifest_path = CURRICULUM_ROOT / "manifest.yaml"
    if not manifest_path.exists():
        level_dir = CURRICULUM_ROOT / level
        if not level_dir.exists():
            return []
        return sorted(
            [p.stem for p in level_dir.glob("*.yaml") if p.stem != "manifest"],
        )

    with open(manifest_path, encoding="utf-8") as f:
        manifest = yaml.safe_load(f)

    if not manifest:
        return []

    levels = manifest.get("levels", {})
    level_data = levels.get(level, {})
    return level_data.get("sequence", level_data.get("modules", []))


def process_module(yaml_path: Path, order: int = 1) -> Path | None:
    """Process a single module YAML to MDX. Returns output path or None on error."""
    try:
        data = load_module(yaml_path)
    except (ValueError, yaml.YAMLError) as e:
        print(f"  ERROR: {e}", file=sys.stderr)
        return None

    level = data.get("level", "a1")
    slug = data["module"]

    mdx_content = generate_mdx(data, order=order)

    out_dir = OUTPUT_ROOT / level
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{slug}.mdx"

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(mdx_content)

    return out_path


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────


def _process_all_modules(level: str) -> None:
    """Process all modules for a given level."""
    manifest = load_manifest(level)

    if not manifest:
        level_dir = CURRICULUM_ROOT / level
        if not level_dir.exists():
            print(f"ERROR: Level directory not found: {level_dir}", file=sys.stderr)
            sys.exit(1)
        yaml_files = sorted(level_dir.glob("*.yaml"))
        if not yaml_files:
            print(f"No YAML modules found in {level_dir}", file=sys.stderr)
            sys.exit(1)

        print(f"Processing {len(yaml_files)} modules from {level_dir} (no manifest)")
        for i, yf in enumerate(yaml_files, 1):
            print(f"  [{i}] {yf.name}")
            out = process_module(yf, order=i)
            if out:
                print(f"      \u2192 {out}")
    else:
        print(f"Processing {len(manifest)} modules from manifest ({level})")
        for i, slug in enumerate(manifest, 1):
            yaml_path = CURRICULUM_ROOT / level / f"{slug}.yaml"
            if not yaml_path.exists():
                print(f"  [{i}] {slug} \u2014 MISSING ({yaml_path})", file=sys.stderr)
                continue
            print(f"  [{i}] {slug}")
            out = process_module(yaml_path, order=i)
            if out:
                print(f"      \u2192 {out}")


def main() -> None:
    """CLI entry point for MDX generation."""
    parser = argparse.ArgumentParser(
        description="Generate MDX pages from l2-uk-direct YAML modules"
    )
    parser.add_argument("--module", type=Path, help="Path to a single module YAML file")
    parser.add_argument("--all", action="store_true", help="Process all modules for a level")
    parser.add_argument("--level", default="a1", help="Level to process (default: a1)")

    args = parser.parse_args()

    if args.module:
        print(f"Processing: {args.module}")
        out = process_module(args.module)
        if out:
            print(f"  \u2192 {out}")
        else:
            sys.exit(1)
    elif args.all:
        _process_all_modules(args.level)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
