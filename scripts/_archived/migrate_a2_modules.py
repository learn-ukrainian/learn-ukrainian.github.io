#!/usr/bin/env python3
import os
import re
import yaml
from pathlib import Path

LEVEL_DIR = Path('curriculum/l2-uk-en/a2')
META_DIR = LEVEL_DIR / 'meta'

def standardize_meta(file_path):
    if not file_path.exists():
        return
    with open(file_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    # Standardize duration (convert '60 min' to 60)
    if isinstance(data.get('duration'), str):
        match = re.search(r'(\d+)', data['duration'])
        if match:
            data['duration'] = int(match.group(1))
    
    # Standardize counts
    if 'vocab_count' in data and 'vocabulary_count' not in data:
        data['vocabulary_count'] = data.pop('vocab_count')
    elif 'vocab_count' in data:
        data.pop('vocab_count')
    
    # Add focus if missing
    if 'focus' not in data:
        # Heuristic for A2
        title = data.get('title', '').lower()
        if 'checkpoint' in title or 'final review' in title or 'grammar review' in title:
            data['focus'] = 'checkpoint'
        elif 'at the' in title or 'shopping' in title or 'cooking' in title or 'nature' in title or 'hobbies' in title or 'work' in title or 'technology' in title or 'sports' in title or 'health' in title:
            data['focus'] = 'vocabulary'
        else:
            data['focus'] = 'grammar'
            
    # Ensure tags are a list
    if 'tags' in data and isinstance(data['tags'], str):
        data['tags'] = [t.strip() for t in data['tags'].split(',')]

    with open(file_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, sort_keys=False, allow_unicode=True)

def standardize_md(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove any existing frontmatter
    if content.startswith('---'):
        content = re.sub(r'^---\n(.*?)\n---\n', '', content, flags=re.DOTALL)
    
    # Canonical headers
    headers = [
        ('summary', r'^#+\s+(Summary|Підсумок)'),
        ('resources', r'^#+\s+(External Resources|Зовнішні ресурси|Resources)'),
        ('activities', r'^#+\s+(Activities|Вправи)'),
        ('vocabulary', r'^#+\s+(Vocabulary|Словник)'),
        ('self_assessment', r'^#+\s+(Self-Assessment|Самооцінка)')
    ]
    
    lines = content.split('\n')
    
    # Find positions of existing sections
    found_headers = {}
    for i, line in enumerate(lines):
        for key, pattern in headers:
            if re.match(pattern, line.strip(), re.IGNORECASE):
                found_headers[key] = i
    
    # Determine where the "end section" starts
    keys_order = ['summary', 'resources', 'activities', 'vocabulary', 'self_assessment']
    first_end_idx = len(lines)
    for key in keys_order:
        if key in found_headers:
            first_end_idx = min(first_end_idx, found_headers[key])
            break
            
    # Extract body content (before any end headers)
    body_content = '\n'.join(lines[:first_end_idx]).strip()
    
    # Clean up trailing separators in body
    body_content = re.sub(r'\n---+\n*$', '', body_content).strip()
    
    # Assemble final content
    new_content = body_content + '\n\n'
    
    # 1. Summary (# Підсумок) - MANDATORY in MD
    if 'summary' in found_headers:
        idx = found_headers['summary']
        # Find next section
        next_idx = len(lines)
        for i in range(idx + 1, len(lines)):
            if re.match(r'^#+\s+', lines[i].strip()):
                next_idx = i
                break
        
        summary_body = '\n'.join(lines[idx+1:next_idx]).strip()
        new_content += "# Підсумок\n\n" + summary_body + '\n\n'
    else:
        # Add placeholder if missing
        new_content += '# Підсумок\n\n'
        
    # 2. Self-Assessment (Optional)
    if 'self_assessment' in found_headers:
        idx = found_headers['self_assessment']
        next_idx = len(lines)
        for i in range(idx + 1, len(lines)):
            if re.match(r'^#+\s+', lines[i].strip()):
                next_idx = i
                break
        sa_body = '\n'.join(lines[idx+1:next_idx]).strip()
        new_content += "## Самооцінка\n\n" + sa_body + '\n\n'

    # Note: Activities, Resources, and Vocabulary headers ARE NOT ADDED.
    # The build system handles them.
    
    new_content = new_content.strip() + '\n'
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

def main():
    print("Standardizing A2 modules...")
    for i in range(1, 59):
        # Find the MD file (some might have different names, but let's assume slug match)
        # We find MD files in the directory
        pattern = f"{i:02d}-"
        matching_files = list(LEVEL_DIR.glob(f"{pattern}*.md"))
        if not matching_files:
            continue
        
        md_file = matching_files[0]
        meta_file = META_DIR / (md_file.stem + '.yaml')
        
        print(f"Processing {md_file.name}...")
        standardize_meta(meta_file)
        standardize_md(md_file)
    print("Done.")

if __name__ == "__main__":
    main()
