# C1-BIO Module Template (AI-Optimized)

> **Full documentation:** `docs/l2-uk-en/templates/c1-biography-module-template.md`
> **Config source of truth:** `scripts/audit/config.py` → `C1-biography`

---

## PHASE 1: BEFORE WRITING

### Step 1.1: Research Figure

```
⛔ STOP: Do NOT generate biographies from memory.
Biographical content requires verified facts.

DO:
1. WebSearch: "[Figure name] site:esu.com.ua"  # PRIMARY SOURCE
2. WebSearch: "[Figure name] site:memory.gov.ua"  # 20th century figures
3. WebSearch: "[Figure name] біографія site:.gov.ua"
4. WebFetch: https://esu.com.ua/article-[id]

DO NOT:
- Use Wikipedia as primary source (information warfare risk)
- Invent birth/death dates
- Generate quotes from memory
- Invent family members, teachers, associates
```

### Step 1.2: Find Primary Sources

```
DO:
1. WebSearch: "[Figure name] листи"
2. WebSearch: "[Figure name] промови"
3. WebSearch: "[Figure name] цитати"
4. WebFetch: [URLs for actual documented quotes]

REQUIRED: At least 2 primary source quotes verified
```

### Step 1.3: Verify URLs

```
⛔ STOP: Before using any external URL:
1. WebFetch to confirm page exists
2. Verify page is about the CORRECT person (common name collisions!)
3. Check page contains substantial biographical content
```

---

## PHASE 2: WRITE CONTENT

### Step 2.1: Create Files

```
CREATE 3 files:
1. curriculum/l2-uk-en/c1-bio/{slug}.md        # Prose content
2. curriculum/l2-uk-en/c1-bio/vocabulary/{slug}.yaml  # Vocabulary
3. curriculum/l2-uk-en/c1-bio/activities/{slug}.yaml  # Activities
```

### Step 2.2: Write Markdown Content

**Required sections (in order):**

| Section | Words | Content |
|---------|-------|---------|
| `# Title` + `🎯 Чому це важливо?` | 100-150 | Figure's significance |
| `## Вступ` | 200-300 | Dramatic opening, context |
| `## Біографія` | 800-1000 | Main narrative with subsections |
| `## Історичний контекст` | 300-400 | Era, political/cultural context |
| `## Порівняльний аналіз` | 300-400 | Compare with contemporary/contrasting figure |
| `## Підсумок` | 100-150 | Summary |

**Total target: 4000+ words**

### Step 2.3: Biography Section Structure

```markdown
## Біографія

### Ранні роки
[200-250 words about birth, childhood, education]

**Ключові дати:**
| Рік | Подія |
|-----|-------|
| [Year] | [Event] |

### Шлях до визнання
[300-350 words about rise to prominence]

> 📜 **Первинне джерело**
> [Quote from figure's letters/speeches — 50-100 words]
> *— Джерело: [Attribution]*

### Головні досягнення
[250-300 words about contributions]

### Останні роки / Сучасний етап
[200-250 words]

### Спадщина / Вплив
[200-250 words about legacy]

> 🌍 **Сучасна Україна**
> [How figure is remembered today]
```

### Step 2.4: Forbidden Patterns

```
DO NOT include:
- ## Vocabulary header (injected from YAML)
- ## Activities header (injected from YAML)
- ## Есе section (essay goes in activities YAML only)
- Conversational dialogs (biography is READING-CENTRIC)
- Factual recall questions (dates, places, names)
```

---

## PHASE 3: WRITE ACTIVITIES YAML

### Step 3.1: Activity Requirements

```yaml
# activities/{slug}.yaml

# REQUIRED (per config.py C1-biography):
min_activities: 4
max_activities: 9
required_types:
  - reading        # External reading with linguistic analysis
  - essay-response # 250-400 word essay
  - critical-analysis  # Deep analytical questions
```

### Step 3.2: Reading Activity Template

```yaml
- type: reading
  id: c1-bio-XX-reading-01
  title: "Первинні джерела: Листи/Промови"
  resource:
    type: primary_source
    url: "https://..."  # VERIFY URL EXISTS
    title: "[Figure Name]: [Document Title]"
  tasks:
    - "Який регістр використовує автор у цьому документі?"
    - "Знайдіть три приклади емоційно забарвленої лексики"
    - "Порівняйте мову автора з сучасною українською"
```

```
⚠️ CRITICAL: Questions must test LANGUAGE, not biographical facts.

✅ GOOD: "Який регістр використовує автор?"
❌ BAD:  "У якому році народився автор?"
```

