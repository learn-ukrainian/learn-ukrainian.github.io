import React, { useState, useMemo } from 'react';
import type { LuLessonV1, LuLessonBlock } from '../lu.lesson.v1.generated';
import type { LuLessonSupportV1 } from '../lu.lesson-support.v1.generated';
import { ActivityPlayer } from '../ActivityPlayer';

export type LessonViewerMode = 'teacher_review' | 'conduct' | 'print' | 'student';

export interface LessonViewerProps {
  lesson: LuLessonV1;
  support?: LuLessonSupportV1 | null;
  initialMode?: LessonViewerMode;
  onModeChange?: (mode: LessonViewerMode) => void;
  onComplete?: (blockId: string, result: Record<string, unknown>) => void;
}

/**
 * Strips all answer keys, model answers, teacher notes, and answer hints from a lesson
 * before rendering in Student mode to ensure ZERO answer leakage in the DOM.
 */
export function sanitizeLessonForStudent(lesson: LuLessonV1): LuLessonV1 {
  return {
    ...lesson,
    blocks: lesson.blocks.map((block) => {
      const sanitizedActivity = block.activity ? {
        ...block.activity,
        answer_key: null,
        payload: block.activity.payload ? {
          ...block.activity.payload,
          model_answer: undefined,
          guidance: undefined,
          rubric: undefined,
          answer_key: undefined,
        } : block.activity.payload,
      } : block.activity;

      return {
        ...block,
        answer_key: null,
        note: null,
        activity: sanitizedActivity as any,
        provenance: {
          ...block.provenance,
          external_options: false,
        },
      };
    }),
  };
}

