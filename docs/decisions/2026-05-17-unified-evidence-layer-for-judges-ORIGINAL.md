# DECISION REQUIRED — How to "unify" the evidence layer between Russianism judges (Python script) and writers/reviewers (Claude Code MCP tools)?

**Status:** PROPOSED
**Surfaced:** 2026-05-17 overnight, while planning brief item 7 from `docs/session-state/2026-05-17-merge-cascade-and-evidence-layer-brief.md`
**Source:** Previous Claude session's handoff ("Refactor `scripts/audit/_judge_eval_lib.py` — replace inline DB queries with `mcp__sources__*` calls so judges use the same evidence layer as writers/reviewers")
**Scope:** `scripts/audit/_judge_eval_lib.py` retrieval functions (`retrieve_antonenko`, `_antonenko_fulltext_search`, `_heritage_check`, `_russian_shadow_check`, `_vesum_unknown`, `_ua_gec_calque_search`) + the MCP server's mirror tools (`mcp__sources__search_style_guide`, `mcp__sources__search_text`, `mcp__sources__search_heritage`, `mcp__sources__check_russian_shadow`, `mcp__sources__search_ua_gec_errors`, `mcp__sources__verify_word`). Does NOT touch the judge prompt, the calibration matrix runner, or downstream scoring.

---

## What's being proposed

The previous handoff said "replace inline DB queries with `mcp__sources__*` calls." But the implementation path is ambiguous, because **`mcp__sources__*` tools are Claude Code-side MCP tools** — they can only be called from inside a Claude Code session, not from a standalone Python script. The calibration matrix runs as `python scripts/audit/judge_calibration_matrix.py`, not inside Claude Code.

Three concrete interpretations of the handoff's intent:

| Option | Implementation | Pros | Cons |
|---|---|---|---|
| **A** — RPC the MCP server | Wrap each Python retrieval call in an HTTP/stdio call to the running MCP server at `:8766`. The Python script becomes an MCP client. | Cheapest by LOC count; literal "use the same MCP" reading. | Adds a runtime dependency on the MCP server being up. Adds HTTP/stdio hop per query (slow). Effectively introduces a network boundary for what's currently a SQLite read. Calibration runs may break if MCP server crashes/restarts. **Architectural smell**: same machine, same DB, same caller → why proxy through HTTP? |
| **B** ⭐ — Extract shared retrieval module | Pull the actual retrieval logic out into a new `scripts/sources/` package (or similar). BOTH the MCP server AND the calibration script import from it. The MCP server becomes a thin protocol-translation wrapper; calibration calls Python functions directly. | The right architecture for "unified evidence layer": one code path, two callers. Easy to test (no MCP roundtrip in tests). Future writer/reviewer integration is identical. | Multi-PR refactor: each retrieval surface needs to move + tests need to update + MCP server changes shape. Non-trivial. Risks: import cycles, packaging questions, MCP server downtime during migration if not staged carefully. |
| **C** — Drop the refactor | Document the divergence between the MCP server's retrievers and `_judge_eval_lib.py`'s retrievers. Accept that they share the underlying DB but have separate code paths. Set a checklist invariant ("when adding a new evidence channel, update both"). | Zero implementation cost. Stays close to current shape. | Long-term: drift between the two implementations. The handoff specifically called this out as a concern. Bug fixes (like #2050 just shipped) have to be applied twice. The dispatch test for H3a's marker filter does NOT automatically propagate to the MCP `search_text` tool. |

---

## Recommendation

**Option B**, staged across 2-3 PRs:

1. **PR1** — Create `scripts/sources/antonenko.py` with `retrieve_keyed`, `retrieve_fulltext`, and the H3a marker-narrowing logic. Migrate `_judge_eval_lib.py`'s 2 Antonenko functions to wrappers calling the shared module. MCP `search_style_guide` / `search_text(antonenko-davydovych-yak-my-hovorymo)` continue using their existing paths in this PR — staged migration.
2. **PR2** — Migrate MCP server's Antonenko tools to call `scripts/sources/antonenko.py`. Now BOTH callers use the same code. Verify equivalent behavior with a contract test.
3. **PR3** — Repeat for `heritage`, `russian_shadow`, `vesum_unknown`, `ua_gec_calque`. One channel per PR.

This keeps each PR small, reversible, and contract-testable.

**Why not A:** The HTTP boundary adds latency and a runtime dependency for no real benefit when caller + server are the same process tree on the same machine reading the same SQLite file. The MCP boundary makes sense for `claude-code` ↔ `MCP server` where the boundary IS the value (sandbox, permissions). For `python script` ↔ `MCP server` on the same machine, it's just an unnecessary wrapper.

**Why not C:** The whole H1/H2/H3 calibration arc was motivated by inconsistencies between what writers/reviewers see and what judges see. Locking in two parallel code paths cements the inconsistency forever. The maintenance cost of "update both places, always" loses to the cost of one careful refactor.

---

## Open question for sign-off

If Option B, **what's the package name and layout?**

Default: `scripts/sources/__init__.py` re-exports from per-channel modules
(`antonenko.py`, `heritage.py`, `russian_shadow.py`, `vesum.py`,
`ua_gec.py`). Each module is sqlite-only, no MCP awareness. The MCP
server (which currently lives at `scripts/mcp_sources/`) imports from
`scripts.sources`.

Alternative: integrate directly into `scripts/mcp_sources/` (the
existing MCP server package) and import the calibration script from
there. Co-locates code; tightly couples calibration to the MCP server
package.

Default (separate `scripts/sources/`) recommended — keeps the MCP
server as a thin wrapper around a generic Python evidence library that
anyone can call.

---

## Acceptance criteria for the experiment

- A single contract test (`tests/sources/test_mcp_judge_parity.py`) runs the same input through BOTH the MCP server tool and the `scripts/sources/` direct call, asserting byte-identical results.
- The judge calibration matrix produces a different result than today only if the channel logic actually changed; this PR series should be behavior-preserving.
- The H3a marker-narrowing (just landed in PR #2063) propagates to MCP `search_text` filtering automatically (one of the concrete wins: a writer asking the MCP for Antonenko prose will get the same high-precision retrieval as the judge).

---

## ADR-007 / decision-graph collision

None known. This refactor doesn't touch reviewer-as-fixer policy (ADR-007), writer-of-the-moment selection (`docs/decisions/2026-05-06-writer-selection-codex-gpt55.md`), or any other live decision card. The only adjacent active decision is `docs/decisions/2026-05-14-agent-sdk-adoption.md` (which is on hold per the predecessor brief), and it doesn't constrain this work.

---

## Default if no decision is taken

If sign-off doesn't land in N days (suggest 7), the orchestrator should re-raise rather than acting on a default. Option B is recommended but multi-PR refactors of evidence-layer infrastructure should not happen without explicit go-ahead.
