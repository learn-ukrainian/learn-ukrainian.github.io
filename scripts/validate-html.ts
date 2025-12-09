#!/usr/bin/env npx ts-node
/// <reference lib="dom" />
/**
 * HTML Validator (Puppeteer-based)
 * 
 * Validates generated HTML files by actually loading them in a headless browser.
 * Checks for:
 * 1. Console Errors (JS parsing/execution issues).
 * 2. Broken Resource Links (Images/Audio 404s).
 * 3. Broken Internal Links (Anchors to missing IDs).
 * 4. Structural Integrity (Title, Main Content).
 */

import { readdir } from 'fs/promises';
import { join, resolve } from 'path';
import { existsSync } from 'fs';
import puppeteer, { Browser, Page } from 'puppeteer';

const OUTPUT_DIR = join(__dirname, '..', 'output', 'html');

export interface ValidationResult {
    file: string;
    passed: boolean;
    errors: string[];
    warnings: string[];
}

export async function validateFile(browser: Browser, filePath: string): Promise<ValidationResult> {
    const errors: string[] = [];
    const warnings: string[] = [];
    const fileName = filePath.split('/').pop() || 'unknown';

    const page = await browser.newPage();

    // Capture console errors
    page.on('console', msg => {
        if (msg.type() === 'error') {
            errors.push(`Console Error: ${msg.text()}`);
        }
    });

    // Capture failed requests (images, CSS, scriptS)
    page.on('requestfailed', req => {
        // Ignore data URLs or analytics if any
        if (req.url().startsWith('file://')) {
            errors.push(`Resource Failed: ${req.url()} (${req.failure()?.errorText})`);
        }
    });

    try {
        // Load file via file:// protocol
        const fileUrl = `file://${resolve(filePath)}`;
        const response = await page.goto(fileUrl, { waitUntil: 'networkidle0' });

        if (!response) {
            errors.push('Failed to load page (no response)');
            return { file: fileName, passed: false, errors, warnings };
        }

        // 1. Check Title
        const title = await page.title();
        if (!title || title.trim() === '') {
            errors.push('Missing or empty <title>');
        }

        // 2. Check Critical Elements
        const hasMain = await page.$('main');
        if (!hasMain) errors.push('Missing <main> element');

        // 3. Check Anchor Links (Internal IDs)
        const anchors = await page.$$eval('a[href^="#"]', els => els.map(e => e.getAttribute('href')));
        for (const anchor of anchors) {
            if (anchor && anchor.length > 1) { // Skip just "#"
                const id = anchor.substring(1);
                const target = await page.$(`#${id}, [name="${id}"]`);
                if (!target) {
                    errors.push(`Broken Anchor: ${anchor} (Target ID not found)`);
                }
            }
        }

        // 4. Check Navigation Links (File existence)
        // Note: This is harder with file://, but we can check if they point to .html files
        const navLinks = await page.$$eval('a[href]:not([href^="#"]):not([href^="http"])', els => els.map(e => e.getAttribute('href')));
        for (const link of navLinks) {
            if (link) {
                // Resolve relative path
                const targetPath = resolve(filePath, '..', link);
                if (!existsSync(targetPath)) {
                    errors.push(`Broken Link: ${link} (File not found)`);
                }
            }
        }

        // 5. Check Audio/Image existence (in case they didn't trigger requestfailed)
        const images = await page.$$eval('img', els => els.map(e => (e as any).naturalWidth));
        const brokenImages = images.filter(w => w === 0);
        if (brokenImages.length > 0) {
            errors.push(`${brokenImages.length} broken images detected (naturalWidth=0)`);
        }

        // 6. Check Planned Layout Sections
        // Note: Activities are separate sections, so we check for 'lesson' and 'vocab' key sections.
        const requiredIds = ['lesson', 'vocab'];
        for (const id of requiredIds) {
            const el = await page.$(`#${id}`);
            if (!el) errors.push(`Missing Layout Section: #${id}`);
        }

        // 7. Check Activity Validity
        // Activities are in sections with id="activity-N"
        const activitySections = await page.$$('section[id^="activity-"]');
        if (activitySections.length < 8) {
            warnings.push(`Low Activity Count: Found ${activitySections.length} (Expected 8+)`);
        }

        // Deep Content Integrity Check
        // We evaluate inside the page to check specific DOM states
        const integrityErrors = await page.evaluate(() => {
            const errors: string[] = [];
            const data = (window as any).activitiesData;
            if (!data || !Array.isArray(data)) {
                return [`CRITICAL: activitiesData missing or invalid on page. Check generate script.`];
            }

            // 1. Validate Data vs DOM Count
            data.forEach((activity: any) => {
                const section = document.getElementById(activity.id);
                if (!section) {
                    errors.push(`Activity #${activity.id}: Section missing in DOM.`);
                    return;
                }

                const container = section.querySelector('[id$="-container"]');

                let expectedCount = 0;
                let actualCount = 0;

                if (activity.type === 'fill-blank' || activity.type === 'gap-fill') {
                    expectedCount = activity.data.items?.length || 0;
                    actualCount = container?.querySelectorAll('.fill-question').length || 0;
                    if (actualCount !== expectedCount) {
                        errors.push(`Activity #${activity.id} (${activity.type}): Count Mismatch. Expected ${expectedCount} items, found ${actualCount}.`);
                    }

                    // Check for Ambiguous Gaps (Multiple gaps for single answer)
                    activity.data.items?.forEach((item: any, i: number) => {
                        const prompt = item.prompt || item.sentence || '';
                        const gapMatches = prompt.match(/_{2,}/g);
                        if (gapMatches && gapMatches.length > 1) {
                            errors.push(`Activity #${activity.id} (Fill-in) Question ${i + 1}: Ambiguous Gaps. Found ${gapMatches.length} gaps but only 1 answer/option set. Remove redundant gaps from prompt.`);
                        }
                    });
                } else if (activity.type === 'anagram') {
                    expectedCount = activity.data.items?.length || 0;
                    actualCount = container?.querySelectorAll('.anagram-question').length || 0;
                    if (actualCount !== expectedCount) {
                        errors.push(`Activity #${activity.id} (${activity.type}): Count Mismatch. Expected ${expectedCount} items, found ${actualCount}.`);
                    }
                }
            });

            // 2. Specific DOM Integrity Checks (Existing logic)
            // Check Fill-in Activities
            document.querySelectorAll('.fill-container').forEach((container: any) => {
                const id = container.closest('section')?.id || 'unknown';
                const questions = container.querySelectorAll('.fill-question');
                if (questions.length === 0 && !errors.some(e => e.includes(id) && e.includes('Count Mismatch'))) {
                    errors.push(`Activity #${id} (Fill-in): No questions rendered. Init failed?`);
                    return;
                }

                // For each question, ensure it has either inputs or selects
                questions.forEach((q: any, idx: number) => {
                    const inputs = q.querySelectorAll('input, select');
                    if (inputs.length === 0) {
                        errors.push(`Activity #${id} (Fill-in) Question ${idx + 1}: Missing interactive gap inputs (Gap likely stripped).`);
                    } else {
                        // Check if select has options
                        const select = q.querySelector('select');
                        if (select && select.options.length <= 1) {
                            errors.push(`Activity #${id} (Fill-in) Question ${idx + 1}: Dropdown has no options (Logic failure).`);
                        }
                    }
                });
            });

            // Check Anagram Activities
            document.querySelectorAll('.anagram-question').forEach((q: any, idx: number) => {
                const id = q.closest('section')?.id || 'unknown';
                const letters = q.querySelectorAll('.anagram-letter');
                if (letters.length <= 1) {
                    errors.push(`Activity #${id} (Anagram) Question ${idx + 1}: Invalid letter count (${letters.length}). Parsing failure?`);
                }
            });

            // Check Unjumble/Order Activities
            document.querySelectorAll('.order-container').forEach((container: any) => {
                const id = container.closest('section')?.id || 'unknown';

                // SKIP if this is actually an Anagram activity (which also uses .order-container)
                if (container.querySelector('.anagram-question')) return;

                // Check if we have items (support both new Unjumble and old Order)
                const items = container.querySelectorAll('.unjumble-word, .order-sentence-card, .order-sentence-item, .order-item');
                if (items.length === 0) {
                    errors.push(`Activity #${id} (Order/Unjumble): No draggable items found.`);
                }
            });

            // Check Match-up
            document.querySelectorAll('.match-container').forEach((container: any) => {
                const id = container.closest('section')?.id || 'unknown';

                const section = container.closest('section');
                if (!section) return;

                const left = section.querySelectorAll('.match-item[data-side="left"]').length;
                const right = section.querySelectorAll('.match-item[data-side="right"]').length;

                if (left === 0 || right === 0) {
                    errors.push(`Activity #${id} (Match-up): Empty or missing items.`);
                } else if (left !== right) {
                    errors.push(`Activity #${id} (Match-up): Unbalanced items (Left: ${left}, Right: ${right}).`);
                }
            });

            // General Interactive Check (Fallback)
            document.querySelectorAll('section[id^="activity-"]').forEach((section: any) => {
                const interactive = section.querySelector('button, input, select, [draggable="true"], .match-item');
                if (!interactive) {
                    errors.push(`Activity #${section.id}: Completely non-interactive (renderer broken).`);
                }
            });

            return errors;
        });

        if (integrityErrors.length > 0) {
            errors.push(...integrityErrors);
        }

        // 8. Check Content Order (High level check)
        // We expect sections order: #lesson -> #activity-0...N -> #vocab
        const sections = await page.$$eval('section[id]', els => els.map(e => e.id));

        const lessonIdx = sections.indexOf('lesson');
        const vocabIdx = sections.indexOf('vocab');

        // Check if activities are between lesson and vocab
        // Actually, in the HTML seen, vocab is after activity-7.
        // Order: lesson, activity-0...7, vocab.

        if (lessonIdx === -1) errors.push('Section Order: #lesson missing');
        if (vocabIdx === -1) errors.push('Section Order: #vocab missing');

        if (lessonIdx > vocabIdx) {
            errors.push('Section Order: #lesson appears after #vocab');
        }

        // Check if any activity appears before lesson or after vocab (strictly speaking vocab is last)
        const firstActivityIdx = sections.findIndex(id => id.startsWith('activity-'));
        if (firstActivityIdx !== -1 && firstActivityIdx < lessonIdx) {
            errors.push('Section Order: Activities appear before Lesson content');
        }

    } catch (err: any) {
        errors.push(`Crash: ${err.message}`);
    } finally {
        await page.close();
    }

    return {
        file: fileName,
        passed: errors.length === 0,
        errors,
        warnings
    };
}

