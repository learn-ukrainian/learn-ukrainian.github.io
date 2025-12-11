#!/usr/bin/env npx ts-node
/**
 * Merge plus levels into parent levels to align with Ukrainian State Standard 2024
 *
 * Merges:
 *   a2+ → a2 (30 + 20 = 50 modules)
 *   b1+ → b1 (40 + 40 = 80 modules)
 *
 * Usage:
 *   npx ts-node scripts/merge-levels.ts --dry-run   # Preview changes
 *   npx ts-node scripts/merge-levels.ts             # Execute merge
 */

import { readdir, readFile, writeFile, rename, rmdir } from 'fs/promises';
import { join } from 'path';
import { existsSync } from 'fs';

const ROOT_DIR = join(__dirname, '..');
const CURRICULUM_DIR = join(ROOT_DIR, 'curriculum', 'l2-uk-en');

// Merge configurations
const MERGES = [
  { source: 'a2+', target: 'a2', targetStartNum: 31 },  // a2 has 30, a2+ starts at 31
  { source: 'b1+', target: 'b1', targetStartNum: 41 },  // b1 has 40, b1+ starts at 41
];

/**
 *
 */
function padNum(n: number): string {
  return String(n).padStart(2, '0');
}

// Cyrillic to Latin transliteration map
const TRANSLIT: Record<string, string> = {
  'а': 'a', 'б': 'b', 'в': 'v', 'г': 'h', 'ґ': 'g', 'д': 'd', 'е': 'e', 'є': 'ye',
  'ж': 'zh', 'з': 'z', 'и': 'y', 'і': 'i', 'ї': 'yi', 'й': 'y', 'к': 'k', 'л': 'l',
  'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
  'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch', 'ь': '',
  'ю': 'yu', 'я': 'ya',
};

/**
 *
 */
function slugify(text: string): string {
  // Transliterate Cyrillic
  let result = text.toLowerCase();
  for (const [cyr, lat] of Object.entries(TRANSLIT)) {
    result = result.replace(new RegExp(cyr, 'g'), lat);
  }
  // Convert to slug
  return result
    .replace(/[''":]/g, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .substring(0, 40);
}

/**
 *
 */
function extractTitle(content: string): string | null {
  const match = content.match(/^title:\s*["']?(.+?)["']?\s*$/m);
  return match ? match[1] : null;
}

// Update phase in frontmatter (e.g., A2+.1 → A2.4, B1+.1 → B1.5)
/**
 *
 */
function updatePhase(content: string, sourceLevel: string, targetLevel: string): string {
  // Map plus-level phases to parent level phases
  // A2+.1, A2+.2 → A2.4, A2.5
  // B1+.1, B1+.2, B1+.3, B1+.4 → B1.5, B1.6, B1.7, B1.8
  const phaseMap: Record<string, Record<string, string>> = {
    'a2+': {
      'A2+.1': 'A2.4',
      'A2+.2': 'A2.5',
    },
    'b1+': {
      'B1+.1': 'B1.5',
      'B1+.2': 'B1.6',
      'B1+.3': 'B1.7',
      'B1+.4': 'B1.8',
    },
  };

  const map = phaseMap[sourceLevel];
  if (!map) return content;

  let updated = content;
  for (const [oldPhase, newPhase] of Object.entries(map)) {
    updated = updated.replace(
      new RegExp(`^(phase:\\s*)${oldPhase.replace('+', '\\+')}`, 'm'),
      `$1${newPhase}`
    );
  }

  return updated;
}

/**
 *
 */
async function main() {
  const dryRun = process.argv.includes('--dry-run');

  console.log('\n🔄 Level Merge Script\n');
  console.log(`Mode: ${dryRun ? 'DRY RUN (no changes)' : 'EXECUTE'}\n`);
  console.log('Merging to align with Ukrainian State Standard 2024:');
  console.log('  - A2+ → A2');
  console.log('  - B1+ → B1\n');

  for (const merge of MERGES) {
    const sourceDir = join(CURRICULUM_DIR, merge.source);
    const targetDir = join(CURRICULUM_DIR, merge.target);

    if (!existsSync(sourceDir)) {
      console.log(`⚠ Source directory ${merge.source}/ not found, skipping...`);
      continue;
    }

    console.log(`\n📁 Merging ${merge.source}/ into ${merge.target}/\n`);

    // Get source files
    const sourceFiles = (await readdir(sourceDir))
      .filter(f => f.match(/^\d{2}-.*\.md$/))
      .sort();

    console.log(`  Found ${sourceFiles.length} files to merge`);

    // Process each file
    for (let i = 0; i < sourceFiles.length; i++) {
      const oldFile = sourceFiles[i];
      const oldNum = parseInt(oldFile.match(/^(\d{2})-/)?.[1] || '0', 10);
      let slug = oldFile.replace(/^\d{2}-/, '');

      const oldPath = join(sourceDir, oldFile);

      // Read content to get title for regenerating slug if needed
      const content = await readFile(oldPath, 'utf-8');

      // If slug is empty or very short, regenerate from title
      if (slug === '.md' || slug.length < 5) {
        const title = extractTitle(content);
        if (title) {
          slug = slugify(title) + '.md';
        }
      }

      const newNum = merge.targetStartNum + (oldNum - 1);
      const newFile = `${padNum(newNum)}-${slug}`;

      const newPath = join(targetDir, newFile);

      console.log(`  ${merge.source}/${oldFile} → ${merge.target}/${newFile}`);

      if (!dryRun) {
        // Update phase in content
        const updatedContent = updatePhase(content, merge.source, merge.target);

        // Write to new location
        await writeFile(newPath, updatedContent);
      }
    }

    // Remove source directory
    if (!dryRun) {
      // Delete source files
      for (const file of sourceFiles) {
        const { unlink } = await import('fs/promises');
        await unlink(join(sourceDir, file));
      }
      // Remove empty directory
      await rmdir(sourceDir);
      console.log(`\n  ✓ Removed empty ${merge.source}/ directory`);
    }
  }

  if (dryRun) {
    console.log('\n✅ Dry run complete. Run without --dry-run to execute.\n');
  } else {
    console.log('\n✅ Merge complete!\n');
    console.log('Next steps:');
    console.log('  1. Update scripts/generate.ts LEVEL_FOLDERS constant');
    console.log('  2. Update module-mapping.json');
    console.log('  3. Regenerate output\n');
  }
}

main().catch(console.error);
