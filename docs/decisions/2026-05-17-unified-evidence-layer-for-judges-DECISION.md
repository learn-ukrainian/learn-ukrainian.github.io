# DRAFT — Decision section (4-agent synthesis) for unified-evidence-layer Decision Card

> **STATUS:** DRAFT awaiting user sign-off. Do NOT move the parent card to `docs/decisions/` until user signs this synthesis.
> **Parent card:** `docs/decisions/pending/2026-05-17-unified-evidence-layer-for-judges.md`
> **Synthesizer:** Claude (orchestrator), 2026-05-17 morning
> **Votes captured:** all 4 agents — Codex, Gemini, Grok, Claude all `[AGREE]` on Option B

---

## Decision

**Adopt Option B.** Extract a canonical structured-retrieval core at `scripts/sources/`. The MCP server (`.mcp/servers/sources/server.py`) and the judge calibration runtime (`scripts/audit/_judge_eval_lib.py`) both become **thin adapters** over the shared core. Migration is staged across **5 PRs** (revised up from the card's "3 PRs" after Grok's surface-size analysis).

### Why Option B (synthesis of 4 votes)

| Voter | Vote | Distinctive contribution |
|---|---|---|
| Codex | B | Premise correct: calibration runner is plain Python, `mcp__sources__*` is the agent tool surface — A adds an unnecessary daemon dependency. Concrete refinement: canonical structured retrieval core, not a third mirror. Path correction: live MCP server lives at `.mcp/servers/sources/server.py`, NOT `scripts/mcp_sources/` (card was stale). |
| Gemini | B | Top concern: Blue Team disruption — Claude relies on MCP continuously; staging must avoid downtime. ADR-005/006 phase-gating: unifying the layer must not regrant writer phases live retrieval. |
| Grok | B | Migration surface LARGER than card states — `scripts/wiki/sources_db.py` already implements `search_style_guide`, `search_heritage`, `search_text` as a separate full SQLite API used by compile. If `scripts/sources/` doesn't consume/replace it, third-mirror failure happens by default. ADR-010 collision is directly adjacent: Phase 3 adds new tools + introduces `envelope.py` to the same `server.py`. |
| Claude | B | Contract test FIRST as PR0 — the H1/H2/H3 calibration arc just stabilized; any refactor of `_judge_eval_lib.py` needs a regression net BEFORE production code moves. Concrete `_phase_gate()` mechanism for runtime ADR-005/006 enforcement. Sequence H3a migration separately (PR1-3 then H3a) so structural changes are independently reviewable. |

### Why not Option A (HTTP/stdio RPC)

Same machine, same SQLite, same caller. The MCP boundary value (sandbox, permissions) does NOT apply when the caller is a Python script in the same process tree. A adds latency + runtime dependency for zero benefit. (Codex, Grok independently flagged.)

### Why not Option C (drop the refactor)

The whole H1/H2/H3 calibration arc was motivated by inconsistencies between writer/reviewer evidence and judge evidence. Locking in two parallel code paths cements the inconsistency forever. (Grok: "C concedes the exact failure mode the H1/H2/H3 calibration arc was built to fix.")

---

## Architecture

```
            ┌─────────────────────────────────────────────┐
            │  scripts/sources/  (canonical core)         │
            │   - antonenko.py  (keyed + fulltext + H3a)  │
            │   - heritage.py                             │
            │   - russian_shadow.py                       │
            │   - vesum.py                                │
            │   - ua_gec.py                               │
            │   - _phase_gate.py  (runtime ADR-005/006)   │
            │   - returns: structured payloads only       │
            │     (list[{source, locator, snippet, score}])│
            └─────────────────────────────────────────────┘
                ▲                                  ▲
                │                                  │
        thin adapter                       thin adapter
                │                                  │
    ┌───────────────────────┐         ┌──────────────────────────┐
    │ .mcp/servers/sources/ │         │ scripts/audit/           │
    │   server.py           │         │   _judge_eval_lib.py     │
    │                       │         │                          │
    │  - protocol translate │         │  - wraps shared funcs    │
    │  - tool registration  │         │  - preserves existing    │
    │  - TextContent render │         │    function signatures   │
    └───────────────────────┘         └──────────────────────────┘
        ▲                                          ▲
        │                                          │
    Claude/agent                          scripts/audit/judge_*.py
    (writer/reviewer)                     (calibration matrix runner)
```

**Critical constraint (Codex+Grok consensus):** the canonical core must SUPERSEDE the SQLite query logic currently in `scripts/wiki/sources_db.py`, not duplicate it. Per-PR plan addresses this explicitly.

---

## Sequencing (5 PRs, revised from card's 3)

### PR0 — Contract test fixture (NEW, per Claude's vote)

- Add `tests/sources/test_mcp_judge_parity.py`.
- For each retrieval channel currently shared (Antonenko, heritage, russian_shadow, VESUM, UA-GEC), assert that the existing `_judge_eval_lib.<func>` and the existing MCP `<tool>` return the same **structured payload** when fed the same input. (Grok+Codex: parity is structured-payload, NOT byte-identical TextContent — MCP renders strings.)
- This is the regression net. PRs 1-4 are validated against it.
- Zero production change in this PR.

### PR1 — Extract Antonenko + `_phase_gate()`

- New file `scripts/sources/__init__.py` + `scripts/sources/_phase_gate.py` + `scripts/sources/antonenko.py`.
- Move `_judge_eval_lib._antonenko_fulltext_search` and `_judge_eval_lib.retrieve_antonenko` body INTO `scripts/sources/antonenko.py`. Existing functions become 1-line wrappers.
- `_phase_gate.py` exposes `enforce(phase: str, *, allow_in_write: bool = False)` raising `WritePhaseRetrievalForbidden`. Every public retrieval function calls it first.
- H3a marker-narrowing logic stays in the existing location for this PR — migration deferred to a separate post-PR4 follow-up so PRs 1-4 are pure structural refactor.
- Contract test from PR0 still green.

