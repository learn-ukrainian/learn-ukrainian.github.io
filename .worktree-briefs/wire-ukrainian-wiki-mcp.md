# Codex Brief — Wire `ukrainian_wiki` corpus into v6 writer retrieval (MCP + prompt)

**Issue:** filing on completion (label: `priority:high, infrastructure`). Reference EPIC #1365.
**Task ID:** `codex-wire-ukrainian-wiki-mcp`
**Worktree:** `.worktrees/codex-wire-ukrainian-wiki-mcp`
**Branch:** `codex/codex-wire-ukrainian-wiki-mcp`
**Effort:** medium
**Hard timeout:** 5400s

## Why this matters

The 1424-chunk `ukrainian_wiki` corpus (compiled Ukrainian textbook DNA, ingested 2026-04-21) is currently **inert during module builds**. The MCP sources server (`.mcp/servers/sources/server.py`) exposes `search_text`, `search_literary`, etc. — but `search_text` calls `search_textbooks` (textbooks table only), NOT the unified `search_sources` that includes `ukrainian_wiki`.

**Result:** v6 writer (`gemini-tools` / `claude-tools` modes) never retrieves from the Ukrainian wiki corpus. The bootstrap effort doesn't reach the modules. We rebuild against the same retrieval surface as before.

This is THE blocker to starting A1+A2 module rebuilds at the new quality bar.

## Worktree instructions (mandatory)

    git worktree add -b codex/codex-wire-ukrainian-wiki-mcp .worktrees/codex-wire-ukrainian-wiki-mcp
    cd .worktrees/codex-wire-ukrainian-wiki-mcp

DO NOT branch in the main checkout.

## Hard prohibitions

1. **DO NOT MERGE the PR yourself.** Open it only.
2. **DO NOT use `gh pr merge` / `--admin` / `gh pr review --approve`.**
3. **DO NOT modify `_CORPORA` in `scripts/wiki/sources_db.py`** — it already correctly includes `ukrainian_wiki`. The bug is downstream.
4. **DO NOT change the existing `search_text` MCP tool's contract.** It's load-bearing for callers that explicitly want textbooks-only results. Add NEW, don't replace.
5. **DO NOT touch `scripts/wiki/sources_db.py`'s search functions** other than maybe a thin wrapper if needed. The `search_sources` unified entry point already exists and works.

## Read before coding (mandatory)

- `.mcp/servers/sources/server.py` — current MCP tool registrations + handlers (especially `handle_search_text`, the tool list block at the top, and the dispatch dict around line 621)
- `scripts/wiki/sources_db.py:864-920` — `search_sources` unified entry point + signature
- `scripts/wiki/sources_db.py:48-65` — `_CORPORA` constant (proves ukrainian_wiki IS already in the corpora set)
- `scripts/build/phases/v6-write.md` — writer prompt (especially the lines mentioning `mcp__sources__search_text`)
- `.claude/rules/mcp-sources-and-dictionaries.md` — documentation that needs updating

## Acceptance criteria

### AC-1 — Add new MCP tool `search_sources` to the sources server

In `.mcp/servers/sources/server.py`:

