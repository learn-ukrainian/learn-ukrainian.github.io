# Narrative Engine v2.2: The "Zero to Scholar" Assembly Line

**Status:** Active Development
**Goal:** Transform the project from "Manual Editing" to an "Autonomous High-Quality Content Factory."
**Core Philosophy:** "Armor + Soul." Strict technical boundaries combined with deep, persona-driven storytelling.

## 1. The Core Architecture (v2.2)

The system relies on a 7-turn atomic workflow that eliminates "Accountant Mode" friction.

| Turn | Name | Function | Tooling |
| :--- | :--- | :--- | :--- |
| **1** | **Research** | "Fueling the Engine." Finds verified facts/myths. | **Persona Mandate:** "Find me 3 myths." |
| **2** | **Meta Architect** | Sets the structural frame. | **Flexible Targets:** "Approximate word counts." |
| **3** | **Narrative Hydration** | **The Creative Act.** | **Dual-Persona:** Track Voice + Situational Role. |
| **3.1** | **Linguistic Polish** | **Quality Gate.** | Fixes gender/case/roboticism before synthesis. |
| **3.5** | **Meta-Sync** | **Friction Remover.** | `sync_meta_outline.py` aligns metadata with reality. |
| **4** | **YAML Synthesis** | **Contextual Drill.** | Activities derived *strictly* from the Turn 3 story. |
| **5** | **Deep Review** | **The Gatekeeper.** | 14-dimension scoring (Naturalness, Richness, Agency). |

## 2. The "Legacy Upgrade" Strategy (Migration)

We are moving from "Patching" to "Rebuilding."

### Step 1: Safe Archival
Before touching any track, we run:
```bash
python scripts/archive_track.py {track}
```
*Moves current content to `_archive/{track}/{date}/`.*

### Step 2: The "Grand Casting"
We ensure every module has a deterministic soul:
```bash
python scripts/suggest_personas.py {track}
```
*Assigns specific roles (e.g., "Military Chronicler") to plan YAMLs.*

### Step 3: The Assembly Line
The `agent_watcher.py` triggers the Narrative Engine. 
*   **Target:** 1.5x Overshoot (e.g., 6000 words for History).
*   **Mandate:** "Ignore existing content. Build fresh."

### Step 5: The "Stateless Reviewer" (Isolation)
To prevent "Self-Review Gaming," the final Quality Gate (Turn 5) must be performed by a **fresh agent session**.
- **Rule:** The Reviewer starts with a clean context.
- **Persona:** Hostile Auditor / Senior Philologist.
- **Mandate:** Identify at least 3 real issues. Hard-cap scores if word targets are missed.
- **Validation:** Auditor script verifies citations in the review against the actual .md file.

## 3. Technical Requirements (Issue #558)

To support this, the Infrastructure Team (Claude) must implement:

1.  **Event-Driven Watcher:** `agent_watcher.py` must detect "Turn Completion" events, not just messages.
2.  **Model Enforcement:** `scripts/config.py` must force `gemini-3-pro-preview` for Seminar tracks.
3.  **Comparison Logic:** A script to parse old vs. new review scores.

## 4. Success Metrics

- **Zero "Exit 1" Crashes** (Solved by Atomic Turns).
- **Zero "Section Length Mismatch"** (Solved by Sync Script).
- **10/10 Naturalness** (Solved by Persona + Polish).
- **95%+ Richness** (Solved by 1.5x Overshoot).
