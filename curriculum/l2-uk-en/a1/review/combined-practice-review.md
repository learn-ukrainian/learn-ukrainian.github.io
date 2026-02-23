<!-- content-hash: 39f3b77b4a97 -->
**Reviewed-By:** claude-opus-4-6

---

## Scores

| # | Dimension | Score | One-Line Evidence |
|---|-----------|-------|-------------------|
| 1 | Language Quality | 7/10 | Model paragraph uses «Бо» and «Тому що» as standalone sentence fragments, contradicting comma rules taught in the same lesson; unjumble answers systematically omit commas |
| 2 | Lesson Quality | 8/10 | Strong PPP arc with warm opening and clear structure, but reading passages (~700+ words) break pacing for A1 learners with no scaffolding |
| 3 | Immersion Balance | 8/10 | 37.1% within target band; reading passages appropriately in Ukrainian, but lack the English support A1 learners need |
| 4 | Factual Accuracy | 8/10 | Grammar rules mostly correct, but the narrative breakdown (lines 294–298) misquotes its own model paragraph |
| 5 | Richness | 8/10 | Good cultural hooks (coffee ritual, market culture), but reading passages at lines 265–277 are generic filler unrelated to module objectives |
| 6 | Activity Quality | 6/10 | 4 unjumble answers missing mandatory commas; quiz marks valid Ukrainian word orders as incorrect; match-up pair contradicts taught pattern |
| 7 | Vocabulary Quality | 7/10 | IPA for «також» has double stress mark `[ˈtɑˈkɔʒ]`; IPA for «вирішити» has wrong stress placement `[ˈʋɪrʲiʃɪtɪ]` |
| 8 | Humanity / Warmth | 8/10 | Warm "Привіт!" opening, regular encouragement, but warmth drops completely in the reading passages |
| 9 | LLM Fingerprint | 7/10 | 9 identical "**How it works:**" subheadings and 9 identical "**Usage note:**" subheadings create rigid structural monotony |
| 10 | Plan Compliance | 7/10 | Large reading passages (lines 265–277) and 6 extra activities not in plan; breakdown section fabricates quotes from its own paragraph |

---

## Critical Issues Found

### Issue 1: Unjumble Answers Missing Mandatory Commas (Activity Quality — CRITICAL)

**Location:** activities/combined-practice.yaml, unjumble activities (lines 365, 367, 418, 424)

The lesson explicitly teaches that commas precede «але» (line 62: "we always place a comma (кома) before **але**") and «тому що» (line 148: "A comma always precedes it"). Yet the unjumble answers omit all punctuation:

- Line 365: `answer: "Ми не гуляємо бо холодно"` → should be «Ми не гуляємо, бо холодно»
- Line 418: `answer: "Вона читає але він працює"` → should be «Вона читає, але він працює»
- Line 367: `answer: "Якщо хочеш ми готуємо разом"` → should be «Якщо хочеш, ми готуємо разом»
- Line 424: `answer: "Ми купуємо це тому що треба"` → should be «Ми купуємо це, тому що треба»

These are 4 separate instances of the same systematic error. An A1 learner who drills these exercises will internalize incorrect punctuation — directly contradicting the grammar rules the module teaches.

**Fix:** Add commas to all 4 unjumble answers and include comma as a "word" tile in the `words` array.

---

### Issue 2: IPA Double Stress and Wrong Stress (Vocabulary Quality — CRITICAL)

**Location:** vocabulary/combined-practice.yaml

(a) Line 43: `ipa: '[ˈtɑˈkɔʒ]'` for «також» — contains TWO primary stress marks (ˈ), which is phonetically impossible. The correct IPA is `[tɑˈkɔʒ]` with stress on the second syllable.

(b) Line 65: `ipa: '[ˈʋɪrʲiʃɪtɪ]'` for «вирішити» — places stress on the first syllable «ви». The correct stress is вирі́шити → `[ʋɪˈrʲiʃɪtɪ]`.

**Fix:** Correct both IPA transcriptions.

---

### Issue 3: Model Paragraph Contradicts Taught Grammar Rules (Language Quality — SIGNIFICANT)

**Location:** combined-practice.md, line 288

The "Мій ідеальний день" model paragraph at line 288 uses «Бо» and «Тому що» as standalone sentence starters after full stops:

«Ми йдемо на каву. **Бо** ранок теплий.»
«Ми готуємо вечерю разом. **Тому що** ми любимо смачну українську їжу.»

But the lesson itself teaches at line 148: "A comma always precedes it" (for тому що), and the subordinating conjunction «бо» is taught as a clause connector, not a sentence starter. An A1 learner reading this model paragraph will be confused about whether these words start new sentences or connect clauses.

**Fix:** Rewrite as connected clauses: «Ми йдемо на каву, бо ранок теплий.» and «Ми готуємо вечерю разом, тому що ми любимо смачну українську їжу.»