- Add tool registration (mirror the shape of `search_text`'s registration block):
  - **Name:** `search_sources`
  - **Description:** "Unified Ukrainian source search across textbooks, literary corpora, Wikipedia, external articles, AND the ukrainian_wiki corpus (compiled Ukrainian textbook pedagogy). Use this for general retrieval when you want all relevant Ukrainian-source content in one query. Use the corpus-specific tools (search_text, search_literary, etc.) only when you need to scope to a single source."
  - **Schema:** mirror `search_text` but add an optional `track` parameter (string, defaults to empty/auto-detect — needed because `search_sources` requires `track=` for query preparation). Keep `query` (string), `limit` (int, default 10).
- Add handler `handle_search_sources(args)` that calls `wiki.sources_db.search_sources(query=..., track=..., limit=...)` — preserving the response-shape pattern other handlers use (TextContent list with structured results).
- Add to the dispatch dict (around line 621).

### AC-2 — Update writer prompt to surface the new tool

`scripts/build/phases/v6-write.md`:

- Find the section that documents available MCP tools (around line 824 onward, where `search_text` is described).
- Add `search_sources` documentation **immediately above** `search_text`. Wording draft:
  > - `{p}search_sources` — **PREFERRED** unified source search across textbooks, literary works, Wikipedia, AND the Ukrainian wiki pedagogy corpus (compiled from Ukrainian textbooks for Ukrainian learners). Use this as your default — it covers the highest-quality decolonized pedagogy first.
- Add a one-sentence note that `search_text` remains available for **textbook-only** scoping when needed.
- Apply the same change to other writer-facing prompts that mention `search_text`: `v6-skeleton.md`, `v6-write-seminar.md`, `v6-review.md`, `v6-research.md` if applicable. Grep for `mcp__sources__search_text` and `{p}search_text` across all prompts.

### AC-3 — Update other tool-instruction docs

`.claude/rules/mcp-sources-and-dictionaries.md`:

- Add `search_sources` to the "Core tools (always use)" list, marked as **PREFERRED unified entry point** with a one-line description.
- Keep the corpus-specific tools listed for explicit-scope use cases.

`scripts/tools/codex_tool_instructions.md` (if it documents search tools):

- Same addition.

### AC-4 — Sanity test

After landing the MCP tool addition:

- Restart the MCP sources server (`pkill -f 'mcp.*sources'` or whatever the standard restart pattern is — check `docs/SCRIPTS.md` or the server's docstring)
- From a fresh Python shell, call `search_sources(query="голосні звуки", track="a1", limit=5)` directly — verify it returns results that include `ukrainian_wiki` rows (look at the `corpus` field or equivalent in the result dicts)
- If the MCP server can be exercised end-to-end (mcp client mock or similar), do that too — but the direct Python call is sufficient evidence.

Document the test command + sample output in the PR body so the reviewer can replicate.

### AC-5 — Adversarial review

```bash
.venv/bin/python scripts/ai_agent_bridge/__main__.py ask-claude \
  "Adversarial review: wiring ukrainian_wiki into v6 writer retrieval via new MCP search_sources tool. Read the diff. Look for: (1) new tool name colliding with anything existing, (2) writer prompt now ambiguous about which tool to use (search_sources vs search_text), (3) new handler missing error handling that other handlers have (timeout, malformed args), (4) docs update missing a referenced location, (5) backward-compat break for callers explicitly using search_text." \
  --task-id wire-ukrainian-wiki-review
```

Address findings. Document any rejected with rationale.

## Workflow

1. Create worktree per worktree instructions
2. Read all 5 files in "Read before coding"
3. Implement AC-1 → AC-2 → AC-3 → AC-4 (one commit per AC is fine, or one combined commit)
4. Run AC-5 adversarial review
5. Push, open PR with title `feat(mcp): add unified search_sources tool — wire ukrainian_wiki corpus into v6 writer retrieval`
6. STOP. Do not merge.

## PR body template

```
## Summary
Wires the `ukrainian_wiki` corpus (1424 chunks, compiled Ukrainian textbook pedagogy, ingested 2026-04-21) into v6 writer retrieval. Previously inert because MCP exposed only `search_text` (textbooks-only); now adds `search_sources` (unified entry point that includes ukrainian_wiki + textbooks + literary + Wikipedia + external).

- AC-1: New MCP tool `search_sources` in `.mcp/servers/sources/server.py`
- AC-2: Writer prompts updated — `search_sources` is now the preferred default
- AC-3: `.claude/rules/mcp-sources-and-dictionaries.md` + `scripts/tools/codex_tool_instructions.md` updated
- AC-4: Sanity test passed — query returns ukrainian_wiki rows
- AC-5: Adversarial review (Claude) — N findings addressed

Backward-compatible: existing `search_text` callers see no behavior change.

## Test plan
- [ ] `pkill -f 'mcp.*sources' && <restart>` — MCP server reloads with new tool
- [ ] Direct python call `search_sources(query="голосні звуки", track="a1", limit=5)` returns ukrainian_wiki hits
- [ ] Smoke test: dispatch one A1 module rebuild via v6_build.py → writer LLM successfully calls `search_sources` and gets ukrainian_wiki content in retrieval results

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

## Done when

PR opened, all 5 ACs documented, adversarial review noted, dispatch reports `done`. User merges. Then we can start canary A1 module rebuild against the now-wired corpus.
