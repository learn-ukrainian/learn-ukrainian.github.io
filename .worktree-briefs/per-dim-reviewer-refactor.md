# Codex Brief — Per-dimension independent v6 reviewer + MIN-score aggregator

**Task ID:** `codex-per-dim-reviewer-refactor`
**Worktree:** `.worktrees/codex-per-dim-reviewer`
**Branch:** `codex/per-dim-reviewer-refactor`
**Hard timeout:** 10800s (3h — substantial refactor + tests)

## Why

User policy 2026-04-23 (codified in `.claude/rules/non-negotiable-rules.md` §5):

> Each review dimension runs as an INDEPENDENT model call with its own strict persona — no single-pass multi-dim bundling. Aggregator takes MIN, not weighted average. **Do NOT design new review prompts that bundle dims into one pass with a weighted average — that pattern is rejected.**

Current state: v6 reviewer (single pass scoring N dims, weighted-average verdict) is the OLD pattern. Needs refactor before A.8 canary can give a meaningful signal — otherwise we're measuring the wiki bootstrap against a yardstick the user has explicitly rejected.

Persona reference: **`docs/best-practices/strict-reviewer-persona.md`** — read in full. Adapt the tutor voice to a HARSH reviewer voice for each dim.

## Worktree instructions (mandatory)

    git worktree add -b codex/per-dim-reviewer-refactor .worktrees/codex-per-dim-reviewer
    cd .worktrees/codex-per-dim-reviewer

DO NOT branch in main checkout.

## Hard prohibitions

1. **DO NOT MERGE the PR yourself.** Open PR only.
2. **DO NOT use `gh pr merge` / `--admin` / `gh pr review --approve`.**
3. **DO NOT use `ask-gemini` for adversarial review** (Keychain block — use `ask-claude`).
4. **DO NOT change writer prompts or build phases beyond review** — refactor is review-only.
5. **DO NOT keep the weighted-average code path "for backwards compat"** — the user explicitly rejected it. Delete it.
6. **DO NOT bundle multiple dims into one prompt** — even as a "fast path" for cheap modules. Each dim independent.
7. **DO NOT branch in main checkout.**

## Read before coding (mandatory)

