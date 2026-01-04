# Morpheme Highlighting Component Usage Guide

## What is Morpheme Highlighting?

Morpheme highlighting is for **word formation activities** where students need to identify **parts within words** (prefixes, suffixes, roots).

## When to Use Morpheme Highlighting

✅ **Use for:**
- Word formation lessons (prefixes, suffixes, roots)
- Morphology activities about word structure
- Teaching how words are built from parts
- Activities where students identify **parts WITHIN words**

**Example:** Finding the prefix *при-* in the word *прийшов*
```yaml
type: mark-the-words
title: Find Prefixes
text: 'Click on all words with arrival prefixes.

  Він *при*йшов до школи. Вона *при*несла книгу.'
```

## When NOT to Use Morpheme Highlighting

❌ **Do NOT use for:**
- Full words or complete phrases
- Multi-word expressions
- Idioms or set phrases
- Preference expressions like "Мені більше подобається"
- Vocabulary matching activities

**For these, use `mark-the-words` component instead.**

## Pattern Syntax

### Prefix Pattern
```yaml
*при*йшов  # Highlights "при" at the start of "прийшов"
*ви*йшов   # Highlights "ви" at the start of "вийшов"
```

### Suffix Pattern
```yaml
Чит*ач*     # Highlights "ач" at the end of "Читач"
читан*ня*   # Highlights "ня" at the end of "читання"
```

### Root Pattern (middle)
```yaml
*важлив*ість  # Highlights "важлив" in the middle of "важливість"
```

### Whole Word
```yaml
*Читач*  # Highlights entire word "Читач"
```

## Writing Clear Instructions

❌ **Vague (students confused):**
```yaml
text: 'Click on the prefix, suffix, or root in each word.'
```

✅ **Clear (students understand):**
```yaml
text: 'Click on all words with the prefix при- (meaning arrival).'
```

✅ **Specific examples:**
- "Click on all words with arrival prefixes (при-, під-)."
- "Click on all words containing the root ход- (walk/go)."
- "Click on all words with the suffix -ач (person who does action)."
- "Click on all words with the suffix -ність (quality/state)."

## Component Behavior

When student clicks a word with a morpheme pattern:
1. The **morpheme part** gets underlined
2. The **full word** is clickable
3. After submit: Green if correct, shows missed morphemes

## Generated MDX Structure

```jsx
<HighlightMorphemes>
  <HighlightMorphemesActivity
    instruction={`Click on all words with the prefix при-.`}
    text={`Він прийшов до школи. Вона прийшла додому.`}
    morphemes={[
      { word: `прийшов`, morpheme: `при`, type: `prefix` },
      { word: `прийшла`, morpheme: `при`, type: `prefix` }
    ]}
  />
</HighlightMorphemes>
```

## Validation

The audit checks:
- ✅ Morpheme patterns are well-formed
- ✅ Full word exists in text
- ✅ Morpheme is actually part of the word
- ⚠️ Warns if mixing full words and fragments
- ⚠️ Warns if instruction is too vague

## Examples by Type

### Prefix Activity (Best Practice)
```yaml
- type: mark-the-words
  title: Find Arrival Prefixes
  text: 'Click on all words with prefixes meaning arrival or approach (при-, під-).

    Він *при*йшов додому. Вона *під*ійшла до столу. Ми *при*везли їжу.'
```

### Root Family Activity
```yaml
- type: mark-the-words
  title: Find "Walk" Root Family
  text: 'Click on all words containing the root ход- (walk/go).

    Ось *вхід* у будинок. Там *вихід* з парку. Це *перехід* через вулицю.'
```

### Suffix Activity
```yaml
- type: mark-the-words
  title: Find Agent Nouns
  text: 'Click on all words with the suffix -ач (person who does action).

    *Читач* читає книгу. *Слухач* слухає музику. *Глядач* дивиться фільм.'
```

## Migration from Old Format

If you find activities using morpheme component for non-morpheme content:

1. Identify what the activity is actually testing
2. If it's full words/phrases → convert to `mark-the-words`
3. If it's actual morphemes → keep and fix instruction to be specific
4. Update the YAML file
5. Regenerate MDX

See Issue #364 for activities that need conversion.
