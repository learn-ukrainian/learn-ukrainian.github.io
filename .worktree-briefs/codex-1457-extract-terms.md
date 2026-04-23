# Fix #1457 (P3-A) — `_extract_terms` emits function words as `required_terms`

## Context

Root cause of `a1/colors` Opus R1 Pedagogical quality 4/10 + Engagement & tone 3/10. `scripts/build/phases/plan_contract.py:42-51` (`_extract_terms`) pulls the first 8 Cyrillic tokens ≥3 chars from teaching-beats with only a 6-word stopword list. For colors this emitted grammatical scaffolding (`для, мові, активно, вчимо, пару, такий, поділених, типами, базових, кольорів`) as hard writer requirements. Writer code-switched to comply: `"follows the same правилами you practiced in модуль 9"`. Full diagnosis: `docs/reports/2026-04-23-a1-colors-opus-r1-dim-diagnosis.md` §3.1 + §5.1.

## Scope

Two files. Pipeline code + prompt template.

## Fix 1 — `scripts/build/phases/plan_contract.py:42-51`

Redesign `_extract_terms`:

- **Source from plan, not prose.** Pull from `plan["vocabulary_hints"]["required"]` and `plan["vocabulary_hints"]["recommended"]` (already curated as learner-target).
- **Section scoping.** Intersect with the section's teaching-beat text to keep only items relevant to this section.
- **Explicit collocations.** Also include tokens from `content_outline[].points` that appear in «guillemets» or `backticks` (already curated as collocations).
- **Grammatical stopword list.** Exclude Ukrainian function words, auxiliary verbs, demonstratives, common participles. Minimum set:
  ```
  для, мові, мовою, активно, вчимо, пару, такий, така, таке, такі,
  поділених, типами, типом, мотивами, базових, вірша, групи, групою,
  варто, використовуються, та, чи, але, або, проте, щоб, якщо, коли,
  де, як, що, якого, якої, який, яка, яке, які, цей, ця, це, ці,
  той, та, те, ті
  ```
  For broader coverage load from VESUM frequency data (top ~300 function words) — optional optimization.
- **Keep** the 8-term cap.

## Fix 2 — section prompt template

The template that builds `v6-chunk-XX-prompt.md` lives in the writer phase (likely `scripts/build/phases/chunk_prompt.py` or similar — grep `v6-chunk` to locate). Add a positive **Teacher voice** anchor block BEFORE the contract section, exactly:

```markdown
## Teacher voice (follow this shape)

Write in English as the narrative medium. Ukrainian appears ONLY as:
- bolded inline lexical items with gloss — «синій» (dark blue)
- block-quoted dialogue turns
- example phrases you are explicitly teaching

Do NOT embed Ukrainian grammatical forms (verbs, participles,
function words) inside English sentences. If you feel pulled to
write "follows the same правилами you practiced…", stop — write
"follows the same rules you practiced…" in English and introduce
«правило» separately as a lexical item if it is a teaching target.
```

## Tests

1. `tests/test_plan_contract.py` — new case on the colors plan:
   - Load `curriculum/l2-uk-en/plans/a1/colors.yaml`
   - Generate the contract via `build_contract(...)`
   - Assert `section.required_terms` for section `Кольори` does NOT contain any of `{для, мові, активно, вчимо, пару, такий, поділених, типами}`
   - Assert `section.required_terms` ⊂ `{червоний, жовтий, зелений, синій, чорний, білий, сірий, блакитний, коричневий, рожевий, помаранчевий, фіолетовий, колір}` (learner-target set from plan vocab_hints)

2. Regenerate `curriculum/l2-uk-en/a1/orchestration/colors/contract.yaml` and verify by hand.

## Verify

1. Unit tests green
2. Full pytest suite green (no regressions)
3. Manual spot-check of regenerated contract

## Out of scope

- `dialogue_situations[].turns:` convention — that's #1458 (P3-B), Claude-owned
- Re-firing the actual `v6_build.py a1 10` build — that's the orchestration step after both P3-A and P3-B land

## PR

Title: `fix(pipeline): kill function-word _extract_terms + add Teacher-voice prompt anchor (#1457)`

Push + open PR. Do NOT auto-merge.

## Worktree

`.worktrees/codex-1457-extract-terms` on branch `codex/1457-extract-terms` (already created from origin/main).

## References

- `docs/reports/2026-04-23-a1-colors-opus-r1-dim-diagnosis.md` §3.1, §5.1
- GH #1457 — P3-A of EPIC #1451
- `docs/reports/2026-04-23-a1-colors-rebuild-plan.md` — Action 1
