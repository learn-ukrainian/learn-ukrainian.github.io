# LIT Module Template (AI-Optimized)

> **Full documentation:** `docs/l2-uk-en/templates/lit-module-template.md`
> **Config source of truth:** `scripts/audit/config.py` → `LIT`

---

## PHASE 1: BEFORE WRITING

### Step 1.1: Confirm Track

```
⛔ STOP: This template is ONLY for LIT track (LIT-001 to LIT-030).

IF creating C1 literature modules (C1.6 M146-160)
  → USE c1-literature-module-template.md INSTEAD
  → STOP HERE

LIT = Graduate-level seminar for C1+ learners
C1 Literature = Language mastery through literature
```

### Step 1.2: Check Reference Modules

```
⛔ STOP: Before creating any LIT module, check reference archive.

LOCATION: curriculum/l2-uk-en/lit/reference/

Available references:
- module-LIT-001.md - Kotliarevsky (~54k words)
- module-LIT-002.md - Eneida Part I (~52k words)
- module-LIT-003.md - Eneida vocabulary (~49k words)
- module-LIT-004.md - Eneida military (~47k words)
- module-LIT-005.md - Natalka Poltavka (~48k words)
- module-LIT-006.md - Kvitka-Osnovianenko (~51k words)

USE for: Historical facts, vocabulary lists, essay topics, engagement ideas
DO NOT: Copy-paste verbatim — adapt to this template
```

### Step 1.3: Research Strategy

```
⛔ STOP: Do NOT generate literary analysis from memory.

DO:
1. WebSearch: "[author name] site:ukrlib.com.ua"
2. WebSearch: "[author name] біографія site:esu.com.ua"
3. WebFetch: https://www.ukrlib.com.ua/bio/printit.php?tid=[ID]
4. WebFetch: https://esu.com.ua/article-[id]

Common UkrLib author IDs (VERIFY before using):
- Котляревський: tid=1672
- Шевченко: tid=57
- Куліш: tid=1621
- Нечуй-Левицький: tid=1646
- Франко: tid=71

DO NOT:
- Use Wikipedia (information warfare risk)
- Generate quotes from memory
- Invent dates or facts
```

---

## PHASE 2: WRITE CONTENT

### Step 2.1: Create Files (Clean MD Architecture)

```
CREATE 4 files:
1. curriculum/l2-uk-en/lit/{slug}.md            # Prose ONLY (no frontmatter)
2. curriculum/l2-uk-en/lit/meta/{slug}.yaml     # Title, tags, objectives
3. curriculum/l2-uk-en/lit/vocabulary/{slug}.yaml  # Vocabulary
4. curriculum/l2-uk-en/lit/activities/{slug}.yaml  # Essays, reading tasks
```

### Step 2.2: Write Markdown Content

**Structure: Pure narrative lecture, no activities embedded**

| Section | Words | Content |
|---------|-------|---------|
| `# Ukrainian Title` | — | Module title only |
| `> 🇺🇦 **Ідентичність:**` | 50-100 | Cultural significance hook |
| `## Підсумок` | 150-200 | Overview of module |
| `## Частина I-XX` | 2200+ total | 15-20 themed sections |

**Total target: 4000+ words (with 2200+ core prose)**

### Step 2.3: Section Types

```
FOR Author Biography modules:
- Early life, education, formative experiences
- Professional career, key relationships
- Political involvement, controversies
- Legacy, influence on later writers

FOR Literary Work modules:
- Plot summary and structure
- Stylistic devices (metaphor, irony, symbolism)
- Themes and motifs
- Language and register analysis
- Historical/cultural context of creation

FOR Historical Context modules:
- Political situation (Ruin, Imperial censorship)
- Social conditions (serfdom, class structure)
- Literary movements (Romanticism, Realism)
- Cultural influences (European, Russian, Polish)
```

### Step 2.4: Engagement Boxes (6-8 throughout)

```markdown
> [!important] **Psychological Insight**
> [Academic insight about psychology/key idea]

> [!cultural] **Спадщина у Бронзі**
> [Cultural/historical significance]

> [!warning] **Myth Buster**
> **Міф:** [Common misconception]
> **Правда:** [Historical truth with evidence]

> [!note] **Historical Parallel**
> [Comparative or contextual information]

> [!tip] **Лінгвістичний Нюанс**
> [Language/style analysis]
```

### Step 2.5: Forbidden Patterns

```
DO NOT include in markdown:
- # Словник (injected from YAML)
- # 🏛️ Читальна Зала (injected from YAML)
- # ✍️ Аналітичний Практикум (injected from YAML)
- ANY traditional activities (quiz, fill-in, match-up)
- Latin characters (ZERO TOLERANCE except specialized linguistic terms)
- H1 headers except module title
```

---

## PHASE 3: WRITE ACTIVITIES YAML

### Step 3.1: Activity Requirements

```yaml
# activities/{slug}.yaml

# REQUIRED (per config.py LIT):
min_activities: 3
max_activities: 9
activity_types: [reading, essay-response, debate]
NO traditional activities: quiz, fill-in, match-up, etc.
```

### Step 3.2: Reading Activity Template (External Resource)

