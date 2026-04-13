## Linguistic Scan
- [CRITICAL] **Граматика (Grammar Summary)**: `Always remember the rule of euphony (милозвучність). We use **у** before a word starting with a consonant, and **в** before a word starting with a vowel...` teaches a false rule. The choice depends on surrounding sounds, not only the initial letter of the next word; the module’s own examples `у понеділок` and `в суботу` already contradict the stated rule.

## Exercise Check
- 3 markers are present and correctly distributed: `fill-in-day-description` after the reading section, `fill-in-time-weather-chunks` after grammar, and `match-up-logical-answers` after the dialogue.
- Marker count matches the 3 `activity_hints` in the plan.
- Marker placement is logical: each marker comes after the relevant teaching block.
- No marker-placement issues found.
- Exercise logic of the injected YAML cannot be checked here because only the markers are visible in the manuscript.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 6/10 | All five planned H2 sections are present, but section pacing is far off the plan: `Що ми знаємо?` is about 286 words vs 200 planned, `Читання` about 343 vs 250, `Граматика` about 361 vs 200, and `Діалог` about 347 vs 300. The planned frequency item `рідко` is also absent from the prose (exact-text search: 0 hits). |
| 2. Linguistic accuracy | 7/10 | The grammar tip states `We use **у** before a word starting with a consonant, and **в** before a word starting with a vowel`, which is factually wrong and contradicted by the module’s own examples `у понеділок` and `в суботу`. |
| 3. Pedagogical quality | 6/10 | The checkpoint spends too much space on English meta-commentary instead of concise review/practice, e.g. `This text is an excellent example of how you can build a narrative` and `This dialogue represents real, functional fluency at the A1 level.` That weakens checkpoint pacing and crowds out the core review function. |
| 4. Vocabulary coverage | 8/10 | Core A1.4 vocabulary appears naturally across the prose, but the planned frequency set is incomplete: the module lists `завжди`, `часто`, `іноді`, `ніколи` and omits `рідко`. |
| 5. Exercise quality | 9/10 | The three activity markers align with the three plan hints and appear after the relevant teaching sections. Distribution is even across the module. |
| 6. Engagement & tone | 7/10 | The tone slips into hype/filler: `Welcome to the A1.4 checkpoint!` and especially `Celebrate this milestone! 4 phase of your Ukrainian learning journey.` The latter is also broken English. |
| 7. Structural integrity | 8/10 | All H2 headings are present and the pipeline word count is 1624, but the self-check ends with a dangling fragment: `If you can understand and answer these questions,` |
| 8. Cultural accuracy | 9/10 | No Russia-centered framing or cultural misinformation found; Ukrainian is presented on its own terms. |
| 9. Dialogue & conversation quality | 9/10 | The dialogue has named speakers, a plausible planning situation, and natural A1 chunks such as `Ходімо в парк!`, `О десятій ранку`, and `А потім ходімо в кіно!` |

