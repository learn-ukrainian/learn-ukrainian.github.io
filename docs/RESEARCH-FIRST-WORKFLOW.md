# Research-First Workflow for Historical & Literary Tracks

> **Applies to:** `b2-hist`, `c1-bio`, `c1-hist`, `lit`, `oes`, `ruth`
> **Purpose**: This workflow ensures high-quality content by requiring deep research BEFORE writing.

---

## ⛔ Research Gate (Smart Enforcement)

**As of February 2026, the `/module` skill enforces research for seminar tracks - but only where it matters.**

### When Research is Required

| Scenario | Research Required? |
|----------|-------------------|
| **New module** (no .md exists) | ✅ Yes - must research first |
| **Existing module under word target** | ✅ Yes - before expansion |
| **Existing module passing audit** | ❌ No - already has content |
| **Using `--from=lesson` flag** | ✅ Yes - rewriting content |

### Examples

```bash
# New module - BLOCKED without research
/module c1-bio 28
  → No content exists
  → ⛔ "Research required. Run /research first."

# Existing module passing word count - ALLOWED
/module c1-bio 15
  → Content exists: 3800 words (target 3500)
  → ✅ "Research gate: SKIPPED (module already has content)"

# Existing module under target - BLOCKED
/module c1-bio 22
  → Content exists: 2100 words (target 3500)
  → ⛔ "Research required for expansion."
```

**Quick commands:**
```bash
/research "Данило Апостол"       # Research topic (saves to audit/)
/module c1-bio 28                # Smart gate check
/module c1-bio 28 --no-research  # Skip check (NOT recommended)
```

**Task integration:** If `/task` is active, research completion auto-updates the issue.

---

## 🎯 Domain Sniping Strategy (Search Quality)

**Problem**: Generic web searches return SEO-heavy sites, Wikipedia summaries, or Russian sources instead of scholarly Ukrainian content.

**Solution**: Use site-specific searches targeting trusted Ukrainian academic sources.

### Trusted Ukrainian Domains

| Domain | Purpose | Example Query |
|--------|---------|---------------|
| `esu.com.ua` | Encyclopedia of Modern Ukraine | `Марія Павлова біографія site:esu.com.ua` |
| `history.org.ua` | Institute of History | `Данило Апостол site:history.org.ua` |
| `zbruc.eu` | Zbruc cultural portal | `Леся Українка site:zbruc.eu` |
| `elib.nlu.org.ua` | National Library Archives | `Марія Занковецька листи site:elib.nlu.org.ua` |
| `wikipedia.org` | Ukrainian Wikipedia only | `site:uk.wikipedia.org NOT site:ru.wikipedia.org` |

### Query Engineering Examples

❌ **Bad Query** (too broad):
```
Mariya Pavlova biography
→ Returns generic results, Russian sources, SEO spam
```

✅ **Sniper Query** (domain-filtered):
```
Марія Павлова біографія site:esu.com.ua OR site:history.org.ua OR site:zbruc.eu
→ Returns Encyclopedia entries, Institute articles, cultural portals
```

✅ **Primary Source Query** (archival):
```
Марія Павлова листи спогади site:elib.nlu.org.ua
→ Returns letters, memoirs, archival documents
```

### Why This Matters

1. **Hallucination Shield**: Specific facts (e.g., "24,000 ruble offer to Zankovetska") vs. generic summaries
2. **Decolonization**: Ukrainian scholarly sources vs. Russian imperial narratives
3. **C1-Grade Authority**: Primary sources and academic research vs. Wikipedia paraphrasing

**Rule**: Always use domain-specific searches. Never search "open web" for historical/biographical content.

---

## 📦 Optimal Batch Size

**Goldilocks Zone: 2-3 modules per batch**

### Why Not More or Less?

| Batch Size | Result |
|------------|--------|
| **1 module** | ❌ Too slow - high overhead for single module |
| **2-3 modules** | ✅ Sweet spot - full research notes in active memory, 4000+ words each |
| **5+ modules** | ❌ Context window full - risk cross-contamination, shortened content, hallucination from module #1 into #5 |

### Context Window Management

**Problem**: Researching 5 complex biographies generates massive internal state. By module #5, token limits force either:
- Shortened content (fails word targets)
- Cross-contamination (facts from one figure bleed into another)
- Rushed writing (loses depth)

**Solution**: Batch 2-3 modules maximum. This allows:
- Holding full research notes while writing
- 4000+ unique words per module
- Rigorous self-audit without rushing

---

## CRITICAL: Ukrainian-Only Research Policy

> **All research MUST be conducted in Ukrainian using Ukrainian sources.**
> **Russian-language sources are STRICTLY PROHIBITED.**

