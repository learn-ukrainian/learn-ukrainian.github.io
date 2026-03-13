# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: a2-034
level: A2
sequence: 34
slug: i-think-that
version: '2.0'
title: I Think That...
subtitle: Expressing Opinions
focus: vocabulary
pedagogy: PPP
phase: A2.2
word_target: 2000
objectives:
- Learner can express personal opinions clearly
- Learner can agree or disagree politely
- Learner can use introductory phrases to structure arguments
- Learner can discuss topics using 'я вважаю' and 'мені здається'
sources:
- name: Ukrainian State Standard 2024 - Opinions
  url: https://mon.gov.ua/
  type: reference
  notes: Communicative requirements for expressing stance and debate at A2
- name: Rhetoric and Debate in Ukrainian Culture
  url: https://uk.wikipedia.org/wiki/Дискусія
  type: reference
  notes: Social norms for agreement and disagreement
content_outline:
- section: 'Вступ: Від фактів до поглядів (Introduction: From Facts to Perspectives)'
  words: 275
  points:
  - The transition from stating objective facts (A1) to expressing subjective perspectives (A2); referencing Ukrainian State
    Standard §2 (Каталог А) on expressing personal stances.
  - 'The cultural concept of sincerity (щирість) vs. politeness (ввічливість): Ukrainians value directness but use specific
    linguistic markers to maintain social harmony in formal contexts.'
  - 'The ''No'' ambiguity: Exploring why a direct ''Ні'' is often avoided in favor of explanatory phrases like ''Мені здається,
    що це не зовсім так'' to prevent sounding harsh or confrontational.'
- section: 'Презентація: Дієслова думки (Presentation: Thinking Verbs)'
  words: 525
  points:
  - 'The contrast between ''Думати'' (mental process: ''I am thinking about it'') and ''Вважати'' (firm opinion: ''I believe/consider
    it to be'').'
  - 'Learner error alert: Explicitly debunking the use of ''рахувати'' (to count numbers) for expressing opinions—a common
    calque from Russian ''считать'' (Error: ''Я рахую, що...'' vs Correct: ''Я вважаю, що...'').'
  - 'Introduction to ''Здаватися'' for impressions: Using the impersonal construction ''Мені здається, що...'' to offer softer,
    less dogmatic opinions.'
  - 'Gender-sensitive agreement: Teaching ''Я згоден'' (Masculine) vs ''Я згодна'' (Feminine) with specific drills to correct
    common mismatch errors (e.g., a woman saying ''Я згоден'').'
- section: 'Граматика: Сполучник ''що'' та впевненість (Grammar: Conjunction ''що'' and Certainty)'
  words: 400
  points:
  - 'The ''Hard Comma'' Rule: Implementing State Standard §4.4.2 requirement for mandatory commas before ''що'' in complex
    sentences (Contrast: ''Я знаю, що ми праві'' vs English optional ''that'').'
  - 'The Certainty Ladder: Categorizing phrases from ''Я впевнений(-а)'' to ''Напевно'' and ''Я сумніваюся'' as per State
    Standard §2 requirements for expressing stance.'
  - 'Introductory structures: ''На мою думку'' and ''На мою особисту думку'' vs ''На думку експертів'' for citing external
    authority.'
- section: 'Практика: Обґрунтування думки (Practice: Justifying Opinions)'
  words: 475
  points:
  - 'Elementary grounding drills: Practice expressing an opinion and providing a basic ''тому що'' (because) justification
    as mandated by the A2 communicative standard.'
  - 'Polite softening patterns: Using ''Вибачте, але...'', ''На жаль, я не згоден'', and ''З одного боку... з іншого боку''
    to structure balanced arguments.'
  - 'Fact-to-Opinion conversion: Exercises changing ''Сьогодні холодно'' into ''Я вважаю, що сьогодні холодно'' or ''Мені
    здається, що сьогодні холодно'' to distinguish degrees of conviction.'
- section: Діалоги та застосування (Dialogues and Application)
  words: 325
  points:
  - 'Scenario-based dialogue: Discussing a movie or work proposal using softeners to navigate disagreement without direct
    ''Ні''.'
  - 'Roleplay: A talk show guest scenario where the learner must use ''Безумовно'', ''Цілком можливо'', and ''Я впевнений''
    to respond to different prompts.'
  - 'Final summary: Reviewing the mandatory punctuation and the distinction between process-thinking and opinion-holding.'