- **`docs/best-practices/strict-reviewer-persona.md`** — the persona + per-dim/MIN architecture spec
- **`.claude/rules/non-negotiable-rules.md` §5** — the canonical rule (already updated 2026-04-23)
- **`scripts/build/phases/v6-review.md`** — current single-pass review prompt (the file you're refactoring)
- **`scripts/build/v6_build.py`** — find the review-phase orchestration (likely around `phase_review` or similar). Identify: where the review prompt is loaded, where the model is invoked, where `<fixes>` are parsed, where the verdict is computed.
- **Current dim list** — extract from existing v6-review.md. There are ~9 dims (factual, language, decolonization, completeness, actionable, naturalness, plan_adherence, honesty, dialogue_quality — verify by reading the file).
- **`.claude/rules/ukrainian-linguistics.md`** — Russianism / Surzhyk / calque / paronym detection rules (some dims will reference these)

## Architecture spec

### Per-dim prompts

Create `scripts/build/phases/v6-review/` directory containing:

- `v6-review-factual.md` — strict reviewer for factual accuracy. Cite sources (Грінченко for etymology, СУМ-11 for definitions, Wikipedia for facts). Single fabrication = max 5/10.
- `v6-review-language.md` — strict reviewer for Ukrainian language quality. Apply zero-tolerance to Russianisms / Surzhyk / calques. ANY hit = max 6/10. Cite Антоненко-Давидович.
- `v6-review-decolonization.md` — strict reviewer for decolonization register. Russian-tradition framings (e.g., "like Russian but...", "as in Russian") = max 5/10.
- `v6-review-completeness.md` — strict reviewer for plan-adherence completeness. Every contract item present = 9+; missing items deduct.
- `v6-review-actionable.md` — strict reviewer for actionable pedagogy. Generic advice ("teach it well") = max 5/10. Specific examples / sequences / exercises = 9+.
- `v6-review-naturalness.md` — strict reviewer for natural Ukrainian prose. Robotic / textbook-drill = max 6/10.
- `v6-review-plan-adherence.md` — strict reviewer for plan vs output match. Plan says X, output should have X.
- `v6-review-honesty.md` — strict reviewer for honesty (Hard Rule #11 from v6-write.md). Invented examples without `<!-- VERIFY -->` = max 5/10.
- `v6-review-dialogue.md` — strict reviewer for dialogue authenticity. Drills disguised as conversation = max 6/10.

(Confirm exact dim list against current `v6-review.md` before creating files. If existing file has 9 dims with different names, mirror those names.)

Each prompt:
- Adopts the strict-reviewer persona (zero-tolerance, bilingual where helpful, source hierarchy citations, honesty-first)
- Scores ITS dimension only (1-10)
- Outputs a `<fixes>` block scoped to its dim
- DOES NOT score other dims (single-responsibility)
- Cites specific evidence from the content (per non-negotiable rule §6)

### v6_build.py orchestration

Refactor the review phase to:

1. **Fan out** N review calls in parallel (one per dim, via ThreadPoolExecutor or similar)
2. **Collect** per-dim scores + `<fixes>` blocks
3. **Aggregate** with MIN: `verdict_score = min(dim_scores)`
4. **Verdict logic** (threshold per user 2026-04-23, MIN ≥ 8 = PASS):
   - All dims ≥8 → PASS
   - Any dim 6.0-7.99 → REVISE (apply that dim's fixes, re-fan-out review)
   - Any dim <6 → REJECT (re-plan or re-write needed)
5. **Apply fixes** from ALL dims in one pass (deterministic find/replace per existing pattern)
6. **Persist** per-dim review files: `curriculum/l2-uk-en/{level}/review/{slug}-review-{dim}-{round}.yaml`

### Aggregator output schema

Save aggregated verdict to `curriculum/l2-uk-en/{level}/review/{slug}-review-aggregate.yaml`:

```yaml
slug: at-the-cafe
round: 1
verdict: PASS  # or REVISE / REJECT
verdict_score: 9.2  # = min(dim_scores)
weighted_average: 9.4  # informational only — NOT used for verdict
dim_scores:
  factual: 9.5
  language: 9.2  # the min — drove the verdict
  decolonization: 10.0
  completeness: 9.8
  actionable: 9.3
  naturalness: 9.4
  plan_adherence: 9.6
  honesty: 9.5
  dialogue: 9.4
fixes_applied:
  - dim: language
    count: 3
    files: [at-the-cafe.md]
  ...
```

## Acceptance criteria

### AC-1 — Per-dim prompt files
9 prompt files under `scripts/build/phases/v6-review/`, each with the strict persona adapted to its dim. Each cites the source hierarchy where relevant. Each scores 1-10 with explicit penalty caps.

### AC-2 — v6_build.py refactored
Review phase fans out per-dim calls, collects, aggregates with MIN. Old single-pass code path deleted (NOT kept for backwards compat). Per-dim review YAML files written to `curriculum/l2-uk-en/{level}/review/`.

### AC-3 — Aggregator
MIN-based verdict. Aggregate YAML schema as above. Weighted-average calculated for INFO only, never used for verdict.

### AC-4 — Tests
`tests/test_v6_review_per_dim.py` covers:
- Fan-out: 9 dims dispatched in parallel
- Aggregation: MIN computed correctly (single low dim drives verdict)
- Verdict mapping: 9-10 → PASS, 7-8.99 → REVISE, <7 → REJECT
- Fix collection: fixes from all dims gathered into one apply pass
- Bilingual cite parsing: review YAML correctly parses Ukrainian-first findings

### AC-5 — Migrate the audit gate
`.claude/rules/non-negotiable-rules.md` §5 says MIN-score is the gate. Verify the audit code (probably in `scripts/audit/`) reads the aggregate YAML's `verdict_score` (the MIN), not a re-computed average. Update if needed.

### AC-6 — Adversarial review (cross-agent, NOT Gemini)

```bash
.venv/bin/python scripts/ai_agent_bridge/__main__.py ask-claude \
  "Adversarial review of per-dim independent v6 reviewer refactor (#?). Read the diff. Look for: (1) per-dim prompts that secretly score multiple dims (single-responsibility violation), (2) weighted-average code path still alive somewhere as a fallback (the user explicitly rejected this), (3) aggregator that takes MAX or AVG instead of MIN under any condition, (4) fan-out that's actually serial (no real parallelism), (5) per-dim prompts that don't cite the source hierarchy where applicable, (6) bilingual finding format breaking the existing fixes-parser, (7) audit gate still reading old single-score field." \
  --task-id per-dim-reviewer-review
```

Address findings or document rejections in PR body.

## Workflow

1. Create worktree
2. READ all files in "Read before coding" — understand current v6-review.md dim list + v6_build.py review phase BEFORE designing
3. Implement AC-1 → AC-2 → AC-3 → AC-4 → AC-5 (commit per AC)
4. Run AC-6 adversarial review
5. Push, open PR titled `feat(v6): per-dim independent reviewer + MIN-score aggregator (strict persona, user policy 2026-04-23)`
6. STOP. Do not merge.

## PR body template

```
## Summary
Refactors v6 review phase from single-pass weighted-average to per-dim independent + MIN-score aggregator, per user policy 2026-04-23 (`.claude/rules/non-negotiable-rules.md` §5).

- AC-1: 9 per-dim prompt files under `scripts/build/phases/v6-review/`, each adopting strict-reviewer persona (`docs/best-practices/strict-reviewer-persona.md`)
- AC-2: v6_build.py review phase fans out, collects, aggregates with MIN. Old single-pass code path DELETED (no backwards-compat fallback per policy)
- AC-3: aggregate YAML schema with `verdict_score = min(dim_scores)`. Weighted average calculated for info only.
- AC-4: tests cover fan-out, aggregation, verdict mapping (PASS ≥8 / REVISE 6-7.99 / REJECT <6), fix collection, bilingual cite parsing
- AC-5: audit gate updated to read aggregate `verdict_score` (the MIN)
- AC-6: cross-agent adversarial review (Claude) — N findings addressed

## Why (not "what")
User has had to re-explain this architecture multiple times. Now codified in always-loaded rules. Single failing dim now correctly fails the module instead of being papered over by a weighted average.

## Test plan
- [ ] `pytest tests/test_v6_review_per_dim.py -v` — all green
- [ ] Smoke: re-run review on a previously-PASSED at-the-cafe build → verdict matches MIN-score expectation
- [ ] Smoke: simulate a "language: 6, others: 9.5" case → verdict = REVISE driven by language dim, not papered over

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

## Done when

PR opened, all 6 ACs documented, adversarial review noted, dispatch reports `done`. After merge, A.8 canary becomes meaningful.
