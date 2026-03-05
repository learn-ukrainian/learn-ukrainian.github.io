# C1 Plan Review Summary

**Track:** C1 | **Plans Reviewed:** 106 | **Date:** 2026-03-05
**Reference:** Issue #729

## Verdict Summary

| Category | Count | % |
|----------|-------|---|
| PASS (no issues) | 3 | 2.8% |
| NEEDS FIXES | 103 | 97.2% |
| FAIL (CRITICAL) | 18 | 17.0% |

Only 3 plans have zero issues detected: none — all 106 plans are missing the `register` field. The 3 plans with the fewest issues (fonetychni-stylistychni-zasoby, frazeolohichni-stylistychni-zasoby, leksykolohiia-c1) are missing only `register`.

---

## Rule Compliance

### word_target: ALL PASS
All 106 plans have `word_target: 4000`, matching config.py for C1.

### Section budgets: ALL PASS
All plans have section word sums within +/-10% of the 4000 target.

### version: ALL PASS
All versions are strings (e.g., `'2.0'` or `'1.0'`).

### slug / filename match: ALL PASS
All plan slugs match their filenames.

### Sequence continuity: PASS
Sequences 1-106 with no gaps or duplicates.

---

## CRITICAL Issues (must fix before build)

### C1. Missing `register` field (103/106 plans)

**Every plan except** `asyndetic-semantics`, `high-formal-register`, and `persuasive-speech` is missing the `register` field. This is a required field per the plan review spec. The 3 plans that have it use values like `літературний` or `офіційно-діловий`.

**Fix:** Add `register:` to all plans. Suggested values:
- Grammar/linguistics modules (seq 1-47): `літературний` or `науковий`
- Stylistics modules (seq 48-62): varies by module (`розмовний`, `літературний`, etc.)
- Folk culture modules (seq 68-90): `літературний`
- Fine arts modules (seq 91-106): `літературний`

### C2. Garbled character in b2-review-bridge (seq 1)

Line 36 contains a CJK character instead of Ukrainian text:
```
Пасивні дієприкметники з суфіксами -ний/-抄 та їх функціонування
```
Should be: `-ний/-тий`

### C3. Template/placeholder objectives (17 plans)

Plans in the "v2.0 early academic" batch (seq 1-20 roughly) have machine-generated placeholder objectives that are not testable:

```yaml
# WRONG - meaningless template output
objectives:
- Identify and correctly use маркери академічного стилю
- Form and apply що таке академічний стиль?
- Distinguish between практика трансформації
```

**Affected plans:** abstract-writing, academic-style-markers, advanced-punctuation, b2-review-bridge, citation-reference, counterarguments, dialects-of-ukrainian, essay-structure, hedging-modality, irregular-verbs-complete, literature-review, logical-connectors, oral-presentations, research-article, summary-paraphrase, surzhyk, thesis-development

**Fix:** Replace with specific, testable learning outcomes. Example for academic-style-markers:
```yaml
objectives:
- Transform colloquial text into academic register using impersonal constructions
- Apply nominalization to condense verbal phrases into noun-based academic expressions
- Use hedging devices to modulate certainty in academic conclusions
```

---

## HIGH Issues (should fix before build)

### H1. Non-testable objectives using "understand" (45 plans)

45 plans contain objectives with "understand" or "learn about" — neither is testable per CEFR guidelines. Objectives must describe observable behavior.

**Pattern A — "Understand and apply {title}"** (seq 3-39, the v2.0 professional/domain batch):
research-verbs, analysis-vocabulary, business-etiquette, case-studies, cv-resume-writing, diaspora-ukrainian, digital-communication, essay-writing-practice, global-context, job-interview, media-landscape, political-system, practice-ii-article-critique, professional-scenarios, review, speaking-practice

**Pattern B — "Learner understands..."** (seq 63-106, the cultural/fine-arts batch):
balet-i-tanets, halychyna, hopak-i-kozachok, istoriia-ukrainskoi-literatury, khrestyny-ta-vesillia, klasychna-muzyka-1/2/3, kolyskovi-ta-dumy, kozatski-lehendy, narodna-medytsyna, narodna-mifolohiia, obrazotvorche-mystetstvo-1/2, podillia-ta-volyn, pomynalni-obriady, pysanky, ritual-songs, suchasna-muzyka, teatralne-mystetstvo-1/2, ukrainska-arkhitektura, ukrainske-kino, vesna-ta-lito, vokalne-mystetstvo, vyshyvanka, zymovi-obriady

Also: euphemism-taboo, slang-youth

**Fix:** Replace "understand" with action verbs: "describe", "analyze", "compare", "classify", "produce", "evaluate".

### H2. Missing `activity_hints` (53 plans)

