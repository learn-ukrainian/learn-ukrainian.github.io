import json
with open('schemas/activities-base.schema.json', 'r') as f:
    schema = json.load(f)

for def_name, def_val in schema.get('$defs', {}).items():
    if def_name == 'fill-in':
        print(json.dumps(def_val, indent=2))
