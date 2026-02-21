
import os
import re
import yaml
import argparse
from pathlib import Path

def setup_yaml():
    """Configure yaml to handle unicode and block style roughly."""
    yaml.safe_dump
    # We'll use safe_dump/safe_load but we want to avoid weird tags.
    pass

def extract_structure(md_path):
    """
    Extracts H2 sections and their H3 subsections (as points).
    Also counts words for each H2 section.
    """
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')
    sections = []
    current_section = None
    
    # Heuristic for frontmatter skip
    in_frontmatter = False
    start_idx = 0
    if lines[0].strip() == '---':
        in_frontmatter = True
        for i, line in enumerate(lines[1:], 1):
            if line.strip() == '---':
                start_idx = i + 1
                break

    for line in lines[start_idx:]:
        line_strip = line.strip()
        
        # H2 Detection
        h2_match = re.match(r'^##\s+(.+)$', line_strip)
        if h2_match:
            title = h2_match.group(1).strip()
            # Clean title
            title = re.sub(r'[📚🎯💡🔍⚠️]', '', title).strip()
            
            current_section = {
                'section': title,
                'words': 0,
                'points': []
            }
            sections.append(current_section)
            continue
            
        # H3 Detection (Points)
        h3_match = re.match(r'^###\s+(.+)$', line_strip)
        if h3_match and current_section:
            title = h3_match.group(1).strip()
            title = re.sub(r'[📚🎯💡🔍⚠️]', '', title).strip()
            # Add to points if not already there
            current_section['points'].append(title)
            # We don't continue here because H3 line also has words? Usually headers don't count towards word target in strict sense, but let's ignore header words for simplicity of logic.
            
        # Word Counting
        if current_section:
             if not line_strip.startswith('#') and \
                not line_strip.startswith('```') and \
                not line_strip.startswith('>') and \
                not line_strip.startswith('---') and \
                not line_strip.startswith('|'):
                words = re.findall(r'[а-яіїєґА-ЯІЇЄҐA-Za-z]+', line_strip)
                current_section['words'] += len(words)

    return sections

def update_yaml(meta_path, new_outline):
    """
    Updates the content_outline in the yaml file.
    """
    if not os.path.exists(meta_path):
        print(f"Meta file not found: {meta_path}")
        return False
        
    with open(meta_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
        
    if not data:
        data = {}
        
    # Update outline
    data['content_outline'] = new_outline
    
    # Also update word_target? No, leave it as configured.
    
    with open(meta_path, 'w', encoding='utf-8') as f:
        # allow_unicode=True is critical for Ukrainian
        yaml.dump(data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
        
    return True

def process_file(slug):
    base_dir = "curriculum/l2-uk-en/b2-hist"
    md_path = f"{base_dir}/{slug}.md"
    meta_path = f"{base_dir}/meta/{slug}.yaml"
    
    if not os.path.exists(md_path):
        print(f"Markdown not found for {slug}")
        return

    print(f"Processing {slug}...")
    structure = extract_structure(md_path)
    
    if not structure:
        print(f"  No H2 sections found in {slug}")
        return

    success = update_yaml(meta_path, structure)
    if success:
        print(f"  Updated outline in {meta_path}")

if __name__ == "__main__":
    slugs = [
        "trypillian-civilization",
        "scythians-sarmatians",
        "greeks-crimea-olbia",
        "sloviany-origins",
        "slavic-tribes",
        "zasnuvannia-kyieva",
        "khozary-i-sloviany",
        "syntez-vytoky-1",
        "oleh-ihor",
        "olha-sviatoslav",
        "volodymyr-khreshchennia",
        "yaroslav-wise",
        "ruska-pravda",
        "sofiya-kyivska",
        "volodymyr-monomakh"
    ]
    
    for slug in slugs:
        process_file(slug)
