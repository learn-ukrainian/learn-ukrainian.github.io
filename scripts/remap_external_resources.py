#!/usr/bin/env python3
"""
Remap external_resources.yaml keys to match current module structure.

This script:
1. Loads the backup external_resources.yaml (with curated content)
2. Creates a mapping from old module slugs to new module keys
3. Remaps all resources to the new keys
4. Handles edge cases (renamed, removed, or reorganized modules)
"""

import yaml
import re
from pathlib import Path
from collections import defaultdict

from slug_utils import to_bare_slug


PROJECT_ROOT = Path(__file__).parent.parent
CURRICULUM_DIR = PROJECT_ROOT / 'curriculum' / 'l2-uk-en'
BACKUP_FILE = PROJECT_ROOT / 'docs' / 'resources' / 'external_resources.yaml.backup'
OUTPUT_FILE = PROJECT_ROOT / 'docs' / 'resources' / 'external_resources.yaml'


def get_current_modules() -> dict:
    """Get current module slugs and their info."""
    modules = {}
    levels = ['a1', 'a2', 'b1', 'b2', 'c1', 'c2', 'lit']
    
    for level in levels:
        level_dir = CURRICULUM_DIR / level
        if not level_dir.exists():
            continue
        
        for md_file in level_dir.glob('*.md'):
            match = re.match(r'^(\d+)-(.+)\.md$', md_file.name)
            if match:
                module_num = int(match.group(1))
                slug = match.group(2)
                
                # Read title from file
                content = md_file.read_text(encoding='utf-8')
                title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
                title = title_match.group(1) if title_match else slug.replace('-', ' ').title()
                
                # New key format: {level}-{stem}
                new_key = f'{level}-{md_file.stem}'
                
                modules[new_key] = {
                    'level': level,
                    'module_num': module_num,
                    'slug': slug,
                    'title': title,
                    'stem': md_file.stem,
                }
    
    return modules


def extract_topic_keywords(slug: str) -> set:
    """Extract topic keywords from a slug."""
    # Remove common suffixes/prefixes
    slug = slug.lower()
    slug = to_bare_slug(slug)  # Remove leading numbers
    
    # Split on hyphens and underscores
    words = set(re.split(r'[-_]', slug))
    
    # Remove common stopwords
    stopwords = {'the', 'a', 'an', 'and', 'or', 'of', 'in', 'to', 'for', 'with', 'on', 'at', 'i', 'ii', 'iii'}
    words -= stopwords
    
    return words


def find_best_match(old_key: str, old_resources: dict, current_modules: dict) -> tuple[str | None, float]:
    """
    Find the best matching new key for an old resource key.
    
    Returns (new_key, confidence_score)
    """
    # Parse old key: a1-01-the-cyrillic-code-i or a1-the-cyrillic-code-i
    match = re.match(r'^([abc]\d|lit)-(?:(\d+)-)?(.+)$', old_key)
    if not match:
        return None, 0.0
    
    old_level = match.group(1)
    old_num = int(match.group(2)) if match.group(2) else None
    old_slug = match.group(3)
    old_keywords = extract_topic_keywords(old_slug)
    
    best_match = None
    best_score = 0.0
    
    for new_key, info in current_modules.items():
        new_level = info['level']
        new_num = info['module_num']
        new_slug = info['slug']
        new_keywords = extract_topic_keywords(new_slug)
        
        # Must match level
        if new_level != old_level:
            continue
        
        score = 0.0
        
        # Exact slug match (highest confidence)
        if old_slug == new_slug:
            score = 1.0
        else:
            # Keyword overlap
            overlap = len(old_keywords & new_keywords)
            if overlap > 0:
                score = overlap / max(len(old_keywords), len(new_keywords))
            
            # Module number match bonus
            if old_num and old_num == new_num:
                score += 0.3
        
        if score > best_score:
            best_score = score
            best_match = new_key
    
    return best_match, best_score


def main():
    print("🔄 Remapping external_resources.yaml keys\n")
    
    # Load backup
    if not BACKUP_FILE.exists():
        print(f"❌ Backup file not found: {BACKUP_FILE}")
        return
    
    with open(BACKUP_FILE, 'r', encoding='utf-8') as f:
        backup_data = yaml.safe_load(f)
    
    old_resources = backup_data.get('resources', {})
    print(f"📂 Loaded {len(old_resources)} resource entries from backup")
    
    # Get current modules
    current_modules = get_current_modules()
    print(f"📂 Found {len(current_modules)} current modules\n")
    
    # Create new resources mapping
    new_resources = {}
    matched = 0
    unmatched = []
    low_confidence = []
    
    for old_key, resources in old_resources.items():
        new_key, confidence = find_best_match(old_key, resources, current_modules)
        
        if new_key and confidence >= 0.5:
            # Merge if key already exists (shouldn't happen normally)
            if new_key in new_resources:
                for rtype, items in resources.items():
                    if rtype in new_resources[new_key]:
                        new_resources[new_key][rtype].extend(items)
                    else:
                        new_resources[new_key][rtype] = items
            else:
                new_resources[new_key] = resources
            
            matched += 1
            
            if confidence < 0.8:
                low_confidence.append((old_key, new_key, confidence))
        else:
            unmatched.append((old_key, new_key, confidence))
    
    print(f"✅ Matched: {matched}")
    print(f"⚠️  Low confidence: {len(low_confidence)}")
    print(f"❌ Unmatched: {len(unmatched)}\n")
    
    # Show some examples
    if low_confidence:
        print("📋 Low confidence matches (review recommended):")
        for old, new, conf in low_confidence[:10]:
            print(f"   {old} → {new} ({conf:.0%})")
        if len(low_confidence) > 10:
            print(f"   ... and {len(low_confidence) - 10} more")
        print()
    
    if unmatched:
        print("📋 Unmatched keys (dropped):")
        for old, new, conf in unmatched[:10]:
            print(f"   {old}")
        if len(unmatched) > 10:
            print(f"   ... and {len(unmatched) - 10} more")
        print()
    
    # Save new resources
    output_data = {
        'version': '2.0',
        'generated_at': '2026-01-07',
        'resources': dict(sorted(new_resources.items()))
    }
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        yaml.dump(output_data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    
    print(f"💾 Saved {len(new_resources)} remapped entries to {OUTPUT_FILE}")
    
    # Summary by level
    print("\n📊 Summary by level:")
    level_counts = defaultdict(int)
    for key in new_resources:
        level = key.split('-')[0]
        level_counts[level] += 1
    
    for level in ['a1', 'a2', 'b1', 'b2', 'c1', 'c2', 'lit']:
        if level in level_counts:
            print(f"   {level.upper()}: {level_counts[level]} modules with resources")


if __name__ == '__main__':
    main()
