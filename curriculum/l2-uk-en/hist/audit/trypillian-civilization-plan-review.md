# Plan Review (Seminar): trypillian-civilization

**Track:** HIST | **Sequence:** 1 | **Version:** '2.0'
**Verdict:** NEEDS FIXES

---

## Rule Compliance

| Check | Status | Details |
|-------|--------|---------|
| word_target | PASS | Plan: 5000, Config: 5000 |
| section_budgets | PASS | Sum = 5000 (10 sections x 500), matches target exactly |
| section_balance | PASS | All sections equal at 500w, no section under target |
| required_fields | PASS | All present: module, level, sequence, slug, version, title, focus, pedagogy, word_target, objectives, content_outline, vocabulary_hints, activity_hints, persona |
| version_string | PASS | `'2.0'` (quoted string) |

## Factual Accuracy

| Claim | Source Used | Verified? | Notes |
|-------|------------|-----------|-------|
| Trypillia culture dates: 5500-2750 BC | Wikipedia | YES | Standard range, sometimes given as 5400-2700. Acceptable. |
| Khvoika dates: 1850-1914 | Wikipedia | YES | Confirmed: born 1850, died 1914 |
| First excavations: 1896 | Wikipedia | YES | Kyrylivska street excavations began 1893; Trypillia discovery ~1896 |
| XI Archaeological Congress in Kyiv, 1899 | Wikipedia | YES | Confirmed: XI Всеросійський археологічний з'їзд, Київ, 1899 |
| Videyko M.Yu. — Trypillia researcher | Wikipedia | YES | Відейко Михайло Юрійович (b. 1956), archaeologist, PhD |
| Тальянки: 450 ha | Wikipedia | YES | Confirmed: "найбільше в Європі поселення — 450 га" |
| Майданецьке: mega-settlement | Wikipedia | YES | 270-300 ha, confirmed |
| Небелівка: Trypillia settlement | Wikipedia | YES | ~250-300 ha, British-Ukrainian expeditions |
| Population "до 15,000 мешканців" | Wikipedia | PARTIAL | Тальянки estimated at 15,000-25,000. The "до 15,000" figure is the conservative low end and may understate the actual range. |
| Khvoika: "чех" (Czech origin) | Wikipedia | YES | Born in Seminy, Bohemia (Богемське королівство) |
| "Древние обитатели Среднего Приднепровья" (1913) | Wikipedia | YES | Real work by Khvoika, published posthumously |
| "Горизонт спалених хат" — ritual burning every 60-80 years | Domain knowledge | PARTIAL | The "горизонт спалених хат" phenomenon is real. The 60-80 year cycle is one hypothesis (Videyko), but debated. Plan correctly marks it as "гіпотеза М. Відейка". |

## Decolonization Check

| Item | Status | Details |
|------|--------|---------|
| No Russian-centric framing | PASS | History told from Ukrainian perspective; Trypillia as Ukrainian heritage |
| No imperial myths | PASS | Explicit section "Деколонізаційний погляд" countering Soviet "примітивних дикунів" myth |
| Correct terminology | PASS | "Трипільська цивілізація", "протоміста", proper Ukrainian names |
| Ukrainian agency | PASS | Ukrainians as inheritors; "автохтонна спадщина" framing |
| Decolonization section present | PASS | Dedicated 500-word section with myth-busting |

## Vocabulary Verification

| Word | VESUM | Issues |
|------|-------|--------|
| протомісто | OK | |
| егалітарний | OK | |
| автохтонний | OK | |
| енеоліт | OK | |
| сакральний | OK | |
| перелоговий (перелогове) | OK | But see HIGH issue below re: English gloss |
| матріархат | OK | |
| вівтар | OK | |
| горно | OK | |
| спіралеподібний | OK | |
| глинобитний | OK | |
| антропоморфний | OK | |
| сварга | OK | |
| мегапоселення | NOT FOUND | Domain-specific compound; widely used in Ukrainian archaeology but absent from VESUM. Acceptable for seminar. |

## Issues Found

### CRITICAL (must fix before build)
None.

### HIGH (should fix before build)

1. **Wrong English gloss for "перелогове землеробство"** — Plan says "slash-and-burn agriculture" but перелогове землеробство = fallow/shifting agriculture (leaving land fallow between cycles). Slash-and-burn = підсічно-вогневе землеробство. These are different agricultural systems. Fix the English translation in `vocabulary_hints.recommended`.

### MEDIUM (fix if possible)

1. **Population figure understated** — Plan says "до 15,000 мешканців" in the Протоміста section. Wikipedia cites Тальянки at 15,000-25,000 inhabitants. The plan uses the most conservative estimate as a ceiling. Consider changing to "15,000-20,000 мешканців" or "понад 15,000" to better represent the scholarly range.

2. **Source URL too generic** — Source #2 (Відейко М.Ю. "Трипільська цивілізація") links to `https://litopys.org.ua/` which is a general portal, not a direct link to the monograph. Consider noting "бібліографічне посилання" or using a more specific URL.

### LOW (informational)

1. **"мегапоселення" absent from VESUM** — Used in `content_outline` and `vocabulary_hints`. It's standard archaeological jargon (widely used by Videyko and others) but not in the morphological dictionary. Not a problem for seminar track, just noting.

2. **All sections exactly 500 words** — Uniform section budgets (10 x 500) are mechanically even. Consider redistributing — the "Протоміста" and "Духовний світ" sections likely need more space (600-700w) while "Потрібно більше практики?" could work with 300w.

3. **Khvoika's book title in Russian** — "Древние обитатели Среднего Приднепровья" is correctly cited in the original Russian publication language. Historically accurate, but could note the Ukrainian transliteration for learner clarity.

## Suggested Fixes

### Fix 1 (HIGH): Correct English gloss

```yaml
# OLD
- перелогове землеробство (slash-and-burn agriculture) — виснаження земель при перелоговій системі

# NEW
- перелогове землеробство (fallow agriculture) — виснаження земель при перелоговій системі
```

### Fix 2 (MEDIUM): Update population figure

```yaml
# OLD
- Масштаби поселень (до 15,000 мешканців) — порівняння з тогочасним Шумером; поселення-гіганти на Черкащині (450 га)

# NEW
- Масштаби поселень (15,000-20,000 мешканців) — порівняння з тогочасним Шумером; поселення-гіганти на Черкащині (до 450 га)
```

---

*Review by: Claude (plan-review-seminar) | Date: 2026-03-05 | ESU: not yet ingested (0 points) | Sources: Wikipedia, VESUM, domain knowledge*
*Reference: #729*
