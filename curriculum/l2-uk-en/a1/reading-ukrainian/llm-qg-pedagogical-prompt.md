{"independent_effort": "medium", "independent_model": "gpt-6-astra", "independent_reviewer": "codex-tools", "self_reviewer": "agy-tools", "writer": {"effort": "high", "model": "gemini-3.8-flash-high", "writer": "agy-tools"}}
V7 UPGRADE review of the complete module across all lessons. Review the published lesson unit, not a fresh module build. No wiki packet or plan rewrite applies. Assess preservation, lesson_split, coherent progression, first-use cumulative vocabulary, final module closure (`Підсумок модуля — Module summary` on the last lesson, not Module completion), no named narrator, marked attributed quotations with Resources entries, no ```text learner examples, and side-by-side English support for added A1 Ukrainian passages of three or more sentences. SOURCES AUDIT: VESUM/`sources` is why the Ukrainian is trustworthy (gender, government, real examples — not Russian calques). This corpus trains a Ukrainian LLM and tests whether the sources tools actually get used. No tool calls = fail. Ungrounded morphology = fail. Judge the current dimension independently using exact quotes from these artifacts. Stress annotation follows review. Lesson map:
{"lessons": [{"n": 1, "title": "Читаємо слова", "sections": ["Склади", "Голосні літери", "Читаємо слова"], "minutes": 60, "word_target": 550, "activities": {"total": 10, "inline": [4, 6], "workbook": [6, 9]}, "unverified_stress": [], "unverified_lemmas": []}, {"n": 2, "title": "Друк, зошит, перевірка", "sections": ["Пастки читання", "Друк, зошит, перевірка"], "minutes": 60, "word_target": 550, "activities": {"total": 10, "inline": [4, 6], "workbook": [6, 9]}, "unverified_stress": [], "unverified_lemmas": []}, {"n": 3, "title": "Далі", "sections": ["Далі"], "minutes": 60, "word_target": 550, "activities": {"total": 10, "inline": [4, 6], "workbook": [6, 9]}, "unverified_stress": [], "unverified_lemmas": []}], "closes_module": 3, "provenance": [{"placement": "inline", "index": 0, "new_id": "act-1", "lesson": 1}, {"placement": "inline", "index": 1, "new_id": "act-2", "lesson": 1}, {"placement": "inline", "index": 2, "new_id": "act-3", "lesson": 1}, {"placement": "inline", "index": 3, "new_id": "act-4", "lesson": 2}, {"placement": "workbook", "index": 0, "new_id": "act-w1", "lesson": 1}, {"placement": "workbook", "index": 1, "new_id": "act-w2", "lesson": 1}, {"placement": "workbook", "index": 2, "new_id": "act-w3", "lesson": 2}, {"placement": "workbook", "index": 3, "new_id": "act-w4", "lesson": 2}, {"placement": "workbook", "index": 4, "new_id": "act-w5", "lesson": 3}, {"placement": "workbook", "index": 5, "new_id": "act-5", "lesson": 3}], "items_min_exempt": [{"id": "act-4", "reason": "4-item original activity preserved from baseline"}, {"id": "act-w2", "reason": "4-item original activity preserved from baseline"}, {"id": "act-w3", "reason": "4-item original activity preserved from baseline"}, {"id": "act-w4", "reason": "5-item original activity preserved from baseline"}, {"id": "act-w5", "reason": "5-item original activity preserved from baseline"}, {"id": "act-5", "reason": "3-item original activity preserved from baseline"}], "proper_names": []}

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
  "slug": "reading-ukrainian",
  "wiki_path": "/home/ops/learn-ukrainian/.worktrees/builds/a1-reading-ukrainian-20260914-120044/wiki/pedagogy/a1/reading-ukrainian.md",
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
    },
    {
      "id": "step-6",
      "obligation_id": "step-6",
      "category": "sequence_steps",
      "summary": "Крок 6."
    }
  ],
  "l2_errors": [
    {
      "id": "err-1",
      "obligation_id": "err-1",
      "category": "l2_errors",
      "summary": "Use Один злитий африкат /d͡ʒ/ або /d͡z/ (схожий на звуки в англійських словах jeans чи kids)."
    },
    {
      "id": "err-2",
      "obligation_id": "err-2",
      "category": "l2_errors",
      "summary": "Use Пом'якшений приголосний + чистий голосний (наприклад, /dʲa/)."
    },
    {
      "id": "err-3",
      "obligation_id": "err-3",
      "category": "l2_errors",
      "summary": "Use Чітка і повна вимова [о] незалежно від того, падає на нього наголос чи ні."
    },
    {
      "id": "err-4",
      "obligation_id": "err-4",
      "category": "l2_errors",
      "summary": "Use Чітке пом'якшення фінального приголосного (/nʲ/)."
    },
    {
      "id": "err-5",
      "obligation_id": "err-5",
      "category": "l2_errors",
      "summary": "Use Роздільна вимова з чітким збереженням твердості попереднього приголосного і наступним повним /j/."
    }
  ],
  "phonetic_rules": [],
  "decolonization_bans": [
    {
      "id": "ban-1",
      "obligation_id": "ban-1",
      "category": "decolonization_bans",
      "summary": "Під час навчання читання та письма надзвичайно важливо повністю ізолювати учня від будь-якого впливу російської фонетичної чи графічної системи."
    },
    {
      "id": "ban-2",
      "obligation_id": "ban-2",
      "category": "decolonization_bans",
      "summary": "1."
    }
  ],
  "external_resources": []
}
```

### Implementation Map Contract

```text
Manifest obligations: 13.
Each row below is a pre-resolved slot the writer MUST fill at the artifact indicated by `artifact`, located by `location_hint`, populated using `treatment_template` as the structural blueprint.

- obligation_id: ban-1  (obligation_type: decolonization_ban)
  artifact: module.md
  location_hint: §Читання слів
  subtype: absence_required
  treatment_template:
    shape: module.md prose absent of any phrasing matching manifest_payload.rule (negative obligation: absence-of-pattern)
- obligation_id: ban-2  (obligation_type: decolonization_ban)
  artifact: module.md
  location_hint: §Голосні літери
  subtype: substance_required
  treatment_template:
    shape: module.md prose absent of any phrasing matching manifest_payload.rule (negative obligation: absence-of-pattern)
- obligation_id: err-1  (obligation_type: l2_error)
  artifact: activities.yaml
  location_hint: activities.yaml
  treatment_template:
    activity_stub: {"items": [], "sentence": "", "type": "error-correction"}
    expected_correction_value: Один злитий африкат /d͡ʒ/ або /d͡z/ (схожий на звуки в англійських словах jeans чи kids).
    expected_error_value: Вимова диграфів ДЖ і ДЗ як двох окремих, розірваних звуків ([д] + [ж]).
    shape: activities.yaml entry with fields {sentence, error, correction}
- obligation_id: err-2  (obligation_type: l2_error)
  artifact: activities.yaml
  location_hint: activities.yaml
  treatment_template:
    activity_stub: {"items": [], "sentence": "", "type": "error-correction"}
    expected_correction_value: Пом'якшений приголосний + чистий голосний (наприклад, /dʲa/).
    expected_error_value: Читання йотованих Я, Ю, Є після приголосного як [й] + голосний (наприклад, [д-й-а-к-у-й-у]).
    shape: activities.yaml entry with fields {sentence, error, correction}
- obligation_id: err-3  (obligation_type: l2_error)
  artifact: activities.yaml
  location_hint: activities.yaml
  treatment_template:
    activity_stub: {"items": [], "sentence": "", "type": "error-correction"}
    expected_correction_value: Чітка і повна вимова [о] незалежно від того, падає на нього наголос чи ні.
    expected_error_value: Редукція ненаголошеного [о] до [а] (акання).
    shape: activities.yaml entry with fields {sentence, error, correction}
- obligation_id: err-4  (obligation_type: l2_error)
  artifact: activities.yaml
  location_hint: activities.yaml
  treatment_template:
    activity_stub: {"items": [], "sentence": "", "type": "error-correction"}
    expected_correction_value: Чітке пом'якшення фінального приголосного (/nʲ/).
    expected_error_value: Ігнорування м'якого знака наприкінці слова (наприклад, вимова «ден» замість «день»).
    shape: activities.yaml entry with fields {sentence, error, correction}
- obligation_id: err-5  (obligation_type: l2_error)
  artifact: activities.yaml
  location_hint: activities.yaml
  treatment_template:
    activity_stub: {"items": [], "sentence": "", "type": "error-correction"}
    expected_correction_value: Роздільна вимова з чітким збереженням твердості попереднього приголосного і наступним повним /j/.
    expected_error_value: Ігнорування апострофа або його сприйняття лише як паузи без відтворення звука /j/.
    shape: activities.yaml entry with fields {sentence, error, correction}
- obligation_id: step-1  (obligation_type: sequence_step)
  artifact: module.md
  location_hint: §Шість чистих голосних фонем і відповідні літери.
  treatment_template:
    required_claim: Крок 1. Шість чистих голосних фонем і відповідні літери. Вводимо літери А, О, У, Е, И, І, які позначають шість простих голосних звуків (/a/, /ɛ/, /u/, /ɔ/, /i/, /ɪ/) . Важливо пояснити, що звук [і] додатково впливає на попередній приголосний, спричиняючи його пом'якшення . Студентам слід давати слова з чистими голосними, наприклад «мама» чи «молоко», щоб продемонструвати відкритість і чистоту звучання .
    shape: module.md section heading or in-prose step marker matching manifest_payload.heading at the position implied by manifest_payload.step_num
- obligation_id: step-2  (obligation_type: sequence_step)
  artifact: module.md
  location_hint: §Базові приголосні та складоподіл.
  treatment_template:
    required_claim: Крок 2. Базові приголосні та складоподіл. Після засвоєння голосних додаємо високочастотні приголосні. Відразу практикуємо поділ на склади за правилом Большакової: «У кожному складі обов'язково є голосний звук» . Учні повинні розуміти, що навіть один-єдиний голосний може утворювати окремий склад .
    shape: module.md section heading or in-prose step marker matching manifest_payload.heading at the position implied by manifest_payload.step_num
- obligation_id: step-3  (obligation_type: sequence_step)
  artifact: module.md
  location_hint: §Йотовані літери (Я, Ю, Є, Ї).
  treatment_template:
    required_claim: Крок 3. Йотовані літери (Я, Ю, Є, Ї). Ці чотири літери української абетки є справжніми «хамелеонами» . Їхня функція цілковито залежить від позиції. Спочатку слід навчити, що на початку слова, після іншого голосного або після апострофа чи м'якого знака вони позначають два звуки: приголосний /j/ плюс відповідний голосний . Потім пояснюємо їхню другу функцію: після приголосного літери Я, Ю, Є позначають один голосний звук і водночас м'якість попереднього приголосного . Наголошуємо, що літера Ї завжди позначає два звуки /ji/ без винятків .
    shape: module.md section heading or in-prose step marker matching manifest_payload.heading at the position implied by manifest_payload.step_num
- obligation_id: step-4  (obligation_type: sequence_step)
  artifact: module.md
  location_hint: §Знак м'якшення (Ь).
  treatment_template:
    required_claim: Крок 4. Знак м'якшення (Ь). Уводимо м'який знак, пояснюючи, що він узагалі не має власного звуку, а слугує виключно для пом'якшення (палаталізації) попереднього приголосного (наприклад, у словах «день», «осінь») .
    shape: module.md section heading or in-prose step marker matching manifest_payload.heading at the position implied by manifest_payload.step_num
- obligation_id: step-5  (obligation_type: sequence_step)
  artifact: module.md
  location_hint: §Апостроф.
  treatment_template:
    required_claim: Крок 5. Апостроф. Апостроф діє як графічна межа (розділювач), яка запобігає пом'якшенню попереднього приголосного і зберігає повне, тверде звучання наступної йотованої літери з чітким /j/ (як у словах «м'ясо», «сім'я») .
    shape: module.md section heading or in-prose step marker matching manifest_payload.heading at the position implied by manifest_payload.step_num
- obligation_id: step-6  (obligation_type: sequence_step)
  artifact: module.md
  location_hint: §Диграфи ДЖ і ДЗ.
  treatment_template:
    required_claim: Крок 6. Диграфи ДЖ і ДЗ. В останню чергу вводимо сполучення літер, що позначають один злитий звук: диграф ДЖ (/d͡ʒ/) як у слові «джерело», та диграф ДЗ (/d͡z/) як у слові «дзеркало» .
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
- Module: 2
- Slug: reading-ukrainian
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
- Over advisory ceiling words: 2558
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
- title: Склади
  word_budget:
    target: 250
    min: 225
    max: 275
- title: Голосні літери
  word_budget:
    target: 300
    min: 270
    max: 330
- title: Читання слів
  word_budget:
    target: 500
    min: 450
    max: 550
- title: Підсумок
  word_budget:
    target: 150
    min: 135
    max: 165
vocabulary_required:
- яблуко (apple) — Я at word start = [йа]
- молоко (milk) — 3 syllables, all simple vowels
- людина (person) — Л + Ю combination
- вулиця (street) — Ц sound practice
- столиця (capital) — Київ — столиця України
- каша (porridge) — Ш sound practice
- пісня (song) — softening by Я after consonant
vocabulary_optional: []
source_note: Full plan below is authoritative for points, activity hints, vocabulary,
  and references.
```

