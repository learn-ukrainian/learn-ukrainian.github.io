# lu.lesson.v1 — lesson document contract (design v1, 2026-07-10)

> Status: DRAFT for cross-family review → implementation in `packages/activity-kit`.
> Sources: POC demo iterations 2026-07-10 (user Правки 2–3), teacher-lesson calibration
> (private corpus — structure only, no content), `docs/best-practices/activity-pedagogy.md`
> constraints recorded on #4542 (2026-07-09 taxonomy validation). Public-repo doc: contains
> no private-repo internals.

## 1. Purpose

`lu.activity.v1` (shipped, PR #4867) is the envelope for ONE activity. A lesson is not a
bag of activities — it is a **plan over an ordered block set**: phased, time-sized,
non-destructively cuttable, with teacher-facing answer keys. This contract is consumed by
the async bake API (build step 5) and the editor/player frontend (step 6).

## 2. Document model

```jsonc
{
  "schema": "lu.lesson.v1",
  "id": "uuid",
  "title": "string",                    // derived: first sentence of anchor, word-boundary cut ≤52
  "level": "B1",                        // v1 pilot: B1 only
  "method": "ttt",                      // v1: Тест→Навчання→Тест; phase set {1,2,3}
  "focus": "string|null",               // grammar focus, free text v1
  "anchor": { "text": "string", "source": "teacher-paste|teacher-url", "chars": 1456 },
  "duration": 45 | 60 | 90,             // minutes; the ONLY sizing input a teacher gives
  "status": "draft|baking|ready",       // + accepted: bool (ready ∧ accepted = final sheet)
  "blocks": [ "Block, see §4" ],        // FULL ordered set (max plan), contiguous by phase
  "rejected": [ "RejectedDraft, §4" ],  // never silently dropped; reason required
  "created_at": "...", "updated_at": "..."
}
```

## 3. Sizing & the non-destructive cut (user decision 2026-07-10)

| duration | planned tasks | per-phase visible split Т1·Н·Т2 | phase minutes |
|---|---|---|---|
| 45 | 6  | 2·3·1 | 10·15·15 |
| 60 | 9  | 3·4·2 | 15·25·15 |
| 90 | 12 | 4·5·3 | 20·40·25 |

- The bake ALWAYS generates toward the 90-min maximum the anchor supports.
- `duration` is a **view**, not a mutation: visible set = per-phase prefix of `blocks`;
  the remainder is the **reserve** («у запасі») — surfaced as homework candidates on the
  final sheet. Switching duration loses nothing, in either direction.
- «включити в план» = move block to the front of its phase (plan size stays fixed; the
  displaced last-visible block returns to reserve).
- Minimum plan is 6 (45 min). There is no 3-task lesson.
- Shortfall honesty: if the anchor supports fewer blocks than planned, the deficit is
  stated to the teacher («складено N із M — додайте текст»); never padded with
  ungrounded filler.

## 4. Block

```jsonc
{
  "id": "stable-id",
  "phase": 1,                              // 1 | 2 | 3
  "type": "registry key (see §5)",
  "mode": "усно",                          // усно | письмово | вдома — 1-1 lesson flow marker
  "activity": { "...": "lu.activity.v1 envelope (payload per type)" },
  "answer_key": "string | structured | null",
  "mark": "ok",                            // ok | warn; warn NEVER auto-accepts (frozen UX rule)
  "note": "string|null",                   // honest reviewer note shown in the margin
  "edited": false,                         // teacher touched it → provenance flips
  "provenance": { "source": "anchor|generated|teacher",
                   "generator": "...", "gates": ["..."],
                   "external_options": false }
}
```

- `answer_key` is REQUIRED for auto-checkable types; free-response types carry teacher
  guidance instead (e.g. «вільна відповідь — перевірте форми порівняння»).
- `external_options: true` ⇒ content not derivable from the anchor (e.g. MC distractors)
  ⇒ mandatory `warn` at generation time.

RejectedDraft: `{ "type", "activity", "reason" }` — reason classes include
`not-verifiable-from-text`, `too-easy-for-level`, `gate-failed:<gate>`, `removed-by-teacher`.

## 5. Type registry v1 (calibrated 2026-07-10 against real 1-1 lessons)

Item counts are **minimums** (word-target policy applies). `mode` defaults shown.

| key | UA label | items (min) | mode | status | notes |
|---|---|---|---|---|---|
| true_false | Правда чи ні | 6 | усно | **shipped** (#4867 TrueFalse) | with «якщо неправда — виправте» |
| cloze | Пропущене слово | 6 | письмово | **shipped** (Cloze) | word-bank form preferred at B1 |
| match_up | Знайди пару | 5 | усно | **shipped** (MatchUp) | definitions flagged when not from anchor |
| text_questions | Питання до тексту | 5 | усно | backlog | open comprehension Qs |
| multiple_choice | Оберіть відповідь | 4 | усно | backlog | `external_options` honesty flag |
| glossary | Словничок | 8 | усно | backlog | gloss language = OPEN Q (§7) |
| form_build | Утворіть форму | 6 | усно | backlog | grammar-focus driven |
| error_hunt | Знайдіть помилку | 4 | письмово | backlog | prime surface for russianism/calque pedagogy |
| paraphrase | Скажіть інакше | 5 | усно | backlog | find-in-text direction |
| continue_sentence | Продовжте речення | 4 | усно | backlog | production, free answers |
| roleplay_dialog | Розіграйте діалог | 1 scenario + 4 prompts | усно | backlog | 1-1: teacher plays the partner (stated in answer_key) |
| short_writing | Коротке письмо | 1 prompt (7–8 речень) | вдома | backlog | natural homework candidate |

Pedagogy constraints carried from #4542 taxonomy validation: ≤1 puzzle-type per B1 lesson;
grammar-identify + highlight-morphemes join the registry when built; диктант deferred to the
TTS asset phase; MatchUp verification must be semantic, not just lexical (Sol defect list).

## 6. Honesty semantics (frozen in the POC, binding here)

1. `warn` requires explicit teacher acceptance — no auto-promotion, ever.
2. Rejected drafts are visible with machine-readable reasons — nothing disappears silently.
3. Content provenance is per-block; anything not derivable from the anchor
   (`external_options`, invented definitions) is flagged at generation time, not discovered
   in review.
4. The final sheet carries the honest footer (складено з тексту вчителя · мову перевірено
   за словником · факти перевірте) and the 🔑 answer key is teacher-only.

## 7. Open questions → teacher feedback 2026-07-12 (do NOT block steps 3–5)

1. Glossary gloss language: UA-UA (immersion policy) vs UA-EN (observed teacher practice).
   Schema stays agnostic: `gloss_lang` field.
2. Custom phase order («Власна» методика) — post-pilot; schema reserves `method`.
3. Per-type item-count defaults — teachers may want the dial; v1 ships the calibrated
   minimums.

## 8. Relationship to existing artifacts

- Wraps `lu.activity.v1` (never duplicates payload schemas).
- The POC flagship lesson («Як ми шукали квартиру у Львові», 12 blocks, full answer keys)
  becomes **canonical fixture #1** for this schema.
- Consumers: durable-jobs API (step 5: `lesson` is the artifact a job produces), editor
  frontend (step 6: the review screen IS this document), engine (private repo) emits it.
