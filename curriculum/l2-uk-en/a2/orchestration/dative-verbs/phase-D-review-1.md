**Reviewed-By:** claude-opus-4-6

# Phase D.1 Review: `dative-verbs` (A2-03)

**Module:** Dative Verbs — Verbs That Demand the Dative Case
**Level:** A2 | **Track:** Core Grammar | **Tier:** 1 (Beginner)
**Persona:** Encouraging Cultural Guide / Volunteer Coordinator
**Word Count:** 3452 / 3000 (115.1%) | **Activities:** 12 | **Immersion:** 51.9%

---

## Scores

| # | Dimension | Score | Justification |
|---|-----------|-------|---------------|
| 1 | **Language** | 8/10 | Ukrainian grammar is largely correct, but internal contradiction with -ові/-еві teaching vs. drill corrections; minor issue with «Ніхто не платив гроші» (Accusative under negation where Genitive is standard); some purple prose passages |
| 2 | **Lesson Quality** | 7/10 | "Would I Continue?" test: 3/5 — Practice starts at line 259 after ~2500 words of presentation; zero encouragement markers ("Great!", "Don't worry") until the final paragraph (line 500); missing mid-module CELEBRATE beats |
| 3 | **Activity Quality** | 8/10 | 12 activities with good variety; internal inconsistency — unjumble uses "лікарю" (line 231) while match-up uses "лікареві" (line 130) and content uses "лікареві" (line 447); translate activity marks "Ти любиш Київ?" as incorrect |
| 4 | **Richness** | 8/10 | Strong cultural hooks (Толока, volunteering, hand-on-heart gesture); named Ukrainian references; good modern contexts (army, displaced persons); weakened by generic metaphors |
| 5 | **Immersion** | 9/10 | 51.9% within the 50-60% A2 M01-20 target; English used appropriately for abstract theory; Ukrainian examples are natural and contextual |
| 6 | **LLM Fingerprint** | 6/10 | 8+ metaphors (CEO, magnets, GPS, heart, bridges, island, two hands, key-to-heart) vs. 4-max threshold; 4x "not just X" pattern; 3/4 section openings use transitional "Now/We will" formula; purple prose in intro |
| 7 | **Factual Accuracy** | 9/10 | Толока description historically accurate; grammar rules correct; "hand on heart" gesture is authentic; no fabricated claims in callout boxes |

**Aggregate:** 55/70

---

## Critical Issues Found

### CRITICAL 1: Massive Vocabulary Scope Gap (Plan Violation)

The plan (`plans/a2/dative-verbs.yaml`) lists 15 required verbs under `vocabulary_hints.required`. The content covers only **7 of 15** — over half of required vocabulary is absent:

**Missing required verbs (8):**
- вибачати (to forgive)
- пробачати (to excuse)
- заздрити (to envy)
- симпатизувати (to sympathize)
- співчувати (to empathize)
- підходити (to suit/fit)
- вистачати (to be enough)
- бракувати (to lack)

**Missing required collocations:**
- «наперед дякую» — not found anywhere in content
- «сліпо довіряти» — not found
- «допомагати по господарству» — not found

The vocabulary YAML file (38 items) also omits these verbs entirely. This is the most serious issue — the module only teaches the "easy" dative verbs and skips the entire impersonal/experiential subgroup (вистачати, бракувати) that the plan specifically requires.

**Location:** Entire module — these verbs should appear in section «Презентація: Дієслова Давального відмінка» under Група 3 or a new Група 4.

**Fix:** Add a Група 4 covering impersonal experientials (вистачати, бракувати) and a Група 5 for emotional datives (співчувати, вибачати, заздрити). Add all missing verbs to the vocabulary YAML. Add corresponding activities.

---

### CRITICAL 2: Severe LLM Fingerprint — Metaphor Overload + Structural Monotony

**Metaphor density (8+ distinct metaphors, threshold ≤4):**

| Line | Metaphor |
|------|----------|
| 14 | «isolated island in the sea of communication» |
| 14 | «Today, we build bridges» |
| 18 | «Verb is the CEO... small company» |
| 22 | «magnets that attract words» |
| 34 | «The ending is your GPS» |
| 78 | «heart of Ukrainian volunteering» |
| 64 | «ваш ключ до серця українців» |
| 162 | «two hands» |

**"Not just X" rhetoric pattern (4 instances, threshold ≤2):**
- Line 14: «Language is not just about naming objects»
- Line 22: «Verbs in Ukrainian are not just words that denote an action»
- Line 78: «"help" is not just an action; it is a cultural code»
- Line 257: «Grammar is not just tables; it is a tool for solving life situations»

