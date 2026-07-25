# ADR-015: Google Drive AppData Sync & Custom Decks Architecture

**Date**: 2026-07-24  
**Status**: APPROVED (Unanimous Sol `gpt-5.6-sol` & Fable `claude-fable-5` Verdict)  
**Track**: Practice Hub / Lexicon Frontend Infrastructure  

---

## 1. Context & Motivation

Learners require:
1. **Teacher Lesson Collection (610+440 Words)**: A built-in, dedicated practice set for private teacher-lesson intake words without duplicating database state.
2. **Custom Special Decks**: The ability to build, name, edit, and practice custom vocabulary sets.
3. **Cross-Device Progress Sync**: A zero-backend method to synchronize SRS review history and custom sets across personal devices without requiring centralized user accounts, servers, or commercial cloud databases.

---

## 2. Decided Architecture

### A. Decoupled Built-In Virtual Special Deck
- The **Teacher Lesson Collection (1,050 words)** is rendered as a **virtual, read-only deck (`virtual_teacher_lesson`)**.
- Derived dynamically from `site/src/data/lexicon-manifest.json` entries where `sources` includes `"teacher_lesson"`.
- Adds **0 KB** of user storage and updates automatically whenever new promotion passes merge into the Word Atlas.

### B. Local-First IndexedDB Core
- IndexedDB database (`learn_ukrainian_db`) serves as the primary local source of truth.
- App remains **100% functional offline** without Google login.

```typescript
export interface CustomSet {
  id: string;             // UUID v4
  title: string;
  description?: string;
  lemma_keys: string[];   // References to Lexicon manifest lemmas
  created_at: string;     // ISO timestamp
  updated_at: string;     // ISO timestamp
  deleted_at?: string;    // Deletion tombstone for 3-way sync
  device_id: string;
  revision: number;
}
```

### C. Zero-Backend Google Drive AppData Sync
- **Scope**: `https://www.googleapis.com/auth/drive.appdata` (Restricted app-isolated hidden directory).
- **Security Assessment**: Non-sensitive / basic OAuth verification. No backend proxy or server required.
- **Privacy**: The app cannot read, view, or modify any user personal files or documents outside its hidden app directory.
- **Engine**: Zero bundled libraries (0 KB impact). Lazy-loads Google Identity Services (`gsi/client`) and executes direct browser `fetch()` calls against Google Drive API v3 REST endpoints (`https://www.googleapis.com/drive/v3/files?spaces=appDataFolder`).
- **Token Hygiene**: Access tokens are kept strictly in volatile JS memory.
- **Account Isolation**: Local IndexedDB database is bound to the Google account `sub` claim.

### D. Monotonic Progress & 3-Way Tombstone Sync
- **Progress Sync**: SRS review history is synchronized as an append-only event log (`event_id`, `lemma_key`, `timestamp`, `grade`), from which SRS interval/ease states are derived deterministically.
- **Custom Sets Sync**: Three-way merge with `deleted_at` tombstones to prevent deck resurrection and handle multi-device creation seamlessly.

---

## 3. Approval Ledger

- **Sol (`gpt-5.6-sol`)**: Approved (Conditional GO satisfied with 3-way tombstones, event-log SRS sync, and virtual special set).
- **Fable (`claude-fable-5`)**: Approved (GO with GIS token memory hygiene and zero-dependency fetch engine).
