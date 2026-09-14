# Content Review R2: things-have-gender

**Track:** a1 | **Sequence:** 8 | **Mode:** core | **Tier:** 1-beginner

**Reviewed content SHA:** `b7407cff1d12e52363baa6dcde22f271dc2de8c3`

**Branch:** `codex/cu-p1-upgrade-mode-machinery` | **PR:** #7999 (draft)

**Writer family:** Google/AGY, as assigned in the review brief.

**Actual reviewer:** OpenAI Codex. The dispatch says Anthropic, but this session is not Anthropic. This is a separate-family content check against the assigned Google writer; it cannot attest Anthropic participation or provide non-OpenAI review of the Codex-authored machinery. The requested commit trailer is a task label, not evidence of provider identity.

**Pipeline:** FAIL — fresh verifier: `shippable: false`, `render_fully_validated: false`.

**Verdict:** **C — content requires correction; keep draft.**

## Findings and disposition

No live recurrence of the previous corrupted possessive was found. No new CRITICAL linguistic defect is established. Three HIGH findings remain under the content-review rubric:

1. **HIGH-R2-1 — required vocabulary missing from teaching prose.** The plan requires `комп'ютер` in prose and vocabulary. It exists in L2 vocabulary and workbook act-204/206 (`lesson-2/activities.yaml:236,321`), but not in any of the three `module.md` files, after stress normalization. The previous review's complete-coverage claim was incorrect. Add its source-backed meaning and gender phrase to the teaching sequence before practice; do not change the plan.
2. **HIGH-R2-2 — a valid answer is rejected.** L2 act-w3 item 3 (`lesson-2/activities.yaml:192`) asks `У ___ є телефо́н?` with `тебе́`, `мене́`, `мій`, accepting only `тебе́`. The instruction is merely “Complete the object sentence”; there is no “Do you have” cue. Both personal-pronoun completions are grammatical and differ in meaning. VESUM confirms the respective genitive forms of `ти` and `я`; both possession frames are explicitly taught in this bundle. `FillIn.tsx:84` compares the selected value directly with the single answer, so `мене́` receives negative feedback. Supply a second-person meaning cue or another uniquely answerable prompt. This is inherited content, but preservation does not make an ambiguous key pedagogically sound.
3. **HIGH-R2-3 — teach-before-test is still incomplete inside L2.** `lesson-2/module.md:43` injects act-201 before the noun/possessive observation at line 45. Its six questions include `стіле́ць`, `су́мка`, and `дзе́ркало`, none explained in the preceding room dialogue/support table (lines 13–32). The chair gloss arrives at lines 90–91; the bag dialogue starts at line 47; the mirror has no English gloss in lesson prose. These are now in the correct lesson's vocabulary tab, so the original cross-lesson HIGH-1 is repaired, but the default Lesson-tab path still asks before explaining. Put the relevant presentation/glosses before that quiz, or explicitly guide the learner through the vocabulary first. Do not assume a hidden prior tab visit.

### MEDIUM

- **M-R2-1 — L3 dialogue lacks a follow-up English breakdown.** The new 14-turn conversation (`lesson-3/module.md:55–71`) proceeds straight to act-9/301. Earlier tables translate isolated profession sentences, not the added exchanges such as `А хто твоя́ ма́ма? Вона́ теж лі́карка?` or the final family relationship. Add a concise breakdown after the conversation, following the upgrade writer contract and ULP presentation practice 4. Meeting a dialogue-line count is not comprehension evidence.
- **M-R2-2 — course-default gender is presented as an unrestricted claim in assessment.** L3 prose properly says “course default” for `мій соба́ка`, but act-303 declares `Сло́во «соба́ка» в украї́нській мо́ві — це вона́` false, and act-w4 calls the masculine usage categorical (`activities.yaml:107,166`). VESUM returns both masculine and feminine nominative analyses. Keep the approved masculine beginner chunk; qualify the question/feedback to the course default instead of implying the dictionary has no feminine analysis. ULIF's returned paradigm does not independently resolve that usage distinction. This is not a recommendation to teach a full exception system at A1.
- **M-R2-3 — L1 scaffolding still previews unglossed L2 vocabulary.** The retained ending table (`lesson-1/module.md:104–106`) contains telephone/notebook/key, lamp/room/pen, and bed/mirror examples; the full-module objective preview also promises room/bag speech and professions in L1. These no longer contaminate L1 activities, but the split would be clearer with explicit preview framing and immediate support. Preserve the original content while adding scaffolding.