### Why This Matters

1. **Decolonization** — Russian sources often contain imperial narratives, distortions, or outright falsifications of Ukrainian history
2. **Language Quality** — Ukrainian sources provide authentic Ukrainian terminology, phrasing, and academic vocabulary
3. **Curriculum Integrity** — Students learning Ukrainian should encounter Ukrainian scholarship, not translations or Russian interpretations

### Allowed Sources (Ukrainian .ua Domains)

| Source | Domain | Use Case |
|--------|--------|----------|
| **Українська Вікіпедія** | `uk.wikipedia.org` | General research starting point |
| **Ізборник** | `litopys.org.ua` | Primary sources, chronicles, historical texts |
| **Институт історії України** | `history.org.ua` | Academic historical research |
| **Електронна бібліотека** | `elib.nlu.org.ua` | National library digitized texts |
| **Лексика** | `lcorp.ulif.org.ua` | Linguistic corpus |
| **Словники України** | `sum.in.ua`, `slovnyk.ua` | Ukrainian dictionaries |
| **Енциклопедія сучасної України** | `esu.com.ua` | Encyclopedia |
| **Chytomo** | `chytomo.com` | Literary analysis |
| **Читанка** | `chtyvo.org.ua` | Ukrainian literature |
| **Українська правда** | `pravda.com.ua` | Contemporary context |

### Blocked Sources (NEVER Use)

| Source | Why Blocked |
|--------|-------------|
| `ru.wikipedia.org` | Russian language, imperial narratives |
| `*.ru` domains | Russian sources |
| `cyberleninka.ru` | Russian academic repository |
| `lib.ru` | Russian library |
| Any source in Russian | Language policy violation |

### Web Search Configuration

When using `WebSearch`, always include domain restrictions:

```python
# CORRECT — Ukrainian sources only
WebSearch(
    query="Іван Мазепа гетьман",
    allowed_domains=["uk.wikipedia.org", "litopys.org.ua", "history.org.ua", "esu.com.ua"]
)

# WRONG — Opens Russian results
WebSearch(query="Иван Мазепа")  # Russian query = Russian results
WebSearch(query="Ivan Mazepa")  # English query may return Russian sources
```

### Search Query Language Rules

| ✅ DO | ❌ DON'T |
|-------|----------|
| `Богдан Хмельницький повстання` | `Богдан Хмельницкий восстание` |
| `Київська Русь історія` | `Киевская Русь история` |
| `Тарас Шевченко біографія` | `Тарас Шевченко биография` |
| `козацтво Запорозька Січ` | `казачество Запорожская Сечь` |

### Verification Checklist

Before using ANY source, verify:

- [ ] Domain is `.ua` or `uk.wikipedia.org`
- [ ] Text is in Ukrainian (not Russian)
- [ ] Author/institution is Ukrainian
- [ ] Content reflects Ukrainian scholarly perspective
- [ ] No Russian imperial terminology (e.g., "Малороссия", "воссоединение")

### Red Flags — Reject Source If:

- Uses "Малороссия" instead of "Україна"
- Uses "воссоединение" instead of "приєднання" or "договір"
- Frames Ukrainian history as subset of Russian history
- Uses Russian-language quotations without Ukrainian translation
- Published by Russian institution or in Russia

---

## The Problem (Solved)

Complex historical and literary modules were failing because:
1. **Wrong activity requirements** - Attempting to use drill-style activities for seminar-style content.
2. **No research phase** - Generating from memory instead of using corpus/primary source knowledge.
3. **Word count anxiety** - Trying to hit 3000-4000 words without sufficient factual substance.

## The Solution: Research-First Workflow

### Phase 0: Deep Research (BEFORE writing)

> **LANGUAGE REQUIREMENT**: All searches and sources MUST be in Ukrainian.
> Use `allowed_domains` parameter to restrict to `.ua` sites.

**Required steps:**
1. **Search Ukrainian Wikipedia** (`uk.wikipedia.org`) for the figure — NEVER `ru.wikipedia.org`
2. **Search academic sources** — `history.org.ua`, `esu.com.ua`, `litopys.org.ua`
3. List all major life events, achievements, quotes, controversies
4. Find primary source quotes (their own words, contemporaries) — in Ukrainian
5. Identify connections to other Ukrainian figures (for cross-references)
6. Note specific dates, places, works, institutions

