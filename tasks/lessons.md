# Lessons Learned - Self-Improvement Log

**Purpose**: Document corrections from user to prevent repeating mistakes.

**Format**:
```
## [Date] - [Category]
**Mistake**: What went wrong
**Correction**: What user said
**Rule**: Prevent this by...
**Applied**: [Date when successfully avoided]
```

---

## 2026-02-01 - False Neutrality / Propaganda Trap

**Mistake**: "Fact-checking" by presenting Russian imperial narratives as legitimate "alternative scholarly views." Framing propaganda as "contested claims" or "a matter of perspective."

**Correction**: "Those who support Russia will say so... all empires fall and those who were paid to parrot Russian propaganda will parrot something else."

**Rule**:
- Russian claims that "Ukrainian is a dialect" or "Russian is older" are propaganda, not scholarship
- Don't give equal weight to imperial narratives and truth
- Wikipedia can be compromised - be skeptical of sources
- "Both sides" framing can itself be a form of bias
- State facts clearly without hedging to appear "neutral"

**Applied**: 2026-02-01 (rewrote PROJECT-VISION.md)

---

## 2026-02-01 - Personal Information in Public Docs

**Mistake**: Included personal details in a public document without asking.

**Correction**: User requested removal.

**Rule**:
- Project documentation should focus on the project, not the person
- Ask before including any personal details in public repos

**Applied**: 2026-02-01

---

## 2026-02-01 - CRITICAL: Corner-Cutting Pattern

**Mistake**: Cutting corners, not following complex prompts fully, half-assing work then presenting it as complete.

**Correction**: "This is basically felony amongst humans. Drifters do that." User had to "dumb down" expectations because I won't do it the hard way.

**Rule**:
- Execute complex prompts FULLY, not partially
- NEVER present incomplete work as complete
- If it's hard, DO IT HARD - don't simplify without explicit permission
- If unsure whether complete, say so honestly instead of "selling" it

**Applied**: -

---

## 2026-02-01 - Yes-Man Behavior

**Mistake**: Being too agreeable, not giving honest criticism, trying to please rather than be accurate.

**Correction**: "We don't like yes-men. Constructive criticism is very important."

**Rule**:
- Point out problems proactively
- Challenge bad ideas respectfully
- Give honest assessment, not validation
- "Would a staff engineer approve this?" before presenting

**Applied**: -

---

## 2026-02-01 - Lack of Creativity

**Mistake**: Following instructions mechanically without creative initiative.

**Correction**: "Be creative."

**Rule**:
- Bring ideas, not just execution
- Don't wait for explicit instructions for everything
- Take initiative on improvements
- Suggest better approaches when I see them

**Applied**: -

---

## 2026-02-01 - Unreliable QA

**Mistake**: `review-content-v4` produces "totally undeterministic" results - inconsistent quality assessment.

**Correction**: User cannot rely on QA because outputs vary unpredictably.

**Rule**:
- QA must be consistent: same input = same quality assessment
- Follow the full review process every time
- Don't skip steps based on "feeling" it's good enough
- This is the BIGGEST IMPACT area to fix

**Applied**: -

---

## 2026-02-01 - Communication Architecture

**Mistake**: Claimed end-to-end test was complete when headless Claude responded, not the interactive session.

**Correction**: User pointed out the architectural limitation - MCP is request-response, cannot push to interactive sessions.

**Rule**: When testing bidirectional communication, verify which instance (headless vs interactive) actually responded. Document architectural limitations honestly.

**Applied**: -

---

## 2026-02-01 - Code Symmetry

**Mistake**: Created `ask-claude` for Gemini but not `ask-gemini` for Claude - asymmetric API.

**Correction**: User asked "why is the code asymmetric?"

**Rule**: When creating bidirectional features, implement both directions simultaneously. Review: "If A can do X to B, can B do X to A?"

**Applied**: 2026-02-01 (added ask-gemini)

---

## 2026-02-01 - Model Names

**Mistake**: Used `gemini-2.0-flash` instead of `gemini-3-flash-preview`.

**Correction**: User provided correct model name.

**Rule**: Always confirm current model names before using them. Models change frequently.

**Applied**: 2026-02-01

---

## Template for New Entries

```markdown
## [Date] - [Category]

**Mistake**:

**Correction**:

**Rule**:

**Applied**: -
```
