## Linguistic Scan

**Russianisms:** None found.
**Surzhyk:** None found.
**Calques:** None found.
**Paronyms:** None found.
**Russian characters (ы, э, ё, ъ):** None found.

**Phonetic claims verified against textbook RAG:**
- 33 літери, 38 звуків — confirmed by Заболотний Grade 5 p.73 (via plan reference) and Litvinova Grade 5 p.129 ✓
- 6 голосних звуків, 10 голосних літер — confirmed by Litvinova Grade 5 p.114: "В українській мові шість голосних звуків, на письмі їх позначаємо десятьма літерами" ✓
- 32 приголосні звуки — consistent with 38 − 6 = 32 ✓
- Щ = [шч] — confirmed by Заболотний Grade 5 p.84: "щ → Два звуки [шч]" and Голуб Grade 5 p.78: "Буква щ завжди позначає два звуки [шч]" ✓
- Ї = [йі] — confirmed by Голуб Grade 5 p.78: "Буква ї завжди позначає два звуки [йі]" ✓
- Большакова poem "Голосні почуєш в пісні" — confirmed verbatim by RAG (Большакова Grade 1 p.24) ✓
- Большакова poem "Приголосні деренчать, і тихенько шелестять" — confirmed by RAG (Большакова Grade 1 p.24) ✓

**VESUM verification:** All 76 content words confirmed in VESUM. The 6 "not found" items are proper nouns (Дніпро, Львів, Одеса, Полтава, Тарас, Харків) — expected, not errors.

**Gender forms:** рада (adj, f) and радий (adj, m) both confirmed in VESUM ✓

No linguistic errors found.

---

## Exercise Check

### Inventory

| # | Type | Section | Items | Plan match |
|---|------|---------|-------|------------|
| 1 | `:::quiz` | Звуки і літери | 6 questions | ✓ matches plan hint (quiz, 6 items) |
| 2 | `:::match-up` | Перші слова | 6 pairs | ✓ matches plan hint (match-up, 6 items) |
| 3 | `:::group-sort` | Перші слова | 14 items (6+8) | ✓ matches plan hint (group-sort, ≥8 items) |
| 4 | `:::fill-in` | Привіт! | 4 sentences | ✓ matches plan hint (fill-in, 4 items) |
| 5 | `<!-- INJECT_ACTIVITY: quiz-reading-practice -->` | Читаємо | N/A — **unfilled placeholder** | No plan hint for this section |

**All 4 plan activity_hints are covered** with matching types, focus areas, and item counts.

### Exercise Issues

**1. QUIZ: All correct answers at index 0 (CRITICAL)**
Every single question in the quiz has `a: 0` — the correct answer is always the first option. A learner will immediately notice the pattern and just pick the first option without thinking. This completely undermines the exercise's pedagogical value.

```
- q: "Що ми чуємо і вимовляємо?"    → a: 0
- q: "Що ми бачимо і пишемо?"       → a: 0
- q: "Скільки літер в абетці?"       → a: 0
- q: "Скільки звуків..."             → a: 0
- q: "Які звуки утворюються..."      → a: 0
- q: "Які звуки створюють..."        → a: 0
```

**2. Unfilled placeholder in Читаємо section**
`<!-- INJECT_ACTIVITY: quiz-reading-practice -->` was not converted to an exercise. This is a structural artifact that will render as invisible HTML comment — harmless but indicates the writer expected a 5th activity that never materialized. Since no plan hint covers this section, it's minor.

**3. Match-up right-side options are too verbose**
Each right-side option includes the negative hint ("not 'b'", "not 'h'"), which makes the exercise trivially solvable even without knowing the answer — just match the Latin letter in the hint. A learner could solve "В → sounds like [в], not 'b'" by just spotting the 'b' visually without learning anything. However, since this matches the plan's exact specification ("В ↔ [в] (not 'b')"), this is a plan-level issue rather than a writer error.

---

## Scores

| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 9/10 | All 5 content_outline sections present with correct content. Every plan point covered: golden rule quote (§1), both Большакова poems (§1), 6 vowel sounds/10 letters (§1), familiar letters А/О/К/М/Т with words мама/тато/кома/атом/мак/око (§2), dental Т and unaspirated К/Т (§2), all 6 false friends with practice words (§2), new shapes with example words (§2), Щ=[шч] and Ь explanation (§2), Ї/Я/Ю/Є note (§2), Привіт/Як справи/responses (§3), Рада/Радий gender (§3), reading breakdown of Привіт (§3), environmental signs (§4), city names (§4), Це sentences + Що це/Хто це (§4), self-check summary (§5). All 4 activity types match plan hints. Minor deduction: unfilled `<!-- INJECT_ACTIVITY -->` placeholder is a structural artifact. |
| 2. Linguistic accuracy | 10/10 | All Ukrainian verified against VESUM (76/76 words confirmed). Phonetic claims verified against Большакова Grade 1 p.24, Заболотний Grade 5, Litvinova Grade 5, Голуб Grade 5 via RAG. No Russianisms, Surzhyk, calques, or paronyms. Gender forms рада/радий correct. Щ=[шч], Ї=[йі] confirmed by multiple textbook sources. |
| 3. Pedagogical quality | 8/10 | Good PPP flow: presents concept (sounds vs letters) → demonstrates with textbook poems → practices with exercises. Textbook pedagogy well-integrated (Большакова poems, Захарійчук notation mentioned in plan). Each grammar point has 3+ examples. Letters taught through real words immediately (мама, тато, вода). False friends taught with contrastive pairs. Deductions: the "new shapes" paragraph (Б, Г, Ґ...) lists 15 letters but only gives 5 example words — learners see a wall of unfamiliar shapes with insufficient practice. The Я/Ю/Є paragraph says "just try to recognize their shapes" which is vague for a phonetics-focused module. |
| 4. Vocabulary coverage | 10/10 | All 10 required vocab used naturally in prose: мама (§2 "мама (mother)"), тато (§2), вода (§2), рука (§2), книга (§2), школа (§2,§4), привіт (§3), як справи (§3), добре (§3), чудово (§3). All 6 recommended vocab present: банк (§2,§4), аптека (§4), метро (§4), пошта (§4), зупинка (§4), нормально (§3). Words introduced in context, not as bare lists. |
| 5. Exercise quality | 5/10 | **Critical flaw:** Quiz has all 6 correct answers at position 0 — completely gameable. Match-up right-side options contain the Latin letter hint making them trivially solvable by pattern-matching rather than knowledge (though this follows plan spec). Fill-in is well-designed — natural dialogue completion with appropriate blanks. Group-sort is solid with balanced groups. Deduction for unfilled `<!-- INJECT_ACTIVITY -->` placeholder. The quiz tests exactly what was taught (sounds vs letters distinction) ✓, but the answer-position bias destroys validity. |
| 6. Engagement & tone | 6/10 | Multiple instances of meta-commentary flagged by rubric: "Let us look at your very first Ukrainian conversation" (§3¶1), "Let us use the word Привіт! as a reading practice exercise" (§3¶3), "Now you can form your very first actual sentences" (§4¶3). Generic enthusiasm: "Another wonderful phrase to learn right away" (§3¶2). The opening paragraph "Look at the text on this page. What you are seeing right now are letters" is actually a nice concrete opener. The environmental reading framing ("Imagine walking down a street in Ukraine") is good. The dialogue with named speakers (Оленка/Тарас) is natural. But the meta-commentary pattern recurs enough to drag the score down. |
| 7. Structural integrity | 8/10 | All 5 H2 sections present and ordered correctly. Word count 1341 ≥ 1200 target ✓. Clean markdown formatting. Video embed and playlist link present. Deductions: raw `<!-- INJECT_ACTIVITY: quiz-reading-practice -->` placeholder left in output; `<div class="dialogue">` with extra blank lines inside (may render with unwanted spacing). |
| 8. Cultural accuracy | 10/10 | Ukrainian presented entirely on its own terms. No "like Russian but..." comparisons anywhere. Ї described as "unique to the Ukrainian language" — correct and culturally affirming. City names are all Ukrainian cities with Ukrainian spellings. Gendered forms (рада/радий) introduced naturally as a feature of Ukrainian, not as something unusual. |
| 9. Dialogue & conversation quality | 8/10 | Named speakers (Оленка, Тарас) — good. Natural greeting exchange appropriate for A1.1 first-ever dialogue. Culturally appropriate: informal привіт between peers, gender-appropriate names. The dialogue is necessarily simple given this is Module 1, but it flows naturally. Minor deduction: only one dialogue in the entire module; a second mini-dialogue (e.g., using Рада/Радий тебе бачити) would strengthen the section. |

---

## Findings

```
[EXERCISE QUALITY] [SEVERITY: critical]
Location: :::quiz block in "Звуки і літери" section
Issue: All 6 correct answers are at index position 0 (a: 0). Learners will 
immediately detect the pattern and select the first option every time without 
engaging with the question. This is a known anti-pattern that destroys exercise validity.
Fix: Shuffle answer positions so correct answers appear at varied indices (0, 1, 2).
```

```
[ENGAGEMENT & TONE] [SEVERITY: major]
Location: §3 "Привіт!" — paragraph 1: "Let us look at your very first Ukrainian conversation."
Issue: Meta-commentary ("Let us look at...") — rubric explicitly flags this pattern.
Fix: Remove the meta-framing. Start with the content directly.
```

```
[ENGAGEMENT & TONE] [SEVERITY: major]
Location: §3 "Привіт!" — paragraph 3: "Let us use the word Привіт! as a reading practice exercise."
Issue: Meta-commentary ("Let us use...") — tells instead of showing.
Fix: Reframe as action: "Now try reading Привіт! letter by letter."
```

```
[ENGAGEMENT & TONE] [SEVERITY: major]
Location: §4 "Читаємо" — paragraph 3: "Now you can form your very first actual sentences"
Issue: Telling the learner what they can do instead of just doing it.
Fix: Remove the meta-sentence and go straight to the examples.
```

