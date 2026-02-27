# Plan: l2-uk-direct Curriculum Rebuild — A1 + A2 + B1

**GH Issues**: #661, #662 (will be updated), new issues for A2/B1
**Scope**: Complete curriculum plans for A1, A2, B1 — built from Ukrainian textbooks + State Standard 2024
**Replaces**: The old 44-module A1 plan (thrown out — designed from LLM memory, not from sources)

## Why

The existing A1 curriculum (44 modules) was designed from LLM memory. Key problems:
- **арбуз** used as key word for А (Russian word — Ukrainian is кавун, and textbooks use автобус)
- Emoji placeholders instead of textbook illustrations
- YouTube videos that don't match what students should be learning
- Module content invented rather than sourced from actual Ukrainian pedagogy
- Textbooks treated as decoration, not as the primary teaching material

The fix: **read the textbooks first, design the curriculum from them**.

## Phase 1: Research (BLOCKING — must complete before ANY planning)

### 1a. Read State Standard 2024 — A1, A2, B1 sections

File: `docs/l2-uk-en/UKRAINIAN-STATE-STANDARD-2024.txt` (6020 lines)
Mapping: `docs/l2-uk-en/state-standard-2024-mapping.yaml`

For each level, extract:
- §1: Speech activities (listening, reading, writing, speaking) — what can they DO?
- §2 Catalogue A: All communicative intentions — what situations must they handle?
- §3 Catalogue B: All thematic areas — what topics must they cover?
- §4 Catalogue C: Linguistic competence — what phonetics, morphology, syntax?
- Vocabulary targets (A1: 750, A2: ?, B1: ?)

### 1b. Read Ukrainian textbooks — one author per grade, systematically

**Selection**: Pick ONE primary author per grade for deep reading. Use others for cross-reference.

| Grade | Primary Author | PDF | Pages | Covers |
|-------|---------------|-----|-------|--------|
| 1 | Bolshakova (2025) | Part 1 + Part 2 | ~250 | ✅ Already read |
| 2 | Bolshakova (2019) | Part 1 + Part 2 | ~250 | ✅ Already read |
| 3 Part 1 | Vashulenko (2020) | Part 1 | ~160 | ✅ Already read |
| 3 Part 2 | Vashulenko (2020) | Part 2 | ~160 | 🔲 MUST READ |
| 4 | Kravtsova (2021) | Part 1 | ~160 | 🔲 MUST READ |
| 4 | Savchenko (2021) | Part 2 | ~160 | 🔲 MUST READ |
| 5 | Avramenko (2022) | мова | ~250 | 🔲 MUST READ |
| 6 | Avramenko (2023) | мова | ~250 | 🔲 MUST READ |

**~980 pages** of new reading across 5 PDFs.

For each textbook, document:
- Teaching sequence (what order are topics introduced?)
- Grammar concepts and how they're explained
- Vocabulary clusters with example words
- Activity types used (загадки, правда/неправда, скоромовки, etc.)
- What illustrations/images teach (not just decorate)
- Key pedagogical patterns that should inform our modules

### 1c. Map Bolshakova Букvar pages to letters (for abetka rebuild)

Systematically read every page of Bolshakova Part 1 + Part 2 to build:
- Complete letter → page mapping (all 33 letters)
- Correct key words (from the textbook, not invented)
- Syllable tables used per letter
- Stories and reading exercises per letter
- Activity types per letter page

### 1d. Cross-reference textbooks

For key teaching concepts, check 2-3 authors to validate:
- Do they agree on the teaching sequence?
- What vocabulary do different authors use for the same concept?
- What activity types appear across all textbooks? (these are proven pedagogy)

## Phase 2: Curriculum Design

**Only starts after ALL Phase 1 reading is complete.**

### 2a. CEFR-to-Textbook mapping

Based on the reading, map which textbook content corresponds to which CEFR level:
- A1: Grade ? content
- A2: Grade ? content
- B1: Grade ? content

This mapping comes FROM the reading, not from assumptions.

### 2b. Module design — from textbooks, not from memory

