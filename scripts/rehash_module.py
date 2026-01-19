#!/usr/bin/env python3
import sys
import os
import re
import hashlib
from pathlib import Path

# Add scripts/ to path for internal imports to reach audit.cleaners
SCRIPT_DIR = Path(__file__).parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.append(str(SCRIPT_DIR))

try:
    from audit.cleaners import extract_core_content, clean_for_stats
except ImportError:
    # Fallback/Mock if imports fail (should not happen in project root)
    def extract_core_content(b): return b
    def clean_for_stats(t): return t

def calculate_hash(file_path):
    """Calculate stable MD5 hash of instructional core (first 8 chars)."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Use stable prose only (Issue #440)
    core_content = extract_core_content(content)
    stable_prose = clean_for_stats(core_content)
    return hashlib.md5(stable_prose.encode('utf-8')).hexdigest()[:8]

def update_review_file(md_file_path, new_hash):
    """Update the Content Hash in the corresponding -llm-review.md file."""
    md_path = Path(md_file_path)
    # Check if we are pointing to a review file itself by accident
    if md_path.name.endswith('-llm-review.md') or md_path.name.endswith('-review.md'):
        return False

    audit_dir = md_path.parent / 'audit'
    review_file = audit_dir / f"{md_path.stem}-llm-review.md"
    
    if not review_file.exists():
        # Try without -llm suffix just in case
        review_file = audit_dir / f"{md_path.stem}-review.md"
        if not review_file.exists():
            return False
    
    try:
        content = review_file.read_text(encoding='utf-8')
        pattern = r'\*\*Content Hash:\*\*\s*[a-f0-9]{8}'
        replacement = f"**Content Hash:** {new_hash}"
        
        if re.search(pattern, content):
            new_content = re.sub(pattern, replacement, content)
            review_file.write_text(new_content, encoding='utf-8')
            print(f"✅ Updated: {review_file.name} -> {new_hash}")
            return True
        else:
            # Fallback: if 'Content Hash:' exists but no 8-char hash
            secondary_pattern = r'\*\*Content Hash:\*\*.*'
            if re.search(secondary_pattern, content):
                new_content = re.sub(secondary_pattern, replacement, content)
                review_file.write_text(new_content, encoding='utf-8')
                print(f"✅ Updated (fixed format): {review_file.name} -> {new_hash}")
                return True
            else:
                # Append if missing
                new_content = content.rstrip() + f"\n\n**Content Hash:** {new_hash}\n"
                review_file.write_text(new_content, encoding='utf-8')
                print(f"✅ Added: {review_file.name} -> {new_hash}")
                return True
    except Exception as e:
        print(f"❌ Error updating {review_file.name}: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/rehash_module.py <file1.md> [dir1 ...]")
        print("Example: python3 scripts/rehash_module.py curriculum/l2-uk-en/b2-hist/")
        sys.exit(1)
    
    for arg in sys.argv[1:]:
        path = Path(arg)
        if not path.exists():
            print(f"Path not found: {arg}")
            continue
            
        if path.is_dir():
            print(f"📂 Scanning directory: {arg}")
            for root, _, files in os.walk(arg):
                for file in files:
                    if file.endswith('.md') and not (file.endswith('-llm-review.md') or file.endswith('-review.md')):
                        full_path = os.path.join(root, file)
                        h = calculate_hash(full_path)
                        update_review_file(full_path, h)
        else:
            h = calculate_hash(arg)
            if update_review_file(arg, h):
                pass
            else:
                print(f"ℹ️ No review file found for {path.name}")

if __name__ == "__main__":
    main()
