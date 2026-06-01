# Current Session Handoff

Generated-At: 2026-06-02T00:42+0200

## Active Branch

- Worktree: `/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/a1-m1-m7-golden-journey-2026-05-30`
- Branch: `codex/a1-m1-m7-golden-journey-2026-05-30`
- Current verified pre-refresh HEAD / origin:
  `8d30ff2246 docs(session): refresh A1 M20 handoff`
- Previous committed handoff:
  `a982daed6f docs(session): refresh A1 journey handoff`
- Latest shipped modules:
  - `ce21c0494c feat(a1): add M19 questions module`
  - `d69677aad4 feat(a1): add M18 i want i can module`
  - `16c1b26e94 feat(a1): add M17 group two verbs module`

Current worktree state:

- Branch aligned with origin at `8d30ff2246` before this handoff refresh.
- Only visible untracked file:
  `curriculum/l2-uk-en/a1/i-want-i-can/python_qg.local.json`
  (pre-existing local artifact; do not stage unless explicitly requested).
- No M20 `my-morning` module directory or Starlight MDX file exists.
- Do not resurrect stale deleted M20 artifacts.

## Open Issues / In-Flight Tasks

Recent open issues from `gh issue list --state open --limit 10`:

- #2535: bio: audit + uplift the EXISTING 1-180 plans & wikis to the source-first seminar standard
- #2533: [B1 epic] Stabilize B1 landing, source-of-truth, and Claude V7.2 pilot
- #2532: B1 source-of-truth cleanup before module fanout
- #2526: lit: 8 slug-mismatch errors block promoting validate_plan_ordering.py to BLOCKING CI
- #2522: B1 V7.2 pilot build lane
- #2480: A1 M1-M7 safe onboarding / first-contact slice
- #2454: gemini dispatches killed by external SIGTERM at ~87s with zero output
- #2451: bio: 4 merged dossiers below the 1200-word template floor
- #2419: Deterministic heritage-defense gate
- #2418: V7 retrieval-discipline gates hard-fail on stochastic writer omissions

Active delegates:

- `curl -sS http://127.0.0.1:8765/api/delegate/active` returned
  `{"total":0,"tasks":[]}`.

Services:

- `./services.sh status` showed sources, api, and starlight running on
  ports 8766, 8765, and 4321.

## Shipped This Run

M18 `i-want-i-can` shipped and pushed in `d69677aad4`.

M19 `questions` shipped and pushed in `ce21c0494c`; committed files:

- `curriculum/l2-uk-en/a1/questions/module.md`
- `curriculum/l2-uk-en/a1/questions/activities.yaml`
- `curriculum/l2-uk-en/a1/questions/vocabulary.yaml`
- `curriculum/l2-uk-en/a1/questions/resources.yaml`
- `starlight/src/content/docs/a1/questions.mdx`

Handoff-only commits `a982daed6f` and `8d30ff2246` followed M19.

## M19 Validation Snapshot

M19 passed:

- activity parser: `scripts.yaml_activities`
- direct `run_python_qg()`:
  - word count 1314/1200
  - section budgets passed
- direct seeded hard wiki coverage: 18/18
- MDX assembly and `scripts/validate_mdx.py l2-uk-en a1 19`
- `npm run build:starlight`
- Browser QA at `http://127.0.0.1:4321/a1/questions/`
- visible nonempty Activities tab; clicked a match-up pair
- Resources tab checked; only learner-safe external links
- current runtime tab hash worked; `#repair-traps` anchor scrolled
- targeted pre-commit, `git diff --check`, trailer audit, and push hooks

Activity freshness check for M19:

- M15 types: quiz -> match-up -> fill-in -> group-sort -> quiz ->
  error-correction -> fill-in -> quiz.
- M18 types: quiz -> order -> fill-in -> unjumble -> true-false ->
  translate -> match-up -> error-correction.
- M19 types: match-up -> fill-in -> true-false -> group-sort -> unjumble ->
  translate -> order -> error-correction.
- M19 learner actions differ: question-word job matching, dialogue gap filling,
  intonation recognition, sorting question/answer/negative lines, rebuilding
  negatives, short translation, home-dialogue ordering, and wiki-specific
  repair. It is not a vocabulary swap.

## M20 Inspection Completed Only

Context pressure is now the quality risk. M20 was inspected, but no artifacts
were written. A continuation attempt on 2026-06-02 stopped immediately because
the session was still past the critical compaction threshold; it verified state
only and did not create M20 content.

M20 plan: `curriculum/l2-uk-en/plans/a1/my-morning.yaml`

- Exact H2 sections required:
  - `Діалоги`
  - `Дієслова на -ся`
  - `Мій ранок`
  - `Підсумок`
- Target 1200 words; 300 per section.
- Objectives: recognize/use `-ся/-сь`, describe morning routine with sequence
  words, conjugate reflexive verbs in present, tell a simple daily story.
- Locked references:
  - `1-klas-bukvar-zaharijchuk-2025-1_s0024`
  - `1-klas-bukvar-zaharijchuk-2025-2_s0052`

Retrieved source chunks:

