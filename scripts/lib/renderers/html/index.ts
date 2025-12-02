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
  const { frontmatter, sections, activities, vocabulary, reviewVocabulary } = parsed;

  // Find specific activity types
  const matchActivity = activities.find(a => a.type === 'match-up');
  const quizActivity = activities.find(a => a.type === 'quiz');
  const sortActivity = activities.find(a => a.type === 'group-sort');
  const fillActivity = activities.find(a => a.type === 'gap-fill' || a.type === 'fill-blank');
  const orderActivity = activities.find(a => a.type === 'order' || a.type === 'unjumble');

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
    hasFill: !!fillActivity,
    hasOrder: !!orderActivity,
  };

  // Build page content
  const content = renderMainContent({
    parsed,
    matchActivity,
    quizActivity,
    sortActivity,
    fillActivity,
    orderActivity,
    vocabulary,
    reviewVocabulary,
    sections,
  });

  // Build data scripts (activity data as JSON)
  const dataScripts = renderDataScripts({
    matchActivity,
    quizActivity,
    sortActivity,
    fillActivity,
    orderActivity,
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
  fillActivity?: Activity;
  orderActivity?: Activity;
  vocabulary: VocabWord[];
  reviewVocabulary: VocabWord[];
  sections: Section[];
}

function renderMainContent(options: ContentOptions): string {
  const { parsed, matchActivity, quizActivity, sortActivity, fillActivity, orderActivity, vocabulary, reviewVocabulary, sections } = options;
  const { frontmatter } = parsed;

  // Determine first activity for navigation
  const firstActivity = matchActivity ? 'match' : quizActivity ? 'quiz' : fillActivity ? 'fill' : 'vocab';

  // Render lesson section
  const lessonSection = renderLessonSection(parsed, firstActivity);

  // Render activity sections - determine next section for each
  const getNextSection = (current: string): string => {
    const order = ['match', 'quiz', 'sort', 'fill', 'order', 'vocab'];
    const hasActivity: Record<string, boolean> = {
      match: !!matchActivity,
      quiz: !!quizActivity,
      sort: !!sortActivity,
      fill: !!fillActivity,
      order: !!orderActivity,
      vocab: true,
    };
    const currentIdx = order.indexOf(current);
    for (let i = currentIdx + 1; i < order.length; i++) {
      if (hasActivity[order[i]]) return order[i];
    }
    return 'vocab';
  };

  const matchSection = matchActivity ? renderMatchSection(matchActivity, getNextSection('match')) : '';
  const quizSection = quizActivity ? renderQuizSection(quizActivity, getNextSection('quiz')) : '';
  const sortSection = sortActivity ? renderSortSection(sortActivity, getNextSection('sort')) : '';
  const fillSection = fillActivity ? renderFillSection(fillActivity, getNextSection('fill')) : '';
  const orderSection = orderActivity ? renderOrderSection(orderActivity, getNextSection('order')) : '';

  // Render vocabulary section (includes both new and review)
  const vocabSection = renderVocabSection(vocabulary, reviewVocabulary);

  return `
    ${lessonSection}
    ${matchSection}
    ${quizSection}
    ${sortSection}
    ${fillSection}
    ${orderSection}
    ${vocabSection}
  `;
}

// =============================================================================
// Section Renderers
// =============================================================================

function renderLessonSection(parsed: ParsedModule, nextSection: string): string {
  const { frontmatter, sections, rawMarkdown } = parsed;

  // Book-style: render all sections faithfully in order (except Activities and Vocabulary tabs)
  // Sections shown in Lesson tab: intro, content, practice, summary
  // Sections shown separately: activities, vocabulary
  const lessonSections = sections.filter(s => !['activities', 'vocabulary'].includes(s.type));

  let contentHtml = '';
  if (lessonSections.length > 0) {
    contentHtml = lessonSections.map(s => renderSectionCard(s)).join('');
  } else {
    // Fallback: convert raw markdown (excluding activities and vocab)
    const cleanedMarkdown = cleanMarkdownForLesson(rawMarkdown);
    contentHtml = `<div class="card"><div class="md-content">${markdownToHtml(cleanedMarkdown)}</div></div>`;
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
        <button class="btn btn-primary" onclick="showSection('${nextSection}')">Activities →</button>
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

function renderSortSection(activity: Activity, nextSection: string): string {
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
      <div class="btn-group"><button class="btn btn-outline" onclick="resetSort()">Reset</button><button class="btn btn-primary" onclick="showSection('${nextSection}')">Next →</button></div>
    </div></section>`;
}

function renderFillSection(activity: Activity, nextSection: string): string {
  const items = (activity.content as any).items || (activity.content as any).blanks || [];
  const text = (activity.content as any).text || '';

  // If it's a gap-fill with text and blanks
  if (text) {
    return `
    <section id="fill" class="section"><div class="card"><h3>${escapeHtml(activity.title)}</h3>
      <div class="score-display"><span class="score"><span id="fill-score">0</span>/${items.length}</span></div>
      <div id="fill-container" class="fill-container"></div>
      <div class="completion-message" id="fill-complete"><h3>Complete!</h3></div>
      <div class="btn-group"><button class="btn btn-outline" onclick="resetFill()">Reset</button><button class="btn btn-primary" onclick="showSection('${nextSection}')">Next →</button></div>
    </div></section>`;
  }

  // Fill-blank items format
  return `
    <section id="fill" class="section"><div class="card"><h3>${escapeHtml(activity.title)}</h3>
      <div class="score-display"><span class="score"><span id="fill-score">0</span>/${items.length}</span></div>
      <div id="fill-container" class="fill-container"></div>
      <div class="completion-message" id="fill-complete"><h3>Complete!</h3></div>
      <div class="btn-group"><button class="btn btn-outline" onclick="resetFill()">Reset</button><button class="btn btn-primary" onclick="showSection('${nextSection}')">Next →</button></div>
    </div></section>`;
}

function renderOrderSection(activity: Activity, nextSection: string): string {
  const items = (activity.content as any).items || [];

  return `
    <section id="order" class="section"><div class="card"><h3>${escapeHtml(activity.title)}</h3>
      <div class="score-display"><span class="score"><span id="order-score">0</span>/${items.length}</span></div>
      <div id="order-container" class="order-container"></div>
      <div class="completion-message" id="order-complete"><h3>Perfect Order!</h3></div>
      <div class="btn-group"><button class="btn btn-outline" onclick="resetOrder()">Reset</button><button class="btn btn-primary" onclick="showSection('${nextSection}')">Next →</button></div>
    </div></section>`;
}

function renderVocabSection(vocabulary: VocabWord[], reviewVocabulary: VocabWord[] = []): string {
  // Render vocabulary as a styled table (book-style)
  const hasTranslit = vocabulary.some(v => v.translit);
  const hasIpa = vocabulary.some(v => v.ipa);
  const hasNote = vocabulary.some(v => v.note);

  const tableRows = vocabulary.map(v => {
    let row = `<tr><td class="vocab-uk">${escapeHtml(v.uk)}</td>`;
    if (hasTranslit) row += `<td class="vocab-translit">${escapeHtml(v.translit || '')}</td>`;
    if (hasIpa) row += `<td class="vocab-ipa">${escapeHtml(v.ipa || '')}</td>`;
    row += `<td class="vocab-en">${escapeHtml(v.en)}</td>`;
    if (hasNote) row += `<td class="vocab-note">${escapeHtml(v.note || '')}</td>`;
    row += '</tr>';
    return row;
  }).join('');

  const headerRow = `<tr>
    <th>Слово</th>
    ${hasTranslit ? '<th>Вимова</th>' : ''}
    ${hasIpa ? '<th>IPA</th>' : ''}
    <th>Переклад</th>
    ${hasNote ? '<th>Примітка</th>' : ''}
  </tr>`;

  // Render review vocabulary section if there are review words
  let reviewSection = '';
  if (reviewVocabulary.length > 0) {
    const reviewRows = reviewVocabulary.map(v => {
      return `<tr><td class="vocab-uk">${escapeHtml(v.uk)}</td><td class="vocab-module">Module ${v.firstModule || '?'}</td></tr>`;
    }).join('');

    reviewSection = `
      <div class="card review-vocab">
        <h3>Повторення (${reviewVocabulary.length})</h3>
        <p class="review-note">Words from earlier modules for review</p>
        <div class="vocab-table-container">
          <table class="vocab-table">
            <thead><tr><th>Слово</th><th>First Module</th></tr></thead>
            <tbody>${reviewRows}</tbody>
          </table>
        </div>
      </div>`;
  }

  const totalWords = vocabulary.length + reviewVocabulary.length;
  const newLabel = reviewVocabulary.length > 0 ? 'Нові слова' : 'Словник';

  return `
    <section id="vocab" class="section">
      <div class="card">
        <h3>${newLabel} (${vocabulary.length})</h3>
        <div class="vocab-table-container">
          <table class="vocab-table">
            <thead>${headerRow}</thead>
            <tbody>${tableRows}</tbody>
          </table>
        </div>
      </div>
      ${reviewSection}
      <div class="btn-group">
        <button class="btn btn-primary" onclick="showSection('lesson')">← Back to Lesson</button>
      </div>
    </section>`;
}

// =============================================================================
// Data Scripts
// =============================================================================

interface DataScriptOptions {
  matchActivity?: Activity;
  quizActivity?: Activity;
  sortActivity?: Activity;
  fillActivity?: Activity;
  orderActivity?: Activity;
  vocabulary: VocabWord[];
}

function renderDataScripts(options: DataScriptOptions): string {
  const { matchActivity, quizActivity, sortActivity, fillActivity, orderActivity, vocabulary } = options;

  const matchPairs = matchActivity ? (matchActivity.content as any).pairs : [];
  const quizQuestions = quizActivity ? (quizActivity.content as any).questions : [];
  const sortGroups = sortActivity ? (sortActivity.content as any).groups : [];

  // Fill data
  const fillData = fillActivity ? {
    items: (fillActivity.content as any).items || [],
    text: (fillActivity.content as any).text || '',
    answers: (fillActivity.content as any).answers || [],
  } : { items: [], text: '', answers: [] };

  // Order/Unjumble data
  let orderData: any = { items: [], correctOrder: [], isUnjumble: false };
  if (orderActivity) {
    const content = orderActivity.content as any;
    if (orderActivity.type === 'unjumble') {
      // Unjumble format: items have words, answer, translation
      orderData = {
        items: (content.items || []).map((item: any) => ({
          words: item.words || [],
          answer: item.answer || '',
          translation: item.translation || '',
        })),
        isUnjumble: true,
      };
    } else {
      // Regular order format: items are strings to reorder
      orderData = {
        items: content.items || [],
        correctOrder: content.correctOrder || [],
        isUnjumble: false,
      };
    }
  }

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
    const fillData = ${JSON.stringify(fillData)};
    const orderData = ${JSON.stringify(orderData)};
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
