/**
 * HTML Renderer
 *
 * Generates interactive HTML pages from parsed modules
 * Each activity gets its own tab/section
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
  const { frontmatter, activities, vocabulary, reviewVocabulary } = parsed;

  // Build navigation options - pass all activities
  const navOptions: NavOptions = {
    moduleNum: frontmatter.module,
    moduleTitle: frontmatter.title,
    level: frontmatter.level,
    langPair: ctx.languagePair,
    prevModule: ctx.prevModule,
    nextModule: ctx.nextModule,
    activities: activities,
  };

  // Build page content
  const content = renderMainContent({
    parsed,
    activities,
    vocabulary,
    reviewVocabulary,
  });

  // Build data scripts (activity data as JSON)
  const dataScripts = renderDataScripts({
    activities,
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
  activities: Activity[];
  vocabulary: VocabWord[];
  reviewVocabulary: VocabWord[];
}

function renderMainContent(options: ContentOptions): string {
  const { parsed, activities, vocabulary, reviewVocabulary } = options;

  // Determine first activity for navigation
  const firstActivityId = activities.length > 0 ? `activity-0` : 'vocab';

  // Render lesson section (includes summary at end)
  const lessonSection = renderLessonSection(parsed, firstActivityId);

  // Render each activity as its own section
  // Last activity links directly to vocab (summary is now part of lesson)
  const activitySections = activities.map((activity, index) => {
    const isLast = index === activities.length - 1;
    const nextSection = isLast ? 'vocab' : `activity-${index + 1}`;
    return renderActivitySection(activity, index, nextSection);
  }).join('\n');

  // Render vocabulary section
  const vocabSection = renderVocabSection(vocabulary, reviewVocabulary);

  return `
    ${lessonSection}
    ${activitySections}
    ${vocabSection}
  `;
}

// =============================================================================
// Section Renderers
// =============================================================================

function renderLessonSection(parsed: ParsedModule, nextSection: string): string {
  const { frontmatter, sections, rawMarkdown } = parsed;

  // Exclude activities, vocabulary - summary is now included at end of lesson
  const lessonSections = sections.filter(s => !['activities', 'vocabulary', 'summary'].includes(s.type));
  const summarySection = sections.find(s => s.type === 'summary');

  let contentHtml = '';
  if (lessonSections.length > 0) {
    contentHtml = lessonSections.map(s => renderSectionCard(s)).join('');
  } else {
    const cleanedMarkdown = cleanMarkdownForLesson(rawMarkdown);
    contentHtml = `<div class="card"><div class="md-content">${markdownToHtml(cleanedMarkdown)}</div></div>`;
  }

  // Add summary at the end of lesson content (before Activities button)
  const summaryHtml = summarySection ? renderSectionCard(summarySection) : '';

  return `
    <section id="lesson" class="section active">
      <div class="lesson-header">
        <span class="level-badge">${frontmatter.level} · ${frontmatter.phase}</span>
        <h2 style="font-size:2rem;margin:0.5rem 0">${escapeHtml(frontmatter.title)}</h2>
        ${frontmatter.subtitle ? `<p style="color:var(--text-muted)">${escapeHtml(frontmatter.subtitle)}</p>` : ''}
      </div>
      ${contentHtml}
      ${summaryHtml}
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

/**
 * Render a single activity section
 */
function renderActivitySection(activity: Activity, index: number, nextSection: string): string {
  const sectionId = `activity-${index}`;
  const type = activity.type;

  switch (type) {
    case 'match-up':
      return renderMatchSection(activity, sectionId, nextSection);
    case 'quiz':
      return renderQuizSection(activity, sectionId, nextSection);
    case 'true-false':
      return renderTfSection(activity, sectionId, nextSection);
    case 'group-sort':
      return renderSortSection(activity, sectionId, nextSection);
    case 'fill-blank':
    case 'gap-fill':
      return renderFillSection(activity, sectionId, nextSection);
    case 'unjumble':
    case 'anagram':
      return renderOrderSection(activity, sectionId, nextSection);
    case 'select':
      return renderSelectSection(activity, sectionId, nextSection);
    case 'error-correction':
      return renderErrorCorrectionSection(activity, sectionId, nextSection);
    default:
      // Generic fallback for unknown types
      return renderGenericSection(activity, sectionId, nextSection);
  }
}

