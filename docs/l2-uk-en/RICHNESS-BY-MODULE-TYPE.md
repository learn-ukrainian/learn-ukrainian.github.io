# Richness Criteria by Module Type

**Problem:** Current richness script applies B1 grammar criteria (bold examples, mini-dialogues) uniformly. This doesn't work for:
- B2 History modules (need source citations, not dialogues)
- C1 Biography modules (need analytical depth, not fill-in examples)
- C2 Style modules (need register analysis, not cultural anchors)
- LIT modules (need philological rigor, not vocabulary drills)

**Solution:** Define richness criteria per module type, keyed by `pedagogy` field in frontmatter.

---

## Template-Derived Requirements Summary

| Module Type | Template Source | Key Requirements |
|-------------|----------------|------------------|
| B1 Grammar | `b1-grammar-module-template.md` | 24+ examples, 4+ dialogues, proverbs |
| B1 Vocabulary | `b1-vocab-module-template.md` | Collocations, synonyms, register |
| B1 Cultural | `b1-cultural-module-template.md` | Authentic materials, regional refs |
| B2 History | `b2-history-module-template.md` | Primary sources, decolonization, 500+ narrative |
| B2 Phraseology | `b2-phraseology-module-template.md` | Idiom context, etymology, register |
| C1 Biography | `c1-biography-module-template.md` | 800-1000 narrative, quotes, legacy |
| C1 Academic | `c1-academic-module-template.md` | Citations, frameworks, data |
| C2 Style | `c2-style-module-template.md` | 600-1000 exemplar, model answers, transformation |
| C2 Professional | `c2-professional-module-template.md` | Domain terminology, documents |
| LIT | `lit-module-template.md` | Philological analysis, essays, 30-40 vocab |

---

## Module Type Categories

### 1. Grammar Modules (B1-B2)
**Pedagogy values:** `TTT`, `PPP`, `grammar`
**Levels:** B1 M06-51, B2 M01-40

| Component | Weight | Target | Why |
|-----------|--------|--------|-----|
| Examples (bold Ukrainian sentences) | 25% | 24+ | Core grammar demonstration |
| Mini-dialogues | 15% | 4+ | Contextual usage |
| Engagement boxes | 15% | 5+ | Cognitive breaks |
| Cultural anchors | 10% | 3+ | Memorable contexts |
| Real-world contexts | 10% | 3+ | Practical application |
| Proverbs/idioms | 5% | 1+ | Natural grammar in use |
| Questions | 5% | 5+ | Learner engagement |
| Visual variety | 5% | 3+ | Tables, callouts |
| Sentence variety | 5% | 60%+ | Avoid repetitive starters |
| Paragraph variety | 5% | — | Rhythm, pacing |

**Dryness flags:** NO_EXAMPLES, NO_DIALOGUE, REPETITIVE_STARTERS, ABSTRACT_ONLY

---

### 2. Vocabulary Expansion Modules (B1)
**Pedagogy values:** `vocabulary`, `lexical`
**Levels:** B1 M52-71

| Component | Weight | Target | Why |
|-----------|--------|--------|-----|
| Collocations | 25% | 20+ | Core vocabulary patterns |
| Usage examples | 20% | 15+ | Words in context |
| Synonym/antonym pairs | 15% | 10+ | Semantic networks |
| Register notes | 10% | 5+ | Formal/informal markers |
| Engagement boxes | 10% | 4+ | Interesting facts |
| Cultural context | 10% | 3+ | Word origins, usage |
| Visual variety | 5% | 3+ | Word maps, tables |
| Paragraph variety | 5% | — | Rhythm |

**Dryness flags:** NO_COLLOCATIONS, ISOLATED_WORDS, NO_CONTEXT

---

### 3. Cultural Modules (B1-C1)
**Pedagogy values:** `cultural`, `CBI`
**Levels:** B1 M72-81, C1 folk culture

| Component | Weight | Target | Why |
|-----------|--------|--------|-----|
| Authentic materials | 25% | 3+ | Real Ukrainian content |
| Regional references | 20% | 5+ | Geographical diversity |
| Contemporary examples | 15% | 3+ | Modern Ukraine |
| Engagement boxes | 15% | 6+ | Interesting facts |
| Historical context | 10% | 2+ | Background |
| Visual variety | 10% | 4+ | Images, tables |
| Questions | 5% | 4+ | Discussion prompts |

**Dryness flags:** NO_AUTHENTIC_MATERIAL, STEREOTYPICAL, NO_CONTEMPORARY

---

### 4. History Modules (B2)
**Pedagogy values:** `history`, `historical`
**Levels:** B2 M41-70

| Component | Weight | Target | Why |
|-----------|--------|--------|-----|
| Primary sources | 25% | 3+ | Historical citations |
| Timeline markers | 20% | 10+ | Dates, periods |
| Decolonizing perspective | 15% | — | Ukrainian-centered narrative |
| Engagement boxes | 15% | 6+ | Myth busters, facts |
| Place references | 10% | 5+ | Geographical context |
| Visual variety | 10% | 4+ | Maps, timelines |
| Analytical questions | 5% | 3+ | Critical thinking |