53 plans have no `activity_hints` field. These are concentrated in:
- v1.0 plans (6 plans: checkpoint-c1-5, intimate-register, kobzari-bandura, review-c1-5, ritual-songs, slang-youth)
- v2.0 cultural/fine-arts batch (seq 63-106): analiz-poezii, balet-i-tanets, halychyna, honcharstvo-ta-rizbyarstvo, hopak-i-kozachok, hyperbole-litotes, irony-sarcasm, istoriia-ukrainskoi-literatury, kazky-ta-prytchi, khrestyny-ta-vesillia, klasychna-muzyka-1/2/3, kolyskovi-ta-dumy, kozatski-lehendy, literaturoznavcha-terminolohiia, metaphor-simile, narodna-medytsyna, narodna-mifolohiia, obrazotvorche-mystetstvo-1/2, operne-mystetstvo, podillia-ta-volyn, politeness-strategies, pomynalni-obriady, praktyka-1-narodna-kultura, praktyka-2-vysoke-mystetstvo, pysanky, rehionalni-tantsi, rhetorical-questions, suchasna-muzyka, teatralne-mystetstvo-1/2, traditional-clothing, ukrainian-avant-garde, ukrainian-cuisine-traditions, ukrainian-house, ukrainska-arkhitektura, ukrainske-kino, vesna-ta-lito, vokalne-mystetstvo, vyshyvanka, zymovi-obriady
- Some checkpoint/review plans: c1-1-checkpoint, checkpoint-c1-5, checkpoint-folk-culture, degrees-of-certainty, euphemism-taboo, review-c1-5

### H3. Missing `grammar` field (41 plans)

41 plans lack the `grammar` field (or it is null). Same distribution as H2 — concentrated in the v2.0 early academic batch and v1.0 plans.

### H4. Missing `pedagogy` field (39 plans)

39 plans lack `pedagogy`. These are exclusively from the v2.0 "early academic" and "professional" batches (seq 1-39).

### H5. Missing `subtitle` field (35 plans)

35 plans lack `subtitle`. These are from the v2.0 "early academic" and "professional" batches (seq 1-39).

### H6. Vocabulary ghost words (3 items across 2 plans)

| Plan | Word | VESUM Status | Notes |
|------|------|-------------|-------|
| kobzari-bandura | братищик | NOT FOUND | Consider: братчик |
| kobzari-bandura | лебійська (мова) | NOT FOUND | Historical term, may be acceptable as cultural vocabulary |
| surzhyk | код-свічинг | NOT FOUND | English loanword; consider: перемикання кодів |
| academic-style-markers | хеджінг | NOT FOUND | English loanword; consider including Ukrainian equivalent пом'якшення |
| slang-youth | душнити | NOT FOUND | Active slang, may not yet be in VESUM |

Note: `лебійська`, `хеджінг`, and `душнити` are real-use words that may simply not be in VESUM yet. `братищик` is the most likely genuine error — the historical term may be `братчик`.

---

## MEDIUM Issues (fix if possible)

### M1. Six v1.0 plans need upgrade to v2.0

These plans are at version 1.0 and lack several fields that v2.0 plans have:
- **checkpoint-c1-5** (seq 67): missing activity_hints, grammar, register
- **intimate-register** (seq 60): missing pedagogy, activity_hints, grammar, register
- **kobzari-bandura** (seq 68): missing pedagogy, activity_hints, grammar, register
- **review-c1-5** (seq 66): missing activity_hints, grammar, register
- **ritual-songs** (seq 69): missing pedagogy, activity_hints, grammar, register
- **slang-youth** (seq 61): missing pedagogy, activity_hints, grammar, register

### M2. Redundant `vocabulary:` block in v1.0 plans

Plans kobzari-bandura, intimate-register, and slang-youth have an empty `vocabulary:` block alongside `vocabulary_hints:`:
```yaml
vocabulary:
  required: '[]'
  recommended: '[]'
  forbidden: '[]'
```
This is dead weight and may confuse the build pipeline.

### M3. `c1-final-checkpoint` has `focus: cultural` — should be `focus: checkpoint`

The final checkpoint (seq 106) is categorized as `cultural` instead of `checkpoint`.

---

## LOW Issues (informational)

### L1. Inconsistent `focus` taxonomy

The `focus` field uses an inconsistent vocabulary across plans:
- grammar (24), style (15), fine-arts (14), cultural (6), culture (5), vocabulary (5), history (5), communication (4), practice (4), checkpoint (3), domain (2), linguistics (1), literature (1), analysis (1), review (1)

Some overlap is clear: `cultural` vs `culture`, `fine-arts` vs `cultural`. This should be standardized.

### L2. Inconsistent `pedagogy` values

Where present, pedagogy uses: PPP, CBI, TTT, Immersion, Academic, Assessment, Review, Literary Analysis, Sociolinguistics, "Immersion & Analysis". Should be standardized to a fixed set.

---

## State Standard Alignment

### Grammar scope: PASS

