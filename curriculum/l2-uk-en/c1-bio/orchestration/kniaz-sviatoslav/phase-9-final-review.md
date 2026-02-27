## Adversarial QA Review — kniaz-sviatoslav (c1-bio-2)

---

## Issues Found

### Issue 1 — FACTUAL ERROR: Age at death overstated

**File**: `kniaz-sviatoslav.md`, line 25
**Text**: `він загинув у віці близько 34 років`
**Problem**: Ukrainian historical consensus (Hrushevsky; сучасна Ukrainian Wikipedia) places Sviatoslav's birth at *~942 CE*. Death in spring 972 gives approximately 30 years of age, not 34. The figure of 34 requires a birth year of ~938, which is outside the mainstream Ukrainian scholarly position. This appears to come from older Russian imperial historiography that pushed the birth year back. A C1 seminar module must reflect Ukrainian scholarly consensus.
**Fix**: Change to `близько 30 років`

---

### Issue 2 — FACTUAL ERROR: Distance to Constantinople

**File**: `kniaz-sviatoslav.md`, line 138
**Text**: `всього за 100 км від Константинополя`
**Problem**: Arcadiopolis (modern Lüleburgaz, Turkey) is approximately 145–150 km from Constantinople (Istanbul) as the crow flies; by any ancient road it is 200+ km. "100 km" significantly understates the distance and misrepresents the strategic threat. Verified against coordinates: Lüleburgaz ~41.4°N 27.4°E vs Istanbul ~41.0°N 29.0°E.
**Fix**: Change to `близько 150 км від Константинополя`

---

### Issue 3 — PLAN COMPLIANCE: Missing skull cup inscription

**File**: `kniaz-sviatoslav.md`, lines 175–177
**Problem**: The plan explicitly requires under "Останні роки": *"Легенда про чашу з черепа: напис хана Курі «Чужого шукаючи, своє втратив»"*. The module describes the skull cup ritual in detail but **completely omits the inscription**. This is a direct plan compliance gap — the phrase is a key memorable pedagogical hook for the section, and it's the only part of the "Чаша з черепа" bullet that is missing.
**Fix**: Add the inscription after the cup description sentence.

---

### Issue 4 — LLM ARTIFACT: Incoherent mixed metaphor

**File**: `kniaz-sviatoslav.md`, line 38
**Text**: `чия кров і чия естетика течуть у жилах сучасних захисників`
**Problem**: "Естетика" (aesthetics/aesthetic sensibility) cannot "flow through veins". This is a classic LLM conflation artifact — two separate ideas ("blood lineage" and "aesthetic tradition") are grammatically merged into a single impossible image. Even at C1 literary register this is incoherent, not poetic.
**Fix**: Replace with a coherent formulation.

---

### Issue 5 — CALQUE: "Більше того"

**File**: `kniaz-sviatoslav.md`, line 135
**Text**: `Більше того, це був стратегічний плацдарм для тиску на Константинополь.`
**Problem**: Calque from Russian "Более того" / English "Moreover". Native literary Ukrainian uses "До того ж", "Ба більше", or restructuring.
**Fix**: `До того ж, це був стратегічний плацдарм...`

---

### Issue 6 — CALQUE: "Врешті-решт"

**File**: `kniaz-sviatoslav.md`, line 152
**Text**: `Врешті-решт, сили були нерівними, і Святослав був змушений укласти почесний мирний договір.`
**Problem**: The literary C1 register calls for "Зрештою" (established in Ukrainian belles-lettres). "Врешті-решт" is a Russianizing calque construction that reads as translated text at this register level.
**Fix**: `Зрештою, сили були нерівними...`

---

### Issue 7 — MISSING FILE: Vocabulary file absent