function renderMatchSection(activity: Activity, sectionId: string, nextSection: string): string {
  const pairs = (activity.content as any).pairs || [];

  return `
    <section id="${sectionId}" class="section"><div class="card"><h3>${escapeHtml(activity.title)}</h3>
      <div class="score-display"><span class="score"><span id="${sectionId}-score">0</span>/${pairs.length}</span></div>
      <div class="match-container" id="${sectionId}-container"><svg class="match-lines" id="${sectionId}-lines"></svg>
        <div class="match-column" id="${sectionId}-left"></div>
        <div class="match-column" id="${sectionId}-right"></div>
      </div>
      <div class="completion-message" id="${sectionId}-complete"><h3>Perfect!</h3></div>
      <div class="btn-group"><button class="btn btn-outline" onclick="resetActivity('${sectionId}')">Reset</button><button class="btn btn-primary" onclick="showSection('${nextSection}')">Next →</button></div>
    </div></section>`;
}

function renderQuizSection(activity: Activity, sectionId: string, nextSection: string): string {
  const questions = (activity.content as any).questions || [];

  return `
    <section id="${sectionId}" class="section"><div class="card"><h3>${escapeHtml(activity.title)}</h3>
      <div class="score-display"><span class="score"><span id="${sectionId}-score">0</span>/${questions.length}</span></div>
      <div id="${sectionId}-container"></div>
      <div class="completion-message" id="${sectionId}-complete"><h3>Complete!</h3></div>
      <div class="btn-group"><button class="btn btn-outline" onclick="resetActivity('${sectionId}')">Reset</button><button class="btn btn-primary" onclick="showSection('${nextSection}')">Next →</button></div>
    </div></section>`;
}

function renderTfSection(activity: Activity, sectionId: string, nextSection: string): string {
  const statements = (activity.content as any).statements || [];

  return `
    <section id="${sectionId}" class="section"><div class="card"><h3>${escapeHtml(activity.title)}</h3>
      <div class="score-display"><span class="score"><span id="${sectionId}-score">0</span>/${statements.length}</span></div>
      <div id="${sectionId}-container"></div>
      <div class="completion-message" id="${sectionId}-complete"><h3>Complete!</h3></div>
      <div class="btn-group"><button class="btn btn-outline" onclick="resetActivity('${sectionId}')">Reset</button><button class="btn btn-primary" onclick="showSection('${nextSection}')">Next →</button></div>
    </div></section>`;
}

function renderSortSection(activity: Activity, sectionId: string, nextSection: string): string {
  const groups = (activity.content as any).groups || [];
  const totalItems = groups.reduce((sum: number, g: any) => sum + g.items.length, 0);

  return `
    <section id="${sectionId}" class="section"><div class="card"><h3>${escapeHtml(activity.title)}</h3>
      <div class="score-display"><span class="score"><span id="${sectionId}-score">0</span>/${totalItems}</span></div>
      <div class="sort-pool" id="${sectionId}-pool"><div class="sort-items" id="${sectionId}-items"></div></div>
      <div class="sort-groups" id="${sectionId}-groups"></div>
      <div class="completion-message" id="${sectionId}-complete"><h3>All Sorted!</h3></div>
      <div class="btn-group"><button class="btn btn-outline" onclick="resetActivity('${sectionId}')">Reset</button><button class="btn btn-primary" onclick="showSection('${nextSection}')">Next →</button></div>
    </div></section>`;
}

function renderFillSection(activity: Activity, sectionId: string, nextSection: string): string {
  const items = (activity.content as any).items || [];

  return `
    <section id="${sectionId}" class="section"><div class="card"><h3>${escapeHtml(activity.title)}</h3>
      <div class="score-display"><span class="score"><span id="${sectionId}-score">0</span>/${items.length}</span></div>
      <div id="${sectionId}-container" class="fill-container"></div>
      <div class="completion-message" id="${sectionId}-complete"><h3>Complete!</h3></div>
      <div class="btn-group"><button class="btn btn-outline" onclick="resetActivity('${sectionId}')">Reset</button><button class="btn btn-primary" onclick="showSection('${nextSection}')">Next →</button></div>
    </div></section>`;
}

function renderOrderSection(activity: Activity, sectionId: string, nextSection: string): string {
  const items = (activity.content as any).items || [];

  return `
    <section id="${sectionId}" class="section"><div class="card"><h3>${escapeHtml(activity.title)}</h3>
      <div class="score-display"><span class="score"><span id="${sectionId}-score">0</span>/${items.length}</span></div>
      <div id="${sectionId}-container" class="order-container"></div>
      <div class="completion-message" id="${sectionId}-complete"><h3>Perfect Order!</h3></div>
      <div class="btn-group"><button class="btn btn-outline" onclick="resetActivity('${sectionId}')">Reset</button><button class="btn btn-primary" onclick="showSection('${nextSection}')">Next →</button></div>
    </div></section>`;
}

