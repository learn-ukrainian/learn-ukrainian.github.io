# TypeSafe citation verifier — live receipt (2026-09-19)

Issue #8192. One live run of

`.venv/bin/python -m scripts.audit.typesafe_citation_verifier --input tests/fixtures/typesafe_citation_cases.jsonl --out audit/2026-09-19-typesafe-citation-verifier/receipt.json`

Model requested `jev-latest`; the API returned `jev-1.13.0` on every stage-2 call (37 citations). The 13 fabricated quotes were decided at stage 1 and did not call the model.

This run was repeated after the second review delta. No fixture case changed verdict because of the new matching rules: every row that reached the model last time still reached it, and the 13 fabricated quotes were still decided at stage 1. `acc-01` left `verified` only because model confidence on the same `supports` choice fell from 0.81 to 0.77, under the 0.80 accept bar.

## Confusion matrix

Rows are the fixture `expected` class. Columns are the verifier verdict. Only `verified` is an accept.

| expected \ verdict | verified | fabricated | contradicted | unsupported | needs_human_review | n |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| accurate | 9 | 0 | 0 | 0 | 4 | 13 |
| fabricated | 0 | 13 | 0 | 0 | 0 | 13 |
| contradicted | 0 | 0 | 12 | 0 | 0 | 12 |
| out_of_context | 0 | 0 | 0 | 11 | 1 | 12 |

## False accepts

False accept means expected class `fabricated` or `contradicted` and verdict `verified`.

- Fabricated: **0** / 13
- Contradicted: **0** / 12

## Human review

`needs_human_review` **5 / 50** (0.10). All five cleared stage 1. The model chose the class that matches the label, but confidence was under 0.80, so the code did not auto-accept:

| id | expected | choice | confidence |
| --- | --- | --- | ---: |
| acc-01 | accurate | supports | 0.77 |
| acc-03 | accurate | supports | 0.75 |
| acc-07 | accurate | supports | 0.54 |
| acc-11 | accurate | supports | 0.35 |
| ooc-09 | out_of_context | says_nothing | 0.65 |

## Spend

- Input tokens: **31678**
- Output tokens: **1737**
- Total tokens: **33415**
- Wall time (`wall_time_seconds` in the receipt): **22.885232** seconds

Numbers are the raw receipt counts. The fixture was not edited after this run.
