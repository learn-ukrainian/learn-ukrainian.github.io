---
date: 2026-10-01
task: revise-a1-p1-p3
issue: 8425
status: stopped
base_sha: f7c5761f5952c2dcbf2cb17cdcd2e3c4498356f6
owner: accountable curriculum driver for issue 8425
---

# A1 positions 1–3 revision: unsupported recap host

STOP: the required first-person bilingual-story comprehension operation has no allowed compatible host on the supplied base or in the inspected proposed listening implementation. This is an engine binding gap, not a claim that the source corpus lacks pedagogical material. No plan, request YAML, pack, word record, scope, grammar entry, approval or manifest was modified. Only this request note is delivered. The requested revised package is **not accepted**.

- Intake: clean `codex/revise-a1-p1-p3` at the exact required base; assignment confirms an authoring worker, no merge authority. No workers, writer calls, lesson builds, plan review, promotion, PR or merge were started.
- Denominator: three plans, 20 lessons, 136 planned activities (35 / 48 / 53); zero revised plans and zero newly verified activity families. Baseline deterministic plan validation is distinct from buildability.
- The STOP follows the brief's explicit prohibition on relabeling a writer-authored bilingual story as a dialogue or quote. Recap shape remains one first-person bilingual story, Ukrainian-only questions about it, and one offline production task (plan schema §2b).
- Residual owner: the #8425 accountable driver. All nine inherited open U-groups remain open; none was resolved or silently removed. No conversion ledger or complete decodability audit is claimed.
- Independent held-out proof: none. Playback and target correspondence, integrated exact-head compatibility probes, publication-registry identity, plan reviews and regeneration of stale manifests remain driver work.
- Entire Context skill: `status` available; bounded `search --query 8425 --limit 5` yielded an unrelated Git locator. It did not inform the decision; no consumption receipt was claimed.

## Reproducible boundary and live dependency evidence

Commands ran from the assigned dispatch worktree. The project interpreter and source-database paths were the exact ones prescribed by the dispatch; public examples below use private environment variables for those absolute paths.

```bash
git log -1 --format='%H %s'
git status --short
git ls-remote --heads origin 'codex/impl-a1-listening-host*' 'codex/impl-wp21-publication-right*'
```

The base head was `f7c5761f5952c2dcbf2cb17cdcd2e3c4498356f6`, with empty status. The remote returned only `codex/impl-a1-listening-host-fin2` at `fc02b4af5f0ad54fbd88f2411a60bd2fb524d501`. No publication-right branch matched that query; its reviewed implementation and registry identity are therefore unverified here, not presumed absent from the project. The original listening task's current status was `needs_finalize`; that status is not review approval. No unrelated worktree was reaped.

Read `scripts/build/fresh/runner.py` (`_host_eligible`, `check_7_a1_choices`), `preflight.py`, `schemas/activities-a1.schema.json`, and `docs/epics/fresh-build-writer-contract.md` §1a/§1e. On this base:

- A comprehension host's kind is closed to `dialogue | quote`.
- A dialogue needs the plan's actual `dialogue` and a preceding dialogue block.
- A quote needs its exact T-ref displayed before the activity. Grounding through `explains` does not display a quote.
- A bilingual block is supported as presentation but is not a comprehension host.
- A quote need returns a publication-right gap before WP21 integration. ULP premium notes remain grounding only even after public school textbook rights are integrated.

The following read-only Python probe called the actual A1 choice check for each real recap lesson, using a structural stimulus only (no lesson artifact, model call, source mutation or semantic answer claim):

```python
from pathlib import Path
from types import SimpleNamespace
import yaml
from scripts.build.fresh.runner import check_7_a1_choices, _host_eligible

root = Path("curriculum/l2-uk-en")
for slug in ("sounds-letters-and-hello", "reading-ukrainian", "special-signs"):
    plan = yaml.safe_load((root / "lesson-plans/a1" / f"{slug}.yaml").read_text())
    recap = plan["lessons"][-1]
    draft = {
        "steps": [{"id": "s1", "blocks": [
            {"kind": "bilingual", "uk": [], "en": []},
            {"kind": "activity", "ref": "a2"},
        ]}],
        "activities": [{"id": "a2", "items": [{
            "kind": "comprehension",
            "host": {"kind": "bilingual", "ref": "s1"},
        }]}],
    }
    print(slug, _host_eligible({"kind": "bilingual"}, draft, recap, "a2"))
    print(check_7_a1_choices(
        draft, recap, {"words": []}, SimpleNamespace(tokens=[]),
        state_dir=root / "evidence/a1/_requests", lesson_n=recap["n"],
        sources=object(),
    ))
```

All three printed `False` and:

