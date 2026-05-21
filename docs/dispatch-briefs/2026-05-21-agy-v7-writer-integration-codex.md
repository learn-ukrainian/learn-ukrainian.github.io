# Dispatch brief — agy V7 writer integration (telemetry + prompt directives)

**Agent**: codex (gpt-5.5, xhigh)
**Mode**: danger
**Worktree**: `.worktrees/codex-agy-v7-integration-2026-05-21`
**Task ID**: `agy-v7-integration-2026-05-21`
**Created**: 2026-05-21
**Supersedes**: `docs/dispatch-briefs/2026-05-21-agy-mcp-telemetry-shim-codex.md` (cancelled before any commits)

## Why

agy has been verified deterministic-tool-calling against the MCP `sources` server on 2026-05-21. Four-call adversarial probe (fake tool name + nonsense word + 2 real verbs with non-obvious VESUM tags) matched the server's live output byte-for-byte through agy's native `call_mcp_tool` integration. Detailed evidence on the per-machine MEMORY entry for this session.

The morning's prior "agy uses curl-via-Bash for MCP" assumption is **obsolete**: agy now has a native `call_mcp_tool` integration that talks to the MCP server directly. The Bash(curl) shim brief (filed earlier today, cancelled) targeted the wrong code path.

Remaining gap for V7 writer promotion:

1. **Telemetry parse.** agy emits its tool-call markers in some shape (likely `● mcp_sources_<method>(...)` plus a `⎿ <result>` line — verify from a live probe before coding). The pipeline's writer_tool_calls.json builder doesn't yet detect agy's marker shape, so gates that count named MCP calls (`verify_words`, `search_text`, `get_chunk_context`) won't see agy's usage.

