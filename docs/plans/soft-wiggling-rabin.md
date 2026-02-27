# Plan: l2-uk-direct A1 Lesson Delivery

**GH Issue**: To be created with ACs below upon plan approval
**Scope**: Full A1 rendering pipeline — YAML modules become interactive Astro/Starlight lessons
**Depends on**: RAG infrastructure (#666, complete), abetka.yaml (complete), schemas (complete)

## Context

The l2-uk-direct track has a complete A1 curriculum plan (44 modules), schemas, and one drafted module (`abetka.yaml`). What's missing is the **delivery mechanism**: how does a `.yaml` file become an interactive lesson a learner can use? The existing `l2-uk-en` pipeline (`generate_mdx.py` + 36 React components) handles `.md` + activity YAML, but l2-uk-direct uses a **single `.yaml` per module** with a fundamentally different structure (letter cards, vocabulary entries with emoji/video, pre-literacy constraints). This plan designs the complete rendering pipeline from YAML to interactive lesson pages.

**Why the whole A1**: The 44 modules share a common pipeline. Building one module end-to-end would still require the full pipeline, so we design for all 44 from the start and validate with `abetka` first.

---

## Architecture: YAML to Interactive Lesson

### Pipeline Overview

```
curriculum/l2-uk-direct/a1/{slug}.yaml
    │
    ▼
scripts/generate_mdx_direct.py          ← NEW script
    │  reads module YAML
    │  selects template by module `type`
    │  renders content sections + activity components
    ▼
starlight/src/content/docs/direct/a1/{slug}.mdx
    │  Astro builds static page
    │  React components hydrate client-side
    ▼
Interactive lesson page at /direct/a1/{slug}/
```

### Module Type → Rendering Template

| Module `type` | Content Sections | Example Modules |
|---|---|---|
| `script_foundation` | Letter/sound cards (grouped into sessions) → activities | abetka, sklad, naholos |
| `communicative` | Phrase tables by function → mini-dialogues → activities | pryvit |
| `vocabulary` | Word cards (emoji + video + examples) → activities | tse, ya, shcho-robyt, yakyi |
| `grammar` | Pattern tables (question-word framed) → drills → activities | znavidminnyk-i, mistse |
| `checkpoint` | Summary cards (referencing prior modules) → assessment activities only | checkpoint-1, checkpoint-2, checkpoint-a1 |

### Key Design Principle: Sessions Within Modules

Large modules (e.g., `abetka` with 33 letters) are split into **sessions** — collapsible sections on a single page. The learner progresses through sessions sequentially. This avoids:
- Splitting one conceptual unit across multiple URLs
- Losing context between page navigations
- Needing a separate "lesson state" backend

---

## Step 1: Three New React Components

### 1a. `WatchAndRepeat.tsx`

**Purpose**: Play YouTube video, show letter/word, prompt learner to repeat aloud.
**Pre-literacy safe**: Yes — no reading required, visual + audio only.

```tsx
interface WatchAndRepeatItem {
  video: string;      // YouTube URL
  letter?: string;    // Letter being demonstrated (shown large)
  word?: string;      // Word being demonstrated
  note?: string;      // Teacher note (shown after video)
}

interface WatchAndRepeatProps {
  items: WatchAndRepeatItem[];
  title?: string;
  isUkrainian?: boolean;  // Always true for l2-uk-direct
}
```

**UI Design**:
- Each item: large letter display (200px font) → embedded YouTube player (lite-youtube-embed for performance) → "Повтори!" button (decorative encouragement, no recording)
- Items paginated: show 1 at a time with prev/next navigation
- Progress indicator: "3 / 10" showing current position
- If `word` is present, show it below the letter with emoji from vocabulary

**File**: `starlight/src/components/WatchAndRepeat.tsx`

### 1b. `Classify.tsx`

**Purpose**: Sort items into labelled bins by dragging/tapping.
**Pre-literacy safe**: Yes when bins use symbols (•, —) or emoji instead of text.

```tsx
interface ClassifyCategory {
  label: string;           // "Голосні", "Приголосні", "•", "—"
  symbolHint?: string;     // "vowel", "consonant" — drives icon rendering
  items: string[];         // Correct items for this bin
}

interface ClassifyProps {
  categories: ClassifyCategory[];
  title?: string;
  instruction?: string;
  isUkrainian?: boolean;
}
```

**UI Design**:
- Bins rendered as drop targets at top, each with label + optional icon (• for vowel, — for consonant)
- Shuffled item tiles below bins — drag to bin or tap item then tap bin (mobile-friendly)
- Instant feedback per item: green flash on correct, red bounce-back on wrong
- Completion state: all items sorted → success animation + score

**Why not reuse GroupSort**: GroupSort's `{[key: string]: string[]}` shape doesn't support `symbolHint`, and GroupSort checks all-at-once (submit button). Classify needs **per-item instant feedback** for pre-literacy learners who can't read error messages. Different interaction model justifies a new component.

**File**: `starlight/src/components/Classify.tsx`

### 1c. `ImageToLetter.tsx`

**Purpose**: See an emoji/image, tap which letter the word starts with.
**Pre-literacy safe**: Yes — emoji stimulus, letter-only options.

```tsx
interface ImageToLetterItem {
  emoji: string;            // "🍉"
  answer: string;           // "А"
  distractors: string[];    // ["Б", "В", "Г"]
  note?: string;            // Shown after correct answer
}

interface ImageToLetterProps {
  items: ImageToLetterItem[];
  title?: string;
  isUkrainian?: boolean;
}
```

**UI Design**:
- Large emoji display (120px) centered
- 3-4 letter options as large tap targets (60px square buttons)
- Options shuffled (answer mixed with distractors)
- Tap correct → green + next item auto-advances after 1s
- Tap wrong → red shake + try again (no penalty, max 2 wrong before hint)
- Progress bar at top

**File**: `starlight/src/components/ImageToLetter.tsx`

---

## Step 2: `generate_mdx_direct.py`

**New script**: Converts l2-uk-direct YAML → MDX with React component calls.

### Input
```
scripts/generate_mdx_direct.py --module curriculum/l2-uk-direct/a1/abetka.yaml
# or
scripts/generate_mdx_direct.py --all --level a1
```

### Processing Logic

1. **Parse YAML** → extract `type`, `title`, content sections, activities
2. **Select template** by `type`:
   - `script_foundation` → `_render_script_module()`
   - `communicative` → `_render_communicative_module()`
   - `vocabulary` → `_render_vocabulary_module()`
   - `grammar` → `_render_grammar_module()`
   - `checkpoint` → `_render_checkpoint_module()`
3. **Render content** as MDX sections with React components
4. **Render activities** using type → component mapping
5. **Write MDX** to `starlight/src/content/docs/direct/a1/{slug}.mdx`

### Activity Type → React Component Mapping

| YAML `type` | React Component | Existing? |
|---|---|---|
| `watch_and_repeat` | `<WatchAndRepeat>` | NEW |
| `classify` | `<Classify>` | NEW |
| `image_to_letter` | `<ImageToLetter>` | NEW |
| `true_false` | `<TrueFalse>` | EXISTS |
| `build_sentence` | `<Unjumble>` | EXISTS (reuse) |
| `match_sound` | `<MatchUp>` | EXISTS (reuse) |
| `pattern_drill` | `<FillIn>` | EXISTS (reuse) |
| `riddle` | `<Quiz>` | EXISTS (variant) |
| `tongue_twister` | `<WatchAndRepeat>` | NEW (variant: text + optional video) |
| `reading` | `<Reading>` | EXISTS |
| `proverb_drill` | `<Cloze>` or `<Quiz>` | EXISTS (variant by sub-type) |

### Content Renderers by Module Type

#### `_render_script_module()` — for abetka, sklad, naholos

```mdx
---
title: "Абетка"
---
import WatchAndRepeat from '../../components/WatchAndRepeat';
import Classify from '../../components/Classify';
import ImageToLetter from '../../components/ImageToLetter';

# Абетка

## Голосні (Vowels)

{/* Letter cards: А, Е, И, І, О, У, Є, Ї, Ю, Я */}
<LetterGrid letters={[...]} />

<WatchAndRepeat client:load items={[...]} title="Повтори голосні" />

## Приголосні — група 1 (Consonants — group 1)

{/* Letter cards: Б, В, Г, Ґ, Д */}
<LetterGrid letters={[...]} />

<WatchAndRepeat client:load items={[...]} title="Повтори приголосні" />

{/* ... more groups ... */}

## Вправи (Activities)

<ImageToLetter client:load items={[...]} title="Яка перша буква?" />
<Classify client:load categories={[...]} title="Голосні чи приголосні?" />
```

**LetterGrid**: A 4th new component — simple grid of letter cards showing upper/lower, emoji, key_word. Stateless display component (not interactive). Keeps the rendering clean.

#### `_render_vocabulary_module()` — for tse, ya, etc.

```mdx
## Нові слова (New Words)

<VocabCards words={[...]} />

{/* Each card: emoji (large) + word + pronunciation video button + 2 example sentences */}

## Вправи

<TrueFalse client:load items={[...]} isUkrainian />
<Classify client:load categories={[...]} title="ХТО? чи ЩО?" />
```

**VocabCard**: 5th new component — displays word entry with emoji, play-video button, example sentences. Stateless.

#### `_render_communicative_module()` — for pryvit

```mdx
## Привітання (Greetings)

<PhraseTable phrases={[...]} />

{/* Grouped by function: greetings, farewells, thanks, apologies */}

## Діалог (Dialogue)

<DialogueBox exchanges={[...]} />

## Вправи

<Classify client:load categories={[...]} />
<TrueFalse client:load items={[...]} isUkrainian />
```

**PhraseTable, DialogueBox**: Display-only components for structured phrase presentation.

### Summary: All New Components

| Component | Type | Purpose |
|---|---|---|
| `WatchAndRepeat` | Interactive | Video + repeat prompt |
| `Classify` | Interactive | Sort into bins with instant feedback |
| `ImageToLetter` | Interactive | Emoji → letter quiz |
| `LetterGrid` | Display | Letter card grid (upper/lower, emoji, key_word) |
| `VocabCard` | Display | Word entry (emoji, video button, examples) |
| `PhraseTable` | Display | Function-grouped phrase table |
| `DialogueBox` | Display | Speaker A/B dialogue display |

**File**: `scripts/generate_mdx_direct.py`
**Reuses**: `scripts/yaml_activities.py` patterns (dataclass → parser → renderer)

---

## Step 3: Abetka Session Design

33 letters grouped into 5 pedagogical sessions following Буквар sequence (sounds before symbols):

### Session 1: Голосні (Vowels) — 10 letters
А, Е, И, І, О, У (basic 6) → Є, Ї, Ю, Я (iotated 4)
- WatchAndRepeat: Anna Ohoiko videos for each letter
- Key teaching: 6 basic vowel sounds vs 4 "double" sounds (Й+vowel)

### Session 2: Сонорні (Sonorants) — 4 letters
Л, М, Н, Р
- Easiest consonants (can be sustained like vowels)
- Tricky: Р is trilled. WatchAndRepeat with focus drill.
- After this session: learner can form first syllables (МА, НО, ЛІ)

### Session 3: Дзвінкі (Voiced) — 7 letters
Б, В, Г, Ґ, Д, Ж, З
- Tricky pair: Г vs Ґ (fricative vs plosive). Dedicated WatchAndRepeat comparison.
- After this: learner knows all voiced consonants

### Session 4: Глухі (Voiceless) — 10 letters
К, П, С, Т, Ф, Х, Ц, Ч, Ш, Щ
- Tricky: Щ = /ʃtʃ/ (two sounds). Dedicated drill.
- Ц and Ч distinction

### Session 5: Особливі (Special) — 2 + signs
Й (semivowel), Ь (soft sign) + apostrophe (ʼ) + digraphs ДЖ, ДЗ
- Ь never starts a word, only softens
- Apostrophe separates: б'ю, п'ять, м'яч

### Activities (after all 5 sessions)
1. `image_to_letter` — 30+ items covering all letters
2. `classify` — vowels (•) vs consonants (—)
3. `classify` — voiced vs voiceless
4. `watch_and_repeat` — tricky pairs: Г/Ґ, И/І, Ш/Щ/Ч

---

## Step 4: Lesson Flow Templates (all 9 phases)

### Phase 0: Script (Modules 1-3)
**Pattern**: Session groups → WatchAndRepeat per group → pre-literacy activities
**Constraint**: NO reading. Activities use only emoji, video, letter tiles.
**Duration**: ~30 min per module

### Phase 1: First Words (Modules 4-9)
**Pattern**: Phrase/vocab presentation → example sentences → mixed activities
**Key**: Module 4 (`pryvit`) is communicative — phrases as fixed chunks, no grammar analysis.
Modules 5-9 introduce ХТО?/ЩО?/ЩО РОБИТЬ?/ЯКИЙ? via vocabulary.
**Activities**: classify (sort by question word), true_false, build_sentence, pattern_drill

### Phase 2: Sentences (Modules 10-16)
**Pattern**: Grammar pattern via question words → example paradigms → activities
**Key**: First sentence-building. Subject + verb + object structures.
**Activities**: build_sentence, pattern_drill, true_false, reading (short dialogues)

### Phase 3: Accusative (Modules 18-20)
**Pattern**: Case endings via question words (КОГО? ЩО?) → form tables → drills
**Activities**: pattern_drill (fill correct form), cloze, build_sentence

### Phase 4: Location (Modules 21-23)
**Pattern**: ДЕ? question word → prepositions + locative → city/home vocabulary
**Activities**: classify (preposition bins), pattern_drill, reading (city descriptions)

### Phase 5: Pronoun/Adj Forms (Modules 24-26)
**Pattern**: Form paradigms (мене/тебе/його; цей/той; adjective endings) → drills
**Activities**: pattern_drill, cloze, build_sentence

### Phase 6: Daily Life (Modules 27-33)
**Pattern**: Thematic vocabulary → real-world dialogues → mixed activities
**Key**: Past/future tense introduced here. Verb forms via ЩО РОБИВ?/ЩО БУДЕ РОБИТИ?
**Activities**: reading, build_sentence, classify, tongue_twister, riddle, proverb_drill

### Phase 7: World (Modules 35-38)
**Pattern**: Topical vocabulary (nature, family, holidays, travel) → longer readings
**Activities**: reading with comprehension, classify, pattern_drill

### Phase 8: Real-World (Modules 39-42)
**Pattern**: Imperative mood, signs/notices, letter writing → practical application
**Activities**: reading (signs), build_sentence (imperatives), pattern_drill

### Checkpoints (Modules 17, 34, 44)
**Pattern**: No new content. Assessment activities pulling from all prior modules.
**Activities**: Mixed quiz, cloze, pattern_drill, reading comprehension

---

## Step 5: State Standard A1 Compliance

### Communicative Intentions (Catalogue A) — all 17 covered

| # | Intention | Module(s) |
|---|---|---|
| 1 | Attract attention | pryvit (4) |
| 2 | Introduce self | ya (6) |
| 3 | Greet | pryvit (4) |
| 4 | Say goodbye | pryvit (4) |
| 5 | Thank | pryvit (4) |
| 6 | Apologize | pryvit (4) |
| 7 | Congratulate | pryvit (4), sviatky (37) |
| 8 | Wish | pryvit (4), sviatky (37) |
| 9 | Ask permission | nakazy (39) |
| 10 | Express agreement/disagreement | zapytuyu (13), checkpoint-1 (17) |
| 11 | Express ability | shcho-robyt (7) |
| 12 | Express desire | podobayetsya (15) |
| 13 | Express feelings | zovnishnist (16), zdorovia (31) |
| 14 | Express need | kupuvatysia (30) |
| 15 | Describe people/objects | yakyi (8), prykmetnyk-vidminky (26) |
| 16 | Describe location | mistse (21), misto (22) |
| 17 | Describe time | chas (27), den (28), mynule (29) |

### Thematic Areas (Catalogue B) — all 12 covered

| # | Theme | Module(s) |
|---|---|---|
| 1 | Personal identification | ya (6), pryvit (4) |
| 2 | Home | dim (23) |
| 3 | Daily life | den (28), chas (27) |
| 4 | Free time | dozvillia (33) |
| 5 | Travel | podorozhi (38) |
| 6 | Relations with others | sim-ya (36), pryvit (4) |
| 7 | Health | zdorovia (31) |
| 8 | Education | Not explicit — embedded in module interactions |
| 9 | Shopping | kupuvatysia (30), yizha (29) |
| 10 | Food and drink | yizha (29) |
| 11 | Services | kupuvatysia (30) |
| 12 | Places | misto (22), mistse (21) |

### Grammar Requirements
- Nominative (ХТО?/ЩО?): from module 5
- Accusative (КОГО?/ЩО?): modules 18-20
- Locative (ДЕ?/НА КОМУ?): modules 21-23
- Vocative: module 4 (embedded in greetings)
- 3 verb tenses: present (7), past (29), future (28)
- Imperative 2nd person: module 39
- ~750 vocabulary target: projected 760+ across 44 modules

---

## Step 6: Image Strategy

### Three-source hierarchy

1. **Custom SVGs** (primary for linguistic visuals):
   - Letter cards with pronunciation hints
   - Grammar diagrams (question-word frames)
   - Classification bin icons (•, —)
   - Generated by templates in `generate_mdx_direct.py` output

2. **Pixabay photos** (for real-world objects):
   - Pipeline: search → manual approval → Cloudinary upload
   - Script: `scripts/source_images_direct.py` (issue #664)
   - For vocabulary `image_url` fields

3. **Textbook images** (pattern library only):
   - Qdrant `search_images` for visual inspiration during module building
   - Never served directly (copyright)
   - Informs SVG/visual design decisions

### Fallback at render time
`image_url` → `emoji` (120px) → letter placeholder

---

## Implementation Order

| Step | What | Effort |
|---|---|---|
| 1 | Create 3 interactive React components (WatchAndRepeat, Classify, ImageToLetter) | Medium |
| 2 | Create 4 display components (LetterGrid, VocabCard, PhraseTable, DialogueBox) | Small |
| 3 | Create `generate_mdx_direct.py` with `script_foundation` template | Medium |
| 4 | Generate `abetka.mdx` and validate rendering in Starlight dev server | Small |
| 5 | Add remaining templates (vocabulary, communicative, grammar, checkpoint) | Medium |
| 6 | Build `sklad.yaml` and `naholos.yaml` (modules 2-3) + generate MDX | Medium |
| 7 | Build `pryvit.yaml` (module 4) — first post-literacy module | Small |
| 8 | Build modules 5-9 (first words) | Medium |
| 9 | Checkpoint: validate full Phase 0 + Phase 1 end-to-end | Small |

**Validate after step 4**: If abetka renders correctly with all 5 sessions, activities work, and the page is usable on mobile — the pipeline is proven. Then build remaining modules.

---

## Files

| File | Action |
|---|---|
| `starlight/src/components/WatchAndRepeat.tsx` | CREATE — video + repeat interactive |
| `starlight/src/components/Classify.tsx` | CREATE — sort into bins interactive |
| `starlight/src/components/ImageToLetter.tsx` | CREATE — emoji → letter quiz |
| `starlight/src/components/LetterGrid.tsx` | CREATE — letter card grid display |
| `starlight/src/components/VocabCard.tsx` | CREATE — word entry display |
| `starlight/src/components/PhraseTable.tsx` | CREATE — grouped phrase display |
| `starlight/src/components/DialogueBox.tsx` | CREATE — dialogue display |
| `scripts/generate_mdx_direct.py` | CREATE — YAML → MDX pipeline |
| `starlight/src/content/docs/direct/a1/abetka.mdx` | GENERATED — first test output |
| `starlight/src/styles/direct.css` | CREATE — l2-uk-direct specific styles |

## Verification

1. `npm run dev` in starlight → navigate to `/direct/a1/abetka/`
2. **LetterGrid**: All 33 letters visible across 5 sessions with emoji and key_word
3. **WatchAndRepeat**: YouTube videos play, "Повтори!" button visible, prev/next works
4. **Classify**: Drag vowels to • bin, consonants to — bin, instant feedback
5. **ImageToLetter**: Tap correct letter for each emoji, progress bar advances
6. **Mobile**: All components usable on 375px width (no horizontal scroll)
7. **Performance**: Page loads <3s (lite-youtube-embed, not full iframes)

## Acceptance Criteria

### AC1: React Components
- [ ] `WatchAndRepeat.tsx` renders YouTube embeds with letter display and prev/next navigation
- [ ] `Classify.tsx` renders drag/tap bins with instant per-item feedback
- [ ] `ImageToLetter.tsx` renders emoji + letter options with progress bar
- [ ] `LetterGrid.tsx` renders letter cards with upper/lower, emoji, key_word
- [ ] `VocabCard.tsx` renders word entry with emoji, video button, example sentences
- [ ] `PhraseTable.tsx` renders function-grouped phrase table
- [ ] `DialogueBox.tsx` renders speaker A/B dialogue exchanges
- [ ] All 7 components work with `isUkrainian={true}` (Ukrainian UI labels)
- [ ] All interactive components are mobile-usable at 375px width

### AC2: MDX Generation Script
- [ ] `generate_mdx_direct.py` reads a l2-uk-direct YAML and produces valid MDX
- [ ] Script supports all 5 module types: script_foundation, communicative, vocabulary, grammar, checkpoint
- [ ] All 11 l2-uk-direct activity types map to React components
- [ ] Generated MDX renders correctly in Starlight dev server (`npm run dev`)

### AC3: Abetka End-to-End
- [ ] `abetka.yaml` → `abetka.mdx` → renders at `/direct/a1/abetka/`
- [ ] 33 letters visible across 5 sessions (vowels, sonorants, voiced, voiceless, special)
- [ ] WatchAndRepeat activities play Anna Ohoiko videos
- [ ] Classify activity: sort letters into vowel/consonant bins
- [ ] ImageToLetter activity: 30+ emoji → letter items work
- [ ] Page loads <3s with lite-youtube-embed

### AC4: Pipeline Validation
- [ ] At least 3 modules rendered end-to-end (abetka + 2 others from different types)
- [ ] Pre-literacy constraint enforced: modules 1-2 only use watch_and_repeat, classify, image_to_letter
- [ ] All activity type → component mappings produce valid JSX

### AC5: State Standard Coverage (Documentation)
- [ ] All 17 communicative intentions mapped to specific modules
- [ ] All 12 thematic areas mapped to specific modules
- [ ] Grammar requirements (cases, tenses, imperative) mapped to modules

## Out of Scope

- Module YAML content for modules 2-44 (built incrementally after pipeline validates)
- Pixabay image sourcing (issue #664, separate pipeline)
- Learner progress tracking / state persistence (future: localStorage or backend)
- Audio recording for "repeat" verification (future: Web Audio API)
- L1 overlay system (future: optional translation file per L1)
