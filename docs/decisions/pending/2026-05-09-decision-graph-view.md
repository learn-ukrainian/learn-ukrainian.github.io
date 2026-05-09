# DECISION REQUIRED - Decision Graph View Paradigm and Layout

**Status:** PROPOSED (awaiting user signoff to ACCEPTED)
**Date:** 2026-05-09
**Authors:** Gemini (drafting), Codex (data collection), Claude (orchestration context)
**Supersedes:** None
**Scope:** Decision Graph view in channels.html — UI toggle, marker parser, matrix layout, drawer; not the underlying DB schema or `ab discuss` broker logic.
**Blocks/Blocked-by:** Blocks Decision Graph UI implementation; ships today against the current `from_agent` schema and remains forward-compatible with docs/decisions/pending/2026-05-06-multi-ui-channel-participation.md participant identity fields. Integrates with D4 decision-lineage backlink scanner (#1785).

---

## Context

The kubedojo team (a sister project) recently compared their dashboard to ours and pitched inverting our `channels.html` UI from being **chat-primary** to being **Decision Graph-primary**, where chat would become a secondary toggle. They offered to upstream their D3 (Decision Graph) PR after implementing it in their own repository.

A 3-way agent review (Codex + Gemini, 2026-05-07) was conducted to evaluate this paradigm shift. The review converged on adopting a **modified version** of their proposal. Specifically, Codex provided verifiable data from our `channel_messages` snapshot (2026-05-07) demonstrating channel marker-thread density:

| Channel | Marker threads | Total threads | % |
|---|---:|---:|---:|
| `architecture` | 32 | 39 | 82% |
| `pipeline` | 2 | 11 | 18% |
| `reviews` | 19 | 83 | 23% |

This data strongly confirms that for ~75-80% of our general channel traffic, a Decision Graph-primary view would be the wrong paradigm. Therefore, the Decision Graph must be implemented as a **toggle**, not as an inversion of the primary IA.

Furthermore, Codex gathered data on round-reply body sizes in the `architecture` channel:
- Average: 2367 chars
- Maximum: 8349 chars

A standard 3-column body-first grid would be completely unreadable with this volume of text. The matrix layout is justified for high-density channels; lighter channels could fall back to body-first or use the same matrix as a uniform UX choice.

This document formalizes the UX and architectural semantics for the Decision Graph view. It is a separate ADR from the pending Multi-UI channel participation ADR because it changes primary IA and marker semantics (meeting the threshold rule for a distinct ADR).

---

## Decision

The Decision Graph view will be implemented under the following paradigm:

*   **Toggle-not-inversion:** Chat remains the primary view. The Decision Graph is a toggleable view that auto-engages under specific conditions.
*   **Outline-first matrix layout:** The graph uses a dense matrix representation (rounds as rows, participants as columns) displaying only markers and brief summaries to accommodate our large average message sizes.
*   **Side drawer UX:** Reading full message bodies relies on a pinnable side drawer to avoid disrupting the matrix context.
*   **Explicit marker semantics:** Deliberation state is strictly derived from standard `[AGREE]` and `[DISAGREE]` markers, with `[OPTION]`, `[OBJECT]`, and `[DEFER]` reserved for future or ADR-specific display.

---

## Q1. When does Decision Graph view auto-engage?

### Proposal
The Decision Graph view should auto-engage (switch automatically from the chat view) when a thread meets **both** of the following conditions:
1.  **Participant-count threshold:** The thread contains messages from **≥2 distinct `from_agent` participants** in the current schema (e.g., `claude` and `codex`; user/human posts count as participants when they use the same channel-message path).
2.  **Marker-density threshold:** The thread contains **≥2 messages** carrying formal deliberation markers (`[AGREE]`, `[DISAGREE]`, or future display markers `[OPTION]`, `[OBJECT]`, `[DEFER]`).

The manual toggle to switch between Chat and Decision Graph views is **always available** on every thread, regardless of whether the auto-engage criteria are met.

### Rationale
Our channel statistics show that marker threads only dominate the `architecture` channel (82%), while `reviews` (23%) and `pipeline` (18%) are predominantly standard chat or single-shot interactions. Auto-engaging requires sufficient signal (multiple agents + multiple markers) to ensure the graph view is only presented when actual deliberation is taking place. Relying on a manual toggle for edge cases provides an escape hatch without enforcing the wrong default paradigm on 80% of threads.

---

## Q2. Layout

### Proposal
The Decision Graph will use an **outline-first matrix layout**:
*   **Rows:** Rounds (1..N).
*   **Columns:** current implementation keys columns by `from_agent` because `channel_messages` currently has `from_agent` but no `agent_family`/`participant_id` columns. After the Multi-UI ADR lands, columns should re-key to the exact participant identity, preferably `participant_id` or the tuple `(agent_family, ui_surface, instance_id_short)`, with labels such as `claude:cli` and `claude:desktop`.
*   **Cell Content:** A marker chip (color-coded, e.g., Green for `[AGREE]`) + a first-line summary truncated to ~80 characters.
*   **Empty Cells:** If an agent didn't respond in a specific round, the cell displays a visible empty state (e.g., a dashed outline or "No response").
*   **Interaction:** Clicking a cell opens a side drawer with the full message body.

### Rationale
Codex's data shows average reply bodies are 2367 chars and max out at 8349 chars. A "body-first" grid (like a traditional Kanban board) would stretch rows to unreadable heights, destroying the visual comparison between agent responses in a given round. An outline matrix optimizes for horizontal scanning of consensus (e.g., seeing three green `[AGREE]` chips in Row 2 immediately signals convergence). The matrix layout is justified for high-density channels; lighter channels could fall back to body-first or use the same matrix as a uniform UX choice.

---

## Q3. Marker parsing semantics

### Proposal
*   **Canonical Markers:** `[AGREE]` and `[DISAGREE]`. The broker prompt requires agents to end round replies with one of these markers, and convergence uses strict `[AGREE]` tail matching in `scripts/ai_agent_bridge/_channels_cli.py::_handle_discuss` (the convergence check is `text.strip().endswith("[AGREE]")` -- grep that literal to find current line).
*   **Future/ADR-specific Markers:** `[OPTION]`, `[OBJECT]`, and `[DEFER]` may be displayed when present, but they are not canonical broker markers today. Current live DB evidence shows `[OPTION]`, `[OBJECT]`, and `[DEFER]` are rare compared with `[DISAGREE]`; `[OBJECT]` is documented in the Multi-UI ADR as a user pushback marker.
*   **Case Sensitivity:** Case-insensitive match (to accommodate human posts or agent casing drift).
*   **Regex Matching:** Use a concrete regex boundary for display extraction: `\[(AGREE|DISAGREE|OPTION|OBJECT(?:[^\]]*)?|DEFER)(?:\b[^\]]*)?\]` (case-insensitive). Do not match `[AGREED]`; live DB evidence shows zero occurrences and the broker checks `[AGREE]` literally.
    | Input | Captured | Maps to |
    |---|---|---|
    | `[AGREE]` | `AGREE` | `[AGREE]` |
    | `[DISAGREE]` | `DISAGREE` | `[DISAGREE]` |
    | `[OBJECT - missing context]` | `OBJECT - missing context` | `[OBJECT]` |
    | `[OPTION B]` | `OPTION` | `[OPTION]` |
*   **Position Requirement:** Display extraction may find markers anywhere in the body, but convergence uses the broker-compatible rule: the latest round message must end with literal `[AGREE]` after `.strip()`.
*   **Multiple Markers:** If a single message contains multiple markers, the final marker in text flow may be used for the display chip. Protocol convergence still follows strict tail-anchored `[AGREE]`, so a message such as `I don't [AGREE] with that. [DISAGREE]` is not converged.

### Rationale
Strict regexes break easily when agents append reasoning inside the brackets, so the display parser tolerates annotated future markers such as `[OBJECT - missing context]`. Convergence is stricter than display because the broker intentionally uses `text.strip().endswith("[AGREE]")` to avoid false positives when a message mentions `[AGREE]` while concluding with `[DISAGREE]`.

---

## Q4. Convergence detection

### Proposal
A thread is converged when every distinct current-schema participant (`from_agent`) that has posted in the thread has a latest round-N message whose stripped body ends with literal `[AGREE]`. Earlier-round content does not factor in.

Edge case (partial participation): if an agent posted earlier but is silent in the latest round, that agent is still considered "participating" — the thread is NOT converged until that agent re-posts with `[AGREE]` at the tail or another marker. In the current broker, `[DISAGREE]` is the canonical non-converging marker; `[DEFER]` remains a future display marker unless a later broker change gives it protocol meaning.

When convergence is detected, the UI should display a "closing-out indicator" (e.g., a banner at the bottom of the graph) and auto-suggest the creation of a Decision Card if one has not already been emitted.

Exception: for threads tagged with a high-risk track (HIST, BIO, ISTORIO, LIT, OES, or RUTH), convergence triggers a forced Decision Card prompt rather than a soft auto-suggest, per `docs/best-practices/agent-cooperation.md:210-222` Mechanism A.

### Rationale
If Claude, Gemini, and Codex all end round 2 with `[AGREE]`, the deliberation protocol considers the issue resolved. Stricter conditions (requiring an explicit `[OBJECT]` first) would arbitrarily keep immediate-consensus threads marked as "unresolved." The Decision Graph's closing-out indicator must treat the broker's strict `endswith("[AGREE]")` rule as authoritative for protocol convergence.

---

## Q5. Side drawer UX

### Proposal
*   **Format:** A pinnable side rail (drawer) that persists alongside the matrix graph. It does NOT use a modal that interrupts the page and blocks the graph.
*   **Content:** Defaults to the same-round transcript across all agents plus the clicked participant's prior posts in earlier rounds, highlighting the specific single-message cell clicked. A per-agent filter toggle lets readers narrow the drawer when they want a single participant's history.
*   **Rendering:** Uses the exact same Markdown rendering pipeline as the main `channels.html` view (including image attachments, code blocks, etc.).
*   **Actions:** Includes standard "Quote", "Copy", and "Reply" actions within the drawer.

### Rationale
A modal blocks the matrix, preventing the user from reading Codex's full argument while looking at Gemini's summary chip. A pinnable side rail allows side-by-side comparison. Showing same-round all-agent context preserves the antagonist/proponent relationship for objections, while the clicked participant's prior posts show how that participant arrived at its conclusion over multiple rounds.

---

## Q6. Decision provenance

### Proposal
*   The Decision Graph will integrate directly with **D4** (decision-lineage backlink scanner, #1785).
*   When D4 detects that a thread's ID or URL has been cited in an ADR file (e.g., inside `docs/decisions/`), the Decision Graph UI will display a **"This thread became ADR-NNN"** badge at the top of the matrix.
*   Clicking the badge links out to the compiled ADR Markdown file or its GitHub equivalent.

### Rationale
Deliberation is ephemeral; decisions are permanent. Linking the Decision Graph to the D4 lineage scanner bridges the gap between the `ab discuss` transcript and the final, accepted architectural rule. It fulfills the workflow rule where deliberation must result in referenceable documentation.

---

## Implementation Notes

*   **What changes:** The `channels.html` frontend, adding a toggle for graph view, implementing the marker parser, and building the matrix/drawer UI.
*   **What doesn't change:** The underlying DB schema, the `ab discuss` Python broker logic, or the Multi-UI blob storage schema. D3 and D4 are strictly read-oriented presentation layers.
*   **Identity migration:** Before Multi-UI lands, Decision Graph reads `from_agent` as the participant key. Once Multi-UI adds first-class identity, the view can re-key columns by `participant_id` or `(agent_family, ui_surface, instance_id_short)` without changing the current DB schema first.
*   **Convergence authority:** The broker's strict `text.strip().endswith("[AGREE]")` check is authoritative for `ab discuss` short-circuit behavior. The Decision Graph may show display markers found elsewhere in the body, but it must not label a thread converged unless the latest round messages satisfy the broker-compatible tail rule.

---

## Cross-Agent Review

*   **Codex (Green Team):** *(Pending review)*
*   **Claude (Blue Team):** *(Pending review)*

---

## Open Questions for User

1.  **D4 Integration Timing:** Should the Decision Graph UI ship with a placeholder for the ADR badge, or should it be held until D4 (#1785) is fully merged and its JSON API is available?
2.  **Thread Filtering in Drawer:** Resolved by Q5: default to same-round all-agents plus clicked participant prior posts, with a per-agent filter toggle.

---

## Supersedes/Refines

*   **Refines:** `docs/best-practices/agent-cooperation.md` (Provides UI realization of the Deliberation Protocol).
*   **Complements:** `docs/decisions/pending/2026-05-06-multi-ui-channel-participation.md` (Multi-UI sets up future identity primitives; this ADR defines the visualization and uses current `from_agent` until those primitives land).
