
import os
import yaml
from pathlib import Path
import subprocess

# List of all missing C1-BIO modules to hydrate
MISSING_SLUGS = [
    # Early Rus'
    "volodymyr-monomakh", "nestor-litopysets",
    
    # Hetmanate
    "ivan-vyhovskyi", "danylo-apostol", "pavlo-polubotok",

    # Executed Renaissance
    "mykhailo-boichuk", "mykola-zerov", "pavlo-fylypovych", "oleksa-slisarenko",
    "maik-yohansen", "anatol-petrytskyi", "yevhen-pluzhnyk", "dmytro-falkivskyi",
    "hryhorii-kosynka", "valerian-pidmohylnyi", "heo-shkurupii",

    # Other missing
    "petro-mohyla", "ivan-sirko", "ivan-nechuy-levytskyi", "ivan-puliui", 
    "andrey-sheptytsky", "yevhen-paton", "yevhen-konovalets", "josyf-slipyj", 
    "milena-rudnytska", "mykola-kulish", "oleksandr-dovzhenko", "maik-yohansen", 
    "yuriy-kondratiuk", "roman-shukhevych", "serhiy-korolyov", "george-shevelov", 
    "mykola-amosov", "borys-paton", "vasyl-sukhomlynskyi", "serhii-plokhy", "oleksandr-usyk"
]

TRACK_DIR = Path("curriculum/l2-uk-en/c1-bio")
PLAN_DIR = Path("curriculum/l2-uk-en/plans/c1-bio")
TEMPLATE_PATH = Path("docs/l2-uk-en/templates/ai/c1-biography-module-template.md")

def create_meta(slug):
    """Create meta/{slug}.yaml if missing."""
    meta_path = TRACK_DIR / "meta" / f"{slug}.yaml"
    if meta_path.exists():
        print(f"Meta exists: {slug}")
        return

    # Read plan to get basic info
    plan_path = PLAN_DIR / f"{slug}.yaml"
    if not plan_path.exists():
        print(f"ERROR: Plan missing for {slug}")
        return
    
    with open(plan_path, 'r') as f:
        plan = yaml.safe_load(f)

    meta_content = {
        "module": slug,  # C1-BIO doesn't use number prefixes in meta module ID usually? Checking convention...
        # Actually standard meta uses slug usually or numbered ID. 
        # Let's check an existing one. 
        "level": "C1",
        "slug": slug,
        "version": "1.0",
        "id": slug, # Using slug as ID for now
        "naturalness": {
            "score": 0,
            "status": "PENDING"
        },
        "duration": 90,
        "tags": plan.get("tags", []),
        "validation_tier": "llm-verified" # Defaulting to Tier 2 for new gen
    }
    
    os.makedirs(meta_path.parent, exist_ok=True)
    with open(meta_path, 'w') as f:
        yaml.dump(meta_content, f, sort_keys=False)
    print(f"Created Meta: {slug}")

def create_vocab(slug):
    """Create vocabulary/{slug}.yaml if missing."""
    vocab_path = TRACK_DIR / "vocabulary" / f"{slug}.yaml"
    if vocab_path.exists():
        print(f"Vocab exists: {slug}")
        return

    # Scaffold
    content = {
        "vocabulary": []
    }
    
    os.makedirs(vocab_path.parent, exist_ok=True)
    with open(vocab_path, 'w') as f:
        yaml.dump(content, f, sort_keys=False)
    print(f"Created Vocab: {slug}")

def create_activities(slug):
    """Create activities/{slug}.yaml if missing."""
    act_path = TRACK_DIR / "activities" / f"{slug}.yaml"
    if act_path.exists():
        print(f"Activities exists: {slug}")
        return

    # Scaffold
    content = {
        "activities": []
    }
    
    os.makedirs(act_path.parent, exist_ok=True)
    with open(act_path, 'w') as f:
        yaml.dump(content, f, sort_keys=False)
    print(f"Created Activities: {slug}")

def hydrate_markdown(slug):
    """Generate markdown skeleton from plan + template."""
    md_path = TRACK_DIR / f"{slug}.md"
    if md_path.exists():
        print(f"Markdown exists: {slug}")
        return

    # Run the existing skeleton generator
    # usage: python scripts/generate_skeleton.py <curriculum> <level> <module_id>
    cmd = [".venv/bin/python", "scripts/generate_skeleton.py", "l2-uk-en", "c1-bio", slug]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"Hydrated Markdown: {slug}")
    except subprocess.CalledProcessError as e:
        print(f"ERROR hydrating {slug}: {e.stderr}")

def main():
    print(f"Hydrating {len(MISSING_SLUGS)} modules...")
    for slug in MISSING_SLUGS:
        create_meta(slug)
        create_vocab(slug)
        create_activities(slug)
        hydrate_markdown(slug)

if __name__ == "__main__":
    main()
