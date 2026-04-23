# a1/colors Rebuild Plan — 4-action sequence

**Origin:** diagnostic `docs/reports/2026-04-23-a1-colors-opus-r1-dim-diagnosis.md` (#1449).
**Goal:** take `a1/colors` from current R1 REJECT (MIN 3.0, Overall 6.1) to R1/R2 PASS.
**Predicted lift after all 4 actions:** MIN 3.0 → 6+ (R2 needed), Overall 6.1 → ~7.8.

---

## Prerequisites (Phase 0 — already queued)

Land before any rebuild work:

- PR **#1448** (tokenizer й/ї fix) — without this, contract compliance demands non-Ukrainian forms and the writer spends 5 rounds failing.
- PR **#1447** (canonical-anchor registry + citation-bound prompts) — closes factual-drift class.

After both merge, the 4 rebuild actions below are unblocked.

---

## Action 1 — Fix `_extract_terms` + add Teacher-voice anchor

**Closes:** Pedagogical quality 4/10 → 7/10, Engagement & tone 3/10 → 6/10.

**Diagnosed root cause (#1449 §3.1, §3.2, §5.1):** `scripts/build/phases/plan_contract.py:42-51` extracts the first 8 Cyrillic tokens ≥3 chars from teaching-beats as hard `required_terms`. For colors it emitted `[для, мові, активно, вчимо, пару, такий, поділених, типами]` — grammatical scaffolding, not learner-target vocabulary. The writer code-switches (`"follows the same правилами you practiced in модуль 9"`) to comply.

**Fix — two files:**

1. `scripts/build/phases/plan_contract.py:42-51` — rewrite `_extract_terms`:
   - Drop first-N-Cyrillic heuristic.
   - Source from `plan["vocabulary_hints"]["required"]` + `recommended` + explicit collocations in `content_outline[].points` («guillemets» / backticked).
   - Intersect with section teaching-beat text to scope per-section.
   - Add VESUM-frequency stopword list for grammatical scaffolding (at minimum `для, мові, активно, вчимо, пару, такий, поділених, типами, мотивами, базових, вірша, групи, варто, використовуються`).
   - Keep the 8-term cap.

2. `v6-chunk-XX-prompt.md` template — add a positive **Teacher voice** anchor block:

   ```markdown
   ## Teacher voice (follow this shape)

   Write in English as the narrative medium. Ukrainian appears ONLY as:
   - bolded inline lexical items with gloss — «синій» (dark blue)
   - block-quoted dialogue turns
   - example phrases you are explicitly teaching

   Do NOT embed Ukrainian grammatical forms (verbs, participles,
   function words) inside English sentences.
   ```

**Test:** regenerate `orchestration/colors/contract.yaml`; confirm section 2 `required_terms` ⊂ `{червоний, жовтий, зелений, синій, чорний, білий, сірий, блакитний, коричневий, рожевий, помаранчевий, фіолетовий, колір}`.

**Owner:** Codex (pipeline code).

## Action 2 — Add `dialogue_situations[].turns:` convention + update colors plan

**Closes:** Dialogue & conversation quality 5/10 → 8/10.

**Diagnosed root cause (#1449 §3.3, §5.2):** `plans/a1/colors.yaml:31-41` uses `setting:` field as English stage direction with linguistic metadata ("Описати: чорна сукня (f), білий светр (m)…"). The writer rendered it as framing narration before the dialogue turns.

**Fix — three files:**

1. `docs/best-practices/dialogue-situations.md` — define `turns:` as a required sibling of `setting:`. `setting:` becomes writer-only metadata, never rendered. Each turn: `{ speaker, ua, en_gloss }`.

2. `plans/a1/colors.yaml:31-41` — add `turns:` for both dialogues. Source the flower-market dialogue from Bolshakova Grade 2 p.38 poem (already the plan's textbook anchor). Bump plan `version`, back up old plan to `.bak`.

3. `v6-chunk-XX-prompt.md` template — for sections with non-empty `dialogue_acts`, inject: *"Render as: H3 title (optional, Ukrainian), 5–8 speaker-turns in block-quote format, ≤2 sentences of analytical gloss in English pointing at specific forms. No narrative framing, no stage directions."*

4. (Optional) `scripts/audit/checks/dialogue_density.py` — new audit: dialogue sections must be ≥70% turn lines, ≤30% prose.

**Test:** re-render dialogue section; confirm ≥70% is speaker-turn block-quotes.

**Owner:** Claude (plan convention + prompt template). Audit check optional / Codex.

## Action 3 — Verify prereq fixes land cleanly on colors

Before re-firing, clear the previous run's orchestration state so the build is fresh:

```bash
rm -rf curriculum/l2-uk-en/a1/orchestration/colors
rm curriculum/l2-uk-en/a1/colors.md
rm -f curriculum/l2-uk-en/a1/review/colors-*
```

Validate prereqs loaded:
- `.venv/bin/python -c "import sys; sys.path.insert(0,'scripts'); from build.phases.plan_contract import _extract_terms; …"` exercising the new extraction on `a1/colors` plan; assert no function words in output.
- Inspect the `plans/a1/colors.yaml` diff — confirm `turns:` present, `version` bumped, `.bak` exists.
- Run contract-compliance test suite: `.venv/bin/pytest tests/test_contract_compliance.py tests/test_plan_contract.py`.

## Action 4 — Re-fire build + evaluate

```bash
.venv/bin/python scripts/build/v6_build.py a1 10 --writer claude-tools
```

Monitor via the `Monitor` tool with JSONL event filter (per `workflow.md`):

```
Monitor(
    command=".venv/bin/python -u scripts/build/v6_build.py a1 10 --writer claude-tools 2>&1 | grep --line-buffered '^{\"event\"'",
    description="a1/colors rebuild",
    persistent=True,
    timeout_ms=3600000
)
```

**Expected R1 scores (per #1449 §7 calibrated prediction):**

| Dim (this-branch schema) | Before | Predicted |
|---|---:|---:|
| Plan adherence | 5 | 7 |
| Linguistic accuracy | 8 | 9 |
| Pedagogical quality | 4 | **7** |
| Vocabulary coverage | 7 | 8 |
| Exercise quality | 8 | 8 |
| Engagement & tone | 3 | **6** |
| Structural integrity | 8 | 8 |
| Cultural accuracy | 9 | 9 |
| Dialogue & conversation quality | 5 | **8** |
| **Overall** | **6.1** | **~7.8** |
| **MIN** | **3** | **6** |

MIN=6 is still below the 8.0-per-dim publish threshold. Expect R2 correction pass to bring the two lowest dims above 8. If MIN < 6 on R1, the `_extract_terms` fix is likely incomplete — check that `required_terms` actually sourced from `vocabulary_hints.required` and stopwords hit.

**If scores land within ±1 of the prediction:** the diagnostic's attribution was correct. Proceed to `i-want-i-can` as second vertical slice.

**If Pedagogical quality < 7 after Action 1:** the secondary plan-authoring cause (teaching-beats written in mixed Ukrainian prose) may need a pass — see #1449 §3.1 root-cause table's 30% plan-weight contribution.

**If Engagement & tone < 6 after the prompt anchor:** the `Patient Guide` voice needs a concrete sample paragraph in the prompt, not just a negative-constraint list.

---

## Ownership split

| Action | Owner | Agent (if dispatched) |
|---|---|---|
| Prereq merges | User | — |
| 1 — `_extract_terms` + Teacher voice | Pipeline code | Codex |
| 2 — `dialogue_situations[].turns:` | Plan + convention | Claude (inline) |
| 3 — Verify prereqs | Orchestrator | Claude |
| 4 — Re-fire + evaluate | Orchestrator | Claude (Monitor) |

## See also

- Audit: [`docs/architecture/2026-04-23-alignment-pipeline-audit.md`](../architecture/2026-04-23-alignment-pipeline-audit.md)
- EPIC: [`docs/epics/2026-04-23-alignment-pipeline-runtime-contracts.md`](../epics/2026-04-23-alignment-pipeline-runtime-contracts.md)
- Diagnostic: `docs/reports/2026-04-23-a1-colors-opus-r1-dim-diagnosis.md` (pending PR)
