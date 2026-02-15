import yaml
import subprocess
import os
import sys
import re

# Paths
TRACK = "a1"
SLUG = "the-gender-code"
ORCH_DIR = f"curriculum/l2-uk-en/{TRACK}/orchestration/{SLUG}"
META_PATH = f"curriculum/l2-uk-en/{TRACK}/meta/{SLUG}.yaml"
CONTENT_PATH = f"curriculum/l2-uk-en/{TRACK}/{SLUG}.md"
PLACEHOLDERS_PATH = f"{ORCH_DIR}/placeholders.yaml"
TEMPLATE_PATH = "claude_extensions/phases/gemini/phase-2-content-section.md"

def run_command(cmd, check=True):
    print(f"Running: {cmd}")
    subprocess.run(cmd, shell=True, check=check)

def load_yaml(path):
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def save_yaml(path, data):
    with open(path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)

def main():
    meta = load_yaml(META_PATH)
    sections = meta['content_outline']
    num_sections = len(sections)
    
    # Base placeholders
    placeholders = load_yaml(PLACEHOLDERS_PATH)
    engagement_min = meta.get('engagement_min', 4)
    example_min = meta.get('example_min', 8)
    
    section_engagement_min = max(1, engagement_min // num_sections)
    section_example_min = max(3, example_min // num_sections)

    # Context tracking
    previous_content_summary = ""
    callout_types_used = []

    for idx, section in enumerate(sections):
        section_title = section['section']
        section_words = section['words']
        # 1.5 multiplier for HARD_MINIMUM
        hard_min = int(section_words * 1.5)
        
        print(f"--- Processing Section {idx+1}/{num_sections}: {section_title} (Target: {section_words}, Min: {hard_min}) ---")

        # Update Placeholders
        placeholders['SECTION_TITLE'] = section_title
        placeholders['HARD_MINIMUM_WORD_COUNT'] = str(hard_min)
        placeholders['SECTION_ENGAGEMENT_MIN'] = str(section_engagement_min)
        placeholders['SECTION_EXAMPLE_MIN'] = str(section_example_min)
        placeholders['PREVIOUS_CONTENT_SUMMARY'] = previous_content_summary
        placeholders['CALLOUT_TYPES_USED'] = ", ".join(callout_types_used)
        
        save_yaml(PLACEHOLDERS_PATH, placeholders)

        # Generate Prompt
        prompt_file = f"{ORCH_DIR}/phase-2-p2-{idx+1}-prompt.md"
        run_command(f".venv/bin/python scripts/fill_template.py --template '{TEMPLATE_PATH}' --placeholders '{PLACEHOLDERS_PATH}' --output '{prompt_file}' --no-strict")
        
        # Call Bridge
        task_id = f"yw-{SLUG}-p2-{idx+1}"
        output_file = f"/tmp/gemini-output-{SLUG}-phase-2-{idx+1}.txt"
        
        bridge_cmd = (
            f".venv/bin/python scripts/ai_agent_bridge.py ask-gemini "
            f"'Activate skill full-rebuild-core-a. Read and execute the instructions at $(pwd)/{prompt_file}' "
            f"--task-id {task_id} --stdout-only --model gemini-3-pro-preview "
            f"> {output_file} 2>&1"
        )
        run_command(bridge_cmd)
        
        # Extract Content
        extract_cmd = (
            f".venv/bin/python scripts/extract_phase.py {output_file} "
            f"--phase 2-section --output-dir {ORCH_DIR}/ --attempt 1"
        )
        run_command(extract_cmd)
        
        # Verify Extraction
        # extract_phase output filename logic: prefix + tag.lower().replace('_', '-') + .md
        # If phase is '2-section', prefix is 'phase-2-section'.
        # Tag is 'SECTION_CONTENT' -> 'section-content'.
        # So 'phase-2-section-section-content.md'? 
        # Or maybe extract_phase just uses the tag if phase is complex?
        # Let's check for likely candidates.
        candidates = [
            f"{ORCH_DIR}/phase-2-section_content.md",
            f"{ORCH_DIR}/phase-2-section-section_content.md",
            f"{ORCH_DIR}/section_content.md",
            f"{ORCH_DIR}/phase-2-section-section-content.md"
        ]
        
        found_file = None
        for c in candidates:
            if os.path.exists(c):
                found_file = c
                break
        
        if not found_file:
            print(f"Error: Extracted file not found for section {idx+1}. Checked: {candidates}")
            # List directory to help debug
            print(f"Directory contents: {os.listdir(ORCH_DIR)}")
            sys.exit(1)
            
        # Rename for safety
        section_file = f"{ORCH_DIR}/phase-2-p2-{idx+1}-section_content.md"
        os.rename(found_file, section_file)
        
        # Density Check
        with open(section_file, 'r') as f:
            content = f.read()
            word_count = len(content.split())
            
        threshold = int(section_words * 0.8)
        if word_count < threshold:
            print(f"THIN: {section_title} = {word_count} words (target: {section_words}, min: {threshold})")
            
        # Append to Content
        with open(CONTENT_PATH, 'a') as f:
            f.write(content + "\n\n")
            
        # Update Context for Next Loop
        lines = content.split('\n')
        headers = [line for line in lines if line.startswith('### ')]
        
        last_chunk = content[-1000:] if len(content) > 1000 else content
        
        previous_content_summary = "\n".join(headers) + "\n---\n" + last_chunk
        
        callouts = re.findall(r'> \[!([a-zA-Z-]+)\]', content)
        callout_types_used.extend(callouts)
        callout_types_used = list(set(callout_types_used))

if __name__ == "__main__":
    main()
