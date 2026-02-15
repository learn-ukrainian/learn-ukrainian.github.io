import yaml
import os
import subprocess
import sys
import re

# Paths
BASE_DIR = "curriculum/l2-uk-en/b2/orchestration/passive-voice-system"
META_PATH = "curriculum/l2-uk-en/b2/meta/passive-voice-system.yaml"
PLACEHOLDERS_PATH = os.path.join(BASE_DIR, "placeholders.yaml")
CONTENT_PATH = "curriculum/l2-uk-en/b2/passive-voice-system.md"
TEMPLATE_PATH = "claude_extensions/phases/gemini/phase-2-content-section.md"
BRIDGE_SCRIPT = ".venv/bin/python scripts/ai_agent_bridge.py"
EXTRACT_SCRIPT = ".venv/bin/python scripts/extract_phase.py"
FILL_SCRIPT = ".venv/bin/python scripts/fill_template.py"

# Load meta
with open(META_PATH, 'r') as f:
    meta = yaml.safe_load(f)

sections = meta['content_outline']
num_sections = len(sections)

# Global context
previous_summary = "None (First section)"
callouts_used = []

def run_command(cmd):
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running command: {cmd}")
        print(result.stderr)
        sys.exit(1)
    return result.stdout

def extract_summary(content):
    # Get all H3 headers
    headers = re.findall(r'^### (.*)', content, re.MULTILINE)
    # Get last 3 paragraphs (approx)
    lines = content.splitlines()
    # Filter empty lines
    lines = [l for l in lines if l.strip()]
    last_para = "\n".join(lines[-3:]) if len(lines) >= 3 else "\n".join(lines)
    
    summary = ""
    if headers:
        summary += "Topics covered:\n" + "\n".join([f"- {h}" for h in headers]) + "\n\n"
    summary += "---\nLast 3 paragraphs:\n" + last_para
    return summary

def extract_callouts(content):
    return re.findall(r'\[!(.*?)\]', content)

# Loop
for i, section in enumerate(sections):
    index = i + 1
    title = section['section']
    words = section['words']
    
    print(f"\n=== Processing Section {index}/{num_sections}: {title} ({words} words) ===\n")
    
    # 1. Update placeholders
    with open(PLACEHOLDERS_PATH, 'r') as f:
        placeholders = yaml.safe_load(f)
    
    placeholders['SECTION_TITLE'] = title
    placeholders['HARD_MINIMUM_WORD_COUNT'] = str(int(words * 1.5)) # Safety margin
    placeholders['SECTION_ENGAGEMENT_MIN'] = "1"
    placeholders['SECTION_EXAMPLE_MIN'] = "3"
    placeholders['PREVIOUS_CONTENT_SUMMARY'] = previous_summary
    placeholders['CALLOUT_TYPES_USED'] = ", ".join(callouts_used) if callouts_used else "None"
    
    # Write back placeholders
    with open(PLACEHOLDERS_PATH, 'w') as f:
        yaml.dump(placeholders, f, allow_unicode=True, sort_keys=False)
        
    # 2. Fill template
    prompt_file = os.path.join(BASE_DIR, f"phase-2-p2-{index}-prompt.md")
    run_command(f"{FILL_SCRIPT} --template {TEMPLATE_PATH} --placeholders {PLACEHOLDERS_PATH} --output {prompt_file} --no-strict")
    
    # 3. Dispatch
    output_file = f"/Users/krisztiankoos/.gemini/tmp/ad818000baf0b7a7c98f509dc95b7b60baa8ddef154856f0b8befd9597cdd77b/gemini-output-passive-voice-system-phase-2-{index}.txt"
    task_id = f"yw-passive-voice-system-p2-{index}"
    
    # Use absolute path for prompt in dispatch command
    abs_prompt_file = os.path.abspath(prompt_file)
    
    dispatch_cmd = f'{BRIDGE_SCRIPT} ask-gemini "Activate skill full-rebuild-core-b. Read and execute the instructions at {abs_prompt_file}" --task-id {task_id} --stdout-only --model gemini-3-pro-preview > {output_file} 2>&1'
    run_command(dispatch_cmd)
    
    # 4. Extract
    run_command(f"{EXTRACT_SCRIPT} {output_file} --phase 2-section --output-dir {BASE_DIR} --attempt 1")
    
    # Check extracted file
    extracted_file = os.path.join(BASE_DIR, f"phase-2-section-section_content.md")
    
    if not os.path.exists(extracted_file):
        # Maybe naming convention is different?
        # Let's list dir to find it
        files = os.listdir(BASE_DIR)
        candidates = [f for f in files if "section_content" in f and f.endswith(".md")]
        if candidates:
            # Sort by modification time to get the newest
            candidates.sort(key=lambda x: os.path.getmtime(os.path.join(BASE_DIR, x)), reverse=True)
            extracted_file = os.path.join(BASE_DIR, candidates[0])
        else:
            print("Error: Extracted file not found")
            sys.exit(1)
            
    with open(extracted_file, 'r') as f:
        content = f.read()
        
    # 5. Append
    with open(CONTENT_PATH, 'a') as f:
        f.write("\n" + content + "\n")
        
    # 6. Update context
    previous_summary = extract_summary(content)
    new_callouts = extract_callouts(content)
    callouts_used.extend(new_callouts)
    callouts_used = list(set(callouts_used)) # Dedupe

print("Phase 2 Complete")
