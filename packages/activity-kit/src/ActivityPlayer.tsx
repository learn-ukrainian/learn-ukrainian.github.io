import Cloze from './components/Cloze';
import ErrorCorrection from './components/ErrorCorrection';
import EssayResponse from './components/EssayResponse';
import FillIn from './components/FillIn';
import MarkTheWords, { MarkTheWordsActivity } from './components/MarkTheWords';
import MatchUp from './components/MatchUp';
import Quiz from './components/Quiz';
import ReadingActivity from './components/ReadingActivity';
import TrueFalse from './components/TrueFalse';
import type { LuActivityV1 } from './lu.activity.v1.generated';

/**
 * Activity shapes emitted by the activities-b1/activity-v2 pipeline.
 *
 * The public lesson-document envelope has a separately versioned schema, so
 * these source activities intentionally remain a small, explicit union rather
 * than widening LuActivityV1 with unvalidated `unknown` payloads.
 */
export type ActivitySourceActivity =
  | {
    id?: string;
    type: 'quiz';
    title?: string;
    instruction: string;
    items: Array<{ question: string; options: string[]; correct: number; explanation?: string }>;
  }
  | {
    id?: string;
    type: 'mark-the-words';
    title?: string;
    instruction: string;
    text: string;
    target_words: string[];
    criteria?: string;
  }
  | {
    id?: string;
    type: 'error-correction';
    title?: string;
    instruction: string;
    items: Array<{
      sentence: string;
      error: string;
      correction: string;
      options?: string[];
      explanation?: string;
    }>;
  }
  | {
    id?: string;
    type: 'fill-in';
    title?: string;
    instruction: string;
    items: Array<{ sentence: string; answer: string; options?: string[] }>;
  };

export type ActivityPlayerActivity = LuActivityV1 | ActivitySourceActivity;
type ActivityPlayerActivityType = ActivityPlayerActivity['type'];

export interface ActivityCompletionEvent {
  activityId: string;
  activityType: ActivityPlayerActivityType;
}

export interface ActivityEditOperation {
  op: 'add' | 'remove' | 'replace';
  path: string;
  old: unknown;
  new: unknown;
}

export interface ActivityPlayerProps {
  activity: ActivityPlayerActivity;
  onComplete?: (event: ActivityCompletionEvent) => void;
  /**
   * Reserved for controlled editor integrations. This player has no editor UI
   * and never transports events; an editor can emit this local operation shape.
   */
  onEdit?: (operation: ActivityEditOperation) => void;
  isUkrainian?: boolean;
}

export function ActivityPlayer({ activity, onComplete, isUkrainian }: ActivityPlayerProps) {
  const complete = () => {
    onComplete?.({ activityId: activity.id ?? activity.type, activityType: activity.type });
  };

  const title = activity.title ?? activity.type;

  return (
    <section data-activity-player={activity.type} aria-label={title}>
      <h2>{title}</h2>
      {activity.type === 'true-false' && (
        <TrueFalse
          items={activity.payload.items.map(({ statement, correct, explanation }) => ({
            statement,
            isTrue: correct,
            explanation,
          }))}
          instruction={activity.payload.instruction}
          isUkrainian={isUkrainian}
          onComplete={complete}
        />
      )}
      {activity.type === 'cloze' && (
        <Cloze
          passage={activity.payload.text}
          blanks={activity.payload.blanks.map(({ id, answer, options }) => ({
            index: id,
            answer,
            options,
          }))}
          instruction={activity.payload.instruction}
          isUkrainian={isUkrainian}
          onComplete={complete}
        />
      )}
      {activity.type === 'match-up' && (
        <MatchUp
          pairs={activity.payload.pairs}
          instruction={activity.payload.instruction}
          isUkrainian={isUkrainian}
          onComplete={complete}
        />
      )}
      {activity.type === 'quiz' && (
        <Quiz
          questions={activity.items.map(({ question, options, correct, explanation }) => ({
            question,
            options: options.map((text, index) => ({ text, correct: index === correct })),
            explanation,
          }))}
          instruction={activity.instruction}
          isUkrainian={isUkrainian}
        />
      )}
      {activity.type === 'mark-the-words' && (
        <MarkTheWords isUkrainian={isUkrainian}>
          <MarkTheWordsActivity
            text={activity.text}
            correctWords={activity.target_words.flatMap((word) => word.split(/\s+/).filter(Boolean))}
            instruction={[activity.instruction, activity.criteria].filter(Boolean).join(' ')}
            isUkrainian={isUkrainian}
          />
        </MarkTheWords>
      )}
      {activity.type === 'error-correction' && 'items' in activity && (
        <ErrorCorrection
          items={activity.items.map(({ sentence, error, correction, options, explanation }) => ({
            sentence,
            errorWord: error,
            correctForm: correction,
            options: options ?? [],
            explanation: explanation ?? '',
          }))}
          instruction={activity.instruction}
          isUkrainian={isUkrainian}
        />
      )}
      {activity.type === 'error-correction' && 'payload' in activity && (
        <ErrorCorrection
          items={activity.payload.items.map((sentence, index) => ({
            sentence,
            errorWord: sentence,
            correctForm: activity.answer_key.items[index] ?? '',
            options: [],
            explanation: '',
          }))}
          instruction={activity.payload.instruction}
          isUkrainian={isUkrainian}
        />
      )}
      {activity.type === 'fill-in' && (
        <FillIn
          items={activity.items.map(({ sentence, answer, options }) => ({
            sentence: sentence.replace(/\{[^{}]+\}/g, '___'),
            answer,
            options: options ?? [answer],
          }))}
          instruction={activity.instruction}
          isUkrainian={isUkrainian}
        />
      )}
      {activity.type === 'multiple-choice' && (
        <Quiz
          questions={activity.payload.items.map(({ prompt, options }, index) => {
            const correct = activity.answer_key.items.find((item) => item.index === index)?.correct;
            return {
              question: prompt,
              options: options.map((text) => ({
                text,
                correct: text === correct || text.startsWith(`${correct})`),
              })),
            };
          })}
          instruction={activity.payload.instruction}
          isUkrainian={isUkrainian}
        />
      )}
      {activity.type === 'text-questions' && (
        <>
          <ReadingActivity
            title={title}
            context={activity.payload.instruction}
            tasks={activity.payload.items}
            activityType="text-questions"
            isUkrainian={isUkrainian}
          />
          <aside data-activity-teacher-guidance="text-questions">
            <strong>{isUkrainian ? 'Для обговорення / оцінювання:' : 'For discussion / grading:'}</strong>{' '}
            {activity.answer_key.guidance}
          </aside>
        </>
      )}
      {activity.type === 'short-writing' && (
        <>
          <EssayResponse
            title={title}
            prompt={activity.payload.prompt}
            activityType="short-writing"
            isUkrainian={isUkrainian}
          />
          <aside data-activity-teacher-guidance="short-writing">
            <strong>{isUkrainian ? 'Для обговорення / оцінювання:' : 'For discussion / grading:'}</strong>{' '}
            {activity.answer_key.guidance}
          </aside>
        </>
      )}
      {![
        'true-false',
        'cloze',
        'match-up',
        'quiz',
        'mark-the-words',
        'error-correction',
        'fill-in',
        'multiple-choice',
        'text-questions',
        'short-writing',
      ].includes(activity.type) && (
        <p data-activity-placeholder={activity.type}>тип поки без віджета</p>
      )}
    </section>
  );
}