**Dryness flags:** NO_PRIMARY_SOURCES, IMPERIAL_NARRATIVE, NO_TIMELINE

---

### 5. Phraseology Modules (B2)
**Pedagogy values:** `phraseology`, `idioms`
**Levels:** B2 M71-80

| Component | Weight | Target | Why |
|-----------|--------|--------|-----|
| Idiom examples | 30% | 15+ | Core content |
| Usage contexts | 20% | 10+ | When to use |
| Etymology notes | 15% | 5+ | Origins |
| Register markers | 15% | 5+ | Formal/informal |
| Contrastive pairs | 10% | 5+ | Similar idioms |
| Engagement boxes | 5% | 4+ | Fun facts |
| Visual variety | 5% | 3+ | Tables |

**Dryness flags:** NO_CONTEXT, ISOLATED_IDIOMS, NO_REGISTER

---

### 6. Biography Modules (C1)
**Pedagogy values:** `biography`, `biographical`
**Levels:** C1 M01-40

| Component | Weight | Target | Why |
|-----------|--------|--------|-----|
| Primary sources | 25% | 4+ | Letters, memoirs, speeches |
| Analytical depth | 20% | — | Critical interpretation |
| Historical context | 15% | 3+ | Era background |
| Legacy analysis | 15% | 2+ | Impact on Ukraine |
| Engagement boxes | 10% | 6+ | Insights, parallels |
| Visual variety | 10% | 4+ | Photos, timelines |
| Discussion prompts | 5% | 3+ | Critical questions |

**Dryness flags:** HAGIOGRAPHIC, NO_SOURCES, NO_ANALYSIS

---

### 7. Academic/Sociolinguistics Modules (C1)
**Pedagogy values:** `academic`, `sociolinguistics`
**Levels:** C1 M41-80

| Component | Weight | Target | Why |
|-----------|--------|--------|-----|
| Scholarly citations | 25% | 5+ | Academic rigor |
| Data/statistics | 20% | 3+ | Evidence-based |
| Analytical frameworks | 15% | 2+ | Theoretical grounding |
| Case studies | 15% | 2+ | Concrete examples |
| Engagement boxes | 10% | 5+ | Key insights |
| Visual variety | 10% | 5+ | Charts, diagrams |
| Critical questions | 5% | 4+ | Discussion |

**Dryness flags:** NO_CITATIONS, ANECDOTAL, NO_FRAMEWORK

---

### 8. Style Modules (C2)
**Pedagogy values:** `style`, `stylistics`
**Levels:** C2 M01-30

| Component | Weight | Target | Why |
|-----------|--------|--------|-----|
| Register examples | 25% | 10+ | Formal/informal/neutral |
| Stylistic analysis | 25% | 5+ | Tropes, devices |
| Literary citations | 15% | 5+ | Canonical examples |
| Contrastive pairs | 15% | 5+ | Register shifts |
| Engagement boxes | 10% | 5+ | Stylistic insights |
| Visual variety | 5% | 4+ | Tables |
| Creative prompts | 5% | 2+ | Writing practice |

**Dryness flags:** NO_REGISTER_CONTRAST, PRESCRIPTIVE, NO_LITERARY_EXAMPLES

---

### 9. Professional Modules (C2)
**Pedagogy values:** `professional`, `specialized`
**Levels:** C2 M31-60

| Component | Weight | Target | Why |
|-----------|--------|--------|-----|
| Domain terminology | 25% | 20+ | Field-specific vocabulary |
| Document examples | 20% | 3+ | Authentic professional texts |
| Register analysis | 15% | 3+ | Professional tone |
| Practical scenarios | 15% | 3+ | Real-world application |
| Engagement boxes | 10% | 4+ | Industry insights |
| Visual variety | 10% | 3+ | Templates, samples |
| Writing tasks | 5% | 2+ | Production practice |

**Dryness flags:** GENERIC_VOCAB, NO_AUTHENTIC_DOCS, THEORETICAL_ONLY

---

### 10. Literature Modules (LIT)
**Pedagogy values:** `literature`, `literary`, `LIT`
**Levels:** LIT-001 to LIT-030

| Component | Weight | Target | Why |
|-----------|--------|--------|-----|
| Philological analysis | 25% | 5+ sections | Core purpose |
| Literary citations | 20% | 5+ | Textual evidence |
| Historical context | 15% | 3+ | Era background |
| Engagement boxes | 15% | 6+ | Insights, parallels |
| Essay prompts | 10% | 2+ | Critical writing |
| Reading resources | 10% | 3+ | UkrLib links |
| Visual variety | 5% | 3+ | Tables |

