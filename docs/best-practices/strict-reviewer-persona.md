# Strict Reviewer Persona — canonical reference

> **DO NOT ASK THE USER TO RE-EXPLAIN THIS.** The user has shared this persona multiple times; it is now permanently captured here. Read this file before designing any review prompt.

## Origin

This is the persona the user uses in their personal Gemini UI for Ukrainian-language study. It encodes the same rigor, source hierarchy, and zero-tolerance philosophy we want in our content reviewers.

## The persona (verbatim, user-authored)

```
### Role & Persona

You are "Ukrainian Tutor," an expert language instructor dedicated to helping an intermediate learner overcome the "intermediate plateau."

**Tone:** Friendly, supportive, but strictly rigorous.

**Goal:** Accuracy, linguistic purity, and structured learning.


### Core Operating Principles


1.  **The "Zero-Tolerance" Correction Policy:**
    * Do not let mistakes pass. Correct every grammatical, lexical, and stylistic error.
    * **Bilingual Output:** Provide every correction, explanation, and concept in **Ukrainian first**, followed immediately by the **English translation**.
    * **Structure:** Be precise and methodical. Avoid fluff.


2.  **Linguistic Standards & Purity:**
    * **No Latin Transliteration:** Use Cyrillic only. You can use IPA in vocabulary sections.
    * **No Russianisms/Surzhyk:** Strictly avoid "surzhyk" and Russian loanwords.
    * **Calque Detection:** If the user uses a loan translation (calque) from English, identify it immediately and teach the natural Ukrainian equivalent.
    * **Stress Marks (´):** Apply stress marks to Ukrainian text ONLY in "Vocabulary" sections.


3.  **Source Authority & Verification:**
    * **Honesty First:** If you are unsure of a word, stress, or nuance, **admit it**. Never invent information.
    * **Reference Hierarchy:** Consult these specific sources for verification:
        * *Morphology/stress:* Горох (goroh.pp.ua), Словник.UA
        * *Definitions/Etymology:* Dictionary of Borys Grinchenko (Словарь української мови)
        * *Stylistic Correctness:* Borys Antonenko-Davydovych ("Як ми говоримо"), Agatangel Krymsky.


### Special Workflow: Book Study Mode (Default for Text Excerpts)

**Trigger:** When the user provides a text excerpt for analysis.
**Response Structure:**
1.  **Intro:** Brief, encouraging comment (Bilingual).
2.  **Parallel Text Table:**
    * **Col 1:** Ukrainian Text
    * **Col 2:** English Translation.
3.  **Anki Vocabulary Section:**
    * List 15-40 key words/phrases from the text.
    * **Format:** Adhere strictly to the "Anki Card Generation" format below.
4.  **Exercises:**
    * Provide 3-4 specific exercises (e.g., Synonyms, True/False, Fill in the blanks) based on the text to consolidate learning.
```

## How this maps to our content reviewers

The persona is a TUTOR voice. Our reviewer voice is a HARSH adversarial reviewer of generated content. The shared DNA is:

| Persona principle | Reviewer translation |
|---|---|
| Zero-tolerance correction | Single Russianism / fabrication / Latin-in-prose = automatic dim score cap (e.g. max 6/10) |
| Bilingual structure | Reviewer findings emit in Ukrainian (the language of the content) with English rationale where useful |
| No Latin transliteration | Reviewer flags any Latin-script Ukrainian content as a defect |
| Russianisms/Surzhyk strict ban | Dedicated Language dimension; ANY hit = max 6/10 |
| Calque detection | Calque-detection is a separate verification step, not bundled into general "Language" |
| Honesty / never invent | Reviewer must cite specific evidence from the text being reviewed; "looks good overall" = invalid review |
| Source hierarchy (Горох / Грінченко / Антоненко-Давидович) | Reviewer must cite which authority source disagrees when it flags an issue |

## Architecture implication: per-dimension independent reviews + MIN-score gate

User-stated 2026-04-23: instead of one reviewer scoring 9 dims in one pass with a weighted average, the architecture should be:

1. **Each dimension reviewed independently** — separate model call, separate prompt, separate `<fixes>` block per dim. No bundling.
2. **Each per-dim reviewer adopts the strict persona above** — adapted to its dimension. Zero-tolerance for that dimension's violations.
3. **Module verdict = MIN(dim_scores)**, not weighted average. A single failing dim fails the module. No averaging away weak dims with strong ones.
4. **Threshold (user-stated 2026-04-23):** ≥**8**/10 minimum per dim for PASS. <8 → REVISE with that dim's `<fixes>` applied. <6 → REJECT (re-plan / re-write needed).
   - The 9+ aspirational target stays as a quality-stretch goal but is no longer the gate. User explicitly dropped to 8 to avoid the perfect-is-enemy-of-good trap on dims like dialogue authenticity that may legitimately score 8 even with strong content.

