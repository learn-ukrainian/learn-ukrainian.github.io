/**
 * Site compatibility shim. The source implementation is versioned in
 * @learn-ukrainian/activity-kit; these declarations retain lesson-schema input.
 */
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
  instruction?: React.ReactNode;
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
  onComplete?: () => void;
  onMatch?: (pairIndex: number, rating: 'again' | 'hard' | 'good') => void;
}

export { default } from '../../../packages/activity-kit/src/components/MatchUp';
