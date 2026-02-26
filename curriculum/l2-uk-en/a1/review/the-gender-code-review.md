<!-- content-hash: 75b36c9fdb0c -->
**Reviewed-By:** claude-opus-4-6

## Scores

| Dimension | Score | Evidence Summary |
|-----------|-------|------------------|
| **Language (Ukrainian)** | 9 | All Ukrainian examples grammatically correct, no Russianisms, no colonial framing. Minor: "doubled consonant" explanation for укриття/Запоріжжя is a workable simplification but linguistically imprecise. |
| **Language (English)** | 9 | Warm, clear, B1-readable English throughout. Encouraging tutor voice consistently maintained. A few dense sentences in section «Практика: Чотири сім'ї та винятки» could be simpler. |
| **Factual Accuracy** | 8 | Proverb «Рідна земля — мати, чужа — мачуха» is authentic. Gender rules accurately presented. Собака treatment is defensible but the optional feminine nuance (line 165) adds confusing optionality for A1. The "doubled consonant = neuter" heuristic (lines 285, 295) oversimplifies the suffix -тт(я) mechanism. |
| **Lesson Quality** | 9 | Strong arc: WELCOME → PREVIEW → PRESENT → PRACTICE → CELEBRATE. Warm opening, clear objectives (line 15-19), encouraging close. Section «Практика: Чотири сім'ї та винятки» packs 4 declension families + 4 exceptions with limited practice breaks between them — slightly dense for A1.1 fragile learners. 4/5 on "Would I Continue?" test. |
| **Immersion** | 9 | 12.6% within 10-25% target. Appropriate for A1.1 First Contact — heavy English scaffolding with Ukrainian introduced through key terms, examples, and engagement cues (Привіт!, Розглянемо!, Готові?, Чудово!, Молодець!). |
| **Activity Quality** | 7 | 9 activities, 6 types. But "Пастки та винятки" quiz has 7/12 items using "Спільний" as 4th distractor — monotonous and auto-generated feel. Same quiz's last 7 items (мама, чоловік, жінка, брат, сестра, дім, серце) are regular nouns, not "traps/exceptions" as the title promises. Two group-sort activities near-duplicate each other. |
| **Richness** | 8 | S.T.A.L.K.E.R. cultural hook is excellent, folk proverb is authentic, city name examples (Київ/Одеса/Запоріжжя) are clever. Missing the plan-specified adjective collocations (великий стіл, цікава книга, чисте вікно). Mini-dialogue well-executed. |
| **LLM Fingerprint** | 8 | Section openings varied (6 different opening patterns). No generic AI rhetoric. Three [!context] "Usage Note" boxes share identical structure but pedagogically justified. The "Пастки та винятки" quiz's last 7 items with identical 4-option template (3 genders + "Спільний") reads as auto-generated filler. |
| **Humanity / Warmth** | 9 | Direct address throughout (>15 instances). Encouragement: "Молодець!", "Чудово!", "you're reading the code like a pro!" (line 189). Reassurance: «The goal at this stage is not perfection but pattern recognition» (line 299). Progress celebration at close. |

---

## Critical Issues Found

### Issue 1: Quiz "Пастки та винятки" — Distractor Monotony and Misleading Title (Activity file, lines 494-630)

**Severity: Moderate**

The quiz "Пастки та винятки" (Traps and Exceptions) has two problems:

1. **Distractor monotony**: Items 6-12 (questions about мама, чоловік, жінка, брат, сестра, дім, серце) ALL use "Спільний" as the 4th distractor option. That is 7 consecutive items with identical distractor structure (Чоловічий/Жіночий/Середній + Спільний). Learners will quickly learn to ignore the 4th option, reducing the quiz to a trivial 3-choice test.

