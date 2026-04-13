## Linguistic Scan
- Factual orthography error: `“Lastly, you will see an apostrophe used as a letter.”` `апостроф` is not a letter; SУМ-11 defines it as a sign, and the textbook corpus returns `“Апостроф — це графічний символ...”`

## Exercise Check
- All 5 planned markers are present: `count-syllables`, `match-up`, `odd-one-out`, `divide-words`, `quiz`.
- Placement is mostly correct: each marker comes after the teaching it is meant to test, and the markers are spread through the module rather than clustered at the end.
- No marker-ID mismatch with `activity_hints`.
- The actual YAML exercise content is not included here, so distractor logic / answer-key quality cannot be audited from this artifact.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | Most plan points are covered and all required/recommended vocab appears, but the notation point is reduced to `“the symbol [●] represents a vowel sound”`; `[—]` and `[=]` never appear, and the **Ї** section omits the plan’s positional rule. |
| 2. Linguistic accuracy | 8/10 | Most Ukrainian examples are fine, but `“apostrophe used as a letter”` is factually wrong. |
| 3. Pedagogical quality | 7/10 | The sequence is good (`“sound, to the syllable, to the complete word”`, `“find the vowels: И and А … кни-га”`), but one planned concept is under-taught and the dialogues add weak communicative practice. |
| 4. Vocabulary coverage | 10/10 | Required vocab is all present: `яблуко, молоко, людина, вулиця, столиця, каша, пісня`; recommended `університет, бібліотека, фотографія, шоколад` also appear in prose. |
| 5. Exercise quality | 9/10 | All five planned markers are present and placed after relevant instruction; no visible marker-logic issue in the provided content. |
| 6. Engagement & tone | 9/10 | Mostly teacherly and concrete: `“A common mistake for beginners…”`, `“A practical way to practice reading…”`; no gamified/corporate filler. |
| 7. Structural integrity | 8/10 | All H2 headings are present and the pipeline word count is 1353, but the summary opens with the broken sentence `“To ensure  How do you count…”`. |
| 8. Cultural accuracy | 10/10 | Fully Ukrainian-centered; `“Київ — столиця України”` is correct and there is no Russian-centric framing. |
| 9. Dialogue & conversation quality | 6/10 | The dialogues are named, but `“Це каша? … Це вода.”` and `“Вона там. А тут — університет.”` sound robotic and context-poor. |

