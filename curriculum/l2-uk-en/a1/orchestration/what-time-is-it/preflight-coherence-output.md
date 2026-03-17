### Step 1: Section Coverage Checklist

| Plan Section | Prompt Match | Where |
|---|---|---|
| Вступ (Introduction) ~250w | YES | "REQUIRED H2 Sections" — `## Вступ (Introduction)` (~250 words), both bullet points present verbatim |
| Презентація часу (Time Presentation) ~350w | YES | `## Презентація часу (Time Presentation)` (~350 words), all 3 bullet points present verbatim |
| Дні та місяці (Days and Months) ~350w | YES | `## Дні та місяці (Days and Months)` (~350 words), all 3 bullet points present verbatim |
| Практика та розклад (Practice and Schedule) ~250w | YES | `## Практика та розклад (Practice and Schedule)` (~250 words), both bullet points present verbatim |

Prompt adds `## Підсумок` (~150 words) — this is standard scaffolding, not a plan violation.

### Step 2: Word Target Check

- Plan `word_target`: **1200**
- Prompt target: **"1200–1800 words"**, section table shows **"Total: 1200+"**
- Audit gate minimum: **1200** ✓, ceiling **~1800** ✓

Match confirmed. The upper ceiling is prompt scaffolding, not a contradiction.

### Step 3: Vocabulary Check

All 8 required items present in the "Required (MUST appear in vocabulary YAML)" list with matching usage hints. All 7 recommended items present in the "Recommended" list. ✓

### Step 4: Objective Check

| Objective | Coverage |
|---|---|
| Ask and tell the time | ✅ Презентація часу — «Котра година?» vs «О котрій?», hour identification |
| Name all days of the week | ✅ Дні та місяці — days + Accusative case rule |
| Name all months of the year | ✅ Дні та місяці — months + Locative case rule |
| Use time prepositions correctly | ✅ Практика та розклад — «о», «до», «після» with conductor schedule example |

All objectives covered.

---

```yaml
prompt_preflight:
  status: PASS
  issues: []
```