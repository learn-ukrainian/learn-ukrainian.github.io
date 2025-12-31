/**
 * File I/O utilities for learn-ukrainian generator
 *
 * Provides:
 * - Async file operations with error handling
 * - JSON read/write helpers
 * - Module file discovery
 * - Project path utilities
 */

import { readFile, writeFile, mkdir, readdir, stat } from 'fs/promises';
import { existsSync } from 'fs';
import { join, dirname, basename, extname } from 'path';

// =============================================================================
// Project Paths
// =============================================================================

/**
 * Get project root directory
 * Assumes we're running from project root or scripts/
 */
export function getProjectRoot(): string {
  // When running via ts-node from project root
  return process.cwd();
}

/**
 * Get curriculum directory for a language pair
 */
export function getCurriculumDir(languagePair: string): string {
  return join(getProjectRoot(), 'curriculum', languagePair);
}

/**
 * Get modules directory for a language pair
 */
export function getModulesDir(languagePair: string): string {
  return join(getCurriculumDir(languagePair), 'modules');
}

/**
 * Get output directory for a specific format and language pair
 */
export function getOutputDir(format: 'json' | 'html' | 'markdown', languagePair: string): string {
  return join(getProjectRoot(), 'output', format, languagePair);
}

/**
 * Get assets directory
 */
export function getAssetsDir(): string {
  return join(getProjectRoot(), 'scripts', 'assets');
}

// =============================================================================
// Basic File Operations
// =============================================================================

/**
 * Read a text file with error handling
 */
export async function readTextFile(filePath: string): Promise<string> {
  try {
    return await readFile(filePath, 'utf-8');
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === 'ENOENT') {
      throw new Error(`File not found: ${filePath}`);
    }
    throw error;
  }
}

/**
 * Write a text file, creating parent directories if needed
 */
export async function writeTextFile(filePath: string, content: string): Promise<void> {
  await ensureDir(dirname(filePath));
  await writeFile(filePath, content, 'utf-8');
}

/**
 * Read and parse a JSON file
 */
export async function readJsonFile<T = unknown>(filePath: string): Promise<T> {
  const content = await readTextFile(filePath);
  try {
    return JSON.parse(content) as T;
  } catch (error) {
    throw new Error(`Invalid JSON in ${filePath}: ${(error as Error).message}`);
  }
}

/**
 * Write a JSON file with pretty formatting
 */
export async function writeJsonFile(filePath: string, data: unknown, indent = 2): Promise<void> {
  const content = JSON.stringify(data, null, indent);
  await writeTextFile(filePath, content + '\n');
}

/**
 * Check if a file or directory exists
 */
export function fileExists(filePath: string): boolean {
  return existsSync(filePath);
}

/**
 * Ensure a directory exists, creating it if necessary
 */
export async function ensureDir(dirPath: string): Promise<void> {
  if (!existsSync(dirPath)) {
    await mkdir(dirPath, { recursive: true });
  }
}

// =============================================================================
// Module File Discovery
// =============================================================================

export interface ModuleFile {
  path: string;
  filename: string;
  moduleNum: number;
}

/**
 * Find all module markdown files for a language pair
 * Returns sorted by module number
 */
export async function findModuleFiles(languagePair: string): Promise<ModuleFile[]> {
  const curriculumDir = getCurriculumDir(languagePair);

  if (!fileExists(curriculumDir)) {
    return [];
  }

  const moduleFiles: ModuleFile[] = [];
  const levels = ['a1', 'a2', 'b1', 'b2', 'c1', 'c2']; // Standard levels

  // Helper to process a directory
  const processDir = async (dirPath: string) => {
    if (!fileExists(dirPath)) return;

    const files = await readdir(dirPath);
    for (const filename of files) {
      // Match standard format: 01-slug.md or legacy module-01.md
      const match = filename.match(/^(\d+)-.*\.md$/) || filename.match(/^module-(\d+)\.md$/);

      if (match) {
        moduleFiles.push({
          path: join(dirPath, filename),
          filename,
          moduleNum: parseInt(match[1], 10),
        });
      }
    }
  };

  // 1. Scan level directories (Preferred)
  for (const level of levels) {
    await processDir(join(curriculumDir, level));
  }

  // 2. Scan legacy modules/ directory (Fallback)
  await processDir(join(curriculumDir, 'modules'));

  // Sort by module number
  return moduleFiles.sort((a, b) => a.moduleNum - b.moduleNum);
}

/**
 * Get path to a specific module file
 * Scans directories to find the file
 */
