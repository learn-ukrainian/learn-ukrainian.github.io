# Phase A: Lightweight Research (Core Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Lightweight research. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: c2-061
level: C2
sequence: 61
slug: professional-portfolio-ii
version: '2.0'
title: Професійне портфоліо II — Багатоформатна презентація
subtitle: Introduction — Multi-format Portfolio
focus: domain
pedagogy: TTT
phase: C2.3 [Professional Language]
word_target: 5000
objectives:
- Аналізувати та класифікувати явища Цифрове портфоліо та платформи у автентичних текстах
- Продукувати тексти з коректним застосуванням Відеопрезентація та риторика
- Оцінювати стилістичну доречність мовних засобів у контексті Професійне портфоліо II — Багатоформатна презентація
- Застосовувати знання з теми «Кейс-стаді та методологія STAR» у власній мовній практиці
sources:
- name: Дія.Бізнес — Підприємництво
  url: https://business.diia.gov.ua/
  type: reference
  notes: Цифрові інструменти для професіоналів
- name: LinkedIn Україна
  url: https://www.linkedin.com/
  type: reference
  notes: Професійні мережі
- name: Behance/Dribbble для творчих професій
  url: https://www.behance.net/
  type: reference
  notes: Портфоліо креативних спеціалістів
content_outline:
- section: Вступ — Мультиформатне портфоліо (Introduction — Multi-format Portfolio)
  words: 500
  points:
  - 'Cultural shift: transitioning from traditional Ukrainian modesty to the proactive ''personal branding'' paradigm prevalent
    in IT and creative sectors'
  - 'Strategic consistency: maintaining a unified professional narrative across disparate digital formats to ensure a coherent
    personal brand'
- section: Цифрове портфоліо та платформи (Digital Portfolio and Platforms)
  words: 900
  points:
  - 'Adaptation of content strategy for different platforms: professional tone for LinkedIn vs. visual storytelling for Behance
    and Dribbble'
  - 'Linguistic purism as a professional marker: using clean Ukrainian (without calques or surzhyk) to signal high educational
    status and expertise'
- section: Відеопрезентація та риторика (Video Presentation and Rhetoric)
  words: 900
  points:
  - 'Video resume: applying rhetorical elements of persuasion and composition according to State Standard §4.3.5 for effective
    self-presentation'
  - 'Technical quality and digital literacy: importance of lighting and sound in video resumes as markers of professional
    attention to detail'
- section: Кейс-стаді та методологія STAR (Case Study and STAR Methodology)
  words: 1000
  points:
  - The STAR method (Situation, Task, Action, Result) as a rhetorical framework for structuring achievement-oriented project
    descriptions
  - 'Shifting from duty-based descriptions to result-based narratives: using measurable metrics and quantitative indicators
    of success'
- section: Презентаційні матеріали та візуалізація (Presentation Materials and Visualization)
  words: 900
  points:
  - 'Pitch deck structure according to State Standard §4.3.6: creating goal-oriented professional texts following a specific
    stylistic plan'
  - 'Infographics and visual hierarchy: highlighting key achievements and skills to manage audience attention and information
    density'
- section: Практикум — Мовна чистота (Practicum — Linguistic Purity)
  words: 800
  points:
  - 'Common learner error: correcting the Russian-influenced «приймати участь» with the proper Ukrainian «брати участь» in
    professional contexts'
  - 'Correction of temporal calques: using «протягом року» or «впродовж року» instead of the erroneous «на протязі року» in
    project documentation'
vocabulary_hints:
  required:
  - word (translation) — collocations; frequency/usage notes
  recommended:
  - word (translation) — usage notes
vocabulary:
  required:
  - цифрове портфоліо (digital portfolio)
  - особистий бренд (personal brand)
  - відеорезюме (video resume)
  - кейс-стаді (case study)
  - презентація (presentation)
  - слайд-дек (slide deck)
  - інфографіка (infographic)
  - метрика (metric)
  - візуалізація (visualization)
  - наратив (narrative)
  recommended:
  - pitch (pitch)
  - брендинг (branding)
  - вебінар (webinar)
  - контент (content)
  - платформа (platform)
  forbidden: []
activity_hints:
- type: quiz
  focus: Identify target structures in context
  items: 15
