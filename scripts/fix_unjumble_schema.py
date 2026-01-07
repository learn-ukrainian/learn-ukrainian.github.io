
import yaml

def fix_unjumble(file_path):
    with open(file_path, 'r') as f:
        data = yaml.safe_load(f)
    
    modified = False
    for activity in data:
        if activity['type'] == 'unjumble':
            items = activity.get('items', [])
            new_items = []
            for item in items:
                # convert old format to new format
                # OLD: sentence: "Full text", scramble: "text Full"
                # NEW: answer: "Full text", words: ["text", "Full"]
                if 'sentence' in item and 'answer' not in item:
                    answer = item.pop('sentence')
                    scramble = item.pop('scramble', '')
                    item['answer'] = answer
                    # Assume scramble is space separated words
                    item['words'] = scramble.split()
                    modified = True
            
    if modified:
        with open(file_path, 'w') as f:
            yaml.dump(data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
        print("Fixed unjumble schema.")
    else:
        print("No unjumble fixes needed.")

fix_unjumble('curriculum/l2-uk-en/c1/activities/17-irregular-verbs-complete.yaml')
