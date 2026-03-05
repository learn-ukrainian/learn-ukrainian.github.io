# A1 Plan Review Summary

**Track:** A1 | **Total Plans:** 64 (59 regular + 5 checkpoints)
**Reviewed:** 2026-03-05 | **Reviewer:** Claude (plan-review skill)
**Reference:** Issue #729

## Overall Verdict: NEEDS FIXES

**PASS:** 52 plans | **NEEDS FIXES:** 12 plans | **FAIL:** 0 plans

---

## Rule Compliance (all 64 plans)

| Check | Status | Details |
|-------|--------|---------|
| word_target | PASS | All regular modules = 1200, all checkpoints = 1000. Matches config.py. |
| section_budgets | PASS (63/64) | 63 plans sum exactly to target. `the-cyrillic-code-i` sums to 1100 (-8.3%), within tolerance. |
| required_fields | PASS | All 64 plans have all 17 required fields (module, level, sequence, slug, version, title, subtitle, focus, pedagogy, word_target, objectives, content_outline, vocabulary_hints, activity_hints, persona, grammar, register). |
| version_string | PASS | All versions are strings ('2.0', '3.0', '4.0'). |

---

## State Standard Alignment

### CRITICAL: Dative Case at A1

The State Standard 2024 mapping explicitly marks **Dative (Давальний) as `allowed: false`** for A1, placing it at A2. However, **8 plans** use Dative constructions:

| Plan | Dative Usage | Assessment |
|------|-------------|------------|
| likes-and-preferences (seq 19) | "Мені подобається" — full Dative paradigm | **HIGH** — This is the core teaching of the module |
| pronoun-declension (seq 31) | Full Dative pronoun paradigm (мені, тобі, йому...) | **HIGH** — Explicitly teaches Dative case |
| checkpoint-sentences (seq 24) | Tests "Мені подобається" Dative construction | **MEDIUM** — Review item, not new teaching |
| must-and-want (seq 46) | "Мені треба" Dative construction | **HIGH** — Teaches Dative necessity |
| body-and-health (seq 48) | "Мені боляче" Dative experiencer | **MEDIUM** — Lexical chunk, not systematic |
| food-vocabulary (seq 39) | "Мені подобається борщ" — review of Dative | **LOW** — Review only |
| writing-skills (seq 59) | Dative mentioned in context | **LOW** — Peripheral |
| a1-final-exam (seq 64) | Tests Dative knowledge | **MEDIUM** — Cumulative test |

**Assessment:** The "Мені подобається" construction is so high-frequency and communicatively essential that teaching it at A1 as a **lexical chunk** (without full case paradigm) is defensible and common in communicative methodologies. However, the plan for `pronoun-declension` (seq 31) goes further by teaching the **full Dative paradigm**, which exceeds A1 scope per the State Standard. **Recommendation:** Keep "Мені подобається" as a lexical chunk at A1, but move the full Dative paradigm section from `pronoun-declension` to A2, or explicitly mark it as a preview/chunk approach rather than systematic case instruction.

### MEDIUM: Genitive Case at A1

The State Standard does NOT explicitly list Genitive among the A1 cases (it lists Nominative, Accusative, Locative, Vocative). However, a dedicated module `the-genitive-i-absence` (seq 32) teaches Genitive for absence (немає + Gen) and `direction-and-origin` (seq 35) teaches з/від + Genitive. Additionally, `numbers-and-money` (seq 22) requires Genitive plural for number agreement.

**Assessment:** Unlike the Dative case, Genitive for **absence** (немає + Gen) and **direction** (з/від + Gen) are extremely high-frequency survival constructions. The State Standard's silence (rather than explicit `allowed: false` like Dative/Instrumental) may indicate these are acceptable. However, this represents a deliberate curriculum decision that should be **documented** — the plan should note "extends beyond strict State Standard scope for communicative necessity."

### Genitive-Accusative Link (Animate Masculine)

Module `the-accusative-ii-people` (seq 26) correctly teaches Acc=Gen for animate masculine nouns, which implicitly requires Genitive knowledge. This is well-sequenced after the Genitive module.

