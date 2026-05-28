# 2026-05-27 — V7 writer prompt + reviewer rubric hardening (Codex)

> Dispatch target: `codex --mode danger --worktree`, model `gpt-5.5` (default), effort `xhigh`.
> Base: `origin/main` (currently `89295fac7d`, post PR #2365).
> Tracking: orchestrator-driven post-m20-ship hardening; m20 (PR #2364) shipped 28/28 + 18/18 + 9.3 LLM-QG but the artifact has 6 substantive failure modes the gates missed. Fresh codex thread (no carry from rounds #11-#17).

## Why this exists

m20 (`a1/my-morning`) shipped as PR #2364 (`38f6348cd5`) with every deterministic gate green and LLM-QG scoring 9.3 PASS. **The artifact is still a salad/kaleidoscope** — verified in `curriculum/l2-uk-en/a1/my-morning/module.md`:

1. **Mid-module register shifts** (lines 20, 30-31, 35) — English explanation → Ukrainian metalanguage TO the learner → preachy third-person framing → casual paraphrase. Reads like 4 different writers.
2. **Lines 30-31** — Ukrainian instruction to the A1 learner ("Контролюй чистоту словника", "Рішуче відкидай русизми...так ранкова рутина занурює студента в автентичний простір"). A1 adults can't process Ukrainian metalanguage — it IS what they're learning.
3. **Line 35** — "сніданок is a thing; снідати is an action." Folksy paraphrase instead of grammar terms (noun/verb).
4. **Line 57** — Hallucinated proper noun "Кнак" (should be "Квак" per lines 58-60 "до Квака", "з Кваком"). Blockquote attributed *— Захарійчук, Grade 1, p.24* — not verified at write time.
5. **Line 133** — `Крок 5: Розширення лексичного та синтаксичного контексту.` Writer-side scaffolding (wiki_coverage obligation label) leaked into published body.
6. **Two Grade 1 textbook blockquotes** (Захарійчук p.24, p.52) — children's primary sources in adult A1 content. Out of register.

Root cause is **iterative patching**: 17 rounds across 4 sessions each fixed one thing while leaving others' fingerprints. The prompt allows the salad shape. Fix: hardened prompt with explicit rules + matching reviewer REJECT criteria.

**Out of scope for this dispatch**: m20 stays as-is; the refire under the hardened pipeline (next phase, separate dispatch) is what produces a clean module — NOT a patch to the existing one. Item #4 (verify_quote gate) is a separate dispatch (gemini); do NOT touch that here.

## What to build

### Part A — `scripts/build/phases/linear-write.md`

Add 6 new `#R-` rules. Each must follow the existing `#R-` rule shape (read the file end-to-end first; do NOT duplicate or contradict existing rules — note any near-overlap in PR body).

1. **`#R-SINGLE-VOICE-A1`** — One teacher voice across the whole module: warm, clear, direct ("you" / "your"). No third-person framing of the learner ("the student", "студента", "the reader", "учня"). No mid-paragraph register shifts. The module reads as if ONE knowledgeable teacher is speaking, end to end.

2. **`#R-AUDIENCE-LANGUAGE-A1`** — At A1, explanation prose stays in **English**. Ukrainian appears only as TARGET: inline vocabulary words with English glosses, dialogue boxes, tables, conjugations, model sentences. NEVER use Ukrainian metalanguage TO the learner (no "Контролюй чистоту словника", no "Рішуче відкидай", no "Запам'ятай..."). The learner cannot read Ukrainian explanations yet — that's what they're learning.

3. **`#R-NO-CHILDREN-PRIMARY-QUOTES`** — No `>` blockquotes from textbooks at Grade 1, 2, or 3 levels in the published module body. Grade 1-3 RAG hits can still ground the writer's lexical choices, but do not surface as quoted material. Default: NO blockquote unless it pedagogically advances the lesson AND comes from an adult-appropriate source (Grade 7+, adult literature, Антоненко-Давидович, style guides). Adult A1 learners are not reading children's primers.

4. **`#R-NO-SCAFFOLDING-LEAKS`** — Writer-side scaffolding never appears in module body. Forbidden in published markdown: panel IDs (`P1`, `P2`, ...), Crock-N labels (`Крок 5:`, `Step 5:`), obligation names from the wiki_coverage manifest (`ban-4`, `step-5`, ...), reviewer-fix anchors, phase names, gate names. The module is a finished lesson, not a writer's worksheet.

5. **`#R-GRAMMAR-TERMS-A1`** — Use proper grammatical terminology in English explanations: **noun**, **verb**, **adjective**, **adverb**, **pronoun**, **reflexive**, **conjugation**. Do NOT paraphrase ("a thing", "an action", "a word for", "a doing-word", "the X-form of Y"). At A1, adult learners benefit from real grammar terms because they transfer to every future module and to any other reference they'll consult.

6. **`#R-CLEAN-TABLES`** — Tables: bold ONLY the target Ukrainian forms. Pronoun columns (я / ти / ...), English headers, and English glosses remain in regular weight. Conjugation tables teaching a present-tense paradigm must include the FULL set of person/number rows: **я / ти / він,вона / ми / ви / вони** (six rows). Do not truncate at 4 rows. Vocabulary tables stay two-column unless a third column adds essential teaching value (e.g., stress mark, IPA).

### Part B — `scripts/build/phases/linear-review-dim.md`

Mirror the 6 writer rules as REJECT criteria in the appropriate review dimension(s). Read the file end-to-end first to find existing dims (e.g., `decolonization`, `pedagogy`, `register`, `accuracy` — names may differ). The rules map roughly:

- **Register / voice / audience dim** (or equivalent — add one if absent, named e.g. `register_consistency`):
  - REJECT mid-module register shifts (English ↔ UK metalanguage ↔ preachy imperative ↔ casual paraphrase)
  - REJECT third-person framing of the learner
  - REJECT Ukrainian metalanguage TO the A1 learner
- **Pedagogy / structure dim** (or equivalent):
  - REJECT scaffolding label leaks ("Крок N:", panel IDs, obligation names, gate names)
  - REJECT Grade 1-3 textbook blockquotes in adult A1 content
  - REJECT bold-everywhere tables
  - REJECT conjugation tables missing `ви` or `вони` rows when teaching a full paradigm
- **Grammar terminology dim** (or fold into pedagogy):
  - REJECT folksy paraphrase ("thing", "action") in lieu of grammar terms

### Cross-file consistency (load-bearing)

Writer rules and reviewer rejection criteria MUST use the **same terminology and the same examples**. If `#R-SINGLE-VOICE-A1` says "no third-person 'the student' framing," the reviewer rejection uses the exact same phrase. Reviewer cannot reject for criteria the writer wasn't told to follow, and writer cannot follow criteria the reviewer doesn't check.

## Anti-fabrication contract (#M-4)

| Claim | Required evidence in PR body |
|---|---|
| "Read linear-write.md end-to-end" | `wc -l scripts/build/phases/linear-write.md` raw output + bullet list of existing `#R-` rule names (just names) |
| "Read linear-review-dim.md end-to-end" | `wc -l` raw + bullet list of existing dim names |
| "Read the m20 failure case" | `grep -n "^##\|^>\|<!-- bad\|Крок" curriculum/l2-uk-en/a1/my-morning/module.md` raw output |
| "New rules don't conflict with existing rules" | One-line note per new rule referencing the nearest existing rule and confirming non-overlap (or noting overlap and dropping the new rule) |
| "Cross-file consistency holds" | A `diff`-style table mapping each writer rule to its reviewer rejection criterion, with the shared key phrase quoted from both files |
| "Tests pass" | `.venv/bin/pytest tests/test_writer_prompt_*.py tests/test_reviewer_prompt_*.py -q --no-header` final summary line raw |
| "Lint clean" | `.venv/bin/ruff check scripts/build/phases/ tests/` final line raw |
| "PR opened" | `gh pr view --json url` raw URL line |

## Numbered execution steps

1. **Worktree.** You start inside `.worktrees/dispatch/codex/v7-prompt-hardening-2026-05-27/` (handled by `delegate.py dispatch --worktree`). Verify with `pwd` and `git branch --show-current`.

2. **Read `scripts/build/phases/linear-write.md`** end-to-end (510 lines). List existing `#R-` rule names in your notes.

3. **Read `scripts/build/phases/linear-review-dim.md`** end-to-end (318 lines). List existing dim names.

4. **Read `curriculum/l2-uk-en/a1/my-morning/module.md`** (the shipped failure case). Verify the 6 failure-mode line refs above match what you see.

5. **Draft Part A** — the 6 new `#R-` rules in `linear-write.md`. Slot them under the "Tone and immersion (mandatory)" section (~line 282) or wherever the existing `#R-` rules cluster. Keep each rule self-contained (~3-6 lines, in the existing rule shape — directive + brief rationale + one positive/negative example).

6. **Draft Part B** — the mirroring REJECT criteria in `linear-review-dim.md`. Use the SAME terminology and SAME examples as Part A. If the existing dim list lacks a home, add or extend the appropriate dim (don't invent a parallel taxonomy).

7. **Tests.** If `tests/test_writer_prompt_*.py` or `tests/test_reviewer_prompt_*.py` exist with invariants on rule count or rule names, update them (don't delete invariants). Add at least one test per new rule covering "rule text is present in the prompt and matches the expected anchor." Run `.venv/bin/pytest tests/ -q --no-header` and capture the final summary line.

8. **Ruff.** Run `.venv/bin/ruff check scripts/build/phases/ tests/`. Capture final line.

9. **Commit conventional.** Single commit:
   ```
   feat(v7-prompt): writer + reviewer rules for single-voice A1 lesson register

   Adds 6 #R- rules to linear-write.md and matching REJECT criteria
   to linear-review-dim.md. Closes the salad/kaleidoscope failure
   mode identified in m20 (PR #2364) post-ship review.

   Rules added (writer):
   - #R-SINGLE-VOICE-A1
   - #R-AUDIENCE-LANGUAGE-A1
   - #R-NO-CHILDREN-PRIMARY-QUOTES
   - #R-NO-SCAFFOLDING-LEAKS
   - #R-GRAMMAR-TERMS-A1
   - #R-CLEAN-TABLES

   Reviewer rejection criteria mirror writer rules 1:1.

   X-Agent: codex/v7-prompt-hardening-2026-05-27
   ```

10. **Push + PR.** `git push -u origin codex/v7-prompt-hardening-2026-05-27` then `gh pr create` with title `feat(v7-prompt): writer + reviewer hardening for single-voice A1 register`. PR body must include: (a) the 6 rules with m20 line-ref justifications, (b) the cross-file consistency mapping table, (c) raw test + lint outputs.

11. **DO NOT auto-merge.** Orchestrator review required.

## Scope guardrails

- **DO NOT** modify `scripts/build/linear_pipeline.py` — that's the parallel gemini dispatch (verify_quote gate + prev/next link safety).
- **DO NOT** touch `curriculum/l2-uk-en/a1/my-morning/` — m20 stays as-is.
- **DO NOT** add more rules than the 6 listed. If you spot other prompt issues during the read, file them as follow-up via `gh issue create`; don't expand scope.
- **DO NOT** skip the cross-file consistency check.

## On unexpected blockers

- If tests fail in ways that look like existing flakes or branch state, run the same test ONCE on main first to baseline. Report both raw outputs.
- If one of the 6 rules duplicates an existing rule, do NOT add it twice. Note in PR body which rule it duplicates and why we don't need the new one.
- If the reviewer prompt has no obvious dim home for some criteria, add a new dim per the existing dim shape; don't force-fit.
- If you discover a 7th systemic failure mode while reading the m20 artifact, file it as a follow-up issue and STOP at the 6 listed rules — don't expand.