## Plan

```yaml
activity_hints:
- focus: 'Поділи слова на склади: мо-ло-ко, ап-те-ка, у-ні-вер-си-тет'
  items: 8
  type: divide-words
- focus: Порахуй склади — скільки голосних, стільки й складів
  items: 8
  type: count-syllables
- focus: 'З''єднай йотовані голосні з їхніми звуковими компонентами: Я=[й]+[а]'
  items: 6
  type: match-up
- focus: Прочитай слово і вибери його значення
  items: 6
  type: quiz
- focus: Яке слово зайве? — за кількістю складів (односкладове серед двоскладових)
  items: 6
  type: odd-one-out
- focus: Типові помилки L2 при читанні (mirror wiki "Типові помилки L2" table). З'єднайте
    слово з типом помилки, яку воно перевіряє.
  items:
  - день: 'Ігнорування м''якого знака: [ден] замість [ден′]'
  - сім'я: 'Злиття через апостроф: [сіма] замість [сімйа]'
  - дякую: 'Йотована після приголосного: [дйакуйу] замість [д''акуйу]'
  - Україна: '`Ї` → [і]: [Украіна] замість [Украйіна]'
  - борщ: '`Щ` → [ш]: [борш] замість [боршч]'
  - джміль: '`ДЖ` як два звуки: [д]-[жміль] замість [джміль]'
  - молоко: Читання по літерах замість по складах
  - огірок: Сплутування СКЛАДОПОДІЛУ з ПЕРЕНЕСЕННЯМ (складоподіл `о-гі-рок`; перенесення
      `огі-рок`, бо одна літера `о-` не може стояти окремо в рядку)
  type: match-up
changelog:
- changes:
  - Review-and-lock pass. Added lifecycle markers (lifecycle/reviewed_at/reviewed_by/review_notes)
    per docs/best-practices/wiki-plan-review-and-lock.md.
  - 'Added new match-up activity: reading-specific L2 error drill (8 items, mirrors
    wiki "Типові помилки L2" table — closes the wiki-plan drift on reading errors).'
  - 'Consolidated `references:` block: added Вашуленко, Кравцова textbook entries
    and back-references to both locked sibling wikis (reading-ukrainian + sounds-letters-and-hello).
    Previous bottom-of-file `references:` had only 3 Большакова/Захарійчук entries.'
  - Removed duplicate `references:` block at end of file (was a pre-existing inconsistency
    — duplicate YAML keys are unsafe and parser-dependent; PyYAML silently takes last-key-wins,
    which meant only the 3-entry tail block was reaching `validate_plans.py`, hiding
    the earlier block). The consolidated single block now carries all 7 entries.
  date: '2026-04-23'
  version: 1.3.0
connects_to:
- a1-003 (Особливі знаки)
content_outline:
- points:
  - 'Большакова, 1 клас, стор. 25: «У слові стільки складів, скільки голосних звуків.»
    Порахуй голосні — дізнаєшся кількість складів. Це правило ніколи не порушується.
    ма-ма (2 голосні = 2 склади), мо-ло-ко (3 голосні = 3 склади), банк (1 голосна
    = 1 склад).'
  - 'Як українські діти вчаться читати — складові ланцюжки: Починаємо з пари приголосний
    + голосний: М → ма, мо, му, ми. Потім навпаки: ам, ом, ум. Далі будуємо слова:
    ма-ма, мо-ло-ко. Це підхід "знизу вгору": звук → склад → слово. (Захарійчук 1
    клас, стор. 46; Большакова 1 клас, стор. 25)'
  - 'Звуковий аналіз слова (Большакова стор. 29): 1) Визначаю голосні звуки 2) Ділю
    слово на склади 3) Ставлю наголос 4) Позначаю приголосні звуки. Тест із підборіддям
    для підрахунку складів (Кравцова 2 клас, стор. 13): покладіть долоню під підборіддя,
    скажіть слово — кожен дотик підборіддя = один склад.'
  - 'Українська система позначення звуків (Захарійчук стор. 15): [●] голосний, [—]
    твердий приголосний, [=] м''який приголосний. Цього вчиться кожна українська дитина
    в 1 класі.'
  section: Склади
  words: 250
- points:
  - 'Повторення з модуля №1: 6 звуків, 10 літер. Тепер розберемо всі 10 окремо. Прості
    голосні (один звук кожна): А [а], О [о], У [у], Е [е], И [и], І [і]. Кожна позначає
    ОДИН стабільний звук — жодних сюрпризів.'
  - 'Йотовані голосні (два звуки або пом''якшення): Я = [йа] на початку слова (яблуко)
    або після голосного (моя). Після приголосного: пом''якшує його + [а] (пісня —
    Н пом''якшений). Ю = [йу] або пом''якшення + [у]. Є = [йе] або пом''якшення +
    [е]. Ї = ЗАВЖДИ [йі] — ніколи не пом''якшує. Лише на початку слова, після голосного
    або після апострофа. Унікальна для української мови.'
  - 'Критичні мінімальні пари: И проти І: кит проти кіт, дим проти дім. Послухайте
    відео Анни з правильною вимовою кожного з них — різниця тонка, але вона змінює
    значення.'
  section: Голосні літери
  words: 300
- points:
  - 'Застосовуйте складові ланцюжки до реальних слів. Не читайте по літерах — читайте
    по складах. Використовуйте звуковий аналіз: спочатку знайдіть голосні, поділіть
    на склади, потім об''єднайте. Приклад: книга — знайдіть голосні И, А → кни-га
    → прочитайте.'
  - 'Поступове ускладнення за українською класифікацією: односкладові (1 склад): дім,
    сон, ліс, дуб, хліб. двоскладові (2 склади): ма-ма, та-то, во-да, ру-ка, ха-та,
    ка-ша. трискладові (3 склади): ап-те-ка, мо-ло-ко, лю-ди-на, ву-ли-ця. багатоскладові
    (4+ склади): у-ні-вер-си-тет, біб-лі-о-те-ка, фо-то-гра-фі-я.'
  - 'Назви українських міст як практика читання: Ки-їв, Льві-в, О-де-са, Хар-ків,
    Дні-про, Пол-та-ва. Зверніть увагу на різну кількість складів та їхню структуру.'
  - 'Особливі буквосполучення, на які слід звернути увагу (анонс для модуля №3): Щ
    — це завжди [шч] — що, ще. Ь не має звуку — він пом''якшує: день, сіль, кінь.
    Апостроф розділяє: сім''я, м''ясо, п''ять. Вони будуть детально розібрані у модулі
    №3.'
  section: Читання слів
  words: 500
- points:
  - 'Самоперевірка: Як порахувати склади в українському слові? Назвіть 6 голосних
    звуків. Назвіть 4 йотовані голосні літери. Що робить Ь? Що робить апостроф? Прочитайте
    це слово: бібліотека — скільки в ньому складів?'
  section: Підсумок
  words: 150
focus: phonetics
grammar:
- 'Правило складоподілу: у слові стільки складів, скільки голосних звуків'
- 'Звуковий аналіз слова: визначити голосні → поділити на склади → наголос → приголосні'
- 'Складові ланцюжки: приголосний + голосний = склад (ма, мо, му)'
- 'Українська система позначення звуків: [●] голосний, [—] твердий приголосний, [=]
  м''який приголосний'
- Співвідношення: 10 голосних літер → 6 голосних звуків
- Йотовані голосні (Я, Ю, Є як два звуки або пом'якшення; Ї завжди [йі])
- 'Класифікація слів: односкладові, двоскладові, трискладові, багатоскладові'
- Ь, апостроф (ознайомлення — детально у модулі №3)
letter_module: true
level: A1
lifecycle: locked
module: a1-002
objectives:
- Вміти читати будь-яке українське слово, розпізнаючи звуки та об'єднуючи їх у склади
- Розуміти правило складоподілу — рахувати голосні, щоб порахувати склади
- Навчитися впевнено читати багатоскладові слова (не по літерах)
- Розуміти, як 10 голосних літер позначають 6 голосних звуків
pedagogy: PPP
phase: A1.1 [Звуки, літери та перший контакт]
plan_fixes:
- changes:
  - strip U+0301 from all string values (7 removals)
  date: '2026-04-24'
  trigger: Plan check rejected U+0301 combining acute stress marks in 7 place(s).
    Pipeline adds stress marks deterministically AFTER review; plans must be stress-free.
  version: 1.3.1
- changes:
  - add letter_module flag (true) — allows higher activity counts for letter-recognition
    coverage; word-count target unchanged
  date: '2026-04-25'
  ref: '#1550'
  trigger: Letter-driven module needs explicit exception class for activity-count
    gates and pedagogical-stage reviewer calibration (a1/2 in alphabet/orthography
    exception class with a1/1 and a1/3).
  version: 1.3.2
prerequisites:
- a1-001 (Звуки, літери та привіт)
references:
- notes: 'Правило складоподілу: «У слові стільки складів, скільки голосних звуків.»'
  title: Большакова, буквар 1 клас, стор. 25
- notes: Звуковий аналіз слова — як аналізувати звуки у слові.
  title: Большакова, буквар 1 клас, стор. 29
- notes: 'Позначення звуків: [•] для голосних, [–] для приголосних, [=] для м''яких.'
  title: Захарійчук 1 клас (НУШ 2025), стор. 13-15
- notes: Правила переносу, наголос як носій значення (сім'я/сім'я, обід/обід), йотовані
    голосні.
  title: Вашуленко, Українська мова 2 клас, стор. 23-27
- notes: Кінестетичний тест «долоня під підборіддям» для підрахунку складів.
  title: Кравцова, Українська мова 2 клас, стор. 13
- notes: Authoritative pedagogical brief — see Кроки 1–7 (sequencing), "Типові помилки
    L2" (reading-specific decoding errors — 8 rows), and Приклад 5 (partner-diagnostic
    drill closing the loop).
  title: 'Wiki: pedagogy/a1/reading-ukrainian (LOCKED 2026-04-23)'
- notes: Sibling wiki for sound-production; this wiki (reading-ukrainian) targets
    the decoding-from-print slice — intentional overlap on Ь/apostrophe/iotated/Щ/ДЖ/ДЗ,
    deliberate distinction in framing (production vs. decoding).
  title: 'Wiki: pedagogy/a1/sounds-letters-and-hello (LOCKED 2026-04-23)'
register: розмовний
review_notes: Review-and-lock pass for A1 scale batch input. See wiki/.reviews/pedagogy/a1/reading-ukrainian-review-LOCKED.md
  for the wiki-side report (5-dim, all ≥9); see PR body for the plan-side findings
  (pragmatic / Russianism / calque / contradiction / references / cross-pair drift).
  The plan was brought into alignment with the locked wiki by (a) adding a reading-specific
  L2 error-drill activity that mirrors the wiki's new "Типові помилки L2" table, (b)
  adding a `references:` block with a back-reference to the locked wiki, (c) adding
  lifecycle markers per docs/best-practices/wiki-plan-review-and-lock.md. No Russianisms,
  calques, or homoglyphs detected in plan prose; Latin-in-Cyrillic homoglyph scan
  is clean.
reviewed_at: '2026-04-23T00:00:00Z'
reviewed_by: claude-opus-4-7-xhigh-reading-ukrainian
sequence: 2
slug: reading-ukrainian
subtitle: Від літер до слів та речень
targets:
  new_grammar: []
  new_vocabulary:
  - яблуко
  - молоко
  - людина
  - вулиця
  - столиця
  - каша
  - пісня
  recycle_vocabulary: []
title: Читаємо українською
version: 1.3.2
vocabulary_hints:
  author_note: На А1 у цьому модулі всі слова (required + recommended) подаються як
    носії фонетичної практики — склади, наголос, йотовані, `ь`, апостроф, ДЖ/ДЗ, Ї,
    Щ. НЕ вводьте відмінкові парадигми, дієвідміну чи ступені порівняння — відмінки
    починаються з модуля №18 (знахідний). Кожне слово тут має одну словоформу, яку
    учень читає вголос і діагностує за таблицею «Типові помилки L2» (див. locked wiki,
    розділ після Словникового мінімуму).
  recommended:
  - університет (university) — long word practice
  - бібліотека (library) — 5 syllables
  - фотографія (photography) — long word with Ф
  - шоколад (chocolate) — Ш + О + К combination
  required:
  - яблуко (apple) — Я at word start = [йа]
  - молоко (milk) — 3 syllables, all simple vowels
  - людина (person) — Л + Ю combination
  - вулиця (street) — Ц sound practice
  - столиця (capital) — Київ — столиця України
  - каша (porridge) — Ш sound practice
  - пісня (song) — softening by Я after consonant
word_target: 1200

```

