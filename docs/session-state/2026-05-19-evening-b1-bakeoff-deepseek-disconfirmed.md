---
date: 2026-05-19
session: "Evening drive — Hermes routing fix, deepseek+qwen V7 writer-tools shipped, B1 writer bakeoff with surprising deepseek disconfirmation"
status: green
main_sha: 7012043def
main_green: true
working_tree_dirty: true   # uncommitted: bakeoff runner + raw outputs
prs_merged_this_session:
  - "#2158 (feat(v7-writer): add deepseek-tools + qwen-tools writer choices)"
direct_commits_to_main:
  - "c16e0cffc6 fix(hermes): force --provider openrouter for moonshotai/minimax routing drift"
  - "7ae1924406 docs(projects): scope UA calque + grammar eval harness (UNLP 2027)"
  - "75a2bc933c docs(audit): REPORT.html v2 — minimax-m2.7 recovered + Hermes postmortem"
  - "b2965e5a58 docs(dispatch-brief): scope deepseek-tools + qwen-tools as V7 writer choices"
active_dispatches: []
issues_filed:
  - "#2156 — Project: UA calque + grammar eval harness (UNLP 2027 target)"
  - "#2157 — [blocker] CoT-removal dispatch conflicts with load-bearing implementation_map gate"
headline_finding: "DeepSeek-v4-pro hypothesis DISCONFIRMED at B1: leads at A1, fails to emit module artifacts at B1's 4000-word target. Production B1+ writer remains claude-tools."
next_session_first_item: "Investigate codex-tools (gpt-5.5) at xhigh effort — does the silent no-response failure recover with more reasoning budget?"
---

# Handoff — B1 writer bakeoff: deepseek hypothesis disconfirmed; investigation queue prepared

## TL;DR for the next session

