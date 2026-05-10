# Gemini-tools deep review — mirror the codex-tools investigation

**Thread tag:** `gemini-tools-deep-review-2026-05-09`
**Predecessor pattern:** `audit/codex-tools-review-2026-05-08/REPORT.md` (CONVERGED — Claude + Codex)
**User hypothesis (still standing):** "Both codex-tools and gemini-tools have bugs, the agents are running in sandbox and cannot use our tools or do not know about our tools and are not using the wiki."
**Outcome of codex-tools review:** ROOT CAUSE = `type="streamable-http"` field rejected by codex CLI → empty MCP catalog → model substituted `exec_command` shell-grep (39-59 calls/run) → pipeline telemetry filtered those out as "0 tool calls". Fix shipped via PR #1813.

The codex-tools fix did NOT touch the gemini-tools path. gemini-tools also produced `writer_tool_calls.json: []`. We do not yet know why. **This dispatch is read-only audit + report writing. No code changes.**

> **Important context (2026-05-09 git hygiene):** Just before this dispatch I committed `cd39544877` which corrected `gemini_extensions/settings.json` from `{"rag", sse, /sse}` back to `{"sources", http, /mcp}` — the LKG config verified by PR #1810 ("Gemini CLI 0.41.2 rejects type=streamable-http but accepts type=http for /mcp; SSE timed out in experiment"). Source-of-truth had bit-rotted but the deploy target `.gemini/settings.json` was clean at the time of the bakeoff. So **the bakeoff in question ran with `{"sources", http, /mcp}`, the verified-working config**. Whatever broke gemini-tools is not the LKG mismatch.

## What we know

From the codex-tools review's E3 table:

