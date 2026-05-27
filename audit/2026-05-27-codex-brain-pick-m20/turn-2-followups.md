# Codex brain-pick on m20 — turn 2 (Q4-Q6 follow-ups)

**Session:** `019e6944-d4c8-7da0-853f-8676ddf526b0` (continued from turn 1)
**Bridge ID:** `bridge-819ed50e`
**Duration:** 102.2s (via `ab send-codex-ui`)
**When:** 2026-05-27 ~13:55 UTC

## Q4 — Plan-stage / writer-prompt conflict on Grade 1 references

**Codex picks:** option (b) + narrowed (c).

> Not (a) [plan schema change] first — too much schema churn for the immediate fix.

**Minimal edit set:**
- Writer prompt: all `plan.references` still require `get_chunk_context` and trace evidence.
- Published 30-word blockquote applies **only** to `publishable` sources inferred from metadata: Grade 7+, adult literature, style guide, dictionary.
- Grade 1-3 refs become `internal_grounding`: retrieved, cited in trace/resources, **never quoted in `module.md`**.
- **Gate split**: `textbook_grounding` → `chunk_context_for_all_refs` + `published_quote_for_publishable_refs`.
- Plan stage: require adult/publishable refs only when a learner-visible quote is pedagogically needed. Do NOT filter Grade 1-3 from internal RAG (lower grades teach the same A1 vocab — keep them for grounding).

## Q5 — Rendered-lesson-pass layer placement

**Codex picks:** (b) hard gate + (a) writer rule. **Skip new reviewer dim** but keep existing tone/pedagogy reviewer criteria mirrored so non-regex register shifts are still rejected.

**Important nuance:** Don't make `<!-- VERIFY:` a hard raw-file pattern yet. Current prompt explicitly allows/encourages verification comments — would create prompt/gate contradiction unless the gate scans rendered output AFTER comments are stripped.

**Suggested hard patterns:**
```python
SCAFFOLDING_LEAK_PATTERNS = [
    r"^\s*(Крок|Step)\s+\d+\s*[:.-]",
    r"^\s*(P|Panel|Панель)\d+\b",
    r"\b(step-\d+|ban-\d+|map-\d+|obligation-\d+)\b",
    r"\b(textbook_grounding|wiki_coverage|llm_qg|python_qg|implementation_map)\b",
    r"\b(plan_reasoning|verification_trace|end_gate|chunk_context|tool_theatre)\b",
    r"\b(INJECT_ACTIVITY|resources_search_attempted|activity_split_audit)\b",
]
```

**False-positive notes:**
- `Крок 1:` can be legitimate in procedural lessons → allow explicit narrow escape when the plan topic teaches instructions/procedures.
- `^P\d+` fine if anchored; unanchored would hit source IDs.
- Do not ban all HTML comments unless the pipeline has moved `VERIFY` and `bad` markers out of `module.md`.

## Q6 — `scripts/audit/config.py` whitelist forensics

**Codex gut:** hand-curated post-hoc patching, not OCR sweep.

> Comments are dated, PR-linked, and m20-specific. `Кнак` was almost certainly added because a build surfaced it, not because a general literary-name list existed.

**Strong cleanup suspects:**

| Entry | Line | Why suspect |
|---|---|---|
| `прийом*` | 69 | Explicitly labeled "SHIP-BLOCKER WORKAROUND"; remove after upstream packet fix |
| `Кнак*` | 58 | Keep only if source verification proves it is genuinely in the excerpt |
| `я-форма*` | 60 | Not wrong, but wrong home; move to linguistic-term/compound-term handling, not proper-name whitelist |
| `Караман*` | 44 | Valid name, but m20-specific citation workaround; better handled by citation/source-title parsing |
| `Ліна / Настя` | (multiple) | Local but normal names; lower priority |

## Synthesized follow-up PR slate (post-Phase-1)

After codex dispatch lands its 6 `#R-` rules + reviewer REJECT criteria, and gemini dispatch lands the HARD `verify_quote` gate + prev/next safety, queue these follow-up PRs in order of dependency:

1. **`textbook_grounding` gate split** (per Q4): refactor into `chunk_context_for_all_refs` + `published_quote_for_publishable_refs` with metadata-based `publishable` determination. Plan stage emits both ref roles. Resolves the Grade 1 conflict identified in turn 1 F2.
2. **Scaffolding-leak HARD gate** (per Q5b): add `_scaffolding_leak_gate` to `linear_pipeline.py` with the `SCAFFOLDING_LEAK_PATTERNS` list. Procedural-lesson escape supported via plan flag (e.g., `plan.lesson_type: procedural` allows `Крок N:` headings).
3. **Rendered-lesson self-check writer rule** (per Q5a): add `#R-RENDERED-LESSON-PASS` to `linear-write.md` — writer must do a final pass simulating learner reading `module.md` stripped of comments, deleting anything addressed to writer/reviewer/teacher/gate.
4. **`scripts/audit/config.py` whitelist cleanup** (per Q6): remove `прийом*`, `Кнак*` (verify against source first), `Караман*`, move `я-форма*` to linguistic-term handling. Document each removal with PR-linked rationale.

These 4 are independent and can ship in any order after Phase 1, but #1 must land before re-firing m20 if the codex Phase 1 dispatch flagged the Grade 1 conflict and dropped `#R-NO-CHILDREN-PRIMARY-QUOTES`.

## End of brain-pick

Both turns complete. Session reachable for future turns via:
```
.venv/bin/python scripts/ai_agent_bridge/__main__.py send-codex-ui \
  --thread 019e6944-d4c8-7da0-853f-8676ddf526b0 \
  "<message>"
```
