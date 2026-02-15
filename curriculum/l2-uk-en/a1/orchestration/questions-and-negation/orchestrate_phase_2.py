import yaml
import subprocess
import os
import sys
import re

# Configuration
TRACK = "a1"
SLUG = "questions-and-negation"
ORCH_DIR = f"curriculum/l2-uk-en/{TRACK}/orchestration/{SLUG}"
META_PATH = f"curriculum/l2-uk-en/{TRACK}/meta/{SLUG}.yaml"
CONTENT_PATH = f"curriculum/l2-uk-en/{TRACK}/{SLUG}.md"
PLACEHOLDERS_PATH = f"{ORCH_DIR}/placeholders.yaml"
TEMPLATE_PATH = "claude_extensions/phases/gemini/phase-2-content-section.md"

def run_command(cmd, check=True):
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"Error running command: {cmd}")
        print(result.stderr)
        sys.exit(1)
    return result.stdout

def read_yaml(path):
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def write_yaml(path, data):
    with open(path, 'w') as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False)

def update_placeholders(section_title, word_count, engagement_min, example_min, prev_summary, callouts_used):
    data = read_yaml(PLACEHOLDERS_PATH)
    data['SECTION_TITLE'] = section_title
    data['HARD_MINIMUM_WORD_COUNT'] = int(word_count * 1.5)
    data['SECTION_ENGAGEMENT_MIN'] = engagement_min
    data['SECTION_EXAMPLE_MIN'] = example_min
    data['PREVIOUS_CONTENT_SUMMARY'] = prev_summary
    data['CALLOUT_TYPES_USED'] = callouts_used
    write_yaml(PLACEHOLDERS_PATH, data)

def get_seam_context(content_file):
    if not os.path.exists(content_file):
        return "", ""
    
    with open(content_file, 'r') as f:
        text = f.read()
    
    # Extract headers
    headers = re.findall(r'^### (.*)$', text, re.MULTILINE)
    header_summary = "\\n".join([f"- {h}" for h in headers])
    
    # Extract last paragraphs
    lines = [line.strip() for line in text.split('\\n') if line.strip()]
    last_prose = "\\n\\n".join(lines[-3:]) if len(lines) >= 3 else "\\n\\n".join(lines)
    
    summary = f"**Topics Covered:**\\n{header_summary}\\n\\n**Ending Context:**\\n...\\n{last_prose}"
    
    # Extract callouts
    callouts = re.findall(r'> \[!(.*?)\]', text)
    return summary, ", ".join(callouts)

# Main logic
meta = read_yaml(META_PATH)
sections = meta.get('content_outline_detailed', []) # Use ordered list
if not sections:
    print("Error: content_outline_detailed missing in meta.")
    sys.exit(1)

# Initialize content file
with open(CONTENT_PATH, 'w') as f:
    f.write(f"<!-- SCOPE\\nCovers: {meta.get('title', 'Topic')}\\n-->\\n\\n# {meta.get('title', 'Topic')}\\n\\n")

total_sections = len(sections)
engagement_min = max(1, int(meta.get('engagement_min', 4) / total_sections))
example_min = max(3, int(meta.get('example_min', 8) / total_sections))

prev_summary = "None (First Section)"
callouts_used = "None"

for i, section in enumerate(sections):
    index = i + 1
    title = section['section']
    words = section['words']
    
    print(f"Processing Section {index}/{total_sections}: {title} ({words} words)")
    
    # Update placeholders
    update_placeholders(title, words, engagement_min, example_min, prev_summary, callouts_used)
    
    # Fill template
    prompt_file = f"{ORCH_DIR}/phase-2-p2-{index}-prompt.md"
    run_command(f".venv/bin/python scripts/fill_template.py --template {TEMPLATE_PATH} --placeholders {PLACEHOLDERS_PATH} --output {prompt_file} --no-strict")
    
    # Dispatch
    task_id = f"yw-{SLUG}-p2-{index}"
    output_file = f"/Users/krisztiankoos/.gemini/tmp/ad818000baf0b7a7c98f509dc95b7b60baa8ddef154856f0b8befd9597cdd77b/gemini-output-{SLUG}-phase-2-p2-{index}.txt"
    # Skip dispatch if output exists (resume)?
    # To save time, if output exists AND is non-empty, skip dispatch.
    should_dispatch = True
    if os.path.exists(output_file) and os.path.getsize(output_file) > 100:
         print(f"Output exists for section {index}, extracting existing output.")
         should_dispatch = False
    
    if should_dispatch:
        cmd = f".venv/bin/python scripts/ai_agent_bridge.py ask-gemini 'Activate skill full-rebuild-core-a. Read and execute the instructions at $(pwd)/{prompt_file}' --task-id {task_id} --stdout-only --model gemini-3-pro-preview > {output_file} 2>&1"
        run_command(cmd)
    
    # Extract
    run_command(f".venv/bin/python scripts/extract_phase.py {output_file} --phase 2-section --output-dir {ORCH_DIR} --attempt 1")
    
    # Rename extracted file
    target_extracted = f"{ORCH_DIR}/phase-2-p2-{index}-section_content.md"
    default_extracted = f"{ORCH_DIR}/phase-2-section-section_content.md" # Found from directory listing
    
    if os.path.exists(default_extracted):
        os.rename(default_extracted, target_extracted)
    else:
        # Check listing again if needed
        if os.path.exists(f"{ORCH_DIR}/section_content.md"):
             os.rename(f"{ORCH_DIR}/section_content.md", target_extracted)
        elif os.path.exists(f"{ORCH_DIR}/section-content.md"):
             os.rename(f"{ORCH_DIR}/section-content.md", target_extracted)
        else:
            print(f"Error: Extracted file not found for section {index}")
            print(os.listdir(ORCH_DIR))
            sys.exit(1)
            
    # Append to content
    with open(target_extracted, 'r') as f:
        content = f.read()
        
    with open(CONTENT_PATH, 'a') as f:
        f.write(content + "\\n\\n")
        
    # Update context for next section
    summary, callouts = get_seam_context(target_extracted)
    if summary:
        prev_summary = summary
    if callouts:
        if callouts_used == "None":
            callouts_used = callouts
        else:
            callouts_used += ", " + callouts

print("Phase 2 Complete.")
