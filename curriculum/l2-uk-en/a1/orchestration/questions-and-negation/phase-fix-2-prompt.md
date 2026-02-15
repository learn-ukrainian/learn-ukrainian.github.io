# Fix Prompt 2: Boost Immersion

You are the Yellow Team builder.
Audit Status: Immersion 9.9% (Target 15-35%).
Goal: Increase Ukrainian content by ~200 words.

## Instructions
1. **Summary Section**: Rewrite the "Summary" section to be **50% Ukrainian**.
   - Use simple Ukrainian sentences for the recap points.
   - Provide English translation in parentheses.
   - Example: "**Ми вивчили слово 'Чи'.** (We learned the word 'Чи'.)"

2. **Cultural Context Section**:
   - Rewrite the first two paragraphs of "The Politeness Scale" and "The Alien Who Taught Us" to include more Ukrainian terms and short sentences.
   - Add a mini-dialogue between Alf and a Cat (3-4 lines) in Ukrainian.

3. **General**:
   - Scan the "Theory" section. Find 5 English sentences that are simple enough to be translated to Ukrainian. Translate them.

4. **Execution**:
   - Read `curriculum/l2-uk-en/a1/questions-and-negation.md`.
   - Use `write_file` to OVERWRITE the file with the boosted version.
   - Ensure IPA is preserved.
   - Run `scripts/audit_module.sh` to verify.
