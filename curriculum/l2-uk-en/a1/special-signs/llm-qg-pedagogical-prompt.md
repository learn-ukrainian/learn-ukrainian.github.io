{"independent_effort": "medium", "independent_model": "gpt-6-astra", "independent_reviewer": "codex-tools", "self_reviewer": "agy-tools", "writer": {"effort": "high", "model": "gemini-3.8-flash-high", "writer": "agy-tools"}}
V7 UPGRADE review of the complete module across all lessons. Review the published lesson unit, not a fresh module build. No wiki packet or plan rewrite applies. Assess preservation, lesson_split, coherent progression, first-use cumulative vocabulary, final module closure (`Підсумок модуля — Module summary` on the last lesson, not Module completion), no named narrator, marked attributed quotations with Resources entries, no ```text learner examples, and side-by-side English support for added A1 Ukrainian passages of three or more sentences. SOURCES AUDIT: VESUM/`sources` is why the Ukrainian is trustworthy (gender, government, real examples — not Russian calques). This corpus trains a Ukrainian LLM and tests whether the sources tools actually get used. No tool calls = fail. Ungrounded morphology = fail. Judge the current dimension independently using exact quotes from these artifacts. Stress annotation follows review. Lesson map:
{"lessons": [{"n": 1, "title": "Апостроф", "sections": ["Йотовані голосні", "М'який знак", "Апостроф"], "minutes": 60, "word_target": 550, "activities": {"total": 10, "inline": [4, 6], "workbook": [6, 9]}, "unverified_stress": [], "unverified_lemmas": []}, {"n": 2, "title": "Перенос і письмо", "sections": ["Контраст і пастки", "Перенос і письмо"], "minutes": 60, "word_target": 550, "activities": {"total": 10, "inline": [4, 6], "workbook": [6, 9]}, "unverified_stress": [], "unverified_lemmas": []}, {"n": 3, "title": "Далі", "sections": ["Далі"], "minutes": 60, "word_target": 550, "activities": {"total": 10, "inline": [4, 6], "workbook": [6, 9]}, "unverified_stress": [], "unverified_lemmas": []}], "closes_module": 3, "provenance": [{"placement": "inline", "index": 0, "new_id": "act-1", "lesson": 1}, {"placement": "inline", "index": 1, "new_id": "act-2", "lesson": 1}, {"placement": "inline", "index": 2, "new_id": "act-3", "lesson": 1}, {"placement": "inline", "index": 3, "new_id": "act-4", "lesson": 2}, {"placement": "inline", "index": 4, "new_id": "act-5", "lesson": 2}, {"placement": "workbook", "index": 0, "new_id": "act-w1", "lesson": 1}, {"placement": "workbook", "index": 1, "new_id": "act-w2", "lesson": 1}, {"placement": "workbook", "index": 2, "new_id": "act-w3", "lesson": 2}, {"placement": "workbook", "index": 3, "new_id": "act-w4", "lesson": 2}, {"placement": "workbook", "index": 4, "new_id": "act-w5", "lesson": 3}, {"placement": "workbook", "index": 5, "new_id": "act-w6", "lesson": 3}, {"placement": "workbook", "index": 6, "new_id": "act-w7", "lesson": 3}], "items_min_exempt": [{"id": "act-1", "reason": "3-item original activity preserved from baseline"}, {"id": "act-2", "reason": "5-item original activity preserved from baseline"}, {"id": "act-3", "reason": "4-item original activity preserved from baseline"}, {"id": "act-4", "reason": "4-item original activity preserved from baseline"}, {"id": "act-5", "reason": "4-item original activity preserved from baseline"}, {"id": "act-w2", "reason": "4-item original activity preserved from baseline"}, {"id": "act-w4", "reason": "4-item original activity preserved from baseline"}, {"id": "act-w5", "reason": "5-item original activity preserved from baseline"}, {"id": "act-w6", "reason": "3-item original activity preserved from baseline"}, {"id": "act-w7", "reason": "3-item original activity preserved from baseline"}], "proper_names": []}

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

Assigned dimension: pedagogical

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

For `pedagogical` specifically:

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
teach while applying the existing `pedagogical` rubric.

### Wiki Obligations Manifest

```json
{
  "slug": "special-signs",
  "wiki_path": "/home/ops/learn-ukrainian/.worktrees/builds/a1-special-signs-20260914-120045/wiki/pedagogy/a1/special-signs.md",
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
      "summary": "Use ✅ Правильна українська форма instead of ❌ Типова помилка L2: Чому виникає ця помилка та як її ефективно виправити методично"
    },
    {
      "id": "err-2",
      "obligation_id": "err-2",
      "category": "l2_errors",
      "summary": "Use Вимова «день» із м'яким, делікатним кінцевим [н'] instead of Вимова слова «день» як [ден] (з грубим, твердим англійським «н»): В англійській мові просто немає фонематичного протиставлення твердих і м'яких приголосних наприкінці слова []."
    },
    {
      "id": "err-3",
      "obligation_id": "err-3",
      "category": "l2_errors",
      "summary": "Use Читання «сім'я» з чітким, виразним звуком [й]: [сімйа] instead of Читання слова «сім'я» як «сімя» (зі злитим, м'яким [м']): Англомовні учні часто ігнорують апостроф, візуально сприймаючи його як пунктуаційну помилку, знак наголосу або декоративний елемент []."
    },
    {
      "id": "err-4",
      "obligation_id": "err-4",
      "category": "l2_errors",
      "summary": "Use Злита вимова «батько» як [бат'ко] instead of Вимова м'якого знака як окремого, повноцінного звуку [і] чи [й] у слові «батько» (виходить: батіко, батйко): Початківці наївно намагаються чесно озвучити кожну літеру алфавіту [S8]."
    },
    {
      "id": "err-5",
      "obligation_id": "err-5",
      "category": "l2_errors",
      "summary": "Use Плавний, але роздільний перехід від твердого приголосного до [й]: [пйат'] instead of Штучна пауза (різке гортанне зімкнення) на місці апострофа: [п'ят'] виголошується як [п — ят']: Англомовні мовці підсвідомо сприймають апостроф як прямий сигнал для різкої зупинки потоку повітря (glottal stop), подібно до того, як це відбувається в д…"
    },
    {
      "id": "err-6",
      "obligation_id": "err-6",
      "category": "l2_errors",
      "summary": "Use Нормативне написання «мільйон» instead of Написання апострофа замість м'якого знака у міжнародних словах типу «мільйон» (помилково: міл'йон): Учні логічно плутають функцію розділення й пом'якшення в словах іншомовного походження."
    }
  ],
  "phonetic_rules": [],
  "decolonization_bans": [
    {
      "id": "ban-1",
      "obligation_id": "ban-1",
      "category": "decolonization_bans",
      "summary": "При створенні навчального контенту з української мови категорично і беззаперечно важливо уникати будь-яких прямих чи прихованих аналогій із російською мовою."
    },
    {
      "id": "ban-2",
      "obligation_id": "ban-2",
      "category": "decolonization_bans",
      "summary": "По-перше, абсолютно неприпустимо та заборонено пояснювати український апостроф як «еквівалент російського твердого знака (ъ)»."
    },
    {
      "id": "ban-3",
      "obligation_id": "ban-3",
      "category": "decolonization_bans",
      "summary": "По-друге, не слід використовувати сумнівні фонетичні кальки або наводити російські приклади для ілюстрації процесу пом'якшення."
    },
    {
      "id": "ban-4",
      "obligation_id": "ban-4",
      "category": "decolonization_bans",
      "summary": "По-третє, під час свідомого вибору лексики для ілюстрації граматичних правил завжди віддавайте перевагу питомо українським словам, реаліям та іменам."
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
  location_hint: §Йотовані голосні як передумова
  subtype: substance_required
  treatment_template:
    shape: module.md prose absent of any phrasing matching manifest_payload.rule (negative obligation: absence-of-pattern)
- obligation_id: ban-3  (obligation_type: decolonization_ban)
  artifact: module.md
  location_hint: §Йотовані голосні як передумова
  subtype: absence_required
  treatment_template:
    shape: module.md prose absent of any phrasing matching manifest_payload.rule (negative obligation: absence-of-pattern)
- obligation_id: ban-4  (obligation_type: decolonization_ban)
  artifact: module.md
  location_hint: §Перенос і підсумок
  subtype: substance_required
  treatment_template:
    shape: module.md prose absent of any phrasing matching manifest_payload.rule (negative obligation: absence-of-pattern)
- obligation_id: err-1  (obligation_type: l2_error)
  artifact: activities.yaml
  location_hint: activities.yaml
  treatment_template:
    activity_stub: {"items": [], "sentence": "", "type": "error-correction"}
    expected_correction_value: ✅ Правильна українська форма
    expected_error_value: ❌ Типова помилка L2
    shape: activities.yaml entry with fields {sentence, error, correction}
- obligation_id: err-2  (obligation_type: l2_error)
  artifact: activities.yaml
  location_hint: activities.yaml
  treatment_template:
    activity_stub: {"items": [], "sentence": "", "type": "error-correction"}
    expected_correction_value: Вимова «день» із м'яким, делікатним кінцевим [н']
    expected_error_value: Вимова слова «день» як [ден] (з грубим, твердим англійським «н»)
    shape: activities.yaml entry with fields {sentence, error, correction}
- obligation_id: err-3  (obligation_type: l2_error)
  artifact: activities.yaml
  location_hint: activities.yaml
  treatment_template:
    activity_stub: {"items": [], "sentence": "", "type": "error-correction"}
    expected_correction_value: Читання «сім'я» з чітким, виразним звуком [й]: [сімйа]
    expected_error_value: Читання слова «сім'я» як «сімя» (зі злитим, м'яким [м'])
    shape: activities.yaml entry with fields {sentence, error, correction}
- obligation_id: err-4  (obligation_type: l2_error)
  artifact: activities.yaml
  location_hint: activities.yaml
  treatment_template:
    activity_stub: {"items": [], "sentence": "", "type": "error-correction"}
    expected_correction_value: Злита вимова «батько» як [бат'ко]
    expected_error_value: Вимова м'якого знака як окремого, повноцінного звуку [і] чи [й] у слові «батько» (виходить: батіко, батйко)
    shape: activities.yaml entry with fields {sentence, error, correction}
- obligation_id: err-5  (obligation_type: l2_error)
  artifact: activities.yaml
  location_hint: activities.yaml
  treatment_template:
    activity_stub: {"items": [], "sentence": "", "type": "error-correction"}
    expected_correction_value: Плавний, але роздільний перехід від твердого приголосного до [й]: [пйат']
    expected_error_value: Штучна пауза (різке гортанне зімкнення) на місці апострофа: [п'ят'] виголошується як [п — ят']
    shape: activities.yaml entry with fields {sentence, error, correction}
- obligation_id: err-6  (obligation_type: l2_error)
  artifact: activities.yaml
  location_hint: activities.yaml
  treatment_template:
    activity_stub: {"items": [], "sentence": "", "type": "error-correction"}
    expected_correction_value: Нормативне написання «мільйон»
    expected_error_value: Написання апострофа замість м'якого знака у міжнародних словах типу «мільйон» (помилково: міл'йон)
    shape: activities.yaml entry with fields {sentence, error, correction}
- obligation_id: step-1  (obligation_type: sequence_step)
  artifact: module.md
  location_hint: §М'який знак наприкінці слова.
  treatment_template:
    required_claim: Крок 1. М'який знак наприкінці слова. Навчання завжди починається з фінальної позиції. Це зумовлено тим, що тут функція м'якого знака є найбільш чистою та очевидною: він просто і беззаперечно пом'якшує попередній приголосний звук . Учень вчиться артикулювати та розрізняти твердий і м'який кінець слова, що є критично важливим для розуміння української морфології (наприклад, утворення відмінків). Вводяться базові, високочастотні іменники: «день», «осінь», «сіль» . На цьому етапі варто детально пояснити анатомію мовного апарату: м'який знак не має власного звуку, а є графічною інструкцією для язика притиснутися до піднебіння під час вимови попереднього приголосного .
    shape: module.md section heading or in-prose step marker matching manifest_payload.heading at the position implied by manifest_payload.step_num
- obligation_id: step-2  (obligation_type: sequence_step)
  artifact: module.md
  location_hint: §М'який знак усередині слова перед твердим або іншим приголосним.
  treatment_template:
    required_claim: Крок 2. М'який знак усередині слова перед твердим або іншим приголосним. Після надійного засвоєння фінальної позиції м'який знак обережно вводиться в середині слова. Українські шкільні підручники наводять прозорі приклади на зразок «батько», «кількість», «польовий», де м'який приголосний чітко артикулюється перед наступним твердим . Тут англомовному учневі вкрай важливо візуально та аудіально показати, що м'якість не поширюється, мов вірус, на весь склад чи слово, а стосується ізольовано лише одного конкретного приголосного звука .
    shape: module.md section heading or in-prose step marker matching manifest_payload.heading at the position implied by manifest_payload.step_num
- obligation_id: step-3  (obligation_type: sequence_step)
  artifact: module.md
  location_hint: §Апостроф як строгий розділовий знак.
  treatment_template:
    required_claim: Крок 3. Апостроф як строгий розділовий знак. Наступним логічним етапом є введення апострофа. Підручники для 5-го класу чітко та безапеляційно вказують, що апостроф ставиться після губних приголосних (б, п, в, м, ф) та вібранта «р» безпосередньо перед йотованими буквами я, ю, є, ї . Головна функція апострофа в цій позиції — показати, що приголосний категорично залишається твердим, а йотований голосний після нього зберігає свій початковий, подвійний звук [й] + голосний . Класичні приклади для рівня А1: «сім'я», «п'ять», «м'ясо», «п'ю» .
    shape: module.md section heading or in-prose step marker matching manifest_payload.heading at the position implied by manifest_payload.step_num
- obligation_id: step-4  (obligation_type: sequence_step)
  artifact: module.md
  location_hint: §Фонетичний контраст: злита проти роздільної вимови.
  treatment_template:
    required_claim: Крок 4. Фонетичний контраст: злита проти роздільної вимови. На фінальному етапі автор-письменник повинен створити спеціальні контрастні вправи. Підручники для 7-го класу роблять сильний наголос на принциповій різниці між роздільною вимовою (коли ми чітко чуємо [й], і тому пишемо апостроф) та злитою вимовою (коли [й] розчиняється в пом'якшенні, і ми пишемо слово без апострофа або з м'яким знаком) . Для учнів А1 надзвичайно корисно порівнювати такі мінімальні пари, як «буряк» (злита вимова, м'який [р'], без апострофа) та «бур'ян» (роздільна вимова, твердий [р] + [й], з апострофом) .
    shape: module.md section heading or in-prose step marker matching manifest_payload.heading at the position implied by manifest_payload.step_num
- obligation_id: step-5  (obligation_type: sequence_step)
  artifact: module.md
  location_hint: §А1-безпечне закріплення без винятків іншомовного походження.
  treatment_template:
    required_claim: Крок 5. А1-безпечне закріплення без винятків іншомовного походження. Після слухового контрасту учень переходить до коротких контрольованих завдань: знайти знак у слові, прочитати слово вголос, пояснити однією фразою, що робить знак. Складні правила іншомовних слів на кшталт «ательє», «конферансьє», «комп'ютер» або «миш'як» не розгортаються як продуктивна система на А1; вони подаються лише як цілісні знайомі слова, якщо потрібні для теми , . Це зберігає фокус модуля на комунікативній впевненості, а не на середньошкільних винятках.
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
   `pedagogical`.** Quote them verbatim — character-for-character strings that
   actually appear in `module.md`, `activities.yaml`, `vocabulary.yaml`, or
   `resources.yaml`. Do not invent. Do not paraphrase. Do not summarize.

2. **For each quote, state how it maps to the residual-judgment rubric for
   `pedagogical`** (see scope section above; deterministic checks already ran).
   Is this quote evidence FOR the dimension being satisfied, or evidence
   AGAINST? A quote that just confirms a deterministic-gate criterion is
   not residual evidence — find a different one.

3. **Aggregate the score on the 1-10 scale.** Strongest evidence weighs more
   than weakest. What does the balance tell you? Round to 1 decimal place.

4. **Final verdict.** Score ≥8 → PASS. Score 6-7.99 → REVISE. Score <6 →
   REJECT.

The JSON response MUST include `evidence_quotes` with 3 verbatim quotes from step 1 and `rubric_mapping` explaining how each quote maps to `pedagogical` before the score. The `evidence` field MUST be one of those verbatim quotes, wrapped in escaped quotes. A summary or paraphrase in any evidence field is a reviewer-protocol failure.

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
that touches dimension `pedagogical`. The audit feeds the evidence list above:
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
- Module: 3
- Slug: special-signs
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
- Over advisory ceiling words: 2866
- Repetition status: clear
- Repetition matches: 0
- Review action: advisory_review_only; distinguish source-backed density from filler/padding

Use this as review context, not as a mechanical word-count gate. Inspect the
deterministic paragraph matches and marginal pedagogical value throughout the
full size band, not only above the advisory ceiling. Source-backed density and
necessary pedagogy remain acceptable even when long. Repeated framing,
conclusions, transitions, definitions, generic exposition, or uncited
interpretation are filler/padding defects when they affect `pedagogical`.

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

## ULP Presentation Pattern — letter_module:true full contract
For `letter_module: true` A1/A2 plans, follow all seven Anna Ohoiko practices:
1. EM-DASH GLOSS: UK terms precede EN glosses (`привіт — hello`); never gloss-first.
2. SIDE-BY-SIDE BILINGUAL: narratives of 3+ sentences use UK-left / EN-right aligned rendering.
3. STRESS MARKS: keep plain Ukrainian ready for deterministic stress marking; do not transliterate.
4. DIALOGUE UK-ONLY: Tab 1 dialogues are pure Ukrainian; support follows in `en` props or a table/paragraph.
5. UK-ONLY Q&A: comprehension stems and content options stay Ukrainian; English only in UI affordances.
6. TRANSLATE TO WORKBOOK: EN→UK translation drills belong in workbook practice, never Tab 1 prose.
7. NAMED PERSONA: use a named Ukrainian teacher/persona or characters with real Ukrainian anchors.
Reject transliteration tables, `X sounds like Y in English`, EN-first dialogue glossing, vocab dumps, and abstract `the student must learn` framing.

## Contract YAML

```yaml
sections:
- title: Йотовані голосні як передумова
  word_budget:
    target: 250
    min: 225
    max: 275
- title: М'який знак
  word_budget:
    target: 250
    min: 225
    max: 275
- title: Апостроф
  word_budget:
    target: 250
    min: 225
    max: 275
- title: Контраст і типові помилки L2
  word_budget:
    target: 250
    min: 225
    max: 275
- title: Перенос і підсумок
  word_budget:
    target: 200
    min: 180
    max: 220
vocabulary_required:
- день (day) - soft sign after Н
- кінь (horse) - soft sign after Н
- сіль (salt) - soft sign after Л
- вчитель (teacher) - soft sign in a common noun
- сім'я (family) - apostrophe after М
- м'ясо (meat) - apostrophe after М
- п'ять (five) - apostrophe after П
- комп'ютер (computer) - apostrophe in a common loanword
- буряк (beetroot) - no apostrophe, soft Р before Я
- бур'ян (weed) - apostrophe after Р
- свято (holiday) - no apostrophe after consonant cluster
- цвях (nail) - no apostrophe after consonant cluster
vocabulary_optional: []
source_note: Full plan below is authoritative for points, activity hints, vocabulary,
  and references.
```

## Plan

```yaml
activity_hints:
- focus: 'Додай `ь` або апостроф: сім_я, ден_, п_ять, комп_ютер, бур_ян, мален_кий'
  items: 6
  type: fill-in
- focus: 'Розподіли слова на три колонки: є `ь` / є апостроф / немає знака'
  items: 12
  type: group-sort
- focus: 'З''єднай слово з поясненням контрасту: `буряк` = м''якість без апострофа,
    `бур''ян` = апостроф, `свято` = збіг приголосних без апострофа, `цвях` = збіг
    приголосних без апострофа'
  items: 4
  type: match-up
- focus: 'Типові помилки L2 - виправте написання з пропущеним знаком: сім_я, п_ять,
    свято з апострофом, ден_, льожка'
  items: 6
  type: error-correction
- focus: 'Поділи слова для переносу: Мар''-яна, дере-в''яний, бур''-ян, паль-ці'
  items: 4
  type: divide-words
changelog:
- changes:
  - Review-and-lock pass per docs/best-practices/wiki-plan-review-and-lock.md. Added
    lifecycle markers (lifecycle/reviewed_at/reviewed_by/review_notes).
  - 'Re-scoped the plan to the actual slug: removed voiced/voiceless, Г/Ґ, Р, and
    И coverage that belonged to sibling phonetics modules; this plan now teaches only
    `ь` + apostrophe.'
  - 'Added explicit wiki-plan hooks for the locked wiki''s key contrasts: `буряк`
    / `бур''ян` / `свято` / `цвях`.'
  - Added a dedicated transfer block (`Мар'-яна`, `дере-в'яний`, `бур'-ян`, `паль-ці`)
    and a matching `divide-words` activity.
  - Added an `error-correction` activity that mirrors the wiki "Типові помилки L2"
    table and a wiki back-reference in references[].
  date: '2026-04-23'
  version: 1.4.0
- changes:
  - add letter_module flag (true) — allows higher activity counts for letter-recognition
    coverage; word-count target unchanged
  date: '2026-04-25'
  ref: '#1550'
  trigger: Letter-driven module needs explicit exception class for activity-count
    gates and pedagogical-stage reviewer calibration (a1/3 in alphabet/orthography
    exception class with a1/1 and a1/2).
  version: 1.4.1
connects_to:
- a1-004 (Наголос та мелодика)
content_outline:
- points:
  - 'Почати з короткого повторення: `я`, `ю`, `є` після приголосного без апострофа
    зазвичай пом''якшують його, а після апострофа читаються роздільно. `Ї` завжди
    дає `[йі]`. Без цього контрасту `ь` та апостроф зависають у повітрі як дві окремі
    "дивні букви".'
  - 'Показати найраніший набір слів-моделей: `буряк`, `люди`, `свято` проти `м''ята`,
    `сім''я`, `п''ять`. На цьому етапі не вчимо нове велике правило - лише ставимо
    слуховий маяк: "тут звук м''якшає", "тут чути `[й]`".'
  section: Йотовані голосні як передумова
  words: 250
- points:
  - 'М''який знак не має власного звука. Він лише змінює попередній приголосний. Основні
    A1-слова: `день`, `кінь`, `сіль`, `вчитель`, `маленький`, `сьогодні`.'
  - 'Для контрасту дати 2-3 короткі пари: `стан` - `стань`, `лан` - `лань`, `рис`
    - `рись`. Саме такі пари показують, що `ь` не "читається", але без нього слово
    звучить і виглядає інакше.'
  - 'Авторова примітка: коротка шкільна мнемоніка `Де ти з''їси ці лини?` корисна
    лише як опора для ядра вправ; у повному орфографічному наборі для `ь` автор пам''ятає
    `д, т, з, с, ц, л, н, р, дз`, але не перевантажує цим учня на першому проході.'
  section: М'який знак
  words: 250
- points:
  - 'Базова A1-модель: апостроф після `б`, `п`, `в`, `м`, `ф`, `р` перед `я`, `ю`,
    `є`, `ї`. Перші слова: `сім''я`, `м''ясо`, `п''ять`, `дев''ять`, `ім''я`, `комп''ютер`.'
  - 'Найважливіше пояснення - апостроф не робить попередній звук м''яким, а навпаки
    не дає його пом''якшити: `м''я` = твердий `м` + `[йа]`. Саме це треба почути вголос
    і повторити кілька разів.'
  - Префіксний апостроф (`під'їзд`, `з'їзд`) згадуємо лише як пізнішу тему; не робимо
    з нього продуктивне правило цього модуля.
  section: Апостроф
  words: 250
- points:
  - 'Центральний контраст модуля: `буряк` проти `бур''ян`. У першому слові `р` м''який
    і немає апострофа; у другому - апостроф утримує `р` твердим і після нього чути
    `[йа]`.'
  - 'Окремо дати "зону без апострофа": `свято`, `цвях`, `морквяний`. Тут апостроф
    не пишеться, хоча учень може чекати його механічно. Це готові приклади, а не правило
    для виведення з нуля.'
  - 'Усі activity_hints цього блоку повинні дзеркалити wiki "Типові помилки L2": пропуск
    апострофа у слові `сім''я`, механічний апостроф (`св''ято`), пропуск `ь` (`ден`),
    механічне `льожка`.'
  section: Контраст і типові помилки L2
  words: 250
- points:
  - 'Закріпити, що `ь` та апостроф тримаються попередньої літери при переносі: `Мар''-яна`,
    `дере-в''яний`, `бур''-ян`, `паль-ці`. Додати правило: одну букву не залишаємо
    окремо і не переносимо саму.'
  - 'Самоперевірка: учень має вміти пояснити різницю між `день`, `сім''я`, `буряк`,
    `бур''ян`, `свято`; вставити знак у 4-5 словах; правильно поділити для переносу
    2-3 приклади.'
  section: Перенос і підсумок
  words: 200
focus: phonetics
grammar:
- 'Йотовані літери як передумова: `я`, `ю`, `є` після приголосного без апострофа зазвичай
  пом''якшують його; після апострофа читаються роздільно'
- '`Ї` завжди позначає `[йі]`; м''який знак перед нею не ставиться'
- М'який знак (`ь`) не має звука й пом'якшує попередній приголосний
- 'Для автора: повний набір приголосних для `ь` - `д, т, з, с, ц, л, н, р, дз`; для
  учня на A1 достатньо високочастотних моделей `день`, `кінь`, `сіль`, `вчитель`'
- 'Базова A1-модель апострофа: після `б`, `п`, `в`, `м`, `ф`, `р` перед `я`, `ю`,
  `є`, `ї`'
- 'Контраст `буряк` / `бур''ян` / `свято` як три окремі сценарії: м''якість без апострофа
  / апостроф / збіг приголосних без апострофа'
- 'Перенос: `ь` та апостроф не відриваються від попередньої літери; одну букву не
  залишаємо окремо'
letter_module: true
level: A1
lifecycle: locked
module: a1-003
objectives:
- Розуміти, як `я`, `ю`, `є`, `ї` працюють як передумова для м'якого знака й апострофа
- Читати й писати базові слова з м'яким знаком (`день`, `кінь`, `сіль`, `вчитель`)
- Читати й писати базові слова з апострофом (`сім'я`, `м'ясо`, `п'ять`, `комп'ютер`)
- Розрізняти три сценарії - м'якість без апострофа (`буряк`), апостроф (`бур'ян`)
  і зону без апострофа після збігу приголосних (`свято`, `цвях`)
- Користуватися готовими моделями переносу (`Мар'-яна`, `дере-в'яний`, `бур'-ян`,
  `паль-ці`)
- Впізнавати й виправляти типові L2-помилки - пропуск апострофа, механічне вставляння
  апострофа, пропуск `ь`, механічне `льожка`
pedagogy: PPP
phase: A1.1 [Звуки, літери та перший контакт]
prerequisites:
- a1-001 (Звуки, літери та привіт)
- a1-002 (Читаємо українською)
references:
- notes: 'Базове правило апострофа: після б, п, в, м, ф, р перед я, ю, є, ї.'
  title: Захарійчук, 1 клас (НУШ 2025), стор. 97
- notes: М'який знак як показник м'якості приголосного; шкільне узагальнення про набір
    приголосних.
  title: Авраменко, 5 клас, стор. 75
- notes: 'Апостроф і перенос слів: моделі `Мар''-яна`, `дере-в''яний`, `бур''-ян`.'
  title: Большакова, 2 клас, стор. 58-59
- notes: Authoritative pedagogical brief - see the contrast block (`буряк` / `бур'ян`
    / `свято` / `цвях`), the writer note after "Словниковий мінімум", and the wiki
    "Типові помилки L2" table.
  title: 'Wiki: pedagogy/a1/special-signs (LOCKED 2026-04-23)'
register: розмовний
review_notes: 'Review-and-lock pass per the #1412 rubric template (docs/best-practices/wiki-plan-review-and-lock.md).
  Plan-side findings: the prior plan drifted outside the slug by teaching voiced/voiceless
  pairs, Г/Ґ, Р, and И inside `special-signs`, while the paired wiki is specifically
  about `ь` + apostrophe. Fixed by re-scoping the plan to special signs only, adding
  hooks for the locked wiki''s key contrasts (`буряк` / `бур''ян` / `свято` / `цвях`),
  adding a transfer block (`Мар''-яна`, `дере-в''яний`), mirroring the wiki''s `Типові
  помилки L2` table in activity_hints, and adding lifecycle markers plus a wiki back-reference.
  Scan clean for Russianisms, calques, homoglyphs, and word-count contradictions.'
reviewed_at: '2026-04-23T09:32:45Z'
reviewed_by: codex-scale-special-signs
sequence: 3
slug: special-signs
subtitle: Ь, апостроф і три ключові контрасти - день, сім'я, буряк/бур'ян
targets:
  new_grammar: []
  new_vocabulary:
  - день
  - кінь
  - сіль
  - вчитель
  - сім'я
  - м'ясо
  - п'ять
  - комп'ютер
  - буряк
  - бур'ян
  - свято
  - цвях
  recycle_vocabulary: []
title: Особливі знаки
version: 1.4.2
vocabulary_hints:
  author_note: 'У цьому модулі слова подаються як орфографічні та фонетичні чанки,
    а не як матеріал для відмінювання чи словотвору. НЕ робіть продуктивним префіксне
    правило апострофа, НЕ перетворюйте `буряк/бур''ян/свято` на повний урок з фонології,
    НЕ виводьте нові "аналогії" поза списком нижче без перевірки у VESUM. Мета модуля
    - стабілізувати три контрасти: `день`, `сім''я`, `буряк/бур''ян`.'
  recommended:
  - дев'ять (nine) - apostrophe after В
  - ім'я (name) - apostrophe after М
  - здоров'я (health) - apostrophe after В
  - маленький (small) - soft sign in a high-frequency adjective
  - сьогодні (today) - soft sign in a frequent adverb
  - Мар'яна (given name) - transfer model `Мар'-яна`
  - дерев'яний (wooden) - transfer model `дере-в'яний`
  - ложка (spoon) - counterexample against mechanical `льожка`
  required:
  - день (day) - soft sign after Н
  - кінь (horse) - soft sign after Н
  - сіль (salt) - soft sign after Л
  - вчитель (teacher) - soft sign in a common noun
  - сім'я (family) - apostrophe after М
  - м'ясо (meat) - apostrophe after М
  - п'ять (five) - apostrophe after П
  - комп'ютер (computer) - apostrophe in a common loanword
  - буряк (beetroot) - no apostrophe, soft Р before Я
  - бур'ян (weed) - apostrophe after Р
  - свято (holiday) - no apostrophe after consonant cluster
  - цвях (nail) - no apostrophe after consonant cluster
word_target: 1200

```

## Generated Content

## lesson-1
## module.md

# Особливі знаки

**день. сім'я́. буря́к. бур'я́н.** — four words, two signs, three
beginner contrasts.

The signs are small on the page, but they are not decorative. They tell your
mouth how to read the nearby letters.

Listen once before you write. A native Ukrainian teacher or tutor can say
**день**, **сім'я́**, **буря́к**, **бур'я́н**, and **свя́то**; you point to
the sign you hear on the page. If you are working alone, record your own voice
and compare it with the routine below.

Teacher Oksana's routine for this module is short: find the sign, say what it
does, then read the word once.

Keep the goal simple. You are not learning every spelling rule today. You are
learning these beginner contrasts:

- **день** — **ь** has no sound, but it softens the consonant before it;
- **сім'я́** — apostrophe keeps the previous consonant hard and lets you hear
  **[й]** before **я**;
- **буря́к / бур'я́н / свя́то / цвях** — sometimes **я** softens, sometimes
  apostrophe separates, and sometimes two consonants before **я** mean there is
  no apostrophe.

By the end, you can:

- recognize **ь** and apostrophe in common A1 words;
- read **день**, **кінь**, **сіль**, and **вчи́тель** without adding an extra
  vowel;
- read **сім'я́**, **м'я́со**, **п'ять**, and **комп'ю́тер** with **й** after
  the apostrophe;
- sort words into **м'яки́й знак**, **апо́строф**, and **без зна́ка**;
- choose the safer form when a visual habit creates a mistake.

## Йотовані голосні

**Я Ю Є Ї** — the four special vowel letters.

Module 2 already introduced these letters. Here you only need the quick review
that makes **ь** and apostrophe readable.

At beginner level, use this rule:

| Position | Beginner reading habit |
| --- | --- |
| **я, ю, є** after a consonant with no apostrophe | the consonant becomes soft, then you read the vowel |
| **я, ю, є, ї** after an apostrophe | keep the previous consonant hard, then read **[й] + vowel** |
| **ї** anywhere | always **[йі]** |

Compare two words:

| Слово́ | Reading effect |
| --- | --- |
| **буря́к** | no apostrophe; **р** softens before **я** |
| **бур'я́н** | apostrophe; **р** stays hard, then you hear **[йа]** |

The apostrophe is a Ukrainian reading instruction: do not soften the previous
consonant; keep the next **й** sound.

Use one listening question before spelling. Say or hear the word slowly: do I
hear a separate **й** before **я, ю, є, ї**? If yes, apostrophe may be part of
the prepared spelling. If no, the vowel letter may simply soften the previous
consonant.

Коли́ ми чита́ємо зли́то, при́голосний перед лі́терою пом'я́кшується — when we read smoothly, the consonant before the letter softens. Коли́ ми чита́ємо розді́льно, між зву́ками з'явля́ється [й] — when we read separately, [й] appears between the sounds.

<!-- INJECT_ACTIVITY: act-1 -->

## М'яки́й знак

**Ь ь** — **м'яки́й знак**.

It has no sound of its own. It changes the consonant before it.

| Слово́ | English support | What to notice |
| --- | --- | --- |
| **день** | day | final **нь** is soft |
| **кінь** | horse | final **нь** is soft |
| **сіль** | salt | final **ль** is soft |
| **вчи́тель** | teacher | final **ль** is soft |

Do not read **ь** as **і**, **й**, or a tiny extra vowel. In **день**, stop on
soft **н**. In **сіль**, stop on soft **л**.

Short contrast pairs show the job. Treat them as sound examples, not new
vocabulary to memorize today:

| Without soft sign | With soft sign | Reading idea |
| --- | --- | --- |
| **стан** | **стань** | listen only for hard **н** vs soft **нь** |
| **лан** | **лань** | listen only for hard **н** vs soft **нь** |
| **рис** | **рись** | listen only for hard **с** vs soft **сь** |

These pairs are reading tools. You do not need to use all of them in
conversation today.

:::tip
**ь** points backward. It is a silent instruction for the consonant before it.
:::

<!-- INJECT_ACTIVITY: act-2 -->

Послу́хайте коро́тку розмо́ву про день та вчи́теля — listen to a short conversation about the day and the teacher:

> **Окса́на**: До́брий день!
> **Іва́н**: До́брий день, вчи́телю!
> **Окса́на**: Сього́дні га́рний день.
> **Іва́н**: Так, день те́плий і я́сний.

| Українська | English support |
| --- | --- |
| **Окса́на: До́брий день!** | Oksana: Good day! |
| **Іва́н: До́брий день, вчи́телю!** | Ivan: Good day, teacher! |
| **Окса́на: Сього́дні га́рний день.** | Oksana: Today is a nice day. |
| **Іва́н: Так, день те́плий і я́сний.** | Ivan: Yes, the day is warm and clear. |

Зверні́ть ува́гу: сло́во **день** ма́є м'яки́й кінце́вий звук [н'], а сло́во **вчи́тель** — м'яки́й звук [л']. Це знак м'я́кшення.

<!-- INJECT_ACTIVITY: act-101 -->

## Апостроф

**'** — **апо́строф**.

Read it as a separation sign. It does not make a big pause. It keeps the
previous consonant hard and lets the next **я, ю, є, ї** start with **[й]**.

The first A1 model is:

**б, п, в, м, ф, р + апостроф + я, ю, є, ї**

Start with these words:

| Слово́ | English support | What to hear |
| --- | --- | --- |
| **сім'я́** | family | **м** stays hard, then **[йа]** |
| **м'я́со** | meat | **м** stays hard, then **[йа]** |
| **п'ять** | five | **п** stays hard, then **[йа]** |
| **де́в'ять** | nine | **в** stays hard, then **[йа]** |
| **ім'я́** | name | **м** stays hard, then **[йа]** |
| **комп'ю́тер** | computer | **п** stays hard, then **[йу]** |

Read **п'ять** smoothly, with a clear **й** sound. The airflow continues; the
spelling tells you to separate the consonant from the iotated vowel.

For now, do not build a large system from loanwords. **Комп'ю́тер** is useful
because learners know the object, but the lesson target is the apostrophe
itself.

<!-- INJECT_ACTIVITY: act-3 -->

Послу́хайте коро́тку розмо́ву про сім'ю́ та комп'ю́тер — listen to a short conversation about family and computer:

> **Окса́на**: Це твоя́ сім'я́?
> **Іва́н**: Так, це моя́ сім'я́. Нас п'ять у роди́ні.
> **Окса́на**: А де твій комп'ю́тер?
> **Іва́н**: Ось мій комп'ю́тер на столі́.
> **Окса́на**: Чудо́во, це твій робо́чий куто́к.

| Українська | English support |
| --- | --- |
| **Окса́на: Це твоя́ сім'я́?** | Oksana: Is this your family? |
| **Іва́н: Так, це моя́ сім'я́. Нас п'ять у роди́ні.** | Ivan: Yes, this is my family. There are five of us in the family. |
| **Окса́на: А де твій комп'ю́тер?** | Oksana: And where is your computer? |
| **Іва́н: Ось мій комп'ю́тер на столі́.** | Ivan: Here is my computer on the table. |
| **Окса́на: Чудо́во, це твій робо́чий куто́к.** | Oksana: Wonderful, this is your working corner. |

Потрену́йтеся у вимо́ві слів із апо́строфом. Повторі́ть уго́лос: **сім'я́**, **м'я́со**, **п'ять**, **комп'ю́тер**. При́голосний залиша́ється тверди́м, а насту́пний звук [й] звучи́ть вира́зно й чі́тко.

<!-- INJECT_ACTIVITY: act-102 -->


## activities.yaml

inline:
- id: act-1
  type: quiz
  title: М'яко чи розді́льно
  instruction: Обери пояснення для читання.
  items:
  - prompt: Буря́к — що відбувається перед літерою я?
    options:
    - text: Р пом'якшується перед я.
      correct: true
    - text: Є апо́строф.
      correct: false
    - text: Ї завжди [йі].
      correct: false
    explanation: У слові буря́к немає апо́строфа; р пом'якшується перед я.
  - prompt: Бур'я́н — що робить апо́строф?
    options:
    - text: Р зникає.
      correct: false
    - text: Р залишається твердим, потім чути [йа].
      correct: true
    - text: Додає звук [і].
      correct: false
    explanation: Апо́строф відділяє р від я.
  - prompt: Ї — що завжди правильно?
    options:
    - text: Мовчить.
      correct: false
    - text: Це м'яки́й знак.
      correct: false
    - text: Завжди [йі].
      correct: true
    explanation: Ї завжди позначає [йі].
- id: act-2
  type: match-up
  title: Що робить ь
  instruction: З'єднай кожне слово з підказкою про м'яки́й знак.
  pairs:
  - left: день
    right: м'який н у слові день
  - left: кінь
    right: м'який н у слові кінь
  - left: сіль
    right: м'який л у слові сіль
  - left: вчи́тель
    right: м'який л у слові вчи́тель
  - left: м'яки́й знак
    right: не має власного звука
- id: act-101
  type: match-up
  title: Тверди́й чи м'яки́й звук
  instruction: З'єднай кожне слово з описом кінцевого звука.
  pairs:
  - left: стань
    right: слово з м'яким звуком [н']
  - left: стан
    right: слово з твердим звуком [н]
  - left: лань
    right: слово з м'яким звуком [н'] у слові лань
  - left: лан
    right: слово з твердим звуком [н] у слові лан
  - left: рись
    right: слово з м'яким звуком [с']
  - left: рис
    right: слово з твердим звуком [с]
- id: act-3
  type: fill-in
  title: Додай знак
  instruction: Обери ь, апо́строф або без знака.
  items:
  - sentence: сім_я
    answer: ''''
    options:
    - ''''
    - ь
    - без знака
  - sentence: ден_
    answer: ь
    options:
    - ь
    - ''''
    - без знака
  - sentence: п_ять
    answer: ''''
    options:
    - ''''
    - ь
    - без знака
  - sentence: У слові свя́то правильний вибір — ____.
    answer: без знака
    options:
    - без знака
    - ''''
    - ь
- id: act-102
  type: quiz
  title: Приголосний перед апострофом
  instruction: Обери правильну відповідь про роль апострофа.
  items:
  - prompt: Що робить апо́строф у слові сім'я́?
    options:
    - text: Зберігає м твердим і відокремлює я.
      correct: true
    - text: Пом'якшує літеру м.
      correct: false
    - text: Додає звук [і].
      correct: false
    explanation: Апо́строф зберігає приголосний твердим перед йотованою голосною.
  - prompt: Як читаємо слово м'я́со?
    options:
    - text: З твердим [м] та початковим [йа].
      correct: true
    - text: З м'яким [м'].
      correct: false
    - text: Як одне злите [ма].
      correct: false
    explanation: Апо́строф показує твердий звук [м] і роздільне [йа].
  - prompt: Яка літера стоїть перед апострофом у слові п'ять?
    options:
    - text: Губна літера п.
      correct: true
    - text: Літера л.
      correct: false
    - text: Літера н.
      correct: false
    explanation: Літера п — одна з губних букв (б, п, в, м, ф).
  - prompt: Що чути після апострофа перед літерою ю в слові комп'ю́тер?
    options:
    - text: Звукосполучення [йу].
      correct: true
    - text: Простий звук [у] без [й].
      correct: false
    - text: Звук [і].
      correct: false
    explanation: Після апострофа ю завжди позначає [йу].
  - prompt: У слові де́в'ять після якої літери стоїть апо́строф?
    options:
    - text: Після літери в.
      correct: true
    - text: Після літери д.
      correct: false
    - text: Після літери я.
      correct: false
    explanation: Апо́строф стоїть після губної літери в перед я.
  - prompt: Чи робить апо́строф велику паузу у вимові?
    options:
    - text: Ні, видих триває, але приголосний не пом'якшується.
      correct: true
    - text: Так, треба зупинити дихання на кілька секунд.
      correct: false
    - text: Так, це знак кінця речення.
      correct: false
    explanation: Апо́строф — це інструкція для вимови, а не довга пауза.
workbook:
- id: act-w1
  type: group-sort
  title: Сортуй за знаком
  instruction: Розподіли кожне слово в правильну групу.
  groups:
  - label: Є ь
    items:
    - день
    - кінь
    - сіль
    - вчи́тель
    - мале́нький
  - label: Є апо́строф
    items:
    - сім'я́
    - м'я́со
    - п'ять
    - комп'ю́тер
    - бур'я́н
  - label: Немає знака
    items:
    - буря́к
    - свя́то
    - цвях
    - ло́жка
- id: act-w2
  type: match-up
  title: Поясни контраст
  instruction: З'єднай слово з поясненням.
  pairs:
  - left: буря́к
    right: 'м''якість без апо́строфа: р + я'
  - left: бур'я́н
    right: 'апо́строф: р твердий, потім [йа]'
  - left: свя́то
    right: збіг св + я без апо́строфа
  - left: цвях
    right: збіг цв + я без апо́строфа
- id: act-w101
  type: fill-in
  title: Встав знак у знайомих словах
  instruction: Вибери ь, апо́строф або без знака.
  items:
  - sentence: Сьогодні гарний ден_.
    answer: ь
    options:
    - ь
    - ''''
    - без знака
  - sentence: Це моя рідна сім_я.
    answer: ''''
    options:
    - ''''
    - ь
    - без знака
  - sentence: На столі лежить свіже м_ясо.
    answer: ''''
    options:
    - ''''
    - ь
    - без знака
  - sentence: У класі працює новий вчител_.
    answer: ь
    options:
    - ь
    - ''''
    - без знака
  - sentence: У кімнаті стоїть комп_ютер.
    answer: ''''
    options:
    - ''''
    - ь
    - без знака
  - sentence: На лузі пасеться білий кін_.
    answer: ь
    options:
    - ь
    - ''''
    - без знака
- id: act-w102
  type: true-false
  title: Правила вимови знаків
  instruction: 'Обери: правда чи неправда.'
  items:
  - statement: М'яки́й знак має власний голосний звук.
    correct: false
    explanation: М'яки́й знак не має власного звука.
  - statement: У слові день кінцевий звук [н'] є м'яким.
    correct: true
    explanation: Буква ь показує м'якість [н'].
  - statement: Апо́строф пом'якшує попередній приголосний.
    correct: false
    explanation: Апо́строф зберігає приголосний твердим.
  - statement: Після апострофа літери я, ю, є позначають два звуки з [й].
    correct: true
    explanation: Після апострофа чути [йа], [йу], [йе].
  - statement: У слові сіль буква ь пом'якшує звук [л'].
    correct: true
    explanation: Ь вказує на м'якість [л'].
  - statement: Слово вчи́тель читається з твердим [л] у кінці.
    correct: false
    explanation: У слові вчи́тель звук [л'] м'який.
- id: act-w103
  type: odd-one-out
  title: Зайве слово за знаком
  instruction: Обери слово, яке відрізняється від інших наявністю знака.
  items:
  - words:
    - день
    - кінь
    - сіль
    - м'я́со
    answer: м'я́со
    explanation: М'я́со має апо́строф, а інші — м'який знак.
  - words:
    - сім'я́
    - п'ять
    - ім'я́
    - вчи́тель
    answer: вчи́тель
    explanation: Вчи́тель має м'який знак, а інші — апо́строф.
  - words:
    - де́в'ять
    - м'я́со
    - комп'ю́тер
    - кінь
    answer: кінь
    explanation: Кінь має м'який знак, а інші — апо́строф.
  - words:
    - день
    - сіль
    - вчи́тель
    - п'ять
    answer: п'ять
    explanation: П'ять має апо́строф перед я, а інші слова мають м'який знак.
  - words:
    - сім'я́
    - де́в'ять
    - м'я́со
    - стан
    answer: стан
    explanation: Стан не має жодного знака, а інші слова мають апо́строф.
  - words:
    - кінь
    - день
    - сіль
    - рис
    answer: рис
    explanation: Рис не має м'якого знака, а інші слова мають ь.
- id: act-w104
  type: match-up
  title: З'єднай слово та переклад
  instruction: З'єднай українське слово з його значенням.
  pairs:
  - left: день
    right: day
  - left: кінь
    right: horse
  - left: сіль
    right: salt
  - left: вчи́тель
    right: teacher
  - left: сім'я́
    right: family
  - left: м'я́со
    right: meat
- id: act-w105
  type: group-sort
  title: Розподіл слів за знаком
  instruction: 'Розподіли слова на дві групи: слова з ь та слова з апострофом.'
  groups:
  - label: Слова з м'яким знаком (ь)
    items:
    - день
    - кінь
    - сіль
    - вчи́тель
  - label: Слова з апострофом (')
    items:
    - сім'я́
    - м'я́со
    - п'ять
    - комп'ю́тер
    - де́в'ять
    - ім'я́


## vocabulary.yaml

- lemma: м'яки́й знак
  translation: soft sign
  pos: noun phrase
  usage: Ь — м'яки́й знак.
- lemma: апо́строф
  translation: apostrophe
  pos: noun
  usage: У сло́ві «сім'я́» є апо́строф.
- lemma: знак
  translation: sign
  pos: noun
  usage: Це знак.
- lemma: м'яки́й
  translation: soft
  pos: adjective
  usage: Це м'яки́й звук.
- lemma: тверди́й
  translation: hard
  pos: adjective
  usage: Це тверди́й звук.
- lemma: йото́ваний
  translation: iotated
  pos: adjective
  usage: Я — йото́вана лі́тера.
- lemma: розді́льно
  translation: separately
  pos: adverb
  usage: Чита́й розді́льно.
- lemma: зли́то
  translation: together / smoothly
  pos: adverb
  usage: Чита́й зли́то.
- lemma: день
  translation: day
  pos: noun
  usage: День.
- lemma: кінь
  translation: horse
  pos: noun
  usage: Кінь.
- lemma: сіль
  translation: salt
  pos: noun
  usage: Сіль.
- lemma: вчи́тель
  translation: teacher
  pos: noun
  usage: Вчи́тель.
- lemma: сім'я́
  translation: family
  pos: noun
  usage: Сім'я́.
- lemma: м'я́со
  translation: meat
  pos: noun
  usage: М'я́со.
- lemma: п'ять
  translation: five
  pos: numeral
  usage: П'ять.
- lemma: де́в'ять
  translation: nine
  pos: numeral
  usage: Де́в'ять.
- lemma: ім'я́
  translation: name
  pos: noun
  usage: Ім'я́.
- lemma: комп'ю́тер
  translation: computer
  pos: noun
  usage: Комп'ю́тер.


## resources.yaml

- title: Захарійчук, 1 клас (НУШ 2025), p. 97
  role: textbook
  source: Захарійчук, 1 клас (НУШ 2025), p. 97
  notes: 'Plan reference: basic apostrophe rule before я, ю, є, ї.'
- title: Український правопис (2019), § 7, § 26
  role: reference
  url: https://2019.pravopys.net/sections/7/
  source: pravopys
  notes: Правила вживання апострофа та знака м'якшення (ь).
- title: Большакова, 2 клас, p. 58-59
  role: textbook
  source: Большакова, 2 клас, p. 58-59
  notes: Апостроф як твердий приголосний + [йа].


## lesson-2
## module.md

## Контраст і пастки

У пе́ршому уро́ці ми ви́вчили два головні́ зна́ки — in the first lesson we learned two main signs: **м'яки́й знак** *(soft sign)* та **апо́строф** *(apostrophe)*. Тепе́р час поєдна́ти їх у три важли́ві контра́сти — now it is time to combine them into three key contrasts: м'я́кість без зна́ка *(softness without a sign)*, розді́льна вимо́ва з апо́строфом *(separated pronunciation with an apostrophe)*, та зо́на без зна́ка після збі́гу при́голосних *(no-sign zone after consonant clusters)*.

**буря́к / бур'я́н / свя́то / цвях** — the central contrast.

| Scenario | Example | Beginner explanation |
| --- | --- | --- |
| softness with no apostrophe | **буря́к** | **р** softens before **я** |
| apostrophe | **бур'я́н** | **р** stays hard, then **[йа]** |
| two consonants before **я** with no apostrophe | **свя́то**, **цвях** | no apostrophe in these prepared words |

Mechanical spelling fails here. You cannot put apostrophe before every **я**.
You also cannot ignore apostrophe when it is written.

Use these safe decisions:

| If you see... | Do this |
| --- | --- |
| **день**, **кінь**, **сіль** | read the final consonant softly; add no extra vowel |
| **сім'я́**, **м'я́со**, **п'ять** | keep the consonant hard and read the following **й** |
| **буря́к** | no apostrophe; read soft **р** before **я** |
| **бур'я́н** | apostrophe; read hard **р** plus **[йа]** |
| **свя́то**, **цвях** | remember them as no-apostrophe words |

Common learner traps:

| Trap | Safer habit |
| --- | --- |
| dropping the apostrophe in the family word | write **сім'я́** |
| putting apostrophe into **свя́то** | keep **свя́то** with no apostrophe |
| writing **ден** for **день** | keep **ь** after **н** |
| inventing a soft-sign version of **ло́жка** | do not invent a soft sign or soft **л** |
| treating apostrophe as a hard stop | keep airflow and pronounce **й** |

Stay inside Ukrainian for this lesson. The apostrophe and soft sign already
have Ukrainian jobs, so you do not need another alphabet or another sign to
explain them.

<!-- INJECT_ACTIVITY: act-4 -->

Послу́хайте коро́тку розмо́ву про свя́то та обі́д — listen to a short conversation about a holiday and lunch:

> **Тара́с**: Сього́дні свя́то! *(Today is a holiday!)*
> **Мар'я́на**: Так, сього́дні чудо́вий день! *(Yes, today is a wonderful day!)*
> **Тара́с**: Ось сві́же м'я́со та черво́ний буря́к на обі́д. *(Here is fresh meat and red beetroot for lunch.)*
> **Мар'я́на**: Чудо́во! Ось вели́ка ло́жка. *(Wonderful! Here is a big spoon.)*

Зверні́ть ува́гу на контра́сти у цій розмо́ві — pay attention to the contrasts in this conversation:
- У сло́ві **буря́к** *(beetroot)* звук [р'] пом'я́кшується перед **я** *(sound [r'] softens before ya)*.
- У сло́ві **бур'я́н** *(weed)* апо́строф трима́є звук [р] тверди́м *(apostrophe keeps sound [r] hard)*: [бур-йа́н].
- У слова́х **свя́то** *(holiday)* та **цвях** *(nail)* апо́строфа нема́є через збіг при́голосних *(there is no apostrophe because of a consonant cluster)*: **св** та **цв** перед **я** *(sv and tsv before ya)*.
- У сло́ві **ло́жка** *(spoon)* лі́тера **л** є твердо́ю *(letter l is hard)*; не дода́ємо ви́гаданий м'яки́й знак *(do not add an invented soft sign)*.

<!-- INJECT_ACTIVITY: act-201 -->

<!-- INJECT_ACTIVITY: act-202 -->

## Перенос і письмо

You will sometimes see words split across a line in printed Ukrainian. At this
level, use only prepared models:

| Whole word | Safe line-break model |
| --- | --- |
| **Мар'я́на** | `Мар'-яна` |
| **дерев'я́ний** | `дере-в'яний` |
| **бур'я́н** | `бур'-ян` |
| **па́льці** | `паль-ці` |

The simple idea: **ь** and apostrophe stay with the letter before them. Also,
do not leave one single letter alone on a line.

Послу́хайте, як обгово́рюють пра́вила перено́су слів — listen to how the word division rules are discussed:

> **Оле́г**: Приві́т! Як перено́сити сло́во бур'я́н? *(Hi! How to divide the word бур'ян across lines?)*
> **Мар'я́на**: Ду́же про́сто: бур'-ян. *(Very simple: бур'-ян.)* Апо́строф залиша́ється з лі́терою перед ним. *(The apostrophe stays with the letter before it.)*
> **Оле́г**: А як перено́сити сло́во па́льці? *(And how to divide the word пальці?)*
> **Мар'я́на**: Ось так: паль-ці. *(Like this: паль-ці.)* М'яки́й знак теж залиша́ється з лі́терою перед ним. *(The soft sign also stays with the letter before it.)*

Коли ми ді́лимо слова́ для перено́су *(when we divide words for line breaks)*, запам'ята́йте дві голо́вні моде́лі *(memorize two main models)*:
1. **М'яки́й знак залиша́ється з лі́терою** *(soft sign stays with the letter)*: **паль-ці** *(fin-gers)*, **ма-лень-кий** *(small)*. Ніко́ли не перено́сьте м'яки́й знак на нови́й рядо́к окре́мо *(never move soft sign to a new line alone)*.
2. **Апо́строф залиша́ється з лі́терою** *(apostrophe stays with the letter)*: **Мар'-яна**, **дере-в'яний** *(wood-en)*, **бур'-ян** *(weed)*. Не відрива́йте апо́строф від лі́тери *(do not detach apostrophe from the letter)*.

Reading before writing: first recognize the printed word, then copy the sign in
a notebook cue.

Use original text on this page, your own notebook, or live handwriting from a
teacher/tutor.

| Printed word | Notebook cue |
| --- | --- |
| **день** | find the soft sign at the end |
| **сім'я́** | find the apostrophe before **я** |
| **п'ять** | find both apostrophe and soft sign |
| **свя́то** | confirm there is no apostrophe |

Ask a native Ukrainian teacher or tutor to listen to a short read-aloud:
**день, сім'я́, буря́к, бур'я́н, свя́то**. The feedback target is small:
soft ending, clear **й**, no invented pause.

Before you leave the lesson tab, check that you can do these things:

- say that **ь** has no sound of its own;
- read **день**, **кінь**, **сіль**, and **вчи́тель** without adding **і**;
- say that apostrophe keeps the previous consonant hard;
- read **сім'я́**, **м'я́со**, **п'ять**, and **комп'ю́тер** with **й** after
  the apostrophe;
- explain **буря́к** and **бур'я́н** with the support table;
- remember that **свя́то** and **цвях** have no apostrophe;
- choose the correct sign in short prepared words;
- identify missing-apostrophe, missing-soft-sign, and invented-soft-sign
  errors.

Use the signs as reading instructions, not decorations. Before moving on,
choose one word from each contrast and do a final sign check: name the sign,
state its effect, then read the word.

<!-- INJECT_ACTIVITY: act-5 -->

<!-- INJECT_ACTIVITY: act-203 -->


## activities.yaml

inline:
- id: act-4
  type: error-correction
  title: Виправ пастки
  instruction: Обери правильну українську форму.
  items:
  - sentence: Не пиши сімя без апо́строфа.
    error: сімя
    correction: сім'я́
    options:
    - сім'я́
    - сімя
    explanation: У слові сім'я́ потрібен апо́строф.
  - sentence: День — не пиши ден.
    error: ден
    correction: день
    options:
    - день
    - ден
    explanation: День потребує м'якого знака.
  - sentence: Не пиши св'ято з апо́строфом.
    error: св'ято
    correction: свя́то
    options:
    - свя́то
    - св'ято
    explanation: У слові свя́то немає апо́строфа.
  - sentence: Не пиши льожка з вигаданим м'яки́м знаком.
    error: льожка
    correction: ло́жка
    options:
    - ло́жка
    - льожка
    explanation: Ло́жка не має м'якого знака після л.
- id: act-201
  type: match-up
  title: Чому такий знак
  instruction: З'єднай кожне слово з поясненням його написання.
  pairs:
  - left: буря́к
    right: р пом'якшується перед я без знака
  - left: бур'я́н
    right: апостроф зберігає р твердим перед я
  - left: свя́то
    right: збіг приголосних св перед я без апострофа
  - left: цвях
    right: збіг приголосних цв перед я без апострофа
  - left: день
    right: м'який знак показує м'якість кінцевого н
  - left: ло́жка
    right: твердий звук л без м'якого знака
- id: act-202
  type: quiz
  title: Обери правильне правило
  instruction: Визнач, яке фонетичне правило діє у кожному слові.
  items:
  - prompt: Чому в слові буря́к немає апострофа?
    options:
    - text: Бо звук [р'] м'який перед я.
      correct: true
    - text: Бо після р завжди пишеться м'який знак.
      correct: false
    - text: Бо це іноземне слово.
      correct: false
    explanation: У слові буря́к звук [р'] є м'яким, тому апостроф не ставиться.
  - prompt: Що робить апостроф у слові бур'я́н?
    options:
    - text: Зберігає р твердим, після чого чути [йа].
      correct: true
    - text: Пом'якшує букву р.
      correct: false
    - text: Робить паузу між складами.
      correct: false
    explanation: Апостроф не пом'якшує приголосний, а розділяє твердий р та йотований
      [йа].
  - prompt: Чому в слові свя́то не пишемо апостроф?
    options:
    - text: Через збіг двох приголосних перед я.
      correct: true
    - text: Бо я тут позначає звук [а].
      correct: false
    - text: Бо в слові є м'який знак.
      correct: false
    explanation: Перед губним стоїть інший кореневий приголосний (збіг св).
  - prompt: Чому слово цвях пишеться без знака?
    options:
    - text: Через збіг двох приголосних цв перед я.
      correct: true
    - text: Бо цвях — це виняток з апострофом.
      correct: false
    - text: Бо звук [ц] завжди м'який.
      correct: false
    explanation: Збіг приголосних цв не потребує роздільного знака.
  - prompt: Яка помилка є типовою для слова ло́жка?
    options:
    - text: Вставляння вигаданого м'якого знака після л.
      correct: true
    - text: Написання апострофа після ж.
      correct: false
    - text: Пропуск літери о.
      correct: false
    explanation: У слові ло́жка звук [л] твердий, не пишіть льожка.
  - prompt: Яка роль м'якого знака в слові день?
    options:
    - text: Пом'якшує кінцевий звук н.
      correct: true
    - text: Додає додатковий голосний звук.
      correct: false
    - text: Розділяє звуки як апостроф.
      correct: false
    explanation: М'який знак не має власного звука і пом'якшує попередній звук н.
- id: act-5
  type: divide-words
  title: Практика переносу слів
  instruction: Обери підготовлену модель переносу.
  items:
  - word: Мар'я́на
    answer: Мар'-яна
  - word: дерев'я́ний
    answer: дере-в'яний
  - word: бур'я́н
    answer: бур'-ян
  - word: па́льці
    answer: паль-ці
- id: act-203
  type: fill-in
  title: Встав знак або залиш пропуск
  instruction: Обери ь, апостроф або без знака.
  items:
  - sentence: Свіжий бур_як росте на городі.
    answer: без знака
    options:
    - без знака
    - ''''
    - ь
    explanation: Буря́к пишеться без знака.
  - sentence: На полі виріс зелений бур_ян.
    answer: ''''
    options:
    - ''''
    - без знака
    - ь
    explanation: Бур'я́н потребує апострофа після р.
  - sentence: Сьогодні в нашій родині велике св_ято.
    answer: без знака
    options:
    - без знака
    - ''''
    - ь
    explanation: Свя́то пишеться без апострофа.
  - sentence: У дерев'яну дошку вбито залізний цв_ях.
    answer: без знака
    options:
    - без знака
    - ''''
    - ь
    explanation: Цвях пишеться без знака.
  - sentence: У моєї подруги Мар_яни гарне ім'я.
    answer: ''''
    options:
    - ''''
    - ь
    - без знака
    explanation: Мар'я́на потребує апострофа після р.
  - sentence: У кімнаті стоїть міцний дерев_яний стіл.
    answer: ''''
    options:
    - ''''
    - ь
    - без знака
    explanation: Дерев'я́ний пишеться з апострофом після в.
workbook:
- id: act-w3
  type: error-correction
  title: Виправ усі пастки
  instruction: Обери правильну українську форму.
  items:
  - sentence: Не пиши сімя без апо́строфа.
    error: сімя
    correction: сім'я́
    options:
    - сім'я́
    - сімя
    explanation: У слові сім'я́ потрібен апо́строф.
  - sentence: Не пиши пять без апо́строфа.
    error: пять
    correction: п'ять
    options:
    - п'ять
    - пять
    explanation: У слові п'ять потрібен апо́строф.
  - sentence: Не пиши бурян без апо́строфа.
    error: бурян
    correction: бур'я́н
    options:
    - бур'я́н
    - бурян
    explanation: У слові бур'я́н потрібен апо́строф після р.
  - sentence: День — не пиши ден.
    error: ден
    correction: день
    options:
    - день
    - ден
    explanation: День потребує м'якого знака.
  - sentence: Не пиши св'ято з апо́строфом.
    error: св'ято
    correction: свя́то
    options:
    - свя́то
    - св'ято
    explanation: У слові свя́то немає апо́строфа.
  - sentence: Не пиши льожка з вигаданим м'яки́м знаком.
    error: льожка
    correction: ло́жка
    options:
    - ло́жка
    - льожка
    explanation: Ло́жка не має м'якого знака після л.
- id: act-w4
  type: true-false
  title: Факти про знаки
  instruction: 'Обери: правда чи неправда.'
  items:
  - statement: Ь не має власного звука.
    correct: true
    explanation: Він пом'якшує попередній при́голосний.
  - statement: Апо́строф тримає попередній при́голосний твердим.
    correct: true
    explanation: Він відділяє при́голосний від йотованої голосної.
  - statement: Ї іноді мовчить.
    correct: false
    explanation: Ї завжди читаємо як [йі].
  - statement: Свя́то має апо́строф.
    correct: false
    explanation: Свя́то — модельне слово без апо́строфа.
- id: act-w201
  type: group-sort
  title: Розподіли за ознакою знака
  instruction: Розподіли слова на три групи відповідно до написання.
  groups:
  - label: З м'яким знаком
    items:
    - день
    - кінь
    - сіль
    - па́льці
  - label: З апострофом
    items:
    - бур'я́н
    - Мар'я́на
    - дерев'я́ний
    - здоро́в'я
  - label: Без знака
    items:
    - буря́к
    - свя́то
    - цвях
    - ло́жка
- id: act-w202
  type: divide-words
  title: Поділи слова для переносу
  instruction: Обери правильний поділ слова для переносу з рядка в рядок.
  items:
  - word: Мар'я́на
    answer: Мар'-яна
  - word: дерев'я́ний
    answer: дере-в'яний
  - word: бур'я́н
    answer: бур'-ян
  - word: па́льці
    answer: паль-ці
  - word: мале́нький
    answer: ма-лень-кий
  - word: сього́дні
    answer: сьо-годні
- id: act-w203
  type: fill-in
  title: Додай пропущений знак
  instruction: Встав правильний знак у поданих реченнях.
  items:
  - sentence: На городі росте солодкий бур_як.
    answer: без знака
    options:
    - без знака
    - ''''
    - ь
    explanation: Буря́к пишеться без апострофа.
  - sentence: Біля тину росте бур_ян.
    answer: ''''
    options:
    - ''''
    - без знака
    - ь
    explanation: Бур'я́н пишеться з апострофом.
  - sentence: Мар_яна читає нову книжку.
    answer: ''''
    options:
    - ''''
    - без знака
    - ь
    explanation: Мар'я́на пишеться з апострофом.
  - sentence: На столі лежить залізний цв_ях.
    answer: без знака
    options:
    - без знака
    - ''''
    - ь
    explanation: Цвях пишеться без апострофа.
  - sentence: Бажаю вам міцного здоров_я.
    answer: ''''
    options:
    - ''''
    - без знака
    - ь
    explanation: Здоро́в'я пишеться з апострофом після в.
  - sentence: Ось мален_кий дерев'яний стілець.
    answer: ь
    options:
    - ь
    - ''''
    - без знака
    explanation: Мале́нький пишеться з м'яким знаком після н.
- id: act-w204
  type: match-up
  title: З'єднай слово та перенос
  instruction: З'єднай повне слово з його моделлю переносу.
  pairs:
  - left: Мар'я́на
    right: Мар'-яна
  - left: дерев'я́ний
    right: дере-в'яний
  - left: бур'я́н
    right: бур'-ян
  - left: па́льці
    right: паль-ці
  - left: мале́нький
    right: ма-лень-кий
  - left: сього́дні
    right: сьо-годні
- id: act-w205
  type: unjumble
  title: Склади речення
  instruction: Розташуй слова у правильному порядку, щоб утворити речення.
  items:
  - words:
    - Сього́дні
    - весе́ле
    - свя́то.
    answer: Сього́дні весе́ле свя́то.
  - words:
    - Це
    - міцни́й
    - дерев'я́ний
    - стіл.
    answer: Це міцни́й дерев'я́ний стіл.
  - words:
    - Мар'я́на
    - готу́є
    - черво́ний
    - буря́к.
    answer: Мар'я́на готу́є черво́ний буря́к.
  - words:
    - На
    - столі́
    - лежи́ть
    - вели́ка
    - ло́жка.
    answer: На столі́ лежи́ть вели́ка ло́жка.
  - words:
    - Бажа́ю
    - вам
    - міцно́го
    - здоро́в'я.
    answer: Бажа́ю вам міцно́го здоро́в'я.
  - words:
    - Сього́дні
    - чудо́вий
    - і
    - те́плий
    - день.
    answer: Сього́дні чудо́вий і те́плий день.


## vocabulary.yaml

- lemma: буря́к
  translation: beetroot
  pos: noun
  usage: Буря́к.
- lemma: бур'я́н
  translation: weed
  pos: noun
  usage: Бур'я́н.
- lemma: свя́то
  translation: holiday
  pos: noun
  usage: Свя́то.
- lemma: цвях
  translation: nail
  pos: noun
  usage: Цвях.
- lemma: мале́нький
  translation: small
  pos: adjective
  usage: Мале́нький знак.
- lemma: сього́дні
  translation: today
  pos: adverb
  usage: Сього́дні свя́то.
- lemma: ло́жка
  translation: spoon
  pos: noun
  usage: Ло́жка.
- lemma: Мар'я́на
  translation: Mariana
  pos: proper noun
  usage: Мар'я́на.
- lemma: дерев'я́ний
  translation: wooden
  pos: adjective
  usage: Дерев'я́ний стіл.
- lemma: па́льці
  translation: fingers
  pos: noun
  usage: Па́льці.
- lemma: здоро́в'я
  translation: health
  pos: noun
  usage: Здоро́в'я.
- lemma: день
  translation: day
  pos: noun
  usage: Сьогодні гарний день.


## resources.yaml

- title: Большакова, 2 клас, p. 58-59
  role: textbook
  source: Большакова, 2 клас, стор. 58-59
  notes: Apostrophe as hard consonant + [йа], and transfer models Мар'-яна / Дере-в'яний.
- title: Вашуленко, 3 клас, p. 90
  role: textbook
  source: Вашуленко, 3 клас, стор. 90
  notes: 'Line-break rule: apostrophe is not separated from the previous letter.'
- title: Захарійчук, 1 клас (НУШ 2025), p. 97
  role: textbook
  source: Захарійчук, 1 клас (НУШ 2025), стор. 97
  notes: 'Plan reference: basic apostrophe rule before я, ю, є, ї.'


## lesson-3
## module.md

## Далі

**Далі** means next. Go to Vocabulary and Activities; those drills reuse the
same six contrast words: **день**, **сім'я́**, **буря́к**, **бур'я́н**,
**свя́то**, **цвях**.

Віта́ємо на підсумко́вому уро́ці пе́ршого мо́дуля — welcome to the concluding lesson of the first module. У пе́рших двох уро́ках ми рете́льно розібра́ли два головні́ зна́ки украї́нської абе́тки — in the first two lessons we carefully analyzed the two main signs of the Ukrainian alphabet: **м'яки́й знак** *(soft sign)* та **апо́строф** *(apostrophe)*. Тепе́р час зібра́ти всі знання́ в єди́ну чітку́ систе́му — now it is time to assemble all knowledge into a single clear system.

Повто́римо три фундамента́льні контра́сти, які́ ви вже вмі́єте розпізнава́ти на слух та на письмі́ — let us review the three fundamental contrasts that you already know how to recognize by ear and in writing:

1. **М'яки́й знак (ь) пом'я́кшує при́голосний** *(soft sign softens the consonant)*:
   У слова́х **день**, **кінь**, **сіль**, **вчи́тель** м'яки́й знак не вимовля́ється як окре́мий звук, а ро́бить попере́дній при́голосний м'яки́м — in the words **день**, **кінь**, **сіль**, **вчи́тель**, the soft sign is not pronounced as a separate sound, but makes the preceding consonant soft.

2. **Апо́строф (') застеріга́є від пом'я́кшення та розділя́є зву́ки** *(apostrophe prevents softening and separates sounds)*:
   У слова́х **сім'я́**, **м'я́со**, **п'ять**, **комп'ю́тер**, **бур'я́н** апо́строф трима́є попере́дній губни́й звук або `[р]` тверди́м, а насту́пна лі́тера **я**, **ю**, **є**, **ї** чита́ється розді́льно зі зву́ком `[й]` — in the words **сім'я́**, **м'я́со**, **п'ять**, **комп'ю́тер**, **бур'я́н**, the apostrophe keeps the preceding labial sound or `[r]` hard, and the following letter **я**, **ю**, **є**, **ї** is read separately with the sound `[й]`.
   Як зазначено в авторитетному шкільному підручнику: «Апостроф позначає роздільну вимову твердого приголосного та звуків [йа], [йу], [йе], [йі]» (quoted from: Большакова, 2 клас, p. 58-59).
   А також базове правило: «Апостроф пишеться після букв б, п, в, м, ф, р перед я, ю, є, ї» (quoted from: Захарійчук, 1 клас (НУШ 2025), p. 97).

3. **Збіг при́голосних перед я без апо́строфа** *(consonant cluster before ya without apostrophe)*:
   У слова́х **свя́то** та **цвях** пе́ред губни́м зву́ком `[в]` стої́ть інший при́голосний (**с** або **ц**), тому́ апо́строф не пи́шеться — in the words **свя́то** and **цвях**, before the labial sound `[v]` stands another consonant (**s** or **ts**), so no apostrophe is written.

4. **Зли́та вимо́ва м'яко́го зву́ка без зна́ків** *(smooth pronunciation of a soft sound without signs)*:
   У сло́ві **буря́к** лі́тера **р** сама́ пом'я́кшується пе́ред **я**, без жо́дного апо́строфа — in the word **буря́к**, the letter **r** itself softens before **ya**, without any apostrophe.

Порівня́льна табли́ця підсумко́вих моде́лей — summary comparative table:

| Моде́ль — Model | При́клад — Example | Вимо́ва — Pronunciation | Пра́вило — Rule |
| --- | --- | --- | --- |
| Знак м'я́кшення | **день**, **сіль** | `[ден']`, `[с'іл']` | м'яки́й кінце́вий звук; нема́є окре́мого зву́ка |
| Розді́льний апо́строф | **бур'я́н**, **сім'я́** | `[бур-йан]`, `[с'ім-йа]` | тверди́й при́голосний + чітке́ `[йа]` |
| Збіг при́голосних | **свя́то**, **цвях** | `[св'а-то]`, `[цв'ах]` | корінни́й збіг св/цв перед я без апо́строфа |
| М'яки́й звук без зна́ка | **буря́к** | `[бу-р'ак]` | р пом'я́кшується перед я; нема́є апо́строфа |

<!-- INJECT_ACTIVITY: act-301 -->

### Пра́вила перено́су слів — Word Division Rules

Коли́ ви пи́шете те́ксти від руки́ або чита́єте книжки́, ду́же важли́во зна́ти прави́льні моде́лі перено́су — when you write texts by hand or read books, it is very important to know the correct word division models:
«При переносі слів апостроф і знак м'якшення не відокремлюються від попередньої букви» (quoted from: Вашуленко, 3 клас, p. 90).

Запам'ята́йте дві головні́ моде́лі перено́су — remember two main division models:
- **М'яки́й знак трима́ється з лі́терою перед ним** *(soft sign stays with the letter before it)*: **паль-ці**, **ма-лень-кий**, **вчи-тель**. Ніко́ли не перено́сьте «ь» на нови́й рядо́к окре́мо — never carry "ь" to a new line alone.
- **Апо́строф трима́ється з лі́терою перед ним** *(apostrophe stays with the letter before it)*: **бур'-ян**, **Мар'-яна**, **дере-в'яний**. Не відрива́йте апо́строф від лі́тери перед ним — do not detach the apostrophe from the letter before it.

<!-- INJECT_ACTIVITY: act-302 -->

### Діало́г: Підсумко́ва самопереві́рка — Concluding Self-Check Dialogue

Послу́хайте коро́тку розмо́ву двох дру́зів, які́ підбива́ють підсу́мки пе́ршого мо́дуля — listen to a short conversation between two friends summarizing the first module:

> **Тара́с**: Приві́т! Ми вже до́бре зна́ємо, як чита́ти особли́ві зна́ки? *(Hi! Do we already know well how to read the special signs?)*
> **Мар'я́на**: Так! Пе́рше пра́вило: знак ь пом'я́кшує при́голосний у слова́х день та сіль. *(Yes! The first rule: sign ь softens the consonant in the words день and сіль.)*
> **Тара́с**: А дру́ге пра́вило — про апо́строф? *(And the second rule — about the apostrophe?)*
> **Мар'я́на**: Апо́строф пи́шемо після б, п, в, м, ф, р перед я, ю, є, ї: сім'я́, м'я́со, бур'я́н. *(We write apostrophe after b, p, v, m, f, r before ya, yu, ye, yi: сім'я́, м'я́со, бур'я́н.)*
> **Тара́с**: А тре́тє — слова́ без зна́ка? *(And the third — words without a sign?)*
> **Мар'я́на**: Са́ме так: буря́к ма́є м'яки́й звук `[р']`, а свя́то та цвях ма́ють збіг при́голосних! *(Exactly so: буря́к has soft sound `[r']`, and свя́то and цвях have a consonant cluster!)*
> **Тара́с**: Чудо́во! Тепе́р ми вмі́ємо чита́ти всі ці слова́ пра́вильно. *(Wonderful! Now we know how to read all these words correctly.)*

Розбі́р ре́плік розмо́ви — breakdown of the dialogue turns:

| Украї́нська ре́пліка — Ukrainian turn | Англі́йська опо́ра — English support | Що помі́тити — What to notice |
| --- | --- | --- |
| **Приві́т! Ми вже до́бре зна́ємо, як чита́ти особли́ві зна́ки?** | Hi! Do we already know well how to read the special signs? | дру́жнє запита́ння для переві́рки знань |
| **Так! Пе́рше пра́вило: знак ь пом'я́кшує при́голосний у слова́х день та сіль.** | Yes! The first rule: sign ь softens the consonant in the words день and сіль. | м'яки́й знак ді́є наза́д на попере́дній при́голосний |
| **А дру́ге пра́вило — про апо́строф?** | And the second rule — about the apostrophe? | перехі́д до дру́гого головно́го зна́ка |
| **Апо́строф пи́шемо після б, п, в, м, ф, р перед я, ю, є, ї: сім'я́, м'я́со, бур'я́н.** | We write apostrophe after b, p, v, m, f, r before ya, yu, ye, yi: сім'я́, м'я́со, бур'я́н. | каноні́чна губна́ моде́ль + р |
| **А тре́тє — слова́ без зна́ка?** | And the third — words without a sign? | контро́льний контра́ст мо́дуля |
| **Са́ме так: буря́к ма́є м'яки́й звук `[р']`, а свя́то та цвях ма́ють збіг при́голосних!** | Exactly so: буря́к has soft sound `[r']`, and свя́то and цвях have a consonant cluster! | безпе́чні рі́шення без механі́чних помило́к |
| **Чудо́во! Тепе́р ми вмі́ємо чита́ти всі ці слова́ пра́вильно.** | Wonderful! Now we know how to read all these words correctly. | впе́внений підсу́мок пра́ктики |

<!-- INJECT_ACTIVITY: act-303 -->

<!-- INJECT_ACTIVITY: act-304 -->

<!-- INJECT_ACTIVITY: act-305 -->

### Па́м'ятка типо́вих помило́к — Common Pitfalls Reminder

Під час письмо́вої та у́сної пра́ктики пам'ята́йте про ці чоти́ри типо́ві па́стки — during written and oral practice, remember these four common pitfalls:
- **Не губі́ть апо́строф** *(do not drop the apostrophe)*: пиші́ть **сім'я́**, **м'я́со**, **п'ять**, **комп'ю́тер** *(write сім'я, м'ясо, п'ять, комп'ютер)*, а не «сімя» чи «пять» *(not сімя or пять)*.
- **Не вставля́йте зайвий апо́строф** *(do not insert extra apostrophe)*: пиші́ть **свя́то** та **цвях** без апо́строфа *(write свято and цвях without apostrophe)*, тому́ що збіг двох при́голосних *(because consonant cluster)* перед я виключа́є розді́льний знак *(before ya excludes separation sign)*.
- **Не забува́йте м'яки́й знак** *(do not forget the soft sign)*: пиші́ть **день**, **кінь**, **сіль**, **вчи́тель** *(write день, кінь, сіль, вчитель)* із м'яки́м знаком на кінці́ *(with soft sign at the end)*.
- **Не вига́дуйте пом'я́кшення** *(do not invent softening)*: у сло́ві **ло́жка** звучи́ть тверди́й звук `[л]` *(in ложка sounds hard [l])*, ніко́ли не додаючи́ ви́гаданий м'яки́й знак *(never adding invented soft sign)*.

### Підсумок модуля — Module summary

- **Впізнава́ти зна́ки — Recognize the signs**: distinguish the soft sign (**ь**) and the apostrophe (**'**) in printed Ukrainian words without confusing their visual shapes.
- **Розрізня́ти контра́ст — Distinguish the core contrast**: understand why **буря́к** has a soft consonant without an apostrophe, while **бур'я́н** keeps the consonant hard followed by a distinct `[йа]`.
- **Уника́ти типо́вих пасто́к — Avoid common traps**: remember that **свя́то** and **цвях** do not take an apostrophe, and never insert an invented soft sign into **ло́жка**.
- **Пра́вильно перено́сити слова́ — Divide words accurately**: keep **ь** and the apostrophe firmly attached to the preceding letter (**паль-ці**, **бур'-ян**, **Мар'-яна**, **дере-в'яний**).
- **Впе́внено чита́ти вго́лос — Read aloud with confidence**: pronounce soft consonants softly (**день**, **сіль**) and iotated vowels after apostrophes with a clear `[й]` sound (**сім'я́**, **комп'ю́тер**).


## activities.yaml

inline:
- id: act-301
  type: match-up
  title: Головні контрасти модуля
  instruction: З'єднай кожне слово з правильним описом вимови.
  pairs:
  - left: день
    right: пом'якшення кінцевого н завдяки знаку ь
  - left: сім'я́
    right: твердий звук м та окреме звучання йа
  - left: буря́к
    right: м'який звук р перед літерою я без апострофа
  - left: бур'я́н
    right: твердий звук р та чітке роздільне йа
  - left: свя́то
    right: збіг приголосних св без роздільного знака
  - left: комп'ю́тер
    right: роздільна вимова твердого п та звуків йу
- id: act-302
  type: quiz
  title: Підсумковий тест на розпізнавання знаків
  instruction: Обери правильне пояснення для кожного випадку.
  items:
  - prompt: Чому в слові бур'я́н пишеться апостроф?
    options:
    - text: Бо після твердого р перед я чути роздільний звук [й].
      correct: true
    - text: Бо літера р пом'якшується перед я.
      correct: false
    - text: Бо апостроф пом'якшує літеру р.
      correct: false
    explanation: Апостроф зберігає приголосний твердим перед йотованою голосною.
  - prompt: Яка роль знака ь у слові день?
    options:
    - text: Він пом'якшує попередній приголосний звук [н].
      correct: true
    - text: Він додає окремий голосний звук [і].
      correct: false
    - text: Він робить слово довшим без зміни звука.
      correct: false
    explanation: М'який знак не має власного звука, він лише вказує на м'якість.
  - prompt: Чому в слові свя́то немає апострофа?
    options:
    - text: Перед губним звуком [в] є приголосний [с], тому апостроф не пишеться.
      correct: true
    - text: Бо літера я завжди пом'якшує звук [в].
      correct: false
    - text: Бо це виняток з м'яким знаком.
      correct: false
    explanation: Після збігу приголосних перед я апостроф не пишеться.
  - prompt: Як правильно перенести слово паль-ці?
    options:
    - text: паль-ці (знак ь залишається з попередньою літерою)
      correct: true
    - text: па-льці (знак ь переходить до наступного складу)
      correct: false
    - text: пальц-і (літеру і залишаємо окремо)
      correct: false
    explanation: Знак м'якшення при переносі залишається з попередньою літерою.
  - prompt: Як правильно перенести слово бур'-ян?
    options:
    - text: бур'-ян (апостроф не відривається від літери р)
      correct: true
    - text: бу-р'ян (літера р з апострофом переходить на новий рядок)
      correct: false
    - text: бур-'ян (апостроф переноситься на новий рядок)
      correct: false
    explanation: Апостроф ніколи не відривається від попередньої літери.
  - prompt: Яка вимова правильна для слова м'я́со?
    options:
    - text: З твердим звуком [м] та роздільним початком [йа].
      correct: true
    - text: З м'яким звуком [м'] без звука [й].
      correct: false
    - text: З довгим звуком [і] між приголосним та голосним.
      correct: false
    explanation: Апостроф розділяє твердий звук [м] і йотовану голосну [йа].
- id: act-303
  type: fill-in
  title: Встав пропущений знак
  instruction: Заповни пропуск відповідним знаком або вибери варіант без знака.
  items:
  - sentence: Сього_дні гарний день.
    answer: ь
    options:
    - ь
    - ''''
    - без знака
  - sentence: Моя сім_я велика.
    answer: ''''
    options:
    - ''''
    - ь
    - без знака
  - sentence: У полі росте бур_ян.
    answer: ''''
    options:
    - ''''
    - ь
    - без знака
  - sentence: Веселе св_ято зібрало друзів.
    answer: без знака
    options:
    - без знака
    - ''''
    - ь
  - sentence: Мален_кий кінь стоїть у дворі.
    answer: ь
    options:
    - ь
    - ''''
    - без знака
  - sentence: Гострий цв_ях лежить на столі.
    answer: без знака
    options:
    - без знака
    - ''''
    - ь
- id: act-304
  type: divide-words
  title: Підсумковий поділ слів для переносу
  instruction: Обери правильну модель переносу слова з одного рядка на інший.
  items:
  - word: бур'я́н
    answer: бур'-ян
  - word: па́льці
    answer: паль-ці
  - word: Мар'я́на
    answer: Мар'-яна
  - word: дерев'я́ний
    answer: дере-в'яний
  - word: мале́нький
    answer: ма-лень-кий
  - word: вчи́тель
    answer: вчи-тель
- id: act-305
  type: true-false
  title: Швидка перевірка правил
  instruction: Визнач, чи твердження є правильним.
  items:
  - statement: У слові день м'який знак вимовляється як окремий звук [і].
    correct: false
    explanation: М'який знак не має власного звука й лише пом'якшує приголосний.
  - statement: У слові бур'ян апостроф показує роздільну вимову звуків.
    correct: true
    explanation: Звук [р] залишається твердим, а після нього звучить [йа].
  - statement: У слові свято пишеться апостроф після літери в.
    correct: false
    explanation: Через збіг двох приголосних св перед я апостроф не пишеться.
  - statement: У слові сім'я є апостроф після літери м.
    correct: true
    explanation: Після губного [м] перед я завжди пишеться апостроф.
  - statement: У слові ложка потрібно писати м'який знак.
    correct: false
    explanation: Ложка має твердий звук [л] і не має м'якого знака.
  - statement: При переносі слів апостроф ніколи не відривається від літери перед
      ним.
    correct: true
    explanation: Апостроф завжди залишається з попередньою літерою.
workbook:
- id: act-w5
  type: fill-in
  title: Додай знак у нових словах
  instruction: Обери ь, апо́строф або без знака.
  items:
  - sentence: бур_ян
    answer: ''''
    options:
    - ''''
    - ь
    - без знака
  - sentence: комп_ютер
    answer: ''''
    options:
    - ''''
    - ь
    - без знака
  - sentence: ім_я
    answer: ''''
    options:
    - ''''
    - ь
    - без знака
  - sentence: У слові мален_кий потрібен ____.
    answer: ь
    options:
    - ь
    - ''''
    - без знака
  - sentence: У слові цвях правильний вибір — ____.
    answer: без знака
    options:
    - без знака
    - ''''
    - ь
- id: act-w6
  type: quiz
  title: Правильна форма
  instruction: Обери правильно написане слово.
  items:
  - prompt: Сім'я́ — яка форма правильна?
    options:
    - text: сім'я́
      correct: true
    - text: сімя
      correct: false
    explanation: Сім'я́ потребує апо́строфа.
  - prompt: День — яка форма правильна?
    options:
    - text: ден
      correct: false
    - text: день
      correct: true
    explanation: День потребує м'якого знака.
  - prompt: Слово без апо́строфа?
    options:
    - text: св'ято
      correct: false
    - text: свя́то
      correct: true
    explanation: У слові свя́то немає апо́строфа.
- id: act-w7
  type: odd-one-out
  title: Зайве за знаком
  instruction: Обери слово, яке не має такого самого знака, як інші.
  items:
  - words:
    - сім'я́
    - м'я́со
    - п'ять
    - буря́к
    answer: буря́к
    explanation: Буря́к без апо́строфа; інші слова мають апо́строф.
  - words:
    - день
    - кінь
    - сіль
    - свя́то
    answer: свя́то
    explanation: Свя́то без ь; інші слова мають м'який знак.
  - words:
    - буря́к
    - свя́то
    - цвях
    - бур'я́н
    answer: бур'я́н
    explanation: Бур'я́н має апо́строф; інші слова тут без знака.
- id: act-w301
  type: group-sort
  title: Класифікація знаків
  instruction: Розподіли слова за типом орфограми.
  groups:
  - label: М'який знак
    items:
    - день
    - кінь
    - сіль
    - вчи́тель
    - мале́нький
    - па́льці
  - label: Апостроф
    items:
    - сім'я́
    - м'я́со
    - п'ять
    - де́в'ять
    - комп'ю́тер
    - бур'я́н
  - label: Без знака
    items:
    - буря́к
    - свя́то
    - цвях
    - ло́жка
- id: act-w302
  type: match-up
  title: Підсумкові пари правил
  instruction: З'єднай кожне слово з правилом його вимови чи написання.
  pairs:
  - left: буря́к
    right: м'який звук [р'] перед я
  - left: бур'я́н
    right: твердий звук [р] та роздільне [йа]
  - left: свя́то
    right: збіг двох приголосних без апострофа
  - left: день
    right: м'який кінцевий звук [н'] завдяки ь
  - left: сім'я́
    right: твердий звук [м] та роздільне [йа]
  - left: па́льці
    right: м'який знак не відривається при переносі
- id: act-w303
  type: true-false
  title: Перевір свої знання
  instruction: Визнач, чи твердження є правильним.
  items:
  - statement: У слові буряк звук [р] є м'яким.
    correct: true
    explanation: Буква я після приголосного пом'якшує його.
  - statement: У слові свято потрібно писати апостроф.
    correct: false
    explanation: Після збігу приголосних св перед я апостроф не пишеться.
  - statement: М'який знак не має власного звука.
    correct: true
    explanation: Він лише вказує на м'якість попереднього приголосного.
  - statement: У слові бур'ян апостроф позначає роздільну вимову.
    correct: true
    explanation: Приголосний [р] залишається твердим, а далі звучить [йа].
  - statement: При переносі слів м'який знак можна перенести окремо на новий рядок.
    correct: false
    explanation: М'який знак завжди залишається з попередньою літерою.
  - statement: У слові ложка потрібно писати м'який знак після л.
    correct: false
    explanation: У слові ложка літера л позначає твердий звук без м'якого знака.


## vocabulary.yaml

- lemma: буря́к
  translation: beetroot
  pos: noun
  usage: Буря́к.
- lemma: бур'я́н
  translation: weed
  pos: noun
  usage: Бур'я́н.
- lemma: свя́то
  translation: holiday
  pos: noun
  usage: Свя́то.
- lemma: цвях
  translation: nail
  pos: noun
  usage: Цвях.
- lemma: день
  translation: day
  pos: noun
  usage: День.
- lemma: сім'я́
  translation: family
  pos: noun
  usage: Сім'я́.
- lemma: м'я́со
  translation: meat
  pos: noun
  usage: М'я́со.
- lemma: п'ять
  translation: five
  pos: numeral
  usage: П'ять.
- lemma: комп'ю́тер
  translation: computer
  pos: noun
  usage: Комп'ю́тер.
- lemma: кінь
  translation: horse
  pos: noun
  usage: Кінь.
- lemma: сіль
  translation: salt
  pos: noun
  usage: Сіль.
- lemma: вчи́тель
  translation: teacher
  pos: noun
  usage: Вчи́тель.
- lemma: мале́нький
  translation: small
  pos: adjective
  usage: Мале́нький знак.
- lemma: сього́дні
  translation: today
  pos: adverb
  usage: Сього́дні свя́то.


## resources.yaml

- title: Большакова, 2 клас, p. 58-59
  role: textbook
  source: Большакова, 2 клас, стор. 58-59
  notes: Apostrophe as hard consonant + [йа], and transfer models Мар'-яна / Дере-в'яний.
- title: Вашуленко, 3 клас, p. 90
  role: textbook
  source: Вашуленко, 3 клас, стор. 90
  notes: 'Line-break rule: apostrophe is not separated from the previous letter.'
- title: Захарійчук, 1 клас (НУШ 2025), p. 97
  role: textbook
  source: Захарійчук, 1 клас (НУШ 2025), стор. 97
  notes: 'Plan reference: basic apostrophe rule before я, ю, є, ї.'


## Task

Review the assigned dimension `pedagogical` and return the required JSON object now.
No preamble, no markdown, no questions.
