I now have all the verification data I need. Let me compile the full adversarial review.

---

## Linguistic Scan

**Russianisms:** None found. "Сім" correctly identified as Ukrainian (not "сем"). All number words verified against VESUM.

**Surzhyk:** None found.

**Calques:** None found.

**Paronyms:** None found.

**Russian characters (ы, э, ё, ъ):** None found.

**Factual/attribution errors found:**

1. **Counting rhyme misattribution.** The module states: "A counting rhyme from Kravcova (Grade 2, p. 92)." RAG search confirms the rhyme is by **Леся Вознюк**, published IN Kravcova's textbook (Grade 2, p. 92). Kravcova is the textbook author, not the rhyme's author. This is a factual attribution error.

2. **Phone number group format error in Summary.** The module states: "Read Ukrainian mobile numbers in groups of 3–2–2–2." But the format shown throughout the module is 0XX-XXX-XX-XX, which is **3–3–2–2** (10 digits total). "3–2–2–2" = 9 digits, which is wrong.

3. **гривна description slightly imprecise** (minor). The module says: "the currency word is **гривня**, not **гривна** — that is a different word meaning a neck ornament." VESUM confirms both exist as separate lemmas. However, **гривна** historically also refers to the monetary unit of Kyivan Rus (not only a neck ornament). For A1 purposes, the core message (use гривня for modern currency) is correct, but the claim about гривна is incomplete. Minor — acceptable simplification at A1.

**All other Ukrainian forms verified correct.** VESUM-verified: гривня/гривні/гривень ✓, all numbers 1–1000 ✓, коштує ✓, копійка ✓, стільці ✓, зошитів ✓, покупець ✓, пекар ✓, йому ✓, їй ✓, старша ✓, продиктуйте ✓. VESUM "not found" words are all accounted for: Тарас/Тарасе (proper nouns), двасто/чотиридесят/шістьнадцять (correctly cited as WRONG forms), дев'/сот (tokenizer splits of apostrophe words), українськи (part of hyphenated adverb по-українськи).

**Stress claims verified:** Textbooks confirm stress on -на- in numbers 11–19 (Захарійчук Grade 4 p.111: "У числівниках від одинадцяти до дев'ятнадцяти наголошується склад -на-"; Литвинова Grade 6 p.223; Вашуленко Grade 3 p.140). ✓

**Etymology claim verified:** Голуб Grade 6 p.161 confirms сорок origin from bundle of forty pelts: "мішок, зв'язку із сорока білячих або соболиних шкурок." ✓

## Exercise Check

**Marker inventory:**
| Marker | Location | Matches plan hint |
|--------|----------|-------------------|
| `<!-- INJECT_ACTIVITY: quiz-age -->` | After Dialogues section | ✓ quiz: ages (6 items) |
| `<!-- INJECT_ACTIVITY: fill-in-numbers -->` | After Numbers 1-20 | ✓ fill-in: numbers in words (10 items) |
| `<!-- INJECT_ACTIVITY: quiz-prices -->` | After Tens and Hundreds | ✓ quiz: prices (8 items) |
| `<!-- INJECT_ACTIVITY: fill-in-phone -->` | After Tens and Hundreds | ✓ fill-in: phone dictation (4 items) |

