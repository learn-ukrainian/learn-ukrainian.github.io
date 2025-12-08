
import * as fs from 'fs';
import * as path from 'path';

/**
 * STRICT ACTIVITY FORMAT VERIFIER
 * Checks specifically for syntax patterns that break the parser but might pass valid Markdown checks.
 */

const targetDir = path.join(process.cwd(), 'curriculum/l2-uk-en/a1');

interface Violation {
    file: string;
    line: number;
    activity: string;
    issue: string;
    snippet: string;
}

const violations: Violation[] = [];

function checkFile(filePath: string) {
    const content = fs.readFileSync(filePath, 'utf8');
    const lines = content.split('\n');
    const filename = path.basename(filePath);

    let inActivity = false;
    let currentActivityType = '';

    for (let i = 0; i < lines.length; i++) {
        const line = lines[i];

        // Detect Activity Header
        const headerMatch = line.match(/^## (anagram|unjumble|quiz|fill-in|match-up|group-sort|true-false):/i);
        if (headerMatch) {
            inActivity = true;
            currentActivityType = headerMatch[1].toLowerCase();
            continue;
        }

        // Reset on other headers
        if (line.startsWith('## ') && !headerMatch) {
            inActivity = false;
            currentActivityType = '';
            continue;
        }

        if (!inActivity) continue;

        const trimmed = line.trim();
        if (!trimmed) continue;

        // --- ANAGRAM CHECKS ---
        if (currentActivityType === 'anagram') {
            // Valid prompt starts with number.
            if (line.match(/^\d+\./)) {
                // 1. Check for parentheses (hints must be in blockquote)
                if (line.match(/\(.*\)/)) {
                    violations.push({
                        file: filename,
                        line: i + 1,
                        activity: 'ANAGRAM',
                        issue: 'Parentheses detected in prompt line. Move `(Hint)` to blockquote.',
                        snippet: line
                    });
                }
                // 2. Check for slashes
                if (line.includes('/')) {
                    violations.push({
                        file: filename,
                        line: i + 1,
                        activity: 'ANAGRAM',
                        issue: 'Slashes "/" detected in prompt line. Use space separation only.',
                        snippet: line
                    });
                }
            }
        }

        // --- UNJUMBLE CHECKS ---
        if (currentActivityType === 'unjumble') {
            // 1. Check for translation in prompt line (anything in parens on the numbered line)
            if (line.match(/^\d+\./)) {
                if (line.match(/\(.*\)/)) {
                    violations.push({
                        file: filename,
                        line: i + 1,
                        activity: 'UNJUMBLE',
                        issue: 'Translation/Hint detected in prompt line. Move `(Translation)` to blockquote.',
                        snippet: line
                    });
                }
            }
        }

        // --- QUIZ CHECKS ---
        if (currentActivityType === 'quiz' || currentActivityType === 'true-false') {
            // Check for malformed checkboxes like -[x] or - [ x]
            if (line.trim().startsWith('-')) {
                if (line.match(/-\s*\[/)) { // it's a checkbox attempt
                    // Allow indentation at start
                    if (!line.match(/^\s*-\s+\[[ x]\]/)) {
                        violations.push({
                            file: filename,
                            line: i + 1,
                            activity: 'QUIZ/TF',
                            issue: 'Malformed checkbox. Must be `- [ ]` or `- [x]`.',
                            snippet: line
                        });
                    }
                }
            }
        }
    }
}

// MAIN
if (!fs.existsSync(targetDir)) {
    console.error(`Directory not found: ${targetDir}`);
    process.exit(1);
}

const files = fs.readdirSync(targetDir).filter(f => f.endsWith('.md') && !f.endsWith('.audit.md'));

console.log(`Scanning ${files.length} files in ${targetDir}...\n`);

files.forEach(f => checkFile(path.join(targetDir, f)));

if (violations.length > 0) {
    console.log('❌ ISSUES FOUND:');
    violations.forEach(v => {
        console.log(`[${v.file}:${v.line}] ${v.activity}: ${v.issue}`);
        console.log(`   Snippet: ${v.snippet.trim()}`);
    });
    process.exit(1);
} else {
    console.log('✅ All activity formats verified clean.');
}
