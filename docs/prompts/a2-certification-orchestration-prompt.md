# A2 Certification Orchestration Prompt

Use this as a standalone handoff prompt for a fresh A2 certification thread.
Copy from `BEGIN PROMPT` through `END PROMPT`.

## BEGIN PROMPT

You are continuing certification orchestration for the A2 Ukrainian course in
`/Users/krisztiankoos/projects/learn-ukrainian`.

Your goal is to make A2 learner pages certification-ready one module at a time,
starting with the first uncertified module in curriculum order. Certification is
stricter than "released" or "live": the page must be source-backed,
teacher-natural, A2-appropriate, reviewed by an independent Claude/Opus pass,
independently gate-checked, merged to `main`, CI-green, and live on the public
site route.

Definition of certified for an A2 module:

- The source files and generated MDX are merged to `main`.
- The public route returns 200 after deploy:
  `https://learn-ukrainian.github.io/a2/<slug>/`.
- The lesson is grounded in the plan, A2 grammar scope, Ukrainian sources, and
  the A2 wiki/locked-review corpus.
- Deterministic gates pass.
- LLM QG has no dimension below 8.0; target 9.0 where practical.
- The PR body records LLM QG scores, Claude/Opus review outcome, independent
  final gate outcome, validation commands, route evidence, and token telemetry.
- No generated status/review/audit artifacts are committed.

## Known Baseline To Verify, Not Assume

