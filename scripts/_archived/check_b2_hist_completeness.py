import yaml
from pathlib import Path

MANIFEST_PATH = "curriculum/l2-uk-en/curriculum.yaml"
BASE_DIR = Path("curriculum/l2-uk-en/b2-hist")

def check_completeness():
    with open(MANIFEST_PATH, 'r') as f:
        manifest = yaml.safe_load(f)
    
    modules = manifest['tracks']['b2-hist']['modules']
    
    missing_files = []
    
    for module in modules:
        slug = module['slug']
        
        # Check .md file
        md_file = BASE_DIR / f"{slug}.md"
        if not md_file.exists():
            missing_files.append(f"MISSING MD: {slug}")
            
        # Check meta
        meta_file = BASE_DIR / "meta" / f"{slug}.yaml"
        if not meta_file.exists():
            missing_files.append(f"MISSING META: {slug}")
            
        # Check vocabulary
        vocab_file = BASE_DIR / "vocabulary" / f"{slug}.yaml"
        if not vocab_file.exists():
            missing_files.append(f"MISSING VOCAB: {slug}")
            
        # Check activities
        activities_file = BASE_DIR / "activities" / f"{slug}.yaml"
        if not activities_file.exists():
            missing_files.append(f"MISSING ACTIVITIES: {slug}")
            
    if not missing_files:
        print("All 140 B2-HIST modules are complete with sidecars.")
    else:
        print(f"Found {len(missing_files)} missing files:")
        for missing in missing_files:
            print(f"  {missing}")

if __name__ == "__main__":
    check_completeness()
