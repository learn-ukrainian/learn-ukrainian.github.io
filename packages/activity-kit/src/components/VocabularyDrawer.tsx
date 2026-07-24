import React, { useState, useMemo } from 'react';
import type { LuLessonSupportVocabularyItem } from '../lu.lesson-support.v1.generated';

export interface VocabularyDrawerProps {
  vocabulary: LuLessonSupportVocabularyItem[];
  isOpen: boolean;
  onClose: () => void;
  title?: string;
}

export const VocabularyDrawer: React.FC<VocabularyDrawerProps> = ({
  vocabulary = [],
  isOpen,
  onClose,
  title = 'Lesson Vocabulary & Morphology',
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedPos, setSelectedPos] = useState<string>('all');

  // Extract unique POS tags for filtering
  const availablePos = useMemo(() => {
    const posSet = new Set<string>();
    vocabulary.forEach((item) => {
      if (item.pos) posSet.add(item.pos.toLowerCase());
    });
    return Array.from(posSet).sort();
  }, [vocabulary]);

  // Filtered vocabulary items (search + POS)
  const filteredVocabulary = useMemo(() => {
    const query = searchTerm.trim().toLowerCase();
    return vocabulary.filter((item) => {
      const matchesSearch =
        !query ||
        item.surface.toLowerCase().includes(query) ||
        item.lemma.toLowerCase().includes(query) ||
        item.gloss.toLowerCase().includes(query);

      const matchesPos = selectedPos === 'all' || item.pos.toLowerCase() === selectedPos;

      return matchesSearch && matchesPos;
    });
  }, [vocabulary, searchTerm, selectedPos]);

  if (!isOpen) return null;

  return (
    <div
      data-testid="vocabulary-drawer-overlay"
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(15, 23, 42, 0.5)',
        backdropFilter: 'blur(4px)',
        zIndex: 1000,
        display: 'flex',
        justifyContent: 'flex-end',
      }}
      onClick={onClose}
    >
      <div
        data-testid="vocabulary-drawer-panel"
        style={{
          width: '100%',
          maxWidth: '440px',
          height: '100%',
          backgroundColor: '#ffffff',
          boxShadow: '-4px 0 24px rgba(0, 0, 0, 0.15)',
          display: 'flex',
          flexDirection: 'column',
          color: '#1e293b',
          fontFamily: 'system-ui, -apple-system, sans-serif',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Drawer Header */}
        <div style={{ padding: '20px', borderBottom: '1px solid #e2e8f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h3 style={{ margin: 0, fontSize: '18px', fontWeight: 700, color: '#0f172a' }}>{title}</h3>
            <span style={{ fontSize: '12px', color: '#64748b' }}>{vocabulary.length} total attested lemmas</span>
          </div>
          <button
            onClick={onClose}
            style={{
              cursor: 'pointer',
              border: 'none',
              backgroundColor: '#f1f5f9',
              borderRadius: '50%',
              width: '32px',
              height: '32px',
              fontWeight: 700,
              color: '#475569',
            }}
          >
            ✕
          </button>
        </div>

        {/* Search & Filter Bar */}
        <div style={{ padding: '16px 20px', borderBottom: '1px solid #f1f5f9', display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <input
            type="text"
            placeholder="Search word, lemma, or gloss..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{ width: '100%', padding: '10px 12px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '14px', boxSizing: 'border-box' }}
          />

          {availablePos.length > 0 && (
            <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
              <button
                onClick={() => setSelectedPos('all')}
                style={{
                  cursor: 'pointer',
                  padding: '4px 10px',
                  borderRadius: '12px',
                  border: 'none',
                  fontSize: '12px',
                  fontWeight: 600,
                  backgroundColor: selectedPos === 'all' ? '#2563eb' : '#f1f5f9',
                  color: selectedPos === 'all' ? '#ffffff' : '#475569',
                }}
              >
                All
              </button>
              {availablePos.map((pos) => (
                <button
                  key={pos}
                  onClick={() => setSelectedPos(pos)}
                  style={{
                    cursor: 'pointer',
                    padding: '4px 10px',
                    borderRadius: '12px',
                    border: 'none',
                    fontSize: '12px',
                    fontWeight: 600,
                    backgroundColor: selectedPos === pos ? '#2563eb' : '#f1f5f9',
                    color: selectedPos === pos ? '#ffffff' : '#475569',
                    textTransform: 'uppercase',
                  }}
                >
                  {pos}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Vocabulary Items List */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '20px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {filteredVocabulary.length === 0 ? (
            <div style={{ padding: '32px', textAlign: 'center', color: '#64748b', fontSize: '14px' }}>
              No vocabulary items match your query.
            </div>
          ) : (
            filteredVocabulary.map((item, index) => (
              <div
                key={`${item.lemma}-${index}`}
                style={{
                  padding: '14px',
                  borderRadius: '8px',
                  border: '1px solid #e2e8f0',
                  backgroundColor: '#f8fafc',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '6px',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                  <span style={{ fontSize: '17px', fontWeight: 700, color: '#0f172a' }}>
                    {item.stress || item.surface}
                  </span>
                  <span style={{ fontSize: '11px', fontWeight: 700, padding: '2px 6px', borderRadius: '4px', backgroundColor: '#e2e8f0', color: '#334155', textTransform: 'uppercase' }}>
                    {item.pos}
                  </span>
                </div>

                <div style={{ fontSize: '13px', color: '#475569' }}>
                  <strong>Lemma:</strong> {item.lemma} {item.surface !== item.lemma ? `(form: ${item.surface})` : ''}
                </div>

                <div style={{ fontSize: '14px', color: '#1e293b', fontStyle: 'italic' }}>
                  "{item.gloss}"
                </div>

                {item.vesum_analysis && (
                  <div style={{ marginTop: '4px', fontSize: '11px', color: '#64748b', backgroundColor: '#ffffff', padding: '6px', borderRadius: '4px', border: '1px solid #e2e8f0' }}>
                    <strong>VESUM:</strong> {typeof item.vesum_analysis === 'string' ? item.vesum_analysis : JSON.stringify(item.vesum_analysis)}
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default VocabularyDrawer;
