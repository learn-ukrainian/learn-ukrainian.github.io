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

1. **Ukrainian is its own reference.** Authentic Ukrainian academic sources — **VESUM, Правопис 2019, Вихованець, Шевельов, Пономарів, Грінченко, ЕСУМ, СУМ-20, школьные textbooks Заболотний / Авраменко / Большакова / Вашуленко** — are sufficient grounding. Do NOT explain or justify Ukrainian features by comparison to Russian or other Slavic languages — that frame imports the imperial reference even when criticizing Russian. Wrong: *"Ukrainian preserved X while Russian innovated Y."* Right: *"In Ukrainian, X is in paradigm Z, attested in [Ukrainian source]."* Other Slavic languages enter only in HIST / OES / ISTORIO seminars about etymology, lens staying Ukrainian-centered. **This is not a comparative-philology curriculum — it teaches one of the oldest Slavic languages on its own terms.** This rule must be re-asserted in every linguistic channel post because both Claude and Gemini drift to Russian-comparison framing reflexively (training-data prior).

   **Антоненко-Давидович «Як ми говоримо»** is the **canonical authority for Russianism identification and correction** — primary, prominent, non-negotiable in that domain. Use it actively for any suspected Russianism (calque morphology, copied lexicon, Russian-pattern agreement, register Russification): it names the Russianism and gives the Ukrainian alternative. It is **not** a general descriptive grammar source (that's VESUM, Правопис 2019, Вихованець, Шевельов, Пономарів) — different specialty, equally authoritative in its own. The mistake is using Антоненко-Давидович as if it described the language; the equally bad mistake is failing to use it where Russianism work is needed. Same model for Караванський (specialist Russian-Ukrainian lexicon).
2. **Terminology hygiene.** Use **Old East Slavic** in English and **давньоруська мова** in Ukrainian (with explicit clarification that *руська* refers to Kyivan Rus', not modern Russia). NEVER "Old Russian" / "древнерусский" — those terms presuppose the imperial conclusion.
3. **No invented Ukrainian.** Every non-trivial form gets verified against VESUM (`mcp__sources__verify_word`).
4. **Textbook grounding.** Dialogues come from real textbook situations, not invented drills.
5. **Adult register at A2+.** A2 should NOT coast on A1 simplicity — more turns, more stakes, richer vocabulary.
6. **Culturally Ukrainian.** No generic ESL settings. Real Kyiv/Lviv/village contexts.

## Who reviews what

- **Gemini reviews prose** (adversarial), flags Russianisms, calques, register issues
- **Claude reviews plans** (architectural fit, level-appropriateness)
- **the native reviewer** (native speaker) reviews periodic batches manually
