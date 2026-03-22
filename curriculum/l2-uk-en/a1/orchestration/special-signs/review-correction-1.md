<correction_directive>
CRITICAL: Your previous module was reviewed and scored below 8.0/10.
You must rewrite the module FROM SCRATCH, fixing ALL issues below.
All original constraints from the writing prompt still apply.

- FIX: [Dimension 5] [SEVERITY: major]
  Location: Exercise block `:::fill-in` "Ь чи апостроф?", specifically: `- sentence: "батьк___вщина"` `answer: "батьківщина"`
  Issue: The exercise prompt asks learners to choose between Ь or an apostrophe, but the gap is placed where the vowel `і` belongs. If the intention was to test the soft sign, the gap is in the wrong place.
  Fix: Change the gap to test the soft sign correctly: `- sentence: "бат___ківщина"` `answer: "батьківщина"` OR replace the word entirely with an easier A1 word like `пальто`.
- FIX: [Dimension 1] [SEVERITY: major]
  Location: Entire exercise section (`:::fill-in`, `:::match-up`, `:::quiz`)
  Issue: The generated activities violate the strict `activity_hints` prescribed in the plan. The plan asked for 4 specific exercises (Quiz 8 items, Match-up 8 items, Fill-in 6 items, Quiz 4 items). The generator created 5 exercises, replaced the first quiz with a fill-in, and hallucinated an extra quiz.
  Fix: Delete the unprompted `:::fill-in` ("Де потрібен Ь?") and `:::quiz` ("Дзвінкий чи глухий?"). Generate the missing 8-item `:::quiz` focusing on "Does this word have a soft sign, apostrophe, or neither?" exactly as specified in the plan.
- NOTE: [Dimension 2] [SEVERITY: minor]
  Location: Section 1 (М'яки́й знак) paragraph 1: "...Ukrainian distinguishes between **тверді** (hard) and **м'якшені** (softened) consonants..."
  Issue: The plan explicitly references Большакова Grade 1: "Тверді і пом'якшені приголосні звуки." The text uses the non-standard variant "м'якшені" instead of the standard "пом'якшені".
  Fix: Change "**м'якшені**" to "**пом'якшені**".
</correction_directive>