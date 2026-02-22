<!-- content-hash: 2d2deba18392 -->
**Reviewed-By:** claude-opus-4-6

---

## Scores

| # | Dimension | Score | Evidence Summary |
|---|-----------|-------|------------------|
| 1 | Language Quality | 7/10 | Fabricated term «Енфонія» in H2 title (line 61); imprecise soft-feminine rule description (line 133); mid-paragraph language switch (line 162) |
| 2 | Lesson Quality | 7/10 | Bloated English paragraphs in 10+ locations create wall-of-text problem; overwhelms A2 learner; pacing breaks between theory and practice too long |
| 3 | Immersion Balance | 9/10 | 58.8% Ukrainian within 50-60% target; English support well-placed for grammar theory |
| 4 | Richness | 8/10 | Strong cultural hooks (Хліб-сіль, friendship hierarchy), two dialogue scenarios; but persona «Wedding Starosta» barely visible in prose |
| 5 | Activities | 7/10 | Scope violation: cloze blanks 8-9 test instrumental of means (овочами, лимоном), contradicting lesson's stated scope; «Ігор → Ігорем» unexplained exception; euphony quiz marks valid answers wrong |
| 6 | LLM Fingerprint | 6/10 | 10 English paragraphs follow identical "In Ukrainian..." → explain → example → motivational closer pattern; 4 grammar subsections use identical example batching format; structural monotony across section openings |
| 7 | Factual Accuracy | 8/10 | «Енфонія» is not a real Ukrainian linguistic term (should be «евфонія»); grammar endings are accurate; cultural claims (Хліб-сіль) verified against research |

---

## Critical Issues Found

### CRITICAL 1: Fabricated term «Енфонія» in section title (line 61)

**Location:** Section «Презентація: Форми та Енфонія» (H2 header, line 61)

The correct Ukrainian linguistic term for euphony is **«евфонія»** (from Greek εὐφωνία). The term **«енфонія»** does not exist in Ukrainian linguistics. The content itself correctly uses the native Ukrainian term «милозвучність» (line 159, 162), which makes the fabricated Latinate form in the section title even more incongruous. This appears in a prominent H2 heading and is a visible error.

**Fix:** Replace «Енфонія» with «Евфонія» in the H2 header on line 61. Also update the meta `content_outline` section header to match.

---

### CRITICAL 2: Scope violation in cloze activity — instrumental of means introduced

**Location:** Activities file, cloze exercise "Історія про відпустку", blanks 8-9 (lines 448-453)

The content explicitly states on line 26: «У цьому модулі ми працюємо майже виключно з питанням Ким? — люди у вашому житті.» The SCOPE comment (lines 2-4) explicitly defers "Instrumental Case (Means/Tools) → a2-05."

Yet the cloze activity tests:
- Blank 8: «рибу {{8}} (овочі)» → answer «з овочами» — this is instrumental of means/accompaniment-of-food, NOT accompaniment with people
- Blank 9: «чай {{9}} (лимон)» → answer «з лимоном» — this is instrumental of means (tea with lemon), explicitly deferred to a2-05

This violates the module's own stated scope and pre-teaches content from a2-05.

**Fix:** Replace blanks 8-9 with person-accompaniment phrases. E.g., blank 8: «Ми пішли на вечерю {{8}} (Олена)» → «з Оленою»; blank 9: «Іван сидів поруч {{9}} (хлопці)» → «з хлопцями».

---

### CRITICAL 3: LLM structural monotony — 10 English paragraphs with identical pattern

**Location:** Lines 68, 89, 111, 162, 193, 213, 243, 269, 340, 366, 396

Every major subsection opens with a long English paragraph that follows the same template:
1. Abstract overview of the concept
2. "This is..." value statement
3. "For example..." concrete detail
4. Motivational closer about importance

Verified examples:
- Line 68: «In Ukrainian grammar, masculine nouns that end in a regular consonant are called "hard stems". When you want to use these words...»
- Line 89: «Soft stems are a key feature of the Ukrainian language. When a masculine noun ends with a soft sign...»
- Line 111: «Feminine nouns ending in "-а" change according to a beautiful, melodic pattern. This is one of the most recognizable...»
- Line 213: «Now that you know the grammatical endings, let's look at how we actually use them in real-life situations...»
- Line 243: «The word order in the Ukrainian language is notoriously flexible, allowing you to move words around...»
- Line 269: «In traditional Ukrainian culture, there are very clear and distinct levels of interpersonal closeness...»

All 10 paragraphs use the same rhetorical structure. This is a strong LLM fingerprint signal.

**Fix:** Vary the English support style: use some Q&A format, some "imagine you're in..." scenario framing, some brief bullet-point summaries. Not every subsection needs a paragraph-length English preamble.

---

### ISSUE 4: Unexplained exception «Ігор → Ігорем» contradicts taught rule

