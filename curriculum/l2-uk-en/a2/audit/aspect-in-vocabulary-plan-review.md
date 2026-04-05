# Plan Review: aspect-in-vocabulary

**Track:** a2 | **Sequence:** 3 | **Version:** 1.0
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
| Aspect pair formation | YES | A2 §4.3.2 | A2 M03 | PASS |
| Prefixation for perfective | YES | A2 §4.3.2 | A2 M03 | PASS |
| Suffix changes for imperfectivization | YES | A2 §4.3.2 | A2 M03 | PASS |
| Suppletive pairs | YES | A2 §4.3.2 | A2 M03 | PASS |

**Notes:** Aspect pair formation is explicitly listed in A2 State Standard under Word Formation §4.3.2. Perfectly scoped.

## Grammar Verification (Textbook RAG)

| Concept | Textbook Source | Correct? | Notes |
|---------|----------------|----------|-------|
| Aspectual pair formation patterns | Grade 7 Літвінова §7 (p.34); Grade 10 Караман §72 (p.181) | YES | Textbooks list 5 methods: prefixes, suffixes, sound alternation, stress change, different stem. Plan covers 3 of these. |
| Prefixation: писати/написати, читати/прочитати | Grade 7 Літвінова (p.34); Grade 10 Караман | YES | Canonical examples confirmed |
| Suffix/root change: відповідати/відповісти | Grade 10 Караман | YES | Confirmed |
| Suppletion: брати/взяти | Grade 7 Літвінова (p.34); Grade 10 Караман | YES | Confirmed as suppletive pair |
| Suppletion: говорити/сказати | Standard knowledge | YES | Classic suppletive pair |
| "Imperfectivization" with -ува-/-юва- | Grade 10 Караман | YES | допомогти/допомагати pattern confirmed |

**Important note on formation types:** Ukrainian textbooks (Літвінова, Караман) list **5** methods of aspect pair formation, not 3:
1. Prefixes (писати → написати)
2. Suffixes (стукати → стукнути)
3. Sound alternation (видирати → видерти)
4. Stress change (зси́пати → зсипа́ти)
5. Different stem/suppletion (брати → взяти)

The plan covers methods 1, 2 (partially — it focuses on -ува-/-юва- imperfectivization rather than the simpler -нути suffixation like стукати/стукнути), and 5. Methods 3 and 4 are missing entirely.

## Vocabulary Verification

| Word | VESUM | Frequency (IPM) | Issues |
|------|-------|-----------------|--------|
| пара | OK | — | — |
| префікс | OK | — | — |
| суфікс | OK | — | — |
| корінь | OK | — | — |
| читати | OK | — | — |
| прочитати | OK | — | — |
| писати | OK | — | — |
| написати | OK | — | — |
| брати | OK | — | VESUM also matches as genitive plural of "брат" (brother); plan context makes verb meaning clear |
| взяти | OK | — | — |
| говорити | OK | — | — |
| сказати | OK | — | — |
| утворювати | OK | — | — |
| словник | OK | — | — |
| запам'ятовувати | OK | — | — |
| базовий | OK | — | — |

All 16 vocabulary items verified. Additional verbs in content_outline also verified:
- ловити/зловити: both OK
- шукати/знайти: both OK
- відповідати/відповісти: both OK
- вирішувати/вирішити: both OK
- запитувати/запитати: both OK
- допомогти/допомагати: both OK

No ghost words, no Russianisms.

## Issues Found

### CRITICAL (must fix before build)

1. **Missing required fields: `persona`, `grammar`, `register`** — Same structural gap as previous plans.

### HIGH (should fix before build)

1. **ловити/зловити listed as suppletive — it's prefixal** — Section 3 (Suppletion) lists "ловити / зловити (to catch)" as a suppletive pair. This is WRONG. зловити = з- + ловити, which is standard prefixation (Method 1), not suppletion. Suppletive pairs are etymologically unrelated stems (брати/взяти, говорити/сказати). This error would teach learners an incorrect classification. The correct catch-related suppletive pair would be **ловити/піймати** (per Караман: "ловити — піймати").

