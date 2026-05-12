# Codex dispatch brief — Tab 3 activity dedupe + vocab/flashcard order swap

> **Issue:** file 1 after PR opens (combined for both bugs)
> **Mode:** danger
> **Worktree:** `.worktrees/dispatch/codex/assembler-tab3-dedupe-2026-05-14/`
> **Base:** `origin/main` (currently `1bc5320472`)
> **Hard timeout:** 3600s
> **Silence timeout:** 1200s
> **Effort:** high

---

## ⚠️ CRITICAL — fresh-shell behavior

Each bash block runs in a FRESH SHELL. Prefix every command with `cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/assembler-tab3-dedupe-2026-05-14 && ...` or absolute path.

Use `/Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/python`.

---

## Goal

Two small assembler bugs surfaced after #1930 (V7 MDX assembler alignment) shipped and the user inspected the rendered `a1/my-morning` page:

1. **Tab 3 (Activities) duplicates Tab 1 (Lesson) inline activities.** `module.md` has 7 `<!-- INJECT_ACTIVITY: act-X -->` markers that substitute activities into Tab 1's prose. Tab 3 then renders ALL 10 activities, including the 7 already shown inline. Tab 3 should show only the activities NOT injected in Tab 1 — the "workbook" subset — so the user doesn't see the same exercise twice on the same page.

2. **Vocab tab has FlashcardDeck above VocabCard.** Per user feedback the order should be reversed: `<VocabCard>` (browsable reference) on top, `<FlashcardDeck>` (flip-card practice) on the bottom. The #1930 brief specced the wrong order. One-line fix.

After this PR merges, re-running `assemble_mdx` on `a1/my-morning` should produce:
- Tab 1: 7 inline activity components (unchanged)
- Tab 3: 3 activity components (act-2, act-4, act-9 — the IDs NOT in any INJECT_ACTIVITY marker)
- Tab 2: `<VocabCard>` first, `<FlashcardDeck>` second

---

## #M-4 preamble — verifiable claims this work will produce

| Claim | Deterministic tool | Output format |
|---|---|---|
| "Tab 3 has 3 (not 10) activity components" | `grep -cE '<(Quiz\|FillIn\|MatchUp\|TrueFalse\|GroupSort\|Unjumble\|Observe\|Order)' <Tab3 slice of regenerated MDX>` | quote count (must be 3) |
| "Tab 3 excludes inline-injected IDs" | the assembler returns activities — assert none of {act-1, act-3, act-5, act-6, act-7, act-8, act-10} appear in Tab 3 IDs | quote test assertion |
| "Vocab tab: VocabCard above FlashcardDeck" | `awk '/<TabItem label="Vocabulary"/,/<\/TabItem>/' regenerated.mdx \| grep -nE '<(VocabCard\|FlashcardDeck)'` | quote line numbers showing VocabCard first |
| "Tests pass" | `pytest tests/test_generate_mdx*.py tests/test_assemble_mdx*.py -x` | quote summary |
| "Lint clean" | `ruff check scripts/generate_mdx` | quote final line |

Inline "I checked X" claims without quoted raw output = hallucination per #M-4.

---

## Bug 1 — Tab 3 duplicates Tab 1 inline activities

**Evidence:** `curriculum/l2-uk-en/a1/my-morning/module.md` contains:

```
<!-- INJECT_ACTIVITY: act-3 -->
<!-- INJECT_ACTIVITY: act-1 -->
<!-- INJECT_ACTIVITY: act-5 -->
<!-- INJECT_ACTIVITY: act-7 -->
<!-- INJECT_ACTIVITY: act-6 -->
<!-- INJECT_ACTIVITY: act-8 -->
<!-- INJECT_ACTIVITY: act-10 -->
```

`activities.yaml` has 10 activities: act-1 through act-10.

Currently `scripts/generate_mdx/core.py` substitutes all 7 INJECT markers in the lesson body (Tab 1) AND passes the full 10-activity list to `yaml_activities_to_jsx()` for Tab 3. The user sees acts 1, 3, 5, 6, 7, 8, 10 in BOTH places.

