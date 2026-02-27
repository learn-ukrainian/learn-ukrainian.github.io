<!-- content-hash: ef33e89e557d -->
**Reviewed-By:** claude-opus-4-6

## Scores

| Dimension | Score | Evidence |
|-----------|-------|----------|
| **Plan Compliance** | 8/10 | All 8 content_outline sections present as H2 headers. All 4 learning objectives addressed. All 8 required + 6 recommended vocabulary items in sidecar. However, section «Підсумок: Потрібно більше практики?» uses H1 heading (line 400: `# Підсумок`) instead of H2 (`##`), breaking structural consistency with all other sections. |
| **Language Quality** | 8/10 | Ukrainian is predominantly natural and warm. Three euphony violations: line 50 «В українській мові ми віддаємо перевагу», line 73 «В українському мовному просторі існує явище», line 285 «В українських медіа дуже часто використовують» — all should use «У» at sentence/clause beginnings before «у»-initial words. Line 199 «Однією з найпрекрасніших і найхарактерніших рис» — «найпрекрасніших» is stilted; «найчудовіших» or «найяскравіших» would be more natural. No Russianisms in the prose itself (Russianisms appear only correctly within error-correction examples). |
| **Teaching Quality** | 9/10 | Excellent TTT structure. Hook at line 10: «Але жива мова — це не лише набір правильних закінчень. Це ще й стиль, тон і доречність.» Discovery via diagnostic test (lines 22-41) before explanation. Three diverse scenarios provide progressive application. The editing laboratory (section «Практика: Лабораторія редагування») with step-by-step error correction at lines 341-348 is particularly effective. The multi-register dialogue (section «Діалоги та текстотворення», lines 363-378) showing the same content in formal/informal registers is an excellent capstone. Slight weakness: the writing prompt at lines 387-391 asks learners to use terms «інтеграція» or «синтез» which feels slightly forced. |
| **Factual/Grammar Accuracy** | 7/10 | **Critical error** at line 261: «Використання дієприкметників на -но, -то дає відчуття завершеності без називання конкретних депутатів» — Forms ending in -но/-то (схвалено, написано, зроблено) are NOT дієприкметники (participles). They are **предикативні безособові форми** (impersonal predicative forms). Дієприкметники have -ний/-тий endings (схвалений, написаний) and agree with nouns in gender/number/case. This is a metalinguistic error in a grammar module. All other grammar explanations are accurate: active/passive voice distinction, збірні числівники usage, дробові числівники with gen. sg., демінутив formation. |
| **LLM Fingerprint** | 9/10 | One instance of «це не просто» at line 69: «Синтез — це не просто використання правильних закінчень, це створення гармонійного тексту». This is only a single occurrence and not excessive. Section openings are varied (no 3+ identical patterns). Example formatting mixes tables, bullet lists, blockquotes, and numbered lists effectively. No «варто зазначити», no «давайте дізнаємося». One «давайте» at line 195, contextually natural. Callout titles are varied: [!reflection], [!important], [!warning], [!cultural], [!tip], [!myth-buster], [!fact] — no repetition. |
| **Activity Quality** | 8/10 | 10 activities with good type variety (error-correction ×2, quiz, unjumble, fill-in, match-up, true-false, group-sort, select, cloze). **Typo** at activities line 142: «Яке слово є доречним демінутвом для неформальної бесіди?» — should be «демінутивом» (missing «и»). **Missing comma** at activities line 375: «Повідомляю що» should be «Повідомляю, що» in the group-sort items. **Fabricated distractor** at activities line 82: «крайнебо» — this is not a real Ukrainian word; while it's marked as incorrect, a plausible real-word distractor would be better pedagogically. Activity items are below plan hints (plan suggests ~70 items total, actual ~80 items across 10 activities — actually this is close). |
| **Richness** | 8/10 | Cultural references: Поділ (line 88, 113), Острозька академія (line 88), Золоті ворота (line 110). 7 engagement boxes (meets threshold). Pre-computed richness shows cultural: 2/3 — one more cultural/culture-note callout needed. Tables at lines 107-113 and 203-209 provide visual variety. The multi-register dialogue comparison (lines 363-378) is an excellent richness element. |
| **Immersion** | 10/10 | 99.1% Ukrainian. No English in the prose body. English appears only in frontmatter scope comments and vocabulary sidecar translations. Fully appropriate for B1.4. |
| **Naturalness** | 9/10 | Teacher voice is warm and engaging throughout. Direct address «ви» used extensively. Encouragement present: line 396 «Тренуйте такі маленькі тексти, і ви відчуєте, як ваша мова стає більш впевненою.» Confusion anticipation: line 85 «Коли ви вивчаєте українську мову, ви можете думати, що використання таких складних конструкцій показує ваш високий рівень. Але насправді це показує лише те, що ви читаєте застарілі документи.» Real-world validation at line 88 «від стартапів на Подолі до студентів Острозької академії». The car driving metaphor at line 63 is effective and natural. |

