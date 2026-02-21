import os
import re

def clean_module(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    modified = False
    
    # 1. Convert ASCII quotes to Ukrainian angular quotes («...»)
    # This matches occurrences of "text" and replaces with «text»
    # We use a non-greedy match to avoid eating up the whole file
    new_content = re.sub(r'"([^"]+)"', r'«\1»', content)
    if new_content != content:
        content = new_content
        modified = True

    # 2. Consolidate and Normalize Summary Header to H1 (# Підсумок)
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

    # 3. Fix Nesting under Presentation/Grammar/Theory or Skill sections (H2 -> H3)
    # Target sections that are H2 but should be H1 (Summary) are handled above.
    # Now we handle sub-headers under H2 sections.
    
    # Identify H2 sections that act as anchors
    anchors = [
        r'## (?:Presentation|Grammar|Focus|Theory|Презентація|Граматика|Теорія)',
        r'## Skill \d+: .+'
    ]
    
    for anchor_pattern in anchors:
        m_anchors = list(re.finditer(anchor_pattern, content, re.IGNORECASE))
        for m_anchor in reversed(m_anchors): # Reverse to avoid index shift
            anchor_start = m_anchor.end()
            # Find the next H1 or H2 that marks the end of this section
            end_markers = [r'## Practice', r'## Практика', r'# Підсумок', r'---', r'## Need More Practice?', r'## Skill \d+']
            end_pos = len(content)
            for p in end_markers:
                m_end = re.search(p, content[anchor_start:])
                if m_end:
                    current_end = anchor_start + m_end.start()
                    if current_end < end_pos:
                        end_pos = current_end
            
            # Within [anchor_start, end_pos], change any ## Topic to ### Topic
            subcontent = content[anchor_start:end_pos]
            # Pattern: start of line, ##, followed by space and anything that isn't an end marker
            new_subcontent = re.sub(r'^##\s+(?!Practice|Практика|Need More Practice\?|Skill \d+)(.+)$', r'### \1', subcontent, flags=re.MULTILINE)
            if new_subcontent != subcontent:
                content = content[:anchor_start] + new_subcontent + content[end_pos:]
                modified = True

    # 4. Final cleanup
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    if modified:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def main():
    a2_dir = "curriculum/l2-uk-en/a2"
    files = sorted([f for f in os.listdir(a2_dir) if f.endswith(".md") and f[0].isdigit()])
    
    fixed_count = 0
    for f in files:
        if clean_module(os.path.join(a2_dir, f)):
            fixed_count += 1
            print(f"Cleaned: {f}")
            
    print(f"Total cleaned: {fixed_count}")

if __name__ == "__main__":
    main()