function renderSelectSection(activity: Activity, sectionId: string, nextSection: string): string {
  const items = (activity.content as any).items || [];

  return `
    <section id="${sectionId}" class="section"><div class="card"><h3>${escapeHtml(activity.title)}</h3>
      <div class="score-display"><span class="score"><span id="${sectionId}-score">0</span>/${items.length}</span></div>
      <div id="${sectionId}-container" class="select-container"></div>
      <div class="completion-message" id="${sectionId}-complete"><h3>Complete!</h3></div>
      <div class="btn-group"><button class="btn btn-outline" onclick="resetActivity('${sectionId}')">Reset</button><button class="btn btn-primary" onclick="showSection('${nextSection}')">Next →</button></div>
    </div></section>`;
}

function renderErrorCorrectionSection(activity: Activity, sectionId: string, nextSection: string): string {
  const items = (activity.content as any).items || [];

  return `
    <section id="${sectionId}" class="section"><div class="card"><h3>${escapeHtml(activity.title)}</h3>
      <div class="score-display"><span class="score"><span id="${sectionId}-score">0</span>/${items.length * 2}</span></div>
      <div id="${sectionId}-container" class="error-correction-container"></div>
      <div class="completion-message" id="${sectionId}-complete"><h3>All Corrected!</h3></div>
      <div class="btn-group"><button class="btn btn-outline" onclick="resetActivity('${sectionId}')">Reset</button><button class="btn btn-primary" onclick="showSection('${nextSection}')">Next →</button></div>
    </div></section>`;
}

function renderGenericSection(activity: Activity, sectionId: string, nextSection: string): string {
  return `
    <section id="${sectionId}" class="section"><div class="card"><h3>${escapeHtml(activity.title)}</h3>
      <p>Activity type: ${activity.type}</p>
      <div class="btn-group"><button class="btn btn-primary" onclick="showSection('${nextSection}')">Next →</button></div>
    </div></section>`;
}

function renderVocabSection(vocabulary: VocabWord[], reviewVocabulary: VocabWord[] = []): string {
  const hasTranslit = vocabulary.some(v => v.translit);
  const hasIpa = vocabulary.some(v => v.ipa);
  const hasNote = vocabulary.some(v => v.note);

  // Helper to render text with audio buttons
  // If textToSpeak is provided, the button will trigger TTS for that text.
  // Otherwise, it falls back to the audio ID (which we are deprecated, but keeping for safety) OR ignores it.
  const renderCell = (text: string, textToSpeak?: string) => {
    // Strategy: Split by audio pattern
    const parts = text.split(/(\[🔊\]\(audio_[^)]+\))/g);
    return parts.map(part => {
      const match = part.match(/^\[🔊\]\((audio_[^)]+)\)$/);
      if (match) {
        // Forvo Strategy: Open popup to Forvo word page
        const text = textToSpeak || 'search'; // Fallback
        return `<button class="audio-btn" onclick="openForvo('${escapeHtml(text)}')" title="Listen on Forvo">🔊</button>`;
      } else {
        return escapeHtml(part);
      }
    }).join('');
  };

  const tableRows = vocabulary.map(v => {
    let row = `<tr><td class="vocab-uk">${renderCell(v.uk, v.uk)}</td>`;
    if (hasTranslit) row += `<td class="vocab-translit">${escapeHtml(v.translit || '')}</td>`;
    if (hasIpa) row += `<td class="vocab-ipa">${escapeHtml(v.ipa || '')}</td>`;
    row += `<td class="vocab-en">${renderCell(v.en)}</td>`;
    // Pass v.uk as the speech target for the note column too, as the audio button is likely there
    if (hasNote) row += `<td class="vocab-note">${renderCell(v.note || '', v.uk)}</td>`;
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
  activities: Activity[];
  vocabulary: VocabWord[];
}

function renderDataScripts(options: DataScriptOptions): string {
  const { activities, vocabulary } = options;

  // Build activities data array - each activity with its data
  const activitiesData = activities.map((activity, index) => {
    const sectionId = `activity-${index}`;
    const type = activity.type;
    const content = activity.content as any;

    return {
      id: sectionId,
      type: type,
      title: activity.title,
      data: content,
    };
  });

  // Vocab data
  const vocabData = vocabulary.map(v => ({
    uk: v.uk,
    translit: v.translit || '',
    en: v.en,
    note: v.note || '',
  }));

  return `
    const activitiesData = ${JSON.stringify(activitiesData)};
    const vocabData = ${JSON.stringify(vocabData)};
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

function cleanMarkdownForLesson(markdown: string): string {
  let cleaned = markdown.replace(/^---[\s\S]*?---\n/, '');
  cleaned = cleaned.replace(/# (?:Activities|Вправи)[\s\S]*?(?=\n# |$)/, '');
  cleaned = cleaned.replace(/# (?:Vocabulary|Словник)[\s\S]*?(?=\n# |$)/, '');
  return cleaned.trim();
}

// =============================================================================
// Exports
// =============================================================================

export { renderHtml as render };
export { getTemplate, HtmlTemplate } from './template';
