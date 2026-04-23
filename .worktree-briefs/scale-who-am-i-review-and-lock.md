# who-am-i — review-and-lock per #1412 rubric template

**Task ID:** `scale-who-am-i-review-and-lock`
**Worktree:** `.worktrees/scale-who-am-i`
**Branch:** `agent/scale-who-am-i`
**Hard timeout:** 5400s

## Why

PR #1415 shipped at-the-cafe as the worked example for the review-and-lock procedure. `docs/best-practices/wiki-plan-review-and-lock.md` is the canonical rubric. This dispatch applies it to **who-am-i**.

This is part of the overnight scale batch (4 A1 slugs in parallel) toward A1 ship-readiness per EPIC #1365 Phase 2 Track A.

## Worktree instructions (mandatory)

    git worktree add -b agent/scale-who-am-i .worktrees/scale-who-am-i
    cd .worktrees/scale-who-am-i

DO NOT branch in main checkout.

## Hard prohibitions

1. **DO NOT MERGE the PR yourself.** Open PR only.
2. **DO NOT use `gh pr merge` / `--admin` / `gh pr review --approve`.**
3. **DO NOT use `ask-gemini` for adversarial review** — Keychain popup loop blocks the user's session (#1416 mitigation: always use `ask-codex` for cross-agent review of Claude-side work, or `ask-claude` for review of Codex-side work).
4. **DO NOT touch other slugs' wikis or plans.** This dispatch = who-am-i ONLY.
5. **DO NOT invent vocabulary.** Every word added MUST verify in VESUM via `mcp__sources__verify_word` or `mcp__sources__verify_lemma`.
6. **DO NOT skip plan-side review.** The plan's pragmatic / Russianism / calque audit is non-negotiable per the rubric.
7. **DO NOT add lifecycle fields without checking the schema** — at-the-cafe (PR #1415) extended the schema with `lifecycle`, `reviewed_at`, `reviewed_by`, `review_notes`. Match those.

## Read before coding (mandatory)

- **The rubric doc**: `docs/best-practices/wiki-plan-review-and-lock.md` — full procedure with at-the-cafe as worked example
- **at-the-cafe shipped artifacts** (the template you're following):
  - `wiki/pedagogy/a1/at-the-cafe.md`
  - `curriculum/l2-uk-en/plans/a1/at-the-cafe.yaml`
  - `wiki/.reviews/pedagogy/a1/at-the-cafe-review-LOCKED.md`
- **Your slug's current state**:
  - `wiki/pedagogy/a1/who-am-i.md`
  - `wiki/pedagogy/a1/who-am-i.sources.yaml`
  - `curriculum/l2-uk-en/plans/a1/who-am-i.yaml`
  - `wiki/.reviews/pedagogy/a1/who-am-i-review*.md` (if prior reviews exist — read all)
- `.claude/rules/non-negotiable-rules.md` (Hard Rules)
- `.claude/rules/ukrainian-linguistics.md` (Russianism / Surzhyk / calque / paronym)
- `.claude/rules/mcp-sources-and-dictionaries.md` (MCP tool reference)

## Acceptance criteria (per the rubric template)

### AC-1 — Wiki to ≥9/10 across 5 dimensions
Apply prior reviewer fixes (if any `<fixes>` blocks exist in prior review files), then close any documented gaps. Re-review and emit `wiki/.reviews/pedagogy/a1/who-am-i-review-LOCKED.md` with final 5-dimension scores (factual, language, decolonization, completeness, actionable, all ≥9).

### AC-2 — Plan REVIEWED + LOCKED
- Adversarial-review the plan for: pragmatic context-blindness (#1392 Defect 2 patterns), Russianisms in plan prose (`приймати ліки` / `Давайте` / etc.), calques in vocabulary_hints, plan-internal contradictions
- Apply or VERIFY-flag findings
- Add lifecycle markers matching at-the-cafe schema:
  ```yaml
  lifecycle: locked
  reviewed_at: '2026-04-23T<timestamp>Z'
  reviewed_by: '<agent-id>-who-am-i'
  review_notes: 'See PR body for findings + fixes'
  ```

### AC-3 — Adversarial review (cross-agent, NOT Gemini)

```bash
# Pick the cross-agent: if you are Claude, call codex; if you are Codex, call claude.
.venv/bin/python scripts/ai_agent_bridge/__main__.py ask-codex \
  "Adversarial review of review-and-lock for who-am-i. Read the diff in this branch. Apply the same 5 risk vectors from #1412 adversarial review (wiki gaps reintroduced, lifecycle field naming, plan-review checklist completeness, rubric-doc drift, hallucinated vocab). Report BLOCKER / MEDIUM / NIT bullets with file:line + concrete fix." \
  --task-id who-am-i-adv-review
```

If `ask-codex` is unavailable, use `ask-claude` instead (Claude reviewing Codex-side work). DO NOT use `ask-gemini`.

Address findings or document rejections in PR body.

## Workflow

1. Create worktree per worktree instructions
2. Read all "Read before coding" files (rubric doc + at-the-cafe template + your slug's current state + rules)
3. AC-1 (wiki) → 1-2 commits
4. AC-2 (plan) → 1 commit
5. AC-3 (adversarial review) → address findings → maybe 1 fix commit
6. Push, open PR with title `feat(quality): review-and-lock who-am-i wiki + plan (scale batch 1)`
7. STOP. Do not merge.

## PR body template

```
## Summary
Locks who-am-i (L2-UK-EN A1) wiki + plan to 9+/10 + LOCKED state per the #1412 rubric template (`docs/best-practices/wiki-plan-review-and-lock.md`).

- AC-1 (wiki): final 5-dim scores: <X>/<Y>/<Z>/<W>/<V>. Fixes applied: <list>. Gaps closed: <list>.
- AC-2 (plan): findings: <list>. Lifecycle markers added.
- AC-3 (cross-agent adversarial review): N findings addressed, M documented rejections.

Part of overnight scale batch 1 (alongside food-and-drink, who-am-i, sounds-letters-and-hello).

## Test plan
- [ ] `yq '.lifecycle' curriculum/l2-uk-en/plans/a1/who-am-i.yaml` returns `locked`
- [ ] All vocab in wiki verifies in VESUM
- [ ] Re-read `docs/best-practices/wiki-plan-review-and-lock.md` against this PR — every step matches the rubric

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

## Done when

PR opened, all 3 ACs documented, adversarial review noted (cross-agent, NOT Gemini), dispatch reports `done`. User reviews + merges in the morning.
