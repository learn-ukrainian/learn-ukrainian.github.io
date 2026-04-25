# Unit 8 — Activity-prompt example de-poisoning (#1550)

You are Codex. Your job is to harden `scripts/build/phases/v6-activities.md`
against example-poisoning, where the model copies concrete Ukrainian words
from the prompt's format examples into the actual activity output.

## Why this exists

Phase B v3 of a1/1 (gpt-5.5 writer, post-Unit-7) hit terminal
`plan_revision_request` because the activity-pre-validation gate caught:

```
nf_76376c179ea15428 (exercise_quality, critical):
  activity grounding failed before review:
  answer word(s) not grounded in prose or plan vocabulary: кіт, гора
```

The activity prompt has a `<strict-grounding>` block (lines 107–113) and a
`<required-vocab-coverage>` block (lines 99–105). Both rules ARE present.
The model violates them anyway because the prompt's own format examples
seed concrete Ukrainian words the model copies. The pre-validation gate
fires, the regenerator runs, the model copies the same words again
(because the example is unchanged), `top3_overlap` and
`content_hash_repeat` stall signals fire after 3 attempts, and the build
hits terminal.

**Smoking gun (line 257):**
```
- **odd-one-out**: ... Example: words: ["кіт", "пес", "молоко"], correct: 2,
  explanation: "молоко — 3 syllables, rest have 1"
```

The a1/1 module's prose contains zero of those three words. The activity
model emits `кіт` anyway. Pre-validation rejects it. Regenerator emits
`кіт` again next attempt. Terminal.

Other lines with the same poisoning risk (audit found at least these):
- L184: `items: ["книга", "ручка", "школа"]`
- L186: `items: ["вікно", "море", "молоко"]`
- L194: `explanation: "Книга закінчується на -а, отже жіночий рід."`
- L223–225: `["швидку!", "Викличте"]`, `["потрібен", "Мені", "лікар."]`
- L254: `word: "молоко", answer: "мо-ло-ко"`
- L255: `word: "яблуко", correct: 3`
- L256: `syllables: ["ка", "май", "ре"]`
- L257: `["кіт", "пес", "молоко"]`

## Worktree instructions (mandatory)

```bash
git fetch origin main
git worktree add -b codex/1550-unit8-activity-depoisoning \
    .worktrees/dispatch/codex/codex-1550-unit8-activity-depoisoning origin/main
cd .worktrees/dispatch/codex/codex-1550-unit8-activity-depoisoning
git log --oneline HEAD..origin/main   # MUST be empty before you proceed
```

## File-level work (numbered, non-optional steps)

### Step 1. Bump the version comment

