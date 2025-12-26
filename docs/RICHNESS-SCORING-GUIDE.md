# Richness Scoring Guide

This document explains how module richness is scored and how to fix low scores.

## How Scoring Works

Richness is calculated by `scripts/calculate_richness.py`. Each module type has different weighted metrics.

### Metric Detection

| Metric | What It Counts | Detection Method |
|--------|----------------|------------------|
| `cultural` | Ukrainian places + cultural terms | Matches against `UKRAINIAN_PLACES` and `CULTURAL_TERMS` sets |
| `realworld` | Practical context markers | Patterns: `уявіть`, `наприклад`, `у реальному житті`, `на практиці`, `у ресторані`, `на роботі`, etc. |
| `dialogues` | Mini-dialogue exchanges | Patterns: `^[АБВ]:`, `^— [Ukr]`, `^> — [Ukr]`, `**Speaker:**` |
| `proverbs` | Ukrainian sayings | Patterns: `кажуть:`, `приказка`, `прислів'я`, `«quoted text»` |
| `examples` | Bold Ukrainian sentences | `**Укр text**` or `- Укр...` patterns |
| `engagement` | Engagement boxes | `💡`, `🎬`, `🌍`, `🎯`, `🎮`, `> [!tip]`, `> [!note]` |

### Module Type Weights

Module type is detected from `pedagogy:` frontmatter field.

#### Grammar (TTT, PPP)
| Metric | Target | Weight |
|--------|--------|--------|
| examples | 24 | 20% |
| dialogues | 4 | 15% |
| engagement | 5 | 15% |
| cultural | 3 | 10% |
| variety | - | 10% |
| realworld | 3 | 10% |
| visual | 3 | 5% |
| paragraph_var | - | 5% |
| questions | 5 | 5% |
| proverbs | 1 | 5% |

#### Vocabulary
| Metric | Target | Weight |
|--------|--------|--------|
| collocations | 20 | 25% |
| usage_examples | 15 | 20% |
| engagement | 4 | 15% |
| cultural | 3 | 10% |
| register_notes | 5 | 10% |
| visual | 3 | 10% |
| variety | - | 5% |
| paragraph_var | - | 5% |

#### Checkpoint (Assessment)
| Metric | Weight |
|--------|--------|
| variety | 20% |
| questions | 20% |
| visual | 15% |
| examples | 15% |
| engagement | 10% |
| cultural | 10% |
| paragraph_var | 10% |

#### Cultural
| Metric | Weight |
|--------|--------|
| cultural | 25% |
| authentic_refs | 15% |
| regional_refs | 15% |
| engagement | 15% |
| contemporary | 10% |
| visual | 10% |
| variety | 5% |
| paragraph_var | 5% |

#### History
| Metric | Weight |
|--------|--------|
| primary_sources | 25% |
| engagement | 15% |
| timeline_markers | 15% |
| decolonization | 15% |
| cultural | 10% |
| visual | 10% |
| variety | 5% |
| paragraph_var | 5% |

#### Literature
| Metric | Weight |
|--------|--------|
| analysis_sections | 20% |
| literary_citations | 20% |
| historical_context | 15% |
| essays | 15% |
| engagement | 15% |
| resources | 10% |
| variety | 5% |

### Thresholds

- **Grammar/Vocabulary modules**: 95/100 to pass
- **Literature modules**: 90/100 to pass
- **Checkpoint modules**: 85/100 to pass (focused on variety)

## Common Dryness Flags & Fixes

### LOW_CULTURAL_ANCHOR / NO_CULTURAL_ANCHOR

**Problem**: Module has fewer than 3 cultural references.

**Detection**: Counts matches from `CULTURAL_TERMS` and `UKRAINIAN_PLACES` sets in `calculate_richness.py`.

**Fix**: Add cultural content boxes with Ukrainian places or traditions:

```markdown
> 🇺🇦 **Культурний момент: [Topic]**
>
> [Reference to Ukrainian place (Київ, Львів, Одеса, Карпати), tradition (толока, вишиванка),
> or cultural figure (Шевченко, Нестор)]
> [Connect to the grammar/vocabulary being taught]
> [Example sentence using the grammar with cultural context]
```

**Important**: The place/tradition name MUST be in `CULTURAL_TERMS` or `UKRAINIAN_PLACES` to be counted! If you use a term that's not in these sets, it won't count.

**Current terms include**:
- Places: Київ, Львів, Одеса, Харків, Карпати, Крим, Полтава, Лавра, Хрещатик, Майдан, etc.
- Terms: вишиванка, борщ, козак, толока, петриківський, Нестор, літопис, Шевченко, etc.

### LOW_REALWORLD / ABSTRACT_ONLY

**Problem**: Module lacks practical, real-life examples.

**Detection**: Counts patterns like `уявіть`, `у ресторані`, `на роботі`, `на практиці`.

**Fix**: Add real-world scenario boxes:

```markdown
> 🌍 **На практиці: У [Location]**
>
> Уявіть, що ви [situation]. [Practical example using the grammar]
```

Locations that trigger detection: `у ресторані`, `на роботі`, `у магазині`, `в аеропорту`, `на вокзалі`, `у лікарні`, `в університеті`

### LOW_DIALOGUE / NO_DIALOGUE

**Problem**: Module has fewer than 4 mini-dialogues.

**Detection**: Counts patterns like `^— Укр...` or `^> — Укр...` (in blockquotes).

**Fix**: Add dialogues with Ukrainian locations:

```markdown
**Діалог: На Бесарабському ринку**

> — [Line 1 with **bolded** grammar examples]
> — [Line 2 response]
> — [Line 3 continuation]
> — [Line 4 conclusion]
```

### NO_PROVERBS

**Problem**: No Ukrainian proverbs found.

**Detection**: Patterns like `кажуть:`, `«...»` (quoted text 10+ chars).

**Fix**: Add a proverb with analysis:

```markdown
> 🗣️ **Прислів'я**
>
> Українці кажуть: «[Proverb in Ukrainian]»
> *(English translation)*
>
> **[word]** — [explanation of why this aspect/form is used].
```

## Adding New Detection Terms

If cultural terms in a module aren't being counted, add them to the appropriate set in `scripts/calculate_richness.py`:

```python
# In UKRAINIAN_PLACES set (lines 258-265):
UKRAINIAN_PLACES = {
    'Київ', 'Львів', ...
    # Add new places here
}

# In CULTURAL_TERMS set (lines 268-281):
CULTURAL_TERMS = {
    'вишиванка', 'борщ', ...
    # Add new terms here
}
```

## Debugging Richness

Run audit with DEBUG output:
```bash
source .venv/bin/activate && python3 scripts/audit_module.py <file>
```

Look for the `DEBUG RICHNESS:` line showing raw counts:
```
DEBUG RICHNESS: {'score': 91, 'raw': {'cultural': 2, 'realworld': 2, 'dialogues': 18, ...}}
```

If a metric is below target, the module needs more content of that type.

## Quick Reference: What To Add When Failing

| Flag | Add This |
|------|----------|
| LOW_CULTURAL_ANCHOR | 🇺🇦 cultural box with place/tradition from detection list |
| ABSTRACT_ONLY | 🌍 real-world box with `Уявіть` + location keyword |
| LOW_DIALOGUE | Dialogue with `> —` format (blockquote em-dash) |
| NO_PROVERBS | Proverb with `кажуть: «...»` format |
| NO_EXAMPLES | More **bold Ukrainian sentences** in explanations |
