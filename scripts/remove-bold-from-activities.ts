
import * as fs from 'fs';
import * as path from 'path';

const TARGET_DIR = path.resolve(__dirname, '../curriculum/l2-uk-en/a1');

function removeBoldFromActivities() {
    console.log(`Scanning files in ${TARGET_DIR}...\n`);

    const files = fs.readdirSync(TARGET_DIR).filter(f => f.endsWith('.md') && !f.endsWith('.audit.md'));

    for (const file of files) {
        const filePath = path.join(TARGET_DIR, file);
        const content = fs.readFileSync(filePath, 'utf-8');
        const lines = content.split('\n');
        const newLines = [];

        let inActivity = false;
        let activityType = '';
        let hasChanges = false;

        for (const line of lines) {
            // Check for activity header
            const headerMatch = line.match(/^##\s+([\w-]+):/);
            if (headerMatch) {
                activityType = headerMatch[1].toLowerCase();
                inActivity = [
                    'anagram', 'unjumble', 'word-scramble', 'letter-scramble', 'word-order', 'unscramble',
                    'quiz', 'multiple-choice', 'test',
                    'fill-in', 'gap-fill', 'cloze', 'fill-blank',
                    'match-up', 'matching', 'connect',
                    'true-false', 'boolean',
                    'group-sort', 'sorting', 'categories',
                    'transformation', 'transform', 'rewrite'
                ].includes(activityType);
                newLines.push(line);
                continue;
            }

            // If we hit a new section, reset
            if (line.startsWith('#')) {
                inActivity = false;
                activityType = '';
                newLines.push(line);
                continue;
            }

            if (inActivity) {
                // Check if content has bolding (any line inside activity)
                if (line.includes('**')) {
                    const strippedContent = line.replace(/\*\*/g, '');
                    newLines.push(strippedContent);
                    hasChanges = true;
                } else {
                    newLines.push(line);
                }
            } else {
                newLines.push(line);
            }
        }

        if (hasChanges) {
            console.log(`✅ Fixed bolding in ${file}`);
            fs.writeFileSync(filePath, newLines.join('\n'), 'utf-8');
        }
    }

    console.log('\nDone removing bold formatting.');
}

removeBoldFromActivities();
