import Cloze from './components/Cloze';
import MatchUp from './components/MatchUp';
import TrueFalse from './components/TrueFalse';
import type { LuActivityType, LuActivityV1 } from './lu.activity.v1.generated';

export interface ActivityCompletionEvent {
  activityId: string;
  activityType: LuActivityType;
}

export interface ActivityEditOperation {
  op: 'add' | 'remove' | 'replace';
  path: string;
  old: unknown;
  new: unknown;
}

export interface ActivityPlayerProps {
  activity: LuActivityV1;
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
    onComplete?.({ activityId: activity.id, activityType: activity.type });
  };

  return (
    <section data-activity-player={activity.type} aria-label={activity.title}>
      <h2>{activity.title}</h2>
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
    </section>
  );
}
