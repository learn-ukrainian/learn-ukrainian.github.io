# A1 M1-M7 Retrofit Audit

> Scope: audit and classification only for A1 modules 1-7. This report applies
> `docs/pedagogy/a1-a2-core-retrofit-audit.md` and does not rewrite plans,
> wikis, lessons, activities, vocabulary, resources, or generated artifacts.

## Verdict

- Status: ready for plan, wiki, prompt, and rebuild scoping; not ready for
  lesson regeneration.
- Smallest safe rewrite layer: prompt/rule guidance plus M5-M7 plan repair,
  then wiki/support repair for M1-M7.
- Main risk: rebuilding directly from current inputs will reproduce the
  English-led A1 artifact shape and under-specify listening, handwriting,
  lawful media, recycling, and teacher-feedback support.

## Evidence Checked

- Retrofit protocol and templates:
  - `docs/pedagogy/a1-a2-core-retrofit-audit.md`
  - `docs/pedagogy/a1-a2-retrofit-template.md`
  - `docs/pedagogy/a1-a2-lesson-construction.md`
  - `docs/pedagogy/commercial-source-policy.md`
- Source-of-truth plans:
  - `curriculum/l2-uk-en/plans/a1/sounds-letters-and-hello.yaml`
  - `curriculum/l2-uk-en/plans/a1/reading-ukrainian.yaml`
  - `curriculum/l2-uk-en/plans/a1/special-signs.yaml`
  - `curriculum/l2-uk-en/plans/a1/stress-and-melody.yaml`
  - `curriculum/l2-uk-en/plans/a1/who-am-i.yaml`
  - `curriculum/l2-uk-en/plans/a1/my-family.yaml`
  - `curriculum/l2-uk-en/plans/a1/checkpoint-first-contact.yaml`
- Support packets:
  - `wiki/pedagogy/a1/sounds-letters-and-hello.md`
  - `wiki/pedagogy/a1/reading-ukrainian.md`
  - `wiki/pedagogy/a1/special-signs.md`
  - `wiki/pedagogy/a1/stress-and-melody.md`
  - `wiki/pedagogy/a1/who-am-i.md`
  - `wiki/pedagogy/a1/my-family.md`
  - `wiki/pedagogy/a1/checkpoint-first-contact.md`
  - `curriculum/l2-uk-en/a1/discovery/*.yaml` for the seven module slugs
- Built artifacts inspected read-only:
  - `curriculum/l2-uk-en/a1/{slug}/module.md`
  - `curriculum/l2-uk-en/a1/{slug}/activities.yaml`
  - `curriculum/l2-uk-en/a1/{slug}/vocabulary.yaml`
  - `curriculum/l2-uk-en/a1/{slug}/resources.yaml`
- Prompt and review guidance:
  - `scripts/build/phases/v6-write.md`
  - `scripts/build/phases/v6-review/v6-review-actionable.md`
  - `scripts/build/phases/v6-review/v6-review-naturalness.md`
  - `scripts/pipeline/module_archetypes.py`
  - `docs/rules/global-friction.yaml`

## Slice Findings

- Current monitor state for M1-M7 is `pending`, `audit:not_run`,
  `pipeline_version:unbuilt`, and `needs_rebuild:true`.
- Current built lessons are English-led. They generally open with English
  titles and English explanatory framing, even when the plan intent is early
  Ukrainian literacy or first-contact speech.
- A1 stress marks are a deterministic post-review requirement. The retrofit
  must ensure the annotate step and review gates still enforce all-word A1
  stress coverage after rebuild, while keeping plans stress-free where the
  existing plan checker requires it.
- The generated module and activity files do not show a stable pattern of
  Ukrainian-first micro-prompts such as short Ukrainian commands, labels, or
  repeated learner-inference prompts before English explanation.
- No M1-M7 built artifact currently provides a consistent handwriting or
  cursive-recognition path before production.
- No M1-M7 built artifact currently has local visual, audio, video, transcript,
  or image files tracked. Existing resources are text references or public-link
  style resources, so the media gap is pedagogical capacity debt rather than
  an IP violation in the current diff.
- Activities are structurally safe at the YAML root level, but they largely
  inherit English-led prompting and do not yet supply the retrofit progression:
  recognition -> controlled practice -> guided short production.