### LOW / limitations

- L1/L2 recap encouragement now exists, but it is Ukrainian-only: `Чудо́ва ро́бота! ...` (L1:142) and `Чудо́во! ...` (L2:102). A short English gloss would make the encouragement accessible to the nervous beginner it is meant to support. L2 still has little explicit reassurance when the task becomes difficult.
- The new L3 exchange is heavily interrogative (`хто ти`, then sister/brother/mother/father/uncle). It practices the intended forms, but lacks a clear reason for this sequence of questions. L1's move from nearby family to `А це твоє́ мі́сто?` likewise lacks a photo/map or video-call frame. Add a brief anonymous situation cue; do not invent a narrator persona.
- No named narrator/self-introduction remains. The removed L1 lead-in is repaired. Literal “names only inside dialogues” compliance is not complete: inherited prose names Olena/Marko (L1:94), and L3 teaches personal-name exceptions outside dialogue. These are pedagogical examples, not a narrator; the driver should distinguish that scope conflict from persona adoption rather than report a blanket pass.
- The Grade 6 resource entries remain in L2/L3. Their metadata is present, but the textbook retrieval attempts failed, so this review does not certify their contents or repeat the earlier assertion that their language was independently checked. Missing wiki and meta files were not reconstructed.

## Repair-claim verification

| Claim | Evidence at reviewed SHA | Disposition |
|---|---|---|
| L1 no longer drills L2 room vocabulary | Parsed all ten L1 activities and searched 14 room nouns; zero hits. act-2 and act-w1 now sort nine familiar nouns each; act-5 has six familiar examples; act-3 has eight. | Original HIGH-1 repaired; see separate within-lesson issue above. |
| L2/L3 DialogueBox conversion and new L3 dialogue | Each source has 14 `> ` turns. Each assembled MDX has two actual `<DialogueBox>` components and 14 speaker entries. | Verified in source and assembled artifacts; full browser rendering not certified. |
| At least 14 dialogue lines per lesson | L1/L2/L3 each have 14, including L3's new profession/family exchange. | Meets the requested bar. Recorded gate policy requires 13 at this head; neither that value nor any gate was changed. |
| Corrupted `воя́` gone, `моя́` retained | Zero whole-word `воя` hits in all three source/MDX pairs; L1:29 has `моя́`. Sources verifies feminine nominative of `мій` and stress `моя́`. | Verified. Historical review/build records are not learner text. |
| L1/L2 recap warmth added | L1:142 and L2:102 quoted above, present in assembled pages too. | Verified; accessibility polish remains. |
| Earlier `говори́ть` problem repaired | L3 act-w4 now uses `гово́рить`; stress oracle returns that exact form without an override. | Verified. |

## Preservation failures: expected detection, not permission to pass

The fresh `verify_shippable` run reproduces exactly the six known blockers: two original dialogue paragraphs and structural containment failures for act-2, act-3, act-5, act-w1.

**Dialogue paragraphs:** all **10/10 original speaker turns** survive in L2 after stripping stress and dialogue markup: seven in the room exchange, three in the original bag exchange. Four additional bag turns are additive. There is no demonstrated semantic loss in these two paragraphs. Rendering them as DialogueBox is appropriate for the intended learner experience and explicitly follows the upgrade writer instruction to use blockquotes rather than code fences. However, `lesson_gates.py:407` compares Markdown with only stress/whitespace normalization; it correctly rejects changed fences under its current literal contract. This exposes a preservation/representation conflict, not a reason to restore code-fence dialogues or count the failed gate as passed.

**Activities:** the four payloads really changed. The new activities address the cross-lesson sequencing defect, but `docs/lesson-contract.md:54` and `linear-write-upgrade.md` still require every original activity's payload to remain intact. `lesson_gates.py:431` correctly detects the actual loss of structural containment. Activity rescoping is pedagogically justified by the repair request; it is **not automatically compliant with the current preserve-and-expand contract**. The driver owns reconciliation of that contract/provenance with the authorized repair, followed by a fresh build and exact-head review. This review does not authorize new normalization rules, exemptions, altered baselines, or weakened gates.

