import os
import yaml

dir_path = 'curriculum/l2-uk-en/plans/ruth/'
files = [f for f in os.listdir(dir_path) if f.endswith('.yaml')]

results = []
for f in files:
    with open(os.path.join(dir_path, f), 'r') as stream:
        try:
            data = yaml.safe_load(stream)
            if data and 'sequence' in data:
                results.append((data['sequence'], data.get('module', f), f))
        except yaml.YAMLError as exc:
            print(f"Error parsing {f}: {exc}")

results.sort()
for seq, mod, fname in results:
    print(f"{seq}: {mod} ({fname})")
