# l2-uk-direct Track Architecture

> Last updated: 2026-02-27
> Status: Planning phase — A1/A2/B1 curriculum plans complete

---

## 1. Core Philosophy

**Five principles that drive everything:**

1. **Language-agnostic core from day one** — No English in content. Meaning is anchored through images, emoji, and pure Ukrainian context. L1 overlay is a separate optional file.
2. **Schema-first, content-second** — Every file type has a schema before any content is written. Schemas enforce pedagogical constraints (e.g., no translation field).
3. **Fewer files per module** — Maximum 3 files per module: `.yaml` (content + activities), `.status.json` (state), manifest entry. No orchestration directories.
4. **Pronunciation-first vocabulary** — `pronunciation_video` (YouTube URL) is required on all vocabulary entries. No IPA — native speaker video IS the pronunciation.
5. **Simpler state machine** — Flat `.status.json` per module. No nested orchestration state. Status values: `draft`, `ready`, `published`.

**This track exists because:**
- The existing `l2-uk-en` track is English-mediated — unsuitable for non-English learners
- L1-agnostic design enables reuse across any speaker community
- Inspired by Ukrainian Буквар pedagogy (Bolshakova, 2025): question words as grammar categories, pre-literacy concept sequence, image-anchored meaning

---

## 2. Target Audience

- Adults with **zero Ukrainian**
- **Self-study** primary use case (no teacher dependency)
- **No L1 assumption** — the content works for any learner
- Optional: teacher-guided use (teachers bring their own supplementary material)

---

## 3. Pedagogical Method

### Grammar Categories (no grammatical terms)
Following the Буквар model, grammar is expressed as question words:

| Question Word | What it covers |
|---|---|
| ХТО? | People, animals — subjects |
| ЩО? | Objects, concepts — subjects or objects |
| ЩО РОБИТЬ? | Actions — verbs |
| ЯКИЙ? ЯКА? ЯКЕ? | Descriptions — adjectives |
| ДЕ? | Location — place |
| КОЛИ? | Time — temporal expressions |
| СКІЛЬКИ? | Quantity — numbers |

### Sequence
Meaning before letters → sounds before symbols → letters → syllables → words → sentences.

Pre-literacy modules use only: video, emoji, images, sound categories (• = vowel, — = consonant). No written text in the first 3 modules.

### Medium of instruction
Ukrainian throughout. Explanatory notes in module YAML use Ukrainian (e.g., `notes`, `tricky_letters`).

---

## 4. File Structure

```
curriculum/l2-uk-direct/
  manifest.yaml                    ← module sequence (replaces numbered filenames)
  a1/
    abetka.yaml                    ← module content + activities
    abetka.status.json             ← flat status
    sklad.yaml
    sklad.status.json
    ...
  a2/
    ...

schemas/
  vocabulary-direct.schema.json    ← L1-agnostic vocabulary entry
  activities-direct.schema.json    ← activity types for direct method

docs/l2-uk-direct/
  ARCHITECTURE.md                  ← this file
  CURRICULUM-PLAN.md               ← full A1/A2 module sequence
  TOOLSET.md                       ← scripts, validators, image pipeline
```

### No numbered prefixes
Module ordering is defined in `manifest.yaml`. Files are named by slug only: `abetka`, `sklad`, `tse`. This makes reordering a 1-line manifest edit rather than a rename cascade.

---

## 5. Module Anatomy

### Module YAML (`.yaml`)
Single file contains everything: metadata, vocabulary entries (for vocab-type modules), activities.

**Special module types:**

| type | Description |
|---|---|
| `script_foundation` | Alphabet, sounds, script — no vocabulary entries |
| `vocabulary` | Themed vocabulary with question-word grammar |
| `grammar` | Grammar patterns (expressed as question words, not terms) |
| `checkpoint` | Assessment — no new content |

### Status JSON (`.status.json`)
```json
{
  "module": "abetka",
  "track": "l2-uk-direct",
  "level": "a1",
  "status": "draft",
  "images_sourced": 0,
  "images_total": 33,
  "last_updated": "2026-02-26",
  "notes": "Human-readable notes about current state."
}
```

