# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: hist-041
level: HIST
sequence: 41
slug: kozatstvo-vytoky
version: '2.0'
title: 'Козацтво: витоки'
subtitle: Origins of Cossackdom
focus: history
pedagogy: seminar
phase: HIST.5 [Становлення козацтва]
word_target: 5000
objectives:
- Учень може пояснити етимологію терміна «козак» та його тюркське коріння
- Учень може проаналізувати соціально-економічні причини виникнення козацтва, зокрема роль уходництва
- Учень може описати географічний контекст Дикого поля та його вплив на формування козацького соціуму
- Учень може оцінити деколонізаційну перспективу на козацтво як на самостійну політичну силу
sources:
- name: Гійом Левассер де Боплан, «Опис України»
  url: http://litopys.org.ua/boplan/bop.htm
  type: primary
  notes: Ключове джерело XVII століття про побут та характер козаків
- name: 'Ярослав Грицак, «Подолати минуле: глобальна історія України»'
  url: https://shron1.chtyvo.org.ua/Hrytsak_Yaroslav/Podolaty_mynule_hlobalna_istoriia_Ukrainy.pdf
  type: secondary
  notes: Сучасний синтез історії України з акцентом на глобальних процесах
content_outline:
- section: 'Вступ: Дике поле як колиска свободи'
  points:
  - Географічне поняття Дикого поля — степова зона на південь від лінії Канів-Черкаси, зона ризику та природних багатств
  - Геополітичне розташування між християнським світом і Степом — [!context] Дике поле не було пустелею, а «Великим Кордоном»,
    де зустрічалися цивілізації
  - Значення козацтва для сучасної української ідентичності — архетип свободи та опору, центральний міф націєтворення
  words: 850
- section: 'Читання: Генезис та уходництво'
  points:
  - Етимологія слова «козак» та його еволюція — тюркське «kazak» (вільна людина, вартовий), вперше у Codex Cumanicus (XIII
    ст.)
  - Феномен уходництва як економічна база — сезонні промисли (риба, мед), перетворення на воїнів для захисту здобичі; [!history-bite]
    Козаки-«амфібії»
  - Втеча від кріпацтва та соціальний протест — перші згадки (1489, 1492); «хліб козацький» (слави і здобичі) як мотивація
    для шляхти
  words: 850
- section: Козацький побут та військова організація
  points:
  - Формування куренів та принцип побратимства — [!culture] ритуал обміну хрестами, зв'язок сильніший за кровний
  - Військова тактика та озброєння (табір, чайки) — «рухома фортеця» з возів, маневрені човни без кіля, тактика «галасу»
  - Аскетизм побуту як необхідність виживання — [!quote] Боплан про витривалість до голоду, спраги і спеки
  words: 850
- section: Первинні джерела
  points:
  - Аналіз описів Гійома де Боплана — «Опис України» (1651) французького інженера; погляд іноземця на «майстрів виживання»
  - Документальні свідчення про перші козацькі атаки — скарга хана Менглі-Гірея (1492) на пограбування корабля під Тягинею
  - Лінгвістичний аналіз мови джерел — Літопис Самовидця як приклад козацького самоопису
  words: 850
- section: Козацтво у геополітиці
  points:
  - 'Відносини з Кримським ханством: війна і торгівля — [!myth-buster] не лише війна, а й ситуативні союзи та спільні походи'
  - 'Політика Речі Посполитої: реєстр та контроль — Універсал Сигізмунда II Августа (1572) про 300 козаків; конфлікт через
    «випищиків»'
  words: 850
- section: Деколонізаційний погляд
  points:
  - Спростування міфу про «бандитизм» — [!decolonization] козацтво як полісоціальне явище (шляхта, міщани), а не лише селянський
    бунт
  - Козацтво як суб'єкт державотворення — самостійна дипломатія (з Імператором, Папою), Дмитро Вишневецький та перша Січ (1550-ті)
  - Сучасна інтерпретація спадщини — фундамент політичної культури (виборність, контрактові відносини)
  words: 750
