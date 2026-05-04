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

## Non-negotiables (content-channel-specific)

> **Project-wide Ukrainian linguistic principles** (Ukrainian-as-its-own-reference, Антоненко-Давидович as Russianism specialist authority, terminology hygiene, four-checks model) live in `shared/context.md` and auto-prepend to every post in this channel. Do not duplicate them here — re-read shared if uncertain.

1. **Textbook grounding.** Dialogues come from real textbook situations (Большакова, Вашуленко for A1-A2; Заболотний, Авраменко for B1+), not invented drills.
2. **Adult register at A2+.** A2 must NOT coast on A1 simplicity — more turns, more stakes, richer vocabulary, less hand-holding.
3. **Culturally Ukrainian, not ESL-generic.** Real Kyiv / Lviv / Chernivtsi / village contexts — never anonymized "the city," "the cafe," "Mark and Anna."
4. **Plans are immutable source of truth.** Plan in `curriculum/l2-uk-en/plans/{level}/{slug}.yaml` defines what the module must contain. Disagreement with the plan = bump the version + backup, never silently mutate.

## Who reviews what

- **Gemini reviews prose** (adversarial), flags Russianisms, calques, register issues
- **Claude reviews plans** (architectural fit, level-appropriateness)
- **the native reviewer** (native speaker) reviews periodic batches manually
