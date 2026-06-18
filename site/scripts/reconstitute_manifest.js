import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const DATASET_DIR = path.resolve(__dirname, '../../data/lexicon-dataset/dataset');
const MANIFEST_PATH = path.resolve(__dirname, '../src/data/lexicon-manifest.json');

function reconstitute() {
    if (!fs.existsSync(DATASET_DIR)) {
        console.warn(`[reconstitute_manifest] Dataset directory not found at ${DATASET_DIR}. Skipping.`);
        return;
    }

    const metadataPath = path.join(DATASET_DIR, '_metadata.json');
    if (!fs.existsSync(metadataPath)) {
        console.error(`[reconstitute_manifest] _metadata.json not found in ${DATASET_DIR}.`);
        process.exit(1);
    }

    const manifest = JSON.parse(fs.readFileSync(metadataPath, 'utf8'));
    const entries = [];

    const files = fs.readdirSync(DATASET_DIR);
    for (const file of files) {
        if (!file.endsWith('.jsonl')) continue;
        const filePath = path.join(DATASET_DIR, file);
        const lines = fs.readFileSync(filePath, 'utf8').split('\n');
        for (const line of lines) {
            if (!line.trim()) continue;
            entries.push(JSON.parse(line));
        }
    }

    entries.sort((a, b) => (a.lemma || "").localeCompare(b.lemma || "", "uk"));

    manifest.entries = entries;

    fs.mkdirSync(path.dirname(MANIFEST_PATH), { recursive: true });
    fs.writeFileSync(MANIFEST_PATH, JSON.stringify(manifest, null, 2) + '\n', 'utf8');

    console.log(`[reconstitute_manifest] Reconstituted ${entries.length} entries to lexicon-manifest.json`);
}

reconstitute();
