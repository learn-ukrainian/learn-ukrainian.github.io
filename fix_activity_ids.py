
import yaml
import sys
import re

file_path = "curriculum/l2-uk-en/b2/activities/03-impersonal-passive.yaml"

with open(file_path, 'r') as f:
    activities = yaml.safe_load(f)

for activity in activities:
    if activity['type'] == 'cloze':
        print(f"Fixing cloze: {activity['title']}")
        # Extract placeholders from passage to ensure IDs match
        passage = activity['passage']
        placeholders = re.findall(r'\{([^}]+)\}', passage)
        
        # Map answers to their blanks
        # We assume the order of blanks matches the order of placeholders
        # Or we can try to match by answer if it's the same
        
        if len(activity['blanks']) != len(placeholders):
            print(f"WARNING: Mismatch blanks ({len(activity['blanks'])}) vs placeholders ({len(placeholders)})")
        
        for i, blank in enumerate(activity['blanks']):
            if 'id' not in blank:
                # Use the placeholder text as ID if possible, otherwise answer
                # But typically the ID in the blank object MUST match the text inside {} in the passage.
                # If the passage has {прийнято} and answer is прийнято, then id is прийнято.
                
                # Let's try to get the placeholder at index i
                if i < len(placeholders):
                    blank['id'] = placeholders[i]
                else:
                    # Fallback to answer, but this might be risky if passage differs
                    blank['id'] = blank['answer']
                
                print(f"  Added id: {blank['id']}")

with open(file_path, 'w') as f:
    yaml.dump(activities, f, allow_unicode=True, sort_keys=False)

print("Done.")
