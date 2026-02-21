#!/usr/bin/env python3
"""
Migrate Vocab to YAML
---------------------
Migrates monolithic Markdown modules to the new YAML architecture.
1. Extracts Frontmatter -> meta/{slug}.yaml
2. Extracts # Vocabulary table -> vocabulary/{slug}.yaml
3. (Optionally) Strips extracted data from the .md file
"""

import argparse
import re
import yaml
import sys
from pathlib import Path

# Custom YAML dumper to preserve order and format nicely
class MyDumper(yaml.SafeDumper):
    def increase_indent(self, flow=False, indentless=False):
        return super(MyDumper, self).increase_indent(flow, False)

def setup_dumper():
    yaml.add_representer(str, str_presenter, Dumper=MyDumper)

def str_presenter(dumper, data):
    if len(data.splitlines()) > 1:  # check for multiline string
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)

setup_dumper()

def parse_frontmatter(content):
    match = re.search(r'^---\n(.*?)\n---\n', content, re.DOTALL)
    if match:
        return yaml.safe_load(match.group(1)), match.group(0)
    return None, ""

def parse_vocab_table(content):
    # Find table under # Vocabulary or # Словник
    match = re.search(r'(#+ (Vocabulary|Словник).*?)\n(\|.*?\|\n\|[-:| ]+\|\n(.*?))\n(?=\n#|$)', content, re.DOTALL)
    if not match:
        return [], ""
    
    full_section = match.group(0)
    table_content = match.group(4)
    
    items = []
    for line in table_content.strip().split('\n'):
        if not line.strip().startswith('|'): continue
        parts = [p.strip() for p in line.strip('|').split('|')]
        
        # Expected: Word | IPA | English | POS | Gender | Note
        # But handle variations
        if len(parts) < 3: continue
        
        raw_pos = parts[3] if len(parts) > 3 and parts[3] else "other"
        # Fix legacy mapping
        if raw_pos == 'name': raw_pos = 'propn'
        
        item = {
            'lemma': parts[0],
            'ipa': parts[1] if parts[1] else "",
            'translation': parts[2] if parts[2] else "",
            'pos': raw_pos
        }
        
        if len(parts) > 4 and parts[4] and parts[4] != '-':
            item['gender'] = parts[4].replace('ч', 'm').replace('ж', 'f').replace('с', 'n')
        
        items.append(item)
        
    return items, full_section

def migrate_module(file_path, dry_run=False):
    print(f"Processing {file_path.name}...")
    content = file_path.read_text(encoding='utf-8')
    
    # 1. Frontmatter -> Meta
    frontmatter, fm_raw = parse_frontmatter(content)
    if not frontmatter:
        print(f"  ❌ No frontmatter found. Skipping.")
        return

    slug = file_path.stem
    level_dir = file_path.parent
    
    # Create Dirs
    (level_dir / "meta").mkdir(exist_ok=True)
    (level_dir / "vocabulary").mkdir(exist_ok=True)
    
    meta_path = level_dir / "meta" / f"{slug}.yaml"
    vocab_path = level_dir / "vocabulary" / f"{slug}.yaml"
    
    # Prepare Meta YAML
    meta_data = frontmatter
    meta_data['slug'] = slug
    
    # 2. Vocab -> Vocabulary YAML
    vocab_items, vocab_raw = parse_vocab_table(content)
    
    vocab_data = {
        'module': slug,
        'level': frontmatter.get('phase', 'UA').split('.')[0],
        'version': '2.0',
        'items': vocab_items
    }
    
    if dry_run:
        print(f"  [Dry Run] Would write {meta_path}")
        print(f"  [Dry Run] Would write {vocab_path} ({len(vocab_items)} items)")
        return

    # Write Files
    with open(meta_path, 'w', encoding='utf-8') as f:
        yaml.dump(meta_data, f, Dumper=MyDumper, sort_keys=False, allow_unicode=True)
        
    with open(vocab_path, 'w', encoding='utf-8') as f:
        yaml.dump(vocab_data, f, Dumper=MyDumper, sort_keys=False, allow_unicode=True)
        
    # Strip Content from Source MD
    # 1. Remove Frontmatter
    new_content = content.replace(fm_raw, "")
    
    # 2. Remove Vocabulary Table
    if vocab_raw:
        new_content = new_content.replace(vocab_raw, "")
        
    # 3. Clean up multiple newlines at end of file
    new_content = re.sub(r'\n{3,}', '\n\n', new_content).strip() + "\n"
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"  ✅ Migrated: {meta_path}, {vocab_path} (And stripped MD)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('files', nargs='+', type=Path)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    
    for f in args.files:
        if f.exists():
            migrate_module(f, args.dry_run)
