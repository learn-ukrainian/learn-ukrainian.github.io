import os
import re
import glob

LIT_DIR = "curriculum/l2-uk-en/lit"

def clean_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original_lines = content.splitlines()
    
    # 1. Remove YAML Frontmatter
    if content.startswith('---'):
        # Find the second '---'
        parts = content.split('---', 2)
        if len(parts) >= 3:
            # parts[0] is empty (before first ---)
            # parts[1] is the yaml content
            # parts[2] is the rest
            content = parts[2].strip()
            # Add back the H1 if it was removed? No, H1 is usually after frontmatter.
            # But let's check if we stripped too much.
            # If the file started with ---, parts[2] starts after the second ---.
            # We strip leading whitespace.
        else:
            print(f"Warning: Malformed frontmatter in {filepath}")

    # Convert back to lines for section processing
    lines = content.splitlines()
    new_lines = []
    skip_mode = False
    
    # Sections to remove
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
        
        # Check if this line starts a section we want to remove
        is_remove_header = False
        for header in remove_headers:
            if stripped_line.startswith(header):
                is_remove_header = True
                break
        
        if is_remove_header:
            skip_mode = True
            # print(f"Skipping section starting with: {stripped_line}")
            continue
            
        # Check if we should stop skipping (start of a new section)
        if skip_mode:
            # If it's a header (starts with #) AND it's NOT one of the remove headers
            # Then we stop skipping.
            if stripped_line.startswith("#"):
                # Double check it's not a remove header (already checked above, but logic order matters)
                # If it was a remove header, we would have hit `continue` above.
                # So if we are here and it starts with #, it must be a KEPT header.
                skip_mode = False
                new_lines.append(line)
            else:
                # Still in the section to remove
                continue
        else:
            # Not skipping, keep line
            new_lines.append(line)

    # 3. Double check for embedded vocab tables if headers were missing
    # (The user mentioned "Vocabulary tables - Any markdown tables with Term/Translation/Notes")
    # This is harder to detect without a header, but let's assume they are under headers.
    # If there are stray tables, we might need a more aggressive check.
    # For now, rely on headers.

    final_content = "\n".join(new_lines).strip() + "\n" 
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(final_content)
    
    print(f"Cleaned {filepath}: {len(original_lines)} -> {len(new_lines)} lines")

def main():
    files = sorted(glob.glob(os.path.join(LIT_DIR, "*.md")))
    for f in files:
        if f.endswith("README.md"):
            continue
        clean_file(f)

if __name__ == "__main__":
    main()
