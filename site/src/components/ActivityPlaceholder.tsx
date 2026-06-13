import React from 'react';

interface ActivityPlaceholderProps {
  type: string;
  description: string;
  itemCount?: number;
  focus?: string;
}

const TYPE_LABELS: Record<string, string> = {
  'quiz': 'Multiple Choice',
  'fill-in': 'Fill in the Blank',
  'match-up': 'Match the Pairs',
  'true-false': 'True or False',
  'unjumble': 'Unjumble',
  'group-sort': 'Group Sort',
  'anagram': 'Anagram',
  'error-correction': 'Error Correction',
  'cloze': 'Cloze',
  'select': 'Select',
  'translate': 'Translate',
  'image-to-letter': 'Image to Letter',
  'classify': 'Classify',
};

const ActivityPlaceholder: React.FC<ActivityPlaceholderProps> = ({
  type,
  description,
  itemCount,
  focus,
}) => {
  const label = TYPE_LABELS[type] || type;

  return (
    <div style={{
      border: '2px dashed #6b7280',
      borderRadius: '8px',
      padding: '1rem 1.25rem',
      margin: '1rem 0',
      backgroundColor: 'var(--sl-color-gray-7, #f3f4f6)',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
        <span style={{
          display: 'inline-block',
          padding: '0.15rem 0.5rem',
          borderRadius: '4px',
          fontSize: '0.75rem',
          fontWeight: 600,
          textTransform: 'uppercase',
          backgroundColor: 'var(--sl-color-accent, #3b82f6)',
          color: 'white',
        }}>
          {label}
        </span>
        {itemCount && (
          <span style={{ fontSize: '0.8rem', color: '#6b7280' }}>
            {itemCount} items
          </span>
        )}
      </div>
      <p style={{ margin: '0.25rem 0', fontSize: '0.9rem' }}>{description}</p>
      {focus && (
        <p style={{ margin: '0.25rem 0', fontSize: '0.8rem', color: '#6b7280', fontStyle: 'italic' }}>
          Focus: {focus}
        </p>
      )}
      <p style={{ margin: '0.5rem 0 0', fontSize: '0.75rem', color: '#9ca3af' }}>
        Planned activity — will be built in activities phase
      </p>
    </div>
  );
};

export default ActivityPlaceholder;
