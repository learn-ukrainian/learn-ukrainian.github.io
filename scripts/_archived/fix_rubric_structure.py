
import yaml

def fix_rubric(file_path):
    with open(file_path, 'r') as f:
        data = yaml.safe_load(f)
    
    modified = False
    rubric_obj = [
        {"criteria": "Лексика", "description": "Використання мінімум 5 неправильних дієслів", "points": 2},
        {"criteria": "Semantics", "description": "Вживання дієслів у переносному значенні", "points": 2},
        {"criteria": "Стиль", "description": "Академічний стиль", "points": 2},
        {"criteria": "Граматика", "description": "Граматична правильність", "points": 2},
        {"criteria": "Логіка", "description": "Логічність викладу", "points": 2}
    ]

    for activity in data:
        if activity.get('type') == 'essay-response':
            if isinstance(activity.get('rubric'), str):
                activity['rubric'] = rubric_obj
                modified = True
                print("Fixed rubric structure.")
            elif not activity.get('rubric'):
                activity['rubric'] = rubric_obj
                modified = True
                print("Added missing rubric.")
    
    if modified:
        with open(file_path, 'w') as f:
            yaml.dump(data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
        print("Completed.")
    else:
        print("No changes needed.")

fix_rubric('curriculum/l2-uk-en/c1/activities/17-irregular-verbs-complete.yaml')
