# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module).**
> **Your ONLY task: Research the topic. The plan's content_outline is the source of truth — do NOT generate a meta outline.**

---

## Your Input

**Plan file (SOURCE OF TRUTH):**

```yaml
module: hist-045
level: HIST
sequence: 45
slug: petro-sahaidachnyi
version: '2.0'
title: 'Петро Сагайдачний: Гетьман і меценат'
subtitle: The Knight of Orthodox Culture and Naval Glory
focus: history
pedagogy: CBI
phase: HIST.5 [Rise of Cossacks]
word_target: 5000
objectives:
- Learner can analyze the military and cultural reforms of Petro Sahaidachnyi
- Learner can explain the significance of the Battle of Khotyn (1621)
- Learner can understand the role of the Kyiv Epiphany Brotherhood School
content_outline:
- section: Вступ
  points:
  - Sahaidachnyi as a statesman-leader — architect of Cossack statehood; combining Sich energy with discipline and education
  - The transition to a professional cossack army — from disorganized bands to a regular army; symbol of transformation into
    a political nation
  words: 600
- section: Шлях від Кульчиць до Січі
  points:
  - Origins and education in Ostroh — noble birth (Pobuh coat of arms); contemporary of Meletiy Smotrytskyi; [!history-bite]
    intellectual with a sword
  - 'Military reforms: discipline and training — division into regiments/hundreds; firearms drills; ban on alcohol during
    campaigns (''overboard if caught'')'
  - 'The ''Marine'' strategy: Campaigns against Istanbul — turning Cossacks into Europe''s special forces; intellect winning
    over brute force'
  words: 600
- section: 'Військова слава: Кафа та Москва — шлях переможця'
  points:
  - The liberation of slaves in Caffa (1616) — blow to heart of slave trade; destruction of Turkish fleet; psychological impact
    on Ottomans
  - The campaign of 1618 and the siege of Moscow — saving Prince Wladyslaw; lightning march (Livny, Yelets); standing at Arbat
    gates; [!military] wolf pack tactics
  - Tactical innovations of the cossack fleet — night assaults; Deulino Truce triumph as Polish victory by Ukrainian hands
  words: 600
- section: 'Читання: Голос барокової епохи'
  points:
  - 'Analysis of ''The Lament over the Grave of Sahaidachnyi'' by Sakovych — [!source] Cossacks as heirs to Kyivan Rus princes;
    legitimization through history and faith; quote analysis: ''freedom bought with blood'''
  words: 600
- section: 'Меценатство та Освіта: Революція духу'
  points:
  - Support for the Kyiv Brotherhood — enrollment of entire Zaporozhian Host; protection of culture/school; [!myth-buster]
    Cossacks as collective patron
  - Restoration of the Orthodox hierarchy (1620) — Patriarch Theophanes III; consecration of Job Boretsky; restoration of
    spiritual statehood
  - The union of the 'sword and the book' — alliance of military force and intellectual elite; legitimizing Cossacks as 'knights'
    of the people
  words: 600
- section: 'Хотинська епопея (1621): Битва за майбутнє Європи'
  points:
  - The clash of civilizations at Khotyn — Sultan Osman II vs Poland; stopping largest army in the world; [!context] Khotyn
    as 17th-century Thermopylae
  - The decisive role of cossacks in saving Europe — wagon fort (wagenburg) tactics; night raids; sniper fire; saving Europe
    from Islamic expansion
  - The fatal wound and death of the Hetman — poisoned arrow wound; death in Kyiv (1622); burial at Bratsky Monastery
  words: 600
- section: 'Первинні джерела: Свідчення очевидців та славослів''я'
  points:
  - 'Excerpts from contemporary panegyrics — Kyiv Brotherhood school texts; Sahaidachnyi''s will: patron to the last breath'
  - 'Foreign accounts of Khotyn — Jakub Sobieski quote: ''Real winners were Cossacks'''
  words: 600
- section: 'Деколонізаційний погляд: Повернення справжнього гетьмана'
  points:
  - Sahaidachnyi as a European-style knight, not an imperial servant — autonomous geopolitical player; blackmailing Warsaw;
    building Hetmanate foundation
  - Reclaiming the naval heritage of Ukraine — [!decolonization] dominance of Black Sea before Russian Empire; scale of Cromwell
    or Wallenstein
  words: 800
vocabulary_hints:
  required:
  - 'гетьман (hetman) — collocations: кошовий отаман, булава гетьмана'
  - 'меценат (patron) — context: підтримка освіти, церков'
  - 'січ (Sich) — context: Запорозька Січ, козацька республіка'
  - 'братство (brotherhood) — context: Київське братство, вступ війська'
  - 'військо (army/host) — collocations: Військо Запорозьке, реєстрове козацтво'
  - 'кампанія (campaign) — context: Московська кампанія, морські походи'
  - 'угода (agreement/truce) — context: Деулінське перемир''я, Хотинський мир'
  - 'ієрархія (hierarchy) — context: відновлення православної ієрархії'
  recommended:
  - 'лицар (knight) — context: лицарі православ''я, milites christi'
  - 'чайка (chaika boat) — context: козацький флот, морські походи'
  - 'панегірик (panegyric) — context: вірші на похвалу, Сакович'
  - 'експансія (expansion) — context: османська експансія, зупинити ворога'
activity_hints:
- type: reading
  focus: Kassian Sakovych's panegyric analysis
- type: essay-response
  focus: The concept of 'Knightly Ethos' in Sahaidachnyi's leadership
- type: comparative-study
  focus: Sahaidachnyi vs. previous cossack leaders (Nalyvaiko, Vyshnevetskyi)
- type: critical-analysis
  focus: The impact of the Khotyn victory on the Ottoman Empire
persona:
  voice: Senior Professor of History
  role: Keeper of the Kyiv Brotherhood Archives
grammar:
- 'Historical narrative: sophisticated causal structures'
- Participles in historical descriptions
register: публіцистичний
prerequisites:
- kozatski-povstannia-16
connects_to:
- khotynska-viyna

```

---

## PART 1: Deep Research

Research **Петро Сагайдачний: Гетьман і меценат** for the **hist** track. Produce structured research notes that will drive content writing in Phase B.

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

# Дослідження: Петро Сагайдачний: Гетьман і меценат

## Key Facts Ledger
<!-- IMMUTABLE TRUTH ANCHOR — Phase D verifies prose against this -->
```yaml
subject: "Петро Сагайдачний: Гетьман і меценат"
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
