import yaml

# 1. Fix Activities YAML
act_path = "curriculum/l2-uk-en/bio/activities/petro-mohyla.yaml"
with open(act_path, 'r') as f:
    acts = yaml.safe_load(f)

# Find and fix comparative-study
for act in acts:
    if act.get('type') == 'comparative-study':
        act.pop('items', None)
        act.pop('id', None)
        act['items_to_compare'] = ["Києво-Могилянський колегіум", "Єзуїтські колегіуми"]
        act['criteria'] = ["Мова викладання", "Ставлення до античної філософії", "Кінцева мета освіти"]
        act['model_answer'] = "Обидві системи використовували латину та античну філософію як базис. Проте колегіум Могили застосовував ці інструменти для захисту православної ідентичності, тоді як єзуїти - для католицької експансії та контрреформації."

with open(act_path, 'w') as f:
    yaml.dump(acts, f, allow_unicode=True, sort_keys=False)

# 2. Fix Markdown File
md_path = "curriculum/l2-uk-en/bio/petro-mohyla.md"
with open(md_path, 'r') as f:
    md_content = f.read()

# Fix Euphony
md_content = md_content.replace("в праці", "у праці")
md_content = md_content.replace("в приватних", "у приватних")
md_content = md_content.replace("в традиціях", "у традиціях")

# Add words
md_content = md_content.replace(
    "Це був абсолютно безпрецедентний випадок в історії:",
    "Це був абсолютно безпрецедентний та унікальний випадок у всій тодішній світовій історії:"
)

md_content = md_content.replace(
    "і нерозривний зв'язок між якісною освітою та розбудовою успішної демократичної держави.",
    "і нерозривний зв'язок між глибокою, якісною європейською освітою та розбудовою успішної, сильної демократичної держави."
)

with open(md_path, 'w') as f:
    f.write(md_content)

print("Fixes applied successfully.")
