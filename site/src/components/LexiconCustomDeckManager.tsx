/**
 * LexiconCustomDeckManager.tsx — Premium Custom Deck Studio & Document Importer Wizard.
 * Implements Sol (gpt-5.6-sol) & Fable (claude-fable-5) UI/UX Design System:
 * - 3-Step Interactive Import Wizard (Upload -> Inspect & Filter -> Save & Cloud Sync)
 * - CEFR Distribution Bar (A1, A2, B1, B2)
 * - Interactive Word Inspector Chips with CEFR Level Badges & Bulk Filters
 * - Glassmorphic visual panel, backdrop blur, smooth micro-interactions
 * - Zero-backend client-side execution & Google Drive AppData Sync
 */

import React, { useState, useCallback, useRef, useMemo } from 'react';
import {
  type CustomSet,
  readLocalCustomSets,
  saveLocalCustomSet,
  deleteLocalCustomSet,
} from '../lib/lexicon/custom-decks';
import { parseDocumentFile, extractDocumentClozeItems, parsePlainTextWithTranslations, type ImportedDeck } from '../lib/lexicon/document-importer';
import {
  buildAtlasAttestationIndex,
  classifyPasteCandidates,
  isSaveEligiblePasteCandidate,
  selectSaveEligiblePasteCandidates,
  summarizePasteCandidates,
  type AtlasAttestationRow,
  type PasteCandidate,
} from '../lib/lexicon/paste-text-vocab';
import { VesumFormShardClient } from '../lib/lexicon/vesum-form-shard';
import type { PracticeClozeItem } from '../lib/lexicon/srs';
import { syncCustomSetsToDrive, requestGoogleAccessToken, setInMemoryAccessToken, getInMemoryAccessToken } from '../lib/lexicon/google-drive-sync';

interface LexiconCustomDeckManagerProps {
  chromeLocale: 'en' | 'uk';
  activeDeckFilter: string;
  onSelectDeckFilter: (filterId: string) => void;
  onClose: () => void;
  shardBaseUrl?: string;
}

type CandidateWord = PasteCandidate;

// Module-level cache: the Atlas attestation index is ~4MB and shared by every
// wizard open in this tab session, so fetch it once per shard base URL.
const attestationIndexPromises = new Map<string, Promise<Map<string, AtlasAttestationRow>>>();

export function loadAttestationIndex(shardBaseUrl: string): Promise<Map<string, AtlasAttestationRow>> {
  const key = shardBaseUrl.trim().replace(/\/+$/, '');
  let promise = attestationIndexPromises.get(key);
  if (!promise) {
    promise = fetch(`${key}/search-index.json`)
      .then((res) => {
        if (!res.ok) throw new Error(`Attestation index fetch failed: ${res.status}`);
        return res.json() as Promise<AtlasAttestationRow[]>;
      })
      .then((rows) => buildAtlasAttestationIndex(rows))
      .catch((err) => {
        attestationIndexPromises.delete(key); // allow retry on next open
        throw err;
      });
    attestationIndexPromises.set(key, promise);
  }
  return promise;
}

// Module-level cache: one VESUM form-shard client per shard base URL, reused
// across wizard opens so already-fetched shards stay cached (#5882 residual).
const vesumShardClients = new Map<string, VesumFormShardClient>();

function loadVesumShardClient(shardBaseUrl: string): VesumFormShardClient {
  const key = shardBaseUrl.trim().replace(/\/+$/, '');
  let client = vesumShardClients.get(key);
  if (!client) {
    client = new VesumFormShardClient(fetch.bind(globalThis), `${key}/vesum-forms/`);
    vesumShardClients.set(key, client);
  }
  return client;
}

