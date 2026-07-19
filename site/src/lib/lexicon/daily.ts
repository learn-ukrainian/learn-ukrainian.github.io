import { seededRandom } from "../../components/utils";

export interface DailyWord {
  lemma: string;
  slug: string;
  gloss: string | null;
  k?: string;
  lessonTag?: string;
  cefr?: string;
  weight?: number;
  /**
   * #5434 verified example sentence for the word of the day.
   * Absent until the sentence corpus lands — the UI omits the slot quietly.
   */
  example?: string | null;
  /** English rendering of `example` (A1 scaffolding only). */
  exampleEn?: string | null;
}

export function dateSeed(d: Date): number {
  return d.getFullYear() * 10000 + (d.getMonth() + 1) * 100 + d.getDate();
}

export function pickDaily<T>(pool: T[], seed: number, n: number): T[] {
  const result = [...pool];
  const rand = seededRandom(seed);
  for (let i = result.length - 1; i > 0; i--) {
    const j = Math.floor(rand() * (i + 1));
    [result[i], result[j]] = [result[j], result[i]];
  }
  return result.slice(0, Math.max(0, Math.min(n, result.length)));
}
