# Grok read-only review — vote on unified evidence layer Decision Card

You are participating in a 4-agent decision sign-off. Codex and Gemini have already voted; you are the third agent. The orchestrator (Claude) will weigh in fourth.

## Read these in order

1. **Decision Card** — `docs/decisions/pending/2026-05-17-unified-evidence-layer-for-judges.md`. Read in full (~80 lines).

# venv symlinked into worktree by delegate.py
2. **Channel thread** — `docs/agent-channels/evidence-layer-unification-2026-05-17/` if it exists on disk, OR run `.venv/bin/python scripts/ai_agent_bridge/__main__.py channel tail evidence-layer-unification-2026-05-17 -n 10` to see existing Codex + Gemini votes (both voted B with caveats).

3. **Live MCP server source** — `.mcp/servers/sources/server.py` (Codex pointed out the Decision Card's path `scripts/mcp_sources/` is stale; confirm).

4. **The Antonenko retrieval function being refactored** — `scripts/audit/_judge_eval_lib.py:278` area (the H3a marker-narrowing logic Codex referenced).

5. **The other existing SQLite source API** — `scripts/wiki/sources_db.py` (Codex flagged this as the at-risk "third evidence layer" if we copy instead of consolidate).

6. **ADR collisions raised by Codex + Gemini** —
   - `docs/architecture/adr/adr-005-wiki-knowledge-base.md:55` (no live RAG during WRITE)
   - `docs/architecture/adr/adr-006-compile-layer-retrieval.md:37` (wiki-as-consumption at WRITE)
   - ADR-010 (VerificationVerdict / envelope migration)

## Your task — vote with rationale

Reply with a short structured analysis (1-2 pages max):

1. **Vote:** A / B / C / something-else. End with explicit `VOTE: <letter>` line.

2. **Top concern with B** (the recommended option) — what's the biggest risk of doing this refactor that Codex + Gemini didn't already cover?

3. **Concrete refinement** — do you agree with Codex's "canonical structured retrieval core" + Gemini's "strict phase-gating at the adapter layer"? Or do you see a cleaner architectural framing? If yes/no, say why in 2-3 sentences.

4. **ADR collision** — is there any ADR or live decision card that Codex + Gemini missed?

5. **Package layout** — `scripts/sources/` (Codex preferred) or co-locate inside the MCP server (Gemini's initial proposal, retracted after path correction)? Or somewhere else? 1-2 sentences.

## Output format

Plain text response is fine — no markdown headers required. End with `VOTE: <letter>` on its own line.

Do NOT modify any files. This is read-only analysis only. The orchestrator will collect your vote from your stdout output and synthesize the 4-vote Decision section.

## Anti-fabrication

- If you can't find a file at the path I gave you, say so explicitly. Don't paper over the gap.
- If the existing channel thread is unreadable, say so. Don't invent the Codex/Gemini votes.
- Quote specific line numbers when you cite a file (e.g., `_judge_eval_lib.py:278`). Don't paraphrase.
