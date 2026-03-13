# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: b1-006
level: B1
sequence: 6
slug: phonetics-assimilation
version: '2.0'
title: 'Фонетика: асиміляція'
subtitle: 'Phonetics: Voicing & Softness Assimilation'
focus: grammar
pedagogy: PPP
phase: B1.1 [Meta-Language and Phonetics]
word_target: 4000
objectives:
- Learner can recognize and apply voicing assimilation rules
- Learner can pronounce -ться correctly as [ц'ц'а]
- Learner can apply softness assimilation in consonant groups
- Learner can distinguish spelling from pronunciation in assimilation contexts
content_outline:
- section: 'Вступ: Принцип милозвучності (Introduction: The Principle of Euphony)'
  words: 600
  points:
  - Align with State Standard §4.1.1 — introduction to assimilation as a core structural design principle of Ukrainian phonetics.
  - 'Discuss ''Милозвучність'' (Euphony) as a core cultural hook: explain how Ukrainian maintains a ''singing'' rhythm (співоча
    мова) by balancing vowels and consonants, differentiating it from the heavier clusters of West Slavic languages.'
  - Frame phonetic rules not as 'restrictions' but as 'tools for harmony' that allow the language to flow melodically, a source
    of national pride reflected in traditional folk songs.
  - Preview the assimilation focus of this module vs the next module (simplification and alternation).
- section: Асиміляція за дзвінкістю та глухістю (Voicing and Devoicing Assimilation)
  words: 900
  points:
  - 'Explain regressive assimilation: when a voiceless consonant is followed by a voiced one, it becomes voiced (вокзал: [вогзал],
    боротьба: [бород''ба]) — provide simple equations like т + б = [дб] for visual learners.'
  - 'Address a critical learner error: Devoicing Final Consonants (Russian/German interference) — emphasize that Ukrainian
    preserves final voiced sounds (хліб is [хл''іб], not [хл''іп]; дід is [дід], not [діт]).'
  - Discuss progressive assimilation and voicing pairs (з/с) before vowels vs consonants (зберегти vs списати) to ensure proper
    articulation in connected speech.
  - 'Extended drill: voiced/voiceless minimal pairs at word ends (плід/пліт, код/кіт, мороз/морок) for auditory discrimination.'
- section: Асиміляція за м'якістю (Softness Assimilation)
  words: 800
  points:
  - 'Present softness assimilation: consonants softening before other soft consonants ([с''в''іт], [з''н''ім]) — focus on
    high-frequency vocabulary to internalize the ''softness flow''.'
  - 'Systematic drilling of consonant pairs: soft+soft chains in common words (свіжість, зніяковіти, снігопад) — how softness
    propagates leftward.'
  - Contrast Ukrainian soft pronunciation with regional interferences to ensure a 'pure' native-like sound.
- section: Вимова -ться (The -ться Pronunciation)
  words: 800
  points:
  - This is the most common assimilation in daily Ukrainian. Dedicated section for thorough drilling.
  - Explicitly drill the pronunciation of -ться as [ц'ц'а] — correct the common error of pronouncing it as two separate sounds
    [т'-с'а] or hard [ца].
  - 'High-frequency reflexive verbs: сміється, навчається, називається, знаходиться, здається — drill each with audio-first
    approach.'
  - 'Spelling vs pronunciation: understand why we write -ться but pronounce [ц''ц''а] — historical grammar explanation (ть
    + ся → assimilation).'
- section: Асиміляція за місцем творення (Place Assimilation)
  words: 500
  points:
  - 'Assimilation of sibilants before ш/ж/ч: зшити → [шшити], безжалісний → [бежжалісний].'
  - 'з/с before ш/ч/ж: розшукати → [рошшукати], безчесний → [бешчесний].'
  - 'Prefix assimilation patterns: роз- + ш/ч, з- + ш/ч — predictable rules.'
- section: Практика та запобігання помилкам (Practice and Error Prevention)
  words: 400
  points:
  - Drill minimal pairs that differ only by assimilation/voicing at word ends to sharpen auditory discrimination.
  - 'Dictation practice: ''Write explicitly, pronounce smoothly'' — focus on words where spelling and pronunciation mismatch
    (like -ться) to prevent phonetic-influenced spelling errors.'
  - Include 'Скоромовки' (tongue twisters) targeting assimilation clusters to build articulatory agility.