```
[ENGAGEMENT & TONE] [SEVERITY: minor]
Location: §3 "Привіт!" — paragraph 2: "Another wonderful phrase to learn right away"
Issue: Generic enthusiasm — "wonderful" adds nothing specific.
Fix: Replace with a concrete framing.
```

```
[STRUCTURAL INTEGRITY] [SEVERITY: major]
Location: §4 "Читаємо" — `<!-- INJECT_ACTIVITY: quiz-reading-practice -->`
Issue: Unfilled activity placeholder left in raw HTML comment. While invisible to 
readers, it indicates a broken injection and is a build artifact that shouldn't ship.
Fix: Remove the placeholder comment entirely.
```

```
[PEDAGOGICAL QUALITY] [SEVERITY: minor]
Location: §2 "Перші слова" — paragraph 3: "These include Б, Г, Ґ, Д, Ж, З, И, Й, Л, П, Ф, Ц, Ч, Ш, and Щ."
Issue: 15 new letter shapes listed but only 5 example words given (банк, дім, зима, книга, школа). 
The wall of 15 unfamiliar letters with insufficient contextualization may overwhelm an A1.1 learner.
Fix: Not actionable as a content fix — this follows the plan's scope. Minor concern only.
```

```
[STRUCTURAL INTEGRITY] [SEVERITY: minor]
Location: §3 "Привіт!" — `<div class="dialogue">` block
Issue: Extra blank lines inside the div may render with unwanted vertical spacing 
depending on the MDX processor.
Fix: Remove extra blank lines between speaker turns inside the dialogue div.
```

---

## Verdict: REVISE

The module has strong linguistic accuracy (10/10), excellent plan adherence, and solid vocabulary coverage. However, it has one **critical** finding (quiz answer positions all at index 0) that must be fixed before shipping, plus several **major** engagement issues (meta-commentary pattern) and a structural artifact (unfilled placeholder). All issues are fixable with targeted patches — no rewrite needed.

<fixes>
- find: "- q: \"Що ми чуємо і вимовляємо?\"\n  o: [\"звуки\", \"літери\", \"слова\"]\n  a: 0\n- q: \"Що ми бачимо і пишемо?\"\n  o: [\"літери\", \"звуки\", \"речення\"]\n  a: 0\n- q: \"Скільки літер в абетці?\"\n  o: [\"33\", \"38\", \"10\"]\n  a: 0\n- q: \"Скільки звуків в українській мові?\"\n  o: [\"38\", \"33\", \"32\"]\n  a: 0\n- q: \"Які звуки утворюються тільки голосом?\"\n  o: [\"голосні\", \"приголосні\"]\n  a: 0\n- q: \"Які звуки створюють перешкоду в роті?\"\n  o: [\"приголосні\", \"голосні\"]\n  a: 0"
  replace: "- q: \"Що ми чуємо і вимовляємо?\"\n  o: [\"літери\", \"звуки\", \"слова\"]\n  a: 1\n- q: \"Що ми бачимо і пишемо?\"\n  o: [\"літери\", \"звуки\", \"речення\"]\n  a: 0\n- q: \"Скільки літер в абетці?\"\n  o: [\"38\", \"10\", \"33\"]\n  a: 2\n- q: \"Скільки звуків в українській мові?\"\n  o: [\"33\", \"38\", \"32\"]\n  a: 1\n- q: \"Які звуки утворюються тільки голосом?\"\n  o: [\"приголосні\", \"голосні\"]\n  a: 1\n- q: \"Які звуки створюють перешкоду в роті?\"\n  o: [\"приголосні\", \"голосні\"]\n  a: 0"
- find: "Let us look at your very first Ukrainian conversation. The most common informal greeting is"
  replace: "The most common informal greeting is"
- find: "Let us use the word **Привіт!** as a reading practice exercise. We can sound out each letter"
  replace: "Try reading **Привіт!** letter by letter. Sound out each one"
- find: "Now you can form your very first actual sentences using the word **Це** (this is). Look at these simple sentences:"
  replace: "The word **Це** (this is) lets you build simple sentences:"
- find: "Another wonderful phrase to learn right away is \"Glad to see you!\"."
  replace: "One more phrase you will hear often is \"Glad to see you!\"."
- find: "<!-- INJECT_ACTIVITY: quiz-reading-practice -->\n\n"
  replace: ""
- find: "<div class=\"dialogue\">\n\n\n**Оленка:** Привіт! Як справи? *(Hi! How are you?)*\n\n\n**Тарас:** Добре! А у тебе? *(Good! And you?)*\n\n\n**Оленка:** Чудово! *(Great!)*\n\n\n</div>"
  replace: "<div class=\"dialogue\">\n\n**Оленка:** Привіт! Як справи? *(Hi! How are you?)*\n\n**Тарас:** Добре! А у тебе? *(Good! And you?)*\n\n**Оленка:** Чудово! *(Great!)*\n\n</div>"
</fixes>