### PR2 — Migrate MCP `search_style_guide` to call shared

- `.mcp/servers/sources/server.py` handler delegates to `scripts.sources.antonenko.retrieve_keyed()`.
- TextContent rendering stays in the MCP server (Codex/Grok consensus: adapter responsibility).
- Contract test from PR0 still green.

### PR3 — Per-channel migrations (heritage, russian_shadow, vesum, ua_gec)

- Each channel = one commit inside the PR (or split into 4 PRs if individual reviewer prefers — orchestrator's call).
- Migrate the matching MCP tool to the shared module same shape as PR2.
- Contract test PR0 still green.

### PR4 — Consume / supersede `scripts/wiki/sources_db.py`

- Per Grok's analysis: `scripts/wiki/sources_db.py` already implements parallel SQLite logic for `search_style_guide`, `search_heritage`, `search_text`. After PR3 lands, refactor these so they call `scripts.sources.*` instead of running their own SQL.
- This closes the "third mirror" risk Codex+Grok warned about.
- Compile pipeline tests must remain green.

### Follow-up (separate issue, post-PR4)

- Migrate H3a marker-narrowing (currently `_judge_eval_lib.py:278`) into `scripts/sources/antonenko.py`. This is a behavior-equivalence migration, not a structural one — needs its own test fixtures.
- Coordinate with ADR-010 Phase 3 implementation (new `verify_*` / `review_dim_*` tools): the unified evidence layer should become the substrate for those new tools so they don't introduce yet another retrieval path.

---

## ADR collisions captured

| ADR | Collision | Mitigation |
|---|---|---|
| **ADR-005** (no live RAG during WRITE, `adr-005-wiki-knowledge-base.md:55`) | Not a structural collision (judges run in audit phase), but the shared core MUST never be importable by writer-phase code without runtime guard. | `_phase_gate.enforce(phase, allow_in_write=False)` at every public function entry. Writer-phase code never passes `allow_in_write=True` → blocked at runtime. |
| **ADR-006** (wiki-as-consumption at WRITE, `adr-006-compile-layer-retrieval.md:37`) | Same as ADR-005. | Same `_phase_gate` mechanism. Record in Decision Card that shared core must never be called from writer prompts (Grok suggestion). |
| **ADR-010** (VerificationVerdict / envelope migration) | DIRECTLY adjacent. Phase 3 adds `verify_*` / `review_dim_*` tools to the SAME `.mcp/servers/sources/server.py` (ADR lines 43-46) + introduces `.mcp/servers/sources/envelope.py`. (Grok flagged.) | Sequencing: this Decision Card's PRs land FIRST (or in tight coordination); the unified evidence layer becomes the implementation substrate for ADR-010 Phase 3's new tools. Otherwise both efforts collide on `server.py` edits. Add cross-link in ADR-010's tracking issue. |
| **ADR-007** (reviewer-as-fixer) | None structural. Caveat: contract test PR0 should include "reviewer prompt assembles without raising" assertion to catch shape changes. (Claude suggestion.) | Add the assertion to PR0's test plan. |

---

## Acceptance criteria (REVISED from card)

Original card had 3 acceptance criteria. Revised after votes:

1. **Contract test passes** (`tests/sources/test_mcp_judge_parity.py`) — same input through both MCP server tool and `scripts/sources/` direct call yields the same **structured payload** (NOT byte-identical TextContent, per Codex/Grok refinement).
2. **Behavior-preserving** — judge calibration matrix score must not change between pre-PR0 main and post-PR4 main (any drift is a regression, not an improvement).
3. **Phase-gate enforcement test** — adding a unit test that imports `scripts.sources.antonenko` from a fake writer-phase context and asserts `WritePhaseRetrievalForbidden` is raised.
4. **No third mirror** — by end of PR4, `scripts/wiki/sources_db.py` no longer has its own SQLite query for `search_style_guide` / `search_heritage` / `search_text`; all three call `scripts.sources.*`. (Grok refinement, PR4-specific.)
5. **MCP server downtime ≤ zero** — each PR2/PR3 sub-migration must keep MCP responses functional throughout. CI deploy preview of the MCP server is recommended before merging PR2. (Gemini refinement.)

---

## What to file as follow-up issues if user signs off

- **Issue A:** Track PR0-PR4 sequencing under one umbrella (link this Decision Card).
- **Issue B:** Post-PR4 H3a migration (separate). Owner unassigned.
- **Issue C:** ADR-010 Phase 3 coordination — cross-link in the ADR-010 tracking issue that the unified evidence layer is the chosen implementation substrate.
- **Issue D:** Pre-PR0 audit of `scripts/wiki/sources_db.py` to confirm Grok's claim about the 3 overlapping retrieval surfaces and document the exact functions to be migrated in PR4.

---

## Default if no further sign-off

Per the original card's section: "If sign-off doesn't land in N days (suggest 7), the orchestrator should re-raise rather than acting on a default." This synthesis preserves that — user signs THIS Decision section (or rejects/modifies); orchestrator does NOT silently begin PR0.

---

## What I need from you

ONE of:
- **(a) Sign as drafted.** I move the parent card to `docs/decisions/2026-05-17-unified-evidence-layer-for-judges.md`, append this synthesis as the Decision section, file follow-up issues A-D above, and queue PR0 for dispatch (no execution until you trigger).
- **(b) Sign with modifications.** Tell me what to change in the synthesis (sequencing, scope, package layout, acceptance criteria).
- **(c) Don't sign yet.** Park as DRAFT; orchestrator focuses on m20 + Phase 2b until you return.
