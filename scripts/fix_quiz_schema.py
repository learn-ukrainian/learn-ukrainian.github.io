import yaml
import sys

def refactor_activities(file_path):
    with open(file_path, 'r') as f:
        data = yaml.safe_load(f)

    for activity in data:
        if activity.get('type') == 'multiple-choice':
            activity['type'] = 'quiz'
            if 'id' in activity:
                # Keep ID if present
                pass
            
            new_items = []
            for item in activity.get('items', []):
                question = item.get('question')
                options = item.get('options', [])
                answer = item.get('answer')
                explanation = item.get('explanation')

                new_options = []
                for opt in options:
                    is_correct = (opt == answer)
                    new_options.append({'text': opt, 'correct': is_correct})
                
                new_item = {
                    'question': question,
                    'options': new_options,
                    'explanation': explanation
                }
                new_items.append(new_item)
            
            activity['items'] = new_items

    with open(file_path, 'w') as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)

if __name__ == "__main__":
    refactor_activities(sys.argv[1])
