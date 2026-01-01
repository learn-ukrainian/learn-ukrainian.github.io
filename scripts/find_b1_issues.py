
import os
import yaml
import json
import re

def find_issues(root_dir):
    issues = []
    
    for filename in sorted(os.listdir(root_dir)):
        if not filename.endswith('.yaml'):
            continue
            
        filepath = os.path.join(root_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            try:
                data = yaml.safe_load(f)
            except yaml.YAMLError:
                print(f"Error parsing {filename}")
                continue
                
        if not data or 'items' not in data:
            continue
            
        file_issues = {}
        for item in data['items']:
            lemma = item.get('lemma')
            translation = item.get('translation', '')
            
            if not translation or "(typo)" in translation or "?" in translation or "???" in translation or "Surzhyk" in translation or "Rus." in translation:
                file_issues[lemma] = {
                    "ipa": item.get('ipa', ''),
                    "en": translation
                }
        
        if file_issues:
            issues.append({
                "file": filepath, # Use absolute path or relative to project root? Script runs from root.
                "enrichments": file_issues
            })
            
    return issues

if __name__ == "__main__":
    root_dir = "curriculum/l2-uk-en/b1/vocabulary"
    issues = find_issues(root_dir)
    
    with open("b1_quality_issues.json", "w", encoding='utf-8') as f:
        json.dump(issues, f, ensure_ascii=False, indent=2)
        
    print(f"Found issues in {len(issues)} files.")
