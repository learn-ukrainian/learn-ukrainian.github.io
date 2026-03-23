<correction_directive>
CRITICAL: Your previous module was reviewed and scored below 8.0/10.
You must rewrite the module FROM SCRATCH, fixing ALL issues below.
All original constraints from the writing prompt still apply.

- FIX: [2. Linguistic accuracy] [Major]
  Location: Throughout the text, especially in "Діало́ги (Dialogues)" (e.g., "У тебе́ є бра́ти чи сестри́?", "у мене́ є", "йо́го зва́ти", "Катя́").
  Issue: The writer manually inserted stress marks, which violates the pipeline process, and placed them entirely incorrectly. This teaches factually wrong pronunciation (e.g., "бра́ти" is the verb 'to take', the noun plural is "брати́"; pronouns shift stress after prepositions to "у ме́не", "у те́бе").
  Fix: Remove all manual stress marks (`´`) from the entire markdown text. Let the downstream deterministic tool handle stress annotation.
- FIX: [2. Linguistic accuracy] [Major]
  Location: Section "У мене є (I have)" — "Ukrainian does not use a verb meaning 'to have.' Instead, possession works like this..."
  Issue: Factually incorrect claim. Ukrainian does have a verb meaning "to have" («мати»: я маю, ти маєш). Claiming it doesn't exist is a linguistic hallucination.
  Fix: Change the sentence to: "Instead of a verb like 'to have', Ukrainian usually expresses possession like this..." or "Ukrainian most commonly expresses possession without the verb 'to have'."
- NOTE: [7. Structural integrity] [Minor]
  Location: Bottom of the file (`<!-- TAB:Словник -->`, `<!-- TAB:Зошит -->`, `<!-- TAB:Ресурси -->`).
  Issue: Writer generated the vocabulary tables, workbook placeholders, and resource links manually. These are injected by the pipeline's downstream `generate_mdx.py` script and will cause duplicates.
  Fix: Delete everything from `<!-- TAB:Словник -->` to the end of the document. Keep only the core module content (`<!-- TAB:Урок -->`).

- FIX (Linguistic): Linguistic errors found:
1. **Phonetic Hallucinations (Incorrect Stress)**: The writer manually inserted stress marks (`´`), violating the instruction that stress is handled downstream. Worse, almost all manual stress marks are factually incorrect and teach wrong pronunciation:
   - `у мене́` → prep shifts stress, should be `у ме́не`.
   - `У тебе́` → prep shifts stress, should be `у те́бе`.
   - `йо́го` → should be `його́`.
   - `Катя́` → should be `Ка́тя`.
   - `бра́ти` (nominative plural) → s
</correction_directive>