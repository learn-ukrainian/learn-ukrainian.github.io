#!/usr/bin/env npx ts-node
/**
 * Curricula-Opus Generator (Refactored)
 *
 * Uses modular lib/ architecture for parsing and rendering.
 * Reads modules from level folders: curriculum/{langPair}/{level}/*.md
 *
 * Usage:
 *   npm run generate                    # Generate all curricula
 *   npm run generate l2-uk-en           # Generate all levels for Ukrainian
 *   npm run generate l2-uk-en a1        # Generate only A1 level
 *   npm run generate l2-uk-en a1 5      # Generate only module 5 of A1
 */

import { readFile, readdir, mkdir, writeFile } from 'fs/promises';
import { join, dirname } from 'path';
import { existsSync } from 'fs';

import {
  parseModule,
  RenderContext,
  ParsedModule,
} from './lib';
import { renderVibeJson } from './lib/renderers/json';
import { renderHtml } from './lib/renderers/html';

// ============================================================================
// CONFIGURATION
// ============================================================================

const ROOT_DIR = join(__dirname, '..');
const CURRICULUM_DIR = join(ROOT_DIR, 'curriculum');
const OUTPUT_DIR = join(ROOT_DIR, 'output');
const ASSETS_DIR = join(__dirname, 'assets');

// ============================================================================
// UTILITIES
// ============================================================================

async function ensureDir(path: string): Promise<void> {
  if (!existsSync(path)) {
    await mkdir(path, { recursive: true });
  }
}

async function writeJSON(path: string, data: any): Promise<void> {
  await ensureDir(dirname(path));
  await writeFile(path, JSON.stringify(data, null, 2));
  console.log(`  ✓ ${path.replace(ROOT_DIR, '')}`);
}

async function writeHTML(path: string, html: string): Promise<void> {
  await ensureDir(dirname(path));
  await writeFile(path, html);
  console.log(`  ✓ ${path.replace(ROOT_DIR, '')}`);
}

function padNumber(n: number, len: number = 2): string {
  return String(n).padStart(len, '0');
}

// Level folder names (lowercase) - aligned with Ukrainian State Standard 2024
// No "plus" levels - these are the official CEFR levels
const LEVEL_FOLDERS = ['a1', 'a2', 'b1', 'b2', 'c1', 'c2'];

function levelFolderToDisplay(folder: string): string {
  return folder.toUpperCase();
}

function levelDisplayToFolder(display: string): string {
  return display.toLowerCase();
}

/**
 * Load vocabulary.csv and build a lookup map for image URLs.
 */
async function loadImageLookupMap(langPair: string): Promise<Map<string, string>> {
  const map = new Map<string, string>();
  const csvPath = join(CURRICULUM_DIR, langPair, 'vocabulary.csv');

  if (!existsSync(csvPath)) return map;

  try {
    const csvContent = await readFile(csvPath, 'utf-8');
    const lines = csvContent.split('\n');
    if (lines.length < 2) return map;

    const headers = lines[0].split(',').map(h => h.trim().toLowerCase());
    const lemmaCol = headers.indexOf('lemma');
    const englishCol = headers.indexOf('english');
    const imageCol = headers.indexOf('image_url');

    if (imageCol < 0) return map;

    for (let i = 1; i < lines.length; i++) {
      const line = lines[i].trim();
      if (!line) continue;

      // Simple CSV parsing
      const cells: string[] = [];
      let current = '';
      let inQuotes = false;

      for (const char of line) {
        if (char === '"') {
          inQuotes = !inQuotes;
        } else if (char === ',' && !inQuotes) {
          cells.push(current.trim());
          current = '';
        } else {
          current += char;
        }
      }
      cells.push(current.trim());

      const imageUrl = cells[imageCol];
      if (imageUrl) {
        if (lemmaCol >= 0 && cells[lemmaCol]) {
          map.set(cells[lemmaCol].toLowerCase(), imageUrl);
        }
        if (englishCol >= 0 && cells[englishCol]) {
          map.set(cells[englishCol].toLowerCase(), imageUrl);
        }
      }
    }
  } catch (error) {
    console.warn(`  ⚠ Could not load vocabulary.csv for images:`, error);
  }

  return map;
}