vocabulary_hints:
  required:
  - вимова (pronunciation) — правильна вимова, чітка вимова, особливості вимови; High core frequency
  - звук (sound) — голосний звук, приголосний звук, твердий звук, м'який звук; High core frequency
  - приголосний (consonant) — твердий/м'який приголосний; Essential for grammatical discussion
  - голосний (vowel) — чергування голосних; Essential for grammatical discussion
  - чергування (alternation) — чергування звуків, історичне чергування; Specialized linguistic term for B1+
  - спрощення (simplification) — спрощення приголосних, спрощення в групах; Specialized term found in State Standard
  - асиміляція (assimilation) — асиміляція за дзвінкістю, уподібнення звуків; Technical term, use alongside 'уподібнення'
  recommended:
  - милозвучність (euphony) — принцип милозвучності, краса і милозвучність; Key cultural concept of Ukrainian identity
  - дзвінкий (voiced) — дзвінкий приголосний; Technical phonetic marker
  - глухий (voiceless) — глухий приголосний; Technical phonetic marker
  - м'який (soft) — м'який приголосний; Contrast with 'твердий'
  - скоромовка (tongue twister) — тренувати скоромовки; Practical tool for phonetic mastery
  - наголос (stress/accent) — ставити наголос; Crucial for rhythm
activity_hints:
- type: quiz
  focus: Identify correct pronunciation of consonant clusters
  items: 15
- type: match-up
  focus: Match written form to phonetic transcription
  items: 12
- type: fill-in
  focus: Write correct spelling despite pronunciation rules
  items: 15
- type: error-correction
  focus: Fix common pronunciation-influenced spelling errors
  items: 10
connects_to:
- 'b1-07 (Phonetics: Alternation & Simplification)'
prerequisites:
- b1-05 (Ready for Immersion)
persona:
  voice: Senior Language & Culture Specialist
  role: Voice Coach
grammar:
- Voicing assimilation (progressive and regressive)
- Softness assimilation (consonant groups)
- -ться pronunciation as [ц'ц'а]
- Place assimilation (sibilants before ш/ж/ч)
register: нейтральний
immersion: 75-100% Ukrainian

```

**Level constraints quick-ref:**

```
# B1 Quick Reference

> This file supplements the build prompt. Do NOT repeat targets already injected
> via `4000`, `Full Ukrainian immersion. Grammar explained IN Ukrainian. English only for disambiguation of false friends. Sentences max 30 words.`, etc.

## Grammar Scope

**Allowed:** All grammar constructions. Participles. Complex subordinate clauses.
Max 30 words per Ukrainian sentence. Max 4 clauses.

## Immersion Strategy (B1)

| Phase | Modules | Immersion | Notes |
|-------|---------|-----------|-------|
| B1.0 (Bridge) | M01-05 | Mixed | Teach grammar metalanguage; English scaffolding for abstract concepts |
| B1.1+ (Core) | M06-92 | **100%** | Full Ukrainian. English ONLY in vocabulary table translations |

**B1.0 Bridge modules:** English grammar term explanations allowed as transition from A2.

**B1.1+ Hard rule:** No English in prose, titles, callouts, or explanations.
No English in parentheses to clarify Ukrainian concepts:
- Wrong: **поки** — дія на тлі іншої дії (While she was cooking...)
- Right: **поки** — дія на тлі іншої дії, тобто одночасні процеси

## B1-Specific Writing Notes

- Content quality: equal treatment for all items in a category (same depth, same format)
- Example variety: mix standalone, table, inline, dialogue — no 5+ consecutive examples in same format
- Tables must have narrative context (2+ sentences before and after)
- Parallel sections use identical internal structure

```

Read the State Standard compliance mapping (small file — read this FIRST):

```
docs/l2-uk-en/state-standard-2024-mapping.yaml
```

The full State Standard 2024 is at `docs/l2-uk-en/UKRAINIAN-STATE-STANDARD-2024.txt` (431KB, ~6000 lines). **Do NOT read the entire file.** Instead:
1. Check the mapping file for the relevant `B1` section — find the grammar topic that matches your module
2. Use the `lines: [start, end]` coordinates to read ONLY that section from the full Standard
3. If no mapping entry exists for this topic, search by §number or keyword as fallback
4. If still no match, say so honestly — do NOT fabricate a §reference

---

## PART 1: Lightweight Research

Research **Фонетика: асиміляція** for the **B1** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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
- **Word count**: minimum **4000** words — allocate outline sections accordingly
- **Colonial framing**: plan decolonized framing NOW so Phase B doesn't default to Russian comparisons
- **Russianisms**: ensure vocabulary_hints and examples avoid banned words (кушати→їсти, получати→отримувати)
- **Duplicate headers**: ensure outline section names don't share keywords

---

## Output Format

> **DELIMITER ENFORCEMENT**: Content outside delimiters is automatically discarded by the extraction pipeline.

### Output Block 1: Research Notes

```
===RESEARCH_START===

# Дослідження: Фонетика: асиміляція

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
