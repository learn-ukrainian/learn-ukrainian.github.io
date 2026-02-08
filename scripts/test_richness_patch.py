
import sys
import re
import yaml
from pathlib import Path

def count_external_yaml_resources(file_path: Path) -> int:
    """Count resources defined in docs/resources/external_resources.yaml."""
    print(f"DEBUG: Checking file path: {file_path}")
    if not file_path:
        return 0
    
    try:
        # Find project root from script location
        script_path = Path(__file__).resolve()
        project_root = script_path.parent.parent
        resource_yaml_path = project_root / 'docs' / 'resources' / 'external_resources.yaml'
        
        print(f"DEBUG: Looking for YAML at: {resource_yaml_path}")
        if not resource_yaml_path.exists():
            print("DEBUG: YAML file not found!")
            return 0
            
        with open(resource_yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            
        if not data or 'resources' not in data:
            print("DEBUG: No 'resources' key in YAML")
            return 0
            
        slug = file_path.stem
        # Also try removing numeric prefix for lookup
        clean_slug = re.sub(r'^\d+-', '', slug) if slug else slug
        
        print(f"DEBUG: Looking for slug '{slug}' or '{clean_slug}'")
        
        resources = data['resources']
        count = 0
        
        # Check entries for slug
        for key in [slug, clean_slug]:
            if key and key in resources:
                print(f"DEBUG: Found match for key '{key}'")
                module_res = resources[key]
                print(f"DEBUG: Module resources: {module_res}")
                if module_res and isinstance(module_res, dict):
                    for cat_list in module_res.values():
                        if isinstance(cat_list, list):
                            count += len(cat_list)
                # If we found resources for one variant, stop (avoid double counting)
                if count > 0:
                    break
                        
        print(f"DEBUG: Final count: {count}")
        return count
    except Exception as e:
        print(f"DEBUG: Exception: {e}")
        return 0

if __name__ == "__main__":
    test_path = Path("curriculum/l2-uk-en/lit/18-women-in-kobzar.md")
    count = count_external_yaml_resources(test_path)
    print(f"Result: {count}")