**Location:** Content line 231: «Олена зустрічається з Ігорем.» Activities line 21-22: «Ігор → з Ігорем».

The lesson teaches that masculine nouns ending in a hard consonant take **-ом** (line 70): «Додайте закінчення -ом до основи слова.» Examples: брат → братом, Олег → Олегом. But «Ігор» ends in a hard consonant (-р) yet takes **-ем** (з Ігорем, not *з Ігором). This is because «Ігор» historically follows the soft-stem pattern (old orthography «Ігорь»).

A learner applying the taught rules would produce *«з Ігором»* and be wrong. Neither the content nor the activities explain this exception.

**Fix:** Either (a) add a brief note near the soft-stem masculine section explaining that some names like «Ігор» follow soft-stem patterns despite lacking a visible -ь, or (b) replace «Ігор» with a clearly hard-stem name in the activities (e.g., «Роман → з Романом»).

---

### ISSUE 5: Euphony quiz marks valid prepositions as incorrect

**Location:** Activities file, quiz "Милозвучність", item on line 113-123:

```
Він працює разом ____ сестрою.
```
Correct answer: «із». The explanation says: «After разом, we often use із for rhythm, though з is also possible.» Yet «з» is marked `correct: false`. If «з» is also possible (as the explanation itself admits), marking it wrong is misleading at A2.

Similarly, item on line 69-79: «Вона щодня гуляє ____ собакою в парку.» — «із» is marked incorrect, but «із собакою» is grammatically valid (just less common). The content itself (line 180-183) says «із» is a stylistic variant, not an error.

**Fix:** Either accept both «з» and «із» as correct in ambiguous cases, or remove the «із» option entirely from the euphony quiz to avoid testing on subjective preference.

---

### ISSUE 6: Bloated English paragraphs hurt A2 pacing

**Location:** Lines 68, 89, 111, 162, 193, 213, 243-245, 269, 340, 366, 396

Multiple subsections contain English paragraphs of 80-120 words that restate what the Ukrainian text already explains, adding little new information. The worst offender is lines 243-245 in section «Практика: Соціальні зв'язки», where TWO consecutive English paragraphs (combined ~150 words) explain word order — content that the three Ukrainian example sentences on lines 249-256 demonstrate perfectly.

Line 245 is pure filler: «Always double-check that you have included the preposition and added the right ending to the noun. This small grammatical detail makes a massive difference in how native speakers perceive your level of fluency.»

For an A2 learner, these dense paragraphs create a wall-of-text effect that breaks pacing between concept and practice.

**Fix:** Trim each English paragraph to 2-3 sentences maximum. The Ukrainian examples + grammar tables already carry the pedagogical load. English should supplement, not duplicate.

---

### ISSUE 7: Mid-paragraph language switch (line 162)

**Location:** Section «Презентація: Форми та Енфонія», euphony subsection, line 162

The paragraph starts in English: «The Ukrainian language loves music and smooth sounds...» and switches to Ukrainian mid-paragraph without any transition: «...making your speech flow naturally. Тому прийменник «з» змінює свою форму залежно від наступного слова.»

This is jarring. A paragraph should maintain consistent language. The bilingual A2 scaffolding works when English and Ukrainian are in separate, clearly marked blocks.

**Fix:** Split into two paragraphs — English explanation, then Ukrainian continuation. Or consolidate into one language.

---

### ISSUE 8: Semantically odd error example (line 425)

**Location:** Section «Діалоги: Зустрічі та плани», error table, line 425

The error table shows: «Вона йде з школа. → Вона йде зі школою.» The corrected form «Вона йде зі школою» means "She goes with a school" (accompaniment), which is semantically bizarre — schools are not companions. The learner's likely intended meaning is either "She goes to school" (до школи) or "She goes from school" (зі школи, genitive). In a lesson specifically about accompaniment WITH PEOPLE, an example about accompanying a school is confusing.

**Fix:** Replace with a person-accompaniment example: «Вона йде з подруга. → Вона йде з подругою.»

---

## Verification Summary

### Plan Compliance

| Plan Section | Content H2 | Present? | Notes |
|-------------|------------|----------|-------|
| Вступ: Орудний відмінок та спільність дії | «Вступ: Сьомий відмінок і гармонія» | Yes | Title differs slightly from plan but content covers all required points |
| Презентація: Закінчення та правила евфонії | «Презентація: Форми та Енфонія» | Yes | Contains fabricated term «Енфонія»; all ending paradigms covered |
| Дієслова спілкування та прийменник «З» | Merged into «Практика: Соціальні зв'язки» | Partial | Social verbs section present; "crucial distinction" (means vs accompaniment) mentioned briefly at line 48 but not drilled deeply |
| Практика: Разом та ієрархія дружби | Part of «Практика: Соціальні зв'язки» | Yes | Friendship hierarchy and «разом з» both covered |
| Діалоги та підсумок | «Діалоги: Зустрічі та плани» + «Підсумок» | Yes | Two dialogues + error section + summary checklist |