- Vocabulary and module word-count targets should remain one-sided minimums.
  The rebuild should audit whether M1-M7 supply enough useful, recycled
  beginner vocabulary for the first-contact slice, but must not chase an
  arbitrary vocabulary-volume quota or import an external sequence.
- M5 and M7 contain the blocking plan-level language-risk debt in this slice.
  The issue is not that the questioned forms are nonexistent; the issue is
  that early A1 plans frame register and official-use contrasts too bluntly for
  learners. M6 is already more nuanced in its locked plan, but its wiki/support
  packet and reusable prompt/rule guidance still need alignment so later agents
  do not reintroduce overcorrection.
- Existing project rule `gf-012` already permits natural memorized chunks before
  formal grammar. Therefore chunks such as name, origin, and possession frames
  are not plan defects by themselves. The repair need is to keep them as chunks,
  avoid grammar analysis, and make that treatment explicit where later agents
  might over-audit them.
- Prompt/review guidance still tells A1 writers and reviewers to accept
  English-dominant output. That guidance conflicts with the new retrofit
  standard and must be repaired before rebuilding.

## Per-Module Classification

| Module | Plan debt | Wiki/support-doc debt | Module lesson-content debt | Activity/practice debt | Vocabulary/recycling debt | Media/audio/visual/cursive debt | Teacher-feedback/conversation debt | Prompt/template/generation-guidance debt | Classification |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M1 sounds, letters, hello | No blocking current plan debt found. Old language issues appear fixed in current teaching content. | Needs compact retrofit packet and stronger first-contact support for Ukrainian-first page entry. Discovery packet is thin. | Current lesson is explicitly English-led and should not be treated as a valid retrofit output. | Needs recognition-first Ukrainian prompt shapes and controlled responses before short production. | Needs clearer recycling hooks from alphabet, greeting, and first words into M2-M4. | Needs lawful visual letter support, listening support, and cursive/handwriting recognition. | Needs teacher/tutor pronunciation and first greeting feedback path. | Current A1 generation guidance would reproduce English-led prose. | Ready for wiki and prompt repair before rebuild. |
| M2 reading Ukrainian | No blocking current plan debt found. | Needs retrofit packet for decoding, stress support, and learner-error risks. | Current lesson is English-framed rather than print-first Ukrainian input. | Needs read/match/sort progression before learner production. | Needs letter and word-reading recycling into M3-M4 and checkpoint review. | Needs lawful audio, visual print support, and cursive exposure. | Needs teacher/tutor feedback for decoding, stress, and rhythm. | Prompt guidance must require print-first and listening-supported scaffolds where feasible. | Ready for wiki and prompt repair before rebuild. |
| M3 special signs | No blocking current plan debt found. | Needs clearer compact packet for soft sign, apostrophe, and verified example selection. | Current lesson is English-led and does not normalize Ukrainian prompts. | Needs recognition and controlled contrast work before short production. | Needs verified sign and spelling-pattern recycling into M4 and M7. | Needs lawful audio, visual contrast support, and handwriting recognition. | Needs teacher/tutor feedback for spelling-pronunciation contrast and fossilized error prevention. | Prompt/review rules must prevent English explanation from replacing contrast practice. | Ready for wiki and prompt repair before rebuild. |
| M4 stress and melody | No blocking current plan debt found. | Needs explicit listening-first support packet; stress and intonation cannot be taught safely as text-only explanation. | Current lesson is English-framed and underserves pronunciation/listening. | Needs listen-before-read, mark-what-you-hear, repeat, and controlled repair tasks. | Needs stress recycling from M1-M3 into M5-M7. | High audio/listening debt; lawful audio or link/embed strategy required. Cursive recognition still absent. | Needs teacher/tutor correction for stress, rhythm, and intonation. | This is pipeline/review debt as well as module debt because text-only generation cannot satisfy the lesson job. | Needs prompt/media strategy first, then wiki repair, then rebuild. |
| M5 who am I | Blocking plan debt: a zero-word summary section and over-blunt register framing around family/name terms. | Wiki/support packet has stale or overly absolute wording and should align with dictionary-grounded register nuance. | Current lesson is English-led and cannot carry the intended first-contact immersion. | Needs recognition -> controlled self-introduction -> short production with model answers. | Needs recycling of greetings, letters, stress, and name/origin frames without importing broad new grammar. | Needs lawful visuals for identity/origin contexts, listening models, and handwriting recognition of known words. | Needs teacher/conversation feedback for names, origin lines, and short self-introduction. | Prompt/rule guidance should preserve memorized chunks under `gf-012` and avoid over-auditing them. | Ready for plan repair plus wiki/prompt repair before rebuild. |
| M6 my family | No blocking current plan debt found; current plan already avoids the earlier overcorrection around family terms, but should be preserved during later alignment. | Wiki appears broader than the current early-family scope and needs tighter retrofit packeting plus register nuance aligned to the locked plan. | Current lesson is English-led and not a safe final output for family-language onboarding. | Needs photo/relationship recognition, controlled family sentences, and short speaking/writing frames. | Needs family vocabulary recycling and careful handling of natural possession chunks without case analysis. | Needs lawful family-image strategy, audio models, and handwriting recognition for family labels. | Needs teacher/conversation feedback for family introductions and pronunciation. | Register guidance belongs in global rule/prompt guidance, not only this module, so future modules do not undo the plan nuance. | Ready for wiki/prompt repair before rebuild. |
| M7 first-contact checkpoint | Blocking plan debt: checkpoint still inherits over-blunt family/name-register contrasts and needs policy on checkpoint word target/focus. | Wiki/support packet has stale verification notes and should become a compact checkpoint evidence packet. | Current checkpoint is English-framed despite Ukrainian-first intent. | Needs cumulative recognition, controlled review, short production, and feedback loops across M1-M6. | Needs deliberate recycling map for letters, sounds, stress, greeting, identity, and family language. | Needs listening checkpoint, lawful visual prompts, and handwriting recognition review. | Needs teacher/tutor conversation checkpoint path, not just self-study answers. | Prompt/review guidance must define how A1 checkpoints assess immersion without overload. | Ready for plan and wiki repair before rebuild. |

