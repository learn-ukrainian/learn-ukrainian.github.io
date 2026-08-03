import { useEffect, useMemo } from 'react';
import { type PracticeStressItem, stripStressMarks } from '../lib/lexicon/srs';

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
  const cleanUnstressed = useMemo(() => stripStressMarks(item.unstressed), [item.unstressed]);

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

  const codePoints = Array.from(cleanUnstressed);
  const isCorrect = selectedPosition === item.stressIndex;

  // P0-5: Digit-1..n is a redundant accelerator, matching the choice/classify
  // pattern — the nucleus array is already in left-to-right reading order.
  useEffect(() => {
    if (answerLocked || item.nuclei.length === 0) return undefined;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.altKey || event.ctrlKey || event.metaKey) return;
      const target = event.target as HTMLElement | null;
      if (target?.closest?.('button, a, input, textarea, select, [role="button"]')) return;
      const digit = Number.parseInt(event.key, 10);
      if (!Number.isFinite(digit) || digit < 1 || digit > item.nuclei.length) return;
      const nucleus = item.nuclei[digit - 1];
      if (!nucleus) return;
      event.preventDefault();
      onSelect(nucleus.index);
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [answerLocked, item.nuclei, onSelect]);

  return (
    <div className="practice-stress" data-testid="practice-stress" data-locked={answerLocked}>
      <p className="practice-stress-word" lang="uk" aria-label={item.stressed}>
        {codePoints.map((char, position) => {
          const nucleus = nucleusByPosition.get(position);
          if (nucleus) {
            const selected = selectedPosition === position;
            const isTargetStressed = position === item.stressIndex;
            let verdictClass = '';
            if (answerLocked) {
              if (selected) {
                verdictClass = isCorrect ? ' correct' : ' wrong';
              } else if (isTargetStressed) {
                verdictClass = ' correct';
              }
            }
            return (
              <button
                key={`nucleus-${position}`}
                type="button"
                className={`stress-vowel${verdictClass}${selected ? ' selected' : ''}`}
                data-nucleus-index={nucleus.nucleusIndex}
                data-position={position}
                disabled={answerLocked}
                aria-pressed={selected}
                aria-keyshortcuts={String(nucleus.nucleusIndex + 1)}
                onClick={() => onSelect(position)}
              >
                <span className="stress-vowel-key" aria-hidden="true">{nucleus.nucleusIndex + 1}</span>
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
