# Claude Brief — #1282 Improve section excerpt selection for scenario-specific wiki context

**Issue:** https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/1282
**Task ID:** `claude-1282-excerpt-selection`
**Worktree:** `.worktrees/claude-1282-excerpt-selection`
**Branch:** `claude/claude-1282-excerpt-selection`
**Effort:** xhigh
**Model:** claude-opus-4-7
**Hard timeout:** 5400s

## Why this matters

Right now even when the repo has scenario-specific wiki articles (e.g., `wiki/pedagogy/a1/at-the-cafe.md`), the contract/excerpt builder for `A1/M18` Dialogues section surfaces generic overview excerpts from `i-want-i-can` / `i-eat-i-drink` instead of the café-specific article. Result: writer/rewrite quality is bottlenecked by retrieval, not by the LLM.

This is a quality-lever fix — we already have the right material; we just need the selector to pick it.

**Tonight's broader context:** there's a separate dispatch in flight (#1410, `codex-wire-ukrainian-wiki-mcp`) that exposes the `ukrainian_wiki` corpus to writers via a new MCP tool. Once that lands, this excerpt-selection fix amplifies its value — together they make the wiki bootstrap actually flow into module quality.

## Worktree instructions (mandatory)

    git worktree add -b claude/claude-1282-excerpt-selection .worktrees/claude-1282-excerpt-selection
    cd .worktrees/claude-1282-excerpt-selection

DO NOT branch in the main checkout.

## Hard prohibitions

1. **DO NOT MERGE the PR yourself.** Open it only.
2. **DO NOT use `gh pr merge` / `--admin` / `gh pr review --approve` for any reason.**
3. **DO NOT wait on or merge in #1410 (the parallel wire-up dispatch).** Stay scoped to excerpt selection — the two land independently.
4. **DO NOT change selection from deterministic to non-deterministic.** Determinism + inspectability is an explicit AC.
5. **DO NOT branch in main checkout.**

## Read before coding

- **Issue body in full** — https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/1282 — the AC list.
- The current excerpt builder. Find via `grep -rn "wiki-excerpts\|wiki_excerpts\|excerpt_selection\|build_packet\|knowledge_packet" scripts/ | head`. Likely lives in `scripts/research/build_knowledge_packet.py` or `scripts/build/research/build_knowledge_packet.py` or `scripts/wiki/`.
- Sample artifact: `wiki/pedagogy/a1/at-the-cafe.md` and the existing `wiki-excerpts.yaml` for `A1/M18` (path: probably under `curriculum/l2-uk-en/a1/orchestration/at-the-cafe/` or similar — but NOTE that orchestration/ was just cleaned up in `8aa69ff268` so check current state).
- The `at-the-cafe` plan YAML at `curriculum/l2-uk-en/plans/a1/at-the-cafe.yaml` to see what scenario/setting cues are available.

## Acceptance criteria (from #1282)

- AC-1: Excerpt selection logic uses scenario/setting cues from the plan when ranking section wiki excerpts
- AC-2: `A1/M18` Dialogues section successfully surfaces café-specific material from `at-the-cafe.md`
- AC-3: Selection remains deterministic and saved in orchestration artifacts
- AC-4: Regression test for at least one scenario-specific selection case
- AC-5: Adversarial review (Gemini) before opening PR. Run:

```bash
.venv/bin/python scripts/ai_agent_bridge/__main__.py ask-gemini \
  "Adversarial review of #1282 excerpt-selection improvement. Read the diff. Look for: (1) over-fitting to A1/M18 — does the selector generalize, (2) ranking heuristic that's brittle to plan-YAML schema changes, (3) determinism actually broken under threading or dict ordering, (4) regression test only covers happy-path café case but misses generic-fallback when no scenario match exists, (5) over-promotion of scenario-specific articles drowning out useful generic context." \
  --task-id 1282-review --model gemini-3.1-pro-preview
```

Address findings. Document any rejected with rationale.

## Workflow

1. Create worktree per worktree instructions
2. Read issue body + current excerpt-builder code BEFORE designing the fix
3. Implement AC-1 → AC-2 → AC-3 → AC-4 (commit per AC or one combined)
4. Run AC-5 adversarial review
5. Push, open PR with title `feat(retrieval): scenario-aware section excerpt selection (#1282)`
6. STOP. Do not merge.

## PR body template

```
## Summary
Improves wiki excerpt selection for sections whose plan/scenario clearly maps to a specific wiki article (e.g., A1/M18 Dialogues → at-the-cafe.md). Selection stays deterministic + inspectable.

- AC-1: scenario/setting cues from plan now feed excerpt ranking
- AC-2: A1/M18 Dialogues surfaces at-the-cafe.md (verified in artifact)
- AC-3: Determinism preserved; orchestration artifact captures selection trace
- AC-4: Regression test covers at-the-cafe scenario match
- AC-5: Adversarial review (Gemini) — N findings addressed

Closes #1282.

## Test plan
- [ ] `.venv/bin/pytest tests/test_excerpt_selection*.py -v` — all green
- [ ] Manual: rebuild A1/M18 packet, inspect wiki-excerpts.yaml — café content present in Dialogues section
- [ ] Manual: rebuild any non-scenario-matching slug, confirm fallback to generic excerpts works

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

## Done when

PR opened, all 5 ACs documented, adversarial review noted, dispatch reports `done`. User merges.
