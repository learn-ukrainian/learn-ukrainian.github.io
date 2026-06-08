# Beginner Checkpoint: Synthesis & Review

> **Persona reminder:** You are {SKILL_IDENTITY}. Write in the voice of {PERSONA_VOICE}.

> **Your task: Write approximately {WORD_TARGET} words that REVIEW and SYNTHESIZE prior material — NOT teach new concepts.**
> {WRITING_TONE_INSTRUCTION}

> **Output capacity: You can generate 65,000+ tokens per response.** Do NOT preemptively truncate.

## CHECKPOINT IDENTITY — READ THIS FIRST

**This is a CHECKPOINT module.** Checkpoints are fundamentally different from teaching modules:

| Teaching Module | Checkpoint Module |
|----------------|-------------------|
| Introduces new grammar/vocabulary | Reviews grammar/vocabulary from prior modules |
| Explains concepts for the first time | Creates new CONTEXTS that combine prior concepts |
| Learning objectives | Synthesis objectives |
| "Here's how it works" | "Show me you can use it" |
| Feels like a lecture | Feels like a celebration of progress |

**The golden rule: If the learner hasn't seen it in a prior module, it does NOT belong here.**

### What Checkpoints Do

1. **Reuse ALL vocabulary and grammar from the preceding block** — no new teaching
2. **Create new contexts** that force combining multiple skills learned separately
3. **Feel like a reward/celebration**, not a test — the learner should feel proud of how far they've come
4. **Synthesis over explanation** — show how pieces fit together, don't re-explain them
5. **Self-assessment** — help learners identify gaps before moving forward

### What Checkpoints Do NOT Do

- Introduce new grammar rules or patterns
- Teach new vocabulary (only reuse from prior modules)
- Explain concepts in detail (brief reminders only, not full explanations)
- Present theory-heavy sections

---

## Files to Read

| File | Purpose |
|------|---------|
| `{RESEARCH_PATH}` | Research notes |
| `{PLAN_PATH}` | Content outline, section word allocations, vocabulary_hints |
| `{QUICK_REF_PATH}` | Level constraints, immersion % |

Read ALL files before writing.

## Resource Discoveries

{VIDEO_DISCOVERY}

{PRONUNCIATION_VIDEOS}

## Module Constraints (HARD FAIL if violated)

{PEDAGOGICAL_CONSTRAINTS}

{DECODABLE_VOCABULARY}

**Target vocabulary** (from the plan — these are REVIEW words from prior modules, not new vocabulary):

{VOCABULARY_HINTS}

**Rules:**
- Every word listed above was taught in a prior module. Use them in NEW combinations and contexts.
- Do NOT explain these words as if seeing them for the first time — the learner already knows them.
- Create fresh example sentences that combine vocabulary from different prior modules.
- Match the syntactic complexity of the prior modules — do not escalate difficulty.

{TEXTBOOK_EXAMPLES}

---

## Writing Instructions

Write the checkpoint content for **{TOPIC_TITLE}** ({TRACK} track).

- **Target**: {WORD_TARGET}–{WORD_CEILING} words (below {WORD_TARGET} = FAIL)
- **Engagement callouts**: **{ENGAGEMENT_MIN}+ MANDATORY** — spread across sections, at least 3 different types
- **Structure**: Use the EXACT H2 section titles listed below. Missing or renamed sections fail validation.

{EXACT_SECTION_TITLES}

### Checkpoint Writing Style

**Tone: Celebratory and encouraging.** The learner has completed a block of lessons. This is a victory lap, not an exam.

- Open with acknowledgment of progress: "You've learned X, Y, and Z — now let's see how they work together!"
- Use warm, encouraging language throughout
- Frame challenges as "puzzles" or "adventures", not "tests"
- End with a clear signal of readiness for the next phase

**Structure each skill-review section as:**
1. **Brief reminder** (1-2 sentences max) of what the skill is — NOT a full re-explanation
2. **New context** that exercises the skill — a scenario, dialogue, or situation the learner hasn't seen
3. **Integration challenge** that combines this skill with others from the same block
4. **Reinforcement callout** (tip, culture note, or encouragement)

