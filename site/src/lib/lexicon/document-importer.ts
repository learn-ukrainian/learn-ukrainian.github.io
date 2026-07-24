import type { PracticeClozeItem } from './srs';

export interface ImportedDeck {
  title: string;
  description: string;
  lemma_keys: string[];
  cloze_items?: PracticeClozeItem[];
}

const UKRAINIAN_WORD_REGEX = /[а-щьюяєіїґА-ЩЬЮЯЄІЇҐ'’ʼ\-]+/g;

/**
 * Parse client-side File object and extract Ukrainian vocabulary items & sentence cloze drills.
 */
export async function parseDocumentFile(file: File): Promise<ImportedDeck> {
  const text = await file.readAsText();
  const filename = file.name.replace(/\.[^/.]+$/, '');
  const title = formatTitleFromFilename(filename);

  let lemmaKeys: string[] = [];

  if (file.name.endsWith('.json')) {
    lemmaKeys = parseJSONFile(text);
  } else if (file.name.endsWith('.csv') || file.name.endsWith('.tsv')) {
    lemmaKeys = parseCSVFile(text);
  } else {
    // Plain text, markdown, or yaml
    lemmaKeys = parsePlainText(text);
  }

  const clozeItems = extractDocumentClozeItems(text, lemmaKeys);

  return {
    title,
    description: `Imported from ${file.name} (${lemmaKeys.length} words, ${clozeItems.length} sentences)`,
    lemma_keys: lemmaKeys,
    cloze_items: clozeItems,
  };
}

function formatTitleFromFilename(name: string): string {
  return name
    .replace(/[-_]+/g, ' ')
    .replace(/\b\w/g, (l) => l.toUpperCase())
    .trim();
}

function parseJSONFile(text: string): string[] {
  try {
    const data = JSON.parse(text);
    if (Array.isArray(data)) {
      const set = new Set<string>();
      for (const item of data) {
        if (typeof item === 'string') {
          extractUkrainianWords(item, set);
        } else if (typeof item === 'object' && item !== null) {
          const val = item.lemma || item.word || item.uk || item.term || '';
          if (typeof val === 'string') extractUkrainianWords(val, set);
        }
      }
      return Array.from(set);
    }
  } catch {
    // Fallback to text scan if invalid JSON
  }
  return parsePlainText(text);
}

function parseCSVFile(text: string): string[] {
  const set = new Set<string>();
  const lines = text.split(/\r?\n/);
  for (const line of lines) {
    const cols = line.split(/[,;\t]/);
    for (const col of cols) {
      extractUkrainianWords(col.trim(), set);
    }
  }
  return Array.from(set);
}

function parsePlainText(text: string): string[] {
  const set = new Set<string>();
  extractUkrainianWords(text, set);
  return Array.from(set);
}

function extractUkrainianWords(input: string, set: Set<string>): void {
  const matches = input.match(UKRAINIAN_WORD_REGEX);
  if (matches) {
    for (const match of matches) {
      const clean = match.toLowerCase().replace(/['’ʼ]/g, "’").trim();
      if (clean.length >= 2) {
        set.add(clean);
      }
    }
  }
}

/**
 * Extract verbatim sentences containing vocabulary words and build cloze fill-in-the-blank items.
 */
export function extractDocumentClozeItems(text: string, lemmaKeys: string[]): PracticeClozeItem[] {
  const sentences = text.split(/(?<=[.!?])\s+/).filter((s) => s.trim().length > 10);
  const clozeItems: PracticeClozeItem[] = [];
  const setKeys = new Set(lemmaKeys);

  let clozeCount = 0;
  for (const rawSentence of sentences) {
    const cleanSentence = rawSentence.trim();
    const words = cleanSentence.match(UKRAINIAN_WORD_REGEX);
    if (!words) continue;

    for (const rawWord of words) {
      const lemma = rawWord.toLowerCase().replace(/['’ʼ]/g, "’").trim();
      if (setKeys.has(lemma)) {
        const blanked = cleanSentence.replace(rawWord, '_____');
        const distractors = Array.from(setKeys)
          .filter((w) => w !== lemma)
          .slice(0, 3)
          .map((w) => ({ label: w, kind: 'distractor' }));

        clozeItems.push({
          clozeId: `doc_cloze_${++clozeCount}_${lemma}`,
          lemmaId: lemma,
          sentenceFrameId: `doc_frame_${clozeCount}`,
          sentence: blanked,
          blankCase: 'context',
          form: rawWord,
          lemma: lemma,
          caseRule: { code: 'document-context', labelUk: 'Контекст з документа', labelEn: 'Document Sentence' },
          clozeEn: 'Sentence from your imported document',
          options: [
            { label: rawWord, kind: 'answer' },
            ...distractors,
          ],
        });
        break; // Max 1 cloze item per sentence
      }
    }
  }

  return clozeItems;
}

// File extension helper extension on File prototype for clean reading
declare global {
  interface File {
    readAsText(): Promise<string>;
  }
}

if (typeof File !== 'undefined' && !File.prototype.readAsText) {
  File.prototype.readAsText = function (): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result as string);
      reader.onerror = () => reject(reader.error);
      reader.readAsText(this);
    });
  };
}
