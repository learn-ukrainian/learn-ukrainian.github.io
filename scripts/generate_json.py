#!/usr/bin/env python3
"""
Learn Ukrainian JSON Generator (Python)

Generates Vibe-format JSON from markdown modules.
Replaces the TypeScript generate.ts for JSON output only.

Usage:
    python scripts/generate_json.py                     # Generate all
    python scripts/generate_json.py l2-uk-en            # Generate all levels
    python scripts/generate_json.py l2-uk-en a1         # Generate A1 only
    python scripts/generate_json.py l2-uk-en a1 5       # Generate A1 module 5
"""

import json
import os
import re
import sys
import yaml
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# Add scripts dir to path for shared module imports
SCRIPT_DIR = Path(__file__).parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.append(str(SCRIPT_DIR))
from yaml_activities import ActivityParser, Activity

# =============================================================================
# CONFIGURATION
# =============================================================================

ROOT_DIR = Path(__file__).parent.parent
CURRICULUM_DIR = ROOT_DIR / "curriculum"
OUTPUT_DIR = ROOT_DIR / "output"
LEVEL_FOLDERS = ["a1", "a2", "b1", "b2", "c1", "c2", "lit"]

# =============================================================================
# FRONTMATTER PARSER
# =============================================================================

def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Extract YAML frontmatter and return (frontmatter_dict, remaining_content)."""
    match = re.match(r"^---\n(.*?)\n---\n?(.*)", content, re.DOTALL)
    if not match:
        return {}, content

    try:
        fm = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError:
        fm = {}

    return fm, match.group(2)

# =============================================================================
# SECTION PARSER
# =============================================================================

SECTION_TYPES = {
    "introduction": "intro",
    "intro": "intro",
    "вступ": "intro",
    "lesson": "content",
    "content": "content",
    "урок": "content",
    "practice": "practice",
    "практика": "practice",
    "summary": "summary",
    "підсумок": "summary",
    "vocabulary": "vocabulary",
    "словник": "vocabulary",
    "activities": "activities",
    "вправи": "activities",
}

def parse_sections(content: str) -> list[dict]:
    """Parse markdown sections (# headings) into structured sections."""
    sections = []

    # Split by top-level headings
    parts = re.split(r"^# ", content, flags=re.MULTILINE)

    for i, part in enumerate(parts):
        if i == 0:
            continue  # Skip content before first heading

        lines = part.split("\n", 1)
        title = lines[0].strip()
        section_content = lines[1] if len(lines) > 1 else ""

        # Determine section type from title
        title_lower = title.lower()
        section_type = "content"
        for key, stype in SECTION_TYPES.items():
            if key in title_lower:
                section_type = stype
                break

        section_id = f"section-{len(sections) + 1}"

        sections.append({
            "id": section_id,
            "type": section_type,
            "title": title,
            "content": section_content.strip(),
        })

    return sections

# =============================================================================
# VOCABULARY PARSER
# =============================================================================

def parse_vocabulary(content: str) -> list[dict]:
    """Parse vocabulary table from markdown."""
    words = []

    # Find vocabulary section
    vocab_match = re.search(
        r"^#\s*(?:Vocabulary|Словник)\s*\n(.*?)(?=^#|\Z)",
        content,
        re.MULTILINE | re.DOTALL | re.IGNORECASE
    )

    if not vocab_match:
        return words

    vocab_content = vocab_match.group(1)

    # Find table rows (skip header and separator)
    table_match = re.search(r"\|.*\|\n\|[-\s|]+\|\n((?:\|.*\|\n?)*)", vocab_content)
    if not table_match:
        return words

    rows = table_match.group(1).strip().split("\n")

    for i, row in enumerate(rows):
        cells = [c.strip() for c in row.split("|")[1:-1]]  # Remove empty first/last
        if len(cells) < 3:
            continue

        word = {
            "id": f"vocab-{i + 1}",
            "uk": cells[0],
            "ipa": cells[1] if len(cells) > 1 else "",
            "en": cells[2] if len(cells) > 2 else "",
            "pos": cells[3] if len(cells) > 3 else "",
            "gender": None,
            "note": cells[5] if len(cells) > 5 else "",
        }

        # Parse gender from column 4 if present
        if len(cells) > 4 and cells[4]:
            gender_map = {"m": "m", "f": "f", "n": "n", "ч": "m", "ж": "f", "с": "n"}
            word["gender"] = gender_map.get(cells[4].lower())

        words.append(word)

    return words

# =============================================================================
# ACTIVITY PARSER (YAML)
# =============================================================================

def yaml_activity_to_vibe(act: Activity, index: int) -> dict:
    """Convert a YAML Activity object to Vibe JSON format."""
    from yaml_activities import (
        QuizActivity, MatchUpActivity, GroupSortActivity, FillInActivity,
        ClozeActivity, UnjumbleActivity, ErrorCorrectionActivity,
        MarkTheWordsActivity, TranslateActivity, AnagramActivity, ReadingActivity,
        SelectActivity
    )
    
    activity_type = act.type
    title = getattr(act, 'title', activity_type.replace('-', ' ').title())
    
    vibe_act = {
        "id": f"act-{index}-{activity_type}",
        "type": activity_type,
        "title": title,
        "description": f"{activity_type.replace('-', ' ').title()} activity",
        "instructions": getattr(act, 'instruction', ""),
        "content": {},
        "tags": [activity_type],
    }
    
    if isinstance(act, (QuizActivity, SelectActivity)):
        items = []
        for item in act.items:
            options = [o.text for o in item.options]
            correct_indices = [i for i, o in enumerate(item.options) if o.correct]
            items.append({
                "question": item.question,
                "options": options,
                "correctIndex": correct_indices[0] if correct_indices and isinstance(act, QuizActivity) else None,
                "correctAnswers": [options[i] for i in correct_indices] if isinstance(act, SelectActivity) else None,
                "explanation": getattr(item, 'explanation', "")
            })
        vibe_act["content"] = {"items" if isinstance(act, SelectActivity) else "questions": items}
        
    elif isinstance(act, MatchUpActivity):
        vibe_act["content"] = {
            "pairs": [{"left": p.left, "right": p.right} for p in act.pairs]
        }
        
    elif isinstance(act, GroupSortActivity):
        groups = {}
        for group in act.groups:
            groups[group.name] = group.items
        vibe_act["content"] = {"groups": groups}
        
    elif isinstance(act, FillInActivity):
        vibe_act["content"] = {
            "items": [{
                "sentence": i.sentence,
                "answer": i.answer,
                "options": i.options,
                "explanation": i.explanation
            } for i in act.items]
        }
        
    elif isinstance(act, ClozeActivity):
        vibe_act["content"] = {
            "text": act.passage,
            "blanks": [{
                "index": b.id - 1 if hasattr(b, 'id') else i,
                "answer": b.answer,
                "options": b.options
            } for i, b in enumerate(act.blanks)]
        }
        
    elif isinstance(act, UnjumbleActivity):
        vibe_act["content"] = {
            "items": [{
                "jumbled": ' / '.join(i.words) if isinstance(i.words, list) else i.words,
                "answer": i.answer
            } for i in act.items]
        }
        
    elif isinstance(act, ErrorCorrectionActivity):
        vibe_act["content"] = {
            "items": [{
                "sentence": i.sentence,
                "error": i.error,
                "answer": i.answer,
                "options": i.options,
                "explanation": i.explanation
            } for i in act.items]
        }
        
    elif isinstance(act, MarkTheWordsActivity):
        vibe_act["content"] = {
            "text": act.text,
            "answers": act.answers
        }
        
    elif isinstance(act, TranslateActivity):
        vibe_act["content"] = {
            "items": [{
                "source": i.source,
                "options": [{"text": o.text, "correct": o.correct} for o in i.options],
                "explanation": i.explanation
            } for i in act.items]
        }
        
    elif isinstance(act, AnagramActivity):
        vibe_act["content"] = {
            "items": [{
                "scrambled": i.scrambled,
                "answer": i.answer,
                "hint": i.hint
            } for i in act.items]
        }
        
    return vibe_act

# =============================================================================
# MODULE PARSER
# =============================================================================

def parse_module(content: str, level: str, module_num: int, yaml_activities: list[Activity] | None = None) -> dict:
    """Parse a complete module markdown file."""
    frontmatter, body = parse_frontmatter(content)

    # Override level/module from path (not frontmatter)
    frontmatter["level"] = level.upper()
    frontmatter["module"] = module_num

    # Set defaults
    frontmatter.setdefault("title", f"Module {module_num}")
    frontmatter.setdefault("phase", f"{level.upper()}.1")
    frontmatter.setdefault("duration", 45)
    frontmatter.setdefault("transliteration", "none")
    frontmatter.setdefault("tags", [])
    frontmatter.setdefault("objectives", [])
    frontmatter.setdefault("pedagogy", "PPP")

    sections = parse_sections(body)
    vocabulary = parse_vocabulary(body)
    
    # Use YAML activities if provided, otherwise parse from markdown
    if yaml_activities:
        activities = [yaml_activity_to_vibe(act, i+1) for i, act in enumerate(yaml_activities)]
    else:
        activities = parse_activities(body)

    return {
        "frontmatter": frontmatter,
        "sections": sections,
        "activities": activities,
        "vocabulary": vocabulary,
        "reviewVocabulary": [],
        "rawMarkdown": content,
    }

# =============================================================================
# JSON RENDERER
# =============================================================================

MODULE_TYPE_MAPPINGS = [
    ("checkpoint", ["checkpoint", "review", "assessment"]),
    ("history", ["history"]),
    ("biography", ["biography"]),
    ("idioms", ["idioms", "phraseology"]),
    ("literature", ["literature", "poetry", "prose"]),
    ("culture", ["culture", "regions", "music"]),
    ("skills", ["skills", "academic", "writing"]),
    ("functional", ["functional", "dialogue", "role-play"]),
    ("vocabulary", ["vocabulary", "vocab"]),
    ("grammar", ["grammar", "cases", "verbs", "aspect"]),
]

def infer_module_type(tags: list[str]) -> str:
    """Infer module type from tags."""
    tag_set = set(t.lower() for t in tags)
    for mtype, keywords in MODULE_TYPE_MAPPINGS:
        if any(k in tag_set for k in keywords):
            return mtype
    return "grammar"

IMMERSION_LEVELS = {
    "A1": 0.30, "A2": 0.40, "B1": 0.60, "B2": 0.85,
    "C1": 0.95, "C2": 0.98,
}

def get_immersion_level(level: str) -> float:
    """Get immersion level for CEFR level."""
    return IMMERSION_LEVELS.get(level.upper(), 0.50)

def render_vibe_json(parsed: dict, lang_pair: str, external_resources: dict | None = None) -> dict:
    """Render parsed module to Vibe JSON format.

    Args:
        parsed: Parsed module data
        lang_pair: Language pair (e.g., 'l2-uk-en')
        external_resources: Optional external resources dict (from YAML)
    """
    fm = parsed["frontmatter"]
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    level = fm["level"]
    module_num = fm["module"]
    module_id = f"mod-uk-{level}-{module_num:02d}"
    lesson_id = f"lesson-uk-{level}-{module_num:02d}"

    # Build sections
    vibe_sections = [
        {
            "id": s["id"],
            "name": s.get("titleUk") or s["title"],
            "nameEn": s["title"] if s.get("titleUk") else None,
            "type": s["type"],
            "content": s["content"],
        }
        for s in parsed["sections"]
    ]

    # Build activities
    vibe_activities = [
        {
            "id": a["id"],
            "type": a["type"],
            "title": a["title"],
            "titleUk": a.get("titleUk"),
            "description": a["description"],
            "content": a["content"],
            "subject": "language",
            "owner": "learn-ukrainian",
            "visibility": "public",
            "language": "uk",
            "difficultyLevel": level,
            "duration": 5,
            "tags": a.get("tags", []),
            "createdAt": now,
            "modifiedAt": now,
        }
        for a in parsed["activities"]
    ]

    # Build vocabulary
    vocab_section = {
        "moduleId": module_id,
        "level": level,
        "phase": fm["phase"],
        "wordCount": len(parsed["vocabulary"]),
        "newWordCount": len(parsed["vocabulary"]),
        "reviewWordCount": len(parsed.get("reviewVocabulary", [])),
        "transliterationMode": fm["transliteration"],
        "words": parsed["vocabulary"],
        "reviewWords": parsed.get("reviewVocabulary", []),
    }

    # Build lesson
    lesson = {
        "id": lesson_id,
        "moduleId": module_id,
        "languagePair": lang_pair,
        "subject": "language",
        "owner": "learn-ukrainian",
        "visibility": "public",
        "language": "uk",
        "targetLevel": level,
        "phase": fm["phase"],
        "moduleNumber": module_num,
        "moduleType": infer_module_type(fm["tags"]),
        "pedagogy": fm.get("pedagogy"),
        "immersionLevel": get_immersion_level(level),
        "title": fm["title"],
        "titleUk": fm.get("titleUk"),
        "subtitle": fm.get("subtitle"),
        "description": fm["objectives"][0] if fm["objectives"] else fm["title"],
        "objectives": fm["objectives"],
        "objectivesUk": fm.get("objectivesUk"),
        "grammarFocus": fm.get("grammar", []),
        "tags": fm["tags"],
        "totalDuration": fm["duration"],
        "transliterationMode": fm["transliteration"],
        "sections": vibe_sections,
        "rawMarkdown": parsed["rawMarkdown"],
        "createdAt": now,
        "modifiedAt": now,
        "version": 2,
    }

    # Build result
    result = {
        "$schema": "../../../schemas/vibe-module.schema.json",
        "lesson": lesson,
        "activities": vibe_activities,
        "vocabulary": vocab_section,
    }

    # Add external resources if present (sorted by priority)
    if external_resources:
        # Priority and relevance maps for sorting
        # Priority 1 = highest (Ukrainian Lessons Priority 1), 5 = lowest
        priority_map = {1: 5, 2: 4, 3: 3, 4: 2, 5: 1, None: 0}
        relevance_map = {'high': 3, 'medium': 2, 'low': 1}

        def sort_resources(items):
            """Sort resources by: priority (1→5) → relevance (high→low) → title (A→Z)"""
            if not items:
                return items
            return sorted(
                items,
                key=lambda x: (
                    -priority_map.get(x.get('priority'), 0),  # Priority 1 appears first
                    -relevance_map.get(x.get('relevance', 'low'), 0),  # High relevance next
                    x.get('title', '').lower()  # Alphabetical last
                )
            )

        result["external_resources"] = {
            "podcasts": sort_resources(external_resources.get("podcasts", [])),
            "youtube": sort_resources(external_resources.get("youtube", [])),
            "articles": sort_resources(external_resources.get("articles", [])),
            "books": sort_resources(external_resources.get("books", [])),
            "websites": sort_resources(external_resources.get("websites", []))
        }

    return result

# =============================================================================
# MAIN
# =============================================================================

def main():
    args = sys.argv[1:]
    target_lang_pair = args[0] if len(args) > 0 else None
    target_level = args[1].lower() if len(args) > 1 else None
    target_module_num = int(args[2]) if len(args) > 2 else None

    print("\n🚀 Learn Ukrainian JSON Generator (Python)\n")
    print("Source: curriculum/[lang]/[level]/*.md")
    print("Output: output/json/\n")

    # Load EXTERNAL RESOURCES (YAML Architecture) - loaded once for all modules
    external_resources_file = ROOT_DIR / 'docs' / 'resources' / 'external_resources.yaml'
    all_resources = {}
    if external_resources_file.exists():
        with open(external_resources_file, 'r', encoding='utf-8') as f:
            resources_data = yaml.safe_load(f)
            all_resources = resources_data.get('resources', {})
        print(f'📚 Loaded {len(all_resources)} modules with external resources\n')

    # Find language pairs
    if target_lang_pair:
        lang_pairs = [target_lang_pair]
    else:
        lang_pairs = [
            d for d in os.listdir(CURRICULUM_DIR)
            if d.startswith("l") and (CURRICULUM_DIR / d).is_dir()
        ]

    for lang_pair in lang_pairs:
        print(f"📚 Processing {lang_pair}...")

        lang_dir = CURRICULUM_DIR / lang_pair
        if not lang_dir.exists():
            print(f"  ⚠ Language directory not found, skipping...")
            continue

        # Find level folders
        level_folders = [
            d for d in LEVEL_FOLDERS
            if (lang_dir / d).is_dir()
        ]

        if not level_folders:
            print(f"  ⚠ No level folders found, skipping...")
            continue

        for level_folder in level_folders:
            if target_level and level_folder != target_level:
                continue

            level_dir = lang_dir / level_folder
            level = level_folder.upper()

            # Find module files (supports 2-3 digit module numbers)
            md_files = sorted([
                f for f in os.listdir(level_dir)
                if re.match(r"^\d{2,3}-.*\.md$", f) or re.match(r"^module-\d+\.md$", f)
            ])

            print(f"\n  📁 Level {level} ({len(md_files)} modules)")

            for md_file in md_files:
                # Extract module number (supports 2-3 digit module numbers)
                match = re.match(r"^(\d{2,3})-", md_file) or re.match(r"^module-(\d+)", md_file)
                module_num = int(match.group(1)) if match else 0

                if target_module_num and module_num != target_module_num:
                    continue

                try:
                    md_path = level_dir / md_file
                    md_content = md_path.read_text(encoding="utf-8")

                    # Check for YAML activities file
                    yaml_activities = None
                    yaml_file = level_dir / 'activities' / (md_path.stem + '.yaml')
                    if not yaml_file.exists():
                        yaml_file = md_path.with_suffix('.activities.yaml')
                    
                    if yaml_file.exists():
                        parser = ActivityParser()
                        try:
                            yaml_activities = parser.parse(yaml_file)
                        except Exception as e:
                            print(f"    ⚠ Error parsing YAML activities: {e}")

                    # Parse module
                    parsed = parse_module(md_content, level_folder, module_num, yaml_activities)

                    # Lookup EXTERNAL RESOURCES by module_id
                    # module_id format: {level}-{filename} (e.g., a1-09-food-and-drinks)
                    # Extract filename without extension
                    module_filename = Path(md_file).stem
                    module_id = f"{level_folder}-{module_filename}"
                    module_resources = all_resources.get(module_id, {})

                    # Render to JSON
                    vibe_json = render_vibe_json(parsed, lang_pair, module_resources)

                    # Write output
                    out_dir = OUTPUT_DIR / "json" / lang_pair / level_folder
                    out_dir.mkdir(parents=True, exist_ok=True)

                    out_path = out_dir / f"module-{module_num:02d}.json"
                    out_path.write_text(
                        json.dumps(vibe_json, ensure_ascii=False, indent=2),
                        encoding="utf-8"
                    )

                    print(f"    ✓ Module {module_num:02d}: {parsed['frontmatter']['title']}")

                except Exception as e:
                    print(f"    ⚠ Error processing {md_file}: {e}")

    print("\n✅ JSON generation complete!\n")

if __name__ == "__main__":
    main()
