# Dialogue Situations in Plans

> Every plan that has dialogues MUST include `dialogue_situations` — specific, unique, grammar-motivated settings that prevent the writer from defaulting to generic scenes (кімната, стіл, сумка).

## Why

Without explicit dialogue situations, LLM writers default to safe, repetitive objects:
- M08-M14 all had "buying a bag" dialogues
- стіл appeared 170+ times across modules
- сумка appeared in 5 consecutive modules

The `dialogue_situations` field tells the writer WHERE the dialogue happens and WHAT objects are discussed.

## Format

```yaml
dialogue_situations:
  - setting: >
      At an outdoor flower market — choosing bouquets for different occasions.
      Describe: червоні троянди (roses), білі лілії (lilies), жовті соняшники
      (sunflowers), синя ваза (f), зелене листя (n, leaves). Use flowers, plants,
      and wrapping.
    speakers:
      - Наталка
      - Продавець (flower seller)
    motivation: >
      Color adjectives: червоний/а/е with троянда(f), соняшник(m), листя(n)
```

### Fields

| Field | Required | Description |
|-------|----------|-------------|
| `setting` | ✅ | WHERE the dialogue happens + WHAT specific objects are discussed. Must include Ukrainian nouns with gender labels: `(m)`, `(f)`, `(n)`, `(pl)`. The more specific, the better — the writer follows this literally. |
| `speakers` | ✅ | List of speaker names with roles. Use Ukrainian names. Avoid Russified forms (Лєна→Оленка, Ваня→Іванко). |
| `motivation` | ✅ | WHY this setting — which grammar does it naturally produce? Link objects to the grammar being taught. |

### Rules

1. **Every plan with dialogues gets `dialogue_situations`** — no exceptions
2. **No two modules in the same level share a setting** — unique situations only
3. **Objects must have gender labels** — `торт (m)`, `булочка (f)`, `тістечко (n)`, `вареники (pl)`
4. **Settings must motivate the grammar** — if the module teaches accusative, the setting must naturally require "I see X / I want X"
5. **Grammar scope must match** — don't include forms the learner hasn't seen yet (e.g., no synthetic future in A1, no adjective+locative before it's taught)
6. **Ukrainian cultural grounding** — use real Ukrainian places, foods, traditions, names. Not generic Western scenarios.
7. **No banned objects list needed** — if the setting is specific enough, the writer won't reach for сумка

### Placement in YAML

Insert BEFORE `content_outline:`:

```yaml
module: a1-010
level: A1
slug: colors
version: '1.1'
title: Colors
# ... other fields ...
dialogue_situations:    # ← HERE
  - setting: ...
    speakers: [...]
    motivation: ...
content_outline:        # ← dialogue_situations goes BEFORE this
  - section: ...
```

### Level-specific guidance

| Level | Setting complexity | Object detail | Cultural depth |
|-------|-------------------|---------------|----------------|
| A1 | Simple real-life (market, school, home) | 3-5 objects with genders | Basic (Ukrainian names, cities) |
| A2 | Moderate (post office, doctor, museum) | 4-6 objects with case forms | Medium (holidays, traditions) |
| B1 | Sophisticated (university, workplace, travel) | 5-8 objects, Ukrainian-specific | Deep (literature, history, regions) |
| B2+ | Full immersion (academic, professional, cultural) | Domain-specific terminology | Expert (politics, science, arts) |

### Script

Generate and apply dialogue situations:
```bash
# Dry run
.venv/bin/python scripts/add_dialogue_situations.py --track a1

# Apply
.venv/bin/python scripts/add_dialogue_situations.py --track a1 --apply
```

### Pipeline integration

The pipeline reads `dialogue_situations` from the plan and injects them into the write prompt via `{DIALOGUE_SITUATIONS}` placeholder. See `_build_dialogue_situations()` in `scripts/build/v6_build.py`.

## Coverage

| Track | Covered | Status |
|-------|---------|--------|
| A1 | 50/50 | ✅ Reviewed |
| A2 | 54/54 | ✅ Done |
| B1 | 91/91 | ✅ Done |
| B2 | — | Plans not written yet |
| C1 | — | Plans not written yet |
| C2 | — | Plans not written yet |

Issue: #1102