**File**: `curriculum/l2-uk-en/c1-bio/vocabulary/kniaz-sviatoslav.yaml`
**Problem**: File does not exist. The audit records this as "1 info" (non-blocking), but the plan specifies 10 required vocabulary items with collocations and learner error notes. For a C1 seminar track module, the vocabulary YAML is a required deliverable — it feeds vocabulary drilling and the enrichment pipeline. Creating it below.

---

## Fixes

===FIX_START===
FILE: curriculum/l2-uk-en/c1-bio/kniaz-sviatoslav.md
---OLD---
Його життя було коротким — він загинув у віці близько 34 років — але настільки насиченим подіями, що змінило баланс сил на континенті назавжди.
---NEW---
Його життя було коротким — він загинув у віці близько 30 років — але настільки насиченим подіями, що змінило баланс сил на континенті назавжди.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/c1-bio/kniaz-sviatoslav.md
---OLD---
Кульмінацією протистояння стала битва під Аркадіополем (970 рік), всього за 100 км від Константинополя.
---NEW---
Кульмінацією протистояння стала битва під Аркадіополем (970 рік), всього за 150 км від Константинополя.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/c1-bio/kniaz-sviatoslav.md
---OLD---
Печенізький хан Куря, згідно з легендою, записаною в «Повісті минулих літ», наказав зробити з черепа Святослава **чашу**, окувавши її золотом.

Цей ритуал має глибоке коріння в степовій культурі.
---NEW---
Печенізький хан Куря, згідно з легендою, записаною в «Повісті минулих літ», наказав зробити з черепа Святослава **чашу**, окувавши її золотом. За переказом, на цій чаші було викарбувано напис: «Чужого шукаючи, своє втратив» — безжальний вирок тому, хто поклав все заради далеких завоювань і не повернувся.

Цей ритуал має глибоке коріння в степовій культурі.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/c1-bio/kniaz-sviatoslav.md
---OLD---
Його образ надихає, бо він є справжнім, не вигаданим героєм, чия кров і чия естетика течуть у жилах сучасних захисників.
---NEW---
Його образ надихає, бо він є справжнім, не вигаданим героєм, чий дух і чия лицарська традиція живуть у серцях сучасних захисників.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/c1-bio/kniaz-sviatoslav.md
---OLD---
Більше того, це був стратегічний плацдарм для тиску на Константинополь.
---NEW---
До того ж, це був стратегічний плацдарм для тиску на Константинополь.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/c1-bio/kniaz-sviatoslav.md
---OLD---
Врешті-решт, сили були нерівними, і Святослав був змушений укласти почесний мирний **договір**.
---NEW---
Зрештою, сили були нерівними, і Святослав був змушений укласти почесний мирний **договір**.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/c1-bio/vocabulary/kniaz-sviatoslav.yaml
---OLD---

---NEW---
- term: воїн
  ipa:
  pos: іменник
  gender: чол.
  translation: warrior
  collocations:
    - хоробрий воїн
    - полеглий воїн
    - воїн-захисник
  learner_note: "Не плутати з «солдат» (сучасний солдат); «воїн» несе архаїчно-героїчне забарвлення"
  example: "Святослав увійшов в історію як хоробрий воїн, якого боялися навіть вороги."

- term: завойовник
  ipa:
  pos: іменник
  gender: чол.
  translation: conqueror
  collocations:
    - жорстокий завойовник
    - великий завойовник
    - завойовник нових земель
  example: "Святослав увійшов у світову історію як завойовник, що знищив Хозарський каганат."

- term: каганат
  ipa:
  pos: іменник
  gender: чол.
  translation: khaganate
  collocations:
    - Хозарський каганат
    - знищення каганату
    - розпад каганату
  example: "Розгром Хозарського каганату відкрив Русі прямий вихід на торгові шляхи Сходу."

- term: похід
  ipa:
  pos: іменник
  gender: чол.
  translation: campaign, march
  collocations:
    - військовий похід
    - піти в похід
    - східний похід
    - балканський похід
  example: "Під час Балканського походу Святослав захопив понад вісімдесят міст уздовж Дунаю."

