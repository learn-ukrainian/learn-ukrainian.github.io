import os
import yaml
import json
import glob

def find_missing_enrichments(directory):
    missing_data = []
    
    files = glob.glob(os.path.join(directory, "*.yaml"))
    
    for file_path in files:
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                data = yaml.safe_load(f)
            except yaml.YAMLError:
                print(f"Error parsing {file_path}")
                continue
        
        if not data or 'items' not in data:
            continue
            
        file_missing = {}
        for item in data['items']:
            lemma = item.get('lemma')
            ipa = item.get('ipa')
            translation = item.get('translation')
            
            if not ipa or not translation:
                file_missing[lemma] = {"ipa": "", "en": ""}
        
        if file_missing:
            # key is the file path relative to project root (or absolute)
            # The script main loop keeps it absolute, but let's make it relative for cleanliness if possible,
            # or just use absolute. The enrich script handles both.
            missing_data.append({
                "file": file_path,
                "enrichments": file_missing
            })
            
    return missing_data

if __name__ == "__main__":
    target_dir = "/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/vocabulary"
    output_file = "enrichment_final_a2.json"
    
    missing = find_missing_enrichments(target_dir)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(missing, f, ensure_ascii=False, indent=2)
    
    print(f"Generated {output_file} with {sum(len(m['enrichments']) for m in missing)} missing items.")