## Generated Content

## lesson-1
## module.md

# Читаємо українською

**ма — мо — му — ми. ма́ма. молоко́.** — syllables and first words.

Приві́т! In Module 1 you met Ukrainian letters and the word **склад**. Here
you turn that word into a reading tool. Printed Ukrainian comes first; English
support helps you check what your eyes already found.

For one listening pass before you read fast, open the public ULP <!-- source: ULP -->
[Ukrainian Alphabet guide](https://www.ukrainianlessons.com/ukrainian-alphabet/).
Use it only as listen-and-repeat support: do not download, transcribe, remix,
or reuse the audio. Listen for the vowel sound, point to the letter on this
page, then read the printed word.

Module 1 only previewed **склад**. This module teaches the counting rule:

**one vowel sound = one склад**

In print, count the letters that mark vowel sounds. Then split the word into
syllables and read it without guessing from another alphabet.

By the end, you can:

- count syllables by counting vowel sounds;
- read simple open syllables such as **ма**, **мо**, **му**, **ми**;
- keep the six simple vowel sounds clear;
- explain what **Я, Ю, Є, Ї** do at beginner level;
- read **ма́ма**, **молоко́**, **день**, **я́блуко**, **люди́на**, and
  **ву́лиця**;
- avoid the first reading traps: splitting **дж** and **дз**, ignoring **ь**,
  blurring **о**, and losing **й** in **ї**.

## Склади

**склад** — syllable.

Start every reading attempt with one Ukrainian question:

**Де голосні звуки?** — Where are the vowel sounds?

In Ukrainian, every syllable has a vowel sound. A single vowel can be a whole
syllable, and a consonant by itself cannot make a syllable.

| Слово́ | Letters that mark vowel sounds | Склади́ |
| --- | --- | --- |
| **день** | **е** | 1 |
| **ма́ма** | **а + а** | 2 |
| **молоко́** | **о + о + о** | 3 |
| **ву́лиця** | **у + и + я** | 3 |

Use a simple body check. Put a hand lightly under your chin and say the word
slowly. Each open vowel pulse makes the chin move. That movement is a
beginner check before you write or choose an answer.

Build from syllables instead of naming letters one by one:

| Letter path | Reading path |
| --- | --- |
| М + А | **ма** |
| М + О | **мо** |
| М + У | **му** |
| М + И | **ми** |

Then join syllables:

**ма + ма = ма́ма**

**мо + ло + ко = молоко́**

:::tip
**склад** — syllable. Find the vowel sound first. That is the anchor.
:::

<!-- INJECT_ACTIVITY: act-1 -->

Ukrainian children learn this rule from their very first school reader: «У слові стільки складів, скільки в ньому голосних звуків» (quoted from: Большакова, буквар 1 клас, p. 25). Each vowel forms the core of its own syllable beat.

<!-- INJECT_ACTIVITY: act-syllables-quiz -->

## Голосні лі́тери

**А О У Е И І** — six simple letters for vowel sounds.

The sounds are:

**[а] [о] [у] [е] [и] [і]**

Read them as clean sounds. In **молоко́**, every **о** stays **о**:

**мо-ло-ко́**

Say it slowly as three open beats, but keep the written word whole on the
page.

Now add the four other letters that mark vowel sounds:

**Я Ю Є Ї**

At beginner level, use this two-job rule:

| Лі́тера | At the start of a word or after a vowel/apostrophe | After a consonant |
| --- | --- | --- |
| **Я** | **[йа]** as in **я́блуко** | softens the consonant + **[а]** |
| **Ю** | **[йу]** | softens the consonant + **[у]** |
| **Є** | **[йе]** | softens the consonant + **[е]** |
| **Ї** | always **[йі]** | always **[йі]** |

**Ї** is not a softening letter. It is always two sounds: **[йі]**. In
**Украї́на**, read **ї** as **[йі]**.

Use three safe examples:

| Слово́ | English support | What to read |
| --- | --- | --- |
| **я́блуко** | apple | **я** starts the word: **[йа]** |
| **люди́на** | person | **ю** follows **л** and marks softness + **[у]** |
| **пі́сня** | song | **я** follows **н** and marks softness + **[а]** |

You do not need every phonetic detail yet. Look at the position of
**Я, Ю, Є, Ї**, then read the word slowly.

:::caution
Keep this beginner rule small: **Ї** is always **[йі]**. For **Я, Ю, Є**,
look at the position first, then read slowly.
:::

<!-- INJECT_ACTIVITY: act-2 -->

Pay special attention to the difference between **И** and **І**: **кит** (whale) has the open, retracted sound **[и]**, while **кіт** (cat) has the front vowel **[і]**. One vowel changes the entire meaning.

<!-- INJECT_ACTIVITY: act-vowels-fill -->

## Читаємо слова́

**ма́ма. та́то. вода́. ка́ша.**

Use this three-step reading routine:

1. Find the vowel sounds.
2. Split the word into syllables.
3. Read the syllables smoothly, not as separate letter names.

Try the routine with easy words:

| Слово́ | Split | English support |
| --- | --- | --- |
| **ма́ма** | 2 syllables | mother |
| **та́то** | 2 syllables | father |
| **вода́** | 2 syllables | water |
| **ка́ша** | 2 syllables | porridge |
| **ву́лиця** | 3 syllables | street |
| **столи́ця** | 3 syllables | capital |

Longer words use the same routine with more vowel sounds:

| Слово́ | Split | Beginner note |
| --- | --- | --- |
| **університе́т** | 5 syllables | read from left to right |
| **бібліоте́ка** | 5 syllables | **о** is its own vowel pulse |
| **фотогра́фія** | 5 syllables | final **я** gives the last vowel |

Names of Ukrainian cities are also good reading practice:

| Мі́сто | Split | Note |
| --- | --- | --- |
| **Ки́їв** | 2 syllables | **ї** is **[йі]** |
| **Львів** | 1 syllable | one vowel sound |
| **Оде́са** | 3 syllables | initial **О** can stand alone |
| **Дніпро́** | 2 syllables | consonant cluster, still two vowels |
| **Полта́ва** | 3 syllables | steady open syllables |

Three signs or combinations return in Module 3:

| Form | Beginner reading habit |
| --- | --- |
| **Ь** | no sound of its own; softens the previous consonant |
| **апо́строф** | keeps the next **я/ю/є/ї** separate with **й** |
| **ДЖ / ДЗ** | one joined sound, not two broken sounds |

Read **день** with soft **н**, not with an extra vowel after it. Read
**сім'я́** with a clear **й** before **я**. Read **джерело́** with joined
**дж**.

:::tip
If a word feels long, do not speed up. Find the letters for vowel sounds, make
small syllable beats, then smooth them into one word.
:::

<!-- INJECT_ACTIVITY: act-3 -->

Practice reading with a partner. Student A reads the syllables slowly; Student B checks the vowel count and meaning:

> Олена: Що тут написано? (What is written here?)
> Тарас: Тут слово «ма-ма». (Here is the word "ma-ma".)
> Олена: А тут? (And here?)
> Тарас: Тут «мо-ло-ко». Три склади! (Here is "mo-lo-ko". Three syllables!)
> Олена: Молодець! А це слово? (Well done! And this word?)
> Тарас: «Ву-ли-ця». Теж три склади! ("Vu-ly-tsia". Also three syllables!)

Support after the dialogue:

| Українська | English support |
| --- | --- |
| **Що тут написано?** | What is written here? |
| **Тут слово «ма-ма».** | Here is the word "ma-ma". |
| **А тут?** | And here? |
| **Тут «мо-ло-ко». Три склади!** | Here is "mo-lo-ko". Three syllables! |
| **Молодець! А це слово?** | Well done! And this word? |
| **«Ву-ли-ця». Теж три склади!** | "Vu-ly-tsia". Also three syllables! |

<!-- INJECT_ACTIVITY: act-words-match -->

Now you can comfortably find vowel sounds, identify open syllables, and read everyday Ukrainian words smoothly. In Lesson 2, you will learn to navigate reading traps and connect print to notebook handwriting.


## activities.yaml

inline:
- id: act-1
  type: count-syllables
  title: Рахуй склади́
  instruction: Рахуй голосні звуки. Кожен голосни́й звук дає один склад.
  maxCount: 5
  items:
  - word: день
    correct: 1
  - word: ма́ма
    correct: 2
  - word: молоко́
    correct: 3
  - word: ву́лиця
    correct: 3
  - word: бібліоте́ка
    correct: 5
  - word: Украї́на
    correct: 4
- id: act-syllables-quiz
  type: quiz
  title: Скільки голосних — стільки складів
  instruction: Визнач кількість складів у слові за кількістю голосних звуків.
  questions:
  - question: Скільки складів у слові «ха-та»?
    options:
    - text: '1'
      correct: false
    - text: '2'
      correct: true
    - text: '3'
      correct: false
    explanation: У слові «хата» два голосні звуки [а], тому два склади.
  - question: Скільки складів у слові «ру-ка»?
    options:
    - text: '2'
      correct: true
    - text: '1'
      correct: false
    - text: '3'
      correct: false
    explanation: У слові «рука» два голосні звуки [у, а] — два склади.
  - question: Скільки складів у слові «во-да»?
    options:
    - text: '3'
      correct: false
    - text: '2'
      correct: true
    - text: '1'
      correct: false
    explanation: У слові «вода» два голосні звуки [о, а] — два склади.
  - question: Скільки складів у слові «ка-ша»?
    options:
    - text: '2'
      correct: true
    - text: '4'
      correct: false
    - text: '1'
      correct: false
    explanation: У слові «каша» два голосні звуки [а, а] — два склади.
  - question: Скільки складів у слові «банк»?
    options:
    - text: '2'
      correct: false
    - text: '1'
      correct: true
    - text: '3'
      correct: false
    explanation: У слові «банк» лише один голосний звук [а] — один склад.
  - question: Скільки складів у слові «сон»?
    options:
    - text: '1'
      correct: true
    - text: '2'
      correct: false
    - text: '3'
      correct: false
    explanation: У слові «сон» один голосний звук [о] — один склад.
- id: act-2
  type: match-up
  title: Роль літер у читанні
  instruction: З'єднай лі́теру з її роллю в читанні.
  pairs:
  - left: А
    right: позначає [а]
  - left: О
    right: позначає [о]
  - left: И
    right: позначає [и]
  - left: І
    right: позначає [і]
  - left: Я на початку слова
    right: '[йа]'
  - left: Ї
    right: завжди [йі]
- id: act-vowels-fill
  type: fill-in
  title: Впізнай голосну літеру
  instruction: Встав правильну літеру у слово.
  items:
  - sentence: Яблуко починається на літеру [Я].
    blanks:
    - Я
    options:
    - Я
    - Ю
    - Є
    explanation: У слові яблуко початкова літера Я позначає [йа].
  - sentence: У слові Україна є особлива літера [Ї].
    blanks:
    - Ї
    options:
    - Ї
    - І
    - И
    explanation: Літера Ї завжди позначає два звуки [йі].
  - sentence: У слові людина після л стоїть літера [ю].
    blanks:
    - ю
    options:
    - ю
    - я
    - є
    explanation: Літера ю пом'якшує приголосний [л'].
  - sentence: У слові пісня після н стоїть літера [я].
    blanks:
    - я
    options:
    - я
    - а
    - о
    explanation: Літера я пом'якшує попередній звук [н'].
  - sentence: У слові молоко всі три голосні — це літери [о].
    blanks:
    - о
    options:
    - о
    - а
    - у
    explanation: Всі три склади у слові молоко мають голосний звук [о].
  - sentence: У слові каша голосні звуки позначає літера [а].
    blanks:
    - а
    options:
    - а
    - о
    - и
    explanation: У слові каша дві голосні літери а.
