/**
 * HTML Renderer
 *
 * Generates interactive HTML pages from parsed modules
 */

import {
  ParsedModule,
  RenderContext,
  Activity,
  VocabWord,
  Section,
} from '../../types';
import { markdownToHtml } from '../../utils/markdown';
import {
  HtmlTemplate,
  getTemplate,
  renderTopNav,
  renderMainNav,
  NavOptions,
} from './template';

// =============================================================================
// Main HTML Renderer
// =============================================================================

/**
 * Render complete HTML page for a module
 */
export async function renderHtml(
  parsed: ParsedModule,
  ctx: RenderContext
): Promise<string> {
  const template = await getTemplate();
  const { frontmatter, sections, activities, vocabulary } = parsed;

  // Find specific activity types
  const matchActivity = activities.find(a => a.type === 'match-up');
  const quizActivity = activities.find(a => a.type === 'quiz');
  const sortActivity = activities.find(a => a.type === 'group-sort');

  // Build navigation options
  const navOptions: NavOptions = {
    moduleNum: frontmatter.module,
    moduleTitle: frontmatter.title,
    level: frontmatter.level,
    langPair: ctx.languagePair,
    prevModule: ctx.prevModule,
    nextModule: ctx.nextModule,
    hasMatch: !!matchActivity,
    hasQuiz: !!quizActivity,
    hasSort: !!sortActivity,
  };

  // Build page content
  const content = renderMainContent({
    parsed,
    matchActivity,
    quizActivity,
    sortActivity,
    vocabulary,
    sections,
  });

  // Build data scripts (activity data as JSON)
  const dataScripts = renderDataScripts({
    matchActivity,
    quizActivity,
    sortActivity,
    vocabulary,
  });

  // Combine navigation
  const nav = renderTopNav(navOptions) + renderMainNav(navOptions);

  return template.renderPage({
    title: `Module ${padNumber(frontmatter.module)}: ${frontmatter.title} | Ukrainian ${frontmatter.level}`,
    content: `<main>${content}</main><footer>Module ${padNumber(frontmatter.module)} · curricula-opus</footer>`,
    dataScripts,
    nav,
  });
}

// =============================================================================
// Content Renderers
// =============================================================================

interface ContentOptions {
  parsed: ParsedModule;
  matchActivity?: Activity;
  quizActivity?: Activity;
  sortActivity?: Activity;
  vocabulary: VocabWord[];
  sections: Section[];
}

function renderMainContent(options: ContentOptions): string {
  const { parsed, matchActivity, quizActivity, sortActivity, vocabulary, sections } = options;
  const { frontmatter } = parsed;

  // Determine first activity for navigation
  const firstActivity = matchActivity ? 'match' : quizActivity ? 'quiz' : 'vocab';

  // Render lesson section
  const lessonSection = renderLessonSection(parsed, firstActivity);

  // Render activity sections
  const matchSection = matchActivity ? renderMatchSection(matchActivity, quizActivity ? 'quiz' : 'vocab') : '';
  const quizSection = quizActivity ? renderQuizSection(quizActivity, sortActivity ? 'sort' : 'vocab') : '';
  const sortSection = sortActivity ? renderSortSection(sortActivity) : '';

  // Render vocabulary section
  const vocabSection = renderVocabSection(vocabulary);

  return `
    ${lessonSection}
    ${matchSection}
    ${quizSection}
    ${sortSection}
    ${vocabSection}
  `;
}

// =============================================================================
// Section Renderers
// =============================================================================

function renderLessonSection(parsed: ParsedModule, nextSection: string): string {
  const { frontmatter, sections, rawMarkdown } = parsed;
  const isImmersive = isImmersiveLevel(frontmatter.level);

  // Render sections or raw markdown
  let contentHtml = '';
  if (isImmersive && sections.length > 0) {
    // Include all sections except activities, vocabulary, and summary (shown separately)
    contentHtml = sections
      .filter(s => !['activities', 'vocabulary', 'summary'].includes(s.type))
      .map(s => renderSectionCard(s))
      .join('');
    // Add summary at end
    const summarySection = sections.find(s => s.type === 'summary');
    if (summarySection) {
      contentHtml += renderSectionCard(summarySection);
    }
  } else {
    // Convert raw markdown (excluding activities and vocab sections)
    const cleanedMarkdown = cleanMarkdownForLesson(rawMarkdown);
    contentHtml = `<div class="card"><h3>Theory</h3><div class="md-content">${markdownToHtml(cleanedMarkdown)}</div></div>`;
  }

  return `
    <section id="lesson" class="section active">
      <div class="lesson-header">
        <span class="level-badge">${frontmatter.level} · ${frontmatter.phase}</span>
        <h2 style="font-size:2rem;margin:0.5rem 0">${escapeHtml(frontmatter.title)}</h2>
        ${frontmatter.subtitle ? `<p style="color:var(--text-muted)">${escapeHtml(frontmatter.subtitle)}</p>` : ''}
      </div>
      ${contentHtml}
      <div class="btn-group">
        <button class="btn btn-primary" onclick="showSection('${nextSection}')">Start →</button>
      </div>
    </section>
  `;
}

function renderSectionCard(section: Section): string {
  const typeClass = `section-${section.type}`;
  const icon = section.type === 'intro' ? '📖 ' : section.type === 'summary' ? '📋 ' : '';

  return `
    <div class="card ${typeClass}">
      <h3>${icon}${escapeHtml(section.title)}</h3>
      <div class="md-content">${markdownToHtml(section.content)}</div>
    </div>
  `;
}

