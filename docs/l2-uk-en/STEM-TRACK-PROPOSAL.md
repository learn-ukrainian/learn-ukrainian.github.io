# STEM & Professional Specialization Tracks — Proposal v2

> **Status**: APPROVED v5 — Gemini scored 9/10, all findings addressed (4/10 → 9/10 over 4 review rounds)
> **Date**: 2026-03-14
> **Authors**: Claude (architect) + Gemini (adversarial reviewer)
> **Related**: #409 (RFC: Curriculum Reorganization), SPECIALIZATION-TRACKS.md

---

## Problem

1. The old SPECIALIZATION-TRACKS.md lists 28 tracks — absurdly fragmented
2. PRO tracks (B2-PRO: 40, C1-PRO: 50 modules) are soft-skill focused, not domain-depth
3. No STEM content exists in the platform
4. No disk capacity for STEM RAG — must work with Wikipedia + VESUM + GRAC + live web fetch

## Design Principles

- **9 new domain tracks** (consolidated from 28)
- **PRO tracks retired** — all 90 modules redistributed into domain tracks
- **Entry at B2** (learners need professional vocabulary while studying, not after C1)
- **2500-word modules** (not 5000 — terminology density ≠ narrative length)
- **No RAG dependency** — research uses Wikipedia + VESUM + GRAC + live web fetch
- **Dual-register**: every module teaches formal standard AND workplace jargon side-by-side
- **Templates distinct from seminars** — term-definition-example structure, not narrative prose

---

## Complete Track Landscape

### Existing seminar tracks (keep as-is)
- **HIST** — Ukrainian History (140 modules)
- **BIO** — Ukrainian Biographies (175 modules)
- **ISTORIO** — Historiography (136 modules)
- **LIT** — Ukrainian Literature + sub-tracks (30+ modules)
- **OES** — Old East Slavic (100 modules)
- **RUTH** — Ruthenian / Old Ukrainian (100 modules)

### New domain tracks (9 tracks, 4 build phases)

---

## Track 1: IT — Information Technology & Computer Science

**Entry**: B2 | **Modules**: 35 | **Word target**: 2500 | **Build phase**: 1