```json
{"check":7,"status":"failed","code":"comprehension_host_ineligible","reason":"comprehension_host_ineligible","layer":"writer","activity":"a2","token":"0"}
```

Separate host probes for a dialogue without a planned dialogue, and the ULP note T-ref without a displayed quote, also returned false in all three recaps. These negative probes establish the current boundary; they do not prove that no future compatible representation can be implemented.

The schema probe used `Draft7Validator` on an activity **array**: an ordinary `comprehension` quiz with a `quote/T-005` host had `errors: []`; replacing the host with `bilingual/s1` returned `valid: false`. The schema-valid quote shape does not certify rights or content.

Read the proposed implementation without importing or merging its tree:

```bash
git show codex/impl-a1-listening-host-fin2:scripts/build/fresh/listening.py
git show codex/impl-a1-listening-host-fin2:tests/build/test_fresh_listening.py
```

Its `model_target` admits a learner-usable W-record lemma, or a T-record whose first line is exactly a capital/small letter heading, plus an exact video model declaration. The extracted function was executed read-only against the supplied reading pack and word store. With V-004, T-016 (story), T-017 (questions), and composite W-075+W-076 each returned `(None, "listening_target_invalid")`. This does not challenge the episodes' existence; it proves that those targets do not have the inspected implementation's supported shape. Neither story comprehension nor spoken multiword question/answer options is thereby admitted.

## Buildability / before-after at the stopping boundary

No activity was changed. The required operations below are retained unchanged, not claimed buildable.

| Position / activity | Type / placement | Learner operation | Host before → host after | Required binding / order | Witness / disposition |
| --- | --- | --- | --- | --- | --- |
| 1 / L6 a2 | quiz / inline | Answer Ukrainian-only questions about the first-person bilingual story | Writer bilingual story with T-005 methodology → unchanged | Comprehension needs a real eligible host before a2; quote from premium T-005 is prohibited | Actual check 7 fails; no accepted witness |
| 2 / L6 a2 | quiz / inline | Hear the source story and the first three questions/answer options | V-004 plus displayed T-016/T-017 notes → unchanged | Public episode playback must precede a2; T-016/T-017 only through explains; story and spoken-answer binding required | Proposed listening target rejects story/questions; no accepted witness |
| 3 / L8 a2 | quiz / inline | Answer substantive Ukrainian-only questions about the writer's first-person bilingual story | Writer bilingual story with T-020/T-021 methodology → unchanged | Printed options are permitted, but still need a compatible comprehension host before a2 | Actual check 7 fails; no accepted witness |

No recap was turned into an exchange, source quotation, vocabulary quiz or generic sound check. That would change the required operation rather than supply its host. No learner-facing note quote was authorized. All other activity families and source displays remain unaudited for the revised-package acceptance criterion; the table is a precise stopping-boundary report, not an all-activity compatibility claim.

## Source searches and what still works

Live MCP calls were successful:

| Tool / query | Observed evidence | Role / limit |
| --- | --- | --- |
| get_chunk_context: 1-klas-bukvar-zaharijchuk-2025-1_s0027 | 282-character peer-greeting page, source title page 31 | Supports the expressly authorized greeting dialogue candidate; not the required recap first-person story |
| get_chunk_context: 5-klas-ukrmova-zabolotnyi-2023_s0001 | 301-character alphabet-table chunk, source title page 2 | Confirms the printed letter-name source is available; no audio playback proof |
| search_external: `"review" "first" "story"`, ulp_youtube, max_results 5 | ext-ulp_youtube-294 (ULP 1-10) plus 274, 248, 284, 297 | Positive discovery evidence for public review recordings; not an engine story binding or a right to quote premium notes |
| search_text: `"Я" "мама"`, bukvar, exact part-1 primer, limit 5 | s0091, s0087, s0031 | Existing narrative/dialogue material, not verbatim attestation of the custom literacy recap or authorization to replace its outcomes |
| search_text: `"Привіт"`, exact part-1 primer | No FTS hits; direct s0027 lookup did return the greeting page | Search-index absence is not corpus absence; direct source lookup controls |

Further exact-target discovery searches used `search_external` on `"тин" OR "тінь" OR "джміль" OR "дзиґа"` and `"рука" OR "ріка" OR "апостроф" OR "letter names"`, channel ulp_youtube. Hits were discovery only; no missing-recording claim was resolved and no scoring target was certified. The prior full catalogue search remains in `listening-sources.md`; its assertions were not renewed as this worker's exhaustive audio search. Local inspection identified the resources catalogues and their ULP entries.

The live tool list does not expose `search_resources`. This search is unavailable in this seat, distinct from an empty query. Driver condition: land the #9409 ingestion/tool implementation and expose it through the current sources MCP, then run the requested catalogue searches. No fallback tool was represented as that search.

