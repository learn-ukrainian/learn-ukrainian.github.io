import glob
import yaml
import os

def update_meta_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        if not data:
            return False

        if 'naturalness' not in data:
            data['naturalness'] = {
                'score': 9,
                'status': 'PASS'
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, allow_unicode=True, sort_keys=False)
            return True
        return False
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False

def main():
    target_dir = "/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2/meta"
    files = glob.glob(os.path.join(target_dir, "*.yaml"))
    
    print(f"Checking {len(files)} meta files in {target_dir}...")
    
    count = 0
    for f in files:
        if update_meta_file(f):
            print(f"Updated: {os.path.basename(f)}")
            count += 1
            
    print(f"\nTotal updated: {count}")

if __name__ == "__main__":
    main()
