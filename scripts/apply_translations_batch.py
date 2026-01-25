#!/usr/bin/env python3
import yaml
import json
from pathlib import Path
import sys

def main():
    if len(sys.argv) < 2:
        print("Usage: python apply_translations_batch.py <translations.json>")
        return

    trans_path = Path(sys.argv[1])
    if not trans_path.exists():
        print(f"Error: {trans_path} not found")
        return

    with open(trans_path, 'r', encoding='utf-8') as f:
        translations = json.load(f)

    base_dir = Path("curriculum/l2-uk-en")
    updated_files = 0
    total_updated = 0

    for level in ['a1', 'a2', 'b1']:
        vocab_dir = base_dir / level / 'vocabulary'
        if not vocab_dir.exists(): continue

        for yaml_file in vocab_dir.glob('*.yaml'):
            with open(yaml_file, 'r', encoding='utf-8') as yf:
                data = yaml.safe_load(yf)
                if not data or 'items' not in data: continue

            file_modified = False
            for item in data['items']:
                lemma = item.get('lemma')
                if not item.get('translation') and lemma in translations:
                    item['translation'] = translations[lemma]
                    file_modified = True
                    total_updated += 1

            if file_modified:
                with open(yaml_file, 'w', encoding='utf-8') as yf:
                    yaml.dump(data, yf, allow_unicode=True, default_flow_style=False, sort_keys=False)
                updated_files += 1

    print(f"Finished. Updated {total_updated} items in {updated_files} files.")

if __name__ == "__main__":
    main()