2. **шукати/знайти classified as suppletive — debatable** — The plan lists шукати/знайти as suppletive. While these have different stems, they represent different semantic actions (search vs find), not a traditional aspect pair. Many Ukrainian grammarians would not consider these a vidova para at all — шукати is "to search" (process) and знайти is "to find" (result), but знайти is not the perfective of шукати. The perfective of шукати is пошукати or відшукати. This is a genuine pedagogical trap that would confuse learners.

3. **Missing `prerequisites` field** — Should list `aspect-concept` as prerequisite.

4. **Two match-up activities with different focuses** — Activity hints list two `match-up` types (one for "Fill in the Blanks" and one for "Sentence Translation"). The "Sentence Translation" activity contradicts the curriculum's core principle of thinking in Ukrainian, not translating. Replace with a context-based activity.

### MEDIUM (fix if possible)

1. **Missing 2 of 5 aspect formation types** — Plan covers prefixation, suffix/root change, and suppletion, but omits:
   - **Sound alternation** (видирати → видерти, скакати → скочити) — textbook-confirmed in Караман
   - **Stress change** (зси́пати → зсипа́ти, розрі́зати → розріза́ти) — textbook-confirmed in Літвінова
   
   For A2, covering 3 types is reasonable, but the plan should at minimum mention that these other patterns exist and will be encountered later. Otherwise learners will be confused when they see them.

2. **Section 2 "imperfectivization" is presented backwards** — The plan introduces aspect pair formation starting with "add a prefix to make perfective" (Section 2), then "imperfectivization" (Section 3). But Section 3's description says "a complex perfective verb gets an -ува-/-юва- suffix to become imperfective." This is the reverse direction (pf → impf), which is confusing when Section 2 went impf → pf. Textbooks (Літвінова) present all formation types together as bidirectional. Consider unifying the direction.

3. **"Using a dictionary" sub-point is vague** — Section 1, point 3 says "how to find aspectual pairs in online or paper dictionaries." This is good pedagogically but needs concrete guidance (e.g., "In Ukrainian dictionaries, look for нв/дв markers" or "Online: slovnyk.ua shows both forms").

4. **Dialogue situation (cooking varenyky) is excellent** — Kudos. Natural, culturally grounded, textbook-aligned (Grade 7 Авраменко has a varenyky passage). The imperative pairs ліпи/зліпи, вари/звари naturally demonstrate aspect in commands.

### LOW (informational)

1. **References duplicate aspect-concept** — Both M02 and M03 reference the same Заболотний Grade 6 §52-54 and ULP link. Add Grade 7 Літвінова §7 (p.34) which has the most detailed formation type table and Grade 10 Караман §72 which lists all 5 methods.

2. **Title "Дієслова ходять парами" is engaging** — Good title that humanizes the concept.

## Suggested Fixes

```yaml
# Add missing required fields:
persona: "A2 learner who understands aspect concept — now learning to form pairs"
grammar: [aspect_pairs, prefixation, suffixation, suppletion]
register: informal

# Add prerequisites:
prerequisites: [aspect-concept]

# FIX CRITICAL: Replace wrong suppletive pairs (Section 3):
# OLD:
  - 'Essential pairs: брати / взяти (to take); говорити / сказати (to say/tell);
      ловити / зловити (to catch); шукати / знайти (to look for / to find).'
# NEW:
  - 'Essential pairs: брати / взяти (to take); говорити / сказати (to say/tell);
      ловити / піймати (to catch); класти / покласти (to put).'
  - 'Note: шукати (to search) and знайти (to find) are often presented together,
      but they are different actions, not a true aspect pair. The perfective of
      шукати is пошукати or відшукати.'

# Fix activity hint — replace translation activity:
# OLD:
  - type: match-up
    focus: Sentence Translation (Aspect Focus)
    items: 8
# NEW:
  - type: fill-in
    focus: Choose the Correct Aspect Partner
    items: 8

# Add references:
  - title: Літвінова Grade 7, §7
    notes: 'Видові пари — 5 formation methods with examples'
  - title: Караман Grade 10, §72
    notes: 'Видові пари — comprehensive formation table'
```
