Activate skill full-rebuild-core-b.

The module audit failed with the following errors:

1. **Schema Violation**:
   `[YAML_SCHEMA_VIOLATION] Schema error in passive-voice-system.yaml: Schema validation error at key 'words': ['всі', 'були', 'вчасно', 'виправлені', 'помилки'] is too short`.
   The `unjumble` activity requires at least 6 words per sentence.
   **Action**: Edit `curriculum/l2-uk-en/b2/activities/passive-voice-system.yaml`.
   - Find the item with `['всі', 'були', 'вчасно', 'виправлені', 'помилки']` and expand it to 6+ words (e.g. add adjectives or conjunctions).
   - **CRITICAL**: Scan ALL other items in the `unjumble` activity. If any have fewer than 6 words, expand them immediately. Every item must have ≥6 words.

2. **Richness (Dialogues)**:
   Richness is 92% (target 95%). Dialogues count is 2 (target 4). You need 2 MORE dialogues.
   **Action**: Write 2 new short dialogues (in Ukrainian) and append them to `curriculum/l2-uk-en/b2/passive-voice-system.md`:
   - **Dialogue 3** (Literary/Descriptive): Two people discussing a painting or a room (using Passive Participles -ний/-тий). Add to "Форма 1".
   - **Dialogue 4** (Technical/Process): Describing how a device works or a house is built (using Reflexive Passive -ся). Add to "Форма 3".
   
   Format:
   `> **Person A**: ...`
   `> **Person B**: ...`

Use `read_file` to locate the files, then `replace` or `write_file` to apply fixes.