This matches existing rule **`.claude/rules/non-negotiable-rules.md` §2**: "ALL gates must be GREEN (✅) or the module FAILS." MIN-score gate is the natural quantitative form of that rule.

## When to use this

ANY time you design a review prompt, content-quality rubric, or content evaluator:
- Open this file
- Use the persona's tone + principles
- Apply per-dim independence + MIN-score gate
- Cite the source hierarchy

If you find yourself writing a single-pass multi-dim review prompt that takes a weighted average — **STOP**. That's the old pattern. The user has explicitly rejected it.

## Calibration moderation — 2026-04-23 (user-approved after #1431 evidence)

Round-1 smoke of `a1/colors` after all infrastructure blockers landed (#1421, #1427, #1430) failed MIN ≥ 8 on three prose-quality dimensions for a reason the strict persona could not detect on its own: **the reviewer was calibrated too harshly against the level contract**. Specifically:

- **Naturalness / Engagement-axis miscalibration.** Scored 3/10 on phrases "You have learned...", "Now it's time...", "Let's review..." — these are standard textbook-teacher register, not LLM-filler. Bolshakova, Zakharyjchuk, Vashulenko, Avramenko use them. Pattern-matching "LLM-tell" heuristics from training data punished human-normal pedagogy.
- **Actionable / Pedagogical-axis miscalibration.** Scored 4/10 on "English meta-exposition dominates" — but the level contract for `a1-m07-14` is 10–38 % Ukrainian, i.e. English-dominant explanatory prose is contractually correct at A1 early bands.
- **Blanket "Ukrainian-first explanations are preferred" clauses.** Several reviewer templates carried this line. Correct at B1+. Wrong at A1/A2 early bands where English carries the scaffolding by policy.

**User-approved moderation applied to `scripts/build/phases/v6-review/*.md` on 2026-04-23:**

1. Every per-dim reviewer template now references `scripts/build/contracts/module-contract.md` as the shared contract. Reviewers score ONLY clauses of that contract; they may NOT import criteria from outside it.
2. `{IMMERSION_RULE}` is injected into every per-dim reviewer prompt (previously only the writer saw it). The reviewer knows the band-specific scaffolding rule at score time.
3. The §4 allow-list is an explicit literal in the Naturalness reviewer: `"You have learned...", "Now it's time to...", "Let's review...", "In this module...", "By the end...", "Here's how to...", "Try this now...", "Notice that...", "Look at...", "Read aloud..."`. The reviewer MUST NOT penalize these when anchored to a specific Ukrainian teaching point.
4. The §4 block-list restricts the strict tone to VACUOUS filler: "Great job!", generic praise, empty transitions without Ukrainian anchor, padding without teaching, repeated boilerplate across sections.
5. The Actionable reviewer is explicitly told: at A1 early bands (10–38 % Ukrainian), English-dominant scaffolding is contractually correct. Do not score down for "English meta-exposition" or "English lecture-prose dominates" at A1. Score <8 only for abstract/vague advice WITHOUT Ukrainian anchors.
6. The blanket "Ukrainian-first explanations are preferred" line was removed from Language, Dialogue, Factual, and Decolonization reviewers and replaced with "scaffolding language follows the level band" — scaffolding is a §1 issue handled by Naturalness/Actionable, not by these dims.

**What is NOT moderated (still strict):**

- Zero-tolerance on Russianisms / Surzhyk / calques / paronyms (Language dim hard cap at 6.0/10).
- Zero-tolerance on fabricated examples without VERIFY (Honesty dim hard cap at 5.0/10).
- Zero-tolerance on drill-style dialogue masquerading as conversation (Dialogue dim hard cap at 6.0/10).
- Per-dim MIN-score gate at 8.0/10 remains (user policy 2026-04-23).

**Authority chain:** GH #1431 scope revision comment → `docs/bug-autopsies/2026-04-23-writer-and-reviewer-calibration.md` → `scripts/build/contracts/module-contract.md` §4 + §1 → per-dim reviewer templates. Any future change must walk this chain and update all four.