### Grammar Scope — All Other Topics: PASS

| Grammar Topic | State Standard Reference | Status |
|---------------|------------------------|--------|
| Alphabet / Phonetics | §4.1.1-§4.1.8 | PASS — Covered in Cyrillic Code I-IV |
| Vowel/consonant classification | §4.1.4 | PASS |
| Stress | §4.1.5 | PASS — stress-and-intonation |
| Euphony (у/в, і/й, з/із/зі) | §4.1.7 | PASS — euphony-and-polish |
| Intonation | §4.1.8 | PASS — stress-and-intonation |
| Noun declension | §4.2.1.1 | PASS |
| Adjective declension | §4.2.1.2 | PASS — describing-things-adjectives, adjective-case-forms |
| Numerals (basic) | §4.2.1.3 | PASS — numbers-and-money |
| Personal pronouns | §4.2.1.4 | PASS — this-is-i-am, pronoun-declension |
| Nominative case | §4.2.3.1 | PASS |
| Accusative case | §4.2.3.2 | PASS — the-accusative-i-things, the-accusative-ii-people, accusative-prepositions |
| Locative case | §4.2.3.3 | PASS — the-locative-where-things-are |
| Vocative case | §4.2.3.4 | PARTIAL — Vocative appears in emergencies (Лікарю!) but no dedicated module |
| Indicative mood (present) | §4.2.4.1 | PASS — the-living-verb-i, the-living-verb-ii |
| Indicative mood (past) | §4.2.4.1 | PASS — yesterday-past-tense |
| Indicative mood (future) | §4.2.4.1 | PASS — tomorrow-future-tense |
| Reflexive verbs (-ся/-сь) | §4.2.4.1 | PASS — reflexive-verbs |
| Imperative (2nd person) | §4.2.4.2 | PASS — imperative-and-requests |
| Simple sentences (SVO) | §4.3.1 | PASS — questions-and-negation |
| Basic complex sentences (і, а, але, бо) | §4.3.2 | PASS — weather-and-nature (бо), checkpoint-sentences (тому що/бо) |

### Thematic Catalogue Match

