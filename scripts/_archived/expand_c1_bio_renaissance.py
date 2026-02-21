import yaml
import os
import re
from pathlib import Path

# Figures to add (11 Renaissance + 5 Historical = 16 new)
NEW_FIGURES = [
    # Early Rus'
    {"slug": "volodymyr-monomakh", "name": "Володимир Мономах", "years": "1053-1125", "role": "Grand Prince of Kyiv", "birth": 1053},
    {"slug": "nestor-litopysets", "name": "Нестор Літописець", "years": "1056-1114", "role": "Chronicler", "birth": 1056},
    
    # Hetmanate
    {"slug": "ivan-vyhovskyi", "name": "Іван Виговський", "years": "1608-1664", "role": "Hetman", "birth": 1608},
    {"slug": "danylo-apostol", "name": "Данило Апостол", "years": "1654-1734", "role": "Hetman", "birth": 1654},
    {"slug": "pavlo-polubotok", "name": "Павло Полуботок", "years": "1660-1724", "role": "Hetman", "birth": 1660},

    # Executed Renaissance
    {"slug": "mykhailo-boichuk", "name": "Михайло Бойчук", "years": "1882-1937", "role": "Painter, founded Boychukism", "birth": 1882},
    {"slug": "mykola-zerov", "name": "Микола Зеров", "years": "1890-1937", "role": "Poet, translator, Neoclassicist leader", "birth": 1890},
    {"slug": "pavlo-fylypovych", "name": "Павло Филипович", "years": "1891-1937", "role": "Poet, Neoclassicist", "birth": 1891},
    {"slug": "oleksa-slisarenko", "name": "Олекса Слісаренко", "years": "1891-1937", "role": "Poet, Futurist", "birth": 1891},
    {"slug": "maik-yohansen", "name": "Майк Йогансен", "years": "1895-1937", "role": "Writer, Futurist", "birth": 1895},
    {"slug": "anatol-petrytskyi", "name": "Анатоль Петрицький", "years": "1895-1964", "role": "Painter/designer", "birth": 1895},
    {"slug": "yevhen-pluzhnyk", "name": "Євген Плужник", "years": "1898-1936", "role": "Poet, died in Solovki", "birth": 1898},
    {"slug": "dmytro-falkivskyi", "name": "Дмитро Фальківський", "years": "1898-1934", "role": "Poet", "birth": 1898},
    {"slug": "hryhorii-kosynka", "name": "Григорій Косинка", "years": "1899-1934", "role": "Short story master", "birth": 1899},
    {"slug": "valerian-pidmohylnyi", "name": "Валер'ян Підмогильний", "years": "1901-1937", "role": "Writer, author of \"Місто\"", "birth": 1901},
    {"slug": "heo-shkurupii", "name": "Гео Шкурупій", "years": "1903-1937", "role": "Poet, Futurist", "birth": 1903},
]

# Map of where to insert the new figures in the current list
# Format: { new_slug: existing_slug_to_insert_after }
INSERT_AFTER = {
    # Early Rus'
    "volodymyr-monomakh": "knyazhna-anna-yaroslavna",
    "nestor-litopysets": "volodymyr-monomakh",
    
    # Hetmanate
    "ivan-vyhovskyi": "petro-mohyla",
    "danylo-apostol": "ivan-mazepa",
    "pavlo-polubotok": "danylo-apostol",

    # Executed Renaissance
    "mykola-zerov": "valentyna-radzymovska",
    "pavlo-fylypovych": "mykola-zerov",
    "oleksa-slisarenko": "pavlo-fylypovych",
    "maik-yohansen": "oleksandr-dovzhenko",
    "anatol-petrytskyi": "maik-yohansen",
    "yevhen-pluzhnyk": "yuriy-kondratiuk",
    "dmytro-falkivskyi": "yevhen-pluzhnyk",
    "hryhorii-kosynka": "dmytro-falkivskyi",
    "valerian-pidmohylnyi": "kateryna-bilokur",
    "heo-shkurupii": "valerian-pidmohylnyi",
    "mykhailo-boichuk": "ivan-ohienko"
}

ROOT = Path("curriculum/l2-uk-en")
BIRTH_ORDER_PATH = ROOT / "c1-bio/BIRTH_ORDER.yaml"
CURRICULUM_PATH = ROOT / "curriculum.yaml"
PLANS_DIR = ROOT / "plans/c1-bio"
META_DIR = ROOT / "c1-bio/meta"

def extract_slugs_from_curriculum():
    with open(CURRICULUM_PATH, 'r') as f:
        content = f.read()
    
    lines = content.splitlines()
    slugs = []
    in_c1_bio = False
    in_modules = False
    
    for line in lines:
        if "c1-bio:" in line:
            in_c1_bio = True
            continue
        if in_c1_bio and "modules:" in line:
            in_modules = True
            continue
        if in_modules:
            stripped = line.strip()
            if stripped.startswith("-"):
                slug = stripped.split("#")[0].strip().replace("- ", "")
                if slug:
                    slugs.append(slug)
            elif stripped.startswith("#"):
                continue
            elif stripped == "":
                continue
            else:
                break
    return slugs