## Critical Issues Found

### Issue 1: Grammar Metalanguage Error (CRITICAL)

**Location:** Content line 261
**Cited text:** «Використання дієприкметників на -но, -то дає відчуття завершеності без називання конкретних депутатів»
**Problem:** The forms -но/-то (схвалено, написано, відкрито) are **NOT** дієприкметники (participles). In Ukrainian grammar, дієприкметники are adjectival forms ending in -ний/-тий (схвалений, написаний, відкритий) that agree with nouns. The -но/-то forms are **предикативні безособові форми** (impersonal predicative forms) — a distinct grammatical category. This is a significant metalinguistic error in a module that explicitly teaches grammar terminology.
**Fix:** Replace «дієприкметників на -но, -то» with «безособових предикативних форм на -но, -то» or simply «форм на -но, -то».
**Severity:** Critical — incorrect grammar terminology in a grammar module.

### Issue 2: Structural Heading Inconsistency

**Location:** Content line 400
**Cited text:** `# Підсумок: Потрібно більше практики?`
**Problem:** All 7 content sections use H2 (`##`), but the summary section uses H1 (`#`). This breaks the document structure and likely confuses any automated processing that expects consistent H2 section headers.
**Fix:** Change `# Підсумок: Потрібно більше практики?` to `## Підсумок: Потрібно більше практики?`.
**Severity:** Moderate — structural inconsistency.

### Issue 3: Euphony Violations (×3)

**Locations:** Content lines 50, 73, 285
**Cited text (line 50):** «В українській мові ми віддаємо перевагу активному стану»
**Cited text (line 73):** «В українському мовному просторі існує явище»
**Cited text (line 285):** «В українських медіа дуже часто використовують теперішній час»
**Problem:** At sentence or clause beginnings, before words starting with «у», the euphonic form should be «У», not «В». The module itself teaches stylistic sensitivity, so these violations are particularly conspicuous.
**Fix:** Replace «В українській» → «У українській», «В українському» → «У українському», «В українських» → «У українських».
**Severity:** Moderate — repeated euphony violations in a module teaching linguistic sensitivity.

### Issue 4: Activity Typo

**Location:** Activities line 142
**Cited text:** «Яке слово є доречним демінутвом для неформальної бесіди?»
**Problem:** «демінутвом» is missing the letter «и» — correct form is «демінутивом» (instrumental case of «демінутив»).
**Fix:** Replace «демінутвом» → «демінутивом».
**Severity:** Moderate — visible typo in a quiz question.

### Issue 5: Activity Missing Punctuation

**Location:** Activities line 375
**Cited text:** «Повідомляю що» (in group-sort, under "Офіційно-діловий стиль")
**Problem:** Missing comma between «Повідомляю» and «що». The correct form «Повідомляю, що» appears in the content itself (line 164), so the activity dropped the comma. This is pedagogically harmful because learners sorting phrases into registers might internalize the incorrect punctuation.
**Fix:** Change to «Повідомляю, що».
**Severity:** Minor — but learners may internalize the error.

### Issue 6: Richness Gap — Cultural Callout Short

**Location:** Whole module
**Problem:** Pre-computed richness shows cultural: 2/3. The module has `[!cultural]` at line 123 and cultural references at lines 88, 110, 113, but needs one more explicit cultural callout to meet the gate.
**Fix:** Add one `[!culture]` or `[!did-you-know]` callout with cultural content, e.g., in section «Сценарій 3: Новини та медіа» — a note about Ukrainian media landscape (e.g., major news outlets like «Українська правда», Hromadske, or the tradition of «Бабель» magazine using modern Ukrainian style).
**Severity:** Minor — one callout short of gate.

## Factual Verification

