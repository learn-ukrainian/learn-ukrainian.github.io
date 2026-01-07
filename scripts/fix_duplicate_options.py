
import yaml

def fix_duplicates(file_path):
    with open(file_path, 'r') as f:
        data = yaml.safe_load(f)
    
    modified_count = 0
    for activity in data:
        atype = activity.get('type')
        items = activity.get('items', [])
        
        # 1. Cloze (top level blanks)
        if atype == 'cloze':
            blanks = activity.get('blanks', [])
            for b in blanks:
                opts = b.get('options', [])
                unique_opts = []
                seen = set()
                for o in opts:
                    if o not in seen:
                        seen.add(o)
                        unique_opts.append(o)
                if len(unique_opts) != len(opts):
                    b['options'] = unique_opts
                    modified_count += 1
        
        # 2. Fill-in / items based
        if items:
            for item in items:
                opts = item.get('options', [])
                if opts and isinstance(opts[0], str): # List of strings
                    unique_opts = []
                    seen = set()
                    for o in opts:
                        if o not in seen:
                            seen.add(o)
                            unique_opts.append(o)
                    if len(unique_opts) != len(opts):
                        item['options'] = unique_opts
                        modified_count += 1
                elif opts and isinstance(opts[0], dict): # List of dicts (Quiz)
                    # Dedupe by 'text'
                    unique_opts = []
                    seen = set()
                    for o in opts:
                        txt = o.get('text')
                        if txt not in seen:
                            seen.add(txt)
                            unique_opts.append(o)
                    if len(unique_opts) != len(opts):
                        item['options'] = unique_opts
                        modified_count += 1
                        
    if modified_count > 0:
        with open(file_path, 'w') as f:
            yaml.dump(data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
        print(f"Fixed duplicates in {modified_count} places.")
    else:
        print("No duplicates found.")

fix_duplicates('curriculum/l2-uk-en/c1/activities/17-irregular-verbs-complete.yaml')