vocabulary_hints:
  required:
  - уходник (frontier industrialist) — сезонний промисловий, що ставав воїном
  - здобичник (booty seeker) — шукач «козацького хліба»
  - 'ясир (captives) — context: slave trade raids by Tatars'
  - реєстр (register) — список 1572 року, еліта війська
  - Дике поле (Wild Fields) — Великий Кордон, frontier zone
  - побратимство (brotherhood) — ritual kinship, exchange of crosses
  - етимологія (etymology) — Turkic origin 'kazak', Codex Cumanicus
  - кріпацтво (serfdom) — escape from serfdom vs attraction of freedom
  recommended:
  - промисел (industry/trade) — fishing, beekeeping, hunting
  - ватага (band/group) — organized group of ukhodnyky
  - шабля (sabre) — symbol of knightly status
  - чайка (cossack boat) — maneuverable boat for river/sea raids
activity_hints:
- type: reading
  focus: Аналіз описів Гійома де Боплана
  source: Боплан, «Опис України»
- type: essay-response
  focus: Деколонізаційний аналіз витоків козацтва
- type: critical-analysis
  focus: Порівняння уходництва та кріпацтва
connects_to:
- 'hist-42: Запорізька Січ'
- 'hist-43: Дмитро Вишневецький'
prerequisites:
- Знання історії Великого князівства Литовського та Люблінської унії
persona:
  voice: Senior Professor of History
  role: Runaway Serf
grammar:
- 'Історичний наратив: вживання минулого часу'
- Пасивні конструкції в історичних описах
- Складнопідрядні речення з підрядними причини та наслідку
register: публіцистичний

```

---

## PART 1: Deep Research

Research **Козацтво: витоки** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

### Your RAG Tools (USE THEM)

You have access to Ukrainian language tools via MCP. **Use them during research.**

| Tool | When to use | Example |
|------|-------------|---------|
| `query_wikipedia` mode=`extract` | Get full article text (50K chars) for deep research | `query_wikipedia("Богдан Хмельницький", mode="extract")` |
| `query_wikipedia` mode=`sections` | See article structure before diving in | `query_wikipedia("Запорізька Січ", mode="sections")` |
| `query_wikipedia` mode=`section` | Read a specific section by index | `query_wikipedia("Запорізька Січ", mode="section", section=3)` |
| `query_wikipedia` mode=`search` | Find the right article title | `query_wikipedia("Переяславська рада", mode="search")` |
| `search_literary` | Find primary source excerpts (chronicles, poetry, legal texts) | `search_literary("Хмельницький", genre="chronicle")` |
| `verify_word` / `verify_words` | Check Ukrainian words exist in VESUM dictionary | `verify_words(["гетьман", "козацтво"])` |
| `query_grac` | Check word frequency in Ukrainian corpus | `query_grac("упокорення", mode="frequency")` |

**Workflow**: Search Wikipedia FIRST for factual foundation → search literary RAG for primary quotes → verify vocabulary with VESUM.

### Research Requirements

1. **Sources**: Use `query_wikipedia` (mode=`extract`) for Ukrainian Wikipedia articles. Also consult history.org.ua, litopys.org.ua. Use `search_literary` for primary source excerpts. Russian-language sources are PROHIBITED.
2. **Timeline**: Build a chronological timeline with 5+ dated events/milestones.
3. **Primary Quotes**: Find 2+ quotable primary source excerpts (original Ukrainian text preferred).
4. **Engagement Hooks**: Identify 6+ engagement hooks mapped to specific content sections:
   - `[!myth-buster]` — Decolonization: correct imperial/Soviet myths
   - `[!history-bite]` — Surprising or lesser-known facts
   - `[!context]` — Broader historical/cultural context
   - `[!quote]` — Primary source citations
   - `[!decolonization]` — Ukraine-centric reframing
   - `[!culture]` — Cultural significance
5. **Decolonization Angle**: Identify how this topic has been distorted by imperial/Soviet historiography and what the Ukrainian-centric framing should be.
6. **Section-Mapped Content**: Structure notes with headings that match the `content_outline` sections from the plan. This makes Phase B content writing mechanical.

### Research Output Cap
Keep research notes under **4000 words** (seminar tracks need depth for historiographical mapping).
Focus on density: Key Facts Ledger, timeline, primary quotes, section-mapped notes.

If this topic involves contested narratives (Ukrainian vs. Russian/Soviet/Polish historiography), include a Contested Terms Table:

```markdown
## Contested Terms

