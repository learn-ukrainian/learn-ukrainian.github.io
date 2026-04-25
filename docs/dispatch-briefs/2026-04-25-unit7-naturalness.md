# Unit 7 — Writer-prompt naturalness rules (#1550)

You are Codex. Your job is to harden the writer prompt
(`scripts/build/phases/v6-write.md`) against three concrete naturalness
failures observed in Unit 6 Phase B v2 (gpt-5.5 writer / Claude reviewer)
on a1/1.

## Why this exists

Phase B v2 produced 8/9 dim scores ≥ 8 — but **Naturalness scored 6.0**
(REVISE), and the MIN-gate failed the build. Claude reviewer cited three
specific writer-side patterns the current `v6-write.md` does NOT explicitly
forbid. Without explicit forbids, the same patterns recur on every Phase B
run.

The verbatim Phase B evidence is in `evidence/unit6-phaseB/review-r1.md`
(merged via PR #1568, on origin/main as of today). **Read that file FIRST
to see the exact quotes and reviewer prose.** Use those quotes verbatim in
your edits — they are evidence, not paraphrasing material.

The three patterns:

1. **`Українською:` meta-frame with inline word-gloss-word-gloss substitution.**
   Example from Phase B prose: `Українською: «голосні» (vowels) вимовляються
   (are pronounced) без (without) перешкоди`. Reviewer: "Robotic word-by-word
   substitution under a meta-frame — reads like a glossary, not a teacher."
2. **Mixed-language clauses (matrix-language switches mid-clause).**
   Example A: `На відміну від English, keep the answer simple at first…`
   Example B: `In англійській (English), learners may miss this contrast at
   first, so listen for it завжди (always).`
   Reviewer: "Жоден український вчитель так не пише."
3. **Forced lexical insertions to satisfy required-vocab obligation.**
   Example: `this is the basic «відповідь» (answer) to "what kind of sound
   is it?"`. Reviewer: "Token-drop, not a teaching move. Слово не несе тут
   ваги, лише дзвенить як обов'язковий пункт."

## Worktree instructions (mandatory)

Work in a git worktree at `.worktrees/dispatch/codex/codex-1550-unit7-naturalness`.
Do NOT branch in the main checkout. Concrete setup:

```bash
git fetch origin main
git worktree add -b codex/1550-unit7-naturalness \
    .worktrees/dispatch/codex/codex-1550-unit7-naturalness origin/main
cd .worktrees/dispatch/codex/codex-1550-unit7-naturalness
# Verify the base is fresh:
git log --oneline HEAD..origin/main   # MUST be empty before you proceed
```

If `HEAD..origin/main` is non-empty, rebase before doing any work.

## File-level work (numbered, non-optional steps)

### Step 1. Read the source-of-truth evidence

Read `evidence/unit6-phaseB/review-r1.md` (now on main). Pay particular
attention to `[NATURALNESS] [SEVERITY: major]` and `[SEVERITY: minor]`
findings — three majors, one minor — and the corresponding `<fixes>` block
at the bottom (find/replace pairs already authored by the reviewer).

### Step 2. Edit `scripts/build/phases/v6-write.md`

#### 2a. Bump the version comment at line 1

Replace the existing `<!-- version: 2.4.0 ...` HTML comment with `2.5.0`,
today's date, and a one-line summary:
> "naturalness register hardening — bans `Українською:` meta-frame,
> mixed-language clauses, and required-vocab token-drops (Phase B v2
> finding, EPIC #1550 U7)"

#### 2b. Insert a new `### Natural Prose Register (anti-patterns)` subsection

Place it inside `## Content Rules`, **AFTER** `### Pedagogy` and
**BEFORE** `### Ukrainian Language Quality`. (The current file has these
two as adjacent sub-subsections — your insertion goes between them.)

Structure of the new subsection:

```markdown
### Natural Prose Register (anti-patterns)

Pick ONE matrix language per clause. Bolded Ukrainian terms with
parenthetical English glosses are the immersion mechanism — robotic
substitution patterns and meta-frames break the teacher voice and tank
the Naturalness review dim.

The three patterns below are observed-in-the-wild failures from a1/1
Phase B v2 (#1550). Each is a hard ban — the WRONG examples are verbatim
quotes from the failed module's prose; the RIGHT rewrites are the
reviewer's authored fixes.

#### Banned: `Українською:` meta-frame with inline word-gloss substitution

WRONG (verbatim from a1/1 Phase B v2):
> Українською: **«голосні»** (vowels) **вимовляються** (are pronounced)
> **без** (without) перешкоди; this is the main feature of **«голосних»**
> (vowel sounds).

RIGHT:
> **«Голосні»** (vowels) are pronounced without any obstruction in the
> mouth — that free, voiced flow is what makes a sound a vowel.

WHY: The meta-frame plus inline word-by-word substitution reads as a
glossary lookup, not a teacher explaining a concept. The learner notices
it as machine-generated. Bold the ONE Ukrainian term at first use, and
let the English sentence carry the explanation.

#### Banned: mixed-language clauses (matrix-language switches mid-clause)

WRONG-A (verbatim):
> На відміну від English, keep the answer simple at first…

WRONG-B (verbatim):
> In **англійській** (English), learners may miss this contrast at first,
> so listen for it **завжди** (always).

RIGHT-A:
> Unlike English, keep the answer simple at first…

RIGHT-B:
> English speakers often miss this hard–soft contrast at first, so train
> your ear to listen for it on every consonant.

WHY: Жоден український вчитель так не пише. Foreign nouns dropped into a
clause that uses a different matrix language read as forced.
A1/A2 clauses pick ONE matrix language; foreign terms appear ONLY as bold
+ parenthetical gloss, never as raw substitution.

#### Banned: required-vocab token-drops

WRONG (verbatim):
> …**«голосні»** (vowels) and **«приголосні»** (consonants) are the first
> **два** (two) sound groups; this is the basic **«відповідь»** (answer)
> to "what kind of sound is it?"

RIGHT:
> …**«голосні»** (vowels) and **«приголосні»** (consonants) are the first
> two sound groups, and that is the basic answer to "what kind of sound
> is it?"

WHY: `«відповідь»` here carries no teaching weight — it's bolted in to
satisfy the vocabulary list. Required vocabulary serves the teaching, not
a count. If a required term cannot earn its place in a sentence, leave it
for a later section where it can. The Vocabulary checklist is a coverage
target across the WHOLE module; not every sentence is a coverage slot.
```

The body MUST quote the WRONG examples verbatim (do not paraphrase) — they
are evidence the writer is being asked to recognize. The RIGHT rewrites
MUST come from the `<fixes>` block of `evidence/unit6-phaseB/review-r1.md`
(use the `replace:` text, not your own invention).

#### 2c. Add ONE new entry to `### Forbidden Tropes (contract §4 block-list)`

Append to the bullet list under `### Forbidden Tropes` (currently has
The Cheerleader / The Empty Announcer / The Translator / The Wall of Text
/ The Filler):

> - **The Glossarist:** literal word-by-word substitution under a
>   `Українською:` meta-frame, mixed-language clauses (Ukrainian matrix
>   with raw English noun, or English matrix with raw Ukrainian noun
>   outside a bolded gloss), or any forced bolded-Ukrainian token whose
>   only function is to satisfy a required-vocab list. Required vocabulary
>   serves teaching; it does not buy line-level immersion. See `Natural
>   Prose Register` above for examples and rewrites.

### Step 3. Add a regression test

Create `tests/test_v6_write_prompt_naturalness.py` with a single
`@pytest.mark.unit` test that asserts each of the three banned patterns
is mentioned by exact substring in `scripts/build/phases/v6-write.md`. The
test must fail loudly if a future edit silently strips the new subsection.
Use the substrings:

- `"Banned: \`Українською:\` meta-frame"`  (note the backticks)
- `"Banned: mixed-language clauses"`
- `"Banned: required-vocab token-drops"`
- `"The Glossarist:"`

The test's job is to be a cheap canary, not a content review.

### Step 4. Verify

```bash
.venv/bin/ruff check scripts/build/phases/ tests/
.venv/bin/pytest tests/test_v6_write_prompt_naturalness.py -q
```

Both must pass.

### Step 5. Commit + push + PR (EXPLICIT — do not stop after commit)

```bash
git add scripts/build/phases/v6-write.md tests/test_v6_write_prompt_naturalness.py
git commit -m "feat(write): naturalness register hardening — ban meta-frame + splices + token-drops (#1550 U7)"
git push -u origin codex/1550-unit7-naturalness
gh pr create \
  --title "feat(write): naturalness register hardening (#1550 U7)" \
  --body "Closes the writer-side root cause for Phase B v2 Naturalness 6.0. Adds 3 banned patterns + 1 Forbidden Trope entry + regression test. Brief: docs/dispatch-briefs/2026-04-25-unit7-naturalness.md. See evidence/unit6-phaseB/review-r1.md for the source findings. Refs #1550 U7."
```

Do NOT enable auto-merge. Do NOT skip the `gh pr create` step.

## Acceptance criteria

- `scripts/build/phases/v6-write.md` v2.5.0 with the new
  `### Natural Prose Register (anti-patterns)` subsection placed between
  `### Pedagogy` and `### Ukrainian Language Quality`
- ONE new `**The Glossarist:**` entry appended to `### Forbidden Tropes`
- `tests/test_v6_write_prompt_naturalness.py` exists with the four
  substring assertions
- `ruff` clean, `pytest` of the new test passes
- Branch `codex/1550-unit7-naturalness` rebased on `origin/main`
  (verify with `git log --oneline HEAD..origin/main` returning empty)
- PR opened, no auto-merge, body references this brief and the evidence
