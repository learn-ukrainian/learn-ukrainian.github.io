import json
import re
import argparse
from pathlib import Path

def get_missing(level):
    base_dir = Path("curriculum/l2-uk-en") / level
    modules = sorted(list(base_dir.glob("*.md")))
    
    # Sort modules numerically
    try:
        modules.sort(key=lambda x: int(x.name.split('-')[0]))
    except:
        pass

    results = []
    
    for mod_file in modules:
        content = mod_file.read_text(encoding="utf-8")
        
        # Regex to find table rows with empty IPA/English
        # Row format: | word |  |  | pos | gender | note |
        # We look for rows where col 1 (IPA) or col 2 (English) is empty.
        
        missing_words = []
        
        lines = content.splitlines()
        in_table = False
        
        for line in lines:
            if "| Word" in line and "| IPA" in line:
                in_table = True
                continue
            if in_table:
                if not line.strip():
                    in_table = False
                    continue
                if line.strip().startswith("| ---"):
                    continue
                
                if line.strip().startswith("|"):
                    parts = [p.strip() for p in line.strip("|").split("|")]
                    if len(parts) >= 3:
                        word = parts[0]
                        ipa = parts[1]
                        eng = parts[2]
                        
                        if not ipa or not eng:
                            missing_words.append(word)
        
        if missing_words:
            results.append({
                "file": str(mod_file),
                "words": missing_words
            })
            
    print(json.dumps(results, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--level", required=True)
    args = parser.parse_args()
    
    get_missing(args.level)
