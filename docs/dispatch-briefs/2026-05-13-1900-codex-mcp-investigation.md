# Claude-headless adversarial investigation — #1900 codex MCP catalog visibility

**Issue:** [#1900](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/1900)
**Filed by orchestrator (Claude) after 2026-05-13 morning re-framing**
**Mode:** `--mode read-only` (NO code changes; this is diagnosis-only)
**Model:** `claude-opus-4-7` `--effort xhigh`
**Estimated effort:** 60-120 min (read pipeline, read JSONLs, grep rollouts, formulate hypotheses, file findings)

## Why Claude (not Codex) for this investigation

Codex has been the writer-of-the-moment under test in 3 consecutive bakeoffs and each time produced `tool_calls_total=0`. Asking Codex to diagnose its own MCP visibility is conflict-of-interest: Codex has a stake in the verdict ("it's the prompt's fault" vs "the CLI is misconfigured" vs "the MCP bridge is broken"). Claude-headless is the adversarial slot — it has no skin in the writer-policy game and can read Codex's rollouts as an external auditor would.

## The empirical pattern this investigation must explain

| Bakeoff | Codex writer model | tool_calls_total | Prompt iteration |
|---|---|---|---|
| 2026-05-06 | gpt-5.5, codex-tools | 0 | First version of writer prompt |
| 2026-05-08 | gpt-5.5, codex-tools | 0 | Second iteration (small fixes) |
| 2026-05-12 night | gpt-5.5, codex-tools | 0 | Third iteration — explicit "single-primitive" rewrite at `28417cc3cb` naming each MCP tool and giving a worked example |

Claude-tools in the same 2026-05-12 night bakeoff invoked 4 MCP tools (`verify_words` ×2, `search_text` ×2) with the same pipeline wrapper. So the pipeline configuration was correct; only Codex was blind to the tools.

**The decision-grade question this investigation answers:** is `tool_calls_total=0` because (a) Codex never received the MCP tool definitions in its CLI session, OR (b) Codex received them but ignored them due to prompt-design or training-data-tier reasons, OR (c) Codex called the tools but the telemetry collector missed them.

Each of these implies a totally different fix.

## Verifiable claims this dispatch will produce (per #M-4)

| Claim | Tool that proves it | Output format |
|---|---|---|
| Codex's MCP catalog at writer-startup | `grep -E "mcp_servers\|tools are not exposed\|MCP" batch_state/tasks/logs/codex/<task-id>.stdout.log` from any of the 3 bakeoffs; if not in logs, search the rollout JSONL at `audit/bakeoff-2026-05-12-night/codex.write.jsonl` for `mcp_config_resolved` or tool-list events | Raw grep output, quoted |
| Pipeline MCP config passed to writer | Read `scripts/build/linear_pipeline.py` around `mcp_config_resolved` emission point + `scripts/build/v7_build.py` flag-passing | Code excerpt with line numbers |
| What writer prompt actually told Codex | Read `scripts/build/phases/linear-write.md` (especially the single-primitive rewrite landed `28417cc3cb`) | Exact prompt section quoted |
| Codex CLI MCP-bridge config on this machine | `cat ~/.codex/config.toml \| grep -A5 -i mcp` + `.codex/config.toml` if it exists in-repo | Config diff between Codex's actual config and what the pipeline assumed |
| Whether claude-tools writer received the same MCP slot | `grep mcp audit/bakeoff-2026-05-12-night/claude.write.jsonl \| head -20` | Side-by-side: what claude saw vs what codex saw |
| Final root-cause hypothesis | Synthesized from the above | One of: (a) catalog not delivered, (b) catalog delivered but ignored, (c) telemetry blind — with evidence trail for each ruled-in/ruled-out |

Quote raw output for each line of evidence. "I read the file" without quoted excerpt is treated as hallucination per #M-4.

## Hypotheses to test (in order of prior probability)

Investigate each in turn. For each, state the test, run the test, quote raw output, classify as RULED IN / RULED OUT / INCONCLUSIVE.

### H1 — Codex CLI MCP bridge config is wrong on this machine

The pipeline emits `mcp_config_resolved` and assumes Codex can read it. But Codex's CLI loads MCP servers from its OWN config (`~/.codex/config.toml` or via `--mcp-config` flag). If those don't match `.mcp.json`, Codex sees an empty catalog regardless of what the pipeline pushed.

**Tests:**
- `cat ~/.codex/config.toml | head -100` — does it have an `mcp` / `mcp_servers` section? If yes, does the `sources` entry point at `127.0.0.1:8766/sse` (or whatever URL the running server is on)?
- `cat .codex/config.toml 2>/dev/null` — repo-level override file?
- `codex --help 2>&1 | grep -i mcp` — what MCP flags does the Codex CLI even support?
- `grep -rn "mcp" scripts/agent_runtime/codex*.py scripts/build/v7_build.py | head -20` — how does our runtime pass MCP config to Codex?

### H2 — Pipeline doesn't actually pass MCP config to Codex (only to Claude)

`v7_build.py` and `linear_pipeline.py` may have a writer-specific MCP-config injection path that only fires for the `--writer claude-tools` branch.

**Tests:**
- Read `scripts/build/v7_build.py` start-to-end (it's small) — find writer dispatch and look for MCP-config flag-passing
- Read `scripts/agent_runtime/codex_*.py` and compare to `claude_*.py` for symmetry on MCP flag handling
- Read `scripts/build/linear_pipeline.py` around the `mcp_config_resolved` event emit — confirm it actually wires through to the codex spawn

### H3 — Codex CLI catalog API doesn't recognize SSE-mode MCP servers

The `sources` server is registered with `type=sse` at `127.0.0.1:8766/sse`. If Codex CLI 0.130.0 only supports stdio-mode MCP servers, the SSE one is silently dropped from the catalog.

**Tests:**
- `codex --version` — confirm CLI version
- Codex documentation / release notes for SSE-mode MCP support (Codex CLI on GitHub or via `codex docs` if available)
- Quick sanity: try `ab ask-codex` with a prompt asking Codex to list available MCP tools — what does Codex report?

### H4 — The single-primitive prompt rewrite (28417cc3cb) named tools incorrectly

If `linear-write.md` says `mcp__sources__verify_word` but Codex sees the tool as `verify_word` (server-prefix stripped) or `sources.verify_word` (different separator), the prompt's explicit invocation example would fail to match the actual tool name and Codex would never invoke it.

**Tests:**
- `git show 28417cc3cb -- scripts/build/phases/linear-write.md | head -100` — what tool names does the prompt actually use?
- For comparison: what tool names does claude-tools see in its writer session? Grep `audit/bakeoff-2026-05-12-night/claude.write.jsonl` for tool-call events and quote the literal tool name in the `name` field.

### H5 — Codex CLI tool catalog has a hard cap and the MCP slot is being squeezed out

Codex 0.130.0 may have a max-tool-count limit; if many native tools + browser tools + MCP tools exceed that, the MCP tools may be dropped silently.

**Tests:**
- `codex --help 2>&1 | grep -iE "tool|cap|limit"` — does the CLI document any cap?
- Try a minimal Codex session via `ab ask-codex` with NOTHING but the MCP config injected, ask it to list its visible tools. If 12+ tools show up, H5 is RULED OUT.

### H6 — Telemetry collector simply misses Codex's tool calls

The pipeline's `phase_writer_summary` event computes `tool_calls_total` from a writer-specific event stream. If Codex emits tool-use in a different envelope than Claude (e.g., `<tool_use>` vs `tool_calls` array in the response), the counter never increments even when Codex calls tools.

**Tests:**
- Read the tool-call counting code in `scripts/build/linear_pipeline.py` (grep for `tool_calls_total` and `writer_tool_call`)
- Manually grep `audit/bakeoff-2026-05-12-night/codex.write.jsonl` for any `tool_use` / `function_call` / `mcp_*` event — is there ANY evidence Codex tried to call tools that the pipeline didn't count?

## Cross-comparison artifact required

Produce a side-by-side table in the report:

|  | claude-tools (night bakeoff) | codex-tools (night bakeoff) |
|---|---|---|
| MCP config delivered (event) |  |  |
| Tool catalog size at writer-startup |  |  |
| Tool names visible (sample of 3) |  |  |
| Tools the writer prompt explicitly named |  |  |
| Tool invocations in writer body |  |  |
| Counted in `tool_calls_total` |  |  |

Every cell must have a tool-backed source line citing the grep / file / log that proved it.

## Deliverables

1. **HTML report** at `audit/2026-05-13-codex-mcp-visibility-investigation.html` — per #M-2 (ai → human). Structure:
   - TL;DR (3 sentences max)
   - Each hypothesis → test → verdict
   - The side-by-side table above
   - Root cause (one paragraph)
   - Proposed fix (one paragraph; just the design, not the implementation)
   - "What I did NOT verify" section — honest gaps

2. **Update #1900** with comment linking to the HTML report + summary of root cause + fix proposal.

3. **NEW issue (if root cause is fixable in scope)** — file a fix-implementation issue, NOT a fix PR. Brief should be detailed enough for a fix-implementation dispatch to consume. Title format: `[codex-mcp] {root-cause-shortname} fix`.

4. **NO code changes.** This is read-only.

5. **If hypotheses are inconclusive after the 6 above** — list what additional evidence would be needed and what tool/access provides it. Honest "I don't know" beats fabricated certainty.

## Out-of-scope (do NOT touch)

- ❌ Any change to `linear_pipeline.py`, `linear-write.md`, `v7_build.py`, or `scripts/agent_runtime/`.
- ❌ Rerunning the bakeoff. The artifacts from the night bakeoff are the evidence base.
- ❌ The #1901 OSError fix (separate Codex dispatch in flight on `codex/1901-prepare-query-oserror`).
- ❌ Touching the ADR. The orchestrator (Claude) updates the ADR after the investigation + 4th bakeoff results are in.
- ❌ Recommending we abandon Codex — investigation must produce evidence-based root cause first.

## Anti-fabrication preamble (per #M-4)

Every hypothesis verdict must include:
- The exact command run (with cwd if relevant)
- The raw output of that command (quoted, not paraphrased)
- The verdict (RULED IN / RULED OUT / INCONCLUSIVE) with one-line reasoning that references the raw output

"I checked and it looks like X" without a command + raw output is hallucination per MEMORY #M-4 — treat as such in self-review before writing the report.

## Context files to read FIRST

Before starting investigation:
- `docs/best-practices/deterministic-over-hallucination.md`
- `audit/bakeoff-2026-05-12-night/REPORT.md` (the verdict that triggered this)
- `audit/bakeoff-2026-05-12-night/claude.write.jsonl` (working example)
- `audit/bakeoff-2026-05-12-night/codex.write.jsonl` (failing example)
- `scripts/build/phases/linear-write.md` lines 60-100 (the tool-grounding section)
- `scripts/build/linear_pipeline.py` — grep `mcp_config_resolved`, `writer_tool_call`, `tool_calls_total`

## On finish

Post a single comment on #1900 with:
- Path to the HTML report
- TL;DR (3 lines)
- Top-2 hypotheses RULED IN
- The proposed fix design (one paragraph)
- Whether the fix is mechanical (codex dispatch possible) or architectural (needs another claude investigation)
