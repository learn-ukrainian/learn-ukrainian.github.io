---
name: vocab-enrichment
description: Use this skill when enriching vocabulary sections in curriculum modules. Adds IPA pronunciation, part of speech, grammatical info, and usage notes. Triggers when working on vocabulary tables, word lists, or running vocab enrichment tasks.
allowed-tools: Read, Glob, Grep, Edit, Write, Bash
---

# Vocabulary Enrichment Skill

You are a vocabulary enrichment specialist for language learning curriculum. Add pronunciation, grammatical info, and usage notes to vocabulary entries.

## When This Skill Activates

- Enriching vocabulary sections in modules
- Adding IPA pronunciation to word lists
- Completing vocabulary table columns
- Running vocab enrichment scripts

## Supported Languages

| Language | Vocab Reference | Format Spec |
|----------|-----------------|-------------|
| Ukrainian | `curriculum/l2-uk-en/vocabulary.csv` | `docs/MARKDOWN-FORMAT.md` |

When new languages are added, their vocabulary files will follow the same pattern.

## Enrichment Workflow

1. **Identify target language** from file path
2. **Read module vocabulary section**
3. **For each word, add**:
   - IPA pronunciation (with stress)
   - Part of speech
   - Grammatical info (gender, case requirements, etc.)
   - Usage notes if relevant
4. **Use script for batch enrichment** (if available):
   ```bash
   npm run vocab:enrich {lang-pair} [moduleNum]
   ```

## Common Notes (All Languages)

| Note | When to use |
|------|-------------|
| colloq. | Colloquial usage |
| formal | Formal register |
| lit. | Literary/written |
| impf | Imperfective aspect |
| pf | Perfective aspect |
| irreg. | Irregular form |

## Reference Files

- `docs/MARKDOWN-FORMAT.md` - Format specification
- `docs/{lang-pair}/module-prompt.md` - Module constraints

---

## Ukrainian-Specific Reference

### Vocabulary Table Formats by Level

#### A1-A2+ (Modules 1-80)
English header, 6 columns:

```markdown
# Vocabulary

| Word | IPA | English | POS | Gender | Note |
|------|-----|---------|-----|--------|------|
| слово | /ˈslɔwɔ/ | word | n | n | - |
```

#### B1 (Modules 81-160)
Ukrainian header, 5 columns:

```markdown
# Словник

| Слово | Вимова | Переклад | ЧМ | Примітка |
|-------|--------|----------|-----|----------|
| слово | /ˈslɔwɔ/ | word | ім.с. | - |
```

#### B2+ (Modules 161+)
Ukrainian header, 3 columns:

```markdown
# Словник

| Слово | Переклад | Примітки |
|-------|----------|----------|
| слово | word | ім.с., н. |
```

### Part of Speech Abbreviations

| English | Ukrainian | Meaning |
|---------|-----------|---------|
| n | ім.с. | noun (іменник) |
| v | дієсл. | verb (дієслово) |
| adj | прикм. | adjective (прикметник) |
| adv | присл. | adverb (прислівник) |
| prep | прийм. | preposition (прийменник) |
| conj | спол. | conjunction (сполучник) |
| pron | займ. | pronoun (займенник) |
| num | числ. | numeral (числівник) |
| part | част. | particle (частка) |
| interj | вигук | interjection (вигук) |
| phr | вираз | phrase (вираз) |

### Gender Abbreviations

| English | Ukrainian | Meaning |
|---------|-----------|---------|
| m | ч. | masculine (чоловічий) |
| f | ж. | feminine (жіночий) |
| n | н. | neuter (середній) |
| pl | мн. | plural only (множина) |

### IPA Guidelines for Ukrainian

#### Vowels
| Letter | IPA | Notes |
|--------|-----|-------|
| а | /ɑ/ | open back |
| е | /ɛ/ | open-mid front |
| и | /ɪ/ | near-close near-front |
| і | /i/ | close front |
| о | /ɔ/ | open-mid back |
| у | /u/ | close back |
| я | /jɑ/ | or /ʲɑ/ after consonant |
| є | /jɛ/ | or /ʲɛ/ after consonant |
| ї | /ji/ | always two sounds |
| ю | /ju/ | or /ʲu/ after consonant |

#### Consonants (key distinctions)
| Letter | IPA | Notes |
|--------|-----|-------|
| г | /ɦ/ | voiced glottal fricative |
| ґ | /ɡ/ | voiced velar stop (rare) |
| щ | /ʃtʃ/ | two sounds |
| ь | /ʲ/ | palatalization marker |

#### Stress
- Mark stressed syllable with /ˈ/ before it
- Example: слово → /ˈslɔwɔ/

### Ukrainian Case Notes

| Note | When to use |
|------|-------------|
| + Acc | Takes accusative case |
| + Gen | Takes genitive case |
| + Loc | Takes locative case |
| + Dat | Takes dative case |
| + Inst | Takes instrumental case |
