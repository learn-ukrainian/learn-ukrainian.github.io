#!/usr/bin/env python3
"""
Enrich YAML Vocabulary
----------------------
Enriches YAML vocabulary files using a JSON dataset.
Maps file paths from .md (in JSON) to vocabulary/*.yaml.
"""

import json
import argparse
from pathlib import Path
import yaml

# Configure YAML to handle unicode characters correctly
def setup_yaml():
    yaml.Dumper.ignore_aliases = lambda *args: True

def enrich_yaml(data_file):
    dataset_path = Path(data_file)
    if not dataset_path.exists():
        print(f"Error: Data file not found: {dataset_path}")
        return

    try:
        data = json.loads(dataset_path.read_text(encoding='utf-8'))
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        return

    updated_count = 0

    for entry in data:
        md_file_path_str = entry.get('file')
        enrichments = entry.get('enrichments', {})
        
        if not md_file_path_str or not enrichments:
            continue
            
        md_path = Path(md_file_path_str)
        # Assuming structure: level/module.md -> level/vocabulary/module.yaml
        vocab_dir = md_path.parent / "vocabulary"
        yaml_name = md_path.stem + ".yaml"
        yaml_path = vocab_dir / yaml_name
        
        if not yaml_path.exists():
            print(f"Warning: YAML file not found: {yaml_path}")
            continue
            
        try:
            vocab_data = yaml.safe_load(yaml_path.read_text(encoding='utf-8'))
        except Exception as e:
            print(f"Error reading YAML {yaml_path}: {e}")
            continue

        if not vocab_data or 'items' not in vocab_data:
            continue
            
        modified = False
        for item in vocab_data['items']:
            lemma = item.get('lemma')
            if lemma in enrichments:
                edss = enrichments[lemma]
                
                new_ipa = edss.get('ipa')
                new_trans = edss.get('en')
                
                if new_ipa:
                    if item.get('ipa') != new_ipa:
                        item['ipa'] = new_ipa
                        modified = True
                        
                if new_trans:
                    if item.get('translation') != new_trans:
                        item['translation'] = new_trans
                        modified = True
        
        if modified:
            with open(yaml_path, 'w', encoding='utf-8') as f:
                yaml.dump(vocab_data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
            updated_count += 1
            
    print(f"Enrichment Complete. Updated {updated_count} files.")

if __name__ == "__main__":
    setup_yaml()
    parser = argparse.ArgumentParser(description="Enrich YAML vocabulary files from JSON data.")
    parser.add_argument("data_file", help="Path to the JSON file containing enrichment data.")
    args = parser.parse_args()
    
    enrich_yaml(args.data_file)
