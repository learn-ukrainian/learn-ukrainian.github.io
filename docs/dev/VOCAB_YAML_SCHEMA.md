# Vocabulary YAML Schema

## File Location

- **Path**: `curriculum/l2-uk-en/{level}/vocabulary/{module_slug}.yaml`
- **Example**: `curriculum/l2-uk-en/a1/vocabulary/01-the-cyrillic-code-i.yaml`

## Root Structure

```yaml
module: "01-the-cyrillic-code-i"  # Required: Must match filename slug
level: "A1"                       # Required: CEFR Level (A1, A2, B1, B2, C1, C2)
version: "2.0"                    # Required: Schema version
status: "draft"                   # draft | review | approved
tags: ["core", "food"]            # Optional: Module-level tags
items:                            # Required: List of vocabulary items
  - lemma: "так"
    ipa: "tɑk"
    translation: "yes"
    pos: "particle"
    ...
```

## Vocabulary Item Field Reference

| Field             | Type   | status        | Description                                                                                                            |
| :---------------- | :----- | :------------ | :--------------------------------------------------------------------------------------------------------------------- |
| **`lemma`**       | string | **Required**  | The base form of the word (nominative/singular/infinitive).                                                            |
| **`ipa`**         | string | **Required**  | International Phonetic Alphabet transcription.                                                                         |
| **`translation`** | string | **Required**  | English translation. **Must be concise**.                                                                              |
| **`pos`**         | enum   | **Required**  | Part of Speech. Valid: `noun`, `verb`, `adj`, `adv`, `pron`, `prep`, `conj`, `part`, `intj`, `num`, `phrase`, `propn`, `suffix`, `prefix`, `other`. |
| `gender`          | enum   | _Conditional_ | Required for **nouns**. valid: `m` (masc), `f` (fem), `n` (neut), `pl` (plural-only).                                  |
| `aspect`          | enum   | _Conditional_ | Required for **verbs** (B1+). valid: `imp` (imperfective), `perf` (perfective).                                        |
| `usage`           | string | Optional      | Context note (e.g., "formal", "slang").                                                                                |
| `audio`           | string | Optional      | Filename of audio asset (e.g., `a1m01_tak.mp3`).                                                                       |
| `tags`            | list   | Optional      | `core` (must drill), `passive` (recognition only), `cognate`.                                                          |

## Validation Rules

1.  **Duplicate Lemmas**: Lemmas must be unique within a single module.
2.  **IPA Format**: Must be wrapped in slashes `/.../` is optional but preferred. Must use standard IPA symbols.
3.  **Gender**: If `pos` is `noun`, `gender` field must be present.
4.  **Enrichment Check**: `ipa` and `translation` cannot be empty. (Violation = Build Failure).

## Example

```yaml
module: '01-the-cyrillic-code-i'
level: 'A1'
version: '2.0'
items:
  - lemma: 'так'
    ipa: 'tɑk'
    translation: 'yes'
    pos: 'part'

  - lemma: 'мама'
    ipa: 'ˈmɑmɑ'
    translation: 'mom'
    pos: 'noun'
    gender: 'f'
    tags: ['core']

  # Morphological affixes (for word formation modules)
  - lemma: '-увати'
    ipa: 'uʋɑtɪ'
    translation: '-uvaty (imperfective suffix)'
    pos: 'suffix'
```
