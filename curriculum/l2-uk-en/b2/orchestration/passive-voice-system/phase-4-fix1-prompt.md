Activate skill full-rebuild-core-b.

The module audit failed with the following errors:

1. **Schema Violation**:
   `[YAML_SCHEMA_VIOLATION] Schema error in passive-voice-system.yaml: Schema validation error at key 'words': ['закрито', 'ремонт', 'на', 'магазин', 'тимчасово'] is too short`.
   The `unjumble` activity requires at least 6 words per sentence.
   **Action**: Edit `curriculum/l2-uk-en/b2/activities/passive-voice-system.yaml` to expand this sentence to 6+ words (e.g. "Цей магазин тимчасово закрито на ремонт").

2. **Transliteration**:
   `AUDIT FAILED: Transliteration detected: 'стану (voice)'. Remove Latin in parentheses.`
   **Action**: Remove `(voice)` from `curriculum/l2-uk-en/b2/passive-voice-system.md`. Check for and remove other Latin transliterations in parentheses.

3. **Richness (Dialogues)**:
   Richness is 92% (target 95%). The main gap is **Dialogues** (2 found, target 4).
   **Action**: Write 2 new short dialogues (in Ukrainian) demonstrating Passive Voice usage in different registers (e.g. one Official/Bureaucratic using -но/-то, one Colloquial using 3rd person plural).
   Append these dialogues to appropriate sections in `curriculum/l2-uk-en/b2/passive-voice-system.md` (e.g. at the end of "Форма 2" and "Форма 4").
   Format them as:
   `> **Person A**: ...`
   `> **Person B**: ...`

Use `read_file` to locate the issues, then `replace` or `write_file` to fix them.
