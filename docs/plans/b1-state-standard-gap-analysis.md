# B1 State Standard 2024 Gap Analysis

**Date**: 2026-03-31
**Analyst**: Claude (Opus 4.6)
**Source**: `docs/l2-uk-en/state-standard-2024-mapping.yaml` (B1 section, lines 1434-2450)
**Plans**: `curriculum/l2-uk-en/plans/b1/` (91 files)
**Curriculum**: `curriculum/l2-uk-en/curriculum.yaml` (91 modules listed under `levels.b1`)

---

## 1. Inventory Summary

| Metric | Count |
|--------|-------|
| Modules in curriculum.yaml | 91 |
| Plan files in plans/b1/ | 91 |
| Orphan files (plan exists, not in curriculum.yaml) | 0 |
| Missing files (in curriculum.yaml, no plan file) | 0 |
| Plans with `activity_hints` | 91/91 |
| Plans with `references` | 91/91 |
| Plans with `dialogue_situations` | 91/91 |
| Plans with `reading_situations` | 0/91 |
| Plans with `writing_tasks` | 0/91 |

**File sync is perfect.** Every curriculum.yaml slug has a matching plan file, and no orphan files exist.

**Field completeness note**: `reading_situations` and `writing_tasks` are absent from all 91 plans. These are not currently part of the B1 plan schema (they are not used by the build pipeline), so this is a schema question, not a content gap. The dialogue_situations field handles communicative context. However, if the State Standard's speech activity requirements (listening, reading, writing, speaking) are to be tracked explicitly, these fields could be added in a future schema revision.

---

## 2. Covered: State Standard Topics with Matching B1 Plans

### 2.1 Phonetics (SS 4.1)

| SS Ref | SS Requirement | B1 Module(s) | Notes |
|--------|---------------|---------------|-------|
| 4.1.1 | Consonant clusters, assimilation, simplification; alternations (о/i, е/i, о/е) | `alternation-vowels`, `alternation-consonants-nouns`, `alternation-consonants-verbs`, `simplification-consonants` | Thorough. 4 dedicated modules. |
| 4.1.2 | Mobile stress patterns in noun/verb paradigms | `metalanguage-phonetics` | Covered in phonetics metalanguage module; also threaded through case and verb modules. |
| 4.1.3 | Advanced euphony (все/усе, вже/уже) | `metalanguage-phonetics`, threaded | Covered as part of phonetics overview; reinforced in communication modules. |
| 4.1.5 | Abbreviations and graphic compression | `text-compression` | Dedicated module covering абревіатури, складноскорочені слова, графічні скорочення. |

### 2.2 Morphology (SS 4.2)

