<!-- content-hash: 51ede8607739 -->
**Reviewed-By:** claude-opus-4-6

---

## Scores

| Dimension | Score | Rationale |
|-----------|-------|-----------|
| **Lesson Quality** | 8/10 | Solid structure with good cultural hooks, but missing warm opening greeting, no explicit "Today you'll learn..." preview, and long stretches before formal practice. "Would I Continue?" test: 4/5 pass (borderline fail on quick wins). |
| **Language Quality** | 8/10 | Ukrainian grammar is correct throughout. Natural phrasing. But multiple IPA errors: double stress marks in content (line 261: «виши́ва́нка») and vocabulary file (вишиванка, коштувати), plus missing stress on розмір. |
| **Activity Quality** | 7/10 | 9 activities across 4 types is adequate. However, quiz activity has 8 questions ALL using identical stem «Скажіть, будь ласка, якого кольору...» — extreme monotony. Three match-ups out of 9 total is repetitive. |
| **Richness** | 9/10 | Strong cultural content: «Два кольори» song reference, vyshyvanka-as-оберіг tradition, seasonal color symbolism, Lviv shopping scenario. Six well-placed engagement boxes. Named cultural references. |
| **Humanity & Warmth** | 7/10 | No warm opening greeting ("Привіт!" only appears on line 358 in final section). Encouragement phrases are sparse — no "Great!", "You've got this!" in instructional voice. The [!warning] boxes are cautionary rather than reassuring. Module reads more like a textbook than a caring tutor. |
| **LLM Fingerprint** | 8/10 | One instance of «це не просто» pattern (line 17). Quiz monotony (8 identical stems) is a structural fingerprint. Example sections use a largely uniform «Приклади:» + bullet list format across multiple sections. Section openings are varied enough. |
| **Immersion** | 7/10 | At 36.3%, this sits at the very bottom of the 35-55% target range. For an A1.3 Consolidation module (a1-27), more Ukrainian is expected. Many instructional passages are entirely in English where Ukrainian could be used with translations. |
| **Factual Accuracy** | 9/10 | «Два кольори» song attribution and lyrics are correct. Color symbolism claims are well-established in Ukrainian folklore. Vyshyvanka-as-оберіг is accurate. Grammar rules are correct. No fabricated claims found. |
| **Plan Compliance** | 7/10 | Missing «На ньому...» construction mandated by plan section 5. Missing «Це мені пасує» phrase from plan section 6. «улюблений» listed in vocabulary but never introduced in content despite plan mandating it. Final section title mismatch: plan says "Практика: Мій улюблений одяг", content has "Практика: Опис одягу". |

---

## Critical Issues Found

### Issue 1: IPA Double Stress Marks (Language Quality — CRITICAL)

**Location:** Content line 261, Vocabulary lines 83 and 116

Ukrainian words have exactly ONE primary stress. Three items have invalid double stress marks:

1. **Content line 261:** «виши́ва́нка» — has two acute accents. Correct: «вишива́нка».
2. **Vocabulary `вишиванка`:** IPA `[ʋɪˈʃɪˈʋɑnkɑ]` — has two stress marks. Correct: `[ʋɪʃɪˈʋɑnkɑ]`.
3. **Vocabulary `коштувати`:** IPA `[ˈkɔʃtuˈʋɑtɪ]` — has two stress marks. Correct: `[kɔʃtuˈʋɑtɪ]`.
4. **Vocabulary `розмір`:** IPA `[rɔzʲmʲir]` — MISSING stress mark entirely. Correct: `[ˈrɔzʲmʲir]`.

**Fix:** Remove the spurious stress mark from each item, keeping only the correct primary stress position. Add missing stress to розмір.

---

### Issue 2: Activity Quiz Monotony — 8 Identical Question Stems (Activity Quality — CRITICAL)

**Location:** Activities file, lines 70-157

All 8 quiz items use the exact same question stem: «Скажіть, будь ласка, якого кольору цей/ця/це/ці...?» This is extreme structural monotony. A real tutor would vary question phrasing.