export function getModulePath(languagePair: string, moduleNum: number): string {
  const curriculumDir = getCurriculumDir(languagePair);
  const levels = ['a1', 'a2', 'b1', 'b2', 'c1', 'c2'];
  const numStr = moduleNum.toString().padStart(2, '0');

  // 1. Search in level directories
  for (const level of levels) {
    const levelDir = join(curriculumDir, level);
    if (existsSync(levelDir)) {
      // synchronous scan needed here as this function is sync? 
      // Wait, the original function was sync but readdir is async context. 
      // But getModulePath signature returns string directly, implying sync existence check.
      // We'll iterate common patterns.

      try {
        const files = require('fs').readdirSync(levelDir);
        for (const file of files) {
          const match = file.match(/^(\d+)-.*\.md$/) || file.match(/^module-(\d+)\.md$/);
          if (match && parseInt(match[1], 10) === moduleNum) {
            return join(levelDir, file);
          }
        }
      } catch (e) {
        // Ignore invalid dirs
      }
    }
  }

  // 2. Fallback to constructed distinct paths (Legacy)
  const legacyPath = join(curriculumDir, 'modules', `module-${moduleNum}.md`);
  if (existsSync(legacyPath)) return legacyPath;

  // Return a theoretical path if not found (defaulting to A1 or flat)
  return legacyPath;
}

/**
 * Get module number from a file path
 */
export function getModuleNumFromPath(filePath: string): number | null {
  const filename = basename(filePath);
  const match = filename.match(/^(\d+)-.*\.md$/) || filename.match(/^module-(\d+)\.md$/);
  return match ? parseInt(match[1], 10) : null;
}

// =============================================================================
// Output Paths
// =============================================================================

/**
 * Get CEFR level from module number
 */
export function getLevelFromModuleNum(moduleNum: number): string {
  if (moduleNum <= 30) return 'a1';
  if (moduleNum <= 60) return 'a2';
  if (moduleNum <= 80) return 'a2+';
  if (moduleNum <= 120) return 'b1';
  if (moduleNum <= 160) return 'b1+';
  if (moduleNum <= 235) return 'b2';
  if (moduleNum <= 310) return 'b2+';
  return 'c1';
}

/**
 * Get output path for a module's HTML file
 */
export function getHtmlOutputPath(languagePair: string, moduleNum: number): string {
  const level = getLevelFromModuleNum(moduleNum);
  return join(getOutputDir('html', languagePair), level, `module-${moduleNum}.html`);
}

/**
 * Get output path for a module's JSON file
 */
export function getJsonOutputPath(languagePair: string, moduleNum: number): string {
  const level = getLevelFromModuleNum(moduleNum);
  return join(getOutputDir('json', languagePair), level, `module-${moduleNum}.json`);
}

// =============================================================================
// Asset Loading
// =============================================================================

/**
 * Load and concatenate CSS files from assets directory
 */
export async function loadStyleAssets(filenames: string[]): Promise<string> {
  const assetsDir = getAssetsDir();
  const contents: string[] = [];

  for (const filename of filenames) {
    const path = join(assetsDir, 'styles', filename);
    if (fileExists(path)) {
      contents.push(await readTextFile(path));
    }
  }

  return contents.join('\n\n');
}

/**
 * Load and concatenate JS files from assets directory
 */
export async function loadScriptAssets(filenames: string[]): Promise<string> {
  const assetsDir = getAssetsDir();
  const contents: string[] = [];

  for (const filename of filenames) {
    const path = join(assetsDir, 'scripts', filename);
    if (fileExists(path)) {
      contents.push(await readTextFile(path));
    }
  }

  return contents.join('\n\n');
}

// =============================================================================
// Batch Operations
// =============================================================================

export interface FileOperation {
  path: string;
  content: string;
}

/**
 * Write multiple files in parallel
 */
export async function writeFiles(operations: FileOperation[]): Promise<void> {
  await Promise.all(
    operations.map(op => writeTextFile(op.path, op.content))
  );
}

/**
 * Read multiple files in parallel
 */
export async function readFiles(paths: string[]): Promise<Map<string, string>> {
  const results = new Map<string, string>();
  const contents = await Promise.all(
    paths.map(async path => {
      try {
        return { path, content: await readTextFile(path), error: null };
      } catch (error) {
        return { path, content: '', error };
      }
    })
  );

  for (const { path, content, error } of contents) {
    if (!error) {
      results.set(path, content);
    }
  }

  return results;
}

// =============================================================================
// File Listing
// =============================================================================

/**
 * List files in a directory with optional extension filter
 */
export async function listFiles(dirPath: string, extension?: string): Promise<string[]> {
  if (!fileExists(dirPath)) {
    return [];
  }

  const entries = await readdir(dirPath, { withFileTypes: true });
  let files = entries
    .filter(e => e.isFile())
    .map(e => join(dirPath, e.name));

  if (extension) {
    const ext = extension.startsWith('.') ? extension : `.${extension}`;
    files = files.filter(f => extname(f) === ext);
  }

  return files;
}

/**
 * List subdirectories in a directory
 */
export async function listDirs(dirPath: string): Promise<string[]> {
  if (!fileExists(dirPath)) {
    return [];
  }

  const entries = await readdir(dirPath, { withFileTypes: true });
  return entries
    .filter(e => e.isDirectory())
    .map(e => join(dirPath, e.name));
}
