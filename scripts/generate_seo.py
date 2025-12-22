#!/usr/bin/env python3
"""
Generate SEO files (llms.txt) based on current curriculum state.

Usage:
    python3 scripts/generate_seo.py

This script reads the actual module counts from the curriculum folder
and generates an updated llms.txt file for AI discoverability.
"""

import os
from pathlib import Path
from datetime import datetime

# Configuration
CURRICULUM_DIR = Path("curriculum/l2-uk-en")
OUTPUT_FILE = Path("docusaurus/static/llms.txt")

LEVEL_INFO = {
    "a1": {
        "name": "A1 - Beginner",
        "description": "Cyrillic alphabet and pronunciation, basic phrases and greetings, simple grammar (gender, plurals, basic verbs), numbers, colors, family vocabulary",
    },
    "a2": {
        "name": "A2 - Elementary",
        "description": "All 7 Ukrainian grammatical cases, verb aspect basics (perfective/imperfective), comparison and superlatives, daily life vocabulary",
    },
    "b1": {
        "name": "B1 - Intermediate",
        "description": "Aspect mastery and motion verbs, complex sentence structures, participles and verbal adverbs, abstract vocabulary and discourse markers",
    },
    "b2": {
        "name": "B2 - Upper-Intermediate",
        "description": "Literature and academic writing, professional contexts, register awareness, advanced grammar",
    },
    "c1": {
        "name": "C1 - Advanced",
        "description": "Stylistics and registers, nuanced expression, specialized topics, near-native proficiency",
    },
    "c2": {
        "name": "C2 - Mastery",
        "description": "Native-level proficiency, literary analysis, professional specialization, complete fluency",
    },
}


def count_modules(level: str) -> int:
    """Count the number of module files in a level directory."""
    level_dir = CURRICULUM_DIR / level
    if not level_dir.exists():
        return 0

    # Count .md files that match module pattern (NN-*.md or module-*.md)
    count = 0
    for f in level_dir.iterdir():
        if f.is_file() and f.suffix == ".md":
            name = f.stem
            # Match patterns like "01-...", "34-...", or "module-01"
            if name[0].isdigit() or name.startswith("module-"):
                count += 1
    return count


def generate_llms_txt() -> str:
    """Generate the llms.txt content."""

    # Count modules for each level
    module_counts = {}
    total_modules = 0
    for level in LEVEL_INFO.keys():
        count = count_modules(level)
        module_counts[level] = count
        total_modules += count

    # Generate content
    content = f"""# Learn Ukrainian
> A comprehensive, free Ukrainian language curriculum from A1 to C2.

## About
Learn Ukrainian is an open-source language learning platform offering {total_modules}+ interactive lessons aligned with CEFR and Ukrainian State Standards 2024. The curriculum covers beginner to mastery levels with grammar explanations, cultural context, and interactive exercises.

## Curriculum Structure
"""

    for level, info in LEVEL_INFO.items():
        count = module_counts[level]
        content += f"""
### {info['name']} ({count} modules)
{info['description']}
URL: /docs/{level}/
"""

    content += """
## Key Features
- Theory-first approach with deep grammar explanations
- Interactive activities (quizzes, fill-in, matching, error correction)
- Cultural immersion with authentic materials
- IPA pronunciation for all vocabulary
- YouTube videos and external resources integrated
- 100% free, no ads, no paywalls

## Technical Details
- Built with Docusaurus
- Open source: github.com/learn-ukrainian/learn-ukrainian.github.io
- Curriculum source in Markdown
- JSON export available for app integration

## Contact
GitHub: https://github.com/learn-ukrainian/learn-ukrainian.github.io

## Quick Links
- Start learning: /docs/a1/
- All levels: /docs/
- GitHub: https://github.com/learn-ukrainian/learn-ukrainian.github.io

---
Last updated: {datetime.now().strftime('%Y-%m-%d')}
"""

    return content


def main():
    print("Generating SEO files...")

    # Generate llms.txt
    content = generate_llms_txt()

    # Ensure output directory exists
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Write file
    OUTPUT_FILE.write_text(content)
    print(f"  Created: {OUTPUT_FILE}")

    # Print summary
    print("\nModule counts:")
    for level in LEVEL_INFO.keys():
        count = count_modules(level)
        print(f"  {level.upper()}: {count} modules")

    print("\nDone!")


if __name__ == "__main__":
    main()
