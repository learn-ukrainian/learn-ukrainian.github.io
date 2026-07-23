# Hramatka App Product & Engineering Roadmap

> **Document Status**: MASTER PRODUCT & ENGINEERING ROADMAP  
> **Author & Architectural Design**: Sol (`gpt-5.6-sol`), Lead Architect  
> **Target Epic**: Epic #4542 (`hramatka` stream)  
> **Target Repositories**:
> - Public: `docs/plans/HRAMATKA_APP_PRODUCT_ROADMAP.md`
> - Private: `/Users/krisztiankoos/projects/learn-ukrainian-infra-private/docs/plans/HRAMATKA_APP_PRODUCT_ROADMAP.md`

---

## 1. Executive Product Vision & Architectural Rules

The **Hramatka App** is the user-facing Ukrainian teacher & learner application powering automated, State Standard 2024-aligned lesson generation, interactive drills, and linguistic feedback.

### **Core Architectural Principles**:
- **Repository Isolation**:
  - **Public Repo**: Versioned `@learn-ukrainian/activity-kit`, JSON Schemas, golden valid/invalid activity fixtures.
  - **Private Repo**: FastAPI backend, Uvicorn process, SQLite/WAL database, teacher/student UI, secrets, TTS audio, telemetry.
- **Tech Stack**: React + TypeScript (Vite app) for UI; FastAPI + Pydantic + SQLite/WAL for service backend.
- **Generator Engine**: **Gemini 3.6 Flash** primary seat (**10.0 / 10 PASS**, 12s latency) + QG linter (`scripts/audit/hramatka_qg_rules.py`).
- **Signature Wire Type Mapping**:
  - `cloze_passage` $\rightarrow$ `cloze`
  - `mark_the_words` $\rightarrow$ `mark-the-words`
  - `matching_pairs` $\rightarrow$ `match-up`
  - `multiple_choice` $\rightarrow$ `multiple-choice`
  - `sentence_transformation` $\rightarrow$ `sentence-transformation`
  - `error_correction` $\rightarrow$ `error-correction`
  - `audio_listen_repeat` $\rightarrow$ `audio-listen-repeat`
  - `model_answer_discussion` $\rightarrow$ `model-answer-discussion`

---

## 2. Epics & Executable Ticket Breakdown

```
EPIC #4542: HRAMATKA TEACHER & LEARNER APPLICATION SUITE
 ├── TICKET #4542-P1.1: Schema Freeze & lesson-support.v1 Sidecar
 ├── TICKET #4542-P1.2: FastAPI Lesson Engine Endpoints & Readiness Probes
 ├── TICKET #4542-P1.3: Content-Addressed Generation Cache
 ├── TICKET #4542-P1.4: Gemini 3.6 Flash Qualified Routing & Failover
 ├── TICKET #4542-P2.1: App Shell & Teacher Dashboard State Machine
 ├── TICKET #4542-P2.2: Lesson Viewer & Student Mode (Zero Answer Leakage)
 ├── TICKET #4542-P2.3: Vocabulary Drawer & Theory Callout Component
 ├── TICKET #4542-P3.1: Cloze & Mark-the-Words Interactive Renderers
 ├── TICKET #4542-P3.2: Matching & Multiple Choice Interactive Renderers
 ├── TICKET #4542-P3.3: Sentence Transformation & Error Correction Renderers
 ├── TICKET #4542-P3.4: Audio Repeat & Model Answer Discussion Renderers
 ├── TICKET #4542-P4.1: SHA-256 Text-Anchored Audio Asset Pipelines
 ├── TICKET #4542-P4.2: Generation Call Telemetry & Cost Accounting
 └── TICKET #4542-P4.3: Offline PWA Export & Bundle Packaging
```

---

## Phase 1: Lesson Engine API & Local Service Layer

### **Ticket #4542-P1.1: Schema Freeze & `lesson-support.v1` Sidecar**
- **Goal**: Extend `@learn-ukrainian/activity-kit` schemas with `audio-listen-repeat`, `model-answer-discussion`, `sentence-transformation`, and create `lesson-support.v1`.
- **Deliverables**:
  - `lesson-support.v1` sidecar containing `vocabulary[]` (lemma, stress, POS, gloss, VESUM analysis), `theory[]` (ID, body, callouts), `assets[]` (audio SHAs).
  - Derive Python and TypeScript registries from single JSON Schema enum.
- **Acceptance Criteria**:
  - Golden fixtures pass public schema, private API validation, and player rendering.
  - Contract-drift CI fails if schema, fixtures, Python, or TypeScript registries disagree.

### **Ticket #4542-P1.2: FastAPI Endpoints & Readiness Probes**
- **Goal**: Complete FastAPI lesson service routes with SQLite/WAL persistence.
- **Deliverables**:
  - `GET /api/lessons/{id}/support`, `POST /api/linguistics/verify` (batched VESUM attestations up to 200 forms).
  - Lifecycle state machine: `draft/queued` $\rightarrow$ `baking` $\rightarrow$ `ready | failed`.
  - `/readyz` probe verifying writable DB, migrations, baker state, schemas, and VESUM manifest.
