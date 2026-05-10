# Phase 4 Round-3.5 Verification — Experiment Artifacts

Failed Gemini-tools writer output from PR #1621. Preserved as evidence
for the round-4 bakeoff trigger decision (#1620).

## Files

- `module.md` — Gemini round-3.5 output (1020 words, fails Python QG)
- `activities.yaml` — Gemini round-3.5 activities (10 items, includes
  `error-correction` activity that surfaced the VESUM gate bug — see
  `errorWord` fields like `вмиваєця` which the Python QG incorrectly
  flagged as "missing in VESUM" rather than recognizing as deliberate
  errors)
- `vocabulary.yaml` — Gemini round-3.5 vocabulary
- `resources.yaml` — Gemini round-3.5 resources (lost textbook
  citations — Qdrant was down during the dispatch, so the knowledge
  packet degraded to plan-only with no textbook RAG)

## Why these are NOT in `curriculum/l2-uk-en/a1/my-morning/`

Per cross-agent adversarial review on PR #1621 (Gemini + Codex):
- Gemini: MERGE (as diagnostic record)
- Codex: REVISE — failed nonpublishable artifacts must NOT overwrite
  canonical curriculum files

Codex's REVISE finding 5 (HIGH) prevailed. The canonical
`curriculum/l2-uk-en/a1/my-morning/` was restored to its pre-PR
round-3 baseline (from `c91ae3bbe1`, the Codex hand-draft from PR #1594);
the failed Gemini outputs live here for evidence preservation.

## Round-3.5 verdict

`Round 3.5 = round-4 bakeoff trigger`. Gemini-tools writer:
- Bypasses anti-meta-narration ban via rephrasing (6+ violations: "Notice how...",
  "Understanding this gap... is essential for...", "As a final self-check, try
  to narrate...", and others not in the explicit forbidden-phrase list)
- Stuffs Ukrainian dialogue into JSX `<DialogueBox>` props with `translation` keys
  (gates immersion checks via component nesting)
- Loses content density on corrective JSON redispatch (writer prioritizes syntax
  over word-budget on retry)

See `docs/phase-4-exemplar-report.md` for the full diagnostic report.