vocabulary_hints:
  required:
  - думати (to think) — про майбутнє, довго думати, думати над проблемою; high frequency, denotes mental process
  - 'вважати (to consider/believe) — я вважаю, що...; вважати правильним; вважати за потрібне; high frequency, denotes firm
    opinion; note: never use ''рахувати'''
  - здаватися (to seem) — мені здається, що...; здається, дощ починається; medium frequency, denotes impression or soft stance
  - згоден / згодна (agree) — я цілком згоден, я не згоден, я згодна з вами; requires gender agreement
  - що (that) — mandatory comma before this conjunction in complex sentences (State Standard §4.4.2)
  - впевнений / впевнена (sure/confident) — я впевнений(-а), що...; expressing high certainty (State Standard §2)
  recommended:
  - на думку (in the opinion of) — на мою думку, на думку експертів, на мою особисту думку; used as an introductory phrase
  - можливо (possible/perhaps) — це можливо, цілком можливо, можливо, що...; high frequency probability marker
  - напевно (probably) — medium certainty marker
  - сумніватися (to doubt) — я сумніваюся, що...; expressing uncertainty (State Standard §2)
  - вибачте, але (excuse me, but) — polite softener for disagreement
  - на жаль (unfortunately) — softener for refusal or disagreement
persona:
  voice: Encouraging Cultural Guide
  role: Talk Show Guest
grammar:
- opinion phrases (я думаю, на мою думку)
- agreement/disagreement phrases
- filler words (можливо, напевно)
- justifying opinions
module_type: vocabulary
immersion: 60-75% Ukrainian
prerequisites:
- she-said-that
connects_to:
- i-feel-like
register: розмовний
activity_hints:
- type: match-up
  focus: Match words to definitions
  items: 12
- type: fill-in
  focus: Complete sentences with vocabulary
  items: 8
- type: group-sort
  focus: Sort by category
  items: 10
- type: quiz
  focus: Choose correct word for context
  items: 10
- type: fill-in
  focus: Use words in sentences
  items: 6
- type: essay-response
  focus: Write using domain vocabulary

```

**Level constraints quick-ref:**

```
# A2 Quick Reference

> This file supplements the build prompt. Do NOT repeat targets already injected
> via `2000`, `TARGET: 55-75% Ukrainian.
LANGUAGE ROLES:
- PRIMARY: Ukrainian for all content — dialogues, examples, section intros, cultural context.
- ENGLISH: Only for abstract grammar concepts that need explicit explanation.
- STRUCTURAL RULE: Each sentence is 100% Ukrainian OR 100% English. Dialogues, examples, section intros all stay Ukrainian-only.
A2 register. Concrete everyday vocabulary. No literary language, no metaphors. Ukrainian sentences max 15 words. Max 2 clauses. All cases allowed. Simple subordinate clauses only. Aspect pairs introduced. No participles.`, ``, etc.

## Grammar Scope

**Allowed:** All 7 cases. Simple subordinate clauses (який/що/коли). Aspect pairs introduced.
Max 15 words per Ukrainian sentence. Max 2 clauses per sentence.

**Forbidden:** Participles. Complex subordinate clauses.

## Immersion Strategy (A2)

A2 uses graduated immersion (50-90%) across three bands:

| Band | Modules | Target | English used for |
|------|---------|--------|-----------------|
| Core grammar | M01-20 | 45-65% | Grammar theory (cases, aspect) |
| Applied grammar | M21-50 | 55-75% | Abstract concepts only |
| Consolidation | M51-70 | 70-90% | Vocabulary tables only |

**Critical rule:** NEVER mix languages within a sentence at A2.
Each sentence is 100% Ukrainian OR 100% English.
Ukrainian paragraph first, then English translation paragraph below if needed.

## A2-Specific Writing Notes

- No Latin transliteration — stress marks (´) only
- No IPA or phonetic brackets
- Register: A2 only. Concrete everyday vocabulary (їсти, ходити, купувати)
- No literary/poetic language, no abstract nouns (почуття, відчуття, стан, сутність)
- No metaphors or figurative speech
- Grammar terms in Ukrainian introduced where relevant (відмінок, називний, etc.)

```

Read the State Standard compliance mapping (small file — read this FIRST):

```
docs/l2-uk-en/state-standard-2024-mapping.yaml
```

The full State Standard 2024 is at `docs/l2-uk-en/UKRAINIAN-STATE-STANDARD-2024.txt` (431KB, ~6000 lines). **Do NOT read the entire file.** Instead:
1. Check the mapping file for the relevant `A2` section — find the grammar topic that matches your module
2. Use the `lines: [start, end]` coordinates to read ONLY that section from the full Standard
3. If no mapping entry exists for this topic, search by §number or keyword as fallback
4. If still no match, say so honestly — do NOT fabricate a §reference

---

## PART 1: Lightweight Research

Research **I Think That...** for the **A2** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

### Your RAG Tools

| Tool | When to use |
|------|-------------|
| `search_text` | Find how this topic is taught in Ukrainian textbooks |
| `verify_words` | Check vocabulary exists in VESUM dictionary |
| `query_grac` mode=`frequency` | Get word frequency data |
| `query_wikipedia` mode=`summary` | Quick fact-check for cultural hooks |

### Research Requirements

1. **State Standard Reference**: Look up the §section in `state-standard-2024-mapping.yaml`, then read ONLY that section from `UKRAINIAN-STATE-STANDARD-2024.txt`. Quote the relevant requirement.
2. **Vocabulary Frequency**: Use `query_grac` (mode=`frequency`) for key vocabulary items. Do NOT rely on memory alone.
3. **Cultural Hook**: Use `query_wikipedia` to find 1-2 verified cultural facts to anchor the lesson.
4. **Cross-References**: Note which modules this builds on and prepares for (check the plan's `connects_to` field).
5. **Common Errors**: Identify 2-3 common learner mistakes for this grammar point/topic.

### Decolonized Framing

When researching, frame Ukrainian independently — **never as a derivative or variant of Russian:**
- Describe Ukrainian features positively ("Ukrainian has...", "Ukrainian uses...")
- Do NOT use Russian as the baseline for comparisons ("Unlike Russian...", "Different from Russian...")
- If comparing language systems is useful, use non-Russian languages (Polish, Portuguese, etc.)
- Note how topics have been historically misframed by Russian/Soviet sources and provide the Ukrainian-centric perspective

### Research Output Cap
Keep research notes under **1500 words**. Focus on density: facts, dates, quotes, tables — not prose.

### Additional for Core B (B1.6+, B2, C1, C2, PRO)

- Domain-specific vocabulary collocations from professional glossaries (PRO tracks)
- Stylistic/dialectal features from academic sources (C2)
- Register distinctions (formal vs. informal usage)

## Downstream Audit Gates (Phase B content will be checked for)

Plan your outline knowing that Phase B content must pass these gates:
- **Word count**: minimum **2000** words — allocate outline sections accordingly
- **Colonial framing**: plan decolonized framing NOW so Phase B doesn't default to Russian comparisons
- **Russianisms**: ensure vocabulary_hints and examples avoid banned words (кушати→їсти, получати→отримувати)
- **Duplicate headers**: ensure outline section names don't share keywords

---

## Output Format

> **DELIMITER ENFORCEMENT**: Content outside delimiters is automatically discarded by the extraction pipeline.

### Output Block 1: Research Notes

```
===RESEARCH_START===

# Дослідження: I Think That...

## State Standard Reference
§{section_number}: "{quoted requirement}"
Alignment: {how this module addresses the standard}

## Vocabulary Frequency
| Word | Frequency / Source | Key collocations |
|------|-------------------|------------------|
| ...  | ...               | ...              |

## Cultural Hooks
1. {Verified fact with source}
2. {Verified fact with source}

## Common Learner Errors
1. {Error pattern} → {Correct form} — {Why it happens}
2. ...

## Cross-References
- Builds on: {module slugs}
- Prepares for: {module slugs}

## Multimedia Resources
(If you naturally encountered relevant Ukrainian-language YouTube videos or audio resources during your web research, note them here. Do NOT search specifically for videos — the discover phase handles that. Maximum 3 entries.)
- {Channel — Title — URL — 1-sentence relevance note}
- (none encountered)

## Notes for Content Writing
- {Any additional observations for Phase B}

===RESEARCH_END===
```

## Friction Report (MANDATORY)

After both output blocks, include:

```
===FRICTION_START===
**Phase**: Phase A: Meta + Research (Core)
**Step**: {what you were doing when friction occurred, or "Full Phase A"}
**Friction Type**: NONE | TOKEN_LIMIT_TRUNCATION | TOOL_REDUNDANCY | STATE_STANDARD_NOT_FOUND | ...
**Raw Error**: {actual error or "None"}
**Self-Correction**: {what you changed, or "N/A"}
**Proposed Tooling Fix**: {if a script/design issue, or "N/A"}
===FRICTION_END===
```

---

## Boundaries

- Do NOT write lesson content — only research notes
- Do NOT generate activities or vocabulary
- Do NOT fabricate State Standard references — if you can't find the exact §, say so
- Do NOT reference persona names or voice instructions — persona is assigned at content generation time
- Do NOT request skills, delegate to Claude, or skip this phase
