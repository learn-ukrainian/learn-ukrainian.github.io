## Linguistic Scan

**Russianisms:** None found. All Ukrainian vocabulary verified against VESUM (86/86 core words confirmed).

**Surzhyk:** None found.

**Calques:** None found.

**Paronyms:** None found.

**Russian characters (ы, э, ё, ъ):** None found.

**Factual claims verified:**
- Правопис 2019 §26 confirms Ь after д, т, з, с, дз, ц, л, н (end of word/syllable) and after д, т, з, с, дз, ц, л, н **та р** before о mid-word — module correctly presents this, including Р's special status.
- Правопис 2019 §7 confirms apostrophe after б, п, в, м, ф, р before я, ю, є, ї — module correctly states this rule with attribution to Захарійчук.
- Правопис 2019 §26 explicitly lists "ларьо́к" as a standard example of Р+Ь+О, confirming the module's usage despite VESUM not containing it.
- Літвінова Grade 5 p.126 (confirmed via textbook RAG) uses the mnemonic «ДЗіДЗьо, Де Ти З'їСи Ці ЛиНи» for exactly the consonants listed.
- Заболотний Grade 10 confirms: "Дзвінкі приголосні переважно не оглушуються" with exception list including легко [лехко] — module correctly presents non-devoicing.
- Karaman Grade 10 classification confirms сонорні (М, Н, В, Л, Р, Й) as a separate group from шумні дзвінкі/глухі — module's presentation is correct.
- Voiced-voiceless 8-pair table matches standard textbook classification (Karaman Grade 10, Golub Grade 5).
- Г as глотковий [ɦ] fricative, Ґ as задньоязиковий [g] stop — matches Karaman Grade 10 classification. Module correctly warns against calling Г "soft."
- VESUM confirms: ґрати = noun (ґрата, plural); грати = verb — minimal pair is accurate.

**No linguistic errors found.**

## Exercise Check

7 activity injection markers found, matching all 7 plan `activity_hints`:

| Plan hint | Marker ID | After section | Correct placement |
|-----------|-----------|---------------|-------------------|
| odd-one-out (М'який знак) | `odd-one-out` | М'який знак | ✅ |
| fill-in (Апостроф) | `fill-in-soft-or-apostrophe` | Апостроф | ✅ |
| error-correction (Апостроф) | `error-correction-apostrophe` | Апостроф | ✅ |
| group-sort (Апостроф) | `group-sort-soft-apostrophe` | Апостроф | ✅ |
| match-up (Дзвінкі і глухі) | `match-voiced-voiceless` | Дзвінкі і глухі | ✅ |
| true-false (Дзвінкі і глухі) | `true-false-voicing` | Дзвінкі і глухі | ✅ |
| quiz (Вимова) | `quiz-g-vs-gx` | Вимова | ✅ |

All markers placed after relevant teaching sections. Distribution is even — 1 in section 1, 3 in section 2 (matching the plan's 3 apostrophe activities), 2 in section 3, 1 in section 4. No clustering issues.

## Scores

| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 9/10 | All 5 content_outline sections present with correct ordering. Three-way consonant distinction (м'які/пом'якшені/тверді) covered per plan with Авраменко Grade 5 and Большакова Grade 2 citations. Mnemonic «ДЗіДЗьо, Де Ти З'їСи Ці ЛиНи» attributed to Літвінова Grade 5 as planned. Apostrophe rule (б,п,в,м,ф,р + я,ю,є,ї) from Захарійчук Grade 1 p.97 — cited and demonstrated. All 8 voiced-voiceless pairs listed. И/І minimal pairs from plan present (бик-бік, дим-дім, лист-ліс, кит-кіт). Г vs Ґ phonetic description matches plan exactly. Self-check covers all plan questions. All 7 activities placed. Підсумок section slightly under its 200-word sub-target but total module at 1472 (target 1200) is 23% over — well within bounds. All plan references cited in text. |
| 2. Linguistic accuracy | 10/10 | All Ukrainian words VESUM-verified. Правопис 2019 §26 confirms Ь rules as presented. §7 confirms apostrophe rule. Phonetic descriptions of Г [ɦ] (fricative) vs Ґ [g] (stop) match Karaman Grade 10 classification. Non-devoicing rule ("дуб = [дуб]") confirmed by Заболотний Grade 10: "дзвінкі приголосні переважно не оглушуються." Exception "легко [лехко]" correctly presented. Three-way consonant classification matches textbooks. No Russianisms, no Surzhyk, no calques, no paronyms, no Russian characters. |
| 3. Pedagogical quality | 9/10 | Strong PPP flow: each section introduces concept → demonstrates with examples → provides practice markers. Multiple examples per concept: Ь section has 4 pattern groups (-нь, -ль, -ть, -зь) with 3+ words each. Apostrophe section walks through 6 examples with phonetic breakdowns (сім'я → М hard + й + а). Voiced/voiceless section uses experiential "hand on throat" technique from textbook pedagogy. И/І section has 4 minimal pairs drilled explicitly. Mnemonic provided for Ь consonants. The "say Х then add voice" instruction for Г is a concrete articulation exercise. Grammar scope respects A1 (correctly defers prefix apostrophe rule to A2). |
| 4. Vocabulary coverage | 10/10 | All 7 required vocab words appear naturally in prose: сім'я (apostrophe section, 3 occurrences), день (Ь section, 2 occurrences), сіль (Ь section, 2 occurrences), м'ясо (apostrophe section, 3 occurrences), п'ять (apostrophe section, 3 occurrences), гарно (Г section + summary), риба (Р section + summary). All 5 recommended words used: батько (Ь section), учитель (Ь section), дев'ять (apostrophe section), комп'ютер (apostrophe section), м'який (apostrophe section with correct note about no Ь). Words introduced in context, never as bare lists. |
| 5. Exercise quality | 9/10 | All 7 plan activity hints have corresponding markers. Types match exactly (odd-one-out, fill-in, error-correction, group-sort, match-up, true-false, quiz). Each marker appears after the relevant teaching content. Item counts in plan hints respected. Activity IDs are descriptive and match their pedagogical focus. Cannot evaluate distractor quality since activities are YAML-generated externally, but marker logic and placement are correct. |
| 6. Engagement & tone | 9/10 | Opens with a specific hook: "Now meet a letter that breaks that rule: Ь." Uses concrete experiential teaching: "Place your fingers lightly on your throat. Say з — you feel vibration." Punchy phrasing: "One letter, one job, zero sounds." Cultural identity noted naturally: "Ґ is an important part of Ukrainian phonetic identity." No motivational filler, no "Let us now explore," no "incredibly melodic." The :::caution blocks serve genuine disambiguation purpose (non-devoicing, Г≠"soft"). Minimal meta-commentary — "Walk through the core examples" is the only borderline instance. |
| 7. Structural integrity | 10/10 | All 5 H2 sections present and correctly ordered (М'який знак → Апостроф → Дзвінкі і глухі → Вимова → Підсумок). Clean markdown with proper :::tip, :::note, :::caution blocks. Table formatting correct. No duplicate summaries. No stray tags or formatting artifacts. Word count 1472 vs 1200 target — 23% over, well within bounds. H3 subsections (И vs І, Г vs Ґ, Р) logically organized within Вимова. |
| 8. Cultural accuracy | 10/10 | "Ґ is uniquely Ukrainian — an important part of Ukrainian phonetic identity." Ukrainian sounds presented on their own terms: "И sits in a mid-tongue position" — no "like English X." Non-devoicing presented as "a defining Ukrainian feature," not as "unlike Russian." Г explicitly not called "soft" with explanation of Ukrainian phonetic terminology. No "like Russian but..." framing anywhere. Module consistently presents Ukrainian phonetics as a self-contained system. |
| 9. Dialogue quality | 8/10 | No formal dialogues present. This is a phonetics module focused on sound system mechanics — the plan contains no dialogue hints or conversation activities. The self-check Q&A in Підсумок provides interactive engagement. The module could theoretically include a short pronunciation practice dialogue (two speakers drilling minimal pairs), which would strengthen this dimension, but its absence is plan-appropriate and not an error. |

## Findings

No critical or major findings.

[STRUCTURAL] [minor]
Location: Підсумок section — "Four new pieces of the Ukrainian sound system..." through "...ґудзик."
Issue: Section runs approximately 170-180 words against a 200-word sub-target (~10-15% under). The Q&A format is pedagogically effective but slightly thin on synthesis prose before the self-check questions.
Fix: Could add 1-2 sentences bridging the sound system overview to the self-check (e.g., reinforcing how these four pieces connect to reading fluency). However, total module word count is 1472 (23% over 1200 target), making this a non-blocking observation.

## Verdict: PASS

**Justification:** Zero linguistic errors found — all Ukrainian forms, phonetic claims, and grammatical descriptions verified against Правопис 2019, VESUM, and Grade 1-10 textbook sources via RAG. All 9 dimensions score ≥8, with 7 of 9 at ≥9. The single dimension below 9 (Dialogue, 8/10) reflects the inherent nature of a phonetics module rather than any quality deficiency — the plan contains no dialogue activities and the module type doesn't naturally accommodate conversation practice. All plan content points covered with textbook citations. All 7 activity markers correctly placed. All required and recommended vocabulary used in context. Word count exceeds target by 23%. The module teaches Ukrainian phonetics on its own terms with accurate, textbook-grounded pedagogy and zero decolonization issues.
