<!-- content-hash: fff21872747f -->
**Reviewed-By:** claude-opus-4-6

---

## Scores

| # | Dimension | Score | Justification |
|---|-----------|-------|---------------|
| 1 | **Lesson Quality** | 8 | Warm tutor voice, good use of tables and visual mapping, engaging dialogues. However, the grammar section (Section «Граматика: Конструкція «Немає» та «Без»») covers 9 sub-topics (~1200 words) before any learner practice. The NO_QUICK_WIN issue is real — no "try it yourself" moment until Section «Практика: Родовий відмінок у дії» (line 207+). No explicit encouragement phrases ("Great!", "You've got this!") anywhere in the content. Zero warm greeting/opening — no "Привіт!" or equivalent. Closing (line 360) is adequate but not celebratory. "Would I Continue?": 4/5 (fail: no quick wins). |
| 2 | **Language** | 7 | Double stress mark error on line 122: «ма́ми́» — Ukrainian words have exactly one stress; correct form is «ма́ми». Genitive plural forms «круасанів» (line 251) and «Кексів» (line 253) appear in the dialogue despite being explicitly out of scope (line 4: "Full Genitive plural (except fixed phrase 'немає грошей') → A2"). IPA inconsistency: line 33 uses with plain 'a', while line 229 uses with 'ɑ' for the same vowel quality. No Russianisms or colonial framing found. |
| 3 | **Immersion** | 8 | Pre-computed at 29.2% (target 25-40%). Within range. Section «Культурний контекст: «Немає проблем»» has good Ukrainian immersion in dialogues and proverbs. Section «Вступ: Ситуація відсутності» appropriately uses English for explanations. Good graduated immersion from English theory to Ukrainian examples to full Ukrainian dialogues. |
| 4 | **Activities** | 7 | 10 activities with good type variety (2 group-sort, 2 match-up, 3 fill-in, 2 unjumble, 1 quiz). However: (1) Activity "Заповніть діалоги" item 3 (activity file line 292): «— Ви бажаєте чай з молоком? — Ні, я люблю ... (без молоко).» — the answer "без молока" creates «я люблю без молока» which is grammatically incomplete ("люблю" requires a direct object). (2) Same activity item 6 (activity file line 316): «— Це вода? — Тут ... (немає вода).» — pragmatic mismatch: "Це вода?" is an identity question, not an existence question; the absence response doesn't match. (3) Activity "Закінчення: -а чи -у?" groups "сир" under «Абстрактні/Речовини/Іншомовні» — calling cheese a "substance" is debatable (it's countable). |
| 5 | **Vocabulary** | 8 | 20 items with IPA, POS, and grammatical notes. All required plan items present. Missing recommended items: ключ, газ (both appear in content but not in vocabulary YAML). "Газ" is used in Section «Граматика: Конструкція «Немає» та «Без»» line 144 «Вода без газу» but has no vocabulary entry. |
| 6 | **Richness** | 8 | Good cultural hooks: «Немає проблем» phrase, proverb «Немає диму без вогню» (line 304), hospitality tradition «Чим багаті, тим і раді» (line 317), bazaar culture (line 323). 6-7 engagement boxes ([!observe], [!tip] ×2, [!warning], [!caution], [!context], [!myth-buster]). The sentence «This dynamic usage of **є/немає** is the heartbeat of daily commerce in Ukraine» (line 331) is a mild LLM-ism but isolated. |
| 7 | **Humanity & Warmth** | 7 | 33 instances of "you/You" (adequate direct address). But ZERO explicit encouragement phrases — no "Great!", "Well done!", "You've got this!", or "Don't worry" directed at the learner. The only "Don't worry" (line 292) is explaining the phrase «Немає проблем», not encouraging the learner. No warm greeting at start. Closing (line 360) has «You are now ready to navigate the world» — adequate but formulaic. The lesson reads as informational rather than encouraging. Needs warmth injection. |
| 8 | **LLM Fingerprint** | 8 | One mild LLM-ism: «heartbeat of daily commerce» (line 331). Section openings vary well — no structural monotony. Example formats vary between bullet lists, tables, and dialogues. No "це не просто" or stacked abstract nouns detected. Callout box types are varied (7 different types). No repetitive callout titles. |
| 9 | **Factual Accuracy** | 9 | Grammar rules are correctly presented: -а/-я for concrete masculine, -у/-ю for abstract/substance, -и/-і for feminine. Proverb «Немає диму без вогню» is authentic. «Немає проблем» cultural explanation is accurate. «Чим багаті, тим і раді» is a genuine Ukrainian saying. One minor concern: line 85 groups «Батько → батька» under "Special Mentions" alongside fleeting vowel examples — батько → батька is regular -о declension, NOT a fleeting vowel, which could confuse learners (the tip on line 90 tries to clarify but the grouping is still misleading). |