---

### Issue 4: Narrative Breakdown Misquotes Its Own Paragraph (Factual Accuracy — SIGNIFICANT)

**Location:** combined-practice.md, lines 294–298

The breakdown section claims to analyze the model paragraph at line 288, but contains inaccurate references:

(a) Line 294: "It connects parallel actions with **і** (зустрічаю друга, і ми йдемо)." — The actual paragraph says «Спочатку я зустрічаю друга. Ми йдемо на каву.» — two separate sentences with no «і» connecting them.

(b) Line 295: "a formal reason with **тому що** (**тому що** ми дуже любимо)." — The actual paragraph says «**Тому що** ми любимо смачну українську їжу» — "дуже" is fabricated and the full phrase is truncated.

(c) Line 297: "It creates a contrast with **але** (але сьогодні там багато людей)." — The actual paragraph says «Але там дуже багато людей» — "сьогодні" is fabricated and "дуже" is removed.

**Fix:** Rewrite all three breakdown bullet points to match the actual paragraph text verbatim.

---

### Issue 5: Quiz Marks Valid Ukrainian Word Order as Incorrect (Activity Quality — SIGNIFICANT)

**Location:** activities/combined-practice.yaml, lines 227–237

Quiz question: "Де в українському реченні правильно стоїть слово також?" marks option «Також я хочу каву.» (line 234) as `correct: false`. However, sentence-initial «також» is grammatically valid in Ukrainian — it functions as a sentence adverb meaning "Also, I want coffee." The quiz's own explanation says «також зазвичай стоїть перед дієсловом» (line 228), and in «Також я хочу каву» it IS before the verb «хочу».

The same issue appears at line 295 where «Також Віктор читає книгу.» is marked incorrect — also a valid Ukrainian sentence.

**Fix:** Either (a) add a nuance to the explanation noting that sentence-initial також is valid but less common, or (b) rephrase the question to "Which is the MOST natural position?" and mark the less common positions as "possible but less common" rather than simply wrong.

---

### Issue 6: Match-Up Pair Contradicts Taught Sequence Pattern (Activity Quality — MODERATE)

**Location:** activities/combined-practice.yaml, lines 347–348

The match-up pair «Спочатку робота,» → «і нарешті відпочинок.» creates the sequence "Спочатку... і нарешті" — skipping «потім» entirely. The lesson explicitly teaches the three-step pattern «Спочатку → потім → нарешті» (line 134), so a drill pair that jumps from спочатку directly to нарешті undermines the taught structure.

**Fix:** Change the right side to «потім відпочинок.» or change the left side to «Потім робота,» with the right side as «і нарешті відпочинок.»

---

### Issue 7: Reading Passages Are Unscaffolded Filler (Plan Compliance / Lesson Quality — MODERATE)

**Location:** combined-practice.md, lines 265–277

Section «Практика: Сценарії реального життя» contains ~700 words of continuous Ukrainian reading text (lines 265–277) that:

- Is not specified in the plan's content outline for this section
- Uses almost none of the taught conjunctions (і, але, тому що, бо, якщо, спочатку, потім, нарешті) — it's mostly simple declarative sentences
- Has no English support, no vocabulary glosses, no comprehension tasks
- The instruction at line 265 says «Читайте і шукайте нові слова» but provides no guidance on which words or how

For an A1 learner, encountering ~700 words of unsupported Ukrainian text after carefully scaffolded instruction is a jarring pacing break that could trigger the "Would I Continue? → No" response.

**Fix:** Either (a) cut to ~200 words and embed the target conjunctions throughout, adding comprehension questions, or (b) move to a separate graded reader appendix outside the main lesson flow.

---

### Issue 8: Structural Monotony — 9× Identical Subheading Pattern (LLM Fingerprint — MODERATE)

**Location:** combined-practice.md, lines 36, 61, 88, 105, 122, 147, 164, 191, 242

Every grammar subsection follows the exact same template:
1. **How it works:** (9 occurrences)
2. **Examples:** (8 occurrences)
3. **Usage note:** (9 occurrences)

This rigid three-part structure repeated identically across 9 subsections is a clear LLM generation pattern. Real tutoring material would vary its presentation — sometimes a table, sometimes a dialogue, sometimes a comparison, sometimes a narrative example.

**Fix:** Vary the presentation format across subsections. For example, use a comparison table for «тому що vs. бо» (already done at line 180 — good), use a dialogue format for «також» placement, use a "spot the error" format for one subsection.

---

## Factual Verification

