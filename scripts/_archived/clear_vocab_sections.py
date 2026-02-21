import re
import argparse
from pathlib import Path

def clear_vocab(level):
    base_dir = Path("/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en")
    modules_dir = base_dir / level
    
    if not modules_dir.exists():
        print(f"Directory not found: {modules_dir}")
        return

    modules = sorted(list(modules_dir.glob("*.md")))
    print(f"Clearing vocabulary from {len(modules)} modules in {level}...")
    
    count = 0
    for mod_file in modules:
        content = mod_file.read_text(encoding="utf-8")
        
        # Regex to find the Vocabulary header and everything after it
        # Try English header first, then Ukrainian
        new_content = content
        found = False
        
        if "# Vocabulary" in content:
            new_content = content.split("# Vocabulary")[0].strip() + "\n"
            found = True
        elif "# Словник" in content:
            new_content = content.split("# Словник")[0].strip() + "\n"
            found = True
            
        if found:
            # Check if we actually removed something substantial (avoid touching files if they end right at the header)
            if len(new_content) < len(content):
                mod_file.write_text(new_content, encoding="utf-8")
                # print(f"Cleared {mod_file.name}")
                count += 1
            else:
                # Header was at the very end or empty
                pass
        else:
            print(f"Skipped {mod_file.name} (No vocabulary section found)")
            
    print(f"Cleared vocabulary from {count} modules.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--level", required=True, help="Level (a2, b1, etc.)")
    args = parser.parse_args()
    
    clear_vocab(args.level)