---

## Critical Issues Found

### Issue 1: SCOPE VIOLATION — Genitive Plural in Dialogue (CRITICAL)

**Location:** Content file, lines 251-253 (Section «Практика: Родовий відмінок у дії», subsection «Діалог: Ввічлива відмова»)

**Evidence:**
- Line 251: «Вибачте, круасанів немає.»
- Line 253: «Кексів теж немає.»

**Problem:** The scope block (lines 2-6) explicitly states: "Not covered: Full Genitive plural (except fixed phrase 'немає грошей') → A2". The forms «круасанів» and «кексів» are Genitive plural, which is out of scope for this A1 module. Learners will encounter forms they haven't been taught, creating confusion. The only plural exception allowed is the fixed phrase «немає грошей» (line 185).

**Fix:** Replace the dialogue items with singular Genitive forms. E.g., «Вибачте, круасана немає» → though "круасан" is unusual in Ukrainian. Better: rewrite the dialogue entirely using vocabulary from the module. E.g.:
- Бариста: Вибачте, молока немає.
- Клієнт: А цукор?
- Бариста: Цукру теж немає.

---

### Issue 2: Double Stress Mark Error (SIGNIFICANT)

**Location:** Content file, line 122 (Section «Граматика: Конструкція «Немає» та «Без»»)

**Evidence:** «**мама** (mom) → немає **ма́ми́**»

**Problem:** Ukrainian words have exactly one stress per word. «Мами» is stressed on the first syllable:, so the correct notation is «ма́ми» (stress on the first syllable only). Two stress marks imply two stressed syllables, which is phonologically impossible.

**Fix:** Change «ма́ми́» to «ма́ми».

---

### Issue 3: Unnatural Activity Sentence (MODERATE)

**Location:** Activity file, line 292 (Activity "Заповніть діалоги", item 3)

**Evidence:** «— Ви бажаєте чай з молоком? — Ні, я люблю ... (без молоко).»

**Problem:** The correct answer «без молока» creates the sentence «Ні, я люблю без молока» — but «люблю» (love/like) requires a direct object. You can't say "I like without milk" in Ukrainian any more than in English. A natural response would be «Ні, я люблю чай без молока» (No, I like tea without milk) or «Ні, мені без молока» (No, without milk for me).

**Fix:** Rewrite the sentence to: «— Ви бажаєте чай з молоком? — Ні, я п'ю чай ... (без молоко).» — answer: «без молока». Or: «— Ні, мені каву ... (без молоко).»

---

### Issue 4: Pragmatic Mismatch in Activity (MODERATE)

**Location:** Activity file, line 316 (Activity "Заповніть діалоги", item 6)

**Evidence:** «— Це вода? — Тут ... (немає вода).»

**Problem:** «Це вода?» (Is this water?) is an identity/identification question. The natural response to an identity question is «Так, це вода» or «Ні, це не вода, це сік.» Responding with absence «Тут немає води» (There is no water here) is a pragmatic non-sequitur. An existence question would be «Тут є вода?» or «У вас є вода?».

**Fix:** Change the prompt to: «— Тут є вода? — Тут ... (немає вода).» — This makes the absence response pragmatically coherent.

---

### Issue 5: Misleading Grouping of «Батько» with Fleeting Vowels (MINOR)

**Location:** Content file, lines 83-90 (Section «Граматика: Конструкція «Немає» та «Без»»)

**Evidence:**
- Line 79: "Words often drop a vowel when you add the ending (the 'fleeting vowel' rule):"
- Line 85: «**Батько** (father) → немає **батька** (The 'о' changes to 'а').»