This session shipped the Hermes provider-routing fix + the deepseek-tools + qwen-tools V7 writer adapters (PR #2158 merged on main as `7012043def`), then ran a 5-model B1 writer bakeoff on `b1-052 genitive-nuances`. **Headline finding: deepseek-v4-pro emitted thorough scaffolding (all 7 plan_reasoning + 2 audit lines) but STOPPED before producing any module artifacts** — the opposite of A1 where it dropped scaffolding and produced the best content. Only claude-tools + qwen-tools shipped real module outputs. Codex (silent no-response), gemini (wrong-tool-family gate), deepseek (no artifacts) all failed.

**User direction at close: do a session handoff, then investigate the failed writers one by one starting with codex (gpt-5.5 xhigh effort).**

## ⚠️ FIRST ITEM NEXT SESSION — Codex investigation

User's stated next step: re-run `codex-tools` on the B1 bakeoff at **effort=xhigh** (current default is `high`, see `WRITER_DEFAULTS["codex-tools"]`). Hypothesis: the silent no-response failure at B1's 210K-char prompt may be a reasoning-budget exhaustion that more effort recovers.

Concrete action:

```bash
# Add --effort flag to the bakeoff runner first (currently uses WRITER_DEFAULTS effort)
# Then:
.venv/bin/python scripts/bakeoff/run_b1_writer.py \
    --level b1 \
    --slug genitive-nuances \
    --writer codex-tools \
    --effort xhigh \
    --out audit/2026-05-19-b1-writer-bakeoff/codex-tools-xhigh
```

If it works: codex-tools at xhigh is viable for B1+. If it ALSO fails: the issue isn't effort — it's something deeper (prompt size, register handling, etc.) and we should look at the codex CLI stdout log for clues.

**Implementation note:** `scripts/bakeoff/run_b1_writer.py` currently does NOT accept `--effort`. Need to add it as an argparse arg, then pass through to `invoke_writer(..., model=..., effort=...)`. Currently `invoke_writer` pulls effort from `WRITER_DEFAULTS[writer]["effort"]` — needs a small refactor to accept an explicit `effort` argument. Look at how v7_build.py's writer-timeout flow does it.

After codex investigation completes, user wants the same pattern applied to:
- deepseek-tools: rerun with effort=xhigh (vs current `medium`)
- gemini-tools: investigate the wrong-tool-family namespace issue (probably needs adapter fix, not effort)
- qwen-tools: investigate the universal-failure pattern (wrong fence + JSON-in-yaml) — already known, separate fix path

## Section 1 — What this session shipped (commits + PR)

### PR #2158 merged (deepseek-tools + qwen-tools writer choices)

Adds two new V7 writer choices mirroring the existing Hermes-backed `grok-tools` pattern:

- `deepseek-tools` → `deepseek-v4-pro` (effort=medium)
- `qwen-tools` → `qwen/qwen3.6-plus` (effort=medium)

Both route MCP access through Hermes (`~/.hermes/config.yaml` with `sources` enabled). 5 files changed; 71 insertions / 13 deletions. Test fixtures parametrized across all writer aliases including the new ones. 89 tests passed. CI all-green except `review / review` (Gemini-Dispatch auth advisory, non-blocking).

Diff was clean, exactly matched the brief at `docs/dispatch-briefs/2026-05-19-deepseek-qwen-writer-tools-codex.md`. Codex completed the dispatch in 896s (~15 min).

### Hermes provider-routing fix (c16e0cffc6)

Root cause: `moonshotai/*` and `minimax/*` model prefixes default to an internal `nvidia` provider mapping despite top-level `model.provider: openrouter` in `~/.hermes/config.yaml`. Per-invocation `-m` routing doesn't honor the top-level config for these vendors.

Fix: `scripts/agent_runtime/adapters/hermes_qwen.py` now passes `--provider openrouter` explicitly. Regression-guarded by 3 new tests in `tests/agent_runtime/adapters/test_hermes_qwen_adapter.py` asserting the flag's presence for both previously-broken (moonshotai/*, minimax/*) and previously-working (qwen/*, deepseek/*) prefixes.

End-to-end validated: `hermes -z "ping" -m moonshotai/kimi-k2.6 --provider openrouter` returns "pong" successfully. minimax-m2.7 dispatch via delegate.py also completes (231s, 34KB output, full universal-failure pattern). The v1 REPORT.html "infra-blocked" rows for these vendors are now graded.

### REPORT.html v2 (75a2bc933c)

`audit/2026-05-19-multi-agent-routing-assessment/REPORT.html` updated: minimax-m2.7 row replaces the v1 BLOCKED placeholder; Hermes postmortem corrected (root cause was internal default routing, NOT a per-model config override the v1 report speculated about); §9 limitations table reframed as `v1 → v2 status by challenger`; §10 appendix adds raw artifacts.

**Note:** kimi-k2.5 and kimi-k2.6 retries ALL TIMED OUT at silence-window with zero stdout (k2.6 retried twice at 600s + 1800s timeouts, k2.5 once at 600s). This is **NOT** the provider-routing bug (already fixed). The actual failure mode is **OpenRouter kimi long-prompt streaming** — Hermes silently buffers output for 60K-token prompts and never flushes. Documented in REPORT.html v2 §5 + §9. Marked as infra-limited (not a model-quality verdict).

### Calque + grammar eval harness scoping (7ae1924406 + GH #2156)

User direction earlier this session: scope the UA-GEC F/Calque + grammar eval harness for UNLP 2027. Two scoring axes coupled into one harness (calque tags + grammar tags). Doc at `docs/projects/ua-eval-harness/README.md`. Tracked via GH #2156. **No personal names in the doc per privacy convention** (the personal-name-audit pattern from `13fd847859`).

Pick-up entrypoint for the eval-harness work is in that README — when the user says "let's continue the eval harness work," that's the canonical doc to read first.

### CoT-removal dispatch escalated at #2157 (NOT merged — work held)

Codex caught a load-bearing conflict in my anchor facts and stopped without making changes. The brief said to remove `<plan_reasoning>` + nested `<implementation_map>`, but `<implementation_map>` IS parsed by `wiki_coverage_gate.py:31` (regex `<implementation_map\b[^>]*>(?P<body>.*?)</implementation_map>`). My grep was too narrow (searched `implementation_map_audit` not the bare tag).

Corrected gate-parsing reality (orchestrator independent verification):

| Block | Parsed by gate? | Disposition |
|---|---|---|
| `<plan_reasoning>` envelope | ✅ YES (`linear_pipeline.py` lines 1702/1705/1886/1890/2036/2056/2405/6687/6691 + `wiki_coverage_gate.py:54`) | KEEP |
| `<implementation_map>` nested | ✅ YES (`wiki_coverage_gate.py:31` regex) | KEEP |
| `<implementation_map_audit>` | ❌ NO (0 hits) | safe to REMOVE |
| `<bad_form_audit>` | ❌ NO (0 hits) | safe to REMOVE |
| `<verification_trace>` | ⚠️ partial (`linear_pipeline.py:188,206-207` — tool-theatre detection) | INVESTIGATE before removing |

The 3-agent CoT-removal consensus was directionally right on the audit lines but conflated the load-bearing envelope with the vestigial audit lines. **Revised dispatch needs a narrower scope** before re-firing.

## Section 2 — The B1 writer bakeoff (raw artifacts on disk)

### Methodology

Writer-only via `invoke_writer` (matches v1 A1 bakeoff methodology). NO reviewer phase, NO audit gates, NO fix loop. Compares raw writer outputs at parity. Module: `b1-052 genitive-nuances` (word_target=4000, grammar focus). Runner script: `scripts/bakeoff/run_b1_writer.py` (UNCOMMITTED at handoff).

Each writer writes to its own audit dir under `audit/2026-05-19-b1-writer-bakeoff/{writer}/` with: `writer_prompt.md` (210K chars), `knowledge_packet.md` (62KB), `wiki_manifest.json`, `implementation_map.json`, `writer_output.md`, `writer_tool_calls.json` (if completed), `summary.json`.

### Results

| Writer | Output | Verdict | Notes |
|---|---|---|---|
| **claude-tools** (Opus 4.7) | 54 KB | ✅ FULL EMISSION | 13.4 min, all 7 plan_reasoning + 2 audit lines + 4 fence tags + end_gate present (rescanned_words, rescanned_sources, grammar_claims_grounded, removed_unverified — honest self-disclosure about MCP tool gaps). Universal-failure pattern persists (wrong fence + JSON-in-yaml). |
| **qwen-tools** (Qwen 3.6 Plus) | 31 KB | ✅ FULL EMISSION | 4.3 min, all 7 plan_reasoning + 2 audit lines + 4 fence tags + end_gate present. Same universal-failure pattern. |
| **deepseek-tools** (DeepSeek v4 Pro) | 9 KB | ❌ SCAFFOLDING-ONLY | 3.4 min. All 7 plan_reasoning + 2 audit lines emitted thoughtfully, then STOPPED before any artifact fence. 8027 of 8958 output chars are plan_reasoning content; ~931 chars actual emission. **Opposite of A1 behavior** where deepseek dropped scaffolding and produced best content. |
| **codex-tools** (GPT-5.5) | 0 | ❌ NO RESPONSE | Failed at `linear_pipeline.py:2748` "Writer call returned no response". MCP resolved OK, codex was invoked, but no response came back. Likely the same content-register friction documented for codex at A1 (see `docs/decisions/2026-05-06-writer-selection-codex-gpt55.md`), worsened at B1's 210K-char prompt scale. |
| **gemini-tools** (Gemini 3.1 Pro) | gate-rejected | ❌ TOOL-NAMESPACE FAIL | Two terminal gates fired: (1) `infra_context_contamination:wrong_tool_family` — used wrong tool namespaces (`mcp_sources_search_text` single-underscore + non-sources tools like `update_topic`, `run_shell_command`); (2) `mcp_tools_never_invoked` — pipeline interpreted wrong-named calls as zero real MCP invocations. Same shape as the v1 audit E5/E6 finding. cwd workaround was applied but didn't help — namespace issue is on Gemini's tool-call generation side. |

**3 of 4 challengers FAILED at B1. Production B1+ writer remains claude-tools.**

### Cost estimate for this bakeoff
- claude-tools: subscription (Claude Code Max plan, weekly limits DOUBLED through July 2026)
- codex-tools: subscription (failed fast, minimal usage)
- gemini-tools: subscription (failed at ~270s with 22 tool calls)
- deepseek-tools: ~$0.20-0.50 metered (DeepSeek direct API)
- qwen-tools: ~$0.05-0.20 metered (OpenRouter)
- **Total metered: ~$0.30-0.70**

Per user note this session: $1.67 burned on DeepSeek-direct across the day, ~$8 OpenRouter across both projects. Most of OpenRouter waste was the 3 kimi long-prompt timeout retries that produced zero output.

## Section 3 — The deepseek hypothesis disconfirmation (the surprising finding)

The user opened the session with the hypothesis that DeepSeek-v4-pro is "really good solution" for V7 writing — supported by the v1 A1 bakeoff where deepseek led on content quality despite dropping the CoT contract.

**B1 disconfirms this hypothesis empirically.** Same writer, same prompt template, larger word target (4000 vs 1200), and deepseek BREAKS — it plans extensively then never emits artifacts. This is the "register inversion" risk I flagged before firing — the bias that helped at A1 (substance over scaffolding) didn't transfer; instead deepseek emitted scaffolding then ran out of budget or signal to continue.

**Possible causes for the next session to investigate:**
1. **Reasoning-budget exhaustion** — `effort=medium` may be insufficient for B1's 4000-word output target after extensive scaffolding. Try `xhigh`.
2. **Context-window pressure** — 290KB prompt + 8KB scaffolding leaves less room for artifact generation if deepseek interprets the audit line as a termination signal.
3. **Prompt-side interpretation** — deepseek may interpret the `<implementation_map_audit>` line as the end-of-output cue and stop, having "satisfied" the contract.

**Routing implication:** the 2026-05-31 DeepSeek discount cliff is now less load-bearing for B1+ routing decisions — we wouldn't have moved B1+ to deepseek anyway based on this data. For A1, deepseek-v4-pro still leads (per v1 REPORT.html §5/§6). Possible plan: keep deepseek as A1 writer candidate (pre-cliff), keep claude-tools as B1+ writer.

## Section 4 — Universal-failure pattern at B1 confirms v1 finding

Both successful B1 writers (claude-tools, qwen-tools) exhibit the same prompt-clarity bugs from v1 A1 bakeoff:

1. Wrong fence syntax: `\`\`\`markdown file=module.md` instead of `\`\`\`module.md`
2. JSON-in-`.yaml` blocks: `[{...}]` arrays inside `\`\`\`activities.yaml` instead of YAML list-of-mappings

Pattern is now confirmed at 10 of 10 graded writer slots across A1 + B1 (everyone except the baseline they don't apply to). This re-validates the CoT-removal brief's recommendation to ADD the 2 prompt-clarity directives — that part of the brief was correct even though the scaffolding-removal scope was wrong.

**Recommendation:** file a narrow PR that ONLY adds the 2 prompt-clarity directives to `linear-write.md`. Don't touch the scaffolding (per the gate-parsing reality from #2157). Estimated effort: trivial Codex dispatch (~$1-3, <1h).

## Section 5 — Carry-over task list

| # | Status | Subject | Notes |
|---|---|---|---|
| #2155 | pending | Fix wiki_coverage_gate semantics: distinguish substance-required vs absence-required bans | Highest-leverage code fix in queue: would push m20 from 67% → 83% coverage. ~2-3h Codex dispatch. |
| #2154 | pending | zizmor MEDIUM triage (21 findings) | ~1h, mostly mechanical. |
| NEW-1 | pending | Investigate codex-tools (gpt-5.5) at xhigh effort on B1 bakeoff | USER FIRST PRIORITY. Add --effort to bakeoff runner, rerun codex-tools with xhigh, compare to high. |
| NEW-2 | pending | Investigate deepseek-tools at xhigh effort + look at writer_tool_calls.json | If xhigh recovers artifact emission, deepseek may be viable at B1+ after all. If not, deepseek stays A1-only. |
| NEW-3 | pending | Investigate gemini-tools wrong-tool-family failure | Probably needs adapter-side fix (tool-name normalization?), not effort. Check the `update_topic` / `run_shell_command` calls — those shouldn't be in the toolset at all. |
| NEW-4 | pending | File narrow prompt-clarity PR (fence syntax + YAML-in-yaml directives) | Universal-failure pattern confirmed at 10/10 graded writer slots. Add 2 directives to `linear-write.md`. ~$1-3 Codex. Don't touch the scaffolding. |
| NEW-5 | pending | Revise CoT-removal scope (close #2157 path or redirect) | Original brief was wrong about `<plan_reasoning>` envelope; corrected gate-parsing table in #2157 comment. Decision: probably skip the larger refactor, just do NEW-4. |
| NEW-6 | pending | Commit + push bakeoff runner + raw outputs | `scripts/bakeoff/run_b1_writer.py` + `audit/2026-05-19-b1-writer-bakeoff/` need to land on main for reproducibility. Recommend: do this BEFORE firing the codex-xhigh investigation so the comparison artifact is committed. |
| NEW-7 | pending | Write B1 bakeoff HTML report (parallel to v1 REPORT.html §5 structure) | After codex-xhigh investigation lands, write up the full B1 verdict. Frame: "A1 deepseek hero, B1 deepseek regresses — claude-tools is the right B1+ default." |

## Section 6 — Cold-start protocol for the next session

1. Read this handoff (you're doing it now).
2. Orient via Monitor API:
   ```
   curl -s http://localhost:8765/api/state/manifest
   curl -s http://localhost:8765/api/orient
   curl -s 'http://localhost:8765/api/comms/inbox?agent=claude'
   ```
3. Check the open issues filed this session: #2156 (calque-eval), #2157 (CoT-removal escalation).
4. **Commit the bakeoff runner + raw outputs first** (NEW-6) so the artifacts are on main before the codex investigation runs.
5. **Add `--effort` flag to `scripts/bakeoff/run_b1_writer.py`** (small refactor — pass through to `invoke_writer`).
6. **Fire the codex-xhigh investigation** (NEW-1) — the user's stated first priority.
7. Process the result; decide on deepseek-xhigh + gemini-investigation paths based on what codex shows.
8. Eventually: file the narrow prompt-clarity PR (NEW-4) and write the B1 bakeoff HTML report (NEW-7).

## Provenance + cross-links

- v1 routing audit: `audit/2026-05-19-multi-agent-routing-assessment/REPORT.html` (now v2)
- v1 A1 writer bakeoff data: `audit/2026-05-19-qwen-writer-bakeoff/` and `audit/2026-05-19-multi-agent-routing-assessment/raw/`
- **B1 bakeoff raw artifacts**: `audit/2026-05-19-b1-writer-bakeoff/{claude-tools,codex-tools,deepseek-tools,gemini-tools,qwen-tools}/`
- B1 bakeoff runner: `scripts/bakeoff/run_b1_writer.py` (uncommitted at handoff)
- Bakeoff log files (per writer): `audit/2026-05-19-b1-writer-bakeoff/{writer}.log`
- Hermes provider-routing fix: commit `c16e0cffc6` + test `tests/agent_runtime/adapters/test_hermes_qwen_adapter.py`
- deepseek/qwen writer-tools: PR #2158 (merged `7012043def`)
- Calque + grammar eval harness: `docs/projects/ua-eval-harness/README.md` + GH #2156
- CoT-removal dispatch escalation: GH #2157 (Codex correctly halted on incomplete anchor facts)
- Predecessor handoff: `docs/session-state/2026-05-19-night-routing-audit-and-handoff.md`
- Writer-selection decision card: `docs/decisions/2026-05-06-writer-selection-codex-gpt55.md`

## Open dispatches at handoff

None. All 5 B1 bakeoff workers completed (mix of success + failure). No PRs awaiting review.
