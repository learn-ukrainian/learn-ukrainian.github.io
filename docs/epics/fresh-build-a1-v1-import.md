# A1-v1 input to the fresh lesson engine

Design for #10881, recorded at 2026-10-16 22:58:09 UTC (`date -u`).
Code anchors use base `066525c9ad3282a3ebedd43a38b31c5b4fe05158`.
Unqualified code filenames below are under `scripts/build/fresh/`.

## Outcome, scope, and owners

Add named repaired A1-v1 blocks to the existing inputs for ONE pilot: position 2,
`sounds-letters-and-hello`, lesson 4 of the map's proposed split, subject to plan
review. Plans, locked packs, word store, Sources MCP and all gates remain required.
A2–B2 and positions 11–55 are unchanged. Positions 1–10 are mapping context only.

Positions 1–7 complete the whole plan/pack stage BEFORE any build
(`docs/epics/fresh-build-build-program.md:74-84`). Only the named pilot then builds,
changing the position-8-first experiment, not its prerequisites. Write NEW plans;
the byte-retired `sounds-letters-and-hello`, `reading-ukrainian` and `special-signs`
plans stay retired (`docs/epics/fresh-build-a1-arc.md:264-270`). The first two slugs
now occupy positions 2 and 5 (`curriculum/l2-uk-en/lesson-plans/a1/_arc.yaml:19-43,86-112`).
The map's ten position/slugs agree with the arc; its primer order/split are proposals.

CTO owns sequencing/review/disposition; a Ukrainian author adapts content,
engine authors implement import/repair, and independent reviewers judge the pilot.

## Frozen grounding

Supplied design evidence, not language authorities; SHA-256 prefixes pin versions:

- `cto-plancrit-2135.md`: `daace53a835669f0`, Blocking 1–4 checked against code.
- `lesson-repair-mode-r3.md`: `4d5cfcc5f0fb7511`, approved applicator behavior.
- `cto-a1map-2040.md`: `3412c755ece69d07`, selections/split.
- `a1v1-m1m2-defects-sol.md`: `96786a28a5787a70`, defects to re-verify.
- `letters-2013/summary.md`: `bbfdc8943f6ec97d`, decoding overload.
- `cto-ohopace-2205.md`: `98a123db34be04e5`, rubric 1–15.
- `cto-sscov-2200.md`: `d41077e811ef40c0`, Standard gaps.

Reuse proves no learning. Plans must restore the map's omitted position-2
stress/intonation from first speech.

## One lesson's baseline

A selection manifest pins position/slug/lesson, new-plan step/activity IDs,
original revision, repository-relative block/item locators, original/repaired-byte
hashes, repair dispositions and mapping/converter version. Repair named defects
before admission. Reject missing, changed, overlapping or unmapped selections.

Use deterministic extraction, then ONE initial writer call for semantic conversion.
With labelled blocks plus normal inputs, the writer adapts content and returns
one complete `lesson-draft-v1` with the NEW plan's structure: `draft_schema`,
`lesson`, `inputs`, `status`, `steps`, `consolidation`, `activities`, `gaps`
(`schemas/lesson-draft-v1.schema.json:8-16`). `writer.py:482-491` validates/persists
this canonical baseline. Missing evidence follows the gap route; no fake ledger
or extra conversion call. Facts need current `ref`/`explains` records. Replace
legacy stress/gloss/example/citation authority with engine references and normal
stress resolution. Track retained/adapted/replaced and new text; keep English support.

Every printed Ukrainian word must use letters taught BEFORE that print
(`docs/epics/fresh-build-a1-arc.md:276-277`). Audit final examples, options, feedback,
captions and gloss expansions with case/stress normalization. `listening.py:72-79`
covers LETTER-CHOICE options only. Add page-wide import admission and reviewer
proof. Supported oral chunks may precede decoding; keep scripts off learner print.
If rendering cannot do that, hold the block, never exempt its spelling.

## Engine boundaries and hashes

| Current anchor | Change |
| --- | --- |
| `path_guard.py:49-52` | Import-stage-only reader for manifest-listed `curriculum/l2-uk-en/a1-v1/` files and pinned pilot identity. Preserve traversal, absolute-path and symlink-boundary rejection (`:37-47`). No general v1, wiki, old-plan or other-level access. |
| `prompt.py:125-135,677-682` | Keep forbidden-path rejection. Add a labelled `A1-v1 repaired baseline input` section with IDs/digest; source paths remain in hashed lineage outside the prompt. Validate selection binding. Scan imported text too; no unlabelled inline bypass. |
| `prompts/lesson-writer.md.j2:5-12,179-185` | Add labelled selection to initial input; return one full draft under binding plan/state/evidence/style. |
| `writer.py:305-324,482-491` | Pass selection initially, persisted baseline for repair. Run check 0 on FINAL augmented bytes before dispatch, including feedback currently appended after the module's check. Apply r3 patches before full-draft validation/persistence. |
| `module.py:54-62,232-272` | Pass selection when dispatching a stale seed. Keep real check-12 currency and writer-seat binding (`:209-212`); never fabricate success. |