Status values: `draft` → `ready` → `published`

### Manifest (`manifest.yaml`)
```yaml
track: l2-uk-direct
levels:
  a1:
    sequence:
      - abetka
      - sklad
      - ...
```

---

## 6. Vocabulary Schema

File: `schemas/vocabulary-direct.schema.json`

Key constraints:
- **No `translation` field** — language-agnostic design
- **`pronunciation_video` required** — YouTube URL (replaces IPA)
- **`examples` required** — minimum 2, Ukrainian sentences only
- **`question` field** — grammar category as question word enum

```yaml
# Example vocabulary entry
word: кіт
pronunciation_video: "https://www.youtube.com/watch?v=XXXXX"
emoji: 🐱
image_url: null          # null until Pixabay + Cloudinary sourced
image_alt: кіт сидить   # Ukrainian alt text
category: тварини
question: ХТО?
examples:
  - Це кіт.
  - Кіт спить.
context_video: null      # optional real-context video
```

---

## 7. Activity Types

File: `schemas/activities-direct.schema.json`

### Pre-literacy activities (no reading required)
| Type | Description | Use in |
|---|---|---|
| `watch_and_repeat` | Play video → learner repeats | abetka, early modules |
| `classify` | Drag items into symbol bins (•/—, images) | abetka, tse |
| `image_to_letter` | See emoji → tap which letter it starts with | abetka |

### Post-literacy activities (reading required — module 4+)
| Type | Description |
|---|---|
| `true_false` | Правда чи неправда? — from Буквар pedagogy |
| `build_sentence` | Arrange word tiles into correct Ukrainian sentence |
| `match_sound` | Match letter to sound description |
| `pattern_drill` | Complete a pattern — syllable reading, conjugation |

> **Critical constraint**: abetka (module 1) and sklad (module 2) activities MUST be pre-literacy. Learners cannot read yet. Activities may not contain Ukrainian text as interaction targets.

---

## 8. Image Pipeline

### Current state
All `image_url` fields are `null`. Images will be sourced in a separate pass.

### Planned pipeline
1. **Pixabay API search** — free, no attribution required for educational use
2. **Manual approval** — human selects from search results
3. **Cloudinary upload** — CDN hosting with transformation support
4. **Status update** — increment `images_sourced` in `.status.json`

Script to be built: `scripts/source_images_direct.py`

### Fallback hierarchy (runtime)
`image_url` → `emoji` → placeholder

---

## 9. Video Sources

### Anna Ohоiko alphabet playlist
- Playlist: `https://www.youtube.com/playlist?list=PLpkSIXDyaJi3mlJlKXWKhdiJZj67fPXQV`
- Permission: granted by Anna for educational use
- Coverage: all 33 Cyrillic letters, individual videos per letter
- Overview: `https://www.youtube.com/watch?v=ksXIXj7CXwc`

### Approved video sources
- Anna Ohоiko (Ukrainian Lessons Podcast) — free YouTube content ONLY
  - **Not permitted**: ULP lesson notes (premium content)
  - **Permitted**: YouTube videos, public blog posts
- Pure Ukrainian content only — no English narration or explanations

### `context_video` field
Optional field for real-world Ukrainian video content showing the word in natural context. Separate from `pronunciation_video`.

---

## 10. Textbook-to-CEFR Mapping: Approach C (Hybrid)

### The Problem

Ukrainian school textbooks (Grades 1–11) teach L1 literacy to native speakers — children who already know 5000+ words when they start school. They follow a **spiral curriculum**: every grammar concept is introduced simply, then revisited with increasing depth across grades. The same case system appears in Grade 1 (implicit), Grade 4 (named explicitly), Grade 6 (full paradigm tables), and Grade 11 (consolidated reference).

A rigid mapping like "A1 = Grade 1–2, A2 = Grade 3–4, B1 = Grade 5–6" breaks because:
- Grade 5 restarts ALL grammar with formal terminology — same content, higher abstraction
- Grade 6 has the BEST declension tables, but they're useful for A2 learners, not just B1
- Grade 11 has the most complete grammar reference, relevant to every level
- L2 learners need communicative vocabulary (transport, shopping, health) that textbooks never teach because native children absorb it from environment

