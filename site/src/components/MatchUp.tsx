/**
 * Site compatibility shim. The source implementation is versioned in
 * @learn-ukrainian/activity-kit; these declarations retain lesson-schema input.
 */
import type { ReactNode } from 'react';
import KitMatchUp from '../../../packages/activity-kit/src/components/MatchUp';
import { useActivityIsUkrainian } from '../lib/i18n/useChromeLocale';

export interface MatchPair {
  /**
   * @schemaDescription Left value consumed by this component.
   * @ukrainianText true
   */
  left: string;
  /**
   * @schemaDescription Right value consumed by this component.
   * @ukrainianText true
   */
  right: string;
  lemmaId?: string;
}

export interface MatchUpProps {
  /**
   * @schemaDescription Pairs value consumed by this component.
   * @ukrainianText true
   */
  pairs: MatchPair[];
  /**
   * @schemaDescription Instruction shown to the learner above the activity.
   * @ukrainianText true
   */
  instruction?: ReactNode;
  /**
   * @schemaDescription UI language flag for Ukrainian labels and feedback.
   * @ukrainianText false
   */
  isUkrainian?: boolean;
  /**
   * @schemaDescription Optional practice-only pair-coding mode.
   * @ukrainianText false
   */
  matchedPairCoding?: 'semantic-four';
  /** Called once after every pair is connected correctly. */
  onComplete?: (correct: boolean) => void;
  onMatch?: (pairIndex: number, rating: 'again' | 'hard' | 'good') => void;
  /** Lets a host lock the board after it has recorded the result. */
  disabled?: boolean;
}

/** Follow site chrome locale toggle; ignore bake-time isUkrainian={false}. */
export default function MatchUp(props: MatchUpProps) {
  const isUkrainian = useActivityIsUkrainian(props.isUkrainian);
  return <KitMatchUp {...props} isUkrainian={isUkrainian} />;
}
