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

export type ActivityPlayerActivity = LuActivityV1;
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
          questions={activity.payload.items.map(({ question, options, correct, explanation }) => ({
            question,
            options: options.map((text, index) => ({ text, correct: index === correct })),
            explanation,
          }))}
          instruction={activity.payload.instruction}
          isUkrainian={isUkrainian}
        />
      )}
      {activity.type === 'mark-the-words' && (
        <MarkTheWords isUkrainian={isUkrainian}>
          <MarkTheWordsActivity
            text={activity.payload.text}
            correctWords={activity.payload.target_words.flatMap((word) => word.split(/\s+/).filter(Boolean))}
            instruction={[activity.payload.instruction, activity.payload.criteria].filter(Boolean).join(' ')}
            isUkrainian={isUkrainian}
          />
        </MarkTheWords>
      )}
      {activity.type === 'error-correction' && (
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
          items={activity.payload.items.map(({ sentence, answer, options }) => ({
            sentence: sentence.replace(/\{[^{}]+\}/g, '___'),
            answer,
            options: options ?? [answer],
          }))}
          instruction={activity.payload.instruction}
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
            {'model_answers' in activity.answer_key && activity.answer_key.model_answers?.length ? (
              <>
                {' '}
                <span data-activity-model-answers="text-questions">
                  {activity.answer_key.model_answers.join(' · ')}
                </span>
              </>
            ) : null}
            {'rubric' in activity.answer_key && activity.answer_key.rubric ? (
              <>
                {' '}
                <span data-activity-rubric="text-questions">{activity.answer_key.rubric}</span>
              </>
            ) : null}
          </aside>
        </>
      )}
      {activity.type === 'short-writing' && (
        <>
          <EssayResponse
            title={title}
            prompt={activity.payload.prompt}
            modelAnswer={'model_answer' in activity.answer_key ? activity.answer_key.model_answer : undefined}
            rubric={'rubric' in activity.answer_key ? activity.answer_key.rubric : undefined}
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