- id: act-3
  type: divide-words
  title: Поділи на склади́
  instruction: Поділи кожне друковане слово на склади́.
  items:
  - word: ма́ма
    answer: ма ма
  - word: молоко́
    answer: мо ло ко
  - word: ву́лиця
    answer: ву ли ця
  - word: столи́ця
    answer: сто ли ця
  - word: люди́на
    answer: лю ди на
  - word: бібліоте́ка
    answer: бі блі о те ка
- id: act-words-match
  type: match-up
  title: Слово та його значення
  instruction: З'єднай прочитане українське слово з англійським перекладом.
  pairs:
  - left: ма́ма
    right: mother
  - left: та́то
    right: father
  - left: вода́
    right: water
  - left: ка́ша
    right: porridge
  - left: ву́лиця
    right: street
  - left: столи́ця
    right: capital
workbook:
- id: act-w1
  type: group-sort
  title: Один, два чи три склади́
  instruction: Розподіли слова за кількістю складів.
  groups:
  - label: Один склад
    items:
    - день
    - Львів
  - label: Два склади́
    items:
    - ма́ма
    - та́то
    - Ки́їв
  - label: Три склади́
    items:
    - молоко́
    - ву́лиця
    - столи́ця
- id: act-w2
  type: odd-one-out
  title: Зайве за кількістю складів
  instruction: Обери слово, яке має іншу кількість складів.
  items:
  - words:
    - ма́ма
    - та́то
    - вода́
    - день
    answer: день
    explanation: День має один склад; інші слова мають два.
  - words:
    - молоко́
    - ву́лиця
    - столи́ця
    - Ки́їв
    answer: Ки́їв
    explanation: Ки́їв має два склади; інші слова мають три.
  - words:
    - день
    - Львів
    - ма́ма
    - так
    answer: ма́ма
    explanation: Ма́ма має два склади; інші слова мають один.
  - words:
    - бібліоте́ка
    - університе́т
    - фотогра́фія
    - ка́ша
    answer: ка́ша
    explanation: Ка́ша має два склади; інші слова мають п'ять.
- id: act-w-count
  type: count-syllables
  title: Підрахунок складів у нових словах
  instruction: Порахуй кількість складів у кожному слові.
  maxCount: 5
  items:
  - word: та́то
    correct: 2
  - word: вода́
    correct: 2
  - word: ка́ша
    correct: 2
  - word: люди́на
    correct: 3
  - word: столи́ця
    correct: 3
  - word: університе́т
    correct: 5
- id: act-w-divide
  type: divide-words
  title: Розподіл слів на склади
  instruction: Запиши слова, розділяючи склади пробілом.
  items:
  - word: вода́
    answer: во да
  - word: та́то
    answer: та то
  - word: ка́ша
    answer: ка ша
  - word: рука́
    answer: ру ка
  - word: я́блуко
    answer: яб лу ко
  - word: Полта́ва
    answer: Пол та ва
- id: act-w-tf
  type: true-false
  title: Правила українського читання
  instruction: Визнач, чи твердження є правильним.
  items:
  - statement: У слові стільки складів, скільки в ньому голосних звуків.
    correct: true
    explanation: Це головне правило складоподілу в українській мові.
  - statement: Приголосний звук без голосного може утворити склад.
    correct: false
    explanation: Склад утворюється лише навколо голосного звука.
  - statement: Літера Ї завжди позначає два звуки [йі].
    correct: true
    explanation: Літера Ї ніколи не пом'якшує приголосні й завжди дає [йі].
  - statement: В українській мові ненаголошений звук [о] читається як [а].
    correct: false
    explanation: В українській мові [о] завжди звучить чітко як [о], наприклад, у
      слові молоко.
  - statement: У слові «день» один склад.
    correct: true
    explanation: У слові «день» один голосний звук [е], тому один склад.
  - statement: У слові «яблуко» перший звук — це лише один звук [а].
    correct: false
    explanation: 'На початку слова літера Я позначає два звуки: [й] та [а].'
- id: act-w-match
  type: match-up
  title: Складові пари
  instruction: З'єднай початок слова з його закінченням.
  pairs:
  - left: мо-ло-
    right: ко
  - left: ву-ли-
    right: ця
  - left: сто-ли-
    right: ця
  - left: лю-ди-
    right: на
  - left: яб-лу-
    right: ко
  - left: піс-
    right: ня
- id: act-w-quiz
  type: quiz
  title: Перевірка читання слів
  instruction: Обери правильний варіант відповіді.
  questions:
  - question: Як правильно прочитати слово «молоко»?
    options:
    - text: мо-ло-ко з чітким [о]
      correct: true
    - text: ма-ла-ко через [а]
      correct: false
    - text: м-л-к по літерах
      correct: false
    explanation: Українське [о] завжди вимовляється чітко й виразно.
  - question: Скільки складів у назві міста «Львів»?
    options:
    - text: 1 склад
      correct: true
    - text: 2 склади
      correct: false
    - text: 3 склади
      correct: false
    explanation: У слові «Львів» лише один голосний звук [і], тому один склад.
  - question: Скільки складів у назві міста «Київ»?
    options:
    - text: 2 склади
      correct: true
    - text: 1 склад
      correct: false
    - text: 3 склади
      correct: false
    explanation: 'Голосні звуки [и] та [йі] утворюють два склади: Ки-їв.'
  - question: Яку роль виконує літера Я у слові «пісня»?
    options:
    - text: пом'якшує попередній приголосний [н'] та позначає звук [а]
      correct: true
    - text: позначає два звуки [йа]
      correct: false
    - text: не позначає звука
      correct: false
    explanation: Після приголосного літера Я позначає м'якість цього приголосного
      та звук [а].
  - question: Що означає слово «столиця»?
    options:
    - text: capital city
      correct: true
    - text: big street
      correct: false
    - text: small village
      correct: false
    explanation: Столиця — це головне місто держави (Київ — столиця України).
  - question: Як діти вчаться читати українські слова?
    options:
    - text: 'по складах: склад за складом'
      correct: true
    - text: називаючи літери окремо
      correct: false
    - text: вгадуючи з іншої мови
      correct: false
    explanation: 'Підхід «знизу вгору»: звук -> склад -> слово.'


## vocabulary.yaml

- lemma: склад
  translation: syllable
  pos: noun
  usage: У сло́ві ма́ма два склади́.
- lemma: голосни́й звук
  translation: vowel sound
  pos: noun phrase
  usage: А - голосни́й звук.
- lemma: при́голосний звук
  translation: consonant sound
  pos: noun phrase
  usage: М - при́голосний звук.
