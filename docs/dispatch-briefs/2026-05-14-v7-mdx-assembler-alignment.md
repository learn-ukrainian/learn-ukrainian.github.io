# Codex dispatch brief — V7 MDX assembler alignment (a1/my-morning rendering)

> **Issue:** none yet — file 1 after PR opens
> **Mode:** danger
> **Worktree:** `.worktrees/dispatch/codex/v7-mdx-assembler-alignment-2026-05-14/`
> **Base:** `origin/main` (currently `ac90fc2f16`)
> **Hard timeout:** 7200s
> **Silence timeout:** 1800s
> **Effort:** high

---

## ⚠️ CRITICAL — fresh-shell behavior

Each bash block runs in a FRESH SHELL. CWD does NOT persist across blocks. Prefix every command with `cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/v7-mdx-assembler-alignment-2026-05-14 && ...` or absolute path.

Inside the worktree, `.venv/` is gitignored. Use `/Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/python`.

---

## Goal

The V7 writer produces 4 separate source artifacts (`module.md`, `activities.yaml`, `vocabulary.yaml`, `resources.yaml`) per `docs/lesson-contract.md` §1. The current MDX assembler at `scripts/generate_mdx/` is v6-aligned and DIVERGES from V7 source format. The live `a1/my-morning` page has 6 visible bugs that all trace to this drift. **Fix them in one focused PR so the page matches `docs/poc/poc-lesson-design.html`.**

The design authority is, in this order of precedence:
1. `docs/lesson-contract.md` — structural (4-tab, source artifacts, transforms)
2. `docs/poc/poc-lesson-design.html` — visual reference for each component
3. `docs/lesson-schema-design.md` + `docs/lesson-schema.yaml` — component prop schemas

---

## #M-4 preamble — verifiable claims this work will produce

| Claim | Deterministic tool | Output format |
|---|---|---|
| "assemble_mdx no longer crashes on V7 a1/my-morning sources" | run `python -c "from scripts.build.linear_pipeline import assemble_mdx; assemble_mdx(...)"` against `curriculum/l2-uk-en/a1/my-morning/` | quote stdout (must end with success message, no traceback) |
| "Generated MDX contains DialogueBox" | `grep -c '<DialogueBox' /tmp/test-my-morning.mdx` | quote count (must be ≥ 1) |
| "Tab 2 has flashcards" | `grep -cE '<(FlashcardDeck|VocabCard)' /tmp/test-my-morning.mdx` | quote count (must be ≥ 1) |
| "Tab 3 has activity components" | `grep -cE '<(Quiz\|FillIn\|MatchUp\|TrueFalse\|GroupSort\|Unjumble\|Observe\|Order)' /tmp/test-my-morning.mdx` | quote count (must be ≥ 4 — matches `assemble_mdx` parsing 4+ activities from the YAML) |
| "Tab 4 has real author attribution, not Unknown" | `grep -c 'by Unknown' /tmp/test-my-morning.mdx` AND `grep -c 'Караман\|Кравцова\|Захарійчук' /tmp/test-my-morning.mdx` | quote both counts (Unknown count = 0; named authors ≥ 1) |
| "Activity parser handles all _ACTIVITY_AUTHORING_FIELDS types" | `python -c "from scripts.yaml_activities import ActivityParser; ..."` parses a fixture with one of each type | quote test pass summary |
| "Tests pass" | `pytest tests/test_generate_mdx*.py tests/test_yaml_activities*.py tests/test_assemble_mdx*.py -x` | quote summary line |
| "Lint clean" | `ruff check scripts/generate_mdx scripts/yaml_activities.py` | quote summary line |

Inline "I checked X" claims without quoted raw output = hallucination per #M-4. Quote everything.

---

## The 6 bugs to fix (in this order — earlier bugs are blockers for later ones)

### Bug 1 (BLOCKER) — ActivityParser raises on `observe`

**Evidence:**
```bash
$ .venv/bin/python -c "from scripts.yaml_activities import ActivityParser; ActivityParser().parse('curriculum/l2-uk-en/a1/my-morning/activities.yaml')"
ValueError: Failed to parse activity 2 id='act-3' type='observe': unknown activity type 'observe'
```