- **Acceptance Criteria**:
  - Owner scoping, CSRF, idempotent UUID creation, and restart recovery pass.
  - No partial lesson is ever returned to client.

### **Ticket #4542-P1.3: Content-Addressed Generation Cache**
- **Goal**: Implement deterministic 14-day generation caching to prevent duplicate provider API calls.
- **Cache Key Formula**: `hash(owner_id + anchor_hash + normalized_request + prompt_sha + schema_sha + data_manifest_sha + model_id + policy_version)`.
- **Acceptance Criteria**:
  - Identical lesson retry performs 0 provider calls.
  - Prompt/schema/data changes force a clean miss and regeneration.

### **Ticket #4542-P1.4: Gemini 3.6 Flash Qualified Routing & Bounded Failover**
- **Goal**: Wire Gemini 3.6 Flash primary generator route with bounded fallback logic.
- **Retry Budget**: Primary qualified route (1x) $\rightarrow$ Secondary fallback route (1x on network/5xx timeout) $\rightarrow$ Maximum 4 provider calls total per unit.
- **Acceptance Criteria**:
  - 10/10 Quality Gate suite remains 100% intact.
  - Latency regression $\le 20\%$ against 12-second baseline.

---

## Phase 2: Teacher & Student Application UI

### **Ticket #4542-P2.1: App Shell & Teacher Dashboard**
- **Goal**: Build Vite/React dashboard managing lesson drafts, baking status, and catalog.
- **Acceptance Criteria**:
  - Page refresh or direct link never renders blank page.
  - Mobile and keyboard-only Playwright E2E tests pass.

### **Ticket #4542-P2.2: Lesson Viewer & Student Mode Isolation**
- **Goal**: Build multi-mode Lesson Viewer (Teacher Review, Conduct, Print, Student Run).
- **Acceptance Criteria**:
  - **Zero Answer Leakage**: Student DOM contains NO answer keys, model answers, teacher notes, or hidden CSS answer hints.
  - Snapshot tests verify student clipboard/print exports carry no answers.

### **Ticket #4542-P2.3: Vocabulary Drawer & Theory Callouts**
- **Goal**: Build interactive Vocabulary Drawer populated exclusively from `lesson-support.v1`.
- **Acceptance Criteria**:
  - Search by surface/lemma with stress marks, POS, and VESUM attestation.
  - No frontend guessing of lemmas, stress, or case.
  - Drawer works 100% offline once lesson is loaded.

---

## Phase 3: Eight Signature Interactive Activity Renderers

### **Ticket #4542-P3.1: Cloze & Mark-the-Words Renderers**
- **`ClozePassageRenderer`**: Gap inputs, Unicode/apostrophe normalization, gap-level feedback.
- **`MarkTheWordsRenderer`**: Token/span selection with precision/recall scoring and stable token IDs.

### **Ticket #4542-P3.2: Matching & Multiple Choice Renderers**
- **`MatchingPairsRenderer`**: Independent shuffling, scored by stable pair IDs.
- **`MultipleChoiceRenderer`**: Single/multiple selection as declared by schema.

### **Ticket #4542-P3.3: Sentence Transformation & Error Correction Renderers**
- **`SentenceTransformationRenderer`**: Compare against preverified accepted-answer set with structural diff display.
- **`ErrorCorrectionRenderer`**: Select error span, provide correction, score by error ID.

### **Ticket #4542-P3.4: Audio Repeat & Model Answer Discussion Renderers**
- **`AudioListenRepeatRenderer`**: Play/pause, speed control, segment replay, self-record/replay.
- **`ModelAnswerDiscussionRenderer`**: Open response text box, rubric checklist, delayed model answer reveal (`score: null`).

---

## Phase 4: Audio, Telemetry, Offline PWA & Production Delivery

### **Ticket #4542-P4.1: SHA-256 Text-Anchored Audio Asset Pipelines**
- **Goal**: Generate immutable audio assets anchored by SHA-256 hash of accepted transcript text.
- **Acceptance Criteria**:
  - Mismatched transcript hash blocks audio playback.
  - Missing audio gracefully degrades to visible text mode.

### **Ticket #4542-P4.2: Generation Telemetry & Cost Accounting**
- **Goal**: Add private `generation_calls` telemetry store tracking tokens, cost, latency, and fallback rates.
- **Acceptance Criteria**:
  - No prompts, responses, anchors, or learner PII ever logged.
  - Token totals reconcile with provider receipts.

### **Ticket #4542-P4.3: Offline PWA Export & Bundle Packaging**
- **Goal**: Create standalone offline PWA export bundles (`.zip`) containing app runtime, lesson JSON, support sidecar, and audio.
- **Acceptance Criteria**:
  - Installed PWA launches and completes all 8 activity types with network disabled.
  - Teacher and student bundles generated independently (student bundle contains 0 teacher keys).

---

*Hramatka App Product & Engineering Roadmap designed by Sol (`gpt-5.6-sol`), Lead Architect (July 24, 2026).*