- lemma: чита́ти
  translation: to read
  pos: verb
  usage: Я чита́ю сло́во.
- lemma: писа́ти
  translation: to write
  pos: verb
  usage: Я пишу́ лі́теру.
- lemma: ма́ма
  translation: mother
  pos: noun
  usage: Ма́ма.
- lemma: та́то
  translation: father
  pos: noun
  usage: Та́то.
- lemma: молоко́
  translation: milk
  pos: noun
  usage: Молоко́.
- lemma: я́блуко
  translation: apple
  pos: noun
  usage: Я́блуко.
- lemma: люди́на
  translation: person
  pos: noun
  usage: Люди́на.
- lemma: ву́лиця
  translation: street
  pos: noun
  usage: Ву́лиця.
- lemma: столи́ця
  translation: capital
  pos: noun
  usage: Ки́їв - столи́ця Украї́ни.
- lemma: ка́ша
  translation: porridge
  pos: noun
  usage: Ка́ша.
- lemma: пі́сня
  translation: song
  pos: noun
  usage: Пі́сня.


## resources.yaml

- title: Большакова, буквар 1 клас, p. 25
  role: textbook
  source: Большакова, буквар 1 клас, p. 25
  notes: 'Plan reference: syllable rule; every syllable has a vowel sound.'
- title: Большакова, буквар 1 клас, p. 29
  role: textbook
  source: Большакова, буквар 1 клас, p. 29
  notes: 'Plan reference: sound analysis routine for Ukrainian words.'
- title: Захарійчук 1 клас (НУШ 2025), p. 13-15
  role: textbook
  source: Захарійчук 1 клас (НУШ 2025), p. 13-15
  notes: 'Plan reference: symbols for vowel, hard consonant, and soft consonant sounds.'
- title: Кравцова, Українська мова 2 клас, p. 13
  role: textbook
  source: Кравцова, Українська мова 2 клас, p. 13
  notes: 'Plan reference: hand-under-chin syllable counting check.'
- title: Anna Ohoiko — Ukrainian alphabet overview
  role: youtube
  url: https://www.youtube.com/watch?v=ksXIXj7CXwc
  notes: Supplemental listening support for the vowel reading pass.


## lesson-2
## module.md

# Друк, зошит, перевірка

У першому уроці ви навчилися рахувати склади та читати перші слова: **ма́ма**, **молоко́**, **ву́лиця**. In Lesson 1 you learned to count syllables and read your first words: **ма́ма** (mother), **молоко́** (milk), **ву́лиця** (street).

Тепер ми переходимо до безпечних читацьких звичок і роботи з рукописним текстом — now we turn to safe reading habits and working with handwritten text:
- **Уникати пасток читання** — avoid common reading traps such as splitting **дж** and **дз**, ignoring **ь**, or blurring **о**;
- **Розпізнавати друк і рукопис** — connect printed letters to handwritten forms in a notebook;
- **Перевіряти себе** — apply a step-by-step decoding routine before reading aloud.

## Пастки читання

**молоко́. день. Украї́на. джерело́.**

Use these safety checks:

| Trap | Safer Ukrainian habit |
| --- | --- |
| Reading letter by letter | Read by syllables: three beats in **молоко́** |
| Blurring unstressed **о** | Keep **о** clear every time |
| Reading **дж** as **д + ж** | Join it as one sound |
| Ignoring **ь** | Make the previous consonant soft |
| Reading **ї** as plain **і** | Read **ї** as **[йі]** |
| Treating apostrophe as decoration | Keep the following **й** sound |

Build the habit from words on this page: **день**, **ма́ма**, **молоко́**,
**Украї́на**. Do not use another language's alphabet as the shortcut.

:::note
These are reading habits, not a pronunciation exam. Slow accurate reading is a
win at A1.
:::

Let us examine the most common traps that English speakers encounter when reading Ukrainian:

- **Злиті звуки ДЖ та ДЗ** (Fused sounds ДЖ and ДЗ):
  In Ukrainian roots, **дж** and **дз** represent single fused sounds: **[дж]** as in **джерело́** (water spring, source) and **[дз]** as in **дзе́ркало** (mirror). Do not pronounce them as separate letters. Ukrainian textbooks highlight this unified pronunciation: «Буквосполучення дж, дз позначають один злитий звук» (quoted from: Вашуленко, Українська мова 2 клас, p. 23-27).

- **Знак м'якшення Ь** (The soft sign Ь):
  The letter **ь** produces no independent sound; its only role is to indicate that the preceding consonant is soft: «Знак м'якшення не позначає окремого звука, а вказує на м'якість попереднього приголосного» (quoted from: Захарійчук 1 клас (НУШ 2025), p. 13-15). Read **день** (day) with a soft final [нʲ], not an extra vowel. The same softening occurs in **о́сінь** (autumn), **ба́тько** (father), and **вчи́тель** (teacher).

- **Апостроф '** (The apostrophe '):
  The apostrophe indicates a distinct, separate pronunciation where the preceding consonant stays hard, and the following iotated vowel retains its full [й] sound: **сім'я́** (family) is read as a firm [сім] followed by [йа], never merged into [сіма].

- **Чистий звук О** (Clean sound О):
  Ukrainian vowels never reduce to a neutral vowel. Every **о** in **молоко́** (milk) stays a distinct and open **[о]**, whether stressed or unstressed.

- **Літера Ї** (The letter Ї):
  The letter **ї** always marks two sounds: **[йі]**. In **Украї́на** (Ukraine) and **Ки́їв** (Kyiv), pronounce the full **[й]** glide every time.

<!-- INJECT_ACTIVITY: act-traps-match -->

<!-- INJECT_ACTIVITY: act-traps-quiz -->

<!-- INJECT_ACTIVITY: act-traps-tf -->

## Друк, зошит, перевірка

**Друк:** **ма́ма**, **молоко́**, **день**, **Ки́їв**.

**Зошит:** the same known words written by you, a teacher, or a tutor.

Recognition comes before long handwriting production. Ask a native Ukrainian
teacher or tutor to write one known word in their own hand. Your job is only to
match it to the printed word and read it aloud. Do not copy or trace a
third-party handwriting sample.

| Друк | Notebook recognition prompt |
| --- | --- |
| **ма́ма** | Which printed word matches the handwritten **ма́ма**? |
| **молоко́** | Which printed word matches the handwritten **молоко́**? |
| **день** | Which printed word has the final soft sign? |
| **Ки́їв** | Which printed word has **ї**? |

Use a short partner routine when possible. Student A points to the word.
Student B says only the number of vowel sounds. Then both students read the
word aloud. If you are alone, cover the English support first, count the vowel
sounds, and read before you check meaning.

When a word feels long, slow down:

| Mark | Meaning |
| --- | --- |
| **1** | I can find the vowel sounds. |
| **2** | I can count the syllables. |
| **3** | I can read the word aloud smoothly. |

Practice this partner routine with a fellow learner:

> Олена: Подивися на цей запис у зошиті. Що тут написано? (Look at this entry in the notebook. What is written here?)
> Тарас: Тут написано друковане слово «день». (Here is written the printed word "день".)
> Олена: Правильно! А скільки голосних звуків у слові «Київ»? (Correct! And how many vowel sounds in the word "Київ"?)
> Тарас: Два голосні звуки: [и] та [і]. Тому це два склади! (Two vowel sounds: [и] and [і]. Therefore it is two syllables!)
> Олена: Молодець! А як прочитати слово «джерело»? (Well done! And how to read the word "джерело"?)
> Тарас: Буквосполучення «дж» читаємо разом: [джерело]. (The letter combination "дж" is read together: [джерело].)

Support after the dialogue:

| Українська | English support |
| --- | --- |
| **Подивися на цей запис у зошиті. Що тут написано?** | Look at this entry in the notebook. What is written here? |
| **Тут написано друковане слово «день».** | Here is written the printed word "день". |
| **Правильно! А скільки голосних звуків у слові «Київ»?** | Correct! And how many vowel sounds in the word "Київ"? |
| **Два голосні звуки: [и] та [і]. Тому це два склади!** | Two vowel sounds: [и] and [і]. Therefore it is two syllables! |
| **Молодець! А як прочитати слово «джерело»?** | Well done! And how to read the word "джерело"? |
| **Буквосполучення «дж» читаємо разом: [джерело].** | The letter combination "дж" is read together: [джерело]. |

Follow the sound analysis routine established in Ukrainian classrooms: «Звуковий аналіз слова: 1) Визначаю голосні звуки 2) Ділю слово на склади 3) Ставлю наголос 4) Позначаю приголосні звуки» (quoted from: Большакова, буквар 1 клас, p. 29). This four-step sequence guarantees steady progress.

<!-- INJECT_ACTIVITY: act-notebook-match -->

<!-- INJECT_ACTIVITY: act-reading-check -->

Before you leave the lesson tab, check that you can do these things:

- explain **склад** as "syllable";
- count the vowel sounds in **молоко́**;
- count three vowel sounds in **ву́лиця**;
- say why **Ї** is always **[йі]**;
- read **я́блуко**, **люди́на**, **пі́сня**, and **день** slowly;
- keep **о** clear in **молоко́** and **столи́ця**;
- say that **дж** and **дз** are joined reading units;
- match a known printed word to a notebook version before copying it.

The workbook repeats easy words and a few longer words on purpose. Repetition
is how the alphabet becomes automatic.

Ви навчилися впевнено розпізнавати друковані форми, уникати підступних пасток та перевіряти себе перед читанням уголос. You have learned to confidently recognize print forms, avoid tricky reading traps, and check yourself before reading aloud. У наступному уроці ми закріпимо всі правила на цілісних текстах та підіб'ємо підсумок модуля. In the next lesson, we will consolidate all the rules on full texts and summarize the module.


## activities.yaml

inline:
- id: act-traps-match
  type: match-up
  title: Правило для кожної пастки
  instruction: З'єднай слово або знак із правилом безпечного читання.
  pairs:
  - left: джерело́
    right: читай [дж] як один злитий звук
  - left: день
    right: м'який знак пом'якшує приголосний [нʲ]
  - left: сім'я́
    right: 'апостроф розділяє звуки: [сім] і [йа]'
  - left: Украї́на
    right: літера ї завжди дає два звуки [йі]
  - left: молоко́
    right: кожен звук [о] звучить чітко й відкрито
  - left: дзе́ркало
    right: читай [дз] як один злитий звук
