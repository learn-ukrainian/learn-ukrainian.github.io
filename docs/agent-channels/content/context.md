# content — curriculum prose, plans, vocabulary, pedagogy

This channel is for conversations about the Ukrainian content itself
— module prose, plans, vocabulary, pedagogy, dialogue design, and
linguistic quality. Pipeline plumbing discussions go in #pipeline.

## What lives in this channel

- Module plan reviews (`curriculum/l2-uk-en/plans/{level}/*.yaml`)
- Dialogue situation design (`dialogue_situations` field — see #1102)
- Vocabulary gap analysis (per-module or cross-track)
- Ukrainian linguistic quality — Russianism hunts, calque fixes, register questions
- Pedagogy pattern library (see #1051)
- Module friction debrief after failed builds (see #1189 for the recurring B1 patterns)
- Cultural authenticity — is a setting *genuinely* Ukrainian or ESL-textbook-generic?

## Reference

| File | What |
|---|---|
| `curriculum/l2-uk-en/plans/{level}/*.yaml` | Plans — immutable source of truth |
| `curriculum/l2-uk-en/{level}/{slug}.md` | Generated prose (output) |
| `curriculum/l2-uk-en/{level}/vocabulary/{slug}.yaml` | Writer-generated vocab |
| `docs/best-practices/dialogue-situations.md` | Dialogue design conventions |
| `docs/best-practices/module-content-quality.md` | What "good prose" means |
| `docs/best-practices/vocabulary-activity-standards.md` | Vocab/activity bar per level |
| `docs/best-practices/ukrainian-linguistics.md` | Linguistic rules |

## Non-negotiables

1. **No invented Ukrainian.** Every non-trivial form gets verified against VESUM (`mcp__sources__verify_word`).
2. **Textbook grounding.** Dialogues come from real textbook situations, not invented drills.
3. **Adult register at A2+.** A2 should NOT coast on A1 simplicity — more turns, more stakes, richer vocabulary.
4. **Culturally Ukrainian.** No generic ESL settings. Real Kyiv/Lviv/village contexts.

## Who reviews what

- **Gemini reviews prose** (adversarial), flags Russianisms, calques, register issues
- **Claude reviews plans** (architectural fit, level-appropriateness)
- **the native reviewer** (native speaker) reviews periodic batches manually
