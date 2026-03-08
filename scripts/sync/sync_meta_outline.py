#!/usr/bin/env python3
"""
Sync Meta Outline Script v1.2

Automatically parses a module's Markdown file, counts words per section,
and updates the 'content_outline' in the corresponding meta YAML file.
Ensures 'points' field exists to satisfy strict seminar schemas.
"""

import re
import sys
from pathlib import Path

import yaml


def extract_actual_sections(md_path: Path) -> list[dict]:
    """Extract section headers and word counts. MATCHES auditor logic."""
    with open(md_path, encoding="utf-8") as f:
        content = f.read()

    sections = {}
    current_section = None
    current_words = 0
    lines = content.split("\n")
    in_frontmatter = False
    skip_until = 0

    for idx, line in enumerate(lines):
        if line.strip() == "---":
            if not in_frontmatter:
                in_frontmatter = True
                skip_until = idx
            else:
                in_frontmatter = False
                skip_until = idx + 1
                continue
        if idx < skip_until:
            continue

        header_match = re.match(r"^#{1,2}\s+(.+)$", line)
        if header_match:
            if not sections and line.strip().startswith("# "):
                continue
            if current_section:
                sections[current_section] = current_words

            name = header_match.group(1).strip()
            name = re.sub(r"\s*[—–:-]\s*.*$", "", name)
            name = re.sub(r"[📚🎯💡🔍]", "", name).strip()
            current_section = name
            current_words = 0
        else:
            if not line.strip().startswith("```") and not line.strip().startswith("---") and not line.strip().startswith("#"):
                text = line
                if line.strip().startswith(">"):
                    text = re.sub(r"^[\s>]+", "", line)
                    if text.strip().startswith("[!"):
                        continue
                words = re.findall(r"[а-яіїєґА-ЯІЇЄҐA-Za-z]+", text)
                current_words += len(words)

    if current_section:
        sections[current_section] = current_words

    return [{"section": k, "words": v, "points": []} for k, v in sections.items()]

def update_meta_yaml(md_path: Path, new_outline: list[dict]):
    meta_path = md_path.parent / "meta" / f"{md_path.stem}.yaml"
    if not meta_path.exists():
        return

    with open(meta_path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    # Preserve existing points if the section name matches
    if "content_outline" in data:
        old_outline = {s['section']: s.get('points', []) for s in data['content_outline']}
        for new_sec in new_outline:
            if new_sec['section'] in old_outline:
                new_sec['points'] = old_outline[new_sec['section']]

    data["content_outline"] = new_outline

    # Ensure ID exists (scholar requirement)
    if "id" not in data:
        data["id"] = f"{data.get('level', 'LIT').lower()}-{md_path.stem}"

    with open(meta_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False, width=1000)

    print(f"✅ Successfully synced {meta_path.name} ({sum(s['words'] for s in new_outline)} words).")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(1)
    md_file = Path(sys.argv[1])
    update_meta_yaml(md_file, extract_actual_sections(md_file))