| Writer | `writer_tool_calls.json` |
|---|---|
| claude-tools | 5 entries (4× search_text, 1× verify_words([47 words])) — real MCP calls |
| codex-tools | `[]` (root cause: type=streamable-http rejection — fixed by #1813) |
| gemini-tools | `[]` (root cause: ?? — your job) |

## Worktree instructions (mandatory)

Work in a git worktree at `.worktrees/codex-gemini-tools-deep-review`. Do NOT create a feature branch in the main checkout. Concrete setup:

```bash
git worktree add -b codex/gemini-tools-deep-review-2026-05-09 .worktrees/codex-gemini-tools-deep-review
cd .worktrees/codex-gemini-tools-deep-review
# do work, commit, push
```

The main checkout stays untouched on `main`. After PR merges, the orchestrator cleans up the worktree.

## Acceptance criteria

1. **Locate gemini-cli's rollout transcripts.** The codex-tools review used `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl`. Find the gemini-cli equivalent. Likely candidates: `~/.gemini/`, `~/.config/gemini/`, project-local `.gemini/`, or platform-specific dirs. If gemini-cli doesn't persist transcripts at all, document that and adapt the investigation to whatever IS available (e.g., the bakeoff's stdout capture).

2. **Read the bakeoff artifacts:**
   - `audit/bakeoff-2026-05-08-claude-gemini-diagnostic/gemini/` (writer_prompt.md, knowledge_packet.md, writer_tool_calls.json — confirm packet/prompt are byte-identical to claude-tools, just like codex's were)
   - `audit/bakeoff-2026-05-08-claude-gemini-diagnostic/gemini.write.jsonl` (top-level pipeline JSONL)

3. **Find the smoking gun** — direct evidence (preferably from gemini-cli itself articulating the failure mode, like the codex rollout's "requested mcp__sources__... tools 'are not exposed in this session'" line). If gemini-cli is more opaque than codex-cli, document what alternative evidence exists.

4. **Compare the actual gemini config delivery path** to what we know works:
   - `.gemini/settings.json` (now: `{"sources": {"url": "http://127.0.0.1:8766/mcp", "type": "http"}}`) — the file gemini-cli reads
   - How does `linear_pipeline._runtime_tool_config` deliver this to the gemini subprocess? Does it pass `--mcp-config <path>`? Inject env vars? Rewrite the file?
   - For the gemini-tools writer specifically, what config does the model see in its catalog? (gemini-cli likely has a `--list-tools` or telemetry equivalent — find it.)
   - PR #1810 commit message says SSE timed out in experiment; was that experiment with `streamable-http` rejection like codex, or a real SSE-vs-http behavior gap? If it's SSE-specific, what does gemini do with `type=http` + endpoint `/mcp` in practice?

5. **Hypothesis test (without running new builds — user runs builds, not us):**
   - Was the bakeoff's `.gemini/settings.json` already at `{"sources", http, /mcp}` when the writer ran? Verify via git log + bakeoff timestamp + the bakeoff's own captured config-snapshot if any.
   - Is there a layer below settings.json — e.g. an env var GEMINI_MCP_DISABLE, a CLI flag dropping MCP, a per-writer config override that bypasses the file?

6. **Write `audit/gemini-tools-review-2026-05-09/REPORT.md`** mirroring the structure of `audit/codex-tools-review-2026-05-08/REPORT.md`:
   - Executive summary table (layer / status / owner)
   - Evidence section (E1, E2, E3, E4… with file paths and direct quotes)
   - Root cause statement (or, if not found, "next-step required" section explaining what would unblock convergence)
   - Recommended fix (code path, test plan, ABAB if multiple options)
   - Decisively NOT a regurgitation of the codex-tools fix — find what's actually different here.

7. **If the smoking gun maps directly to a code fix ≤ 30 LOC**, include the patch in the report as a recommendation but **do not commit code changes** in this dispatch. Leave the fix for a separate dispatch the orchestrator will fire after Claude reviews this report. (One scope at a time.)

8. **Commit + push + PR:**
   - One commit: `docs(audit): gemini-tools deep review — root cause hypothesis & evidence`
   - Push to `origin codex/gemini-tools-deep-review-2026-05-09`
   - `gh pr create` with title `docs(audit): gemini-tools deep review (#1809-related)` and body that links the report, summarizes the hypothesis, and explicitly tags `decision-pending` if the fix is non-obvious.

## What to NOT do

- **Do NOT** modify `linear_pipeline.py`, `tool_config.py`, `.gemini/settings.json`, or `gemini_extensions/settings.json` in this dispatch. Read-only investigation. (PR #1813 was the codex-tools fix; this is the parallel investigation, not the parallel fix.)
- **Do NOT** run new bakeoff builds. The user is the only one who runs builds. Use existing artifacts.
- **Do NOT** rewrite the codex-tools report's E1-E4 evidence — those facts are already established. Use them as cross-reference, build on them.
- **Do NOT** speculate beyond evidence. If you cannot find the smoking gun, explicitly say so and list the gaps that would resolve it. Honest "we don't know" is more valuable than a confident wrong root cause.

## Pre-flight commands the next agent should run before merge

```bash
# Verify the report's evidence reproduces (paste each command's output back into the report comment thread):
ls audit/bakeoff-2026-05-08-claude-gemini-diagnostic/gemini/
cat audit/bakeoff-2026-05-08-claude-gemini-diagnostic/gemini/writer_tool_calls.json
diff -q audit/bakeoff-2026-05-08-codex-only/gpt55/knowledge_packet.md audit/bakeoff-2026-05-08-claude-gemini-diagnostic/gemini/knowledge_packet.md

# Verify the gemini settings file is at LKG (not the rag/sse rot — that was just fixed in cd39544877):
git show cd39544877 -- gemini_extensions/settings.json .gemini/settings.json
cat .gemini/settings.json
```

## Reference

- Codex-tools converged review: `audit/codex-tools-review-2026-05-08/REPORT.md`
- Last night's HTML handoff: `docs/session-state/2026-05-09-overnight-codex-tools-and-html-migration.html`
- The git hygiene commit that just landed: `cd39544877` (closes #1811)
- `MEMORY.md` rule `#M-2`: HTML over markdown for new artifacts. **The report SHOULD be HTML, not markdown** — apply the parchment template from the handoff above. Markdown is acceptable as a fallback if it makes investigation faster, but HTML is the goal per #M-2. (Codex-tools' report is markdown only because it predates the policy.)

Effort: high. Model: default (gpt-5.5). No `--model` flag.
