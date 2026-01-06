
import sys
import yaml
from pathlib import Path

def fix_yaml(file_path):
    path = Path(file_path)
    if not path.exists():
        print(f"File not found: {path}")
        return

    with open(path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    changed = False
    
    # helper to process items
    def process_items(items):
        local_changed = False
        for item in items:
            if 'options' in item and isinstance(item['options'], list) and len(item['options']) > 0:
                first_opt = item['options'][0]
                if isinstance(first_opt, str):
                    # It's a list of strings, need to convert
                    answer = item.get('answer')
                    if not answer:
                        print(f"Warning: Item has string options but no answer field: {item.get('question', '???')}")
                        continue
                    
                    new_options = []
                    for opt in item['options']:
                        new_options.append({
                            'text': opt,
                            'correct': (opt == answer)
                        })
                    
                    item['options'] = new_options
                    if 'answer' in item:
                        del item['answer']
                    local_changed = True
            elif 'answers' in item and isinstance(item['answers'], list):
                # Format: answers (list of str) + correct (int index)
                answers = item['answers']
                correct_idx = item.get('correct')
                
                if correct_idx is None or not isinstance(correct_idx, int):
                     print(f"Warning: Item has answers but no valid correct index: {item.get('question', '???')}")
                     continue

                new_options = []
                for idx, ans in enumerate(answers):
                    new_options.append({
                        'text': str(ans),
                        'correct': (idx == correct_idx)
                    })
                
                item['options'] = new_options
                del item['answers']
                # Optional: keep or remove 'correct' field at item level? 
                # The generator ignores item['correct'], it looks at option['correct'].
                # So we can remove it.
                if 'correct' in item:
                    del item['correct']
                local_changed = True
        return local_changed

    activities = []
    if isinstance(data, list):
        activities = data
    elif isinstance(data, dict) and 'activities' in data:
        activities = data['activities']

    for activity in activities:
        atype = activity.get('type')
        if atype in ['quiz', 'select']:
            if 'items' in activity:
                if process_items(activity['items']):
                    changed = True
        elif atype == 'unjumble':
            if 'items' in activity:
                new_items = []
                local_changed = False
                for item in activity['items']:
                    if isinstance(item, str):
                        # Convert string item to object
                        new_items.append({
                            'scrambled': item.strip(),
                            'answer': item.strip()
                        })
                        local_changed = True
                    else:
                        new_items.append(item)
                
                if local_changed:
                    activity['items'] = new_items
                    changed = True
        elif atype == 'match-up':
            # No special handling needed for match-up
            pass
        elif atype == 'group-sort':
            # No special handling needed for group-sort
            pass
        elif atype == 'fill-in':
            if 'items' in activity:
                new_items = []
                local_changed = False
                for i, item in enumerate(activity['items']):
                    if isinstance(item, str):
                        new_lines.append({
                            'text': line.strip(),
                            'order': i + 1,
                            'speaker': ''
                        })
                        local_changed = True
                    else:
                        new_lines.append(line)
                
                if local_changed:
                    activity['lines'] = new_lines
                    changed = True

    if changed:
        print(f"Fixing {path}...")
        with open(path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True, sort_keys=False, width=1000)
        print("Done.")
    else:
        print(f"No changes needed for {path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fix_yaml_quiz.py <yaml_file>")
        sys.exit(1)
    
    fix_yaml(sys.argv[1])
