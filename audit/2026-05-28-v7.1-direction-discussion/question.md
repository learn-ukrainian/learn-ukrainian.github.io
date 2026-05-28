# V7.1 vs V7-hardened — direction discussion (2026-05-28 morning)

You are being asked a strategic direction question about the V7.1 pivot the team committed to two days ago. Read the three concrete artifacts referenced below before answering. Ground your reasoning in what those artifacts actually show, not in abstract framing.

## Where we are

The team signed off **V7.1 Option 1** on 2026-05-28 (per `docs/decisions/pending/2026-05-27-v7.1-wiki-driven-writer.md`): structural refactor of `linear-write.md` to charter-first renderer framing + wiki vocab allowlist + upstream `wiki_completeness_gate`. PR #2377 (Day 1 charter) and PR #2379 (Day 2 gate + manifest + allowlist) both landed.

Tonight's pilot exposed four V7.1 regressions (issue #2380):

1. **Pipeline silent-exit** between phases (no `module_done`, no error event). Both V7.1 builds tonight exited silently before MDX assembly. Likely from PR #2379's `v7_build.py` +46/-3 diff.
2. **Activity schema-field drift** — V7.1 writer emits `translate` items with `prompt`/`answer` instead of canonical `source`/`target`. MDX assembly fails: `ValueError: Failed to parse activity 7 type='translate': 'source'`.
3. **Tone REJECT 3.0** under V7.1 charter (down from Pt 10's clean tone). The V7.1 renderer-charter weakened `#R-AUDIENCE-LANGUAGE-A1` — claude-tools slipped UK metalanguage into A1 EN prose (`або -сь після голосних`, `наприклад`, `поява вставного «л»`).
4. **Codex tool-call regression** 20 → 4 (–80%). Same model (gpt-5.5), same effort. V7.1 charter or Day-2 gate changes are starving codex's corpus utilization.

The pipeline regressions (1+2) block both writers from producing comparable MDX. So we have NO clean V7.1 result to compare against the Pt 10 baseline.

## Three concrete m20 artifacts to read

All three are `module.md` source files (the Markdown body of the lesson before MDX assembly). Read them as a human learner would.

1. **`/tmp/pt10-baseline-module.md`** (152 lines, 10.1KB) — Pt 10's 9.5/10 baseline.
   - Writer: **codex-tools** (gpt-5.5, workspace-write, 282.85s + 60.37s correction round) — definitively confirmed from the preserved Pt 10 worktree's `batch_state/api_usage/usage_codex-dispatch_2026-05-27.jsonl`.
   - Pipeline version: **V7-hardened** (post PR #2371 wiki_coverage per-item gate, BEFORE V7.1 charter)
   - 20 tool calls across 8 distinct sources tools (query_cefr_level ×6, check_modern_form ×4, check_russian_shadow ×3, etc.)
   - llm_qg aggregate 9.5/10 PASS. Single gate fail was `word_count` 1058 < 1104 (Path B / PR #2372 addressed that gate threshold).

2. **`/tmp/v71-claude-module.md`** (143 lines, 13.2KB) — V7.1-claude pilot.
   - Writer: **claude-tools** (Claude Opus 4.7, 493s)
   - Pipeline version: **V7.1** (Day 1 charter + Day 2 gate)
   - 12 tool calls, 4/4 sections with CoT, 0 tool theatre. wiki_completeness_gate PASSED (21/20 vocab). wiki_coverage_gate ran 2 correction iterations.
   - llm_qg: decolonization 10.0 PASS, engagement 9.5 PASS, pedagogical 7.5 REVISE, naturalness 7.5 REVISE, **tone 3.0 REJECT**.
   - Tone reviewer's 3 evidence quotes (all UK-metalanguage-in-EN slips): `(або -сь після голосних)`, `наприклад, користуватися або одружуватися`, `(наприклад, дивитися в дзеркало... поява вставного «л»)`.

3. **`/tmp/v71-codex-module.md`** (113 lines, 9.8KB) — V7.1-codex pilot.
   - Writer: **codex-tools** (gpt-5.5, 285s)
   - Pipeline version: **V7.1** (Day 1 charter + Day 2 gate)
   - **4 tool calls only** (vs Pt 10 baseline's 20 — same writer, same model). 4/4 sections with CoT, 0 tool theatre.
   - Did NOT reach wiki_coverage_gate or llm_qg — pipeline regression 1 fired right after python_qg.
   - No tone score available; quality is unverified.

## The question

Given the empirical evidence above, what is the right next step?

### Option A: Keep grinding V7-hardened

Roll back V7.1 PRs #2377 (charter) + #2379 (gate/manifest/allowlist). Resume the V7-hardened pipeline that delivered Pt 10's 9.5/10 with codex-tools. Address word_count via the Path B PR #2372 threshold tolerance (already on main, separate from V7.1). Promote to ship.

- Pro: PROVEN to deliver 9.5/10 quality on m20. The remaining gap to ship was `word_count`, which already has a tolerance fix.
- Con: V7 prompt remains 135KB with ceiling pressure. Hardening cycle for each new failure mode persists. Doesn't materially address the "visible compliance tokens" pattern codex's earlier brain-pick identified.

### Option B: Fix V7.1 regressions and retry

Patch issue #2380's four regressions in one follow-up PR:
- Re-add `translate` schema directive to `linear-write.md` (Regression 2)
- Diagnose + fix the silent-exit in `v7_build.py` post-llm_qg path (Regression 1)
- Sharpen `#R-AUDIENCE-LANGUAGE-A1` under V7.1 charter (Regression 3)
- Investigate codex tool-call regression cause (Regression 4)
Then re-fire V7.1+codex pilot to see if it scores 9.5+.

- Pro: V7.1 architecture (renderer charter + wiki-bound vocab + completeness gate) is the better long-term shape per codex+gemini+cursor's prior r1/r2 convergence. Fixes don't require reverting.
- Con: Four regressions in one PR is a lot of blind churn. Each fix is a judgment call. May expose more regressions.

### Option C: Partial revert + selective keep

Revert PR #2377 (V7.1 Day 1 charter — caused Regression 3 + likely 4) but KEEP PR #2379 (Day 2 gate + manifest + allowlist — the gate worked and passed m20). Re-fire V7-prompt + V7.1-gates + codex-tools.

- Pro: Tests whether the gates alone are sufficient (without the charter) to reproduce 9.5 + improve via wiki audit later. Smaller change surface than B.
- Con: Loses the renderer-pivot architectural framing that codex/gemini r2 converged on. We don't know what caused Regression 1 (silent exit) — may also be in PR #2379, in which case partial-revert doesn't fix it.

### Option D: Pause, run V7-hardened + codex as the actual A1 anchor while we redesign

Promote Pt 10's 185032 baseline (V7+codex, 9.5/10) to main as the actual m20 anchor. Path B PR #2372 already lowered word_count tolerance. Then spend a couple sessions redesigning V7.1 with the regressions in mind — perhaps an ADR revision before next PR.

- Pro: Ships m20 NOW (it's been the rolling pipeline-proof for three weeks). Buys time to design V7.1 properly.
- Con: Pt 10's baseline still had `word_count` 1058 < 1104 fail under the stricter ceiling. Need to verify the Path B tolerance fix actually resolves that for this build.

### Option E: Something else

Propose an option I missed. The user has explicit constraints: V7.1 must scale to B1+ (100% UK body), seminars (full Ukrainian, contested facts), and activities (bounded composition). Any path forward must honor those.

## What I want from you

1. **Read the 3 module.md files** (paths above). Compare quality directly. Don't trust the scores — judge as a Ukrainian-language teacher reading three different lessons on the same topic.

2. **Vote A / B / C / D / E** with one-paragraph reasoning. Be specific about which artifact's content drove your reasoning.

3. **Pick the regression you'd attack first** if Option B or C. Which of the four (silent exit, schema drift, charter A1-discipline, codex utilization) is the root cause vs a downstream symptom?

4. **Flag any blind spot** I'm missing. Examples: does the wiki_completeness_gate actually validate enough at A1 (m20 wiki passed all checks with 21/20 vocab — was that audit shallow)? Did PR #2379's allowlist `learner_state.py` rewrite +439/-18 silently disable some prior check?

End your reply with one of:
- `[VOTE: A]` / `[VOTE: B]` / `[VOTE: C]` / `[VOTE: D]` / `[VOTE: E]`

Then your one-line bottom-line summary. The user is making a directional call and your vote contributes.
