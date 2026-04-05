# Plan Review: aspect-concept

**Track:** a2 | **Sequence:** 2 | **Version:** 1.0
**Verdict:** NEEDS FIXES

## Rule Compliance

| Check | Status | Details |
|-------|--------|---------|
| word_target | PASS | Plan: 2000, Config: 2000 |
| section_budgets | PASS | Sum = 2000 vs target 2000 (0%) |
| required_fields | FAIL | Missing: `persona`, `grammar`, `register` |
| version_string | PASS | `'1.0'` is a string |

## State Standard Alignment

| Grammar Topic | In Standard? | Standard Level | Plan Level | Status |
|--------------|-------------|----------------|------------|--------|
| Aspect (вид дієслова) | YES | A2 §4.2.3.1 + §4.3.2 | A2 M02 | PASS |
| Perfective/Imperfective distinction | YES | A2 §4.2.3.1 | A2 M02 | PASS |
| Perfective has no true present tense | YES | A2 verb forms | A2 M02 | PASS |
| Past tense forms | YES | A1 §4.2.4.1 (review) | A2 M02 | PASS |

**Notes:** Aspect introduction is perfectly placed at A2 M02 per State Standard. The Standard explicitly lists "aspect pairs (доконаний/недоконаний)" under A2 verbs.

## Grammar Verification (Textbook RAG)

| Concept | Textbook Source | Correct? | Notes |
|---------|----------------|----------|-------|
| Вид дієслова: доконаний і недоконаний | Grade 7 Літвінова §7 (p.30-31); Grade 7 Заболотний; Grade 10 Караман §72 | YES | "Діє слова доконаного виду позначають завершену, обмежену в часі дію" — matches plan exactly |
| Imperfective = process/repetition | Grade 7 Літвінова §7 | YES | "Діє слова недоконаного виду позначають незавершену, не обмежену в часі дію" |
| Perfective has no present tense | Grade 7 Літвінова §7; Grade 10 Караман §72 | YES | "Дієслова доконаного виду не мають форми теперішнього часу" — confirmed |
| Signal words: завжди, часто, зазвичай, довго, щодня | Standard textbook approach | YES | These are standard frequency/duration markers for imperfective |
| Signal words: раптом, нарешті | Standard textbook approach | YES | Appropriate perfective markers |
| Aspect pair questions: що робити? / що зробити? | Grade 7 Літвінова; Grade 10 Караман | YES | The canonical test for aspect in Ukrainian grammar |

## Vocabulary Verification

| Word | VESUM | Frequency (IPM) | Issues |
|------|-------|-----------------|--------|
| вид | OK | — | Also means "view" — plan should clarify as metalinguistic term |
| дієслово | OK | — | — |
| недоконаний | OK | — | — |
| доконаний | OK | — | — |
| процес | OK | — | — |
| результат | OK | — | — |
| дія | OK | — | — |
| повторення | OK | — | — |
| робити | OK | — | — |
| зробити | OK | — | — |
| завершений | OK | — | — |
| тривалий | OK | — | — |
| одноразовий | OK | — | — |
| концепція | OK | — | Exists in Ukrainian (not a Russicism — confirmed via R2U: концепція is the standard Ukrainian form) |

All 14 vocabulary items verified in VESUM. No ghost words, no Russianisms.

## Issues Found

### CRITICAL (must fix before build)

1. **Missing required fields: `persona`, `grammar`, `register`** — Same structural gap as a2-bridge.

### HIGH (should fix before build)

1. **Section 4 is severely underbudgeted at 200 words** — "Порівняння пар" at 200 words is 10% of total budget. For the most important pedagogical section (where learners actually see the difference in action), this is dangerously thin. Side-by-side comparisons with visual aids need space. Recommend redistributing to at least 300 words (take 100 from section 2 or 3).

2. **Missing `prerequisites` field** — Should list `a2-bridge` as prerequisite.

3. **Football dialogue may not resonate with all learners** — The dialogue scenario (watching a football match) is culturally specific and may not engage all teen/adult learners. While culturally valid (football is huge in Ukraine), consider offering an alternative scenario in the plan or ensuring the built content doesn't rely exclusively on football knowledge. The verb examples are good (біжить/забив, грають/передала), but the setting could alienate non-sports learners.

### MEDIUM (fix if possible)

1. **Movie analogy may be culturally thin** — "Imperfective is like watching a movie; perfective is like seeing the 'The End' screen" is a reasonable analogy but somewhat surface-level. Ukrainian textbooks (Grade 7 Літвінова) use the more concrete approach of contrasting "Я розв'язував задачу..." vs "Я розв'язав задачу!" with illustrations. Consider incorporating this textbook-grounded approach into the plan.

2. **'вчора' listed as perfective signal word** — вчора (yesterday) is not exclusively perfective. "Вчора я читав книгу" (impf) is perfectly natural. The plan qualifies it as "for a single event" but this could mislead. Better to drop вчора from the signal words list or explicitly contrast: "Вчора я читав" (impf, process) vs "Вчора я прочитав" (pf, completed).

3. **Content_outline section titles** — Sections 2 and 3 use "Недоконаний вид:" and "Доконаний вид:" with subtitles. The subtitles in English (Process & Repetition, The Result!) are good for A2 learners but the Ukrainian section names use colons which need proper YAML quoting (they are quoted, so technically OK).

### LOW (informational)

1. **Aspect is taught in Grade 7 in Ukrainian schools** — Plan references Заболотний Grade 6 §52-54 and ULP. The richest textbook source is actually Grade 7 Літвінова §7 and Grade 10 Караман §72. Consider adding these references.

2. **No visual aids mentioned in plan** — Section 4 mentions "Visual aids: timelines showing the duration..." but the plan has no explicit guidance for the builder on how to represent these. Consider adding an activity hint for a timeline-based exercise.

## Suggested Fixes

```yaml
# Add missing required fields:
persona: "A2 learner encountering aspect for the first time — needs clear conceptual grounding"
grammar: [aspect, perfective, imperfective, past_tense]
register: informal

# Add prerequisites:
prerequisites: [a2-bridge]

# Redistribute word budget for section 4:
# OLD: section 4 words: 200
# NEW: section 4 words: 300
# Reduce section 2 from 700 to 600

# Add references:
references:
  - title: Заболотний Grade 6, §52-54
    notes: 'Вид дієслова: доконаний і недоконаний'
  - title: 'ULP: Ukrainian Verb Aspect'
    url: https://www.ukrainianlessons.com/ukrainian-verb-aspect/
    notes: Imperfective vs perfective
  - title: Літвінова Grade 7, §7
    notes: 'Види дієслова — illustrations with розв''язував/розв''язав'
  - title: Караман Grade 10, §72
    notes: 'Види дієслів — formation patterns, двовидові дієслова'

# Fix signal words — remove вчора from perfective-only list:
# OLD: 'Key signal words: вчора (yesterday, for a single event), раптом (suddenly), нарешті (finally).'
# NEW: 'Key signal words: раптом (suddenly), нарешті (finally), вже (already). Note: вчора (yesterday) works with BOTH aspects — Вчора я читав (impf) vs Вчора я прочитав (pf).'
```