No r3 applicator exists today. Insert approved r3 at that writer boundary and
after check 9 (`runner.py:1720-1753`). Repair needs a persisted, green, reviewed
baseline, not initial conversion. Keep r3 pins, freshness, unique targets, synthetic
unit refusal, replace-only/expected-original/frozen-key/gloss guards and canonical/
rendered preservation. Tables, bilinguals, references, dialogues, non-item payloads,
recap and structural fields stay ineligible. Mixed/ineligible findings regenerate.
Keep holds, budgets, rejected-attempt counts, dependency invalidation and independent
current-manifest closure.

BOTH distinct hash sets need import identity:

- Draft `inputs`: SIX keys, `plan_sha256`, `pack_lock`, `words_lock`,
  `lesson_lock_entry_sha256`, `learner_state_sha256`, `style_card_sha256`
  (`schemas/lesson-draft-v1.schema.json:41-72`). Require `import_sha256` in A1
  import mode only, binding selection, repaired bytes and mapping/converter
  version. Edit `schemas/templates/lesson-draft-v1.template.json`, regenerate
  with `gen_draft_schemas.py`, and compute expected values at `cli.py:593-627`
  and `module.py:138-144`.
- Regeneration: FIVE keys, `plan_sha256`, `pack_lock`, `words_lock`,
  `card_sha256`, `prompt_sha256` (`regeneration.py:26,56-64`). Extend import-mode
  `INPUT_KEYS`, `writer_inputs`, task IDs and ledger snapshots/schema
  (`schemas/fresh-regeneration-ledger-v1.schema.json`), including the duplicate
  runner construction (`runner.py:1471-1477`). Non-import identities stay unchanged.
  Output `draft_sha256` stays separate (`runner.py:1806-1808`).

Check 1 compares expected keys only if present (`runner.py:1530-1532`): require
the import key in schema and supply expectations from EVERY entry point. Missing
cannot opt out. Import drift invalidates reuse, review and dependents. Extend r3 upstream-stale comparison while retaining its six checks;
continue hashing actual effective prompt bytes.

## Provenance and gates

Keep span `source` values `record` and `writer_prose`
(`schemas/lesson-provenance-v1.schema.json:107-111`): imported/adapted prose is
`writer_prose`, pack/store expansions are `record`. Keep fix routing
(`assemble.py:80-92`). A validated lineage sidecar joins draft pointers to final
unit keys, labelling origin `a1_v1_import`, original/repaired hashes, locators,
import digest and retained/adapted/replaced disposition. Distinguish new text and
retain patch history without inventing records or span `source` values. Hash
selection/lineage in the manifest (`manifest.py:124-157`) with schema validation.
Missing/stale lineage blocks import manifests; r3 eligibility remains valid.

Every check retains its pass/fail rule, thresholds, budget and routing. Changed
INPUTS (`prompt.py:640-690`; `runner.py:1518-1808`) are:

- 0: labelled selection/digest and final repair/feedback prompt, fully scanned.
- 1–4: adapted schema/hash identity, gaps, NEW-plan structure, activities/keys/models.
- 5–6: assembled draft/lineage and expanded lesson under current sizing rules.
- 7–8: tokens against normal plan/state allowlists, resolver questions/receipts.
- 9: print/provenance under existing stress/render rules, plus r3 preservation.
- 10: unchanged `not_checked: grammar_checker_undecided` (`runner.py:1754`).
- 11–12: adapted local page/interactions and selection/lineage in hashed manifests.

Plan-schema §6 (`docs/epics/fresh-build-plan-schema.md:562-575`) keeps
`plan-validate`, `pack-verify`, coverage, inventory, standard-coverage, stress,
practice, atlas-link, immersion and independent review. Their new inputs are
reviewed plans/packs, adapted lesson/deck/tokens and manifest; rules stay unchanged.
Missing runtime implementation/proof holds a contractual gate, owned by the CTO.

## Listening and blind pilot

`listening.py:21-50` accepts locked pack VIDEO models with URL and declared
letter/sound or learner-word targets. `:53-99` validates keys/taught options.
It offers no arbitrary phrase-audio, TTS or human-recording host. Learn-by-ear
exchanges need matching playable audio, not an alphabet clip. If existing verified
pack videos cannot model the pilot, the CTO must ask the OPERATOR about a new
asset type. This design chooses none; missing audio holds the pilot.

Map lesson 2.4 has relatively high reuse: M1 `module.md:52-75,136-137,175-181`,
`act-1` item 5, `act-4` item 5, `act-9` item 1, adapted `act-3` П/Р/В items and
split `act-5` item 1. Retain decodable rows, replace unreadable example words and
obsolete first-word wording, and add verified frames/practice. Plan review fixes
the three-letter split and taught-before-print inventory.

Before generation freeze SHA-256s of plan, pack, sources, selection, CURRENT
A1-v1 `sounds-letters-and-hello` lesson/activities, rubric and evaluation brief.
Use the complete current comparator, not repaired import. Disclose module-sized
scope; judge fixed one-lesson tasks/starting state, without post-result cropping
or matched-size learning claims. Fresh non-author Opus 5.5, Sol 6.1 and Gemini
Flash seats independently judge randomized A/B with Sources access. Hide origin,
hypothesis, writer and defect list. A custody key binds artifact hashes. Seal
scores before sharing them or revealing lineage for source verification.

