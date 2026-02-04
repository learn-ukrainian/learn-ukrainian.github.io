# ISSUE-502: OES/RUTH Activity Types Specification
# Version: 1.1.0 (2026-02-04)
# Description: Specification for historical linguistics activity types to support OES and RUTH tracks.

---

## 1. Refined Existing Types

### transcription
- **id**: transcription
- **name**: Historical Transcription
- **name_uk**: Історична транскрипція
- **description**: Practice reading and transcribing OES/RUTH manuscripts into modern Cyrillic or modern standard Ukrainian.
- **tracks**: [oes, ruth]
- **schema**:
  - **required**: [type, title, original, answer]
  - **optional**: [instruction, hints, image_url]
- **ui_guidance**: Display the original text (possibly an image). Support specialized characters (ѣ, ѫ, ѧ) via a virtual keyboard or character picker.
- **example**:
    type: transcription
    title: Транскрипція берестяної грамоти
    original: "СЕ АЗЪ ПОСЛАЛЪ КЪ ТОБѢ"
    answer: "Це я послав до тебе"
    hints: ["АЗЪ = я", "КЪ ТОБѢ = до тебе"]

### etymology-trace
- **id**: etymology-trace
- **name**: Etymology Trace
- **name_uk**: Етимологічний родовід
- **description**: Tracing a word's evolution from its root to modern Ukrainian, including sound changes and semantic shifts.
- **tracks**: [oes, ruth]
- **schema**:
  - **required**: [type, title, items]
  - **item_fields**: [word, modern, evolution, source_language (optional), origin (optional)]
- **ui_guidance**: Vertical timeline or flowchart view showing shifts.
- **example**:
    type: etymology-trace
    title: Від OES до сучасності
    items:
      - word: "градъ"
        modern: "місто / город"
        evolution: "Повноголосся (TorT -> ToroT) та семантичний зсув від 'огорожа' до 'поселення'."
        source_language: "Common Slavic"

### grammar-identify
- **id**: grammar-identify
- **name**: Grammar Identification
- **name_uk**: Граматичне визначення
- **description**: Identifying specific archaic grammatical forms (Dual, Aorist, etc.) in a text.
- **tracks**: [oes, ruth]
- **schema**:
  - **required**: [type, title, items]
  - **item_fields**: [text, form, answer]
- **ui_guidance**: Highlight the target text in a passage and ask for its morphological category.
- **example**:
    type: grammar-identify
    title: Визначення дієслівних форм
    items:
      - text: "придоша"
        form: "Час і особа"
        answer: "Аорист, 3-я особа множини"

---

## 2. New Historical Types

### phonology-lab
- **id**: phonology-lab
- **name**: Phonology Lab
- **name_uk**: Фонологічна лабораторія
- **description**: Step-by-step reconstruction of sound changes (e.g., fall of yers, palatalization).
- **tracks**: [oes, ruth]
- **schema**:
  - **required**: [type, title, input, law, output]
  - **optional**: [steps, explanation]
- **ui_guidance**: Interactive "lab" where learners apply a linguistic law to see the transformation.
- **example**:
    type: phonology-lab
    title: Падіння редукованих
    input: "сънъ"
    law: "Закон Гавліка"
    output: "сон"
    steps:
      - "Кінцевий ъ (слабкий) зникає."
      - "Кореневий ъ (сильний) переходить в [о]."

### grammar-lab
- **id**: grammar-lab
- **name**: Grammar Lab
- **name_uk**: Граматична лабораторія
- **description**: Structured morphological analysis of archaic forms (root, prefix, suffix, ending).
- **tracks**: [oes, ruth]
- **schema**:
  - **required**: [type, title, focus, items]
  - **item_fields**: [form, analysis, modern_equivalent, explanation]
- **ui_guidance**: Tabular/breakdown view of morphology.
- **example**:
    type: grammar-lab
    title: Аналіз двоїни
    focus: "Іменна двоїна"
    items:
      - form: "двѣ руцѣ"
        analysis:
          root: "рук-"
          change: "k -> c (II палаталізація)"
          ending: "-ѣ"
        modern_equivalent: "дві руки"

### parallel-text
- **id**: parallel-text
- **name**: Parallel Text Analysis
- **name_uk**: Паралельний аналіз текстів
- **description**: Comparison of a passage across multiple versions/stages of the language.
- **tracks**: [oes, ruth]
- **schema**:
  - **required**: [type, title, versions]
  - **version_fields**: [label, text]
  - **optional**: [comparison_points]
- **ui_guidance**: Side-by-side columnar view with synced scrolling.
- **example**:
    type: parallel-text
    title: "Еволюція займенників"
    versions:
      - label: "OES (XI ст.)"
        text: "иже еси"
      - label: "Modern"
        text: "що єси"
    comparison_points: ["иже -> що (відносний займенник)"]

