import os
import re
import glob
import yaml
from pathlib import Path

LIT_DIR = Path("curriculum/l2-uk-en/lit")
META_DIR = LIT_DIR / "meta"

def parse_frontmatter(content: str):
    match = re.match(r'^---\n(.*?)\n---\n(.*)', content, re.DOTALL)
    if not match:
        return None, content
    try:
        fm = yaml.safe_load(match.group(1))
        return fm, match.group(2)
    except yaml.YAMLError:
        print("Error parsing YAML frontmatter")
        return None, content

def extract_summary(content):
    lines = content.splitlines()
    summary_lines = []
    in_summary = False
    
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("# Summary") or stripped.startswith("## Summary") or stripped.startswith("# Підсумок"):
            in_summary = True
            continue 
        
        if in_summary:
            if stripped.startswith("#") or stripped.startswith("---"):
                break
            if stripped and not stripped.startswith(">"): # Skip blockquotes if any (usually summary is text)
                 summary_lines.append(stripped)
            
    return " ".join(summary_lines).strip()

def merge_meta(sidecar_path, data):
    if not sidecar_path.exists():
        # Create new
        with open(sidecar_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, sort_keys=False, allow_unicode=True)
        print(f"Created sidecar: {sidecar_path}")
        return

    with open(sidecar_path, 'r', encoding='utf-8') as f:
        sidecar_data = yaml.safe_load(f) or {}

    # Merge logic
    if sidecar_data.get('title') == 'Title Placeholder':
        sidecar_data.update(data)
    else:
        sidecar_data.update(data)

    with open(sidecar_path, 'w', encoding='utf-8') as f:
        yaml.dump(sidecar_data, f, sort_keys=False, allow_unicode=True)
    print(f"Updated sidecar: {sidecar_path}")

def clean_content(content):
    lines = content.splitlines()
    new_lines = []
    skip_mode = False
    
    remove_headers = [
        "# Summary",
        "## Summary", 
        "# Vocabulary",
        "## Vocabulary",
        "# Словник",
        "## Словник",
        "# Activities",
        "## Activities",
        "# Завдання",
        "## Завдання",
        "## 🏛️ Читальна Зала",
        "# 🏛️ Читальна Зала",
        "## Reading Hall",
        "# Reading Hall"
    ]

    for line in lines:
        stripped_line = line.strip()
        
        is_remove_header = False
        for header in remove_headers:
            if stripped_line.startswith(header):
                is_remove_header = True
                break
        
        if is_remove_header:
            skip_mode = True
            continue
            
        if skip_mode:
            if stripped_line.startswith("#"):
                skip_mode = False
                new_lines.append(line)
            else:
                continue
        else:
            new_lines.append(line)
            
    return "\n".join(new_lines).strip() + "\n"

def process_file(filepath):
    print(f"Processing {filepath.name}...")
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Parse Frontmatter
    frontmatter, body = parse_frontmatter(content)
    
    # 2. Extract Summary from Body
    summary_text = extract_summary(body)
    
    # 3. Prepare Sidecar Data
    sidecar_update = {}
    if frontmatter:
        sidecar_update.update(frontmatter)
    
    if summary_text:
        # Check if description already exists and is non-empty/non-placeholder
        # Actually, if we are extracting, we should overwrite/set it.
        sidecar_update['description'] = summary_text

    # 4. Update Sidecar
    if sidecar_update:
        sidecar_path = META_DIR / (filepath.stem + ".yaml")
        merge_meta(sidecar_path, sidecar_update)
    
    # 5. Clean Body
    cleaned_body = clean_content(body)
    
    # 6. Write back
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(cleaned_body)
    
    print(f"Cleaned {filepath.name}: {len(content.splitlines())} -> {len(cleaned_body.splitlines())} lines")

def main():
    files = sorted(list(LIT_DIR.glob("*.md")))
    for f in files:
        if f.name == "README.md":
            continue
        process_file(f)

if __name__ == "__main__":
    main()