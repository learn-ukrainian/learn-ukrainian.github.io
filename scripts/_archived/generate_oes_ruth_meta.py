#!/usr/bin/env python3
"""
Generate meta files for OES and RUTH tracks from mapping files.
Source: Gemini Research (ISSUE-490-496, ISSUE-501)
"""

import yaml
from pathlib import Path

PLANS_DIR = Path("curriculum/l2-uk-en/plans")
CURRICULUM_DIR = Path("curriculum/l2-uk-en")

def load_mapping(track: str) -> dict:
    """Load mapping file for a track."""
    mapping_path = PLANS_DIR / f"{track}_mapping.yaml"
    with open(mapping_path) as f:
        return yaml.safe_load(f)

def get_phase_info(track: str, module_num: int) -> dict:
    """Get phase information based on module number."""
    phases = {
        "oes": [
            (1, 25, "vernacular-foundations", "Vernacular Foundations"),
            (26, 50, "literary-tradition", "Literary Tradition"),
            (51, 75, "legal-tradition", "Legal Tradition"),
            (76, 100, "literary-art", "Literary Art"),
        ],
        "ruth": [
            (1, 25, "chancery-legal", "Chancery & Legal"),
            (26, 50, "sacred-word", "Sacred Word"),
            (51, 75, "baroque-fight", "Baroque Fight"),
            (76, 100, "cossack-word", "Cossack Word"),
        ],
    }

    for start, end, phase_id, phase_name in phases[track]:
        if start <= module_num <= end:
            return {
                "phase": (module_num - 1) // 25 + 1,
                "phase_id": phase_id,
                "phase_name": phase_name,
            }
    return {}

def generate_meta(track: str, module_num: int, module_data: dict) -> str:
    """Generate YAML content for a module meta file."""
    phase_info = get_phase_info(track, module_num)
    slug = module_data["slug"]
    title_uk = module_data["title_uk"]
    title_en = module_data["title_en"]
    focus = module_data["focus"]

    # Determine word target and type
    is_checkpoint = "checkpoint" in slug or "capstone" in slug
    is_lab = "lab" in slug
    is_review = "review" in slug

    if is_checkpoint:
        module_type = "checkpoint"
        word_target = 2500
        duration = 90
    elif is_lab:
        module_type = "lab"
        word_target = 2500
        duration = 60
    elif is_review:
        module_type = "review"
        word_target = 2500
        duration = 45
    else:
        module_type = "lesson"
        word_target = 3500
        duration = 60

    meta = f'''# Module Meta: {title_en}
# Track: {track.upper()}
# Module: {module_num:03d}
# Generated: 2026-02-04

module_number: {module_num}
slug: {slug}
title: "{title_uk}"
title_en: "{title_en}"

type: {module_type}
phase: {phase_info["phase"]}
phase_id: {phase_info["phase_id"]}

# Pedagogy
pedagogy: theory-first
duration_minutes: {duration}
word_target: {word_target}
immersion_level: 100

# Focus
grammar_focus: "{focus}"
vocabulary_focus: []
cultural_focus: []

# Activity hints (minimum counts)
activity_hints:
'''

    # Add activity type hints based on module type
    if is_checkpoint:
        meta += '''  - type: transcription
    min_items: 3
  - type: grammar-identify
    min_items: 5
'''
    elif is_lab:
        meta += '''  - type: grammar-lab
    min_items: 3
  - type: transcription
    min_items: 2
'''
    else:
        meta += '''  - type: transcription
    min_items: 2
  - type: etymology-trace
    min_items: 2
  - type: grammar-identify
    min_items: 3
'''

    # Add prerequisites
    if module_num > 1:
        meta += f'''
# Prerequisites
prerequisites:
  - module: {module_num - 1}
'''
    else:
        meta += '''
# Prerequisites
prerequisites: []
'''

    return meta

def main():
    for track in ["oes", "ruth"]:
        print(f"Generating {track.upper()} meta files...")
        mapping = load_mapping(track)

        output_dir = CURRICULUM_DIR / track / "meta"
        output_dir.mkdir(parents=True, exist_ok=True)

        for key, module_data in mapping.items():
            module_num = int(key)
            slug = module_data["slug"]

            meta_content = generate_meta(track, module_num, module_data)

            output_path = output_dir / f"{slug}.yaml"
            with open(output_path, "w") as f:
                f.write(meta_content)

            print(f"  Created: {output_path}")

        print(f"  Total: {len(mapping)} modules")

    print("\nDone!")

if __name__ == "__main__":
    main()