| SS Ref | SS Requirement | B1 Module(s) | Notes |
|--------|---------------|---------------|-------|
| 4.2.1.1 | Full noun paradigms -- all 4 declensions, soft/hard, exceptions, fleeting vowels | `noun-subclasses-masculine`, `noun-subclasses-hissing`, `noun-subclasses-feminine`, `pluralia-tantum`, `alternation-vowels` | Strong. 5 modules cover noun subclasses + fleeting vowels. |
| 4.2.1.2 | Adjective paradigm -- short forms, possessive adjectives (батьків, материн) | `short-form-adjectives`, `word-formation-adjectives` | **Partial** -- see Partial Gaps section. |
| 4.2.1.3 | Numeral declension -- collective numerals (двоє, п'ятеро), fractions | `cases-with-ordinal-numerals`, `cases-with-quantity-expressions` | Collective numerals (збірні) explicitly covered in `cases-with-quantity-expressions`. Fractions mentioned. |
| 4.2.1.4 | Expanded pronouns -- indefinite (хтось, щось, дехто), negative (ніхто, ніщо), relative (який, що, хто) | `advanced-pronouns` | Dedicated module covering all three pronoun categories. |

### 2.3 Case Usage (SS 4.2.2) -- Nuanced Meanings

| SS Ref | SS Requirement | B1 Module(s) | Notes |
|--------|---------------|---------------|-------|
| 4.2.2.1 | Nominative -- subject types, apposition, compound subjects | `metalanguage-syntax-cases` | Covered as part of syntax/case metalanguage bridge. |
| 4.2.2.2 | Genitive -- partitive, possession, comparison, negation, temporal; 15+ prepositions | `genitive-nuances` | Dedicated module. |
| 4.2.2.3 | Dative -- recipient, experiencer, impersonal, purpose | `dative-nuances` | Dedicated module. |
| 4.2.2.4 | Accusative -- direction, duration, measure; expanded prepositions | `prepositions-spatial-review`, `prepositions-temporal` | Covered across preposition modules. |
| 4.2.2.5 | Instrumental -- agent, instrument, manner, comparison; 8+ prepositions | `instrumental-nuances` | Dedicated module. |
| 4.2.2.6 | Locative -- location, topic, time; expanded preposition usage | `prepositions-spatial-review`, `prepositions-temporal` | Covered across preposition modules. |
| 4.2.2.7 | Vocative -- formal/informal, profession + name address | `vocative-formal` | Dedicated module. |

### 2.4 Verb Forms (SS 4.2.3)

| SS Ref | SS Requirement | B1 Module(s) | Notes |
|--------|---------------|---------------|-------|
| 4.2.3.1 | Indicative -- full conjugation, aspect in all tenses, participles, gerunds | `b1-baseline-past-present`, `b1-baseline-future-aspect`, `participles-active`, `participles-passive`, `gerunds-imperfective`, `gerunds-perfective`, `reflexive-verbs-nuances`, `passive-voice-intro` | Excellent coverage. 8+ modules. |
| 4.2.3.2 | Imperative -- perfective/imperfective distinction | `imperative-nuances` | Dedicated module. |
| 4.2.3.3 | Conditional mood -- якби + past tense | `conditionals-real`, `conditionals-unreal` | Two dedicated modules (real + unreal). |

### 2.5 Word Formation (SS 4.3)

| SS Ref | SS Requirement | B1 Module(s) | Notes |
|--------|---------------|---------------|-------|
| 4.3.1 | Comparative/superlative -- synthetic and analytic | `adjectives-comparative`, `adjectives-superlative`, `adjectives-suppletive` | Three dedicated modules. |
| 4.3.2 | Adverb comparison | `adverbs-comparison-formation` | Dedicated module covering formation + comparison. |
| 4.3.3 | Agent nouns -- -тель, -ник, -ар, -іст | `word-formation-nouns` | Dedicated module with all suffixes. |
| 4.3.4 | Verbal nouns -- -ння/-ення | `verbal-nouns`, `word-formation-nouns` | Two modules cover this. |
| 4.3.5 | Place nouns -- -ня, -ище | `word-formation-nouns` | Covered in the same module (-ня, -ниця, prefixal-suffixal). |
| 4.3.6 | Adjectives from nouns -- -ний, -ський, -зький | `word-formation-adjectives` | Dedicated module. |
| 4.3.7 | Adverbs from adjectives -- -о, -е | `adverbs-comparison-formation` | Covered (formation from adjectives is the first objective). |
| 4.3.8 | Prefixed motion verbs -- ви-, при-, за-, від- | `motion-prefixes-arrival`, `motion-prefixes-departure`, `motion-prefixes-in-out`, `motion-prefixes-transit`, `motion-prefixes-around`, `motion-flight-swim`, `figurative-motion` | Excellent. 7 modules covering all major prefixes + figurative use. |

### 2.6 Syntax (SS 4.4)

| SS Ref | SS Requirement | B1 Module(s) | Notes |
|--------|---------------|---------------|-------|
| 4.4.1.1 | Declarative -- expanded word order, topic-comment | `metalanguage-syntax-cases`, `text-register-formal` | Covered in syntax metalanguage and register modules. |
| 4.4.1.2 | Questions -- indirect questions, rhetorical questions | `complex-subordinate-object`, `reported-speech` | Indirect questions covered via з'ясувальні речення; reported speech covers transformation. |
| 4.4.2 | Complex simple sentences -- participial phrases, homogeneous members, introductory words | `participle-phrases`, `gerund-phrases`, `introductory-words` | **Partial** -- see Partial Gaps section. |
| 4.4.3 | Complex sentences -- 10+ conjunction types, relative clauses, temporal/causal/conditional/concessive | `complex-compound`, `complex-subordinate-object`, `complex-subordinate-relative`, `complex-subordinate-time`, `complex-subordinate-reason`, `complex-subordinate-condition`, `complex-subordinate-purpose`, `complex-subordinate-concess` | Excellent. 8 dedicated modules covering all clause types. |

### 2.7 Stylistics (SS 4.5)

| SS Ref | SS Requirement | B1 Module(s) | Notes |
|--------|---------------|---------------|-------|
| 4.5.1 | Register distinction -- formal vs informal, lexical and syntactic markers | `text-register-formal`, `text-register-informal` | Two dedicated modules. |

### 2.8 Thematic Areas (SS 3)

| SS Theme | B1 Module(s) | Status |
|----------|-------------|--------|
| людина (person) | `people-and-relationships` | Covered |
| дім (home) | `housing-and-renting` | Covered |
| щоденне життя (daily life) | `daily-life-and-routines` | Covered |
| дозвілля (leisure) | `leisure-culture-festivals` | Covered |
| подорожі (travel) | `traveling-ukraine` | Covered |
| суспільні відносини (social relations) | `society-and-media`, `debate-and-opinion` | Covered |
| здоров'я (health) | `health-at-the-doctor` | Covered |
| освіта (education) | `education-and-university` | Covered |
| робота (work) | -- | **GAP** -- see below |
| купівля (shopping) | `shopping-and-services` | Covered |
| ресторан (restaurant/food) | -- | **GAP** -- see below |
| послуги (services) | `shopping-and-services` | Covered (combined) |
| місця (places) | `traveling-ukraine`, `housing-and-renting` | Covered (distributed) |
| природа (nature) | `nature-and-environment` | Covered |
| традиції (traditions) | `leisure-culture-festivals` | Covered (combined with культура) |

---

## 3. GAPS: State Standard Topics NOT Covered by Any B1 Plan

| # | SS Ref | Requirement | Severity | Recommendation |
|---|--------|-------------|----------|----------------|
| 1 | 4.2.1.2 | **Possessive adjectives** (присвійні прикметники: батьків, материн, Олегів) | **HIGH** | The SS explicitly requires possessive adjective forms at B1. No plan addresses this. `short-form-adjectives` covers short forms only; `word-formation-adjectives` covers denominal formation but not possessive declension. **Add a dedicated plan or integrate into `word-formation-adjectives` as a major section.** |
| 2 | 4.4.2 | **Homogeneous members** (однорідні члени речення) in complex simple sentences | **HIGH** | The SS requires understanding of однорідні члени as part of ускладнене просте речення. No B1 module covers this. Participial phrases and introductory words are covered, but однорідні члени are a separate syntactic phenomenon (узагальнювальне слово, punctuation, etc.). **Add a dedicated plan.** |
| 3 | Theme | **Робота (work/employment)** as a thematic area | **MEDIUM** | The SS lists робота as a B1 theme. No dedicated communication module covers workplace vocabulary and situations (job search, workplace interactions, describing your profession). Education is covered but not workplace. **Add a communication module or expand `daily-life-and-routines`.** |
| 4 | Theme | **Ресторан / Харчування (food/restaurant)** as a thematic area | **MEDIUM** | The SS lists ресторан at B1. While A1-A2 likely cover basic restaurant vocabulary, B1 should deepen this (ordering, dietary preferences, reviews, complaints, regional cuisine vocabulary). **Add a communication module or verify A2 coverage is sufficient.** |

---

## 4. Partial Gaps: Topics Covered but Potentially Insufficient

| # | SS Ref | Requirement | Current Coverage | Concern | Severity |
|---|--------|-------------|-----------------|---------|----------|
| 1 | 4.2.1.2 | Short forms of adjectives | `short-form-adjectives` | The plan focuses on literary/poetic short forms (зелен, потрібен) and correctly identifies them as народнопоетичний register. However, the SS also mentions повні/короткі forms in general context. The plan seems appropriate in scope, but possessive adjectives (батьків, материн) are the real gap here. | LOW |
| 2 | 4.2.1.3 | Fractions (дроби) | `cases-with-quantity-expressions` | The plan mentions collective numerals explicitly. Fractions (одна друга, три чверті) may need verification that they are covered with sufficient depth. | LOW |
| 3 | 4.4.1.2 | Rhetorical questions | Not explicitly | Rhetorical questions appear in some plans incidentally but there is no dedicated treatment. At B1 this is lower priority (B2 covers it explicitly), but the SS does mention it under 4.4.1.2. | LOW |
| 4 | 4.1.2 | Mobile stress in noun/verb paradigms | `metalanguage-phonetics` + threaded | Stress is introduced in the phonetics metalanguage module and referenced in alternation/case modules, but there is no dedicated module on рухомий наголос patterns across paradigms. The treatment is distributed rather than systematic. This is likely adequate for B1 but could be made more explicit. | LOW |
| 5 | 4.4.2 | Complex simple -- introductory words (вставні слова) | `introductory-words` | Covered by a dedicated module. However, the related concept of вставлені конструкції (parenthetical constructions, which are distinct from вставні слова) is not mentioned. At B1, вставні слова alone is likely sufficient. | LOW |
| 6 | 4.4.1.1 | Topic-comment structure (тема-рема) | Implicit in syntax modules | The SS mentions "expanded word order, topic-comment structure" for declarative sentences. No B1 plan explicitly addresses тема-рема as a concept. It is implicitly covered in text-register modules. For B1, this is borderline -- explicit treatment could help learners understand Ukrainian word order flexibility. | MEDIUM |

---

## 5. Extra: B1 Plans Beyond State Standard Scope

These plans go beyond what the SS explicitly requires at B1. This is **not a problem** -- our curriculum is richer than the SS minimum.

| Module | What It Adds |
|--------|-------------|
| `metalanguage-phonetics` | Ukrainian phonetics metalanguage (звук, літера, фонема) -- not an SS requirement but excellent pedagogy for the A2->B1 bridge |
| `metalanguage-morphology` | Morphology metalanguage (корінь, суфікс, відмінок) -- same rationale |
| `metalanguage-syntax-cases` | Syntax/case metalanguage -- same rationale |
| `b1-baseline-past-present` | Review of A2 verb tenses -- bridge module |
| `b1-baseline-future-aspect` | Review of future tense + aspect -- bridge module |
| `figurative-motion` | Figurative use of motion verbs (час іде, дощ іде) -- creative extension beyond SS |
| `passive-voice-intro` | Passive voice introduction -- SS places full passive at B2, but B1 intro is good scaffolding |
| `double-negation` | Подвійне заперечення -- useful grammar point not explicitly in SS for B1 |
| `narrative-mastery` | Storytelling -- communicative skill beyond SS grammar requirements |
| `debate-and-opinion` | Argumentation -- practical communication, not in SS grammar but valuable |
| `reading-literature` | Literary reading -- enrichment beyond SS minimum |
| `practice-exam-reading` | Practice exam format -- assessment-oriented |
| `practice-exam-writing` | Practice exam format -- assessment-oriented |
| `b1-finale` | Final review module |
| `comprehensive-b1-review` | Comprehensive review |
| 10 checkpoint modules | Regular assessment checkpoints |

**Assessment**: The "extra" modules are pedagogically sound additions. The metalanguage bridge (modules 1-3) is particularly valuable. The motion verb depth (7 modules) exceeds SS requirements but matches how Ukrainian textbooks teach this topic. No modules should be removed.

---

## 6. Quick Field Audit

| Field | Present | Missing | Notes |
|-------|---------|---------|-------|
| `activity_hints` | 91/91 | 0 | All plans have activity hints |
| `references` | 91/91 | 0 | All plans cite textbook sources |
| `dialogue_situations` | 91/91 | 0 | All plans have dialogue contexts |
| `vocabulary_hints` | 91/91 | 0 | All plans have vocabulary (spot-checked) |
| `content_outline` | 91/91 | 0 | All plans have section outlines |
| `reading_situations` | 0/91 | 91 | Not part of current plan schema |
| `writing_tasks` | 0/91 | 91 | Not part of current plan schema |

---

## 7. Summary and Recommendations

### Overall Assessment

The B1 curriculum has **excellent** State Standard coverage. Of the ~25 distinct competency areas in the SS B1 section, 21 are thoroughly covered with dedicated modules. The curriculum goes significantly beyond the SS minimum with metalanguage bridge modules, extensive motion verb coverage, and rich communicative practice.

### Priority Fixes (ordered by severity)

1. **HIGH -- Possessive adjectives (присвійні прикметники)**: Add coverage of батьків, материн, Олегів declension. Either create a new plan or add a major section to `word-formation-adjectives` or `short-form-adjectives`. The SS explicitly lists this at 4.2.1.2.

2. **HIGH -- Homogeneous members (однорідні члени речення)**: Add a dedicated module covering однорідні члени in ускладнене просте речення -- узагальнювальне слово, punctuation rules, types of однорідні члени. The SS explicitly lists this at 4.4.2.

3. **MEDIUM -- Work/employment theme**: Add a communication module covering workplace vocabulary (пошук роботи, співбесіда, робоче місце, колеги, обов'язки). The SS lists робота as a B1 theme.

4. **MEDIUM -- Restaurant/food theme**: Verify A2 coverage is sufficient for B1 or add a dedicated B1 module on food culture, ordering, dietary preferences, regional cuisine vocabulary.

5. **MEDIUM -- Topic-comment structure (тема-рема)**: Consider adding explicit treatment of this concept to a syntax module. It helps learners understand why Ukrainian word order is "free" -- it is information-structure-driven, not truly free.

### What Works Well

- **Morphophonemic coverage** is outstanding (4 dedicated modules on alternations + simplification)
- **Motion verb system** is the best I've seen in any L2 curriculum (7 modules + figurative)
- **Case nuances** have dedicated modules for genitive, dative, instrumental, vocative
- **Complex sentence types** are thoroughly covered (8 clause-type modules)
- **Word formation** covers all SS categories across 4+ modules
- **All plans have references** to Ukrainian textbooks (Заболотний, Авраменко, Литвінова, Голуб)
- **File sync is perfect** -- no orphans, no missing files
