# Plan Review: a2-bridge

**Track:** a2 | **Sequence:** 1 | **Version:** 1.1
**Verdict:** NEEDS FIXES

## Rule Compliance

| Check | Status | Details |
|-------|--------|---------|
| word_target | PASS | Plan: 2000, Config: 2000 |
| section_budgets | PASS | Sum = 2000 vs target 2000 (0%) |
| required_fields | FAIL | Missing: `persona`, `grammar`, `register` |
| version_string | PASS | `'1.1'` is a string |

## State Standard Alignment

| Grammar Topic | In Standard? | Standard Level | Plan Level | Status |
|--------------|-------------|----------------|------------|--------|
| Nominative/Accusative/Locative/Vocative review | YES | A1 (review) | A2 M01 | PASS |
| Vowel alternations о/і, е/і | YES | A1 §4.1.4 + A2 §4.1.1 | A2 M01 | PASS |
| Consonant alternations г/ж, к/ч, х/ш | YES | A1 §4.1.4 + A2 §4.1.1 | A2 M01 | PASS |
| Euphony у/в, і/й, з/зі/із | YES | A1 §4.1.7 + A2 §4.1.3 | A2 M01 | PASS |
| Stress patterns / mobile stress | YES | A2 §4.1.2 | A2 M01 | PASS |
| Consonant assimilation (voicing) | YES | A2 §4.1.1 | A2 M01 | PASS |
| дж/дз as affricates | YES | A1 §4.1.4 (phonetics) | A2 M01 | PASS |
| Genitive/Dative/Instrumental preview | YES | A2 cases | A2 M01 | PASS — roadmap only, not teaching |

**Notes:** All grammar topics are appropriate for an A2 bridge/review module. The phonology section is ambitious for a 2000-word module but topically correct.

## Grammar Verification (Textbook RAG)