**Structural monotony (section openings):**
- Section «Вступ: Керування та Адресат» → "Imagine that a sentence is a small company..."
- Section «Презентація: Дієслова Давального відмінка» → "We will divide these verbs..."
- Section «Практика: Відмінки в дії» → "Now that we know the theory, let's see..."
- Section «Діалоги: Взаємодопомога та Вдячність» → "Now let's listen to how..."

3/4 sections use the same transitional "Now/We will/Let's" formula.

**Purple prose:**
Line 64: «Кожне слово, яке ми вивчимо сьогодні, має свою особливу енергію.» — Empty filler. Words don't have "special energy."

**Fix:** Cut metaphor count to ≤4 (keep CEO, bridges — cut GPS, magnets, island, key-to-heart). Eliminate the "not just X but Y" pattern entirely. Vary section openings. Remove purple prose.

---

### CRITICAL 3: Pedagogical Inconsistency with -ові/-еві Forms

The module explicitly teaches at lines 293–301 in section «Практика: Відмінки в дії» that -ові/-еві is preferred for masculine persons:

> «The Dative case loves the endings **-ові** and **-еві** for men. This sounds more natural and "Ukrainian" than the short ending **-у/-ю**, especially for animate beings»

Yet the correction table at line 290 in the same section contradicts this:

| Wrong (line 290) | "Correct" (line 290) | Should be per module's own rule |
|---|---|---|
| «Ми дякуємо *вчителя*.» | «Ми дякуємо **вчителю**.» | «Ми дякуємо **вчителеві**.» |

Compare with line 104 where the long form IS used: «Студенти дякують **викладачеві** за цікаву лекцію.»

The same inconsistency appears in the activities — unjumble at line 231 uses «лікарю» while the match-up at line 130 and content at line 447 use «лікареві».

**Fix:** Change Drill 2 correction to «вчителеві». Change unjumble answer to use «лікареві» consistently. The module must practice what it preaches.

---

### Issue 4: Practice Starts Too Late — Pacing Problem

Section «Вступ: Керування та Адресат» runs from line 16 to line 66 (~600 words). Section «Презентація: Дієслова Давального відмінка» runs from line 68 to line 253 (~1800 words). The first actual practice drill in section «Практика: Відмінки в дії» doesn't appear until line 259.

That's ~2400 words of continuous presentation before any practice — violating the beginner pacing rule of ≤2 concepts before practice. By line 259, the learner has been introduced to: verb government, recipient concept, English vs Ukrainian logic, допомагати, дякувати, заважати, вірити, довіряти, радити, давати, дарувати, повідомляти, пропонувати, показувати, надсилати, подобатися, здаватися, пасувати/личити, боліти. That's **17+ verbs** before any practice.

**Fix:** Insert mini-drills after each Group in the Презентація section. After Група 1 (line 158), add a quick "Try it yourself" exercise. After Група 2 (line 204), add another. This distributes practice evenly.

---

### Issue 5: Insufficient Warmth & Encouragement

**Warmth markers found:**
- Encouragement phrases: **1** total — only at line 500: «Ви зробили великий крок уперед» + «Бажаємо успіхів!»
- "Don't worry" moments: **0** found
- "You can now..." validation: **1** — at line 500: «Тепер ви можете не тільки описувати світ, але й взаємодіяти з ним»
- "Great!", "Well done": **0** found anywhere (verified via Grep)

The rubric requires ≥3 encouragement phrases and ≥2 "don't worry" moments. All encouragement is concentrated in the final 2 lines. The entire 3400-word body is warmth-free.

**"Would I Continue?" assessment:**
1. Overwhelmed? **FAIL** — 17+ verbs before practice
2. Instructions clear? **PASS** — patterns/formulas are well-structured
3. Quick wins? **FAIL** — first practice at line 259
4. Ukrainian scary? **PASS** — good English scaffolding
5. Come back? **PASS** — cultural hooks are engaging

Score: 3/5 → Lesson Quality 8, reduced to 7 for zero warmth markers.

**Fix:** Add "Чудово!" or "You're doing great!" after each practice drill. Add at least one "Don't worry, this is the most common mistake even for natives" near the [!warning] at line 51. Add a mid-module progress marker after section «Практика: Відмінки в дії».

---

### Issue 6: IPA Errors in Vocabulary File

**Missing stress marks (2 items):**

