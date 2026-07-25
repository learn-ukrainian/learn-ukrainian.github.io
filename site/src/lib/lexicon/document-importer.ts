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

  const { lemmaKeys, wordTranslations } = parsePlainTextWithTranslations(text);
  const clozeItems = extractDocumentClozeItems(text, lemmaKeys, wordTranslations);

  return {
    title,
    description: `Imported from ${file.name} (${lemmaKeys.length} words, ${clozeItems.length} sentences)`,
    lemma_keys: lemmaKeys,
    cloze_items: clozeItems,
  };
}

export function parsePlainTextWithTranslations(text: string): { lemmaKeys: string[]; wordTranslations: Map<string, string> } {
  const set = new Set<string>();
  const wordTranslations = new Map<string, string>();
  const lines = text.split(/\r?\n/);

  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) continue;

    // Check for delimiter pairs like "слово - translation", "слово : translation", "слово = translation"
    const delimiterMatch = trimmed.match(/^([а-щьюяєіїґА-ЩЬЮЯЄІЇҐ'’ʼ\-\s]+)\s*[\-:=—\t]\s*([a-zA-Z0-9\s,;'.()]+)$/);
    if (delimiterMatch) {
      const ukPart = delimiterMatch[1].trim();
      const enPart = delimiterMatch[2].trim();
      const words = ukPart.match(UKRAINIAN_WORD_REGEX);
      if (words) {
        for (const w of words) {
          const lemma = w.toLowerCase().replace(/['’ʼ]/g, "’").trim();
          if (lemma.length >= 2) {
            set.add(lemma);
            if (enPart) wordTranslations.set(lemma, enPart);
          }
        }
      }
    } else {
      extractUkrainianWords(trimmed, set);
    }
  }

  return { lemmaKeys: Array.from(set), wordTranslations };
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
  return parsePlainTextWithTranslations(text).lemmaKeys;
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
  return parsePlainTextWithTranslations(text).lemmaKeys;
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
 * Supports inflected form stem matching (e.g. книжка -> книжку, книжкою).
 */
export function extractDocumentClozeItems(text: string, lemmaKeys: string[], wordTranslations: Map<string, string> = new Map()): PracticeClozeItem[] {
  const sentences = text.split(/(?<=[.!?])\s+/).filter((s) => s.trim().length > 10);
  const clozeItems: PracticeClozeItem[] = [];
  const setKeys = new Set(lemmaKeys);

  const lemmaStems = new Map<string, string>();
  for (const key of lemmaKeys) {
    lemmaStems.set(key, getUkrainianStem(key));
  }

  let clozeCount = 0;
  for (const rawSentence of sentences) {
    const cleanSentence = rawSentence.trim();
    const words = cleanSentence.match(UKRAINIAN_WORD_REGEX);
    if (!words) continue;

    for (const rawWord of words) {
      const wordLower = rawWord.toLowerCase().replace(/['’ʼ]/g, "’").trim();
      const wordStem = getUkrainianStem(wordLower);

      let matchedLemma = setKeys.has(wordLower) ? wordLower : null;
      if (!matchedLemma && wordStem.length >= 3) {
        for (const [lemma, stem] of lemmaStems.entries()) {
          if (stem.length >= 3 && (wordStem.startsWith(stem) || stem.startsWith(wordStem))) {
            matchedLemma = lemma;
            break;
          }
        }
      }

      if (matchedLemma) {
        const blanked = cleanSentence.replace(rawWord, '_____');
        const distractors = Array.from(setKeys)
          .filter((w) => w !== matchedLemma)
          .slice(0, 3)
          .map((w, idx) => ({ optionId: `opt_dec_${idx}`, lemmaId: w, label: w, kind: 'distractor' }));

        const translation = wordTranslations.get(matchedLemma);

        clozeItems.push({
          clozeId: `doc_cloze_${++clozeCount}_${matchedLemma}`,
          lemmaId: matchedLemma,
          sentenceFrameId: `doc_frame_${clozeCount}`,
          sentence: blanked,
          blankCase: 'context',
          form: rawWord,
          lemma: matchedLemma,
          caseRule: { code: 'document-context', labelUk: 'Контекст з документа', labelEn: 'Document Sentence', caseLabel: 'знахідний' },
          clozeEn: translation ? `Translation: ${translation}` : 'Sentence from your imported text',
          options: [
            { optionId: 'opt_ans', lemmaId: matchedLemma, label: rawWord, kind: 'answer' },
            ...distractors,
          ],
        });
        break; // Max 1 cloze item per sentence
      }
    }
  }

  return clozeItems;
}

function getUkrainianStem(word: string): string {
  const clean = word.toLowerCase().replace(/['’ʼ]/g, "’").trim();
  if (clean.length <= 3) return clean;
  return clean.replace(/(ами|ями|ах|ях|ом|ем|єю|ою|ів|ев|єв|а|я|у|ю|е|є|и|і|ї)$/u, '');
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
