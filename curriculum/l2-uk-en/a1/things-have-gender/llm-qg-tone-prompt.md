{"review_model": "claude-opus-4-8", "reviewer": "claude-tools", "writer": {"effort": "high", "model": "gemini-3.8-flash-high", "writer": "agy-tools"}}
V7 UPGRADE review of the complete module across all lessons. Review the published lesson unit, not a fresh module build. No wiki packet or plan rewrite applies. Assess preservation, lesson_split, coherent progression, first-use cumulative vocabulary, final module closure, no named narrator, marked attributed quotations with Resources entries, and side-by-side English support for added A1 Ukrainian passages of three or more sentences. Judge the current dimension independently using exact quotes from these artifacts. Stress annotation follows review. Lesson map:
{"lessons": [{"n": 1, "title": "Він, вона, воно", "sections": ["Діалоги", "Він, вона, воно"], "minutes": 60, "word_target": 550, "activities": {"total": 10, "inline": [4, 6], "workbook": [6, 9]}, "unverified_stress": [], "unverified_lemmas": []}, {"n": 2, "title": "Предмети навколо", "sections": ["Предмети навколо"], "minutes": 60, "word_target": 550, "activities": {"total": 10, "inline": [4, 6], "workbook": [6, 9]}, "unverified_stress": [], "unverified_lemmas": []}, {"n": 3, "title": "Підсумок", "sections": ["Підсумок", "Імена, пастки й самоперевірка"], "minutes": 60, "word_target": 550, "activities": {"total": 10, "inline": [4, 6], "workbook": [6, 9]}, "unverified_stress": [], "unverified_lemmas": []}], "closes_module": 3, "provenance": [{"placement": "inline", "index": 0, "new_id": "act-1", "lesson": 1}, {"placement": "inline", "index": 1, "new_id": "act-2", "lesson": 1}, {"placement": "inline", "index": 2, "new_id": "act-3", "lesson": 1}, {"placement": "inline", "index": 3, "new_id": "act-5", "lesson": 1}, {"placement": "inline", "index": 4, "new_id": "act-4", "lesson": 2}, {"placement": "inline", "index": 5, "new_id": "act-9", "lesson": 3}, {"placement": "workbook", "index": 0, "new_id": "act-w1", "lesson": 1}, {"placement": "workbook", "index": 1, "new_id": "act-w2", "lesson": 2}, {"placement": "workbook", "index": 2, "new_id": "act-w3", "lesson": 2}, {"placement": "workbook", "index": 3, "new_id": "act-w4", "lesson": 3}, {"placement": "workbook", "index": 4, "new_id": "act-w5", "lesson": 3}], "items_min_exempt": [{"id": "act-9", "reason": "4-item original activity preserved from baseline"}, {"id": "act-w5", "reason": "5-item original activity preserved from baseline"}], "proper_names": []}

You are reviewing one quality dimension for the generated module below.
Return ONLY the JSON object described in the response format. Do not ask for
clarification, do not summarize the prompt, and do not emit prose outside the
JSON object.

# North Star — Curriculum Reboot (#1577 Phase 0 draft)

> **Status:** DRAFT v3.1 — v3 signed off by Codex + Gemini in `architecture`
> channel thread `6de2be4789394536abdb6356cd5bb006` (round 2, both
> `[AGREE]`). v3.1 layered 2026-05-18 to reflect the ULP-derived
> student-aware immersion model that landed via decision card
> `2026-05-13-ulp-derived-student-aware-immersion.md` (ACCEPTED).
> Open questions §OPEN QUESTIONS resolved per panel consensus and folded
> into policy. Ready for Phase 3 prompt-template injection.
>
> v3 corrects v2 on the immersion model: there is **no B1 entry sub-band**.
> The transition out of English finishes inside A2; B1 onwards is 100 %
> Ukrainian. The only sanctioned English at B1+ is the **Словник (vocab
> tab) translation column** — used for L1 anchoring of new lemmas and
> idiom/expression explanation.
>
> **v3.1 — immersion is now ULP-derived, not flat-%.** The earlier model
> read flat band percentages from `scripts/config.py` `IMMERSION_POLICIES`.
> That model has been superseded by **`compute_immersion_band(track,
> module_num, learner_state)`** which derives immersion floors and
> ceilings from the learner's cumulative vocabulary count + the module's
> declared `plan.targets.new_vocabulary` + the lemma-frequency map. The
> feature flag `USE_ULP_IMMERSION_DERIVATION` is set to `True` at
> `scripts/config.py:145` (live default). The earlier "Known pipeline
> drift" callout below (Phase 2 IMMERSION_POLICIES cleanup) has been
> RESOLVED via the ULP card's Phase 4 calibration replay. The B1+ rule
> ("100 % Ukrainian everywhere except Tab 2") is unchanged in intent —
> the mechanism is now cumulative-vocabulary-aware derivation rather
> than static module-range bands.
>
> This document, with `docs/lesson-contract.md`, is the preamble every
> prompt template will inject from Phase 3 onward (writer, all LLM QG
> reviewers, activities author, plan reviewer). It answers "what are we
> shipping and why?" — referenced, not re-explained, downstream.

---

## WHO — the learner

A self-driven adult or older teen who reads English fluently and starts
with **zero Ukrainian**. Three real archetypes:

1. **The reconnecting diaspora** learner whose grandparents spoke
   Ukrainian and who wants to read Ukrainian literature, history, and
   thought without going through Russian.
2. **The post-2022 supporter** who picked up "Слава Україні" and now
   wants to understand the country at the intellectual depth that
   Ukrainians themselves engage at.
3. **The serious linguist / educator** who needs a free,
   source-grounded reference because nothing else in English meets that
   bar.

What unites all three: the destination is **engaging directly with the
Ukrainian intellectual tradition** in Ukrainian — Shevchenko, Franko,
Lesya Ukrainka, Stus, Zabuzhko, Andrukhovych, Pidmohylny, Khvylovy,
Zhadan; Hrushevsky and Plokhy on history; Hulak-Artemovsky and the
Cossack chronicles; Ruthenian Baroque sermons; Old East Slavic
manuscripts. **L2 acquisition is the cost of admission, not the finish
line.**

The learner is not a child. Talk to them as a peer. They will not be
flattered by emoji confetti or "great job!" stickers; they will be
respected by clear explanations, honest references to source, and a
visible escalator from "literally cannot read Cyrillic" to "reading
Stus in the original."

## WHY — what does not exist anywhere else

There is no free, comprehensive, decolonized, source-grounded
**escalator from zero-Ukrainian to the Ukrainian intellectual canon**
in English. What exists today is one of:

- Soviet-era textbook frames lightly retranslated (Russian as the
  invisible default, Ukrainian as the dialect)
- Tourist-phrasebook surface (Привіт / дякую / borshch, no grammar)
- Paid apps optimized for streak retention, not language acquisition
- Excellent native-Ukrainian school textbooks (Караман, Большакова,
  Вашуленко, Захарійчук, Кравцова) that English speakers cannot read
  because they are written in Ukrainian for Ukrainian children
- Niche scholarly anthologies (Plokhy, Snyder, Pidmohylny in
  translation) that an English speaker can read about Ukraine but not
  read FROM Ukraine

We close that last gap end to end. We treat the native textbook
tradition as the authority, cite it directly, and engineer an
end-to-end L2 escalator that ends inside the Ukrainian intellectual
canon. **This is education, not software.** Real people will use these
modules as their first contact with the language. Bad pedagogy becomes
bad habits that take years to undo. There is no "ship and iterate" for
someone's foundation. **Five excellent modules beat fifty-five mediocre
ones.**

## HOW — the working principles

### The escalator, end to end

The curriculum is one long arc with three structurally different
stages:

1. **A1 + A2 — literacy bootstrap (124 modules).** The learner cannot
   read Cyrillic on day one. English is the carrier; Ukrainian is the
   target. Immersion ramps progressively as cumulative vocabulary
   builds — early A1 modules sit in the 5–25 % Ukrainian range,
   late A2 modules sit in the 65–90 % range, but the exact band per
   module is **derived per-build** by `compute_immersion_band(track,
   module_num, learner_state)` from cumulative-vocab count + this
   module's declared new vocabulary + the lemma-frequency map. The
   end of A2 is structurally where the learner finishes the
   transition out of English; A2's final band absorbed the work that
   used to live in a "B1 entry" sub-band.

2. **B1 + B2 + C1 — immersion preparation (319 modules).** **At and
   after B1, every module body is 100 % Ukrainian.** No English in
   theory prose, no English in dialogues, no English in activity
   instructions, no parenthetical glosses on grammar terms, no rescue
   notes. The single sanctioned English at this stage lives in **Tab 2
   (Словник)** — the vocabulary tab carries English translations and
   English explanations of idioms and expressions, because that is the
   tab's structural purpose (L1-anchored flashcards). Nothing else in
   the module body is English. B1+B2+C1's job is to take a literate
   A2 graduate and make them ready to consume Ukrainian primary
   intellectual material directly.