- `1-klas-bukvar-zaharijchuk-2025-1_s0024`, page 26: "Мій день" list with
  `Поснідати. Одягнутися. Піти до Квака. Прогулятися... Погратися...`
- `1-klas-bukvar-zaharijchuk-2025-2_s0052`, page 53: self-directed morning:
  `Уранці Євген устав... Прибрав ліжко... Зробив зарядку... Після сніданку
  ...`

M20 wiki / manifest obligations:

- Start from regular first-conjugation endings, then add `-ся`.
- Active morning reflexives: `прокидатися`, `одягатися`, `умиватися` /
  `вмиватися`; include `-сь` after vowels.
- Pronunciation: `-шся` -> `[с':а]`, `-ться` -> `[ц':а]`, `-ся` -> `[с':а]`.
- Recognition-only: `-уватися/-юватися` with `-ва-` dropping
  (`користуюся`, `користуєшся`); second-conjugation reflexives
  `дивитися`, `вчитися`, `дивлюся`.
- Routine words: `вода`, `руханка`, `сніданок`, `раненько/рано`,
  `швиденько/швидко`, `завжди`, `ніколи`.
- L2 traps to cover in activities:
  - `Я прокидаєшся. / Він прокидаюся.` -> `Я прокидаюся. / Він прокидається.`
  - `[прокидайешся]` -> `[прокидайес':а]`
  - `[одягайет'с'а]` -> `[одягайец':а]`
  - `Я мию себе.` -> `Я миюся. / Я вмиваюся.`
  - `Я дивюся. / Я дивюсь.` -> `Я дивлюся.`
  - `Я користуювася.` -> `Я користуюся.`
- Decolonization: no Russian comparisons; do not frame `-ся` as Russian/shared
  borrowing; use Ukrainian vocabulary (`рушник`, `сніданок`), avoid `завтрак`.
  Do not label `одіватися` as surzhyk/russianism.

Resource notes:

- `wiki/pedagogy/a1/my-morning.sources.yaml` lists learner-safe external
  candidates:
  - `https://www.ukrainianlessons.com/episode109/`
  - `https://opentext.ku.edu/dobraforma/chapter/23-1/`
  - `https://opentext.ku.edu/dobraforma/chapter/23-2/`
- Fresh `mcp__sources.search_external` queries for reflexive verbs returned no
  rows; use the locked source registry candidates and verify links in browser.

Recent pattern files inspected:

- `curriculum/l2-uk-en/a1/questions/module.md`
- `curriculum/l2-uk-en/a1/questions/activities.yaml`
- `curriculum/l2-uk-en/a1/questions/vocabulary.yaml`
- `curriculum/l2-uk-en/a1/questions/resources.yaml`
- `starlight/src/content/docs/a1/questions.mdx`
- `curriculum/l2-uk-en/a1/i-want-i-can/module.md`
- `curriculum/l2-uk-en/a1/i-want-i-can/activities.yaml`
- `curriculum/l2-uk-en/a1/i-want-i-can/resources.yaml`

## Next Steps

Stop this near-compaction session. In a fresh session, continue with M20:

1. Re-run the initial verification from the user objective in the dispatch
   worktree.
2. Create the M20 artifact set:
   - `curriculum/l2-uk-en/a1/my-morning/module.md`
   - `curriculum/l2-uk-en/a1/my-morning/activities.yaml`
   - `curriculum/l2-uk-en/a1/my-morning/vocabulary.yaml`
   - `curriculum/l2-uk-en/a1/my-morning/resources.yaml`
   - `starlight/src/content/docs/a1/my-morning.mdx`
3. Include ignored `writer_tool_calls.json` with the two locked
   `get_chunk_context` calls and external-resource search attempts.
4. Keep activity shapes fresh versus M15-M19. Suggested M20 actions:
   pronunciation recognition, transform regular forms into `-ся` forms, choose
   reflexive vs non-reflexive morning lines, order a morning timeline,
   mini-dialogue completion, and targeted repair for the manifest traps.
5. Validate per user instructions: activity parser, direct QG, seeded hard wiki
   coverage, MDX assembly/validation, `npm run build:starlight`, browser QA,
   targeted pre-commit, and trailer audit.
6. Commit/push M20 as its own slice with
   `X-Agent: codex/a1-m1-m14-golden-journey`.
7. Continue to M21 only after M20 is clean and pushed.

## Restart Commands

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/a1-m1-m7-golden-journey-2026-05-30
git status --short --branch --untracked-files=all
git log --oneline --decorate -8 --no-merges
./services.sh status
curl -sS http://127.0.0.1:8765/api/delegate/active
sed -n '1,240p' curriculum/l2-uk-en/plans/a1/my-morning.yaml
sed -n '1,260p' wiki/pedagogy/a1/my-morning.md
sed -n '1,220p' wiki/pedagogy/a1/my-morning.sources.yaml
```

Guardrails:

- Work only in the dispatch worktree above.
- Use `./services.sh` and
  `/Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/python`.
- Do not touch BIO-owned work, `.python-version`, `.yamllint`,
  `.markdownlint.json`, generated status/audit/review files, or root docs.
- Do not use Gemini for review confidence.