// ============================================================================
// MODULE INFO
// ============================================================================

interface ModuleInfo {
  num: number;
  level: string;
  title: string;
  subtitle?: string;
  phase: string;
  duration?: number;
  parsed: ParsedModule;
  vibeJSON: any;
}

// ============================================================================
// INDEX PAGE GENERATORS (kept from original)
// ============================================================================

// Extract phase prefix (e.g., "A2.5" from "A2.5 Vocabulary Expansion")
function getPhasePrefix(phase: string): string {
  const match = phase.match(/^[A-C]\d\+?\.\d+/);
  return match ? match[0] : phase;
}

// Convert HSL to Hex color
function hslToHex(h: number, s: number, l: number): string {
  s /= 100;
  l /= 100;
  const a = s * Math.min(l, 1 - l);
  const f = (n: number) => {
    const k = (n + h / 30) % 12;
    const color = l - a * Math.max(Math.min(k - 3, 9 - k, 1), -1);
    return Math.round(255 * color).toString(16).padStart(2, '0');
  };
  return `#${f(0)}${f(8)}${f(4)}`;
}

// Generate colors dynamically based on phase
// Each level gets a base hue, subphases rotate through that range
function getPhaseColor(phase: string): { bg: string; light: string } {
  const prefix = getPhasePrefix(phase);

  // Parse level and subphase: "A2.5" -> level="A2", sub=5
  const match = prefix.match(/^([A-C]\d\+?)\.(\d+)$/);
  if (!match) {
    return { bg: '#6b7280', light: '#f3f4f6' }; // default grey
  }

  const level = match[1];
  const subphase = parseInt(match[2], 10);

  // Base hues for each level (spread across color wheel)
  // A1: green (140), A2: blue-violet (250), B1: magenta (320), B2: orange (30), C1: teal (180), C2: red (0)
  const levelHues: Record<string, number> = {
    'A1': 140,   // green
    'A2': 250,   // blue-violet
    'A2+': 280,  // purple
    'B1': 320,   // magenta
    'B1+': 340,  // pink
    'B2': 30,    // orange
    'B2+': 60,   // yellow-green
    'C1': 180,   // teal
    'C1+': 200,  // cyan
    'C2': 0,     // red
  };

  const baseHue = levelHues[level] ?? 220;

  // Rotate hue slightly for each subphase (15 degrees per subphase)
  const hue = (baseHue + (subphase - 1) * 15) % 360;

  // Generate dark (bg) and light versions
  const bg = hslToHex(hue, 70, 45);      // saturated, medium dark
  const light = hslToHex(hue, 80, 92);   // saturated, very light

  return { bg, light };
}

