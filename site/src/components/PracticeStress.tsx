import { useMemo } from 'react';
import type { PracticeStressItem } from '../lib/lexicon/srs';

export interface PracticeStressProps {
  item: PracticeStressItem;
  selectedPosition: number | null;
  answerLocked: boolean;
  onSelect(position: number): void;
}

interface NucleusInfo {
  nucleusIndex: number;
  label: string;
}

export default function PracticeStress({
  item,
  selectedPosition,
  answerLocked,
  onSelect,
}: PracticeStressProps) {
  const nucleusByPosition = useMemo(() => {
    const map = new Map<number, NucleusInfo>();
    for (let index = 0; index < item.nuclei.length; index += 1) {
      const nucleus = item.nuclei[index];
      if (nucleus && !map.has(nucleus.index)) {
        map.set(nucleus.index, { nucleusIndex: index, label: nucleus.label });
      }
    }
    return map;
  }, [item.nuclei]);

  const codePoints = Array.from(item.unstressed);
  const isCorrect = selectedPosition === item.stressIndex;

  return (
    <div className="practice-stress" data-testid="practice-stress" data-locked={answerLocked}>
      <p className="practice-stress-word" lang="uk" aria-label={item.stressed}>
        {codePoints.map((char, position) => {
          const nucleus = nucleusByPosition.get(position);
          if (nucleus) {
            const selected = selectedPosition === position;
            const verdictClass = answerLocked
              ? selected
                ? isCorrect
                  ? ' correct'
                  : ' wrong'
                : ''
              : '';
            return (
              <button
                key={`nucleus-${position}`}
                type="button"
                className={`stress-vowel${verdictClass}${selected ? ' selected' : ''}`}
                data-nucleus-index={nucleus.nucleusIndex}
                data-position={position}
                disabled={answerLocked}
                aria-pressed={selected}
                onClick={() => onSelect(position)}
              >
                {char}
              </button>
            );
          }
          return (
            <span key={`char-${position}`} className="stress-consonant" aria-hidden="true">
              {char}
            </span>
          );
        })}
      </p>
      {answerLocked && selectedPosition !== null ? (
        <p
          className={`practice-stress-verdict ${isCorrect ? 'correct' : 'wrong'}`}
          role="status"
          aria-live="polite"
          data-testid="practice-stress-verdict"
        >
          {isCorrect ? '✓' : '✗'}
        </p>
      ) : null}
    </div>
  );
}
