import yaml
import os
import subprocess
import sys
import re

ORCH_DIR = "curriculum/l2-uk-en/a1/orchestration/the-accusative-i-things"
META_PATH = "curriculum/l2-uk-en/a1/meta/the-accusative-i-things.yaml"
PLACEHOLDERS_PATH = os.path.join(ORCH_DIR, "placeholders.yaml")
CONTENT_PATH = "curriculum/l2-uk-en/a1/the-accusative-i-things.md"
TEMPLATE_PATH = "claude_extensions/phases/gemini/phase-2-content-section.md"
FILL_SCRIPT = "scripts/fill_template.py"
BRIDGE_SCRIPT = "scripts/ai_agent_bridge.py"
EXTRACT_SCRIPT = "scripts/extract_phase.py"

def run_command(cmd):
    print(f"Running: {cmd}")
    subprocess.run(cmd, shell=True, check=True)

def load_yaml(path):
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def save_yaml(data, path):
    with open(path, 'w') as f:
        yaml.dump(data, f, allow_unicode=True)

def main():
    meta = load_yaml(META_PATH)
    placeholders = load_yaml(PLACEHOLDERS_PATH)
    
    sections = meta.get('content_outline', [])
    # Convert dict to list if necessary (handle both formats)
    if isinstance(sections, dict):
        sections_list = []
        for title, words in sections.items():
             sections_list.append({'section': title, 'words': words})
        sections = sections_list

    previous_summary = ""
    callout_types = []
    
    engagement_min_total = int(meta.get('engagement_min', 4))
    example_min_total = int(meta.get('example_min', 8))
    num_sections = len(sections)

    for i, section in enumerate(sections):
        section_title = section['section']
        words = int(section['words'])
        
        # Calculate per-section targets
        hard_min = int(words * 1.5)
        eng_min = max(1, engagement_min_total // num_sections)
        ex_min = max(3, example_min_total // num_sections)
        
        print(f"--- Processing Section {i+1}/{num_sections}: {section_title} ---")
        
        # Update placeholders
        placeholders['SECTION_TITLE'] = section_title
        placeholders['HARD_MINIMUM_WORD_COUNT'] = str(hard_min)
        placeholders['SECTION_ENGAGEMENT_MIN'] = str(eng_min)
        placeholders['SECTION_EXAMPLE_MIN'] = str(ex_min)
        placeholders['PREVIOUS_CONTENT_SUMMARY'] = previous_summary if previous_summary else "No previous content."
        placeholders['CALLOUT_TYPES_USED'] = ", ".join(callout_types) if callout_types else "None"
        
        save_yaml(placeholders, PLACEHOLDERS_PATH)
        
        # Fill Template
        prompt_path = os.path.join(ORCH_DIR, f"phase-2-p2-{i+1}-prompt.md")
        run_command(f".venv/bin/python {FILL_SCRIPT} --template {TEMPLATE_PATH} --placeholders {PLACEHOLDERS_PATH} --output {prompt_path} --no-strict")
        
        # Dispatch
        task_id = f"yw-the-accusative-i-things-p2-{i+1}"
        output_file = f"/tmp/gemini-output-the-accusative-i-things-phase-2-{i+1}.txt"
        
        cmd = f'.venv/bin/python {BRIDGE_SCRIPT} ask-gemini "Activate skill full-rebuild-core-a. Read and execute the instructions at $(pwd)/{prompt_path}" --task-id {task_id} --stdout-only --model gemini-3-pro-preview > {output_file} 2>&1'
        try:
            run_command(cmd)
        except subprocess.CalledProcessError:
             print(f"Dispatch failed for section {section_title}")
             sys.exit(1)

        # Extract
        run_command(f".venv/bin/python {EXTRACT_SCRIPT} {output_file} --phase 2-section --output-dir {ORCH_DIR} --attempt 1")
        
        # Append content
        extracted_file = os.path.join(ORCH_DIR, "phase-2-section-section_content.md")
        
        # Fallback if specific file not found (though script usually produces phase-2-section_content.md for tag SECTION_CONTENT)
        if not os.path.exists(extracted_file):
             # Try checking if extraction script produced something else or failed silently
             print(f"Warning: Extracted file {extracted_file} not found. Checking directory.")
             print(os.listdir(ORCH_DIR))
        
        if os.path.exists(extracted_file):
            with open(extracted_file, 'r') as f:
                content = f.read()
                
            with open(CONTENT_PATH, 'a') as f:
                f.write(content + "\\n\\n")
            
            # Update Context
            # Extract H3s
            h3s = [line.strip() for line in content.splitlines() if line.startswith('### ')]
            
            # Extract last 3 paragraphs
            paragraphs = [p for p in content.split('\\n\\n') if p.strip() and not p.strip().startswith('#') and not p.strip().startswith('===')]
            last_paragraphs = paragraphs[-2:] if len(paragraphs) >= 2 else paragraphs
            last_prose = "\\n\\n".join(last_paragraphs)
            
            summary_update = f"## {section_title}\\n" + "\\n".join(h3s) + "\\n---\\n" + last_prose
            previous_summary += "\\n\\n" + summary_update
            
            # Extract Callouts
            callouts = re.findall(r'\[!(\w+[-\w]*)\]', content)
            for c in callouts:
                if c not in callout_types:
                    callout_types.append(c)
        else:
             print(f"Critical Error: Could not find extracted content for section {section_title}")
             sys.exit(1)

if __name__ == "__main__":
    main()
