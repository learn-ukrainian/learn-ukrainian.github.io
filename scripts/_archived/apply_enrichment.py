import json
import sys
from pathlib import Path

def apply_enrichment(json_file):
    try:
        data = json.loads(Path(json_file).read_text(encoding='utf-8'))
    except Exception as e:
        print(f"Error loading JSON: {e}")
        return

    # Structure:
    # [
    #   {
    #     "file": "curriculum/...",
    #     "enrichments": {
    #        "word_uk": {"ipa": "...", "en": "..."},
    #        ...
    #     }
    #   },
    #   ...
    # ]
    
    for item in data:
        file_path = Path(item['file'])
        if not file_path.exists():
            print(f"File not found: {file_path}")
            continue
            
        enrichments = item['enrichments'] # dict of word -> {ipa, en}
        
        content = file_path.read_text(encoding='utf-8')
        lines = content.splitlines()
        new_lines = []
        
        in_table = False
        table_start_idx = -1
        
        # We need to parse the table carefully
        # Simple line-by-line check
        
        for line in lines:
            if "| Word" in line and "| IPA" in line:
                in_table = True
                new_lines.append(line)
                continue
            
            if in_table:
                if not line.strip():
                    in_table = False
                    new_lines.append(line)
                    continue
                
                if line.strip().startswith("| ---"):
                    new_lines.append(line)
                    continue
                
                if line.strip().startswith("|"):
                    # Table row: | word | ipa | english | pos | gender | note |
                    parts = [p.strip() for p in line.strip("|").split("|")]
                    if len(parts) >= 1:
                        word = parts[0]
                        if word in enrichments:
                            info = enrichments[word]
                            # Update IPA (idx 1) and English (idx 2)
                            # Reconstruct line to preserve spacing? 
                            # Hard to preserve exact spacing, but we can format nicely.
                            
                            # Existing parts might be empty strings if empty
                            # Ensure we have enough parts
                            while len(parts) < 6:
                                parts.append("")
                                
                            parts[1] = info.get('ipa', parts[1])
                            parts[2] = info.get('en', parts[2])
                            
                            # Reconstruction
                            # | word | ipa | english | pos | gender | note |
                            new_line = f"| {parts[0]} | {parts[1]} | {parts[2]} | {parts[3]} | {parts[4]} | {parts[5]} |"
                            new_lines.append(new_line)
                        else:
                            new_lines.append(line)
                    else:
                        new_lines.append(line)
                else:
                    # End of table?
                    in_table = False
                    new_lines.append(line)
            else:
                new_lines.append(line)
                
        file_path.write_text("\n".join(new_lines) + "\n", encoding='utf-8')
        print(f"Updated {file_path.name}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 apply_enrichment.py <data.json>")
        sys.exit(1)
        
    apply_enrichment(sys.argv[1])
