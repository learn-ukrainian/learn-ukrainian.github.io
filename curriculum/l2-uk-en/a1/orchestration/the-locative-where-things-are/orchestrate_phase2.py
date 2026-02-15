import yaml
import subprocess
import os
import re

meta_path = "curriculum/l2-uk-en/a1/meta/the-locative-where-things-are.yaml"
placeholders_path = "curriculum/l2-uk-en/a1/orchestration/the-locative-where-things-are/placeholders.yaml"
content_path = "curriculum/l2-uk-en/a1/the-locative-where-things-are.md"
slug = "the-locative-where-things-are"
track = "a1"
num = "13"
orch_dir = f"curriculum/l2-uk-en/{track}/orchestration/{slug}"

# Ensure safe loading
def load_yaml(path):
    with open(path, 'r') as f:
        return yaml.safe_load(f)

meta = load_yaml(meta_path)
sections = list(meta['content_outline'].keys())
section_words = meta['content_outline']
engagement_min = meta.get('engagement_min', 4)
example_min = meta.get('example_min', 8)
num_sections = len(sections)

placeholders = load_yaml(placeholders_path)

previous_summary = ""
callout_types = []

for idx, section_title in enumerate(sections, 1):
    print(f"Processing Section {idx}: {section_title}")
    
    target_words = section_words[section_title]
    hard_min = int(target_words * 1.5)
    section_eng = max(1, engagement_min // num_sections)
    section_ex = max(3, example_min // num_sections)
    
    placeholders['SECTION_TITLE'] = section_title
    placeholders['HARD_MINIMUM_WORD_COUNT'] = str(hard_min)
    placeholders['SECTION_ENGAGEMENT_MIN'] = str(section_eng)
    placeholders['SECTION_EXAMPLE_MIN'] = str(section_ex)
    placeholders['PREVIOUS_CONTENT_SUMMARY'] = previous_summary
    placeholders['CALLOUT_TYPES_USED'] = ", ".join(callout_types)
    
    with open(placeholders_path, 'w') as f:
        yaml.dump(placeholders, f, allow_unicode=True, sort_keys=False)
        
    prompt_path = f"{orch_dir}/phase-2-p2-{idx}-prompt.md"
    subprocess.run([
        ".venv/bin/python", "scripts/fill_template.py",
        "--template", "claude_extensions/phases/gemini/phase-2-content-section.md",
        "--placeholders", placeholders_path,
        "--output", prompt_path,
        "--no-strict"
    ], check=True)
    
    task_id = f"yw-{slug}-p2-{idx}"
    output_path = f"/Users/krisztiankoos/.gemini/tmp/ad818000baf0b7a7c98f509dc95b7b60baa8ddef154856f0b8befd9597cdd77b/gemini-output-{slug}-phase-2-{idx}.txt"
    
    print(f"Dispatching task {task_id}...")
    with open(output_path, 'w') as outfile:
        subprocess.run([
            ".venv/bin/python", "scripts/ai_agent_bridge.py", "ask-gemini",
            f"Activate skill full-rebuild-core-a. Read and execute the instructions at {os.getcwd()}/{prompt_path}",
            "--task-id", task_id,
            "--stdout-only",
            "--model", "gemini-3-pro-preview"
        ], stdout=outfile, stderr=subprocess.STDOUT, check=True)
    
    print(f"Extracting output for section {idx}...")
    subprocess.run([
        ".venv/bin/python", "scripts/extract_phase.py",
        output_path,
        "--phase", "2-section",
        "--output-dir", orch_dir,
        "--attempt", "1"
    ], check=True)
    
    # Check possible extracted filenames
    extracted_path = f"{orch_dir}/phase-2-section-section_content.md"
    
    if not os.path.exists(extracted_path):
        print(f"Error: Extracted file {extracted_path} not found. Checking directory...")
        found = False
        for f in os.listdir(orch_dir):
            if f.endswith("section_content.md") and f"phase-2-section" in f:
                extracted_path = f"{orch_dir}/{f}"
                found = True
                break
        if not found:
             print(f"Could not find extracted file in {orch_dir}")
             continue # Skip to next section or break?

    with open(extracted_path, 'r') as f:
        content = f.read()
        
    words = len(content.split())
    threshold = int(target_words * 0.8)
    if words < threshold:
        print(f"THIN: {section_title} = {words} words (target: {target_words}, min: {threshold})")
        
    with open(content_path, 'a') as f:
        f.write(content + "

")
        
    headers = [line.strip() for line in content.split('
') if line.strip().startswith('### ')]
    paragraphs = [p for p in content.split('

') if p.strip()]
    last_paragraphs = paragraphs[-3:] if len(paragraphs) >= 3 else paragraphs
    
    previous_summary = "
".join(headers) + "
---
" + "

".join(last_paragraphs)
    
    new_callouts = re.findall(r'\[!(\w+)\]', content)
    callout_types.extend(new_callouts)
    callout_types = list(set(callout_types))

print("Phase 2 Complete")