**Root cause:** `_ACTIVITY_AUTHORING_FIELDS` map in `scripts/build/linear_pipeline.py:~3683` declares 8 activity types as **authoring-valid** but `ActivityParser` in `scripts/yaml_activities.py` has NO `_parse_*` method for them:

| Type | Authoring fields | React component (already exists in `starlight/src/components/`) |
|---|---|---|
| `observe` | `examples`, `prompt` | `Observe.tsx` |
| `order` | `items`, `correct_order` | `Order.tsx` |
| `count-syllables` | `items`, `maxCount` | `CountSyllables.tsx` |
| `divide-words` | `items` | `DivideWords.tsx` |
| `highlight-morphemes` | `(implicit)` | `HighlightMorphemes.tsx` |
| `letter-grid` | `letters` | `LetterGrid.tsx` |
| `odd-one-out` | `items` | `OddOneOut.tsx` |
| `pick-syllables` | `syllables`, `category`, `correctIndices`, `explanation` | `PickSyllables.tsx` |

Pre-#1926, these were silently dropped at parse time. Post-#1926 (loud-raise — kept), the whole assembly halts before Tab 3 renders.

**Fix:** add `_parse_observe`, `_parse_order`, `_parse_count_syllables`, `_parse_divide_words`, `_parse_highlight_morphemes`, `_parse_letter_grid`, `_parse_odd_one_out`, `_parse_pick_syllables`. Each should:

1. Validate the type-specific authoring fields per the table above.
2. Construct the corresponding `<ActivityType>Activity` dataclass (some may already exist in `scripts/generate_mdx/dataclasses_.py` — check and reuse; create them if absent, matching the React component's prop interface from the `.tsx` file).
3. Have a corresponding `_<type>_to_mdx` method in the parser that emits the JSX snippet matching the React component's prop names (verify component prop names by reading the `.tsx` interface).

**Test:** create `tests/test_yaml_activities_v7_types.py` with a fixture per missing type that round-trips through `ActivityParser().parse() + _to_mdx()`.

### Bug 2 — `process_dialogues` doesn't match V7 dialogue format

**Evidence:** `curriculum/l2-uk-en/a1/my-morning/module.md` has 14 dialogue lines like:

```markdown
> **Ліна:** Коли ти прокидаєшся?
> **Настя:** Я прокидаюся о сьомій.
```

The current `scripts/generate_mdx/converters.py:process_dialogues()` regex requires an **em-dash prefix** (`> — **Speaker:** ...`), which v6 had but V7 doesn't. So the function produces a no-op pass-through; the live MDX shows raw blockquotes instead of `<DialogueBox>`.

**Fix:** update `process_dialogues()` to detect BOTH formats:
- Legacy v6: `> — **Speaker:** UK *(EN)*` — em-dash and parenthetical English
- V7: `> **Speaker:** UK` — no em-dash, no inline English

When the V7 format is detected, emit:
```jsx
<DialogueBox
  client:only="react"
  title="Діалог 1 — Будній ранок"
  exchanges={[
    { speaker: "Ліна", text: "Коли ти прокидаєшся?" },
    { speaker: "Настя", text: "Я прокидаюся о сьомій." },
    ...
  ]}
/>
```

The `title` should be drawn from the preceding `**Діалог N — ...**` heading line if present (look 1-2 lines back). The `exchanges` JSON literal must use **single-line `JSON.parse('...')`** if it would otherwise break Astro's MDX parser; check the existing `<Unjumble>` pattern in `scripts/yaml_activities.py:_unjumble_to_mdx` for the right shape.

**Test:** new fixture in `tests/test_dialogue_render.py` — given the V7-format dialogue block from `my-morning/module.md`, assert `process_dialogues()` returns a single `<DialogueBox` block with all 9 exchanges and the correct title.

### Bug 3 — Verify INJECT_ACTIVITY substitution order

**Evidence:** `curriculum/l2-uk-en/a1/my-morning/module.md` has 4 `<!-- INJECT_ACTIVITY: id -->` placeholders. The live MDX shows ZERO inline activity components in the Lesson tab.

**Investigation:** read `scripts/generate_mdx/core.py:_apply_shared_transforms()` (~line 314-322). The current order is:
1. `convert_callouts`
2. `resolve_slug_links`
3. `fix_html_for_jsx`
4. `re.sub(r'<!--(.*?)-->', r'{/**/}', ...)` ← strips ALL HTML comments
5. `process_story_sections`
6. `process_dialogues`

Step 4 strips `<!-- INJECT_ACTIVITY: id -->` BEFORE any substitution code can find it. The substitution must run BEFORE step 4, OR step 4 must skip INJECT_ACTIVITY markers.

**Fix:** find where INJECT_ACTIVITY substitution lives (grep `INJECT_ACTIVITY` across `scripts/generate_mdx/`) — if a substituter exists, move it before the comment-strip. If no substituter exists, add one that:
- Locates `<!-- INJECT_ACTIVITY: id -->` markers in the lesson body
- For each marker, finds the matching activity in `yaml_activities` by `id`
- Replaces the marker with the activity's `_to_mdx` output (single rendered component, not a `Tabs` block)

**Test:** module.md fixture with 1 INJECT_ACTIVITY marker + matching activity → assert the marker is replaced by the activity's component JSX in the generated lesson tab.

### Bug 4 — Vocab tab is a markdown table, not flashcards/cards

**Evidence:** live Tab 2 (Vocabulary) renders a 7-column markdown table (`| Word | IPA | English | POS | Gender | Note |`). Per `docs/poc/poc-lesson-design.html` lines 465-528 and `docs/lesson-contract.md` §2, V7 wants the **`<FlashcardDeck>` + `<VocabCard>`** components.

**Component prop signatures (read from `.tsx` files):**

```ts
// FlashcardDeck.tsx
interface FlashcardData {
  front: string;  // Ukrainian
  back: string;   // English
  hint?: string;
}
interface FlashcardDeckProps {
  cards: FlashcardData[];
}

// VocabCard.tsx
interface VocabEntry {
  word: string;        // Ukrainian
  translation: string; // English
  pos?: string;
  gender?: 'm' | 'f' | 'n' | 'pl';
  example?: string;
}
interface VocabCardProps {
  words: VocabEntry[];
  title?: string;
}
```

**V7 vocabulary.yaml entry shape (from `my-morning/vocabulary.yaml`):**

```yaml
- lemma: прокидатися
  translation: to wake up
  pos: verb
  example: Я прокидаюся о сьомій.
```

**Fix:** in `scripts/generate_mdx/resources.py`, REPLACE `vocab_items_to_markdown()` (or add `vocab_items_to_components()` and switch the caller in `core.py`) to emit:

1. A `<FlashcardDeck cards={JSON.parse('[{"front": "прокидатися", "back": "to wake up"}, ...]')}/>` block at the top.
2. A `<VocabCard words={JSON.parse('[{"word": "прокидатися", "translation": "to wake up", "pos": "verb", "example": "Я прокидаюся о сьомій."}, ...]')}/>` block below it.

The two components complement each other: deck = flip-card practice; vocab card = browsable reference. Per the POC design, both should appear on the vocab tab.

**Backwards compatibility:** keep `vocab_items_to_markdown()` available as a fallback for legacy callers (or remove if call-sites are within `scripts/generate_mdx/` only).

**Test:** fixture vocabulary.yaml with 3 entries → assert generated MDX contains `<FlashcardDeck` AND `<VocabCard`, both with the expected JSON payload.

### Bug 5 — Resources tab shows "by Unknown"

**Evidence:** live Tab 4 shows:
```
- Заболотний, 10 клас, с. 78 by Unknown
- Захарійчук, 4 клас, с. 119–120, 162–163 by Unknown
- Караман, 10 клас, с. 176 by Unknown
- Кравцова, 4 клас, с. 113 by Unknown
```

But `curriculum/l2-uk-en/a1/my-morning/resources.yaml` has:
```yaml
- title: Караман Grade 10, p.176
  source_ref: Караман Grade 10, p.176
  author: Караман        ← present!
  pages: "176"
  description: "Reflexive verbs with -ся/-сь as actions directed back to the subject."
  role: textbook
```

So the renderer is falling back to "by Unknown" instead of using `author`. Likely path: `scripts/generate_mdx/resources.py:format_resources_for_mdx()` is reading the wrong key OR the resources dict construction in `scripts/build/linear_pipeline.py:assemble_mdx()` (`resources = {"books": resources_list}`) is wrapping the list in a way the renderer doesn't expect.

**Fix:** trace the resources flow from `resources.yaml` → `assemble_mdx` → `generate_mdx` → `format_resources_for_mdx`. Make sure:
- `author` is propagated (renamed if the renderer wants a different key)
- `pages` is included in the rendered citation
- `description` appears as a sub-line (per POC `source-cite` styling)
- The `role` field decides whether it gets the textbook icon (📚), wiki icon (🔗), audio (🎧), etc.

The final rendered citation should look something like:
```
📚 **Караман — Grade 10, p. 176**
Reflexive verbs with -ся/-сь as actions directed back to the subject.
```

**Test:** fixture resources.yaml with 3 entries (mixed roles) → assert rendered MDX has no "by Unknown" AND contains each author name + role icon.

### Bug 6 — Activities tab populated (cascades from Bug 1)

Once Bug 1 is fixed, `yaml_activities_to_jsx()` will receive a 10-item list and Tab 3 will populate. Verify this is the case (post-fix, Tab 3 should have ≥4 typed components: at least the originally-parseable `fill-in`, `quiz`, `match-up`, `true-false`, `group-sort`, `unjumble`, `order`, `observe`, `fill-in`, `fill-in`).

---

## Numbered steps (mandatory checklist)

1. **Worktree setup:**
   ```bash
   cd /Users/krisztiankoos/projects/learn-ukrainian && \
   git worktree add -b codex/v7-mdx-assembler-alignment-2026-05-14 .worktrees/dispatch/codex/v7-mdx-assembler-alignment-2026-05-14 origin/main
   ```
2. **Read the design docs:** `docs/lesson-contract.md`, `docs/poc/poc-lesson-design.html` (especially lines 80-95 dialogue, 465-528 vocab/flashcard, 110-115 source-box), `docs/lesson-schema-design.md`, `docs/lesson-schema.yaml`. Understand the V7 contract before writing code.
3. **Bug 1: Activity parser methods.** Add the 8 `_parse_*` methods to `ActivityParser`. Each needs a matching `_<type>_to_mdx` for JSX rendering. Verify the React component's prop names from each `.tsx` file before naming the JSX attributes.
4. **Bug 2: process_dialogues V7 format.** Update regex in `scripts/generate_mdx/converters.py`. Handle both v6 (em-dash) and V7 (blockquote-only) formats. Emit `<DialogueBox>` with title + exchanges.
5. **Bug 3: INJECT_ACTIVITY ordering.** Grep `INJECT_ACTIVITY` across `scripts/generate_mdx/`. Either move the existing substituter before the comment-strip, OR add a new substituter. Wire it into the lesson-tab pipeline.
6. **Bug 4: Flashcard + VocabCard rendering.** Replace or augment `vocab_items_to_markdown()` in `scripts/generate_mdx/resources.py`. Emit BOTH `<FlashcardDeck>` and `<VocabCard>`.
7. **Bug 5: Resources author attribution.** Fix `format_resources_for_mdx()`. Use `author`, `pages`, `description`, `role` from V7 `resources.yaml`. No "by Unknown".
8. **Tests:**
   ```bash
   cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/v7-mdx-assembler-alignment-2026-05-14 && \
   /Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/pytest tests/test_generate_mdx*.py tests/test_yaml_activities*.py tests/test_dialogue*.py tests/test_assemble_mdx*.py -x
   ```
   Quote final summary line.
9. **Ruff:**
   ```bash
   /Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/ruff check scripts/generate_mdx scripts/yaml_activities.py scripts/build/linear_pipeline.py
   ```
   Quote final line.
10. **End-to-end repro:**
    ```bash
    cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/v7-mdx-assembler-alignment-2026-05-14 && \
    /Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/python -c "
    from pathlib import Path
    from scripts.build.linear_pipeline import assemble_mdx
    out = Path('/tmp/test-my-morning.mdx')
    plan = Path('curriculum/l2-uk-en/plans/a1/my-morning.yaml')
    mod = Path('curriculum/l2-uk-en/a1/my-morning')
    mdx = assemble_mdx(mod, out, plan)
    print(f'OK wrote {len(mdx)} chars')
    "
    ```
    Then quote:
    - `grep -c '<DialogueBox' /tmp/test-my-morning.mdx` (must be ≥ 1)
    - `grep -cE '<(FlashcardDeck|VocabCard)' /tmp/test-my-morning.mdx` (must be ≥ 1)
    - `grep -cE '<(Quiz\|FillIn\|MatchUp\|TrueFalse\|GroupSort\|Unjumble\|Observe\|Order)' /tmp/test-my-morning.mdx` (must be ≥ 4)
    - `grep -c 'by Unknown' /tmp/test-my-morning.mdx` (must be 0)
    - `grep -c 'Караман\|Кравцова\|Захарійчук' /tmp/test-my-morning.mdx` (must be ≥ 1)
11. **File an issue** retroactively documenting this work — title: "V7 MDX assembler alignment: dialogues, flashcards, resources, parser-types".
12. **Commit** — conventional message: `fix(generate_mdx+yaml_activities): align assembler to V7 source format (dialogues, flashcards, parser types, resources)`. One large commit OK if changes are tightly coupled, OR split per-bug if cleaner.
13. **Push:** `git push -u origin codex/v7-mdx-assembler-alignment-2026-05-14`.
14. **Open PR** via `gh pr create`. Body MUST include:
    - All 5 grep counts from step 10
    - Test/ruff summary lines
    - Before/after MDX excerpts for each tab
    - Reference to design docs (poc-lesson-design.html, lesson-contract.md)
    - `Closes` line for the issue filed in step 11
15. **DO NOT auto-merge.** Hand back for review.

---

## What blocks the merge

- assemble_mdx still crashes on a1/my-morning sources.
- Generated MDX missing ANY of: `<DialogueBox>`, `<FlashcardDeck>`/`<VocabCard>`, populated Tab 3, real author names in Tab 4.
- Any of the 5 grep predicates from step 10 fails.
- Tests failing.
- Ruff failing.
- Behavior change for ALREADY-WORKING modules (e.g. deployed `folk/` modules that the v6 assembler renders fine — run `assemble_mdx` on at least one folk module to confirm no regression).

---

## Reference: V7 my-morning source artifacts

The live `curriculum/l2-uk-en/a1/my-morning/` directory contains the **uncommitted V7 writer output** in the main checkout. Read these files via absolute path (they are read-only references):

- `module.md` — has 14 dialogue blockquote lines + 4 `<!-- INJECT_ACTIVITY: id -->` placeholders
- `activities.yaml` — 10 activities, types: `fill-in`, `quiz`, `observe`, `match-up`, `true-false`, `group-sort`, `unjumble`, `order`, `fill-in`, `fill-in`
- `vocabulary.yaml` — 20 entries, shape: `{lemma, translation, pos, example}`
- `resources.yaml` — 3 entries, shape: `{title, source_ref, author, pages, description, role}`

Plan file: `curriculum/l2-uk-en/plans/a1/my-morning.yaml` (committed, sacred).

---

## Pre-submit checklist (per AGENTS.md:11-26)

- [ ] `.python-version` unchanged (`3.12.8`)
- [ ] `.yamllint` and `.markdownlint.json` unchanged
- [ ] No `status/*.json`, `audit/*-review.md`, or `review/*-review.md` files in diff
- [ ] No `sys.executable` — use `.venv/bin/python`
- [ ] No `@pytest.mark.skip` with empty `pass`
- [ ] No assertions weakened (`is True` → `isinstance(..., bool)`)
- [ ] Every changed file directly related to the V7 assembler alignment
- [ ] Total files changed < 20

---

## Related

- Predecessor handoff: `docs/session-state/2026-05-13-night-wiki-obligations-e2e-brief.md`
- Live broken MDX: `starlight/src/content/docs/a1/my-morning.mdx` (do NOT edit directly; it's an `assemble_mdx` output)
- Design POC: `docs/poc/poc-lesson-design.html`
- Companion in-flight: PR #1928 (writer phonetic IPA — independent file scope)
