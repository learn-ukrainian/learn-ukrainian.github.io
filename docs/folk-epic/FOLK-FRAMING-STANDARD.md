# FOLK Framing Standard — the non-negotiable editorial standard for the folk track

> **This is the SSOT for HOW Ukrainian folk material is framed.** Every folk writer prompt,
> orchestrator, exemplar, review rubric, dossier, plan, and module is bound by it. Where any other
> folk doc disagrees with this one, **this doc wins** and the other doc is the bug.
>
> **Origin (DECISIVE, threat-class trust issue):** teacher feedback, user directive 2026-06-25. The
> folk track had drifted into a Soviet-ethnography *"pagan-survival / demonology / occultism / magic"*
> lens that (a) offends Christian Ukrainians — heirs of a Christian nation of 1000+ years — and (b)
> parrots the Russian *"Ukrainians-as-witches/характерники"* smear. This standard is the root-cause fix
> so that frame cannot regrow. Companion partial fixes that this doc supersedes/absorbs: PR #3745, the
> writer rule `#R-FOLK-RELIGIOUS-FRAMING`, and `folk-review-rubric.md` gate 7.

---

## Course identity (read this first — it determines everything below)

This is a **pre-literature course.** Ukrainian folklore (усна народна творчість) is taught as the **oral
foundation of WRITTEN Ukrainian literature** — exactly how the school program (gr 5–8 ukrlit) positions
it: the oral tradition that feeds Shevchenko, Franko, Lesya Ukrainka, the whole written canon. It is
**cultural and artistic heritage** — legends, songs, verbal art, and myths *as text-attested literary /
poetic material* (never as reconstructed pagan belief) — **not** a religion, not an occult practice, not a
field guide to spells. Frame it as literature-in-the-making, taught to learners of a Christian nation.

---

## The 4 pillars (every folk artifact must satisfy all four)

### Pillar 1 — Pre-literature / oral foundation of written literature
Present folklore as the **oral root of the written canon**, not as standalone ethnography or a worldview
manual. Tie genres forward to the literature they seed (дума → Shevchenko's epic voice; казка/легенда →
the literary fairy tale; народна пісня → the lyric). The learner should leave a module understanding how
this oral form fed Ukrainian *written* literature.

### Pillar 2 — Christian-heritage-first
Ukraine has been a **Christian nation for 1000+ years**; the folk corpus is overwhelmingly the heritage
of Christian people. Where a tradition is Christian, **the Christian meaning gets parity or primacy** —
never demotion to a "shell" over a "pagan core."
- **колядки = Christmas / Nativity carols; щедрівки = Christmas-season / New-Year / Маланка / Щедрий-вечір
  well-wishing songs** in the Eastern-rite folk-Christian tradition — both величально-побажальні
  (praise + well-wishing).
- Великдень, Різдво, вертеп (Nativity drama), народні легенди (народне християнство), обжинки (harvest
  thanksgiving transmitted in Christian village culture) etc. are framed in their Christian meaning first;
  agrarian imagery may be noted descriptively, never as an older "core" the Christian meaning overlays.
- **In Christian framing, God is the Creator** — a pagan cosmogony is **never** presented as *the* creation
  account; at most it is a minor, explicitly-scholarly note about an older poetic stratum — never doctrine,
  never foregrounded.

### Pillar 3 — Written-text base + school-canonical sourcing
Every module is built on **written, verifiable text** from the school-aligned canon, not on reconstructed
"folk belief."
- **PRIMARY canonical source = the school textbooks in `data/sources.db`** (`textbook_sections` /
  `textbooks`, gr 5–8 ukrlit — the folklore unit). These ARE the МОН / osvita.ua-aligned canon; host the
  text in its **standard / school form.**
- **SECONDARY = ukrlib / uk.wikisource / litopys** — corroboration only.
- **`osvita.ua` is an authoritative reference but is © — verify against it and LINK; never host verbatim.**
- **Tag provenance** on every text (primary-canonical vs secondary-corroboration). **Stop treating
  secondary as primary.** Do NOT host archaic-dialect variants where a standard school form exists
  (the bad `koliadka-yak-shche-ne-bulo` reading «лем / небонько / сонінько…» is the anti-example).

### Pillar 4 — No occult / no pagan-as-held-belief; material culture is context, not a module
- **Never** present pre-Christian religion as held-true belief, demonology / occultism / witchcraft /
  spell-craft as real practice, or "magic" as the thesis of a module. Pre-Christian motifs appear **only**
  as minor poetic / folk-art imagery or a scholarly-noted older layer — never foregrounded, never doctrine.
- **Material culture / народознавство** (instruments, dance, pysanky, embroidery, crafts, dwelling,
  ritual food) is **CONTEXT inside a song/genre module, never its own module** — it has ~no ukrlit-canon
  basis as a standalone literature unit.

---

## The framing standard, stated as a hard rule (the NEVER list)