- id: act-traps-quiz
  type: quiz
  title: Перевірка читацьких пасток
  instruction: Обери правильне пояснення для поданого слова.
  items:
  - prompt: Як правильно читати буквосполучення «дж» у слові джерело́?
    options:
    - text: Як один злитий звук [дж]
      correct: true
    - text: Як два окремі звуки [д] і [ж]
      correct: false
    explanation: Буквосполучення «дж» у корені позначає один злитий звук.
  - prompt: Яку роль відіграє знак м'якшення у слові день?
    options:
    - text: Пом'якшує попередній звук [н]
      correct: true
    - text: Позначає окремий голосний звук
      correct: false
    explanation: Ь не має власного звука, він пом'якшує попередній приголосний.
  - prompt: Як правильно прочитати слово сім'я́ через апостроф?
    options:
    - text: 'Роздільно: твердий [м] + [йа]'
      correct: true
    - text: 'М''яко разом: [сіма]'
      correct: false
    explanation: 'Апостроф вимагає роздільної вимови: твердий приголосний і йотований
      голосний [йа].'
  - prompt: Чому літеру ї у слові Украї́на не можна читати як просте [і]?
    options:
    - text: Бо ї завжди позначає два звуки [йі]
      correct: true
    - text: Бо ї пом'якшує попередній звук
      correct: false
    explanation: 'Літера Ї в українській мові завжди позначає два звуки: [й] та [і].'
  - prompt: Як звучить ненаголошене «о» в українському слові молоко́?
    options:
    - text: Залишається чистим і виразним звуком [о]
      correct: true
    - text: Перетворюється на нечітке [а]
      correct: false
    explanation: В українській мові ненаголошене «о» ніколи не перетворюється на [а].
  - prompt: Як читаємо буквосполучення «дз» у слові дзе́ркало?
    options:
    - text: Як один злитий звук [дз]
      correct: true
    - text: Як окремі звуки [д] та [з]
      correct: false
    explanation: Буквосполучення «дз» читається як один неподільний злитий звук.
- id: act-traps-tf
  type: true-false
  title: Твердження про пастки читання
  instruction: Визнач, чи є твердження правильним.
  items:
  - statement: У слові «молоко» всі три звуки [о] звучать чітко.
    correct: true
    explanation: В українській мові немає акання.
  - statement: Буквосполучення «дж» у слові «джерело» вимовляємо як два роздільні
      звуки.
    correct: false
    explanation: ДЖ позначає один злитий звук.
  - statement: Літера «ї» в слові «Україна» позначає два звуки [йі].
    correct: true
    explanation: Літера Ї завжди позначає два звуки.
  - statement: М'який знак позначає окремий голосний звук.
    correct: false
    explanation: Ь не має власного звука.
  - statement: Апостроф вимагає твердої вимови приголосного перед я, ю, є, ї.
    correct: true
    explanation: Приголосний перед апострофом залишається твердим.
  - statement: Буквосполучення «дз» у слові «дзеркало» позначає один злитий звук.
    correct: true
    explanation: ДЗ вимовляється як один неподільний звук.
- id: act-notebook-match
  type: match-up
  title: Друк і рукописні форми
  instruction: З'єднай друковане слово з його описом або рукописною ознакою.
  pairs:
  - left: 'друк: день'
    right: 'зошит: слово з кінцевим знаком м''якшення'
  - left: 'друк: Київ'
    right: 'зошит: слово з двома крапками над ї'
  - left: 'друк: джерело'
    right: 'зошит: слово зі злитим буквосполученням дж'
  - left: 'друк: сім''я'
    right: 'зошит: слово з роздільним апострофом'
  - left: 'друк: осінь'
    right: 'зошит: слово з двома м''якими приголосними'
  - left: 'друк: дзеркало'
    right: 'зошит: слово зі злитим буквосполученням дз'
- id: act-reading-check
  type: true-false
  title: Правила самоперевірки читання
  instruction: Визнач, чи є твердження правильним.
  items:
  - statement: Знак м'якшення (ь) ніколи не має власного звука.
    correct: true
    explanation: Ь лише показує м'якість попереднього приголосного.
  - statement: У слові джерело буквосполучення дж вимовляємо як два роздільні звуки.
    correct: false
    explanation: ДЖ у корені слова читаємо як один злитий звук.
  - statement: Апостроф вказує на роздільну вимову твердого приголосного перед я,
      ю, є, ї.
    correct: true
    explanation: Апостроф зберігає твердість приголосного і розділяє його з наступним
      йотованим.
  - statement: Літера ї іноді позначає один звук після м'якого приголосного.
    correct: false
    explanation: Літера Ї завжди позначає два звуки [йі] і ніколи не пом'якшує.
  - statement: В українській мові всі ненаголошені звуки [о] читаються чітко.
    correct: true
    explanation: Українське [о] ніколи не зазнає акання й звучить чітко.
  - statement: Перед читанням слова корисно порахувати голосні звуки.
    correct: true
    explanation: Скільки в слові голосних звуків — стільки й складів.
workbook:
- id: act-4
  type: error-correction
  title: Пастки читання
  instruction: Обери безпечнішу українську читацьку звичку.
  items:
  - sentence: Не читай молоко́ як малоко.
    error: малоко
    correction: молоко
    options:
    - молоко
    - нечітке о
    explanation: Українське о залишається чистим; читай молоко́ у три відкриті удари.
  - sentence: Не читай дж у слові джерело́ як д плюс ж.
    error: д плюс ж
    correction: один злитий звук
    options:
    - один злитий звук
    - д плюс ж
    explanation: ДЖ читаємо як один злитий звук у словах як джерело́.
  - sentence: Украї́на — не читай ї як просте і.
    error: просте і
    correction: '[йі]'
    options:
    - '[йі]'
    - '[і]'
    explanation: Ї завжди читаємо як [йі].
  - sentence: День — не треба додати голосний після нь.
    error: додати голосний
    correction: пом'якшити н і зупинитися
    options:
    - пом'якшити н і зупинитися
    - додати і після нь
    explanation: Ь не має власного звука; він м'якшить попередній при́голосний.
- id: act-w3
  type: true-false
  title: Факти про читання
  instruction: Обери правда чи неправда.
  items:
  - statement: Кожен український склад має голосни́й звук.
    correct: true
    explanation: Голосни́й звук — центр складу.
  - statement: Ї іноді м'якшить попередній при́голосний.
    correct: false
    explanation: Ї завжди читаємо як [йі].
  - statement: У молоко́ звук о залишається чистим.
    correct: true
    explanation: Не перетворюй о на нечіткий голосни́й.
  - statement: ДЖ і ДЗ читаємо як злиті одиниці.
    correct: true
    explanation: ДЖ і ДЗ читаємо як злиті одиниці.
- id: act-w4
  type: match-up
  title: Друк і зошит
  instruction: З'єднай друковане слово з підказкою в зо́шиті.
  pairs:
  - left: 'друк: ма́ма'
    right: 'зошит: ма́ма'
  - left: 'друк: молоко́'
    right: 'зошит: молоко́'
  - left: 'друк: день'
    right: 'зошит: слово з кінцевим ь'
  - left: 'друк: Ки́їв'
    right: 'зошит: слово з ї'
  - left: 'друк: ву́лиця'
    right: 'зошит: трискладове слово про місто'
- id: act-wb-group
  type: group-sort
  title: Розподіл слів за фонетичною ознакою
  instruction: Розподіли слова за їхньою ключовою фонетичною ознакою.
  groups:
  - label: Знак м'якшення (ь)
    items:
    - день
    - о́сінь
    - ба́тько
  - label: Злиті звуки (дж, дз)
    items:
    - джерело́
    - дзе́ркало
  - label: Літера ї або апостроф
    items:
    - Ки́їв
    - Украї́на
    - сім'я́
- id: act-wb-quiz
  type: quiz
  title: Читацькі правила на практиці
  instruction: Обери правильну відповідь на запитання про читання слів.
  items:
  - prompt: Скільки звуків позначає літера ї у слові Київ?
    options:
    - text: два звуки [йі]
      correct: true
    - text: один звук [і]
      correct: false
    explanation: 'Літера Ї завжди позначає два звуки: [й] та [і].'
  - prompt: Який приголосний є м'яким у слові батько?
    options:
    - text: звук [тʲ]
      correct: true
    - text: звук [к]
      correct: false
    explanation: 'Знак м''якшення після літери т пом''якшує саме її: [батʲко].'
  - prompt: Як вимовляємо буквосполучення дж у слові джерело?
    options:
    - text: як один неподільний злитий звук
      correct: true
    - text: як два роздільні звуки
      correct: false
    explanation: У кореневих словах буквосполучення «дж» є єдиним звуком.
  - prompt: Що вказує на роздільну вимову в слові сім'я?
    options:
    - text: апостроф
      correct: true
    - text: знак м'якшення
      correct: false
    explanation: Апостроф вказує на роздільну тверду вимову перед йотованим.
  - prompt: Який кінцевий приголосний є м'яким у слові вчитель?
    options:
    - text: звук [лʲ]
      correct: true
    - text: звук [ч]
      correct: false
    explanation: М'який знак у кінці слова вчитель пом'якшує звук [л].
  - prompt: Скільки складів має слово дзеркало?
    options:
    - text: три склади
      correct: true
    - text: чотири склади
      correct: false
    explanation: У слові дзеркало три голосні [е, а, о], отже, три склади.
- id: act-wb-odd
  type: odd-one-out
  title: Зайве слово за звуковою ознакою
  instruction: Обери слово, яке відрізняється від інших за вказаною фонетичною ознакою.
  items:
  - words:
    - день
    - о́сінь
    - вчи́тель
    - ма́ма
    answer: ма́ма
    explanation: Ма́ма не має знака м'якшення, тоді як інші три слова закінчуються
      м'яким знаком.
  - words:
    - джерело́
    - дзе́ркало
    - дзвін
    - молоко́
    answer: молоко́
    explanation: Молоко́ не містить буквосполучень дж чи дз.
  - words:
    - Ки́їв
    - Украї́на
    - ї́жа
    - ба́тько
    answer: ба́тько
    explanation: Ба́тько не має літери ї.
  - words:
    - сім'я́
    - м'я́со
    - п'ять
    - вода́
    answer: вода́
    explanation: Вода́ пишеться без апострофа.
  - words:
    - молоко́
    - столи́ця
    - ка́ша
    - день
    answer: день
    explanation: День — односкладове слово, а інші мають два або три склади.
  - words:
    - ба́тько
    - о́сінь
    - день
    - джерело́
    answer: джерело́
    explanation: Джерело́ не має знака м'якшення.
- id: act-wb-fill
  type: fill-in
  title: Встав правильну літеру або знак
  instruction: Встав пропущену літеру або графічний знак у слово.
  items:
  - sentence: Сьогодні гарний де__ь.
    options:
    - н
    - нь
    answer: нь
    explanation: 'У слові день у кінці пишемо знак м''якшення: день.'
  - sentence: У лісі б'є холодне __ерело.
    options:
    - дж
    - ж
    answer: дж
    explanation: Слово джерело починається зі злитого звука, що позначається буквосполученням
      дж.
  - sentence: Це дружна сім__я.
    options:
    - ''''
    - ь
    answer: ''''
    explanation: У слові сім'я ставимо апостроф для роздільної вимови.
  - sentence: Золота о́сі__ь настала.
    options:
    - н
    - нь
    answer: нь
    explanation: Слово о́сінь закінчується м'яким знаком.
  - sentence: У кімнаті висить велике __еркало.
    options:
    - дз
    - з
    answer: дз
    explanation: Слово дзеркало починається з буквосполучення дз.
  - sentence: Місто Ки__в — столиця України.
    options:
    - ї
    - і
    answer: ї
    explanation: У назві Київ пишемо літеру ї, яка завжди дає два звуки [йі].


