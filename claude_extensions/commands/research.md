# /research - Ukrainian-Only Research Skill

<skill>
name: research
description: Research topics for seminar tracks using strictly Ukrainian resources. Use before writing content for b2-hist, c1-bio, c1-hist, oes, ruth, lit modules. Auto-updates active /task if set.
arguments: topic - The topic to research (figure, event, era, literary work, document)
</skill>

## Purpose

Conduct research using **only Ukrainian-language sources** to gather accurate, authoritative information before writing module content. This enforces the research-first workflow and prevents thin, inaccurate content.

> **🔗 Task Integration**: If `/task` is active, research completion auto-updates the issue.

## Supported Tracks (MANDATORY Research)

| Track | Research Focus |
|-------|----------------|
| `c1-bio` | Historical figures - birth/death dates, key events, legacy, quotes |
| `b2-hist` | Historical events, eras, causes/consequences, primary sources |
| `c1-hist` | Historiographical analysis, interpretations, scholarly debates |
| `lit` | Literary works, authors, movements, textual analysis |
| `oes` | Old East Slavic documents, paleography, linguistic features |
| `ruth` | Ruthenian documents, Cossack-era texts, legal/religious writings |

## Workflow

### Step 0: Check Context

Before researching, determine:

1. **Track type** - Which seminar track is this for?
2. **Module slug** - What's the target module? (for saving research notes)
3. **Active task** - Is there a `/task` active? (for auto-updates)

```bash
# If active task exists, we'll update it when done
# ACTIVE_TASK_ID is set by /task create
```

### Step 1: Identify Research Needs

Based on the topic and track, determine what information is needed:

**For Biography (c1-bio):**
- Full name in Ukrainian (with patronymic if applicable)
- Birth/death dates and locations
- Key life events (chronological)
- Major achievements/contributions
- Historical context (era, political situation)
- Primary source quotes (in Ukrainian)
- Legacy and modern significance
- Myths vs facts (for decolonization perspective)
- **VITAL STATUS**: Is the person ALIVE or DECEASED?

**For History (b2-hist, c1-hist):**
- Event dates and timeline
- Key figures involved
- Causes and consequences
- Primary source documents
- Historiographical interpretations
- Russian imperial myths to debunk
- Ukrainian perspective and agency

**For Literature (lit):**
- Author biographical context
- Work's publication history
- Literary movement/period
- Key themes and motifs
- Notable quotes (original Ukrainian)
- Critical interpretations
- Cultural significance

**For Historical Linguistics (oes, ruth):**
- Document provenance and dating
- Linguistic features (phonology, morphology, syntax)
- Historical context of text
- Paleographic details if relevant
- Scholarly editions and translations

### Step 2: Search Ukrainian Sources

Use WebSearch with Ukrainian queries. **CRITICAL: Search in Ukrainian only.**

```python
# Good search queries (Ukrainian):
WebSearch(
    query="Іван Сірко біографія",
    allowed_domains=["uk.wikipedia.org", "esu.com.ua", "history.org.ua"]
)

WebSearch(
    query="Гадяцька угода 1658 історія",
    allowed_domains=["uk.wikipedia.org", "litopys.org.ua", "history.org.ua"]
)

# BAD - English/Russian queries:
"Ivan Sirko biography" ❌
"Иван Сирко биография" ❌
```

**Preferred Ukrainian sources:**
| Source | Domain | Use Case |
|--------|--------|----------|
| Українська Вікіпедія | `uk.wikipedia.org` | Starting point for overview |
| Енциклопедія сучасної України | `esu.com.ua` | Encyclopedia entries |
| Інститут історії України | `history.org.ua` | Academic historical research |
| Ізборник | `litopys.org.ua` | Primary sources, chronicles |
| Історична правда | `istorychna-pravda.com.ua` | Historical analysis |
| Збруч | `zbruc.eu` | Culture and history |
| Літакцент | `litakcent.com` | Literary criticism |
| УМодерна | `uamoderna.com` | Modern Ukrainian history |
| Historians.in.ua | `historians.in.ua` | Academic history |
| Діаспоріана | `diasporiana.org.ua` | Diaspora archives |
| Читанка | `chtyvo.org.ua` | Digital library |

**BLOCKED sources (NEVER use):**
- `ru.wikipedia.org` - Russian language
- Any `*.ru` domains - Russian sources
- Sources using "Малороссия", "воссоединение"

### Step 2.5: Load Content Outline from Meta

**BEFORE compiling notes**, read the module's meta file to get the `content_outline`:

```bash
yq '.content_outline' curriculum/l2-uk-en/{track}/meta/{slug}.yaml
```

This gives you the exact section names and word targets. **Structure your research notes to match these sections.** This eliminates the mapping step during writing — research flows directly into content.

### Step 3: Compile Research Notes

Create structured notes using this template. **The "Зміст за секціями" section MUST match content_outline from meta.**