| Claim | Source | Verdict |
|-------|--------|---------|
| Coffee ritual as social hub in Lviv | Research notes line 21, culturally well-established | **PASS** |
| Market (базар) as fresh produce center | Research notes line 22 | **PASS** |
| Standard §4.3.2 on складне речення | Research notes line 4 | **PASS** |
| «і» changes to «й» after vowels | Standard Ukrainian euphony rule | **PASS** |
| «тому що» = formal, «бо» = colloquial | Research notes line 27, Standard | **PASS** |
| «також» placement rule | Research notes line 26 | **PASS** (but quiz overgeneralizes — see Issue 5) |
| Comma always precedes «але» | Ukrainian punctuation standard | **PASS** (but lesson's own examples violate this — line 71) |
| Comma always precedes «тому що» | Ukrainian punctuation standard | **PASS** (but model paragraph violates this — line 288) |

**Note on line 71:** The example «Ми хотіли піти в парк. Але почався дощ.» uses «Але» as a sentence starter. While this is stylistically acceptable in Ukrainian (especially spoken/narrative), placing it right after teaching "we always place a comma before але" (line 62) creates an internal contradiction. This should at minimum have a note explaining that sentence-initial «але» after a period is a stylistic choice.

---

## Section-by-Section Assessment

### Section «Вступ: Культура планування» (lines 15–55)
Strong opening with warm «Привіт!» and culturally grounded coffee hook. The sample dialogue between Олена and Віктор is well-crafted and accessible. Grammar introduction of «і» and «але» is clear with good examples. The [!tip] on «і vs. й» euphony is excellent — pedagogically valuable and naturally placed. The [!culture] box about «Пішли на каву!» is culturally accurate and engaging. This section delivers on the plan's outline effectively.

### Section «Презентація: Структура та Причини» (lines 77–205)
Solid coverage of all planned grammar points. The [!warning] box on the "Потім loop" (line 136–138) is a smart, well-targeted warning. The comparison table for «тому що vs. бо» (line 180) is one of the few format variations and works well. The «також» placement section correctly identifies the English interference pattern. Main weakness: the structural monotony of "How it works → Examples → Usage note" repeated 7 times in this section alone.

### Section «Практика: Сценарії реального життя» (lines 207–277)
The market dialogue (lines 220–229) is excellent — authentic, well-paced, and effectively demonstrates all taught conjunctions. The [!history-bite] box (line 215) adds cultural depth. The «якщо» introduction (lines 238–261) is clear. The [!observe] "Logic Blocks" (line 258) is a creative programming analogy appropriate for the audience. However, the reading passages at lines 265–277 are the module's weakest point — see Issue 7.

### Section «Висновок: Мій наратив» (lines 279–323)
The consolidation paragraph "Мій ідеальний день" (line 288) is a good concept but has execution issues — standalone conjunctions contradict taught rules (Issue 3), and the breakdown misquotes it (Issue 4). The self-check questions (lines 317–322) are pedagogically sound and well-targeted. The «Додаткова історія для читання» (line 304) is better than the earlier reading passages — it actually uses all the target conjunctions — but still lacks comprehension scaffolding.

---

## Verification Summary

| Check | Result |
|-------|--------|
| Russianisms | **PASS** — No Russianisms detected |
| Calques | **PASS** — No calques detected |
| Colonial framing | **PASS** — Ukrainian presented on its own terms throughout |
| Word salad | **PASS** — Paragraphs are coherent (reading passages are simple but not word salad) |
| Grammar scope violations | **PASS** — Content stays within A1 scope (no conditional б/би, no коли) |
| IPA correctness | **FAIL** — Double stress on «також», wrong stress on «вирішити» |
| Activity accuracy | **FAIL** — Missing commas in unjumble answers, misleading quiz options |
| Plan outline compliance | **PARTIAL FAIL** — All 4 planned sections present, but reading passages are extraplanary |
| Engagement boxes | **PASS** — 5 callout boxes, varied types ([!culture], [!tip], [!warning], [!history-bite], [!observe]) |
| "Would I Continue?" Test | 4/5 Pass (overwhelmed at reading passages) → Lesson Quality 9 → adjusted to 8 for additional issues |

---

## Verdict

**FAIL** — Module requires targeted fixes before passing.

**Critical fixes (must resolve):**
1. Add commas to all 4 unjumble answers (activities lines 365, 367, 418, 424) and include comma tiles
2. Fix IPA: «також» → `[tɑˈkɔʒ]`, «вирішити» → `[ʋɪˈrʲiʃɪtɪ]`
3. Rewrite model paragraph at line 288 to connect «бо» and «тому що» clauses with commas instead of periods
4. Fix breakdown at lines 294–298 to match the actual model paragraph text

**Significant fixes (strongly recommended):**
5. Rephrase також quiz question or add nuance about sentence-initial position
6. Fix match-up pair at line 347–348 to align with taught спочатку/потім/нарешті pattern
7. Trim reading passages (lines 265–277) to ~200 words with embedded target conjunctions and comprehension tasks
8. Vary structural format across subsections to break the 9× "How it works / Examples / Usage note" monotony