| Concept | Textbook Source | Correct? | Notes |
|---------|----------------|----------|-------|
| Vowel alternation о/і in closed syllables | Grade 10 Глазова §25; Grade 5 Авраменко §50 | YES | стіл/стола, Київ/Києва confirmed |
| Consonant alternation г/з/ж, к/ц/ч, х/с/ш | Grade 5 Авраменко §50 | YES | нога/на нозі/ніжка confirmed |
| First palatalization label | Grade 5 Авраменко §50 | IMPRECISE | Plan calls it "first palatalization" — textbooks just say "чергування приголосних" without numbering. The term "first palatalization" is a historical linguistics concept (Proto-Slavic), not how Grade 5-7 textbooks present it. |
| Euphony у/в, і/й | Grade 10 Глазова §15; Grade 5 Літвінова; Grade 10 Авраменко §23 | YES | Rules confirmed across multiple textbooks |
| з/зі/із alternation | Grade 5 Літвінова (p.177) | YES | Rules and conditions confirmed |
| Voicing assimilation: просьба → [проз'ба] | Grade 5 Голуб (p.75); Grade 10 Заболотний (p.78) | YES | Confirmed: глухий перед дзвінким → парний дзвінкий |
| Voicing assimilation: боротьба → [бород'ба] | Grade 10 Заболотний (p.78) | PARTIALLY | Textbook writes [бородба], plan writes [бород'ба]. The softness mark placement differs. |
| Voicing assimilation: вокзал → [воґзал] | Grade 10 Заболотний (p.78) | YES | Confirmed |
| дж/дз as affricates | Grade 2 Вашуленко; Grade 1-2 Кравцова | YES | Confirmed as single sounds |
| Mobile stress: вода́/во́ду | Standard knowledge | YES | Classic examples of mobile stress |

## Vocabulary Verification

| Word | VESUM | Frequency (IPM) | Issues |
|------|-------|-----------------|--------|
| відмінок | OK | — | — |
| називний | OK | — | — |
| знахідний | OK | — | — |
| місцевий | OK | — | — |
| кличний | OK | — | — |
| чергування | OK | — | — |
| голосний | OK | — | — |
| приголосний | OK | — | — |
| наголос | OK | — | — |
| милозвучність | OK | — | — |
| огляд | OK | — | — |
| система | OK | — | — |
| правило | OK | — | — |

All 13 vocabulary items verified in VESUM. No ghost words, no Russianisms.

## Issues Found

### CRITICAL (must fix before build)

1. **Missing required fields: `persona`, `grammar`, `register`** — The plan lacks `persona` (who is the learner in this module?), `grammar` (explicit grammar tags for pipeline matching), and `register` (formal/informal). These are required by the plan schema.

2. **Phonology section is overloaded for 700 words** — Section 2 "Магія української фонології" packs 5 dense points into 700 words: vowel alternations, consonant alternations, stress patterns, consonant assimilation (дж/дз affricates + voicing), and mobile stress paradigms. That's ~140 words per complex phonological concept. At A2.1, learners need clear explanations with examples. This will inevitably result in either (a) rushed, shallow treatment or (b) exceeding the word budget. The section should either be split or scope reduced.

### HIGH (should fix before build)

1. **"First palatalization" terminology** — The plan uses the term "first palatalization (г/ж, к/ч, х/ш)" which is a historical linguistics concept. Ukrainian school textbooks (Grade 5 Авраменко, Заболотний) simply call this "чергування приголосних звуків" without the Slavic linguistics numbering. For A2 learners, "consonant alternation" is clearer. Using "first palatalization" risks confusing the target audience and introducing unnecessary metalanguage.

2. **Consonant assimilation is Grade 10 material** — Voicing assimilation (просьба → [проз'ба], боротьба → [бород'ба]) appears in Grade 10 textbooks (Глазова, Заболотний, Караман) and Grade 5 (Голуб, Літвінова) as part of advanced phonetics. While it fits A2 State Standard §4.1.1 ("expanded phonetics — consonant assimilation"), presenting it alongside дж/дз affricates AND mobile stress in the same section is scope creep for a bridge module. Consider deferring assimilation to a later A2 phonology module.

3. **Missing `prerequisites` field** — As the first A2 module, this should explicitly list A1 completion as a prerequisite (e.g., `prerequisites: [a1-finale]`).

4. **Activity hint formatting error** — Line 97 has a bare `- error-correction` without proper `type:` key. Should be `- type: error-correction`.

### MEDIUM (fix if possible)

1. **Dialogue situation uses Genitive example before it's taught** — The dialogue setting mentions "Я з Канади (genitive)" but Genitive is not yet introduced at this point. While the dialogue says "reviewing what you know," the Genitive case is an A2 topic, not A1. The dialogue should only showcase A1 cases (Nominative, Accusative, Locative, Vocative) and possibly hint at new ones without requiring learners to produce them.

2. **Section 4 is very thin at 300 words** — "What awaits us in A2?" at 300 words may feel like an afterthought. Consider expanding the roadmap section to 400 words by redistributing from section 2.

3. **Transcription inconsistency** — Plan writes `[бород'ба]` but textbooks write `[бородба]` (without explicit softness mark). Minor but should match textbook conventions.

### LOW (informational)

1. **Title is entirely in Ukrainian** — "Ласкаво просимо до рівня А2" is all-Ukrainian, which is great for immersion, but for a bridge module where learners are still at A1-exit, an English subtitle with Ukrainian is more aligned with the A2 M01-20 immersion target (45-65%).

2. **No references to Большакова or Вашуленко** — For a phonology-heavy module, Grade 1-2 textbooks provide excellent foundational approaches to Ukrainian sounds. The current reference (Заболотний Grade 5) is appropriate but could be supplemented.

## Suggested Fixes

```yaml
# Add missing required fields after 'phase:' line:
persona: "A1 graduate arriving at A2 — eager but needs review and confidence boost"
grammar: [nominative, accusative, locative, vocative, vowel_alternation, consonant_alternation, euphony, stress]
register: informal

# Fix activity hint formatting (line 97):
# OLD:
  - error-correction
# NEW:
  - type: error-correction
    focus: Euphony Error Correction
    items: 6

# Fix dialogue to use only A1 cases:
# OLD:
  - setting: 'Arrival at a Kyiv language school on the first day of A2 — reviewing
      what you know: Я з Канади (genitive)...'
# NEW:
  - setting: 'Arrival at a Kyiv language school on the first day of A2 — reviewing
      what you know: Я — студент (nominative). Я вивчаю українську мову
      (accusative). Я живу в Києві (locative). Привіт, Оксано! (vocative).'

# Add prerequisites:
prerequisites: [a1-finale]
```
