import React, { useState, useEffect, useCallback } from 'react';
import type { LuLessonV1 } from '../lu.lesson.v1.generated';
import type { LuLessonSupportV1 } from '../lu.lesson-support.v1.generated';

export type DashboardState = 
  | 'catalog_loading'
  | 'catalog_ready'
  | 'generating'
  | 'baking_poll'
  | 'lesson_active'
  | 'error';

export interface LessonSummary {
  id: string;
  title: string;
  cefr_level: 'a1' | 'a2' | 'b1' | 'b2' | 'c1' | 'c2';
  status: 'draft' | 'baking' | 'ready' | 'failed';
  topic?: string;
  created_at?: string;
  error_message?: string;
}

export interface TeacherDashboardProps {
  apiBaseUrl?: string;
  ownerId?: string;
  onSelectLesson?: (lesson: LuLessonV1, support?: LuLessonSupportV1) => void;
}

export const TeacherDashboard: React.FC<TeacherDashboardProps> = ({
  apiBaseUrl = '/api',
  ownerId = 'default_teacher',
  onSelectLesson,
}) => {
  const [state, setState] = useState<DashboardState>('catalog_loading');
  const [lessons, setLessons] = useState<LessonSummary[]>([]);
  const [selectedLesson, setSelectedLesson] = useState<LuLessonV1 | null>(null);
  const [selectedSupport, setSelectedSupport] = useState<LuLessonSupportV1 | null>(null);
  const [bakingLessonId, setBakingLessonId] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isBackendReady, setIsBackendReady] = useState<boolean | null>(null);

  // Form State
  const [cefrLevel, setCefrLevel] = useState<'a1' | 'a2' | 'b1' | 'b2' | 'c1' | 'c2'>('a2');
  const [topic, setTopic] = useState('');
  const [targetGrammar, setTargetGrammar] = useState('');
  const [targetVocabulary, setTargetVocabulary] = useState('');

  // Check Backend Readiness Probe
  const checkReadiness = useCallback(async () => {
    try {
      const res = await fetch(`${apiBaseUrl}/readyz`);
      setIsBackendReady(res.ok);
    } catch {
      setIsBackendReady(false);
    }
  }, [apiBaseUrl]);

  // Fetch Lessons Catalog
  const fetchCatalog = useCallback(async () => {
    setState('catalog_loading');
    setErrorMessage(null);
    try {
      const res = await fetch(`${apiBaseUrl}/lessons?owner_id=${encodeURIComponent(ownerId)}`);
      if (!res.ok) {
        throw new Error(`Failed to load lessons catalog (HTTP ${res.status})`);
      }
      const data = await res.json();
      setLessons(Array.isArray(data) ? data : data.lessons || []);
      setState('catalog_ready');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to fetch catalog';
      setErrorMessage(msg);
      setState('error');
    }
  }, [apiBaseUrl, ownerId]);

  useEffect(() => {
    checkReadiness();
    fetchCatalog();
  }, [checkReadiness, fetchCatalog]);

  // Poll Baking Status
  useEffect(() => {
    if (state !== 'baking_poll' || !bakingLessonId) return;

    const interval = setInterval(async () => {
      try {
        const res = await fetch(`${apiBaseUrl}/lessons/${encodeURIComponent(bakingLessonId)}`);
        if (!res.ok) return;
        const data: LessonSummary = await res.json();
        
        if (data.status === 'ready') {
          clearInterval(interval);
          setBakingLessonId(null);
          await fetchCatalog();
        } else if (data.status === 'failed') {
          clearInterval(interval);
          setBakingLessonId(null);
          setErrorMessage(data.error_message || 'Lesson baking failed during generation validation.');
          setState('error');
        }
      } catch {
        // Retry silently on transient poll errors
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [state, bakingLessonId, apiBaseUrl, fetchCatalog]);

  // Handle Lesson Generation Request
  const handleGenerateLesson = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!topic.trim()) return;

    setState('generating');
    setErrorMessage(null);

    try {
      const payload = {
        owner_id: ownerId,
        cefr_level: cefrLevel,
        topic: topic.trim(),
        target_grammar: targetGrammar.split(',').map(s => s.trim()).filter(Boolean),
        target_vocabulary: targetVocabulary.split(',').map(s => s.trim()).filter(Boolean),
      };

      const res = await fetch(`${apiBaseUrl}/lessons`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `Generation request failed (HTTP ${res.status})`);
      }

      const lesson: LessonSummary = await res.json();
      if (lesson.status === 'ready') {
        await fetchCatalog();
      } else {
        setBakingLessonId(lesson.id);
        setState('baking_poll');
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to generate lesson';
      setErrorMessage(msg);
      setState('error');
    }
  };

  // Load Active Lesson
  const handleSelectLesson = async (id: string) => {
    setErrorMessage(null);
    try {
      const [lessonRes, supportRes] = await Promise.all([
        fetch(`${apiBaseUrl}/lessons/${encodeURIComponent(id)}`),
        fetch(`${apiBaseUrl}/lessons/${encodeURIComponent(id)}/support`),
      ]);

      if (!lessonRes.ok) throw new Error(`Failed to load lesson (HTTP ${lessonRes.status})`);
      const lessonData: LuLessonV1 = await lessonRes.json();

      let supportData: LuLessonSupportV1 | undefined = undefined;
      if (supportRes.ok) {
        supportData = await supportRes.json();
      }

      setSelectedLesson(lessonData);
      setSelectedSupport(supportData || null);
      setState('lesson_active');

      if (onSelectLesson) {
        onSelectLesson(lessonData, supportData);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load selected lesson';
      setErrorMessage(msg);
      setState('error');
    }
  };

  return (
    <div style={{ fontFamily: 'system-ui, -apple-system, sans-serif', padding: '24px', maxWidth: '1200px', margin: '0 auto', color: '#1e293b' }}>
      {/* Header Bar */}
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', borderBottom: '1px solid #e2e8f0', paddingBottom: '16px' }}>
        <div>
          <h1 style={{ margin: 0, fontSize: '24px', fontWeight: 700, color: '#0f172a' }}>Hramatka Teacher Dashboard</h1>
          <p style={{ margin: '4px 0 0', fontSize: '14px', color: '#64748b' }}>State Standard 2024 Lesson Generator & Interactive Classroom Hub</p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontSize: '12px', fontWeight: 600, padding: '4px 10px', borderRadius: '12px', backgroundColor: isBackendReady ? '#dcfce7' : '#fee2e2', color: isBackendReady ? '#166534' : '#991b1b' }}>
            {isBackendReady === null ? 'Checking API...' : isBackendReady ? '● API Online' : '○ API Offline'}
          </span>
          <button onClick={fetchCatalog} style={{ cursor: 'pointer', padding: '8px 14px', borderRadius: '6px', border: '1px solid #cbd5e1', backgroundColor: '#ffffff', color: '#334155', fontWeight: 500 }}>
            Refresh
          </button>
        </div>
      </header>

      {/* Error Banner */}
      {errorMessage && (
        <div style={{ padding: '14px 18px', backgroundColor: '#fef2f2', border: '1px solid #fecaca', borderRadius: '8px', color: '#991b1b', marginBottom: '20px' }}>
          <strong>Error:</strong> {errorMessage}
        </div>
      )}

      {/* Main Layout Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: '24px' }}>
        {/* Left Column: Catalog / Active Lesson View */}
        <main>
          {state === 'catalog_loading' && (
            <div style={{ padding: '40px', textAlign: 'center', color: '#64748b' }}>
              Loading lesson catalog...
            </div>
          )}

          {state === 'baking_poll' && (
            <div style={{ padding: '32px', border: '1px solid #bae6fd', borderRadius: '12px', backgroundColor: '#f0f9ff', textAlign: 'center', marginBottom: '24px' }}>
              <h3 style={{ margin: '0 0 8px', color: '#0369a1' }}>Baking Lesson Draft...</h3>
              <p style={{ margin: 0, fontSize: '14px', color: '#0284c7' }}>
                Gemini 3.6 Flash engine is validating State Standard 2024 alignment and generating activity sidecars.
              </p>
            </div>
          )}

          {state === 'lesson_active' && selectedLesson && (
            <div style={{ border: '1px solid #cbd5e1', borderRadius: '12px', padding: '24px', backgroundColor: '#ffffff', marginBottom: '24px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <h2 style={{ margin: 0, fontSize: '20px', color: '#0f172a' }}>{selectedLesson.title}</h2>
                <button onClick={() => setState('catalog_ready')} style={{ cursor: 'pointer', padding: '6px 12px', borderRadius: '6px', border: '1px solid #cbd5e1', backgroundColor: '#f8fafc' }}>
                  ← Back to Catalog
                </button>
              </div>

              <div style={{ display: 'flex', gap: '12px', fontSize: '14px', color: '#475569', marginBottom: '20px' }}>
                <span><strong>CEFR:</strong> {selectedLesson.cefr_level.toUpperCase()}</span>
                <span>•</span>
                <span><strong>Blocks:</strong> {selectedLesson.blocks.length}</span>
                <span>•</span>
                <span><strong>Support Vocab:</strong> {selectedSupport?.vocabulary?.length || 0} lemmas</span>
              </div>

              <div style={{ backgroundColor: '#f8fafc', padding: '16px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                <h4 style={{ margin: '0 0 8px', color: '#334155' }}>Lesson Summary</h4>
                <p style={{ margin: 0, fontSize: '14px', color: '#475569' }}>{selectedLesson.summary || 'No summary provided.'}</p>
              </div>
            </div>
          )}

          {(state === 'catalog_ready' || state === 'baking_poll' || state === 'error') && (
            <div>
              <h3 style={{ margin: '0 0 16px', fontSize: '18px', color: '#0f172a' }}>Lesson Catalog ({lessons.length})</h3>
              {lessons.length === 0 ? (
                <div style={{ padding: '32px', textAlign: 'center', border: '2px dashed #e2e8f0', borderRadius: '12px', color: '#64748b' }}>
                  No lessons found. Use the panel on the right to generate your first lesson!
                </div>
              ) : (
                <div style={{ display: 'grid', gap: '12px' }}>
                  {lessons.map((lesson) => (
                    <div
                      key={lesson.id}
                      onClick={() => lesson.status === 'ready' && handleSelectLesson(lesson.id)}
                      style={{
                        padding: '16px',
                        borderRadius: '8px',
                        border: '1px solid #e2e8f0',
                        backgroundColor: '#ffffff',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        cursor: lesson.status === 'ready' ? 'pointer' : 'default',
                        transition: 'border-color 0.15s ease',
                      }}
                    >
                      <div>
                        <div style={{ fontWeight: 600, color: '#0f172a', marginBottom: '4px' }}>{lesson.title || `Lesson ${lesson.id}`}</div>
                        <div style={{ fontSize: '13px', color: '#64748b' }}>
                          CEFR {lesson.cefr_level.toUpperCase()} {lesson.topic ? `• ${lesson.topic}` : ''}
                        </div>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                        <span style={{
                          fontSize: '12px',
                          fontWeight: 600,
                          padding: '4px 10px',
                          borderRadius: '12px',
                          backgroundColor:
                            lesson.status === 'ready' ? '#dcfce7' :
                            lesson.status === 'baking' ? '#e0f2fe' :
                            lesson.status === 'failed' ? '#fee2e2' : '#f1f5f9',
                          color:
                            lesson.status === 'ready' ? '#166534' :
                            lesson.status === 'baking' ? '#0369a1' :
                            lesson.status === 'failed' ? '#991b1b' : '#475569',
                        }}>
                          {lesson.status.toUpperCase()}
                        </span>
                        {lesson.status === 'ready' && (
                          <button style={{ cursor: 'pointer', padding: '6px 12px', borderRadius: '6px', border: 'none', backgroundColor: '#2563eb', color: '#ffffff', fontWeight: 500 }}>
                            Open
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </main>

        {/* Right Column: Generation Panel */}
        <aside>
          <div style={{ border: '1px solid #cbd5e1', borderRadius: '12px', padding: '20px', backgroundColor: '#ffffff' }}>
            <h3 style={{ margin: '0 0 16px', fontSize: '16px', color: '#0f172a' }}>Generate New Lesson</h3>
            <form onSubmit={handleGenerateLesson} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: '#475569', marginBottom: '4px' }}>CEFR Level</label>
                <select
                  value={cefrLevel}
                  onChange={(e) => setCefrLevel(e.target.value as any)}
                  style={{ width: '100%', padding: '8px', borderRadius: '6px', border: '1px solid #cbd5e1' }}
                >
                  <option value="a1">A1 (Beginner)</option>
                  <option value="a2">A2 (Elementary)</option>
                  <option value="b1">B1 (Intermediate)</option>
                  <option value="b2">B2 (Upper Intermediate)</option>
                  <option value="c1">C1 (Advanced)</option>
                  <option value="c2">C2 (Mastery)</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: '#475569', marginBottom: '4px' }}>Topic / Theme</label>
                <input
                  type="text"
                  placeholder="e.g., В магазині та супермаркеті"
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  required
                  style={{ width: '100%', padding: '8px', borderRadius: '6px', border: '1px solid #cbd5e1', boxSizing: 'border-box' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: '#475569', marginBottom: '4px' }}>Target Grammar (comma separated)</label>
                <input
                  type="text"
                  placeholder="e.g., Знахідний відмінок, числа"
                  value={targetGrammar}
                  onChange={(e) => setTargetGrammar(e.target.value)}
                  style={{ width: '100%', padding: '8px', borderRadius: '6px', border: '1px solid #cbd5e1', boxSizing: 'border-box' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: '#475569', marginBottom: '4px' }}>Target Vocabulary (comma separated)</label>
                <input
                  type="text"
                  placeholder="e.g., хліб, молоко, ціна, яблуко"
                  value={targetVocabulary}
                  onChange={(e) => setTargetVocabulary(e.target.value)}
                  style={{ width: '100%', padding: '8px', borderRadius: '6px', border: '1px solid #cbd5e1', boxSizing: 'border-box' }}
                />
              </div>

              <button
                type="submit"
                disabled={state === 'generating' || !topic.trim()}
                style={{
                  marginTop: '8px',
                  padding: '10px 16px',
                  borderRadius: '6px',
                  border: 'none',
                  backgroundColor: state === 'generating' ? '#94a3b8' : '#2563eb',
                  color: '#ffffff',
                  fontWeight: 600,
                  cursor: state === 'generating' ? 'not-allowed' : 'pointer',
                  width: '100%',
                }}
              >
                {state === 'generating' ? 'Requesting Gemini 3.6...' : '⚡ Generate Lesson'}
              </button>
            </form>
          </div>
        </aside>
      </div>
    </div>
  );
};

export default TeacherDashboard;
