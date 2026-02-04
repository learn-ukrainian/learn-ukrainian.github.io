#!/usr/bin/env python3
"""
Generate module plan files for OES and RUTH tracks from mapping files.
Source: Gemini Research (ISSUE-490-496, ISSUE-501)
"""

import yaml
from pathlib import Path

PLANS_DIR = Path("curriculum/l2-uk-en/plans")

def load_mapping(track: str) -> dict:
    """Load mapping file for a track."""
    mapping_path = PLANS_DIR / f"{track}_mapping.yaml"
    with open(mapping_path) as f:
        return yaml.safe_load(f)

def get_phase_info(track: str, module_num: int) -> dict:
    """Get phase information based on module number."""
    phases = {
        "oes": [
            (1, 25, "vernacular-foundations", "Vernacular Foundations", "ISSUE-501"),
            (26, 50, "literary-tradition", "Literary Tradition", "ISSUE-490"),
            (51, 75, "legal-tradition", "Legal Tradition", "ISSUE-491"),
            (76, 100, "literary-art", "Literary Art", "ISSUE-492"),
        ],
        "ruth": [
            (1, 25, "chancery-legal", "Chancery & Legal", "ISSUE-493"),
            (26, 50, "sacred-word", "Sacred Word", "ISSUE-494"),
            (51, 75, "baroque-fight", "Baroque Fight", "ISSUE-495"),
            (76, 100, "cossack-word", "Cossack Word", "ISSUE-496"),
        ],
    }

    for start, end, phase_id, phase_name, source_issue in phases[track]:
        if start <= module_num <= end:
            return {
                "phase": (module_num - 1) // 25 + 1,
                "phase_id": phase_id,
                "phase_name": phase_name,
                "source_issue": source_issue,
            }
    return {}

def generate_plan(track: str, module_num: int, module_data: dict) -> str:
    """Generate YAML content for a module plan."""
    phase_info = get_phase_info(track, module_num)
    slug = module_data["slug"]
    title_uk = module_data["title_uk"]
    title_en = module_data["title_en"]
    focus = module_data["focus"]

    # Determine word target
    is_checkpoint = "checkpoint" in slug or "capstone" in slug
    is_lab = "lab" in slug
    word_target = 2500 if is_checkpoint or is_lab else 3500

    plan = f'''# Module Plan: {title_en}
# Track: {track.upper()}
# Module: {module_num:03d}
# Source: Gemini Research ({phase_info["source_issue"]})
# Generated: 2026-02-04

module_number: {module_num}
slug: {slug}
title_uk: "{title_uk}"
title_en: "{title_en}"

phase: {phase_info["phase"]}
phase_id: {phase_info["phase_id"]}
phase_name: "{phase_info["phase_name"]}"

focus: "{focus}"

word_target: {word_target}

# Content outline to be expanded during content generation
content_outline:
  - section: "Вступ"
    description: "Introduction to {title_en}"
  - section: "Основний матеріал"
    description: "Primary source analysis and grammar focus"
  - section: "Практика"
    description: "Exercises and activities"
  - section: "Підсумок"
    description: "Summary and connection to next module"

# Vocabulary hints (to be populated during content generation)
vocabulary_hints: []

# Activity types appropriate for this module
activity_types:
'''

    # Add activity types based on track and content
    if track == "oes":
        activities = ["transcription", "etymology-trace", "grammar-identify"]
        if "lab" in slug:
            if "phonology" in slug:
                activities.append("phonology-lab")
            else:
                activities.append("grammar-lab")
        if "paleography" in slug or "graffiti" in slug:
            activities.append("paleography-analysis")
    else:  # ruth
        activities = ["transcription", "etymology-trace", "grammar-identify"]
        if "lab" in slug:
            activities.append("grammar-lab")
        if "parallel" in slug or "contrast" in slug:
            activities.append("parallel-text")
        if "paleography" in slug or "skoropys" in slug:
            activities.append("paleography-analysis")
        if "capstone" in slug:
            activities.append("historical-writing")
        if "register" in slug or "stylistic" in slug:
            activities.append("register-identify")
        if "polonism" in slug or "latinism" in slug or "loanword" in slug:
            activities.append("loanword-trace")

    for activity in activities:
        plan += f"  - {activity}\n"

    return plan

def main():
    for track in ["oes", "ruth"]:
        print(f"Generating {track.upper()} module plans...")
        mapping = load_mapping(track)

        output_dir = PLANS_DIR / track
        output_dir.mkdir(exist_ok=True)

        for key, module_data in mapping.items():
            module_num = int(key)
            slug = module_data["slug"]

            plan_content = generate_plan(track, module_num, module_data)

            output_path = output_dir / f"{slug}.yaml"
            with open(output_path, "w") as f:
                f.write(plan_content)

            print(f"  Created: {output_path}")

        print(f"  Total: {len(mapping)} modules")

    print("\nDone!")

if __name__ == "__main__":
    main()
