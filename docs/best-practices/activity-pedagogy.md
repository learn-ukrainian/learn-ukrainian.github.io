# Activity Pedagogy — Type System and Allowlist Matrix

> **Scope:** WHICH activity types belong at WHICH CEFR level, and why.
> **Complementary doc:** [`vocabulary-activity-standards.md`](vocabulary-activity-standards.md) covers YAML format, property names, quoting, and validation. This doc covers pedagogical progression and the level → type allowlist.
> **Source of truth:** [`scripts/pipeline/config_tables.py`](../../scripts/pipeline/config_tables.py) — `ACTIVITY_CONFIGS`, `INLINE_ONLY_TYPES`, `WORKBOOK_ONLY_TYPES`.
> **Enforcement:** [`scripts/build/activity_repair.py`](../../scripts/build/activity_repair.py) drops out-of-allowlist activities and moves misplaced ones between inline/workbook.

---

## 1. The 8+1 Pedagogical Principles

These are the rules that govern the level → type allowlist matrix in `ACTIVITY_CONFIGS`. Every change to the matrix must keep all eight principles intact. The +1 is a known gap (dictation) that is tracked separately.

### Principle 1 — Puzzle-gamification fades with level

Pure puzzle types — `anagram`, `unjumble`, `order`, `odd-one-out`, `observe`, `phrase-table`, `classify` — are beginner dopamine hits. They decrease as the learner matures.

| Level | Puzzle density |
|---|---|
| A1, A2 | Heavy |
| B1 | Present (sparingly, one per module for variety) |
| B2 and above | Gone |

`match-up` and `group-sort` are **not** puzzle-gamification — they are legitimate comprehension checks used in Ukrainian academic materials and ZNO exams through C2.

### Principle 2 — A1 phonetics never reappear

`image-to-letter`, `letter-grid`, `watch-and-repeat`, `divide-words`, `count-syllables`, `pick-syllables` are A1-only tools for learning to read Cyrillic. Forbidden at A2 and above — the learner already decodes fluently.

### Principle 3 — Metalinguistic analysis earns in at B1

| Type | First allowed |
|---|---|
| `mark-the-words` | A2 (sparingly, grammar spotting) |
| `grammar-identify` | B1 |
| `highlight-morphemes` | B1 |

These require naming grammatical categories in Ukrainian — wait until the learner has the metalanguage.

### Principle 4 — Production-long earns in at B1

| Type | First allowed | Rationale |
|---|---|---|
| `essay-response` | B1 | Learner has enough morphology to write a paragraph |
| `reading` (long passage) | B2 | Learner can process 200+ word passages |
| `translation-critique` | B2 | Requires register awareness |
| `critical-analysis` | C1 | Requires academic Ukrainian |

These take 10–15 minutes each. They live in the workbook, never inline.

### Principle 5 — Zero gamification in seminars

HIST, BIO, ISTORIO, LIT, OES, RUTH are **content tracks**. Zero puzzle types. Only reading → evaluation → writing. The "tab" metaphor (inline/workbook) stays; the puzzle metaphor goes.

Inline checks use only `quiz`, `true-false`, `fill-in`, `mark-the-words`, `match-up` — just enough to verify comprehension without breaking scholarly tone.

### Principle 6 — No seminar in early language levels

`essay-response`, `reading`, `critical-analysis` are **never** allowed at A1 (not enough Ukrainian to read a passage).

- `essay-response` — from B1
- `reading` — from B2
- `critical-analysis` — from C1

### Principle 7 — Philological types are track-gated

| Type | Allowed tracks |
|---|---|
| `etymology-trace` | C1, C2 (as "word history"), OES, RUTH (as discipline) |
| `paleography-analysis` | OES, RUTH only |
| `transcription` | OES, RUTH only |
| `dialect-comparison` | RUTH only |

### Principle 8 — ZNO (TODO, deferred schema)

