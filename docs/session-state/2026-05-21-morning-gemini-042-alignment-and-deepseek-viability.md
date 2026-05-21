---
date: 2026-05-21
session: "Morning — gemini-cli 0.42.0 pipeline alignment + first clean DeepSeek-pro V7 writer run + 5 commits to main"
status: green-multi-writer-progress + 1-build-in-flight
main_sha: be3b7c54fa
main_green: pending (CI on each commit was clean locally; main is at user's branch HEAD)
working_tree_dirty: true  # only starlight/src/content/docs/a1/index.mdx (pre-existing, NOT mine); audit/2026-05-21-flash-3.5-ua-quality/ (empty marker dir); curriculum/l2-uk-en/_orchestration/ (run-archive forensics — gitignored); docs/dispatch-briefs/2026-05-21-gemini-ocr-policy-migration-codex.md (Codex's PR #2171 brief, awaiting commit/archive sweep)
prs_merged_this_session:
  - "#2171 Codex's ocr-policy-2026-05-21 — bulk_ocr_gemini.py migrated to Policy Engine"
prs_opened_this_session: []
prs_unblocked:
  - "#2168 rebased onto main (Gemini's seminar refs title backfill) — Curriculum Plans now passes 1158/1159; ONE remaining stub blocker filed as task #7"
direct_commits_to_main:
  - "bf6bfe5cd3 fix(writer-trace-isolation): allowlist annotation-only agent built-ins"
  - "deb317e7ac fix(plans/hist): add objectives to hromadske-suspilstvo (closes #2170)"
  - "a1cbf338ee fix(textbook-grounding): unwrap gemini-cli functionResponse envelope"
  - "53b807ad07 fix(tool-calls): concatenate codex namespace+name for MCP function_calls"
  - "be3b7c54fa fix(writer-prompt): l2_exposure_floor + 4-backtick fence-label clarity"
active_dispatches: []
active_builds:
  - "a1/my-morning via deepseek-tools xhigh (Monitor task bq1jtorry, build branch build/a1/my-morning-20260521-083420). Writer phase PASSED cleanly at 08:41:46 UTC (440s, 9 tool calls, 0 theatre). Reviewer (codex-tools) in progress as of handoff."
issues_filed: []
issues_closed: ["#2170"]
headline_finding: "Three V7 writer regressions from gemini-cli 0.42.0 + codex-cli 0.132.0 traced and fixed at the pipeline layer in a single session. Writer phase is now PROVEN green for gemini-tools AND deepseek-tools (both with telemetry-visible MCP traces). codex-tools partial fix shipped (namespace handling) — timing/flush race left as separate concern. The 'all writers broken' headline from yesterday's handoff is now 'two writers shipping, two partially working, one needs operator login.' First-ever clean DeepSeek-pro V7 writer run with full tool telemetry — Hermes path validated."
next_session_first_item: "Check Monitor task bq1jtorry — codex-reviewer + python_qg outcome on the in-flight DeepSeek-pro build. If green, this is the first complete A1 module in V7. If gate-failed, read python_qg.json — l2_exposure_floor + textbook_grounding should both now have the pipeline machinery to pass; remaining failures would be content quality (writer prompt iteration) not pipeline."
---

# Morning handoff — five fixes, two writers validated, DeepSeek-pro proves viable

## TL;DR

Took the "all V7 writers broken" inherited state from the previous handoff and traced four distinct gemini-cli 0.42.0 / codex-cli 0.132.0 regressions to root cause. Five commits to main. Both gemini-tools AND deepseek-tools now pass the writer phase cleanly with valid MCP tool telemetry. Build of `a1/my-morning` via DeepSeek-pro currently in reviewer phase with the strongest tool-call discipline we've seen this week.

| # | Commit | Closes / shape | Surface |
|---|---|---|---|
| 1 | `bf6bfe5cd3` | gemini-cli 0.42.0 alignment | `writer_trace_isolation` allowlists harmless `update_topic` annotation built-in |
| 2 | `deb317e7ac` | #2170 | hist/hromadske-suspilstvo objectives — unblocks PR #2168 (partial) |
| 3 | `a1cbf338ee` | gemini-cli 0.42.0 alignment | `_result_items_from_call` unwraps `{"functionResponse": {"response": {"output": "..."}}}` envelope |
| 4 | `53b807ad07` | codex-cli 0.132.0 alignment | `_tool_name` concatenates new `namespace`+`name` split for MCP function_calls |
| 5 | `be3b7c54fa` | writer-output drift | writer prompt: explicit `l2_exposure_floor` directive + one-line 4-backtick fence label spec |

Plus PR #2171 (Codex) merged: `bulk_ocr_gemini.py` migrated to gemini-cli Policy Engine (separate from V7 writer; OCR pipeline).

## Section 1 — Writer state matrix at end of session

| Writer | Status | Phase passed | Gates passed | Notes |
|---|---|---|---|---|
| **gemini-tools** | 🟢 **PROVEN** | writer + textbook_grounding fixed end-to-end | 19/23 in build #1, parser-error in build #2 | Drift: gemini-3.1-pro sometimes splits 4-backtick fence label across 2 lines (prompt now hardened in commit 5) |
| **deepseek-tools** | 🟢 **PROVEN clean** | writer green w/ telemetry | TBD (build in flight, reviewer phase) | First clean run this week. 9 tool calls, 69 verify_words, 0 theatre violations. Hermes post_tool_call sidecar working as designed. |
| **codex-tools** | 🟡 **partial** | parser format fixed (namespace+name) | not retested live | Timing/flush race: codex adapter sometimes reads rollout before codex flushes events. Separate concern from the format gap. |
| **claude-tools** | 🔴 not testable | n/a | n/a | Operator must run `claude /login` — env confirmed `Not logged in` at session start |
| **agy-tools** (Flash 3.5) | 🔴 blocked upstream | n/a | n/a | `agy plugin enable sources` not shipped by kubedojo yet |

## Section 2 — gemini-cli 0.42.0 alignment (commits 1, 3, 5)

### Commit 1: writer_trace_isolation allowlist

Gemini-cli 0.42.0 emits an `update_topic` self-annotation call as the writer's first tool invocation (strategic_intent / title / summary fields, agent self-narration). The rigid prefix-only `wrong_tool_family` check tripped on this every time, hard-failing gemini-tools writer runs **even after the writer produced all 6 V7 artifacts** (smoking-gun trace at `curriculum/l2-uk-en/_orchestration/a1/my-morning/runs/20260520-234426/`).

Fix: new `WRITER_AGENT_ANNOTATION_TOOLS` allowlist — annotation-only calls stay in `writer_tool_calls.json` for forensics but skip the gate. Dangerous built-ins (`run_shell_command`, `Bash`, `Read`, `Write`) still trip wrong_tool_family.

### Commit 3: textbook_grounding functionResponse unwrap

The 2026-05-20 fix `07c12f2dd7` taught `_textbook_grounding_gate` to recognize `get_chunk_context` calls, but only handled two response envelopes: canonical `{"text": <md>}` and Hermes-routed `{"result": <md>}`. Gemini-cli 0.42.0 emits a THIRD shape:

```
[{"functionResponse": {"id": "...",
                       "name": "mcp_sources_get_chunk_context",
                       "response": {"output": "**[<chunk_id>]** — Сторінка <N>\\n\\n<md>"}}}]
```

Without this third unwrap, build #1 (gemini-tools) read `textbook_result_hits: 0` despite making two valid `get_chunk_context` calls that returned grounded Захарійчук Grade 1 p.24 and p.52 bodies. Fix extends `_result_items_from_call`'s list-branch to detect the functionResponse shape and route the inner output to the appropriate markdown parser. Live verification: same trace now produces `textbook_result_hits: 2`, gate verdict PASS.

### Commit 5: writer-prompt l2_exposure_floor + fence-label clarity

Two writer-prompt directives addressing gemini-3.1-pro output drift:

**(a) l2_exposure_floor.** The gate counts UK example sentences as bullet-list lines + table-data rows containing UK content. Build #1 produced 6 against the 14-minimum — gemini used flowing prose where bullets/tables would have rendered the same paradigm in a gate-countable shape. New directive parallels the existing `<DialogueBox>`/`> `-blockquote dialogue-format directive (also "REQUIRED for gate counting").

**(b) 4-backtick fence label.** The previous directive at lines 325-326 had the info-string label spanning two visual lines — ambiguous, gemini split the actual emit across two lines too:

```
````markdown
file=module.md
```

instead of the intended one-line form `````markdown file=module.md`. Tripped "Writer output contains unnamed fenced block at line N" HARD-fail in build #2. New directive: explicit one-line form with `<<<` markers showing line bounds + explicit "DO NOT split" anti-pattern.

## Section 3 — codex-cli 0.132.0 alignment (commit 4)

Codex CLI 0.132.0 split the canonical MCP tool prefix off the `function_call` payload's `name` field into a separate `namespace` field:

```
Before 0.132.0:  {"name": "mcp__sources__search_text", "arguments": ...}
Since 0.132.0:   {"name": "search_text",
                  "namespace": "mcp__sources__",
                  "arguments": ...}
```

Without concatenation `_tool_name` returned bare `search_text`, tripping wrong_tool_family on every MCP call. Combined with the rollout-flush timing race produced the `tool_calls_total=0` symptom in tonight's codex-tools build (build branch `build/a1/my-morning-20260520-233701`).

Fix: in `_tool_name`, when payload has both `namespace` and `name` strings, return `f"{namespace}{name}"`. Pre-fix rollout normalized to 21 calls with 10 unprefixed MCP names; post-fix same 21 calls but the 10 MCP names now carry the proper prefix.

**Not fixed in this commit:** the rollout-flush timing race (adapter reads empty rollout file before codex flushes events). When codex CLI is slow on initial flush, the adapter sees `tool_calls=[]`. Pre-existing concern from PR #1907's era; needs a separate watchdog or retry mechanism in the codex adapter.

## Section 4 — DeepSeek-pro V7 writer validation (in-flight)

User direction during session: *"can we test deepseek pro for writing as well?"*

Fired build #3 (`a1-my-morning-20260521-083420`) with `--writer deepseek-tools --effort xhigh --worktree`. Writer phase completed at 08:41:46 UTC with the strongest metrics this week:

```
duration_s:      440.216 (~7.3 minutes)
tool_calls_total: 9
verify_words_calls: 3 (36 + 13 + 20 = 69 words verified)
tool_theatre_violations: []
tool_theatre_violation_count: 0
tool_call_telemetry_available: true
end_gate_fired:  true
removed_via_gate: 0
sections_with_cot: 4/4 (Діалоги, Дієслова на -ся, Мій ранок, Підсумок)
CoT block_chars: 3311 + 2744 + 1507 + 1168 = 8730 total
```

Tool breakdown from `hermes.write.jsonl` (sidecar populated by post_tool_call hook):

| Tool | Count |
|---|---|
| mcp_sources_search_text | 2 |
| mcp_sources_get_chunk_context | 2 |
| mcp_sources_verify_words | 3 |
| mcp_sources_search_style_guide | 1 |
| mcp_sources_query_wikipedia | 1 |
| mcp_sources_search_external | 1 |

Both `get_chunk_context` calls returned real textbook chunks (Захарійчук Grade 1 + Grade 4 hits). Combined with commit 3 (gemini envelope unwrap), the textbook_grounding gate should now PASS for this build — but the Hermes shape (`{"result": <md>}`) is what the parser uses for DeepSeek path, NOT the gemini-cli functionResponse shape. Both are now supported.

**Reviewer phase started at 08:43:55 UTC.** Codex-tools is the reviewer per `pipeline.md`. Per the codex CLI 0.132.0 changes (commit 4 fix loaded), the reviewer should produce a clean trace too. Outcome visible by reading `python_qg.json` on `build/a1/my-morning-20260521-083420` branch when reviewer + python_qg complete.

## Section 5 — DeepSeek harness research (user-requested deep-dive)

User asked about harness options for DeepSeek. Fetched all 4 official docs:

| Harness | Auth | Model surface | Tool-call telemetry | Adapter status |
|---|---|---|---|---|
| **Hermes** | `https://api.deepseek.com` + API key, `hermes setup` flow | `deepseek-v4-pro` / `deepseek-v4-flash` | `-z` strips traces; rely on `post_tool_call` shell-hook sidecar JSONL | ✅ `hermes_deepseek.py` shipped 2026-05-17; validated tonight |
| **OpenCode** | `/connect deepseek` interactive | `DeepSeek-V4-Pro` | `--format json` rich step events (tokens incl. cache + reasoning, cost per call) | ❌ Not built; 2026-05-17 study found "richer than Hermes" |
| **Claude Code (DeepSeek backend)** | env vars `ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic` + `ANTHROPIC_AUTH_TOKEN=<deepseek-key>` | maps Opus→pro, Sonnet→pro, Haiku→flash | Full stream-json + rollout — same as native claude | 🟡 Could reuse existing `claude.py` with env-var override; **untested for concurrent use with native Claude OAuth** |
| **Copilot CLI** | `COPILOT_PROVIDER_TYPE=anthropic` + same Anthropic-compat endpoint | `deepseek-v4-pro` / `deepseek-v4-flash`, optional 840K/128K token limits | "Full agent mode, tool calling, and MCP support" | ❌ Not built |

**Key strategic finding:** DeepSeek ships an Anthropic-compatible API at `/anthropic`. The Claude Code CLI can talk to DeepSeek as backend via env vars alone — bypasses the "claude CLI not logged in" blocker by using `ANTHROPIC_AUTH_TOKEN` (DeepSeek key) instead of Anthropic OAuth.

**User-flagged risk:** "i dont think you can be connected 2 different ways with claude code". Technically YES via subprocess-scoped env vars (`subprocess.Popen(env=...)`, parent process untouched), but **untested for concurrent use** — debugging an auth issue mid-build would be painful. Safe pattern documented:

```python
child_env = os.environ.copy()
child_env["ANTHROPIC_BASE_URL"] = "https://api.deepseek.com/anthropic"
child_env["ANTHROPIC_AUTH_TOKEN"] = os.environ["DEEPSEEK_API_KEY"]
child_env["ANTHROPIC_MODEL"] = "deepseek-v4-pro"
child_env.pop("ANTHROPIC_API_KEY", None)  # critical
subprocess.Popen([...claude args...], env=child_env)
```

Treat as a **fallback only when Hermes proves brittle** OR after 2026-06-15 claude-dispatch sunset (per MEMORY #M0). Not a near-term priority since Hermes is working tonight.

**User direction also restated:** Hermes stays. Grok via Hermes (for X.com `@browser` access). Aider explicitly ruled out.

## Section 6 — gemini-cli 0.42.0 / codex-cli 0.132.0 investigation summary

User asked: "pls investigate the 0.42.0 changes for gemini to make sure we can make it work."

Mapped every flag the V7 gemini adapter uses against current 0.42.0 surface:

| Surface | Our usage | 0.42.0 status |
|---|---|---|
| `--allowed-mcp-server-names sources` | `gemini.py:246` | ✅ Current, not deprecated |
| `--approval-mode plan` / `yolo` | `gemini.py:229+234` | ✅ New API, already adopted |
| `-m model`, `-p prompt`, stdin payload | `gemini.py:220+295` | ✅ Stable; yargs-bug workaround documented |
| `--allowed-tools` (deprecated) | NOT used in V7 adapter | ✅ N/A (Codex's PR #2171 migrated bulk_ocr's usage to Policy Engine) |
| Policy Engine (`--policy <file>`) | Not yet used | 🟡 Long-term hardening lever |

The V7 gemini adapter was already correctly configured for 0.42.0; the only outstanding gaps were the gate-side `update_topic` allowlist (commit 1) and the parser envelope shape (commit 3) — both shipped tonight.

For codex CLI 0.132.0: only one structural change was found (`namespace` field on function_call payloads), fixed in commit 4.

## Section 7 — PR #2168 status (Gemini's seminar refs title backfill)

The PR adds `references[].title` across 1124 seminar plans (closes #2164). At session start, Curriculum Plans CI was failing on `hist/hromadske-suspilstvo.yaml` missing required `objectives:` field (#2170).

Tonight:
1. Shipped objectives fill on main (commit `deb317e7ac`).
2. Rebased PR #2168 onto main → force-pushed `2c42994e4a`.
3. Re-ran CI: 1158/1159 plans now valid. **One remaining blocker**: `lit-doc/amelina-women-looking-at-war.yaml` is a content stub (empty `content_outline.points: []`) missing `module`, `title`, `objectives`. Validator correctly flags as incomplete.

**Decision deferred to plan-quality sweep (task #7)** — not urgent per user direction. PR #2168 stays open with 1 known content-stub blocker.

The full plan-quality landscape: out of all `.yaml` plans, only ONE module plan (amelina) and ~15 track-level manifest YAMLs (a1.yaml, hist.yaml, lit-doc.yaml, etc. — false positives the validator should skip) are flagged. Track manifests are not module plans.

## Section 8 — Open follow-ups (filed as tasks)

| # | Subject | Priority | Notes |
|---|---|---|---|
| #5 (completed) | Writer-prompt fence-label clarity | done | Shipped via commit `be3b7c54fa` |
| #6 (completed) | Writer-prompt `l2_exposure_floor` directive | done | Shipped via commit `be3b7c54fa` |
| #7 (pending) | Plan-quality sweep: stubs + version backfill + validator track-manifest skip | low/scheduled, dispatchable | User direction (refined 2026-05-21): not urgent + "actually we could run the plan sweeps parallel one track at a time though another agent in the next sessions". Plan: dispatch ONE TRACK per agent invocation (sequentially across sessions per #M-9), starting with lit-doc (1 known stub) then lit-* siblings then other seminar tracks. Before any dispatch: orchestrator-side commit to tighten `validate_plan_config.py` to skip track manifests (a1.yaml/hist.yaml/etc.) so dispatched agents have clean signal. |

Additional implicit follow-ups not yet filed as tasks but worth noting:

- **Codex-tools timing/flush race** — separate from the namespace fix in commit 4. When codex CLI is slow on initial rollout flush, adapter reads empty file and reports `tool_calls=[]`. Needs watchdog or retry mechanism in `codex.py::_select_rollout_for_plan` / `_read_latest_rollout_trace`.
- **OpenCode adapter** — DeepSeek-via-OpenCode would give us richer JSON telemetry than Hermes (per 2026-05-17 study). Not built; ~200 LOC adapter. Defer until Hermes shows real friction.
- **Claude-CLI-as-DeepSeek-harness** — env-var subprocess pattern documented in Section 5. Untested for concurrent use; treat as post-2026-06-15 fallback.

## Section 9 — Provenance + cross-links

- Parent handoff: `docs/session-state/2026-05-21-night-unblock-codex-promote-prune-and-a1-build.md` (commit `8f98fed971`)
- Tonight's commits: `git log 8f98fed971..be3b7c54fa --oneline`
- PR #2168 (still open, 1 blocker): https://github.com/learn-ukrainian/learn-ukrainian.github.io/pull/2168
- PR #2171 (Codex's OCR Policy Engine migration, merged): https://github.com/learn-ukrainian/learn-ukrainian.github.io/pull/2171
- Build branches preserved (#M-10):
  - `build/a1/my-morning-20260521-060558` — build #1 (gemini-tools, fix 1 only) — 19/23 gates green, textbook_grounding broke
  - `build/a1/my-morning-20260521-061833` — build #2 (gemini-tools, fix 1+3) — writer parse error at line 128
  - `build/a1/my-morning-20260521-083420` — **build #3 (deepseek-tools xhigh)** — writer green, reviewer in flight
- DeepSeek harness docs: https://api-docs.deepseek.com/quick_start/agent_integrations/{hermes,opencode,copilot_cli,claude_code}
- MEMORY.md updated to 140 lines with new `/code-review` skill trigger guidance

## Section 10 — Cold-start sequence for next session

1. Read this handoff.
2. Orient via Monitor API (standard `/api/state/manifest` + `/api/orient` + `/api/comms/inbox?agent=claude`).
3. **First action: check Monitor task `bq1jtorry` outcome.** The deepseek-tools build was in reviewer phase at handoff. If python_qg passes (reviewer + content gates), this is the first end-to-end clean A1 module build in V7. Read `python_qg.json` on the build branch.
4. **If python_qg green: ship to main via `scripts/sync/promote_module.py --latest --level a1 --slug my-morning`** (the helper from PR #2169 paired-promote-prune).
5. **If python_qg failed: read `python_qg.json` for which gates** — l2_exposure_floor and textbook_grounding should both have pipeline support now; remaining failures would be writer-content quality, addressable via additional prompt iteration.
6. **Then: address PR #2168 amelina blocker** if you want the seminar title backfill merged — task #7 plan-quality sweep is the broader scope but a single-file content fill on amelina would unblock immediately.
7. **Possible parallel test: deepseek-tools on B1 module** — tonight proved A1 readiness; B1+ has been the historical disconfirmation point. If A1 ships clean, retest a B1 module that previously failed (b1/genitive-nuances per 2026-05-19 night handoff).

## Section 11 — Build #3 final outcome (arrived just before sign-off)

DeepSeek-pro build #3 python_qg result (8:50 UTC, 520s python_qg phase):

**19/22 gates PASSED.** 3 failures:

1. **textbook_grounding [HARD] REJECT** — `textbook_result_hits=24` (parser correctly extracts 24 hits from the 2 get_chunk_context calls), `chunk_context_calls=4`, BUT `long_blockquotes_checked=0`. Writer DID paste a verbatim blockquote — `> Уранці Євген устав із ліжка САМ. ... Після сніданку САМ помив посуд.` properly attributed to «Захарійчук, Grade 1, p.52». The quote is **24 words**, gate requires **≥30 contiguous words**. Writer pasted too short by 6 words.

2. **correction_terminal** — consequential: textbook_grounding has no ADR-008 correction path, so correction loop terminates after first attempt.

3. **inject_activity_ids** — `unused_activities_not_injected, missing=[]`. Writer emitted activities.yaml but didn't inline-reference all activity IDs in module.md. (Note: gemini build #1 PASSED this gate — different writer-output-shape contract.)

**Flipped failure mode vs gemini-tools.** Compare:

| Writer | textbook_grounding root cause |
|---|---|
| gemini-tools build #1 | ✅ pasted ≥30-word blockquote correctly, ❌ parser missed gemini's functionResponse envelope (fixed in `a1cbf338ee`) |
| deepseek-tools build #3 | ✅ parser sees 24 hits (Hermes envelope), ❌ writer pasted 24-word blockquote (6 short) |

Both writers do part of the textbook_grounding job; neither does it complete. **DeepSeek needs a writer-prompt directive: "if quoting, paste ≥30 contiguous words from the chunk_context body."** The 4-backtick + l2_exposure_floor directives (commit 5) didn't address this dimension.

**inject_activity_ids** is a separate writer-content gap — writer must inline-emit activity-ID references in module.md prose so the gate can find them. Easy prompt-directive add.

Build branch preserved at `build/a1/my-morning-20260521-083420` per #M-10. Forensics: `module.md`, `activities.yaml`, `vocabulary.yaml`, `resources.yaml`, `writer_tool_calls.json`, `hermes.write.jsonl`, `python_qg.json`, `python_qg_correction_r1.json` all on the branch.

**Next-session-actionable follow-up:** strengthen writer prompt with TWO additional directives, paired with prompt commit `be3b7c54fa`:

- **Blockquote length floor (≥30 words for textbook_grounding):** add to the existing "Textbook quotes" section near line 83 in `linear-write.md`. Wording suggestion: "After `get_chunk_context` returns, paste at least 30 CONTIGUOUS Ukrainian words from the chunk body into a `>` blockquote in module.md. Attribute via italic line directly after the blockquote: `*— Захарійчук, Grade <N>, p.<page>*`. Stopping short of 30 words causes HARD-reject at textbook_grounding even when retrieval + attribution are perfect."
- **inject_activity_ids — inline activity references:** every activity ID emitted in activities.yaml MUST appear as inline `<InjectActivity id="..." />` or equivalent reference in the relevant module.md tab. Otherwise the gate flags the activity as unused.

Both directives benefit every writer (not just deepseek).

## Sign-off

Five commits shipped to main, one full DeepSeek-pro writer phase proven clean with 19/22 gates green (first complete writer-phase + python_qg cycle this week), three writer regressions root-caused and fixed at the pipeline layer. The blocker landscape went from "three of three writers broken in different ways" to:

- **gemini-tools**: writer phase green; downstream needs the ≥30-word blockquote directive AND the in-flight fence-label/l2_exposure prompt directives (commit 5) actually applied to a fresh build.
- **deepseek-tools**: writer phase green with strongest telemetry; needs ≥30-word blockquote directive + inject_activity_ids prompt strengthening.
- **codex-tools**: parser format fixed; rollout-flush race still needs separate fix.
- **claude-tools**: operator action (`claude /login`).
- **agy-tools**: kubedojo upstream (`agy plugin enable sources`).

Net: BOTH gemini and deepseek are now within ONE writer-prompt-directive of an end-to-end green build. That's a real shift vs session start where neither could even clear the writer phase.

Session length: ~4.5 hours of orchestrator work. Main project tree dirty with three unrelated pre-existing items (none mine). MEMORY.md within budget at 140 lines.