async function main() {
    const args = process.argv.slice(2);
    const targetLang = args[0] || 'l2-uk-en';
    const targetLevel = args[1] || 'a1';

    console.log(`\n🔍 Validating HTML for ${targetLang}/${targetLevel}...\n`);

    const dir = join(OUTPUT_DIR, targetLang, targetLevel);
    if (!existsSync(dir)) {
        console.error(`Directory not found: ${dir}`);
        process.exit(1);
    }

    const files = (await readdir(dir)).filter(f => f.endsWith('.html') && f !== 'index.html');
    if (files.length === 0) {
        console.error('No HTML files found.');
        process.exit(1);
    }

    const browser = await puppeteer.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    const results: ValidationResult[] = [];

    try {
        for (const file of files) {
            process.stdout.write(`  Checking ${file}... `);
            const result = await validateFile(browser, join(dir, file));
            results.push(result);
            console.log(result.passed ? '✅' : '❌');

            if (!result.passed) {
                result.errors.forEach(e => console.log(`    - ${e}`));
            }
        }
    } finally {
        await browser.close();
    }

    const passed = results.filter(r => r.passed).length;
    const failed = results.filter(r => !r.passed).length;

    console.log(`\n📊 Summary: ${passed} Passed, ${failed} Failed`);
    process.exit(failed > 0 ? 1 : 0);
}

if (require.main === module) {
    main().catch(console.error);
}
