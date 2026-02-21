import yaml
import os
from pathlib import Path

CURRICULUM_PATH = "curriculum/l2-uk-en/curriculum.yaml"
PLANS_BASE = Path("curriculum/l2-uk-en/plans")

# Load curriculum
with open(CURRICULUM_PATH, 'r') as f:
    curriculum = yaml.safe_load(f)

# 1. Expand LIT canon with patriotic gaps
lit_modules = curriculum['levels']['lit']['modules']

# Insertions
dov_idx = lit_modules.index('dovzhenko-cinema-as-literature')
new_phase4_authors = ['samchuk-maria', 'barka-yellow-prince', 'osmachka-prose']
for i, slug in enumerate(new_phase4_authors):
    if slug not in lit_modules:
        lit_modules.insert(dov_idx + 1 + i, slug)

mal_idx = lit_modules.index('malyshko-songs')
resistance_poets = ['malaniuk-poetry', 'teliha-poetry', 'olzhych-poetry']
for i, slug in enumerate(resistance_poets):
    if slug not in lit_modules:
        lit_modules.insert(mal_idx + 1 + i, slug)

izd_idx = lit_modules.index('izdryk-poetry')
if 'andijewska-magic-realism' not in lit_modules:
    lit_modules.insert(izd_idx + 1, 'andijewska-magic-realism')

# 2. Expand specialized tracks
essay_modules = curriculum['levels']['lit-essay']['modules']
new_essayists = ['solomea-pavlychko-modernism', 'oxana-hundorova-postcolonialism', 'vira-ageyeva-canon']
for slug in new_essayists:
    if slug not in essay_modules:
        essay_modules.append(slug)

war_modules = curriculum['levels']['lit-war']['modules']
new_war_poets = ['maksym-kryvtsov-poetry', 'yaryna-chornohuz-war']
for slug in new_war_poets:
    if slug not in war_modules:
        war_modules.append(slug)

# 3. Clean up non-UA first authors
if 'kourkov-grey-bees' in curriculum['levels']['lit-hist-fic']['modules']:
    curriculum['levels']['lit-hist-fic']['modules'].remove('kourkov-grey-bees')
    if 'shevchuk-three-leaves' not in curriculum['levels']['lit-hist-fic']['modules']:
        curriculum['levels']['lit-hist-fic']['modules'].append('shevchuk-three-leaves')

# Save updated curriculum
with open(CURRICULUM_PATH, 'w') as f:
    yaml.dump(curriculum, f, allow_unicode=True, sort_keys=False)

print(f"Updated {CURRICULUM_PATH}")

# 4. Generate plan skeletons for all literature tracks
LIT_TRACKS = ["lit", "lit-essay", "lit-hist-fic", "lit-fantastika", "lit-war", "lit-humor", "lit-juvenile"]

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
- section: "Аналіз ключових творів"
  words: 1200
  points: []
- section: "Стилістика та мова автора"
  words: 1000
  points: []
- section: "Деколонізаційна перспектива"
  words: 800
  points:
  - "Як цей автор руйнує імперські міфи"
  - "Українська суб'єктність у тексті"
- section: "Підсумок та спадщина"
  words: 700
  points: []
word_target: 4500
vocabulary_hints:
  required:
  - "історіографія"
  - "наратив"
  - "суб'єктність"
  recommended:
  - "деколонізація"
activity_hints:
- type: reading
  focus: "Аналіз першоджерела"
- type: essay-response
  focus: "Критичне есе"
- type: critical-analysis
  focus: "Деконструкція тексту"
focus: literature
pedagogy: literature
immersion: 100% Ukrainian
phase: "{phase}"
objectives:
- "Проаналізувати творчість {title} у контексті української літератури"
- "Дослідити вплив автора на формування національної ідентичності"
"""

def slug_to_title(slug):
    return slug.replace("-", " ").title()

for track in LIT_TRACKS:
    track_dir = PLANS_BASE / track
    track_dir.mkdir(parents=True, exist_ok=True)
    
    modules = curriculum['levels'][track]['modules']
    level = track.upper().replace("-", ".")
    
    # Get existing plans to find their slugs (to avoid duplicates)
    existing_slugs = set()
    for f in track_dir.glob("*.yaml"):
        existing_slugs.add(f.stem.split("-", 1)[-1] if "-" in f.stem and f.stem[0].isdigit() else f.stem)

    for i, slug in enumerate(modules):
        seq = i + 1
        seq_str = f"{seq:02d}" if seq < 100 else f"{seq:03d}"
        
        # Check if plan already exists (either bare or numbered)
        if slug in existing_slugs:
            continue
            
        # For lit track, check if it's already there with a number
        found = False
        for f in track_dir.glob(f"*-{slug}.yaml"):
            found = True
            break
        if found:
            continue

        # Generate new plan
        title = slug_to_title(slug)
        content = PLAN_TEMPLATE.format(
            sequence=seq,
            sequence_str=seq_str,
            track=track,
            level=level,
            slug=slug,
            title=title,
            subtitle=title,
            phase="LIT Expansion"
        )
        
        plan_path = track_dir / f"{seq_str}-{slug}.yaml"
        with open(plan_path, 'w') as f:
            f.write(content)
        print(f"Created plan: {plan_path}")

print("Plan generation complete.")