export function LexiconCustomDeckManager({
  chromeLocale,
  activeDeckFilter,
  onSelectDeckFilter,
  onClose,
  shardBaseUrl = '/lexicon',
}: LexiconCustomDeckManagerProps) {
  const [customSets, setCustomSets] = useState<CustomSet[]>(() => readLocalCustomSets());
  const [activeTab, setActiveTab] = useState<'decks' | 'wizard'>('decks');

  // Wizard state: 1 = Upload/Paste, 2 = Inspect & Filter, 3 = Save & Sync
  const [wizardStep, setWizardStep] = useState<1 | 2 | 3>(1);
  const [uploadMode, setUploadMode] = useState<'file' | 'paste'>('file');
  const [pastedText, setPastedText] = useState('');

  // Editing set state
  const [editingSetId, setEditingSetId] = useState<string | null>(null);
  const [deckTitle, setDeckTitle] = useState('');
  const [deckDescription, setDeckDescription] = useState('');

  // Candidates extracted from document or paste
  const [candidates, setCandidates] = useState<CandidateWord[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [levelFilter, setLevelFilter] = useState<
    'ALL' | 'A1' | 'A2' | 'B1' | 'B2' | 'C1' | 'C2' | 'VESUM_FORM' | 'UNVERIFIED'
  >('ALL');
  const [isClassifying, setIsClassifying] = useState(false);
  const [attestationError, setAttestationError] = useState<string | null>(null);

  // Drive sync state
  const [isDriveSyncing, setIsDriveSyncing] = useState(false);
  const [syncStatusMsg, setSyncStatusMsg] = useState<string | null>(null);
  const [driveConnected, setDriveConnected] = useState<boolean>(() => Boolean(getInMemoryAccessToken()));

  // Drag-and-drop state
  const [isDragOver, setIsDragOver] = useState(false);
  const [parseError, setParseError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  // Private Curated Deck unlock gate
  const [teacherDeckUnlocked, setTeacherDeckUnlocked] = useState<boolean>(() => {
    if (typeof window === 'undefined') return false;
    return localStorage.getItem('learn_uk_unlock_teacher_deck') === 'true';
  });

  const toggleTeacherDeckUnlock = useCallback(() => {
    const next = !teacherDeckUnlocked;
    setTeacherDeckUnlocked(next);
    if (typeof window !== 'undefined') {
      localStorage.setItem('learn_uk_unlock_teacher_deck', String(next));
    }
  }, [teacherDeckUnlocked]);

  // Handle Google Drive Sync via Google Identity Services (GIS) Popup Auth
  const handleDriveSync = useCallback(async () => {
    setIsDriveSyncing(true);
    setSyncStatusMsg(chromeLocale === 'uk' ? 'Авторизація через Google...' : 'Authenticating with Google...');
    try {
      let token = getInMemoryAccessToken();
      if (!token) {
        token = await requestGoogleAccessToken();
      }
      setSyncStatusMsg(chromeLocale === 'uk' ? 'Синхронізація з Google Drive...' : 'Syncing with Google Drive...');
      const res = await syncCustomSetsToDrive(token);
      setIsDriveSyncing(false);
      if (res.success) {
        setDriveConnected(true);
        setSyncStatusMsg(
          chromeLocale === 'uk'
            ? `Успішно! Синхронізовано колод: ${res.customSetsSynced}`
            : `Success! Synced ${res.customSetsSynced} decks.`
        );
        setCustomSets(readLocalCustomSets());
      } else {
        setSyncStatusMsg(`Error: ${res.message}`);
      }
    } catch (err: any) {
      setIsDriveSyncing(false);
      setSyncStatusMsg(err?.message || 'Google Auth Error');
    }
  }, [chromeLocale]);

  // Extract candidate words, then classify each in three tiers (#5882 residual):
  // a direct hit against the VESUM-verified Atlas index gets a real gloss and
  // optional CEFR guidance; a form VESUM recognizes as an unambiguous inflection
  // of an Atlas-attested lemma folds up to that same tier; everything else that
  // VESUM still recognizes as a real word form is flagged "vesum_form" (deselected,
  // not save-eligible); anything neither index knows is "unverified". Nothing is
  // ever invented — a VESUM shard fetch failure degrades to unverified, never to
  // a guessed attestation.
  const processTextToCandidates = useCallback(async (words: string[], defaultTitle = ''): Promise<void> => {
    const uniqueWords = Array.from(new Set(words.map((w) => w.toLowerCase().trim()).filter((w) => w.length >= 2)));

    setIsClassifying(true);
    setAttestationError(null);
    let index: Map<string, AtlasAttestationRow>;
    try {
      index = await loadAttestationIndex(shardBaseUrl);
    } catch {
      index = new Map();
      setAttestationError(
        chromeLocale === 'uk'
          ? 'Не вдалося перевірити слова за словником Atlas. Усі слова позначені як неперевірені.'
          : 'Could not verify words against the Atlas dictionary. All words are flagged unverified.',
      );
    }
    // VesumFormShardClient.resolve() never throws — a shard fetch failure
    // degrades the affected forms instead, surfaced via cefrCounts.degraded.
    const vesumResults = await loadVesumShardClient(shardBaseUrl).resolve(uniqueWords);
    setIsClassifying(false);

    setCandidates(classifyPasteCandidates(uniqueWords, index, vesumResults));
    if (defaultTitle && !deckTitle) {
      setDeckTitle(defaultTitle);
    }
    setWizardStep(2);
  }, [deckTitle, chromeLocale, shardBaseUrl]);

  const [importedClozeItems, setImportedClozeItems] = useState<PracticeClozeItem[]>([]);

  // Handle File Input or Drop
  const handleFileRead = useCallback(async (file: File) => {
    setParseError(null);
    try {
      const parsed: ImportedDeck = await parseDocumentFile(file);
      if (parsed.cloze_items) {
        setImportedClozeItems(parsed.cloze_items);
      }
      await processTextToCandidates(parsed.lemma_keys, parsed.title);
    } catch (err: any) {
      setParseError(err?.message || 'Failed to read document');
    }
  }, [processTextToCandidates]);

  const handlePasteSubmit = useCallback(async () => {
    if (!pastedText.trim()) return;
    const { lemmaKeys, wordTranslations } = parsePlainTextWithTranslations(pastedText);
    const clozes = extractDocumentClozeItems(pastedText, lemmaKeys, wordTranslations);
    setImportedClozeItems(clozes);
    await processTextToCandidates(lemmaKeys, chromeLocale === 'uk' ? 'Моя імпортована колода' : 'My Imported Deck');
  }, [pastedText, processTextToCandidates, chromeLocale]);

  // Attestation + CEFR distribution counts (real Atlas data, never invented)
  const cefrCounts = useMemo(() => summarizePasteCandidates(candidates), [candidates]);

  // Toggle individual word selection. Selecting (not deselecting) is fail-closed:
  // an attested row with missing CEFR needs a real gloss; known-CEFR rows retain
  // the legacy attested path, and missing CEFR remains guidance metadata (#6073 F001).
  const toggleCandidateSelection = useCallback((index: number) => {
    setCandidates((prev) =>
      prev.map((item, idx) => {
        if (idx !== index) return item;
        const nextSelected = !item.selected;
        if (nextSelected && !isSaveEligiblePasteCandidate(item)) return item;
        return { ...item, selected: nextSelected };
      })
    );
  }, []);

  // Bulk toggle for a specific CEFR level. Unverified and unlevelled candidates
  // have no CEFR group; they are handled by the default selection and final
  // attestation/gloss gate rather than assigned an invented level.
  const toggleGroupSelection = useCallback((group: 'A1' | 'A2' | 'B1' | 'B2' | 'C1' | 'C2', enable: boolean) => {
    setCandidates((prev) =>
      prev.map((item) => (item.cefr === group ? { ...item, selected: enable } : item))
    );
  }, []);

  // Save Deck
  const handleSaveDeck = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      // Fail-closed final gate (#6073 F001): only Atlas-attested candidates are
      // materialized; a missing-CEFR row also needs a real gloss, regardless of
      // how `selected` got set. CEFR remains nullable and no downstream fallback
      // may invent it.
      const selectedWords = selectSaveEligiblePasteCandidates(candidates).map((c) => c.text);
      if (selectedWords.length === 0 || !deckTitle.trim()) return;

      const saved = saveLocalCustomSet({
        id: editingSetId || undefined,
        title: deckTitle.trim(),
        description: deckDescription.trim(),
        lemma_keys: selectedWords,
        cloze_items: importedClozeItems.length > 0 ? importedClozeItems : undefined,
      });

      setCustomSets(readLocalCustomSets());
      onSelectDeckFilter(saved.id);
      onClose();
    },
    [candidates, deckTitle, deckDescription, editingSetId, importedClozeItems, onSelectDeckFilter, onClose]
  );

  const handleDeleteDeck = useCallback((id: string) => {
    if (confirm(chromeLocale === 'uk' ? 'Видалити цю колоду?' : 'Delete this deck?')) {
      deleteLocalCustomSet(id);
      setCustomSets(readLocalCustomSets());
      if (activeDeckFilter === id) {
        onSelectDeckFilter('all');
      }
    }
  }, [activeDeckFilter, chromeLocale, onSelectDeckFilter]);

  // Filtered Candidates for Grid View
  const filteredCandidates = useMemo(() => {
    return candidates.map((item, originalIdx) => ({ ...item, originalIdx })).filter((item) => {
      if (levelFilter === 'UNVERIFIED' && item.status !== 'unverified') return false;
      else if (levelFilter === 'VESUM_FORM' && item.status !== 'vesum_form') return false;
      else if (
        levelFilter !== 'ALL' &&
        levelFilter !== 'UNVERIFIED' &&
        levelFilter !== 'VESUM_FORM' &&
        item.cefr !== levelFilter
      )
        return false;
      if (searchQuery && !item.text.includes(searchQuery.toLowerCase().trim())) return false;
      return true;
    });
  }, [candidates, levelFilter, searchQuery]);

  return (
    <div
      tabIndex={-1}
      role="dialog"
      aria-modal="true"
      aria-labelledby="deck-studio-title"
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(7, 11, 24, 0.88)',
        backdropFilter: 'blur(16px)',
        zIndex: 9999,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '1rem',
      }}
    >
      <div
        className="deck-studio-shell deck-glass-panel"
        style={{
          maxWidth: '740px',
          width: '100%',
          maxHeight: '92vh',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          color: '#f8fafc',
        }}
      >
        {/* Header Ribbon */}
        <div style={{ padding: '1.25rem 1.5rem', borderBottom: '1px solid rgba(255,255,255,0.1)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h2 id="deck-studio-title" style={{ margin: 0, fontSize: '1.35rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span>🎨</span>
              <span>{chromeLocale === 'uk' ? 'Студія власних колод' : 'Custom Deck Studio'}</span>
            </h2>
            <div style={{ fontSize: '0.8rem', color: '#94a3b8', marginTop: '0.2rem' }}>
              {chromeLocale === 'uk' ? 'Створення, імпорт документів та синхронізація з Google Drive' : 'Creation, document import & Google Drive sync'}
            </div>
          </div>
          <button
            type="button"
            className="btn btn-sm"
            onClick={onClose}
            style={{ background: 'transparent', border: 'none', color: '#94a3b8', fontSize: '1.5rem', cursor: 'pointer' }}
          >
            ✕
          </button>
        </div>

        {/* Google Drive Status Bar */}
        <div style={{ background: 'rgba(37, 99, 235, 0.12)', padding: '0.6rem 1.5rem', borderBottom: '1px solid rgba(255,255,255,0.08)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.85rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: driveConnected ? '#22c55e' : '#94a3b8' }} />
            <span>{syncStatusMsg || (driveConnected ? (chromeLocale === 'uk' ? 'Синхронізовано з Google Drive AppData' : 'Synced to Google Drive AppData') : (chromeLocale === 'uk' ? 'Локальне збереження (0 KB backend)' : 'Local storage (Zero backend)'))}</span>
          </div>
          <button
            type="button"
            className="btn btn-sm"
            onClick={handleDriveSync}
            disabled={isDriveSyncing}
            style={{ background: '#2563eb', color: '#fff', padding: '0.25rem 0.65rem', borderRadius: '6px', fontSize: '0.75rem', fontWeight: 600 }}
          >
            {isDriveSyncing ? '...' : driveConnected ? (chromeLocale === 'uk' ? 'Синхронізувати' : 'Sync Now') : (chromeLocale === 'uk' ? 'Увійти в Google' : 'Sign in Google')}
          </button>
        </div>

        {/* Navigation Tabs */}
        <div style={{ padding: '0.75rem 1.5rem 0 1.5rem', display: 'flex', gap: '0.5rem', borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
          <button
            type="button"
            className={`btn btn-sm ${activeTab === 'decks' ? 'btn-accent' : ''}`}
            onClick={() => setActiveTab('decks')}
            style={{ borderRadius: '8px 8px 0 0', padding: '0.5rem 1rem' }}
          >
            📋 {chromeLocale === 'uk' ? 'Мої колоди' : 'My Decks'} ({customSets.length})
          </button>
          <button
            type="button"
            className={`btn btn-sm ${activeTab === 'wizard' ? 'btn-accent' : ''}`}
            onClick={() => {
              setEditingSetId(null);
              setDeckTitle('');
              setDeckDescription('');
              setWizardStep(1);
              setActiveTab('wizard');
            }}
            style={{ borderRadius: '8px 8px 0 0', padding: '0.5rem 1rem' }}
          >
            🪄 {chromeLocale === 'uk' ? 'Майстер імпорту / Створити' : 'Import Wizard / Create'}
          </button>
        </div>

        {/* Content Body */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '1.25rem 1.5rem' }}>
          {/* VIEW 1: MY DECKS LIST */}
          {activeTab === 'decks' ? (
            <div>
              {/* Private Curated Deck unlock toggle */}
              <div style={{ background: 'rgba(245, 158, 11, 0.1)', border: '1px solid rgba(245, 158, 11, 0.3)', borderRadius: '12px', padding: '0.85rem 1rem', marginBottom: '1.25rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div>
                  <div style={{ fontWeight: 600, fontSize: '0.9rem', color: '#fef08a' }}>
                    🔒 {chromeLocale === 'uk' ? 'Приватна відібрана добірка' : 'Private Curated Deck'}
                  </div>
                  <div style={{ fontSize: '0.8rem', color: '#cbd5e1', marginTop: '0.2rem' }}>
                    {chromeLocale === 'uk' ? 'Схована від публічних відвідувачів сайту за замовчуванням' : 'Protected and hidden from general public visitors'}
                  </div>
                </div>
                <button
                  type="button"
                  className={`btn btn-sm ${teacherDeckUnlocked ? 'btn-accent' : ''}`}
                  onClick={toggleTeacherDeckUnlock}
                >
                  {teacherDeckUnlocked ? '🟢 Unlocked' : '🔑 Unlock'}
                </button>
              </div>

              {customSets.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '3rem 1rem', color: '#94a3b8' }}>
                  <div style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>📚</div>
                  <p style={{ margin: '0 0 1rem 0' }}>{chromeLocale === 'uk' ? 'У вас ще немає створених колод.' : 'No custom decks found.'}</p>
                  <button
                    type="button"
                    className="btn btn-accent"
                    onClick={() => {
                      setWizardStep(1);
                      setActiveTab('wizard');
                    }}
                  >
                    🪄 {chromeLocale === 'uk' ? 'Імпортувати перший документ' : 'Import First Document'}
                  </button>
                </div>
              ) : (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '1rem' }}>
                  {customSets.map((set) => (
                    <div
                      key={set.id}
                      style={{
                        background: activeDeckFilter === set.id ? 'rgba(59, 130, 246, 0.25)' : 'rgba(255, 255, 255, 0.04)',
                        border: activeDeckFilter === set.id ? '1px solid #3b82f6' : '1px solid rgba(255, 255, 255, 0.08)',
                        borderRadius: '14px',
                        padding: '1rem',
                        display: 'flex',
                        flexDirection: 'column',
                        justify: 'space-between',
                      }}
                    >
                      <div>
                        <div style={{ fontWeight: 700, fontSize: '1rem', color: '#f8fafc' }}>{set.title}</div>
                        {set.description ? <div style={{ fontSize: '0.8rem', color: '#94a3b8', marginTop: '0.2rem' }}>{set.description}</div> : null}
                        <div style={{ fontSize: '0.8rem', color: '#38bdf8', marginTop: '0.5rem', fontWeight: 600 }}>
                          {set.lemma_keys.length} {chromeLocale === 'uk' ? 'слів' : 'words'}
                        </div>
                      </div>
                      <div style={{ display: 'flex', gap: '0.4rem', marginTop: '1rem' }}>
                        <button
                          type="button"
                          className="btn btn-sm btn-accent"
                          style={{ flex: 1 }}
                          onClick={() => {
                            onSelectDeckFilter(set.id);
                            onClose();
                          }}
                        >
                          ▶️ {chromeLocale === 'uk' ? 'Практика' : 'Practice'}
                        </button>
                        <button type="button" className="btn btn-sm" onClick={() => handleDeleteDeck(set.id)}>
                          🗑️
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : null}

          {/* VIEW 2: 3-STEP IMPORT WIZARD */}
          {activeTab === 'wizard' ? (
            <div>
              {/* Stepper Rail */}
              <div className="deck-wizard-stepper">
                <div className={`deck-wizard-step ${wizardStep >= 1 ? 'active' : ''} ${wizardStep > 1 ? 'completed' : ''}`}>
                  <span className="deck-wizard-step-num">1</span>
                  <span>{chromeLocale === 'uk' ? 'Файл / Текст' : 'Upload / Paste'}</span>
                </div>
                <div className={`deck-wizard-step ${wizardStep >= 2 ? 'active' : ''} ${wizardStep > 2 ? 'completed' : ''}`}>
                  <span className="deck-wizard-step-num">2</span>
                  <span>{chromeLocale === 'uk' ? 'Перегляд слів' : 'Inspect Words'}</span>
                </div>
                <div className={`deck-wizard-step ${wizardStep >= 3 ? 'active' : ''}`}>
                  <span className="deck-wizard-step-num">3</span>
                  <span>{chromeLocale === 'uk' ? 'Збереження' : 'Save & Sync'}</span>
                </div>
              </div>

              {/* STEP 1: UPLOAD / PASTE */}
              {wizardStep === 1 ? (
                <div>
                  <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
                    <button
                      type="button"
                      className={`btn btn-sm ${uploadMode === 'file' ? 'btn-accent' : ''}`}
                      onClick={() => setUploadMode('file')}
                    >
                      📁 {chromeLocale === 'uk' ? 'Файл (.txt, .csv, .json, .md)' : 'File (.txt, .csv, .json, .md)'}
                    </button>
                    <button
                      type="button"
                      className={`btn btn-sm ${uploadMode === 'paste' ? 'btn-accent' : ''}`}
                      onClick={() => setUploadMode('paste')}
                    >
                      📝 {chromeLocale === 'uk' ? 'Вставити текст' : 'Paste Text'}
                    </button>
                  </div>

                  {uploadMode === 'file' ? (
                    <div>
                      <input
                        type="file"
                        ref={fileInputRef}
                        accept=".txt,.csv,.tsv,.json,.yaml,.yml,.md"
                        style={{ display: 'none' }}
                        onChange={(e) => {
                          const file = e.target.files?.[0];
                          if (file) void handleFileRead(file);
                        }}
                      />
                      <div
                        className={`importer-dropzone ${isDragOver ? 'drag-active' : ''}`}
                        onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
                        onDragLeave={() => setIsDragOver(false)}
                        onDrop={(e) => {
                          e.preventDefault();
                          setIsDragOver(false);
                          const file = e.dataTransfer.files?.[0];
                          if (file) void handleFileRead(file);
                        }}
                        onClick={() => fileInputRef.current?.click()}
                      >
                        <div style={{ fontSize: '3rem', marginBottom: '0.5rem' }}>📄</div>
                        <div style={{ fontWeight: 700, fontSize: '1.1rem' }}>
                          {chromeLocale === 'uk' ? 'Перетягніть файл сюди або натисніть для вибору' : 'Drag & drop file here or click to browse'}
                        </div>
                        <div style={{ fontSize: '0.8rem', color: '#94a3b8', marginTop: '0.4rem' }}>
                          Підтримуються TXT, CSV, JSON, Markdown (100% браузерна обробка)
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div>
                      <textarea
                        rows={7}
                        placeholder={chromeLocale === 'uk' ? 'Вставте текст або список слів тут...' : 'Paste Ukrainian text or word list here...'}
                        value={pastedText}
                        onChange={(e) => setPastedText(e.target.value)}
                        style={{ width: '100%', padding: '0.75rem', borderRadius: '12px', background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.15)', color: '#fff' }}
                      />
                      <button
                        type="button"
                        className="btn btn-accent"
                        onClick={() => void handlePasteSubmit()}
                        disabled={isClassifying}
                        style={{ marginTop: '0.75rem', width: '100%' }}
                      >
                        {isClassifying
                          ? (chromeLocale === 'uk' ? '⏳ Перевірка за словником...' : '⏳ Checking dictionary...')
                          : `⚡ ${chromeLocale === 'uk' ? 'Витягнути слова' : 'Extract Words'}`}
                      </button>
                    </div>
                  )}

                  {parseError ? <p style={{ color: '#ef4444', fontSize: '0.85rem', marginTop: '0.5rem' }}>{parseError}</p> : null}
                </div>
              ) : null}

              {/* STEP 2: WORD INSPECTOR & CEFR BREAKDOWN */}
              {wizardStep === 2 ? (
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{ fontWeight: 700, fontSize: '0.95rem' }}>
                      {chromeLocale === 'uk'
                        ? `Знайдено слів: ${cefrCounts.selected} з ${cefrCounts.total}`
                        : `Selected words: ${cefrCounts.selected} of ${cefrCounts.total}`}
                    </div>
                    <div style={{ display: 'flex', gap: '0.3rem' }}>
                      <button
                        type="button"
                        className="btn btn-sm"
                        onClick={() => setCandidates((prev) => prev.map((c) => ({ ...c, selected: isSaveEligiblePasteCandidate(c) })))}
                      >
                        {chromeLocale === 'uk' ? 'Обрати всі' : 'Select All'}
                      </button>
                      <button type="button" className="btn btn-sm" onClick={() => setCandidates((prev) => prev.map((c) => ({ ...c, selected: false })))}>
                        {chromeLocale === 'uk' ? 'Очистити' : 'Clear'}
                      </button>
                    </div>
                  </div>

                  {/* CEFR + Attestation Distribution Bar */}
                  <div className="cefr-distribution-bar">
                    <div className="cefr-seg-a1" style={{ width: `${(cefrCounts.byLevel.A1 / (cefrCounts.selected || 1)) * 100}%` }} title={`A1: ${cefrCounts.byLevel.A1}`} />
                    <div className="cefr-seg-a2" style={{ width: `${(cefrCounts.byLevel.A2 / (cefrCounts.selected || 1)) * 100}%` }} title={`A2: ${cefrCounts.byLevel.A2}`} />
                    <div className="cefr-seg-b1" style={{ width: `${(cefrCounts.byLevel.B1 / (cefrCounts.selected || 1)) * 100}%` }} title={`B1: ${cefrCounts.byLevel.B1}`} />
                    <div className="cefr-seg-b2" style={{ width: `${(cefrCounts.byLevel.B2 / (cefrCounts.selected || 1)) * 100}%` }} title={`B2: ${cefrCounts.byLevel.B2}`} />
                    <div className="cefr-seg-c1" style={{ width: `${(cefrCounts.byLevel.C1 / (cefrCounts.selected || 1)) * 100}%` }} title={`C1: ${cefrCounts.byLevel.C1}`} />
                    <div className="cefr-seg-c2" style={{ width: `${(cefrCounts.byLevel.C2 / (cefrCounts.selected || 1)) * 100}%` }} title={`C2: ${cefrCounts.byLevel.C2}`} />
                  </div>

                  {/* Attestation banner — every candidate is checked against the Atlas
                      dictionary, then (#5882 residual) against VESUM's 6.7M
                      recognized word forms; nothing outside either is treated
                      as confirmed vocabulary. */}
                  <div style={{ display: 'flex', gap: '1rem', fontSize: '0.78rem', color: '#94a3b8', margin: '0.5rem 0 0.75rem', flexWrap: 'wrap' }}>
                    <span>✅ {chromeLocale === 'uk' ? `У словнику: ${cefrCounts.attested}` : `In dictionary: ${cefrCounts.attested}`}</span>
                    <span>🧬 {chromeLocale === 'uk' ? `Форма VESUM: ${cefrCounts.vesumForm}` : `VESUM word form: ${cefrCounts.vesumForm}`}</span>
                    <span>❓ {chromeLocale === 'uk' ? `Неперевірено: ${cefrCounts.unverified}` : `Unverified: ${cefrCounts.unverified}`}</span>
                  </div>
                  {attestationError ? (
                    <p style={{ color: '#fbbf24', fontSize: '0.8rem', marginBottom: '0.5rem' }}>{attestationError}</p>
                  ) : null}
                  {cefrCounts.degraded > 0 ? (
                    <p style={{ color: '#fbbf24', fontSize: '0.78rem', marginBottom: '0.5rem' }}>
                      {chromeLocale === 'uk'
                        ? `Перевірку форм VESUM тимчасово недоступно для ${cefrCounts.degraded} слів(а) — їх позначено неперевіреними, а не вгадано.`
                        : `Form-level VESUM verification was unavailable for ${cefrCounts.degraded} word(s) — they're flagged unverified rather than guessed.`}
                    </p>
                  ) : null}
                  {cefrCounts.vesumForm > 0 ? (
                    <p style={{ color: '#94a3b8', fontSize: '0.78rem', marginBottom: '0.5rem' }}>
                      {chromeLocale === 'uk'
                        ? 'Слова 🧬 — це реальні форми української мови (перевірено VESUM), але ще не в кураторському словнику Atlas; їх не можна зберегти як базові картки.'
                        : "Words marked 🧬 are real Ukrainian word forms (VESUM-verified) but not yet in the curated Atlas dictionary — they can't be saved as basic cards yet."}
                    </p>
                  ) : null}
                  {cefrCounts.unverified > 0 ? (
                    <p style={{ color: '#94a3b8', fontSize: '0.78rem', marginBottom: '0.5rem' }}>
                      {chromeLocale === 'uk'
                        ? 'Неперевірені слова відсутні в нашому словнику Atlas і не обрані за замовчуванням — перегляньте перед додаванням.'
                        : "Unverified words aren't in our Atlas dictionary yet and are deselected by default — review before adding."}
                    </p>
                  ) : null}

                  {/* Level Filters & Search */}
                  <div style={{ display: 'flex', gap: '0.4rem', margin: '0.75rem 0', flexWrap: 'wrap' }}>
                    <input
                      type="text"
                      placeholder={chromeLocale === 'uk' ? 'Пошук слова...' : 'Search word...'}
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      style={{ padding: '0.3rem 0.6rem', borderRadius: '6px', background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.15)', color: '#fff', fontSize: '0.8rem', flex: 1 }}
                    />
                    {(['ALL', 'A1', 'A2', 'B1', 'B2', 'C1', 'C2', 'VESUM_FORM', 'UNVERIFIED'] as const).map((lvl) => (
                      <button
                        key={lvl}
                        type="button"
                        className={`btn btn-sm ${levelFilter === lvl ? 'btn-accent' : ''}`}
                        onClick={() => setLevelFilter(lvl)}
                        style={{ fontSize: '0.75rem' }}
                      >
                        {lvl === 'UNVERIFIED' ? '❓' : lvl === 'VESUM_FORM' ? '🧬' : lvl}
                      </button>
                    ))}
                  </div>

                  {/* Bulk group toggles by CEFR level. Unverified and unlevelled
                      candidates have no group; no level is invented for them. */}
                  <div style={{ display: 'flex', gap: '0.3rem', marginBottom: '0.5rem', flexWrap: 'wrap' }}>
                    {(['A1', 'A2', 'B1', 'B2', 'C1', 'C2'] as const).map((group) => (
                      <React.Fragment key={group}>
                        <button type="button" className="btn btn-sm" style={{ fontSize: '0.7rem' }} onClick={() => toggleGroupSelection(group, true)}>
                          +{group}
                        </button>
                        <button type="button" className="btn btn-sm" style={{ fontSize: '0.7rem' }} onClick={() => toggleGroupSelection(group, false)}>
                          -{group}
                        </button>
                      </React.Fragment>
                    ))}
                  </div>

                  {/* Word Chips Grid */}
                  <div className="word-chip-grid">
                    {filteredCandidates.map((item) => (
                      <div
                        key={item.originalIdx}
                        className={`word-inspector-chip ${item.selected ? 'selected' : 'excluded'} ${item.status === 'vesum_form' ? 'vesum-form-chip' : ''}`}
                        onClick={() => toggleCandidateSelection(item.originalIdx)}
                        title={
                          item.status === 'vesum_form'
                            ? (chromeLocale === 'uk'
                                ? `Форма слова: ${(item.vesumLemmas ?? []).join(', ')} — не в словнику Atlas`
                                : `Word form of: ${(item.vesumLemmas ?? []).join(', ')} — not in the Atlas dictionary`)
                            : item.status === 'unverified'
                              ? (item.degraded
                                  ? (chromeLocale === 'uk'
                                      ? 'Перевірку форм VESUM тимчасово недоступно для цього слова'
                                      : 'Form-level VESUM verification was unavailable for this word')
                                  : (chromeLocale === 'uk' ? 'Немає в словнику Atlas — неперевірено' : 'Not in the Atlas dictionary — unverified'))
                              : (item.gloss ?? undefined)
                        }
                      >
                        <span>{item.selected ? '✓' : '✗'}</span>
                        <span>{item.text}</span>
                        <span
                          className={`word-chip-badge badge-${item.cefr ? item.cefr.toLowerCase() : item.status === 'vesum_form' ? 'vesum-form' : 'unverified'}`}
                        >
                          {item.cefr ?? (item.status === 'vesum_form' ? '🧬' : '❓')}
                        </span>
                      </div>
                    ))}
                  </div>

                  {/* Step 2 Actions */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '1rem' }}>
                    <button type="button" className="btn" onClick={() => setWizardStep(1)}>
                      ← {chromeLocale === 'uk' ? 'Назад' : 'Back'}
                    </button>
                    <button
                      type="button"
                      className="btn btn-accent"
                      disabled={cefrCounts.selected === 0}
                      onClick={() => setWizardStep(3)}
                    >
                      {chromeLocale === 'uk' ? 'Далі →' : 'Next →'}
                    </button>
                  </div>
                </div>
              ) : null}

              {/* STEP 3: SAVE & CLOUD SYNC */}
              {wizardStep === 3 ? (
                <form onSubmit={handleSaveDeck}>
                  <div style={{ marginBottom: '1rem' }}>
                    <label style={{ display: 'block', fontSize: '0.85rem', marginBottom: '0.3rem' }}>
                      {chromeLocale === 'uk' ? 'Назва колоди:' : 'Deck Title:'}
                    </label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. Мої особливі 600 слів"
                      value={deckTitle}
                      onChange={(e) => setDeckTitle(e.target.value)}
                      style={{ width: '100%', padding: '0.6rem', borderRadius: '8px', background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.2)', color: '#fff' }}
                    />
                  </div>
                  <div style={{ marginBottom: '1.25rem' }}>
                    <label style={{ display: 'block', fontSize: '0.85rem', marginBottom: '0.3rem' }}>
                      {chromeLocale === 'uk' ? 'Опис (необов\'язково):' : 'Description (optional):'}
                    </label>
                    <input
                      type="text"
                      placeholder="e.g. Уроки з вчителем"
                      value={deckDescription}
                      onChange={(e) => setDeckDescription(e.target.value)}
                      style={{ width: '100%', padding: '0.6rem', borderRadius: '8px', background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.2)', color: '#fff' }}
                    />
                  </div>

                  <div style={{ background: 'rgba(255,255,255,0.05)', padding: '0.85rem 1rem', borderRadius: '10px', marginBottom: '1.25rem', fontSize: '0.85rem', color: '#cbd5e1' }}>
                    <div>📊 {chromeLocale === 'uk' ? `Вибрано слів до збереження: ${cefrCounts.selected}` : `Words to save: ${cefrCounts.selected}`}</div>
                    <div>☁️ {chromeLocale === 'uk' ? 'Збереження локально + синхронізація в Google Drive AppData' : 'Local save + Google Drive AppData sync'}</div>
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <button type="button" className="btn" onClick={() => setWizardStep(2)}>
                      ← {chromeLocale === 'uk' ? 'Назад' : 'Back'}
                    </button>
                    <button type="submit" className="btn btn-accent">
                      💾 {chromeLocale === 'uk' ? 'Зберегти колоду' : 'Save Deck'}
                    </button>
                  </div>
                </form>
              ) : null}
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}