2. **Output shape mismatch.** agy's `call_mcp_tool` returns a parsed JSON view ("structured" by default) rather than the MCP server's raw markdown-text payload. The pipeline parses the markdown payload (see e.g. `_textbook_grounding_gate`'s logic around `get_chunk_context` returns), so for agy we need the writer prompt to demand verbatim raw text output, not the parsed view.

3. **Sandbox directives.** A separate sandbox-enforcement probe is in flight (see latest agy-v7-readiness bridge thread). Whatever the outcome, the writer prompt for agy needs explicit "MCP-only / no bash beyond curl-fallback / no sqlite3 / no scripts / no codebase grep" directives — the agy CLI's `--dangerously-skip-permissions` flag is a blanket-yes; without per-tool restrictions in the prompt, agy will side-investigate when MCP retrieval comes up short (observed today, build #4 worktree forensics).

## What

### Step 0 — observe before coding (mandatory)

Before writing any parser, run a small agy probe and capture its stdout to a file. Examples:

```
cd /Users/krisztiankoos/projects/learn-ukrainian && \
  agy -p --dangerously-skip-permissions \
    "Call mcp_sources_verify_words with arguments {\"words\":[\"стіл\",\"ранок\"]}. \
     Output the verbatim MCP response text." \
    > /tmp/agy-marker-sample.txt 2>&1
```

Read `/tmp/agy-marker-sample.txt`. Identify the marker characters that bracket each tool call (likely `●` U+25CF and `⎿` U+23BF based on earlier captures, but with native MCP the surrounding text may differ from the curl-via-Bash shape). Document the shape in a PR-body section titled "Marker shape observed" with literal samples.

### Layer 1 — telemetry parser

1. In `scripts/agent_runtime/adapters/agy.py`, extend `parse_response` to also produce synthesized `tool_calls` entries (or whatever the existing field name is on `ParseResult` — check `scripts/agent_runtime/result.py`).
2. Parse agy stdout for the canonical marker pair (`●` opening + `⎿` result), matching only those where the tool name starts with `mcp_sources_`. Bash, file-read, file-write, and other markers can stay unparsed — we don't synthesize for non-MCP work.
3. For each MCP-named marker, extract the tool name (stripping the `mcp_sources_` prefix is acceptable; check what shape other adapters emit), the args dict (from the `(...)` argument list — note this may be agy-specific structured JSON, not a curl `-d` body), and the result text (from the `⎿` line until the next blank line or next `●`).
4. Synthesize an entry that matches the shape claude-tools / gemini-tools emit in `writer_tool_calls.json`. Use `build/a1/my-morning-20260521-101042/curriculum/l2-uk-en/a1/my-morning/writer_tool_calls.json` as the reference shape (claude-tools, 21/22 build today).

### Layer 2 — writer-prompt directive

1. In `scripts/build/phases/linear-write.md` add a writer-specific section gated by writer kind. If `linear_pipeline.py` doesn't already support per-writer prompt blocks, add minimum scaffolding (a `{WRITER_SPECIFIC_DIRECTIVES}` placeholder filled by the pipeline from a Python dict mapping writer name → directive block; empty for writers without a custom block).
2. The agy directive block must include:
   - "Use `mcp_sources_*` tools directly. Do NOT issue curl-via-Bash for MCP retrieval — your native integration is wired."
   - "After each MCP call, emit the verbatim TEXT field from the server's response (the markdown-text payload inside `content[0].text`). Do NOT substitute your parsed JSON view of the response — the pipeline parser expects the raw payload format."
   - "If an MCP retrieval returns 0 hits or the wrong page, emit a `<!-- VERIFY: ... -->` marker in the artifact and continue. Do NOT side-investigate via `sqlite3`, codebase grep, `python` scripts, or any other path outside MCP."
   - "Allowed bash: NONE except `curl` against `http://127.0.0.1:8766/mcp` as a fallback when the native integration returns an error."
   - "Allowed file operations: read/write ONLY within the build worktree's `curriculum/l2-uk-en/<level>/<slug>/` directory."
3. Run all 96 existing linear-write tests (see `tests/test_prompt_cot_*` and friends) to confirm the scaffolding doesn't break the existing prompt for claude-tools / gemini-tools / deepseek-tools / codex-tools.

### Touch points

- `scripts/agent_runtime/adapters/agy.py` (~80-120 LOC additions for parser).
- `scripts/agent_runtime/result.py` (only if `ParseResult` needs a new field; current `tool_calls` may already be plumbed).
- `scripts/build/linear_pipeline.py` (if writer-specific prompt sections need scaffolding; preferred path is reusing whatever exists for the current writers).
- `scripts/build/phases/linear-write.md` (add the agy-specific directive block).
- `tests/` — unit tests for the parser using captured agy stdout as fixtures; integration smoke test that runs the prompt assembly for `writer=agy-tools` and asserts the directive block is included.

## Don't

- Don't parse non-MCP markers (Bash, file-read, etc.) into the synthesized tool_calls list. That pollutes the gate counters.
- Don't change other adapters.
- Don't widen `--dangerously-skip-permissions` handling in the agy adapter. If sandbox enforcement needs CLI flag changes, that's a follow-up brief.
- Don't ship without a real-output fixture. Hand-rolled mock fixtures hide marker-shape surprises.

## Verification before commit

```
cd /Users/krisztiankoos/projects/learn-ukrainian && .venv/bin/ruff check scripts/agent_runtime/ scripts/build/ tests/
cd /Users/krisztiankoos/projects/learn-ukrainian && .venv/bin/python -m pytest tests/ -k 'agy or agent_runtime or linear_pipeline or linear_write or prompt_cot' -v --tb=short
```

All green required.

## Commit + PR shape

- **Branch**: `feat/agy-v7-integration-2026-05-21`
- **Single commit**: `feat(agy): V7 writer telemetry parser + prompt directives`
- **PR title**: `feat(agy): wire agy-tools as V7 writer (telemetry + sandbox prompt)`
- **PR body**: include "Marker shape observed" section with literal samples from the Step-0 probe; link this brief; note the prior shim brief was superseded.
- **Do NOT auto-merge.** Orchestrator (Claude) reviews and merges after CI green.

## Steps (mandatory)

1. `git worktree add -B feat/agy-v7-integration-2026-05-21 .worktrees/codex-agy-v7-integration-2026-05-21 origin/main`
2. Run the Step-0 probe and capture marker shape.
3. Implement Layer 1 + Layer 2 per spec.
4. Run verification.
5. Single conventional commit.
6. Push + open PR (no auto-merge).
7. Report task done.

## Anti-fabrication (per #M-4)

Every claim in the report — "tests pass", "ruff clean", "marker shape observed", "PR opened" — MUST be backed by literal command output. A bare "all green" with no transcript is invalid. Especially: include the literal Step-0 stdout sample in the PR body as evidence the parser was designed against real output.
