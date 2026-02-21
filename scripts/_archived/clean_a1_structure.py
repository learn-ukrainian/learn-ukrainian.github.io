import os
import re

def clean_module(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    modified = False
    
    # 1. Consolidate and Normalize Summary Header to H1 (# Підсумок)
    summary_pattern = r'^(?:#+|##)\s+(?:Summary|Підсумок|Recap)(?:\s*\(Summary\))?\s*$'
    summary_matches = list(re.finditer(summary_pattern, content, re.MULTILINE | re.IGNORECASE))
    
    if summary_matches:
        # Keep track of where the first one was
        first_summary_pos = summary_matches[0].start()
        # Remove all
        content = re.sub(summary_pattern, '', content, flags=re.MULTILINE | re.IGNORECASE)
        # Insert one H1
        content = content[:first_summary_pos] + "# Підсумок" + content[first_summary_pos:]
        modified = True

    # 2. Fix Nesting under Presentation/Grammar/Theory (H2 -> H3)
    # If we have ## Presentation and then ## Sub-topic, the ## Sub-topic must be H3
    presentation_pattern = r'## (?:Presentation|Grammar|Focus|Theory|Презентація|Граматика|Теорія)'
    m_pres = re.search(presentation_pattern, content, re.IGNORECASE)
    if m_pres:
        pres_start = m_pres.end()
        # Find the next H1 or H2 that marks the end of this section
        # End markers: ## Practice, # Підсумок, ---, ## Need More Practice?
        end_markers = [r'## Practice', r'## Практика', r'# Підсумок', r'---', r'## Need More Practice?']
        end_pos = len(content)
        for pattern in end_markers:
            m_end = re.search(pattern, content[pres_start:])
            if m_end:
                current_end = pres_start + m_end.start()
                if current_end < end_pos:
                    end_pos = current_end
                    
        # Within [pres_start, end_pos], change any ## Topic to ### Topic
        subcontent = content[pres_start:end_pos]
        new_subcontent = re.sub(r'^##\s+(?!Practice|Практика|Need More Practice\?)(.+)$', r'### \1', subcontent, flags=re.MULTILINE)
        if new_subcontent != subcontent:
            content = content[:pres_start] + new_subcontent + content[end_pos:]
            modified = True

    # 3. Ensure "## Practice" section exists (H2)
    if not re.search(r'## (?:Practice|Exercises|Activity|Практика|Вправи)', content, re.IGNORECASE):
        # Insert before Summary (# Підсумок)
        m_summary = re.search(r'# Підсумок', content)
        if m_summary:
            target_pos = m_summary.start()
            practice_block = """## Практика

### Вправа 1: Переклад
Перекладіть речення на українську мову.

1. I am a student.
2. This is my house.
3. She is in the city.

---

"""
            content = content[:target_pos] + practice_block + content[target_pos:]
            modified = True

    # 4. Final cleanup
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    if modified:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def main():
    a1_dir = "curriculum/l2-uk-en/a1"
    files = sorted([f for f in os.listdir(a1_dir) if f.endswith(".md") and f[0].isdigit() and "checkpoint" not in f])
    
    fixed_count = 0
    for f in files:
        if clean_module(os.path.join(a1_dir, f)):
            fixed_count += 1
            print(f"Cleaned: {f}")
            
    print(f"Total cleaned: {fixed_count}")

if __name__ == "__main__":
    main()
