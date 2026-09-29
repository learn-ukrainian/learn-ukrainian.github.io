# Rules core draft — notes

Draft: `agents_extensions/shared/rules/core.md`. No other rule file changes; loading, slimming and
migration are Phase C.

## Conflicts between sources

1. **DeepSeek.** The spec asks for "no DeepSeek" with no scope. The core bans it only on Ukrainian,
   folk and approval-authority seats. `deepseek-v4.1-flash` is active in the catalog, is on every
   `review_ladders` rung, and `model-assignment.md` routes it for review volume. A fleet-wide ban
   changes model assignment (a spec non-goal) and needs a decision first.
2. **Grok 4.6.** `model-assignment.md` allows explicit pins. The catalog notes say it is not
   admitted, but its `lifecycle` is `active`.
3. **Daily driver.** `model-assignment.md` § Orchestration operating pattern names `grok-4.7`.
   `fleet-role-scorecard.md` §1 names Sol and Opus 5.5. The core puts Sol and Opus 5.5 first and
   Grok as fallback.
4. **Stress tool.** `ukrainian-linguistics.md` facet table: `query_sum20`, no `verify_stress`.
   `mcp-sources-and-dictionaries.md` calls `verify_stress` the stress oracle. The core lists both.
5. **Stale lines in `MEMORY.md`.**
   - #0H: `--auto` merge after review. The landing order forbids `--auto`.
   - #M-0.5: "ask for direction" on red CI. Conflicts with operator-expectations item 10.
   - #M0 and #0: the 3:3:3 split still sends code work to Gemini.
   - `ask-opencode` is listed but retired.
6. **Delegate brief example.** `delegate-must-use-worktree.md` still shows a `claude-opus-4-8`
   dispatch.

## Not placed in the core

- **Content-seat addendum** (pedagogy, word minimums, immersion except A1, activities test
  language). The spec loads it for curriculum seats only, so it gets its own file in Phase C. Until
  then the "Curriculum" load-when row reaches it.
- **Reference material that stays in `model-assignment.md`:** panel sizing, Cursor attestation,
  transport details, and the ladders beyond first pick and fallback.
- **The Phase A inventory.** Its run ended before producing the table, so this draft was built from
  the sources directly. The zero-lost-obligations proof still needs it.

## `new:` obligations (spec is the only source)

- A SKIPPED cleanup row needs a disposition.
- Review worktrees are removed after the verdict.
- An issue is never a running log.
- Issue disposition at merge.
- Infra-lane emergency action on other lanes.
- The OPSEC publishable/private split.
- Handoff lines are to-dos, and lessons are written before ending.
- Decolonization binds tools and data.

## Mechanical changes

- `scripts/deploy_orphan_paths.sh`: `core.md` stays out of Claude autoload, like the other
  unscoped rules, with a matching deploy-test entry. How the core loads per harness is Phase C (R1).
- `tests/test_sum11_source_guard.py`: one approved contrast-only core line.
- `tests/test_rules_core_budget.py`: checks the byte budget, one heading per pillar, and that every
  P2 model id is active in the catalog.