export const LessonViewer: React.FC<LessonViewerProps> = ({
  lesson,
  support,
  initialMode = 'teacher_review',
  onModeChange,
  onComplete,
}) => {
  const [mode, setMode] = useState<LessonViewerMode>(initialMode);
  const [activeBlockIndex, setActiveBlockIndex] = useState<number>(0);
  const [revealedAnswers, setRevealedAnswers] = useState<Record<string, boolean>>({});

  const handleModeToggle = (newMode: LessonViewerMode) => {
    setMode(newMode);
    if (onModeChange) onModeChange(newMode);
  };

  const toggleAnswerReveal = (blockId: string) => {
    setRevealedAnswers((prev) => ({ ...prev, [blockId]: !prev[blockId] }));
  };

  // Compute safe lesson object according to active view mode
  const displayLesson = useMemo(() => {
    if (mode === 'student') {
      return sanitizeLessonForStudent(lesson);
    }
    return lesson;
  }, [lesson, mode]);

  const activeBlock: LuLessonBlock | undefined = displayLesson.blocks[activeBlockIndex];

  return (
    <div className={`hramatka-lesson-viewer mode-${mode}`} style={{ fontFamily: 'system-ui, -apple-system, sans-serif', color: '#1e293b' }}>
      {/* View Mode Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', backgroundColor: '#0f172a', padding: '12px 20px', borderRadius: '8px 8px 0 0', color: '#ffffff' }}>
        <div style={{ fontWeight: 700, fontSize: '16px' }}>
          {lesson.title} <span style={{ opacity: 0.7, fontWeight: 400, fontSize: '13px' }}>({lesson.level})</span>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          {(['teacher_review', 'conduct', 'print', 'student'] as LessonViewerMode[]).map((m) => (
            <button
              key={m}
              onClick={() => handleModeToggle(m)}
              style={{
                cursor: 'pointer',
                padding: '6px 14px',
                borderRadius: '6px',
                border: 'none',
                backgroundColor: mode === m ? '#2563eb' : '#1e293b',
                color: '#ffffff',
                fontWeight: mode === m ? 600 : 400,
                fontSize: '13px',
                textTransform: 'capitalize',
              }}
            >
              {m.replace('_', ' ')} Mode
            </button>
          ))}
        </div>
      </div>

      {/* Main Content Body */}
      <div style={{ border: '1px solid #cbd5e1', borderTop: 'none', borderRadius: '0 0 8px 8px', padding: '24px', backgroundColor: '#ffffff' }}>
        {/* STUDENT MODE (Zero Answer Leakage) */}
        {mode === 'student' && (
          <div data-testid="student-mode-container">
            <div style={{ display: 'flex', gap: '12px', marginBottom: '20px', borderBottom: '1px solid #e2e8f0', paddingBottom: '12px' }}>
              {displayLesson.blocks.map((b, i) => (
                <button
                  key={b.id}
                  onClick={() => setActiveBlockIndex(i)}
                  style={{
                    cursor: 'pointer',
                    padding: '8px 16px',
                    borderRadius: '6px',
                    border: '1px solid #cbd5e1',
                    backgroundColor: activeBlockIndex === i ? '#2563eb' : '#f8fafc',
                    color: activeBlockIndex === i ? '#ffffff' : '#334155',
                    fontWeight: 600,
                  }}
                >
                  Activity {i + 1}
                </button>
              ))}
            </div>

            {activeBlock && (
              <div key={activeBlock.id} data-testid={`student-block-${activeBlock.id}`}>
                <ActivityPlayer
                  activity={activeBlock.activity}
                  onComplete={(res) => onComplete && onComplete(activeBlock.id, res as Record<string, unknown>)}
                />
              </div>
            )}
          </div>
        )}

        {/* TEACHER REVIEW MODE */}
        {mode === 'teacher_review' && (
          <div data-testid="teacher-review-container">
            <div style={{ backgroundColor: '#f8fafc', padding: '16px', borderRadius: '8px', border: '1px solid #e2e8f0', marginBottom: '24px' }}>
              <h4 style={{ margin: '0 0 8px', color: '#334155' }}>Teacher Notes & Focus</h4>
              <p style={{ margin: 0, fontSize: '14px', color: '#475569' }}>{lesson.focus || 'Standard lesson plan focus.'}</p>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
              {lesson.blocks.map((block, idx) => (
                <div key={block.id} style={{ border: '1px solid #e2e8f0', borderRadius: '8px', padding: '20px', backgroundColor: '#ffffff' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px', borderBottom: '1px solid #f1f5f9', paddingBottom: '8px' }}>
                    <span style={{ fontWeight: 600, color: '#0f172a' }}>Block {idx + 1}: {block.type}</span>
                    <span style={{ fontSize: '12px', padding: '2px 8px', borderRadius: '4px', backgroundColor: '#e0f2fe', color: '#0369a1' }}>
                      Phase {block.phase} • {block.mode}
                    </span>
                  </div>

                  <ActivityPlayer activity={block.activity} />

                  {block.answer_key && (
                    <div style={{ marginTop: '16px', padding: '12px', backgroundColor: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: '6px' }} data-testid={`answer-key-${block.id}`}>
                      <strong style={{ color: '#166534', fontSize: '13px' }}>Answer Key:</strong>
                      <pre style={{ margin: '4px 0 0', fontSize: '12px', color: '#14532d', whiteSpace: 'pre-wrap' }}>
                        {JSON.stringify(block.answer_key, null, 2)}
                      </pre>
                    </div>
                  )}

                  {block.note && (
                    <div style={{ marginTop: '12px', padding: '10px 12px', backgroundColor: '#fffbeb', border: '1px solid #fde68a', borderRadius: '6px', fontSize: '13px', color: '#92400e' }} data-testid={`block-note-${block.id}`}>
                      <strong style={{ color: '#78350f' }}>Note:</strong> {block.note}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* CONDUCT MODE */}
        {mode === 'conduct' && (
          <div data-testid="conduct-mode-container" style={{ textAlign: 'center', padding: '20px 0' }}>
            {activeBlock && (
              <div>
                <div style={{ fontSize: '18px', fontWeight: 600, color: '#334155', marginBottom: '16px' }}>
                  Presentation Activity {activeBlockIndex + 1} of {displayLesson.blocks.length}
                </div>

                <div style={{ textAlign: 'left', maxWidth: '800px', margin: '0 auto' }}>
                  <ActivityPlayer activity={activeBlock.activity} />
                </div>

                <div style={{ marginTop: '24px', display: 'flex', justifyContent: 'center', gap: '16px' }}>
                  <button
                    disabled={activeBlockIndex === 0}
                    onClick={() => setActiveBlockIndex((prev) => Math.max(0, prev - 1))}
                    style={{ cursor: activeBlockIndex === 0 ? 'not-allowed' : 'pointer', padding: '8px 20px', borderRadius: '6px', border: '1px solid #cbd5e1' }}
                  >
                    Previous
                  </button>
                  <button
                    onClick={() => toggleAnswerReveal(activeBlock.id)}
                    style={{ cursor: 'pointer', padding: '8px 20px', borderRadius: '6px', border: 'none', backgroundColor: '#0284c7', color: '#ffffff', fontWeight: 600 }}
                  >
                    {revealedAnswers[activeBlock.id] ? 'Hide Answer Key' : 'Reveal Answer Key'}
                  </button>
                  <button
                    disabled={activeBlockIndex === displayLesson.blocks.length - 1}
                    onClick={() => setActiveBlockIndex((prev) => Math.min(displayLesson.blocks.length - 1, prev + 1))}
                    style={{ cursor: activeBlockIndex === displayLesson.blocks.length - 1 ? 'not-allowed' : 'pointer', padding: '8px 20px', borderRadius: '6px', border: '1px solid #cbd5e1' }}
                  >
                    Next
                  </button>
                </div>

                {revealedAnswers[activeBlock.id] && activeBlock.answer_key && (
                  <div style={{ marginTop: '20px', padding: '16px', backgroundColor: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: '8px', maxWidth: '800px', margin: '20px auto 0', textAlign: 'left' }}>
                    <strong style={{ color: '#166534' }}>Answer Key:</strong>
                    <pre style={{ margin: '8px 0 0', fontSize: '13px', color: '#14532d' }}>
                      {JSON.stringify(activeBlock.answer_key, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* PRINT MODE */}
        {mode === 'print' && (
          <div data-testid="print-mode-container">
            <div style={{ textAlign: 'center', marginBottom: '32px', borderBottom: '2px solid #0f172a', paddingBottom: '16px' }}>
              <h2 style={{ margin: 0, fontSize: '24px' }}>{lesson.title}</h2>
              <div style={{ fontSize: '14px', color: '#475569', marginTop: '4px' }}>Level: {lesson.level} • Date: ____________ • Student Name: _____________________</div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
              {lesson.blocks.map((block, idx) => (
                <div key={block.id} style={{ pageBreakInside: 'avoid' }}>
                  <h4 style={{ margin: '0 0 12px', fontSize: '16px', color: '#0f172a' }}>Task {idx + 1}</h4>
                  <ActivityPlayer activity={block.activity} />
                </div>
              ))}
            </div>

            {/* Separate Answer Sheet for Print */}
            <div style={{ marginTop: '60px', pageBreakBefore: 'always', borderTop: '2px dashed #94a3b8', paddingTop: '24px' }}>
              <h3 style={{ margin: '0 0 16px', textAlign: 'center' }}>--- Answer Key Sheet (Teacher Copy) ---</h3>
              {lesson.blocks.map((block, idx) => (
                <div key={block.id} style={{ marginBottom: '12px' }}>
                  <strong>Task {idx + 1}:</strong> {JSON.stringify(block.answer_key)}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default LessonViewer;
