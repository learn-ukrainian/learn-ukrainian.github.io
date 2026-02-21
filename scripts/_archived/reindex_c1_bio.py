import yaml
import os
import re

# Paths
BIRTH_ORDER_PATH = 'curriculum/l2-uk-en/c1-bio/BIRTH_ORDER.yaml'
CURRICULUM_PATH = 'curriculum/l2-uk-en/curriculum.yaml'
PLANS_DIR = 'curriculum/l2-uk-en/plans/c1-bio'
META_DIR = 'curriculum/l2-uk-en/c1-bio/meta'

def update_file_content(file_path, slug, index):
    if not os.path.exists(file_path):
        # print(f"Warning: File {file_path} not found.")
        return False
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Update module ID (e.g., c1-bio-157 -> c1-bio-116)
    # We use \d+ to match any number of digits
    content = re.sub(r'module: c1-bio-\d+', f'module: c1-bio-{index:03d}', content)
    content = re.sub(r'id: c1-bio-\d+', f'id: c1-bio-{index:03d}', content)
    content = re.sub(r'module_id: c1-bio-\d+', f'module_id: c1-bio-{index:03d}', content)
    
    # Update sequence
    content = re.sub(r'sequence: \d+', f'sequence: {index}', content)
    
    # Update manifest_id and curriculum_index (for meta files)
    content = re.sub(r'manifest_id: "M\d+"', f'manifest_id: "M{index:03d}"', content)
    content = re.sub(r'curriculum_index: \d+', f'curriculum_index: {index}', content)
    
    # Update prerequisites (previous module)
    if index > 1:
        prev_id = f'c1-bio-{(index-1):03d}'
        # More robust regex for prerequisites
        content = re.sub(r'prerequisites:\s*\n\s*-\s*"c1-bio-\d+"', f'prerequisites:\n  - "{prev_id}"', content)
    
    with open(file_path, 'w') as f:
        f.write(content)
    return True

def main():
    # 1. Load BIRTH_ORDER
    with open(BIRTH_ORDER_PATH, 'r') as f:
        birth_order = yaml.safe_load(f)
    
    slugs = birth_order['modules']
    
    # 2. Update curriculum.yaml
    with open(CURRICULUM_PATH, 'r') as f:
        curriculum = yaml.safe_load(f)
    
    curriculum['levels']['c1-bio']['modules'] = slugs
    
    with open(CURRICULUM_PATH, 'w') as f:
        # Use a custom representer or just write it out carefully to preserve format
        # but for now standard dump is fine for verification
        yaml.dump(curriculum, f, allow_unicode=True, sort_keys=False)
    print("Updated curriculum.yaml")
    
    # 3. Update plans and meta files
    updated_count = 0
    for i, slug in enumerate(slugs, 1):
        plan_path = os.path.join(PLANS_DIR, f"{slug}.yaml")
        meta_path = os.path.join(META_DIR, f"{slug}.yaml")
        
        if update_file_content(plan_path, slug, i):
            updated_count += 1
        if update_file_content(meta_path, slug, i):
            updated_count += 1
        
    print(f"Updated {updated_count} files for {len(slugs)} modules.")

if __name__ == "__main__":
    main()