function renderMatchSection(activity: Activity, nextSection: string): string {
  const pairs = (activity.content as any).pairs || [];

  // Shuffle right column
  const shuffledPairs = [...pairs].sort(() => Math.random() - 0.5);

  return `
    <section id="match" class="section"><div class="card"><h3>${escapeHtml(activity.title)}</h3>
      <div class="score-display"><span class="score"><span id="match-score">0</span>/${pairs.length}</span></div>
      <div class="match-container" id="match-container"><svg class="match-lines" id="match-lines"></svg>
        <div class="match-column" id="match-left">${pairs.map((p: any, i: number) => `<div class="match-item" data-pair="${i}">${p.left}</div>`).join('')}</div>
        <div class="match-column" id="match-right">${shuffledPairs.map((p: any) => {
          const idx = pairs.findIndex((x: any) => x.right === p.right);
          return `<div class="match-item" data-pair="${idx}">${p.right}</div>`;
        }).join('')}</div>
      </div>
      <div class="completion-message" id="match-complete"><h3>Perfect!</h3></div>
      <div class="btn-group"><button class="btn btn-outline" onclick="resetMatch()">Reset</button><button class="btn btn-primary" onclick="showSection('${nextSection}')">Next →</button></div>
    </div></section>`;
}

function renderQuizSection(activity: Activity, nextSection: string): string {
  const questions = (activity.content as any).questions || [];

  return `
    <section id="quiz" class="section"><div class="card"><h3>${escapeHtml(activity.title)}</h3>
      <div class="score-display"><span class="score"><span id="quiz-score">0</span>/${questions.length}</span></div>
      <div id="quiz-container"></div>
      <div class="completion-message" id="quiz-complete"><h3>Complete!</h3></div>
      <div class="btn-group"><button class="btn btn-outline" onclick="resetQuiz()">Reset</button><button class="btn btn-primary" onclick="showSection('${nextSection}')">Next →</button></div>
    </div></section>`;
}

function renderSortSection(activity: Activity): string {
  const groups = (activity.content as any).groups || [];
  const totalItems = groups.reduce((sum: number, g: any) => sum + g.items.length, 0);

  // Group class names for styling
  const groupClasses = ['true-friends', 'false-friends', 'new-letters'];

  return `
    <section id="sort" class="section"><div class="card"><h3>${escapeHtml(activity.title)}</h3>
      <div class="score-display"><span class="score"><span id="sort-score">0</span>/${totalItems}</span></div>
      <div class="sort-pool" id="sort-pool"><div class="sort-items" id="sort-items"></div></div>
      <div class="sort-groups">${groups.map((g: any, i: number) => `<div class="sort-group ${groupClasses[i] || ''}" data-group="${groupClasses[i] || `group-${i}`}"><h4>${g.name.split('(')[0].trim()}</h4><div class="sort-items"></div></div>`).join('')}</div>
      <div class="completion-message" id="sort-complete"><h3>All Sorted!</h3></div>
      <div class="btn-group"><button class="btn btn-outline" onclick="resetSort()">Reset</button><button class="btn btn-primary" onclick="showSection('vocab')">Vocab →</button></div>
    </div></section>`;
}

function renderVocabSection(vocabulary: VocabWord[]): string {
  return `
    <section id="vocab" class="section"><div class="card"><h3>Vocabulary (${vocabulary.length})</h3><div class="vocab-grid" id="vocab-grid"></div></div>
      <div class="btn-group"><button class="btn btn-primary" onclick="showSection('lesson')">← Back</button></div>
    </section>`;
}

// =============================================================================
// Data Scripts
// =============================================================================

interface DataScriptOptions {
  matchActivity?: Activity;
  quizActivity?: Activity;
  sortActivity?: Activity;
  vocabulary: VocabWord[];
}

function renderDataScripts(options: DataScriptOptions): string {
  const { matchActivity, quizActivity, sortActivity, vocabulary } = options;

  const matchPairs = matchActivity ? (matchActivity.content as any).pairs : [];
  const quizQuestions = quizActivity ? (quizActivity.content as any).questions : [];
  const sortGroups = sortActivity ? (sortActivity.content as any).groups : [];

  // Build sort data object
  const sortData: Record<string, string[]> = {};
  const groupClasses = ['true-friends', 'false-friends', 'new-letters'];
  sortGroups.forEach((g: any, i: number) => {
    const key = groupClasses[i] || `group-${i}`;
    sortData[key] = g.items.map((item: any) => typeof item === 'string' ? item : item.text);
  });

  const totalSort = sortGroups.reduce((sum: number, g: any) => sum + g.items.length, 0);

  // Vocab data
  const vocabData = vocabulary.map(v => ({
    uk: v.uk,
    translit: v.translit || '',
    en: v.en,
    note: v.note || '',
  }));

  return `
    const matchPairs = ${JSON.stringify(matchPairs)};
    const quizData = ${JSON.stringify(quizQuestions)};
    const sortData = ${JSON.stringify(sortData)};
    const vocabData = ${JSON.stringify(vocabData)};
    const totalSort = ${totalSort};
  `;
}

// =============================================================================
// Utilities
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

function isImmersiveLevel(level: string): boolean {
  return ['B1', 'B2', 'C1', 'C2'].includes(level);
}

function cleanMarkdownForLesson(markdown: string): string {
  // Remove frontmatter
  let cleaned = markdown.replace(/^---[\s\S]*?---\n/, '');
  // Remove Activities section
  cleaned = cleaned.replace(/# (?:Activities|Вправи)[\s\S]*?(?=\n# |$)/, '');
  // Remove Vocabulary section
  cleaned = cleaned.replace(/# (?:Vocabulary|Словник)[\s\S]*?(?=\n# |$)/, '');
  return cleaned.trim();
}


// =============================================================================
// Exports
// =============================================================================

export { renderHtml as render };
export { getTemplate, HtmlTemplate } from './template';