### Vocabulary Coverage

| Required Vocab (from plan) | In Content? | In Vocab YAML? |
|---------------------------|-------------|----------------|
| з / із / зі | Yes (throughout) | Yes |
| разом / разом з | Yes (lines 296-310) | Yes |
| зустрічатися | Yes (lines 228-232) | Yes |
| розмовляти | Yes (lines 222-226) | Yes |
| гуляти | Yes (lines 215-220) | Yes |
| спілкуватися | Yes (lines 258-264) | Yes |
| познайомитися | Yes (line 274) | Yes |
| одружитися | Yes (line 289) | Yes |
| подружитися | Yes (line 288) | Yes |
| друг / приятель / знайомий | Yes (lines 266-294) | Yes |
| помиритися (recommended) | Not in content | Yes (in vocab YAML) |
| посваритися (recommended) | Not in content | Yes (in vocab YAML) |
| товаришувати (recommended) | Not in content | Yes (in vocab YAML) |

### Activity Alignment

| Activity | Type | Items | Issue? |
|----------|------|-------|--------|
| Хто з ким? | match-up | 12 pairs | Clean |
| Сортування закінчень | group-sort | 4 groups/20 items | Clean |
| Милозвучність | quiz | 9 items | Valid answers marked wrong (Issue 5) |
| Чоловічий рід | fill-in | 8 items | Clean |
| Жіночий рід | fill-in | 8 items | Clean |
| Весілля | mark-the-words | 6 answers | Clean |
| Складіть речення | unjumble | 6 items | Clean |
| Знайдіть помилку | error-correction | 6 items | Clean |
| Дії та люди | match-up | 12 pairs | Clean |
| Мішані форми | fill-in | 8 items | Clean |
| Оберіть правильні | select | 6 multi-select | Clean |
| Історія про відпустку | cloze | 12 blanks | Scope violation blanks 8-9 (Issue 2) |

### Colonial Framing Check
No instances of Ukrainian defined by contrast with Russian. Line 20 compares to English (learner's L1), which is appropriate.

### Russianisms Check
No Russianisms detected. Forms are standard Ukrainian throughout.

### "Would I Continue?" Test (Beginner)

| Question | Result | Notes |
|----------|--------|-------|
| Did I feel overwhelmed? | FAIL | 10+ dense English paragraphs create wall-of-text; too much theory before each practice point |
| Were instructions clear? | PASS | Grammar rules clearly stated with tables |
| Did I get quick wins? | PASS | Simple examples appear early in each section |
| Was Ukrainian scary? | PASS | English scaffolding throughout |
| Would I come back tomorrow? | PASS | Engaging cultural hooks, practical dialogues |

**Result:** 4/5 Pass → Baseline Lesson Quality 9, downgraded to 7 for severity of English bloat and LLM monotony affecting learner experience.

### LLM Fingerprint Evidence

**Structural monotony:** First lines of the 4 grammar subsections in «Презентація: Форми та Енфонія»:
1. Line 66: «Більшість чоловічих іменників закінчуються на приголосний (тверда основа).»
2. Line 87: «Деякі чоловічі іменники мають м'яку основу — вони закінчуються на -ь або -й.»
3. Line 109: «Жіночі іменники на -а змінюються за красивою, мелодійною схемою.»
4. Line 130: «Як і чоловічі іменники, жіночі теж мають м'які варіанти.»

These are then each followed by the same structure: Ukrainian intro → long English paragraph → **Правило:** → bullet list of forms → **Приклади в реченнях:** → bullet list. 4/4 sections identical.

**Example batching:** All grammar sections use the identical format of `**word** → **з word_instr**` bullet lists followed by `**Приклади в реченнях:**` with sentence bullets. No variation (no tables, no inline examples, no interleaved practice).

**Callout variety:** Callout types used: [!culture] ×2, [!warning] ×2, [!tip] ×1, [!note] ×1, [!observe] ×1. Reasonable variety — no monotony here.

---

## Verdict

**FAIL — Requires targeted repair (Phase D.2)**

**Blocking issues requiring fix:**
1. **«Енфонія» → «Евфонія»** — fabricated linguistic term in H2 title (line 61)
2. **Cloze blanks 8-9 scope violation** — remove instrumental-of-means items from accompaniment module
3. **Euphony quiz false negatives** — stop marking valid «з»/«із» as incorrect
4. **«Вона йде зі школою»** — replace semantically bizarre error example with person-accompaniment

**Non-blocking improvements recommended:**
5. Trim English paragraphs to 2-3 sentences each (currently 80-120 words each)
6. Vary example presentation formats across grammar subsections to reduce LLM monotony
7. Fix mid-paragraph language switch at line 162
8. Add note about «Ігор → Ігорем» exception or replace with regular hard-stem name
9. Replace «доця» with more standard «донька» for soft-feminine rule illustration