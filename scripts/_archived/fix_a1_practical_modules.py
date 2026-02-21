import os
import re
import yaml

def fix_module_field(base_dir, sub_dir):
    dir_path = os.path.join(base_dir, sub_dir)
    if not os.path.exists(dir_path):
        print(f"Directory not found: {dir_path}")
        return

    for filename in os.listdir(dir_path):
        # Filter for M35-M44
        if not re.match(r'^(3[5-9]|4[0-4])-', filename):
            continue
        
        if not filename.endswith('.yaml'):
            continue

        file_path = os.path.join(dir_path, filename)
        expected_module = os.path.splitext(filename)[0]
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = yaml.safe_load(f)
            
            if content is None:
                print(f"Skipping empty file: {filename}")
                continue
                
            current_module = content.get('module')
            
            if current_module != expected_module:
                print(f"Fixing {filename}: {current_module} -> {expected_module}")
                content['module'] = expected_module
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    yaml.dump(content, f, allow_unicode=True, sort_keys=False)
            else:
                print(f"OK {filename}")
                
        except Exception as e:
            print(f"Error processing {filename}: {e}")

base_path = "curriculum/l2-uk-en/a1"
print("Checking Meta files...")
fix_module_field(base_path, "meta")
print("\nChecking Vocabulary files...")
fix_module_field(base_path, "vocabulary")