Issue [#715](https://github.com/anthropics/learn-ukrainian/issues/715) tracks ZNO integration. The plan is a dedicated `zno` type with 8 subcategories (наголос, пароніми, орфографія, case endings, lexical choice, phonetics, word formation, punctuation), added at the schema level before the B2 content build. When the type lands, append it to the WORKBOOK allowlists for B2, C1, C2, B2-PRO, C1-PRO.

Interim: ZNO questions are generated as `quiz` with a ZNO-style question bank.

### Principle +1 — Dictation (диктант) is a known gap

Ukrainian pedagogy's most iconic exercise has no schema type yet. A `dictation` type (audio → text input with stress and orthography checking) is required and will be central at A1–B1. Tracked separately from [#1185](https://github.com/anthropics/learn-ukrainian/issues/1185); file a schema ticket before the next A1 revision batch.

---

## 2. Activity Types Classified by Pedagogical DNA

37 types total (36 active + 1 deprecated). Each entry: purpose, level range.

### Phonetics / Alphabet (A1 only)

| Type | Purpose | Where |
|---|---|---|
| `image-to-letter` | Click the picture whose name starts with a given Cyrillic letter | A1 inline |
| `letter-grid` | Alphabet reference grid with hover/click audio | A1 inline |
| `watch-and-repeat` | Pronunciation video with repeat prompt | A1 inline |
| `divide-words` | Split a word into syllables visually | A1 inline + workbook |
| `count-syllables` | Count syllables in a word | A1 inline + workbook |
| `pick-syllables` | Choose the correct syllable to complete a word | A1 inline + workbook |

Gone forever from A2 onward. Principle 2.

### Puzzle-gamification (fades by B2)

| Type | Purpose | Where |
|---|---|---|
| `anagram` | Unscramble letters into a word | A1 workbook only |
| `unjumble` | Reorder shuffled words into a correct sentence | A1–B1 |
| `order` | Put items in correct sequence (chronological, logical) | A1–B1 |
| `odd-one-out` | Pick the item that doesn't belong with the rest | A1–B1 |
| `observe` | Study a picture/diagram and answer | A1–A2 |
| `phrase-table` | Fill cells in a substitution table | A1–A2 |
| `classify` | Assign items to categories (listed in comment, not currently in any allowlist; deprecated in favor of `group-sort`) | — |

### Sort / Match (not gamification, runs through C2)

| Type | Purpose | Where |
|---|---|---|
| `match-up` | Pair items between two columns (word↔translation, question↔answer, term↔definition) | A1 through seminars and C1-core |
| `group-sort` | Assign items to 2+ bins (gender, case, aspect, register) | A1 through B2-PRO |

These survive because Ukrainian school materials and ZNO exams use them at every level. They are comprehension, not puzzle.

### Core comprehension checks

| Type | Purpose | Where |
|---|---|---|
| `quiz` | Multiple-choice question with 2–5 options | All tracks, all levels |
| `true-false` | Judge a statement against the text | A1–B2, all seminars except C1/C2-core |
| `fill-in` | Short-answer blank in a single sentence | All tracks, all levels |
| `mark-the-words` | Click every word matching a criterion in a passage | A2 onward, all tracks |

### Production (short → long)

| Type | Purpose | Where |
|---|---|---|
| `error-correction` | Find and fix errors in given sentences | A1 workbook onward, core tracks only |
| `cloze` | Multi-blank passage, 14+ gaps | A2–C1, workbook only (Principle 4) |
| `translate` | Translate sentences between UK and EN | A1–C1, workbook only. **Gone at C2** — at C2 translation is professional, not exercise; use `translation-critique` |

### Metalinguistic (earns in at B1)

| Type | Purpose | Where |
|---|---|---|
| `grammar-identify` | Name the grammatical category of a highlighted form (case, aspect, tense) | B1–C2 core, B2/C1-PRO, OES, RUTH |
| `highlight-morphemes` | Mark prefix/root/suffix/ending in words | B1 onward in core, central in OES/RUTH |

### Academic / long-form

| Type | Purpose | Where |
|---|---|---|
| `essay-response` | 50–500 word free writing to a prompt | B1+ and all seminars, workbook only |
| `reading` | Long passage (200+ words) + comprehension questions | B2+ and all seminars, workbook only |
| `critical-analysis` | Deep argumentative response to a claim or source | C1+, all seminars, workbook only |
| `translation-critique` | Compare two translations of the same Ukrainian text | B2+, LIT, workbook only |
| `comparative-study` | Multi-text comparison | C1+, all seminars except pure HIST early, workbook only |

### Seminar-specific

| Type | Purpose | Where |
|---|---|---|
| `source-evaluation` | Scholarly evaluation of a primary source's reliability | HIST, BIO, ISTORIO, workbook only |
| `authorial-intent` | Analyze why an author wrote something a particular way | C2, BIO, LIT, workbook only |
| `debate` | Multi-turn argumentative exchange on a thesis | C2, LIT, workbook only |

### Philological (OES / RUTH)

| Type | Purpose | Where |
|---|---|---|
| `etymology-trace` | Trace a word through historical stages | C1, C2, OES, RUTH, workbook only |
| `paleography-analysis` | Analyze script / manuscript features | OES, RUTH, workbook only |
| `transcription` | Transcribe from old orthography to modern | OES, RUTH, workbook only |
| `dialect-comparison` | Compare forms across Ukrainian dialects | RUTH only, workbook only |

### Deprecated

| Type | Status |
|---|---|
| `select` | Legacy, subsumed by `mark-the-words`. Listed in every level's `FORBIDDEN_ACTIVITY_TYPES`. New content must not produce it. |

---

## 3. Full Allowlist Matrix

Rows = levels, columns = activity types. Cell legend:

- `B` — allowed in **b**oth inline and workbook
- `I` — **i**nline only
- `W` — **w**orkbook only
- `-` — not allowed at this level

This matrix is generated directly from `ACTIVITY_CONFIGS`. To regenerate, see the script in section 5.

### Counts per level

| Level | Total | Inline min–max | Workbook min–max | Items min | Vocab target |
|---|---|---|---|---|---|
| a1 | 10 | 4–6 | 6–9 | 6 | 20 |
| a2 | 12 | 4–6 | 8–11 | 8 | 25 |
| b1-core | 16 | 5–7 | 11–15 | 8 | 30 |
| b2 | 16 | 5–7 | 11–15 | 8 | 30 |
| c1-core | 16 | 5–7 | 11–15 | 8 | 30 |
| c2 | 12 | 4–5 | 8–10 | 6 | 30 |
| hist | 10 | 3–4 | 7–9 | 4 | 25 |
| bio | 10 | 3–4 | 7–9 | 4 | 30 |
| istorio | 10 | 3–4 | 7–9 | 4 | 30 |
| lit | 10 | 3–4 | 7–9 | 4 | 0 (no vocab gate) |
| b2-pro | 12 | 4–5 | 8–10 | 6 | 35 |
| c1-pro | 12 | 4–5 | 8–10 | 6 | 40 |
| oes | 10 | 3–4 | 7–9 | 4 | 35 |
| ruth | 10 | 3–4 | 7–9 | 4 | 35 |

### Type → level matrix

| Type | a1 | a2 | b1-core | b2 | c1-core | c2 | hist | bio | istorio | lit | b2-pro | c1-pro | oes | ruth |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| image-to-letter      | I | - | - | - | - | - | - | - | - | - | - | - | - | - |
| letter-grid          | I | - | - | - | - | - | - | - | - | - | - | - | - | - |
| watch-and-repeat     | I | - | - | - | - | - | - | - | - | - | - | - | - | - |
| divide-words         | B | - | - | - | - | - | - | - | - | - | - | - | - | - |
| count-syllables      | B | - | - | - | - | - | - | - | - | - | - | - | - | - |
| pick-syllables       | B | - | - | - | - | - | - | - | - | - | - | - | - | - |
| anagram              | W | - | - | - | - | - | - | - | - | - | - | - | - | - |
| unjumble             | B | B | B | - | - | - | - | - | - | - | - | - | - | - |
| order                | B | B | B | - | - | - | - | - | - | - | - | - | - | - |
| odd-one-out          | B | B | W | - | - | - | - | - | - | - | - | - | - | - |
| observe              | B | B | - | - | - | - | - | - | - | - | - | - | - | - |
| phrase-table         | B | W | - | - | - | - | - | - | - | - | - | - | - | - |
| classify             | - | - | - | - | - | - | - | - | - | - | - | - | - | - |
| match-up             | B | B | B | B | I | - | I | I | I | I | B | I | - | - |
| group-sort           | B | B | B | B | - | - | - | - | - | - | W | - | - | - |
| quiz                 | B | B | B | I | I | I | I | I | I | I | I | I | I | I |
| true-false           | B | B | B | B | - | - | I | I | I | I | I | - | I | I |
| fill-in              | B | B | B | B | B | I | I | I | I | I | B | B | I | I |
| mark-the-words       | - | B | B | B | B | I | B | B | B | B | B | B | B | B |
| error-correction     | W | B | B | B | B | W | - | - | - | - | B | B | - | - |
| cloze                | - | W | W | W | W | W | - | - | - | - | W | W | - | - |
| translate            | W | W | W | W | W | - | - | - | - | - | W | W | - | - |
| grammar-identify     | - | - | B | B | B | B | - | - | - | - | B | B | B | B |
| highlight-morphemes  | - | - | B | B | B | B | - | - | - | - | B | B | B | B |
| essay-response       | - | - | W | W | W | W | W | W | W | W | W | W | W | W |
| reading              | - | - | - | W | W | W | W | W | W | W | W | W | W | W |
| critical-analysis    | - | - | - | - | W | W | W | W | W | W | - | W | W | W |
| translation-critique | - | - | - | W | W | W | - | - | - | W | W | W | - | - |
| comparative-study    | - | - | - | - | W | W | W | W | W | W | - | W | W | W |
| source-evaluation    | - | - | - | - | - | - | W | W | W | - | - | - | - | - |
| authorial-intent     | - | - | - | - | - | W | - | W | - | W | - | - | - | - |
| debate               | - | - | - | - | - | W | - | - | - | W | - | - | - | - |
| etymology-trace      | - | - | - | - | W | W | - | - | - | - | - | - | W | W |
| paleography-analysis | - | - | - | - | - | - | - | - | - | - | - | - | W | W |
| dialect-comparison   | - | - | - | - | - | - | - | - | - | - | - | - | - | W |
| transcription        | - | - | - | - | - | - | - | - | - | - | - | - | W | W |

Reading the matrix:

- A column full of `-` except for A1 means a phonetics type (Principle 2).
- Puzzle-gamification types (`anagram`, `unjumble`, `order`, `odd-one-out`, `observe`, `phrase-table`) form a triangle shrinking from A1 to B1, then empty from B2 onward (Principle 1).
- `quiz`, `fill-in`, `mark-the-words`, `match-up` are the backbone rows — present at almost every level.
- The bottom block (`essay-response` through `transcription`) is strictly workbook-only production/academic types, earning in at progressively higher levels (Principles 4, 6, 7).

---

## 4. Special Rules (Semantic Placement)

Two sets in `config_tables.py` override the per-level allowlist for **placement only**. A type in these sets is restricted regardless of level config.

### `INLINE_ONLY_TYPES`

```
image-to-letter, letter-grid, watch-and-repeat
```

These are short visual aids that cannot work inside the workbook tab. If a writer puts one in workbook, the repair step (`activity_repair.py` FIX 4) moves it to inline.

### `WORKBOOK_ONLY_TYPES`

```
essay-response, reading, cloze, critical-analysis,
source-evaluation, debate, comparative-study,
authorial-intent, translation-critique,
etymology-trace, paleography-analysis,
transcription, dialect-comparison
```

These are long-form types that would break prose flow if placed inline. The repair step moves them to workbook.

### How `activity_repair.py` enforces the allowlist

See [`scripts/build/activity_repair.py`](../../scripts/build/activity_repair.py). The relevant fixes:

1. **FIX 4 — Section placement.** Walks inline list; any activity whose type is in `WORKBOOK_ONLY_TYPES` is moved to the workbook list. Walks workbook list; any activity whose type is in `INLINE_ONLY_TYPES` is moved to inline and assigned a stable id.
2. **FIX 5 — Allowlist violations.** Collects every activity whose type is not in the per-level `INLINE_ALLOWED_TYPES` or `WORKBOOK_ALLOWED_TYPES` for its section. Drops them from the YAML.
3. **Regen trigger.** After drops, if `len(inline) < INLINE_MIN` or `len(workbook) < WORKBOOK_MIN`, the module is marked `needs_regen` and the pipeline re-runs the activities step. Otherwise the repaired YAML ships as-is.

The writer is never asked to "please respect the allowlist" in the prompt — the prompt ships the allowed set as the complete list of options, and the repair step deterministically corrects any drift. This is faster, cheaper, and more reliable than nagging an LLM.

---

## 5. How to Change the System

**There is one place to edit: `ACTIVITY_CONFIGS` in [`scripts/pipeline/config_tables.py`](../../scripts/pipeline/config_tables.py).** Do not scatter allowlists into writer prompts, review prompts, or schema files. The config loader resolves level-aware settings from this single dict.

### Change workflow

1. **Edit the config.** Change `INLINE_ALLOWED_TYPES`, `WORKBOOK_ALLOWED_TYPES`, `FORBIDDEN_ACTIVITY_TYPES`, and `INLINE_PRIORITY_TYPES` / `WORKBOOK_PRIORITY_TYPES` together. Keep the legacy `ALLOWED_ACTIVITY_TYPES` field as the union of inline + workbook. Verify all 8 principles still hold.
2. **Run the in-wild survey script** (below) to see which existing activity YAMLs would be affected. This reports how many activities per level would be dropped under the new allowlist.
3. **Verify no unintended drops.** Any drop should match a principle. If the script reports a drop you didn't expect, investigate whether the existing YAML is wrong or your config change is too strict.
4. If the change adds a new level, add the full entry to `ACTIVITY_CONFIGS` — the loader reads it by key. If the change adds a new activity type, also update the schema file (`schemas/activities-*.schema.json`) and the type list in section 2 of this doc.

### In-wild survey script

Save as a one-off or run from a REPL. Walks all activity YAMLs under `curriculum/l2-uk-en/{level}/activities/`, counts types per section, and reports gaps against the current config.

```python
"""Survey activity YAMLs against the current allowlist.

Reports, per level:
- total modules
- inline/workbook types currently in use
- types that would be dropped under the live config
- modules that would fall below INLINE_MIN/WORKBOOK_MIN after drops
"""
import sys, collections, pathlib, yaml
sys.path.insert(0, 'scripts')
from pipeline.config_tables import (
    ACTIVITY_CONFIGS, INLINE_ONLY_TYPES, WORKBOOK_ONLY_TYPES,
)

CURRICULUM = pathlib.Path("curriculum/l2-uk-en")

def parse_types(csv: str) -> set[str]:
    return {t.strip() for t in csv.split(",") if t.strip()}

def survey(level: str) -> None:
    cfg = ACTIVITY_CONFIGS.get(level)
    if not cfg:
        print(f"[{level}] no config — skipping")
        return
    inline_allowed = parse_types(cfg["INLINE_ALLOWED_TYPES"])
    wb_allowed = parse_types(cfg["WORKBOOK_ALLOWED_TYPES"])
    imin = int(cfg["INLINE_MIN"])
    wmin = int(cfg["WORKBOOK_MIN"])

    act_dir = CURRICULUM / level / "activities"
    if not act_dir.is_dir():
        print(f"[{level}] no activities dir")
        return

    inline_counter: collections.Counter = collections.Counter()
    wb_counter: collections.Counter = collections.Counter()
    drops_inline: collections.Counter = collections.Counter()
    drops_wb: collections.Counter = collections.Counter()
    under_min = []

    files = sorted(act_dir.glob("*.yaml"))
    for f in files:
        try:
            data = yaml.safe_load(f.read_text()) or {}
        except yaml.YAMLError:
            continue
        inline = [a for a in (data.get("inline") or []) if isinstance(a, dict)]
        workbook = [a for a in (data.get("workbook") or []) if isinstance(a, dict)]

        kept_inline = 0
        for a in inline:
            t = a.get("type", "")
            inline_counter[t] += 1
            # Simulate repair: WORKBOOK_ONLY moves to workbook, else check allowlist
            if t in WORKBOOK_ONLY_TYPES:
                if t in wb_allowed:
                    pass  # would be moved, still kept
                else:
                    drops_wb[t] += 1
            elif t not in inline_allowed:
                drops_inline[t] += 1
            else:
                kept_inline += 1

        kept_wb = 0
        for a in workbook:
            t = a.get("type", "")
            wb_counter[t] += 1
            if t in INLINE_ONLY_TYPES:
                if t in inline_allowed:
                    pass
                else:
                    drops_inline[t] += 1
            elif t not in wb_allowed:
                drops_wb[t] += 1
            else:
                kept_wb += 1

        if kept_inline < imin or kept_wb < wmin:
            under_min.append((f.stem, kept_inline, kept_wb))

    print(f"\n[{level}] {len(files)} modules")
    print(f"  inline types in use:   {dict(inline_counter)}")
    print(f"  workbook types in use: {dict(wb_counter)}")
    if drops_inline:
        print(f"  WOULD DROP inline:   {dict(drops_inline)}")
    if drops_wb:
        print(f"  WOULD DROP workbook: {dict(drops_wb)}")
    if under_min:
        print(f"  WOULD FALL BELOW MIN ({imin}i + {wmin}w):")
        for slug, i, w in under_min:
            print(f"    {slug}: {i} inline, {w} workbook")

for lvl in ["a1", "a2", "b1-core", "b2", "c1-core", "c2",
            "hist", "bio", "istorio", "lit", "b2-pro", "c1-pro",
            "oes", "ruth"]:
    survey(lvl)
```

A clean run prints zero `WOULD DROP` lines. If any appear, decide case-by-case: drop is intentional (content is stale under the new rules → regen those modules) or unintentional (config is too strict → relax).

---

## 6. History

- **2026-04-10 (issue [#1185](https://github.com/anthropics/learn-ukrainian/issues/1185))** — One-shot comprehensive tuning of `ACTIVITY_CONFIGS` for all 14 levels. Adversarial review by Gemini (`gemini-3.1-pro-preview`) found 7 fixable issues plus a schema gap (dictation). All 7 fixes applied; dictation tracked separately as a schema ticket.
