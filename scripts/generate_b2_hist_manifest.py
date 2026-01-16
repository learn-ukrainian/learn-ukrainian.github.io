import re
import yaml
from pathlib import Path

PLAN_PATH = "docs/l2-uk-en/B2-HIST-CURRICULUM-PLAN-EXPANDED.md"
OUTPUT_PATH = "curriculum/l2-uk-en/curriculum.yaml"

def parse_plan():
    with open(PLAN_PATH, 'r') as f:
        content = f.read()

    modules = []
    current_phase = None
    
    # Regex to match the table rows
    # | # | Slug | Title (UK) | ...
    # | 01 | trypillian-civilization | ...
    
    # First, find phase headers to track phases
    lines = content.split('\n')
    
    for line in lines:
        if line.startswith('## Synthesis Modules') or line.startswith('## Source Alignment') or line.startswith('## Thematic Strands') or line.startswith('## Module Count Summary'):
            break

        phase_match = re.match(r'### Phase (HIST\.\d+): (.+)', line)
        if phase_match:
            current_phase = phase_match.group(1)
            continue
            
        # Match table row
        # | 01 | trypillian-civilization | ...
        if line.strip().startswith('|') and 'Slug' not in line and '---' not in line:
            parts = [p.strip() for p in line.split('|')]
            if len(parts) > 3:
                slug = parts[2]
                title = parts[3]
                
                if slug and slug != 'Slug' and not slug.startswith('---'):
                    # Validate slug format (lowercase, numbers, hyphens only)
                    if re.match(r'^[a-z0-9]+(-[a-z0-9]+)*$', slug):
                        module = {
                            'slug': slug,
                            'title': title,
                            'phase': current_phase,
                            'focus': 'history'
                        }
                        if 'syntez' in slug:
                            module['focus'] = 'checkpoint'
                        
                        modules.append(module)
    
    return modules

def generate_manifest(modules):
    manifest = {
        "version": "2.0",
        "language_pair": "uk-en",
        "name": "Ukrainian for English Speakers",
        "settings": {
            "default_transliteration": True
        },
        "core": {
            "a1": {"name": "A1 - Beginner", "modules": []},
            "a2": {"name": "A2 - Elementary", "modules": []},
            "b1": {"name": "B1 - Intermediate", "modules": []},
            "b2": {"name": "B2 - Upper Intermediate", "modules": []},
            "c1": {"name": "C1 - Advanced", "modules": []},
            "c2": {"name": "C2 - Mastery", "modules": []}
        },
        "tracks": {
            "b2-hist": {
                "name": "B2 History Track",
                "description": "Ukrainian History from Kyivan Rus' to Independence",
                "prerequisite": "b2",
                "modules": modules
            }
        }
    }
    
    # Ensure directory exists
    Path(OUTPUT_PATH).parent.mkdir(parents=True, exist_ok=True)
    
    with open(OUTPUT_PATH, 'w') as f:
        yaml.dump(manifest, f, allow_unicode=True, sort_keys=False)
    
    print(f"Generated manifest with {len(modules)} B2-HIST modules at {OUTPUT_PATH}")

if __name__ == "__main__":
    modules = parse_plan()
    generate_manifest(modules)