**Evidence:**
- Line 70: «Скажіть, будь ласка, якого кольору цей автобус?»
- Line 81: «Скажіть, будь ласка, якого кольору ця машина?»
- Line 92: «Скажіть, будь ласка, якого кольору це яблуко?»
- Line 103: «Скажіть, будь ласка, якого кольору ці штани?»
- Line 114: «Скажіть, будь ласка, якого кольору ця сукня?»
- Line 125: «Скажіть, будь ласка, якого кольору цей папір?»
- Line 136: «Скажіть, будь ласка, якого кольору ця куртка?»
- Line 147: «Скажіть, будь ласка, якого кольору ці окуляри?»

**Fix:** Vary question phrasing across at least 3 different patterns. Examples: «Який колір має...?», «Опишіть колір...», «Якого кольору...?» (dropping the «Скажіть, будь ласка» formula), «Це ... автобус. Який колір?» (gap-fill style).

---

### Issue 3: Plan-Mandated Constructions Missing (Plan Compliance — MAJOR)

**Location:** Sections «Опис зовнішності та вишиванка» and «Діалог: У магазині одягу»

The plan (plans/a1/colors-and-clothing.yaml) specifies three constructions that are completely absent from the content:

1. **Section 5 (line 256-312):** Plan mandates "Constructing a full description: «Він має...» vs «На ньому...» (On him is...)" — The «На ньому...» construction never appears anywhere in the content. This is a key descriptive pattern for talking about what someone is wearing.

2. **Section 6 (line 314-337):** Plan mandates key phrase «Це мені пасує» (This fits me / This suits me) — absent from both the dialogue and the key phrases list.

3. **Section 1 (line 15-75):** Plan mandates "Brief introduction of «улюблений колір» (favorite color) concept" — The word «улюблений» appears in the vocabulary file but is never introduced or used in the content. The content uses «Який колір ви любите?» instead of teaching the adjective form «улюблений колір».

**Fix:** Add «На ньому...» examples in section «Опис зовнішності та вишиванка» (e.g., «На ньому чорний костюм.» vs «Він носить чорний костюм.»). Add «Це мені пасує» to the dialogue or key phrases. Introduce «улюблений колір» in section «Кольори навколо нас».

---

### Issue 4: Missing Warm Opening & Sparse Encouragement (Humanity & Warmth — MAJOR)

**Location:** Lines 1-17 (opening), throughout module

The module opens directly with a SCOPE comment and a blockquote about why colors matter. There is no warm greeting — «Привіт!» only appears on line 358 in the final practice example paragraph. A beginner at A1.3 still needs the emotional safety of a warm welcome.

Throughout the instructional prose, encouragement markers are nearly absent:
- No "Great!", "You've got this!", "Well done!" type phrases
- No "Don't worry, this is normal" reassurances
- The [!warning] boxes on lines 119-121 and 251-254 flag errors but don't reassure learners that mistakes are OK

The closing «Підсумок» (line 369-380) summarizes content but lacks explicit "You can now..." validation beyond the self-check questions.

**Fix:** Add a warm "Привіт!" opening paragraph with a preview ("Today you'll learn to name colors, describe your clothes, and shop like a local in Lviv!"). Sprinkle 2-3 encouraging phrases throughout (e.g., after the color table: "Look at that — you already know six colors!"). Add reassurance near [!warning] boxes (e.g., "This is the most common mistake — even native speakers sometimes slip!").

---

### Issue 5: Final Section Title Mismatch (Plan Compliance — MINOR)

**Location:** Section «Практика: Опис одягу» (line 339)

The plan specifies this section as "Практика: Мій улюблений одяг" (My Favorite Clothes), which ties to the «улюблений» concept. The content renames it to «Практика: Опис одягу» (Clothing Description), losing the personal connection. This also relates to Issue 3 — the «улюблений» thread is dropped entirely.

**Fix:** Rename section to «Практика: Мій улюблений одяг» and incorporate «улюблений» into the guided writing task (e.g., "Start with «Мій улюблений одяг — це...»").

---

## Factual Verification

### Callout Box Verification

