# DECISION REQUIRED - Decision Graph View Paradigm and Layout

**Status:** PROPOSED (awaiting user signoff to ACCEPTED)
**Date:** 2026-05-09
**Authors:** Gemini (drafting), Codex (data collection), Claude (orchestration context)
**Supersedes:** None
**Blocks/Blocked-by:** Blocks Decision Graph UI implementation; independent of Multi-UI ADR (ADR-008). Integrates with D4 decision-lineage backlink scanner (#1785).

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

A standard 3-column body-first grid would be completely unreadable with this volume of text. This justifies an outline-first matrix layout.

This document formalizes the UX and architectural semantics for the Decision Graph view. It is a separate ADR from the pending Multi-UI channel participation ADR because it changes primary IA and marker semantics (meeting the threshold rule for a distinct ADR).

---

## Decision

The Decision Graph view will be implemented under the following paradigm:

*   **Toggle-not-inversion:** Chat remains the primary view. The Decision Graph is a toggleable view that auto-engages under specific conditions.
*   **Outline-first matrix layout:** The graph uses a dense matrix representation (rounds as rows, agent families as columns) displaying only markers and brief summaries to accommodate our large average message sizes.
*   **Side drawer UX:** Reading full message bodies relies on a pinnable side drawer to avoid disrupting the matrix context.
*   **Explicit marker semantics:** Deliberation state is strictly derived from standard `[AGREE]`, `[OPTION]`, `[OBJECT]`, and `[DEFER]` markers.

---

## Q1. When does Decision Graph view auto-engage?

### Proposal
The Decision Graph view should auto-engage (switch automatically from the chat view) when a thread meets **both** of the following conditions:
1.  **Participant-count threshold:** The thread contains messages from **≥2 distinct `agent_family` participants** (e.g., `claude` and `codex`).
2.  **Marker-density threshold:** The thread contains **≥2 messages** carrying formal deliberation markers (`[AGREE]`, `[OPTION]`, `[OBJECT]`, `[DEFER]`).

The manual toggle to switch between Chat and Decision Graph views is **always available** on every thread, regardless of whether the auto-engage criteria are met.

### Rationale
Our channel statistics show that marker threads only dominate the `architecture` channel (82%), while `reviews` (23%) and `pipeline` (18%) are predominantly standard chat or single-shot interactions. Auto-engaging requires sufficient signal (multiple agents + multiple markers) to ensure the graph view is only presented when actual deliberation is taking place. Relying on a manual toggle for edge cases provides an escape hatch without enforcing the wrong default paradigm on 80% of threads.

---

## Q2. Layout

### Proposal
The Decision Graph will use an **outline-first matrix layout**:
*   **Rows:** Rounds (1..N).
*   **Columns:** `agent_family` (e.g., `claude`, `gemini`, `codex`, plus a `human` column for posts where `from_agent='human'`).
*   **Cell Content:** A marker chip (color-coded, e.g., Green for `[AGREE]`) + a first-line summary truncated to ~80 characters.
*   **Empty Cells:** If an agent didn't respond in a specific round, the cell displays a visible empty state (e.g., a dashed outline or "No response").
*   **Interaction:** Clicking a cell opens a side drawer with the full message body.

### Rationale
Codex's data shows average reply bodies are 2367 chars and max out at 8349 chars. A "body-first" grid (like a traditional Kanban board) would stretch rows to unreadable heights, destroying the visual comparison between agent responses in a given round. An outline matrix optimizes for horizontal scanning of consensus (e.g., seeing three green `[AGREE]` chips in Row 2 immediately signals convergence).

---

## Q3. Marker parsing semantics

### Proposal
*   **Target Markers:** `[AGREE]`, `[OPTION]`, `[OBJECT]`, `[DEFER]`.
*   **Case Sensitivity:** Case-insensitive match (to accommodate human posts or agent casing drift).
*   **Fuzzy Matching:** Match exact bases and safe adjacent variants using a regex boundary (e.g., matching `[AGREED]` or `[OBJECT - missing context]`).
*   **Position Requirement:** Anywhere in the body. While agents typically place markers at the end, human participants or modified prompts might place them at the top.
*   **Multiple Markers:** If a single message contains multiple markers (e.g., `[OPTION] ... [DEFER]`), **last-wins** logic is applied. The final marker in the text flow is considered the agent's concluding stance for that round.

### Rationale
Strict regexes break easily when agents append reasoning inside the brackets. Case-insensitivity and "anywhere in body" rules ensure human participants don't have to fight a rigid parser. "Last-wins" matches standard LLM reasoning behavior, where the model deliberates and concludes at the end of its generation.

---

## Q4. Convergence detection

### Proposal
A thread is considered "decided" (converged) when:
*   All distinct participating `agent_family` instances in the thread have emitted an `[AGREE]` marker in the **latest round**.
*   **Looser historical condition:** At least one round must have had an `[OPTION]` or `[OBJECT]` marker, OR it can be an immediate 1-round agreement. We define convergence strictly by the state of the *terminal* round.

When convergence is detected, the UI should display a "closing-out indicator" (e.g., a banner at the bottom of the graph) and auto-suggest the creation of a Decision Card if one has not already been emitted.

### Rationale
If Claude, Gemini, and Codex all end round 2 with `[AGREE]`, the deliberation protocol considers the issue resolved. Stricter conditions (requiring an explicit `[OBJECT]` first) would arbitrarily keep immediate-consensus threads marked as "unresolved."

---

## Q5. Side drawer UX

### Proposal
*   **Format:** A pinnable side rail (drawer) that persists alongside the matrix graph. It does NOT use a modal that interrupts the page and blocks the graph.
*   **Content:** Displays the full-thread transcript filtered to that specific `agent_family` up to that round, highlighting the specific single-message cell clicked.
*   **Rendering:** Uses the exact same Markdown rendering pipeline as the main `channels.html` view (including image attachments, code blocks, etc.).
*   **Actions:** Includes standard "Quote", "Copy", and "Reply" actions within the drawer.

### Rationale
A modal blocks the matrix, preventing the user from reading Codex's full argument while looking at Gemini's summary chip. A pinnable side rail allows side-by-side comparison. Showing the filtered thread context for that agent helps the user understand how that specific agent arrived at its conclusion over multiple rounds.

---

## Q6. Decision provenance

### Proposal
*   The Decision Graph will integrate directly with **D4** (decision-lineage backlink scanner, Epic #1785).
*   When D4 detects that a thread's ID or URL has been cited in an ADR file (e.g., inside `docs/decisions/`), the Decision Graph UI will display a **"This thread became ADR-NNN"** badge at the top of the matrix.
*   Clicking the badge links out to the compiled ADR Markdown file or its GitHub equivalent.

### Rationale
Deliberation is ephemeral; decisions are permanent. Linking the Decision Graph to the D4 lineage scanner bridges the gap between the `ab discuss` transcript and the final, accepted architectural rule. It fulfills the workflow rule where deliberation must result in referenceable documentation.

---

## Implementation Notes

*   **What changes:** The `channels.html` frontend, adding a toggle for graph view, implementing the marker parser, and building the matrix/drawer UI.
*   **What doesn't change:** The underlying DB schema, the `ab discuss` Python broker logic, or the Multi-UI blob storage schema. D3 and D4 are strictly read-oriented presentation layers.

---

## Cross-Agent Review

*   **Codex (Green Team):** *(Pending review)*
*   **Claude (Blue Team):** *(Pending review)*

---

## Open Questions for User

1.  **D4 Integration Timing:** Should the Decision Graph UI ship with a placeholder for the ADR badge, or should it be held until D4 (#1785) is fully merged and its JSON API is available?
2.  **Thread Filtering in Drawer:** Should the side drawer default to showing *only* the clicked message, or the clicked message *plus* its parent thread context?

---

## Supersedes/Refines

*   **Refines:** `docs/best-practices/agent-cooperation.md` (Provides UI realization of the Deliberation Protocol).
*   **Complements:** `docs/decisions/pending/2026-05-06-multi-ui-channel-participation.md` (Multi-UI sets up the identity primitives; this ADR defines the visualization).
