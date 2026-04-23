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
| `setting` | ✅ (writer-only metadata) | WHERE the dialogue happens + WHAT specific objects are discussed. **NEVER rendered as prose in the student module.** Must include Ukrainian nouns with gender labels: `(m)`, `(f)`, `(n)`, `(pl)`. The more specific, the better — the writer uses this as scene-planning context only. |
| `speakers` | ✅ | List of speaker names with roles. Use Ukrainian names. Avoid Russified forms (Лєна→Оленка, Ваня→Іванко). |
| `motivation` | ✅ | WHY this setting — which grammar does it naturally produce? Link objects to the grammar being taught. |
| `turns` | ✅ for A1/A2 (2026-04-23 onward) | **The canonical render source** — an ordered list of `{speaker, ua, en_gloss?}`. The writer renders these directly as block-quote speaker lines. See `turns:` section below. |

### `turns:` — canonical render source (added 2026-04-23)

**Background:** Before this convention, writers rendered `setting:` directly as English stage-direction narration ("Ліза picks a party outfit with Дмитро's help. He also asks how to recognize Оля…") before the actual Ukrainian turns. This consistently killed the Dialogue & Conversation Quality review dim (see `docs/reports/2026-04-23-a1-colors-opus-r1-dim-diagnosis.md` §3.3). Root cause: the plan only gave `setting:` as English metadata; the writer had no turn-by-turn skeleton so it invented stage directions.

**`turns:` fixes this.** With `turns:` present, the writer has a ready speaker-by-speaker skeleton. `setting:` becomes pure writer-side metadata that is NEVER rendered as prose in the module.

#### Shape

```yaml
dialogue_situations:
  - setting: 'На відкритому квітковому ринку — червоні троянди, білі лілії, жовті соняшники, синя ваза (f), зелене листя (n). (писати-тільки; не рендерити як прозу)'
    speakers:
      - Наталка
      - Продавець
    motivation: 'Запитання «Якого кольору?» + узгодження з троянда(f), соняшник(m), листя(n), ваза(f)'
    turns:
      - { speaker: Наталка, ua: "Які гарні троянди! Якого вони кольору?" }
      - { speaker: Продавець, ua: "Червоні." }
      - { speaker: Наталка, ua: "А ці лілії — білі?" }
      - { speaker: Продавець, ua: "Так, білі лілії." }
      - { speaker: Наталка, ua: "Мені подобаються жовті соняшники." }
      - { speaker: Продавець, ua: "Добре. Загорнути букет?" }
      - { speaker: Наталка, ua: "Так, дякую. У синю стрічку." }
```

Optional `en_gloss:` per turn for rare/novel vocabulary only — **not a full translation** of each line. A1–A2 learners should be reading Ukrainian, not reading English beside Ukrainian.

#### Writer render contract

When `turns:` is present, the writer MUST:
- Render EACH turn as a block-quote speaker line in Ukrainian: `> **Ім'я:** текст`
- Use 5–8 turns per dialogue for A1–A2; 6–12 for B1; 8–15 for B2+
- Write **≤2 sentences** of analytical gloss in English AFTER the dialogue, pointing at 1–2 specific forms (e.g. "`Якого кольору?` is a fixed pattern — `якого` agrees with `колір` in genitive masculine"). No summary narration of what happened in the scene.
- NEVER emit English framing narration ("Liza picks an outfit…", "The scene opens at a market…"). The `setting:` field is not for rendering.
- NEVER render `setting:` or `motivation:` as prose. Those are writer-side planning context only.

#### Backward compatibility

For plans authored before 2026-04-23 that have only `setting:` without `turns:`, the writer MAY synthesize 5–8 turns from `setting:` + `motivation:` — but the acceptance gate is the same: block-quote turns, ≤2 sentences of gloss, no stage direction narration. Scale-lock passes should add `turns:` to the plan when the dialogue is authoritatively validated.

#### Audit gate (optional but recommended)

`scripts/audit/checks/dialogue_density.py` (new — see EPIC #1451 Phase 3-B): dialogue sections must be ≥70% turn-line content; non-dialogue prose ≤30% of section body. Triggers on sections whose plan has non-empty `dialogue_acts`.

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

## Beyond Dialogues: B2-C2 Situations

At B2 level and above, the curriculum evolves beyond simple dialogues. Plans for B2, C1, and C2 must incorporate:
- **Reading Situations**: Analytical reading of articles, literature, and documents.
- **Listening Situations**: Comprehension of videos, podcasts, and lectures.
- **Writing Tasks**: Structured production (essays, formal letters, ZNO-style "власне висловлення").
- **Discussion Topics**: Argumentative speaking and debates.

For detailed guidance on B2+ plan fields, see [B2-C2 Plan Architecture](b2-c2-plan-architecture.md).

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
