/**
 * Zero-Backend Document Importer for Practice Hub Custom Sets.
 * Client-side file parsing using FileReader API (txt, csv, tsv, json, yaml, md).
 * Zero server dependencies — 100% client-side.
 */

export interface ImportedDeck {
  title: string;
  description: string;
  lemma_keys: string[];
}

const UKRAINIAN_WORD_REGEX = /[а-щьюяєіїґА-ЩЬЮЯЄІЇҐ'’ʼ\-]+/g;

/**
 * Parse client-side File object and extract Ukrainian vocabulary items.
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

  return {
    title,
    description: `Imported from ${file.name} (${lemmaKeys.length} words)`,
    lemma_keys: lemmaKeys,
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
