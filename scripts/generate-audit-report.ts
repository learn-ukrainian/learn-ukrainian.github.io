
import { auditModule } from './module-audit';
import { getVocabDatabase } from './lib/vocab-sqlite';
import * as fs from 'fs';
import * as path from 'path';

async function loadVocabDb() {
    const dbPath = path.join(process.cwd(), 'curriculum', 'l2-uk-en');
    return getVocabDatabase(dbPath);
}

async function generateReport(modulePath: string, outputDir: string) {
    const vocabDb = await loadVocabDb();
    const result = auditModule(modulePath, vocabDb);

    const reportPath = path.join(outputDir, `${path.basename(modulePath, '.md')}.audit.md`);
    const date = new Date().toISOString();

    const issues = result.issues;
    const errors = issues.filter(i => i.type === 'error');
    const warnings = issues.filter(i => i.type === 'warning');
    const infos = issues.filter(i => i.type === 'info');

    const isClean = errors.length === 0 && warnings.length === 0;
    const statusEmoji = isClean ? '✅' : (errors.length > 0 ? '❌' : '⚠️');

    const reportContent = `---
module: ${result.module}
type: audit
date: ${date}
status: ${isClean ? 'pass' : 'fail'}
---

# Audit Report: ${result.title}

**Status:** ${statusEmoji} ${isClean ? 'PASSED' : 'NEEDS REVIEW'}
**Level:** ${result.level}
**File:** \`${path.basename(modulePath)}\`

## 📊 Statistics

| Metric | Count | Target | Status |
|--------|-------|--------|--------|
| **Activities** | ${result.stats.activities} | 8+ | ${result.stats.activities >= 8 ? '✅' : '❌'} |
| **Vocab Count** | ${result.stats.vocabCount} | ~25 | ${result.stats.vocabCount >= 18 && result.stats.vocabCount <= 35 ? '✅' : '⚠️'} |
| **Word Count** | ${result.stats.wordCount} | ${result.stats.targetWordCount}+ | ${result.stats.wordCount >= result.stats.targetWordCount ? '✅' : '⚠️'} |
| **Engagement** | ${result.stats.engagementBoxes} | 2+ | ${result.stats.engagementBoxes >= 2 ? '✅' : '⚠️'} |

## 🔍 Detailed Verification

### 1. Structural Integrity
- [x] Frontmatter (Title, Phase, Duration, Tags)
- [${result.stats.hasSummary ? 'x' : ' '}] Summary Section
- [${result.stats.hasVocabSection ? 'x' : ' '}] Vocabulary Table (Markdown format)

### 2. Activity Quality
**Total Activities:** ${result.stats.activities}

| Activity Type | Count |
|---------------|-------|
${Object.entries(result.stats.activityTypes.reduce((acc: any, type) => { acc[type] = (acc[type] || 0) + 1; return acc; }, {})).map(([type, count]) => `| ${type} | ${count} |`).join('\n')}

> **Note:** A1 modules require 8+ activities with 12+ items each.

### 3. Linguistic Purity (Surzhyk Check)
${issues.filter(i => i.category === 'linguistic-purity').length === 0
            ? '- ✅ **No Surzhyk detected.** Anti-Russification Shield active.'
            : '- ❌ **Surzhyk Detected:**\n' + issues.filter(i => i.category === 'linguistic-purity').map(i => `  - ${i.context} (Line ${i.line}) -> ${i.message}`).join('\n')}

### 4. Vocabulary Hygiene
${result.stats.vocabDuplicates.length === 0
            ? '- ✅ **Unique Vocabulary.** No duplicates from previous modules.'
            : '- ⚠️ **Duplicates Detected:**\n' + result.stats.vocabDuplicates.map(w => `  - ${w}`).join('\n')}

## 🛑 Issues & Warnings

${issues.length === 0 ? 'No issues found. Excellent work! 🎉' : ''}

${errors.length > 0 ? '### ❌ Errors (Must Fix)\n' + errors.map(i => `- **${i.category}:** ${i.message} (Line ${i.line})`).join('\n') : ''}

${warnings.length > 0 ? '### ⚠️ Warnings (Should Fix)\n' + warnings.map(i => `- **${i.category}:** ${i.message} (Line ${i.line})`).join('\n') : ''}

${infos.length > 0 ? '### ℹ️ Info (Suggestions)\n' + infos.map(i => `- **${i.category}:** ${i.message} (Line ${i.line})`).join('\n') : ''}
`;

    fs.writeFileSync(reportPath, reportContent);
    console.log(`Generated report: ${reportPath}`);
}

const targetModule = process.argv[2];
const outputDir = process.argv[3];

if (!targetModule || !outputDir) {
    console.error('Usage: npx ts-node scripts/generate-audit-report.ts <module-path> <output-dir>');
    process.exit(1);
}

generateReport(targetModule, outputDir).catch(console.error);