> Ukrainian folk culture = the heritage of a **Christian nation (1000+ yrs)**, taught as the oral
> foundation of written literature — legends, songs, verbal art, and myths *as text-attested literary /
> poetic material (never reconstructed pagan belief)* = **cultural/artistic heritage.**
> NEVER frame it as:
> - **(a)** literal pre-Christian **religion presented as held-true belief**;
> - **(b)** **demonology / occultism / witchcraft / spell-craft** (the Russian smear — "Ukrainians as
>   witches / характерники"); reduce a Christian-folk genre to «прикладна магія» / a "magic" act; or build
>   a «дохристиянське ядро / християнська оболонка (нашарування / шар)» **pagan-core-Christian-veneer**
>   structure — that is the Soviet-atheist "pagan-survival" distortion, a known writer-bias trap, **not**
>   a neutral scholarly default;
> - **(c)** **pagan cosmogony as THE creation account** — God created the world; Christian creation gets
>   primacy.
>
> Pre-Christian motifs only as minor poetic / folk-art imagery or scholarly-noted older layers — never
> foregrounded, never doctrine. Christian meaning gets **parity/primacy** where the tradition is Christian.
> If the "magic / pagan-survival" reading is mentioned at all, attribute it explicitly as a contested /
> Soviet-era frame and balance it — never assert it as neutral fact.
> Where older agrarian strata are genuinely relevant (e.g. spring веснянки/гаївки, купальські), treat them
> as **older poetic motifs / formulae attested in cited scholarly notes — never as the learner-facing
> thesis, and never as "magic" the rite performs.** The scholarly term `продукувальна магія` may appear
> **only** inside such a cited note, **never** as framing and **never** for колядки/щедрівки.

---

## The osvita.ua / school-canon validity test (does this module deserve to exist?)

A folk module is only valid if its topic is a **real unit of the school-aligned ukrlit canon.** The
**deterministic test = query the school textbooks in `data/sources.db`** (`textbook_sections` /
`textbooks`, gr 5–8 ukrlit) — the imported textbooks ARE the osvita.ua / МОН canon, so this is faster and
more reliable than crawling osvita.ua.

- **TEACHES (valid units):** колядки, щедрівки, купальські, веснянки, козацькі / чумацькі пісні,
  соціально-побутові пісні, родинно-побутові пісні, коломийки, думи, балади, легенди, перекази,
  прислів'я, загадки, колискові, казки, історичні пісні, кобзарство / кобзарська традиція, …
- **NEARLY ABSENT → badly-conceived → CUT or redesign:** окультизм (**0** canon hits), замовляння-as-
  spells (≈4), демонологія (≈5 — and those hits sit in *authored literary works* as characters/motifs,
  NOT as folk-belief units). If a topic has no real canon basis, the module is the bug — **cut it or fold
  its genuine content into a valid genre module as context.**

> **Counts above are from a `textbook_sections` / `textbooks` query over gr 5–8 ukrlit, 2026-06-25 (#M-4).
> Re-run the query before citing a specific number as a cut rationale — do not treat these as frozen.**

**Rule:** no folk module survives that fails this test. Material-culture / народознавство topics fail it
as standalone *literature* units and become context, per Pillar 4.

---

## Consequences already locked (keep / fix / cut)

These follow directly from the pillars + validity test (full per-module verdict in the driver handoff,
user-confirmed 2026-06-25). The principle, not the list, is canonical here:

- **CUT — contaminated, no canon basis:** `narodni-viruvannia-mifolohiia-demonolohiia`,
  `zamovliannia-zaklynannia-prymovky`.
- **CUT — material culture / народознавство (no ukrlit-canon basis as a standalone literature unit; use as
  context inside genre modules):** instruments, dance, pysanky, embroidery, crafts, dwelling, ritual food.
- **RETITLE / REFRAME:** `koliadky-shchedrivky` (drop «Міф про створення світу» → Nativity / Christian
  carols), купальські/русальні (recenter on songs + Зелені свята; русалки handled carefully as motif),
  чарівні казки (drop "ініціація"), казки про тварин (drop "тотемізм"), narodna-kultura-yak-systema
  (→ clean pre-literature intro).
- **KEEP & FIX (the clean canon core):** kalendarna, vesnianky, жниварські, родинна обрядовість, весільні,
  голосіння, думи, кобзарство, історичні пісні, балади, народні легенди (народне християнство), приказки,
  прислів'я, загадки, колискові, коломийки, родинно-побутові / суспільно-побутові пісні, вертеп (Nativity
  drama), and the rest of the ukrlit-canonical genres.

**Reuse-and-fix, not delete:** nothing is deleted from the corpus; nothing is reused without re-vetting
against THIS standard + the validity test. The poison is in the framing and in which modules exist — fix
those, keep the good text.

---

## How to use this doc

- **Writers** (`scripts/build/phases/linear-write-seminar-folk-rules.md`, rule `#R-FOLK-RELIGIOUS-FRAMING`):
  obey the NEVER list and all 4 pillars on every folk module.
- **Orchestrators** (`docs/prompts/orchestrators/folk/*`): read this doc First; apply the validity test in
  preflight, the framing checks in production/remediation, and flag any violation in quality audit.
- **Reviewers** (`docs/folk-epic/folk-review-rubric.md`): the framing standard is a **hard, fail-the-
  artifact gate** — a single pagan-survival / magic / occult / demonology-as-belief framing = BLOCK.
  Reviewer is **cross-family to the writer (GPT↔Claude); NO DeepSeek for folk culture.**
- **Exemplar** (`docs/folk-epic/EXEMPLAR-STANDARD.md`): describes the mechanical shape; this doc governs
  the editorial framing of whatever fills that shape.
