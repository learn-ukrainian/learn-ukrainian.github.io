# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: b1-074
level: B1
sequence: 74
slug: health-wellness
version: '2.0'
title: Здоров'я та самопочуття
subtitle: Health and Wellness
focus: vocabulary
pedagogy: PPP
phase: B1.6 [Vocabulary Expansion II]
word_target: 4000
objectives:
- Learner can use 30 health and wellness words in context
- Learner can distinguish between здоров'я/самопочуття/стан
- Learner can form natural collocations with health-related nouns
- Learner can discuss health topics fluently
content_outline:
- section: Вступ (Introduction)
  words: 600
  points:
  - 'Introduction of the core concepts: ''здоров''я'' (health) vs. ''самопочуття'' (well-being/state). Connect to module b1-62
    by discussing how environmental factors like ecology impact one''s ''стан здоров''я''.'
  - 'Establish the ''Active Patient'' persona: learners practice asking ''Як ваше самопочуття?'' and ''На що ви скаржитеся?''
    while taking an active role in describing their condition rather than passively receiving advice.'
- section: Термінологія та симптоми (Terminology and Symptoms)
  words: 1000
  points:
  - 'Linguistic accuracy focus: Correction of the common Russism ''хворіти грипом'' (Instrumental) to the correct Ukrainian
    construction ''хворіти на грип'' (на + Accusative). Drill with various diseases (кір, ангіна, застуда).'
  - 'Grammar of Sensation: Clarify the distinction between ''почуватися'' (to feel as a state) and ''відчувати'' (to sense/perceive).
    Explicitly correct the error ''Я відчуваю добре'' to ''Я почуваюся добре''.'
  - 'Pain Construction: Detailed drill on the structure [У мене] (Genitive) + [болить/болять] (Verb) + [частина тіла] (Nominative).
    Contrast with English ''I have a...'' to ensure proper syntax.'
- section: 'Культурний контекст: Протяг та траволікування (Cultural Context: Drafts and Herbal Wisdom)'
  words: 800
  points:
  - 'The Cult of ''Protyah'': Explore the uniquely Ukrainian fear of drafts (''протяг''). Discuss social scenarios like closing
    windows in public transport and the belief that ''протяг'' is a primary cause of ''нездужання'' even in summer.'
  - 'Herbalism and Home Remedies: Introduction to ''народна медицина''. Focus on ''калина'' (viburnum) for colds, ''ромашка''
    (chamomile) for inflammation, and ''м''ята'' (mint) for digestion. Note the ubiquity of pharmacies (''аптеки'') that sell
    these alongside modern drugs.'
- section: 'Практика: У лікаря та в аптеці (Practice: At the Doctor and Pharmacy)'
  words: 1000
  points:
  - 'Medical Competencies (State Standard §3.7): Functional language for ''діагностика'' (diagnostics), including ''здавати
    аналізи'' (to take tests) and ''проходити обстеження'' (to undergo examination).'
  - 'Register Differentiation: Practice formal interaction with a doctor (describing history, receiving a ''діагноз'') vs.
    informal registers (complaining to a friend or asking for advice on ''лікування'' at the pharmacy).'
  - 'Pharmacy Scenarios: Asking for ''ліки'' (medicine) and ''засоби профілактики'' (preventative measures), focusing on ''зміцнення
    імунітету'' (strengthening immunity).'
- section: Підсумок та поради (Summary and Advice)
  words: 600
  points:
  - 'Wellness Advice: Using ''варто/треба'' with health verbs. Focus on ''профілактика'' as ''краще ніж лікування''. Discuss
    ''здорове харчування'' and ''режим дня'' for ''міцне здоров''я''.'
  - 'Social Etiquette and Wishes: Proper use of the toast/response ''На здоров''я!'' and the standard wish for a sick person
    ''Бажаю швидкого одужання!''.'
vocabulary_hints:
  required:
  - здоров'я (health) — міцне здоров'я, берегти здоров'я, стан здоров'я; High-frequency core term
  - самопочуття (well-being) — погане/гарне самопочуття, скаржитися на самопочуття; Essential for B1 state description
  - хворіти на... (to be ill with) — хворіти на грип/застуду; Must use 'на' + Accusative, avoid Instrumental case
  - почуватися (to feel [state]) — я почуваюся добре/кепсько; Reflects internal state, reflexive verb
  - боліти (to hurt) — у мене болить голова, у мене болять зуби; Verb agrees with the body part (subject)
  - одужувати (to recover) — швидко одужувати, бажаю одужання; Medium frequency, vital for social empathy
  - протяг (draft) — боятися протягу, зачинити вікно через протяг; High cultural relevance in Ukraine
  - лікування (treatment) — проходити курс лікування, ефективне лікування; Focus on the process of recovery
  - аптека (pharmacy) — купувати трави в аптеці, зайти в аптеку по ліки; Ubiquitous medical point of contact
  recommended:
  - діагностика (diagnostics) — аналізи й обстеження; State Standard §3.7 competency
  - профілактика (prevention) — профілактика захворювань, краще ніж лікування; Formal register
  - імунітет (immunity) — зміцнювати імунітет, слабкий імунітет; Common wellness topic
  - калина (viburnum) — чай з калини, народний засіб від застуди; Cultural icon of health
  - ромашка (chamomile) — полоскати горло ромашкою; Standard home remedy
  - діагноз (diagnosis) — поставити діагноз, попередній діагноз; Doctor-patient interaction
activity_hints:
- type: match-up
  focus: Health noun phrases
  items: 25
- type: fill-in
  focus: Complete health sentences
  items: 20
- type: fill-in
  focus: Health consultation scenarios
  items: 15
- type: quiz
  focus: Discuss wellness topics
  items: 10
connects_to:
- 'b1-75 (Емоції: глибоке занурення)'
prerequisites:
- b1-73 (Довкілля та екологія)
persona:
  voice: Senior Language & Culture Specialist
  role: Family Doctor
grammar:
- Noun collocations with health vocabulary
- Adjective-noun agreement in health contexts
- Expressing physical states
register: розмовний

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

Research **Здоров'я та самопочуття** for the **B1** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Здоров'я та самопочуття

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
