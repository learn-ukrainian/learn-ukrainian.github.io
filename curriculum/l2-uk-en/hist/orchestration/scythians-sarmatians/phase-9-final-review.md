---

## Issues Found

### Issue 1 — [Critical | Pedagogical Dishonesty] Activity instruction falsely attributes a paraphrase as a direct Herodotus excerpt

**File:** `activities/scythians-sarmatians.yaml`, line 8  
**Exact text:** `instruction: Прочитайте уривок з «Історії» Геродота та дайте відповідь на запитання.`

The reading text in lines 5–7 is a creative paraphrase/conflation, **not** a translation. The phrase "засипаючи криниці та знищуючи траву" merges Herodotus 4.46 and 4.120+ into a single continuous sentence that Herodotus never wrote. Compare against the actual translation in the main module (line 166) — they are materially different. Labelling a paraphrase as "уривок з «Історії» Геродота" is academically dishonest and would confuse students who later look up the source.

---

### Issue 2 — [Important | Russianism] Analytic superlative

**File:** `scythians-sarmatians.md`, line 23  
**Exact text:** `це була найбільш ефективна, раціональна та складна стратегія виживання`  
Ukrainian State Standard 2024 requires synthetic superlatives. "Найбільш + adj" is a calque from Russian. Correct form: **найефективніша, найраціональніша та найскладніша**.  
Green Team flagged this in their table but the fix was never applied to the file.

---

### Issue 3 — [Important | Russianism] Analytic comparative

**File:** `scythians-sarmatians.md`, line 47  
**Exact text:** `більш організовані і жорстокі`  
Same category. Correct form: **організованіші й жорстокіші**.  
Green Team flagged this but did not apply the fix.

---

### Issue 4 — [Important | Style] Triple repetition of «невід'ємною частиною»

**File:** `scythians-sarmatians.md`, lines 134, 195, 200  
Three identical constructions in the same module:
1. Line 134: `ці мовчазні вартові стали невід'ємною частиною українського пейзажу`
2. Line 195: `Скіфія була невід'ємною частиною європейської історії та економіки`
3. Line 200: `вони є невід'ємною частиною нашої історії`

Green Team flagged this but did not apply fixes.

---

### Issue 5 — [Minor | Euphony] Hard consonant cluster «з самим»

**File:** `scythians-sarmatians.md`, line 59  
**Exact text:** `а з самим простором`  
Before a sibilant, Ukrainian orthography requires «із» → **а із самим простором**.

---

### Issue 6 — [Minor | Persona] "Читання:" prefix breaks the history professor voice

**File:** `scythians-sarmatians.md`, line 42  
**Exact text:** `## Читання: Скіфи: Імперія золота`  
The prefix "Читання:" is a language-textbook convention. In a HIST seminar module narrated in the voice of a university professor, it is register-breaking and out of place. Green Team flagged it; was not applied.

---

### Issue 7 — [Pedagogical Gap] comparative-study model_answer silently omits one of its own four criteria