`scripts/build/phases/v6-activities.md` — top-of-file HTML comment. If a
version comment exists, bump the patch/minor and add today's date with a
one-line summary: "example de-poisoning — concrete Ukrainian words in
format examples replaced with abstract placeholders to stop the model from
copying them into output (#1550 U8)". If no version comment exists at the
top, add one in the same shape as `scripts/build/phases/v6-write.md` line
1 (HTML comment with `version`, `updated`, summary).

### Step 2. Replace concrete Ukrainian-word examples with placeholders

For EVERY format example in the prompt that contains concrete Ukrainian
content words, replace the Ukrainian words with the placeholders
`<UKR_1>`, `<UKR_2>`, `<UKR_3>` (numbered if multiple words appear in the
same example). Keep the example's structure, types, and English glosses
intact — only the Ukrainian content words change.

Concrete instructions:
- **Ukrainian content words** (nouns, verbs, adjectives, full
  sentences in Ukrainian) → replace with `<UKR_1>`, `<UKR_2>`, …
- **Ukrainian function words inside grammar metalanguage** (case names
  like `називний`, paradigm labels, register labels like `розмовне`) →
  KEEP. Those are referring to grammar concepts, not lexical content.
- **Standalone Ukrainian letters** (like `Я`, `Ь`, `й`) inside a
  phonetic/orthographic explanation → KEEP. They are the topic, not
  lexical examples.
- **English glosses** → KEEP, but make the gloss literal-placeholder too,
  e.g. `<UKR_1> (placeholder noun A)` rather than a real English word.

Example transformations (for guidance):

```
BEFORE:  word: "молоко", answer: "мо-ло-ко"
AFTER:   word: "<UKR_1>", answer: "<syl-1>-<syl-2>-<syl-3>"

BEFORE:  words: ["кіт", "пес", "молоко"], correct: 2, explanation: "молоко — 3 syllables, rest have 1"
AFTER:   words: ["<UKR_1>", "<UKR_2>", "<UKR_3>"], correct: 2, explanation: "<UKR_3> — 3 syllables, rest have 1"

BEFORE:  syllables: ["ка", "май", "ре"], correctIndices: [1], category: "закриті"
AFTER:   syllables: ["<SYL_1>", "<SYL_2>", "<SYL_3>"], correctIndices: [1], category: "закриті"

BEFORE:  explanation: "Книга закінчується на -а, отже жіночий рід."
AFTER:   explanation: "<UKR_1> закінчується на <suffix>, отже жіночий рід."
```

The category labels (`закриті`, `жіночий рід`, `називний`) are grammar
metalanguage — keep them.

Keep ALL English-language explanatory prose, English glosses-as-format,
and English schema-talk verbatim.

### Step 3. Add an explicit anti-poisoning meta-rule

Insert a new block at the very top of the `<strict-grounding>` block
(lines 107–113), BEFORE the existing strict-grounding rule. Use this
exact text:

```markdown
<no-example-words>
The format examples in THIS prompt use placeholder tokens like `<UKR_1>`
because the activity validator REJECTS any Ukrainian word in your output
that does not appear in the prose or in `PLAN_VOCABULARY`. NEVER copy a
Ukrainian word from this prompt's format examples into your activity
items. The placeholders mark the SHAPE of the data; the words you put
there must come from the module's prose or the plan's vocabulary list,
not from this prompt.

If a placeholder cannot be filled with a prose-grounded or
plan-vocabulary-grounded word for a given activity type at this level,
DROP the activity and pick a different type from the allowed list. Do
not fall back to "common A1 words" the model knows — those are exactly
the words the validator will reject.
</no-example-words>
```

### Step 4. Add a regression test

Create `tests/test_v6_activities_prompt_depoisoned.py` with a single
`@pytest.mark.unit` test asserting:

1. The text `<no-example-words>` appears in
   `scripts/build/phases/v6-activities.md`.
2. The text `<UKR_1>` appears at least once.
3. The literal substrings `"кіт"`, `"пес"`, `"молоко"`, `"книга"`,
   `"яблуко"` (each as a quoted string with the surrounding double
   quotes) DO NOT appear anywhere in the file.

The test's job is to be a tight canary against the same regression. Use
`pathlib.Path` with the relative path `scripts/build/phases/v6-activities.md`,
matching the convention in `tests/test_v6_write_prompt_naturalness.py`.

### Step 5. Verify

```bash
.venv/bin/ruff check scripts/build/phases/ tests/
.venv/bin/pytest tests/test_v6_activities_prompt_depoisoned.py -q
```

Both must pass.

### Step 6. Commit + push + PR (EXPLICIT)

```bash
git add scripts/build/phases/v6-activities.md \
        tests/test_v6_activities_prompt_depoisoned.py
git commit -m "feat(activities): de-poison format examples — placeholders + anti-poisoning rule (#1550 U8)"
git push -u origin codex/1550-unit8-activity-depoisoning
gh pr create \
  --title "feat(activities): de-poison format examples (#1550 U8)" \
  --body "Closes the activity-grounding terminal that hit Phase B v3 of a1/1. Replaces all concrete Ukrainian-word examples in v6-activities.md with abstract placeholders; adds <no-example-words> anti-poisoning rule; regression test. Brief: docs/dispatch-briefs/2026-04-25-unit8-activity-depoisoning.md. Refs #1550 U8."
```

Do NOT enable auto-merge.

## Acceptance criteria

- `scripts/build/phases/v6-activities.md` — every concrete Ukrainian
  content word in a format example replaced with a `<UKR_N>` /
  `<SYL_N>` / `<suffix>` placeholder
- `<no-example-words>` block inserted before `<strict-grounding>`
- New regression test exists and passes
- ruff clean
- PR opened, no auto-merge
- Branch fresh on `origin/main`
