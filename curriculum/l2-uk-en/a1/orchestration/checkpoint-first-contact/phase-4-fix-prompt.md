Activate skill full-rebuild-core-a.

The file `curriculum/l2-uk-en/a1/checkpoint-first-contact.md` failed the audit.

**Audit Errors:**
1. Checkpoint Format Errors: Missing H3 headers '### Model:', '### Practice:', '### Self-Check' in each Skill section.
2. Outline Compliance Errors: The sections are named '## Skill N: ...' but meta.yaml expects '...'.
3. Metalanguage: Terms like 'рід', 'іменник' used but not in vocabulary.

**Your Task:**
1. Update `curriculum/l2-uk-en/a1/meta/checkpoint-first-contact.yaml` to match the markdown headers:
   - 'Вступ: Читання кирилиці та рід іменників' -> 'Skill 1: Вступ: Читання кирилиці та рід іменників'
   - 'Дієвідмінювання дієслів теперішнього часу' -> 'Skill 2: Дієвідмінювання дієслів теперішнього часу'
   - 'Комунікація: Питальні речення та замовлення в кафе' -> 'Skill 3: Комунікація: Питальні речення та замовлення в кафе'
   
2. Update `curriculum/l2-uk-en/a1/checkpoint-first-contact.md`:
   - Add the required H3 headers (### Model, ### Practice, ### Self-Check) to EACH '## Skill' section. Structure the existing content under these headers.
   - Add the missing metalanguage terms to the vocabulary table.

Use `write_file` or `replace` to apply fixes.
