# Context-Aware Ukrainian Error-Correction Practice Pipeline

> **Scope**: Pedagogical architecture and ingestion framework for harvesting intentional grammar errors from textbooks, UA-GEC, and Antonenko-Davydovych, while preventing false-positive ingestion into positive cloze practice.

## 1. Background & The Naive Extraction Trap

Ukrainian school language textbooks (notably Grades 5–11 by Oleksandr Avramenko, Oleksandr Zabolotnyi, Oksana Hlazova, and Mykola Pohribnyi) contain extensive pedagogical material featuring **deliberately incorrect sentences**:

- **Editing drills (*«Відредагуйте речення»*)**:
  - *«Більша половина учнів прийняла участь у святі.»* (Contains deliberate Russianism *«прийняла участь»* for *«взяла участь»*).
- **Contrastive usage tables (*«Культура мовлення: НЕПРАВИЛЬНО / ПРАВИЛЬНО»*)**:
  - ❌ *на протязі року* → ✅ *протягом року*
  - ❌ *завідуючий кафедрою* → ✅ *завідувач кафедри*
  - ❌ *я вибачаюсь* → ✅ *перепрошую / вибачте*
  - ❌ *самий кращий* → ✅ *найкращий*
- **Spelling and morphology tests (*«Вставте пропущені літери / розкрийте дужки»*)**:
  - Words with missing letters or intentional splits (*«(пів)яблука»*, *«не/покоїтися»*, *«пр..красний»*).

A naive corpus search (e.g. searching for *«прийняти»* or *«на протязі»*) treats the raw text as authoritative Ukrainian, accidentally ingesting the exact error the textbook was warning against.

---

## 2. The Dual-Track Corpus Architecture

To address this, the pipeline bifurcates sentence harvesting into two strictly isolated tracks:

```
                               ┌──────────────────────────────────────────────┐
                               │       Raw Sources Database (sources.db)      │
                               │  - Textbooks (52k chunks)                    │
                               │  - Literary Classics (137k chunks)           │
                               │  - SUM-11 Citations (127k entries)           │
                               │  - UA-GEC Errors (8.9k pairs)                │
                               │  - Style Guide (Antonenko-Davydovych, 342)   │
                               └──────────────────────┬───────────────────────┘
                                                      │
                                   [Context & Heading Classifier]
                                                      │
                         ┌────────────────────────────┴────────────────────────────┐
                         ▼                                                         ▼
            [Negative Error Context]                                  [Positive Context]
  («Виправте», «НЕПРАВИЛЬНО», «Відредагуйте»)                   (Literature, Expository Chapters, SUM-11)
                         │                                                         │
                         ▼                                                         ▼
       ┌────────────────────────────────────┐                    ┌───────────────────────────────────┐
       │   Error-Correction Practice Track  │                    │     Standard Cloze & Reading      │
       │   - Identify incorrect token       │                    │   - Guaranteed authentic prose    │
       │   - Multi-choice correction        │                    │   - Natural syntax & morphology   │
       │   - Pedagogical explanation        │                    │   - VESUM-verified inflections    │
       └────────────────────────────────────┘                    └───────────────────────────────────┘
```

### Track A: Positive Corpus (Cloze, Flashcards, Match-Up)
- **Sources**:
  - `literary_texts`: Authentic Ukrainian classics (Іван Франко, Леся Українка, Михайло Коцюбинський, Іван Багряний, Микола Хвильовий, Валер'ян Підмогильний).
  - Expository textbook chapters: History, geography, biology, and literary biography sections.
  - `sum11`: Verified academic dictionary citations.
- **Firewall**: Blocks any chunk matching negative error patterns (`виправте`, `помилк`, `відредагуйте`, `НЕПРАВИЛЬНО`, `Антисуржик`).

### Track B: Error-Correction Track (*«Знайдіть помилку»*)
- **Sources**:
  - Contrastive tables and exercise pairs from `textbooks`.
  - `ua_gec_errors` (8,937 annotated sentences with error/correction annotations).
  - `style_guide` (Antonenko-Davydovych *«Як ми говоримо»*).
  - `data/russianism-patterns-ua-gec.csv`.
- **Target Schema**: Maps directly to the frontend `ErrorCorrectionItemProps`:
  ```typescript
  export interface ErrorCorrectionItemProps {
    sentence: string;          // Sentence containing the deliberate error
    errorWord: string;         // The exact incorrect word/token to identify
    correctForm: string;       // The correct Ukrainian replacement
    options: string[];         // Answer options (correctForm + 3 plausible distractors)
    explanation: string;       // Linguistic rule / why it is wrong
    isUkrainian?: boolean;     // UI flag for Ukrainian labels
  }
  ```

---

## 3. Strict Source Boundaries & IP Compliance

1. **Zero Proprietary Exposure**: Anna Ohoiko / Ukrainian Lessons Podcast (ULP) material is completely left alone. No scraping of lesson notes, exercise formats, dialogues, or premium PDFs.
2. **Decolonized Standards**: All error corrections explicitly target contact-calques from Russian (surzhyk), passive agentive constructions, unadapted borrowings, and grammatical case drifts, reinforcing State Standard 2024 Ukrainian norms.
3. **VESUM Integrity**: All target forms and distractors must be validated against `data/vesum.db` (409,000 lemmas, 6.7M inflections).