## Protocol Debt-Class Mapping

The table above keeps the expanded layer names requested for issue #2480. For
the canonical retrofit protocol, map them as follows:

| Requested layer | Canonical debt class |
| --- | --- |
| plan debt | Plan debt |
| wiki/support-doc debt | Wiki debt |
| module lesson-content debt | Module/activity debt |
| activity/practice debt | Module/activity debt |
| vocabulary/recycling debt | Vocabulary/resource debt |
| media/audio/visual/cursive debt | IP/media debt when source or licensing is unsafe; otherwise Wiki debt or Module/activity debt |
| teacher-feedback/conversation-practice debt | Wiki debt when packet guidance is missing; Module/activity debt when practice artifacts are missing |
| prompt/template/generation-guidance debt | Pipeline/review debt |

## Cross-Cutting Debt

### Plan Debt

- M1-M4 plans are not blocking this retrofit slice.
- M5 needs plan repair for the zero-word summary section and register-sensitive
  name/family framing.
- M6 does not need blocking plan repair in this slice. Preserve its current
  nuance around family terms, and make the wiki/prompt guidance explicit enough
  that possession chunks remain memorized language under `gf-012`.
- M7 needs plan repair for inherited register contrasts and for checkpoint
  word-target/focus policy.

### Wiki/Support-Doc Debt

- All seven modules need compact retrofit evidence packets that explicitly
  cover Ukrainian-first entry points, controlled English, visual/audio support,
  handwriting recognition, cognitive load, recycling, and teacher-feedback
  opportunities.
- Auto-discovery packets for this slice are thin and do not substitute for
  retrofit support packets.
- M5-M7 support docs need register nuance grounded in project source tools,
  avoiding both Russian-shadow overcorrection and beginner overexplanation.

### Module Lesson-Content Debt

- Current lessons are outputs of the older English-led approach. They should
  not be patched around source debt.
- Rebuilds should wait until source-of-truth plans, support packets, and
  generation/review guidance are aligned.

### Activity/Practice Debt

- Activity YAML shape is structurally safe, but task language and sequencing
  should be rebuilt after source repair.
- The retrofit target is a visible progression from recognition to controlled
  practice to guided short production in every module.

### Vocabulary/Recycling Debt

- M1-M4 need stronger documented recycling into M5-M7.
- M5-M7 need a clear rule for early family/name terms: teach common beginner
  defaults, but frame alternate attested forms as register/meaning context, not
  as nonexistent Ukrainian.