| Word | Current IPA | Correct IPA | File Line |
|------|-------------|-------------|-----------|
| дякувати | `[dʲɑkuʋɑtɪ]` | `` | vocabulary/dative-verbs.yaml:9 |
| толока | `[tɔlɔkɑ]` | `` | vocabulary/dative-verbs.yaml:60 |

**Inconsistent quoting:** Some IPA entries have surrounding quotes (`'[...]'`), others don't (`[...]`). Compare line 6 (`''`) with line 18 (``). Should be consistent.

---

### Issue 7: Minor Grammar — Accusative Under Negation

Line 93 in section «Презентація: Дієслова Давального відмінка» (Толока culture box):

> «Ніхто не платив гроші.»

Standard Ukrainian grammar prefers Genitive after negated transitive verbs: «Ніхто не платив **грошей**.» While the Accusative form is increasingly accepted in colloquial speech, a grammar-focused A2 module should model the standard form. This is especially important because the module explicitly teaches case selection.

---

## Factual Verification

| Claim | Location | Verdict |
|-------|----------|---------|
| **Толока** as communal labor tradition | Line 93, [!culture] box in section «Презентація: Дієслова Давального відмінка» | **ACCURATE** — Толока is a well-documented communal work tradition in Ukrainian villages |
| «Красно дякую» as a sincerity expression | Line 112, [!context] box in section «Презентація: Дієслова Давального відмінка» | **ACCURATE** — «Красно дякую» is an authentic Ukrainian expression meaning "thank you beautifully/generously" |
| Hand-on-heart gesture with «Дякую» | Line 112, [!context] box in section «Презентація: Дієслова Давального відмінка» | **ACCURATE** — This is an authentic Ukrainian cultural gesture of sincerity |
| «Подобати» existed in old language but reflexive form is standard today | Line 227, [!myth-buster] box in section «Презентація: Дієслова Давального відмінка» | **ACCURATE** — The non-reflexive form is archaic; modern standard uses only «подобатися» |
| «Вірити в + Acc» vs. «Вірити + Dat» distinction | Line 141–146, [!tip] box in section «Презентація: Дієслова Давального відмінка» | **ACCURATE** — This distinction is correctly explained: faith/existence vs. truthfulness |
| State Standard §4.2.2.3 reference for повідомляти | Line 179 in section «Презентація: Дієслова Давального відмінка» | **ACCURATE** — Matches research notes line 4 |

No fabricated claims found. All cultural and grammatical assertions verified.

---

## Verification Summary

| Check | Result | Details |
|-------|--------|---------|
| **Plan section compliance** | PARTIAL FAIL | All 4 H2 sections present, but vocabulary scope grossly incomplete (7/15 required verbs) |
| **Colonial framing** | PASS | No "unlike Russian" patterns found |
| **Russianisms** | PASS | No Russian calques detected in Ukrainian text |
| **Grammar accuracy** | MINOR ISSUE | «Ніхто не платив гроші» — Genitive preferred under negation |
| **Activity errors** | MINOR ISSUE | Inconsistent -ові/-еві forms across activities; translate activity marks valid Ukrainian as incorrect |
| **IPA accuracy** | FAIL (2 items) | Missing stress marks on дякувати and толока |
| **LLM fingerprint** | FAIL | 8+ metaphors, 4x "not just" pattern, structural monotony |
| **Warmth markers** | FAIL | 0 encouragement mid-module; all warmth concentrated at final paragraph |
| **Factual accuracy** | PASS | All callout box claims verified |
| **Immersion target** | PASS | 51.9% within 50-60% range |

---

## Verdict

**REVISE** — The module requires targeted repairs before passing.

**Priority 1 (Critical):**
- Add the 8 missing required verbs (вибачати, пробачати, заздрити, симпатизувати, співчувати, підходити, вистачати, бракувати) with examples and corresponding activities
- Fix -ові/-еві inconsistency in Drill 2 (line 290) and unjumble (line 231)
- Reduce metaphor count from 8+ to ≤4; eliminate "not just X" pattern; vary section openings

**Priority 2 (Important):**
- Redistribute practice — add mini-drills after each Група in section «Презентація: Дієслова Давального відмінка»
- Add ≥3 encouragement phrases distributed throughout the module body
- Fix IPA stress marks for дякувати and толока in vocabulary file
- Fix «Ніхто не платив гроші» → «Ніхто не платив грошей» (line 93)

**Priority 3 (Polish):**
- Standardize IPA quote formatting in vocabulary YAML
- Add missing collocations: «наперед дякую», «сліпо довіряти», «допомагати по господарству»