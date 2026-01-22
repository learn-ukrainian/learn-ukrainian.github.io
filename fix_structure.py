import re
import sys
import glob

def fix_file(file_path):
    print(f"Processing {file_path}...")
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Parse headers
    sections = []
    current_header = "START"
    current_content = []

    for line in content.split('\n'):
        if re.match(r'^#{1,3} ', line):
            if current_content:
                sections.append((current_header, '\n'.join(current_content)))
            current_header = line.strip()
            current_content = []
        else:
            current_content.append(line)
    if current_content:
        sections.append((current_header, '\n'.join(current_content)))

    # Identify blocks
    intro_blocks = []
    summary_block = None
    misplaced_analysis_blocks = []
    practice_block = None
    
    # State machine: 
    # 0: Intro (Before Summary)
    # 1: Summary found
    # 2: Practice found
    state = 0
    
    for header, text in sections:
        if header == "START":
            intro_blocks.append((header, text))
            continue
            
        is_summary = "# Підсумок" in header
        is_practice = "## Потрібно більше практики?" in header
        
        if is_summary:
            state = 1
            summary_block = (header, text)
        elif is_practice:
            state = 2
            practice_block = (header, text)
        else:
            if state == 0:
                intro_blocks.append((header, text))
            elif state == 1:
                # After Summary, Before Practice -> Misplaced Analysis
                # Check if it's a subsection (###)
                if header.startswith("###"):
                    misplaced_analysis_blocks.append((header, text))
                else:
                    # If it's H1/H2, it might be something else, but let's assume it's part of the analysis flow
                    # or structure we want to move up.
                    # M10 had ### sections.
                    misplaced_analysis_blocks.append((header, text))
            elif state == 2:
                # After Practice - usually nothing, or practice subsections
                # If it's a practice subsection, keep it with practice
                # Practice subsections in M15: "### 🔄 Інтеграція знань", "### 🌐 Онлайн-ресурси"
                # So we append to practice block content?
                # Actually, sections list separates them. We need to append them to the output sequence.
                # Let's handle post-practice blocks separately.
                pass

    # Post-practice blocks need to be gathered too
    post_practice_blocks = []
    if practice_block:
        # Find index of practice block
        try:
            p_idx = sections.index(practice_block)
            post_practice_blocks = sections[p_idx+1:]
        except ValueError:
            pass

    # Reassemble
    new_content = ""

    # 1. Intro/Decol
    for h, t in intro_blocks:
        if h != "START":
            new_content += f"\n\n{h}\n"
        new_content += t

    # 2. Misplaced Analysis (Moved UP)
    for h, t in misplaced_analysis_blocks:
        new_content += f"\n\n{h}\n"
        new_content += t

    # 3. Summary
    if summary_block:
        h, t = summary_block
        new_content += f"\n\n{h}\n"
        new_content += t

    # 4. Practice
    if practice_block:
        h, t = practice_block
        new_content += f"\n\n{h}\n"
        new_content += t
        
    # 5. Post-Practice
    for h, t in post_practice_blocks:
        new_content += f"\n\n{h}\n"
        new_content += t

    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content.strip() + '\n')
    
    print(f"Fixed {file_path}")

if __name__ == "__main__":
    files = sys.argv[1:]
    for f in files:
        fix_file(f)
