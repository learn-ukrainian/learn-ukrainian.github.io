# expert-review-seminar-skills.md

**To:** The Curriculum Architecture Team  
**From:** Prof. [Name Redacted], Chair of Ukrainian Studies  
**Date:** February 13, 2026  
**Subject:** Moving from "Textbook" to "Seminar": A Critical Review of the v3.0 Narrative Engine

## Executive Summary

I have reviewed the `full-rebuild-bio`, `full-rebuild-hist`, and `full-rebuild-lit` skill definitions. The current "Tier 3 Rigorous" standard is technically impressive and pedagogically sound for a high-level language course. The focus on *Agency*, *Decolonization*, and *Sensory Detail* places it well ahead of standard language curricula.

However, to make these modules **"the best in the world"**—to truly simulate a university-level seminar—we must move beyond *narrative reconstruction* (telling a better story) to *historiographical conflict* (debating how the story is told).

A seminar is not about "facts"; it is about "arguments". The current skills are excellent at *presenting* a decolonized narrative, but they do not sufficiently *problematize* the sources or the narrative itself.

## Critical Gaps & Recommendations

### 1. The Missing Friction: Historiographical Debate
**Critique:** The current skills focus on "Active Agency" and "Decolonization". This risks replacing one monolithic narrative (Imperial) with another (Patriotic). A true seminar exposes the *messiness* of history.
**Recommendation:**
*   **Add "Turn 1.5: The Conflict Map"**: Before writing content, the model must explicitly identify 2-3 academic debates regarding the subject.
    *   *Example:* Was Khmelnytskyi a state-builder or a pragmatist improviser? (Hrushevsky vs. Yakovleva).
    *   *Action:* In `SKILL.md`, add a mandatory "Conflict Mapping" step in Phase 1 or 2.

### 2. The "Anti-Hagiography" Clause
**Critique:** The "Agency Pass" rule ("Shevchenko created...") is vital but can lead to uncritical worship. Seminar students must encounter *flawed* heroes.
**Recommendation:**
*   **Add an "Anti-Monument Rule"**: Explicitly forbid "Great Man" worship. Require at least one section analyzing a failure, a doubt, or a moral ambiguity of the subject.
    *   *Prompt:* "Analyze the subject not as a marble statue, but as a living, conflicted human being."

### 3. Global Synchronicity (The "Mean Time" Context)
**Critique:** Ukrainian history is often taught in isolation. The best seminars place Ukraine in the world.
**Recommendation:**
*   **Mandate "Synchronous Anchors"**: Every module must link a Ukrainian event/text to a simultaneous global event.
    *   *Example:* While Shevchenko was writing *The Caucasus* (1845), what was happening in the British Empire or the US (Douglass's *Narrative*)?
    *   *Action:* Add a requirement for "1 Global Context Anchor" in the content rules.

### 4. Primary Source Hierarchy
**Critique:** "Harvest primary quotes" is too vague. It allows for "textbook quotes" (secondary sources quoting primary).
**Recommendation:**
*   **Enforce a "Source Hierarchy"**:
    1.  **Archival/Memoir** (Letters, Diaries, Decrees) — Gold Standard.
    2.  **Contemporary Press** (Newspapers of the era).
    3.  **Academic Monograph** (Hrytsak, Plokhy, Grabowicz).
    *   *Action:* Require at least 2 quotes from Category 1 (Diaries/Letters) to capture the "voice" of the era.

### 5. Material Culture (The "Sensory" Expansion)
**Critique:** `full-rebuild-hist` has the excellent "Sensory Historian" persona. This should be universal, especially for BIO and LIT.
**Recommendation:**
*   **Universalize "Sensory Anchors"**: Every biography must mention *material* details: the cost of bread, the texture of paper, the smell of the ink, the specific coffee house. This grounds abstract ideas in physical reality.

## Specific Updates for `SKILL.md`

### Update 1: Refined Personas (Moving beyond "Journalist")
The current personas are functional but generic. Let's make them *academic archetypes*:

**For `full-rebuild-bio`:**
*   **Current:** *Investigative Journalist* / *Humanist Biographer*
*   **Proposed:**
    *   **The Micro-Historian**: Focuses on "small" details (a letter, a receipt) to reveal "big" structures. (Carlo Ginzburg style).
    *   **The Intellectual Historian**: Focuses on the *genealogy of ideas*. Who did the subject read? Who did they argue with?

**For `full-rebuild-lit`:**
*   **Current:** *Stylistic Critic* / *Cultural Analyst*
*   **Proposed:**
    *   **The Close Reader**: Obsessed with syntax, rhythm, and word choice. (New Criticism).
    *   **The Post-Colonial Critic**: Deconstructs imperial power structures within the text. (Said/Grabowicz style).

### Update 2: The "Epistemic Humility" Rule
Add to **Section 2. Core Pedagogical Rules**:
> **Epistemic Humility**: Never present a contested theory as absolute fact. Use markers of academic caution: "За версією Грабовича..." (According to Grabowicz...), "Існує гіпотеза..." (There is a hypothesis...). Acknowledge what we *do not* know.

## Conclusion

Your skills are currently building excellent *encyclopedias*. To build *seminars*, you must inject **conflict, doubt, and global context**.

A student should finish a module not just knowing "Shevchenko was a genius," but understanding *why his genius was contested, how it fit into European Romanticism, and what he paid for his coat.*

**Rating:** 8.5/10 (Excellent Foundation)  
**Potential:** 10/10 (World Class with these changes)
