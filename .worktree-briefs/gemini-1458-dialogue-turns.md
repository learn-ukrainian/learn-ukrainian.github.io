# Gemini dispatch — #1458 (P3-B) `dialogue_situations[].turns:` convention + a1/colors plan update

## Why you

This is plan-authoring + convention-docs work, which is your lane. You also flagged the *exact* pain point in your 2026-04-23 content-builder diagnostic (bridge msg 428) — "sterile vocabulary lists without connective tissue" + "dialogue situations as English stage directions" were your findings. You're the right author.

Full context:
- `docs/reports/2026-04-23-a1-colors-opus-r1-dim-diagnosis.md` — #1449 diagnostic §3.3 + §5.2 (exact location of the bug, cites plan lines 31-41)
- `docs/epics/2026-04-23-alignment-pipeline-runtime-contracts.md` — EPIC #1451 Phase 3-B
- `docs/reports/2026-04-23-a1-colors-rebuild-plan.md` — Action 2
- `docs/best-practices/dialogue-situations.md` — existing convention doc

## Root cause (one sentence)

`plans/a1/colors.yaml:31-41` uses `dialogue_situations[].setting:` as English stage-direction metadata ("Описати: чорна сукня (f), білий светр (m)…"). The writer renders it as framing narration before the dialogue turns. Dim score: Dialogue & conversation quality 5/10.

## Task

### 1. Update `docs/best-practices/dialogue-situations.md`

Add a new section formally defining `turns:` as a required sibling of `setting:`:

- `setting:` — writer-only metadata (scene description, linguistic focus). **NEVER rendered as prose.**
- `turns:` — required list of speaker turns. Shape: `[{speaker: str, ua: str, en_gloss: str}]`. Render: block-quote Ukrainian + optional parenthetical English gloss only for novel vocabulary, 5-8 turns per dialogue for A1-A2.
- Include 2-3 examples: one A1 market-scene, one A2 cafe-scene, drawn from Ukrainian textbook patterns (Bolshakova Grades 1-2 have the kind of natural dialogues we want).

### 2. Update `curriculum/l2-uk-en/plans/a1/colors.yaml` (lines 31-41 area)

- Back up the current file as `colors.yaml.bak` before editing (non-negotiable rule 7).
- Bump the plan's `version:` field.
- Add `turns:` to BOTH `dialogue_situations` entries.
- Source dialogues from the textbook anchor already in the plan (Bolshakova Grade 2 p.38 flower-market poem + the Дмитро/Ліза outfit dialogue).
- Keep `setting:` but rewrite it as TERSE writer-only metadata (scene + linguistic focus in ≤2 lines, Ukrainian). Add a comment in the YAML: `# writer-only metadata; never rendered`.
- Each `turns:` entry should use forms the A1 learner can parse: simple SVO, concrete color nouns, minimal case variation beyond nominative + accusative.

### 3. Update the dialogue-section render template

The writer prompt template that builds `v6-chunk-XX-prompt.md` for dialogue sections needs a positive render directive. Locate the template (likely in `scripts/build/phases/` — grep for `dialogue_acts` or `Діалоги` section prompt construction). Add a render block that fires when `current_section.dialogue_acts` is non-empty:

```
## Dialogue render format

Render this section as:
- Optional Ukrainian H3 title
- 5–8 speaker turns formatted as block-quotes:
    > **Ім'я:** Ukrainian turn.
- ≤2 sentences of analytical gloss in English pointing at specific forms
- NO narrative framing ("Liza picks a party outfit…")
- NO stage directions in English
- NO inline English translation of every line (use gloss ONLY for novel vocabulary)
```

### 4. Optional — `scripts/audit/checks/dialogue_density.py`

Skip this if code-writing is outside your comfort zone — leave it for Codex as a followup. If you do it: new audit check that computes `non_dialogue_prose_chars / total_section_chars` and FAILs if > 0.30 for any section whose plan has non-empty `dialogue_acts`.

## Ukrainian authenticity bar

The `turns:` content is the learner's FIRST contact with natural Ukrainian dialogue patterns at A1. Do not invent stilted textbook speech. Use:
- Natural greetings (`Привіт`, `Добрий день`)
- Natural back-channel (`Ага`, `О!`, `Так?`)
- Real turn-taking — questions actually answered, not interrogation
- Bolshakova's poem as real textbook source (anchor already in the plan)

Reference `docs/best-practices/dialogue-situations.md` + `memory/textbook-research.md` if they exist.

## Verify

1. `docs/best-practices/dialogue-situations.md` renders cleanly; includes the `turns:` convention + 2-3 examples
2. `plans/a1/colors.yaml` parses as valid YAML; `version:` bumped; `.bak` exists; `turns:` has 5-8 entries per dialogue
3. Render template updated; unit test (if applicable) passes
4. Visual spot-check: the dialogue content in `turns:` reads as natural Ukrainian, not stage direction

## PR

Title: `feat(plan): dialogue_situations[].turns: convention + a1/colors plan update (#1458) (P3-B of #1451)`

Body: reference #1458 + EPIC #1451 + the #1449 diagnostic. Include the new dialogue text excerpted. Do NOT auto-merge.

## Worktree

Create: `git worktree add -b gemini/1458-dialogue-turns .worktrees/gemini-1458-dialogue-turns origin/main`

Work in `.worktrees/gemini-1458-dialogue-turns`. Commit + push + open PR.

## Model + effort

Use `gemini-3.1-pro-preview`. This is non-trivial content work; take your time.

## Out of scope

- `_extract_terms` fix (that's #1457, Codex)
- `compiler._format_sources` (that's #1459, Codex)
- Re-firing the actual colors build — Claude orchestrates after all 3 P3-A/B/C land