- term: дружина
  ipa:
  pos: іменник
  gender: жін.
  translation: retinue, warband (princely armed force)
  collocations:
    - княжа дружина
    - вірна дружина
    - очолити дружину
  learner_note: "У середньовічному контексті — «збройне оточення князя», не «дружина» (wife/жінка)"
  example: "Дружина Святослава відзначалася незламним бойовим духом і сліпою відданістю своєму ватажкові."

- term: печеніги
  ipa:
  pos: іменник
  gender: чол. мн.
  translation: Pechenegs (nomadic steppe people)
  collocations:
    - напад печенігів
    - облога печенігів
    - союз з печенігами
  example: "Поки Святослав воював на Балканах, печеніги оточили Київ і ледь не захопили місто."

- term: пороги
  ipa:
  pos: іменник
  gender: чол. мн.
  translation: rapids (in a river)
  collocations:
    - Дніпрові пороги
    - загибель на порогах
    - обійти пороги
  example: "Свенельд застерігав: «Обійди, княже, пороги на конях, бо стоять печеніги»."

- term: засідка
  ipa:
  pos: іменник
  gender: жін.
  translation: ambush
  collocations:
    - влаштувати засідку
    - потрапити в засідку
    - засідка ворога
  example: "Біля Дніпрових порогів на Святослава вже чекала підготовлена засідка."

- term: данник
  ipa:
  pos: іменник
  gender: чол.
  translation: tributary (one who pays tribute)
  collocations:
    - брати в данники
    - звільнити від данини
    - данники хозарів
  example: "В'ятичі були данниками хозарів, доки Святослав не звільнив їх і не включив до складу Русі."

- term: договір
  ipa:
  pos: іменник
  gender: чол.
  translation: treaty, agreement
  collocations:
    - укласти договір
    - мирний договір
    - порушити договір
  example: "Зрештою, сили були нерівними, і Святослав був змушений укласти почесний мирний договір."

- term: чаша
  ipa:
  pos: іменник
  gender: жін.
  translation: cup, goblet
  collocations:
    - ритуальна чаша
    - чаша з черепа
    - пити з чаші
  example: "Хан Куря наказав зробити ритуальну чашу з черепа Святослава, окувавши її золотом."

- term: череп
  ipa:
  pos: іменник
  gender: чол.
  translation: skull
  collocations:
    - череп ворога
    - зробити чашу з черепа
  example: "Пити з черепа великого воїна означало не зневагу, а найвищу честь і містичне причастя до його сили."

- term: здобич
  ipa:
  pos: іменник
  gender: жін.
  translation: spoils, booty
  collocations:
    - багата здобич
    - ділити здобич
    - захопити здобич
  example: "Дружинники жили за рахунок здобичі та данини з підкорених народів."

- term: облога
  ipa:
  pos: іменник
  gender: жін.
  translation: siege
  collocations:
    - тримати облогу
    - зняти облогу
    - виснажлива облога
  example: "Тримісячна облога Доростола стала легендою військової доблесті руських воїнів."

- term: перемога
  ipa:
  pos: іменник
  gender: жін.
  translation: victory
  collocations:
    - здобути перемогу
    - велика перемога
    - піррова перемога
  example: "Перемога над Хазарією відкрила Русі шлях до нових торгових артерій, але ціною безпеки кордонів."
===FIX_END===

---

===VERDICT===
APPROVE
===END_VERDICT===

**Post-fix summary**: 6 issues fixed in the main content file (1 factual age error, 1 factual distance error, 1 plan compliance gap — skull cup inscription, 1 LLM mixed metaphor, 2 calques); vocabulary file created with all 10 required + 5 recommended terms. The module is otherwise excellent: narrative is compelling, decolonization framing is sharp, all plan sections present, activities are factually sound, no Russianisms in core prose, no Russian characters, chronicle quotes are accurate.