def update_ordered_list(existing_slugs):
    new_list = existing_slugs.copy()
    if "c1-bio-checkpoint" in new_list:
        new_list.remove("c1-bio-checkpoint")
        
    for fig in NEW_FIGURES:
        slug = fig['slug']
        if slug in new_list:
            continue
        after_slug = INSERT_AFTER.get(slug)
        if not after_slug or after_slug not in new_list:
            print(f"Warning: {slug} insertion point '{after_slug}' not found, appending to end.")
            new_list.append(slug)
            continue
        idx = new_list.index(after_slug)
        new_list.insert(idx + 1, slug)
    return new_list

def save_birth_order(ordered_slugs):
    data = {"modules": ordered_slugs}
    with open(BIRTH_ORDER_PATH, 'w') as f:
        yaml.dump(data, f, sort_keys=False)

def save_curriculum(ordered_slugs):
    with open(CURRICULUM_PATH, 'r') as f:
        content = f.read()
    
    lines = content.splitlines()
    new_lines = []
    in_c1_bio = False
    in_modules = False
    skip = False
    
    for line in lines:
        if "c1-bio:" in line:
            in_c1_bio = True
            new_lines.append(line)
            continue
        if in_c1_bio and "modules:" in line:
            in_modules = True
            new_lines.append(line)
            new_lines.append(f"      # C1-BIO chronological order by birth date ({len(ordered_slugs)} biographies)")
            for i, slug in enumerate(ordered_slugs):
                new_lines.append(f"      - {slug} # [{i+1}]")
            skip = True
            continue
        if in_modules and line.strip().startswith("-"):
            continue
        if in_modules and line.strip().startswith("# C1-BIO"):
            continue
        if in_modules and (line.strip() == "" or (not line.strip().startswith("-") and not line.strip().startswith("#"))):
            in_modules = False
            in_c1_bio = False
            skip = False
        if not skip:
            new_lines.append(line)
            
    with open(CURRICULUM_PATH, 'w') as f:
        f.write("\n".join(new_lines) + "\n")

def create_and_update_plans(ordered_slugs):
    new_slug_map = {f['slug']: f for f in NEW_FIGURES}
    
    for i, slug in enumerate(ordered_slugs):
        plan_path = PLANS_DIR / f"{slug}.yaml"
        seq = i + 1
        
        if slug in new_slug_map:
            fig = new_slug_map[slug]
            if not plan_path.exists():
                # Create default plan structure for NEW modules
                p = {
                    "module": slug,
                    "level": "C1-BIO",
                    "sequence": seq,
                    "slug": slug,
                    "version": "2.0",
                    "title": f"{fig['name']}: <!-- Title -->",
                    "content_outline": [
                        {"section": "Вступ", "words": 400, "points": ["<!-- point -->"]},
                        {"section": "Життєпис", "words": 600, "points": ["<!-- point -->"]},
                        {"section": "Внесок та діяльність", "words": 800, "points": ["<!-- point -->"]},
                        {"section": "Останні роки / Спадщина", "words": 700, "points": ["<!-- point -->"]},
                        {"section": "Підсумок", "words": 100, "points": ["<!-- point -->"]},
                    ],
                    "focus": "biography",
                    "pedagogy": "seminar",
                    "objectives": [f"Дізнатися про життя та роль {fig['name']}"],
                    "module_type": "biography",
                    "immersion": "100% Ukrainian"
                }
                with open(plan_path, 'w') as f:
                    yaml.dump(p, f, sort_keys=False, allow_unicode=True)
            else:
                # Update existing plan's sequence
                with open(plan_path, 'r') as f:
                    p = yaml.safe_load(f)
                if p.get('sequence') != seq:
                    p['sequence'] = seq
                    with open(plan_path, 'w') as f:
                        yaml.dump(p, f, sort_keys=False, allow_unicode=True)
                    print(f"Updated sequence for {slug} to {seq}")

            # Meta sync
            meta_path = META_DIR / f"{slug}.yaml"
            if not meta_path.exists():
                meta = {
                    "module": slug,
                    "level": "C1-BIO",
                    "slug": slug,
                    "version": "1.0",
                    "id": slug,
                    "naturalness": {"score": 0, "status": "PENDING"},
                    "duration": 90,
                    "tags": ["Biography", "Patriot"],
                    "validation_tier": "llm-verified"
                }
                os.makedirs(META_DIR, exist_ok=True)
                with open(meta_path, 'w') as f:
                    yaml.dump(meta, f, sort_keys=False)
                print(f"Created plan and meta for {slug}")
        else:
            if plan_path.exists():
                with open(plan_path, 'r') as f:
                    p = yaml.safe_load(f)
                if p.get('sequence') != seq:
                    p['sequence'] = seq
                    with open(plan_path, 'w') as f:
                        yaml.dump(p, f, sort_keys=False, allow_unicode=True)
                    print(f"Updated sequence for {slug} to {seq}")

if __name__ == "__main__":
    existing = extract_slugs_from_curriculum()
    ordered = update_ordered_list(existing)
    save_birth_order(ordered)
    save_curriculum(ordered)
    create_and_update_plans(ordered)
    print(f"Success! Track now has {len(ordered)} modules (No checkpoint).")
