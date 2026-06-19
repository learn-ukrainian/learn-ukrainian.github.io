# Folk module production standard + ship checklist

**Canonical reference exemplar:** `curriculum/l2-uk-en/folk/koliadky-shchedrivky/`
(promoted as the quality bar for the ~36 remaining folk seminar builds, 2026-06-19).

This is the practical, copy-this-shape standard. The deeper design rationale lives in
`docs/best-practices/v7-design-and-corpus.md` (V7 SSOT) and the folk write rules at
`scripts/build/phases/linear-write-seminar-folk-rules.md`. Read those first; this doc is the
folk-specific "what a finished module looks like" + the predicate you run before shipping.

---

## 1. Section shape (what koliadky-shchedrivky uses)

A folk seminar module is long-form Ukrainian prose (≈5,000+ words) with these movements:

1. **Розминка** — a hook that opens on a *primary text* and poses the module's central question.
2. **Конфліктна карта** — lays out the live scholarly debates as debates (name / text / rite), not as
   settled fact. Teaches the reader to separate *claim type* (etymological / textual / ritual / comparative).
3. **Читання** — guided close-reading of the verbatim primary texts, with an explicit read-model
   (name the situation → extract the action → state the conclusion, each tied to a line).
4. **Аналіз** — poetics + ritual function (the thesis that every device is applied magic, not ornament).
5. **Дискусія** — "what survived and why," competing hypotheses held side by side, honest treatment of
   dark motifs (the antisemitism `:::caution`), and modern relevance (2022–2025).
6. **Підсумок** — returns to the opening question; the reader now answers with evidence.
7. **Словничок** — key terms consolidated.
8. **Питання для самоперевірки** — source-grounded self-check questions.

Plus the experiential folk text-layer components below, and `<!-- INJECT_ACTIVITY: act-N -->` anchors
for the folk activity families.

## 2. The styled folk components (custom container directives → MDX islands)

| Directive | Renders as | Use for | Required? |
|---|---|---|---|
| `:::primary-reading` | 📜 "Читаємо першоджерело" box (`PrimaryReading`) | Every verbatim corpus-verified folk-song original. **Word-count-excluded.** | **≥4 when the corpus has ≥4 distinct verified fragments** (see §3 caveat) |
| `:::myth-box` | `MythBuster` (claim vs truth, both sourced) | Decolonial correction of an imperial / Soviet / romantic myth | ≥1 where evidence supports |
| `:::high-culture-bridge` | `HighCultureBridge` (≥2 nodes + note) | Folk-form → opera / literature / world-circulation connection | ≥1 where evidence supports |
| `:::note` / `:::caution` / `:::info` | Starlight-native admonitions | Asides, honest cautions, external-resource panels | as needed |

`:::myth-box` and `:::high-culture-bridge` take a YAML payload (claim/truth/claim_source/truth_source;
nodes/note). `:::primary-reading` wraps a Markdown blockquote + an `— attribution` line.
Converter: `scripts/generate_mdx/converters.py::convert_folk_content_blocks`.