The remaining 45/47 baseline long paragraphs pass the existing comparison; the two failures are the dialogues above. No duplicate or misplaced long paragraphs are reported. All five hashes in `upgrade_inputs.json` match the current archived four artifacts and plan. The union of 48 vocabulary entries remains allocated 18/16/14 without baseline loss. These checks support preservation of this specific denominator, not general upgrade-mode correctness.

## Plan adherence

| Objective | Coverage | Evidence / limit |
|---|---|---|
| Determine gender with він/вона/воно | YES | L1 noun tables and act-1/2/3/5. |
| Recognize common endings | YES | L1:102–112; rules explicitly say “usually” and introduce male-person exceptions. |
| Name more than 20 everyday objects with gender | PARTIAL | Room/bag vocabulary is practiced, but 34 L1+L2 entries are not 34 objects: that total includes pronouns, grammar labels, people, and phrases. The previous review's denominator does not establish this objective. Required computer is absent from prose. |
| Use У мене є with objects | YES | L2 dialogues, act-4/w3/205/207; ambiguous w3 item needs repair. |
| Five-item diagnostic gender check | YES | L3 act-w5 retains pain, steppe, painting, chronicle, and literary path contexts. They remain diagnostic props, not active-vocabulary expansion. |
| Feminine professions as default for women | YES | L3:12–32 and act-9/301/304. |

### Required vocabulary coverage

| Required form | Prose | Vocabulary YAML | Activities |
|---|---|---|---|
| стіл | YES | L1 | YES |
| книга | YES | L1 | YES |
| вікно | YES | L1 | YES |
| кімната | YES | L2 | YES |
| ліжко | YES | L2 | YES |
| стілець | YES | L2 | YES |
| лампа | YES | L2 | YES |
| телефон | YES | L2 | YES |
| комп'ютер | **NO** | L2 | YES |
| він / вона / воно | YES | L1 | YES |

All major outline themes survive. Additional recap/production sections serve the lesson split. No full adjective declension paradigm was introduced. No pronunciation-video embed is specifically required by this plan. Its wiki reference could not be reviewed because `wiki/` is absent in the assigned sparse worktree.

## Linguistic evidence

Live `mcp__sources__verify_words` batches returned **38/38** and **21/21** found. They cover the central gender nouns, possessives, profession forms, diagnostic nouns, personal pronouns, and selected dialogue/name forms. This is 59 queried forms, not an assertion that every running token or all phrase meanings were verified.

- First batch evidence: `vesum:d119947f00dc6fb918833d4aad340b286ca86f600320c1fc281975226e2ec047`.
- Second batch evidence: `vesum:0a0a5218b61743d1797dc2cbac39d66f2ed4eb0f731085948b168223f9baaee2`.
- VESUM gives `моя` feminine nominative, `моє` neuter nominative; table/book/window have the taught masculine/feminine/neuter analyses. The feminine profession forms are attested feminine nominatives. `Оксано` is an attested vocative of `Оксана`.
- Diagnostic `степ`, `розпис`, `літопис` have masculine analyses; `путь` feminine. `біль` has distinct masculine and feminine homonym analyses, so bare spelling alone is not meaning-specific proof. The pain-context diagnostic is not a reason to collapse homonyms.
- `verify_stress("моя́")` and `verify_stress("гово́рить")`: `status: ok`, `input_mismatch: false`, `override_applied: false`.
- No additional Russianism or ghost-word error was established in the reviewed learner text. Deliberately wrong answer options were read as distractors, not learner models.
- Textbook `search_text` and `get_chunk_context` returned tool failures; СУМ-20 lookup failed, and СУМ-11 returned no result for the requested dog entry. The Ukrainian Lessons infographic fetch timed out. These are evidence limits, not proof that the sources or forms do not exist. No live textbook-rule verification is claimed.

## Tier 1 pedagogical and lesson-split checks

**Lesson Quality Score: 8/10**, a diagnostic human-style rubric judgment, not a replacement for independent pipeline dimensions. Three of the five “Would I continue?” checks pass: quick wins, broadly manageable Ukrainian with English support, and willingness to continue. Teaching-order overload and the ambiguous instruction prevent clean passes on pacing and instruction clarity.