**Problem:** Lines 79-81 correctly explain the fleeting vowel rule (квиток → квитка, кінець → кінця — the vowel disappears). But line 85 presents «батько → батька» under "Special Mentions" in the same subsection. Батько → батька is NOT a fleeting vowel — it's regular declension of a -ко ending noun. The tip box (line 90) tries to clarify: "(This one keeps the stem but changes -о to -а!)" — but the initial grouping under the fleeting vowel subsection is still misleading for learners.

**Fix:** Move «батько → батька» to a separate mini-section or clearly label it: "This is NOT a fleeting vowel. The ending -о simply changes to -а."

---

### Issue 6: IPA Inconsistency — [a] vs [ɑ] (MINOR)

**Location:** Content file, lines 33, 68, 229

**Evidence:**
- Line 33: «» — final vowel uses plain 'a'
- Line 68: «» — final vowel uses plain 'a'
- Line 229: «» — final vowel uses 'ɑ'

**Problem:** Ukrainian has the open back unrounded vowel [ɑ] in all positions. The transcription inconsistently uses [a] (lines 33, 68) and [ɑ] (line 229) for the same phoneme. This should be standardized.

**Fix:** Normalize all instances of Ukrainian /а/ to [ɑ] in IPA transcriptions. Change →, →.

---

### Issue 7: Missing Warmth / Encouragement (STRUCTURAL)

**Location:** Entire content file — affects all sections

**Problem:** Zero explicit encouragement phrases directed at the learner. No "Great!", "Well done!", "You've got this!", or equivalent. No warm greeting at the opening. The "Would I Continue?" test reveals a cold start — Section «Вступ: Ситуація відсутності» begins with grammar explanation ("In English, when we want to say something is missing...") with no orientation or welcome. The required emotional beats for beginners (welcome → curiosity → small win → encouragement → progress visible) are missing the "welcome" and "encouragement" beats entirely.

**Fix:** (1) Add warm opening before line 17: "Welcome back! Today's lesson is a big step..." (2) Add ≥3 encouragement phrases throughout: after the Є/Немає contrast table (line 54), after the endings summary (line 112), after the dialogue section (line 266). (3) Strengthen closing (line 360) with explicit celebration.

---

## Verification Summary

| Check | Result | Details |
|-------|--------|---------|
| **Colonial framing** | PASS | No Russian-comparison patterns found. Ukrainian grammar presented on its own terms throughout. |
| **Russianisms** | PASS | No Russian calques or vocabulary detected (кушати, прекрасне, etc. absent). |
| **Scope compliance** | FAIL | Genitive plural forms «круасанів», «кексів» in dialogue (lines 251, 253) violate the scope declaration (line 4). |
| **Plan alignment** | PASS | All 4 content_outline sections present as H2. All learning objectives addressed. Vocabulary hints covered (required: 8/8; recommended: partial — missing ключ, газ in vocab YAML). |
| **LLM fingerprint** | PASS | One isolated "heartbeat" metaphor. No structural monotony. No repeated patterns. |
| **Factual accuracy** | PASS | Grammar rules accurate. Cultural claims verified. Proverb and sayings authentic. |
| **Activity quality** | PARTIAL FAIL | 2 activities have pragmatic/grammatical issues (items at activity lines 292 and 316). Remaining 8+ activities are well-formed. |
| **IPA accuracy** | PARTIAL FAIL | Stress placement correct throughout. Vowel notation inconsistent ([a] vs [ɑ]). Double stress on «ма́ми́» (line 122). |
| **Beginner warmth** | FAIL | Zero encouragement phrases. No warm greeting. Functional but cold. |

---

## Verdict

**FAIL — Requires targeted fixes before approval.**

The module has strong grammar content, well-organized visual aids, and engaging cultural context. The grammar explanations in Section «Граматика: Конструкція «Немає» та «Без»» are thorough and accurate. The dialogues in Section «Практика: Родовий відмінок у дії» and cultural material in Section «Культурний контекст: «Немає проблем»» are pedagogically valuable.

However, three issues require fixes before passing:

1. **Scope violation** (Critical): Remove Genitive plural forms from the dialogue or replace with singular Genitive examples.
2. **Double stress mark** (Significant): Fix «ма́ми́» → «ма́ми» on line 122.
3. **Activity quality** (Moderate): Fix the two broken dialogue items (activity lines 292, 316).

Additionally, warmth injection is needed to meet A1 beginner standards — the lesson is informational rather than encouraging.

**Estimated fix effort:** D.2 targeted repair (30-45 minutes). No rebuild needed.