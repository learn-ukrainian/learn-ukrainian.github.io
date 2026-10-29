import type { DailyWord } from './daily';
import type { DailyPracticeDeckItem, PracticeLexeme } from './srs';
import { publicRecordId } from './practice-report';
const dailySources = new WeakMap<DailyPracticeDeckItem, DailyWord>();
export function bindDailyReport(item: DailyPracticeDeckItem, source: DailyWord): DailyPracticeDeckItem {
  dailySources.set(item, source);
  return item;
}
export function dailyReportRecords(item: DailyPracticeDeckItem, lexeme: PracticeLexeme | null): object[] {
  const source = dailySources.get(item);
  if (!source || publicRecordId(source) !== item.lemmaId) return [];
  const fields = ['lemma', 'gloss', 'cefr', 'pos', 'example', 'exampleEn', 'exampleProvenance', 'etymology'] as const;
  if (fields.some((key) => (item[key] ?? null) !== (source[key] ?? null))) return [];
  if (lexeme && (lexeme.ipa || (['lemma', 'gloss', 'cefr', 'pos', 'example', 'exampleEn'] as const).some((field) => !item[field] && lexeme[field]))) return [];
  return [source];
}
