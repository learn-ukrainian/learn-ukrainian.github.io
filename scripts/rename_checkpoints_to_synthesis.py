import yaml
from pathlib import Path

CURRICULUM_PATH = Path("curriculum/l2-uk-en/curriculum.yaml")
PLANS_BASE = Path("curriculum/l2-uk-en/plans")

# Load curriculum
with open(CURRICULUM_PATH, 'r') as f:
    curriculum = yaml.safe_load(f)

# Mapping of old slugs to new synthesis slugs
MAPPING = {
    "lit": {
        "phase-1-checkpoint": "synthesis-1",
        "phase-2-checkpoint": "synthesis-2",
        "phase-3-checkpoint": "synthesis-3",
        "phase-4-checkpoint": "synthesis-4",
        "phase-5-checkpoint": "synthesis-5",
    },
    "lit-essay": {
        "essay-capstone-1": "essay-synthesis-1",
        "essay-capstone-2": "essay-synthesis-2",
    },
    "lit-hist-fic": {
        "hist-fic-capstone": "hist-fic-synthesis",
    },
    "lit-fantastika": {
        "fantastika-capstone": "fantastika-synthesis",
    },
    "lit-war": {
        "war-lit-capstone": "war-lit-synthesis",
    },
    "lit-humor": {
        "humor-capstone": "humor-synthesis",
    },
    "lit-juvenile": {
        "kids-capstone": "juvenile-synthesis",
    }
}

SYNTHESIS_TEMPLATE = """---
sequence: {sequence}
module: {track}-{sequence_str}
level: {level}
slug: {slug}
version: '2.0'
title: "Синтез: {title_uk}"
subtitle: "Intellectual Synthesis: {title_en}"
content_outline:
- section: "Діахронний аналіз: Зв'язок поколінь"
  words: 1000
  points:
  - "Еволюція ключових ідей та архетипів у вивченому періоді"
  - "Як пізніші автори ведуть діалог з попередниками"
- section: "Деколонізаційна оптика: Сталева нитка"
  words: 1200
  points:
  - "Спільні стратегії інтелектуального опору в різних жанрах"
  - "Деконструкція імперського наративу як системний процес"
- section: "Стилістичний калейдоскоп"
  words: 800
  points:
  - "Порівняльний аналіз авторських технік та мовних експериментів"
  - "Трансформація літературної мови від епохи до епохи"
- section: "Філософія ідентичності"
  words: 1000
  points:
  - "Конструювання образу українського суб'єкта"
  - "Література як простір формування національної етики"
- section: "Спадщина та горизонти майбутнього"
  words: 500
  points:
  - "Вплив періоду на сучасний літературний процес"
  - "Значення канону для інтелектуальної безпеки"
word_target: 4500
vocabulary_hints:
  required:
  - "діахронія"
  - "синтез"
  - "архетип"
  - "інтертекстуальність"
  - "дискурс"
  recommended:
  - "деколонізація"
  - "суб'єктність"
activity_hints:
- type: comparative-study
  focus: "Порівняння ідеологічних концепцій двох ключових авторів періоду"
- type: authorial-intent
  focus: "Аналіз прихованих смислів та стратегій опору в текстах"
- type: essay-response
  focus: "Синтезуюче есе про роль літератури у державотворенні"
focus: literature
pedagogy: literature
immersion: 100% Ukrainian
phase: "{phase}"
objectives:
- "Синтезувати знання про літературний процес вивченого періоду"
- "Застосувати деколонізаційну оптику для аналізу взаємозв'язків між авторами"
- "Оцінити тяглість української інтелектуальної традиції"
"""

def get_titles(old_slug, track):
    if track == "lit":
        num = old_slug.split("-")[1]
        return f"Горизонти епохи {num}", f"Horizons of Era {num}"
    if "essay" in old_slug:
        num = old_slug[-1]
        return f"Інтелектуальна броня {num}", f"Intellectual Armor {num}"
    if "war" in old_slug:
        return "Література чину", "Literature of Action"
    if "hist-fic" in old_slug:
        return "Палімпсести пам'яті", "Palimpsests of Memory"
    if "fantastika" in old_slug:
        return "Простір уяви", "Space of Imagination"
    if "humor" in old_slug:
        return "Зброя сміху", "Weapon of Laughter"
    if "kids" in old_slug or "juvenile" in old_slug:
        return "Формування майбутнього", "Shaping the Future"
    return "Великий синтез", "Great Synthesis"

# Process each track
for track, mapping in MAPPING.items():
    if track not in curriculum['levels']:
        continue
        
    modules = curriculum['levels'][track]['modules']
    track_dir = PLANS_BASE / track
    
    for old_slug, new_slug in mapping.items():
        if old_slug in modules:
            # 1. Update curriculum.yaml
            idx = modules.index(old_slug)
            modules[idx] = new_slug
            print(f"[{track}] Renamed {old_slug} -> {new_slug}")
            
            # 2. Prepare data for template
            seq = idx + 1
            seq_str = f"{seq:02d}" if seq < 100 else f"{seq:03d}"
            level = track.upper().replace("-", ".")
            phase = f"{track.upper()} Synthesis"
            title_uk, title_en = get_titles(old_slug, track)
            
            # 3. Create new plan
            new_content = SYNTHESIS_TEMPLATE.format(
                sequence=seq,
                sequence_str=seq_str,
                track=track,
                level=level,
                slug=new_slug,
                title_uk=title_uk,
                title_en=title_en,
                phase=phase
            )
            
            new_plan_path = track_dir / f"{seq_str}-{new_slug}.yaml"
            new_plan_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 4. Remove old plan file if exists
            for old_file in track_dir.glob(f"*-{old_slug}.yaml"):
                old_file.unlink()
                print(f"  Deleted old plan: {old_file}")
            
            # 5. Write new plan
            with open(new_plan_path, 'w') as f:
                f.write(new_content)
            print(f"  Created synthesis plan: {new_plan_path}")

# Save updated curriculum
with open(CURRICULUM_PATH, 'w') as f:
    yaml.dump(curriculum, f, allow_unicode=True, sort_keys=False)

print(f"Successfully updated {CURRICULUM_PATH} and all synthesis plans.")