**What it covers**:
- Programming fundamentals & paradigms (змінна, функція, цикл, масив, об'єкт)
- Web development: frontend (верстка, фреймворк, компонент) + backend (сервер, API, маршрутизація)
- Databases & data engineering (таблиця, запит, індекс, транзакція)
- Software architecture & design patterns (мікросервіси, патерн, рефакторинг)
- Cybersecurity (шифрування, автентифікація, вразливість, брандмауер)
- Data science & AI/ML (нейромережа, модель, датасет, навчання з підкріпленням)
- Project management: Agile/Scrum in Ukrainian (спринт, беклог, ретроспектива)
- QA & testing (тестування, баг-репорт, регресія, автотест)

**Target audience**: Developers, IT professionals, CS students working in Ukrainian-speaking teams (Kyiv, Lviv tech hubs)

**First 5 modules**:
1. `it-fundamentals` — Базова IT-термінологія: апаратне/програмне забезпечення, операційна система — formal vs jargon (софт, залізо)
2. `programming-basics` — Мови програмування: змінна, функція, цикл, масив, об'єкт — formal vs jargon (фіча, баг, коміт)
3. `web-frontend` — Фронтенд: верстка, стилі, скрипти, фреймворк, компонент, рендеринг
4. `web-backend` — Бекенд: сервер, API, база даних, запит, відповідь, маршрутизація
5. `databases` — Бази даних: таблиця, запит, індекс, транзакція, нормалізація, реплікація

**Absorbs from PRO** (7 modules): `it-vocabulary-1`, `it-vocabulary-2`, `technical-documentation`, `technical-checkpoint`, `technical-integration` (B2-PRO); `it-management`, `it-architecture` (C1-PRO)

**Key sources**: dou.ua, itc.ua, ain.ua, speka.media, Ukrainian Wikipedia, ДСТУ 2938:1994

**Activity types**: term-to-definition matching, formal→jargon matching (програмне забезпечення↔софт), "fix the calque" exercises (surzhyk→standard), categorization (frontend/backend/DevOps), scenario MCQ (standup, code review, incident response)

---

## Track 2: MED — Medical, Healthcare & Life Sciences

**Entry**: B2 | **Modules**: 35 | **Word target**: 2500 | **Build phase**: 1

**What it covers**:
- Anatomy & body systems (скелет, серцево-судинна, дихальна, травна система)
- Human biology & genetics (клітина, ДНК, генетика, імунітет, гормон) — human-focused biology per Gemini recommendation; macro-biology (екосистема, еволюція) moved to AGR
- Symptoms, conditions, diagnoses (біль, набряк, запаморочення, діагноз)
- Pharmaceutical terminology (ліки, дозування, побічні ефекти, рецепт)
- Patient communication & medical history taking (анамнез, скарга, огляд)
- Emergency medicine (травма, кровотеча, реанімація, шок)
- Mental health & psychology (депресія, тривожність, психотерапія, ПТСР)
- Public health & epidemiology (вакцинація, карантин, пандемія, імунітет)
- Ukrainian healthcare system (МОЗ, НСЗУ, сімейний лікар, е-Здоров'я)

**Target audience**: Healthcare workers (doctors, nurses, paramedics), medical students, humanitarian workers in Ukraine, diaspora medical professionals, psychologists

**First 5 modules**:
1. `body-systems` — Системи організму: скелет, м'язи, серцево-судинна, дихальна, травна система
2. `human-biology` — Біологія людини: клітина, ядро, мембрана, ДНК, білок, фермент, імунітет
3. `symptoms-complaints` — Скарги пацієнта: біль, набряк, запаморочення, нудота, задишка, висип
4. `diagnosis-procedures` — Діагностика: аналіз крові, УЗД, рентген, МРТ, біопсія
5. `emergency` — Невідкладна допомога: травма, кровотеча, перелом, опік, реанімація, шок

**Absorbs from PRO** (4 modules): `medical-vocabulary`, `medical-consultation` (B2-PRO); `healthcare-management`, `pharmaceutical` (C1-PRO)

**Key sources**: umj.com.ua, moz.gov.ua (МОЗ protocols), inscience.io, Ukrainian Wikipedia, VESUM

**Activity types**: symptom-to-system matching, patient history fill-in dialogue, prescription reading, process ordering (triage, surgical prep), scenario MCQ (differential diagnosis vocabulary)

---

## Track 3: STEM — Science, Mathematics & Engineering

**Entry**: B2 | **Modules**: 25 | **Word target**: 2500 | **Build phase**: 2

**What it covers** (math + physics + chemistry + engineering — biology moved to MED):
- Mathematical terminology & Ukrainian notation conventions (рівняння, функція, похідна, інтеграл)
- Statistics & probability (ймовірність, вибірка, середнє, стандартне відхилення)
- Physics: mechanics, electricity, optics, thermodynamics (сила, маса, енергія, опір, напруга)
- Chemistry: elements, reactions, lab equipment (елемент, сполука, реакція, розчин, кислота)
- Engineering fundamentals: materials, structures, systems (матеріал, конструкція, навантаження)
- Scientific method & research methodology (гіпотеза, експеримент, достовірність)
- Ukrainian scientific tradition (Вернадський, Кондратюк, Патон, Королев — decolonized)

**Target audience**: University students in STEM fields, researchers, science teachers, engineers

**First 5 modules**:
1. `scientific-method` — Науковий метод: гіпотеза, експеримент, спостереження, аналіз, висновок, достовірність
2. `math-fundamentals` — Математична мова: рівняння, функція, похідна, інтеграл, множина, нерівність
3. `physics-mechanics` — Механіка: сила, маса, швидкість, прискорення, енергія, імпульс
4. `chemistry-basics` — Хімічна мова: елемент, сполука, реакція, розчин, кислота, основа
5. `statistics` — Статистика: ймовірність, вибірка, розподіл, кореляція, регресія

**Absorbs from PRO** (3 modules): `scientific-writing-basics` (B2-PRO); `industry-integration`, `industry-checkpoint` (C1-PRO)

**Key sources**: Ukrainian Wikipedia, nas.gov.ua (NASU), kunsht.com.ua, ДСТУ standards for scientific terminology, VESUM, GRAC

**Activity types**: formula notation exercises, term-to-definition matching, unit conversion vocabulary, lab equipment identification, process ordering (lab procedures), categorization (organic/inorganic, types of energy)

---

## Track 4: MIL — Military & Defense

**Entry**: B2 | **Modules**: 30 | **Word target**: 2500 | **Build phase**: 2

**What it covers**:
- ЗСУ structure: бригада, батальйон, рота, взвод, відділення
- Ranks & positions: солдат → генерал, штабні посади
- Weapons & equipment: стрілецька зброя, артилерія, БПЛА, бронетехніка, боєприпаси
- Tactical & operational vocabulary: оборона, наступ, фланг, прикриття, евакуація
- Military communications & radio protocol: позивний, шифрування, координати
- Logistics & supply: постачання, ланцюг забезпечення, медевак
- Intelligence & security: розвідка, контррозвідка, OSINT, шифрування
- NATO integration: STANAG terminology, interoperability vocabulary
- Tactical medicine: тактична медицина, турнікет, евакуаційний маршрут (cross-ref MED)

**Target audience**: Foreign volunteers, NATO liaison personnel, military translators, defense journalists, diaspora supporting Ukraine's defense

**First 5 modules**:
1. `zsu-structure` — Структура ЗСУ: бригада, батальйон, рота, взвод, відділення, командир, штаб
2. `ranks-positions` — Звання та посади: солдат, сержант, лейтенант, полковник, генерал
3. `weapons-equipment` — Озброєння: гвинтівка, кулемет, гаубиця, БПЛА, броньовик, боєприпаси
4. `tactical-vocabulary` — Тактика: позиція, оборона, наступ, фланг, прикриття, відступ
5. `communications` — Зв'язок: позивний, радіостанція, шифрування, координати, цілевказівка

**Absorbs from PRO**: none

**Key sources**: mil.gov.ua, armyinform.com.ua, mil.in.ua (Мілітарний), Ukrainian Wikipedia, NATO-Ukraine terminology guides

**Activity types**: rank ordering, map reading vocabulary, radio protocol fill-in, equipment categorization, scenario MCQ (tactical situations)

---

## Track 5: BUS — Business, Finance & Economics

**Entry**: B2 | **Modules**: 35 | **Word target**: 2500 | **Build phase**: 3

**What it covers**:
- Microeconomics & macroeconomics (попит, пропозиція, ринок, інфляція, ВВП)
- Finance & banking (кредит, депозит, валюта, інвестиція, акція)
- Accounting & taxation (баланс, прибуток, витрати, ПДВ, звітність)
- Marketing & sales (бренд, цільова аудиторія, конверсія, SEO)
- Entrepreneurship & startups (бізнес-план, інвестор, ФОП, ТОВ)
- International trade & customs (експорт, імпорт, мито, логістика)
- HR & career management (резюме, співбесіда, випробувальний термін)
- Corporate communication: email, meetings, presentations, negotiations
- Executive communication: board presentations, strategic reports

**Target audience**: Business professionals, economists, entrepreneurs, MBA students, investors, corporate employees

**First 5 modules**:
1. `economics-basics` — Основи економіки: попит, пропозиція, ринок, інфляція, ВВП, бюджет
2. `finance-banking` — Фінанси та банківська справа: кредит, відсоток, депозит, валюта, інвестиція
3. `accounting` — Бухгалтерія: баланс, прибуток, витрати, податок, ПДВ, звітність
4. `business-communication` — Ділове листування: лист, запит, пропозиція, протокол наради
5. `entrepreneurship` — Підприємництво: стартап, бізнес-план, інвестор, масштабування, ФОП, ТОВ

**Absorbs from PRO** (41 modules): `business-email-foundations`, `email-requests-proposals`, `email-followups-threads`, `meeting-participation`, `meeting-minutes`, `presentations-structure`, `presentations-delivery`, `reports-writing`, `reports-analysis`, `small-talk-networking`, `negotiations-basics`, `negotiations-tactics`, `finance-vocabulary`, `financial-reports`, `hr-vocabulary`, `job-applications`, `business-checkpoint`, `business-writing-integration`, `business-communication-capstone`, `cross-domain-practice`, `b2-pro-integration`, `b2-pro-capstone` (B2-PRO 22); `executive-email`, `board-presentations`, `strategic-reports`, `leadership-rhetoric`, `executive-networking`, `fintech-banking`, `investment-analysis`, `executive-capstone`, `executive-checkpoint`, `executive-integration`, `c1-pro-integration`, `c1-pro-capstone`, `career-development`, `change-management`, `negotiation-advanced`, `conflict-resolution`, `mentoring-coaching`, `personal-branding`, `professional-portfolio` (C1-PRO 19)

**Key sources**: Forbes Ukraine, epravda.com.ua (Економічна правда), mind.ua, bank.gov.ua (НБУ), Ukrainian Wikipedia

**Activity types**: financial statement reading, term matching, startup pitch vocabulary, tax form comprehension, email/meeting scenario MCQ, business registration process

---

## Track 6: LAW — Legal & Public Administration

**Entry**: B2 | **Modules**: 25 | **Word target**: 2500 | **Build phase**: 3

**What it covers**:
- Ukrainian legal system structure (Конституційний суд, Верховна Рада, прокуратура)
- Constitutional law (права людини, свободи, громадянство)
- Civil & contract law (договір, зобов'язання, позов, компенсація)
- Criminal law (злочин, покарання, вирок, апеляція)
- Corporate & commercial law (статут, засновник, ліцензія)
- Administrative procedures (дозвіл, реєстрація, оскарження)
- Court procedures & legal document reading (засідання, свідок, вердикт)
- International law & EU integration (міжнародне право, ратифікація, конвенція)
- Diplomatic protocol (дипломатична нота, акредитація, імунітет) — absorbed from DIP

**Target audience**: Lawyers, legal translators, NGO workers, government employees, diplomats, diaspora dealing with Ukrainian legal system

**First 5 modules**:
1. `legal-system` — Правова система України: закон, підзаконний акт, Конституція, правосуддя
2. `constitutional-law` — Конституційне право: права людини, свободи, обов'язки, громадянство
3. `civil-law` — Цивільне право: договір, зобов'язання, позов, відповідач, позивач
4. `criminal-law` — Кримінальне право: злочин, покарання, підозрюваний, обвинувачений, вирок
5. `court-procedures` — Судочинство: засідання, свідок, прокурор, адвокат, вердикт

**Absorbs from PRO** (4 modules): `legal-vocabulary`, `contract-reading` (B2-PRO); `international-law`, `corporate-law` (C1-PRO)

**Key sources**: zakon.rada.gov.ua, yur-gazeta.com, mfa.gov.ua, Ukrainian Wikipedia, VESUM

**Activity types**: legal document reading, term matching, court role identification, contract clause analysis, scenario MCQ (jurisdiction, procedures)

---

## Track 7: ACAD — Academic Research & Pedagogy

**Entry**: B2 | **Modules**: 25 | **Word target**: 2500 | **Build phase**: 4

**What it covers**:
- Academic writing structure (вступ, основна частина, висновки, анотація)
- Citation & referencing (покликання, бібліографія, ДСТУ 8302:2015)
- Literature review methodology (аналіз джерел, систематизація, критичний огляд)
- Research methodology (методологія, вибірка, валідність, надійність)
- Grant writing & project proposals (грант, заявка, кошторис, очікувані результати)
- Conference presentations & abstracts (тези, доповідь, секція, дискусія)
- Ukrainian education system: НУШ, ЗНО/НМТ, МОН structure
- Classroom language & pedagogy (урок, завдання, оцінювання, компетентність)
- Higher education: Bologna process (бакалавр, магістр, аспірант, кафедра, деканат)
- Thesis & dissertation (дисертація, захист, опонент, автореферат)
- Peer review process (рецензування, редакційна колегія, відхилення, доопрацювання)

**Target audience**: University students, researchers, teachers, education administrators, grant writers, academic translators

**First 5 modules**:
1. `academic-writing` — Науковий стиль: анотація, тези, стаття, монографія, дисертація
2. `citation-referencing` — Оформлення покликань: ДСТУ 8302:2015, бібліографічний опис
3. `education-system` — Система освіти України: НУШ, МОН, ЗНО, НМТ, заклади освіти
4. `classroom-language` — Мова уроку: завдання, вправа, оцінювання, компетентність, методика
5. `research-methodology` — Методологія дослідження: вибірка, валідність, кількісний/якісний метод

**Absorbs from PRO** (17 modules): `academic-writing-structure`, `literature-review-academic`, `methodology-writing`, `results-presentation`, `discussion-writing`, `peer-review-process`, `conference-abstracts`, `conference-presentations`, `grant-writing`, `thesis-dissertation`, `academic-correspondence`, `citation-referencing` (C1-PRO); `academic-checkpoint`, `academic-integration`, `academic-capstone` (C1-PRO); `cross-cultural-communication`, `stakeholder-communication` (C1-PRO)

**Key sources**: mon.gov.ua, nus.org.ua, НФДУ (nrfu.org.ua), Ukrainian Wikipedia, «Українська мова за професійним спрямуванням» textbook

**Activity types**: citation format exercises, abstract writing structure, education system matching, classroom instruction vocabulary, research proposal fill-in, scenario MCQ (academic ethics, peer review decisions)

---

## Track 8: MEDIA — Journalism, Media & Communications

**Entry**: B2 | **Modules**: 25 | **Word target**: 2500 | **Build phase**: 4

**What it covers**:
- News writing & reporting (заголовок, лід, джерело, коментар, фактчекінг)
- Broadcasting: TV, radio, podcast (ефір, сюжет, репортаж, монтаж, трансляція)
- Digital media & social media (контент, підписник, охоплення, алгоритм, стрім)
- Disinformation & media literacy (фейк, пропаганда, ІПСО, верифікація)
- Public relations & advertising (PR, прес-реліз, рекламна кампанія, імідж)
- Public speaking & debate (промова, аргументація, риторика, дебати)
- Translation & interpretation basics (переклад, тлумачення, локалізація)
- Crisis communications (антикризові комунікації, спікер, меседж)
- Press freedom & media law (свобода слова, наклеп, авторське право)

**Target audience**: Journalists, media professionals, PR specialists, content creators, translators, activists, OSINT analysts

**First 5 modules**:
1. `news-writing` — Новинна журналістика: заголовок, лід, джерело, коментар, фактчекінг
2. `broadcasting` — Телерадіомовлення: ефір, сюжет, репортаж, ведучий, монтаж, трансляція
3. `digital-media` — Цифрові медіа: контент, підписник, охоплення, алгоритм, монетизація
4. `disinformation` — Дезінформація: фейк, пропаганда, маніпуляція, ІПСО, верифікація
5. `public-speaking` — Публічний виступ: промова, аргументація, риторика, дебати

**Absorbs from PRO** (12 modules): `news-analysis-1`, `news-analysis-2`, `journalism-writing`, `public-speaking-1`, `public-speaking-2`, `debate-skills-advanced`, `interview-skills`, `media-checkpoint` (B2-PRO 8); `media-relations`, `crisis-communication`, `translation-basics`, `interpretation-basics` (C1-PRO 4)

**Key sources**: detector.media, imi.org.ua (IMI), Suspilne style guides, Ukrainian Wikipedia

**Activity types**: headline analysis (identify bias), news article structure, fact-checking vocabulary, public speaking phrase bank, scenario MCQ (editorial decisions, source verification)

---

## Track 9: AGR — Agriculture, Energy & Environment

**Entry**: B2 | **Modules**: 20 | **Word target**: 2500 | **Build phase**: 4

**What it covers**:
- Crop production & soils (посів, урожай, добрива, зрошення, ґрунт)
- Animal husbandry (тваринництво, поголів'я, корм, ветеринарія)
- Agribusiness economics (агрохолдинг, зернотрейдер, елеватор, експорт)
- Energy sector: nuclear, renewables, grid (атомна енергія, відновлювані джерела, мережа)
- Environmental protection (забруднення, утилізація, біорізноманіття, заповідник)
- Ecology & evolution (екосистема, еволюція, природний добір, популяція, ареал) — macro-biology from STEM/MED
- Climate change (парниковий ефект, вуглецевий слід, сталий розвиток)
- Food processing & safety (переробка, сертифікація, НАССР, маркування)
- Rural development (сільська громада, децентралізація, кооператив)

**Target audience**: Agricultural professionals, environmental scientists, energy sector workers, rural development NGOs, EU integration specialists

**First 5 modules**:
1. `crop-production` — Рослинництво: посів, урожай, добрива, зрошення, ґрунт, сівозміна
2. `animal-husbandry` — Тваринництво: поголів'я, стадо, корм, ветеринарія, породи
3. `agribusiness` — Агробізнес: агрохолдинг, зернотрейдер, елеватор, ф'ючерс, логістика
4. `energy-sector` — Енергетика: АЕС, ТЕС, ВЕС, СЕС, мережа, тариф, енергоефективність
5. `environmental-protection` — Довкілля: забруднення, утилізація, біорізноманіття, заповідник

**Absorbs from PRO** (2 modules): `agriculture-agribusiness`, `energy-sector` (C1-PRO)

**Key sources**: latifundist.com, agroportal.ua, energoatom.com.ua, Ukrainian Wikipedia, Geography textbooks (industry/agriculture sections)

**Activity types**: crop cycle process ordering, energy source categorization, environmental impact term matching, agricultural document reading, scenario MCQ (farm management, energy policy)

---

## PRO Track Retirement — Full Module Redistribution

**B2-PRO** (40 modules) → **ALL redistributed**:

| Destination | Modules absorbed | Count |
|-------------|-----------------|-------|
| BUS | business-email-foundations, email-requests-proposals, email-followups-threads, meeting-participation, meeting-minutes, presentations-structure, presentations-delivery, reports-writing, reports-analysis, small-talk-networking, negotiations-basics, negotiations-tactics, finance-vocabulary, financial-reports, hr-vocabulary, job-applications, business-checkpoint, business-writing-integration, business-communication-capstone, cross-domain-practice, b2-pro-integration, b2-pro-capstone | 22 |
| IT | it-vocabulary-1, it-vocabulary-2, technical-documentation, technical-checkpoint, technical-integration | 5 |
| MED | medical-vocabulary, medical-consultation | 2 |
| STEM | scientific-writing-basics | 1 |
| LAW | legal-vocabulary, contract-reading | 2 |
| MEDIA | news-analysis-1, news-analysis-2, journalism-writing, public-speaking-1, public-speaking-2, debate-skills-advanced, interview-skills, media-checkpoint | 8 |
| **Total** | | **40** |

**C1-PRO** (50 modules) → **ALL redistributed**:

| Destination | Modules absorbed | Count |
|-------------|-----------------|-------|
| BUS | executive-email, board-presentations, strategic-reports, leadership-rhetoric, executive-networking, fintech-banking, investment-analysis, executive-capstone, executive-checkpoint, executive-integration, c1-pro-integration, c1-pro-capstone, career-development, change-management, negotiation-advanced, conflict-resolution, mentoring-coaching, personal-branding, professional-portfolio | 19 |
| ACAD | academic-writing-structure, literature-review-academic, methodology-writing, results-presentation, discussion-writing, peer-review-process, conference-abstracts, conference-presentations, grant-writing, thesis-dissertation, academic-correspondence, citation-referencing, academic-checkpoint, academic-integration, academic-capstone, stakeholder-communication, cross-cultural-communication | 17 |
| MED | healthcare-management, pharmaceutical | 2 |
| IT | it-management, it-architecture | 2 |
| LAW | international-law, corporate-law | 2 |
| MEDIA | media-relations, crisis-communication, translation-basics, interpretation-basics | 4 |
| STEM | industry-checkpoint, industry-integration | 2 |
| AGR | agriculture-agribusiness, energy-sector | 2 |
| **Total** | | **50** |

**Grand total**: 40 + 50 = 90 PRO modules → 90 redistributed (verified against curriculum.yaml). **PRO track fully retired.**

---

## What Gets DROPPED (from the 28-track wishlist)

| Old Track | Decision | Reason |
|-----------|----------|--------|
| PROF/PRO | **RETIRED** | All modules redistributed into domain tracks |
| HUM | **DROP** | Too vague. Philosophy → C2 core. Sociology/Psychology → MED (mental health) |
| TRN | **DROP** | Translation basics → MEDIA. Full translation training is graduate-level, not L2 |
| DIP | **MERGE → LAW** | Diplomatic protocol = international law + communication. Not enough for standalone |
| TRS | **DROP** | Tourism vocabulary covered in A2-B1 core practical modules |
| ART | **DROP** | Arts vocabulary covered in LIT seminar track + C2 stylistics |
| SPT | **DROP** | Too niche, no professional demand |
| REL | **DROP** | Covered in HIST track (religion-in-ukraine module) |
| PSY | **MERGE → MED** | Clinical terms in MED mental health section |
| ARC | **MERGE → STEM** | Architecture/construction → engineering section |
| NUC | **MERGE → AGR** | Nuclear energy → AGR energy sector section |
| NGO | **MERGE → LAW** | NGO operations → LAW public administration |
| AVN, MAR, SPC | **DROP** | Hyper-niche, no audience |
| FAS, PUB, CHD | **DROP** | Hyper-niche |

---

## Build Priority Order

| Phase | Tracks | Modules | Rationale |
|-------|--------|---------|-----------|
| **Phase 1** | IT, MED | 35 + 35 = 70 | Highest demand (tech + humanitarian). Validates templates |
| **Phase 2** | STEM, MIL | 25 + 30 = 55 | STEM = science foundation. MIL = wartime urgency |
| **Phase 3** | BUS, LAW | 35 + 25 = 60 | Professional demand, good sources |
| **Phase 4** | ACAD, MEDIA, AGR | 25 + 25 + 20 = 70 | Lower urgency but important niches |

**Total new modules**: 255 (across 9 domain tracks)

---

## Track Dependencies

```
B2 Core (prerequisite for all domain tracks)
  │
  ├── IT ←── STEM (recommended, not required)
  │
  ├── MED (teaches its own biology/chemistry inline — no STEM dependency)
  │
  ├── STEM (no prereqs beyond B2)
  │
  ├── MIL (no prereqs beyond B2; cross-refs MED for tactical medicine)
  │
  ├── BUS (no prereqs beyond B2)
  │
  ├── LAW (no prereqs beyond B2)
  │
  ├── ACAD (no prereqs beyond B2; cross-refs STEM for research methodology)
  │
  ├── MEDIA (no prereqs beyond B2)
  │
  └── AGR (teaches its own ecology inline — no STEM dependency)
```

---

## Template Architecture (shared across all domain tracks)

### Content structure (per module — target 2500w minimum, template ~2800w for buffer):

**Header hierarchy**: `# Title` (H1), content sections as `##` (H2), subsections as `###` (H3). Must include `# Підсумок` (H1) at the end to pass `audit_module.py` structural checks.

```
# {Module Title}

## Вступ (Introduction) — 200w
   - Context: why this terminology matters
   - Learning objectives (3-5)

2. Ключові терміни (Key Terms) — 600w
   - Term table: Ukrainian | Definition | Example sentence
   - Formal vs jargon pairs where applicable
   - VESUM-verified, GRAC frequency noted

3. Тематичний контекст (Thematic Context) — 1000w
   - Domain explanation using the vocabulary
   - Real-world scenarios
   - [!definition], [!jargon], [!formula] callouts

4. Практичне застосування (Practical Application) — 600w
   - Dialogue / scenario using terms in context
   - Document reading exercise (code, medical form, legal clause, etc.)

5. Мовні особливості (Language Notes) — 400w
   - Grammar patterns specific to domain register
   - Common calques to avoid (Russian/English interference)
   - Formal register markers

## Підсумок — 0w (structural requirement)

Total: ~2800 words (minimum audit gate: 2500)
```

### New callout types:
- `[!definition]` — Formal standard definition (ДСТУ or domain standard)
- `[!jargon]` — Real-world workplace usage vs formal term
- `[!formula]` — Mathematical/chemical formula with Ukrainian reading
- `[!code]` — Code snippet with Ukrainian comments
- `[!standard]` — Reference to specific ДСТУ, МОЗ protocol, or legal article

### Research template differences from seminars:
- No `search_literary` (no literary RAG for domain tracks)
- `query_wikipedia` as primary source (Ukrainian Wikipedia has good domain coverage)
- `verify_words` mandatory for ALL domain terms (catch Russian calques)
- `query_grac` for competing term frequency (which synonym is actually used?)
- No decolonization angle (replaced by anti-calque/Russicism detection)
- No primary quotes requirement (replaced by ДСТУ/standard references)
- No chronological timeline (replaced by term etymology where relevant)

### Activity types (new for domain tracks):
- **Term-to-definition matching** — drag & drop Ukrainian terms to definitions
- **Formal↔Jargon matching** — match standard Ukrainian terms to their workplace equivalents
- **Process ordering** — sequence steps of a procedure (surgical prep, SDLC, court process)
- **Categorization** — sort terms into groups (frontend/backend, civil/criminal)
- **Scenario MCQ** — workplace situation vocabulary in context
- **Document reading** — comprehension exercises with authentic document types (code, prescriptions, contracts, news articles)
- **Fill-in dialogue** — complete a professional conversation (patient history, standup, court hearing). All open-ended production activities must include `[!model-answer]` callout per B2+ quality gates

---

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| No STEM RAG — Gemini may hallucinate terminology | Aggressive VESUM verification in validate phase; research template forces `verify_words` on all terms |
| Russian calques in scientific/professional Ukrainian | `query_r2u` tool flags Russian→Ukrainian pairs; content template has explicit anti-calque section |
| Jargon changes fast (especially IT) | Research phase checks domain-specific sites for current usage; modules dated with "terminology as of YYYY" |
| LLM generates bad quiz distractors for science | Activity template requires distractors to be real terms from the same domain, not invented words |
| 2500 words may be too short for complex topics | Allow up to 3000 for foundational modules; keep 2500 for intermediate+ |
| 90 PRO modules need reworking during absorption | Absorbed modules are reference material for plan writing, not direct copy. Plans are written fresh in domain context |
| Wikipedia coverage uneven across domains | Research template has gap-detection: if Wikipedia article is < 2000 chars, flag for manual research |

---

## Infrastructure Work Required (Epic scope)

### Phase 0: Architecture & Design
- 0.1: Design domain content template (`content-domain.md`)
- 0.2: Design domain research template (`research-domain.md`)
- 0.3: Design domain activity types (YAML schema + validation)
- 0.4: Define word targets, plan YAML schema for domain tracks
- 0.5: Gemini adversarial review of all Phase 0 designs

### Phase 1: Infrastructure (shared code)
- 1.1: Implement `research-domain.md` prompt template
- 1.2: Implement `content-domain.md` prompt template
- 1.3: Implement `_score_domain()` research rubric in `research_quality.py`
- 1.4: Add domain activity types to YAML schema + validation
- 1.5: Add new callout types to MDX renderer + patch `audit/config.py` to register them as valid engagement callouts (prevents richness audit failures)
- 1.6: Patch `audit/config.py` LEVEL_CONFIG to set `target_words: 2500` for all 9 domain tracks (prevents default B2 core target from triggering validation failures)
- 1.7: Add domain sources to known-good domains (dou.ua, umj.com.ua, etc.)
- 1.8: Register all 9 tracks in pipeline config
- 1.9: Design plan YAML format for domain tracks (term tables, jargon pairs)

### Phase 2: Curriculum & Plans (per track, as build phases proceed)
- Per-track: design curriculum → write plans → Gemini review → finalize
- First: IT + MED (Phase 1 build tracks)

### Phase 3: Validation
- Build 2 pilot modules per track end-to-end
- Review, fix template/rubric issues
- Retrospective before batch build
