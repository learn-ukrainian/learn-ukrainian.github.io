import yaml
import json
from pathlib import Path

def main():
    base_dir = Path("curriculum/l2-uk-en")
    missing = set()
    
    for level in ['a1', 'a2', 'b1']:
        vocab_dir = base_dir / level / 'vocabulary'
        for f in vocab_dir.glob('*.yaml'):
            with open(f, 'r', encoding='utf-8') as yf:
                data = yaml.safe_load(yf)
                if not data or 'items' not in data: continue
                
                for item in data['items']:
                    if not item.get('translation'):
                        missing.add(item['lemma'])
                        
    print(json.dumps(sorted(list(missing)), ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
