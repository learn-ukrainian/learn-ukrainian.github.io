## Linguistic Scan
No linguistic errors found.

## Exercise Check
Four activity markers are present, and their placement is correct.

`order-112-call` comes after the two model dialogues. `quiz-emergency-phrases` and `fill-in-emergency-call` come after the emergency-phrase teaching in `Екстрені ситуації`. `fill-in-reporting-issue` comes after the hospital/police language in `Допомога`. The IDs match the four `activity_hints`, and the markers are spread sensibly through the module. No exercise issues found in the prose-visible layer.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 9/10 | All planned H2 sections appear in order: `Dialogues`, `Екстрені ситуації`, `Допомога`, `Summary`. Core plan points are covered with concrete language such as `Допоможіть! Тут аварія!`, `Мені потрібен лікар.`, and `Я загубив паспорт.` |
| 2. Linguistic accuracy | 10/10 | No Russianisms, Surzhyk, calques, paronym errors, or bad case/gender forms were found. Forms such as `загубив/загубила`, `Мені потрібен лікар`, `У мене алергія на антибіотики`, and `Залишайтеся на місці` are standard Ukrainian. |
| 3. Pedagogical quality | 6/10 | The lesson spends a long English-only block before the first Ukrainian example: `Emergencies happen unexpectedly in any country... Read the following situations.` It also adds metalanguage beyond the plan scope: `Use the formal, plural **наказовий спосіб**...` and `...in the **називний відмінок**...` instead of keeping these as A1 chunks. |
| 4. Vocabulary coverage | 9/10 | Required vocabulary is well covered in context: `допоможіть`, `швидка`, `поліція`, `лікарня`, `аварія`, `загубити`, `викликати`. Recommended items such as `пожежа`, `паспорт`, `адреса`, `алергія`, `форма`, and `будинок` also appear naturally in prose and dialogue. |
| 5. Exercise quality | 9/10 | Four markers are present and well placed: `order-112-call`, `quiz-emergency-phrases`, `fill-in-emergency-call`, `fill-in-reporting-issue`. They align with the four `activity_hints` and test the material after it is taught. |
| 6. Engagement & tone | 8/10 | The module is practical and calm overall, but the opener is generic and explanatory rather than teacher-direct: `Emergencies happen unexpectedly in any country...` delays the first useful Ukrainian input. |
| 7. Structural integrity | 10/10 | All planned sections are present, marker comments are clean, and the pipeline word count is `1720`, safely above the `1200` target. |
| 8. Cultural accuracy | 10/10 | The module frames emergency Ukrainian on Ukrainian terms, with no Russia-centered comparisons. The `112` description matches current MVS guidance that treats 112 as a nationwide single emergency number ([MVS, 18 Feb 2026](https://mvs.gov.ua/news/specprojekt-mvs-112-jedinii-nomer-bezpeki-dlia-vsijeyi-krayini), [MVS project page](https://mvs.gov.ua/ministry/projekti-mvs/informatizaciya-sistemi-mvs-ukrayini/sistema-112-ukrayini)). |
| 9. Dialogue & conversation quality | 9/10 | The first call is a believable multi-turn emergency exchange with named speakers and good sequencing: problem, location, then personal details. The second dialogue is simpler but still functional and context-appropriate. |

## Findings
[ENGAGEMENT & TONE] [SEVERITY: major]  
Location: `Emergencies happen unexpectedly in any country. In high-stress moments, clear and direct communication is your most valuable tool. ... Read the following situations.`  
Issue: The module opens with a long generic English preface before any Ukrainian input. This slows the PPP presentation and spends words on filler instead of immediate survival language.  
Fix: Replace the paragraph with a short, task-focused lead-in.

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: `When disaster strikes, you must alert people immediately. Use the formal, plural **наказовий спосіб** (imperative mood) to call for help. Do not worry about grammar rules here; simply memorize these phrases as unchangeable chunks.`  
Issue: The plan frames emergency imperatives as ready-made chunks. Introducing `наказовий спосіб` adds unnecessary grammar metalanguage for an A1 survival module.  
Fix: Replace the paragraph with chunk-based wording and remove the grammar term.

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: `To describe pain, Ukrainian uses a completely different structure than English. You do not say "I have a headache". Instead, you use the fixed structure **у мене болить** (at me it aches), followed by the body part in the **називний відмінок** (nominative case).`  
Issue: `називний відмінок` is unnecessary grammar jargon here and conflicts with the plan’s `chunk, no grammar analysis` approach for emergency language.  
Fix: Replace the explanation with a simple chunk instruction.

## Verdict: REVISE
REVISE because there are major pedagogical findings, and `Pedagogical quality` and `Engagement & tone` are below 9. The Ukrainian itself is clean, but the lesson needs tighter A1 delivery and less grammar metalanguage before it should ship.

<fixes>
- find: "Emergencies happen unexpectedly in any country. In high-stress moments, clear and direct communication is your most valuable tool. You do not need perfect grammar or complex sentences during a crisis. You only need to know specific, formulaic phrases to get immediate assistance. Ukrainian emergency operators are trained to ask simple questions. Your goal is to provide fast, accurate answers without hesitation. We focus on the essential vocabulary for survival in Ukraine. You will learn to state the problem clearly, give your exact location, and provide your personal details. Read the following situations."
  replace: "In an emergency, short phrases matter more than perfect grammar. Learn how to state the problem, give your location, and give your personal details in Ukrainian."
- find: "When disaster strikes, you must alert people immediately. Use the formal, plural **наказовий спосіб** (imperative mood) to call for help. Do not worry about grammar rules here; simply memorize these phrases as unchangeable chunks."
  replace: "When disaster strikes, call for help immediately. Learn these phrases as ready-made chunks and use them exactly as you hear them."
- find: "To describe pain, Ukrainian uses a completely different structure than English. You do not say \"I have a headache\". Instead, you use the fixed structure **у мене болить** (at me it aches), followed by the body part in the **називний відмінок** (nominative case)."
  replace: "To describe pain, use the fixed structure **у мене болить**. Then add the body part after it."
</fixes>