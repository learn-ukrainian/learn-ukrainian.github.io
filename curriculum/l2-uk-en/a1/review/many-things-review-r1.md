Now I have all the data I need. Let me compile the full review.

## Linguistic Scan

**Russianisms:** None found. All vocabulary is native Ukrainian.
**Surzhyk:** None found.
**Calques:** None found.
**Paronyms:** None found.
**Russian characters (ы, э, ё, ъ):** None found.

All 110 Ukrainian word forms verified against VESUM — every plural form, adjective form, demonstrative, and possessive is correct. Specific verifications:
- Noun plurals: столи←стіл ✓, книги←книга ✓, вікна←вікно ✓, стільці←стілець ✓, олівці←олівець ✓, речі←річ ✓ (all confirmed nominative plural)
- Adjective plurals: великі←великий ✓, нові←новий ✓, старі←старий ✓, чисті←чистий ✓, червоні←червоний ✓, сині←синій ✓ (all confirmed)
- Demonstratives/possessives: ці←цей ✓, ті←той ✓, мої←мій ✓

**One pedagogical concern (not a linguistic error):** "Скільки зошитів?" introduces genitive plural (зошитів), which is an untaught case form. The plan deliberately avoided this by writing "Скільки?" without the noun. This isn't wrong Ukrainian — it's natural and correct — but it exposes A1 learners to a form they can't yet parse. The transition paragraph correctly only discusses the nominative form (зошити), which makes the unexplained зошитів a loose end.

**Grammar claims verified:**
- "ALL adjectives take -і in the plural" — correct for nominative plural ✓
- "після г, к, х → -и" guideline — correctly hedged as guideline, not rule ✓
- "Neuter -о → -а" pattern — correct ✓
- річ → речі described as non-standard — fair characterization for A1 (consonant alternation і→е) ✓
- Textbook citations: Большакова Grade 2 p.18 (однина/множина) confirmed via RAG ✓; Большакова Grade 2 p.42 (який/яка/яке → які, веселий→веселі) confirmed via RAG ✓

No linguistic errors found.

## Exercise Check

**Activity markers found (4):**
1. `<!-- INJECT_ACTIVITY: fill-in-plural -->` — after Один → багато section ✓
2. `<!-- INJECT_ACTIVITY: fill-in-adj-plural -->` — in Прикметники section ✓
3. `<!-- INJECT_ACTIVITY: quiz-plural-adj -->` — in Прикметники section ⚠️
4. `<!-- INJECT_ACTIVITY: group-sort-singular-plural -->` — in Підсумок section ✓

**Plan activity_hints (4):**
1. fill-in (noun plurals, 10 items) → matched by `fill-in-plural` ✓
2. quiz (choose correct noun plural, 8 items) → should be matched by a noun-focused quiz, but `quiz-plural-adj` is named and placed as if testing adjective plurals ⚠️
3. fill-in (adj agreement, 8 items) → matched by `fill-in-adj-plural` ✓
4. group-sort (singular vs plural, 12 items) → matched by `group-sort-singular-plural` ✓

**Issue:** Plan hint 2 is a quiz about **noun** plurals ("Choose the correct plural: стіл → столи/стола/столів?"). The marker `quiz-plural-adj` is named as if it tests adjective plurals and is placed after the adjective section. The activity generator uses marker IDs as hints — this name could produce adjective quiz items instead of the plan's intended noun plural quiz. The marker should be renamed to `quiz-plural-nouns` and ideally placed after the noun section for immediate reinforcement, though post-adjective placement is defensible as spaced recall.

**Marker spread:** Even — one per major section. ✓
**Placement logic:** Each marker follows its teaching content. ✓ (with the quiz caveat above)

## Scores

| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 9/10 | All 4 content_outline sections present with correct structure. Dialogue 1 matches plan almost verbatim (Що тут є? Столи, стільці і вікна...). Dialogue 2 captures the supply-shopping scenario. Большакова p.18 and p.42 references correctly integrated. All vocabulary_hints (required + recommended) present in prose. Minor deductions: (a) plan specifies Вчитель/Учні speakers but content uses Олена/Іван — the classroom setup setting is preserved but the teacher-student dynamic is lost; (b) "Скільки зошитів?" adds genitive plural not in plan's dialogue script; (c) quiz marker named for adjectives instead of nouns per plan hint 2. Word count 1459 vs 1200 target — comfortably above. |
| 2. Linguistic accuracy | 10/10 | All 110 Ukrainian word forms VESUM-verified. Plural formations correct: стіл→столи, книга→книги, вікно→вікна, стілець→стільці, олівець→олівці all confirmed. Adjective plural rule (always -і) is correct for nominative. Demonstrative forms ці←цей, ті←той confirmed. Fleeting vowel description (стілець→стільці) is accurate. No Russianisms, no Surzhyk, no calques, no paronyms. Gender assignments correct throughout. |
| 3. Pedagogical quality | 9/10 | Excellent PPP flow: dialogues present plurals in context (Presentation), tables + explanations systematize the patterns (Practice setup), self-check + writing prompt provide Practice/Production. Each grammar point has 5+ examples. Textbook pedagogy followed — Большакова's "один предмет → багато предметів" approach reproduced faithfully. Tables organize patterns clearly by gender. The caveat about exceptions ("learn each plural alongside its singular") is honest and appropriate. Minor deduction: "Скільки зошитів?" casually exposes learners to genitive plural without explanation, which could confuse careful learners at A1. |
| 4. Vocabulary coverage | 10/10 | All 8 required vocab items used naturally in prose: столи (Dialogue 1), книги (Section 2 table), вікна (Dialogue 1 + tables), стільці (Dialogue 1), ці/ті/мої (Section 3 examples), які (Dialogue 1). All 7 recommended items present: ручки (Dialogue 2), сумки (Section 2 table), лампи (Section 2 table), зошити (Dialogue 2), дзеркала (Section 2 table), крісла (Section 2 table), речі (Section 2 + Підсумок). Every word introduced in context, not as isolated lists. |
| 5. Exercise quality | 9/10 | 4 markers for 4 plan hints — count matches. Placement is logical: fill-in after noun teaching, fill-in after adjective teaching, group-sort in summary. Markers are spread evenly (one per section). Minor deduction: `quiz-plural-adj` marker name mismatches plan hint 2's intent (noun plurals, not adjective plurals), risking wrong exercise generation. |
| 6. Engagement & tone | 9/10 | No motivational openers, no gamified language, no "Let us explore..." meta-commentary. Direct, specific instruction: "Notice what just happened" is genuine pedagogical pointing, not filler. Dialogues have a real scenario (classroom setup), named speakers with distinct roles (Олена organizing, Іван asking). "Try it yourself: look around your room" is a natural bridge to production. The writing prompt "Write 3–4 sentences about your own room" with a model answer is excellent scaffolding. One borderline phrase: "The elegant economy here is worth appreciating" — slightly literary for A1 prose, but it makes a specific point about one-ending simplification. |
| 7. Structural integrity | 10/10 | All 4 H2 sections from plan present in correct order. Clean markdown throughout. No duplicate summaries, no meta-commentary sections, no stray tags. Word count 1459 vs 1200 target — 22% above, well within range. Activity markers properly formatted as HTML comments. Tables render correctly. |
| 8. Cultural accuracy | 10/10 | Ukrainian presented entirely on its own terms. No "like Russian but..." or "similar to English..." comparisons. Grammar terminology uses Ukrainian categories (однина/множина, not "singular/plural" as primary). Textbook references are Ukrainian pedagogical sources (Большакова, Вашуленко). No decolonization concerns. |
| 9. Dialogue & conversation quality | 9/10 | Two multi-turn dialogues with named speakers (Олена, Іван). Real situation: setting up a classroom, counting supplies. Natural exchanges — not interrogation-style. Dialogue 2 has genuine back-and-forth (asking about pen colors, adding notebooks, asking about pencils). Dialogue 1 is slightly more transactional (Q&A about what's in the room) but appropriate for introducing plural vocabulary. Both dialogues serve the grammar point without feeling forced. Minor: plan specified Вчитель/Учні which would add a teacher-student dynamic; Олена/Іван are peers, which is fine but loses that pedagogical framing. |

## Findings

**[Exercise quality] [MAJOR]**
Location: `<!-- INJECT_ACTIVITY: quiz-plural-adj -->` in Прикметники section
Issue: Plan activity_hint 2 specifies a quiz about **noun** plural choice ("Choose the correct plural: стіл → столи/стола/столів?"). The marker is named `quiz-plural-adj` (suggesting adjective focus) and placed after the adjective section. The activity generator uses marker IDs as content hints — this name could produce adjective items instead of the plan's intended noun plural quiz.
Fix: Rename marker to `quiz-plural-nouns` and move it to after the Один → багато section.

**[Plan adherence] [MINOR]**
Location: Dialogue 2 — `Скільки зошитів?`
Issue: The plan's dialogue script deliberately writes "Скільки?" (without the noun) to avoid exposing A1 learners to genitive plural. The content adds "зошитів" (genitive plural of зошит), introducing a case form not yet taught. While natural Ukrainian, this creates a loose end — learners see зошитів vs зошити without explanation.
Fix: Change "Скільки зошитів?" to "Скільки?" to match plan and avoid untaught case form.

**[Engagement & tone] [MINOR]**
Location: Підсумок section — "The elegant economy here is worth appreciating: plural adjectives have one form."
Issue: Slightly literary register for A1 prose. "Elegant economy" is the kind of phrasing a linguistics professor would use, not a language teacher addressing beginners.
Fix: Simplify to something more direct.

## Verdict: REVISE

Two actionable findings: one major (exercise marker mismatch with plan), one minor with pedagogical impact (untaught genitive form in dialogue). All dimensions ≥ 9, but the exercise marker naming could cause wrong exercise generation downstream — worth fixing now.

<fixes>
- find: "quiz-plural-adj"
  replace: "quiz-plural-nouns"
- find: "Скільки зошитів? *(How many notebooks?)*"
  replace: "Скільки? *(How many?)*"
- find: "The elegant economy here is worth appreciating: plural adjectives have one form."
  replace: "This is worth remembering: plural adjectives have one form."
</fixes>