The C1 plans collectively cover the State Standard 2024 C1 requirements:
- Morphology mastery (noun, adjective, numeral, pronoun declension) -- covered in morfolohichna-norma-c1
- All case usage at mastery level -- covered across multiple modules
- Verb forms (indicative, imperative, conditional) -- covered in irregular-verbs-complete, b2-review-bridge
- Word formation -- covered in leksykolohiia-c1, morfolohichni-stylistychni-zasoby
- Complex sentences (conjunctive, asyndetic) -- covered in skladnosuriadne-rechennia through checkpoint-complex-sentences
- Stylistics (5 styles, phonetic/lexical/syntactic devices) -- covered extensively in seq 48-56
- Rhetoric -- covered in rhetorical-questions, persuasive-speech

### Thematic catalogue: PASS

C1 themes from State Standard are covered:
- Суспільні відносини, внутрішня/зовнішня політика -- political-system, global-context
- Культурне дозвілля -- extensive folk culture and fine arts modules
- Наука і техніка -- academic writing modules
- Медіа -- media-landscape, digital-communication
- Традиції -- folk culture block (seq 68-90)
- Освіта -- academic writing block (seq 1-20)
- Робота -- professional communication block (seq 21-39)

---

## Grammar Verification (Textbook RAG)

### Compound sentences (skladnosuriadne-rechennia)
Verified against Grade 9 textbooks (Voron 2017, Avramenko 2017). The plan correctly categorizes conjunctions into єднальні, протиставні, розділові groups. Punctuation rules (comma before conjunction, exceptions for shared members) align with textbook content.

### Stylistic devices (metaphor-simile)
Verified against Grade 5 (Avramenko 2022), Grade 7 (Avramenko 2024), Grade 8 (Avramenko 2025). Definitions of метафора, порівняння, персоніфікація, епітет, гіпербола match textbook sources.

---

## Issue Pattern Summary

| Pattern | Severity | Count | Root Cause |
|---------|----------|-------|------------|
| Missing `register` | CRITICAL | 103 | Field not in plan generation template |
| Template objectives | CRITICAL | 17 | LLM-generated placeholder text not replaced |
| Non-testable objectives | HIGH | 45 | "Understand" used instead of action verbs |
| Missing `activity_hints` | HIGH | 53 | Cultural/fine-arts batch generated without this field |
| Missing `grammar` | HIGH | 41 | Same batch issue |
| Missing `pedagogy` | HIGH | 39 | Early academic batch generated without this field |
| Missing `subtitle` | HIGH | 35 | Early academic batch generated without this field |
| Garbled character | CRITICAL | 1 | Encoding error in b2-review-bridge |
| Ghost vocabulary | HIGH | 3-5 | Unverified words in vocabulary_hints |
| v1.0 plans | MEDIUM | 6 | Older generation, need field parity with v2.0 |

---

## Suggested Template Fixes

### 1. Add `register` to plan generation template
```yaml
# Add to all C1 plans:
register: літературний  # default; override for specific modules
```

### 2. Fix objectives template
Replace the 3-objective pattern:
```yaml
# OLD (template garbage):
objectives:
- Identify and correctly use {title}
- Form and apply {section_name}
- Distinguish between {practice_section}

# NEW (testable):
objectives:
- [Action verb] + [specific grammar/vocabulary/skill] + [in context]
- [Action verb] + [specific grammar/vocabulary/skill] + [in context]
- [Action verb] + [specific grammar/vocabulary/skill] + [in context]
```

### 3. Add missing fields to cultural/fine-arts batch (seq 63-106)
These plans need: `activity_hints`, `grammar` (at minimum).
Template for activity_hints:
```yaml
activity_hints:
- type: quiz
  focus: [topic-specific comprehension]
  items: 15
- type: match-up
  focus: [vocabulary matching]
  items: 10
- type: fill-in
  focus: [grammar in context]
  items: 12
- type: reading
  focus: [text analysis]
  items: 4
```

### 4. Fix b2-review-bridge garbled character
```yaml
# Line 36, OLD:
- Пасивні дієприкметники з суфіксами -ний/-抄

# NEW:
- Пасивні дієприкметники з суфіксами -ний/-тий
```

### 5. Standardize `focus` taxonomy
Consolidate to: `grammar`, `vocabulary`, `style`, `culture`, `communication`, `practice`, `checkpoint`, `literature`, `fine-arts`, `linguistics`

---

## Recommendations

1. **Batch fix `register` field** across all 106 plans (script-able).
2. **Rewrite objectives** for the 17 template-objective plans and 45 non-testable-objective plans. This requires human or LLM review per-plan.
3. **Add `activity_hints`** to the 53 plans missing them. Use the plan content_outline to generate appropriate activity types.
4. **Upgrade 6 v1.0 plans** to v2.0 field parity.
5. **Fix b2-review-bridge** encoding error immediately.
6. **Verify all vocabulary_hints** with VESUM before build (automated script recommended).
