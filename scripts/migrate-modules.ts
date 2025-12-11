#!/usr/bin/env npx ts-node
/**
 * Migration script: Refactor module directory structure
 *
 * FROM: curriculum/l2-uk-en/modules/module-01.md (global numbering)
 * TO:   curriculum/l2-uk-en/a1/01-cyrillic-code-i.md (level folders, local numbering)
 *
 * Changes:
 * - Creates level subfolders (a1, a2, a2+, b1, b1+, b2)
 * - Renames files to: {local-num}-{slug}.md
 * - Removes module: and level: from frontmatter (derived from path)
 * - Keeps phase:, title:, subtitle:, etc.
 *
 * Usage:
 *   npx ts-node scripts/migrate-modules.ts --dry-run   # Preview changes
 *   npx ts-node scripts/migrate-modules.ts             # Execute migration
 */

import { readdir, readFile, writeFile, mkdir, rm } from 'fs/promises';
import { join, dirname } from 'path';
import { existsSync } from 'fs';

const ROOT_DIR = join(__dirname, '..');
const CURRICULUM_DIR = join(ROOT_DIR, 'curriculum', 'l2-uk-en');
const OLD_MODULES_DIR = join(CURRICULUM_DIR, 'modules');

// Level definitions: global module ranges
const LEVEL_CONFIG = [
  { level: 'a1', start: 1, end: 30 },
  { level: 'a2', start: 31, end: 60 },
  { level: 'a2+', start: 61, end: 80 },
  { level: 'b1', start: 81, end: 120 },
  { level: 'b1+', start: 121, end: 160 },
  { level: 'b2', start: 161, end: 210 },
];

/**
 *
 */
function getLevelForModule(num: number): { level: string; localNum: number } | null {
  for (const cfg of LEVEL_CONFIG) {
    if (num >= cfg.start && num <= cfg.end) {
      return {
        level: cfg.level,
        localNum: num - cfg.start + 1,
      };
    }
  }
  return null;
}

/**
 *
 */
function slugify(text: string): string {
  return text
    .toLowerCase()
    .replace(/['']/g, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .substring(0, 40);
}

/**
 *
 */
function padNum(n: number): string {
  return String(n).padStart(2, '0');
}

interface ModuleMeta {
  globalNum: number;
  level: string;
  localNum: number;
  title: string;
  slug: string;
  oldPath: string;
  newPath: string;
  content: string;
  newContent: string;
}

/**
 *
 */
async function parseModuleFile(filePath: string, globalNum: number): Promise<ModuleMeta | null> {
  const content = await readFile(filePath, 'utf-8');

  // Extract frontmatter
  const fmMatch = content.match(/^---\n([\s\S]*?)\n---/);
  if (!fmMatch) {
    console.error(`  ⚠ No frontmatter in module-${globalNum}`);
    return null;
  }

  const fm = fmMatch[1];
  const titleMatch = fm.match(/^title:\s*["']?(.+?)["']?\s*$/m);
  if (!titleMatch) {
    console.error(`  ⚠ No title in module-${globalNum}`);
    return null;
  }

  const title = titleMatch[1];
  const levelInfo = getLevelForModule(globalNum);
  if (!levelInfo) {
    console.error(`  ⚠ Module ${globalNum} outside known level ranges`);
    return null;
  }

  const slug = slugify(title);
  const newFileName = `${padNum(levelInfo.localNum)}-${slug}.md`;
  const newPath = join(CURRICULUM_DIR, levelInfo.level, newFileName);

  // Create new content: remove module: and level: lines from frontmatter
  const newFm = fm
    .split('\n')
    .filter(line => !line.match(/^module:\s*\d+/) && !line.match(/^level:\s*/))
    .join('\n');

  const newContent = content.replace(/^---\n[\s\S]*?\n---/, `---\n${newFm}\n---`);

  return {
    globalNum,
    level: levelInfo.level,
    localNum: levelInfo.localNum,
    title,
    slug,
    oldPath: filePath,
    newPath,
    content,
    newContent,
  };
}

/**
 *
 */
function printMigrationSummary(byLevel: Map<string, ModuleMeta[]>) {
  console.log('📊 Migration Summary:\n');
  for (const [level, mods] of [...byLevel.entries()].sort()) {
    console.log(`  ${level.toUpperCase()}: ${mods.length} modules`);
    for (const m of mods.slice(0, 3)) {
      console.log(`    ${padNum(m.globalNum)} → ${level}/${padNum(m.localNum)}-${m.slug}.md`);
    }
    if (mods.length > 3) {
      console.log(`    ... and ${mods.length - 3} more`);
    }
    console.log();
  }
}

/**
 *
 */
async function main() {
  const dryRun = process.argv.includes('--dry-run');

  console.log('\n🔄 Module Directory Migration\n');
  console.log(`Mode: ${dryRun ? 'DRY RUN (no changes)' : 'EXECUTE'}\n`);

  if (!existsSync(OLD_MODULES_DIR)) {
    console.error('❌ Old modules directory not found:', OLD_MODULES_DIR);
    process.exit(1);
  }

  // Read all module files
  const files = (await readdir(OLD_MODULES_DIR))
    .filter(f => f.match(/^module-\d+\.md$/))
    .sort((a, b) => {
      const numA = parseInt(a.match(/\d+/)?.[0] || '0');
      const numB = parseInt(b.match(/\d+/)?.[0] || '0');
      return numA - numB;
    });

  console.log(`Found ${files.length} module files\n`);

  // Parse all modules
  const modules: ModuleMeta[] = [];
  for (const file of files) {
    const num = parseInt(file.match(/\d+/)?.[0] || '0');
    const meta = await parseModuleFile(join(OLD_MODULES_DIR, file), num);
    if (meta) {
      modules.push(meta);
    }
  }

  // Group by level for summary
  const byLevel = new Map<string, ModuleMeta[]>();
  for (const m of modules) {
    const arr = byLevel.get(m.level) || [];
    arr.push(m);
    byLevel.set(m.level, arr);
  }

  printMigrationSummary(byLevel);

  if (dryRun) {
    console.log('✅ Dry run complete. Run without --dry-run to execute.\n');
    return;
  }

  // Execute migration
  console.log('\n🚀 Executing migration...\n');

  // Create level directories
  for (const level of [...byLevel.keys()]) {
    const levelDir = join(CURRICULUM_DIR, level);
    if (!existsSync(levelDir)) {
      await mkdir(levelDir, { recursive: true });
      console.log(`  📁 Created ${level}/`);
    }
  }

  // Write new files
  for (const m of modules) {
    await mkdir(dirname(m.newPath), { recursive: true });
    await writeFile(m.newPath, m.newContent);
    console.log(`  ✓ ${m.level}/${padNum(m.localNum)}-${m.slug}.md`);
  }

  console.log(`\n✅ Migrated ${modules.length} modules to new structure`);
  console.log('\n⚠️  Old modules/ directory preserved. Delete manually after verification:');
  console.log(`    rm -rf ${OLD_MODULES_DIR}\n`);

  // Create a mapping file for reference
  const mappingPath = join(CURRICULUM_DIR, 'module-mapping.json');
  const mapping = modules.map(m => ({
    old: `modules/module-${padNum(m.globalNum)}.md`,
    new: `${m.level}/${padNum(m.localNum)}-${m.slug}.md`,
    globalNum: m.globalNum,
    localNum: m.localNum,
    level: m.level,
    title: m.title,
  }));
  await writeFile(mappingPath, JSON.stringify(mapping, null, 2));
  console.log(`📝 Mapping saved to: ${mappingPath}\n`);
}

main().catch(console.error);
