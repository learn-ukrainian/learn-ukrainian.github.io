# Claude Brief — #1412 Review-and-lock at-the-cafe wiki + plan as A1/A2 template

**Issue:** https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/1412
**Task ID:** `claude-1412-at-the-cafe-lock`
**Worktree:** `.worktrees/claude-1412-at-the-cafe-lock`
**Branch:** `claude/claude-1412-at-the-cafe-lock`
**Effort:** xhigh
**Model:** claude-opus-4-7
**Hard timeout:** 7200s

## Why this matters

Read the issue body in full — it's the canonical spec. TL;DR:

A.8 canary needs clean inputs. at-the-cafe wiki is 8/10 with documented gaps; at-the-cafe plan has `<unset>` lifecycle and was never formally reviewed. Running A.8 against these contaminates the signal. Lock both inputs to 9+/10 + LOCKED state, document the rubric, ship a template the rest of A1+A2 can follow.

## Worktree instructions (mandatory)

    git worktree add -b claude/claude-1412-at-the-cafe-lock .worktrees/claude-1412-at-the-cafe-lock
    cd .worktrees/claude-1412-at-the-cafe-lock

DO NOT branch in main checkout.

## Hard prohibitions

1. **DO NOT MERGE the PR yourself.** Open it only.
2. **DO NOT use `gh pr merge` / `--admin` / `gh pr review --approve`.**
3. **DO NOT touch other slugs' wikis or plans.** at-the-cafe ONLY for this PR. Scope discipline is load-bearing — the rubric template is for OTHERS to apply, not for this PR to apply 53 times.
4. **DO NOT invent café vocab.** Every word added to the wiki or plan vocabulary_hints MUST verify in VESUM. Use `mcp__sources__verify_word` or `mcp__sources__verify_lemma`. If verification fails, do NOT include the word; flag with `<!-- VERIFY -->` instead.
5. **DO NOT skip plan-side review** (AC-2). It's tempting to focus on the wiki since it has more visible gaps, but the plan side is the part that's never been reviewed at all. The plan is potentially more contaminated than the wiki.
6. **DO NOT add lifecycle fields to the plan YAML without checking the schema.** Find the plan schema first (likely under `scripts/audit/schemas/` or `curriculum/l2-uk-en/schemas/` or similar). Either fit existing fields OR document the schema addition explicitly in the PR body.
7. **DO NOT skip MCP source verification.** Use `mcp__sources__search_text`, `mcp__sources__search_style_guide` (Антоненко-Давидович — calques + Russianisms), `mcp__sources__verify_word`/`verify_lemma`, `mcp__sources__query_pravopys`, `mcp__sources__search_definitions` (СУМ-11). The whole point is that the locked artifact is verified, not just LLM-asserted.

## Read before coding (mandatory)

