# Vocabulary Enrichment Skill

Expert knowledge for Ukrainian vocabulary enrichment pipeline.

## What is Vocabulary Enrichment?

Vocabulary enrichment adds linguistic metadata to minimal vocabulary entries:

### Input (minimal entry)
```yaml
- lemma: їсти
  translation: to eat
  pos: verb
```

### Output (enriched entry)
```yaml
- lemma: їсти
  ipa: ˈjisˌtɪ
  translation: to eat
  pos: verb
  aspect: imperfective
  pair: з'їсти
  note: replaces Russianism "кушать"
  gender: null
```

## Enrichment Pipeline

### 1. Manual Enrichment (espeak-ng)
```bash
npm run vocab:enrich l2-uk-en [moduleNum]
```

Adds:
- IPA pronunciation (espeak-ng)
- Gender for nouns
- Aspect for verbs
- Usage notes

### 2. Global Vocabulary Rebuild
```bash
npm run vocab:rebuild
```

Rebuilds `curriculum/l2-uk-en/vocabulary.db` from all enriched YAML files.

### 3. Validation
```bash
.venv/bin/python scripts/global_vocab_audit.py --level [level]
```

Checks:
- No duplicate lemmas within level
- IPA present for all entries
- Gender present for nouns
- Aspect present for verbs

## Vocabulary File Structure

### A1-B1 (Embedded in Module)
Vocabulary table in module markdown:
```markdown
# Vocabulary

| Word | IPA | English | POS | Gender | Note |
|------|-----|---------|-----|--------|------|
| слово | ˈslɔwɔ | word | noun | n | neutral gender |
```

### B2+ (Separate YAML)
Vocabulary in `{level}/vocabulary/{slug}.yaml`:
```yaml
vocabulary:
  - lemma: слово
    ipa: ˈslɔwɔ
    translation: word
    pos: noun
    gender: n
    note: neutral gender
```

## Enrichment Workflow

### For New Module
1. Create module with vocabulary table/YAML
2. Run enrichment: `npm run vocab:enrich l2-uk-en {level} {moduleNum}`
3. Review enriched entries
4. Rebuild database: `npm run vocab:rebuild`
5. Validate: `npm run test:vocab`

### For Vocabulary Updates
1. Edit YAML file
2. Add new entries (minimal: lemma, translation, pos)
3. Run enrichment on that file:
   ```bash
   .venv/bin/python scripts/enrich_yaml_vocab.py curriculum/l2-uk-en/{level}/vocabulary/{slug}.yaml
   ```
4. Rebuild database
5. Validate

## Vocabulary Database

**Location**: `curriculum/l2-uk-en/vocabulary.db` (SQLite)

**Schema**:
```sql
CREATE TABLE vocabulary (
  id INTEGER PRIMARY KEY,
  level TEXT,
  module INTEGER,
  lemma TEXT,
  ipa TEXT,
  translation TEXT,
  pos TEXT,
  gender TEXT,
  aspect TEXT,
  pair TEXT,
  note TEXT
);
```

**Usage**:
- Global vocabulary searches
- Duplicate detection
- Cross-level vocabulary tracking
- Cumulative vocabulary counting

## Common Issues

### Missing IPA
**Cause**: espeak-ng not installed or Ukrainian voice missing
**Fix**:
```bash
brew install espeak-ng
```

### Duplicate Lemmas
**Cause**: Same word added in multiple modules
**Fix**: Check if word belongs in both contexts or remove duplicate

### Incorrect Gender
**Cause**: espeak-ng misidentification
**Fix**: Manually correct in YAML, re-run enrichment

## Vocabulary Targets by Level

| Level | Cumulative Vocab | New This Level |
|-------|------------------|----------------|
| A1    | ~750             | 750            |
| A2    | ~1,800           | 1,050          |
| B1    | ~3,300           | 1,500          |
| B2    | ~5,940           | 2,640          |
| C1    | ~9,780           | 3,840          |
| C2    | ~12,280          | 2,500          |

## Best Practices

1. **Always enrich before committing** - Don't commit minimal entries
2. **Review IPA pronunciations** - espeak-ng can make errors
3. **Add usage notes** - Context helps learners (register, collocations)
4. **Validate globally** - Check for duplicates across all levels
5. **Rebuild database** - Keep vocabulary.db in sync with YAML files
