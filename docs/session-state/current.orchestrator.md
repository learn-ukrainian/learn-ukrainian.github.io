# Orchestrator — 2026-09-12 curriculum-upgrade session snapshot

Written at session end by claude-fable-5-1 (session 005deabf). Resume from live state; this is the pointer set.

Retirement update (2026-09-24): #7995 is closed and `a1-upgrade` is no longer a launchable lane. The session notes below are historical; verify live state before resuming #7994.

## Epics and boundary
- **#7994 `curriculum-upgrade`** — the upgrade MACHINERY (pipeline upgrade mode, `lessons.yaml` deriver, per-lesson gates, MDX assembler + nav, writer/reviewer prompts, skill edits). Stays open; rollout-found defects are fixed here.
- **#7995 `a1-upgrade`** — CONTENT rollout was planned through this machinery in this snapshot; epic closed 2026-09-24 and selector retired.
- Operator decisions (2026-09-12): Option A (one page per lesson under a module landing) · parallel level `a1-v2`, current `/a1/` untouched until cut-over (`a1`→`a1-v1`, `a1-v2`→`/a1/`) · **upgrade, not rebuild**: input = existing built module, original prose preserved verbatim + expanded, activities added for variety · no named narrator / no «Приві́т! Я …» opener · quoting reference material only as a marked, attributed quotation listed in Ресурси · taxonomy alias `curriculum-upgrade` under `core` and skill edits (`track-completion`, `curriculum-lifecycle`, `build-monitoring`, `curriculum-writer`) still need the operator's explicit go.

## Phase 0 pilot — PR #7991 (draft, branch `agy/cu-p0-pilot-writer-things-have-gender`)
- Fixture: `curriculum/l2-uk-en/a1-v2/things-have-gender/` (lessons.yaml, lesson-1..3, NOTES.md); rendered `docs/poc/poc-lesson-split-things-have-gender.html`; design template `docs/poc/poc-lesson-split-design.html`; checker `audit/curriculum-upgrade/pilot-things-have-gender/{verify_pilot.py, browser_check.mjs}` (baseline pinned to commit 7829e74b; run from the worktree root; `VERIFY_OUT=` redirects the report).
- Head 4ca001d2: VERIFY_PILOT PASS, BROWSER_CHECK PASS. Cross-family content review (Codex, `batch_state/tasks/cu-p0-pr7991-content-review-codex.result`) = **REQUEST-CHANGES** (unintroduced words вдо́ма/там/нова́ су́мка; ambiguous act-102/301/304/306; A1 stem length in act-203/303; translate bonuses unmarked; vocabulary first-use allocation; resources lack chunk_ids; inherited-prose findings → plan level).
- **In flight:** AGY repair pass, task `cu-p0-pilot-writer-things-have-gender` (run 9cafc72f), brief `docs/dispatch-briefs/2026-09-12-cu-p0-pilot-repair-brief.md`. When terminal: re-run both proofs at the new head, dispatch Codex re-review at that exact head (brief `…-content-review-brief.md`), route `NOTES.md §6` plan-level findings to plan review. PR stays a draft until operator design sign-off; nothing deploys.
- Lessons for the machinery (in #7994 body): writer-placed stress marks were 29× wrong → annotator + correctness gate; homograph readings need a proper-name policy (Марко́ vs Ма́рко, стіна́ vs Сті́на); odd-one-out renderer gap; added UK passages ≥3 sentences need side-by-side support; dialogues as blockquotes.

## Next for the machinery driver (#7994)
1. Write `docs/epics/curriculum-upgrade-phase1-spec.md` (lesson plan derivation from `content_outline` + `lessons.yaml` schema; `a1-v2` level with `base_level: a1` config alias + site collection glob; per-lesson learner state; gates ported from `verify_pilot.py` into `python_qg`; assembler landing + `<n>.mdx` + nav + `LevelLanding` counters; `verify_shippable --lesson`; upgrade-mode writer/reviewer prompts). Freeze SHA-256; two independent critics (Codex + AGY) before dispatch.
2. Dispatch Codex slices (a)–(f) per #7994; cross-family review at exact head; CI green; enqueue.
3. Acceptance: pipeline upgrade mode on `things-have-gender` passes the Phase 0 checker.

## Artifacts (claude.ai)
Design mockup `912272b0-324d-4691-af08-9d731603c88f` · rendered pilot `43e22462-fa81-43ec-bb34-24cc1fc3f121`.
