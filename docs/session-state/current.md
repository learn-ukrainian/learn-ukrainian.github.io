# Current Session Handoff

Generated-At: 2026-06-01T22:35Z

## Active Branch

- Worktree: `/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/a1-m1-m7-golden-journey-2026-05-30`
- Branch: `codex/a1-m1-m7-golden-journey-2026-05-30`
- Latest pushed commit: `ce21c0494c feat(a1): add M19 questions module`
- Previous pushed commit: `d69677aad4 feat(a1): add M18 i want i can module`

Current worktree state after M19 push:

- Branch aligned with origin at `ce21c0494c`.
- One pre-existing untracked local artifact remains:
  `curriculum/l2-uk-en/a1/i-want-i-can/python_qg.local.json`.
- `curriculum/l2-uk-en/a1/questions/writer_tool_calls.json` is ignored by
  `.gitignore`; it was not committed.
- No M20 `my-morning` artifacts exist in the worktree; do not resurrect stale
  deleted M20 artifacts.

## Shipped This Run

M18 `i-want-i-can` shipped and pushed in commit `d69677aad4`.

M19 `questions` shipped and pushed in commit `ce21c0494c`; committed files:

- `curriculum/l2-uk-en/a1/questions/module.md`
- `curriculum/l2-uk-en/a1/questions/activities.yaml`
- `curriculum/l2-uk-en/a1/questions/vocabulary.yaml`
- `curriculum/l2-uk-en/a1/questions/resources.yaml`
- `starlight/src/content/docs/a1/questions.mdx`

## M19 Validation

M19 passed:

- `python -m scripts.yaml_activities curriculum/l2-uk-en/a1/questions/activities.yaml`
- direct `run_python_qg()`:
  - word count 1314/1200
  - section budgets passed: Dialogues 295, Question Words 314, Negation 282,
    Summary 292
- direct seeded hard wiki coverage: 18/18
- MDX assembly via `scripts.build.linear_pipeline.assemble_mdx`
- `scripts/validate_mdx.py l2-uk-en a1 19`
- `npm run build:starlight` (108 pages built)
- targeted pre-commit on the five committed files
- `git diff --check`
- `scripts/audit/lint_agent_trailer.py` before and after commit
- push-side hooks during `git push`

Browser QA for M19:

- Loaded `http://127.0.0.1:4321/a1/questions/`; H1 `Питання`.
- Starlight needed one targeted `./services.sh restart starlight` after adding
  the new content file; after restart the route loaded correctly.
- Activities tab visible, selected, and nonempty with 8 activities.
- Clicked a match-up pair: `Хто?` + `asks for a person`; both became matched
  and disabled.
- Cleaned a literal `<br />` rendering issue in repair activity prompts by
  moving exact wiki coverage strings into non-rendered activity notes.
- Resources tab visible with only external links:
  `ukrainianlessons.com/negation-in-ukrainian/`,
  `ukrainianlessons.com/question-words/`,
  `ukrainianlessons.com/useful-ukrainian-questions/`,
  `ukrainianlessons.com/episode35/`.
- No internal wiki/docs resource links in student-facing resources.
- Current runtime Activities tab hash worked via the tab's actual `href`; the
  `#repair-traps` in-page anchor link scrolled to the heading.

Activity freshness check:

- M15 types: quiz -> match-up -> fill-in -> group-sort -> quiz ->
  error-correction -> fill-in -> quiz.
- M16/M17 use verb-table recognition, repeated fill-ins/group-sort, and repair.
- M18 types: quiz -> order -> fill-in -> unjumble -> true-false -> translate ->
  match-up -> error-correction.
- M19 types: match-up -> fill-in -> true-false -> group-sort -> unjumble ->
  translate -> order -> error-correction.
- M19 actions are question-word job matching, dialogue gap filling, yes/no
  intonation recognition, question/answer/negative sorting, negative
  rebuilding, short translation, home-dialogue ordering, and wiki-specific
  repair. It is not a vocabulary swap of M15-M18.

## M20 Inspection Started

Do not continue in this session without fresh context. M20 inspection only was
started; no M20 files were created.

M20 plan: `curriculum/l2-uk-en/plans/a1/my-morning.yaml`

- Exact H2 sections required:
  - `Діалоги`
  - `Дієслова на -ся`
  - `Мій ранок`
  - `Підсумок`
- Target 1200 words; 300 per section.
- Locked plan references:
  - `1-klas-bukvar-zaharijchuk-2025-1_s0024`: page 26, simple daily plan with
    `Поснідати. Одягнутися. Піти до Квака. Прогулятися... Погратися...`
  - `1-klas-bukvar-zaharijchuk-2025-2_s0052`: page 53, self-directed morning
    sequence: got up, made bed, did exercise, set a cup, washed dishes after
    breakfast.
- `get_chunk_context` was retrieved for both chunk IDs through the sources MCP.

M20 manifest obligations from `build_wiki_manifest_data`:

- sequence steps: regular first-conjugation endings first; then morning `-ся`
  verbs with `-сь` after vowels and pronunciation `[с':а]` / `[ц':а]`; then
  recognition-only `-уватися/-юватися` with `-ва-` drop; then recognition-only
  second-conjugation `дивитися/вчитися` with `дивлюся`; then routine nouns and
  sequence/time words.
- L2 errors to cover in activities:
  - `Я прокидаєшся. / Він прокидаюся.` -> `Я прокидаюся. / Він прокидається.`
  - `Вимова: [прокидайешся]` -> `Вимова: [прокидайес':а]`
  - `Вимова: [одягайет'с'а]` -> `Вимова: [одягайец':а]`
  - `Я мию себе.` -> `Я миюся. / Я вмиваюся.`
  - `Я дивюся. / Я дивюсь.` -> `Я дивлюся.`
  - `Я користуювася.` -> `Я користуюся.`
- phonetic rules: `-шся` -> `[с':а]`, `-ться` -> `[ц':а]`, `-ся` -> `[с':а]`.
- decolonization bans: no Russian comparisons for reflexive verbs or
  pronunciation; do not frame `-ся` as Russian/shared borrowing; use Ukrainian
  morning vocabulary (`рушник`, `сніданок`) and avoid the bad form `завтрак`.

Suggested M20 resources from searches:

- `https://www.ukrainianlessons.com/reflexive-verbs/`
- `https://www.ukrainianlessons.com/episode109/`
- Dobra Forma reflexive verb chapters are listed in the source registry:
  `https://opentext.ku.edu/dobraforma/chapter/23-1/` and
  `https://opentext.ku.edu/dobraforma/chapter/23-2/`.

## Next Steps

Continue with M20 `my-morning` only after refreshing context:

1. Create the full M20 artifact set under
   `curriculum/l2-uk-en/a1/my-morning/` plus
   `starlight/src/content/docs/a1/my-morning.mdx`.
2. Include ignored `writer_tool_calls.json` with both locked
   `get_chunk_context` calls and at least one external resource search.
3. Validate per user instructions: activity parser, direct QG, seeded wiki
   coverage, MDX assembly/validation, `npm run build:starlight`, browser QA,
   targeted pre-commit, and trailer audit.
4. Commit/push M20 as its own safe slice with:
   `X-Agent: codex/a1-m1-m14-golden-journey`.

Guardrails:

- Work only in the dispatch worktree above.
- Use `./services.sh` and
  `/Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/python`.
- Do not touch BIO-owned work, `.python-version`, `.yamllint`,
  `.markdownlint.json`, generated status/audit/review files, or root docs.
- Do not use Gemini for review confidence.