function generateLevelIndex(
  modules: Array<{ num: number; title: string; subtitle?: string; phase: string; duration?: number }>,
  level: string,
  langPair: string
): string {

  const phases = [...new Set(modules.map(m => m.phase))];

  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${level} Modules | Ukrainian for English Speakers</title>
  <style>
    :root { --primary: #1a5fb4; --bg: #f8fafc; --card-bg: #fff; --text: #1e293b; --text-muted: #64748b; --border: #e2e8f0; }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: var(--bg); color: var(--text); line-height: 1.6; }
    .top-nav { background: #1e293b; color: white; padding: 0.75rem 2rem; font-size: 0.875rem; }
    .top-nav a { color: white; text-decoration: none; opacity: 0.9; }
    .top-nav a:hover { opacity: 1; text-decoration: underline; }
    header { background: linear-gradient(135deg, #1e40af, #7c3aed); color: white; padding: 3rem 2rem; text-align: center; }
    header h1 { font-size: 2.75rem; margin-bottom: 0.5rem; font-weight: 700; }
    header p { opacity: 0.9; font-size: 1.125rem; }
    main { max-width: 1200px; margin: 0 auto; padding: 2rem; }
    .phase-section { margin-bottom: 3rem; }
    .phase-header { display: flex; align-items: center; gap: 1rem; margin-bottom: 1.5rem; padding-bottom: 0.75rem; border-bottom: 2px solid var(--border); }
    .phase-header h2 { font-size: 1.25rem; font-weight: 600; color: var(--text); }
    .phase-count { background: var(--border); color: var(--text-muted); padding: 0.25rem 0.75rem; border-radius: 9999px; font-size: 0.75rem; font-weight: 500; }
    .tile-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 1.25rem; }
    .tile { background: var(--card-bg); border-radius: 16px; overflow: hidden; text-decoration: none; color: inherit; transition: transform 0.2s, box-shadow 0.2s; box-shadow: 0 1px 3px rgba(0,0,0,0.08); display: flex; flex-direction: column; }
    .tile:hover { transform: translateY(-4px); box-shadow: 0 12px 24px rgba(0,0,0,0.12); }
    .tile-header { padding: 1.25rem 1.25rem 1rem; display: flex; align-items: flex-start; gap: 1rem; }
    .tile-num { width: 48px; height: 48px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 1.125rem; color: white; flex-shrink: 0; }
    .tile-titles { flex: 1; min-width: 0; }
    .tile-title { font-size: 1rem; font-weight: 600; color: var(--text); margin-bottom: 0.25rem; line-height: 1.3; }
    .tile-subtitle { font-size: 0.875rem; color: var(--text-muted); line-height: 1.4; }
    .tile-footer { padding: 0.875rem 1.25rem; background: #f8fafc; border-top: 1px solid var(--border); display: flex; align-items: center; justify-content: space-between; margin-top: auto; }
    .tile-phase { font-size: 0.75rem; font-weight: 600; padding: 0.25rem 0.625rem; border-radius: 6px; }
    .tile-meta { font-size: 0.75rem; color: var(--text-muted); }
    footer { text-align: center; padding: 3rem 2rem; color: var(--text-muted); font-size: 0.875rem; }
    @media (max-width: 640px) { .tile-grid { grid-template-columns: 1fr; } header { padding: 2rem 1rem; } header h1 { font-size: 2rem; } main { padding: 1.5rem 1rem; } }
  </style>
</head>
<body>
  <div class="top-nav"><a href="../index.html">← ${langPair} Curriculum</a></div>
  <header>
    <h1>Level ${level}</h1>
    <p>Ukrainian for English Speakers · ${modules.length} Modules</p>
  </header>
  <main>
    ${phases.map(phase => {
    const phaseModules = modules.filter(m => m.phase === phase);
    return `
    <section class="phase-section">
      <div class="phase-header">
        <h2>${phase}</h2>
        <span class="phase-count">${phaseModules.length} modules</span>
      </div>
      <div class="tile-grid">
        ${phaseModules.map(m => {
      const c = getPhaseColor(m.phase);
      return `
        <a href="module-${padNumber(m.num)}.html" class="tile">
          <div class="tile-header">
            <div class="tile-num" style="background: ${c.bg};">${padNumber(m.num)}</div>
            <div class="tile-titles">
              <div class="tile-title">${m.title}</div>
              ${m.subtitle ? `<div class="tile-subtitle">${m.subtitle}</div>` : ''}
            </div>
          </div>
          <div class="tile-footer">
            <span class="tile-phase" style="background: ${c.light}; color: ${c.bg};">${m.phase}</span>
            <span class="tile-meta">${m.duration || 45} min</span>
          </div>
        </a>`;
    }).join('')}
      </div>
    </section>`;
  }).join('')}
  </main>
  <footer>curricula-opus · ${level}</footer>
</body>
</html>`;
}

function generateCurriculumIndex(
  levels: Array<{ level: string; moduleCount: number }>,
  langPair: string
): string {
  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Ukrainian for English Speakers | Curriculum</title>
  <style>
    :root { --primary: #1a5fb4; --bg: #fafafa; --card-bg: #fff; --text: #1e1e1e; --text-muted: #5e5e5e; --border: #e0e0e0; }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: var(--bg); color: var(--text); line-height: 1.6; }
    header { background: linear-gradient(135deg, #1a5fb4, #613583); color: white; padding: 4rem 2rem; text-align: center; }
    header h1 { font-size: 2.5rem; margin-bottom: 0.5rem; }
    header p { opacity: 0.9; font-size: 1.125rem; }
    main { max-width: 700px; margin: 0 auto; padding: 2rem; }
    .level-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1.5rem; }
    .level-card { background: var(--card-bg); border: 2px solid var(--border); border-radius: 16px; padding: 2rem; text-align: center; text-decoration: none; color: inherit; transition: all 0.2s; }
    .level-card:hover { border-color: var(--primary); transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0,0,0,0.1); }
    .level-card h2 { font-size: 2rem; color: var(--primary); margin-bottom: 0.5rem; }
    .level-card p { color: var(--text-muted); }
    footer { text-align: center; padding: 2rem; color: var(--text-muted); }
  </style>
</head>
<body>
  <header>
    <h1>🇺🇦 Ukrainian</h1>
    <p>for English Speakers</p>
  </header>
  <main>
    <div class="level-grid">
      ${levels.map(l => `
      <a href="${l.level.toLowerCase()}/index.html" class="level-card">
        <h2>${l.level}</h2>
        <p>${l.moduleCount} modules</p>
      </a>`).join('')}
    </div>
  </main>
  <footer>curricula-opus</footer>
</body>
</html>`;
}

function generateRootIndex(curricula: { langPair: string; name: string; levels: { level: string; count: number }[] }[]): string {
  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Curricula Opus</title>
  <style>
    :root { --primary: #1a5fb4; --bg: #fafafa; --card-bg: #fff; --text: #1e1e1e; --text-muted: #5e5e5e; --border: #e0e0e0; }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: var(--bg); color: var(--text); line-height: 1.6; }
    header { background: linear-gradient(135deg, #1a5fb4, #613583); color: white; padding: 4rem 2rem; text-align: center; }
    header h1 { font-size: 2.5rem; margin-bottom: 0.5rem; }
    header p { opacity: 0.9; font-size: 1.125rem; }
    main { max-width: 700px; margin: 0 auto; padding: 2rem; }
    .curriculum-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.5rem; }
    .curriculum-card { background: var(--card-bg); border: 2px solid var(--border); border-radius: 16px; padding: 2rem; text-decoration: none; color: inherit; transition: all 0.2s; }
    .curriculum-card:hover { border-color: var(--primary); transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0,0,0,0.1); }
    .curriculum-card h2 { font-size: 1.5rem; color: var(--primary); margin-bottom: 0.5rem; }
    .curriculum-card p { color: var(--text-muted); }
    .badge { background: #e8f4fd; color: var(--primary); padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.75rem; }
    footer { text-align: center; padding: 2rem; color: var(--text-muted); }
    footer a { color: var(--primary); }
  </style>
</head>
<body>
  <header>
    <h1>Curricula Opus</h1>
    <p>Open Language Learning Curricula</p>
  </header>
  <main>
    <div class="curriculum-grid">
      ${curricula.map(c => `<a href="${c.langPair}/index.html" class="curriculum-card">
        <h2>${c.name}</h2>
        <p>For English Speakers</p>
        <p style="margin-top: 1rem;">${c.levels.map(l => `<span class="badge">${l.level}</span> ${l.count} modules`).join(' ')}</p>
      </a>`).join('\n      ')}
    </div>
  </main>
  <footer>
    <p>Open source curriculum - <a href="https://github.com/krisztiankoos/curricula-opus">GitHub</a></p>
  </footer>
</body>
</html>`;
}

// ============================================================================
// MAIN
// ============================================================================

async function main() {
  const args = process.argv.slice(2);
  const targetLangPair = args[0];
  // Target can be: level (e.g., "a1"), or level + module num (e.g., "a1 5")
  const targetLevel = args[1]?.toLowerCase();
  const targetModuleNum = args[2] ? parseInt(args[2], 10) : null;

  console.log('\n🚀 Curricula-Opus Generator (Refactored)\n');
  console.log('Source: curriculum/[lang]/[level]/*.md');
  console.log('Output: output/json/ + output/html/\n');

  const langPairs = targetLangPair
    ? [targetLangPair]
    : (await readdir(CURRICULUM_DIR)).filter(f => f.startsWith('l'));

  const allCurricula: { langPair: string; name: string; levels: { level: string; count: number }[] }[] = [];

  for (const langPair of langPairs) {
    console.log(`📚 Processing ${langPair}...`);

    const langDir = join(CURRICULUM_DIR, langPair);
    if (!existsSync(langDir)) {
      console.log(`  ⚠ Language directory not found, skipping...`);
      continue;
    }

    // Find level folders (a1, a2, a2+, b1, etc.)
    const allEntries = await readdir(langDir, { withFileTypes: true });
    const levelFolders = allEntries
      .filter(e => e.isDirectory() && LEVEL_FOLDERS.includes(e.name))
      .map(e => e.name)
      .sort((a, b) => LEVEL_FOLDERS.indexOf(a) - LEVEL_FOLDERS.indexOf(b));

    if (levelFolders.length === 0) {
      console.log(`  ⚠ No level folders found, skipping...`);
      continue;
    }

    const imageMap = await loadImageLookupMap(langPair);
    if (imageMap.size > 0) {
      console.log(`  📷 Loaded ${imageMap.size} image URLs from vocabulary.csv`);
    }

    // Process each level folder
    const modules: ModuleInfo[] = [];
    const navInfo: Map<string, { level: string; num: number; title: string; subtitle?: string; phase: string; duration?: number }[]> = new Map();

    for (const levelFolder of levelFolders) {
      // Skip if targeting a specific level
      if (targetLevel && levelFolder !== targetLevel) continue;

      const levelDir = join(langDir, levelFolder);
      const level = levelFolderToDisplay(levelFolder);

      const mdFiles = (await readdir(levelDir))
        .filter(f => f.match(/^\d{2}-.*\.md$/) || f.match(/^module-\d+\.md$/))  // Match: 01-slug.md OR module-01.md
        .sort();

      console.log(`\n  📁 Level ${level} (${mdFiles.length} modules)`);

      // Initialize nav info for this level
      navInfo.set(level, []);

      for (const mdFile of mdFiles) {
        // Extract module number from filename: "01-slug.md" -> 1 OR "module-01.md" -> 1
        const moduleNum = parseInt(mdFile.match(/^(\d{2})-/)?.[1] || mdFile.match(/^module-(\d+)/)?.[1] || '0', 10);

        try {
          const mdPath = join(levelDir, mdFile);
          const mdContent = await readFile(mdPath, 'utf-8');

          // Quick frontmatter extraction for navigation AND index
          const fmMatch = mdContent.match(/^---\n([\s\S]*?)\n---/);
          const titleMatch = fmMatch?.[1].match(/^title:\s*["']?(.+?)["']?\s*$/m);
          const subtitleMatch = fmMatch?.[1].match(/^subtitle:\s*["']?(.+?)["']?\s*$/m);
          const phaseMatch = fmMatch?.[1].match(/^phase:\s*["']?(.+?)["']?\s*$/m);
          const durationMatch = fmMatch?.[1].match(/^duration:\s*(\d+)/m);

          const title = titleMatch?.[1] || mdFile.replace(/^\d+-/, '').replace('.md', '');
          const subtitle = subtitleMatch?.[1];
          const phase = phaseMatch?.[1] || 'A1.1'; // Default fallback
          const duration = durationMatch ? parseInt(durationMatch[1], 10) : 45;

          const meta = { level, num: moduleNum, title, subtitle, phase, duration };

          // Add to navInfo (used for Prev/Next)
          navInfo.get(level)!.push(meta);

          // If targeting a single module, only fully parse that one
          if (targetModuleNum && moduleNum !== targetModuleNum) continue;

          const parsed = parseModule(mdContent, { languagePair: langPair, imageMap });

          // Inject level and module number from path (not frontmatter)
          parsed.frontmatter.level = level as typeof parsed.frontmatter.level;
          parsed.frontmatter.module = moduleNum;

          const vibeCtx: RenderContext = {
            moduleNum: moduleNum,
            level: level,
            languagePair: langPair,
          };
          const vibeJSON = renderVibeJson(parsed, vibeCtx);

          modules.push({
            ...meta,
            parsed,
            vibeJSON,
          });
        } catch (error) {
          console.error(`  ⚠ Error parsing ${levelFolder}/${mdFile}:`, error);
        }
      }
    }

    // Group modules by level
    const modulesByLevel = new Map<string, ModuleInfo[]>();
    for (const mod of modules) {
      const levelMods = modulesByLevel.get(mod.level) || [];
      levelMods.push(mod);
      modulesByLevel.set(mod.level, levelMods);
    }

    // Build sorted list of modules in same level for navigation
    const getNavNeighbors = (moduleNum: number, level: string) => {
      // Get all modules in the same level, sorted by number
      const levelModules = navInfo.get(level) || [];
      const sorted = [...levelModules].sort((a, b) => a.num - b.num);

      const idx = sorted.findIndex(m => m.num === moduleNum);
      const prevEntry = idx > 0 ? sorted[idx - 1] : undefined;
      const nextEntry = idx < sorted.length - 1 ? sorted[idx + 1] : undefined;

      return {
        prev: prevEntry ? { num: prevEntry.num, title: prevEntry.title } : undefined,
        next: nextEntry ? { num: nextEntry.num, title: nextEntry.title } : undefined,
      };
    };

    // Second pass: generate files with navigation
    for (const [level, levelModules] of modulesByLevel) {
      const levelLower = level.toLowerCase();
      levelModules.sort((a, b) => a.num - b.num);

      console.log(`\n  📁 Level ${level} (${levelModules.length} modules processed)`);

      for (let i = 0; i < levelModules.length; i++) {
        const mod = levelModules[i];
        const { prev: prevMod, next: nextMod } = getNavNeighbors(mod.num, level);

        console.log(`    📦 Module ${padNumber(mod.num)}: ${mod.title}`);

        // Generate Vibe JSON
        await writeJSON(
          join(OUTPUT_DIR, 'json', langPair, levelLower, `module-${padNumber(mod.num)}.json`),
          mod.vibeJSON
        );

        // Generate HTML with navigation
        const ctx: RenderContext = {
          moduleNum: mod.num,
          level,
          languagePair: langPair,
          prevModule: prevMod ? { num: prevMod.num, title: prevMod.title } : undefined,
          nextModule: nextMod ? { num: nextMod.num, title: nextMod.title } : undefined,
        };

        const html = await renderHtml(mod.parsed, ctx);
        await writeHTML(
          join(OUTPUT_DIR, 'html', langPair, levelLower, `module-${padNumber(mod.num)}.html`),
          html
        );
      }

      // Generate Level Index ALWAYS (using light metadata from navInfo)
      // This ensures the index is updated even if we only re-generated one module
      const allLevelModules = navInfo.get(level) || [];
      allLevelModules.sort((a, b) => a.num - b.num);

      const levelIndex = generateLevelIndex(
        allLevelModules,
        level,
        langPair
      );
      await writeHTML(join(OUTPUT_DIR, 'html', langPair, levelLower, 'index.html'), levelIndex);
    }

    // Generate curriculum index (scan ALL levels, not just processed ones)
    if (!targetModuleNum) {
      // Scan all level folders to get accurate counts for curriculum index
      const allLevelCounts: { level: string; moduleCount: number }[] = [];
      for (const levelFolder of levelFolders) {
        const levelDir = join(langDir, levelFolder);
        const level = levelFolderToDisplay(levelFolder);
        const mdFiles = (await readdir(levelDir)).filter(f => f.match(/^\d{2}-.*\.md$/) || f.match(/^module-\d+\.md$/));
        if (mdFiles.length > 0) {
          allLevelCounts.push({ level, moduleCount: mdFiles.length });
        }
      }
      allLevelCounts.sort((a, b) => a.level.localeCompare(b.level));

      if (allLevelCounts.length > 0) {
        const curriculumIndex = generateCurriculumIndex(allLevelCounts, langPair);
        await writeHTML(join(OUTPUT_DIR, 'html', langPair, 'index.html'), curriculumIndex);

        const langName = langPair === 'l2-uk-en' ? 'Ukrainian (for English Speakers)' : langPair;
        allCurricula.push({
          langPair,
          name: langName,
          levels: allLevelCounts.map(l => ({ level: l.level, count: l.moduleCount }))
        });
      }
    }
  }

  // Generate root index
  if (!targetModuleNum && allCurricula.length > 0) {
    const rootIndex = generateRootIndex(allCurricula);
    await writeHTML(join(OUTPUT_DIR, 'html', 'index.html'), rootIndex);
  }

  console.log('\n✅ Generation complete!\n');
}

main().catch(console.error);
