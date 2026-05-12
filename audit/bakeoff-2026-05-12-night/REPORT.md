# Bakeoff Report — claude-tools vs codex-tools on a1/my-morning (2026-05-12 night)

> **Run timestamp:** 2026-05-12 ~02:20 CET (claude phase) / ~02:27 CET (codex phase)
> **Writers compared:** claude-tools, codex-tools
> **Slug:** a1/my-morning
> **Plan:** curriculum/l2-uk-en/plans/a1/my-morning.yaml
> **Prompt commit at run time:** `4637511615 fix(prompts): re-qualify search_literary as mcp__sources__search_literary in linear-write.md` (descendant of `28417cc3cb` — the 2026-05-11 single-primitive rewrite addressing #1807 tool-theatre).
> **Acceptance criteria source:** `docs/decisions/2026-05-06-writer-selection-codex-gpt55.md` § "Concrete rollback criteria" + § "What the bakeoff showed".

## Verdict

**Winner: claude-tools** — the *only* writer that satisfied gate (a) `tool_calls_total > 0`.

**One-sentence rationale:** codex-tools produced `tool_calls_total=0` and triggered the `MCP_TOOLS_NEVER_INVOKED` pipeline guard before any artifact could be written — pure tool theatre persists post-rewrite (`phase_writer_summary.writer="codex-tools" tool_calls_total=0`), whereas claude-tools invoked 4 real MCP tools (`verify_words` ×2 with 21 + 22 words, `search_text` ×2) and produced a complete artifact set with `vesum_verified.passed=true (159/159 forms)`.

**Decision card delta: REVISED — flip recommended.** The 2026-05-06 ACCEPTED choice of `codex-tools` rests on Option-A's premise that Codex's gate failures were "addressable by prompt iteration." The single-primitive prompt rewrite at `28417cc3cb` was that iteration, and codex still emitted zero tool calls. Meanwhile the *prior* loser (claude-tools, which in 2026-05-06 produced a 485-byte meta-summary) has converged on the prompt and now passes the structural gate. The roles have reversed.

> Note: claude-tools still committed partial theatre on the two newly-introduced single-call verifiers (`verify_quote`, `verify_source_attribution` — cited but uncalled). It earned tool-credit on `verify_words` and `search_text` only. That is a follow-up prompt-tightening issue, not a rollback trigger — strand-1 already caught it via `writer_tool_theatre`.

## Comparison table

| Field | claude-tools | codex-tools |
|---|---|---|
| Module file produced? (size > 1000 bytes) | **yes** (10 369 bytes) | **no** (writer guard aborted; only empty `writer_tool_calls.json = []` 3 bytes) |
| `tool_calls_total` | **4** | **0** |
| `writer_tool_theatre` violations | 2 (`verify_quote`, `verify_source_attribution` — cited 4× / called 3× of *other* tools) | full (entire write phase was theatre — `phase_writer_summary.tool_calls_total=0` while CoT blocks listed verification signatures) |
| python_qg gates passed | **14 of 18** (1 HARD fail, 2 soft fails, 1 pending) | **n/a** — build aborted in writer phase, python_qg never ran |
| Hard-gate fails | `textbook_grounding` (verdict=REJECT, severity=HARD, reason=`corpus_missing`) | n/a (gate phase never reached) |
| Soft-gate fails | `citations_resolve` (3 unknown labels, page-number drift), `immersion` (`long_ukrainian_sentences` triggered at 27.6% — within 15–35% policy band, fails on long-sentence sub-check), `correction_terminal` (`citations_resolve` after one ADR-008 retry) | n/a |
| word_count vs target | **1224 vs 1200** ✓ | n/a |
| Plan-section word budgets | 4/4 within (270–330) ✓ | n/a |
| Invented `-ся` forms (decision-card rollback criterion) | **0** — `vesum_verified.passed=true checked=159 missing=0` | n/a (no module produced) |
| wiki-path miscites in `references[]` | 0 in the YAML references; 3 page-label citations in prose don't resolve to `references[]` entries | n/a |
| Immersion percentage | 27.61% (band 15–35%, within range; fails on long-sentence sub-check, not on density) | n/a |
| ai_slop_clean / russianisms / surzhyk / calques / paronym | all ✓ | n/a |
| Writer phase: `mcp_config_resolved.status` | `ok` | `ok` (config is fine — failure is *behavioral*, not infrastructure) |
| `end_gate_fired` | true (rescanned_words, rescanned_sources, grammar_claims_grounded, removed_unverified; removed_count=0) | true (gate fired but produced no tool calls in the run) |

## Telemetry — claude-tools

- `tool_calls_total`: 4
- Tool names invoked: `verify_words` ×2 (21 + 22 Ukrainian lemmas/forms — all FOUND in VESUM), `search_text` ×2 (60-char + 49-char queries on `звороті дієслова постфікс ся означає дію спрямовану на себе`)
- `writer_tool_theatre`: 2 violations
- `phase_writer_summary`:

```json
{
  "event": "phase_writer_summary",
  "ts": "2026-05-12T00:20:09.524155+00:00",
  "writer": "claude-tools",
  "module": "a1/20",
  "sections_total": 4,
  "sections_with_cot": 4,
  "tool_calls_total": 4,
  "verify_words_calls": 2,
  "end_gate_fired": true,
  "removed_via_gate": 0,
  "tool_theatre_violations": ["verify_quote", "verify_source_attribution"],
  "tool_theatre_violation_count": 2
}
```

- `writer_end_gate`: gate_present=true, actions=`[rescanned_words, rescanned_sources, grammar_claims_grounded, removed_unverified]`, removed_count=0.

## Telemetry — codex-tools

- `tool_calls_total`: **0**
- Tool names invoked: **none**
- `writer_tool_theatre`: fired (entire run)
- `phase_writer_summary.tool_calls_total = 0`
- `mcp_config_resolved.status = ok` for codex-tools — the MCP config string resolved correctly; the model simply did not invoke any of the tools it had access to. Per the pipeline guard message: *"Pre-flight `mcp_config_resolved.resolution_status='ok'` only verifies config string resolution. The model must actually invoke at least one MCP tool. If this fires, check the rollout JSONL for catalog-visibility errors (e.g., 'tools are not exposed in this session')."*
- `module_failed.reason`:

```
MCP_TOOLS_NEVER_INVOKED: writer='codex-tools' module='a1/20'
expected='>=1 mcp__sources__* call from a -tools writer' got=0.
```

Build halted in writer phase. No `module.md`, no `python_qg.json`, no further artifacts.

## python_qg — claude-tools (gates section)

```json
{
  "word_count":   {"passed": true,  "count": 1224, "target": 1200},
  "plan_sections": {"passed": true,
    "word_budgets": [
      {"section": "Діалоги",        "count": 305, "min": 270, "max": 330, "passed": true},
      {"section": "Дієслова на -ся", "count": 320, "min": 270, "max": 330, "passed": true},
      {"section": "Мій ранок",       "count": 307, "min": 270, "max": 330, "passed": true},
      {"section": "Підсумок",        "count": 285, "min": 270, "max": 330, "passed": true}
    ]
  },
  "formatting_standards": {"passed": true},
  "vesum_verified":       {"passed": true, "checked": 159, "whitelisted": 8, "missing": [], "missing_count": 0},
  "citations_resolve":    {"passed": false,
    "unknown": [
      "Караман, Українська мова, 10 клас, с. 187",
      "Заболотний, Українська мова, 10 клас, с. 78",
      "Авраменко, Українська мова, 7 клас, с. 67"
    ]
  },
  "textbook_grounding":   {"passed": false, "verdict": "REJECT", "severity": "HARD",
    "required": 1, "matched": [],
    "missing": ["Караман Grade 10, p.176", "Кравцова Grade 4, p.113", "Захарійчук Grade 4, p.162"],
    "warnings": ["corpus_missing"], "reason": "corpus_missing"
  },
  "immersion":           {"passed": false, "pct": 27.61, "min_pct": 15, "max_pct": 35,
    "policy": "a1-m15-24", "long_ukrainian_sentences": [/* 2 sentences > policy length */]
  },
  "inject_activity_ids":  {"passed": true, "injected": ["act-1","act-2","act-5","act-10"]},
  "activity_types":       {"passed": true, "types": ["fill-in","quiz","match-up","true-false","group-sort","order","fill-in","unjumble","fill-in","fill-in"]},
  "ai_slop_clean":        {"passed": true},
  "component_props":      {"passed": true},
  "russianisms_clean":    {"passed": true},
  "surzhyk_clean":        {"passed": true},
  "calques_clean":        {"passed": true},
  "paronym_clean":        {"passed": true},
  "previously_passed_regression": {"passed": true},
  "mdx_render":           {"passed": null, "message": "Run after publish stage"},
  "passed":               false,
  "correction_terminal":  {"passed": false, "gate": "citations_resolve",
    "message": "citations_resolve failed after its single ADR-008 correction attempt"}
}
```

## python_qg — codex-tools

**Not produced.** Writer phase aborted via `MCP_TOOLS_NEVER_INVOKED` guard before python_qg ran.

## Qualitative sample — first sentence of "Діалоги" section, three eras

**Target:** opening sentence of the **## Діалоги** section.

- **2026-04-26 incumbent module** (codex run committed in `c91ae3bbe1`):
  > *"Morning routine is a useful place to learn Ukrainian reflexive verbs because the actions are concrete."* (English narration — 14 words)
- **2026-05-12 night, claude-tools** (this run, `audit/.../claude/module.md` line 3):
  > *"Reflexive verbs in Ukrainian end in **-ся** (or **-сь** after a vowel) and describe actions you do to yourself — washing up, getting dressed, waking up."* (English narration with Ukrainian morphology callout — 26 words; cites a Ukrainian dialogue immediately below)
- **2026-05-12 night, codex-tools:** **no Діалоги line produced** — writer phase aborted before any markdown was written.

The qualitative comparison reduces to "claude module vs no codex module" for this bakeoff. The 2026-04-26 incumbent stands as the prior best.

## Artifacts

- claude/ — `audit/bakeoff-2026-05-12-night/claude/` (module.md 10 369 B, knowledge_packet.md 41 374 B, writer_output.raw.md 34 151 B, activities.yaml 8 572 B, vocabulary.yaml 2 294 B, resources.yaml 1 866 B, python_qg.json 5 016 B, writer_tool_calls.json 6 018 B, writer_prompt.md 120 002 B)
- codex/ — `audit/bakeoff-2026-05-12-night/codex/` (writer_tool_calls.json 3 B = `[]` — sole artifact before abort)
- claude telemetry — `audit/bakeoff-2026-05-12-night/claude.write.jsonl` (22 events)
- codex telemetry — `audit/bakeoff-2026-05-12-night/codex.write.jsonl` (12 events; ends at `module_failed`)
- claude stdout — `audit/bakeoff-2026-05-12-night/claude.stdout.log` (single line: python_qg failure summary)
- codex stdout — `audit/bakeoff-2026-05-12-night/codex.stdout.log` (single line: MCP_TOOLS_NEVER_INVOKED)

## Next action for orchestrator

**Recommended on wake (one action):** flip `docs/decisions/2026-05-06-writer-selection-codex-gpt55.md` from ACCEPTED:codex-tools → revise / re-open under a new ADR slug, with claude-tools as the new candidate. Then file a follow-up issue against #1807 to:

1. Tighten the writer prompt to *force* `verify_quote` and `verify_source_attribution` calls when the writer cites them in `<verification_trace>` (mirror the existing strand-1 detection — currently it logs theatre but doesn't block).
2. Open a parallel issue against codex-tools' MCP catalog visibility — the `mcp_config_resolved.status=ok` pre-flight clearly does not guarantee the model *sees* the tools. Investigate codex rollout JSONL for catalog-visibility messages (per the guard's own hint).
3. Do **not** flip `curriculum/l2-uk-en/a1/my-morning/` to the new claude artifacts — the build still failed `correction_terminal` on `citations_resolve` + has a HARD `textbook_grounding` fail (`corpus_missing` — the cited textbook pages may need ingestion before the gate can pass). The 2026-04-26 incumbent remains the published module until a green build lands.

Alternative if rollback to claude-tools is rejected: schedule a third bakeoff after a *prompt-rework* cycle aimed at codex's catalog visibility, but the empirical pattern over three bakeoffs (2026-05-06, 2026-05-08, 2026-05-12) is that codex-tools cannot reliably call MCP tools in this pipeline.
