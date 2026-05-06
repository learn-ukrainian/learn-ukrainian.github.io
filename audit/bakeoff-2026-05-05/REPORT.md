# Bakeoff comparison report

- Bakeoff dir: `/Users/krisztiankoos/projects/learn-ukrainian/audit/bakeoff-2026-05-05`
- Writers: claude, gemini, gpt55
- Plan: `curriculum/l2-uk-en/plans/a1/my-morning.yaml`
- Word target: 1200

## Prompt adherence - writers

| sub-dim | claude | gemini | gpt55 |
| --- | --- | --- | --- |
| CoT block usage (writer_cot_emit fields_filled) | 0 (0/4 sections; 0 fields) | telemetry absent | 3 (4/4 sections; 16 fields) |
| verify_words density (calls per 100 words) | 0 (0 calls) | telemetry absent | 0 (0 calls) |
| Modern-Ukrainian compliance (no archaic forms in output) | missing output | missing output | missing output |
| Source-citation discipline (writer_tool_call success ratio) | 0 (0 tool calls) | telemetry absent | 0 (0 tool calls) |
| End-gate fired (writer_end_gate gate_present) | 0 (gate_present=false) | telemetry absent | 3 (gate_present=true) |

## Prompt adherence - reviewers

| sub-dim | claude | gemini | gpt55 |
| --- | --- | --- | --- |
| Per-dim CoT (reviewer_dim_evidence count >=2) | telemetry absent | telemetry absent | telemetry absent |
| Audit calls (reviewer_audit_call count, by audit_type) | telemetry absent | telemetry absent | telemetry absent |
| Source-attribution audit coverage | telemetry absent | telemetry absent | telemetry absent |
| Quote-verification coverage | telemetry absent | telemetry absent | telemetry absent |
| Sovietization flag triggered (when applicable) | telemetry absent | telemetry absent | telemetry absent |
| Modern-form guard (when applicable) | telemetry absent | telemetry absent | telemetry absent |

## Content quality - writers

| dim | claude | gemini | gpt55 |
| --- | --- | --- | --- |
| immersion | n/a | n/a | n/a |
| word count | n/a | n/a | n/a |
| naturalness | n/a | n/a | n/a |
| activity quality | n/a | n/a | n/a |
| vocabulary | n/a | n/a | n/a |
| plan adherence | n/a | n/a | n/a |
| **min dim** | n/a | n/a | n/a |
| **weighted score** | n/a | n/a | n/a |

## Tool usage

| tool | claude | gemini | gpt55 |
| --- | --- | --- | --- |
| verify_words | 0 | telemetry absent | 0 |
| search_definitions | 0 | telemetry absent | 0 |
| search_definitions_slovnyk | 0 | telemetry absent | 0 |
| search_grinchenko_1907 | 0 | telemetry absent | 0 |
| search_literary | 0 | telemetry absent | 0 |
| search_style_guide | 0 | telemetry absent | 0 |
| other tools used | none | telemetry absent | none |
| **calls per 100 words** | 0.00 | telemetry absent | 0.00 |

## Cross-reviewer bias check

| writer | dim | score from claude | score from gemini | score from gpt55 |
| --- | --- | --- | --- | --- |
| claude | immersion | n/a | n/a | n/a |
| claude | word count | n/a | n/a | n/a |
| claude | naturalness | n/a | n/a | n/a |
| claude | activity quality | n/a | n/a | n/a |
| claude | vocabulary | n/a | n/a | n/a |
| claude | plan adherence | n/a | n/a | n/a |
| gemini | immersion | n/a | n/a | n/a |
| gemini | word count | n/a | n/a | n/a |
| gemini | naturalness | n/a | n/a | n/a |
| gemini | activity quality | n/a | n/a | n/a |
| gemini | vocabulary | n/a | n/a | n/a |
| gemini | plan adherence | n/a | n/a | n/a |
| gpt55 | immersion | n/a | n/a | n/a |
| gpt55 | word count | n/a | n/a | n/a |
| gpt55 | naturalness | n/a | n/a | n/a |
| gpt55 | activity quality | n/a | n/a | n/a |
| gpt55 | vocabulary | n/a | n/a | n/a |
| gpt55 | plan adherence | n/a | n/a | n/a |

## Findings + recommendations

| finding | recommendation |
| --- | --- |
| No candidate winner could be computed. | Run at least one writer and one review with telemetry. |
| No writer prompt-adherence sub-dimension was a three-way zero. | Keep the current prompt-adherence checks; inspect individual low cells for targeted fixes. |
| No self-family over-rating signal was detected from available review telemetry. | Keep cross-family reviews as the default; add self-review rows only when deliberately measuring bias. |
| No writer used: verify_words, search_definitions, search_definitions_slovnyk, search_grinchenko_1907, search_literary, search_style_guide. | If these tools were expected, make the prompt/tool affordance more explicit. |
| 10 input warning(s) occurred during aggregation. | Review the Warnings section before treating rankings as complete. |

## Warnings

- missing writer markdown: /Users/krisztiankoos/projects/learn-ukrainian/audit/bakeoff-2026-05-05/claude.md
- missing writer markdown: /Users/krisztiankoos/projects/learn-ukrainian/audit/bakeoff-2026-05-05/gemini.md
- no writer telemetry events found in: /Users/krisztiankoos/projects/learn-ukrainian/audit/bakeoff-2026-05-05/gemini.write.jsonl
- missing writer markdown: /Users/krisztiankoos/projects/learn-ukrainian/audit/bakeoff-2026-05-05/gpt55.md
- missing review JSONL file: /Users/krisztiankoos/projects/learn-ukrainian/audit/bakeoff-2026-05-05/claude-gemini.review.jsonl
- missing review JSONL file: /Users/krisztiankoos/projects/learn-ukrainian/audit/bakeoff-2026-05-05/claude-gpt55.review.jsonl
- missing review JSONL file: /Users/krisztiankoos/projects/learn-ukrainian/audit/bakeoff-2026-05-05/gemini-claude.review.jsonl
- missing review JSONL file: /Users/krisztiankoos/projects/learn-ukrainian/audit/bakeoff-2026-05-05/gemini-gpt55.review.jsonl
- missing review JSONL file: /Users/krisztiankoos/projects/learn-ukrainian/audit/bakeoff-2026-05-05/gpt55-claude.review.jsonl
- missing review JSONL file: /Users/krisztiankoos/projects/learn-ukrainian/audit/bakeoff-2026-05-05/gpt55-gemini.review.jsonl
