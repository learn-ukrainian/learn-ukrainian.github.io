# Personal-name audit — fact-finding (Phase 1 prep)

> **Status: AUDIT DATA — pending Phase 1 consultation Q4 disposition.**
> Inventories every committed file referencing the user's two private
> teachers' names, classified PERSONAL (must scrub) vs GENERIC (a common
> Ukrainian first name used in invented dialogue, fine to leave).

## Scope

User's two private teachers' names (privately identified in
`memory/MEMORY.md`, NOT spelled in this doc) appear in 43 committed files,
95 line occurrences total.

**Policy** (per user, 2026-04-25 evening):
- Personal references to the user's actual teachers MUST be scrubbed from
  every committed file. Wartime Ukraine, real targeting risk.
- Names stay in `memory/MEMORY.md` (Claude's private project memory).
- Public creators (Anna Ohoiko, textbook authors) — fine, keep.
- Generic uses of the names as common Ukrainian first names in invented
  dialogue — fine, keep (one of the names is among the most common
  Ukrainian female first names; characters can be called that).

## Classification

### PERSONAL references — MUST SCRUB (~30 occurrences across ~18 files)

These all refer to the user's actual private contacts as authorities,
calibrators, reviewers, or teaching-material owners.

| File | Lines | Pattern | Replacement |
|---|---|---|---|
| `.gitignore` | 207-208 | "{Name}'s teaching material" | "Private teaching material" |
| `tests/test_human_eval_tracker.py` | 91-92, 107, 168-170, 173, 239, 251 | Used as test-fixture reviewer names | "Reviewer A" / "Reviewer B" |
| `wiki/.reviews/pedagogy/a1/checkpoint-first-contact-review-LOCKED.md` | 36 | "(Teacher {N1} / Teacher {N2})" | "(native-speaker reviewer)" |
| `wiki/.reviews/pedagogy/a1/sounds-letters-and-hello-review-LOCKED.md` | 36 | same | same |
| `wiki/.reviews/pedagogy/a1/things-have-gender-review-LOCKED.md` | 60 | same | same |
| `wiki/.reviews/pedagogy/a1/how-many-review-LOCKED.md` | 44 | same | same |
| `wiki/.reviews/pedagogy/a1/at-the-cafe-review-LOCKED.md` | 36 | same | same |
| `wiki/.reviews/pedagogy/a1/reading-ukrainian-review-LOCKED.md` | 36 | same | same |
| `wiki/.reviews/pedagogy/a1/this-and-that-review-LOCKED.md` | 60 | same | same |
| `wiki/.reviews/pedagogy/a1/who-am-i-review-LOCKED.md` | 63 | same | same |
| `wiki/.reviews/pedagogy/a1/my-day-review-LOCKED.md` | 36 | same | same |
| `wiki/.reviews/pedagogy/a1/what-is-it-like-review-LOCKED.md` | 1 | same | same |
| `wiki/.reviews/pedagogy/a1/hey-friend-review-LOCKED.md` | 1 | same | same |
| `wiki/.reviews/pedagogy/a1/my-family-review-LOCKED.md` | 1 | same | same |
| `wiki/.reviews/pedagogy/a1/stress-and-melody-review-LOCKED.md` | 1 | same | same |
| `docs/wiki-rebuild-plan.md` | 228 | "hand articles to teacher {N1}" | "hand articles to a native-speaker reviewer" |
| `docs/style-guide.md` | 121 | "Teacher {N1} or Teacher {N2} on the…" | "a native-speaker reviewer" |
| `docs/session-state/2026-04-21-evening.md` | 10 hits | reviewer references | (session-state — historical record; consider just deleting the file post-reboot since V6 sessions are obsolete reference) |
| `docs/session-state/2026-04-21-morning-handoff.md` | 2 hits | "Native teacher signed off (Alona...)" | "a native teacher" |
| `docs/session-state/2026-04-21-evening-strategic-audit.md` | 3 hits | various | scrub or delete file |
| `docs/architecture/2026-04-21-pilot-readiness-audit.md` | 13 hits | reviewer authority references | "native reviewer" |
| `docs/architecture/adr/adr-008-uk-native-track-destination.md` | 8 hits | "{N2} reviews it..." | "the native reviewer reviews it..." |
| `docs/architecture/2026-04-22-execution-plan-corpus-bootstrap.md` | 2 hits | reviewer references | "native reviewer" |
| `docs/design/dimensional-review.md` | 8 hits | "{N1} validation", "Teacher {N1}", etc. | "native validation", "the native reviewer" |
| `docs/eval/human-eval-rubric.md` | 2 hits | reviewer setup references | "the native reviewer" |
| `scripts/build/pilot_uk_lesson.py` | 3 hits | code/strings | "native reviewer" |
| `scripts/build/research/build_knowledge_packet.py` | 2 hits | strings | same |
| `docs/references/dobra-forma/chapters/24.1.md` | 1 hit | unclear, needs context | (inspect) |
| `docs/references/textbooks-txt/nation-builders.txt` | 1 hit | textbook content (probably generic) | (inspect, likely keep) |

### GENERIC dialogue uses — KEEP (~7 occurrences across 5 files)

These use one of the names as a character name in fictional dialogues.
The name in question is among the most common Ukrainian female first
names; characters in family/workplace/school scenarios will naturally be
called that. No personal reference, no exposure.

| File | Line | Context | Disposition |
|---|---|---|---|
| `curriculum/l2-uk-en/a1/my-family.md` | 20 | "**Даша:** її звати {Name}" — character introduces her aunt by name | KEEP — fictional family dialogue |
| `curriculum/l2-uk-en/a2/dative-nouns.md` | 152, 154 | Generic dative-case practice sentences | KEEP — grammar practice example |
| `curriculum/l2-uk-en/b1/work-and-career.md` | 160-165 | Workplace dialogue, character named {Name} | KEEP — fictional workplace scene |
| `curriculum/l2-uk-en/b1/orchestration/work-and-career/chunk-03.md` | 25 | Same dialogue (orchestration mirror) | KEEP |
| `curriculum/l2-uk-en/b1/orchestration/work-and-career/v6-activities-prompt.md` | 223 | Same dialogue (orchestration mirror) | KEEP |
| `curriculum/l2-uk-en/b1/orchestration/work-and-career/v6-review-prompt.md` | 327 | Same dialogue (orchestration mirror) | KEEP |

The other private-contact name is less common. There are NO generic dialogue uses of it identified in the audit.

### Borderline — needs eyes-on inspection (~3-5 occurrences)

| File | Why borderline |
|---|---|
| `docs/references/dobra-forma/chapters/24.1.md` | One hit; unclear if generic or personal |
| `docs/references/textbooks-txt/nation-builders.txt` | One hit in textbook content; probably generic but might mention a Ukrainian historical figure with same name |

## Replacement strategy

**For all PERSONAL references:**
- Wiki review files (`wiki/.reviews/...LOCKED.md`): single-line replacement of the parenthetical "(Teacher {N1} / Teacher {N2})" with "(native-speaker reviewer)". Templated, deterministic, ~12 files.
- Session-state files (`docs/session-state/2026-04-21-*`): these are historical V6 records. Either scrub line-by-line OR delete the files (they're superseded session-state from before the reboot decision). Recommendation: **delete** — Phase 0 starts fresh, old session-state has no forward value AND has the most exposure.
- Tests: rename fixtures to "Reviewer A" / "Reviewer B" — preserves test logic.
- Design docs / ADRs / style guide / scripts: line-by-line replacement of the names with role descriptions.

**For GENERIC uses:** keep. No action.

**For borderline files:** inspect before action.

## Estimated effort

- Wiki LOCKED files: 30 min (template find/replace across 12 files)
- Session-state cleanup (delete pre-reboot session-state): 5 min
- Tests rename: 10 min
- Design docs / ADRs: 30 min (careful line-by-line)
- Borderline inspection: 10 min

**Total ≈ 1.5 hours of focused work.** Single commit, clean diff.

## Open question (for Phase 1 consultation Q4)

Phase 1 (now) or later? Argument for now: real wartime targeting risk;
the names have been in committed files for weeks. Argument for later:
the existing live site already has these references (separate cleanup
pass needed); doing it now may produce extra commits before Phase 0
North Star is even drafted.

**Claude's read:** do it now (Phase 1). It's a security concern, the
work is bounded (~1.5 hours), and the existing live site can be cleaned
up by re-publishing post-Phase-5 anyway.
