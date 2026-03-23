<correction_directive>
CRITICAL: Your previous module was reviewed and scored below 8.0/10.
You must rewrite the module FROM SCRATCH, fixing ALL issues below.
All original constraints from the writing prompt still apply.

- FIX: [Cultural accuracy] [MAJOR]
  Location: Section "Сім'я (Family Vocabulary)": "A Grade 1 textbook poem by Марія Братко begins: «В мене дружна є сім'я»"
  Issue: [NEEDS RAG VERIFICATION] This appears to be an LLM hallucination. There is no widely known Ukrainian children's author named "Марія Братко" who wrote this exact poem. Inventing primary sources violates the project's strict anti-hallucination rules.
  Fix: Remove the reference to the specific author and poem. Rewrite to state a factual observation: "You will often see **сім'я** used in children's books and everyday speech."
- FIX: [Pedagogical quality] [MAJOR]
  Location: Section "Діалоги (Dialogues)", quiz items: `q: "У Марка є сестра?"` and `q: "Марко з Києва. У нього є..."`
  Issue: The text explicitly defers the Genitive case (у нього, у неї) to A2, but uses it in the quiz prompts. A1.1 learners do not know that "Марка" is the genitive of "Марко", nor do they know "нього".
  Fix: Rewrite the quiz questions to avoid the genitive case. Example: `q: "Марко каже: «У мене є...»"` or `q: "Брат Марка — це..."` (if testing possessives) or `q: "Хто є на фото?"`.
- NOTE: [Exercise quality] [MINOR]
  Location: Section "У мене є (I have)", fill-in exercise: `sentence: "У тебе є ___?" answer: "брат"`
  Issue: The blank is too open-ended. A learner could logically fill in "сестра", "мама", "діти", etc.
  Fix: Add context to constrain the answer. Example: `sentence: "У тебе є ___ чи сестра?" answer: "брат"`.
- NOTE: [Structural integrity] [MINOR]
  Location: Section `<!-- TAB:Словник -->`, table row: `| **мати** | more formal or literary; **тато** is everyday, **батько** is formal | ім. | ж. |`
  Issue: Instructional prose has been dumped directly into the "Translation" column of the generated vocabulary table, breaking the data structure.
  Fix: Change the translation cell to simply: `mother (formal/literary)`. Move pedagogical explanations back to the main prose if necessary.
</correction_directive>