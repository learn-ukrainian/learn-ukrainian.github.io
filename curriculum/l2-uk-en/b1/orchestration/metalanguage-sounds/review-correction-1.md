<correction_directive>
CRITICAL: Your previous module was reviewed and scored below 8.0/10.
You must rewrite the module FROM SCRATCH, fixing ALL issues below.
All original constraints from the writing prompt still apply.

- FIX: [Structural integrity] [critical]
  Location: Entire document
  Issue: The word count is massively below the 4000-word target (estimated ~1800-2000 words). The sections are too brief to fulfill the B1-level depth expected for a 4000-word module.
  Fix: Expand every section significantly. Add more examples, deep-dive explanations on how these concepts affect future grammar (e.g., how voiced/voiceless pairs interact in prefixes), and detailed step-by-step walk-throughs for phonetic transcription.
- FIX: [Exercise quality] [critical]
  Location: All `:::` exercise blocks
  Issue: The generated activities completely ignore the `activity_hints` array in the plan. Types, item counts, and focuses are all wrong.
  Fix: Delete the current activities and generate exactly what is in the plan: an 8-item classify quiz, an 8-item term match-up, a 6-item transcription fill-in, a 10-item consonant group-sort, a 6-item mark-the-words for sonorants, and a 6-item error-correction for transcriptions.
- FIX: [Plan adherence] [major]
  Location: Section "Приголосні звуки: дзвінкі та глухі"
  Issue: The plan explicitly required a "Reading practice passage: a short Ukrainian text about sounds, with learners identifying дзвінкі, глухі, and сонорні in context." This is missing.
  Fix: Write the requested short reading passage and integrate it into the section before the activities.
- FIX: [Plan adherence] [major]
  Location: Section "Підсумок: ваш фонетичний словник"
  Issue: The plan explicitly required a "Self-check in Ukrainian: Дайте відповіді на запитання 1-5" and a "Preview of next module: Будова слова". Both are missing.
  Fix: Add the 5 numbered self-check questions and the preview paragraph exactly as requested in the plan outline.
- NOTE: [Linguistic accuracy] [minor]
  Location: Section "Приголосні звуки: тверді та м'які", paragraph starting with "Також приголосні можуть ставати пом'якшеними..."
  Issue: Incorrect phonetic classification. The text claims [с] in "пісня" becomes "пом'якшеним [с']". In Ukrainian phonetics, dental sibilants like [с] have a full soft pair and become completely **м'які** (soft) before another soft dental, not just пом'якшені (half-soft/partially softened).
  Fix: Change the example of a "пом'якшений" consonant. Use a labial, velar, or hushing consonant before [i] (e.g., [б] in "білий", [к] in "кіт", [ж] in "жінка" are пом'якшені). Reserve "пісня" for an example of full assimilation of softness (м'якість).

- FIX (Linguistic): One minor phonetic terminology error found regarding assimilation:
- "У слові «пісня» звук [с] стає пом'якшеним [с'] через те, що наступний звук [н'] є дуже м'яким." -> Звук [с] належить до зубних/свистячих і має повноцінну м'яку пару. Перед м'яким [н'] він стає повністю **м'яким** [с'], а не "пом'якшеним" (напівм'яким). Термін "пом'якшені" стосується губних, шиплячих та задньоязикових (напр. [ж] у "жінка", [б] у "білий"), які не мають справжньої м'якої пари.
</correction_directive>