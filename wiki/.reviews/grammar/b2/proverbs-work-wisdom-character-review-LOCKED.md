# proverbs-work-wisdom-character (L2-UK-EN B2/M70) - LOCKED review

- **File reviewed:** `wiki/grammar/b2/proverbs-work-wisdom-character.md`
- **Review date:** 2026-06-15
- **Reviewer:** codex/b2-wiki-readiness-batch-21
- **Rubric:** B2 wiki readiness pass: no unresolved VERIFY markers, source-backed factual claims, lifecycle metadata on wiki and paired plan, and a companion LOCKED review note.
- **Prior state:** unlocked B2 wiki page with VERIFY markers around elliptical proverb syntax, generalized-personal past-tense claims, and generated canonical etiquette/state anchors.
- **Fixes applied:** Added lifecycle metadata, replaced stale source registry chunk ids, cleared all markers, removed unsupported numeric detail, bounded grammar rules to source-present proverb forms, and checked the canonical-anchor list against repo-local evidence.

## Evidence

| Claim area | Evidence used | Resolution |
|---|---|---|
| Proverb/prykazka theory | `5-klas-ukrlit-avramenko-2022_s0031` explains hidden meaning, proverb/prykazka contrast, thematic grouping, and active use in speech. | Repointed [S1] from a stale nonresolving chunk and removed the unsupported "almost seven thousand" numeric claim. |
| Thematic-group exercises | `5-klas-ukrlit-avramenko-2022_s0035` asks about thematic groups and why many items concern economic activity. | Repointed [S2] and kept only source-present thematic guidance. |
| Main proverb theory and examples | `10-klas-ukrmova-karaman-2018_s0202` gives the 10th-grade definition and examples including `більше діла`, `менше говори`, `тримай слово`, `Згаяного часу`, `Згода будує`, and `Хто багато обіцяє`. | Repointed [S3], corrected `Набалакав -- і в торбу не забереш`, and reframed the ellipsis/past-tense claims as exercise guidance. |
| Labor proverbs | `9-klas-ukrajinska-mova-avramenko-2017_s0050` lists `Праця чоловіка годує`, `Щоб рибу їсти`, `Під лежачий камінь`, and `Що посієш`. | Repointed [S4] and retargeted all old [S8] labor-proverb citations. |
| Proper Ukrainian words | `6-klas-ukrmova-zabolotnyi-2020_s0018` directly asks whether own-Ukrainian words are an ornament of the language. | Added [S5] for the lexical/decolonization guidance. |
| Rhetoric topics | `10-klas-ukrajinska-mova-zabolotnij-2018_s0092` lists the public-speech topics used on the page. | Added [S6] for the rhetoric section. |
| Etiquette formulas | `2-klas-ukrmova-bolshakova-2019-1_s0007`, `1-klas-bukvar-bolshakova-2018-1_s0003`, and `6-klas-ukrmova-golub-2023_s0245` attest `Добрий день`, `До побачення`, `Мене звати`, and `Я студентка`. | Added [S7]-[S9]; removed generated inline VERIFY comments. |
| Personal-name fields | `2-klas-ukrmova-bolshakova-2019-2_s0023` lists `прізвище`, `ім'я`, and `по батькові`. | Added [S10]. |
| State/geographic anchors | `11-klas-istoriya-ukr-hlibovska-2024_s0407`, `2-klas-ukrmova-bolshakova-2019-2_s0033`, and `5-klas-ukrmova-golub-2022_s0166` support `синьо-жовтий`, `Тризуб`, `Київ`, and `гривня`. The forbidden variants were checked against `data/canonical_anchors.yaml`. | Added [S11]-[S13] for the source-present forms and recorded the canonical-anchor check here instead of adding non-DB inline citations. |

## Dimension Scores

| # | Dimension | Score | Evidence |
|---|-----------|-------|----------|
| 1 | Factual accuracy | **9/10** | Stale source ids were replaced and unsupported overclaims were removed or narrowed. |
| 2 | Ukrainian language quality | **9/10** | Proverb examples now match resolving source text. |
| 3 | Decolonization | **8/10** | Canonical anchors remain, but are framed as repo-canonical generation guidance rather than unsourced absolutes. |
| 4 | Completeness | **8/10** | Core proverb syntax, examples, and exercise guidance remain; unsupported detail was intentionally dropped. |
| 5 | Actionable guidance | **9/10** | Writers get concrete source-present patterns and clear limits for generation. |

**Overall: 8.6/10 - LOCKED.**

## What "LOCKED" Means For This Artifact

- The wiki meta block carries `lifecycle: locked`, `last_reviewed`, and `reviewed_by`.
- The paired plan carries `lifecycle: locked`, `reviewed_at`, `reviewed_by`, and `review_notes`.
- No unresolved VERIFY markers remain on the page.
- Batch 21 changes are limited to source-registry repair, source-bounded corrections, and lifecycle metadata.

## Unlock Triggers

1. A future phraseology review adds stronger corpus or dictionary evidence for the broader proverb-syntax generalizations.
2. A future source-ingest pass creates DB-addressable records for `data/canonical_anchors.yaml` so canonical anchors can be cited inline without breaking citation-resolution invariants.
3. A future wiki rebuild reintroduces VERIFY markers or drops lifecycle metadata.