**Fix:** in `core.py`, the INJECT_ACTIVITY substituter (added in #1930) must record which IDs it injected. Pass the COMPLEMENT (activities NOT injected) to `yaml_activities_to_jsx()` for Tab 3. Pseudo:

```python
# Around the INJECT_ACTIVITY substitution call:
injected_ids = set(...substituted markers...)
tab3_activities = [a for a in yaml_activities if a.id not in injected_ids]
activities_content = yaml_activities_to_jsx(tab3_activities, is_ukrainian_forced)
```

**Edge case:** if ALL activities are injected inline (e.g., a small module with 3 activities and 3 INJECT markers), Tab 3 should fall back to a friendly "No workbook activities — see Lesson tab" message (or the existing "No activities for this module" placeholder, English/Ukrainian per `is_ukrainian_forced`).

**Test:** new fixture in `tests/test_generate_mdx_v7_resources_vocab.py` (or sibling) with a module.md containing 2 INJECT markers + 5-activity yaml → assert Tab 1 has 2 activity JSX blocks and Tab 3 has 3 activity JSX blocks (the other 3) AND none of the Tab 1 IDs appear in Tab 3.

---

## Bug 2 — Vocab/FlashcardDeck order swap

**Evidence:** current regenerated `starlight/src/content/docs/a1/my-morning.mdx` shows:

```
<TabItem label="Vocabulary">
<FlashcardDeck client:only="react" cards={...} />
<VocabCard client:only="react" words={...} title="Vocabulary" />
</TabItem>
```

**Fix:** in `scripts/generate_mdx/resources.py` (the function added in #1930 that emits both components — likely `vocab_items_to_components()` or similar), swap the emission order: `<VocabCard>` first, `<FlashcardDeck>` second.

**Test:** existing vocab test fixture — assert the rendered output has `<VocabCard` appearing before `<FlashcardDeck` (string index).

---

## Numbered steps (mandatory checklist)

1. **Worktree setup:**
   ```bash
   cd /Users/krisztiankoos/projects/learn-ukrainian && \
   git worktree add -b codex/assembler-tab3-dedupe-2026-05-14 .worktrees/dispatch/codex/assembler-tab3-dedupe-2026-05-14 origin/main
   ```
2. **Bug 1:** Find the INJECT_ACTIVITY substituter in `scripts/generate_mdx/core.py` (the one added in #1930). Modify it to record `injected_ids`. Filter `yaml_activities` for Tab 3 by `id not in injected_ids`.
3. **Bug 2:** Find the vocab-tab-2 renderer in `scripts/generate_mdx/resources.py`. Swap `<FlashcardDeck>` and `<VocabCard>` emission order.
4. **Tests:** new + existing tests cover both fixes. Run:
   ```bash
   cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/assembler-tab3-dedupe-2026-05-14 && \
   /Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/pytest tests/test_generate_mdx*.py tests/test_assemble_mdx*.py -x
   ```
   Quote final summary.
5. **Ruff:**
   ```bash
   /Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/ruff check scripts/generate_mdx
   ```
6. **End-to-end repro:**
   ```bash
   /Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/python -c "
   from pathlib import Path
   from scripts.build.linear_pipeline import assemble_mdx
   mdx = assemble_mdx(
       Path('curriculum/l2-uk-en/a1/my-morning'),
       Path('/tmp/test-tab3-dedupe.mdx'),
       Path('curriculum/l2-uk-en/plans/a1/my-morning.yaml'),
   )
   print(f'wrote {len(mdx)} chars')
   "
   ```
   Then quote:
   - Tab 1 activity-component count (must be ≥7)
   - Tab 3 activity-component count (must be 3 — act-2, act-4, act-9)
   - First component in Tab 2 (must be VocabCard, not FlashcardDeck)
7. **File issue** describing both bugs + linking this PR.
8. **Commit** — conventional: `fix(generate_mdx): dedupe Tab3 inline-injected activities + swap Vocab/Flashcard order`. Reference `Closes #<issue>`.
9. **Push + PR.**
10. **DO NOT auto-merge.**

---

## What blocks the merge

- Tab 3 still contains injected activity IDs.
- Vocab tab still has FlashcardDeck before VocabCard.
- Tests failing.
- Ruff failing.
- Regression on the existing 5 PRs that just merged (#1925, #1926, #1927, #1928, #1930) — run their related tests too.

---

## Pre-submit checklist

- [ ] `.python-version` unchanged (`3.12.8`)
- [ ] `.yamllint` / `.markdownlint.json` unchanged
- [ ] No generated artifacts in diff
- [ ] No `sys.executable` — use `.venv/bin/python`
- [ ] No `@pytest.mark.skip` with empty `pass`
- [ ] Every changed file directly related to these two bugs
- [ ] Total files changed < 8

---

## Related

- Predecessor PR: #1930 (V7 MDX assembler alignment — this PR fixes 2 follow-up bugs)
- Bug c (resources: YouTube/blog missing) — tracked separately, NOT in scope of this PR
- Live broken MDX: `starlight/src/content/docs/a1/my-morning.mdx`
- Source artifacts at `curriculum/l2-uk-en/a1/my-morning/` (read-only references)