## vocabulary.yaml

- lemma: день
  translation: day
  pos: noun
  usage: День.
- lemma: о́сінь
  translation: autumn
  pos: noun
  usage: О́сінь.
- lemma: ба́тько
  translation: father
  pos: noun
  usage: Ба́тько.
- lemma: вчи́тель
  translation: teacher
  pos: noun
  usage: Вчи́тель.
- lemma: джерело́
  translation: source / spring
  pos: noun
  usage: Джерело́.
- lemma: дзе́ркало
  translation: mirror
  pos: noun
  usage: Дзе́ркало.
- lemma: абе́тка
  translation: alphabet
  pos: noun
  usage: Украї́нська абе́тка.
- lemma: м'яки́й знак
  translation: soft sign
  pos: noun phrase
  usage: Ь - м'яки́й знак.
- lemma: апо́строф
  translation: apostrophe
  pos: noun
  usage: У сло́ві «сім'я́» є апо́строф.
- lemma: Ки́їв
  translation: Kyiv
  pos: proper noun
  usage: Ки́їв - столи́ця Украї́ни.
- lemma: Украї́на
  translation: Ukraine
  pos: proper noun
  usage: Украї́на.
- lemma: так
  translation: yes / like this
  pos: adverb
  usage: Так.
- lemma: ні
  translation: 'no'
  pos: particle
  usage: Ні.


## resources.yaml

- title: Большакова, буквар 1 клас, p. 29
  role: textbook
  source: Большакова, буквар 1 клас, p. 29
  notes: 'Plan reference: sound analysis routine for Ukrainian words.'
- title: Захарійчук 1 клас (НУШ 2025), p. 13-15
  role: textbook
  source: Захарійчук 1 клас (НУШ 2025), p. 13-15
  notes: 'Plan reference: symbols for vowel, hard consonant, and soft consonant sounds.'
- title: Вашуленко, Українська мова 2 клас, p. 23-27
  role: textbook
  source: Вашуленко, Українська мова 2 клас, p. 23-27
  notes: 'Plan reference: transfer, stress, and iotated-vowel reading context.'
- title: Anna Ohoiko — Ukrainian alphabet overview
  role: youtube
  url: https://www.youtube.com/watch?v=ksXIXj7CXwc
  channel: Ukrainian Lessons
  notes: Supplemental listening support for the vowel reading pass.


## lesson-3
## module.md

# Далі

У перших двох уроках ви дізналися, що голосні звуки є центром кожного складу: **ма́ма**, **молоко́**, **ву́лиця**. In the first two lessons you learned that vowel sounds are the center of every syllable: **ма́ма** (mother), **молоко́** (milk), **ву́лиця** (street). Ви також навчилися розпізнавати знак м'якшення **ь**, апостроф, йотовані літери та злиті звуки **дж** і **дз**. You also learned to recognize the soft sign **ь**, the apostrophe, iotated letters, and the fused sounds **дж** and **дз**.

Тепер ми переходимо до плавного читання цілих речень і багатоскладових слів — now we move to the smooth reading of full sentences and multi-syllable words:
- **Читати плавно від слова до речення** — read connected phrases and simple sentences smoothly;
- **Ділити багатоскладові слова на склади** — split long words into manageable syllable beats;
- **Застосовувати надійну читацьку рутину** — use a four-step decoding check before reading aloud.

## Далі

Тепер переходь до словника й вправ. You can now look at a printed Ukrainian
word, find the letters that mark vowel sounds, count the syllables, and read
the whole word more calmly.

Коли окремі склади стають знайомими, об'єднуйте їх у слова, а слова — у перші прості речення. When separate syllables become familiar, combine them into words, and words into your first simple sentences. Пам'ятайте золоте правило української фонетики: «Скільки у слові голосних звуків, стільки й складів» (quoted from: Большакова, буквар 1 клас, p. 25). Кожен склад має один голосний імпульс.

Спробуйте прочитати прості речення за складами — try reading simple sentences syllable by syllable:

| Речення | Поскладове читання | English support |
| --- | --- | --- |
| **Ма́ма чита́є.** | **Ма-ма чи-та-є.** | Mother is reading. |
| **Та́то пи́ше.** | **Та-то пи-ше.** | Father is writing. |
| **Ки́їв — столи́ця Украї́ни.** | **Ки-їв — сто-ли-ця У-кра-ї-ни.** | Kyiv is the capital of Ukraine. |
| **Ось моє́ я́блуко.** | **Ось мо-є яб-лу-ко.** | Here is my apple. |
| **Це на́ша ву́лиця.** | **Це на-ша ву-ли-ця.** | This is our street. |
| **Луна́є гарна пі́сня.** | **Лу-на-є гар-на піс-ня.** | A nice song is playing. |

<!-- INJECT_ACTIVITY: act-l3-sent-match -->

Під час читання довших слів не поспішайте й не називайте окремі літери: «Під час читання по складах не робіть пауз між літерами одного складу, а зливайте приголосний з голосним» (quoted from: Вашуленко, Українська мова 2 клас, p. 23-27). Розбийте слово на відкриті та закриті частини:

- **бі-блі-о-те-ка** — п'ять голосних звуків, п'ять складів (бібліоте́ка);
- **у-ні-вер-си-тет** — п'ять голосних звуків, п'ять складів (університе́т);
- **фо-то-гра-фі-я** — п'ять голосних звуків, п'ять складів (фотогра́фія);
- **шо-ко-лад** — три голосні звуки, три склади (шокола́д).

Якщо ви сумніваєтеся в кількості складів, скористайтеся простим тілесним тестом: «Покладіть долоню під підборіддя: кожен дотик — це один голосний звук і один склад» (quoted from: Кравцова, Українська мова 2 клас, p. 13).

<!-- INJECT_ACTIVITY: act-l3-syllables-count -->

<!-- INJECT_ACTIVITY: act-l3-divide -->

Послухайте розмову двох учнів про читання нових слів і речень — listen to a conversation between two learners about reading new words and sentences:

> Олена: Що ти читаєш? (What are you reading?)
> Тарас: Я читаю нове слово. (I am reading a new word.)
> Олена: Яке це слово? (What word is it?)
> Тарас: «Університет». Тут п'ять складів! ("University". Five syllables here!)
> Олена: Чудово! А речення можеш прочитати? (Great! And can you read a sentence?)
> Тарас: Так: «Київ — красива столиця». (Yes: "Kyiv is a beautiful capital".)
> Олена: Молодець, читаєш дуже чисто й плавно! (Well done, you read very purely and smoothly!)

Розбір реплік розмови — breakdown of lines:

| Українська | English support |
| --- | --- |
| **Що ти читаєш?** | What are you reading? |
| **Я читаю нове слово.** | I am reading a new word. |
| **Яке це слово?** | What word is it? |
| **«Університет». Тут п'ять складів!** | "University". Five syllables here! |
| **Чудово! А речення можеш прочитати?** | Great! And can you read a sentence? |
| **Так: «Київ — красива столиця».** | Yes: "Kyiv is a beautiful capital". |
| **Молодець, читаєш дуже чисто й плавно!** | Well done, you read very purely and smoothly! |

<!-- INJECT_ACTIVITY: act-l3-quiz -->

Перед тим як читати будь-який новий текст уголос — before reading any new text aloud, apply this four-step self-check routine:

1. **Голосні звуки** — find all letters marking vowel sounds.
2. **Кількість складів** — count the syllables (as many syllables as vowel sounds).
3. **Особливі знаки** — notice **ь**, apostrophe, **ї**, **дж**, or **дз**.
4. **Плавне злиття** — read word by word in syllables, then smooth into a phrase.

<!-- INJECT_ACTIVITY: act-l3-tf -->

### Підсумок модуля — Module summary

Підіб'ємо підсумки всього модуля — module summary:
- **Рахувати склади за голосними звуками** — count syllables accurately by identifying vowel sounds in any Ukrainian word;
- **Читати відкриті та закриті склади** — smoothly blend consonants and vowels into open and closed syllables without letter-by-letter spelling;
- **Розрізняти всі 10 голосних літер** — read the six simple vowels (**а, о, у, е, и, і**) and know what iotated vowels (**я, ю, є, ї**) do in different positions;
- **Уникати типових читацьких пасток** — keep unstressed **о** pure, pronounce **дж** and **дз** as single fused sounds, and correctly decode the soft sign **ь** and apostrophe;
- **Читати багатоскладові слова та перші речення** — break down long words into syllables and read connected Ukrainian sentences with natural cadence;
- **З'єднувати друк і зошит** — recognize printed vocabulary in handwritten notebook forms before copying or writing.

Вітаємо з успішним завершенням модуля! — Congratulations on successfully completing the module! Тепер ви володієте надійним читацьким інструментом і можете впевнено переходити до наступних кроків у вивченні української мови. — Now you have a reliable reading tool and can confidently take your next steps in Ukrainian.


## activities.yaml

inline:
- id: act-l3-sent-match
  type: match-up
  title: З'єднай речення з перекладом
  instruction: З'єднай просте українське речення з його англійським перекладом.
  pairs:
  - left: Ма́ма чита́є.
    right: Mother is reading.
  - left: Та́то пи́ше.
    right: Father is writing.
  - left: Ки́їв — столи́ця Украї́ни.
    right: Kyiv is the capital of Ukraine.
  - left: Ось моє́ я́блуко.
    right: Here is my apple.
  - left: Це на́ша ву́лиця.
    right: This is our street.
  - left: Луна́є гарна пі́сня.
    right: A nice song is playing.
- id: act-l3-syllables-count
  type: count-syllables
  title: Порахуй склади у довгих словах
  instruction: Порахуй голосні звуки та визнач кількість складів.
  maxCount: 6
  items:
  - word: бібліоте́ка
    correct: 5
  - word: університе́т
    correct: 5
  - word: фотогра́фія
    correct: 5
  - word: шокола́д
    correct: 3
  - word: абе́тка
    correct: 3
  - word: ре́чення
    correct: 3
- id: act-l3-divide
  type: divide-words
  title: Поділи слова на склади
  instruction: Поділи кожне слово на склади за голосними звуками.
  items:
  - word: кни́га
    answer: кни га
  - word: шокола́д
    answer: шо ко лад
  - word: абе́тка
    answer: а бе тка
  - word: столи́ця
    answer: сто ли ця
  - word: пі́сня
    answer: піс ня
  - word: джерело́
    answer: дже ре ло