As of 2026-06-16, local `origin/main` was at `b3827f1b51` and A2 release PR
[#3262](https://github.com/learn-ukrainian/learn-ukrainian.github.io/pull/3262)
had already merged at `9ad2c982b73fdae267bac0d0af2ef848d952166c`.

PR #3262 made A2 release-ready by:

- accepting the existing `targets` alias in `mark-the-words` activities;
- aligning the activities schema with A2 source formats already supported by
  the parser;
- treating `scripts/yaml_activities.py` as an MDX generator dependency in the
  source-parity gate;
- regenerating all 69 released A2 lesson MDX pages;
- adding regression tests for parser aliases and parity dependencies.

Do not treat #3262 as certification. It is the release-readiness baseline.
Verify current `main`, current open PRs, current A2 route status, and any
already-certified A2 modules before choosing the next target. If no certified
A2 module evidence exists, start at M01 `a2-bridge`.

## Non-Negotiable Repo Rules

- Do all implementation in a dispatch worktree:
  `.worktrees/dispatch/codex/a2-mXX-<slug>-certify/`.
- Branch name:
  `codex/a2-mXX-<slug>-certify`.
- Commit trailer:
  `X-Agent: codex/a2-mXX-<slug>-certify`.
- Do not modify `.python-version`, `.yamllint`, or `.markdownlint.json`.
- Do not use `sys.executable`; always use `.venv/bin/python`.
- Do not use container paths such as `/app/...`.
- Use `site/`, not `starlight/`.
- Do not hand-edit generated MDX unless the generator itself is the scoped
  target. Edit curriculum sources, regenerate MDX, and include both only when
  source changes require generated MDX changes.
- Do not commit:
  - `curriculum/l2-uk-en/**/status/*.json`
  - `curriculum/l2-uk-en/**/audit/*-review.md`
  - `curriculum/l2-uk-en/**/review/*-review.md`
  - `docs/*-STATUS.md`
  - `data/telemetry/**`
  - `llm_qg.json`, `python_qg.json`, raw reviewer prompts/responses, or other
    transient QG evidence unless an existing module-build workflow explicitly
    requires that artifact in git. Prefer summarizing scores in the PR body.
- Keep changed files directly related to the module.
- One PR certifies one module unless the user explicitly expands scope.
- Never weaken tests or linter configs to pass CI.

## Mandatory First Reads

Before editing, read and report what you learned from:

- `AGENTS.md`
- `agents_extensions/shared/memory/MEMORY.md`
- `docs/runbooks/module-build-token-telemetry.md`
- `curriculum/l2-uk-en/curriculum.yaml`, A2 section
- `agents_extensions/shared/quick-ref/a2.md`
- `agents_extensions/shared/phases/calibration/a2.md`
- `site/src/content/docs/a2/index.mdx`
- PR #3262 body and files
- any current A2 PRs:
  `gh pr list --state open --search "a2" --json number,title,headRefName,url`
- `docs/decisions/pending/*.md`; only block if a pending decision's `Scope`
  covers the target module

For the selected module also read:

- `curriculum/l2-uk-en/plans/a2/<slug>.yaml`
- `curriculum/l2-uk-en/a2/<slug>/module.md`
- `curriculum/l2-uk-en/a2/<slug>/activities.yaml`
- `curriculum/l2-uk-en/a2/<slug>/vocabulary.yaml`
- `curriculum/l2-uk-en/a2/<slug>/resources.yaml`
- `wiki/grammar/a2/<slug>.md`
- `wiki/grammar/a2/<slug>.sources.yaml`
- `wiki/.reviews/grammar/a2/<slug>-review-LOCKED.md`
- `site/src/content/docs/a2/<slug>.mdx`

## A2 Curriculum Order

Use this sequence unless current source says otherwise:

### A2.1 [Основи та вступ до виду дієслова]

1. M01 `a2-bridge`
2. M02 `aspect-concept`
3. M03 `aspect-in-vocabulary`
4. M04 `liudyna-i-stosunky`
5. M05 `genitive-intro`
6. M06 `genitive-dates-numbers`
7. M07 `foundations-practice`
8. M08 `checkpoint-foundations`

### A2.2 [Родовий відмінок: завершення]

1. M09 `genitive-prepositions-source`
2. M10 `genitive-prepositions-purpose`
3. M11 `genitive-prepositions-direction`
4. M12 `euphony-advanced`
5. M13 `genitive-adjectives-pronouns`
6. M14 `genitive-plural`
7. M15 `shopping-and-health`
8. M16 `checkpoint-genitive`

### A2.3 [Давальний відмінок]

1. M17 `dative-pronouns`
2. M18 `dative-nouns`
3. M19 `dative-adjectives-pronouns`
4. M20 `locative-expanded`
5. M21 `dative-verbs`
6. M22 `services-and-communication`
7. M23 `checkpoint-dative`

### A2.4 [Орудний відмінок і звертання]

1. M24 `instrumental-accompaniment`
2. M25 `instrumental-means`
3. M26 `instrumental-profession`
4. M27 `vocative-expanded`
5. M28 `instrumental-prepositions`
6. M29 `instrumental-adjectives-pronouns`
7. M30 `work-and-food`
8. M31 `checkpoint-instrumental`

### A2.5 [Синтез відмінків та множина]

1. M32 `plural-nominative-accusative`
2. M33 `plural-genitive`
3. M34 `plural-other-cases`
4. M35 `dozvillia-i-khobi`
5. M36 `which-case-when`
6. M37 `all-cases-practice`
7. M38 `home-and-daily-life`
8. M39 `checkpoint-cases`

### A2.6 [Вид, часи та рух]

1. M40 `aspect-in-past`
2. M41 `synthetic-future`
3. M42 `aspect-mastery`
4. M43 `motion-verbs`
5. M44 `imperative-complete`
6. M45 `telling-stories-and-travel`
7. M46 `checkpoint-verbs`

### A2.7 [Складні речення та умови]

1. M47 `because-and-although`
2. M48 `purpose-clauses`
3. M49 `relative-clauses`
4. M50 `word-order-emphasis`
5. M51 `real-conditionals`
6. M52 `education-and-work`
7. M53 `checkpoint-syntax`

### A2.8 [Удосконалення та випуск]

1. M54 `comparison`
2. M55 `numerals-and-cases`
3. M56 `sviy-and-sebe`
4. M57 `indefinite-negative-pronouns`
5. M58 `synonyms-antonyms-style`
6. M59 `preferences-and-choices`
7. M60 `nature-and-traditions`

### A2.9 [Метамова: місток та основи]

1. M61 `metalanguage-words-and-cases`
2. M62 `metalanguage-verbs-and-time`
3. M63 `metalanguage-sentences-and-classroom`
4. M64 `metalanguage-phonetics`
5. M65 `metalanguage-morphology`
6. M66 `metalanguage-syntax-cases`

### A2.10 [Вдосконалення та випуск]

1. M67 `a2-comprehensive-review`
2. M68 `a2-practice-exam`
3. M69 `a2-finale`

## A2 Pedagogy Bar

A2 is not B1. Do not deepen by making the material abstract or advanced.
Improve by making it clearer, better scaffolded, better sourced, and more
usable by a real A2 learner.

Use these A2 constraints:

- Allowed grammar: all 7 cases, simple subordinate clauses with
  `який` / `що` / `коли`, aspect pairs introduced.
- Forbidden grammar: participles and complex subordinate clauses.
- Ukrainian sentences should stay short: max 15 words, max 2 clauses.
- Do not mix languages inside one sentence. A sentence is fully Ukrainian or
  fully English.
- Teach Ukrainian IN Ukrainian. Easy Ukrainian is the teaching voice from M01;
  immersion is already high and converges to full by end of A2:
  - M01-M20: 85-100% Ukrainian
  - M21-M50: 90-100% Ukrainian
  - M51-M69: 95-100% Ukrainian
- English appears ONLY as vocabulary glosses (inline em-dash or Tab 2 Словник).
  NEVER explain Ukrainian grammar in English prose. NEVER add mirrored English
  translation paragraphs after Ukrainian content. The learner builds Ukrainian by
  using it, not by hearing about it in English.
- No Latin transliteration.
- No IPA or phonetic brackets.
- Stress marks only where the project convention requires them.
- Register is concrete everyday A2: real actions, real objects, real service
  situations, real school/work/home/travel needs.
- Avoid literary, poetic, figurative, and heavily abstract language. In M58,
  where style is the topic, keep figures controlled, glossed, and A2-limited.
- Grammar metalanguage is allowed where the plan requires it, but gloss it and
  teach it as language a learner can use, not as academic taxonomy.

Run explicit A2 calque/russianism checks. At minimum, reject:

- `приймати участь` -> `брати участь`
- `самий кращий` -> `найкращий`
- `на то, що` -> `на те, що`
- `відноситися` when the intended meaning is `стосуватися` or `ставитися`
- `слідуючий` -> `наступний`
- `скучати` when the intended meaning is `сумувати` / `нудьгувати`
- `нравитися` -> `подобатися`
- `робити рішення` -> `приймати рішення`
- `брати місце` -> `відбуватися`
- `робити сенс` -> `мати сенс`

## Source And Evidence Rules

- The plan remains the source of truth. If a plan is wrong or underspecified,
  isolate that as a separate problem before rewriting around it.
- Use Ukrainian sources and repo-local tools before guessing:
  VESUM, `data/sources.db`, textbook corpus, wiki grammar source files, and
  locked A2 grammar reviews.
- Do not fabricate quotes, textbook references, source titles, error codes,
  route statuses, PR states, or review outcomes.
- Every claim in the PR body must be backed by a local command, GitHub command,
  route check, or reviewer output.
- If Qdrant or a search service is unavailable, use local deterministic sources
  and say exactly which tool/source was used.

## Per-Module Workflow

1. Sync and select the next target.

   ```bash
   git fetch --prune origin
   git switch main
   git pull --ff-only
   gh pr list --state open --search "a2" --json number,title,headRefName,url
   ```

2. Create the worktree.

   ```bash
   git worktree add -b codex/a2-mXX-<slug>-certify \
     .worktrees/dispatch/codex/a2-mXX-<slug>-certify origin/main
   cd .worktrees/dispatch/codex/a2-mXX-<slug>-certify
   ```

3. Read the target source set and find actual defects.

   Do not churn prose for style alone. Prioritize:

   - A2 grammar scope violations
   - weak or missing scaffolding
   - unnatural Ukrainian
   - Russianisms, calques, or Anglicisms
   - activity answers that do not match component schemas
   - vocabulary entries that lack useful learner support
   - source-plan drift
   - MDX generation drift
   - route/build failures

4. Apply narrowly scoped fixes in source files.

   Common source files:

   - `curriculum/l2-uk-en/a2/<slug>/module.md`
   - `curriculum/l2-uk-en/a2/<slug>/activities.yaml`
   - `curriculum/l2-uk-en/a2/<slug>/vocabulary.yaml`
   - `curriculum/l2-uk-en/a2/<slug>/resources.yaml`

   Activity YAML may be a V1 bare list or a V2 object with `inline:` and
   `workbook:` lists. Never wrap the root list in an `activities:` key.

5. Regenerate MDX.

   The wrapper usage is:

   ```bash
   .venv/bin/python scripts/generate_mdx.py l2-uk-en a2 <module_num> --validate
   ```

   Do not run `scripts/generate_mdx.py --help`; the wrapper interprets the
   first positional argument as the curriculum.

6. Run deterministic gates.

   ```bash
   .venv/bin/python scripts/validate_plan_config.py --quiet a2
   .venv/bin/python scripts/validate_activities.py l2-uk-en a2 <module_num>
   .venv/bin/python scripts/validate_activities_v2.py \
     curriculum/l2-uk-en/a2/<slug>/activities.yaml
   .venv/bin/python scripts/audit/check_mdx_generation_drift.py --files \
     curriculum/l2-uk-en/plans/a2/<slug>.yaml \
     curriculum/l2-uk-en/a2/<slug>/module.md \
     curriculum/l2-uk-en/a2/<slug>/activities.yaml \
     curriculum/l2-uk-en/a2/<slug>/vocabulary.yaml \
     curriculum/l2-uk-en/a2/<slug>/resources.yaml \
     site/src/content/docs/a2/<slug>.mdx
   .venv/bin/python scripts/audit/check_mdx_source_parity.py --files \
     curriculum/l2-uk-en/a2/<slug>/module.md \
     curriculum/l2-uk-en/a2/<slug>/activities.yaml \
     curriculum/l2-uk-en/a2/<slug>/vocabulary.yaml \
     curriculum/l2-uk-en/a2/<slug>/resources.yaml \
     site/src/content/docs/a2/<slug>.mdx
   git diff --check
   npm run build --prefix site -- --outDir /tmp/learn-ukrainian-a2-mXX-<slug>-dist
   ```

   If `validate_activities_v2.py` rejects a V1-only file shape, report that
   and rely on the level validator plus schema-specific tests relevant to the
   file. Do not convert V1 to V2 unless the module fix requires it.

7. Run LLM QG.

   Use the current project runner. For Codex-authored module edits, the reviewer
   must be a different model family:

   ```bash
   .venv/bin/python scripts/build/run_llm_qg_parity.py a2 <slug> \
     --writer codex-tools --reviewer claude-tools
   ```

   The script writes transient JSON evidence. Summarize the scores and verdicts
   in the PR body. Do not commit transient QG JSON unless current project rules
   explicitly require it.

8. Ask Claude/Opus for review before committing.

   Use the available Claude review bridge/dispatch path. The review request must
   include the target module, diff, plan, A2 calibration constraints, local gate
   outputs, and LLM QG summary. Ask for this output:

   ```text
   Review A2 MXX <slug> certification diff.
   Return one of: BLOCKER, FIX_BEFORE_PR, PASS.
   Focus on A2 scope, Ukrainian naturalness, Russianisms/calques,
   activity correctness, source-plan adherence, and whether the page is
   genuinely useful to an A2 learner.
   Cite concrete file paths and lines for every finding.
   ```

   Fix surviving findings, regenerate, and rerun affected gates.

9. Run the independent final gate.

   Use Agy/Gemini-family only through the established bridge/fleet protocol if
   available. Do not use GitHub Gemini Code Assist and do not let the same model
   family review itself. Treat concrete findings as actionable; challenge vague
   or unsupported findings with evidence.

10. Commit, push, and open a PR.

    ```bash
    git status --short
    git add <only-related-files>
    git diff --cached --stat
    git commit -m "fix(a2): certify MXX <slug>" \
      --trailer "X-Agent: codex/a2-mXX-<slug>-certify"
    .venv/bin/python scripts/audit/lint_agent_trailer.py
    git push -u origin codex/a2-mXX-<slug>-certify
    gh pr create --base main --head codex/a2-mXX-<slug>-certify \
      --title "fix(a2): certify MXX <slug>" \
      --body-file /tmp/a2-mXX-<slug>-pr-body.md
    ```

11. PR body requirements.

    Include:

    - summary of source changes;
    - exact A2 module and public route;
    - deterministic validation commands and outcomes;
    - LLM QG dimension scores and verdict;
    - Claude/Opus review outcome;
    - independent final gate outcome;
    - public or local route/build evidence;
    - artifact exclusion note;
    - token telemetry summary.

    Token telemetry must follow
    `docs/runbooks/module-build-token-telemetry.md` and explicitly state:

    ```text
    Token telemetry:
    - swarm_used: true/false
    - swarm_label: ...
    - swarm_note: ...
    - wall_clock_minutes: ...
    - token_source: actual/estimated/unavailable
    ```

    Persist the same record through the Monitor API endpoint described in the
    runbook. Do not commit the local SQLite telemetry store.

12. CI, review, merge, and public route.

    ```bash
    gh pr checks <PR_NUMBER> --watch --interval 10
    ```

    If blocking CI fails, fix it. Do not admin-bypass blocking failures.

    When CI is green and required reviews are addressed:

    ```bash
    gh pr merge <PR_NUMBER> --squash --delete-branch
    git switch main
    git pull --ff-only
    ```

    After deploy, verify:

    ```bash
    curl -sI https://learn-ukrainian.github.io/a2/<slug>/ | head
    ```

    Then clean the worktree:

    ```bash
    git worktree remove .worktrees/dispatch/codex/a2-mXX-<slug>-certify
    git branch -d codex/a2-mXX-<slug>-certify
    ```

13. Move to the next module only after the previous module is merged and live.

## First Response In The New Thread

Do not implement immediately. First respond with:

- confirmation that mandatory reads were completed;
- current `main` and `origin/main` SHAs;
- root dirty/clean state;
- current A2 open PRs, if any;
- verified A2 release baseline and whether #3262 is present in current `main`;
- known certified A2 modules, if any, with evidence;
- selected next target module;
- branch name, worktree path, public route, and `X-Agent` trailer;
- any blocker from pending decisions or current CI.

Then wait for the user to say to proceed.

## END PROMPT

## Construction Review

- Built from the B1 orchestration example but adapted to A2's actual 69-module,
  10-phase curriculum in `curriculum/l2-uk-en/curriculum.yaml`.
- Checked A2-specific calibration in `agents_extensions/shared/quick-ref/a2.md`
  and `agents_extensions/shared/phases/calibration/a2.md`.
- Anchored the release baseline to merged PR #3262 without conflating release
  readiness with certification.
- Used current repo commands for A2 validation, MDX drift, source parity, site
  build, LLM QG, agent trailers, and PR checks.
- Preserved hard project constraints: `.venv/bin/python`, `site/`, worktree
  subtree layout, no linter config edits, no `.python-version` edits, no
  generated status/audit/review artifacts, and no committed telemetry DB.