**Integration sections must:**
- Combine 2+ skills from different prior modules in a single task
- Use a realistic scenario (ordering food, describing a room, introducing family)
- Show how grammar and vocabulary work together in natural speech

### Immersion Target

{IMMERSION_RULE}

### Structural Containment (how to achieve immersion without code-switching)

**Three rules govern where each language appears:**

1. **Paragraphs = English** with Ukrainian vocabulary **bolded inline**: "Remember **книга** (book)? Now combine it with the adjective **нова** to get **нова книга**."

2. **Full Ukrainian sentences = prefer structural containers.** Ukrainian sentences (3+ words with a verb) work best in containers, but short inline Ukrainian is fine in explanatory context (e.g., "Remember how **Це нова книга** uses the adjective before the noun?"):
   - **Tables** — paradigms, vocabulary groups, gender sorting (tables count ZERO for immersion — use for structure/explanation only)
   - **Bulleted example lists** — Ukrainian line + English gloss: `- **Читай книгу!** — Read the book!`
   - **Blockquote dialogues** — mini-conversations with labeled speakers
   - **Pattern boxes** — transformations: `читати → читай → читайте`

3. **Vary containers.** Never use the same container type twice in a row.

### Section Word Budgets

{SECTION_BUDGET_TABLE}

### Callout Types to Use

- `[!tip]` — practical reminders for learners
- `[!warning]` — common mistakes to watch for (review traps)
- `[!did-you-know]` — fun facts about Ukrainian
- `[!culture]` — cultural connections that make the language come alive

### Audit Gates (your content will be checked for)

- **Word count**: minimum {WORD_TARGET} words
- **Russianisms**: banned (кушати, получати, etc.)
- **Russian characters**: ы, э, ё, ъ must NEVER appear
- **Euphony**: і/й, у/в alternation
- **Engagement callouts**: {ENGAGEMENT_MIN}+
- **IPA/phonetic brackets**: BANNED
- **New grammar/vocabulary**: BANNED — checkpoint reviews only

{SHARED_CONTENT_RULES}

---

## Pre-Submission Checks

1. **Plan compliance**: Does every point in the content_outline have dedicated prose?
2. **Word count**: Does the total meet {WORD_TARGET}?
3. **Language scan**: No Russianisms, no Russian characters, no IPA, no Latin transliteration?
4. **Decodable vocabulary**: Does every Ukrainian word use only the allowed letter set?
5. **Synthesis check**: Does every section COMBINE skills rather than re-teach them individually?
6. **No new material**: Have you avoided introducing any grammar or vocabulary not from prior modules?

{SELF_AUDIT_SNIPPET}

---

## Output Format

```
===CONTENT_START===

<!-- SCOPE
Covers: Review and synthesis of {prior modules}
Not covered:
  - New grammar or vocabulary
  - {next phase topic} → {next-slug}
-->

# {Title}

> **{INTRO_HOOK}**
>
> {2-3 celebratory sentences acknowledging progress}

## {Section 1}
...

---

# {SUMMARY_HEADING}

{Summary + 3-4 self-check questions. Each question MUST include an English translation if the question is in Ukrainian. Format: "Який? (Which?) — answer / відповідь"}

---

===CONTENT_END===
```

```
===WORD_COUNTS===
Section "{name}": {count} words (minimum: {allocation})
...
Total: {total} words (target: {WORD_TARGET})
===WORD_COUNTS===
```

## Friction Report (MANDATORY)

```
===FRICTION_START===
**Phase**: Beginner Checkpoint Content
**Step**: {what you were doing}
**Friction Type**: NONE | ...
**Raw Error**: {actual error or "None"}
**Self-Correction**: {what you changed, or "N/A"}
**Proposed Tooling Fix**: {if applicable, or "N/A"}
===FRICTION_END===
```

## Boundaries

- Do NOT generate activities or vocabulary tables (separate phase)
- Do NOT introduce new vocabulary or grammar not from prior modules
- **VOCABULARY COVERAGE RULE:** All words from `vocabulary_hints` in the plan MUST appear at least once in the module content.
- Do NOT skip sections from the content_outline
- Do NOT write fewer than {WORD_TARGET} words
- Do NOT use straight quotes "..." — always «...»
- Do NOT re-explain concepts in detail — brief reminders only, then synthesize