The corpus is available, the alphabet and greeting candidates are retrievable, and the word store verifies. The unmet requirement is compatible hosting of the required recap operation. No new architecture or teaching-shape decision was taken.

## Baseline gate tails

Read-only baseline checks were run for all three positions; no `--write-report`, `--write-scope`, offline weakening, or promotion was used:

```bash
"$PROJECT_PYTHON" -m scripts.curriculum.evidence words-verify a1 --sources-db "$SOURCES_DB" --vesum-db "$VESUM_DB"
"$PROJECT_PYTHON" -m scripts.curriculum.evidence pack-verify a1 <slug> --strict --sources-db "$SOURCES_DB" --vesum-db "$VESUM_DB"
"$PROJECT_PYTHON" -m scripts.curriculum.validate a1 <slug> --provisional-pack
```

### Position 1: sounds-letters-and-hello

`words-verify a1` (shared): exit 0, `status=OK`, 153 records / 1762 forms; 166 pending forms and 4 override forms remain reported, not learner admission proof.

`pack-verify a1 sounds-letters-and-hello --strict`: exit 1.

```text
ERROR: open_unsupported: 1 unsupported records open: ['U-001']
Evidence Pack Verification: module=a1/sounds-letters-and-hello status=FAILED
Verified: texts=21, exercises=5, examples=0, errors=0, notes=0, videos=16, standard=3
Unsupported: 1 open, 0 resolved
REPORT: open_unsupported: 1 unsupported records open: ['U-001']
```

`plan-validate a1 sounds-letters-and-hello --provisional-pack`: exit 0.

```text
status: pass
mode: provisional
NOTE core_cefr_above_module: lesson 2: core lemma 'звук' (W-077) is A2 in the word store, 1 band above the module's level A1 (gate M5)
NOTE core_cefr_above_module: lesson 2: core lemma 'літера' (W-078) is A2 in the word store, 1 band above the module's level A1 (gate M5)
NOTE core_cefr_above_module: lesson 3: core lemma 'голосний' (W-079) is A2 in the word store, 1 band above the module's level A1 (gate M5)
NOTE core_cefr_above_module: lesson 3: core lemma 'приголосний' (W-080) is A2 in the word store, 1 band above the module's level A1 (gate M5)
NOTE core_cefr_above_module: lesson 4: core lemma 'малина' (W-082) is A2 in the word store, 1 band above the module's level A1 (gate M5)
NOTE core_cefr_above_module: lesson 4: core lemma 'слива' (W-083) is A2 in the word store, 1 band above the module's level A1 (gate M5)
NOT_CHECKED minutes_constants_undefined: not_checked: minutes is computed, and the constants it needs do not exist yet (§2a)
NOT_CHECKED word_target_not_calibrated: not_checked: word_target presence and type are checked; the per-level minimum is not calibrated (§2a)
NOT_CHECKED lesson_activity_minimums_not_calibrated: not_checked: per-lesson inline/workbook activity minimums are not calibrated (§2a)
NOT_CHECKED arc_has_no_structured_grammar_or_vocabulary: not_checked: the arc carries letters only; it has no structured grammar or vocabulary to compare against (§2a)
NOT_CHECKED title_quantities_not_parsed: subtitle digits: 1, 3; digit quantities are not parsed — the plan review checks stated quantities against the scope sidecar (§2a)
NOT_CHECKED pending_promotion: evidence_ref.sha256 is 96b696344c3bb5ba94463718cafc55df5aecf13955f1e1d8c16d9a34709c5515 and the provisional pack's sha256 is 125c6dd76afb38b820531f614ec55e677cd4867221d99cd4b994c2cca2e0e63f; plan-promote sets evidence_ref.sha256 to the pack's after the plan review approves
NOT_CHECKED mechanical_rule_not_checked: gate M5 was not checked: core word records carry no CEFR level: W-074
```

### Position 2: reading-ukrainian

`words-verify a1` (shared): exit 0, `status=OK`, 153 records / 1762 forms; 166 pending forms and 4 override forms remain reported, not learner admission proof.

`pack-verify a1 reading-ukrainian --strict`: exit 1.

```text
ERROR: open_unsupported: 3 unsupported records open: ['U-002', 'U-003', 'U-004']
Evidence Pack Verification: module=a1/reading-ukrainian status=FAILED
Verified: texts=21, exercises=5, examples=4, errors=0, notes=0, videos=15, standard=0
Unsupported: 3 open, 1 resolved
REPORT: open_unsupported: 3 unsupported records open: ['U-002', 'U-003', 'U-004']
```

`plan-validate a1 reading-ukrainian --provisional-pack`: exit 0.

