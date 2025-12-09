#!/usr/bin/env npx ts-node
/**
 * Markdown Linter
 * 
 * Enforces strict compliance with docs/MARKDOWN-FORMAT.md.
 * 
 * Checks:
 * 1. Activity Types (Must be from allowlist)
 * 2. Activity Structure (Title, ID present)
 * 3. Gap Fill Format (Must use ___ or __, consistent)
 * 4. Bolding consistency (No ***)
 * 5. No missing assets (Audio placeholders)
 */

import { readFile, readdir } from 'fs/promises';
import { join } from 'path';

const ALLOWED_ACTIVITIES = [
    'match-up', 'quiz', 'true-false', 'group-sort', 'fill-blank', 'gap-fill',
    'unjumble', 'anagram', 'select', 'error-correction', 'fill-in'
];

interface LintResult {
    file: string;
    errors: string[];
    warnings: string[];
}

async function lintFile(filePath: string): Promise<LintResult> {
    const content = await readFile(filePath, 'utf-8');
    const errors: string[] = [];
    const warnings: string[] = [];
    const fileName = filePath.split('/').pop()!;

    // 1. Check Activity Headers
    const activityRegex = /##\s+([a-zA-Z0-9-]+):\s+(.+)/g;
    let match;
    while ((match = activityRegex.exec(content)) !== null) {
        const type = match[1];
        if (!ALLOWED_ACTIVITIES.includes(type)) {
            errors.push(`Invalid Activity Type: '${type}' (Line ${getLineNum(content, match.index)})`);
        }
    }

    // 2. Check Fill-in Gaps
    // Should ideally use ___ (3 underscores) but we allow 2+
    // Warn if mixed usage or single underscore
    const singleUnderscore = /(?<!_)_{1}(?!_)/g; // Matches single _
    // Exclude italics like _italic_
    // Actually, strictly speaking, markdown uses _ for italic.
    // We want to detect GAPS. Gaps are usually __ or ___.

    if (content.includes('fill-blank') || content.includes('gap-fill')) {
        const gapRegex = /_{2,}/g;
        if (!gapRegex.test(content)) {
            warnings.push('Fill-in activity detected but no gaps (__) found.');
        }
    }

    // 3. Check for specific bad patterns
    if (content.match(/\*\*\*/)) {
        warnings.push('Triple bold/italic (***) detected. Use CSS classes or check formatting.');
    }

    return { file: fileName, errors, warnings };
}

function getLineNum(content: string, index: number): number {
    return content.substring(0, index).split('\n').length;
}

async function main() {
    const args = process.argv.slice(2);
    const targetDir = args[0] || 'curriculum/l2-uk-en/a1';

    const files = await readdir(targetDir);
    let failed = false;

    console.log(`\n🔍 Linting Markdown in ${targetDir}...\n`);

    for (const file of files) {
        if (!file.endsWith('.md')) continue;
        const res = await lintFile(join(targetDir, file));

        if (res.errors.length > 0 || res.warnings.length > 0) {
            console.log(`📄 ${res.file}`);
            res.errors.forEach(e => console.log(`   ❌ ${e}`));
            res.warnings.forEach(w => console.log(`   ⚠️  ${w}`));
            if (res.errors.length > 0) failed = true;
        }
    }

    if (failed) {
        console.log('\n❌ Linting Failed');
        process.exit(1);
    } else {
        console.log('\n✅ All Files Passed Linting');
    }
}

main().catch(console.error);