| Concept | Imperial framing | Ukrainian (decolonized) framing |
|---------|-----------------|-------------------------------|
| ...     | ...             | ...                           |
```

---

## Downstream Audit Gates (Phase B content will be checked for)

Plan your research and outline knowing that Phase B content must pass these gates:
- **Word count**: minimum **5000** words — allocate outline sections accordingly
- **Colonial framing**: plan decolonized framing NOW so Phase B doesn't default to Russian comparisons
- **Engagement callouts**: map 6+ hooks to specific sections during research (not as afterthought patches)
- **Duplicate headers**: ensure outline section names don't share keywords

---

## Output Format

> **DELIMITER ENFORCEMENT**: Content outside delimiters is automatically discarded by the extraction pipeline.

### Output Block 1: Research Notes

```
===RESEARCH_START===

# Дослідження: Козацтво: витоки

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — Phase D verifies prose against this -->
```yaml
subject: "Козацтво: витоки"
vital_status: "deceased" # or "alive"
dates:
  birth: "YYYY-MM-DD"    # or approximate: "~YYYY"
  death: "YYYY-MM-DD"    # omit if alive
  key_events:
    - year: YYYY
      event: "Event description (Ukrainian)"
    - year: YYYY
      event: "Event description"
primary_quotes:
  - text: "Exact Ukrainian quote"
    source: "Source name, year"
    attribution: "Who said/wrote it"
  - text: "..."
    source: "..."
    attribution: "..."
forbidden_claims:
  - "Common myth or Russian propaganda claim to avoid"
  - "..."
```

## Використані джерела
1. [Source name](URL) — brief description
2. ...
3. ...

## Хронологія
- {date}: {event}
- ...

## Ключові факти та цитати
- ...

## Engagement Hooks (mapped to sections)
- Section "{section_name}": [!hook_type] — description
- ...

## Деколонізаційний контекст
- Imperial/Soviet myth: ...
- Ukrainian reality: ...

## Contested Terms (if applicable)
| Concept | Imperial framing | Ukrainian framing |
|---------|-----------------|-------------------|
| ...     | ...             | ...               |

## Відеоресурси
(Якщо під час дослідження ви натрапили на релевантні відеоматеріали — документальні фільми, архівні записи, інтерв'ю — зазначте їх тут. НЕ шукайте відео спеціально — це робить фаза discover. Максимум 3 записи.)
- {Канал — Назва — URL — Короткий опис релевантності}
- (нічого не знайдено)

## Section-Mapped Research Notes

### {Section 1 from content_outline}
Key facts, dates, sources for this section...

### {Section 2 from content_outline}
...

===RESEARCH_END===
```

## Friction Report (MANDATORY)

After both output blocks, include:

```
===FRICTION_START===
**Phase**: Phase A: Research + Meta (Seminar)
**Step**: {what you were doing when friction occurred, or "Full Phase A"}
**Friction Type**: NONE | TOKEN_LIMIT_TRUNCATION | TOOL_REDUNDANCY | SOURCE_NOT_FOUND | ...
**Raw Error**: {actual error or "None"}
**Self-Correction**: {what you changed, or "N/A"}
**Proposed Tooling Fix**: {if a script/design issue, or "N/A"}
===FRICTION_END===
```

---

## Boundaries

- Do NOT write lesson content — only research notes
- Do NOT generate activities or vocabulary
- Do NOT skip any section from the plan's content_outline
- Do NOT use Russian-language sources
- Do NOT fabricate quotes or dates — if unsure, mark as "[needs verification]"
- Do NOT reference persona names or voice instructions — persona is assigned at content generation time
- Do NOT request skills, delegate to Claude, or skip this phase
