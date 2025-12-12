import re
import glob

def check_translations():
    files = sorted(glob.glob("curriculum/l2-uk-en/a1/module-*.md"))
    missing = []

    for file_path in files:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Split into sections
        sections = re.split(r'\n##\s+', content)
        
        has_missing = False
        missing_sections = []

        for section in sections:
            header = section.split('\n')[0].lower()
            
            # Sections that MUST have translation
            target_sections = ["reading practice", "story time", "dialogue", "narrative", "conversation"]
            
            is_target = any(t in header for t in target_sections)
            
            if is_target:
                # Check for explicit translation markers (flexible)
                has_translation_marker = "**English Translation:**" in section or "**English:**" in section or "> **English:**" in section or "**English Translation**" in section
                
                # Check if it actually has significant Cyrillic text (some might be empty placeholders)
                has_cyrillic = bool(re.search(r'[\u0400-\u04ff]{10,}', section))
                
                if has_cyrillic and not has_translation_marker:
                    has_missing = True
                    missing_sections.append(header)
        
        if has_missing:
            print(f"MISSING: {file_path} -> {missing_sections}")

if __name__ == "__main__":
    check_translations()