```text
status: pass
mode: provisional
NOT_CHECKED minutes_constants_undefined: not_checked: minutes is computed, and the constants it needs do not exist yet (§2a)
NOT_CHECKED word_target_not_calibrated: not_checked: word_target presence and type are checked; the per-level minimum is not calibrated (§2a)
NOT_CHECKED lesson_activity_minimums_not_calibrated: not_checked: per-lesson inline/workbook activity minimums are not calibrated (§2a)
NOT_CHECKED arc_has_no_structured_grammar_or_vocabulary: not_checked: the arc carries letters only; it has no structured grammar or vocabulary to compare against (§2a)
NOT_CHECKED title_quantities_not_parsed: no ASCII digits in the title or subtitle; digit quantities are not parsed — the plan review checks stated quantities against the scope sidecar (§2a)
NOT_CHECKED pending_promotion: evidence_ref.sha256 is 434724cb67dbfbc88d12945fc165ff7bd9eaba1563085c963173f0d5cf249234 and the provisional pack's sha256 is e8853fc0faaef6092ce7c93ed571c6829224a3a375ca35e85d8b6f56cbc1a60a; plan-promote sets evidence_ref.sha256 to the pack's after the plan review approves
```

### Position 3: special-signs

`words-verify a1` (shared): exit 0, `status=OK`, 153 records / 1762 forms; 166 pending forms and 4 override forms remain reported, not learner admission proof.

`pack-verify a1 special-signs --strict`: exit 1.

```text
ERROR: open_unsupported: 5 unsupported records open: ['U-003', 'U-004', 'U-005', 'U-006', 'U-007']
Evidence Pack Verification: module=a1/special-signs status=FAILED
Verified: texts=26, exercises=5, examples=1, errors=0, notes=0, videos=7, standard=1
Unsupported: 5 open, 2 resolved
REPORT: open_unsupported: 5 unsupported records open: ['U-003', 'U-004', 'U-005', 'U-006', 'U-007']
```

`plan-validate a1 special-signs --provisional-pack`: exit 0.

```text
status: pass
mode: provisional
NOT_CHECKED minutes_constants_undefined: not_checked: minutes is computed, and the constants it needs do not exist yet (§2a)
NOT_CHECKED word_target_not_calibrated: not_checked: word_target presence and type are checked; the per-level minimum is not calibrated (§2a)
NOT_CHECKED lesson_activity_minimums_not_calibrated: not_checked: per-lesson inline/workbook activity minimums are not calibrated (§2a)
NOT_CHECKED arc_has_no_structured_grammar_or_vocabulary: not_checked: the arc carries letters only; it has no structured grammar or vocabulary to compare against (§2a)
NOT_CHECKED title_quantities_not_parsed: no ASCII digits in the title or subtitle; digit quantities are not parsed — the plan review checks stated quantities against the scope sidecar (§2a)
NOT_CHECKED pending_promotion: evidence_ref.sha256 is a637dc9c37ffb8be028c2d249e7bbde75ae490f753fc817eef6bc72c08c27ab6 and the provisional pack's sha256 is 469fb2f530606343ba7805524e7bcfd82e6ee0355e290b165e9abd45276ca093; plan-promote sets evidence_ref.sha256 to the pack's after the plan review approves
```


Mechanical notes are inherited. Position-1 M5 above-band records are the plan's literacy terminology and primer reading words, not newly admitted exceptions; W-074 has no CEFR field and remains explicitly unmeasured. No M1 or M3 NOTE was emitted. The calibration, arc-structure and title limitations remain unmeasured; provisional hash mismatches still require the driver’s new exact-input review/promotion. A provisional pass does not erase any of these notes or establish recap buildability.

## Residual and restart condition

- Issue #8425 was observed OPEN. Open inherited U-groups: position 1 U-001; position 2 U-002/U-003/U-004; position 3 U-003/U-004/U-005/U-006/U-007. Newly resolved U-records: **none**.
- Revised versions delivered: **0/3**. Revised activity bindings certified: **0/136**. Complete before/after outcome ledger, conversions, decodability checks and valid family witnesses: not produced because the whole-outcome host prerequisite fails.
- Narrow driver-owned condition: supply a reviewed compatible binding for the required first-person bilingual recap story and its questions, including position-2 spoken answer options, while retaining the brief's recap shape and ULP no-quote rule. This must not be inferred from letter/word listening acceptance.
- Then integrate the exact reviewed listening and WP21 publication-right implementations with the evidence/plan revision, record the combined SHA and registry identity, and resume the authorized plan revisions. Independent target playback, per-family schema/preflight/choice probes (including host order), strict pack gates, fresh plan reviews and stale-manifest regeneration still follow in position order.
- No engine/schema workaround, silent substitution, fake U-resolution, lesson build or PR was used. No tests were added or run for this note-only change; deterministic gate and structural-probe outputs above are the verification performed.