**Search Example:**
```python
# For biographical research
WebSearch(
    query="Леся Українка біографія життєпис",
    allowed_domains=["uk.wikipedia.org", "esu.com.ua", "chytomo.com"]
)

# For historical events
WebSearch(
    query="Батуринська трагедія 1708",
    allowed_domains=["uk.wikipedia.org", "history.org.ua", "litopys.org.ua"]
)

# For primary sources (OES/RUTH)
WebSearch(
    query="Літопис Самовидця текст",
    allowed_domains=["litopys.org.ua", "izbornyk.org.ua"]
)
```

**Output**: Research notes with specific details to reference while writing — ALL IN UKRAINIAN.

### Phase 1: Structured Outline with Word Targets

Map research to required sections with word allocations:

| Section | Target Words | Content Focus |
|---------|--------------|---------------|
| Вступ | 300-500 | Hook, why this person matters, European/Ukrainian context |
| Життєпис | 1000-1500 | Chronological narrative with specific dates, places, events |
| Досягнення | 800-1000 | Major contributions, works, influence |
| Спадщина | 500-700 | Legacy, modern relevance, rehabilitation |
| Підсумок | 200-300 | Summary, key takeaways |

**Total**: 2800-4000 words

### Phase 2: Write with Research Notes Open

- Reference research as you write
- Include specific details (dates, places, quotes)
- Build authentic 4000+ words from real content
- Use engagement boxes (💡, 🇺🇦, 🌍) for cultural depth
- Include at least 1 primary source quote

### Phase 3: Activities (ONLY 4-9 needed!)

**Activity Requirements (Seminar Style):**
> **Applies to:** C1-BIO, C1-HIST, OES, RUTH, LIT (B2-HIST may vary)

- Min activities: **4**
- Max activities: **9**
- Items per activity: **1+**
- Required types: `reading`, `essay-response`, `critical-analysis`

**Typical activity set:**
1. `reading` - External reading assignment with linguistic analysis
2. `essay-response` - 250-400 word essay prompt (NO model answer)
3. `critical-analysis` - Deep analytical questions about sources/legacy
4. (Optional) `comparative-study` or `quiz`

### Phase 4: Audit and Fix

Run audit to verify:
- Word count: 4000+ (95%+ of target)
- Activities: 4-9 with required types
- Richness: 95%+ (engagement boxes, quotes, tables)
- Naturalness: 8/10+ Ukrainian quality

---

## Example: Ivan Mazepa Module

### Research Notes (Phase 0)
```
- Born: March 20, 1639, Mazepyntsi (Kyiv oblast)
- Parents: Adam-Stepan (Khmelnytsky's associate), Marina Mokiyevska (later Abbess)
- Education: Kyiv-Mohyla → Warsaw Jesuits → Deventer (Netherlands)
- Languages: Latin, Italian, German, French, Polish, Russian
- Page to Jan II Kazimierz (1656-1659)
- Sirko's prophecy: "Ukraine will need this man"
- Hetman: 1687-1709 (22 years - record)
- Cultural: Mazepa Baroque, 100,000 gold to Academy, 1701 status
- Buildings: Sofia restoration, Миколаївський собор (13 domes), Братський монастир
- Intellectuals: Stefan Yavorsky, Feofan Prokopovych
- Baturyn: November 2, 1708 - Menshikov assault, 6,000-15,000 casualties
- Poltava: June 27, 1709 - defeat
- Death: September 21, 1709, Bendery
- Anathema: 1708-2024 (lifted by OCU)
```

### Outline with Word Targets (Phase 1)
```
1. Вступ (500 words) - Romantic myth vs. reality, European choice
2. Молоді роки (700 words) - Birth, education, European travels
3. Козацька кар'єра (600 words) - Ruina, Doroshenko, Sirko, Samoilovych
4. Культурне будівництво (800 words) - Mazepa Baroque, Academy, printing
5. Великий розрив (1000 words) - Peter I, Baturyn, Poltava
6. Вигнання та спадщина (500 words) - Exile, death, rehabilitation
7. Підсумок (200 words) - Summary
```

---

## Key Principles

1. **4000 words is achievable** - With proper research, you could write 10,000 words about these figures
2. **Use your corpus** - Ukrainian Wikipedia, school content, academic sources
3. **Specific details matter** - Dates, names, places make content authentic
4. **Activities are light** - Only 4-9 needed, not 96+
5. **Research first, write second** - Never generate from memory alone

---

## Quick Reference

| Metric | Seminar Style Requirement |
|--------|-------------------|
| Word target | 4000 |
| Min activities | 4 |
| Max activities | 9 |
| Items per activity | 1+ |
| Required activity types | reading, essay-response, critical-analysis |
| Engagement boxes | 6+ |
| Primary sources | 1+ quote |
| Immersion | 100% Ukrainian |
| Naturalness | 8/10+ |
