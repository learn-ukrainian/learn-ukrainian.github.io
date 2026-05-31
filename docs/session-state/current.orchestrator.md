# Current - Codex orchestrator handoff (2026-05-31T22:00Z)

Latest-Brief: docs/session-state/current.orchestrator.md

> Handoff-only update. Treat `origin/main` and this file as authoritative.

## Role / Direction

- Codex is the orchestrator and sidekick for GitHub issue memory, agent bridge
  awareness, A1 golden learner journey, tooling, infra, and tech debt.
- BIO track is fully owned by the BIO orchestrator (Claude). Do not interfere
  with BIO PRs/content/delegates unless Claude explicitly asks Codex for help.
- When a track orchestrator is promoted, let that orchestrator run the track.
  They can call headless Codex when needed; Codex main stays organized around
  repo-wide orchestration and non-BIO work.
- Use the strong-agent mix actively for bounded work:
  - Codex: orchestration, integration, code changes, final merge judgment.
  - Claude: BIO ownership, deep PR/path review via `review-deep`, sensitive
    reasoning.
  - Cursor: implementation/content rebuild work through delegate/bridge.
  - DeepSeek: cheap code/content review and deterministic triage via delegate.
- Stop using Gemini for reviews until the user says otherwise. Gemini review
  checks are currently unreliable/noisy and should not provide merge confidence.
- Do not delete or pause old automation unless explicitly instructed.

## Git State

- Repo: `/Users/krisztiankoos/projects/learn-ukrainian`
- Main checkout branch: `main`
- Current authoritative remote head at handoff:
  `836526d165 feat(api): surface bridge activity for orchestrators`
- Main checkout has unrelated dirty user/Claude files; do not revert:
  - `docs/bio-epic/CLAUDE-DRIVER-HANDOFF.md`
  - `scripts/deploy_prompts.sh`
  - `docs/bio-epic/phase2-word-target-defects-2026-05-31.txt`
  - `docs/session-state/2026-05-30-pr2460-bak-fix-inflight.md`

## Completed Since Prior Handoff

- #2459 merged: BIO Claude driver handoff refresh.
- #2450 merged: agent-specific thread handoff routers. `docs/session-state/current.md`
  is now a router; detailed state lives in `current.<agent>.md`.
- #2447 merged: stressed plan section heading gate.
- #2478 merged: `GET /api/comms/agent-activity` read-only bridge activity
  endpoint plus manifest discovery. Local API at `127.0.0.1:8765` was still
  serving the old process when checked, so restart it before expecting the new
  endpoint locally.

Note: #2478 deterministic CI passed and local Gemini diff review had no
findings, but the user has since corrected policy: do not use Gemini for review
confidence going forward.

## Active Delegates

Check with:

```bash
curl -sS http://127.0.0.1:8765/api/delegate/active
```

Active at handoff time:

- `review-2477-20260531080952` - Claude Opus review-deep for BIO PR #2477.
- `bio-rebuild-blockI1` - Cursor, running before this handoff.
- `bio-rebuild-blockG7` - Cursor, running before this handoff.
- `review-pr2476-plan-ci` - DeepSeek v4 flash read-only triage for BIO PR
  #2476. Dispatched before the BIO boundary correction; let Claude decide
  whether to use or ignore the result.
- `review-pr2474-plan-ci` - DeepSeek v4 flash read-only triage for BIO PR
  #2474. Dispatched before the BIO boundary correction; let Claude decide
  whether to use or ignore the result.

Do not assume the bridge `status` command is authoritative for delegates; use
`/api/delegate/active` and task logs/state.

## BIO Boundary

Open BIO PRs remain, but they are Claude/BIO-orchestrator owned. Codex should
not triage, fix, merge, or route BIO content PRs unless Claude asks. Awareness:

- #2477 deterministic checks clean; Gemini review canceled; Claude review
  running.
- #2476 has real `Curriculum Plans` failure:
  `hryhorii-khomyshyn` content outline sum 4000 under word target 5200.
- #2474 has real `Curriculum Plans` failure:
  `danylo-shcherbakivskyi` word target under config, plan 3400 vs config 5000.
- #2473 and #2471 have real `Curriculum Plans` failures and active Cursor BIO
  rebuild delegates.
- #2475, #2472, #2470, #2469, #2468 appeared deterministic-clean except
  Gemini review failure/cancellation at last check.

Let Claude/BIO orchestrator handle these.

## Agent Bridge Routes

Use these instead of Gemini:

```bash
.venv/bin/python scripts/ai_agent_bridge/__main__.py review-deep <PR-or-path> --effort high
.venv/bin/python scripts/ai_agent_bridge/__main__.py ask-claude "<prompt>" --task-id <id> --review
.venv/bin/python scripts/ai_agent_bridge/__main__.py ask-cursor - --task-id <id>
.venv/bin/python scripts/delegate.py dispatch --agent deepseek --model deepseek-v4-flash --mode read-only --task-id <id> --prompt '<prompt>'
```