| Claim | Location | Status | Notes |
|-------|----------|--------|-------|
| «приймати участь» is a Russicism; correct is «брати участь» | Line 91, 345 | ✅ Correct | Standard reference in all Ukrainian style guides |
| «являється» should be «є» | Line 91 | ✅ Correct | Well-known Russicism |
| «слідуючий» should be «наступний» | Line 347 | ✅ Correct | Direct Russian calque |
| «самі кращі» should be «найкращі» | Line 343 | ✅ Correct | Russian superlative pattern |
| «даний» in meaning «цей» is a chancellarism | Line 341 | ✅ Correct | Standard chancellarism |
| Збірний числівник «двоє» requires genitive plural | Line 149 | ✅ Correct | Standard Ukrainian grammar rule |
| Дробові числівники take genitive singular | Line 152 | ✅ Correct | «п'ять цілих і дві десятих відсотка» — gen. sg. |
| Historical present tense used in Ukrainian news | Line 285 | ✅ Correct | Standard journalistic technique |
| -но/-то forms called «дієприкметники» | Line 261 | ❌ **Incorrect** | These are безособові предикативні форми, not дієприкметники |
| «Шановна Олено Іванівно» — vocative case correct | Line 162 | ✅ Correct | Proper vocative forms |
| «здійснити покупку» as канцелярит example | Line 48 | ✅ Correct | Standard anti-chancellarism example |
| Synonymic row: горизонт (neutral) → обрій (poetic) → небокрай (highly poetic) | Lines 99-101 | ✅ Correct | Well-established stylistic gradation |

**Research cross-reference:** Research notes confirm State Standard §4.5.1 alignment, the cultural significance of «канцелярит», and the learner error patterns addressed. No claims outside research scope detected.

## Verification Summary

| Check | Result | Details |
|-------|--------|---------|
| All H2 sections from plan present | ⚠️ PARTIAL | 7/8 sections use H2; section «Підсумок: Потрібно більше практики?» uses H1 |
| Vocabulary coverage | ✅ PASS | All 8 required + 6 recommended items present in sidecar |
| Learning objectives addressed | ✅ PASS | All 4 objectives clearly addressed across content |
| Grammar scope (no forward leakage) | ✅ PASS | Односкладні речення acknowledged as B2 preview (line 256) — appropriate |
| Russianisms in author prose | ✅ PASS | No Russianisms in instructional text; Russianisms appear only in error examples |
| Colonial framing | ✅ PASS | Канцелярит discussed as Soviet legacy, not Russian vs Ukrainian contrast |
| LLM cliché count | ✅ PASS | 1× «це не просто» — below threshold |
| Immersion target (85-100%) | ✅ PASS | 99.1% |
| Engagement boxes (B1: ≥6) | ✅ PASS | 7 callout boxes |
| Factual accuracy | ⚠️ ISSUE | One metalanguage error (дієприкметники vs предикативні форми) |
| Activity correctness | ⚠️ ISSUE | 1 typo, 1 missing comma |
| Richness gate | ⚠️ ISSUE | Cultural 2/3 — one callout short |

## Verdict

**CONDITIONAL PASS — Requires D.2 Targeted Repair**

The module is well-constructed with excellent TTT pedagogy, natural Ukrainian prose, a warm teacher voice, and diverse, culturally embedded examples. The three-scenario approach (business, family, media) is pedagogically effective and covers the plan's objectives fully. The content is above the 4000-word target at 4329 words.

**Mandatory fixes before approval (5 items):**

1. **Line 261:** Replace «дієприкметників на -но, -то» with «безособових форм на -но, -то» or «предикативних форм на -но, -то» — grammar metalanguage error in a grammar module.
2. **Line 400:** Change `# Підсумок` to `## Підсумок` — heading level consistency.
3. **Lines 50, 73, 285:** Fix euphony: «В українській» → «У українській» (×3 instances).
4. **Activities line 142:** Fix typo «демінутвом» → «демінутивом».
5. **Activities line 375:** Fix punctuation «Повідомляю що» → «Повідомляю, що».

**Recommended improvement (non-blocking):**

6. Add one cultural callout in section «Сценарій 3: Новини та медіа» to close the richness cultural gap (2/3 → 3/3).
7. Line 199: Consider replacing «найпрекрасніших» with more natural «найчудовіших» or «найяскравіших».