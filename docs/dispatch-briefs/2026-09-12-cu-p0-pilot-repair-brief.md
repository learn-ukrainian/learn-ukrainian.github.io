# Repair pass — PR #7991 (a1-v2/things-have-gender pilot) after cross-family content review

You are the writer seat repairing your own pilot. Work ONLY in the existing dispatch worktree branch `agy/cu-p0-pilot-writer-things-have-gender` (the runtime places you there; `pwd` must be under `.worktrees/dispatch/`). Python is `.venv/bin/python` (primary checkout interpreter; set `LEARN_UKRAINIAN_PRIMARY_REPO_ROOT` when an extra search root is required). **Do not touch** `scripts/`, `site/`, `starlight/`, `.github/`, `curriculum/l2-uk-en/plans/`, or the original module under `curriculum/l2-uk-en/a1/things-have-gender/`. Do not edit `audit/curriculum-upgrade/pilot-things-have-gender/verify_pilot.py` or `browser_check.mjs`.

## What happened
The independent Codex review returned REQUEST-CHANGES. Read it in full first:
`batch_state/tasks/cu-p0-pr7991-content-review-codex.result`
The orchestrator has already fixed stress placement (29 forms) and `Стіна́`, and rebuilt the odd-one-out cards; the current head is what you start from (`git log -3`).

Your previous report claimed "every stress verified" and "every lemma verified"; the batch re-check found 29 wrong stresses. This time **every language claim in your report carries the pasted tool output** (`mcp__sources__verify_stress`, `verify_words`, `check_russian_shadow`, `search_ua_gec_errors`, `search_text`). A claim without a receipt counts as unverified.

## Scope rule — inherited vs added
The original module's prose is **locked**: the checker requires every original paragraph verbatim. Review findings that concern the **original** content (the categorical rejection of «моя́ соба́ка»; `act-9`'s English prompts; `act-w2`'s English cues; `act-w3`'s missing context) are **not** fixed by editing them. Record each of them in `NOTES.md` under a new heading `## 6. Plan-level findings (inherited from the original module)` with the reviewer's evidence (e.g. СУМ-11 «ч. і рідше ж.» for соба́ка) and a proposed plan change; the orchestrator routes those to plan review. Everything you **added** is yours to fix.

## Fix list (do all; ranked by learner harm)
1. **`вдо́ма`, `там`, `нова́ су́мка`** and any other word/chunk you introduced in an activity before it is taught: either introduce it in the lesson prose with an em-dash gloss (and add it to that lesson's `vocabulary.yaml` — then the module union grows and you must list the addition in `NOTES.md` for the orchestrator's decision) or replace it with already-taught material. Verify each with `verify_words`.
2. **Ambiguous answer structures**: `act-102` (duplicate matching labels), `act-304` (overlapping groups; label says `-а/-о` but contains `Ілля́`; instruction mentions professions/names yet supplies `соба́ка`), `act-301` (`вчитель/учитель` variant matching without a rule), `act-306` (say the criterion: «за ро́дом»), `act-205` (`нова́ су́мка` chunk). Every item must have exactly one defensible answer; solve each activity yourself and paste the solution set in the report.
3. **A1 sentence length**: true/false and quiz stems at A1 are 4–6 words (`scripts/audit/config.py` A1 `words_min 4 / words_max 6`); `act-203` and `act-303` run 7–10 words — shorten without losing the tested point.
4. **Presentation**: mark every EN→UK `translate` activity as bonus (`bonus: true` plus a title starting «Бо́нус:»); keep recall Ukrainian-only in everything you added; the added summaries and the module closing («Віта́ємо! …») get a side-by-side Ukrainian/English table (any added Ukrainian passage of 3+ sentences), and simplify the dense metalanguage there.
5. **Vocabulary allocation by first use**: `соба́ка` is used in lesson 1 (original prose) but listed in lesson 3; `Мико́ла` is tested in lesson 1 but listed in lesson 3. Re-home entries to the lesson of first use (the union stays 48; each lesson keeps ≥ 12).
6. **Resources**: every entry gets a resolvable locator — `chunk_id` from `mcp__sources__search_text` for textbook pages (paste the search result), or a full URL with access date for external pages; drop what you cannot resolve.
7. **Pedagogical completeness per sitting**: each lesson's opener states 2–3 lesson-specific objectives (Ukrainian first, em-dash gloss), the summary asks for one short independent Ukrainian production (2–3 lines), and lesson 3's self-check covers professions and the exceptions, not only lesson 1–2 material.
8. Dialogues: emit them as `> ` blockquote lines (speaker in bold), not fenced code — the future MDX assembler maps blockquotes to `<DialogueBox>`.

## Language procedure (unchanged, receipts required)
For every word you add or change: `verify_words` on the inflected form; `check_russian_shadow` on the lemma; `search_ua_gec_errors` on new verb/preposition phrases; stress marks on every multi-syllable word — **but do not guess a stress**: call `verify_stress` and paste the result; for a `not_found` form add it to that lesson's `unverified_stress` in `lessons.yaml` with a reason in `NOTES.md`. Proper names go in `lessons.yaml: proper_names`.

## Verification before you push (paste raw command + cwd + output in the PR)
1. `.venv/bin/python audit/curriculum-upgrade/pilot-things-have-gender/verify_pilot.py` → `VERIFY_PILOT: PASS`
2. `node audit/curriculum-upgrade/pilot-things-have-gender/browser_check.mjs` → `BROWSER_CHECK: PASS`
3. `git diff --stat 7829e74b6031cdcc4ef69895b5f42e0643569e44 -- scripts site starlight .github curriculum/l2-uk-en/plans curriculum/l2-uk-en/a1/things-have-gender` → empty
4. Rendered page updated for every change (the checker's render-coverage check enforces it).
5. A table: fix # → files/lines changed → tool receipts.

Commit with a conventional message and the `X-Agent` trailer (`fix(curriculum-upgrade): pilot repair after cross-family review — …`), push to the same branch, and post the §Verification block plus the fix table as a PR comment on #7991. Do not merge. If any fix cannot be completed, say so in the comment under "Not done" with the reason — never silently skip.