- **Issue body in full** — https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/1412 (the canonical AC list)
- `wiki/pedagogy/a1/at-the-cafe.md` — current wiki state
- `wiki/pedagogy/a1/at-the-cafe.sources.yaml` — sidecar citation registry
- `wiki/.reviews/pedagogy/a1/at-the-cafe-review-final.md` — the 8/10 final review with `<fixes>` block (much of AC-1 is applying these fixes)
- `wiki/.reviews/pedagogy/a1/at-the-cafe-review-r1.md`, `-r2.md`, etc. — review history if you need context on what was already addressed
- `curriculum/l2-uk-en/plans/a1/at-the-cafe.yaml` — the plan to review-and-lock
- `curriculum/l2-uk-en/plans/a1/checkpoint-first-contact.yaml` — fixed today via #1393, useful for understanding plan structure + recent corrections
- `gh issue view 1392 --json body` — the plan-audit issue with the systemic defects (Latin M## refs CLOSED via #1393, pragmatic imprecisions PARTIALLY ADDRESSED — verify what was actually fixed)
- `.claude/rules/non-negotiable-rules.md` — Hard Rules (esp. word targets, audit gates, cite-or-hedge)
- `.claude/rules/ukrainian-linguistics.md` — Russianism / Surzhyk / calque / paronym detection
- `.claude/rules/mcp-sources-and-dictionaries.md` — MCP tool usage

## Acceptance criteria (full text in issue body — summary here)

- **AC-1:** at-the-cafe wiki to ≥9/10 across all 5 dims. Apply reviewer fixes + close 2 named gaps (modern café vocab, café-specific Surzhyk table). Re-review and emit LOCKED review file.
- **AC-2:** at-the-cafe plan reviewed (pragmatic + Russianism + calque + contradiction + references). Apply or VERIFY-flag findings. Add lifecycle markers. Mark LOCKED.
- **AC-3:** `docs/best-practices/wiki-plan-review-and-lock.md` rubric template documenting the full process with at-the-cafe as worked example.
- **AC-4:** Adversarial review (Gemini) before PR.

## Suggested workflow

1. Create worktree per worktree instructions
2. Read the 8 files in "Read before coding" — DO NOT skip the review history
3. **AC-1 first** (wiki) — apply existing reviewer fixes, then close gaps, then re-review. ~2-3 commits worth of work.
4. **AC-2** (plan) — adversarial review the plan, apply fixes, add lifecycle markers. ~1-2 commits.
5. **AC-3** (rubric doc) — write the template doc with at-the-cafe as the worked example. ~1 commit.
6. **AC-4** — Gemini adversarial review:
   ```bash
   .venv/bin/python scripts/ai_agent_bridge/__main__.py ask-gemini \
     "Adversarial review of #1412 review-and-lock for at-the-cafe wiki + plan. Read the diff. Look for: (1) wiki fixes that introduce NEW gaps while closing documented ones, (2) lifecycle field naming colliding with existing plan schema fields, (3) plan-review checklist missing categories that #1392 would have caught, (4) the rubric doc drifting from what was actually applied to at-the-cafe (the worked example must match the rubric step-for-step), (5) hallucinated café vocab not verifiable in VESUM (the new Surzhyk-table 'right' column items must verify)." \
     --task-id 1412-review --model gemini-3.1-pro-preview
   ```
7. Address findings. If Gemini's review surfaces non-trivial issues, do a second round with the fixes applied.
8. Push, open PR with title `feat(quality): review-and-lock at-the-cafe wiki + plan + rubric template (#1412)`
9. STOP. Do not merge.

## PR body template

```
## Summary
Locks at-the-cafe (L2-UK-EN A1/M18) wiki + plan to 9+/10 + LOCKED state, unblocking A.8 canary. Establishes the review-and-lock rubric template the remaining 53 A1 wikis + plans (then A2) will follow.

- AC-1: Wiki reviewer fixes applied + 2 documented gaps closed (modern café vocab, café-specific Surzhyk table). Re-review final score: <X>/10 across 5 dims.
- AC-2: Plan reviewed for pragmatic / Russianism / calque / contradiction. Findings: <list>. Applied + LOCKED with lifecycle markers (note: schema addition documented below).
- AC-3: docs/best-practices/wiki-plan-review-and-lock.md — rubric + worked example.
- AC-4: Gemini adversarial review (N rounds) — findings addressed.

Closes #1412. Unblocks A.8 (docs/architecture/a8-canary-protocol.md). Template ready for A.9 scale.

## Schema addition
Added `lifecycle`, `reviewed_at`, `reviewed_by`, `review_notes` fields to the plan YAML. Either: (a) extends existing schema, or (b) net-new fields documented in <schema-file>.

## Test plan
- [ ] Manual diff review on the wiki — every new vocab item verified in VESUM
- [ ] Manual diff review on the plan — every fix matches a specific finding from the review pass
- [ ] `cat curriculum/l2-uk-en/plans/a1/at-the-cafe.yaml | yq '.lifecycle'` returns `locked`
- [ ] Read docs/best-practices/wiki-plan-review-and-lock.md as if you were going to apply it to a NEW slug — is the procedure clear and unambiguous?

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

## Done when

PR opened, all 4 ACs documented, wiki re-review file present, plan has lifecycle markers, rubric doc present, Gemini adversarial review noted. User merges. Then A.8 canary is unblocked AND the next 53 A1 wikis + plans have a clear template to follow.