The Standard is the normative floor; OHO rules are the pilot rubric.
Standard anchors in `docs/l2-uk-en/UKRAINIAN-STATE-STANDARD-2024.txt`: listening
§1.1.1 `:230-250`, supported writing §1.3.1.1 `:342-351`, dialogue §1.4.2 `:431-433`,
greetings `:453-460`, ready models `:562-567`, alphabet §4.1.1 `:571-572`, stress
§4.1.5 `:586`, intonation §4.1.8 `:596`. Judge the assigned slice; deferred clauses
retain owners. Rule 9's later recycling uses reviewed next-lesson/recap plans,
explicitly distinguished from unbuilt behavior.

Score every OHO row: 1, maximum three new letters; 2, maximum one grammar slice,
none beside new letters; 3, hear/example/practise/produce; 4, example-led note
shorter than model; 5, language-use answers, not terminology; 6, minimum four sets,
drills of 5–16 items, listening, own voice and assigned writing; 7, four modes per
letter and decodable print; 8, maximum 12 required phrases on conversation lessons;
9, model/practice/later recycling; 10, 4–6 conversation turns; 11, recap adds nothing
and mixes two earlier lessons; 12, meaningful contrast; 13, unscored worked item
and all valid answers; 14, taught-slip correction with a written Ukrainian answer; 15, English instructions
and own-voice production. Freeze applicability with reasons before generation.
These comparison criteria change no engine gate.

Success requires every existing gate, no unresolved material defect, and BETTER
from all three reviewers without required correctness/coverage loss. Tie, worse,
disagreement or missing proof is not better. If not better, the fresh engine is
NOT used for A1. Do not try another lesson seeking a win. A win permits a later
adoption decision, not rollout certification. Pages still needs current GO.

## Contract revision owed

Only the requirements exception changes here. The CTO owns a separate
design-revision PR with two independent seats before implementation
(`docs/epics/fresh-build-build-program.md:63,94`). This inventory identifies each
affected sentence by its opening words and original lines; it does not edit them:

| Sentence locator | Revision owed |
| --- | --- |
| Requirements `:11-13`, "`--upgrade` (preserve and expand an old module) is abandoned..." | Qualify preservation for A1 input; old command remains abandoned. |
| Requirements `:13-14`, "Curriculum upgrade now means an upgraded build engine..." | Add labelled input; new plans and the following layout sentence remain true. |
| R-26 `:152-154`, "A lesson writer receives that lesson's plan entry..." | Add A1 input. No-search and post-draft MCP verification remain. |
| Plan schema `:552`, "The four inputs below are unchanged." | Qualify for A1 import. |
| Plan schema `:554-557`, "Exactly four things: the lesson's plan entry..." | Add labelled selection/baseline. |
| Plan schema `:557`, "Not the other lessons' plans, not the whole pack, not any earlier edition." | Qualify earlier-edition material only. |
| Plan schema `:590`, "No v1 plan is converted." | Still true for PLANS; clarify scope of "Start clean". |
| Plan schema `:590-591`, "v1 plans stay on disk as the record of `/a1-v1/`..." | Engine still cannot read old plans. Material import is distinct. |
| Plan schema `:591-592`, "The arc author may look up which textbook pages they cited..." | Citation re-verification remains required. |
| Writer contract `:7-8`, "The writer receives exactly four things..." | Add A1 input and conversion/repair distinction. Other sentences retain call count, no-search, binding structure and recap inputs. |

R-10/R-11 stay verbatim under the added exception. The follow-up also reconciles
the runbook's position-8-first experiment with this one-lesson trial.

## Later falsifiers and completion

No test applies to this docs-only change. Later implementation must prove:

- Seed without check-12 ledger: a fake writer overwrites it TODAY
  (`module.py:232-272`); integration passes selection without bypassing currency.
- Wrong-level/unlisted paths, old plans, wiki, traversal, symlinks and byte drift
  fail before dispatch. New-plan structure and evidence gaps remain binding.
- Untaught letters outside listening choices fail final-print admission;
  oral chunks without matching playable audio hold.
- Mutate each six-key draft input, ledger key and import digest; missing hashes,
  stale lineage/repairs/converter invalidate reuse/manifests/review. Non-import
  behavior/identity stays unchanged.
- Execute ALL r3 fixture/mutations, including preservation, refusals, budgets,
  dependencies and independent resolution. Its green precondition is unproved.
- Imported/repair/feedback paths and uncited IDs fail check 0 on FINAL bytes before
  payment. Every check 0–12 and §6 failure fixture retains its outcome.
- Anonymization preserves comparator hashes; tie/worse/missing judgments stop use.

Delivery is two docs committed/pushed for CTO review. Residual owner: CTO for
contract revision, implementation/tests, plans/packs, audio question and blind pilot.
Inability to preserve any gate requires REQUEST_CHANGES.
