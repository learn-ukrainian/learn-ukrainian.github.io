<correction_directive>
CRITICAL: Your previous module was reviewed and scored below 8.0/10.
You must rewrite the module FROM SCRATCH, fixing ALL issues below.
All original constraints from the writing prompt still apply.

- FIX: [Structural integrity] [MAJOR]
  Location: Entire Module
  Issue: The module misses the 1200 word count target by a significant margin. For example, "Діалоги" requested 350 words but provides ~180. "Мене звати..." requested 250 words but provides ~200.
  Fix: Expand the sections with more examples, slightly longer dialogues, and deeper explanations of the cultural contexts of introducing oneself in Ukraine to meet the word count targets specified in the plan.
- FIX: [Structural integrity] [MAJOR]
  Location: `### Додаткові слова з уроку — Additional words from the lesson` table
  Issue: The LLM hallucinated literal text snippets as dictionary definitions. "студент" is translated as "I am a student", and "інженер" is translated as "He — engineer".
  Fix: Correct the translations to their base meanings: "студент" -> "student", "інженер" -> "engineer". Ensure the script/LLM generating the table pulls lemmas, not full sentences.
- NOTE: [Exercise quality] [MINOR]
  Location: `:::fill-in` (Introduce yourself)
  Issue: One of the answers contains a stress mark: `answer: "студе́нт"`. Unless the exercise validation engine automatically strips stress marks, learners typing the standard "студент" will be marked wrong.
  Fix: Remove the stress mark from the answer key: `answer: "студент"`.
</correction_directive>