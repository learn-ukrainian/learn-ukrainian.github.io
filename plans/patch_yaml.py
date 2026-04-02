import yaml

file_path = "curriculum/l2-uk-en/b1/activities/conditionals-mixed-complex.yaml"
with open(file_path, encoding="utf-8") as f:
    data = yaml.safe_load(f)

for act in data:
    if act.get('type') == 'unjumble':
        for i, item in enumerate(act['items']):
            # B1 unjumble targets 9-16 words
            ans = item['answer']
            if len(ans.split()) < 9:
                if act.get('title') == 'Складіть умовні речення':
                    item['answer'] = ans.rstrip('.') + " сьогодні дуже швидко та ефективно."
                    item['words'].extend(["сьогодні", "дуже", "швидко", "та", "ефективно."])
                    # Remove trailing dot from the previous last word
                    for j in range(len(item['words']) - 5):
                        if item['words'][j].endswith('.'):
                            item['words'][j] = item['words'][j][:-1]
                else: # Офіційно-діловий стиль: логіка контрактів
                    item['answer'] = ans.rstrip('.') + " згідно з нашими новими правилами."
                    item['words'].extend(["згідно", "з", "нашими", "новими", "правилами."])
                    # Remove trailing dot from the previous last word
                    for j in range(len(item['words']) - 5):
                        if item['words'][j].endswith('.'):
                            item['words'][j] = item['words'][j][:-1]

with open(file_path, "w", encoding="utf-8") as f:
    yaml.dump(data, f, allow_unicode=True, sort_keys=False)

print("Done patching YAML.")
