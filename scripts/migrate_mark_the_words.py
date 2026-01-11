import os
import re
from pathlib import Path

def migrate_activity_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split by '-' at start of line which indicates start of an activity
    parts = re.split(r'\n-\s+', '\n' + content)
    header = parts[0].lstrip()
    activities_raw = parts[1:]
    
    modified = False
    new_activities = []
    
    for act in activities_raw:
        if 'type: mark-the-words' in act:
            # 1. Standardize field names first
            if 'passage:' in act:
                act = act.replace('passage:', 'text:')
                modified = True
            if 'correct_words:' in act:
                act = act.replace('correct_words:', 'answers:')
                modified = True

            # 2. Extract text and answers fields
            text_pattern = r'(text:\s*)((?:>|\|)?\s*.*?)(?=\n\s*\w+:|\Z)'
            answers_pattern = r'(answers:\s*)(\n\s+-\s+.*?|(\s*\[\]\s*.*))(?=\n\s*\w+:|\Z)'
            
            text_match = re.search(text_pattern, act, re.DOTALL)
            answers_match = re.search(answers_pattern, act, re.DOTALL)
            
            if text_match and answers_match:
                raw_text_val = text_match.group(2).strip()
                # Clean quotes
                clean_text = raw_text_val
                if clean_text.startswith('"') and clean_text.endswith('"'):
                    clean_text = clean_text[1:-1]
                elif clean_text.startswith("'") and clean_text.endswith("'"):
                    clean_text = clean_text[1:-1]
                
                answers_raw = answers_match.group(2).strip()
                if answers_raw == '[]' or answers_raw.startswith('[]'):
                    answers = []
                else:
                    answers = [line.strip().lstrip('- ').strip().strip('"').strip("'") for line in answers_raw.split('\n') if line.strip()]

                final_text = clean_text
                if '*' not in clean_text and answers:
                    for ans in sorted(answers, key=len, reverse=True):
                        esc_ans = re.escape(ans)
                        # Corrected regex without newline break
                        boundary_pattern = r'(?<![\wа-яіїєґА-ЯІЇЄҐ])(' + esc_ans + r')(?![\\wа-яіїєґА-ЯІЇЄҐ])'
                        final_text = re.sub(boundary_pattern, r'*\1*', final_text, flags=re.IGNORECASE)
                
                # Reconstruct
                if '\n' in final_text or '"' in final_text or "'" in final_text:
                    new_text_val = '|\n    ' + final_text.replace('\n', '\n    ')
                else:
                    new_text_val = f'"{final_text}"'
                
                # Extract all fields EXCEPT answers
                all_fields = re.findall(r'(\w+):\s*((?:>|\|)?\s*.*?)(?=\n\s*\w+:|\Z)', act, re.DOTALL)
                field_dict = {f[0]: f[1].strip() for f in all_fields}
                
                # Update text
                field_dict['text'] = new_text_val
                
                # Remove answers key
                if 'answers' in field_dict:
                    del field_dict['answers']
                
                # Reconstruct activity string
                reordered_act = ""
                preferred_order = ['type', 'title', 'instruction', 'text']
                
                for k in preferred_order:
                    if k in field_dict:
                        reordered_act += f"{k}: {field_dict[k]}\n  "
                        del field_dict[k]
                
                for k, v in field_dict.items():
                    reordered_act += f"{k}: {v}\n  "
                
                act = reordered_act.strip()
                modified = True
            
            elif 'answers: []' in act:
                act = act.replace('answers: []', '').strip()
                act = re.sub(r'\n\s*\n', '\n', act)
                modified = True

        new_activities.append(act)
    
    if modified:
        new_content = header.strip() + '\n- ' + '\n- '.join([a.strip() for a in new_activities])
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content.strip() + '\n')
        return True
    return False

def main():
    base_dir = Path('curriculum/l2-uk-en')
    levels = ['a1', 'a2', 'b1', 'b2', 'c1', 'c2', 'lit']
    
    total_migrated = 0
    for level in levels:
        act_dir = base_dir / level / 'activities'
        if not act_dir.exists():
            continue
            
        print(f"Processing Level {level.upper()}...")
        for yaml_file in act_dir.glob('*.yaml'):
            try:
                if migrate_activity_file(yaml_file):
                    print(f"  Cleaned: {yaml_file.name}")
                    total_migrated += 1
            except Exception as e:
                print(f"  Error migrating {yaml_file.name}: {e}")
                
    print(f"\nTotal files cleaned: {total_migrated}")

if __name__ == "__main__":
    main()