### The Solution: Three-Layer Architecture

| Layer | Source | Role | Scope |
|-------|--------|------|-------|
| **Structure** | CEFR framework | Defines progression levels (A1 → A2 → B1 → B2) | Fixed |
| **Requirements** | State Standard 2024 | Defines WHAT to teach per level: communicative intentions, thematic areas, linguistic competence | Fixed |
| **Content library** | Textbooks (ALL grades) | Provides HOW to teach: explanations, examples, paradigm tables, activities | Searchable |

**Key principle**: Any module at any CEFR level can draw content from ANY textbook grade. An A2 case module might use Grade 4's question-word approach, Grade 6's paradigm tables, and Grade 3's practice exercises.

### Textbook Content Index

| Grade | Primary Author | Best Content For |
|-------|---------------|-----------------|
| 1 (Букvar) | Bolshakova 2025 | Alphabet, sounds-before-letters, pre-literacy, first words |
| 2 | Tsepova 2019 | Question-word grammar, basic sentence patterns |
| 3 | Vashulenko 2020 | Word structure, phonetics, folklore activities, prefix rules |
| 4 | Kravtsova/Savchenko 2021 | Case system (all 7 named), verb tenses, adjective agreement |
| 5 | Avramenko 2022 | Euphony tables, stress patterns, formal terminology, anti-суржик |
| 6 | Avramenko 2023 | Full declension paradigms, phraseology, morphology reference |
| 7–11 | Various | Advanced syntax, consolidated tables, NMT/ZNO prep (to be indexed) |

Research notes: `docs/l2-uk-direct/textbook-reading-notes/`

### What This Means in Practice

**For A2 case modules**: Use Grade 4's question-word approach to INTRODUCE the case. Use Grade 6's paradigm tables as REFERENCE. Use Grade 3's riddle/proverb activities for PRACTICE.

**For B1 declension modules**: Use Grade 6's full paradigm tables as PRIMARY source. Use Grade 5's formal terminology for NAMING. Use Grade 11 tables (once indexed) for CONSOLIDATION.

**For any vocabulary module**: State Standard 2024 defines required thematic areas. Textbooks provide themed word clusters. Missing daily-life vocabulary (transport, shopping, health) is sourced externally because textbooks never teach what native children already know.

---

## 11. State Standard Compliance

Reference: `docs/l2-uk-en/state-standard-2024-mapping.yaml`
Extracted requirements: `docs/l2-uk-direct/textbook-reading-notes/state-standard-2024-notes.md`

The Ukrainian State Standard 2024 defines WHAT to teach, not HOW. It is the structural spine of this curriculum. Every module must map to specific State Standard requirements.

### Key Level Constraints

| Constraint | A1 | A2 | B1 |
|-----------|----|----|-----|
| Cases | 4 (Н, Зн, М, Кл) | ALL 7 | ALL 7 (nuanced meanings) |
| Verb moods | Indicative + Imperative (2nd only) | + Full imperative (хай/нехай) | + Conditional |
| Sentence types | Simple + basic compound | + Complex with що/щоб/де/бо | + Full subordination |
| Vocabulary | 750 | 1800 cumulative | 3300 cumulative |
| Dialogue length | 4–6 turns | 8–10 turns | 10–12 turns |

See curriculum plans for full module-by-module alignment:
- `CURRICULUM-PLAN.md` (A1)
- `A2-CURRICULUM.md` (A2)
- `B1-CURRICULUM.md` (B1)

---

## 12. What This Track Is NOT

- Not a replacement for `l2-uk-en` — parallel track, different audience
- Not translation-based — no bilingual glossaries
- Not teacher-dependent — designed for solo study
- Not IPA-dependent — video pronunciation only
- Not image-generator-dependent — Pixabay/Cloudinary pipeline, no AI images
- Not tied to the Vibe project — Vibe is a separate rendering application
