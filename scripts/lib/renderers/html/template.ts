/**
 * HTML Template with asset inlining
 *
 * Loads CSS and JS from separate files and inlines them during build
 */

import { loadStyleAssets, loadScriptAssets, fileExists } from '../../utils/files';
import { join } from 'path';
import { Activity } from '../../types';

// =============================================================================
// Template Class
// =============================================================================

export class HtmlTemplate {
  private css: string = '';
  private js: string = '';
  private loaded: boolean = false;

  /**
   * Load and cache assets
   * Call this before rendering
   */
  async loadAssets(): Promise<void> {
    if (this.loaded) return;

    // Load CSS files
    this.css = await loadStyleAssets([
      'base.css',
      'layout.css',
      'activities.css',
    ]);

    // Load JS files
    this.js = await loadScriptAssets([
      'main.js',
      'quiz.js',
      'tf.js',
      'match.js',
      'sort.js',
      'fill.js',
      'order.js',
      'select.js',
      'error-correction.js',
      'vocab.js',
    ]);

    this.loaded = true;
  }

  /**
   * Get inlined CSS
   */
  getStyles(): string {
    return this.css;
  }

  /**
   * Get inlined JS
   */
  getScripts(): string {
    return this.js;
  }

  /**
   * Render complete HTML page
   */
  renderPage(options: PageOptions): string {
    const {
      title,
      content,
      dataScripts = '',
      nav,
    } = options;

    return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${escapeHtml(title)}</title>
  <style>
${this.css}
  </style>
</head>
<body>
  ${nav || ''}
  ${content}
  <script>
${dataScripts}
${this.js}
  </script>
</body>
</html>`;
  }
}

// =============================================================================
// Page Options Interface
// =============================================================================

export interface PageOptions {
  title: string;
  content: string;
  dataScripts?: string;
  nav?: string;
}

// =============================================================================
// Navigation Helpers
// =============================================================================

export interface NavOptions {
  moduleNum: number;
  moduleTitle: string;
  level: string;
  langPair: string;
  prevModule?: { num: number; title: string };
  nextModule?: { num: number; title: string };
  activities: Activity[];
}

/**
 * Generate top navigation bar
 */
export function renderTopNav(options: NavOptions): string {
  const { langPair, level, prevModule, nextModule } = options;

  const prevLink = prevModule
    ? `<a href="module-${padNumber(prevModule.num)}.html" class="module-nav-link">← Module ${padNumber(prevModule.num)}</a>`
    : `<span class="module-nav-link disabled">← Prev</span>`;
  const nextLink = nextModule
    ? `<a href="module-${padNumber(nextModule.num)}.html" class="module-nav-link">Module ${padNumber(nextModule.num)} →</a>`
    : `<span class="module-nav-link disabled">Next →</span>`;

  return `
  <div class="top-nav">
    <a href="../index.html">← ${langPair} Curriculum</a>
    <div class="module-nav">
      ${prevLink}
      <a href="index.html" class="module-nav-link">${level} Index</a>
      ${nextLink}
    </div>
  </div>`;
}

/**
 * Generate main navigation with tabs
 * Each activity gets its own tab
 */
export function renderMainNav(options: NavOptions): string {
  const { moduleNum, moduleTitle, activities } = options;

  // Generate activity tabs dynamically
  const activityTabs = activities.map((activity, index) => {
    const label = getActivityLabel(activity.type, index + 1);
    return `<button class="nav-tab" data-section="activity-${index}">${label}</button>`;
  }).join('\n      ');

  return `
  <nav class="nav">
    <h1>Module ${padNumber(moduleNum)}: ${escapeHtml(moduleTitle)}</h1>
    <div class="nav-tabs">
      <button class="nav-tab active" data-section="lesson">Lesson</button>
      ${activityTabs}
      <button class="nav-tab" data-section="vocab">Vocab</button>
    </div>
  </nav>`;
}

/**
 * Get short label for activity type
 */
function getActivityLabel(type: string, num: number): string {
  const labels: Record<string, string> = {
    'match-up': 'Match',
    'quiz': 'Quiz',
    'true-false': 'T/F',
    'group-sort': 'Sort',
    'fill-blank': 'Fill',
    'gap-fill': 'Fill',
    'fill-in': 'Fill',
    'unjumble': 'Order',
    'anagram': 'Anagram',
    'select': 'Select',
    'error-correction': 'Fix',
  };
  const base = labels[type] || type;
  return `${num}. ${base}`;
}

// =============================================================================
// Utility Functions
// =============================================================================

function escapeHtml(str: string): string {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function padNumber(num: number): string {
  return num.toString().padStart(2, '0');
}

// =============================================================================
// Singleton Instance
// =============================================================================

let templateInstance: HtmlTemplate | null = null;

/**
 * Get or create template instance
 */
export async function getTemplate(): Promise<HtmlTemplate> {
  if (!templateInstance) {
    templateInstance = new HtmlTemplate();
    await templateInstance.loadAssets();
  }
  return templateInstance;
}

// HtmlTemplate is exported above via `export class HtmlTemplate`