### Step 3.3: Essay Activity Template

```yaml
- type: essay-response
  id: c1-bio-XX-essay-01
  title: "Есе: Порівняльний аналіз"
  prompt: |
    Напишіть порівняльне есе (250-400 слів):
    "[Figure 1] та [Figure 2]: Порівняльний аналіз внеску"

    Вимоги:
    - Використайте лексику модуля
    - Наведіть цитати з первинних джерел
    - Порівняйте підходи та спадщину
  rubric:
    - criterion: Мовна якість
      weight: 40
    - criterion: Використання матеріалу
      weight: 30
    - criterion: Порівняльний аналіз
      weight: 20
    - criterion: Структура
      weight: 10
```

### Step 3.4: Critical Analysis Template

```yaml
- type: critical-analysis
  id: c1-bio-XX-analysis-01
  title: "Критичний аналіз спадщини"
  questions:
    - "Як сучасна українська культура оцінює внесок цієї постаті?"
    - "Які аспекти діяльності залишаються дискусійними?"
    - "Як деколонізаційний підхід змінює оцінку цієї постаті?"
```

---

## PHASE 4: WRITE VOCABULARY YAML

### Step 4.1: Vocabulary Requirements

```yaml
# vocabulary/{slug}.yaml

# Per config.py C1-biography:
min_items: 30
format: 3-column (lemma, translation, note)
```

### Step 4.2: Vocabulary Template

```yaml
items:
  - lemma: [Ukrainian word]
    translation: [English]
    note: [biographical context/collocation]
```

**Include categories:**
- Biographical terms (постать, спадщина, внесок)
- Domain-specific (literature, politics, science, arts)
- Historical vocabulary (era-specific terms)
- Decolonization terms (if applicable)

---

## PHASE 5: VALIDATE

### Step 5.1: Pre-Submission Checklist

```
⛔ STOP: Verify ALL before submitting.

CONTENT:
- [ ] 4000+ words (prose only)
- [ ] ≥2 primary source quotes with [!quote] callouts
- [ ] Historical context section
- [ ] Comparative analysis section
- [ ] Decolonization lens (Ukrainian perspective)
- [ ] NO dialogs (reading-centric only)
- [ ] No ## Vocabulary or ## Activities headers

ACTIVITIES (in YAML):
- [ ] 4-9 activities total
- [ ] Includes reading activity (linguistic analysis)
- [ ] Includes essay-response (250-400 words)
- [ ] Includes critical-analysis
- [ ] All URLs verified with WebFetch
- [ ] NO factual recall questions (dates, places, names)

VOCABULARY (in YAML):
- [ ] 30+ items
- [ ] 3-column format (lemma, translation, note)

SOURCES:
- [ ] Dates verified from ЕСУ or .gov.ua
- [ ] Quotes from actual documented sources
- [ ] No Wikipedia-only claims
```

### Step 5.2: Run Audit

```bash
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/c1-bio/{slug}.md
```

---

## QUICK REFERENCE

### Key Academic Resources

| Domain | Primary Resources |
|--------|-------------------|
| **Literature** | esu.com.ua, litopys.org.ua, ukrlib.com.ua |
| **Politics/Military** | memory.gov.ua, history.org.ua, esu.com.ua |
| **Science/Academia** | nas.gov.ua, esu.com.ua |
| **Arts/Culture** | esu.com.ua, namu.kiev.ua |
| **Religious figures** | risu.ua, esu.com.ua |
| **Contemporary** | ukrinform.ua, president.gov.ua |

### Activity Question Guide

| ❌ BAD (Tests Facts) | ✅ GOOD (Tests Language) |
|---------------------|-------------------------|
| "Шевченко народився в [___] році." | "Згідно з текстом, Шевченко [___] визначну роль." |
| "Хто викупив Шевченка?" | "Як автор характеризує вплив постаті?" |
| "Де навчався автор?" | "Який регістр використовує автор?" |

**Key phrases to use:**
- "Згідно з текстом..."
- "Як автор характеризує..."
- "Який внесок автор виділяє..."

### Decolonization Corrections

| Colonial Myth | Ukrainian Reality |
|---------------|-------------------|
| Shevchenko = "Russian poet" | Ukrainian poet persecuted by Russian Empire |
| Mazepa = "Traitor" | Defender of Ukrainian autonomy |
| Hrushevsky = "Nationalist" | Historian documenting Ukrainian statehood |

---

**Template version:** 2.0-ai
**Last updated:** 2026-01-24
