# Codex dispatch — bakeoff aggregator script

## Goal

Write `scripts/audit/bakeoff_aggregate.py` — reads the bakeoff's JSONL telemetry events + writer markdown outputs + reviewer scores, emits a deterministic comparison matrix at `audit/bakeoff-{date}/REPORT.md`.

Telemetry events were added in PR #1699 (`writer_cot_emit`, `writer_tool_call`, `writer_end_gate`, `phase_writer_summary`, `reviewer_dim_evidence`, `reviewer_audit_call`, `phase_review_summary`). Schema documented in `docs/MONITOR-API.md` + `tests/test_linear_pipeline_telemetry.py`.

## Worktree

Bare `--worktree`. Auto-derived at `.worktrees/dispatch/codex/bakeoff-aggregator/`.

## Numbered steps

1. **Read the new event schemas** in `docs/MONITOR-API.md` + `tests/test_linear_pipeline_telemetry.py`. Capture exact field names per event.

2. **Design the aggregator CLI:**
    ```
    .venv/bin/python scripts/audit/bakeoff_aggregate.py \
      --bakeoff-dir audit/bakeoff-2026-05-05 \
      --writers gemini,claude,gpt55 \
      --output audit/bakeoff-2026-05-05/REPORT.md
    ```
    Reads from `--bakeoff-dir` the per-writer `.md` files and the per-review `.jsonl` files (1 file per writer × reviewer pair). Writes the markdown report to `--output`.

3. **Comparison matrix sections** (write each as a markdown table in the report):

    a. **Prompt adherence — writers** (per writer, scored 0-3 per sub-dim from telemetry):
        | sub-dim | gemini | claude | gpt55 |
        | CoT block usage (writer_cot_emit fields_filled) | … | … | … |
        | verify_words density (calls per 100 words) | … | … | … |
        | Modern-Ukrainian compliance (no archaic forms in output) | … | … | … |
        | Source-citation discipline (writer_tool_call success ratio) | … | … | … |
        | End-gate fired (writer_end_gate gate_present) | … | … | … |

    b. **Prompt adherence — reviewers** (per reviewer):
        | sub-dim | gemini | claude | gpt55 |
        | Per-dim CoT (reviewer_dim_evidence count ≥2) | … | … | … |
        | Audit calls (reviewer_audit_call count, by audit_type) | … | … | … |
        | Source-attribution audit coverage | … | … | … |
        | Quote-verification coverage | … | … | … |
        | Sovietization flag triggered (when applicable) | … | … | … |
        | Modern-form guard (when applicable) | … | … | … |

    c. **Content quality — writers** (cross-reviewer mean per dim):
        | dim | gemini | claude | gpt55 |
        | immersion | … | … | … |
        | word count | … | … | … |
        | naturalness | … | … | … |
        | activity quality | … | … | … |
        | vocabulary | … | … | … |
        | plan adherence | … | … | … |
        | **min dim** | … | … | … |
        | **weighted score** | … | … | … |

    d. **Tool usage** (per writer):
        | tool | gemini | claude | gpt55 |
        | verify_words | … | … | … |
        | search_definitions | … | … | … |
        | search_definitions_slovnyk | … | … | … |
        | search_grinchenko_1907 | … | … | … |
        | search_literary | … | … | … |
        | search_style_guide | … | … | … |
        | (others used) | … | … | … |
        | **calls per 100 words** | … | … | … |

    e. **Cross-reviewer bias check** — for each writer, the per-dim score from each reviewer separately, so we can spot when one reviewer over-rates a particular writer:
        | writer | dim | score from gemini | score from claude | score from gpt55 |

    f. **Findings + recommendations** — generated programmatically:
        - Highlight the writer with the highest weighted score AND highest prompt-adherence score (the candidate winner)
        - Highlight any sub-dim where ALL three writers scored 0 (signal that the prompt itself has a problem)
        - Highlight any reviewer that systematically over-rated the writer of its own family (bias signal)
        - Note any tool that no writer used (signal that the prompt didn't surface it)

4. **Inputs the aggregator must accept:**
    - JSONL files per writer phase (containing `writer_*` + `phase_writer_summary` events) — at `audit/bakeoff-2026-05-05/{writer}.write.jsonl`
    - JSONL files per review run (containing `reviewer_*` + `phase_review_summary` events) — at `audit/bakeoff-2026-05-05/{writer}-{reviewer}.review.jsonl`
    - Markdown writer outputs — at `audit/bakeoff-2026-05-05/{writer}.md`
    - Plan YAML for the module being baked off — auto-resolved from `curriculum/l2-uk-en/plans/{level}/{slug}.yaml`

5. **Robustness:**
    - Missing files → warn + skip (e.g. if user only ran 2 of 3 writers)
    - Malformed JSONL line → skip that line, log to stderr, continue
    - No telemetry events for a writer → fall back to "telemetry-absent" warning column instead of 0 score

6. **Tests** — `tests/test_bakeoff_aggregate.py`:
    - Fixture: a synthetic `audit/bakeoff-fixture/` dir with all 3 writers' JSONL + .md
    - Run aggregator
    - Assert REPORT.md contains all 6 expected tables (a-f) + the auto-findings section
    - Assert column counts match expected agents
    - Assert min-dim and weighted-score calculations are correct against fixture inputs

7. **Run tests.** `.venv/bin/python -m pytest tests/test_bakeoff_aggregate.py -x -v`

8. **Run ruff.** `.venv/bin/ruff check scripts/audit/`

9. **CLI `--help` standard.** Per `claude_extensions/rules/cli-help-standard.md`: description (what it does + when to use it / when NOT), every `add_argument()` has meaningful `help`, `epilog` with examples + outputs + exit codes + related references.

10. **Commit.**
    ```
    feat(audit): bakeoff_aggregate.py — comparison matrix from telemetry events
    ```

11. **Push + open PR (NOT draft).**
    ```bash
    git push -u origin codex/bakeoff-aggregator
    gh pr create --title "feat(audit): bakeoff_aggregate.py — comparison matrix from telemetry events" --body "..."
    ```

12. **Do NOT enable auto-merge.**

## Acceptance criteria

- `scripts/audit/bakeoff_aggregate.py` exists, parseable + runnable
- 6 markdown tables + auto-findings section in output
- Robust to missing files / malformed lines
- Test fixture covers all 6 tables
- ruff clean
- `--help` meets repo standard
- PR opened referencing bakeoff brief at `docs/dispatch-briefs/2026-05-05-a1-20-bakeoff-with-new-prompts.md`

## Discipline

- Reference bakeoff brief in commit + PR
- No `--no-verify`
- Worktree cleanup post-merge by next session
