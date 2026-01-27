# LIT Curriculum Migration Strategy

**Date:** 2026-01-03
**Scope:** LIT-001 to LIT-030 (Ukrainian Literature & Classics specialization track)
**Goal:** Unified YAML Architecture with specialized handling for Literature tracks.

## Important Distinction: LIT vs C1 Literature

**This strategy applies ONLY to the LIT track** (`curriculum/l2-uk-en/lit/`).

| Aspect | LIT Track | C1 Literature (M146-160) |
|--------|-----------|--------------------------|
| **Location** | `curriculum/l2-uk-en/lit/` | `curriculum/l2-uk-en/c1/` |
| **Prerequisite** | C1 Core complete | C1.1-C1.5 phases |
| **Focus** | Golden Age (19th century) | Full Canon (Classics to Contemporary) |
| **Pedagogy** | Graduate seminar (essay-based) | C1 language mastery through literature |
| **Template** | `lit-module-template.md` | `c1-literature-module-template.md` |

**C1/C2 literature modules use standard C1/C2 YAML architecture** (not this LIT-specific strategy).

## 1. Architectural Decision: "Reading Hall" (`## 🏛️ Читальна Зала`)

The "Reading Hall" section found in LIT modules is **not** a passive resource list. It represents **Active Reading Tasks**. Therefore, it will be migrated to the `activities` YAML sidecar, distinct from `external_resources.yaml`.

### Schema Mapping

**Source Markdown:**
```markdown
### 1. Біографічні Нариси: Життя як Роман
> 📖 **Читати Повністю:** [Link](url)
> *Завдання для читання:*
> 1.  Знайдіть опис...
> 2.  Прочитайте про...
```

**Target YAML (`activities/{slug}.yaml`):**
```yaml
- type: reading
  id: lit-001-reading-01
  title: "Біографічні Нариси: Життя як Роман"
  context: "Ваше завдання — не просто прочитати, а відчути дух епохи."
  resource:
    type: article  # or 'book', 'primary_source'
    url: "https://www.ukrlib.com.ua/bio/printit.php?tid=1672"
    title: "Іван Котляревський. Життя і творчість"
  tasks:
    - "Знайдіть опис служби Котляревського в полку. Які конкретно битви він бачив?"
    - "Прочитайте про його стосунки з кріпаками. Як це характеризує його?"
```

**Rationale:**
- **Activity vs. Resource:** Resources are for optional deep dives. Reading Hall items are *required* assignments with specific questions.
- **Future Proofing:** This sets the pattern for C1/C2 "Research" or "Analysis" tasks.

## 2. Gap Filling Protocols ("The Error Correction")

If a LIT module is missing standard components, it is considered an **error state** that must be rectified during migration.

### Missing Vocabulary
-   **Condition:** No `# Vocabulary` / `# Словник` table in Markdown and no existing `vocabulary/` sidecar.
-   **Action:** Extract **15-20 key terms** from the text.
  -   Focus: Literary terms (e.g., *бурлеск*, *травестія*), historical context (*гетьманщина*, *кріпацтво*), and sophisticated abstract nouns (*суб'єктність*, *ідентичність*).
  -   Enrich with IPA and English translations.

### Missing Resources
-   **Condition:** No "Reading Hall" and no "Resources" section.
-   **Action:**
    1.  Locate the **Primary Source** text (e.g., full text on UkrLib, Yakaboo, or reputable academic sources).
    2.  Add it to `external_resources.yaml`.
    3.  If applicable, generate a `reading` activity for it.

### Missing Activities
-   **Condition:** No `# Activities` section.
-   **Action:** Generate **3 Critical Thinking Prompts** (Essay/Discussion topics).
  -   *Type:* `writing` or `discussion`.
  -   *Level:* C1 (Analysis, Synthesis, Evaluation).
  -   *Example:* "Analyze the contrast between..." rather than "What year was..."

## 3. Migration Workflow

1.  **Inventory:** Scan `curriculum/l2-uk-en/lit/` for all `.md` files.
2.  **Meta Extraction:** Ensure `meta/{slug}.yaml` exists and is complete.
3.  **Content Migration:**
    -   Identify `## 🏛️ Читальна Зала` -> Move to `activities/` (Type: `reading`).
    -   Identify `# Activities` -> Move to `activities/` (Standard types).
    -   Identify `# Vocabulary` -> Move to `vocabulary/`.
    -   Identify `## Resources` -> Move to `docs/resources/external_resources.yaml`.
4.  **Cleanup:** Remove migrated sections from `.md`.
5.  **Audit:** Run `scripts/audit_module.py`.
