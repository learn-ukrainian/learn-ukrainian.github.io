import React from 'react';
import type { LuLessonSupportTheoryItem } from '../lu.lesson-support.v1.generated';

export interface TheoryCalloutProps {
  theory: LuLessonSupportTheoryItem;
  type?: 'rule' | 'tip' | 'warning' | 'note';
}

export const TheoryCallout: React.FC<TheoryCalloutProps> = ({
  theory,
  type = 'rule',
}) => {
  const colorMap = {
    rule: { bg: '#eff6ff', border: '#bfdbfe', text: '#1e3a8a', title: 'Grammar Rule' },
    tip: { bg: '#f0fdf4', border: '#bbf7d0', text: '#14532d', title: 'Linguistic Tip' },
    warning: { bg: '#fffbeb', border: '#fde68a', text: '#78350f', title: 'Usage Caution' },
    note: { bg: '#f8fafc', border: '#cbd5e1', text: '#334155', title: 'Theoretical Note' },
  };

  const style = colorMap[type] || colorMap.rule;

  return (
    <div
      data-testid={`theory-callout-${theory.id}`}
      style={{
        padding: '16px 20px',
        borderRadius: '8px',
        border: `1px solid ${style.border}`,
        backgroundColor: style.bg,
        color: style.text,
        marginBottom: '16px',
        fontFamily: 'system-ui, -apple-system, sans-serif',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
        <strong style={{ fontSize: '15px' }}>{style.title}</strong>
        <span style={{ fontSize: '11px', opacity: 0.7 }}>({theory.id})</span>
      </div>

      <div style={{ fontSize: '14px', lineHeight: '1.5', whiteSpace: 'pre-wrap' }}>
        {theory.body}
      </div>

      {theory.callouts && theory.callouts.length > 0 && (
        <ul style={{ margin: '12px 0 0', paddingLeft: '20px', fontSize: '13px' }}>
          {theory.callouts.map((c, i) => (
            <li key={i} style={{ marginBottom: '4px' }}>{c}</li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default TheoryCallout;
