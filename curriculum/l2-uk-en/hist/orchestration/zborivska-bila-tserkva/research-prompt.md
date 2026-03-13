# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: hist-054
level: HIST
sequence: 54
slug: zborivska-bila-tserkva
version: '2.0'
title: Зборівська та Білоцерківська угоди
subtitle: The Treaties of Zboriv and Bila Tserkva
focus: history
pedagogy: CBI
phase: HIST.6 [Khmelnytsky & Cossack State]
word_target: 5000
objectives:
- Учень може пояснити умови Зборівського та Білоцерківського договорів
- Учень може проаналізувати причини дипломатичних поступок Хмельницького
- Учень може порівняти територіальні межі автономії за різними угодами
sources:
- name: History of Ukraine-Rus
  url: http://litopys.org.ua/hrushrus/iur.htm
  type: reference
  notes: Detailed analysis of treaties
- name: Diplomacy of Bohdan Khmelnytsky
  url: https://history.org.ua
  type: reference
  notes: International context
content_outline:
- section: 'Вступ: Між перемогами та миром'
  points:
  - 'Diplomatic situation after Zboriv (1649) — context of the English Revolution (execution of Charles I) and the Fronde
    in France: a world in turmoil; cultural hook: [!context]'
  - The goals of the Hetmanate vs. the Crown — shift from seeking 'pardon' to the goal of 'liberating the Rus' people from
    Polish bondage'
  words: 550
- section: 'Зборівський договір (1649): Перше визнання'
  points:
  - 'Key conditions: 40,000 register, three voivodeships — signed August 18, 1649; exclusion of Crown army from Kyiv, Bratslav,
    and Chernihiv voivodeships'
  - 'Legal status of the Hetmanate — factual recognition of a separate territory and administration (Orthodox nobility only);
    engagement hook: [!history-bite] regarding the ban on Jesuit colleges'
  - The role of the Orthodox Church — the Metropolitan of Kyiv granted a seat in the Senate (though opposed by Catholic bishops)
  words: 550
- section: Берестечко та поворот подій
  points:
  - The impact of the 1651 defeat — the scale of the battle (largest in 17th-century Europe); the tactical masterpiece of
    Bohun's retreat
  - 'Shift in the balance of power — the retreat of Islam-Girey and Khmelnytsky''s captivity; engagement hook: [!myth-buster]
    on the ''Tatar betrayal'' vs. geopolitical pragmatism'
  words: 550
- section: 'Білоцерківський договір (1651): Гіркий компроміс'
  points:
  - Reduction of the register (20,000) — signed September 28, 1651; drastic cut from the previous 40k
  - Territorial losses (only Kyiv voivodeship) — Bratslav and Chernihiv voivodeships return to Polish administration
  - 'Social tension and dissatisfaction among Cossacks — the prohibition of foreign relations (especially with Crimea); engagement
    hook: [!decolonization] ''Not a defeat, but a pause'''
  words: 550
- section: 'Читання: Тексти угод'
  points:
  - 'Analysis of the Zboriv articles — comparison of preambles: ''Declaration of Grace'' (Zboriv) vs. ''Humble Subjecthood''
    (Bila Tserkva)'
  words: 550
- section: Первинні джерела
  points:
  - 'Ossonlinski and Khmelnytsky quotes — Jerzy Ossoliński: ''The only means of salvation is to separate the Tatars from the
    Cossacks''; Khmelnytsky on divine providence and victory'
  words: 550
- section: 'Аналіз: Дипломатія як мистецтво можливого'
  points:
  - Khmelnytsky's tactical retreat — Zboriv provided legitimacy, Bila Tserkva provided time
  - Preserving the core of the state — treaties as acts of state-building, not just truce in a rebellion
  words: 550
- section: 'Деколонізаційний погляд: Вихід з-під польського права'
  points:
  - 'Treaties as steps towards total sovereignty — engagement hook: [!analysis] on ''Subjecthood'' (international recognition);
    debunking the Soviet myth of ''class struggle'''
  - 'Debunking the ''betrayal'' narrative — contested terms: ''Treason'' vs. ''Pragmatic Politics'' regarding the Crimean
    Khanate'
  words: 550
- section: Спадщина угод та історична пам'ять
  points:
  - Impact on future legal acts — Zboriv as the prototype for the Union of Hadiach (1658); the lesson that diplomacy requires
    a strong army (Berestechko -> Bila Tserkva)
  words: 600
vocabulary_hints:
  required:
  - угода (agreement/treaty) — Зборівська угода, підписати угоду
  - компроміс (compromise) — піти на компроміс, вимушений компроміс
  - автономія (autonomy) — широка автономія, урізана автономія
  - ратифікація (ratification) — ратифікація сеймом, чекати ратифікації
  - воєводство (voivodeship) — Київське воєводство, три воєводства
  - амністія (amnesty) — повна амністія, оголосити амністію
  - шляхта (nobility) — православна шляхта, права шляхти
  - реєстр (register) — козацький реєстр, скорочення реєстру
  - легітимність (legitimacy) — державна легітимність, визнання легітимності
  - поступка (concession) — територіальні поступки, дипломатичні поступки
  recommended:
  - сейм (Sejm/Parliament) — рішення сейму
  - митрополит (Metropolitan) — Київський митрополит
  - універсал (Universal/Manifesto) — гетьманський універсал
  - суверенітет (sovereignty) — кроки до суверенітету
  - геополітика (geopolitics) — складна геополітика
activity_hints:
- type: reading
  focus: Analysis of diplomatic documents
- type: essay-response
  focus: Evolution of Cossack autonomy
- type: critical-analysis
  focus: 'Спростування міфів: Common myths about the compromises'
  items: 4
- type: comparative-study
  focus: Zboriv vs. Bila Tserkva territorial changes
persona:
  voice: Senior Professor of History
  role: Treaty Negotiator
grammar:
- 'Diplomatic register: official terminology'
- Conditional sentences in negotiations
register: публіцистичний
prerequisites:
- bitva-pid-zhovtymy-vodamy
connects_to:
- kozatska-derzhava

```

---

## PART 1: Deep Research

Research **Зборівська та Білоцерківська угоди** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Зборівська та Білоцерківська угоди

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — Phase D verifies prose against this -->
```yaml
subject: "Зборівська та Білоцерківська угоди"
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