DeepSeek is wired through Hermes:

- `deepseek-v4-flash`: cheap code/PR review and CI triage.
- `deepseek-v4-pro`: content review / VESUM-heavy lanes.

Cursor has broker/delegate support but no PR-comment auto-posting wrapper.
Claude `review-deep` is the explicit PR/path review wrapper.

## A1 Direction

Codex focus now: A1, tooling, infra, tech debt, and GitHub issues.

Do not treat m20/m21/m22 as product strategy. They are support/validation
items. Product direction:

- Start A1 from the beginning.
- Build the learner experience as the product spine.
- First slice is A1 M1-M7 safe onboarding / first contact.
- Fix pipeline/gates only when they block excellent learner content.

A1 M1-M7 sequence:

1. `sounds-letters-and-hello`
2. `reading-ukrainian`
3. `special-signs`
4. `stress-and-melody`
5. `who-am-i`
6. `my-family`
7. `checkpoint-first-contact`

## A1 M1 / Infra Update (2026-05-31)

- Active A1 worktree:
  `.worktrees/dispatch/codex/a1-m1-m7-golden-journey-2026-05-30`
- Branch:
  `codex/a1-m1-m7-golden-journey-2026-05-30`
- Latest introduced-before-use implementation commit:
  `c50829a667 feat(audit): gate A1 M1 introduced-before-use`
- Latest resource-coverage implementation commit:
  `e8633c3145 feat(pipeline): gate A1 M1 resource coverage`
- Follow-up commits after the M1 rewrite:
  - `e514421f78 fix(infra): decouple etymology from lesson builds`
  - `594c72e928 feat(pipeline): define module archetype contracts`
  - `f84e8a8702 feat(pipeline): inject module archetype into writer prompts`
  - `b6dd723acb fix(pipeline): block internal wiki resources`
  - `c50829a667 feat(audit): gate A1 M1 introduced-before-use`
  - `e8633c3145 feat(pipeline): gate A1 M1 resource coverage`
  - `099c6d5009 fix(pipeline): allow A1 workbook-only activities`
  - `04860251b9 fix(a1): replace passive alphabet map`
  - `6ccce0946a fix(a1): close M1 wiki and gate coverage`
  - `79c8d84fe9 feat(pipeline): gate module archetype fit`
  - `42195a1d59 fix(pipeline): gate A1 M1-M7 resource coverage`
  - `48b3b15978 fix(pipeline): allow A1 M2-M7 English section headings`
  - `f07757ea58 feat(a1): add M2 reading Ukrainian module`
  - `440cd017a6 feat(a1): add M3 special signs module`
- M1 is a hand-authored zero-learner textbook/workbook template, not a
  universal golden module for all A1/A2. Treat it as the quality bar for the
  `A1-zero-script-onboarding` archetype only.
- The writer prompt now receives a `MODULE_ARCHETYPE` block derived from
  `scripts/pipeline/module_archetypes.py`; it is injected into all linear
  writer templates (`linear-write.md`, generated, and grok variants).
- Student-facing `resources.yaml` must not include internal AI-facing wiki
  paths such as `wiki/pedagogy/...`; the writer artifact validator now blocks
  `wiki/` and `docs/wiki/` URLs, and A1 M1's resource file has had the internal
  wiki entry removed.
- Completed read-only delegate:
  `a1-archetype-gate-design` (`codex`, `gpt-5.4-mini`) finished successfully;
  result is in `batch_state/tasks/a1-archetype-gate-design.result`.
- First deterministic gate implemented:
  `check_introduced_before_use()` in
  `scripts/audit/checks/learner_state.py`. It is scoped through
  `resolve_module_archetype()` and only fires for
  `a1-zero-script-onboarding` for now. It checks plan-required terms from
  `vocab_grammar_targets.must_introduce`, `targets.new_vocabulary`, and
  `vocabulary_hints.required`, then requires the first learner-facing lesson or
  activity use to include an English gloss/explicit introduction. A1 M1 now
  passes this gate after adding same-row glosses for `звук` and `літера`.
- Second deterministic gate implemented and extended:
  `resource_coverage` in `scripts/build/linear_pipeline.py` now fires for A1
  M1-M7 archetypes. It checks non-internal plan references, plan
  `pronunciation_videos`, and wiki manifest `external_resources` against
  `resources.yaml`; internal AI-facing wiki references are skipped, not
  published. A1 M1 and M2 now pass this gate. Manual resource-search telemetry
  pass-through is allowed only for A1 M1-M7 when deterministic coverage has
  already passed.
- `inject_activity_ids` now respects the M1-M7 textbook/workbook split. For A1
  zero/script/first-contact archetypes, workbook-only activities are allowed
  while unknown injected ids still fail. A1 M1 now passes this gate with
  `act-4`, `act-7`, `act-8`, and `act-9` classified as workbook-only.