| Box | Location | Claim | Verdict |
|-----|----------|-------|---------|
| [!culture] "Два кольори" | Lines 29-36 | References Ukrainian song «Два кольори» with lyric «Червоне — то любов, а чорне — то журба» | **VERIFIED** — Song by Дмитро Павличко, lyrics accurate. The cultural note correctly states that in older tradition, black symbolized earth/life rather than sorrow. |
| [!tip] Pronunciation | Lines 73-75 | Claims soft «ль» in «колір» is palatalized | **VERIFIED** — «колір» [ˈkɔlʲir] contains palatalized lateral. Pedagogical explanation is accurate. |
| [!warning] Common Mistake | Lines 119-121 | Says "червоний ручка" confuses listeners due to clashing gender signals | **VERIFIED** — Correct. «Ручка» is feminine, requires «червона ручка». |
| [!observe] Case Comparison | Lines 206-211 | Contrasts nominative «синя сукня» with accusative «синю сукню» | **VERIFIED** — Correct case forms. The "I wear she" analogy (line 211) is pedagogically creative if slightly imprecise. |
| [!warning] "Don't count" | Lines 251-254 | Claims you cannot say "один штани", must use «одні́» | **VERIFIED** — Correct. «Одні» is the standard collective numeral for pluralia tantum. |
| [!myth-buster] Vyshyvanka | Lines 310-312 | Claims vyshyvanka is worn in modern settings, not just holidays | **VERIFIED** — Accurate. Modern Ukrainian fashion incorporates vyshyvanka into everyday and professional wear. |

### Grammar Rule Verification

| Rule | Location | Verdict |
|------|----------|---------|
| Hard group adjective endings (-ий, -а, -е) | Lines 94-95 | **CORRECT** |
| Soft group adjective endings (-ій, -я, -є) for синій | Lines 95-96 | **CORRECT** |
| Feminine accusative: -а → -у, -я → -ю | Lines 193-204 | **CORRECT** |
| Masculine inanimate accusative = nominative | Lines 190-191 | **CORRECT** |
| Носити vs одягати distinction | Lines 216-219 | **CORRECT** — habitual vs. momentary action |
| Plural adjective ending -і for pluralia tantum | Lines 235-241 | **CORRECT** |
| Invariant borrowed colors (бордо, беж, хакі) | Lines 133-148 | **CORRECT** |
| Носити conjugation (Class II, с→ш alternation) | Lines 175-181 | **CORRECT** |

### Colonial Framing Check

No instances of colonial framing found. The word "Russian" does not appear in the content. Ukrainian features are presented on their own terms throughout.

---

## Verification Summary

| Check | Result | Details |
|-------|--------|---------|
| Russianisms | **PASS** | No Russianisms detected |
| Colonial Framing | **PASS** | No Russian-baseline comparisons |
| Calques | **PASS** | No unnatural calques found |
| Grammar Accuracy | **PASS** | All grammar rules correctly stated |
| IPA Accuracy | **FAIL** | 4 IPA errors: double stress (×2), missing stress (×1), double accent in content (×1) |
| Factual Accuracy | **PASS** | All cultural claims verified |
| Plan Compliance | **FAIL** | Missing 3 mandated constructions, 1 section title mismatch |
| Activity Quality | **FAIL** | 8/8 quiz questions use identical stem |
| Warmth Threshold | **FAIL** | No warm opening greeting, <3 encouragement markers |
| LLM Fingerprint | **PASS** | 1× "це не просто" (below threshold), section openings varied |
| Beginner Safety | **PASS** | 4/5 on "Would I Continue?" test |

**Citation Verification:** All Ukrainian text in «» quotes was copy-pasted from Read tool output and verified via Grep.

---

## Verdict

**NEEDS REVISION** — The module has strong bones: correct grammar throughout, rich cultural content (especially the color symbolism and vyshyvanka sections), a well-constructed shopping dialogue in section «Діалог: У магазині одягу», and solid engagement boxes. Section «Основні кольори та узгодження» presents the gender agreement table cleanly. Section «Множина: штани та окуляри» handles pluralia tantum well.

However, three categories of issues require repair before approval:

1. **IPA errors** (4 instances across content and vocabulary) — mechanical fixes
2. **Activity monotony** in quiz (8 identical question stems) — requires rewording
3. **Plan compliance gaps** — missing «На ньому...», «Це мені пасує», and «улюблений колір» constructions; section title mismatch in «Практика: Опис одягу»
4. **Warmth deficit** — needs warm opening, scattered encouragement, and reassurance near error-flagging boxes

None of these issues require a full rewrite. Targeted D.2 repair should address all of them.