**File:** `activities/scythians-sarmatians.yaml`, lines 46–50  
The `criteria` list declares four items: *Головна військова сила*, *Основна зброя*, *Соціальний статус жінок*, **Вплив на грецькі колонії**. The `model_answer` covers only the first three (military tactics and women's status). The fourth criterion — Greek colony influence — is completely absent. Students shown this model answer will not know how a complete response looks, because the model answer does not model completeness.

---

## Fixes

===FIX_START===
FILE: curriculum/l2-uk-en/hist/activities/scythians-sarmatians.yaml
---OLD---
  instruction: Прочитайте уривок з «Історії» Геродота та дайте відповідь на запитання.
---NEW---
  instruction: Прочитайте адаптований текст за мотивами «Історії» Геродота та дайте відповідь на запитання.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/hist/scythians-sarmatians.md
---OLD---
це була найбільш ефективна, раціональна та складна стратегія виживання людства в суворих умовах посушливого клімату степу.
---NEW---
це була найефективніша, найраціональніша та найскладніша стратегія виживання людства в суворих умовах посушливого клімату степу.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/hist/scythians-sarmatians.md
---OLD---
Вони були краще озброєні (їхні стріли з бронзовими наконечниками були смертоносними), більш організовані і жорстокі.
---NEW---
Вони були краще озброєні (їхні стріли з бронзовими наконечниками були смертоносними), організованіші й жорстокіші.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/hist/scythians-sarmatians.md
---OLD---
Стоячи століттями серед степу, ці мовчазні вартові стали невід'ємною частиною українського пейзажу, свідками зміни епох і народів.
---NEW---
Стоячи століттями серед степу, ці мовчазні вартові вросли в серце українського пейзажу, ставши свідками зміни епох і народів.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/hist/scythians-sarmatians.md
---OLD---
Насправді ж Скіфія була невід'ємною частиною європейської історії та економіки.
---NEW---
Насправді ж Скіфія була органічно вплетена в тканину європейської історії та економіки.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/hist/scythians-sarmatians.md
---OLD---
вони є невід'ємною частиною нашої історії.
---NEW---
вони складають фундамент нашої історії.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/hist/scythians-sarmatians.md
---OLD---
а з самим простором, з порожнечею, яку неможливо перемогти мечем,
---NEW---
а із самим простором, з порожнечею, яку неможливо перемогти мечем,
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/hist/scythians-sarmatians.md
---OLD---
## Читання: Скіфи: Імперія золота
---NEW---
## Скіфи: Імперія золота
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/hist/activities/scythians-sarmatians.yaml
---OLD---
  model_answer: |
    > [!model-answer]
    Головна відмінність полягає у військовій тактиці. Скіфи покладалися на легку кінноту та масований обстріл з луків (дистанційний бій). Сармати ж здійснили революцію, створивши важку кінноту (катафрактаріїв), озброєну довгими списами для таранного удару (ближній бій).

    У соціальному плані сармати відрізнялися значно вищим статусом жінок. Якщо у скіфів влада була патріархальною, то сарматські жінки («амазонки») брали участь у війнах нарівні з чоловіками, що підтверджується похованнями зі зброєю.
---NEW---
  model_answer: |
    > [!model-answer]
    Головна відмінність полягає у військовій тактиці. Скіфи покладалися на легку кінноту та масований обстріл з луків (дистанційний бій). Сармати ж здійснили революцію, створивши важку кінноту (катафрактаріїв), озброєну довгими списами для таранного удару (ближній бій).

    У соціальному плані сармати відрізнялися значно вищим статусом жінок. Тоді як скіфське суспільство було переважно патріархальним, сарматські жінки («амазонки») брали участь у війнах нарівні з чоловіками — це підтверджується похованнями зі зброєю.

    Вплив на грецькі колонії також суттєво різнився. Скіфи торгували із грецькими містами, постачаючи зерно і хутро в обмін на вино та металеві вироби — саме скіфський хліб годував Афіни. Сармати пішли далі: «сарматизація» Боспорського царства означала, що грецька еліта Пантікапея переймала сарматський одяг, зброю і імена, а сарматські династії безпосередньо приходили до влади у грецьких містах.
===FIX_END===

---

## Notes (non-blocking)

- **Vocabulary file missing** — the audit flags this as INFO (non-blocking), but `vocabulary/scythians-sarmatians.yaml` does not exist. The plan's `vocabulary_hints` lists 12 required terms. This should be created in a follow-up pass.
- **Factual claims all verified** — dates (513 BC, 21 June 1971), pectoral weight (1150 g, 958 purity), Mozolevsky, river etymologies (*dānu*), Gobryas interpretation, Sarmatian 20% burial statistic — all accurate or appropriately hedged.
- **No Russian characters** (ы, э, ё, ъ) found. **No Russianisms** beyond the two analytic forms already fixed above.

===VERDICT===
APPROVE
===END_VERDICT===