- A1 M1 `act-4` is no longer a passive alphabet map. It is now an active
  recognition quiz for high-value letters/signs, and the generated Starlight
  MDX has been refreshed. The YAML `letter-grid` renderer also no longer
  duplicates a title as both a heading and component prop.
- A1 M1 seeded full wiki coverage now passes at 12/12 (`coverage_pct: 1.0`,
  minimum 0.8). This is separate from `resource_coverage`, which also passes
  and still has no missing plan references, pronunciation videos, or wiki
  external resources.
- A1 M1 direct `run_python_qg()` now passes. Commit `6ccce0946a` closed the
  prior failures by:
  - adding real wiki-obligation coverage to M1 content and workbook activities;
  - adding translate explanations and preserving them through YAML-to-MDX;
  - adding an active pronunciation-trap error-correction workbook activity for
    the required L2 contrast pairs;
  - allowing English heading aliases only for `a1-zero-script-onboarding`;
  - allowing manual resource-search telemetry pass-through only for A1
    zero-script modules with passing deterministic `resource_coverage`;
  - ignoring sung vowel practice strings in VESUM and alphabet rows in the
    long-UK immersion ceiling.
- Latest deterministic gate implemented:
  `archetype_fit`. `scripts/audit/checks/contract_compliance.py` now exposes
  `check_archetype_fit()`, and `scripts/build/linear_pipeline.py` records it in
  `run_python_qg()`. It does not replace wiki/resource, VESUM, Russianism, or
  decolonization gates. For A1 M1-M7 it checks no internal wiki links,
  English-led surface, workbook activity floor, A1-compatible activity
  families, and a real textbook/workbook split. A1 M1 passes this gate.
- M2 build completed:
  `f07757ea58 feat(a1): add M2 reading Ukrainian module` added the English-led
  `reading-ukrainian` module, activities, vocabulary, resources, and rendered
  Starlight MDX. Direct M2 `run_python_qg()` passes, including hard
  `resource_coverage` and `archetype_fit` for `a1-script-building`.
- M3 build completed:
  `440cd017a6 feat(a1): add M3 special signs module` added the English-led
  `special-signs` module, activities, vocabulary, resources, and rendered
  Starlight MDX. Direct M3 `run_python_qg()` passes, including hard
  `resource_coverage` and `archetype_fit` for `a1-script-building`.
- `plan_sections` now allows approved English learner-facing headings for A1
  M1-M7 while still requiring every locked plan section.
- Validation for `79c8d84fe9`:
  - `tests/test_contract_compliance.py`: 36 passed.
  - focused suite covering contract, inject, resource, plan-reference, and
    translate explanations: 55 passed.
  - direct A1 M1 `run_python_qg()`: passed.
  - `ruff check` on touched files: passed.
  - `git diff --check`: passed.
  - `npm run build:starlight`: passed; 91 pages built.
  - pre-commit on commit: passed.
- Latest validation:
  - M2 `scripts.yaml_activities`: passed.
  - M2 direct `run_python_qg()`: passed.
  - focused gate suite after infra changes: 73 passed.
  - `scripts/validate_mdx.py l2-uk-en a1 2`: passed.
  - `npm run build:starlight`: passed; 92 pages built.
  - local Starlight restarted via `services.sh` and serves
    `/a1/reading-ukrainian/`.
  - Playwright browser inspection could not run because the local Playwright
    browser binary is missing; served HTML was inspected instead.
  - M3 `scripts.yaml_activities`: passed.
  - M3 direct `run_python_qg()`: passed.
  - `scripts/validate_mdx.py l2-uk-en a1 3`: passed.
  - `npm run build:starlight`: passed; 93 pages built.
  - local Starlight was restarted after a hot-reload 500 and now serves
    `/a1/special-signs/`; served HTML was inspected.
- Next implementation target:
  build M4 (`stress-and-melody`) with the same full artifact set and direct
  `run_python_qg()` validation. Keep wiki/resource coverage hard.
- Product/infra findings are documented in
  `docs/architecture/learner-runtime-and-build-split.md`.
- Normal lesson builds should not rebuild the ESUM etymology dynamic route
  set. Use `npm run build:starlight` for fast learner-surface builds and
  `npm run build:starlight:full` only for full reference/deploy builds.
- `services.sh` should own the local Starlight preview. Run it from the active
  worktree when previewing that worktree:

```bash
./services.sh restart starlight
./services.sh status
```

## Restart Commands

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
git status --short
git log --oneline -8 --decorate --no-merges
curl -sS http://127.0.0.1:8765/api/delegate/active
gh pr list --state open --json number,title,headRefName,mergeStateStatus,statusCheckRollup,url,updatedAt,isDraft,reviewDecision --limit 20
```

## Guardrails

- Use `.worktrees/dispatch/<agent>/<task>/` for implementation.
- Do not edit generated status/audit/review artifacts, linter configs, or
  `.python-version`.
- Every commit must carry an `X-Agent` trailer.
- Use `.venv/bin/python`, not `sys.executable` or system Python.
- Do not revert unrelated dirty files in the main checkout.