## Findings
[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: **Граматика (Grammar Summary)** — `Always remember the rule of euphony (милозвучність). We use **у** before a word starting with a consonant, and **в** before a word starting with a vowel, to make speaking smoother and more natural.`  
Issue: This teaches a false rule of милозвучність. The choice is not determined only by the first letter of the following word; the module itself immediately gives `у понеділок` and `в суботу`, both before consonants.  
Fix: Replace the tip with a correct explanation that `у/в` are chosen for euphony according to surrounding sounds, with examples.

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: Multiple sections — `Welcome to the A1.4 checkpoint!...`, `This text is an excellent example of how you can build a narrative.`, `This dialogue represents real, functional fluency at the A1 level.`  
Issue: The checkpoint is padded with English meta-commentary and motivational filler instead of concise review and practice. This also pushes 4 of 5 sections over their planned word budgets by more than 10%.  
Fix: Compress the English framing paragraphs and keep only short instructions plus the core Ukrainian examples.

[VOCABULARY COVERAGE] [SEVERITY: major]  
Location: **Граматика (Grammar Summary)** — frequency list  
Issue: The plan’s frequency set includes `рідко`, but exact-text search confirms 0 occurrences in the module. One planned review item is missing.  
Fix: Add `* **рідко** (rarely)` to the frequency list.

[STRUCTURAL INTEGRITY] [SEVERITY: major]  
Location: End of **Що ми знаємо?** — `If you can understand and answer these questions,`  
Issue: Dangling incomplete sentence.  
Fix: Complete the sentence or delete it.

[ENGAGEMENT & TONE] [SEVERITY: minor]  
Location: **Підсумок — Summary** — `Celebrate this milestone! 4 phase of your Ukrainian learning journey.`  
Issue: Self-congratulatory opener plus broken English (`4 phase`) weakens the teacherly tone.  
Fix: Replace it with a neutral, grammatical transition.

## Verdict: REVISE
Critical factual grammar error plus several major plan/pedagogy/structure issues. Multiple dimensions are below 9, so this cannot pass as written.

<fixes>
- find: "Welcome to the A1.4 checkpoint! Over the past few modules, you have built a solid foundation for talking about the world around you. You have learned how to tell time, navigate the calendar, describe the weather, outline your daily routine, and talk about your hobbies. When you learn a new language, it is easy to memorize individual words. The real challenge—and the real reward—comes when you start combining those words into meaningful sentences. This checkpoint is your opportunity to bring all these separate pieces together. Our goal is to consolidate this knowledge so you can build coherent stories and engage in natural conversations about your day-to-day life. Before we move on to the next phase of your Ukrainian language journey, we will review and practice these essential skills."
  replace: "This checkpoint reviews the main patterns from A1.4: time, calendar, weather, daily routine, and hobbies. Use it to check whether you can combine these chunks into clear, simple Ukrainian."
- find: "If you can understand and answer these questions, "
  replace: "If you can understand and answer these questions, you are ready for the checkpoint practice below."
- find: "Now, let's put these concepts into practice with a short reading exercise. In the text below, Oksana is talking about her typical week. She describes her work schedule, her favorite seasons, and how her hobbies change depending on the weather outside. Notice how she uses time expressions, days of the week, and weather vocabulary to tell a complete story. Reading this text aloud will also help you practice the rhythm and intonation of Ukrainian sentences.\n\nRead the text slowly and pay attention to the highlighted words."
  replace: "Read the short text about Oksana's week. Notice the time expressions, days, seasons, and weather words."
- find: "This text is an excellent example of how you can build a narrative. Oksana starts with an introduction, describes her routine, connects her activities to the weather, and finishes by asking a question to keep the conversation going.\n\nAfter reading Oksana's story, try to answer these questions to test your comprehension. You can answer in English or try using simple Ukrainian phrases.\n* What are Oksana's working hours on Monday and Wednesday?\n* What does she do on Tuesday?\n* What is the weather like in autumn?\n* What does she do when it snows and is cold outside?\n* What question does she ask you at the end?\n\nThis short text shows how you can use basic vocabulary to describe a full and interesting life."
  replace: "Oksana links schedule, weather, and hobbies in one short story. Answer these questions in English or simple Ukrainian.\n* What are Oksana's working hours on Monday and Wednesday?\n* What does she do on Tuesday?\n* What is the weather like in autumn?\n* What does she do when it snows and is cold outside?\n* What question does she ask you at the end?"
- find: "You now have the necessary tools to accurately locate events in time using specific prepositions and case endings. Let's review the key patterns you have learned in this phase. These structures are the building blocks of daily conversation.\n\nFirst, let's look at how to tell time and name days. When you want to know the current time, you use the nominative case. When you want to say *at* what time something happens, you use the locative case with the preposition **о** (at) or **об** (before vowels)."
  replace: "Here is a quick review of the key A1.4 patterns.\n\nTo ask the time, use **Котра година?** To ask when something happens, use **О котрій годині?**"
- find: "For days of the week, we use the preposition **у** (in/on) or **в** (in/on) followed by the accusative case. Remember that **у** and **в** mean the same thing; we choose between them to make the sentence sound melodic and easy to pronounce."
  replace: "For days of the week, use **у/в** + accusative. We choose **у** or **в** for euphony depending on the surrounding sounds."
- find: "Let's look at more examples with months to see how they are used in a full sentence:"
  replace: "More examples:"
- find: "Always remember the rule of euphony (милозвучність). We use **у** before a word starting with a consonant, and **в** before a word starting with a vowel, to make speaking smoother and more natural."
  replace: "Always remember the rule of euphony (милозвучність). We choose **у** or **в** according to the surrounding sounds, so both forms are possible: **у понеділок**, **в суботу**, **у січні**, **в серпні**."
- find: "Finally, let's review weather, sequence, and frequency. To describe the weather, we use impersonal adverbs or simple verbs."
  replace: "Weather, sequence, and frequency also stay simple at A1."
- find: "* **завжди** (always)\n* **часто** (often)\n* **іноді** (sometimes)\n* **ніколи** (never)"
  replace: "* **завжди** (always)\n* **часто** (often)\n* **іноді** (sometimes)\n* **рідко** (rarely)\n* **ніколи** (never)"
- find: "Now it is time to see all these elements working together in a natural conversation. Two friends, Andriy and Olena, are planning a weekend outing. They need to discuss the weather forecast, agree on an activity, and set a specific time to meet. Pay attention to how they use time chunks and weather words. This type of conversation is very common in Ukraine. Friends often make plans based on the weather, especially in the spring and summer."
  replace: "Now read a short dialogue that combines weather, time, and weekend plans. Notice how the speakers set a time and add a second activity."
- find: "Let's break down this conversation. Notice how naturally the speakers combined different concepts into a single, flowing exchange. Olena describes the weather using simple adverbs: **тепло і сонячно** (warm and sunny). Andriy invites her using a direct command: **Ходімо в парк!** (Let's go to the park!).\n\nWhen setting the schedule, they use locative time chunks. Andriy asks **О котрій?** (At what time?), and Olena replies with **О десятій ранку** (At ten in the morning). Notice how they don't use full, complete sentences for every reply. Just like in English, Ukrainian speakers use short, efficient phrases in conversation. Instead of repeating the whole sentence, they just state the time.\n\nAndriy confirms the plan using a frequency word and a day of the week: **Я часто гуляю в суботу** (I often walk on Saturday). Finally, Olena uses a sequence word to add another activity: **А потім ходімо в кіно!** (And then let's go to the cinema!).\n\nThis dialogue represents real, functional fluency at the A1 level. You don't need complex sentences to make plans and discuss your day; you just need to link these basic chunks together."
  replace: "This dialogue combines weather, invitations, time, a day of the week, and a sequence word in a natural A1 exchange. Notice the short replies: **О котрій?**, **О десятій ранку**, **А потім ходімо в кіно!**"
- find: "Celebrate this milestone! 4 phase of your Ukrainian learning journey."
  replace: "This checkpoint completes A1.4 of your Ukrainian learning journey."
</fixes>