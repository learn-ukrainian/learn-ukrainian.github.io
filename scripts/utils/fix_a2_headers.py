import os
import re

def fix_a2_headers_robust():
    a2_dir = "curriculum/l2-uk-en/a2"
    fixed_count = 0
    
    for filename in os.listdir(a2_dir):
        if filename.endswith(".md"):
            path = os.path.join(a2_dir, filename)
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            orig_content = content
            
            # --- 1. Introduction | Вступ ---
            # Pattern: Check if any header contains Introduction, Вступ, or Warm-up
            has_intro = False
            has_vstup = False
            
            lines = content.split('\n')
            new_lines = []
            
            title_line_idx = -1
            found_intro_at = -1
            
            for i, line in enumerate(lines):
                if line.startswith("# "):
                    title_line_idx = i
                if line.startswith("## "):
                    h_text = line[3:].strip().lower()
                    if "introduction" in h_text:
                        has_intro = True
                    if "вступ" in h_text:
                        has_vstup = True
                    if "warm-up" in h_text or "розминка" in h_text:
                        # Convert Warm-up to Introduction and ensure Вступ
                        if not has_intro:
                            lines[i] = "## Introduction"
                            has_intro = True
                        if not has_vstup and "вступ" not in h_text:
                            # We'll insert Вступ later
                            pass

            # Final check and insertion
            if not has_intro or not has_vstup:
                content = '\n'.join(lines)
                if not has_intro:
                    # Insert after title
                    content = re.sub(r'(^# [^\n]+\n)', r'\1\n## Introduction\n', content)
                if not has_vstup:
                    # Insert after Introduction
                    content = re.sub(r'(## Introduction\s*\n)', r'\1\n## Вступ\n', content)
            else:
                content = '\n'.join(lines)

            # --- 2. Presentation / Grammar ---
            if not any(x in content.lower() for x in ["presentation", "grammar", "презентація", "граматика", "теорія"]):
                # Look for synonyms or just insert before Practice
                if "## Practice" in content:
                    content = content.replace("## Practice", "## Presentation\n\n## Practice")
                elif "## Практика" in content:
                    content = content.replace("## Практика", "## Presentation\n\n## Практика")

            # --- 3. Practice ---
            if not any(x in content.lower() for x in ["practice", "exercises", "практика", "вправи"]):
                if "## Summary" in content:
                    content = content.replace("## Summary", "## Practice\n\n## Summary")
                elif "## Підсумок" in content:
                    content = content.replace("## Підсумок", "## Practice\n\n## Підсумок")

            if content != orig_content:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
                fixed_count += 1
                print(f"Fixed headers (robust) in {filename}")
                
    print(f"Finished. Fixed {fixed_count} modules.")

if __name__ == "__main__":
    fix_a2_headers_robust()
