/**
 * Site compatibility shim. The source implementation is versioned in
 * @learn-ukrainian/activity-kit; these declarations retain lesson-schema input.
 */
export interface TrueFalseQuestionProps {
  /**
   * @schemaDescription Statement the learner marks true or false.
   * @ukrainianText true
   */
  statement: string;
  /**
   * @schemaDescription Is True value consumed by this component.
   * @ukrainianText false
   */
  isTrue: boolean;
  /**
   * @schemaDescription Feedback explanation shown after the learner answers.
   * @ukrainianText true
   */
  explanation?: string;
  /**
   * @schemaDescription UI language flag for Ukrainian labels and feedback.
   * @ukrainianText false
   */
  isUkrainian?: boolean;
}

export interface TrueFalseItem {
  /**
   * @schemaDescription Statement the learner marks true or false.
   * @ukrainianText true
   */
  statement: string;
  /**
   * @schemaDescription Is True value consumed by this component.
   * @ukrainianText false
   */
  isTrue: boolean;
  /**
   * @schemaDescription Feedback explanation shown after the learner answers.
   * @ukrainianText true
   */
  explanation?: string;
}

export interface TrueFalseProps {
  /**
   * @schemaDescription Array of activity items rendered by the component.
   * @ukrainianText true
   */
  items: TrueFalseItem[];
  /**
   * @schemaDescription Instruction shown to the learner above the activity.
   * @ukrainianText true
   */
  instruction?: string;
  /**
   * @schemaDescription UI language flag for Ukrainian labels and feedback.
   * @ukrainianText false
   */
  isUkrainian?: boolean;
  onComplete?: () => void;
}

export { default, TrueFalseQuestion } from '../../../packages/activity-kit/src/components/TrueFalse';
