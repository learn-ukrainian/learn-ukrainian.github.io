import yaml
from pathlib import Path

CURRICULUM_PATH = Path("curriculum/l2-uk-en/curriculum.yaml")
PLANS_BASE = Path("curriculum/l2-uk-en/plans")

# Load curriculum
with open(CURRICULUM_PATH, 'r') as f:
    curriculum = yaml.safe_load(f)

# 1. Add to c1-bio (Agency and Sacrifice)
bio_new = [
    "volodymyr-vakulenko",
    "victoria-amelina",
    "maksym-kryvtsov",
    "yuriy-ruf",
    "illia-chernilevskyi"
]
for slug in bio_new:
    if slug not in curriculum['levels']['c1-bio']['modules']:
        curriculum['levels']['c1-bio']['modules'].append(slug)

# 2. Add to lit-war (The Texts)
lit_war_new = [
    "yuriy-ruf-steel",
    "illia-chernilevskyi-poetry"
]
for slug in lit_war_new:
    if slug not in curriculum['levels']['lit-war']['modules']:
        curriculum['levels']['lit-war']['modules'].append(slug)

# 3. Add to c1-hist (Historiographical Continuity)
hist_new = [
    "continuity-of-cultural-genocide"
]
# Insert before final-syntez
hist_modules = curriculum['levels']['c1-hist']['modules']
if "continuity-of-cultural-genocide" not in hist_modules:
    idx = hist_modules.index("finalnyi-syntez")
    hist_modules.insert(idx, "continuity-of-cultural-genocide")

# Save updated curriculum
with open(CURRICULUM_PATH, 'w') as f:
    yaml.dump(curriculum, f, allow_unicode=True, sort_keys=False)

# 4. Generate the new plans
PLAN_TEMPLATE = """---
sequence: {sequence}
module: {track}-{sequence_str}
level: {level}
slug: {slug}
version: '2.0'
title: "{title}"
subtitle: "{subtitle}"
content_outline:
- section: "Вступ та контекст"
  words: 800
  points: []
- section: "{section2}"
  words: 1200
  points: []
- section: "{section3}"
  words: 1000
  points: []
- section: "Деколонізаційна перспектива"
  words: 800
  points:
  - "Зв'язок з Розстріляним Відродженням 1930-х"
  - "Українська суб'єктність та опір"
- section: "Підсумок та спадщина"
  words: 700
  points: []
word_target: 4500
vocabulary_hints:
  required:
  - "суб'єктність"
  - "тяглість"
  - "геноцид"
  recommended:
  - "деколонізація"
activity_hints:
- type: reading
  focus: "Аналіз життєвого шляху та вибору"
- type: essay-response
  focus: "Критичне есе про ціну культури"
focus: {focus}
pedagogy: seminar
immersion: 100% Ukrainian
phase: "Executed Renaissance 2.0"
objectives:
- "Дослідити життя та внесок {title} у сучасну українську культуру"
- "Проаналізувати історичну тяглість російських репресій проти української інтелігенції"
"""

def generate_plan(track, slug, title, focus, s2, s3):
    track_dir = PLANS_BASE / track
    track_dir.mkdir(parents=True, exist_ok=True)
    
    modules = curriculum['levels'][track]['modules']
    seq = modules.index(slug) + 1
    seq_str = f"{seq:02d}" if seq < 100 else f"{seq:03d}"
    level = track.upper().replace("-", ".")
    
    content = PLAN_TEMPLATE.format(
        sequence=seq,
        sequence_str=seq_str,
        track=track,
        level=level,
        slug=slug,
        title=title,
        subtitle=title,
        focus=focus,
        section2=s2,
        section3=s3
    )
    
    path = track_dir / f"{seq_str}-{slug}.yaml"
    with open(path, 'w') as f:
        f.write(content)
    print(f"Created plan: {path}")

# Generate specific plans
generate_plan("c1-bio", "volodymyr-vakulenko", "Володимир Вакуленко", "history", "Життя та мучеництво в Ізюмі", "Щоденник окупації: Голос з-під землі")
generate_plan("c1-bio", "victoria-amelina", "Вікторія Амеліна", "history", "Від романістки до дослідниці воєнних злочинів", "Концепція Нового Розстріляного Відродження")
generate_plan("c1-bio", "maksym-kryvtsov", "Максим Кривцов", "history", "Поет у камуфляжі: Творчий шлях", "Вірші з передньої лінії: Спадщина «Далі»")
generate_plan("c1-bio", "yuriy-ruf", "Юрій Руф", "history", "Націоналістичний інтелектуал та воїн", "Формування патріотичного світогляду")
generate_plan("c1-bio", "illia-chernilevskyi", "Ілля Чернілевський", "history", "Голос розстріляного покоління Z", "Музика та поезія спротиву")

generate_plan("lit-war", "yuriy-ruf-steel", "Юрій Руф: Поезія сталі", "literature", "Концепт «Літератури чину» в ХХІ столітті", "Мілітарна естетика та національна етика")
generate_plan("lit-war", "illia-chernilevskyi-poetry", "Ілля Чернілевський: Поезія несправдженого майбуття", "literature", "Ліризм та війна: Аналіз збірки", "Метафорика втраченої весни")

generate_plan("c1-hist", "continuity-of-cultural-genocide", "Тяглість культурного геноциду: 1937 vs 2022", "history", "Методи нищення: Від Сандармоху до Ізюма", "Історіографічне порівняння імперських практик")

print("Expansion complete.")
