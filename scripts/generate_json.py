#!/usr/bin/env python3
"""
Curricula-Opus JSON Generator (Python)

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
# ACTIVITY PARSER
# =============================================================================

ACTIVITY_PATTERNS = {
    "quiz": r"^##\s*quiz:\s*(.+)$",
    "match-up": r"^##\s*match(?:-up)?:\s*(.+)$",
    "group-sort": r"^##\s*group(?:-sort)?:\s*(.+)$",
    "fill-in": r"^##\s*fill(?:-in)?:\s*(.+)$",
    "true-false": r"^##\s*(?:true-false|tf):\s*(.+)$",
    "translate": r"^##\s*translate:\s*(.+)$",
    "unjumble": r"^##\s*unjumble:\s*(.+)$",
    "anagram": r"^##\s*anagram:\s*(.+)$",
    "error-correction": r"^##\s*error(?:-correction)?:\s*(.+)$",
    "select": r"^##\s*select:\s*(.+)$",
    "cloze": r"^##\s*cloze:\s*(.+)$",
    "dialogue-reorder": r"^##\s*dialogue(?:-reorder)?:\s*(.+)$",
    "mark-the-words": r"^##\s*mark(?:-the-words)?:\s*(.+)$",
}

def parse_activities(content: str) -> list[dict]:
    """Parse activity blocks from markdown."""
    activities = []

    # Find activities section
    act_match = re.search(
        r"^#\s*(?:Activities|Вправи)\s*\n(.*?)(?=^#[^#]|\Z)",
        content,
        re.MULTILINE | re.DOTALL | re.IGNORECASE
    )

    if not act_match:
        return activities

    act_content = act_match.group(1)

    # Split by ## activity headers
    parts = re.split(r"^##\s*", act_content, flags=re.MULTILINE)

    for i, part in enumerate(parts):
        if i == 0:
            continue

        # Determine activity type
        activity_type = None
        title = ""

        for atype, pattern in ACTIVITY_PATTERNS.items():
            match = re.match(pattern.replace("^##\\s*", ""), part, re.IGNORECASE)
            if match:
                activity_type = atype
                title = match.group(1).strip()
                break

        if not activity_type:
            continue

        # Get content after the title line
        lines = part.split("\n", 1)
        activity_content = lines[1] if len(lines) > 1 else ""

        activity_id = f"act-{len(activities) + 1}-{activity_type}"

        parsed_content = parse_activity_content(activity_type, activity_content.strip())

        activities.append({
            "id": activity_id,
            "type": activity_type,
            "title": title,
            "description": f"{activity_type.replace('-', ' ').title()} activity",
            "instructions": "",
            "content": parsed_content,
            "tags": [activity_type],
        })

    return activities

def parse_activity_content(activity_type: str, content: str) -> dict:
    """Parse activity-specific content."""

    if activity_type == "quiz":
        return parse_quiz_content(content)
    elif activity_type == "match-up":
        return parse_matchup_content(content)
    elif activity_type == "group-sort":
        return parse_groupsort_content(content)
    elif activity_type == "fill-in":
        return parse_fillin_content(content)
    elif activity_type == "true-false":
        return parse_truefalse_content(content)
    elif activity_type == "translate":
        return parse_translate_content(content)
    elif activity_type == "unjumble":
        return parse_unjumble_content(content)
    elif activity_type == "anagram":
        return parse_anagram_content(content)
    elif activity_type == "error-correction":
        return parse_errorcorrection_content(content)
    elif activity_type == "select":
        return parse_select_content(content)
    elif activity_type == "cloze":
        return parse_cloze_content(content)
    else:
        return {"type": activity_type, "raw": content}

def parse_quiz_content(content: str) -> dict:
    """Parse quiz questions."""
    questions = []

    # Split by numbered questions
    parts = re.split(r"^\d+\.\s*", content, flags=re.MULTILINE)

    for part in parts[1:]:  # Skip empty first part
        lines = part.strip().split("\n")
        if not lines:
            continue

        question_text = lines[0].strip()
        options = []
        correct_index = 0
        explanation = ""

        for j, line in enumerate(lines[1:]):
            line = line.strip()
            if line.startswith("- [x]"):
                options.append(line[5:].strip())
                correct_index = len(options) - 1
            elif line.startswith("- [ ]"):
                options.append(line[5:].strip())
            elif line.startswith(">"):
                explanation = line[1:].strip()

        if question_text and options:
            questions.append({
                "question": question_text,
                "options": options,
                "correctIndex": correct_index,
                "explanation": explanation,
            })

    return {
        "type": "quiz",
        "questions": questions,
        "shuffleQuestions": False,
        "shuffleOptions": True,
        "showCorrectAnswers": True,
    }

def parse_matchup_content(content: str) -> dict:
    """Parse match-up pairs."""
    pairs = []

    for line in content.split("\n"):
        line = line.strip()
        if not line.startswith("-"):
            continue

        # Parse: - left | right
        match = re.match(r"-\s*(.+?)\s*\|\s*(.+)", line)
        if match:
            pairs.append({
                "left": match.group(1).strip(),
                "right": match.group(2).strip(),
            })

    return {
        "type": "match-up",
        "pairs": pairs,
        "shuffleRight": True,
    }

def parse_groupsort_content(content: str) -> dict:
    """Parse group-sort groups."""
    groups = []
    current_group = None

    for line in content.split("\n"):
        line = line.strip()

        # Group header: ### GroupName
        if line.startswith("###"):
            if current_group:
                groups.append(current_group)
            group_name = line[3:].strip()
            current_group = {
                "id": f"group-{len(groups) + 1}",
                "name": group_name,
                "items": [],
            }
        elif line.startswith("-") and current_group:
            item = line[1:].strip()
            if item:
                current_group["items"].append(item)

    if current_group:
        groups.append(current_group)

    return {
        "type": "group-sort",
        "groups": groups,
        "shuffleItems": True,
    }

def parse_fillin_content(content: str) -> dict:
    """Parse fill-in items."""
    items = []

    parts = re.split(r"^\d+\.\s*", content, flags=re.MULTILINE)

    for part in parts[1:]:
        lines = part.strip().split("\n")
        if not lines:
            continue

        prompt = lines[0].strip()
        answer = ""
        options = []

        for line in lines[1:]:
            line = line.strip()
            if line.startswith("answer:"):
                answer = line[7:].strip()
            elif line.startswith("options:"):
                opts = line[8:].strip()
                options = [o.strip() for o in opts.split(",")]
            elif line.startswith("-"):
                opt = line[1:].strip()
                if opt.startswith("[x]"):
                    answer = opt[3:].strip()
                    options.append(answer)
                elif opt.startswith("[ ]"):
                    options.append(opt[3:].strip())
                else:
                    options.append(opt)

        if prompt:
            items.append({
                "prompt": prompt,
                "answer": answer or (options[0] if options else ""),
                "options": options,
            })

    return {
        "type": "fill-in",
        "items": items,
    }

def parse_truefalse_content(content: str) -> dict:
    """Parse true-false statements."""
    statements = []

    parts = re.split(r"^\d+\.\s*", content, flags=re.MULTILINE)

    for part in parts[1:]:
        lines = part.strip().split("\n")
        if not lines:
            continue

        statement = lines[0].strip()
        is_true = False
        explanation = ""

        for line in lines[1:]:
            line = line.strip().lower()
            if "true" in line and "[x]" in line:
                is_true = True
            elif "false" in line and "[x]" in line:
                is_true = False
            elif line.startswith(">"):
                explanation = line[1:].strip()

        if statement:
            statements.append({
                "statement": statement,
                "isTrue": is_true,
                "explanation": explanation,
            })

    return {
        "type": "true-false",
        "statements": statements,
    }

def parse_translate_content(content: str) -> dict:
    """Parse translate items."""
    items = []
    direction = "to-uk"  # default

    # Check for direction hint
    if "to english" in content.lower() or "to-en" in content.lower():
        direction = "to-en"

    parts = re.split(r"^\d+\.\s*", content, flags=re.MULTILINE)

    for part in parts[1:]:
        lines = part.strip().split("\n")
        if not lines:
            continue

        source = lines[0].strip()
        answer = ""
        options = []

        for line in lines[1:]:
            line = line.strip()
            if line.startswith("-"):
                opt = line[1:].strip()
                if opt.startswith("[x]"):
                    answer = opt[3:].strip()
                    options.append(answer)
                elif opt.startswith("[ ]"):
                    options.append(opt[3:].strip())

        if source:
            items.append({
                "source": source,
                "answer": answer,
                "options": options,
            })

    return {
        "type": "translate",
        "items": items,
        "direction": direction,
    }

def parse_unjumble_content(content: str) -> dict:
    """Parse unjumble items."""
    items = []

    parts = re.split(r"^\d+\.\s*", content, flags=re.MULTILINE)

    for part in parts[1:]:
        lines = part.strip().split("\n")
        if not lines:
            continue

        words_line = lines[0].strip()
        answer = ""
        hint = ""

        for line in lines[1:]:
            line = line.strip()
            if line.lower().startswith("answer:"):
                answer = line[7:].strip()
            elif line.lower().startswith("hint:"):
                hint = line[5:].strip()

        # Parse words (separated by / | or ,)
        words = re.split(r"[/|,]\s*", words_line)
        words = [w.strip() for w in words if w.strip()]

        if words:
            items.append({
                "words": words,
                "answer": answer or " ".join(words),
                "hint": hint,
            })

    return {
        "type": "unjumble",
        "items": items,
    }

def parse_anagram_content(content: str) -> dict:
    """Parse anagram items."""
    items = []

    parts = re.split(r"^\d+\.\s*", content, flags=re.MULTILINE)

    for part in parts[1:]:
        lines = part.strip().split("\n")
        if not lines:
            continue

        letters_line = lines[0].strip()
        answer = ""
        hint = ""
        translation = ""

        for line in lines[1:]:
            line = line.strip()
            if line.lower().startswith("answer:"):
                answer = line[7:].strip()
            elif line.lower().startswith("hint:"):
                hint = line[5:].strip()
            elif line.lower().startswith("translation:"):
                translation = line[12:].strip()

        # Parse letters (space-separated)
        letters = letters_line.split()

        if letters:
            items.append({
                "letters": letters,
                "answer": answer or "".join(letters),
                "hint": hint,
                "translation": translation,
            })

    return {
        "type": "anagram",
        "items": items,
    }

def parse_errorcorrection_content(content: str) -> dict:
    """Parse error-correction items."""
    items = []

    parts = re.split(r"^\d+\.\s*", content, flags=re.MULTILINE)

    for part in parts[1:]:
        lines = part.strip().split("\n")
        if not lines:
            continue

        sentence = lines[0].strip()
        error_word = None
        correct_form = ""
        options = []
        explanation = ""

        for line in lines[1:]:
            line = line.strip()
            if line.lower().startswith("error:"):
                error_word = line[6:].strip()
                if error_word.lower() == "none":
                    error_word = None
            elif line.lower().startswith("correct:"):
                correct_form = line[8:].strip()
            elif line.lower().startswith("options:"):
                opts = line[8:].strip()
                options = [o.strip() for o in opts.split(",")]
            elif line.startswith(">"):
                explanation = line[1:].strip()

        if sentence:
            items.append({
                "sentence": sentence,
                "errorWord": error_word,
                "correctForm": correct_form,
                "options": options,
                "explanation": explanation,
            })

    return {
        "type": "error-correction",
        "items": items,
    }

def parse_select_content(content: str) -> dict:
    """Parse select (multi-choice) items."""
    items = []

    parts = re.split(r"^\d+\.\s*", content, flags=re.MULTILINE)

    for part in parts[1:]:
        lines = part.strip().split("\n")
        if not lines:
            continue

        question = lines[0].strip()
        options = []
        correct_answers = []

        for line in lines[1:]:
            line = line.strip()
            if line.startswith("-"):
                opt = line[1:].strip()
                if opt.startswith("[x]"):
                    text = opt[3:].strip()
                    options.append(text)
                    correct_answers.append(text)
                elif opt.startswith("[ ]"):
                    options.append(opt[3:].strip())

        if question and options:
            items.append({
                "question": question,
                "options": options,
                "correctAnswers": correct_answers,
            })

    return {
        "type": "select",
        "items": items,
    }

def parse_cloze_content(content: str) -> dict:
    """Parse cloze passage."""
    # Extract passage text and blanks
    text = ""
    blanks = []

    lines = content.split("\n")
    for line in lines:
        line = line.strip()
        if line.startswith(">"):
            # This is the passage
            text = line[1:].strip()
        elif line.lower().startswith("blank"):
            # blank1: answer, options: a, b, c
            match = re.match(r"blank(\d+):\s*(\w+)(?:,\s*options:\s*(.+))?", line, re.IGNORECASE)
            if match:
                idx = int(match.group(1)) - 1
                answer = match.group(2)
                opts = match.group(3).split(",") if match.group(3) else [answer]
                blanks.append({
                    "index": idx,
                    "answer": answer,
                    "options": [o.strip() for o in opts],
                })

    return {
        "type": "cloze",
        "text": text,
        "blanks": blanks,
    }

# =============================================================================
# MODULE PARSER
# =============================================================================

def parse_module(content: str, level: str, module_num: int) -> dict:
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

def render_vibe_json(parsed: dict, lang_pair: str) -> dict:
    """Render parsed module to Vibe JSON format."""
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
            "owner": "curricula-opus",
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
        "owner": "curricula-opus",
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

    return {
        "$schema": "../../../schemas/vibe-module.schema.json",
        "lesson": lesson,
        "activities": vibe_activities,
        "vocabulary": vocab_section,
    }

# =============================================================================
# MAIN
# =============================================================================

def main():
    args = sys.argv[1:]
    target_lang_pair = args[0] if len(args) > 0 else None
    target_level = args[1].lower() if len(args) > 1 else None
    target_module_num = int(args[2]) if len(args) > 2 else None

    print("\n🚀 Curricula-Opus JSON Generator (Python)\n")
    print("Source: curriculum/[lang]/[level]/*.md")
    print("Output: output/json/\n")

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

                    # Parse module
                    parsed = parse_module(md_content, level_folder, module_num)

                    # Render to JSON
                    vibe_json = render_vibe_json(parsed, lang_pair)

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
