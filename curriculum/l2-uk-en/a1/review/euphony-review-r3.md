## Linguistic Scan
- `## У чи В?`: “At the very start of a sentence, you must always use **У**…” is false. The repo textbook corpus gives sentence-start `в` before a vowel: `В Одесі тепло.`
- Same paragraph: “The exact same exception applies after a heavy pause or a comma…” is also false as stated. After a pause, the choice still depends on the following sound.
- `## І чи Й?`: “Furthermore, **і** is always used at the absolute beginning of a sentence.” is false. The repo textbook corpus gives sentence-start `й` before a vowel: `Й учимося грамотно писати.`
- Same subsection: “you must use … **й** when the conjunction is placed immediately between two vowels” is too narrow and contradicted by the module’s own example `Вона й він.` Textbook evidence also allows `й` after a vowel before a consonant.

## Exercise Check
- `quiz-u-or-v` appears after `## У чи В?`
- `quiz-i-or-y` and `fill-in-z-iz-zi` appear after `## І чи Й? З, із, чи зі?`
- `quiz-euphony-comparison` appears after `## Підсумок — Summary`
- Marker count and placement match the 4 `activity_hints`, and they are distributed through the module rather than dumped at the end.
- No marker-placement issues found. Exercise logic itself is not inspectable here because only injection markers are present.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 9/10 | All planned H2 sections are present and in order, and plan examples/vocab recur in prose: `в Києві`, `у Львові`, `в офісі`, `в парк`, `у театр`, `з Одеси`, `Максим із Семеном`, `зі мною`. |
| 2. Linguistic accuracy | 4/10 | The module states “you must always use **У**” and “**і** is always used at the absolute beginning of a sentence,” but the repo textbook corpus gives sentence-start `В Одесі тепло` and `Й учимося грамотно писати`; `Вона й він` also contradicts the module’s own “between two vowels” rule. |
| 3. Pedagogical quality | 6/10 | The opening spends a long English theory paragraph before the first Ukrainian example: “The Ukrainian language is famous for its musical quality…”; later explanations are overprescriptive (`at all costs`, `must always`) instead of teaching euphony as a sound-based choice. |
| 4. Vocabulary coverage | 10/10 | Required alternants `у/в`, `і/й`, `з/із/зі` are taught in context, and recommended vocab `Київ`, `Львів`, `офіс`, `парк`, `театр` all appear naturally in prose/examples. |
| 5. Exercise quality | 9/10 | Four markers match the four plan hints and are placed after the relevant teaching blocks: `quiz-u-or-v`, `quiz-i-or-y`, `fill-in-z-iz-zi`, `quiz-euphony-comparison`. |
| 6. Engagement & tone | 7/10 | There is teacher voice, but phrases such as “famous for its musical quality,” “key to sounding like a native speaker,” and “perfectly aligning with Ukrainian euphony” add hype more than instruction. |
| 7. Structural integrity | 10/10 | All planned H2 headings are present and ordered correctly; pipeline word count is 1548, above the 1200 target. |
| 8. Cultural accuracy | 10/10 | The module explains Ukrainian on its own terms and does not lean on Russian comparison or colonial framing. |
| 9. Dialogue & conversation quality | 8/10 | Speakers are named and the exchanges are multi-turn (`Де ти живеш?...`, `Ти й Олена йдете...`), though the dialogues are brief. |

## Findings
[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: `## У чи В?` — “At the very start of a sentence, you must always use **У**… The exact same exception applies after a heavy pause or a comma…”  
Issue: This teaches a false absolute rule. The repo textbook corpus distinguishes sentence-start/post-pause `у` before a consonant from `в` before a vowel (`В Одесі тепло`).  
Fix: Replace the “always У” explanation with a sound-based rule for sentence start and pause position.

[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: `## І чи Й? З, із, чи зі?` — “Furthermore, **і** is always used at the absolute beginning of a sentence.”  
Issue: This is false. The repo textbook corpus gives sentence-start `й` before a vowel (`Й учимося грамотно писати`).  
Fix: Replace the absolute claim with a sound-based sentence-start rule.

[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: `## І чи Й? З, із, чи зі?` — “Conversely, you must use the short consonant glide **й** when the conjunction is placed immediately between two vowels.”  
Issue: The rule is too narrow and is contradicted by the module’s own example `Вона й він.` Textbook evidence also allows `й` after a vowel before a consonant.  
Fix: Rewrite the rule so `й` is presented as common after a vowel, especially between vowels and also before many consonants.

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: `## Діалоги (Dialogues)` — opening paragraph beginning “The Ukrainian language is famous for its musical quality…”  
Issue: The module front-loads a long block of English theory before the first Ukrainian example, which weakens PPP flow and adds filler.  
Fix: Replace the opening with a shorter introduction that moves learners into the examples immediately.

## Verdict: REVISE
Critical linguistic findings are present, so this cannot pass. Dimensions 2, 3, and 6 are below 9, and the false absolute rules about sentence-initial/post-pause alternation would teach learners the wrong generalization.

<fixes>
- find: |
    The Ukrainian language is famous for its musical quality, a defining feature formally known as **милозвучність** (euphony, or "sweet-soundingness"). This concept is not an optional stylistic choice, a poetic flourish, or a suggestion for advanced learners. It is a strict grammatical foundation designed to make the spoken language flow naturally and effortlessly. Ukrainian actively avoids harsh clashes of multiple consonants or awkward sequences of multiple vowels. Instead of forcing the speaker to stumble over difficult sound combinations, the language itself changes the shapes of its prepositions and conjunctions to maintain a continuous, smooth rhythm. Learning these rules is the key to sounding like a native speaker.
  replace: |
    Ukrainian uses **милозвучність** (euphony) to avoid awkward sound combinations. Speakers often choose between **у/в**, **і/й**, and **з/із/зі** so that a phrase is easier to pronounce aloud. These alternations are common and important, but the best test is not a rigid formula: it is whether the sentence sounds smooth when you say it.
- find: |
    At the very start of a sentence, you must always use **У**, regardless of the sound that follows it. For example, you always say **У мене є...** (I have...) or **У понеділок...** (On Monday...). The exact same exception applies after a heavy pause or a comma in a sentence: **Так, у нас є...** (Yes, we have...).
  replace: |
    At the very start of a sentence or after a pause, the choice still depends on the next sound. **У** is common before a consonant: **У мене є...** (I have...). **В** is common before a vowel: **В Одесі тепло.** Some clusters still strongly prefer **у**, as in **у Львові**.
- find: |
    Furthermore, **і** is always used at the absolute beginning of a sentence.
  replace: |
    At the absolute beginning of a sentence, **і** is common before a consonant, while **й** is also possible before a vowel.
- find: |
    Conversely, you must use the short consonant glide **й** when the conjunction is placed immediately between two vowels. If you used the full **і** in this specific environment, you would create a noticeable pause or glottal stop in the middle of your sentence, which sounds incredibly robotic and unnatural in Ukrainian speech. The **й** creates a seamless, fluid glide from one vowel to the next.
  replace: |
    Conversely, **й** is common after a vowel, especially between vowels (**Олена й Андрій**) and often before a consonant (**мама й тато**, **вона й він**). This short glide keeps the phrase moving smoothly from one word to the next.
</fixes>