- Memorized chunks are allowed under `gf-012`; the debt is missing alignment
  language, not the presence of natural chunks.
- M1-M7 should be checked during rebuild for useful beginner vocabulary density
  and cross-module recycling against plan minima, without adding a maximum or
  a fixed external vocabulary quota.

### Media/Audio/Visual/Cursive Debt

- There is no current tracked media/IP violation in this slice.
- There is also no adequate media plan for the retrofit standard.
- M4 has the highest audio debt because stress and melody need lawful listening
  input, not text-only prose.
- All seven modules need a lawful handwriting/cursive recognition path before
  asking for production.
- Handwriting and cursive samples must be original project work, generated
  assets, licensed fonts, or other properly licensed material. Do not imitate,
  extract, trace, or preserve third-party workbook penmanship samples.

### Teacher-Feedback/Conversation-Practice Debt

- Every module in this slice needs an explicit native Ukrainian teacher, tutor,
  or conversation feedback opportunity.
- M1-M4 should prioritize pronunciation, stress, rhythm, and script reading.
- M5-M7 should add short speaking/writing feedback for self-introduction,
  family descriptions, and cumulative first-contact conversation.

### Prompt/Template/Generation-Guidance Debt

- Existing A1 writing and review prompts still accept English-dominant A1
  output, which conflicts with the retrofit standard.
- A1 stress annotation is part of the pipeline contract. Rebuild readiness
  should include deterministic checks that A1 prose and vocabulary receive the
  required stress marks after review, while plans remain stress-free.
- M4 audio/listening support is not only module debt; generation and review
  guidance need a way to require lawful audio/link/listening scaffolds where
  the lesson job depends on sound.
- Family/name register rules should be codified globally or in prompt/rule
  guidance before M5 and M7 plans are repaired, so later A1/A2 modules do not
  repeat the same overcorrection.
- Prompt fixes should be backed by deterministic audit or review gates where
  practical, especially for Ukrainian-first starts, controlled English, stress
  annotation, and root-level activity structure.

## Language-Risk Grounding

- Project word-form and dictionary tools confirm that the questioned family and
  name terms are not a simple present/absent issue.
- Historic and modern-source checks support a nuanced repair: prefer stable
  beginner defaults and official-use forms in learner output, but do not teach
  learners that every alternate attested form is nonexistent Ukrainian.
- Style/error searches did not justify stronger claims than register,
  official-use, or meaning-context distinctions for this slice.
- No paid source, proprietary example, exercise, sequence, screenshot, audio,
  transcript, or private path was used in this audit.

## Recommended Repair Order

1. Plan-level and rule/prompt fixes for issue #2713.
   - Add or update global rule/prompt guidance for early A1 register contrasts
     and Ukrainian-first generation.
   - Add deterministic audit/review coverage where practical for Ukrainian-first
     starts, controlled English, A1 stress annotation, and other repeatable
     gates; do not rely only on writer prose instructions.
   - Repair M5 and M7 plan defects, and preserve M6's existing plan nuance.
   - Keep natural memorized chunks as allowed under `gf-012`.
2. Wiki/support fixes for issue #2713.
   - Create compact retrofit packets for M1-M7.
   - Add lawful media, audio/listening, handwriting recognition, review, and
     native-teacher feedback specifications.
   - Specify that handwriting/cursive samples must be original, generated, or
     properly licensed, with no extracted or imitated third-party penmanship.
   - Tighten M5-M7 support docs so register guidance is nuanced and reusable.
3. Module/activity/media rebuilds for issue #2714.
   - Rebuild M1-M7 only after the upstream sources and prompts are repaired.
   - Rebuild lessons, activities, vocabulary/resource roles, and media plans
     as one coherent first-contact slice.
   - Preserve IP boundaries: original, generated, public-domain, properly
     licensed, or lawfully linked media only; no copied source material.

## Acceptance Checks Before Rewrite

- [x] Audit happened before rewriting.
- [x] Findings are classified by debt layer.
- [x] Ukrainian-first immersion, controlled English, multimodal support,
      pronunciation/reading, handwriting recognition, review cadence,
      cognitive load, and teacher-feedback needs are checked.
- [x] Language-risk claims are tool-grounded or kept at the proper level of
      certainty.
- [x] Lawful media/IP status is clear.
- [x] No lesson regeneration happened in this audit slice.
