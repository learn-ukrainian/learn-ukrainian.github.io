#!/usr/bin/env python3
"""
Regenerate module_metadata.json from current curriculum structure.

This creates the module metadata needed for resource mapping with correct keys.
Key format: {level}-{module_num:02d}-{slug} (e.g., a1-01-the-cyrillic-code-i)
"""

import json
import re
import yaml
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent
CURRICULUM_DIR = PROJECT_ROOT / 'curriculum' / 'l2-uk-en'
OUTPUT_FILE = PROJECT_ROOT / 'docs' / 'resources' / 'ukrainianlessons' / 'module_metadata.json'


def extract_module_info(md_file: Path, level: str) -> dict | None:
    """Extract module info from a markdown file."""
    match = re.match(r'^(\d+)-(.+)\.md$', md_file.name)
    if not match:
        return None
    
    module_num = int(match.group(1))
    slug = match.group(2)
    
    # Read file content
    content = md_file.read_text(encoding='utf-8')
    
    # Extract title from H1
    title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    title = title_match.group(1) if title_match else slug.replace('-', ' ').title()
    
    # Try to load metadata from YAML sidecar
    meta_file = md_file.parent / 'meta' / f'{md_file.stem}.yaml'
    meta_data = {}
    if meta_file.exists():
        with open(meta_file, 'r', encoding='utf-8') as f:
            meta_data = yaml.safe_load(f) or {}
    
    # Extract topics from content headers
    headers = re.findall(r'^#{2,3}\s+(.+)$', content, re.MULTILINE)
    topics = [h.lower().strip() for h in headers if not h.startswith('🎯') and not h.startswith('📋')]
    
    # Try to load vocabulary from YAML sidecar
    vocab_file = md_file.parent / 'vocabulary' / f'{md_file.stem}.yaml'
    vocabulary = []
    if vocab_file.exists():
        with open(vocab_file, 'r', encoding='utf-8') as f:
            vocab_data = yaml.safe_load(f) or {}
            items = vocab_data.get('items', [])
            vocabulary = [item.get('lemma', '') for item in items if item.get('lemma')]
    
    # Also check for inline vocabulary table
    if not vocabulary:
        vocab_match = re.search(r'\|\s*Word\s*\|.*?\n\|[-\s|]+\n((?:\|.+\|\n?)+)', content, re.IGNORECASE)
        if vocab_match:
            for row in vocab_match.group(1).strip().split('\n'):
                cells = [c.strip() for c in row.split('|') if c.strip()]
                if cells:
                    vocabulary.append(cells[0])
    
    # Create module_id matching expected format for resource lookup
    # Format: {level}-{filename_stem} = a1-01-the-cyrillic-code-i
    module_id = f'{level}-{md_file.stem}'
    
    return {
        'module_id': module_id,
        'level': level.upper(),
        'module_num': module_num,
        'title': title,
        'subtitle': meta_data.get('subtitle', ''),
        'file_path': str(md_file.relative_to(PROJECT_ROOT)),
        'topics': topics[:10],  # Limit to first 10 topics
        'vocabulary': vocabulary[:30],  # Limit to first 30 vocab words
        'vocab_count': len(vocabulary),
        'focus': meta_data.get('focus', ''),
        'tags': meta_data.get('tags', []),
    }


def main():
    print("🔄 Regenerating module_metadata.json\n")
    
    modules = {}
    levels = ['a1', 'a2', 'b1', 'b2', 'c1', 'c2', 'lit']
    
    for level in levels:
        level_dir = CURRICULUM_DIR / level
        if not level_dir.exists():
            continue
        
        module_files = sorted(level_dir.glob('*.md'))
        level_count = 0
        
        for md_file in module_files:
            info = extract_module_info(md_file, level)
            if info:
                modules[info['module_id']] = info
                level_count += 1
        
        print(f"  {level.upper()}: {level_count} modules")
    
    # Save output
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(modules, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Saved {len(modules)} modules to {OUTPUT_FILE}")
    
    # Show sample keys
    print("\n📋 Sample module_ids:")
    for i, key in enumerate(list(modules.keys())[:5]):
        print(f"   {key}")
    print("   ...")


if __name__ == '__main__':
    main()