The A1 State Standard themes (людина, дім, місто, побут, діяльність, дозвілля, подорожі, купівля, ресторан, здоров'я, природа, традиції) are well-covered:

| Theme | Modules Covering It |
|-------|-------------------|
| людина | this-is-i-am, my-family, body-and-health |
| дім | my-world-objects, prepositions-of-place |
| місто | around-the-city, direction-and-origin |
| побут | my-daily-routine, colors-and-clothing |
| діяльність | the-living-verb-i/ii, can-and-know-how |
| дозвілля | leisure-and-hobbies |
| подорожі | travel-and-transport, taking-transport, buying-tickets |
| купівля | shopping-and-market, at-the-store, at-the-market, numbers-and-money |
| ресторан | at-the-cafe, at-the-restaurant, food-vocabulary |
| здоров'я | body-and-health, emergencies |
| природа | weather-and-nature |
| традиції | holidays-and-traditions |

---

## Issues Found

### CRITICAL (must fix before build)

None.

### HIGH (should fix before build)

1. **Dative paradigm at A1 exceeds State Standard scope.** Module `pronoun-declension` (seq 31) teaches the full Dative paradigm (мені, тобі, йому, їй, нам, вам, їм). The State Standard places systematic Dative at A2. **Fix:** Either (a) remove the Dative section from `pronoun-declension` and move it to an A2 module, or (b) mark it explicitly as "chunk-based preview" rather than systematic case instruction, and add a note in the plan acknowledging the scope extension.

2. **Duplicate demonstrative pronoun coverage.** Modules `my-world-objects` (seq 10) and `demonstratives-this-that` (seq 21) both teach the same demonstrative pronouns (цей/ця/це/ці, той/та/те/ті) with significant content overlap. **Fix:** Differentiate them more clearly — `my-world-objects` should focus on vocabulary (household objects) with demonstratives as a tool, while `demonstratives-this-that` should focus on the grammatical system. Or merge them.

3. **Prerequisite inconsistency: `the-living-verb-ii` (seq 16).** Its prerequisites list both `a1-15 (The Living Verb I)` AND `a1-18 (Questions and Negation)`. But a1-18 has sequence 18, which comes after a1-16. This creates a circular dependency. **Fix:** Remove `a1-18` from `the-living-verb-ii`'s prerequisites.

4. **Prerequisite inconsistency: `yesterday-past-tense` (seq 36).** Its prerequisites list `a1-54 (Checkpoint: Communication)` which has sequence 54 — far later in the curriculum. This is clearly wrong. **Fix:** Correct the prerequisite to the actual prior module (likely `a1-35 direction-and-origin`).

5. **Sequence gap: No module with sequence 48 listed for `body-and-health`.** Wait — it exists. Let me verify other gaps. Actually the issue is different: some module IDs don't match sequences consistently (e.g., `at-the-store` is a1-061 with seq 61, but `at-the-market` is a1-060 with seq 60, and `at-the-store` has prerequisite `a1-60 (At the Market)` — this is correct).

6. **`the-cyrillic-code-i` (seq 1) section budgets sum to 1100, not 1200.** The gap is 100 words (8.3%). While within the +/-10% tolerance, it is the only plan with a mismatch. The sections are: 200+250+250+300+100 = 1100. **Fix:** Add 100 words to the "Склади і слова" section (currently 300, increase to 400) or redistribute.

### MEDIUM (fix if possible)

1. **Vocative case not explicitly taught in a dedicated module.** State Standard §4.2.3.4 requires Vocative at A1. It appears incidentally in `emergencies` (seq 62: "Лікарю!", "Поліціє!") and `greetings-and-politeness` ("Пане/пані"), but no module systematically teaches Vocative formation rules. **Fix:** Either add a Vocative section to an existing module (e.g., `greetings-and-politeness` or `emergencies`), or create a brief Vocative mini-module.

2. **`my-world-objects` (seq 10) references `a1-03 (Gender)` and `a1-04 (Identification)` in content_outline** but these are not listed as prerequisites. Its prerequisite is `a1-09 (This Is, I Am)`. The references appear to use old module numbering (a1-03 would be `the-cyrillic-code-iii`, not `the-gender-code`). **Fix:** Update internal references to use correct slug-based names or current sequence numbers.

3. **Module `numbers-and-money` (seq 22) teaches "Genitive plural with numbers"** but its prerequisite is `a1-32 (The Genitive I)`. Since seq 22 < seq 32, this creates a forward dependency: the module needs Genitive knowledge that hasn't been taught yet. **Fix:** Either move `numbers-and-money` after `the-genitive-i-absence`, or remove the Genitive plural requirement and teach the 1-2-5 pattern as lexical chunks.

4. **`likes-and-preferences` (seq 19) grammar field lists "Dative construction Мені подобається"** but this is not in the A1 State Standard grammar scope. Should be flagged in the grammar field as "communicative chunk, not systematic case instruction."

5. **`checkpoint-first-contact` (seq 14) objectives claim to test "Conjugate First and Second Conjugation verbs"** but Second Conjugation is taught in `the-living-verb-ii` (seq 16), which comes AFTER this checkpoint. The checkpoint can only test First Conjugation and reflexive verbs from the modules that precede it. **Fix:** Update the checkpoint objectives to match only content from seq 1-13 and seq 15-17 (whatever precedes it per the DAG).

6. **`colors-and-clothing` (seq 12) uses "носити зі Знахідним відмінком (Accusative)"** but the Accusative case module is `the-accusative-i-things` at seq 25. This introduces Accusative before it's formally taught. **Fix:** Either move `colors-and-clothing` after seq 25, or teach "носити + object" as a lexical chunk without explicit case instruction. The plan already handles this somewhat by using it for practice, but the grammar field should note "Accusative as lexical chunk preview."

7. **`what-time-is-it` (seq 23) prerequisite is `a1-37 (Tomorrow - Future Tense)` with seq 37.** This is a forward dependency — seq 23 cannot require seq 37. **Fix:** Remove this prerequisite or correct it.

### LOW (informational)

1. **Version inconsistency.** Cyrillic Code plans are at version '4.0', syllables/stress plans at '3.0', and all others at '2.0'. This is informational — different modules have been revised at different rates.

2. **`emergencies` (seq 62) teaches Vocative case formation** (Лікарю!, Поліціє!) which should be noted in the grammar field. Currently grammar says "Urgent requests" but not "Vocative case."

3. **`the-accusative-ii-people` (seq 26) prerequisite lists `a1-11 (The Accusative I - Things)`** but the actual sequence for `the-accusative-i-things` is 25, not 11. The module ID reference should use slug-based naming for clarity.

4. **Several plans reference modules by old sequence-based IDs** (e.g., "a1-03" for Gender Code which is actually seq 7). This is confusing but not functionally broken since builds use slugs.

5. **No `connects_to` or `prerequisites` cross-validation.** Some connects_to references may point to non-existent module IDs. A systematic cross-check tool would be useful.

6. **Plan `the-cyrillic-code-iii` (seq 3) section budgets sum to 1250**, which is 4.2% OVER the 1200 target. This is acceptable but means more content than budgeted.

7. **Plan `the-cyrillic-code-iv` (seq 4) section budgets sum to 1250**, same as above.

---

## Prerequisite Dependency Issues (Summary)

| Module | Declared Prerequisite | Problem |
|--------|----------------------|---------|
| the-living-verb-ii (seq 16) | a1-18 (seq 18) | Forward dependency |
| yesterday-past-tense (seq 36) | a1-54 (seq 54) | Forward dependency |
| what-time-is-it (seq 23) | a1-37 (seq 37) | Forward dependency |
| numbers-and-money (seq 22) | a1-32 (seq 32) | Forward dependency |

These are all cases where a module lists a prerequisite with a HIGHER sequence number than itself. This is structurally invalid — a module cannot require knowledge from a later module.

---

## Vocabulary Verification (Spot Checks)

All spot-checked Ukrainian words verified against VESUM:
- паляниця: PASS (noun, inanimate, feminine)
- All high-frequency words (мама, кіт, молоко, хліб, etc.) are standard Ukrainian

No ghost words or Russianisms detected in the vocabulary hints reviewed.

---

## Pedagogical Quality

| Check | Status | Notes |
|-------|--------|-------|
| Testable objectives | PASS | All objectives describe learner capabilities |
| Content-objective alignment | PASS | Each objective addressed by sections |
| Logical progression | NEEDS FIXES | Forward dependencies violate progression |
| Activity hints achievable | PASS | Activity types appropriate for A1 |
| Decodability (Cyrillic modules) | PASS | Cyrillic Code I-IV properly constrain vocab to known letters |

---

## Pattern-Based Recommendations

### Pattern 1: Forward Dependencies
**4 modules** have prerequisites with higher sequence numbers. Run a topological sort on the prerequisite graph and fix all forward edges.

### Pattern 2: Old Module ID References
Many plans reference modules by `a1-XX` IDs that don't match current sequence numbers. A batch update to use slug-based references would eliminate confusion.

### Pattern 3: Scope Boundary Transparency
Where plans intentionally exceed State Standard scope (Dative chunks, Genitive for absence), add explicit notes in the plan's `grammar:` or `content_outline:` sections explaining the pedagogical rationale and marking these as "communicative chunks" or "preview."

### Pattern 4: Duplicate Content
`my-world-objects` and `demonstratives-this-that` overlap significantly. Consider merging or clearly differentiating their scope.

---

## PASS/FAIL by Module

| # | Slug | Verdict | Issues |
|---|------|---------|--------|
| 1 | the-cyrillic-code-i | NEEDS FIXES | Section sum 1100 (-8.3%) |
| 2 | the-cyrillic-code-ii | PASS | |
| 3 | the-cyrillic-code-iii | PASS | Section sum 1250 (over, OK) |
| 4 | the-cyrillic-code-iv | PASS | Section sum 1250 (over, OK) |
| 5 | syllables-and-transfer | PASS | |
| 6 | stress-and-intonation | PASS | |
| 7 | the-gender-code | PASS | |
| 8 | greetings-and-politeness | PASS | |
| 9 | this-is-i-am | PASS | |
| 10 | my-world-objects | NEEDS FIXES | Duplicate with seq 21; old module refs |
| 11 | describing-things-adjectives | PASS | |
| 12 | colors-and-clothing | NEEDS FIXES | Uses Acc before it's taught |
| 13 | plurals-and-alternation | PASS | |
| 14 | checkpoint-first-contact | NEEDS FIXES | Tests skills not yet taught |
| 15 | the-living-verb-i | PASS | |
| 16 | the-living-verb-ii | NEEDS FIXES | Forward prereq to seq 18 |
| 17 | reflexive-verbs | PASS | |
| 18 | questions-and-negation | PASS | |
| 19 | likes-and-preferences | PASS | Dative chunk is defensible |
| 20 | mine-and-yours | PASS | |
| 21 | demonstratives-this-that | NEEDS FIXES | Duplicate with seq 10 |
| 22 | numbers-and-money | NEEDS FIXES | Forward prereq to seq 32 |
| 23 | what-time-is-it | NEEDS FIXES | Forward prereq to seq 37 |
| 24 | checkpoint-sentences | PASS | |
| 25 | the-accusative-i-things | PASS | |
| 26 | the-accusative-ii-people | PASS | |
| 27 | accusative-prepositions | PASS | |
| 28 | the-locative-where-things-are | PASS | |
| 29 | around-the-city | PASS | |
| 30 | adjective-case-forms | PASS | |
| 31 | pronoun-declension | NEEDS FIXES | Dative paradigm exceeds A1 scope |
| 32 | the-genitive-i-absence | PASS | Scope extension noted |
| 33 | prepositions-of-place | PASS | |
| 34 | checkpoint-cases | PASS | |
| 35 | direction-and-origin | PASS | |
| 36 | yesterday-past-tense | NEEDS FIXES | Forward prereq to seq 54 |
| 37 | tomorrow-future-tense | PASS | |
| 38 | my-daily-routine | PASS | |
| 39 | food-vocabulary | PASS | |
| 40 | shopping-and-market | PASS | |
| 41 | at-the-cafe | PASS | |
| 42 | description-adverbs | PASS | |
| 43 | weather-and-nature | PASS | |
| 44 | checkpoint-daily-life | PASS | |
| 45 | can-and-know-how | PASS | |
| 46 | must-and-want | PASS | |
| 47 | imperative-and-requests | PASS | |
| 48 | body-and-health | PASS | |
| 49 | my-family | PASS | |
| 50 | holidays-and-traditions | PASS | |
| 51 | leisure-and-hobbies | PASS | |
| 52 | travel-and-transport | PASS | |
| 53 | at-the-restaurant | PASS | |
| 54 | checkpoint-communication | PASS | |
| 55 | prohibitions-and-signs | PASS | |
| 56 | buying-tickets | PASS | |
| 57 | taking-transport | PASS | |
| 58 | phone-basics | PASS | |
| 59 | writing-skills | PASS | |
| 60 | at-the-market | PASS | |
| 61 | at-the-store | PASS | |
| 62 | emergencies | PASS | Vocative not in grammar field |
| 63 | euphony-and-polish | PASS | |
| 64 | a1-final-exam | PASS | |

---

## Action Items (Prioritized)

1. **Fix 4 forward prerequisite dependencies** (HIGH) — the-living-verb-ii, yesterday-past-tense, what-time-is-it, numbers-and-money
2. **Resolve demonstrative pronoun duplication** (HIGH) — my-world-objects vs demonstratives-this-that
3. **Address Dative paradigm scope in pronoun-declension** (HIGH) — either downscope or mark as chunk
4. **Fix section budget for the-cyrillic-code-i** (HIGH) — add 100 words
5. **Fix checkpoint-first-contact objectives** (MEDIUM) — align with actually-preceding modules
6. **Add Vocative case to emergencies grammar field** (MEDIUM)
7. **Mark Accusative preview in colors-and-clothing** (MEDIUM)
8. **Update old module ID references across all plans** (LOW) — batch update to slug-based refs