```yaml
- type: reading
  id: reading-bio                    # REQUIRED for linking
  title: Біографія [Author]
  resource:
    type: Biography
    url: https://www.ukrlib.com.ua/bio/printit.php?tid=[ID]  # VERIFY!
    title: "[Author]. Життя і творчість"
  tasks:
    - "Знайдіть паралелі між життям автора і сюжетом твору."
    - "Як вплинув [historical event] на творчість?"
    - "Порівняйте мову автора з сучасною українською."
```

### Step 3.3: Reading Activity Template (Inline Primary Source)

```yaml
- type: reading
  id: reading-poem                   # REQUIRED for linking
  title: 'Джерело: [Work Title]'
  source: '[Author Name] ([Year])'   # Attribution
  text: |
    [Full poem or excerpt text]
    [In original Ukrainian]
  tasks:
    - "Які географічні образи використовує поет?"
    - "Яка роль імперативу в тексті?"
    - "Знайдіть три приклади метафори."
```

### Step 3.4: Essay Activity Template

```yaml
- type: essay-response
  id: essay-analysis
  title: "Роль [topic]"
  source_reading: reading-bio  # Links to reading id above
  prompt: |
    Напишіть аналітичне есе (300-500 слів):
    "[Essay topic question]"

    Вимоги:
    - Використайте літературознавчу лексику модуля
    - Наведіть цитати з первинних джерел
    - Застосуйте критичний аналіз
  model_answer: |
    [Complete 300-500 word model answer demonstrating:
    - Academic tone
    - Literary analysis
    - Use of vocabulary
    - Citation of sources]
```

```
⚠️ CRITICAL: Every essay prompt MUST have a complete model_answer.
```

---

## PHASE 4: WRITE VOCABULARY YAML

### Step 4.1: Vocabulary Requirements

```yaml
# vocabulary/{slug}.yaml

# Per config.py LIT:
min_items: 30
max_items: 40
format: 3-column (lemma, translation, note)
```

### Step 4.2: Vocabulary Template

```yaml
items:
  - lemma: травестія
    translation: travesty (genre)
    note: комічне наслідування
  - lemma: бурлеск
    translation: burlesque
    note: стиль грубого комізму
```

**Include categories:**
- Literary terms (genre, style, device names)
- Historical terms (political/social concepts)
- Cultural terms (traditional practices, beliefs)
- Author vocabulary (unique words from the work)
- Archaic/dialectal forms

---

## PHASE 5: VALIDATE

### Step 5.1: Pre-Submission Checklist

```
⛔ STOP: Verify ALL before submitting.

FILE STRUCTURE:
- [ ] Clean Markdown: NO frontmatter, NO vocabulary table, NO activity lists
- [ ] Meta sidecar created in meta/
- [ ] Vocab sidecar created in vocabulary/
- [ ] Activities sidecar created in activities/

CONTENT:
- [ ] 2200+ words core prose narrative
- [ ] 15-20 content sections (Частини I-XX)
- [ ] 6-8 engagement boxes (all in Ukrainian)
- [ ] 100% Ukrainian (English ONLY in MDX description)
- [ ] NO Latin characters (run: grep -P "[a-zA-Z]")
- [ ] NO traditional activities

ESSAYS:
- [ ] 1-2 essay prompts (300-500 words)
- [ ] Model answers for ALL essays
- [ ] Academic tone, critical thinking

READING RESOURCES:
- [ ] UkrLib or equivalent links
- [ ] All URLs verified with WebFetch
- [ ] Reading guidance provided

QUALITY:
- [ ] University-level literary criticism
- [ ] Historical accuracy verified
- [ ] Decolonized narrative (Ukrainian perspective)
```

### Step 5.2: Run Audit

```bash
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/lit/{slug}.md
```

---

## QUICK REFERENCE

### No Reference Module? Bulk Content Strategy

```
IF no 50k-word reference exists:
1. Include 3-4 full pages (1000-1500 words) of original public domain text
2. Use UkrLib for full texts
3. Present as "Key Excerpts for Analysis" with blockquotes
4. Intersperse with philological commentary
```

### LIT vs C1/C2 Core

| Aspect | C1/C2 Core | LIT Track |
|--------|------------|-----------|
| Philosophy | Language mastery | Literary specialization |
| Word count | 2000-2200+ | 2200-3000+ |
| Vocabulary | 35-40 general | 30-40 literary/historical |
| Activities | 3-9 interactive | 3-9 essay-based only |
| Texts | Excerpts | Full works (external) |
| Focus | Language skills | Philological analysis |
| Pedagogy | TTT/CBI | Academic seminar |

### Phase Breakdown

| Phase | Modules | Focus |
|-------|---------|-------|
| LIT.1 | M001-005 | Kotliarevsky (burlesque, folk) |
| LIT.2 | M006-010 | Kvitka-Osnovianenko (sentimentalism) |
| LIT.3 | M011-020 | Shevchenko (Romanticism) |
| LIT.4 | M021-025 | Kulish & Kostomarov (Europeanism) |
| LIT.5 | M026-030 | Nechuy-Levytsky (Realism) |

### Cultural Sensitivity

```
✅ DO: "Ukrainian resisted Russian imperial suppression"
❌ DON'T: "Ukrainian developed from Russian influence"

✅ DO: Center Ukrainian experience
❌ DON'T: Use Russian Imperial/Soviet perspectives

✅ DO: Acknowledge trauma (Russification, censorship, executions)
❌ DON'T: Romanticize oppression
```

---

**Template version:** 2.0-ai
**Last updated:** 2026-01-24