### paleography-analysis (Extended)
- **id**: paleography-analysis
- **name**: Paleography Analysis
- **name_uk**: Палеографічний аналіз
- **description**: Identifying visual and orthographic features of manuscripts.
- **tracks**: [oes, ruth]
- **schema**:
  - **required**: [type, title, image_url, hotspots]
  - **hotspot_fields**: [x, y, label, explanation]
- **ui_guidance**: Zoomable image with hotspot markers. Supports "Character Grid" mode for identifying obsolete letters.
- **example**:
    type: paleography-analysis
    image_url: "assets/manuscripts/ostromir.jpg"
    hotspots:
      - x: 10
        y: 20
        label: "Титло"
        explanation: "Знак скорочення над священними іменами."

### historical-writing
- **id**: historical-writing
- **name**: Historical Stylization
- **name_uk**: Історична стилізація
- **description**: Composition task requiring period-appropriate style, vocabulary, and grammar.
- **tracks**: [oes, ruth]
- **schema**:
  - **required**: [type, title, prompt, constraints, model_answer]
  - **optional**: [rubric]
- **ui_guidance**: Text editor with "orthography check" and detailed rubric feedback.
- **example**:
    type: historical-writing
    title: "Лист у канцелярію"
    prompt: "Напишіть звернення до воєводи про земельну суперечку (Статут 1588)."
    constraints: ["Використовуйте 'челомъ бью'", "Використовуйте термін 'застенок'"]
    model_answer: "Воєводі ясновельможному... челомъ бью..."

### register-identify
- **id**: register-identify
- **name**: Register Identification
- **name_uk**: Визначення регістру
- **description**: Analyzing diglossia by identifying the register/style of a text excerpt (Vernacular, Chancery, Sacred, Macaronic).
- **tracks**: [oes, ruth]
- **schema**:
  - **required**: [type, title, items]
  - **item_fields**: [text, options, answer, explanation]
- **ui_guidance**: Sorting or classification interface with focus on linguistic markers.
- **example**:
    type: register-identify
    items:
      - text: "И по сей грамотѣ воевода..."
        options: ["Chancery Ruthenian", "Sacred Church Slavonic", "Vernacular Ukrainian"]
        answer: "Chancery Ruthenian"

### loanword-trace
- **id**: loanword-trace
- **name**: Loanword Trace
- **name_uk**: Слід запозичення
- **description**: Identifying and tracing foreign influences (Greek, Turkic, Polish, Latin) in OES/RUTH.
- **tracks**: [oes, ruth]
- **schema**:
  - **required**: [type, title, items]
  - **item_fields**: [word, source_language, meaning, modern_reflex (optional)]
- **ui_guidance**: Map-based or etymological path showing the journey of the word.
- **example**:
    type: loanword-trace
    title: Польські запозичення в RUTH
    items:
      - word: "уряд"
        source_language: "Polish (urząd)"
        meaning: "Office / Government"

### comparative-style
- **id**: comparative-style
- **name**: Comparative Stylistics
- **name_uk**: Порівняльна стилістика
- **description**: Comparing linguistic features (syntax, vocabulary, phonology) across different registers or historical periods.
- **tracks**: [oes, ruth]
- **schema**:
  - **required**: [type, title, items_to_compare, criteria, model_answer]
  - **optional**: [instruction, source_reading]
- **ui_guidance**: Side-by-side analysis with highlighting of specific stylistic markers.
- **example**:
    type: comparative-style
    title: "Канцелярський vs Сакральний стиль"
    items_to_compare: ["Литовський Статут", "Пересопницьке Євангеліє"]
    criteria: ["Синтаксис (довжина речень)", "Вживання полонізмів", "Дієслівні закінчення"]
    model_answer: "Канцелярський стиль характеризується довшими реченнями..."

---

## 3. Answers to Key Questions

### Q1: Grammar Lab Subtypes?
**Decision:** One generic `grammar-lab` type with a `focus` property.
**Rationale:** Avoids schema bloat while allowing UI to dynamically label the task (e.g., "Aorist Lab", "Dual Lab") based on the `focus` field.

### Q2: Evaluation for Historical Writing?
**Decision:** Rubric-based evaluation + Model Answer.
**Criteria:**
1. **Orthography (25%)**: Use of period-appropriate characters (ѣ, ь/ъ, etc.).
2. **Morphology (25%)**: Consistency of archaic endings and conjugations.
3. **Vocabulary (25%)**: Absence of modernisms/anachronisms.
4. **Style (25%)**: Adherence to genre conventions (Chancery, Hagiography, etc.).

### Q3: UI for Paleography?
**Decision:**
- **Hotspots**: For identifying layout and decorative features.
- **Character Picker**: Integrated virtual keyboard for obsolete letters.
- **Overlay hints**: Semi-transparent modern transcription overlay for difficult sections.