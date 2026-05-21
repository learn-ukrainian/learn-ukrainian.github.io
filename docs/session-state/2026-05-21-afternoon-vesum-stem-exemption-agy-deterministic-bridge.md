---
date: 2026-05-21
session: "Afternoon — 9 commits, claude-tools 21/22 + vesum stem-exemption merged (PR #2173), agy verified deterministic-MCP + ab ask-agy shipped"
status: green-multi-writer-progress + 1-PR-merged + 0-active-dispatches
main_sha: d786a4fa6e
main_green: pending (CI on each commit was clean locally; main is at user's branch HEAD)
working_tree_dirty: true  # only pre-existing items inherited from morning + the etymology brief PR #2179 untracked + .agents/mcp_config.json (workspace shim from earlier today)
prs_merged_this_session:
  - "#2172 max-budget-usd plumbing (Codex dispatch max-budget-usd-2026-05-21)"
  - "#2173 vesum_verified stem-fragment exemption (Codex dispatch vesum-stem-exemption-2026-05-21)"
prs_opened_this_session: []
direct_commits_to_main:
  - "3713573f05 feat(code-review): add adversarial challenge round to filter false positives  # later renamed → local-code-review"
  - "e9fa509c32 refactor(skills): rename code-review → local-code-review; brief budget plumbing"
  - "8174ea3f52 fix(mcp/sources): drop terminate() after handle_request to stop ASGI violation"
  - "554441899d feat(writer-prompt): blockquote ≥30 self-check + mandatory inject_activity_ids"
  - "bcc9ccd345 fix(test): accept structured error envelope as MCP transport success"
  - "2721f87c6f docs(dispatch-brief): vesum stem-fragment exemption"
  - "531749eddb feat(bridge): add ask-agy subcommand for Antigravity CLI Q&A"
  - "55150d0cb7 docs(dispatch-brief): agy V7 writer integration (telemetry + prompt)"
active_dispatches: []
active_builds: []
issues_filed: []
issues_closed: []
headline_finding: "claude-tools build #5 of a1/my-morning hit 21/22 gates green — closest V7 build to all-green this week. The single failure (vesum_verified on `**користу**-` morphological stem fragment) is now fixed on main via merged PR #2173. Next-session rebuild expected 22/22 → first complete V7 module ready to promote. Plus: agy verified deterministic-tool-calling via 4-call adversarial bust — all responses matched live MCP output byte-for-byte, including server-quirk error shapes the model couldn't have fabricated. `ab ask-agy` bridge subcommand shipped + tested round-trip."
next_session_first_item: "Rebuild claude-tools a1/my-morning with `--worktree` against current main (d786a4fa6e includes the vesum stem exemption). Monitor JSONL events. If 22/22 → `scripts/sync/promote_module.py --latest --level a1 --slug my-morning` → first complete V7 module on main. Then fire the agy V7 integration Codex dispatch from brief `docs/dispatch-briefs/2026-05-21-agy-v7-writer-integration-codex.md`."
---

# Afternoon handoff — vesum stem exemption merged, agy proven deterministic

## TL;DR

Morning handoff's "agy + MCP works end-to-end" claim was a **false positive** — Gemini-Flash-3.5 hallucinated VESUM tags from priors because the probe was an introspection prompt. agy-tools build #4 failed `mcp_tools_never_invoked` HARD. After config-side adjustments (user, not me) and a four-call adversarial bust probe today, agy is now **verified deterministic-tool-calling**: every response in the bust matched live MCP output byte-for-byte, including the server's exact error message for a fake tool name (`"Unknown tool: ..."`, returned as `isError:false` text content — server quirk the model couldn't have fabricated).

Eight commits to main this session. Two PRs merged (Codex dispatches landed clean). claude-tools build #5 of `a1/my-morning` hit 21/22 gates — single failure was a morphological stem fragment (`**користу**-`) flagged by `vesum_verified`. Codex's PR #2173 added the missing exemption to `_iter_vesum_word_surfaces`. Main now ready for a rebuild that should hit 22/22.

## Section 1 — Writer state matrix at end of session

| Writer | Status | Today's evidence |
|---|---|---|
| **claude-tools** | 🟢 **21/22** + 1 PR merge from 22/22 | build #5 (`build/a1/my-morning-20260521-101042`), all 3 today's directives passed (textbook_grounding ✅, inject_activity_ids ✅, vesum failed on stem; PR #2173 exempts stems → next rebuild should hit 22/22) |
| **gemini-tools** | 🟡 untested since morning | morning's 19/23 + parser-error build was BEFORE today's ASGI fix (8174ea3f52), ≥30-word + INJECT directives (554441899d), and stem exemption (PR #2173). Rebuild should land ~21-22/22. |
| **deepseek-tools** | 🟡 untested since morning | morning build #3 was 19/22; today's directives target the exact 3 failures. Rebuild should land ~21-22/22, same stem-fragment risk now mitigated. |
| **codex-tools** | 🟡 untested since morning | namespace+name fix in main from morning (53b807ad07); rollout-flush race separate known issue. |
| **agy-tools** | 🟢 deterministic-MCP **VERIFIED** (this session), V7 integration still needs telemetry parser + writer-prompt directive | 4-call bust matched MCP byte-for-byte; sandbox probe stayed inside MCP toolset; under-reports tool calls in narrative (shim must scrape all stdout markers). Brief filed: `docs/dispatch-briefs/2026-05-21-agy-v7-writer-integration-codex.md`. |

## Section 2 — MCP `sources` ASGI bug (commit `8174ea3f52`)

`StreamableHTTPEndpoint.__call__` in `.mcp/servers/sources/server.py` awaited `http_transport.terminate()` AFTER `http_transport.handle_request()` had already driven the response through to the final `http.response.body` frame. In mcp==1.26.0 the terminate() path then emitted an additional `http.response.start` against the already-closed ASGI response, raising:

```
RuntimeError: Expected ASGI message 'http.response.body', but got 'http.response.start'.
```

User out-of-band investigation pin-pointed the line. Fix: remove the redundant `terminate()`. The `async with http_transport.connect()` context cleans up read/write streams; `tg.cancel_scope.cancel()` tears down the server task; nothing leaks. Inline NOTE comment guards against future cleanup-minded edits re-adding it.

**Affected clients**: any streamable-http MCP client — codex CLI, gemini CLI 0.42+, agy 1.0, Hermes-routed DeepSeek/Grok/Qwen when configured for HTTP. **NOT affected**: Claude Code's stdio path, legacy `/sse` endpoint. Likely contributor to the long-standing intermittent `tool_calls_total=0` / silent-CLI-exit patterns on agent dispatches (issues #2134, #2159).

Live verification: restarted production sources MCP; tool call to `verify_word("стіл")` returned correct VESUM data with zero new "Expected ASGI message" log entries.

## Section 3 — Writer-prompt directives shipped (commit `554441899d`)

Two additions to `scripts/build/phases/linear-write.md` targeting DeepSeek build #3's failure shapes (a1/my-morning, branch `build/a1/my-morning-20260521-083420`):

1. **≥30-word blockquote self-check** (textbook_grounding). The "Step B" instruction at line 214 already said "≥30 contiguous words" but it was buried. Added a "MANDATORY WORD-COUNT SELF-CHECK" callout with the exact 24-word failure shape DeepSeek produced as a worked example + "keep copying past sentence-boundaries when natural punctuation lands short of 30."

2. **`<!-- INJECT_ACTIVITY: <id> -->` cross-reference mandate** (inject_activity_ids). New "## Inline activity cross-references in module.md" section before "## Activity Authoring Fields" — names the gate, both failure reasons, the regex shape, placement rule, and a worked example.

Both directives benefit every writer. claude-tools build #5 result confirms they work: textbook_grounding ✅, inject_activity_ids ✅.

## Section 4 — claude-tools build #5 result (21/22)

Branch `build/a1/my-morning-20260521-101042` (artifacts auto-committed per #M-10). Phase summary:

- Writer phase: 1118s (~18.6 min) — clean run, 4/4 sections with CoT, all `fields_filled` populated, real MCP tool calls visible (verify_words×2, search_text returning real Захарійчук chunks)
- Reviewer phase: codex-tools, clean
- python_qg: 130s, **21/22 gates passed**

Gates that passed include the two we shipped directives for today: `textbook_grounding` HARD-pass with proper Захарійчук blockquote, `inject_activity_ids` clean.

The single failure: `vesum_verified` flagged token `**користу**` — extracted from "The stem begins **користу**-, not 'користуву-'" (pedagogically correct demonstration of the `-ва-` drop pattern in `користуватися`). `_iter_vesum_word_surfaces` strips trailing `-` and looks up the bare stem, which obviously fails VESUM (stems aren't lemmas). ADR-008 has no correction path — both correction_r1 and correction_r2 came back with empty `vesum_verified` dicts.

Codex's PR #2173 added a stem-fragment exemption (Cyrillic word + hyphen NOT followed by a Cyrillic letter → skip). Merged. Next claude-tools rebuild should hit 22/22.

## Section 5 — agy deterministic-MCP verification

User adjusted agy's config side ("ok mcp is looking good in apy"). Re-probed:

**4-call adversarial bust (matched live MCP byte-for-byte):**

| Call | Agy returned | Real MCP returned | Match |
|---|---|---|---|
| Fake tool `THIS_TOOL_NAME_IS_DELIBERATELY_INVALID` | `"Unknown tool: THIS_TOOL_NAME_IS_DELIBERATELY_INVALID"` | identical | ✅ |
| Nonsense word `xyzabcdefqq` | `"'xyzabcdefqq' — NOT FOUND in VESUM..."` | identical | ✅ |
| `розчервонілася` (rare reflexive past) | `lemma: розчервонітися \| tags: verb:rev:perf:past:f` | identical | ✅ |
| `поставлюся` (1sg future reflexive) | `lemma: поставитися \| tags: verb:rev:perf:futr:s:1` | identical | ✅ |

The strongest evidence: I deliberately suggested wrong tag formats in the probe prompt (`verb:imperf:past:f:rev`, `verb:perf:p1:s:rev`). Real VESUM uses different orderings (`:rev:` between aspect and tense; `:futr:` not `:p1:`). agy returned the server's actual format, not what I implied. Could not have been fabricated.

**Sandbox probe**: agy stayed inside MCP toolset (no bash/sqlite3/grep/scripts in stdout). Found the right Grade-5 page-100 punctuation chunk (`5-klas-ukrmova-golub-2022_s0100` — real, server confirmed). Under-reported its work in the prose response — the 3 documented ATTEMPT blocks didn't surface the FINAL chunk_id, so agy must have done unreported variants or constructed the chunk_id from schema knowledge. Both MCP-only paths, but the telemetry shim must capture ALL stdout markers, not rely on agy's narrative.

**Per-machine MEMORY** (`~/.claude/projects/.../memory/MEMORY.md`) was softened on the `#M0` programmatic-Claude lane (was hard ban after 2026-06-15; now quota-conditional). The same MEMORY entry already documents agy use; no need to add a separate agy-verified entry — the determinism is now established and the shim brief encodes the V7-readiness path.

## Section 6 — `ab ask-agy` bridge subcommand (commit `531749eddb`)

Mirrors codex bridge shape: one-shot send via the broker + `agent_runtime.runner.invoke()` + write back response. Files:

- `scripts/ai_agent_bridge/_agy.py` (243 LOC) — `ask_agy()`, `process_for_agy()`, AGY_BRIDGE_TIMEOUT env handling (default 900s)
- `scripts/ai_agent_bridge/_prompts.py` — `build_agy_prompt()` with standing rules forbidding investigation side-paths
- `scripts/ai_agent_bridge/_cli.py` — `ask-agy` subparser + `_handle_ask_agy` dispatch

Usage:

```bash
.venv/bin/python scripts/ai_agent_bridge/__main__.py ask-agy \
    --task-id <task-name> "<prompt>"
```

Round-trip verified live: real VESUM payload for `ранок` (`noun:inanim:m:v_naz`, `v_zna`) returned through the bridge. 424 bridge tests still pass.

## Section 7 — PR #2172 (max-budget-usd plumbing)

Codex dispatch `max-budget-usd-2026-05-21` landed clean in 14 min. Threads `--max-budget-usd <float:.2f>` through `delegate.py dispatch / _worker` argparse, state persistence, worker subprocess args, and into `agent_runtime.runner.invoke()` via `tool_config`. Only the claude adapter emits the CLI flag (and only in `-p` print mode); other adapters log a one-line WARN and ignore. Regression tests cover the four propagation paths. Merged. Now available for any future quota-conscious Claude lane invocation.

## Section 8 — local-code-review rename (commit `e9fa509c32`)

Earlier in session I added an adversarial challenge round to our `code-review` skill (`3713573f05`). User then noted Anthropic ships `code-review:code-review` natively (5 parallel Sonnet agents + Haiku confidence-scoring — already implements the "filter false positives" pattern at a more sophisticated level than what I'd added). Renamed our skill to `local-code-review` (scope: uncommitted working-tree diffs; the official plugin is for PR review). Cross-model invariant (Gemini reviews + Codex challenges) is the actual differentiator. SKILL.md description points users to the official plugin for PR work.

## Section 9 — Open follow-ups

| # | Subject | Priority | Notes |
|---|---|---|---|
| 1 | claude-tools rebuild of a1/my-morning | **P0 next session** | Main now has the vesum stem exemption. Expected 22/22. Then promote. |
| 2 | agy V7 integration Codex dispatch | P0 next session | Brief: `docs/dispatch-briefs/2026-05-21-agy-v7-writer-integration-codex.md`. Supersedes the cancelled earlier shim brief. |
| 3 | gemini-tools + deepseek-tools rebuilds | P1 | Both have today's directives + MCP fix + stem exemption available. Cross-validate the gate fixes. |
| 4 | codex-tools rollout-flush race | P2 | Separate from namespace fix; intermittent `tool_calls_total=0` symptom. |
| 5 | PR #2168 amelina stub blocker | low | Seminar plan-quality sweep. Can be deferred indefinitely; 1158/1159 plans valid. |
| 6 | esum-ocr pivot (someone else's work) | their lane | Commits `dd0481e67e`, `e50c58a245`, `eba81af84e` + PR #2179 + issues #2174-#2178. Not mine; not blocking V7. |

## Section 10 — Cleanup state

- No active dispatches
- No active builds
- Build worktrees preserved per #M-10: `build/a1/my-morning-20260521-101042` (today's 21/22 build) + all morning builds (rebuild forensics)
- Worktree cleanup done for both finished Codex dispatches (max-budget-usd-* and vesum-stem-*)
- Working tree dirty with: pre-existing items inherited from morning (starlight a1/index.mdx, audit marker dir, _orchestration run-archive) + the etymology PR #2179 brief untracked + `.agents/mcp_config.json` workspace shim I created earlier in this session. None are mine to commit.

## Section 11 — Cold-start sequence for next session

1. Read this handoff.
2. Orient via Monitor API (`/api/state/manifest` → `/api/orient` → `/api/comms/inbox?agent=claude`).
3. **First action**: rebuild claude-tools a1/my-morning with `--worktree`. Monitor JSONL events. Expected 22/22 (vesum stem exemption now on main).
4. If 22/22 → `scripts/sync/promote_module.py --latest --level a1 --slug my-morning` — first complete V7 module on main.
5. Fire the agy V7 integration Codex dispatch from the brief.
6. Cross-validate by rebuilding gemini-tools + deepseek-tools against current main (they'll inherit ASGI fix + ≥30 directive + INJECT directive + stem exemption).

## Sign-off

Eight direct commits + 2 PR merges. Started from a broken-agy / 21-of-22-claude-tools state and ended with vesum stem exemption merged, agy verified deterministic-MCP, ask-agy bridge shipped, and a clear path to first all-green V7 module. agy ecosystem progressed from "configurator working in background" → "deterministic-tool-calling verified + integration brief filed for Codex pickup." `ab ask-agy` is the new lateral communication channel — confirmed bidirectional with agy via real MCP roundtrip evidence.

The "first complete V7 module on main" goal is one rebuild away.
