import type React from 'react';

/**
 * Site compatibility shim. The source implementation is versioned in
 * @learn-ukrainian/activity-kit; these declarations retain lesson-schema input.
 */
export interface ClozeBlank {
  /**
   * @schemaDescription Index value consumed by this component.
   * @ukrainianText false
   */
  index: number;
  /**
   * @schemaDescription Answer options shown to the learner.
   * @ukrainianText true
   */
  options: string[];
  /**
   * @schemaDescription Correct answer used for validation and feedback.
   * @ukrainianText true
   */
  answer: string;
}

export interface ClozePassageProps {
  /**
   * @schemaDescription Text passage shown to the learner.
   * @ukrainianText true
   */
  text: string;
  /**
   * @schemaDescription Blanks value consumed by this component.
   * @ukrainianText true
   */
  blanks: ClozeBlank[];
  /**
   * @schemaDescription UI language flag for Ukrainian labels and feedback.
   * @ukrainianText false
   */
  isUkrainian?: boolean;
  onComplete?: () => void;
}

export interface ClozeProps {
  /**
   * @schemaDescription Passage value consumed by this component.
   * @ukrainianText true
   */
  passage?: string;
  /**
   * @schemaDescription Blanks value consumed by this component.
   * @ukrainianText true
   */
  blanks?: ClozeBlank[];
  /**
   * @schemaDescription Instruction shown to the learner above the activity.
   * @ukrainianText true
   */
  instruction?: string;
  /**
   * @schemaDescription Nested MDX content rendered inside the component.
   * @ukrainianText false
   */
  children?: React.ReactNode;
  /**
   * @schemaDescription UI language flag for Ukrainian labels and feedback.
   * @ukrainianText false
   */
  isUkrainian?: boolean;
  onComplete?: () => void;
}

export { default, ClozePassage } from '../../../packages/activity-kit/src/components/Cloze';