3. **The seminars — the destination (1,100+ modules across HIST,
   BIO, ISTORIO, LIT, LIT-essay, LIT-war, LIT-fantastika,
   LIT-hist-fic, LIT-humor, LIT-youth, LIT-doc, LIT-drama,
   LIT-crimea, OES, RUTH, plus PRO tracks for B2-pro / C1-pro).**
   Full-Ukrainian deep dives into Ukrainian history, biography,
   literature, paleography, Ruthenian Baroque, Old East Slavic. They
   are why the rest exists. NOT in the EPIC #1577 MVP cut, but the
   architecture of every preceding module must keep them as the
   gravitational center. (See `mvp-deferred` labels on issues #1141,
   #1140, #1139, #1137, #1135, #1134, #1133, #1132, #658, #497.)

The EPIC #1577 MVP cut — A1 + A2 + B1 — is the **first three
escalators** in the chain. We ship them first because they prove the
entire pipeline; we keep the seminars in mind because they're where
every learner is going.

### Plans, contract, immersion

**Plans are sacred.** All 218 MVP plans (A1: 55, A2: 69, B1: 94) plus
the seminar plans are State Standard 2024 grounded and already
reviewed. The reboot does not redesign plans. It designs the pipeline
that consumes them faithfully. (See `curriculum/l2-uk-en/plans/`,
EPIC #1577, salvage manifest §1 KEEP.)

**Plans drive content; the contract drives shape.** A plan says WHAT
the module teaches and WHICH SECTIONS in WHICH ORDER. The lesson
contract (`docs/lesson-contract.md`) says WHAT TABS, WHAT COMPONENTS,
and WHAT DATA SHAPES the published MDX must have. Writer respects
both. Reviewer scores against both.

**Immersion is band-strict and tab-aware, derived per-build.** A1+A2
immersion uses `compute_immersion_band(track, module_num,
learner_state)` to derive each module's band from cumulative
vocabulary + this module's declared new vocabulary + lemma-frequency
map. The derivation is deterministic and tested; the calibration
constants (`_ULP_VOCAB_KNEE_PER_BAND`, `_RECYCLE_CADENCE_DEFAULTS`,
`_PATTERN_FREQ_MASTERY_THRESHOLD`) live in `scripts/config.py`,
calibrated against Anna Ohoiko's ULP S1–S6 corpus.
**B1 onwards is uniformly 100 % Ukrainian** in every tab except
Tab 2 (Словник), where English translations and idiom/expression
explanations are sanctioned as the only L1 scaffolding. Writer hits
the band; reviewer scores against the band; nobody freelances. The
A2→B1 boundary is the single biggest discontinuity in the whole
curriculum.

> **Phase 2 IMMERSION_POLICIES cleanup — RESOLVED 2026-05-13.** The
> earlier flat-% `b1-m01-05` and `b1-core` "rescue English" bands
> have been superseded by the ULP-derived model. The decision card
> at `docs/decisions/2026-05-13-ulp-derived-student-aware-immersion.md`
> shipped via PR1 (learner-state V7 wiring) + PR2 (ULP derivation +
> Phase 4 calibration replay). The feature flag
> `USE_ULP_IMMERSION_DERIVATION = True` at `scripts/config.py:145`
> activates the derivation. The B1+ rule ("Full Ukrainian immersion.
> No English in module body. Tab 2 (Словник) keeps L1 translations
> and idiom explanations as the only English") is enforced today.

### Sourcing and verification

**Real textbook citations, not invented authority.** Every grammar
claim and every cultural fact roots in an attributed source —
Караман Grade 10 p. 176; Кравцова Grade 4 p. 113; Заболотний Grade 5
p. 83; Большакова Grade 1 p. 24; Захарійчук Grade 1 p. 13. The wiki
packets the writer consumes are themselves source-cited. Ghost
references fail the build.

**VESUM verification is non-negotiable.** Every Ukrainian word the
writer emits is checked against `data/vesum.db` (409 K lemmas, 6.7 M
forms) before publish. Pre-training is contaminated by Russian; we do
not trust ourselves on Ukrainian morphology. Whitelist exceptions
live in `scripts/audit/config.py` `PROPER_NAME_WHITELIST`.

**Decolonized framing is the default, not an opt-in.** Ukraine has
its own canon (Шевченко, Франко, Леся Українка, Стус, Жадан, Забужко,
Андрухович, Підмогильний, Хвильовий). It has its own history
(Київська Русь as Ukrainian, the Cossacks, the UNR, the OUN-UPA, the
Holodomor, the language ban decrees, 2014, 2022). We do not inherit
the Soviet cultural map. Kyiv-born Russian-imperial writers
(Bulgakov, Gogol, Akhmatova, Pasternak) stay Russian. Yulia
Tymoshenko and other Russian-aligned figures do not appear as
exemplars. Holodomor is genocide; the war is a war, not a "conflict."

### Pipeline discipline

**Cross-agent QG, not self-review.** The writer never reviews its own
output. The pipeline runs Python QG (deterministic, objective) and
LLM QG (pedagogical, by a different agent than the writer).
Self-review is caught by `SELF_REVIEW_DETECTED` and fails the build.

**No autonomous patching loops.** The V6 convergence loop (writer →
reviewer → writer-rewrites-from-feedback → reviewer → ...) failed to
converge over 5 months. The new pipeline is linear: deterministic
check → if Python can auto-fix the format, do it; else fail fast →
if LLM QG fails, scoped regeneration of THE failing section OR human
review. Maximum 1 scoped regen attempt per failing section. No
infinite repair.

**Python QG and LLM QG do not overlap.** Python checks word count,
forbidden lemmas, structural rules, vocabulary-coverage, citation
roundtrip, MDX renders, INJECT_ACTIVITY ids resolve. LLM checks
pedagogical flow, naturalness, decolonized framing, register,
dialogue authenticity. LLM is forbidden from enforcing structural
rules; Python is forbidden from scoring tone.

**Three-agent consultation discipline.** Architecture decisions: all
three agents (Claude + Codex + Gemini) discuss in the `architecture`
channel; both `[AGREE]` before commit. Implementation: primary agent
plus one peer review. Mechanical edits: primary alone. (See EPIC
#1577 critical invariants §7.)

**Freeze contracts per slice.** One lesson schema; one wiki schema;
one plan schema; one QG rubric; one exemplar module. Scale only
after the exemplar ships clean end-to-end.

## VOICE — how the prose sounds

Voice changes by stage because the carrier language changes.

**A1 + A2 voice (English carrier ramping out, Ukrainian growing):**
- Peer English, not teacherly-condescending. Direct, friendly, dry.
- Concrete characters from the textbook tradition (Марко and Софія
  meet on the street; their teacher walks in; the dialogues have
  stakes).
- English carries the explanation; Ukrainian carries the examples
  and dialogues; we never translate Ukrainian examples into English
  when their job is to BE Ukrainian.
- Stress marks on first introduction.
- No AI tells. No "Let's dive in." No "It's important to note." No
  "In conclusion." No emoji confetti. No "great job!" stickers.

**B1 + B2 + C1 voice (full Ukrainian, no English in body):**
- Ukrainian peer voice — natural, register-appropriate, not
  textbook-formal unless the section calls for it.
- Grammar is explained in Ukrainian using Ukrainian linguistic
  terms (дієслово, відмінок, недоконаний вид, видова пара). New
  abstract terms get a one-sentence Ukrainian definition the first
  time they appear, the way Ukrainian school textbooks introduce
  them. **No parenthetical English glosses in the body.** L1
  anchoring lives in Tab 2 (Словник), where each new lemma carries
  an English translation column and idioms / expressions get an
  English explanation note.
- No mirrored English translations after Ukrainian paragraphs. No
  English blockquote glosses. No English narrative scaffolding in
  the main body. No "rescue notes" in English.
- Activity instructions (Tab 3) are 100 % Ukrainian.

**Seminar voice (full Ukrainian, scholarly register):**
- The voice of the level (Decolonizer for HIST, Stylistic Critic for
  LIT, Paleographer for OES, Baroque Scholar for RUTH — per
  `scripts/config.py:51-141` `TRACK_CONFIG`).
- Decolonized framing throughout: not "Russian and Ukrainian
  literature both," but "the Ukrainian tradition that imperial
  power tried to erase and the chronology that survives in the
  primary sources."
- Honest about uncertainty. Unverified claims wear a
  `<!-- VERIFY: ... -->` marker until verified.
- Concrete primary-source citations: page numbers, manuscript refs,
  archival shelfmarks where relevant.

**Decolonized vocabulary across all stages:** Кіт, not кот. Добре,
not хорошо. Брати душ, not приймати душ. Тактовний (tactful) ≠
тактичний (tactical).

## SHIPPABLE — when a module is done

A module ships when ALL of these are true:

1. **Plan respected.** Every `content_outline.section.points` item
   appears in its named section. Word budget per section within
   ±10 % tolerance. (`scripts/build/contracts/module-contract.md`
   §2.)
2. **Word count.** Total ≥ `word_target` from
   `scripts/audit/config.py` `LEVEL_CONFIG[{level}].target_words`.
   (Targets are MINIMUMS. Never lowered to fit short content.)
3. **Vocabulary clean.** 100 % VESUM-verified or whitelisted. Zero
   Russianisms, Surzhyk, calques, paronym confusions. (Four
   separate checks per `ukrainian-linguistics.md` rule.)
4. **Citations resolve.** Every textbook citation roundtrips against
   the wiki packet / sources MCP. No ghost authors. No invented
   page numbers.
5. **Immersion band respected.** A1+A2 modules respect the band
   derived per-build by `compute_immersion_band(track, module_num,
   learner_state)` from cumulative vocabulary + declared new vocab +
   lemma-frequency map. **B1 and every higher level are 100 %
   Ukrainian in every tab EXCEPT Tab 2 (Словник).** Any English in
   B1+ Tab 1 / Tab 3 / Tab 4 module body fails the immersion gate
   regardless of percentage math. Tab 2 English is structural and
   does not count against the body-immersion rule.
6. **Python QG green.** All deterministic checks pass.
7. **LLM QG ≥ floor.** Pedagogical, Naturalness, Decolonization,
   Engagement, Tone — each ≥ the per-level floor in
   `scripts/common/thresholds.LEVEL_THRESHOLDS`. No weighted
   average: one failing dim fails the module.
8. **MDX renders.** All 4 tabs build clean in Starlight; every
   `INJECT_ACTIVITY` id resolves; every component prop is
   well-formed.
9. **Activity types match level.** Per
   `docs/best-practices/activity-pedagogy.md` level → type matrix.
10. **Native-speaker reviewer signoff.** Phase 6 onward; for the
    Phase 4 exemplar, agent QG + author signoff is the gate. Tracked
    in `tests/test_human_eval_tracker.py`.

## WRONG — what we will not ship

- **AI slop English.** "Let's dive in." "In conclusion." "It's
  important to note." "Buckle up." Any padding the reader can
  detect as machine-generated.
- **Any English in B1+ module body** outside Tab 2 (Словник). No
  rescue notes, no parenthetical grammar-term glosses, no English
  activity instructions, no English mirror-translations of
  Ukrainian dialogues. The only English at B1+ is the Словник
  translation column and Словник expression notes.
- **Unflagged invented Ukrainian.** Any word VESUM rejects without
  a `<!-- VERIFY -->` and a verification path.
- **Russianisms.** Кот, хорошо, пожалуйста, спасибо, и так далее.
- **Surzhyk.** Шо, чо, ладно, харашо, в общем — unless explicitly
  taught as a register-marker.
- **Calques.** Приймати участь (→ брати участь), приймати душ (→
  брати душ), у мене є (→ я маю when "have" is the main predicate).
- **Russian-imperial cultural map.** Bulgakov, Gogol, Akhmatova,
  Pasternak, Brodsky as "Ukrainian writers" because of biography.
  They wrote in Russian, in Russian-imperial frames; they stay
  Russian.
- **Russian-aligned figures as exemplars.** Yulia Tymoshenko in
  particular. Default to verified contemporary figures: Yulia
  Svyrydenko (current PM), Volodymyr Zelenskyi, Serhiy Plokhy,
  Oksana Zabuzhko, Yuri Andrukhovych.
- **Soviet-era euphemisms.** "Conflict" for the war. "Famine" for
  the Holodomor. "Reunification" for occupation. "Brotherly peoples"
  for imperial subordination.
- **Activities that test content recall instead of language.**
  "У якому році Хмельницький підписав Переяславську угоду?" tests
  history memory, not Ukrainian. (See non-negotiable rule §9.) ZNO-
  format activities testing pure language mechanics are exempt.
- **Robotic dialogues.** Two strangers interrogating each other
  about jobs and addresses. Real Ukrainian dialogues from
  textbooks have someone looking for keys, ordering coffee,
  comparing morning routines — situations from life.
- **The user's two private teacher contacts named anywhere
  committed.** They live in `memory/MEMORY.md` only. Generic
  dialogue uses of common Ukrainian first names are fine; personal
  references to the user's two teachers are not.
- **"For now" or "good enough."** Word target not met → expand the
  content, not the threshold. Audit gate red → fix it, not lower
  it. Five excellent modules beat fifty-five mediocre ones.
- **LLM-rewritten content during the review loop.** Banned by
  ADR-007 / `tests/test_no_rewrite_contract.py`. Reviewer can
  output `<fixes>` find/replace pairs; the pipeline applies them
  deterministically; the writer does not regenerate prose
  mid-review.
- **Treating A1+A2+B1 as the product.** It is the L2 escalator.
  The product is reading Ukrainian intellectual material directly.
  Modules in the MVP that visibly forget this — that do not link
  forward to where the learner is going — fail the Engagement dim.

## RESOLVED POLICY (panel-confirmed 2026-04-25)

3-agent review thread `6de2be4789394536abdb6356cd5bb006` resolved the
following design questions unanimously. Each is now binding policy
and survives into the prompt-template preamble.

**P1 — Forward links to seminars are required, capped at 1 per module.**
Every MVP module MAY include exactly one natural one-sentence forward
link to a future-level or seminar-track destination ("Once you reach
B2 you'll meet this concept again in HIST/04 on the Hetmanate").
Forced or artificial linkage fails the LLM Engagement dim; the cap
prevents attention fragmentation. Source: panel consensus.

**P2 — Seminar plans are FROZEN under salvage manifest §1 KEEP.**
The seminar plans (HIST, ISTORIO, BIO, LIT, OES, RUTH, plus the lit-*
sub-tracks) do NOT get re-planned during the reboot. They sit in the
`keep` bucket and stay the destination. Re-planning only triggers if
the lesson contract forces shape changes seminars cannot accommodate
— and that gets its own design pass. Source: panel consensus.

**P3 — Native-speaker reviewer cadence: starts at Phase 5 fan-out.**
The Phase 4 exemplar (A1/20 `my-morning`) ships under agent QG +
author signoff only. Native-speaker review enters at Phase 5 when the
pipeline scales to A1 fan-out. Reasoning: the exemplar is a pipeline
proof, not a content-quality benchmark; introducing the human reviewer
before the pipeline is stable wastes their cycles. Source: panel
consensus.

**P4 — VESUM whitelist additions: writer proposes, reviewer approves.**
Writers may propose new entries to `PROPER_NAME_WHITELIST` during
build (e.g. when a wiki figure or place name needs to ship and isn't
in VESUM). Proposals require explicit reviewer signoff with source +
context (e.g. "Severyn Nalyvaiko — Cossack hetman, 1597; cited in
HIST plan; appears in Hrushevsky vol. VII"). Strict PR-only governance
would bottleneck seminar production at hundreds of historical /
literary / scientific names. Source: panel consensus.

**P5 — AI-slop detection: Python QG with hardcoded banlist.**
A small, deterministic list of banned English phrases ("Let's dive
in", "In conclusion", "It's important to note", "Buckle up", "Great
job!", etc.) lives in Python QG and fails the build deterministically.
Broader tone scoring (peer voice, no condescension, no AI cadence)
remains in the LLM Tone dim. Reasoning: hardcoded list is faster,
cheaper, and drift-free; LLM tone dim catches subtler patterns the
list cannot enumerate. Source: panel consensus.

**P6 — B1+ body-English Python QG threshold = ≤ 1 % Latin character
ratio**, token-aware, with Tab 2 + citation metadata excluded.
Tokenization skips URLs, ISO codes (e.g. `[uk]`), and proper-name
transliterations like `Kyiv` rendered inline next to `Київ`. See
`docs/lesson-contract.md` §5 for implementation detail. Source: panel
consensus.

**P7 — `scripts/config.py` IMMERSION_POLICIES cleanup is a Phase 2
sub-issue, not blocking Phase 4.** The Phase 4 exemplar is A1/20 and
does not hit the stale B1 code paths. The cleanup (delete
`b1-m01-05`, collapse `b1-core` to 100 %, rewrite rule string,
audit pipeline branches) is filed as a Phase 2 sub-issue under EPIC
#1577. Source: panel consensus.

> **2026-05-13 RESOLUTION:** P7 superseded by the broader ULP-derived
> immersion replacement (decision card
> `2026-05-13-ulp-derived-student-aware-immersion.md`). The static
> bands are no longer authoritative; `compute_immersion_band()` is.
> The B1+ rule string survives unchanged in intent; only the
> derivation mechanism changed.

---

**Phase 0 closeout actions** (after this commit):
1. Update `docs/session-state/archive/2026-04-25-evening-reboot-decision.md`
   line 82: `Зошит` → `Вправи` (lesson contract P1).
2. File the Phase 2 `scripts/config.py` IMMERSION_POLICIES B1
   cleanup issue per P7.
3. Wire `NORTH_STAR` and `LESSON_CONTRACT` placeholders into
   `scripts/build/phases/v6-write.md` "Shared Contract" preamble
   section as the AC-3 proof for #1578.
4. Comment on #1578 with the channel thread id and close.


# Lesson Contract v4 — published lessons under a module landing (#7994)

> **History:** DRAFT v3 — signed off by Codex + Gemini in `architecture` channel
> thread `6de2be4789394536abdb6356cd5bb006` (round 2, both `[AGREE]`).
> Open questions §7 resolved per panel consensus. Activity matrix in §3.4
> aligned with `docs/best-practices/activity-pedagogy.md` per Codex
> finding. Component count corrected per Codex finding.
>
> v3 corrections from v2:
> - §3.4 activity types fully aligned with `docs/best-practices/activity-pedagogy.md`
>   (was contradicting it on Transcription, EssayResponse, Observe,
>   ReadingActivity, MarkTheWords, Classify, Select)
> - §3 component-count line corrected: 50 `.tsx` + 5 `.astro` overrides
>   = 55 files, minus `utils.tsx` = 54 non-utility components
> - §7 open questions resolved inline as policy
>
> v2 from v1: B1+ immersion is uniform 100 % Ukrainian across every tab
> body, with the **Словник (Tab 2) translation column + idiom/expression
> notes** as the ONLY sanctioned English at B1+. The stale `b1-m01-05`
> band in `scripts/config.py` does not exist in this contract — Phase 2
> config audit cleans up the file. Tab 2 ``VocabCard`` stays slim per
> EPIC #1581 (site-wide dictionary section is separate from per-module
> Словник).
>
> **Purpose.** This document is the single source of truth for the SHAPE of
> a published lesson. The North Star says what we're shipping and why; this
> says what artifacts the pipeline must produce, what tabs the published
> MDX must have, and which Starlight components live in which tab. Phase 3
> formalizes the per-component prop schemas in YAML; this doc defines the
> structural skeleton Phase 3 will fill in.
>
> **Scope.** A1 + A2 + B1 MVP (218 modules). Higher-level
> (B2 / C1 / C2 / seminar / PRO) component support is described where
> relevant but the MVP does not exercise it. The seminar-only / C-only
> components are noted as "out-of-scope-for-MVP."

---

## 1. Published unit and source artifacts (v4)

V4 applies to curriculum upgrades: the **lesson** is the published unit under a
module landing. Option A emits `site/src/content/docs/{level}/{slug}/index.mdx`
and `{slug}/{n}.mdx`. Every lesson retains the four tabs described below. The
landing carries objectives, lesson cards and linked unions of vocabulary, practice
and resources; previous/next links advance by lesson. The final lesson closes the
module. Existing unsplit V7 modules continue to use the v3 single-page shape.

The canonical output level is `a1`; the previous edition is archived unchanged
at `a1-v1` with `base_level: a1`. Plans stay in `plans/a1/`. Production stays
untouched. A deterministic `lessons.yaml` assigns original sections and activities
before writing. The upgrade input is the existing module's four artifacts and
immutable plan. No wiki packet or new plan is authored. Source lesson files live
in `{level}/{slug}/lesson-{n}/`; only the map is pipeline-owned. Every original
paragraph remains verbatim in its assigned lesson (stress/whitespace normalization
only), and every original activity retains its payload and stable identity.

Each 60-minute lesson has at least 550 prose tokens and ten activities (4–6 inline,
6–9 workbook). The complete pilot split has at least 2000 prose tokens. Original
short-item exemptions are explicit in the map. Vocabulary is allocated once across
lessons and accumulates in published tabs and learner state. Stress annotation runs
after review; correctness, not just mark presence, is checked against the oracle.
No named narrator or self-introduction; people are named only inside dialogues.
Quotations are visibly attributed and listed in Resources. Added A1 Ukrainian
passages of at least three sentences have side-by-side English support.

Schema and exact acceptance: [Phase 1 spec](epics/curriculum-upgrade-phase1-spec.md).
The existing immersion exposure allocation remains a blocking residual documented
there; v4 does not silently change current thresholds.

### Legacy v3 artifact history

Every module's authoring output is a small set of files at
`curriculum/l2-uk-en/{level}/{slug}/`:

| File | Purpose | Schema authority |
|---|---|---|
| `module.md` | Theory prose (lesson narrative) — Tab 1 source | Plan section structure + Starlight `:::tip` callouts + `<!-- INJECT_ACTIVITY: {id} -->` placeholders + blockquoted dialogues |
| `activities.yaml` | Typed activity definitions — Tab 3 + inline-Tab-1 | `docs/ACTIVITY-YAML-REFERENCE.md`. Bare list at root, no `activities:` wrapper. Each item has `id`, `type`, `instruction`, type-specific payload |
| `vocabulary.yaml` *(or inline)* | Vocab list — Tab 2 source | Per `docs/best-practices/vocabulary-activity-standards.md`. Each entry: lemma + translation + part-of-speech + example sentence |
| `resources.yaml` *(or inline in `module.md`)* | External citations + media — Tab 4 source | Each entry: title + author + URL + access date + role (textbook/wiki/audio/video) |

Pipeline inputs the writer DOES NOT produce:

- **Plan YAML** — lives at `curriculum/l2-uk-en/plans/{level}/{slug}.yaml` (sacred, pre-existing, immutable mid-build per ADR-007 / non-negotiable rule §7).
- **Wiki packet** — context the writer reads but does not author. Owned by Phase 5+ wiki retrieval.
- **Annotation pass** — stress marks added deterministically AFTER review by `ukrainian-word-stress`, not by the writer.

### Plan Targets (PR2)

Plan YAML may declare an optional `targets` block. This is the unified,
machine-readable source for what a module introduces and deliberately
recycles:

```yaml
targets:
  new_vocabulary:
    - lemma1
    - lemma2
  new_grammar:
    - topic1
    - topic2
  recycle_vocabulary:
    - earlier-lemma
```

`targets.new_vocabulary` lists lemmas this module introduces.
`targets.new_grammar` lists grammar topics this module introduces.
`targets.recycle_vocabulary` is optional and names earlier lemmas the
module intentionally brings back. During PR2 migration, plans without
`targets` remain valid; tooling falls back to
`vocabulary_hints.required` for `new_vocabulary` so legacy plans keep
building while the explicit schema rolls out.

## 2. Published MDX shape

The pipeline's MDX assembler (today: `scripts/generate_mdx/core.py:267-364`)
produces ONE `.mdx` file at `starlight/src/content/docs/{level}/{slug}.mdx`
with:

- **Frontmatter:** `title`, `description`, `sidebar.order`, `sidebar.label`,
  optional `pipeline`, optional `build_status`, optional `draft`. Schema
  extension declared in `starlight/src/content.config.ts`.
- **Imports block:** every component used in the body, imported from
  `@site/src/components/...`.
- **One `<Tabs syncKey="module-tab">` block** with **exactly four
  `<TabItem>` children** in this order. Tab labels are the Ukrainian
  strings shown to learners; the English labels in the table are the
  canonical English aliases used throughout this contract:

| # | EN label | UK label (in code) | UK label (in handoff text) | What it contains |
|---|---|---|---|---|
| 1 | Lesson | **Урок** | Урок | Theory prose from `module.md` after activity-id substitution and shared transforms |
| 2 | Vocabulary | **Словник** | Словник | Vocabulary cards / flashcard deck / phrase table from `vocabulary.yaml` |
| 3 | Activities | **Вправи** | **Зошит** *(handoff says Зошит — code says Вправи — open Q1 below)* | All activities from `activities.yaml`, rendered as their typed components |
| 4 | Resources | **Ресурси** | Ресурси | External citations, source attribution, embedded video links |

The 4-tab structure is fixed; learners always see all four labels even
if a tab is empty (the empty state is a localized "No vocabulary for
this module" / "Немає словника для цього модуля" message — already
implemented at `core.py:283-302`).

## 3. Component inventory — 1:1 mapping

See `docs/best-practices/writer-prompt-appendix.md` § Component inventory for the full React component → MDX mapping. The writer prompt does NOT inline this — the authoring fields (consumed by `scripts/yaml_activities.py`) are surfaced via the COMPONENT_PROPS_SCHEMA template substitution and the §Activity Authoring Fields section in `linear-write.md`, which is what the writer acts on. Reference the appendix only if you need to debug a downstream MDX-render issue.

Per-tab activity surfaces:
- Tab 1 — Урок: explanation prose, dialogues, vocabulary previews
- Tab 2 — Словник: full vocabulary list
- Tab 3 — Вправи: workbook activities (fill-in, quiz, match, select, error-correction, drag-drop, anagram, mark-the-words, multiple-choice, true-false, hangman, gap-fill, listening, pair-up, order)
- Tab 4 — Джерела: textbook citations + multimedia resources

Component compatibility note: legacy `fill-in-the-blanks` is Deprecated; subsumed by `mark-the-words` and `gap-fill` in the V7 component inventory.

## 4. Constraints the writer must obey

1. **Tab 3 activities use only the 22 type strings in §3.4** (or the
   B2+ extensions when explicitly authorized by the plan). Unknown
   types fall through to `ActivityPlaceholder` and FAIL Python QG.
2. **`<!-- INJECT_ACTIVITY: {id} -->` ids must resolve** to an entry
   in `activities.yaml`. Unresolved ids fail the build.
3. **Every Tab 4 SourceBox must trace back** to a citation present in
   the plan's `references` field or in the wiki packet. Ghost
   citations (a SourceBox not justified by source data) fail Python
   QG.
4. **Vocabulary in Tab 2** — every lemma is VESUM-verified or
   whitelisted in `PROPER_NAME_WHITELIST`. Translations come from the
   writer with contextual disambiguation (not Балла-direct lookup).
5. **No empty tabs without justification.** The plan should account
   for all four tabs. If a module legitimately has no external
   resources, the plan declares this and the empty state renders.
6. **Immersion is band-strict and tab-aware:**
   - **A1 + A2:** writer hits the per-band ramp from `scripts/config.py`
     IMMERSION_POLICIES across all four tabs.
   - **B1+ (including B2, C1, C2, all seminars):** **Tab 1 / Tab 3 /
     Tab 4 module body is 100 % Ukrainian.** No exceptions, no rescue
     notes, no parenthetical English glosses on grammar terms, no
     English mirror-translations, no English narrative scaffolding.
     Tab 2 (Словник) carries English translations + English
     idiom/expression notes as a structural carve-out — this is
     the ONLY sanctioned English at B1+.
7. **Decolonized framing across all four tabs.** Same standards in
   `docs/north-star.md` § WRONG apply uniformly: no Russianisms, no
   Russian-imperial cultural framing, no Soviet-era euphemisms.

## 5. Constraints the pipeline must enforce

Python QG (deterministic) catches:

- Missing tab content (any of the four tabs entirely empty when the
  plan asserts content for it)
- Unknown activity `type` strings
- Unresolved `INJECT_ACTIVITY` ids
- Vocabulary entries failing VESUM verification (with whitelist)
- SourceBox citations that don't roundtrip against plan / wiki packet
- Word count under `target_words`
- Forbidden lemmas (Russianism / Surzhyk / calque list — to be
  formalized in Phase 3 / Phase 4)
- A1 + A2: immersion ratio outside the band's tolerance per
  `IMMERSION_POLICIES`
- **B1+: Latin-character ratio in Tab 1 / Tab 3 / Tab 4 module body
  exceeds a small allowance for proper-name spellings + ISO codes
  (≤ 1 % default). Tab 2 is exempt from this check.**
- MDX renders cleanly under Starlight (`npm run build` smoke test —
  enforced in CI per Phase 4)

LLM QG (pedagogical, by a non-writer agent) scores:

- Naturalness of the Ukrainian prose
- Pedagogical flow (do sections build on each other; is the rule
  introduced before the practice)
- Decolonization (framing, examples, references)
- Engagement (does the prose hold attention; are dialogues real)
- Tone (peer voice, no AI slop, no robotic interrogations)

The two layers must NOT overlap. LLM does not score word count; Python
does not score tone. (See North Star § HOW.)

## 6. What this contract DOES NOT specify

- Per-component prop schemas (Phase 3 work — `docs/lesson-schema.yaml`)
- Wiki packet schema (Phase 5 work)
- Plan YAML schema (already defined in `curriculum/l2-uk-en/plans/`
  and `scripts/build/contracts/module-contract.md`; this doc accepts
  it as given)
- Per-level word targets (already in `scripts/audit/config.py`)
- Activity-type pedagogy (already in
  `docs/best-practices/activity-pedagogy.md`)
- Site-wide ``/dictionary/`` section design (covered separately by
  EPIC #1581; per-module ``VocabCard`` only cross-links to dictionary
  entries — see §3.3)

## 7. Resolved policy decisions (panel-confirmed 2026-04-25)

3-agent review thread `6de2be4789394536abdb6356cd5bb006` resolved the
following design questions unanimously. Each is now binding policy.

**P1 — Tab 3 canonical Ukrainian label = `Вправи`.**
The running code (`scripts/generate_mdx/core.py:356`) is canonical.
The handoff doc reference to `Зошит` was a drafting error and gets a
one-line correction. Reasoning: `Вправи` accurately translates
"Exercises / Activities" and matches every existing curriculum module;
`Зошит` (notebook) is conceptually closer to the Tab 2 vocabulary
deck and would be misleading. Source: panel consensus.

**P2 — Inline-AND-aggregate activity rendering is intentional.**
An activity referenced via `INJECT_ACTIVITY` in Tab 1 ALSO appears in
the Tab 3 aggregate. The Tab 3 aggregate adds a
`(see lesson, §<section-title>)` cross-reference next to each entry
that was already encountered inline, so the learner knows they are
reviewing an activity they have seen rather than meeting a new one.
Source: panel consensus (intentional reinforcement; explicit
cross-reference required).

**P3 — At least one inline activity per major section is required.**
The writer must place at least one `INJECT_ACTIVITY` marker per
major Tab 1 section. No maximum cap; writer discretion for additional
inline activities and for end-of-section placement. Reasoning: breaks
walls of text, paces cognitive load, prevents writer from frontloading
all activities into Tab 3. Source: panel consensus.

**P4 — At least one Tab 4 (Resources) entry is required per module.**
The plan ALWAYS has `references`, so at minimum the module's plan
references re-list as `SourceBox` entries in Tab 4. Empty Tab 4
fails Python QG. Reasoning: zero-cost enforcement that prevents
citation drift; the empty-state localized message remains in the
codebase only as a fallback for malformed plans. Source: panel
consensus.

**P5 — Out-of-scope MVP components are hard-rejected by Python QG.**
At A1 + A2 + B1, any writer output emitting an out-of-MVP component
type (per §3.4.b list) or a deprecated type (per §3.4.c) fails the
build deterministically. The writer prompt at MVP levels ships only
the in-scope component list as the complete option set. Reasoning:
the writer should never need the out-of-scope set at MVP levels; an
emission is a hallucination. Source: panel consensus, contingent on
the §3.4 matrix alignment with `activity-pedagogy.md` (now done in
v3).

**P6 — B1+ body-English Python QG threshold = ≤ 1 % Latin character
ratio in Tab 1 / Tab 3 / Tab 4 module body, with Tab 2 + citation
metadata excluded.** Token-aware tokenization
(skip URLs, ISO codes like `[uk]`, proper-name transliterations like
`Kyiv` inline next to `Київ`). Tab 2 (Словник) is exempt — the
translation column is structural English, not body English. Citation
metadata in Tab 4 (English source titles, English publisher names,
English-language URL paths) is also exempt. Source: panel consensus
on the ≤ 1 % default with Codex's refinement that enforcement should
be token-aware rather than raw-character-ratio-only.

**P7 — VocabCard cross-link to dictionary section: SUPPRESSED until
EPIC #1581 ships.** Per-module `VocabCard` at MVP levels does NOT
emit a cross-link to `/dictionary/{lemma}/`. Once #1581 lands, this
contract is amended (see §6) and the cross-link prop becomes
required. Reasoning: keep the contract simple now; amend only when
the dictionary destination is real. Source: panel consensus
(option c).

---

**Phase 0 closeout actions** (after this commit):
1. Update `docs/session-state/archive/2026-04-25-evening-reboot-decision.md`
   line 82: `Зошит` → `Вправи` per P1.
2. File `scripts/config.py` IMMERSION_POLICIES B1 cleanup issue
   (Phase 2 sub-issue under EPIC #1577) — delete `b1-m01-05`,
   collapse `b1-core` to 100 % Ukrainian, rewrite rule string to
   match B2+ language, audit pipeline code for any `b1-m01-05` key
   branches.
3. Wire `NORTH_STAR` and `LESSON_CONTRACT` placeholders into
   `scripts/build/phases/v6-write.md` "Shared Contract" preamble
   section as the AC-3 proof for #1578.
4. Comment on #1578 with the channel thread id and close.


Shared module contract path: `scripts/build/contracts/module-contract.md`.

# Phase 4 Linear Per-Dimension Reviewer Prompt

Review only the assigned dimension. Cite concrete evidence from the generated
content. Return a machine-readable mapping with `score`, `evidence`, and
`verdict` for this one dimension.

The Generated Content block below is the only reviewable module text. Do not
read local files, follow filesystem paths, or use module text obtained from any
other checkout/session as evidence. Tools may be used for linguistic/source
verification, but not to replace the generated artifacts embedded in this
prompt.

Assigned dimension: tone

## Scope — JUDGMENT ONLY, do NOT re-litigate deterministic gates

Deterministic gates already ran before you. Treat their verdicts as ground
truth and do not score them again. The deterministic floor includes
(non-exhaustive): word counts, plan adherence, vesum_verified vocabulary
coverage, textbook grounding, immersion ratios, AI-slop patterns, activity
schema + types + props, formatting standards, `forbidden_words`
(SEVERE_RUSSIANISMS hard list), and `engagement_floor` (callout minimums +
META_NARRATION zero-tolerance ban).

Your job in this LLM dim is the residual judgment that regex cannot make.

## Level Calibration — do not mis-score intended scaffolding

Apply the level contract before scoring any dimension:

- A1: English scaffolding is expected and often substantial. Do NOT penalize
  English task support, English grammar terminology, or line-level glosses when
  they support a Ukrainian-first teaching move. Penalize only English-led
  lecture prose that replaces the Ukrainian anchor, or internal writer/reviewer
  scaffolding that leaked into learner-facing content.
- A2: easy Ukrainian should be the default body voice, with decreasing English
  support for first-introduction grammar, safety clarifications, and concise
  glosses. Do not demand B1-style Ukrainian-only prose, but flag English
  paragraphs that take over the lesson.
- B1/B2/C1/C2: learner-facing prose should be Ukrainian-led. English support is
  exceptional, local, and justified; English-led sections are evidence against
  tone, naturalness, and pedagogy.
- Seminars: use advanced Ukrainian teaching voice. English leakage, generic
  inspirational language, or school-textbook simplification is evidence against
  tone/naturalness unless the plan explicitly requires a bilingual artifact.

For `tone` specifically:

- `engagement`: does the prose actually *hold attention*? The gate already
  confirmed callout count + META_NARRATION absence; you assess whether the
  callouts carry real pedagogy vs filler, whether the tone is warm vs
  bureaucratic, whether direct-address phrases (e.g. `Notice the soft sign
  in **писатися**`) are content-anchored vs generic, whether dialogue feels
  human vs robotic. Score the *quality* of engagement, not its presence —
  presence is the gate's job.
- `pedagogical`: does the sequencing actually teach? Are examples
  illuminating? Does each concept earn the next? The gate confirmed word
  budgets and section presence; you assess whether the pedagogy *works*.
  Source-pedagogy failures are in scope even when the plan/wiki asked for
  them: REVISE or REJECT any grammar module that promotes a metaphor,
  discourse heuristic, activity label, or writer-created grouping into a
  grammar taxonomy unless Ukrainian textbook/corpus evidence explicitly
  supports that framing. Do not reward plan adherence when the upstream
  plan/wiki itself appears pedagogically unsupported. For example, a lesson
  may use "background/foreground" as an optional writing heuristic after
  aspect is taught, but if it asks learners to classify every verb as
  `тло`/`подія` as though those are textbook grammar categories, flag
  `unsupported_taxonomy_frame` and score the pedagogical dim below PASS.
  Likewise, if a module teaches impersonal/no-subject forms, examples and
  activities must preserve the no-subject property; adding an ordinary subject
  noun to the target pattern is a pedagogical grammar error, not harmless
  context.
  REJECT-level failures mirroring writer rules:
  - Mirrors `#R-NO-SCAFFOLDING-LEAKS`: REJECT writer-side scaffolding leaks.
    Writer-side scaffolding never appears in module body. Forbidden in
    published markdown: panel IDs (`P1`, `P2`, ...), Krok-N labels
    (`Крок 5:`, `Step 5:`), obligation names from the wiki_coverage manifest
    (`ban-4`, `step-5`, ...), reviewer-fix anchors, phase names, gate names.
    The module is a finished lesson, not a writer's worksheet.
  - Mirrors `#R-NO-CHILDREN-PRIMARY-QUOTES`: REJECT `>` blockquotes from
    textbooks at Grade 1, 2, or 3 levels in the published module body. Grade
    1-3 RAG hits can still ground lexical choices, but do not surface as
    quoted material. Default: NO blockquote unless it pedagogically advances
    the lesson AND comes from an adult-appropriate source (Grade 7+, adult
    literature, Антоненко-Давидович, style guides). Adult A1 learners are
    not reading children's primers; reject `Захарійчук, Grade 1, p.24` as
    lesson prose.
  - Mirrors `#R-GRAMMAR-TERMS-A1`: REJECT A1 English explanations that avoid
    the rule: Use proper grammatical terminology in English explanations.
    The accepted terms are **noun**, **verb**, **adjective**, **adverb**,
    **pronoun**, **reflexive**, **conjugation**.
    REJECT folksy paraphrase (`a thing`, `an action`, `a word for`,
    `a doing-word`, `the X-form of Y`) in lieu of grammar terms.
  - Mirrors `#R-CLEAN-TABLES`: REJECT bold-everywhere tables. Tables: bold
    ONLY the target Ukrainian forms; pronoun columns (`я`, `ти`, ...),
    English headers, and English glosses remain in regular weight. REJECT
    conjugation tables teaching a present-tense paradigm that omit `ви` or
    `вони` from the FULL set of person/number rows: **я / ти /
    він,вона,воно / ми / ви / вони** (six rows). Vocabulary tables stay
    two-column unless a third column adds essential teaching value (e.g.,
    stress mark, IPA).
- `naturalness`: does Ukrainian read as native? The gate confirmed VESUM +
  russianism shadow; you assess flow, register, idiom, grammar government, and
  collocation. This is a linguistic-quality review, not a vibes review.
  Actively search for:
  - calqued or evasive passives where native Ukrainian would use an active,
    impersonal, or result-state construction;
  - wrong government/prepositions (for example, prefer `чекати на когось/щось`
    where a bare English-style object such as `чекайте номер` sounds calqued);
  - wrong verb choice for ordinary Ukrainian collocations (`відчинити/зачинити`
    for doors/windows, `відімкнути/замкнути` for lock/unlock actions,
    `прийняти препарат/ліки` rather than drinking medicine, etc.);
  - anthropomorphic or model-translated metalanguage (`форма просить`,
    `застереження каже`, `правило хоче`) unless quoted as a deliberate learner
    mnemonic;
  - unnatural nominalizations, bureaucratic phrasing, literal English/Russian
    sentence architecture, or register shifts that a Ukrainian editor would
    rewrite even if every surface form passes VESUM.
  If you find two or more concrete native-style Ukrainian defects in generated
  Ukrainian prose, score naturalness below PASS even when deterministic gates
  passed. Name the defect type in `rubric_mapping` and quote the exact offending
  phrase.
- `decolonization`: is the lesson teaching Ukrainian **on its own terms**?
  The gate confirmed forbidden_words.

  **Anchoring principle: teaching codified Ukrainian to learners of a
  historically depressed language IS the substantive decolonization act.**
  Do NOT score 9.0+ as requiring extra anti-colonial rhetoric piled on top
  of clean canonical teaching. That would politicize grammar lessons
  without adding pedagogical value. The scoring anchor differs by module
  type:

  **Topic-neutral modules (grammar, vocabulary basics, phonetics):**
  9.0+ baseline if all three apply when learner-facing contrast is explicitly authorized;
  if contrast is deferred for foundational modules, baseline is still possible when (a), (c), and strict anti-Russian-as-reference execution are present.
  (a) Ukrainian-canonical vocabulary throughout (e.g. `сніданок` not
  `завтрак`, `рушник` not `полотенце`, `одягатися` not `одіватися`) —
  using VESUM/Pravopys-2019 codified forms, not Russified or surzhyk
  approximations.
  (b) If the module is authorized for learner-facing bad-form contrast,
  include at least one bad-form contrast marker pair
  (`<!-- bad -->завтрак<!-- /bad -->` → `сніданок`) where learners are
  likely to encounter the Russified form.
  If no contrast is authorized, this point is satisfied through clear absence-only
  decolonization: no Russian-as-reference framing, no raw bad-form insertion, and
  full VESUM/Pravopys-2019 form coverage.
  (c) Grammar and morphology presented on Ukrainian terms — VESUM /
  Pravopys-2019 as the authority — NOT scaffolded through "like Russian
  but..." or cross-language similarity as the entry point. One brief
  stance line (e.g. "Ukrainian routine words are short and practical")
  is a bonus but NOT a requirement to clear 9.0.

  **Topic-loaded modules (history, biography, literature, culture, war,
  politics):** higher bar because the topic demands it. 9.0+ requires
  substantive framing: explicit Russification / imperial-framing /
  Soviet-euphemism rejection where relevant. A history module that says
  "Civil War" instead of "Українська революція 1917-1921" or "Soviet
  famine" instead of "Holodomor / genocide", a bio module that uses
  Russian-imperial transliteration of a Ukrainian figure's name, or a
  literature module that frames Ukrainian writers as "regional Russian
  literature" — these fail decolonization regardless of vocabulary
  cleanliness.

  **REVISE territory (<9.0):**
  - Leans on Russian to explain Ukrainian ("the Russian equivalent
    would be...") as the primary scaffolding.
  - Uses Russified vocabulary unmarked (no bad-form contrast).
  - Presents Ukrainian as derivative of Russian.
  - For topic-loaded content, omits substantive framing the topic demands.

  **REJECT territory (<7.0):**
  - Uses Russocentric periodization or Soviet euphemisms uncritically.
  - Treats Russian-imperial sources as authoritative on Ukrainian subjects.

  When you score, name the module's TYPE explicitly (topic-neutral vs
  topic-loaded) in your reasoning and apply the corresponding anchor.
  A morning-routine grammar module scoring 8.5 because the rubric was
  read as demanding more rhetoric than the topic supports is a
  reviewer-protocol failure under this anchor.
- `tone`: is the teacher's voice consistent and warm? The gate caught
  META_NARRATION; you assess everything else about register.
  REJECT-level failures mirroring writer rules:
  - Mirrors `#R-SINGLE-VOICE-A1`: REJECT mid-module register shifts (English
    -> Ukrainian metalanguage -> preachy imperative -> casual paraphrase).
    The module must have one teacher voice across the whole module: warm,
    clear, direct ("you" / "your"). REJECT third-person framing of the
    learner (`the student`, `студента`, `the reader`, `учня`).
  - Mirrors `#R-AUDIENCE-LANGUAGE-A1`: REJECT grammar-translation lectures
    at A1/A2. The module must teach Ukrainian through Ukrainian with English
    as a receding scaffold: Ukrainian term first, em-dash gloss after
    (`прокидаюся — I wake up`), `<DialogueBox uk="..." en="..." />` with a
    Ukrainian-only `uk` turn, Ukrainian-only comprehension/recall content, a
    named persona or named characters, and no foreigner-textbook anti-patterns
    such as transliteration tables, "X sounds like Y in English", "the student
    must learn", or English topic-sentence openers.

A dim score that re-states what a deterministic gate already enforced is a
reviewer-protocol failure. Cite something the gate cannot see.

## Writer Obligation Context — same source material the writer saw

Use these blocks as context when judging the residual quality dimension. Do
not turn this into a new scoring dimension and do not re-run the deterministic
wiki coverage gate; the point is to know what the writer was obligated to
teach while applying the existing `tone` rubric.

### Wiki Obligations Manifest

```json
{
  "slug": "things-have-gender",
  "wiki_path": "wiki/pedagogy/a1/things-have-gender.md",
  "phonetic_format_reference": [
    "Spoken target in `[...]` single-character square brackets, not Unicode look-alikes",
    "Pair written and spoken form in close lexical proximity (same sentence or adjacent bullet)",
    "Copy >=1 textbook example verbatim when the wiki provides one"
  ],
  "sequence_steps": [
    {
      "id": "step-1",
      "obligation_id": "step-1",
      "category": "sequence_steps",
      "summary": "Крок 1."
    },
    {
      "id": "step-2",
      "obligation_id": "step-2",
      "category": "sequence_steps",
      "summary": "Крок 2."
    },
    {
      "id": "step-3",
      "obligation_id": "step-3",
      "category": "sequence_steps",
      "summary": "Крок 3."
    },
    {
      "id": "step-4",
      "obligation_id": "step-4",
      "category": "sequence_steps",
      "summary": "Крок 4."
    },
    {
      "id": "step-5",
      "obligation_id": "step-5",
      "category": "sequence_steps",
      "summary": "Крок 5."
    }
  ],
  "l2_errors": [
    {
      "id": "err-1",
      "obligation_id": "err-1",
      "category": "l2_errors",
      "summary": "Use Моя книга, моя ручка instead of Мій книга, мій ручка (якщо говорить чоловік): Помилка: Англомовні учні часто намагаються узгодити присвійний займенник зі своєю власною статтю (як мовця), а не з граматичним родом самого предмета."
    },
    {
      "id": "err-2",
      "obligation_id": "err-2",
      "category": "l2_errors",
      "summary": "Use Де стіл?"
    },
    {
      "id": "err-3",
      "obligation_id": "err-3",
      "category": "l2_errors",
      "summary": "Use Це мій тато."
    },
    {
      "id": "err-4",
      "obligation_id": "err-4",
      "category": "l2_errors",
      "summary": "Use Мій собака дуже гарний."
    },
    {
      "id": "err-5",
      "obligation_id": "err-5",
      "category": "l2_errors",
      "summary": "Use Я студент."
    }
  ],
  "phonetic_rules": [],
  "decolonization_bans": [
    {
      "id": "ban-1",
      "obligation_id": "ban-1",
      "category": "decolonization_bans",
      "summary": "Цей розділ є критично важливим для формування автентичної української мовної картини світу."
    },
    {
      "id": "ban-2",
      "obligation_id": "ban-2",
      "category": "decolonization_bans",
      "summary": "По-перше, категорично забороняється пояснювати рід чи відмінювання українських слів через порівняння з російською («в українській так само, як у російській, але...»)."
    },
    {
      "id": "ban-3",
      "obligation_id": "ban-3",
      "category": "decolonization_bans",
      "summary": "По-друге, необхідно пильнувати за лексичним наповненням."
    },
    {
      "id": "ban-4",
      "obligation_id": "ban-4",
      "category": "decolonization_bans",
      "summary": "Під час фонетичного супроводу нових слів (наприклад, при поясненні голосних закінчень роду) не можна наводити англомовні фонетичні аналогії, які спотворюють українські звуки (наприклад, порівнювати українське «и» з англійським «i» у слові «bit» чи з російським «ы»)."
    },
    {
      "id": "ban-5",
      "obligation_id": "ban-5",
      "category": "decolonization_bans",
      "summary": "При формулюванні привітань та прощань у прикладах і діалогах використовуйте лише питомо українські форми: Добрий день (а не «здрастуйте » чи інші кальки) та До побачення."
    }
  ],
  "external_resources": []
}
```

### Implementation Map Contract

```text
Manifest obligations: 15.
Each row below is a pre-resolved slot the writer MUST fill at the artifact indicated by `artifact`, located by `location_hint`, populated using `treatment_template` as the structural blueprint.

- obligation_id: ban-1  (obligation_type: decolonization_ban)
  artifact: module.md
  location_hint: (any prose section)
  subtype: absence_required
  treatment_template:
    shape: module.md prose absent of any phrasing matching manifest_payload.rule (negative obligation: absence-of-pattern)
- obligation_id: ban-2  (obligation_type: decolonization_ban)
  artifact: module.md
  location_hint: (any prose section)
  subtype: absence_required
  treatment_template:
    shape: module.md prose absent of any phrasing matching manifest_payload.rule (negative obligation: absence-of-pattern)
- obligation_id: ban-3  (obligation_type: decolonization_ban)
  artifact: module.md
  location_hint: §Він, вона, воно
  subtype: substance_required
  treatment_template:
    shape: module.md prose absent of any phrasing matching manifest_payload.rule (negative obligation: absence-of-pattern)
- obligation_id: ban-4  (obligation_type: decolonization_ban)
  artifact: module.md
  location_hint: §Підсумок
  subtype: absence_required
  treatment_template:
    shape: module.md prose absent of any phrasing matching manifest_payload.rule (negative obligation: absence-of-pattern)
- obligation_id: ban-5  (obligation_type: decolonization_ban)
  artifact: module.md
  location_hint: (any prose section)
  subtype: absence_required
  treatment_template:
    shape: module.md prose absent of any phrasing matching manifest_payload.rule (negative obligation: absence-of-pattern)
- obligation_id: err-1  (obligation_type: l2_error)
  artifact: activities.yaml
  location_hint: activities.yaml
  treatment_template:
    activity_stub: {"items": [], "sentence": "", "type": "error-correction"}
    expected_correction_value: Моя книга, моя ручка
    expected_error_value: Мій книга, мій ручка (якщо говорить чоловік)
    shape: activities.yaml entry with fields {sentence, error, correction}
- obligation_id: err-2  (obligation_type: l2_error)
  artifact: activities.yaml
  location_hint: activities.yaml
  treatment_template:
    activity_stub: {"items": [], "sentence": "", "type": "error-correction"}
    expected_correction_value: Де стіл? — Він там.
    expected_error_value: Де стіл? — Воно там. (Where is the table? — It is there.)
    shape: activities.yaml entry with fields {sentence, error, correction}
- obligation_id: err-3  (obligation_type: l2_error)
  artifact: activities.yaml
  location_hint: activities.yaml
  treatment_template:
    activity_stub: {"items": [], "sentence": "", "type": "error-correction"}
    expected_correction_value: Це мій тато. / Він Микола.
    expected_error_value: Це моя тато. / Вона Микола.
    shape: activities.yaml entry with fields {sentence, error, correction}
- obligation_id: err-4  (obligation_type: l2_error)
  artifact: activities.yaml
  location_hint: activities.yaml
  treatment_template:
    activity_stub: {"items": [], "sentence": "", "type": "error-correction"}
    expected_correction_value: Мій собака дуже гарний.
    expected_error_value: Моя собака дуже гарна.
    shape: activities.yaml entry with fields {sentence, error, correction}
- obligation_id: err-5  (obligation_type: l2_error)
  artifact: activities.yaml
  location_hint: activities.yaml
  treatment_template:
    activity_stub: {"items": [], "sentence": "", "type": "error-correction"}
    expected_correction_value: Я студент. / Мене звати Джон.
    expected_error_value: Я є студент. / Моє ім'я є Джон.
    shape: activities.yaml entry with fields {sentence, error, correction}
- obligation_id: step-1  (obligation_type: sequence_step)
  artifact: module.md
  location_hint: §Концепція «Хто?» і «Що?» та базові займенники.
  treatment_template:
    required_claim: Крок 1. Концепція «Хто?» і «Що?» та базові займенники. Спочатку вводиться концепція іменника як слова, що називає предмет. Учні вчаться розрізняти питання «Хто?» (істоти: людина, тварина) і «Що?» (неістоти: предмети, явища) . На цьому ж етапі вводяться особові займенники «він», «вона», «воно». Завдання автора-письменника — створити достатню кількість вправ, де учні просто тренуються ставити правильне питання до зображення чи слова .
    shape: module.md section heading or in-prose step marker matching manifest_payload.heading at the position implied by manifest_payload.step_num
- obligation_id: step-2  (obligation_type: sequence_step)
  artifact: module.md
  location_hint: §Рід істот (біологічна стать дорівнює граматичному роду).
  treatment_template:
    required_claim: Крок 2. Рід істот (біологічна стать дорівнює граматичному роду). Наступний крок — пояснити рід на прикладі людей. Тут англомовному учневі найлегше, адже граматичний рід збігається з біологічною статтю. Використовуються слова-маркери «мій/він» для чоловіків (тато, брат, син, співак) та «моя/вона» для жінок (мати, сестра, дочка, співачка) . Важливо показати, як утворюються парні назви істот, наприклад: малюк — маля, соліст — солістка . На цьому етапі учні вчаться конструкціям на кшталт «Це мій брат Назар. Він архітектор» або «Це моя сестра Оксана. Вона студентка» . Обов'язково вказується правильна форма: тато, а не російський відповідник .
    shape: module.md section heading or in-prose step marker matching manifest_payload.heading at the position implied by manifest_payload.step_num
- obligation_id: step-3  (obligation_type: sequence_step)
  artifact: module.md
  location_hint: §Перенесення категорії роду на неістоти.
  treatment_template:
    required_claim: Крок 3. Перенесення категорії роду на неістоти. Це критичний момент. Потрібно прямо заявити: «В українській мові стіл — це він, книга — це вона, а вікно — це воно». Для цього використовуємо слова з максимально прозорими фонетичними закінченнями . Чоловічий рід: приголосний звук (олівець, будинок, колектив, ячмінь) . Жіночий рід: закінчення -а, -я (земля, країна, мати) . Середній рід: закінчення -о, -е (сонце) . Учні тренуються замінювати слова на «він», «вона», «воно» .
    shape: module.md section heading or in-prose step marker matching manifest_payload.heading at the position implied by manifest_payload.step_num
- obligation_id: step-4  (obligation_type: sequence_step)
  artifact: module.md
  location_hint: §Засвоєння маркерів-закінчень як системи.
  treatment_template:
    required_claim: Крок 4. Засвоєння маркерів-закінчень як системи. Після того як концепція засвоєна, подаються таблиці типових закінчень. Учні дізнаються, що іменники, до яких можна додати слова «мій, він» (наприклад: тато, батько, ранок, січень), є іменниками чоловічого роду . Іменники зі словами «моя, вона» (мати, бабуся, річка, зима) — жіночого роду . А слова «моє, воно» (маля, серце, життя, літо) — середнього . На цьому етапі вводяться вправи на категоризацію слів за колонками (Ч.р., Ж.р., С.р.) .
    shape: module.md section heading or in-prose step marker matching manifest_payload.heading at the position implied by manifest_payload.step_num
- obligation_id: step-5  (obligation_type: sequence_step)
  artifact: module.md
  location_hint: §Винятки та слова спільного роду.
  treatment_template:
    required_claim: Крок 5. Винятки та слова спільного роду. Лише коли базова система закріпилася, можна переходити до ускладнень. Слід пояснити, що деякі чоловічі імена (Микола, Ілля, Михайло, Павло, Петро, Данило) закінчуються на -а/-я/-о, але залишаються чоловічого роду, оскільки позначають чоловіків . Також вводяться такі слова як батько, тато, дядько, що мають нетипове для чоловічого роду закінчення -о . Додається інформація про те, що слово собака в українській мові належить до чоловічого роду (на відміну від російської) . Згодом, на рівні А2-В1, можна вводити поняття іменників спільного роду (базікало, вереда) .
    shape: module.md section heading or in-prose step marker matching manifest_payload.heading at the position implied by manifest_payload.step_num

```

The Tier-1 audits below (A through I, expanded in this rebuild) feed evidence
into specific dims as labeled. Audit F (activity split) → pedagogical +
engagement. Audit G (corpus access) → all dims, weighted strongest for
pedagogical (out-of-level citations are mostly a pedagogical problem). Audit H
(student-aware) → pedagogical + engagement + naturalness. Audit I (audit-line
integrity) → all dims, as a meta-signal that the writer was honest with itself.

A dim scoring high while the audits surface FLAGs is a reviewer-protocol
failure — the dim's rubric must absorb the audit evidence. A dim scoring low
without any audit FLAGs is allowed, but evidence_quotes must justify the score
from the residual rubric alone.

## Reasoning checklist (do this before scoring)

Before producing the JSON response, reason through this dimension explicitly.
If the model supports extended thinking (Claude, Gemini, GPT-5.5), use it
for these four steps. Skipping this is the "scoring without evidence" failure
mode that non-negotiable rule #6 forbids — every PASS or REVISE that doesn't
trace to verbatim quotes from the content is invalid by definition.

1. **List 3 specific evidence quotes from the Generated Content related to
   `tone`.** Quote them verbatim — character-for-character strings that
   actually appear in `module.md`, `activities.yaml`, `vocabulary.yaml`, or
   `resources.yaml`. Do not invent. Do not paraphrase. Do not summarize.

2. **For each quote, state how it maps to the residual-judgment rubric for
   `tone`** (see scope section above; deterministic checks already ran).
   Is this quote evidence FOR the dimension being satisfied, or evidence
   AGAINST? A quote that just confirms a deterministic-gate criterion is
   not residual evidence — find a different one.

3. **Aggregate the score on the 1-10 scale.** Strongest evidence weighs more
   than weakest. What does the balance tell you? Round to 1 decimal place.

4. **Final verdict.** Score ≥8 → PASS. Score 6-7.99 → REVISE. Score <6 →
   REJECT.

The JSON response MUST include `evidence_quotes` with 3 verbatim quotes from step 1 and `rubric_mapping` explaining how each quote maps to `tone` before the score. The `evidence` field MUST be one of those verbatim quotes, wrapped in escaped quotes. A summary or paraphrase in any evidence field is a reviewer-protocol failure.

Quote-copy discipline: copy/paste exact substrings from Generated Content. Do
not normalize spelling, repair grammar, add or drop prepositions, change case
endings, translate, or smooth punctuation inside quoted evidence. If a sentence
is long, quote the shortest exact offending span instead of reconstructing the
whole sentence from memory. A finding is invalid if the `quote` string does not
appear in the generated artifacts exactly or via harmless whitespace
normalization.

Do not assign a score below 8 unless `rubric_mapping` names at least one
grounded residual defect and `findings` includes a quote from the Generated
Content for that defect. If all three evidence quotes are evidence FOR the
dimension and no concrete residual defect is present, the score must be at
least 8.

If you find concrete defects, emit structured `findings` entries and canonical
`issue_ids`. Use these issue IDs when they apply:

The examples in the issue-ID definitions below are canary examples and label
definitions, not evidence from the module. Do NOT copy them into `evidence`,
`evidence_quotes`, `quote`, `rubric_mapping`, or `findings` unless the exact
same string appears in the Generated Content artifacts. A finding whose quote
comes from this instruction block instead of the generated artifacts is a
reviewer-protocol failure and will be discarded/retried.

- `AWKWARD_PASSIVE_RESULT_STATE`: calqued/evasive passive or result-state
  wording such as `застосунок має бути відкритий` where a native Ukrainian
  editor would use an active, impersonal, or clearer state construction.
- `UNNATURAL_ANTHROPOMORPHISM`: model-translated metalanguage such as
  `форма просить`, `застереження каже`, or `правило хоче`.
- `UKRAINIAN_GRAMMAR_CALQUE`: Ukrainian grammar/naturalness calque, unnatural
  explanatory metalanguage, or reviewer-like paraphrase in learner-facing
  prose, such as `будь обережний, щоб небажаний результат не стався`.
- `ENGLISH_LEAKAGE`: English-led learner-facing prose that violates the level
  calibration above. Do not use this for allowed A1/A2 glosses or scaffolding.
- `AI_LEAKAGE`: model persona, scratchpad, refusal, draft, or self-correction
  text leaked into learner-facing content.
- `PATH_LEAKAGE` / `INTERNAL_LEAKAGE`: filesystem paths, source paths,
  internal gate names, or debug artifacts leaked into learner-facing content.
- `SEMINAR_REGISTER_PATHOS`: seminar prose that drifts into motivational,
  generic, propagandistic, or wrong-register pathos instead of advanced
  Ukrainian teaching voice.

For each finding, include at minimum `issue_id`, `quote`, `severity`, and
`explanation`. Leave `issue_ids` empty when no concrete defect applies.

## Tier-1 verification audit (do this during evidence search)

Сибір case study (May 2026): an unhardened reviewer let two fabricated
citations and a fused Shevchenko line pass on the writer's first try.
Run this audit on every quote / citation / claim in the Generated Content
that touches dimension `tone`. The audit feeds the evidence list above:
unverified items become FLAG strings in your evidence and weigh the score
down, not silent passes.

A. **Source-attribution audit (all dims).** For every dictionary / style-guide / author cited in the Generated Content, use the single-call primitive `mcp__sources__verify_source_attribution(source, claim)` where `source` ∈ {`grinchenko_1907`, `esum`, `sum11`, `antonenko_davydovych`, `literary`, `heritage`, `wikipedia`, `style_guide`}. Verdict `discusses=false` → FLAG `unverified citation`, treat as score-against. The compose-pattern (calling `search_definitions` / `search_style_guide` / `search_grinchenko_1907` / `query_pravopys` / `search_esum` separately) is acceptable only when you need to inspect specific evidence chunks beyond the boolean verdict; for the audit pass itself, the single-call primitive is mandatory.

B. **Quote verification (all dims).** For every authored quote attributed to a literary source, call `mcp__sources__verify_quote(author, text)`. Required: `matched=true` AND `best_confidence ≥ 0.85`. Verdict false or confidence below threshold → FLAG `fabricated quote`. The tool detects fused composites (two real sources stitched into one attributed line) by returning `matched=false` with non-zero near-misses — flag those as `fused quote`. The compose-pattern (`mcp__sources__search_literary` + grep) is forbidden for this audit; use `verify_quote` exclusively.

C. **Sovietization flag (decolonization, naturalness).** When the content
   draws from `search_definitions` (СУМ-11) for politically loaded
   headwords (`ленін*`, `більшовик*`, `радянськ*`, `соціалістичн*`,
   `партійн*`, `національн*`, `школа`, `шлях`, `прапор`), apply
   heightened scrutiny. The result row's `sovietization_risk` field
   (0/1/2) is ground truth; until it is wired through the writer, fall
   back to the keyword regex above. Soviet framing reproduced into the
   module without paraphrase or correction → FLAG
   `soviet-framed definition unsupervised`.

D. **Modern Ukrainian + heritage-defense audit (naturalness, decolonization).** Flag historical / Old East Slavic / Russian-shadow / pre-Pravopys-2019 forms presented as modern Ukrainian. Also flag the opposite error: authentic Ukrainian archaisms, historisms, or dialectisms mislabeled as Russianism/surzhyk/calque without VESUM/check_modern_form plus historical/etymological/source-context verification. Authentic non-standard forms must carry `[Archaism]`, `[Historism]`, or `[Dialectism]`, a modern standard equivalent, and a brief heritage note. Missing tag/equivalent → FLAG `untagged heritage form`; false Russianism claim → FLAG `heritage form misclassified`.

Reviewers verifying a heritage flag MUST themselves call `mcp__sources__search_heritage` (or `mcp__sources__search_slovnyk_me` for a slovnyk.me-only check) before sustaining or rejecting a heritage claim. A reviewer evidence_quote that asserts heritage status without a tool-grounded citation is a reviewer-protocol failure.
When reviewing a writer heritage claim, verify that slovnyk.me citations use canonical `dictionary_slug` values from `scripts/wiki/slovnyk_me.py` and that merged `search_heritage` citations name `source_family`, `source`, and `classification` when no `dictionary_slug` is present. If the writer cites no raw tool-result excerpt, or if your own `search_heritage` call returns empty, treat the claim as unresolved rather than accepting a heritage or Russianism label.

E. **Reinforce rule #6.** Every claim pairs (i) a verbatim quote from the
   content and (ii) a specific MCP-grounded verification or an explicit
   absence-of-verification flag. A `PASS` with no grounded evidence is a
   reviewer-protocol failure.

F. **Source-pedagogy audit (pedagogical dim; grammar modules).** Verify that
   the lesson's named teaching frame is a source-backed way to teach the
   grammar, not just an attractive model-generated metaphor. Search the
   textbook/corpus layer for the key Ukrainian terms in the module's grammar
   frame and compare the results to the generated task labels. If sources
   support the underlying grammar but not the module's taxonomy, flag
   `unsupported_taxonomy_frame`. If the plan/wiki introduced the unsupported
   frame, still flag it; do not treat "the writer followed the plan" as
   evidence for pedagogy. Heuristics are allowed only when clearly labeled as
   heuristics and not drilled as grammar categories. For impersonal/no-subject
   material, verify that target examples remain subjectless; a subject noun in
   the target pattern is `impersonal_subject_intrusion`.

G. **Activity split audit (pedagogical, engagement).** The writer is
contracted to emit two complementary activity sets per `ACTIVITY_CONFIGS[A1]`:
INLINE (light, theory-time checks anchored via `<!-- INJECT_ACTIVITY: act-N -->`)
and WORKBOOK (substantive, after-lesson drill, no INJECT marker). For A1:
INLINE 4-6 / WORKBOOK 6-9 (10 total). For A2: INLINE 4-6 / WORKBOOK 8-11
(12 total). For B1-core/B2-core/C1-core: INLINE 5-7 / WORKBOOK 11-15
(16 total). For C2: INLINE 4-5 / WORKBOOK 8-10 (12 total).

The writer is required to emit a self-audit line
`<activity_split_audit>level=A1 inline_n=N workbook_n=N inline_range=[lo,hi] workbook_range=[lo,hi] split_valid=true|false</activity_split_audit>`
before the artifact fences. Locate this line and verify:

1. The line is PRESENT. Missing → FLAG `activity_split_audit_missing`
   (counts as evidence-against this dim).
2. The reported `inline_n` matches the actual count of
   `<!-- INJECT_ACTIVITY: act-N -->` markers in `module.md`.
3. The reported `workbook_n` matches `len(activities.yaml) - inline_n`.
4. Both counts fall within the level's allowed ranges per §"Corpus Access" of
   the writer prompt.

If the writer's self-audit reports `split_valid=true` BUT the actual counts
violate the range, that is a worse failure than `split_valid=false` (a writer
lying in its own audit). FLAG `activity_split_audit_lied`.

Pedagogical consequence to score against: INLINE activities that are too
long/substantive (item count > 3, multi-paragraph rubrics) break their "fast
theory check" purpose; WORKBOOK activities that are too trivial (single-item
quizzes, no discrimination depth) break their drill purpose. Score the
BALANCE-vs-PURPOSE not just the count.

H. **Corpus-access audit (all dims).** The writer is gated to a level-specific
corpus surface per the Corpus Access (level-gated) table in `linear-write.md`.
Verify the writer did not cite out-of-level sources:

- **a1/a2 textbook scope**: only Grades 1-4 (a1) or 1-5 (a2) source files
  allowed in citations. A `Караман Grade 10` citation in an a1 module is OUT
  OF SCOPE. FLAG `out_of_level_textbook`.
- **a1/a2 literary scope**: only children's literature, folk songs,
  fairy-tale openings, iconic phrases. A Stus / Khvylovy / Zabuzhko /
  Pidmohylny quote in an a1/a2 module is a register break. FLAG
  `out_of_level_literary`. (The curated-tag filter — F1 — is not yet built;
  rely on author/work register judgment.)
- **a1/a2 external scope**: only `ulp_blogs`, `ulp_youtube`,
  `pohribnyi_pronunciation` from `search_external`. Citations from
  `istoria_movy`, `realna_istoria`, `komik_istoryk`, `imtgsh`, `other_blogs`
  at a1/a2 are out of scope. FLAG `out_of_level_external`.
- **b1+/seminars**: full corpus allowed; only flag if the writer claims a
  source NOT in our corpus at all (fabrication, separate failure class covered
  by audits A-B).

For ANY out-of-level citation, the quote may STILL be factually correct but the
register/source choice is wrong for the learner level. Score this as
PEDAGOGICAL evidence-against, not as a fabrication.

I. **Student-aware audit (pedagogical, engagement, naturalness).** The writer
is given a `(This is the first module — no prior learner knowledge.)` block listing cumulative_vocabulary +
known_grammar from prior modules. Verify the writer:

1. **Did not re-explain already-taught grammar.** If the learner-state lists
   "Genitive case endings -а/-я" as known_grammar and this module derives the
   rule from scratch in 200+ words, FLAG `re_explained_known_grammar`. Brief
   reference (`як ти бачив у модулі 7`) is fine; a full re-derivation is not.

2. **Did not introduce unknown vocabulary without inline gloss.** Scan
   `module.md` prose for Ukrainian content words. For any word that is (a) NOT
   in cumulative_vocabulary, (b) NOT in this module's `vocabulary.yaml`, (c)
   NOT a proper noun / Latin borrowing, and (d) NOT introduced with inline
   italic gloss `*(translation)*`, FLAG `unknown_vocab_unscaffolded`.

3. **Foreshadowing pattern visible.** If new lemmas appear in prose BEFORE
   their `vocabulary.yaml` entry, they should carry inline gloss at first
   mention. Absence of gloss on first mention = `missing_foreshadowing_gloss`.

4. **Stacked vocab-level check evidence.** For non-plan lemmas the writer
   introduced, check the `<plan_reasoning>` for `<vocab_level_check>` nodes.
   Missing for a non-plan lemma = `unverified_vocab_introduction`.

5. **Intentional repetition is signposted.** If the module repeats a
   learner-facing concept, skill, or activity family from earlier modules,
   the prose should explicitly frame it as review, reuse, or deeper practice
   before asking the learner to do it again. Good patterns: "You already
   practiced X in Module N; now use it for Y", "Quick review: X. New step:
   Y", or "This is the same X, but the task is harder because Y." If the
   repeated concept appears as if new, FLAG `unsignposted_repetition`.

Pedagogical score: respecting the learner's prior knowledge is what makes the
module BUILD instead of REPEAT. Naturalness score: scaffolded vocabulary
introduction reads as a real teacher's voice; un-introduced vocab feels like a
textbook dump.

J. **Pre-emit audit-line integrity (all dims).** The writer is required to
emit three machine-readable audit lines BEFORE the artifact fences, in order:

1. `<implementation_map_audit>manifest_obligations=N covered_in_map=M missing=[...]</implementation_map_audit>`
   (per #2094)
2. `<bad_form_audit>italic_bad_form_patterns_found=N converted_to_marker=N remaining=0</bad_form_audit>`
   (per #2095)
3. `<activity_split_audit>level=A1 inline_n=N workbook_n=N inline_range=[lo,hi] workbook_range=[lo,hi] split_valid=true|false</activity_split_audit>`
   (per the just-merged Activity Types section)

Verify ALL THREE lines are present, parseable, and report values consistent
with the artifacts. Any missing line = the writer has failed the protocol;
FLAG `audit_line_missing` with the missing line name. Any line whose claim
doesn't match the artifacts = FLAG `audit_line_inconsistent`.

These audits exist BECAUSE the writer is doing self-grading; the reviewer's
job here is to cross-check that the self-grading matches reality. A green audit
line on broken content is a more serious failure than a red audit line on
broken content (the writer is lying to its own audit).

Return the review object conforming to this authoritative JSON Schema (qg_schema.py, dimension profile). Use empty arrays for no findings/items and null only where the schema permits it.

```json
{
  "type": "object",
  "properties": {
    "score": {
      "type": "number",
      "minimum": 0,
      "maximum": 10
    },
    "evidence": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ]
    },
    "evidence_quotes": {
      "type": "array",
      "items": {
        "type": "string",
        "minLength": 1
      }
    },
    "rubric_mapping": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ]
    },
    "issue_ids": {
      "type": "array",
      "items": {
        "type": "string",
        "minLength": 1
      }
    },
    "findings": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "issue_id": {
            "type": "string",
            "minLength": 1
          },
          "quote": {
            "type": "string",
            "minLength": 1
          },
          "severity": {
            "type": "string",
            "minLength": 1
          },
          "explanation": {
            "type": "string",
            "minLength": 1
          },
          "replacement": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ]
          },
          "dimension": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ]
          }
        },
        "required": [
          "issue_id",
          "quote",
          "severity",
          "explanation",
          "replacement",
          "dimension"
        ],
        "additionalProperties": false
      }
    },
    "flags": {
      "type": "array",
      "items": {
        "type": "string",
        "minLength": 1
      }
    },
    "verdict": {
      "type": "string",
      "enum": [
        "PASS",
        "REVISE",
        "REJECT"
      ]
    }
  },
  "required": [
    "score",
    "evidence",
    "evidence_quotes",
    "rubric_mapping",
    "issue_ids",
    "findings",
    "flags",
    "verdict"
  ],
  "additionalProperties": false
}
```

The `flags` array MUST contain any FLAG strings raised during audits A-J that
apply to your assigned dim per the per-dim labeling in §"Scope". An empty array
is fine when no flags fired. The pipeline aggregates flags across dims and
surfaces them in the build telemetry; the writer's self-correction loop reads
them to know what to fix on retry.

## Module Context

- Level: A1
- Module: 8
- Slug: things-have-gender
- Word target: 1200

## Module Size Policy — dossier/evidence-led advisory context (#4801)

- Basis: core_evidence_packet
- Density band: core_pedagogy_standard
- Plan floor words: 1200
- Recommended range: 3500-5000
- Advisory ceiling words: 5000
- Expansion permission: source_backed_only
- Status: over_advisory_ceiling
- Rule: satisfy objectives and evidence coverage, not a token target; the reviewed plan floor still binds.
- Rule: expand only when added material is source-backed and pedagogically necessary.
- Rule: if grounded material runs out before the floor, emit `<!-- SIZE_POLICY_MISMATCH: plan floor exceeds sourced evidence -->` instead of inventing depth.
- Rule: do not repeat framing, conclusions, transitions, definitions, generic exposition, or uncited interpretation to reach the floor.
Notes:
- Core A1-C2 uses a pedagogy/evidence-packet basis; do not apply seminar dossier ceilings mechanically.
- Built module exceeds the advisory ceiling; expansion should be justified by sourced pedagogy.
- Reviewer rule: do not fail or pass a module on word count alone; deterministic gates handled the floor.
- Reviewer rule: inspect deterministic repetition evidence and marginal pedagogical value throughout the full size band, not only above the advisory ceiling.
- Reviewer rule: if the module is over the advisory ceiling, decide whether the extra length is source-backed density, necessary pedagogy, or filler/padding; length alone is not a failure.
- Reviewer rule: source-backed density is acceptable evidence; repeated framing, generic exposition, uncited interpretation, and inflated transitions are padding evidence.
Padding diagnostic:
- Status: over_advisory_ceiling
- Over advisory ceiling words: 1886
- Repetition status: clear
- Repetition matches: 0
- Review action: advisory_review_only; distinguish source-backed density from filler/padding

Use this as review context, not as a mechanical word-count gate. Inspect the
deterministic paragraph matches and marginal pedagogical value throughout the
full size band, not only above the advisory ceiling. Source-backed density and
necessary pedagogy remain acceptable even when long. Repeated framing,
conclusions, transitions, definitions, generic exposition, or uncited
interpretation are filler/padding defects when they affect `tone`.

## Immersion Rule

STRUCTURAL TARGETS (Phase A placeholders; Phase B calibrates):
- At least N UK dialogue lines (band: 0)
- At least N vocab entries (band: 0)
- At least N UK example sentences in bulleted lists (band: 0)
- No UK-only run longer than K words without inline English support (band: 10)
TARGET: 40-55% Ukrainian. ULP S1 bilingual immersion.
LANGUAGE ROLES:
- PRIMARY POSTURE: Ukrainian-first, example-first teaching with brief receding English support.
- ULP SSOT: follow docs/best-practices/ulp-presentation-pattern.md for the Ohoiko S1 rhythm. The full seven-practice contract is injected only for `letter_module: true` plans.

## Contract YAML

```yaml
sections:
- title: Діалоги
  word_budget:
    target: 300
    min: 270
    max: 330
- title: Він, вона, воно
  word_budget:
    target: 300
    min: 270
    max: 330
- title: Предмети навколо
  word_budget:
    target: 300
    min: 270
    max: 330
- title: Підсумок
  word_budget:
    target: 300
    min: 270
    max: 330
vocabulary_required:
- стіл (table, m)
- книга (book, f)
- вікно (window, n)
- кімната (room, f)
- ліжко (bed, n)
- стілець (chair, m)
- лампа (lamp, f)
- телефон (phone, m)
- комп'ютер (computer, m)
- він, вона, воно (he, she, it — gender test words)
vocabulary_optional: []
source_note: Full plan below is authoritative for points, activity hints, vocabulary,
  and references.
```

## Plan

```yaml
activity_hints:
- focus: Розподіліть предмети за родами (чоловічий/жіночий/середній)
  items: 12
  type: group-sort
- focus: Він, вона чи воно? Виберіть для кожного іменника.
  items: 8
  type: quiz
- focus: мій/моя/моє ___ (доберіть присвійний займенник до іменника)
  items: 8
  type: fill-in
- focus: Який рід? Подивіться на закінчення.
  items: 6
  type: quiz
- focus: Gender-flip diagnostic — оберіть український займенник (він / вона / воно).
    Дзеркалить п'ять рядків wiki "Типові помилки L2" + Приклад 5 один-до-одного (AC-3
    drift check). Усі правильні відповіді перевірено в VESUM.
  items:
  - answer: він
    options:
    - він
    - вона
    - воно
    question: Який у мене сильний ___ у плечі! (БІЛЬ)
  - answer: він
    options:
    - він
    - вона
    - воно
    question: Український ___ широкий і вітряний. (СТЕП)
  - answer: він
    options:
    - він
    - вона
    - воно
    question: Цей ___ на стіні — робота українського художника. (РОЗПИС)
  - answer: він
    options:
    - він
    - вона
    - воно
    question: Давній ___ «Повість временних літ» розповідає про Київську Русь. (ЛІТОПИС)
  - answer: вона
    options:
    - він
    - вона
    - воно
    question: 'Книжне / урочисте: «У далеку ___» — форма ж.р. (ПУТЬ, зворотний напрям)'
  type: quiz
changelog:
- changes:
  - 'Review-and-lock pass per docs/best-practices/wiki-plan-review-and-lock.md (rubric
    template: at-the-cafe #1412, who-am-i #1436).'
  - Added lifecycle markers (lifecycle / reviewed_at / reviewed_by / review_notes).
  - 'Added two objectives: (a) diagnostic принцип «український тест він/вона/воно
    + VESUM-парадигма» (5-item mini-drill); (b) feminitive as primary form for female
    professions.'
  - 'Added feminitive pairs `вчителька / учителька`, `лікарка` to recommended vocabulary_hints
    — mirrors locked wiki Декол. #4. Gender-flip demo words (`біль`, `степ`, `розпис`,
    `літопис`, `путь`) are intentionally NOT in vocabulary_hints — they live only
    in activity_hints[4] quiz items as diagnostic props (writer-note in Підсумок makes
    this explicit).'
  - 'Added two grammar items: (a) diagnostic principle + five demo pairs; (b) feminitive
    as primary form. Each mapped to new objectives.'
  - Added fifth activity_hint (gender-flip quiz, 5 enumerated items one-to-one with
    wiki Типові помилки L2 five rows) — satisfies rubric AC-3 drift check.
  - 'Added writer-note in section Підсумок: five indivisible chunks (`мій стіл` etc.);
    gender-flip treated as short diagnostic mini-drill mirroring wiki; feminitive-first
    rule for female professions.'
  - Added wiki back-reference to references list.
  - 'Post-Codex-adversarial-review tightening: (a) wiki Типові помилки L2 table shrunk
    9 → 5 rows (addresses Goroh нестандартне-form nuance for `ярмарка` and rubric
    AC-3 compliance); (b) objective 5 rephrased from "не переносити рід з російської"
    → positive-framing "застосовувати український тест … зокрема там, де інтуїція
    з іншої мови могла б дати неправильну відповідь" (reduces D3 rubric-cap risk);
    (c) grammar item 4 similarly rephrased; (d) `кір` removed from wiki Exercise 5
    (off-scope A1) — replaced with `розпис`; (e) `ярмарок` dropped from both wiki
    table and plan/wiki exercises; (f) Anglicism `Мірор` → `Дзеркалить` fixed.'
  date: '2026-04-23'
  version: 1.2.0
connects_to:
- a1-009 (Яке воно?)
content_outline:
- points:
  - 'Діалог 1 — Відеодзвінок із демонстрацією кімнати: — Привіт! Дивись, це моя кімната.
    — Класно! У тебе є стіл? — Так, у мене є стіл і ліжко. Рід виникає природно через
    словосполучення мій стіл, моя кімната, моє ліжко.'
  - Діалог 2 — Що у твоїй сумці? — Що у тебе є? — У мене є книга, телефон і фото.
    — А у мене є ручка і зошит.
  section: Діалоги
  words: 300
- points:
  - 'Пономарова, 3 клас, с. 86: Українські іменники мають рід. Тест: чи можете ви
    замінити іменник на він, вона або воно? Чоловічий рід: стіл — він. Можна додати:
    мій стіл. Жіночий рід: книга — вона. Можна додати: моя книга. Середній рід: вікно
    — воно. Можна додати: моє вікно.'
  - 'Вашуленко, 3 клас, с. 112 — закінчення за родами: Чоловічий: зазвичай закінчується
    на приголосний — стіл, телефон, зошит. Жіночий: зазвичай закінчується на -а або
    -я — книга, лампа, кімната, ручка. Середній: зазвичай закінчується на -о або -е
    — вікно, ліжко, крісло, місто. Це охоплює ~90% іменників. Винятки (наприклад,
    слова на -ь) вивчатимуться пізніше.'
  section: Він, вона, воно
  words: 300
- points:
  - 'Лексика кімнати, згрупована за родами: Чоловічий: стіл, стілець, телефон, комп''ютер,
    зошит, ключ. Жіночий: книга, лампа, сумка, ручка, кімната, стіна. Середній: вікно,
    ліжко, крісло, дзеркало, фото.'
  - 'Поширення конструкції "У мене є" з модуля модуль №6 (родина) на предмети: У мене
    є стіл. У мене є книга. У мене є вікно. Та сама модель, нова лексика.'
  section: Предмети навколо
  words: 300
- points:
  - 'Визначення роду в 3 кроки: 1. Скажіть він/вона/воно з іменником — що підходить?
    2. Перевірте закінчення — приголосний? -а/-я? -о/-е? 3. Використовуйте правильний
    присвійний займенник — мій/моя/моє. Самоперевірка: Якого роду слово "стіл"? Якого
    роду слово "книга"? А як щодо "вікно"? Скажіть українською, що у вас є стілець.'
  - 'УВАГА до автора: (а) на A1 подавати `мій стіл / моя ручка / моє вікно / велике
    яблуко / синє море` як неподільні чанки — НЕ пояснювати повну парадигму відмінювання
    прикметників, тверду/м''яку групу, узгодження у множині чи відмінювання присвійних
    займенників. (б) Діагностична gender-flip міні-вправа (activity_hints[4], 5 пунктів)
    — короткий фінальний дрил на 5 хвилин, що дзеркалить п''ять рядків wiki «Типові
    помилки L2». НЕ робити з неї окрему повноцінну лексичну тему: слова `біль`, `степ`,
    `розпис`, `літопис`, `путь` — діагностичні опори, не module vocab. (в) Для професій
    (`вчителька`, `лікарка`) використовувати фемінітив як основну форму, коли мова
    про жінку, — не «Вона — лікар».'
  section: Підсумок
  words: 300
dialogue_situations:
- motivation: Займенники він/вона/воно з іменниками, що позначають кімнату та предмети
    побуту, такі як стіл, книга, вікно, лампа, ліжко, телефон, а також кілька знайомих
    живих істот, наприклад, кіт
  setting: 'Вдома або під час відеодзвінка з демонстрацією кімнати. Учні вказують
    на повсякденні предмети та вживають із ними слова він/вона/воно: стіл, книга,
    вікно, лампа, ліжко, телефон, а також кілька знайомих домашніх улюбленців чи речей,
    як-от кіт та дзеркало.'
  speakers:
  - Марія
  - Оленка
focus: grammar
grammar:
- 'Рід іменників: чоловічий (він, мій), жіночий (вона, моя), середній (воно, моє)'
- 'Визначення роду за закінченням: приголосний=ч, -а/-я=ж, -о/-е=с'
- Конструкція "У мене є", розширена на предмети (з теми родини у модулі №6)
- 'Діагностичний принцип: український рід визначає VESUM-парадигма + тест він/вона/воно.
  П''ять показових пар (`біль`, `степ`, `розпис`, `літопис`, `путь`) у wiki «Типові
  помилки L2» + quiz №5 в activity_hints.'
- 'Фемінітиви як основна форма назви професії для жінки: вчителька, лікарка (НЕ «Вона
  — вчитель»)'
level: A1
lifecycle: locked
module: a1-008
objectives:
- Визначати рід іменників за допомогою тесту він/вона/воно
- Розпізнавати рід за закінченнями слів (приголосний = ч, -а/-я = ж, -о/-е = с)
- Називати понад 20 поширених предметів із правильним родом
- Використовувати конструкцію "У мене є" з предметами (розширення теми родини з модуля
  модуль №6)
- Застосовувати український тест `він/вона/воно` до будь-якого іменника — зокрема
  там, де інтуїція з іншої мови могла б дати неправильну відповідь (діагностична міні-вправа
  з 5 пунктів; детальна таблиця у wiki «Типові помилки L2»)
- Використовувати фемінітив як основну форму професії для жінки (`вчителька`, `лікарка`)
pedagogy: PPP
phase: A1.2 [Мій світ]
prerequisites:
- a1-007 (Рубіж — Перший контакт)
references:
- notes: 'Тест на рід: він/мій, вона/моя, воно/моє.'
  title: Пономарова Grade 3, p.86
- notes: 'Таблиця закінчень за родами: приголосний, -а/-я, -о/-е.'
  title: Вашуленко Grade 3, p.112
- notes: Рід природно випливає з уже вивчених присвійних займенників.
  title: ULP Season 1, Episode 6 — Gender naturally through family
  url: https://www.ukrainianlessons.com/episode6/
- notes: Authoritative pedagogical brief — see the four-step sequence (Крок 1-4),
    the animate-masculine exceptions block (`тато`, `дядько`, `Микола`), the Словниковий
    мінімум table (VESUM-cited), the "Типові помилки L2" gender-flip table (9 rows,
    every pair evidenced by VESUM presence of the Ukrainian form + VESUM absence of
    the Russian counterpart), the feminitive decolonization point (#4), and Приклад
    5 (gender-flip drill). The writer-note block pinning `мій стіл` / `моя ручка`
    / `моє вікно` / `велике яблуко` / `синє море` as indivisible chunks is load-bearing
    — do NOT teach adjective declension, hard/soft group, or plural agreement at this
    level.
  title: 'Wiki: pedagogy/a1/things-have-gender (LOCKED 2026-04-23)'
register: розмовний
review_notes: 'Review-and-lock pass per docs/best-practices/wiki-plan-review-and-lock.md
  (rubric template from PR #1412 `at-the-cafe` + PR #1436 `who-am-i`). See PR body
  for the full plan-side findings (pragmatic / Russianism / calque / contradiction
  / references / wiki-alignment) and wiki/.reviews/pedagogy/a1/things-have-gender-review-LOCKED.md
  for the wiki-side report. Plan brought into alignment with the locked wiki: (1)
  gender-flip objective added (`біль` ч.р. / `степ` ч.р. as demo pairs); (2) feminitive
  pairs (`вчителька`, `лікарка`) added as recommended vocab to mirror wiki Декол.
  #4; (3) gender-flip drill added as new quiz activity_hint mirroring wiki "Типові
  помилки L2" table + Exercise 5; (4) chunk-guidance writer-note in content_outline
  (`мій стіл / моя ручка / моє вікно / велике яблуко / синє море` as indivisible chunks);
  (5) wiki back-reference added.'
reviewed_at: '2026-04-23T00:00:00Z'
reviewed_by: claude-opus-4-7-xhigh-things-have-gender
sequence: 8
slug: things-have-gender
subtitle: він, вона, воно — кожен іменник має рід
title: Речі мають рід
version: 1.2.0
vocabulary_hints:
  recommended:
  - зошит (notebook, m)
  - ручка (pen, f)
  - сумка (bag, f)
  - крісло (armchair, n)
  - дзеркало (mirror, n)
  - ключ (key, m)
  - фото (photo, n)
  - стіна (wall, f)
  - вчителька / учителька (teacher, f — feminitive, VESUM-verified; mirror of вчитель
    / учитель m)
  - лікарка (doctor, f — feminitive, VESUM-verified; mirror of лікар m)
  required:
  - стіл (table, m)
  - книга (book, f)
  - вікно (window, n)
  - кімната (room, f)
  - ліжко (bed, n)
  - стілець (chair, m)
  - лампа (lamp, f)
  - телефон (phone, m)
  - комп'ютер (computer, m)
  - він, вона, воно (he, she, it — gender test words)
word_target: 1200

```

## Generated Content

## lesson-1
## module.md

# Він, вона́ чи воно́?

У попере́дніх мо́дулях ви ви́вчили привіта́ння, знайо́мство та сім'ю́ — in previous modules you learned greetings, introductions, and family. У цьо́му уро́ці ми дослі́джуємо грамати́чний рід украї́нських іме́нників:
- **Визнача́ти рід іме́нників** — determine noun gender using **він / вона́ / воно́**;
- **Розпізнава́ти закі́нчення слів** — recognise basic noun endings (consonant, **-а / -я**, **-о / -е**);
- **Вжива́ти присві́йні слова́** — use **мій / моя́ / моє́** as a single phrase with each noun.

English has "he," "she," and "it." Ukrainian also has **він**, **вона́**,
and **воно́**, but Ukrainian uses them for every noun, including things in your
room. A table is **він**. A book is **вона́**. A window is **воно́**.

By the end, you can:

- ask whether a word is a person or a thing with **Хто це?** and **Що це?**;
- test common nouns with **він / вона́ / воно́**;
- use the easy ending signals: consonant = usually masculine, **-а / -я** =
  usually feminine, **-о / -е** = usually neuter;
- say simple room and bag lines with **У мене́ є...**;
- choose **мій / моя́ / моє́** as a whole phrase with a noun;
- use **вчи́телька** and **лі́карка** when the person is a woman;
- repair the most common A1 gender traps without comparing Ukrainian to any
  other language.

Keep the goal small. You are not learning a full adjective or case system.
You are learning to store a noun with its gender cue.

:::tip
Treat gender as part of the noun card. Do not ask, "Who owns it?" Ask, "What
phrase travels with this noun: **мій**, **моя́**, or **моє́**?"
:::

## Діало́ги

Послу́хайте та прочита́йте коро́тку розмо́ву — listen to and read the short conversation:

> **Марко́**: Приві́т! Диви́сь, це мій стіл.
> **Окса́на**: Кла́сно! А це що?
> **Марко́**: Це моє́ вікно́. А це — моя́ кни́га.
> **Окса́на**: До́бре. А хто це?
> **Марко́**: Це мій та́то.
> **Окса́на**: А хто це бі́ля та́та?
> **Марко́**: Це моя́ ма́ма і мій брат.

Продо́вження розмо́ви — the conversation continues:

> **Окса́на**: А де твоя́ сестра́?
> **Марко́**: Моя́ сестра́ там.
> **Окса́на**: А це твоє́ мі́сто?
> **Марко́**: Так, це моє́ мі́сто.
> **Окса́на**: А це хто?
> **Марко́**: А це — мій соба́ка.
> **Окса́на**: Він ду́же га́рний!

Розбі́р розмо́ви по́дано ни́жче — the breakdown of the conversation is given below:

| Украї́нська | English support |
| --- | --- |
| **Диви́сь, це мій стіл.** | Look, this is my table. |
| **Це моє́ вікно́. А це — моя́ кни́га.** | This is my window. And this is my book. |
| **Це мій та́то.** | This is my dad. |
| **А це — мій соба́ка.** | And this is my dog. |

<!-- INJECT_ACTIVITY: act-1 -->

### Пита́льні слова́

Start with the noun question.

| Question | Use it for | Examples |
| --- | --- | --- |
| **Хто це?** | a person or animal | **та́то**, **сестра́**, **кіт** |
| **Що це?** | a thing or place | **стіл**, **кни́га**, **вікно́** |

In family words, gender often feels familiar:

| Ukrainian | Gender test | My phrase |
| --- | --- | --- |
| **та́то** | **він** | **мій та́то** |
| **брат** | **він** | **мій брат** |
| **сестра́** | **вона́** | **моя́ сестра́** |
| **ма́ма** | **вона́** | **моя́ ма́ма** |

But things also have gender:

| Ukrainian | English | Gender test | My phrase |
| --- | --- | --- | --- |
| **стіл** | table | **він** | **мій стіл** |
| **кни́га** | book | **вона́** | **моя́ кни́га** |
| **вікно́** | window | **воно́** | **моє́ вікно́** |

<!-- INJECT_ACTIVITY: act-2 -->

Do not ask whether the speaker is a man or a woman. Ask what gender the
Ukrainian noun has. **Мій стіл** is the same if the owner is Olena, Marko, or
you.

## Він, вона́, воно́

The fastest A1 habit is the **він / вона́ / воно́** test. Endings help you guess
when the word is new.

| Signal | Usually | Examples |
| --- | --- | --- |
| consonant ending | **він**, **мій** | **стіл**, **телефо́н**, **зо́шит**, **ключ** |
| **-а / -я** | **вона́**, **моя́** | **кни́га**, **ла́мпа**, **кімна́та**, **ру́чка** |
| **-о / -е** | **воно́**, **моє́** | **вікно́**, **лі́жко**, **дзе́ркало**, **мо́ре** |

At A1, this covers the clear everyday words you need. Some nouns are not clear
from the ending. You have already seen one important pattern: **та́то** and
**ба́тько** are masculine because they name a male person. Later you will learn
more exceptions. Today you only need a safe beginner reaction: if a word does
not fit the easy pattern, learn it as a phrase.

<!-- INJECT_ACTIVITY: act-5 -->

:::tip
The ending rule is a first guess, not a debate. If this lesson gives you a safe
phrase such as **мій та́то** or **мій соба́ка**, store the whole phrase.
:::

One high-value exception is **соба́ка**. In Ukrainian, use **він** and
**мій соба́ка**. For father, keep the course words **та́то** and **ба́тько**.
Do not replace them with **па́па** in these A1 lines.

Keep these phrases whole:

| Phrase | Meaning |
| --- | --- |
| **мій стіл** | my table |
| **моя́ ру́чка** | my pen |
| **моє́ вікно́** | my window |
| **вели́ке я́блуко** | a big apple |
| **си́нє мо́ре** | a blue sea |

Those last two phrases preview the next module. Do not turn them into a full
adjective table yet.

<!-- INJECT_ACTIVITY: act-3 -->

### Підсу́мок уро́ку 1

Чудо́ва ро́бота! Ви вже впе́внено розрізня́єте три роди́ слів:

| Украї́нська | English support |
| --- | --- |
| **Ко́жен іме́нник ма́є рід: він, вона́ чи воно́.** | Every noun has a gender: he, she, or it. |
| **Закі́нчення слів підка́зують пра́вильний рід.** | Word endings hint at the correct gender. |
| **Запам'ято́вуйте сло́во ра́зом із мій, моя́, моє́.** | Remember each word together with my: **мій, моя́, моє́**. |

### Ва́ше мо́влення

Напиші́ть 2–3 коро́ткі рядки́ про ре́чі бі́ля вас:
1. **Це мій стіл.**
2. **Це моя́ кни́га.**
3. **Це моє́ вікно́.**


## activities.yaml

inline:
- id: act-1
  type: quiz
  title: Хто чи що?
  instruction: Choose the question or pronoun that fits the noun.
  items:
  - prompt: та́то
    options:
    - text: Хто це?
      correct: true
    - text: Що це?
      correct: false
    - text: Воно́?
      correct: false
    explanation: Та́то is a person word, so ask Хто це?
  - prompt: стіл
    options:
    - text: Що це?
      correct: true
    - text: Хто це?
      correct: false
    - text: Вона́?
      correct: false
    explanation: Стіл is a thing word, so ask Що це?
  - prompt: сестра́
    options:
    - text: вона́
      correct: true
    - text: він
      correct: false
    - text: воно́
      correct: false
    explanation: Сестра́ is feminine.
  - prompt: брат
    options:
    - text: він
      correct: true
    - text: вона́
      correct: false
    - text: воно́
      correct: false
    explanation: Брат is masculine.
  - prompt: кни́га
    options:
    - text: вона́
      correct: true
    - text: він
      correct: false
    - text: воно́
      correct: false
    explanation: Кни́га is feminine.
  - prompt: вікно́
    options:
    - text: воно́
      correct: true
    - text: вона́
      correct: false
    - text: він
      correct: false
    explanation: Вікно́ is neuter.
- id: act-2
  type: group-sort
  title: Сорту́й слова́ за ро́дом
  instruction: Sort each noun by its safest A1 gender phrase.
  groups:
  - label: він / мій
    items:
    - стіл
    - та́то
    - ба́тько
    - соба́ка
  - label: вона́ / моя́
    items:
    - кни́га
    - сестра́
    - ма́ма
  - label: воно́ / моє́
    items:
    - вікно́
    - мі́сто
- id: act-5
  type: quiz
  title: Закі́нчення підка́зує рід
  instruction: Choose the usual gender signal from the noun ending.
  items:
  - prompt: стіл закі́нчується на при́голосний.
    options:
    - text: він / мій
      correct: true
    - text: вона́ / моя́
      correct: false
    - text: воно́ / моє́
      correct: false
    explanation: A clear consonant ending is usually masculine.
  - prompt: брат закі́нчується на при́голосний.
    options:
    - text: він / мій
      correct: true
    - text: вона́ / моя́
      correct: false
    - text: воно́ / моє́
      correct: false
    explanation: Брат ends in a consonant and is masculine.
  - prompt: кни́га закі́нчується на -а.
    options:
    - text: вона́ / моя́
      correct: true
    - text: він / мій
      correct: false
    - text: воно́ / моє́
      correct: false
    explanation: A clear -а ending is usually feminine.
  - prompt: сестра́ закі́нчується на -а.
    options:
    - text: вона́ / моя́
      correct: true
    - text: він / мій
      correct: false
    - text: воно́ / моє́
      correct: false
    explanation: Сестра́ ends in -а and is feminine.
  - prompt: вікно́ закі́нчується на -о.
    options:
    - text: воно́ / моє́
      correct: true
    - text: він / мій
      correct: false
    - text: вона́ / моя́
      correct: false
    explanation: A clear -о ending is usually neuter.
  - prompt: мі́сто закі́нчується на -о.
    options:
    - text: воно́ / моє́
      correct: true
    - text: вона́ / моя́
      correct: false
    - text: він / мій
      correct: false
    explanation: Мі́сто ends in -о and is neuter.
- id: act-3
  type: quiz
  title: Він, вона́ чи воно́?
  instruction: Choose the Ukrainian gender-test word.
  items:
  - prompt: стіл
    options:
    - text: він
      correct: true
    - text: вона́
      correct: false
    - text: воно́
      correct: false
    explanation: Стіл ends in a consonant and is masculine.
  - prompt: кни́га
    options:
    - text: вона́
      correct: true
    - text: він
      correct: false
    - text: воно́
      correct: false
    explanation: Кни́га is feminine.
  - prompt: вікно́
    options:
    - text: воно́
      correct: true
    - text: він
      correct: false
    - text: вона́
      correct: false
    explanation: Вікно́ is neuter.
  - prompt: ба́тько
    options:
    - text: він
      correct: true
    - text: вона́
      correct: false
    - text: воно́
      correct: false
    explanation: Ба́тько is masculine because it names a male person.
  - prompt: сестра́
    options:
    - text: вона́
      correct: true
    - text: воно́
      correct: false
    - text: він
      correct: false
    explanation: Сестра́ is feminine.
  - prompt: мі́сто
    options:
    - text: воно́
      correct: true
    - text: вона́
      correct: false
    - text: він
      correct: false
    explanation: Мі́сто is neuter.
  - prompt: та́то
    options:
    - text: він
      correct: true
    - text: воно́
      correct: false
    - text: вона́
      correct: false
    explanation: Та́то is masculine because it names a male person.
  - prompt: Мико́ла
    options:
    - text: він
      correct: true
    - text: вона́
      correct: false
    - text: воно́
      correct: false
    explanation: Мико́ла is a masculine name.
workbook:
- type: group-sort
  title: Сорту́й за ро́дом
  instruction: Sort each noun by its A1 gender signal.
  groups:
  - label: він / мій
    items:
    - стіл
    - та́то
    - ба́тько
    - брат
  - label: вона́ / моя́
    items:
    - кни́га
    - сестра́
    - ма́ма
  - label: воно́ / моє́
    items:
    - вікно́
    - мі́сто
  id: act-w1
- id: act-101
  type: true-false
  title: Пра́вда чи ні?
  instruction: Ви́значте, чи пра́вильне тве́рдження про рід іме́нника.
  statements:
  - statement: «Стіл» — це іме́нник чолові́чого ро́ду (він).
    correct: true
  - statement: «Кни́га» — це іме́нник чолові́чого ро́ду (він).
    correct: false
  - statement: «Вікно́» — це іме́нник сере́днього ро́ду (воно́).
    correct: true
  - statement: «Та́то» — це іме́нник жіно́чого ро́ду (вона́).
    correct: false
  - statement: «Мі́сто» — це іме́нник сере́днього ро́ду (воно́).
    correct: true
  - statement: «Ба́тько» — це іме́нник чолові́чого ро́ду (він).
    correct: true
- id: act-102
  type: quiz
  title: Він, вона́ чи воно́?
  instruction: Ви́беріть прави́льний займе́нник для ко́жного іме́нника.
  items:
  - prompt: стіл
    options:
    - text: він
      correct: true
    - text: вона́
      correct: false
    - text: воно́
      correct: false
  - prompt: кни́га
    options:
    - text: вона́
      correct: true
    - text: він
      correct: false
    - text: воно́
      correct: false
  - prompt: вікно́
    options:
    - text: воно́
      correct: true
    - text: він
      correct: false
    - text: вона́
      correct: false
  - prompt: та́то
    options:
    - text: він
      correct: true
    - text: вона́
      correct: false
    - text: воно́
      correct: false
  - prompt: ма́ма
    options:
    - text: вона́
      correct: true
    - text: він
      correct: false
    - text: воно́
      correct: false
  - prompt: мі́сто
    options:
    - text: воно́
      correct: true
    - text: він
      correct: false
    - text: вона́
      correct: false
- id: act-103
  type: fill-in
  title: Вста́вте мій, моя́ чи моє́
  instruction: Ви́беріть прави́льний присві́йний займе́нник до ко́жного іме́нника.
  items:
  - sentence: Це ___ стіл.
    answer: мій
    options:
    - мій
    - моя́
    - моє́
  - sentence: Це ___ кни́га.
    answer: моя́
    options:
    - моя́
    - мій
    - моє́
  - sentence: Це ___ вікно́.
    answer: моє́
    options:
    - моє́
    - мій
    - моя́
  - sentence: Це ___ та́то.
    answer: мій
    options:
    - мій
    - моя́
    - моє́
  - sentence: Це ___ ма́ма.
    answer: моя́
    options:
    - моя́
    - мій
    - моє́
  - sentence: Це ___ мі́сто.
    answer: моє́
    options:
    - моє́
    - мій
    - моя́
- id: act-104
  type: unjumble
  title: Складі́ть ре́чення
  instruction: Розташу́йте слова́ у прави́льному поря́дку, щоб утвори́ти ре́чення.
  words:
  - words:
    - Це
    - мій
    - стіл
    answer: Це мій стіл.
  - words:
    - Це
    - моя́
    - кни́га
    answer: Це моя́ кни́га.
  - words:
    - Це
    - моє́
    - вікно́
    answer: Це моє́ вікно́.
  - words:
    - Ось
    - мій
    - та́то
    answer: Ось мій та́то.
  - words:
    - Ось
    - моя́
    - ма́ма
    answer: Ось моя́ ма́ма.
  - words:
    - Це
    - моє́
    - мі́сто
    answer: Це моє́ мі́сто.
- id: act-105
  type: translate
  bonus: true
  title: 'Бо́нус: перекладі́ть ре́чення'
  instruction: Перекладі́ть ре́чення з англі́йської мо́ви на украї́нську.
  items:
  - sentence: This is my table.
    answer: Це мій стіл.
  - sentence: This is my book.
    answer: Це моя́ кни́га.
  - sentence: This is my window.
    answer: Це моє́ вікно́.
  - sentence: My brother is here.
    answer: Мій брат тут.
  - sentence: My mother is there.
    answer: Моя́ ма́ма там.
  - sentence: This is my city.
    answer: Це моє́ мі́сто.


## vocabulary.yaml

- lemma: рід
  translation: grammatical gender
  pos: noun
  usage: Украї́нські іме́нники ма́ють рід.
- lemma: іме́нник
  translation: noun
  pos: noun
  usage: Стіл — це іме́нник.
- lemma: хто це?
  translation: who is this?
  pos: phrase
  usage: Хто це? Це та́то.
- lemma: що це?
  translation: what is this?
  pos: phrase
  usage: Що це? Це стіл.
- lemma: він
  translation: he / masculine gender-test word
  pos: pronoun
  usage: Стіл — він.
- lemma: вона́
  translation: she / feminine gender-test word
  pos: pronoun
  usage: Кни́га — вона́.
- lemma: воно́
  translation: it / neuter gender-test word
  pos: pronoun
  usage: Вікно́ — воно́.
- lemma: мій
  translation: my, masculine
  pos: pronoun
  usage: Це мій стіл.
- lemma: моя́
  translation: my, feminine
  pos: pronoun
  usage: Це моя́ кни́га.
- lemma: моє́
  translation: my, neuter
  pos: pronoun
  usage: Це моє́ вікно́.
- lemma: стіл
  translation: table
  pos: noun
  usage: У мене́ є стіл.
- lemma: кни́га
  translation: book
  pos: noun
  usage: Це моя́ кни́га.
- lemma: вікно́
  translation: window
  pos: noun
  usage: Моє́ вікно́ вели́ке.
- lemma: мі́сто
  translation: city
  pos: noun
  usage: Моє́ мі́сто вели́ке.
- lemma: та́то
  translation: dad
  pos: noun
  usage: Це мій та́то.
- lemma: ба́тько
  translation: father
  pos: noun
  usage: Це мій ба́тько.
- lemma: соба́ка
  translation: dog
  pos: noun
  usage: Це мій соба́ка.
- lemma: Мико́ла
  translation: Mykola
  pos: proper noun
  usage: Він Мико́ла.


## resources.yaml

- title: Пономарьова, 4 клас — с. 35 «Визначаю рід і число іменників»
  role: textbook
  chunk_id: 4-klas-ukrayinska-mova-ponomarova-2021-1_s0033
  source: 'Пономарьова К. І. Українська мова та читання: підруч. для 4 класу, ч. 1
    (2021), с. 35'
  notes: 'Таблиця родів іменників: чоловічий (він, мій), жіночий (вона, моя), середній
    (воно, моє).'
- title: Noun Genders in Ukrainian (Infographic)
  role: article
  url: https://www.ukrainianlessons.com/noun-genders-in-ukrainian/
  accessed: '2026-09-12'
  source: Ukrainian Lessons (джерело)
  notes: Infographic with noun-gender rules and clear everyday examples.


## lesson-2
## module.md

# Предме́ти навко́ло

У пе́ршому уро́ці ви навчи́лися перевіря́ти рід: стіл — він, кни́га — вона́, вікно́ — воно́. У цьо́му уро́ці ми перехо́димо до предме́тів навко́ло нас:
- **Назива́ти ре́чі в кімна́ті та су́мці** — name everyday items in your room and bag;
- **Говори́ти про володі́ння** — say what you have with **У мене́ є...** and ask with **У тебе́ є...?**;
- **Замі́нювати іме́нники займе́нниками** — replace nouns with **він / вона́ / воно́** based on gender.

## Предме́ти навко́ло

Use **У мене́ є...** from the family module with objects. Read the Ukrainian
dialogue first. Use the support table after the dialogue to check meaning.

> **Марі́я**: Приві́т! Диви́сь, це моя́ кімна́та.
> **Оле́нка**: Кла́сно! У тебе́ є стіл?
> **Марі́я**: Так, у мене́ є стіл і лі́жко.
> **Оле́нка**: А це твоя́ ла́мпа?
> **Марі́я**: Так. Це моя́ ла́мпа. Вона́ тут.
> **Оле́нка**: А вікно́?
> **Марі́я**: Ось воно́. Моє́ вікно́ вели́ке.

Support after the dialogue:

| Украї́нська | English support |
| --- | --- |
| **Приві́т!** | Hi! |
| **Диви́сь, це моя́ кімна́та.** | Look, this is my room. |
| **У тебе́ є стіл?** | Do you have a table? |
| **У мене́ є стіл і лі́жко.** | I have a table and a bed. |
| **А це твоя́ ла́мпа?** | And is this your lamp? |
| **Вона́ тут.** | It is here. The word **ла́мпа** chooses **вона́**. |
| **Ось воно́.** | Here it is. The word **вікно́** chooses **воно́**. |
| **Моє́ вікно́ вели́ке.** | My window is big. |

Read the object lines again and notice the pronoun:

- **Де стіл? Він тут.**
- **Де кни́га? Вона́ тут.**
- **Де вікно́? Воно́ тут.**

English uses "it" for all three. Ukrainian does not. Let the Ukrainian noun
choose the pronoun.

<!-- INJECT_ACTIVITY: act-201 -->

<!-- INJECT_ACTIVITY: act-202 -->

## Що у твої́й су́мці?

Now move to a bag:

> **Оле́нка**: Що у тебе́ є?
> **Марі́я**: У мене́ є кни́га, телефо́н і фо́то.
> **Оле́нка**: А у мене́ є ру́чка і зо́шит.
> **Марі́я**: Де твоя́ ру́чка?
> **Оле́нка**: Ось вона́. А де твій телефо́н?
> **Марі́я**: Мій телефо́н тут, у су́мці.
> **Оле́нка**: Ду́же до́бре!

Support after the dialogue:

| Украї́нська | English support |
| --- | --- |
| **Що у тебе́ є?** | What do you have? |
| **У мене́ є кни́га, телефо́н і фо́то.** | I have a book, a phone, and a photo. |
| **А у мене́ є ру́чка і зо́шит.** | And I have a pen and a notebook. |

**Фо́то** is a useful beginner word. Store it as **воно́**: **моє́ фо́то**.

<!-- INJECT_ACTIVITY: act-203 -->

## Мій, моя́, моє́

The possessive word follows the noun (that is, its form follows the noun's grammatical gender, not word order).

| Noun | Gender | Say |
| --- | --- | --- |
| **стіл** | masculine | **мій стіл** |
| **телефо́н** | masculine | **мій телефо́н** |
| **кни́га** | feminine | **моя́ кни́га** |
| **ру́чка** | feminine | **моя́ ру́чка** |
| **вікно́** | neuter | **моє́ вікно́** |
| **лі́жко** | neuter | **моє́ лі́жко** |

This is the same habit from family:

- **мій брат**, **мій та́то**, **мій стіл**
- **моя́ сестра́**, **моя́ ма́ма**, **моя́ кни́га**
- **моє́ мі́сто**, **моє́ прі́звище**, **моє́ вікно́**

If you want to say "my room," use **моя́ кімна́та**. If you want to say "my
chair," use **мій стіле́ць**. If you want to say "my bed," use **моє́ лі́жко**.

:::tip
The owner does not decide the form. The noun decides it. Learn the phrase as a
pair: **стіл -> мій стіл**, **кни́га -> моя́ кни́га**, **вікно́ -> моє́ вікно́**.
:::

<!-- INJECT_ACTIVITY: act-4 -->

### Підсу́мок уро́ку 2

Чудо́во! Тепе́р ви вмі́єте опи́сувати свій про́стір украї́нською мо́вою:

| Украї́нська | English support |
| --- | --- |
| **Ми назива́ємо предме́ти в кімна́ті та су́мці.** | We name objects in the room and bag. |
| **Констру́кція «У мене́ є...» поє́днується з усіма́ рода́ми.** | The phrase "I have..." pairs with all genders. |
| **Присві́йне сло́во узго́джується з ро́дом іме́нника.** | The possessive word matches the noun's gender. |

### Ва́ше мо́влення

Напиші́ть 2–3 коро́ткі рядки́ про свою́ кімна́ту чи су́мку:
1. **Це моя́ кімна́та.**
2. **У мене́ є стіл і лі́жко.**
3. **Ось мій телефо́н і моя́ су́мка.**


## activities.yaml

inline:
- id: act-4
  type: fill-in
  title: Мій предме́т
  instruction: Choose мій, моя́, or моє́.
  items:
  - sentence: Це ___ стіл.
    answer: мій
    options:
    - мій
    - моя́
    - моє́
    explanation: Стіл is masculine.
  - sentence: Це ___ кни́га.
    answer: моя́
    options:
    - моя́
    - мій
    - моє́
    explanation: Кни́га is feminine.
  - sentence: Це ___ вікно́.
    answer: моє́
    options:
    - моє́
    - мій
    - моя́
    explanation: Вікно́ is neuter.
  - sentence: Це ___ кімна́та.
    answer: моя́
    options:
    - моя́
    - мій
    - моє́
    explanation: Кімна́та is feminine.
  - sentence: Це ___ лі́жко.
    answer: моє́
    options:
    - моє́
    - моя́
    - мій
    explanation: Лі́жко is neuter.
  - sentence: Це ___ телефо́н.
    answer: мій
    options:
    - мій
    - моя́
    - моє́
    explanation: Телефо́н is masculine.
  - sentence: Це ___ ру́чка.
    answer: моя́
    options:
    - моя́
    - мій
    - моє́
    explanation: Ру́чка is feminine.
  - sentence: Це ___ фо́то.
    answer: моє́
    options:
    - моє́
    - моя́
    - мій
    explanation: Фо́то is neuter in this lesson.
- id: act-201
  type: quiz
  title: Рід рече́й навко́ло
  instruction: Обері́ть прави́льний займе́нник (він, вона́ чи воно́) для ко́жного
    предме́та.
  items:
  - prompt: стіле́ць
    options:
    - text: він
      correct: true
    - text: вона́
      correct: false
    - text: воно́
      correct: false
  - prompt: ла́мпа
    options:
    - text: вона́
      correct: true
    - text: він
      correct: false
    - text: воно́
      correct: false
  - prompt: лі́жко
    options:
    - text: воно́
      correct: true
    - text: вона́
      correct: false
    - text: він
      correct: false
  - prompt: телефо́н
    options:
    - text: він
      correct: true
    - text: вона́
      correct: false
    - text: воно́
      correct: false
  - prompt: су́мка
    options:
    - text: вона́
      correct: true
    - text: він
      correct: false
    - text: воно́
      correct: false
  - prompt: дзе́ркало
    options:
    - text: воно́
      correct: true
    - text: він
      correct: false
    - text: вона́
      correct: false
- id: act-202
  type: observe
  title: Порівня́йте предме́ти та рід
  instruction: Зверні́ть ува́гу на поєдна́ння іме́нника та присві́йного займе́нника.
  pairs:
  - left: стіле́ць (при́голосний)
    right: мій стіле́ць (він)
  - left: су́мка (закі́нчення -а)
    right: моя́ су́мка (вона́)
  - left: лі́жко (закі́нчення -о)
    right: моє́ лі́жко (воно́)
  - left: телефо́н (при́голосний)
    right: мій телефо́н (він)
  - left: ла́мпа (закі́нчення -а)
    right: моя́ ла́мпа (вона́)
  - left: дзе́ркало (закі́нчення -о)
    right: моє́ дзе́ркало (воно́)
- id: act-203
  type: true-false
  title: 'Пра́вда чи ні: ре́чі в кімна́ті й су́мці'
  instruction: Ви́значте, чи пра́вильно вка́зано рід предме́та.
  statements:
  - statement: Сло́во «стіл» — це він.
    correct: true
  - statement: Сло́во «ла́мпа» — це воно́.
    correct: false
  - statement: Сло́во «лі́жко» — це воно́.
    correct: true
  - statement: Сло́во «су́мка» — це вона́.
    correct: true
  - statement: Сло́во «телефо́н» — це вона́.
    correct: false
  - statement: Сло́во «дзе́ркало» — це воно́.
    correct: true
workbook:
- id: act-w2
  type: match-up
  title: Слова́ для кімна́ти й су́мки
  instruction: Match each Ukrainian noun with its English cue.
  pairs:
  - left: стіл
    right: table
  - left: кни́га
    right: book
  - left: вікно́
    right: window
  - left: кімна́та
    right: room
  - left: лі́жко
    right: bed
  - left: телефо́н
    right: phone
  - left: ру́чка
    right: pen
  - left: зо́шит
    right: notebook
- id: act-w3
  type: fill-in
  title: У мене́ є предме́ти
  instruction: Complete the object sentence.
  items:
  - sentence: ___ мене́ є стіл.
    answer: У
    options:
    - У
    - Це
    - Хто
    explanation: У мене́ є... is the I-have phrase.
  - sentence: У мене́ ___ кни́га.
    answer: є
    options:
    - є
    - зва́ти
    - моя́
    explanation: У мене́ є... stays as one phrase.
  - sentence: У ___ є телефо́н?
    answer: тебе́
    options:
    - тебе́
    - мене́
    - мій
    explanation: У тебе́ є...? asks one familiar person.
  - sentence: У мене́ є ___.
    answer: вікно́
    options:
    - вікно́
    - він
    - моя́
    explanation: Вікно́ is an object noun after У мене́ є.
  - sentence: Де стіл? ___ тут.
    answer: Він
    options:
    - Він
    - Вона́
    - Воно́
    explanation: Стіл is masculine, so use він.
  - sentence: Де кни́га? ___ тут.
    answer: Вона́
    options:
    - Вона́
    - Він
    - Воно́
    explanation: Кни́га is feminine, so use вона́.
  - sentence: Де вікно́? ___ там.
    answer: Воно́
    options:
    - Воно́
    - Вона́
    - Він
    explanation: Вікно́ is neuter, so use воно́.
- id: act-204
  type: group-sort
  title: Сорту́й ре́чі в кімна́ті й су́мці
  instruction: 'Розподілі́ть предме́ти за ро́дом: він, вона́ чи воно́.'
  groups:
  - label: він / мій
    items:
    - стіле́ць
    - телефо́н
    - комп'ю́тер
    - ключ
    - зо́шит
  - label: вона́ / моя́
    items:
    - кімна́та
    - ла́мпа
    - су́мка
    - ру́чка
    - стіна́
  - label: воно́ / моє́
    items:
    - лі́жко
    - крі́сло
    - дзе́ркало
    - фо́то
- id: act-205
  type: unjumble
  title: Складі́ть ре́чення з «У мене́ є»
  instruction: Складі́ть слова́ у прави́льному поря́дку.
  words:
  - words:
    - У
    - мене́
    - є
    - стіл
    answer: У мене́ є стіл.
  - words:
    - У
    - тебе́
    - є
    - ла́мпа
    answer: У тебе́ є ла́мпа?
  - words:
    - У
    - мене́
    - є
    - су́мка
    answer: У мене́ є су́мка.
  - words:
    - У
    - тебе́
    - є
    - телефо́н
    answer: У тебе́ є телефо́н?
  - words:
    - У
    - мене́
    - є
    - лі́жко
    answer: У мене́ є лі́жко.
  - words:
    - У
    - тебе́
    - є
    - зо́шит
    answer: У тебе́ є зо́шит?
- id: act-206
  type: odd-one-out
  title: За́йве сло́во за ро́дом
  instruction: Знайді́ть одне́ сло́во, яке́ відрізня́ється за грамати́чним ро́дом.
  items:
  - words:
    - стіл
    - телефо́н
    - зо́шит
    - кни́га
    answer: кни́га
    explanation: Кни́га — жіно́чий рід, і́нші — чолові́чий.
  - words:
    - ла́мпа
    - су́мка
    - ру́чка
    - лі́жко
    answer: лі́жко
    explanation: Лі́жко — сере́дній рід, і́нші — жіно́чий.
  - words:
    - вікно́
    - дзе́ркало
    - крі́сло
    - стіле́ць
    answer: стіле́ць
    explanation: Стіле́ць — чолові́чий рід, і́нші — сере́дній.
  - words:
    - ключ
    - комп'ю́тер
    - стіл
    - стіна́
    answer: стіна́
    explanation: Стіна́ — жіно́чий рід, і́нші — чолові́чий.
  - words:
    - кімна́та
    - стіна́
    - су́мка
    - фо́то
    answer: фо́то
    explanation: Фо́то — сере́дній рід, і́нші — жіно́чий.
  - words:
    - лі́жко
    - вікно́
    - фо́то
    - зо́шит
    answer: зо́шит
    explanation: Зо́шит — чолові́чий рід, і́нші — сере́дній.
- id: act-207
  type: translate
  bonus: true
  title: 'Бо́нус: перекладі́ть про ре́чі'
  instruction: Перекладі́ть ре́чення на украї́нську мо́ву.
  items:
  - sentence: I have a table and a bed.
    answer: У мене́ є стіл і лі́жко.
  - sentence: Do you (informal) have a phone?
    answer: У тебе́ є телефо́н?
  - sentence: This is my bag.
    answer: Це моя́ су́мка.
  - sentence: Where is the mirror?
    answer: Де дзе́ркало?
  - sentence: Here is my armchair.
    answer: Ось моє́ крі́сло.
  - sentence: My room is here.
    answer: Моя́ кімна́та тут.


## vocabulary.yaml

- lemma: у мене́ є
  translation: I have
  pos: phrase
  usage: У мене́ є стіл.
- lemma: у тебе́ є
  translation: do you have / you have
  pos: phrase
  usage: У тебе́ є стіл?
- lemma: кімна́та
  translation: room
  pos: noun
  usage: Це моя́ кімна́та.
- lemma: лі́жко
  translation: bed
  pos: noun
  usage: Це моє́ лі́жко.
- lemma: стіле́ць
  translation: chair
  pos: noun
  usage: Це мій стіле́ць.
- lemma: ла́мпа
  translation: lamp
  pos: noun
  usage: Це моя́ ла́мпа.
- lemma: телефо́н
  translation: phone
  pos: noun
  usage: Це мій телефо́н.
- lemma: комп'ю́тер
  translation: computer
  pos: noun
  usage: Це мій комп'ю́тер.
- lemma: зо́шит
  translation: notebook
  pos: noun
  usage: Це мій зо́шит.
- lemma: ру́чка
  translation: pen
  pos: noun
  usage: Це моя́ ру́чка.
- lemma: су́мка
  translation: bag
  pos: noun
  usage: Це моя́ су́мка.
- lemma: крі́сло
  translation: armchair
  pos: noun
  usage: Це моє́ крі́сло.
- lemma: дзе́ркало
  translation: mirror
  pos: noun
  usage: Це моє́ дзе́ркало.
- lemma: ключ
  translation: key
  pos: noun
  usage: Це мій ключ.
- lemma: фо́то
  translation: photo
  pos: noun
  usage: Це моє́ фо́то.
- lemma: стіна́
  translation: wall
  pos: noun
  usage: Це моя́ стіна́.


## resources.yaml

- title: Літвінова, 6 клас — с. 129 «§ 25. Рід іменників»
  role: textbook
  chunk_id: 6-klas-ukrmova-litvinova-2023_s0134
  source: 'Літвінова І. М. Українська мова: підруч. для 6 класу (2023), с. 129'
  notes: Три роди іменників на прикладах предметів і понять; форми однини.
- title: Авраменко, 6 клас — с. 83 «§ 43. Рід іменників»
  role: textbook
  chunk_id: 6-klas-ukrmova-avramenko-2023_s0084
  source: 'Авраменко О. Українська мова: підруч. для 6 класу (2023), с. 83'
  notes: Постійна ознака роду іменника; граматичний рід речей (стіл — він).


## lesson-3
## module.md

# Профе́сії, па́стки й самопереві́рка

У пе́рших двох уро́ках ви опанува́ли рід предме́тів у кімна́ті та су́мці. Цей уро́к підсумо́вує мо́дуль і додає́ важли́ві дета́лі:
- **Вжива́ти фемініти́ви профе́сій** — use feminine profession forms (**вчи́телька, лі́карка**);
- **Розпізнава́ти чолові́чі імена́ на -а/-о** — recognise masculine names and family words ending in **-а / -о** (**Мико́ла, та́то**);
- **Уника́ти типо́вих пасто́к ро́ду** — avoid common gender traps (**мій соба́ка** as course default).

## Підсу́мок

For people, choose the form that fits the person.

| Masculine | Feminine |
| --- | --- |
| **студе́нт** | **студе́нтка** |
| **вчи́тель / учи́тель** | **вчи́телька / учи́телька** |
| **лі́кар** | **лі́карка** |
| **акто́р** | **акто́рка** |
| **співа́к** | **співа́чка** |

Use the feminine profession as the normal form for a woman:

```text
Вона́ студе́нтка.
Вона́ вчи́телька.
Вона́ лі́карка.
```

| Украї́нська | English support |
| --- | --- |
| **Вона́ студе́нтка.** | She is a student. |
| **Вона́ вчи́телька.** | She is a teacher. |
| **Вона́ лі́карка.** | She is a doctor. |

For a man:

```text
Він студе́нт.
Він вчи́тель.
Він лі́кар.
```

| Украї́нська | English support |
| --- | --- |
| **Він студе́нт.** | He is a student. |
| **Він вчи́тель.** | He is a teacher. |
| **Він лі́кар.** | He is a doctor. |

Keep the earlier identity rule: **Я студе́нт. Я студе́нтка.** Do not force
**є** into that A1 sentence.

### Діало́г про профе́сії

Послу́хайте та прочита́йте розмо́ву про профе́сії та сім'ю́ — listen to and read the conversation about professions and family:

> **Марко́**: Окса́но, хто ти? Ти студе́нтка?
> **Окса́на**: Так, я студе́нтка. А хто ти?
> **Марко́**: Я теж студе́нт. А хто твоя́ сестра́?
> **Окса́на**: Моя́ сестра́ — вчи́телька.
> **Марко́**: Кла́сно! Вона́ до́бра вчи́телька.
> **Окса́на**: Так. А хто твій брат?
> **Марко́**: Мій брат — лі́кар.

Розмо́ва про сім'ю́ — conversation about family:

> **Окса́на**: Твій брат лі́кар? Чудо́во!
> **Марко́**: А хто твоя́ ма́ма? Вона́ теж лі́карка?
> **Окса́на**: Так, моя́ ма́ма — лі́карка.
> **Марко́**: А хто твій та́то?
> **Окса́на**: Мій та́то — співа́к. А твій дя́дько Мико́ла?
> **Марко́**: Мій дя́дько — акто́р.
> **Окса́на**: А йо́го сестра́ — акто́рка!

<!-- INJECT_ACTIVITY: act-9 -->

<!-- INJECT_ACTIVITY: act-301 -->

## Імена́, па́стки й самопереві́рка

Some male names end in **-а**, **-я**, or **-о**: **Мико́ла**, **Ілля́**,
**Павло́**. They are still **він** because they name men. Family words such as
**та́то**, **ба́тько**, and **дя́дько** are also masculine.

### Пильну́й па́стки

Most errors come from using English habits too directly or from trusting the
ending when the word is an exception.

| Trap | Say this |
| --- | --- |
| **мій кни́га** | **моя́ кни́га** |
| **мій ру́чка** | **моя́ ру́чка** |
| **Де стіл? Воно́ там.** | **Де стіл? Він там.** |
| **Це моя́ та́то.** | **Це мій та́то.** |
| **Вона́ Мико́ла.** | **Він Мико́ла.** |
| **Моя́ соба́ка га́рна.** | **Мій соба́ка га́рний.** |
| **Я є студе́нт.** | **Я студе́нт.** |
| **Моє́ ім'я́ є Джон.** | **Мене́ зва́ти Джон.** |

For **соба́ка**, just memorize the course phrase **мій соба́ка**. You do not need
a long exception list today.

The gender-flip mini-check uses five words that are not your active vocabulary:
**біль**, **степ**, **ро́зпис**, **літо́пис**, and **путь**. They are diagnostic
props. The point is simple: trust the Ukrainian gender test, not an instinct
from another language.

<!-- INJECT_ACTIVITY: act-302 -->

<!-- INJECT_ACTIVITY: act-303 -->

### Самопереві́рка

Cover the English support and say the Ukrainian aloud:

| Украї́нська | English support |
| --- | --- |
| **Це моя́ кімна́та.** | This is my room. |
| **У мене́ є стіл.** | I have a table. |
| **У мене́ є кни́га.** | I have a book. |
| **У мене́ є вікно́.** | I have a window. |
| **мій стіл** | my table |
| **моя́ ру́чка** | my pen |
| **моє́ лі́жко** | my bed |
| **Де стіл? Він тут.** | Where is the table? It is here. |
| **Де кни́га? Вона́ тут.** | Where is the book? It is here. |
| **Де вікно́? Воно́ тут.** | Where is the window? It is here. |

Тепе́р переві́рте профе́сії, чолові́чі імена́ та ви́нятки:

| Украї́нська | English support |
| --- | --- |
| **Він студе́нт. Вона́ студе́нтка.** | He is a student. She is a student. |
| **Він вчи́тель. Вона́ вчи́телька.** | He is a teacher. She is a teacher. |
| **Він лі́кар. Вона́ лі́карка.** | He is a doctor. She is a doctor. |
| **Він Мико́ла. Це мій та́то.** | He is Mykola. This is my dad. |
| **Це мій соба́ка.** | This is my dog (course default). |
| **Це мій дя́дько.** | This is my uncle. |

Then make three tiny room lines. Read the Ukrainian first, then check the
support.

```text
Це моя́ кімна́та.
У мене́ є стіл, кни́га і вікно́.
Мій стіл тут, моя́ кни́га тут, моє́ вікно́ там.
```

| Украї́нська | English support |
| --- | --- |
| **Це моя́ кімна́та.** | This is my room. |
| **У мене́ є стіл, кни́га і вікно́.** | I have a table, a book, and a window. |
| **Мій стіл тут, моя́ кни́га тут, моє́ вікно́ там.** | My table is here, my book is here, my window is there. |

Workbook practice will make the pattern automatic: sort nouns by gender, choose
**він / вона́ / воно́**, complete **мій / моя́ / моє́**, use **У мене́ є...**, and
repair the gender traps.

### Заве́ршення мо́дуля

| Украї́нська | English support |
| --- | --- |
| **Віта́ємо! Ви успі́шно заверши́ли мо́дуль 8 «Ре́чі ма́ють рід».** | Congratulations! You have successfully completed Module 8 "Things Have Gender." |
| **Тепе́р ви зна́єте рід іме́нників, закі́нчення слів та фемініти́ви.** | Now you know noun genders, word endings, and feminine profession forms. |
| **Ви упе́внено вжива́єте «мій / моя́ / моє́» та констру́кцію «У мене́ є...».** | You confidently use "my" forms and the construction "I have...". |
| **У насту́пному мо́дулі ви познайо́митеся з прикме́тниками.** | In the next module, you will discover descriptive adjectives. |

### Ва́ше мо́влення

Напиші́ть 2–3 коро́ткі рядки́ про себе́ та свій про́стір:
1. **Я студе́нт (або́: Я студе́нтка).**
2. **Це моя́ кімна́та.**
3. **У мене́ є стіл, кни́га і моє́ фо́то.**


## activities.yaml

inline:
- id: act-9
  type: quiz
  title: Фо́рми профе́сій
  instruction: Choose the natural profession form.
  items:
  - prompt: She is a teacher.
    options:
    - text: Вона́ вчи́телька.
      correct: true
    - text: Вона́ вчи́тель.
      correct: false
    - text: Воно́ вчи́телька.
      correct: false
    explanation: Use the feminine profession form for a woman.
  - prompt: She is a doctor.
    options:
    - text: Вона́ лі́карка.
      correct: true
    - text: Вона́ лі́кар.
      correct: false
    - text: Він лі́карка.
      correct: false
    explanation: Лі́карка is the feminine form.
  - prompt: He is a student.
    options:
    - text: Він студе́нт.
      correct: true
    - text: Він студе́нтка.
      correct: false
    - text: Вона́ студе́нт.
      correct: false
    explanation: Студе́нт is the masculine form.
  - prompt: She is an actor.
    options:
    - text: Вона́ акто́рка.
      correct: true
    - text: Вона́ акто́р.
      correct: false
    - text: Воно́ акто́рка.
      correct: false
    explanation: Акто́рка is the feminine profession form.
- id: act-301
  type: match-up
  title: Чолові́чі та жіно́чі фо́рми профе́сій
  instruction: 'З''єдна́йте чолові́чу фо́рму профе́сії з відпові́дним фемініти́вом
    (зберіга́йте початко́ву лі́теру: вчи́тель → вчи́телька, учи́тель → учи́телька).'
  pairs:
  - left: студе́нт
    right: студе́нтка
  - left: вчи́тель
    right: вчи́телька
  - left: учи́тель
    right: учи́телька
  - left: лі́кар
    right: лі́карка
  - left: акто́р
    right: акто́рка
  - left: співа́к
    right: співа́чка
- id: act-302
  type: fill-in
  title: Він чи вона́ для люде́й
  instruction: 'Вста́вте прави́льний займе́нник: він чи вона́.'
  items:
  - sentence: Мико́ла — чолові́к. ___ студе́нт.
    answer: Він
    options:
    - Він
    - Вона́
  - sentence: Окса́на — жі́нка. ___ лі́карка.
    answer: Вона́
    options:
    - Вона́
    - Він
  - sentence: Павло́ — вчи́тель. ___ тут.
    answer: Він
    options:
    - Він
    - Вона́
  - sentence: Марі́я — співа́чка. ___ там.
    answer: Вона́
    options:
    - Вона́
    - Він
  - sentence: Ілля́ — акто́р. ___ працю́є.
    answer: Він
    options:
    - Він
    - Вона́
  - sentence: Оле́на — вчи́телька. ___ працю́є.
    answer: Вона́
    options:
    - Вона́
    - Він
- id: act-303
  type: true-false
  title: 'Пра́вда чи ні: чолові́чі імена́ та ви́нятки'
  instruction: Ви́значте, чи прави́льне тве́рдження про рід слів.
  statements:
  - statement: Ім'я́ «Мико́ла» — це він.
    correct: true
  - statement: Ім'я́ «Павло́» — це воно́.
    correct: false
  - statement: Сло́во «дя́дько» — це він.
    correct: true
  - statement: Сло́во «соба́ка» в украї́нській мо́ві — це вона́.
    correct: false
  - statement: Для жі́нки-лі́каря вжива́ємо фо́рму «лі́карка».
    correct: true
  - statement: Сло́во «та́то» — це він.
    correct: true
workbook:
- type: error-correction
  title: Ви́прав па́стки ро́ду
  instruction: Choose the safer Ukrainian sentence.
  items:
  - sentence: Мій кни́га, мій ру́чка (якщо́ гово́рить чолові́к).
    error: Мій кни́га, мій ру́чка (якщо́ гово́рить чолові́к).
    correction: Моя́ кни́га, моя́ ру́чка.
    options:
    - Моя́ кни́га, моя́ ру́чка.
    - Мій кни́га, мій ру́чка.
    explanation: The possessive follows the nouns кни́га and ру́чка, not the speaker.
  - sentence: Мій кни́га тут.
    error: Мій кни́га тут.
    correction: Моя́ кни́га тут.
    options:
    - Моя́ кни́га тут.
    - Мій кни́га тут.
    explanation: Кни́га is feminine, so use моя́.
  - sentence: Мій ру́чка там.
    error: Мій ру́чка там.
    correction: Моя́ ру́чка там.
    options:
    - Моя́ ру́чка там.
    - Мій ру́чка там.
    explanation: Ру́чка is feminine, so use моя́.
  - sentence: Де стіл? — Воно́ там. (Where is the table? — It is there.)
    error: Де стіл? — Воно́ там. (Where is the table? — It is there.)
    correction: Де стіл? — Він там.
    options:
    - Де стіл? — Він там.
    - Де стіл? — Воно́ там.
    explanation: Стіл is masculine, so the pronoun is він.
  - sentence: Це моя́ та́то.
    error: Це моя́ та́то.
    correction: Це мій та́то.
    options:
    - Це мій та́то.
    - Це моя́ та́то.
    explanation: Та́то is masculine.
  - sentence: Вона́ Мико́ла.
    error: Вона́ Мико́ла.
    correction: Він Мико́ла.
    options:
    - Він Мико́ла.
    - Вона́ Мико́ла.
    explanation: Мико́ла is a masculine name.
  - sentence: Моя́ соба́ка ду́же га́рна.
    error: Моя́ соба́ка ду́же га́рна.
    correction: Мій соба́ка ду́же га́рний.
    options:
    - Мій соба́ка ду́же га́рний.
    - Моя́ соба́ка ду́же га́рна.
    explanation: Соба́ка is masculine in Ukrainian; memorize мій соба́ка.
  - sentence: Я є студе́нт.
    error: Я є студе́нт.
    correction: Я студе́нт.
    options:
    - Я студе́нт.
    - Я є студе́нт.
    explanation: Present identity normally omits є.
  - sentence: Моє́ ім'я́ є Джон.
    error: Моє́ ім'я́ є Джон.
    correction: Мене́ зва́ти Джон.
    options:
    - Мене́ зва́ти Джон.
    - Моє́ ім'я́ є Джон.
    explanation: Мене́ зва́ти... is the safe name phrase.
  id: act-w4
- type: quiz
  title: Переві́рка ро́ду
  instruction: Choose the Ukrainian gender-test word. These are diagnostic props,
    not new active vocabulary.
  items:
  - prompt: Яки́й у мене́ си́льний біль у плечі́!
    options:
    - text: він
      correct: true
    - text: вона́
      correct: false
    - text: воно́
      correct: false
    explanation: Біль is masculine in Ukrainian.
  - prompt: Украї́нський степ широ́кий і ві́тряний.
    options:
    - text: він
      correct: true
    - text: вона́
      correct: false
    - text: воно́
      correct: false
    explanation: Степ is masculine in Ukrainian.
  - prompt: Цей ро́зпис на стіні́ — робо́та украї́нського худо́жника.
    options:
    - text: він
      correct: true
    - text: вона́
      correct: false
    - text: воно́
      correct: false
    explanation: Ро́зпис is masculine in Ukrainian.
  - prompt: Да́вній літо́пис розповіда́є про Ки́ївську Русь.
    options:
    - text: він
      correct: true
    - text: вона́
      correct: false
    - text: воно́
      correct: false
    explanation: Літо́пис is masculine in Ukrainian.
  - prompt: 'Кни́жне / урочи́сте: у дале́ку путь.'
    options:
    - text: вона́
      correct: true
    - text: він
      correct: false
    - text: воно́
      correct: false
    explanation: Путь is feminine in this diagnostic expression.
  id: act-w5
- id: act-304
  type: group-sort
  title: 'Розподілі́ть слова́: він чи вона́'
  instruction: 'Розподілі́ть профе́сії та імена́ за ро́дом: він чи вона́.'
  groups:
  - label: він (чолові́чий рід)
    items:
    - студе́нт
    - вчи́тель
    - лі́кар
    - Мико́ла
    - Ілля́
    - дя́дько
  - label: вона́ (жіно́чий рід)
    items:
    - студе́нтка
    - вчи́телька
    - лі́карка
    - акто́рка
    - співа́чка
    - Окса́на
- id: act-305
  type: unjumble
  title: Складі́ть ре́чення з профе́сіями
  instruction: Розташу́йте слова́, щоб утвори́ти прави́льне ре́чення.
  words:
  - words:
    - Вона́
    - моя́
    - вчи́телька
    answer: Вона́ моя́ вчи́телька.
  - words:
    - Він
    - мій
    - лі́кар
    answer: Він мій лі́кар.
  - words:
    - Це
    - мій
    - соба́ка
    answer: Це мій соба́ка.
  - words:
    - Це
    - мій
    - дя́дько
    answer: Це мій дя́дько.
  - words:
    - Він
    - акто́р
    - а
    - вона́
    - акто́рка
    answer: Він акто́р, а вона́ акто́рка.
  - words:
    - Мене́
    - зва́ти
    - Мико́ла
    answer: Мене́ зва́ти Мико́ла.
- id: act-306
  type: odd-one-out
  title: За́йве сло́во за ро́дом
  instruction: Знайді́ть одне́ за́йве сло́во за грамати́чним ро́дом.
  items:
  - words:
    - вчи́телька
    - лі́карка
    - студе́нтка
    - студе́нт
    answer: студе́нт
    explanation: Студе́нт — чолові́ча фо́рма, і́нші — жіно́чі.
  - words:
    - акто́р
    - співа́к
    - лі́кар
    - акто́рка
    answer: акто́рка
    explanation: Акто́рка — жіно́ча фо́рма, і́нші — чолові́чі.
  - words:
    - Мико́ла
    - Ілля́
    - Павло́
    - Окса́на
    answer: Окса́на
    explanation: Окса́на — жіно́че ім'я́, і́нші — чолові́чі.
  - words:
    - та́то
    - ба́тько
    - дя́дько
    - ма́ма
    answer: ма́ма
    explanation: Ма́ма — жіно́чий рід, і́нші — чолові́чий.
  - words:
    - стіл
    - телефо́н
    - зо́шит
    - кни́га
    answer: кни́га
    explanation: Кни́га — жіно́чий рід, і́нші — чолові́чий.
  - words:
    - вікно́
    - лі́жко
    - фо́то
    - ла́мпа
    answer: ла́мпа
    explanation: Ла́мпа — жіно́чий рід, і́нші — сере́дній.
- id: act-307
  type: translate
  bonus: true
  title: 'Бо́нус: перекладі́ть про люде́й і ре́чі'
  instruction: Перекладі́ть ре́чення з англі́йської мо́ви на украї́нську.
  items:
  - sentence: She is a teacher (vchytelka).
    answer: Вона́ вчи́телька.
  - sentence: He is a doctor.
    answer: Він лі́кар.
  - sentence: My dog is handsome.
    answer: Мій соба́ка га́рний.
  - sentence: This is my uncle.
    answer: Це мій дя́дько.
  - sentence: My name is John.
    answer: Мене́ зва́ти Джон.
  - sentence: She is a student.
    answer: Вона́ студе́нтка.


## vocabulary.yaml

- lemma: дя́дько
  translation: uncle
  pos: noun
  usage: Це мій дя́дько.
- lemma: студе́нт
  translation: male student
  pos: noun
  usage: Він студе́нт.
- lemma: студе́нтка
  translation: female student
  pos: noun
  usage: Вона́ студе́нтка.
- lemma: вчи́тель
  translation: male teacher
  pos: noun
  usage: Він вчи́тель.
- lemma: вчи́телька
  translation: female teacher
  pos: noun
  usage: Вона́ вчи́телька.
- lemma: учи́телька
  translation: female teacher
  pos: noun
  usage: Вона́ учи́телька.
- lemma: лі́кар
  translation: male doctor
  pos: noun
  usage: Він лі́кар.
- lemma: лі́карка
  translation: female doctor
  pos: noun
  usage: Вона́ лі́карка.
- lemma: акто́р
  translation: male actor
  pos: noun
  usage: Він акто́р.
- lemma: акто́рка
  translation: female actor
  pos: noun
  usage: Вона́ акто́рка.
- lemma: співа́к
  translation: male singer
  pos: noun
  usage: Він співа́к.
- lemma: співа́чка
  translation: female singer
  pos: noun
  usage: Вона́ співа́чка.
- lemma: Ілля́
  translation: Illia
  pos: proper noun
  usage: Він Ілля́.
- lemma: Павло́
  translation: Pavlo
  pos: proper noun
  usage: Він Павло́.


## resources.yaml

- title: Авраменко, 6 клас — с. 84 «Фемінітиви»
  role: textbook
  chunk_id: 6-klas-ukrmova-avramenko-2023_s0085
  source: 'Авраменко О. Українська мова: підруч. для 6 класу (2023), с. 84'
  notes: 'Творення фемінітивів суфіксом -к(а): учителька, співачка, лікарка.'
- title: Літвінова, 6 клас — с. 130 «Вправа 264. Рід іменників»
  role: textbook
  chunk_id: 6-klas-ukrmova-litvinova-2023_s0135
  source: 'Літвінова І. М. Українська мова: підруч. для 6 класу (2023), с. 130'
  notes: 'Рід іменників-винятків: біль, собака, степ (чоловічий рід), путь (жіночий
    рід).'


## Task

Review the assigned dimension `tone` and return the required JSON object now.
No preamble, no markdown, no questions.
