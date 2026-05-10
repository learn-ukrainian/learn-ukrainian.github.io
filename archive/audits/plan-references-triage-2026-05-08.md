# Plan References Triage - 2026-05-08

**Issue:** #1770
**Scope:** Triage 32 plans citing missing textbooks.
**Goal:** Unblock plan review by deciding whether to ingest the textbook, amend the plan to an in-corpus equivalent, or defer.

## Per-Textbook Ingestion Priority

| Textbook | Priority | Availability | Rationale / Recommendation |
| --- | --- | --- | --- |
| **Кравцова Grade 4** | HIGH | ✅ PDF in `data/textbooks/grade-04/` | Cited by 11 A1-B1 plans. Critical to unblock. Option A (Ingest). |
| **Варзацька Grade 4** | HIGH | ✅ PDF + TXT available | Cited by 5 A1-B1 plans. Already partially in `docs/references/textbooks-txt/`. Option A (Ingest). |
| **Пономарьова Grade 3 & 4** | HIGH | ✅ PDFs in `data/textbooks/` | Cited by 3 A1/A2 plans. Option A (Ingest). |
| **Кравцова 3 клас** | HIGH | ✅ PDF in `data/textbooks/grade-03/` | Cited by 1 B1 plan. Option A (Ingest). |
| **Заболотний 4 клас / 4-5 клас** | LOW | ❌ Not in `data/textbooks/` | Заболотний generally doesn't write Grade 4 textbooks. Likely a hallucinated author attribution for generic grammar. Option B (Amend to Захарійчук 4 клас). |
| **Большакова Grade 2 & 4** | MED | ❓ TBD | Not found in `data/textbooks/`. Cited by 3 plans. Option B (Amend to Захарійчук or Кравцова) is faster, or Option A if user fetches PDF. |
| **Вашуленко Grade 4** | MED | ❓ TBD | Not found in `grade-04` list (though Grade 3 is present). Option B (Amend) or C (Defer) until fetched. |
| **Заболотний 7 клас (2015)** | LOW | ❓ TBD | Cited by B2 plans (not a priority per #1577). Option C (Defer) or A (Ingest) later. |
| **Таблиця відмінків за 4 клас** | LOW | N/A | Generic reference. Option B (Amend to a real textbook). |

## Per-Plan Verdict

### A — Ingest Textbook (19 plans)
The textbook is real, available offline, and highly cited. We should ingest it into `data/sources.db`.

| Plan | Target Textbook | Tag |
| --- | --- | --- |
| `a1/my-morning` | Кравцова Grade 4 | `[A1-PRIORITY]` |
| `a2/checkpoint-dative` | Кравцова Grade 4 | `[A2-PRIORITY]` |
| `a2/dative-nouns` | Кравцова Grade 4 | `[A2-PRIORITY]` |
| `a2/instrumental-means` | Кравцова Grade 4 | `[A2-PRIORITY]` |
| `a2/instrumental-profession` | Кравцова Grade 4 | `[A2-PRIORITY]` |
| `a2/plural-other-cases` | Кравцова Grade 4 | `[A2-PRIORITY]` |
| `a2/services-and-communication` | Кравцова Grade 4 | `[A2-PRIORITY]` |
| `a2/work-and-food` | Кравцова Grade 4 | `[A2-PRIORITY]` |
| `b1/b1-baseline-future-aspect` | Кравцова Grade 4 | `[B1-PRIORITY]` |
| `b1/instrumental-nuances` | Кравцова Grade 4 | `[B1-PRIORITY]` |
| `b1/reflexive-verbs-nuances` | Кравцова Grade 4 | `[B1-PRIORITY]` |
| `a1/questions` | Варзацька Grade 4 | `[A1-PRIORITY]` |
| `a1/verbs-group-one` | Варзацька Grade 4 | `[A1-PRIORITY]` |
| `a2/all-cases-practice` | Варзацька Grade 4 | `[A2-PRIORITY]` |
| `a2/checkpoint-cases` | Варзацька Grade 4 | `[A2-PRIORITY]` |
| `b1/narrative-mastery` | Варзацька Grade 4 | `[B1-PRIORITY]` |
| `a1/things-have-gender` | Пономарьова Grade 3 | `[A1-PRIORITY]` |
| `a1/what-is-it-like` | Пономарьова Grade 3 | `[A1-PRIORITY]` |
| `a2/instrumental-accompaniment` | Пономарьова Grade 4 | `[A2-PRIORITY]` |
| `b1/traveling-ukraine` | Кравцова 3 клас | `[B1-PRIORITY]` |

### B — Amend Plan (9 plans)
The textbook citation is dubious, generic, or an equivalent in-corpus textbook exists. We should edit the YAML to point to an ingested book like `Захарійчук Grade 4` (or `Кравцова` once ingested).

| Plan | Current Citation | Recommendation | Tag |
| --- | --- | --- | --- |
| `a1/hey-friend` | Заболотний 4 клас (Кличний) | Amend to `Захарійчук Grade 4` (or `Варзацька`). | `[A1-PRIORITY]` |
| `a1/i-eat-i-drink` | Заболотний 4 клас (Знахідний) | Amend to `Захарійчук Grade 4`. | `[A1-PRIORITY]` |
| `a1/people-around-me` | Заболотний 4 клас (Знахідний) | Amend to `Захарійчук Grade 4`. | `[A1-PRIORITY]` |
| `a1/linking-ideas` | Заболотний 4-5 клас (Сполучники) | Amend to `Захарійчук Grade 4` or `Літвінова 5 клас`. | `[A1-PRIORITY]` |
| `a1/where-to` | Таблиця відмінків за 4 клас | Amend to `Захарійчук Grade 4` (or `Кравцова`). | `[A1-PRIORITY]` |
| `a2/metalanguage-sentences-and-classroom` | Большакова Grade 4 | Amend to `Захарійчук Grade 4`. Большакова is missing. | `[A2-PRIORITY]` |
| `a2/metalanguage-words-and-cases` | Большакова Grade 4 | Amend to `Захарійчук Grade 4`. | `[A2-PRIORITY]` |
| `b1/nature-and-environment` | Большакова Grade 2 | Amend to `Цепова 2 клас` (which is in `txt` format). | `[B1-PRIORITY]` |
| `a2/metalanguage-verbs-and-time` | Вашуленко Grade 4 | Amend to `Захарійчук Grade 4` or ingest if found. | `[A2-PRIORITY]` |

### C — Defer Plan (3 plans)
The module is not a priority right now (B2+) and the textbook is missing or needs later ingestion.

| Plan | Missing Textbook | Rationale | Tag |
| --- | --- | --- | --- |
| `b2/kharchuvannia-i-kukhnia` | Заболотний, 7 клас (2015) | B2 is not an immediate priority. Needs ingestion. | `[B2]` |
| `b2/pobut-shchodenne` | Заболотний, 7 клас (2015) | Same as above. | `[B2]` |
| `b2/sport-i-dozvillia` | Заболотний, 7 клас (2015) | Same as above. | `[B2]` |

## Recommended Action Plan

1. **Immediate Unblock (A1/A2/B1):**
   - Run dictionary pipeline ingestion for `Кравцова Grade 4`, `Кравцова 3 клас`, `Варзацька Grade 4`, and `Пономарьова Grade 3 & 4`. This single action will rescue 20 priority plans.
2. **YAML Fixes:**
   - Open a PR to amend the 9 Option B plans to cite `Захарійчук Grade 4` or other fully-ingested alternatives. This eliminates the ghost citations (like the hallucinated "Заболотний 4 клас").
3. **Defer B2:**
   - Keep the 3 B2 plans blocked/deferred until B2 scaling begins.