Activities (`activities.yaml`): prefer the folk families `ritual-sequencing` (#42),
`variant-comparison` (#43), `motif-formula` (#44), `performance` (#45) over generic quiz/match-up where
the corpus supports them. Do NOT emit `audio-block`, `symbolic-decode`, or `aural-genre-id` (deferred).

**Activity placement — inline vs workbook (intent must be explicit).** `activities.yaml` is a bare
list. An activity is rendered **inline** in the lesson where the module body has a matching
`<!-- INJECT_ACTIVITY: act-N -->` marker (the activity needs an `id: act-N`). Every activity WITHOUT an
inject marker is **auto-appended as a "Вправи / Workbook" section** at the end (each gets its own `###`
heading) — it is NOT dropped. koliadky-shchedrivky uses 3 inline (act-1/2/3) + 7 workbook. This is by
design, but it is easy to misread as "7 unreferenced activities," so make the split deliberate: give the
inline ones `id:`+markers, and treat the rest as the intentional workbook set.

**`peer_review_guidelines` MUST be a YAML list, never a bare string.** A string is iterated
character-by-character into single-letter bullets in the rendered «Взаємоперевірка» block (caught on this
exemplar; root-caused in `scripts/yaml_activities.py::ActivityParser._as_str_list`, which now coerces a
string to a one-item list, with a regression test). Author it as a list of 1–3 guideline sentences.

## 3. Corpus-hammer law (the part that bites — learned on this exemplar)

**Every embedded verbatim folk fragment must `verify_quote` against the build corpus, under the author
it is attributed to.** Concretely:

- Box only fragments that return `matched=true` (aim confidence ≥0.95) via `mcp__sources__verify_quote`
  with `author="Народна творчість"` (or the actual folk-collection author). The koliadky exemplar's
  three boxes all verify at 1.0 against chunks `61bfde21` (колядка) and `70435c0b` (щедрівка).
- **A folk variant that exists in the corpus only as a quotation inside a scholarly work (Грушевський,
  Енциклопедія українознавства, etc.) is NOT a gate-safe folk-primary quote** — it returns
  `matched=false` under «Народна творчість» because the corpus row is authored by the scholar. Do NOT
  box it. You may mention such a variant in *prose* (it is a factual claim about the folkloric record),
  but only if VESUM-clean (next bullet). This is exactly why the exemplar's Розминка was switched from
  the from-memory «Коли не било з нащада світа» variant to the corpus-exact «Як ще не було початку світа».
- **The `vesum_verified` gate scans PROSE (including incipits inside «лапки»), not just plain words.**
  Archaic/dialectal forms (`нащада`, …) fail VESUM and turn `python_qg` red. Keep archaic forms ONLY
  inside `:::primary-reading` (excluded from the gate); in prose use modern codified forms.
- Never quote a folk song from memory — not even famous ones (`Щедрик-ведрик`, `Коляд-коляд`,
  `А ми просо сіяли`). Never embed literary-authored verse (Шевченко, Франко, …) as a folk primary text.
- **≥4 is corpus-bound.** koliadky-shchedrivky's gate-safe folk corpus holds 2 distinct songs → 3 boxes.
  Topics with a richer §4 dossier should hit ≥4. Do NOT backfill to 4 with memory or scholarly-cited
  fragments; honesty over count.

## 4. Resources (`resources.yaml`)

- ≥1 `role: reading` entry with a one-line learner task in `notes`, whose `url:` is a **public
  allowlisted URL** (`data/primary_text_sources.yaml`) — the topic's `uk.wikipedia.org` article is the
  floor; a specific `uk.wikisource.org` / `litopys.org.ua` / `ukrlib.com.ua` work page when one resolves.
- On-site primary text is surfaced via `:::primary-reading`, NOT via an internal `wiki/...` path
  (those are AI-facing and are rejected).
- All resource titles/notes must be VESUM-clean (the `vesum_verified` gate scans them too — brand names
  like «Вікіджерела» and hyphenated tokens can fail; prefer plain attested words).

## 5. Definition of Done — run the predicate, don't assert it (#3137/#3138, #M-4)

From the **data-bearing tree** (symlink `data/sources.db` + `data/vesum.db` + `site/node_modules` into
the worktree), per module:

```
.venv/bin/python -m scripts.build.verify_shippable folk <slug>            # python_qg + assemble + mdx_render
.venv/bin/python -m scripts.build.verify_shippable folk <slug> --astro-build   # + full astro render (CI also runs this)
```

Green means: `python_qg` all gates · `assemble_mdx` ok · `mdx_render` all island props evaluate.
(`astro_build` may be un-runnable locally if astro isn't installed in `node_modules` — CI's
"Frontend (build + vitest)" is then the authoritative full-render gate.)

**Then, and only then:**
1. **Corpus-hammer** (§3) — human read + independent `verify_quote` of every embedded fragment.
2. **Regenerate the site MDX** — folk uses `assemble_mdx` (NOT `generate_mdx.py`, which is core-only).
   Write `site/src/content/docs/folk/<slug>.mdx` from source and **commit it in the same PR** as the
   source edits (the MDX Source Parity gate requires both move together; #3643 tracks the missing
   forward-drift gate).
3. **Independent content review** — DeepSeek-pro (VESUM-backed), off-seat:
   `delegate.py dispatch --agent deepseek --model deepseek-v4-pro --mode read-only`. Apply valid deltas.
4. `handoff_ready --pr <N>` before declaring ready.

## 6. Per-module ship checklist (copy this)

- [ ] Section shape present (§1); ≈5,000+ words of grounded Ukrainian prose
- [ ] `:::primary-reading` for every verbatim original; each `verify_quote`=match under its author (§3)
- [ ] ≥1 `:::myth-box`, ≥1 `:::high-culture-bridge` where evidence supports
- [ ] Folk activity families used where the corpus supports; no deferred surfaces
- [ ] No from-memory or literary-authored verse boxed as folk-primary; archaic forms only inside boxes
- [ ] Prose + resource titles VESUM-clean (`vesum_verified` green)
- [ ] `role: reading` resource with a real task + public allowlisted URL
- [ ] Full Ukrainian immersion; no drift to explaining-in-English (#M-13)
- [ ] `verify_shippable` green (python_qg + assemble + mdx_render); CI astro build green
- [ ] Site MDX regenerated via `assemble_mdx` and committed in the same PR
- [ ] DeepSeek-pro content review clean (or deltas applied)
- [ ] Handoff refreshed + bundled in the PR; PR opened, NOT merged to main