**NOT measured:** Examples, dialogues, real-world contexts (inappropriate for academic literary analysis)

**Dryness flags:** NO_ANALYSIS, PLOT_SUMMARY_ONLY, NO_CITATIONS

---

### 11. Checkpoint Modules (All Levels)
**Pedagogy values:** `checkpoint`, `review`, `assessment`
**Levels:** B1-C2 (phase-end assessments)

| Component | Weight | Target | Why |
|-----------|--------|--------|-----|
| Activity variety | 30% | 8+ types | Comprehensive testing |
| Skill coverage | 25% | — | All skills from phase |
| Diagnostic feedback | 15% | — | Self-assessment guidance |
| Review summaries | 15% | 3+ | Key concepts |
| Engagement boxes | 10% | 3+ | Encouragement |
| Visual variety | 5% | 3+ | Tables, progress |

**NOT measured:** New content (checkpoints review, not introduce)

**Dryness flags:** INCOMPLETE_COVERAGE, NO_FEEDBACK

---

## Implementation

### 1. Read Pedagogy from Frontmatter

```python
def get_module_type(content: str, file_path: Path) -> str:
    """Extract module type from frontmatter pedagogy field."""
    import yaml

    # Extract frontmatter
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            try:
                fm = yaml.safe_load(parts[1])
                pedagogy = fm.get('pedagogy', '').lower()

                # Map pedagogy values to module types
                if pedagogy in ('ttt', 'ppp', 'grammar'):
                    return 'grammar'
                elif pedagogy in ('vocabulary', 'lexical'):
                    return 'vocabulary'
                elif pedagogy in ('cultural', 'cbi'):
                    return 'cultural'
                elif pedagogy in ('history', 'historical'):
                    return 'history'
                elif pedagogy in ('phraseology', 'idioms'):
                    return 'phraseology'
                elif pedagogy in ('biography', 'biographical'):
                    return 'biography'
                elif pedagogy in ('academic', 'sociolinguistics'):
                    return 'academic'
                elif pedagogy in ('style', 'stylistics'):
                    return 'style'
                elif pedagogy in ('professional', 'specialized'):
                    return 'professional'
                elif pedagogy in ('literature', 'literary', 'lit'):
                    return 'literature'
                elif pedagogy in ('checkpoint', 'review', 'assessment'):
                    return 'checkpoint'
            except:
                pass

    # Fallback: infer from path
    path_str = str(file_path).lower()
    if '/lit/' in path_str:
        return 'literature'

    return 'grammar'  # Default
```

### 2. Module Type Targets

```python
MODULE_TYPE_TARGETS = {
    'grammar': {
        'examples': 24,
        'dialogues': 4,
        'engagement': 5,
        'cultural': 3,
        'realworld': 3,
        'proverbs': 1,
        'questions': 5,
        'visual': 3,
    },
    'vocabulary': {
        'collocations': 20,
        'usage_examples': 15,
        'synonyms': 10,
        'register': 5,
        'engagement': 4,
        'cultural': 3,
        'visual': 3,
    },
    'history': {
        'primary_sources': 3,
        'timeline_markers': 10,
        'engagement': 6,
        'places': 5,
        'visual': 4,
        'questions': 3,
    },
    'biography': {
        'primary_sources': 4,
        'historical_context': 3,
        'legacy': 2,
        'engagement': 6,
        'visual': 4,
        'questions': 3,
    },
    'literature': {
        'analysis_sections': 5,
        'citations': 5,
        'historical_context': 3,
        'engagement': 6,
        'essays': 2,
        'resources': 3,
        'visual': 3,
    },
    # ... etc
}
```

### 3. Weights per Module Type

Each module type has its own weight distribution that emphasizes what matters for that type.

---

## Migration Path

1. **Phase 1:** Add `pedagogy` field to all module frontmatter (if missing)
2. **Phase 2:** Update `calculate_richness.py` to read module type
3. **Phase 3:** Define targets for each module type
4. **Phase 4:** Update dryness flags per module type
5. **Phase 5:** Re-audit all modules with new criteria

---

## Summary Table

| Module Type | Key Criteria | NOT Measured |
|-------------|--------------|--------------|
| Grammar | Examples, Dialogues, Cultural | — |
| Vocabulary | Collocations, Context, Synonyms | Dialogues |
| Cultural | Authentic materials, Regions | Formal analysis |
| History | Primary sources, Timeline | Dialogues, Examples |
| Phraseology | Idioms, Context, Etymology | — |
| Biography | Sources, Analysis, Legacy | Dialogues |
| Academic | Citations, Data, Frameworks | Examples |
| Style | Register, Literary citations | Real-world |
| Professional | Terminology, Documents | Literary |
| Literature | Philological analysis, Essays | Examples, Dialogues, Real-world |
| Checkpoint | Activity variety, Coverage | New content |

---

**Created:** 2024-12-26
**Status:** PROPOSAL - Awaiting implementation