For each level:
1. List all State Standard requirements (communicative intentions, thematic areas, grammar)
2. Map each requirement to specific textbook pages/sections that teach it
3. Group related textbook content into modules
4. Design activities that practice what the textbook page teaches
5. Select textbook images as primary teaching content (emoji = absolute last fallback)
6. Add video only where it genuinely supplements the teaching (pronunciation demos)

### 2c. Module YAML structure update

Based on what we learn from the textbooks, update:
- The YAML schema to properly support textbook images as primary content
- The `image_ref` field usage (page-level references to specific textbook pages)
- The `image_sources` attribution system
- Activity types to match what Ukrainian pedagogues actually use

### 2d. Write curriculum plans

One plan document per level:
- `docs/l2-uk-direct/A1-CURRICULUM.md`
- `docs/l2-uk-direct/A2-CURRICULUM.md`
- `docs/l2-uk-direct/B1-CURRICULUM.md`

Each plan includes:
- Module list with teaching objectives (from State Standard)
- Textbook source mapping (which pages feed each module)
- Activity types per module
- Image references per module
- Vocabulary targets with actual word lists (from textbooks)
- State Standard compliance checklist

## Phase 3: Implementation

### 3a. Rebuild abetka.yaml from Bolshakova Букvar

- Correct key words from actual textbook pages
- image_ref for every letter (textbook page images)
- Activities that match what the textbook teaches
- No invented content

### 3b. Update components and generator

- LetterGrid: show textbook images, not emoji
- WatchAndRepeat: video as supplement, not primary
- New component: TextbookPage (shows a textbook page with optional annotations)
- generate_mdx_direct.py: handle image_ref rendering

### 3c. Build modules level by level

Follow the curriculum plans. Each module built from textbook sources.

## Phase 4: Image Quality + Search Testing

After curriculum planning, build a web-based test suite for image search quality:
- Search interface to query Qdrant image collection
- Visual results display (see the actual images)
- Quality scoring (relevance, resolution, clarity)
- Coverage report (which modules have images, which don't)

## Files

| File | Action |
|------|--------|
| `docs/l2-uk-direct/CURRICULUM-PLAN.md` | REWRITE — old plan thrown out |
| `docs/l2-uk-direct/A1-CURRICULUM.md` | CREATE — new A1 from textbooks |
| `docs/l2-uk-direct/A2-CURRICULUM.md` | CREATE — new A2 from textbooks |
| `docs/l2-uk-direct/B1-CURRICULUM.md` | CREATE — new B1 from textbooks |
| `docs/l2-uk-direct/textbook-reading-notes/` | CREATE — research notes per grade |
| `curriculum/l2-uk-direct/a1/abetka.yaml` | REWRITE — from Bolshakova pages |
| `curriculum/l2-uk-direct/a1/sklad.yaml` | REWRITE — from textbook pedagogy |
| `curriculum/l2-uk-direct/manifest.yaml` | REWRITE — new module list |
| `schemas/activities-direct.schema.json` | UPDATE — new activity types from textbooks |
| `scripts/image_search_test.py` | CREATE — web-based image search tester |

## Verification

1. Every module traces back to specific textbook pages (no invented content)
2. Every key word verified against actual textbook usage
3. State Standard compliance: all communicative intentions, thematic areas, grammar requirements covered
4. Image coverage: every module has textbook image references
5. Cross-validated against 2+ textbook authors where possible

## Estimated Reading Work

| Item | Pages | Time Est. |
|------|-------|-----------|
| State Standard A1+A2+B1 | ~500 lines | 1 session |
| Grade 3 Part 2 | ~160 pages | 1 session |
| Grade 4 Parts 1+2 | ~320 pages | 2 sessions |
| Grade 5 мова | ~250 pages | 1 session |
| Grade 6 мова | ~250 pages | 1 session |
| Bolshakova letter mapping | ~120 pages | 1 session |
| **Total** | ~1600 pages | ~7 sessions |

Research notes saved to `docs/l2-uk-direct/textbook-reading-notes/` for cross-session persistence.