| Check | Result |
|---|---|
| Welcome → preview → present → practice → celebrate | Present across the split. L1 links prior family/greetings; L2 retrieves gender; L3 consolidates. L1/L2 now celebrate at recap; only L3 closes the module. |
| Emotional safety | Scope reassurance in L1 (“Keep the goal small”), frequent small drills, and recap progress markers. Warmth improved; L2 reassurance and recap glossing could improve. No cold-pedagogy auto-fail established. |
| Practice / production | Four inline plus six workbook activities per lesson, with short writing frames at every close. Thirty activities total; largest type share is quiz, 7/30. |
| Activity schema / answers | Fresh deterministic checks find no additional schema blocker. Items were read across all thirty activities; the ambiguous L2 w3 key is a semantic issue the shape check misses. |
| Language practice | Sorting, pronoun choice, possessive completion, and profession pairs exercise Ukrainian form/meaning; diagnostic sentences do not quiz historical facts. |
| Tables and callouts | Tables L1/L2/L3: 7/4/8; tip callouts: 2/1/0. A1 has no callout-count minimum. No >300-word unbroken prose wall identified. |
| Dialogue quantity vs quality | 14 turns per lesson verified; L3 breakdown and situational motivation remain weaker than the count suggests. |
| Lesson duration / size | Recorded prose tokens 1029/716/1061, total 2806; targets 550 each and 2000 total. Estimates 53/48/54 minutes are heuristics, not timed learner evidence. |
| Immersion | Recorded advisory percentages 45.66/61.77/59.33 against 40–55. L2/L3 exceed the advisory range but exposure/unsupported-run checks pass; no band was adjusted. |
| Four tabs / navigation / closure | Assembled lesson artifacts have four tabs, cumulative vocabulary, and lesson navigation; `closes_module: 3`. Landing plus three pages remain drafts. No browser-level usability claim. |
| Attribution / narrator | Resources are separately attributed; no reference-author persona adopted. Source-content verification and literal name-placement caveats are listed above. |
| LLM fingerprint | No repeated generic “In this lesson, we will explore” opening; some repetitive interrogative dialogue and formal Ukrainian metalinguistic instructions remain. |

## Reproducible verification and release boundary

All project commands and Git operations ran in the assigned dispatch worktree:
`.worktrees/dispatch/codex/cu-p1-pilot-rereview-thg-codex`.

```text
git rev-parse HEAD
b7407cff1d12e52363baa6dcde22f271dc2de8c3

git branch --show-current
codex/cu-p1-upgrade-mode-machinery

.venv/bin/python -m scripts.build.verify_shippable a1 things-have-gender --lesson --json
exit: 1
shippable: false
render_fully_validated: false
lesson_python_qg: false (the six preservation blockers above)
mdx_render.index: true (20 JSON.parse island props evaluate)
mdx_render.1: true (12 JSON.parse island props evaluate)
mdx_render.2: true (12 JSON.parse island props evaluate)
mdx_render.3: true (12 JSON.parse island props evaluate)
corpus_hammer_required: true
```

The checker validates assembled island expressions; it does not establish a full Astro/browser pass. Existing QG artifacts also retain `aggregate.verdict: REVISE` with `terminal_verdict: PASS`: minima are 7.5/7.5/7.0 for L1/L2/L3 and 6.5 for module coherence. Those terminal labels cannot be treated as independent pedagogical approval, and this review does not rewrite them.

Only this R2 report is changed. The user explicitly requested this tracked audit deliverable and PR comment; no lesson, archive, plan, gate, or historical R1 artifact was edited. Content fixes belong to the Google/AGY writer; preservation-contract reconciliation and independent machinery review remain with the accountable PR driver. Required CI and exact-head review after any future content change remain outstanding release gates.

**Grade justification:** C replaces the earlier content F because the live corrupted possessive is repaired and the requested activity/dialogue/warmth changes are substantially present. Required prose coverage, a fair answer key, and teach-before-test sequencing still need correction. This is neither an A/B content approval nor a pipeline pass; #7999 must remain draft.