- id: act-l3-quiz
  type: quiz
  title: Правила та кроки читання
  instruction: Обери правильну відповідь про читання слів і речень.
  items:
  - prompt: З чого починається читання незнайомого слова?
    options:
    - text: З пошуку голосних звуків і поділу на склади
      correct: true
    - text: З читання кожної окремої літери поспіль
      correct: false
    - text: З запам'ятовування форми слова без читання
      correct: false
    explanation: Голосні звуки визначають кількість складів і допомагають прочитати
      слово плавно.
  - prompt: Скільки складів у слові «університет»?
    options:
    - text: '5'
      correct: true
    - text: '4'
      correct: false
    - text: '6'
      correct: false
    explanation: У слові «університет» п'ять голосних звуків (у, і, е, и, е), тому
      п'ять складів.
  - prompt: Як правильно прочитати речення «Мама читає»?
    options:
    - text: Прочитати кожне слово по складах і з'єднати у фразу
      correct: true
    - text: Назвати окремо кожну літеру кожного слова
      correct: false
    - text: Пропустити голосні звуки
      correct: false
    explanation: Читання по складах допомагає об'єднати звуки у плавне осмислене речення.
  - prompt: Що допомагає перевірити кількість складів під час вимови?
    options:
    - text: Долоня під підборіддям на кожному голосному поштовху
      correct: true
    - text: Рахування приголосних літер
      correct: false
    - text: Закривання очей під час мовлення
      correct: false
    explanation: Кожен дотик підборіддя до долоні відповідає одному голосному звуку
      і складу.
  - prompt: Яке слово складається з трьох відкритих складів?
    options:
    - text: молоко
      correct: true
    - text: день
      correct: false
    - text: Львів
      correct: false
    explanation: 'Слово «молоко» має три відкриті склади: мо-ло-ко.'
  - prompt: Як читаємо речення з літерою «ї» в слові «Україна»?
    options:
    - text: Чітко вимовляємо [йі] у складі «ї»
      correct: true
    - text: Читаємо як просте [і]
      correct: false
    - text: Пропускаємо цю літеру
      correct: false
    explanation: Літера Ї завжди позначає два звуки [йі].
- id: act-l3-tf
  type: true-false
  title: Факти про плавне читання
  instruction: Визнач, чи є твердження правильним.
  items:
  - statement: У слові рівно стільки складів, скільки в ньому голосних звуків.
    correct: true
    explanation: Це основне правило українського складоподілу.
  - statement: Приголосний звук сам по собі може утворити склад.
    correct: false
    explanation: Приголосний звук без голосного не утворює складу.
  - statement: Довгі слова легше читати, якщо спочатку розбити їх на склади.
    correct: true
    explanation: Поскладове читання запобігає помилкам у багатоскладових словах.
  - statement: Під час читання речення слова слід об'єднувати у плавний потік.
    correct: true
    explanation: Плавне інтонування робить мовлення природним і зрозумілим.
  - statement: Слово «бібліотека» має три склади.
    correct: false
    explanation: 'Слово «бібліотека» має п''ять голосних і п''ять складів: бі-блі-о-те-ка.'
  - statement: Тест із долонею під підборіддям показує кожен голосний імпульс.
    correct: true
    explanation: Опускання щелепи відбувається на кожному відкритому голосному звуці.
workbook:
- id: act-w5
  type: watch-and-repeat
  title: Повтор голосних
  instruction: Подивися огляд абетки ще раз, потім повтори прості голосні.
  items:
  - letter: А
    sound: '[а]'
    word: ма́ма
    video: https://www.youtube.com/watch?v=ksXIXj7CXwc
  - letter: О
    sound: '[о]'
    word: молоко́
    video: https://www.youtube.com/watch?v=ksXIXj7CXwc
  - letter: У
    sound: '[у]'
    word: ву́лиця
    video: https://www.youtube.com/watch?v=ksXIXj7CXwc
  - letter: И
    sound: '[и]'
    word: ми
    video: https://www.youtube.com/watch?v=ksXIXj7CXwc
  - letter: І
    sound: '[і]'
    word: пі́сня
    video: https://www.youtube.com/watch?v=ksXIXj7CXwc
- id: act-5
  type: quiz
  title: Мініперевірка читання
  instruction: Обери правильну відповідь.
  items:
  - prompt: Склад — що це?
    options:
    - text: лі́тера
      correct: false
    - text: syllable
      correct: true
    - text: greeting
      correct: false
    explanation: Склад — це частина слова з голосним звуком.
  - prompt: Молоко́ — скільки складів?
    options:
    - text: '2'
      correct: false
    - text: '3'
      correct: true
    - text: '1'
      correct: false
    explanation: Молоко́ має три голосні звуки й три склади́.
  - prompt: Яка літера завжди [йі]?
    options:
    - text: І
      correct: false
    - text: И
      correct: false
    - text: Ї
      correct: true
    explanation: Ї завжди читаємо як [йі].
- id: act-l3-wb-odd
  type: odd-one-out
  title: Зайве слово за кількістю складів
  instruction: Знайди слово, яке відрізняється кількістю складів від решти слів у
    рядку.
  items:
  - words:
    - ма́ма
    - та́то
    - ка́ша
    - день
    answer: день
    explanation: День має один склад, тоді як інші слова мають два склади.
  - words:
    - молоко́
    - ву́лиця
    - столи́ця
    - Ки́їв
    answer: Ки́їв
    explanation: Київ має два склади, а інші слова мають по три склади.
  - words:
    - університе́т
    - бібліоте́ка
    - фотогра́фія
    - ка́ша
    answer: ка́ша
    explanation: Каша має два склади, а інші слова мають по п'ять складів.
  - words:
    - Львів
    - сон
    - ліс
    - вода́
    answer: вода́
    explanation: Вода має два склади, а слова Львів, сон і ліс — односкладові.
  - words:
    - люди́на
    - апте́ка
    - пі́сня
    - маши́на
    answer: пі́сня
    explanation: Пісня має два склади, а людина, аптека і машина — трискладові слова.
  - words:
    - так
    - ні
    - дім
    - та́то
    answer: та́то
    explanation: Тато має два склади, а інші слова мають лише один склад.
- id: act-l3-wb-sort
  type: group-sort
  title: Групування слів за кількістю складів
  instruction: Розподіли слова за кількістю складів.
  groups:
  - label: Один склад
    items:
    - день
    - Львів
    - хліб
  - label: Два склади
    items:
    - ма́ма
    - та́то
    - ка́ша
  - label: Три склади
    items:
    - молоко́
    - ву́лиця
    - столи́ця
- id: act-l3-wb-fill
  type: fill-in
  title: Встав пропущене слово в речення
  instruction: Заповни пропуск відповідним словом, яке підходить за змістом.
  items:
  - sentence: Ки́їв — це головна {столи́ця} Украї́ни.
    options:
    - столи́ця
    - ка́ша
    - пі́сня
    explanation: Київ є столицею України.
  - sentence: У сло́ві {молоко́} три відкриті склади.
    options:
    - молоко́
    - день
    - Львів
    explanation: 'Молоко має три склади: мо-ло-ко.'
  - sentence: Ма́ма чита́є чудове {сло́во} у книзі.
    options:
    - сло́во
    - ка́ша
    - так
    explanation: Мама читає слово.
  - sentence: На столі лежить свіже соковите {я́блуко}.
    options:
    - я́блуко
    - ву́лиця
    - абе́тка
    explanation: Яблуко лежить на столі.
  - sentence: Це наша рідна міська {ву́лиця}.
    options:
    - ву́лиця
    - молоко́
    - ні
    explanation: Вулиця — назва міського шляху.
  - sentence: З радіо лунає гарна українська {пі́сня}.
    options:
    - пі́сня
    - та́то
    - день
    explanation: Пісня лунає з радіо.
- id: act-l3-wb-match
  type: match-up
  title: З'єднай слово з моделлю читання
  instruction: З'єднай слово з його поскладовою моделлю читання.
  pairs:
  - left: ка́ша
    right: два склади (ка-ша)
  - left: молоко́
    right: три відкриті склади (мо-ло-ко)
  - left: люди́на
    right: три склади з йотованою ю (лю-ди-на)
  - left: університе́т
    right: п'ять складів (у-ні-вер-си-тет)
  - left: день
    right: один склад із м'яким знаком (день)
  - left: я́блуко
    right: три склади, я позначає [йа] (яб-лу-ко)
- id: act-l3-wb-translate
  type: translate
  title: Читаємо та розуміємо слова
  instruction: Прочитай українське слово та обери правильний переклад.
  items:
  - source: столи́ця
    target: capital
    options:
    - capital
    - street
    - city
    - country
    explanation: Столиця означає capital.
  - source: люди́на
    target: person
    options:
    - person
    - people
    - teacher
    - student
    explanation: Людина перекладається як person.
  - source: ву́лиця
    target: street
    options:
    - street
    - house
    - room
    - city
    explanation: Вулиця означає street.
  - source: я́блуко
    target: apple
    options:
    - apple
    - bread
    - milk
    - water
    explanation: Яблуко перекладається як apple.
  - source: пі́сня
    target: song
    options:
    - song
    - story
    - book
    - letter
    explanation: Пісня означає song.
  - source: абе́тка
    target: alphabet
    options:
    - alphabet
    - word
    - sound
    - syllable
    explanation: Абетка перекладається як alphabet.


## vocabulary.yaml

- lemma: склад
  translation: syllable
  pos: noun
  usage: У сло́ві ма́ма два склади́.
- lemma: голосни́й звук
  translation: vowel sound
  pos: noun phrase
  usage: А - голосни́й звук.
- lemma: при́голосний звук
  translation: consonant sound
  pos: noun phrase
  usage: М - при́голосний звук.
- lemma: чита́ти
  translation: to read
  pos: verb
  usage: Я чита́ю сло́во.
- lemma: писа́ти
  translation: to write
  pos: verb
  usage: Я пишу́ лі́теру.
- lemma: ма́ма
  translation: mother
  pos: noun
  usage: Ма́ма.
- lemma: та́то
  translation: father
  pos: noun
  usage: Та́то.
- lemma: молоко́
  translation: milk
  pos: noun
  usage: Молоко́.
- lemma: я́блуко
  translation: apple
  pos: noun
  usage: Я́блуко.
- lemma: люди́на
  translation: person
  pos: noun
  usage: Люди́на.
- lemma: ву́лиця
  translation: street
  pos: noun
  usage: Ву́лиця.
- lemma: столи́ця
  translation: capital
  pos: noun
  usage: Ки́їв - столи́ця Украї́ни.
- lemma: день
  translation: day
  pos: noun
  usage: День.
- lemma: абе́тка
  translation: alphabet
  pos: noun
  usage: Украї́нська абе́тка.


## resources.yaml

- title: Большакова, буквар 1 клас, p. 25
  role: textbook
  source: Большакова, буквар 1 клас, p. 25
  notes: 'Plan reference: syllable rule; every syllable has a vowel sound.'
- title: Вашуленко, Українська мова 2 клас, p. 23-27
  role: textbook
  source: Вашуленко, Українська мова 2 клас, p. 23-27
  notes: 'Plan reference: transfer, stress, and iotated-vowel reading context.'
- title: Кравцова, Українська мова 2 клас, p. 13
  role: textbook
  source: Кравцова, Українська мова 2 клас, p. 13
  notes: 'Plan reference: hand-under-chin syllable counting check.'
- title: Anna Ohoiko — Ukrainian alphabet overview
  role: youtube
  url: https://www.youtube.com/watch?v=ksXIXj7CXwc
  channel: Ukrainian Lessons
  notes: Supplemental listening support for the vowel reading pass.


## Task

Review the assigned dimension `pedagogical` and return the required JSON object now.
No preamble, no markdown, no questions.