- type: fill-in
  focus: Complete sentences with correct forms
  items: 12
- type: match-up
  focus: Match Цифрове портфоліо та платформи examples to categories
  items: 12
- type: error-correction
  focus: Find and fix errors in authentic texts
  items: 10
- type: group-sort
  focus: Classify by Відеопрезентація та риторика
  items: 12
- type: essay-response
  focus: Produce text using target structures
activities:
  types_required:
  - reading
  - quiz
  - fill-in
  - critical-analysis
  - essay-response
  - comparative-study
  min_items_per_type: 6
  total_min_items: 30
  no_mirroring: true
connects_to:
- c2-62 (Професійна ідентичність — Особистий бренд українською)
- c2-63 (Повторення C2.3 — Консолідація професійної спеціалізації)
- c2-64 (Контрольна точка C2.3 — Оцінювання професійної спеціалізації)
persona:
  voice: Senior Specialist
  role: Agency Director
prerequisites:
- professional-portfolio-i
grammar:
- Вступ — Мультиформатне портфоліо
- Цифрове портфоліо та платформи
- Відеопрезентація та риторика
- Кейс-стаді та методологія STAR
register: академічний

```

**Level constraints quick-ref:**

```
# C2 Quick Reference

> This file supplements the build prompt. Do NOT repeat targets already injected
> via `5000`, `Full Ukrainian immersion. No English except technical terminology. Sentences max 35 words.`, etc.

## Grammar Scope

No grammar restrictions. Full literary Ukrainian. Near-native mastery expected.

## Immersion (100% Ukrainian)

Everything in Ukrainian — learner operates as near-native.
English ONLY in vocabulary table translations (YAML).
Latin/Greek scholarly terms (e.g., "damnatio memoriae", "genius loci") acceptable in academic contexts.

## Module Types

| Type | Modules | Focus |
|------|---------|-------|
| Stylistics | M01-25 | Stylistic perfection (7 styles) |
| Literary | M26-40 | Literary mastery |
| Professional | M41-75 | Professional meta-skills & specialization |
| Capstone | M76-100 | Meta-skills & final capstone |
| Checkpoint | M20,25,40,55,75,100 | Review + assessment |

## C2 Activity Design

C2 uses **analytical** activity types, not drill exercises:
- **reading** — extended authentic text analysis
- **essay-response** — long-form written production
- **critical-analysis** — literary/linguistic critique
- **comparative-study** — cross-text or cross-register comparison
- **quiz** — fewer but native-level complexity
- **true-false** — nuanced claim evaluation

**Not used at C2:** fill-in, cloze, unjumble, anagram, match-up, error-correction, mark-the-words, group-sort

```

Read the State Standard compliance mapping (small file — read this FIRST):

```
docs/l2-uk-en/state-standard-2024-mapping.yaml
```

The full State Standard 2024 is at `docs/l2-uk-en/UKRAINIAN-STATE-STANDARD-2024.txt` (431KB, ~6000 lines). **Do NOT read the entire file.** Instead:
1. Check the mapping file for the relevant `C2` section — find the grammar topic that matches your module
2. Use the `lines: [start, end]` coordinates to read ONLY that section from the full Standard
3. If no mapping entry exists for this topic, search by §number or keyword as fallback
4. If still no match, say so honestly — do NOT fabricate a §reference

---

## PART 1: Lightweight Research

Research **Професійне портфоліо II — Багатоформатна презентація** for the **C2** core track. Core tracks need lighter research than seminar tracks — focus on accuracy and State Standard alignment.

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
- **Word count**: minimum **5000** words — allocate outline sections accordingly
- **Colonial framing**: plan decolonized framing NOW so Phase B doesn't default to Russian comparisons
- **Russianisms**: ensure vocabulary_hints and examples avoid banned words (кушати→їсти, получати→отримувати)
- **Duplicate headers**: ensure outline section names don't share keywords

---

## Output Format

> **DELIMITER ENFORCEMENT**: Content outside delimiters is automatically discarded by the extraction pipeline.

### Output Block 1: Research Notes

```
===RESEARCH_START===

# Дослідження: Професійне портфоліо II — Багатоформатна презентація

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