```markdown
# Research Notes: {Topic}

**Track**: {track}
**Module**: {slug}
**Researched**: {date}
**Sources consulted**: {count}

## Основні факти
- Повне ім'я:
- Роки життя: (або "живий/жива" якщо сучасник)
- Ключові місця:
- Діяльність:

## Хронологія
1. [Рік] - Подія
2. [Рік] - Подія
...

## Ключові досягнення
-
-

## Первинні джерела (цитати українською)
> "Цитата українською" — Джерело, рік

> "Ще одна цитата" — Джерело, рік

## Історичний контекст
- Епоха:
- Політична ситуація:
- Пов'язані події:
- Пов'язані постаті:

## Зміст за секціями (mapped to content_outline)

> For each section in meta's content_outline, gather relevant facts here.
> This makes Phase 2 writing mechanical: read section research → write section.

### {Section 1 name from content_outline} ({word_target} words)
- Key facts:
- Dates:
- Quotes:
- Engagement hook idea:

### {Section 2 name from content_outline} ({word_target} words)
- Key facts:
- Dates:
- Quotes:
- Engagement hook idea:

(Repeat for all sections in content_outline)

## Деколонізаційні нотатки
- Російські/радянські міфи для спростування:
- Українська агентність для висвітлення:
- Термінологічні корекції:

## Перехресні посилання
- Інші модулі для посилань:
- Пов'язані постаті в курикулумі:

## Використані джерела
1. [Назва джерела](URL)
2. [Назва джерела](URL)
...

---
**Research quality checklist:**
- [ ] At least 3 Ukrainian sources consulted
- [ ] Primary source quote found
- [ ] Decolonization angle identified
- [ ] Cross-references noted
- [ ] Vital status confirmed (living/deceased)
```

### Step 4: Validate Research Quality

Before saving, verify research meets minimum standards:

| Criterion | Minimum | Check |
|-----------|---------|-------|
| Sources consulted | 3+ | `## Використані джерела` has 3+ entries |
| Primary quotes | 1+ | `## Первинні джерела` has content |
| Decolonization notes | Present | `## Деколонізаційні нотатки` not empty |
| Chronology | 5+ events | `## Хронологія` has 5+ items |
| Basic facts | Complete | All fields in `## Основні факти` filled |

**If validation fails:** Continue researching until criteria met.

### Step 5: Save Research

Save notes to the module's **research** directory:

```bash
curriculum/l2-uk-en/{track}/research/{slug}-research.md
```

**Example paths:**
- `curriculum/l2-uk-en/c1-bio/research/danylo-apostol-research.md`
- `curriculum/l2-uk-en/b2-hist/research/kozatstvo-vytoky-research.md`

### Step 6: Update Active Task (if exists)

If `ACTIVE_TASK_ID` is set, auto-update the GitHub issue:

```bash
# Add comment to active task
gh issue comment $ACTIVE_TASK_ID --body "📚 Research completed for {topic}

**Sources**: {count} Ukrainian sources consulted
**Primary quotes**: {quote_count} found
**Decolonization**: {myth_count} myths identified to debunk
**Saved to**: research/{slug}-research.md

Ready for content generation."
```

### Step 7: Report Summary

Output research summary for the user:

```
📚 Research Complete: {topic}

Track: {track}
Saved: curriculum/l2-uk-en/{track}/research/{slug}-research.md

Key findings:
- {name} ({dates})
- {key_achievement_1}
- {key_achievement_2}
- Primary quote: "{short_quote}..."

Sources: {count} Ukrainian sources
Decolonization: {myth_count} myths to debunk
Cross-references: {refs}

✅ Research quality: PASSED
   - Sources: {actual}/3+ ✅
   - Primary quotes: {actual}/1+ ✅
   - Chronology: {actual}/5+ events ✅

Ready for /module {track} {num}
```

If active task:
```
📋 Updated task #{ACTIVE_TASK_ID}
```

## Example Usage

### Basic Usage

```
User: /research Данило Апостол

Claude: [Searches Ukrainian sources]
[Compiles research notes]
[Validates quality]
[Saves to curriculum/l2-uk-en/c1-bio/audit/danylo-apostol-research.md]

📚 Research Complete: Данило Апостол

Track: c1-bio
Saved: curriculum/l2-uk-en/c1-bio/audit/danylo-apostol-research.md

Key findings:
- Данило Павлович Апостол (1654-1734)
- Останній виборний гетьман України
- Автор "Рішительних пунктів" 1728 року
- Primary quote: "Права народу козацького..."

Sources: 5 Ukrainian sources
Decolonization: 2 myths to debunk (Russian "reunification" narrative)
Cross-references: Ivan Mazepa, Pylyp Orlyk, Pavlo Polubotok

✅ Research quality: PASSED

Ready for /module c1-bio 28
```

### With Active Task

```
User: /task create "Write C1-BIO Danylo Apostol"
      /research Данило Апостол

Claude: [Research process...]

📚 Research Complete: Данило Апостол
...
📋 Updated task #500: "📚 Research completed for Данило Апостол"
```

## Integration with /module

The `/module` skill enforces research for seminar tracks:

```
/module c1-bio 28
  → Check: Does research/danylo-apostol-research.md exist?
  → If NO: "Research required. Run /research 'Данило Апостол' first."
  → If YES: Proceed with content generation
```

**To skip research check (NOT recommended):**
```
/module c1-bio 28 --no-research
```

## Gemini Collaboration Pattern

For complex research, leverage both agents:

```bash
# Claude structures, Gemini researches (parallel)
# Send research request to Gemini:
# Use --quiet and redirect to temp file to save context!
.venv/bin/python scripts/ai_agent_bridge.py ask-gemini \
  "Research Данило Апостол for C1-BIO module. Save notes to research/danylo-apostol-research.md" \
  --task-id gh-500 \
  --quiet \
  > /tmp/gemini-research-gh-500.txt 2>&1

# Continue with other work while Gemini researches
# Check for response later
```

## Important Rules

1. **Ukrainian sources only** - No English Wikipedia, no Russian sources
2. **Cite sources** - Every fact should be traceable
3. **Primary sources** - Find original quotes when possible
4. **Decolonization lens** - Note Russian/Soviet myths to debunk
5. **Save notes** - Research should be reusable for future edits
6. **Validate quality** - Don't save incomplete research
7. **Update task** - If active, keep issue informed
8. **Vital status** - Confirm if subject is living or deceased
