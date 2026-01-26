#!/usr/bin/env python3
"""
scripts/fix_essay_sections.py

Migrates "## Есе" sections from B2-HIST Markdown files to activities/*.yaml.
Updates meta/*.yaml to remove the essay section from the outline.

Usage:
    python scripts/fix_essay_sections.py --slug <slug>  (Run on single module)
    python scripts/fix_essay_sections.py --all          (Run on all B2-HIST modules)
"""

import os
import re
import sys
import yaml
import argparse
from pathlib import Path

# Paths
CURRICULUM_DIR = Path("curriculum/l2-uk-en/b2-hist")
META_DIR = CURRICULUM_DIR / "meta"
ACTIVITIES_DIR = CURRICULUM_DIR / "activities"

def load_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def save_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def yaml_load(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def yaml_dump(path, data):
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False, width=float("inf"))

def clean_markdown_section(content):
    """
    Extracts the content of the ## Есе section and returns (essay_content, cleaned_full_content).
    """
    # Regex to find ## Есе section up to the next ## or end of file
    # Handles variations like "## Есе", "## Есе: ...", "## Essay"
    pattern = re.compile(r"(^|\n)#{1,2}\s+(Есе|Essay).*?\n(.*?)(?=\n#{1,2}\s|\Z)", re.DOTALL | re.MULTILINE)
    
    match = pattern.search(content)
    if not match:
        return None, content

    full_match = match.group(0)
    essay_body = match.group(3).strip()
    
    # Remove the section from content
    # We replace with empty string, but need to be careful about newlines
    cleaned_content = content.replace(full_match, "")
    
    return essay_body, cleaned_content

def update_activity_file(slug, essay_content):
    """
    Updates or creates the essay-response activity in the YAML file.
    """
    activity_path = ACTIVITIES_DIR / f"{slug}.yaml"
    
    if not activity_path.exists():
        print(f"  ⚠️  Activity file not found: {activity_path}")
        return False

    try:
        data = yaml_load(activity_path)
    except Exception as e:
        print(f"  ❌ Error parsing YAML {activity_path}: {e}")
        return False

    activities_list = []
    if isinstance(data, list):
        activities_list = data
    elif isinstance(data, dict) and 'activities' in data:
        activities_list = data['activities']
    else:
        print(f"  ❌ Unknown YAML format in {activity_path}")
        return False

    found = False
    for activity in activities_list:
        if activity.get('type') == 'essay-response':
            # Update existing essay prompt
            # We append the extracted Markdown text to the prompt or rubric
            # prioritizing the 'prompt' field if it's text, or creating a new instructional field
            
            # Strategy: If the extracted content is complex (bullet points, etc), 
            # we might want to put it in 'instruction' or 'context'.
            # For now, let's prepend/append to 'prompt' or 'instruction'.
            
            # Simple approach: Overwrite 'instruction' or 'prompt' with the rich text?
            # User wants to KEEP the rich context.
            
            # Let's clean the markdown specific artifacts if needed (like bolding) but usually safe.
            
            # If prompt exists, let's look at it.
            current_prompt = activity.get('prompt', "")
            
            # We will merge them: Markdown Content + \n\n + Old Prompt (if short)
            # Actually, usually the Markdown has the *real* prompts (Theme 1, Theme 2).
            # The YAML usually has a stub or a duplicate.
            
            # Let's replace 'instruction' with the Markdown Body, because that's usually where the meat is.
            # And ensure 'prompt' is generic like "Choose one topic..."
            
            activity['instruction'] = essay_content
            # Ensure prompt is present
            if 'prompt' not in activity:
                activity['prompt'] = "Оберіть одну з тем та напишіть есе."
            
            found = True
            print(f"  ✅ Updated existing essay-response in {slug}.yaml")
            break
    
    if not found:
        # Create new activity
        new_activity = {
            'type': 'essay-response',
            'title': 'Есе: Рефлексія та Аналіз',
            'instruction': essay_content,
            'prompt': "Напишіть есе на основі наведених тем.",
            'min_words': 250,
            'rubric': [
                {'criteria': 'Argumentation', 'points': 40, 'description': 'Logic and evidence'},
                {'criteria': 'Historical Accuracy', 'points': 30, 'description': 'Use of facts'},
                {'criteria': 'Language', 'points': 30, 'description': 'Grammar and style'}
            ]
        }
        if isinstance(data, list):
            data.append(new_activity)
        elif isinstance(data, dict):
            data['activities'].append(new_activity)
        print(f"  ✨ Created NEW essay-response in {slug}.yaml")

    yaml_dump(activity_path, data)
    return True

def update_meta_outline(slug):
    """
    Removes the 'Есе' section from content_outline in meta YAML.
    """
    meta_path = META_DIR / f"{slug}.yaml"
    
    if not meta_path.exists():
        print(f"  ⚠️  Meta file not found: {meta_path}")
        return False
        
    try:
        meta = yaml_load(meta_path)
    except Exception as e:
        print(f"  ❌ Error parsing YAML {meta_path}: {e}")
        return False

    if 'content_outline' not in meta:
        return True

    new_outline = []
    removed = False
    
    for section in meta['content_outline']:
        # Check if section title contains "Есе" or "Essay"
        title = section.get('section', '').lower()
        if 'есе' in title or 'essay' in title:
            removed = True
            print(f"  🗑️  Removed '{section['section']}' from outline in {slug}.yaml")
            continue
        new_outline.append(section)
    
    if removed:
        meta['content_outline'] = new_outline
        yaml_dump(meta_path, meta)
        
    return True

def process_module(slug):
    md_path = CURRICULUM_DIR / f"{slug}.md"
    
    if not md_path.exists():
        print(f"❌ Markdown not found: {md_path}")
        return

    content = load_file(md_path)
    
    print(f"🔍 Processing {slug}...")
    
    # 1. Extract and Clean Markdown
    essay_body, cleaned_content = clean_markdown_section(content)
    
    if not essay_body:
        print(f"  ℹ️  No ## Есе section found in Markdown.")
        return

    print(f"  📄 Found essay section ({len(essay_body)} chars)")

    # 2. Update Activity
    if update_activity_file(slug, essay_body):
        # 3. Save Cleaned Markdown (only if activity update succeeded)
        save_file(md_path, cleaned_content)
        print(f"  💾 Saved cleaned Markdown: {slug}.md")
        
        # 4. Update Meta Outline
        update_meta_outline(slug)

def main():
    parser = argparse.ArgumentParser(description="Migrate Essay sections.")
    parser.add_argument("--slug", help="Specific module slug to process")
    parser.add_argument("--all", action="store_true", help="Process all B2-HIST modules")
    
    args = parser.parse_args()
    
    if args.slug:
        process_module(args.slug)
    elif args.all:
        # Find all .md files in the directory
        for filename in os.listdir(CURRICULUM_DIR):
            if filename.endswith(".md"):
                slug = filename[:-3]
                process_module(slug)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