## Findings
- [LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: `Читання слів`, final preview paragraph — `“Lastly, you will see an apostrophe used as a letter.”`  
Issue: `апостроф` is not a Ukrainian letter; it is an orthographic/graphic sign marking separate pronunciation.  
Fix: Change `used as a letter` to `used as a graphic sign` and describe its function accordingly.

- [PLAN ADHERENCE] [SEVERITY: major]  
Location: `Склади`, notation paragraph — `“the symbol [●] represents a vowel sound”`  
Issue: The plan requires the full notation set `[●] голосний, [—] твердий приголосний, [=] м'який приголосний`; in the provided content `[●]` appears once, `[—]` appears 0 times, `[=]` appears 0 times.  
Fix: Expand the paragraph to include all three symbols and their meanings.

- [PLAN ADHERENCE] [SEVERITY: major]  
Location: `Голосні літери`, **Ї** paragraph — `“This unique letter ALWAYS makes two sounds: [йі]. It never softens a consonant. You will see it proudly standing in words like Україна.”`  
Issue: The plan explicitly requires the positional rule for **Ї** (`only at word start, after vowel, or after apostrophe`), but that rule is omitted; `after apostrophe` appears 0 times in the provided content.  
Fix: Add the positional rule and one example after an apostrophe.

- [STRUCTURAL INTEGRITY] [SEVERITY: minor]  
Location: `Підсумок — Summary` — `“You have reached the end of this foundational reading lesson. To ensure  How do you count syllables in a Ukrainian word?”`  
Issue: Broken transition / dangling sentence artifact.  
Fix: Replace with a clean self-check transition.

- [DIALOGUE & CONVERSATION QUALITY] [SEVERITY: major]  
Location: `Читання слів`, both dialogue blocks — `“Це каша? … Це вода.”` and `“Вона там. А тут — університет.”`  
Issue: The exchanges are grammatically fine but feel like placeholders rather than natural A1 conversations.  
Fix: Replace them with simple, plausible mini-exchanges that still recycle the target vocabulary.

## Verdict: REVISE
Critical factual error plus multiple major quality issues. The module is close structurally, but it should not ship until the orthography claim, missing plan content, broken summary line, and weak dialogues are fixed.

<fixes>
- find: |
    To help visualize this, the Ukrainian sound notation system uses a specific symbol. According to *Захарійчук Grade 1*, page 15, the symbol [●] represents a vowel sound, known as a **голосний** (vowel). 
  replace: |
    To help visualize this, the Ukrainian sound notation system uses three basic symbols. According to *Захарійчук Grade 1*, page 15, [●] represents a vowel sound (**голосний**), [—] marks a hard consonant (**твердий приголосний**), and [=] marks a soft consonant (**м'який приголосний**). 

- find: |
    The second function of **Я**, **Ю**, and **Є** occurs when they are placed directly after a consonant. In this position, they represent only one vowel sound, but they do something crucial: they soften the preceding consonant. Look at the word **пісня** (song). The **Я** here does not make a "y" sound; instead, it softens the **Н** and then makes a pure "a" sound. Finally, you must meet the letter **Ї**. This unique letter ALWAYS makes two sounds: [йі]. It never softens a consonant. You will see it proudly standing in words like **Україна** (Ukraine).
  replace: |
    The second function of **Я**, **Ю**, and **Є** occurs when they are placed directly after a consonant. In this position, they represent only one vowel sound, but they do something crucial: they soften the preceding consonant. Look at the word **пісня** (song). The **Я** here does not make a "y" sound; instead, it softens the **Н** and then makes a pure "a" sound. Finally, you must meet the letter **Ї**. This unique letter always makes two sounds: [йі]. It never softens a consonant, and you see it only at the start of a word, after a vowel, or after an apostrophe, as in **їжа**, **Україна**, and **під'їзд**.

- find: |
    Lastly, you will see an apostrophe used as a letter. The apostrophe acts as a wall that separates sounds in words like **сім'я** (family), **м'ясо** (meat), and **п'ять** (five). These special characters will be explored fully very soon.
  replace: |
    Lastly, you will see an apostrophe used as a graphic sign. The apostrophe marks separate pronunciation in words like **сім'я** (family), **м'ясо** (meat), and **п'ять** (five). These special characters will be explored fully very soon.

- find: |
    > **Олег:** Це **каша**? *(Is this porridge?)*
    > **Ірина:** Ні, це не **каша**. Це **вода**. *(No, this is not porridge. This is water.)*
  replace: |
    > **Олег:** Це **каша** чи **вода**? *(Is this porridge or water?)*
    > **Ірина:** Це **каша**. **Вода** ось тут. *(This is porridge. The water is right here.)*

- find: |
    > **Марко:** Де **бібліотека**? *(Where is the library?)*
    > **Олена:** Вона там. А тут — **університет**. *(It is there. And here is the university.)*
    > **Марко:** Дякую! *(Thanks!)*
  replace: |
    > **Марко:** Я шукаю **бібліотеку**. Де вона? *(I am looking for the library. Where is it?)*
    > **Олена:** **Бібліотека** там. А **університет** ось тут. *(The library is there. And the university is right here.)*
    > **Марко:** Дякую! *(Thanks!)*

- find: |
    You have reached the end of this foundational reading lesson. To ensure  How do you count syllables in a Ukrainian word?
  replace: |
    You have reached the end of this foundational reading lesson. To check yourself: How do you count syllables in a Ukrainian word?
</fixes>