2. **Title mismatch**: The title promises «Пастки та винятки» but only the first 5 items (собака, ім'я, ніч, день, тато) are genuine exceptions. The remaining 7 (мама, чоловік, жінка, брат, сестра, дім, серце) are completely regular nouns with predictable genders — no traps involved.

**Fix**: Replace items 6-12 with genuinely tricky items (e.g., любов, радість, кімната, хліб, дядько) and vary the 4th distractor across items.

### Issue 2: Duplicate Group-Sort Activities (Activity file, lines 1-28 and 371-392)

**Severity: Minor**

Activity 1 «Сортування за родом» asks learners to sort words by gender (Він/Вона/Воно). Activity 7 «Сортування за закінченням» asks learners to sort words by ending (-consonant / -а/-я / -о/-е). For regular nouns, these are the same cognitive operation — knowing the ending IS knowing the gender. The activities use largely overlapping word sets with nearly identical answers.

**Fix**: Replace the second group-sort with a different activity type that tests a distinct skill — e.g., a sentence-completion activity where learners identify gender from context, or a "find the exception" exercise.

### Issue 3: Potentially Confusing Собака Nuance for A1 (Content file, lines 163-167)

**Severity: Minor**

The content states: «**собака** is **Masculine** by default in standard Ukrainian» (line 163), then immediately adds: «**моя собака** — Also acceptable when specifically referring to a female dog» (line 165). For A1.1 learners who are just learning that gender exists, presenting an "exception to the exception" creates unnecessary cognitive load. The learner has just been told the ending -а usually means feminine, then told собака is masculine despite -а, then told "but also feminine sometimes." This three-step reversal is likely to confuse rather than clarify.

**Fix**: Remove line 165 entirely. At A1, teach собака as masculine, period. The feminine usage nuance can be introduced at A2 or later.

### Issue 4: Missing Vocabulary IPA Stress Mark (Vocabulary file, line 121-122)

**Severity: Minor**

The vocabulary entry for зона shows IPA as `[zɔnɑ]` without a stress mark. For a disyllabic word, the stress mark is necessary: should be ``. All other polysyllabic entries (мама, тато, сестра, etc.) correctly include stress marks.

**Fix**: Change `[zɔnɑ]` to `` in vocabulary file.

### Issue 5: Plan-Specified Adjective Collocations Missing from Section «Презентація: Три кити роду» (Content file, lines 58-140)

**Severity: Minor**

The plan (plan file, line 27-29) specifies: "Syntactic Agreement: How gender dictates the form of adjectives and pronouns — examples with 'великий стіл' (M), 'цікава книга' (F), and 'чисте вікно' (N)." None of these three collocations appear in the content. The content uses other adjective-noun pairs in later sections (добрий день, велике місто, тиха ніч, рідна земля, добре серце) but the Презентація section focuses exclusively on мій/моя/моє agreement, omitting the adjective agreement dimension.

**Fix**: Add one brief paragraph or callout in section «Презентація: Три кити роду» demonstrating adjective agreement with the plan-specified examples — even a simple table showing «великий стіл» / «цікава книга» / «чисте вікно» would satisfy the plan's intent.

---

## Factual Verification

### Grammar Rules Verified

| Rule | Status | Notes |
|------|--------|-------|
| Masculine = consonant ending | ✓ Correct | Standard rule, accurately presented |
| Feminine = -а/-я ending | ✓ Correct | With appropriate "90%" qualifier (line 89) |
| Neuter = -о/-е ending | ✓ Correct | Standard rule |
| тато = Masculine despite -о | ✓ Correct | Natural gender override, well-explained |
| собака = Masculine default | ✓ Defensible | Standard dictionaries list as masculine; the added feminine option creates unnecessary confusion |
| ім'я = Neuter (Family 4) | ✓ Correct | Properly explained as ancient neuter form |
| день = Masculine (soft sign) | ✓ Correct | |
| ніч = Feminine (consonant) | ✓ Correct | Family 3 exception, well-flagged |
| Запоріжжя = Neuter | ✓ Correct | Geographic name, neuter gender |

### Callout Box Verification

| Callout | Claim | Status |
|---------|-------|--------|
| Cultural Hook (line 35-37) | Sun is neuter in Ukrainian, masculine in French/Spanish, feminine in German | ✓ Correct (le soleil M, el sol M, die Sonne F, сонце N) |
| Proverb (line 297) | «Рідна земля — мати, чужа — мачуха» | ✓ Authentic Ukrainian proverb |
| S.T.A.L.K.E.R. (lines 281-286) | Артефакт (M), Зона (F), Укриття (N) | ✓ Correct genders; game is Ukrainian-made |
| [!myth-buster] (lines 217-219) | ім'я commonly confused with feminine | ✓ Pedagogically sound, common learner error |
| [!warning] (lines 183-186) | Don't say "моє тато" | ✓ Correct guidance |

### Colonial Framing Check
No Russian comparisons found. References are to French, Spanish, German, and English — legitimate cross-linguistic comparison. **Clean pass.**

---

## Verification Summary

| Check | Result |
|-------|--------|
| All H2 sections from plan present | ✓ All 6 sections present and match meta outline |
| Vocabulary scope matches plan | ✓ All 8 required + 12 recommended items present |
| Grammar scope — no creep | ✓ Stays within gender identification, мій/моя/моє, declension family overview |
| Learning objectives addressed | ✓ All 4 objectives from line 16-19 covered |
| Colonial framing | ✓ Clean — no Russian comparisons |
| Russianisms | ✓ None detected |
| LLM fingerprints | Minor — activity distractor monotony; content prose is clean |
| Activity correctness | ✓ All answers verified correct across 9 activities |
| IPA accuracy | 1 issue: зона missing stress mark |
| "Would I Continue?" test | 4/5 — Practice section slightly dense |

**Sections referenced**: Section «Вступ: Таємний код української мови» — strong warm opening with cultural hook. Section «Презентація: Три кити роду» — clear rule presentation with good visual table, but missing plan-specified adjective collocations. Section «Практика: Чотири сім'ї та винятки» — comprehensive exception coverage but dense pacing. Section «Продукція: Колір і форма» — effective "Gender Algorithm" and mini-dialogue. Section «Культурний контекст: Жива мова» — excellent S.T.A.L.K.E.R. hook and authentic proverb. Section «Підсумок» — warm close with progress celebration and self-check questions.

---

## Verdict

**PASS WITH FIXES**

This is a solid A1.1 module with warm pedagogy, accurate grammar, and engaging cultural hooks. The content prose is well-written, the emotional arc is appropriate for fragile beginners, and the lesson structure follows PPP faithfully.

The main weakness is in activity quality: the "Пастки та винятки" quiz has monotonous distractors (7/12 items use "Спільний") and misleading title (regular nouns presented as "exceptions"), and the two group-sort activities near-duplicate each other. These should be fixed before the module ships.

**Required fixes (3):**
1. Diversify distractors and replace regular items in "Пастки та винятки" quiz
2. Replace second group-sort with a distinct activity type
3. Fix зона IPA stress mark: `[zɔnɑ]` → ``

**Recommended fixes (2):**
4. Remove собака feminine usage option (line 165) — simplify for A1
5. Add plan-specified adjective collocations to section «Презентація: Три кити роду»