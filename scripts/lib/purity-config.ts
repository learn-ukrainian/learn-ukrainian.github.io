import * as fs from 'fs';
import * as path from 'path';

/**
 * Purity Config - Dynamic Parser
 * 
 * Parses `docs/l2-uk-en/LINGUISTIC-PURITY-GUIDE.md` to extract
 * forbidden Surzhyk patterns. This ensures the Markdown guide 
 * remains the Single Source of Truth.
 */

export interface ForbiddenPattern {
    regex: RegExp;
    label: string;
    correction: string;
    context?: string;
}

export function loadPurityConfig(docsPath: string = 'docs/l2-uk-en/LINGUISTIC-PURITY-GUIDE.md'): ForbiddenPattern[] {
    try {
        const fullPath = path.resolve(process.cwd(), docsPath);
        if (!fs.existsSync(fullPath)) {
            console.warn(`Purity guide not found at: ${fullPath}`);
            return getFallbackPatterns();
        }

        const content = fs.readFileSync(fullPath, 'utf8');
        const patterns: ForbiddenPattern[] = [];

        // Extract the table from "Mandatory Surzhyk Corrections" section
        const tableMatch = content.match(/#### Mandatory Surzhyk Corrections\n\n([\s\S]*?)(?=\n###|\n##|$)/);

        if (tableMatch) {
            const tableRows = tableMatch[1].split('\n').filter(line => line.trim().startsWith('|') && !line.includes('---'));

            for (const row of tableRows) {
                // | **Term** | **Correction** | Note |
                const cells = row.split('|').map(c => c.trim()).filter(c => c);
                if (cells.length < 2) continue;

                // Skip header row
                if (cells[0].toLowerCase().includes('calque') || cells[0].toLowerCase().includes('surzhyk')) continue;

                const prohibitedTerm = cells[0].replace(/\*\*/g, '').replace(/\[.*?\]/g, '').trim();
                const correction = cells[1].replace(/\*\*/g, '').trim();
                const note = cells[2] ? cells[2].trim() : '';

                // Clean up term (remove parens explanations like "(door/book)")
                const cleanTerm = prohibitedTerm.replace(/\(.*?\)/g, '').trim();

                if (cleanTerm) {
                    patterns.push({
                        // Create case-insensitive regex, handle potential word boundaries if it's a single word
                        regex: new RegExp(cleanTerm.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'i'),
                        label: cleanTerm,
                        correction: correction,
                        context: note
                    });
                }
            }
        }

        if (patterns.length === 0) {
            console.warn('No patterns parsed from Purity Guide table. Using fallbacks.');
            return getFallbackPatterns();
        }

        return patterns;

    } catch (error) {
        console.error('Failed to parse Purity Guide:', error);
        return getFallbackPatterns();
    }
}

function getFallbackPatterns(): ForbiddenPattern[] {
    return [
        { regex: /приймати участь/i, label: 'Приймати участь', correction: 'Брати участь' },
        { regex: /самий кращий/i, label: 'Самий кращий', correction: 'Найкращий' },
        { regex: /слідуючий/i, label: 'Слідуючий', correction: 'Наступний' }
    ];
}
