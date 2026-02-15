import yaml
import os

META_PATH = "curriculum/l2-uk-en/a1/meta/the-accusative-i-things.yaml"
OUTLINE_PATH = "curriculum/l2-uk-en/a1/orchestration/the-accusative-i-things/phase-1-meta_outline.md"

def load_yaml(path):
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def save_yaml(data, path):
    with open(path, 'w') as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False)

def main():
    meta = load_yaml(META_PATH)
    outline_data = load_yaml(OUTLINE_PATH)
    
    # Merge content_outline
    if 'content_outline' in outline_data:
        meta['content_outline'] = outline_data['content_outline']
        print(f"Updated content_outline in {META_PATH}")
    else:
        print("Error: No content_outline found in phase-1 output")
        
    save_yaml(meta, META_PATH)

if __name__ == "__main__":
    main()