**Issues:**
- 4 markers for 4 activity hints — count matches ✓
- Each marker appears AFTER the relevant teaching content ✓
- Minor clustering: `quiz-prices` and `fill-in-phone` are both in the "Десятки і сотні" section. The phone marker ideally should follow the phone number paragraph specifically, which it does (it's after the phone explanation). Acceptable.
- `quiz-age` is well-placed after both age dialogue and the explanation of рік/роки/років ✓

## Scores

| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | **Covered:** All 4 content_outline sections present with correct headings. Numbers 1–20 ✓, tens/hundreds ✓, prices ✓, age formula ✓, phone numbers ✓. Vashulenko and Голуб textbook references integrated. All required and recommended vocabulary present. **Deductions:** (a) Dialogue 2 deviates from plan — plan specifies ages "двадцять п'ять" (25), "тридцять два" (32), "вісімнадцять" (18) to practice compound numbers in conversational context; content uses ages 14, 13, 18, 11 (all teen/simple numbers), missing the opportunity to demonstrate tens+units in dialogue. (b) Plan's dialogue_situation 2 (school backpack counting: "один олівець, дві ручки, п'ять зошитів") not implemented as a dialogue — school items appear only as counting examples in prose, not in a conversational Учень/Мама exchange. |
| 2. Linguistic accuracy | 9/10 | All Ukrainian forms VESUM-verified. Number forms correct (двісті, триста, п'ятсот). Gender agreement correct (одне тістечко — neuter, одна гривня — feminine). Case forms correct (п'ять гривень — genitive plural). Stress claims confirmed by 3 textbook sources. шістнадцять spelling rule correct. **Deduction:** Counting rhyme misattributed to Kravcova (textbook editor) instead of Леся Вознюк (actual author). Phone format error: "3–2–2–2" should be "3–3–2–2." |
| 3. Pedagogical quality | 9/10 | Excellent PPP flow: dialogues introduce numbers in situation (bakery, age), then systematic teaching, then summary practice. 5+ examples per number group. Counting rhyme is excellent authentic pedagogy. "Memorize as chunks, grammar in A2" approach is sound for A1. Textbook references (Vashulenko Grade 3, Голуб Grade 6) strengthen credibility. **Minor deduction:** Compound numbers (двадцять п'ять, тридцять два) first appear only in prose examples, not in dialogue — the plan's PPP design had them in dialogue first. |
| 4. Vocabulary coverage | 10/10 | All 8 required vocabulary groups present and used in context: один–десять ✓, двадцять/тридцять/сорок ✓, сто/тисяча ✓, скільки ✓, коштує ✓, гривня ✓, рік/роки/років ✓. All 6 recommended items present: п'ятдесят–сімдесят ✓, вісімдесят/дев'яносто ✓, двісті/триста/п'ятсот ✓, копійка ✓ ("дев'яносто дві копійки"), номер ✓ ("Мій номер"), нуль ✓. Words introduced in natural contexts, never as bare lists. |
| 5. Exercise quality | 9/10 | 4 markers matching all 4 plan activity_hints by type and focus. Each marker placed after relevant teaching. Age quiz tests language (dative pronoun + number + рік/роки/років pattern), not content recall. Price quiz tests Скільки коштує? answers. Phone dictation is practical production. **Minor:** Two markers in same section, but content justifies it. |
| 6. Engagement & tone | 9/10 | No LLM filler detected. No "Let us explore," no "incredibly," no motivational openers. Concrete throughout: real bakery prices (15₴, 45₴, 200₴), real phone number format, the Вознюк counting rhyme. Named dialogue speakers with distinct teen voices (Оленка, Тарас). Summary self-check is practical ("Say your age," "Dictate your phone number"). **Minor:** "This module built three number systems" in Summary is slightly meta — could be more natural. |
| 7. Structural integrity | 10/10 | All 4 H2 headings match plan exactly: Діалоги ✓, Числа 1-20 ✓, Десятки і сотні ✓, Підсумок ✓. Word count 1338 > 1200 target ✓. Clean markdown, no stray tags, no duplicate sections. Activity markers properly formatted. |
| 8. Cultural accuracy | 10/10 | Decolonized — "сім" explicitly contrasted with Russian ghost form "сем" without framing Ukrainian as derivative. Etymology of сорок presented from Ukrainian textbook (Голуб), grounded in Ukrainian trade history. Гривня correctly distinguished from гривна. Phone number format is specifically Ukrainian (0XX-XXX-XX-XX). No "like Russian but..." anywhere. |
| 9. Dialogue & conversation quality | 8/10 | Bakery dialogue is natural: multi-turn, named speakers (Покупець/Пекар), escalating complexity (торт → хліб → три булочки → одне тістечко), ends with natural farewell. Age dialogue has named teen speakers (Оленка/Тарас), extends to family members (sister, brother), uses vocative "Тарасе." **Deductions:** (a) Age dialogue uses only simple teen numbers — misses plan's compound-number practice (25, 32). (b) School backpack dialogue entirely absent — the Учень/Мама exchange from plan's dialogue_situation 2 would have added a third conversational scenario with counting objects. |

## Findings

**[LINGUISTIC ACCURACY] [MAJOR]**
Location: Numbers 1-20 section, paragraph 2: "A counting rhyme from Kravcova (Grade 2, p. 92)"
Issue: The counting rhyme «Один і два — росла трава...» is by **Леся Вознюк**, published in Kravcova's textbook. Attributing it to Kravcova misidentifies the author.
Fix: Change "from Kravcova (Grade 2, p. 92)" to "by Леся Вознюк (Kravcova, Grade 2, p. 92)"

**[LINGUISTIC ACCURACY] [CRITICAL]**
Location: Summary section, paragraph on phone numbers: "Read Ukrainian mobile numbers in groups of 3–2–2–2."
Issue: The format 0XX-XXX-XX-XX has groups of 3–3–2–2 (10 digits). "3–2–2–2" = 9 digits, which is factually wrong. Learners will misread phone numbers.
Fix: Change "3–2–2–2" to "3–3–2–2"

**[PLAN ADHERENCE / DIALOGUE QUALITY] [MAJOR]**
Location: Dialogue 2 (age dialogue)
Issue: Plan's content_outline specifies ages двадцять п'ять (25), тридцять два (32), вісімнадцять (18) — designed to practice compound numbers in conversational context before formal teaching. Content uses ages 14, 13, 18, 11 — all simple teen numbers. Compound numbers (tens + units) appear only in later prose, never in dialogue. The plan's PPP design (expose in situation first → teach formally) is undermined.
Fix: Revise dialogue to include at least one compound number (e.g., change one speaker's age to двадцять п'ять or тридцять два). See `<fixes>` block below for specific replacement.

**[PLAN ADHERENCE] [MINOR]**
Location: Dialogues section (missing)
Issue: Plan's dialogue_situation 2 (school backpack — Учень/Мама counting ручка, олівець, зошит, підручник) not implemented as a dialogue. School items appear as counting examples in prose ("один стіл, два стільці, три книги, чотири ручки, п'ять зошитів") but not in conversational format.
Fix: Not requiring a fix at this time — the content_outline's two dialogues are both present, and the school items are covered in prose. The dialogue_situation was aspirational. Minor plan gap.

## Verdict: REVISE

Two findings require fixes: the phone number format error is **critical** (teaches wrong information), and the counting rhyme misattribution is **major** (factual error). The dialogue age deviation is **major** but can be addressed with a targeted fix to bring compound numbers into the conversation. All three are fixable with minimal find/replace edits.

<fixes>
- find: "A counting rhyme from Kravcova (Grade 2, p. 92) puts numbers 1–7 into context:"
  replace: "A counting rhyme by Леся Вознюк (in Kravcova, Grade 2, p. 92) puts numbers 1–7 into context:"
- find: "Read Ukrainian mobile numbers in groups of 3–2–2–2."
  replace: "Read Ukrainian mobile numbers in groups of 3–3–2–2."
- find: "<div class=\"dialogue-line\"><span class=\"speaker\">Оленка:</span> Привіт, Тарасе! Скільки тобі років? *(Hi, Taras! How old are you?)*</div>\n\n<div class=\"dialogue-line\"><span class=\"speaker\">Тарас:</span> Мені чотирнадцять. А тобі? *(I'm fourteen. And you?)*</div>\n\n<div class=\"dialogue-line\"><span class=\"speaker\">Оленка:</span> Мені тринадцять. А твоя сестра старша? *(I'm thirteen. Is your sister older?)*</div>\n\n<div class=\"dialogue-line\"><span class=\"speaker\">Тарас:</span> Так, їй вісімнадцять. *(Yes, she's eighteen.)*</div>\n\n<div class=\"dialogue-line\"><span class=\"speaker\">Оленка:</span> А твій брат? *(And your brother?)*</div>\n\n<div class=\"dialogue-line\"><span class=\"speaker\">Тарас:</span> Йому одинадцять. *(He's eleven.)*</div>"
  replace: "<div class=\"dialogue-line\"><span class=\"speaker\">Оленка:</span> Привіт, Тарасе! Скільки тобі років? *(Hi, Taras! How old are you?)*</div>\n\n<div class=\"dialogue-line\"><span class=\"speaker\">Тарас:</span> Мені двадцять п'ять. А тобі? *(I'm twenty-five. And you?)*</div>\n\n<div class=\"dialogue-line\"><span class=\"speaker\">Оленка:</span> Мені тридцять два. А твоя сестра молодша? *(I'm thirty-two. Is your sister younger?)*</div>\n\n<div class=\"dialogue-line\"><span class=\"speaker\">Тарас:</span> Так, їй вісімнадцять. *(Yes, she's eighteen.)*</div>\n\n<div class=\"dialogue-line\"><span class=\"speaker\">Оленка:</span> А твій брат? *(And your brother?)*</div>\n\n<div class=\"dialogue-line\"><span class=\"speaker\">Тарас:</span> Йому одинадцять. *(He's eleven.)*</div>"
- find: "The age formula in Ukrainian works like a fixed chunk: **Мені** (I am), **тобі** (you are), **йому** (he is), **їй** (she is) + a number + **років**. Ukrainian uses three different words for \"year(s)\" depending on the number: **рік** (year) after 1, **роки** (years) after 2–4, and **років** (years) after 5 and above. At A1, memorize these as a pattern — one **рік**, two **роки**, five **років**. No case analysis needed."
  replace: "The age formula in Ukrainian works like a fixed chunk: **Мені** (I am), **тобі** (you are), **йому** (he is), **їй** (she is) + a number + **років**. Ukrainian uses three different words for \"year(s)\" depending on the number: **рік** (year) after 1, **роки** (years) after 2–4, and **років** (years) after 5 and above. At A1, memorize these as a pattern — one **рік**, twenty-two **роки**, five **років**. Notice in the dialogue: **двадцять п'ять** (25) and **тридцять два** (32) — these combined numbers are just the tens word plus the unit, with no connector. No case analysis needed."
- find: "**Мені чотирнадцять років** (14), **Йому двадцять два роки** (22), **Їй тридцять п'ять років** (35)."
  replace: "**Мені двадцять п'ять років** (25), **Йому двадцять два роки** (22), **Їй тридцять п'ять років** (35)."
</fixes>
