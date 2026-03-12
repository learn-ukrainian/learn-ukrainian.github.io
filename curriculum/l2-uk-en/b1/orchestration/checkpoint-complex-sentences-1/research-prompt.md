# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: b1-037
level: B1
sequence: 37
slug: checkpoint-complex-sentences-1
version: '2.0'
title: 'Контрольна точка: складні речення (частина 1)'
subtitle: Checkpoint - Complex Sentences Part 1
focus: checkpoint
pedagogy: TTT
phase: B1.3a [Complex Sentences Checkpoint]
word_target: 4000
objectives:
- Learner can demonstrate mastery of complex sentence structures
- Learner can integrate knowledge from M26-M33
- Learner can self-assess readiness for B1.3b phase
- Learner can use relative clauses, purpose clauses, and conditionals
content_outline:
- section: Вступ та огляд (Introduction and Overview)
  words: 500
  points:
  - 'Review learning objectives focusing on learner autonomy and meta-cognition terms: «оцінювання» (assessment) and «результат»
    (result)'
  - Frame the milestone using terms «фінальна контрольна точка» and «ключова точка» to establish progress tracking for the
    B1.3a phase
  - Explain the importance of self-assessment («самооцінювання») in mastering complex syntax as defined in State Standard
    §4.4.3
- section: Відносні речення та «симфонічний» синтаксис (Relative Clauses and «Symphonic» Syntax)
  words: 1000
  points:
  - Mastering «який» in all cases; explicitly address the learner error of failure to agree in gender/number (e.g., correcting
    «Дівчина, який я бачив» to «яку я бачив»)
  - Syntactic integration of relative adverbs (де, куди, звідки, коли, що) according to Standard §4.4.3 for explanatory subordinate
    parts
  - 'Cultural Hook: Explore the «Symphonic Syntax» of Ukrainian literature (Gogol, Ukrainka); how complex sentences create
    «panoramic» views of reality'
  - 'Correcting «Preposition Stranding»: Address the English habit of ending with prepositions (e.g., «Дім, який я живу в»)
    by drilling the correct Ukrainian pattern «у якому я живу»'
- section: Підрядні речення мети (Purpose Clauses)
  words: 800
  points:
  - Usage of «щоб» + infinitive for identical subjects; mastery checkpoint for purpose clauses defined in the State Standard
  - Usage of «щоб» + past tense for different subjects; verify correct usage of gendered and plural past forms in subordinate
    clauses
  - Contrasting purpose clauses with simple results to ensure logical precision in academic and formal Ukrainian registers
- section: 'Умовні речення: Реальні та ірреальні ситуації (Conditionals: Real and Unreal Situations)'
  words: 900
  points:
  - 'Addressing the «Якби vs Якщо» Trap: Detailed drill on real conditionals («якщо») versus unreal/hypothetical situations
    («якби»)'
  - Correcting the error «Якщо я був би тобою...» to the required «Якби я був тобою...» to reflect the strict distinction
    in Standard §4.4.3
  - 'Consolidation of mixed conditionals: Applying distinctions between real possibility and hypothetical scenarios in complex
    narratives'
- section: Інтеграційний виклик та самоконтроль (Integration Challenge and Self-Control)
  words: 800
  points:
  - Comprehensive test applying «критерії оцінювання» (assessment criteria) and «формувальне оцінювання» (formative assessment)
  - 'Integration task: Combining relative, purpose, and conditional clauses into «panoramic» paragraphs reflecting authentic
    Ukrainian literary style'
  - Final error analysis focusing on relative pronoun agreement and preposition placement before relative pronouns to ensure
    B1.3a readiness
vocabulary_hints:
  required:
  - контрольна точка (checkpoint) — пройти контрольну точку, фінальна контрольна точка, ключова точка; medium frequency, educational/tech
    context
  - повторення (review) — інтервальне повторення, повторення вивченого, мати вигляд повторення; high frequency general term
  - оцінювання (assessment) — критерії оцінювання, формувальне оцінювання, самооцінювання, система оцінювання; key pedagogical
    term
  - інтеграція (integration) — процес інтеграції, інтеграція знань, європейська інтеграція, повна інтеграція; academic/political
    register
  - речення (sentence) — складне речення, просте речення, головне/підрядне речення, будувати речення; high frequency linguistic
    term
  - результат (result) — досягти результату, кінцевий результат, результат оцінювання; high frequency, critical for autonomy
  recommended:
  - самооцінювання (self-assessment) — важливий елемент автономного навчання; critical for checkpoint modules
  - прогрес (progress) — відстежувати прогрес, значний прогрес; tracking growth over the module arc
  - правильний (correct) — правильна відповідь, правильна форма; context of accuracy in grammar checks
  - помилка (error) — граматична помилка, допустити помилку; used for identifying specific syntactic traps
activity_hints:
- type: quiz
  focus: Complex sentence structures
  items: 30
- type: fill-in
  focus: Complete complex sentences
  items: 25
- type: error-correction
  focus: Fix sentence errors
  items: 20
- type: error-correction
  focus: Create complex sentences
  items: 15
connects_to:
- 'b1-38 (Допустові речення: хоча, незважаючи на)'
prerequisites:
- 'b1-36 (Умовні речення: змішані та складні умови)'
persona:
  voice: Senior Language & Culture Specialist
  role: Copy Editor
grammar:
- Integration of M26-M33 grammar
- Relative clauses (який, де/куди/звідки, коли/що)
- Purpose clauses and conditionals
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

Research **Контрольна точка: складні речення (частина 1)** for the **B1** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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

# Дослідження: Контрольна точка: складні речення (частина 1)

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
