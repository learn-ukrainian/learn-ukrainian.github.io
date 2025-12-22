
import { existsSync, readFileSync } from 'fs';
import { join } from 'path';
import { execSync } from 'child_process';

const LEVEL_CONFIG = {
    'A1': { min_vocab: 30, target_words: 750 },
    'A2': { min_vocab: 25, target_words: 1000 },
    'B1': { min_vocab: 35, target_words: 1250 },
    'B2': { min_vocab: 25, target_words: 1500 },
    'C1': { min_vocab: 25, target_words: 1500 },
    'C2': { min_vocab: 25, target_words: 1500 }
};

/**
 *
 */
async function main() {
    const args = process.argv.slice(2);
    const command = args[0];
    const level = args[1]?.toUpperCase();

    if (!command || !level) {
        console.log('Usage: npx ts-node scripts/preflight.ts <level|module> <level_id> [module_num]');
        process.exit(1);
    }

    if (command === 'level') {
        await checkLevel(level);
    } else if (command === 'module') {
        const moduleNum = parseInt(args[2], 10);
        if (isNaN(moduleNum)) {
            console.log('Error: Module number required for module check.');
            process.exit(1);
        }
        await checkModule(level, moduleNum);
    } else {
        console.log(`Unknown command: ${command}`);
    }
}

/**
 *
 */
async function checkLevel(level: string) {
    console.log(`\n✈️  Preflight Check: Level ${level}`);
    let errors = 0;

    // 1. Check Curriculum Plan
    const planPath = `docs/l2-uk-en/${level}-CURRICULUM-PLAN.md`;
    if (existsSync(planPath)) {
        console.log(`✅ Curriculum Plan found: ${planPath}`);
    } else {
        console.log(`❌ MISSING Curriculum Plan: ${planPath}`);
        errors++;
    }

    // 2. Check Audit Config
    if (LEVEL_CONFIG[level as keyof typeof LEVEL_CONFIG]) {
        console.log(`✅ Audit Config exists for ${level}`);
    } else {
        console.log(`❌ MISSING Audit Config for ${level} in script parameters`);
        errors++;
    }

    // 3. Check Guidelines
    const guidelinesPath = `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md`;
    const guidelinesContent = readFileSync(guidelinesPath, 'utf-8');
    if (guidelinesContent.includes(`| **${level}** |`)) {
        console.log(`✅ Guidelines verified for ${level}`);
    } else {
        console.log(`❌ Level ${level} not found in Richness Guidelines table`);
        errors++;
    }

    if (errors === 0) {
        console.log(`\n🎉 Level ${level} is READY for takeoff!`);
    } else {
        console.log(`\n🚫 Level ${level} FAILED preflight checks (${errors} errors).`);
        process.exit(1);
    }
}

/**
 *
 */
async function checkModule(level: string, num: number) {
    console.log(`\n✈️  Preflight Check: Module ${level} ${num}`);
    let errors = 0;

    const paddedNum = num.toString().padStart(2, '0');
    const targetFile = `curriculum/l2-uk-en/${level.toLowerCase()}/module-${paddedNum}.md`;

    // 1. Check if Target Exists (Prevent Overwrite, unless user insists - handled by tool logic usually, but here we enforce check)
    if (existsSync(targetFile)) {
        console.log(`⚠️  Warning: Target file already exists: ${targetFile}`);
    } else {
        console.log(`✅ Target path clear: ${targetFile}`);
    }

    // 2. Check Previous Module (Continuity)
    if (num > 1) {
        const prevNum = (num - 1).toString().padStart(2, '0');
        const prevFile = `curriculum/l2-uk-en/${level.toLowerCase()}/module-${prevNum}.md`;
        if (existsSync(prevFile)) {
            console.log(`✅ Previous module found: ${prevFile}`);
        } else {
            console.log(`❌ MISSING Previous Module: ${prevFile} (Break in continuity!)`);
            errors++;
        }
    }

    // 3. Check Vocabulary DB
    if (existsSync('vocabulary.db')) {
        console.log(`✅ Vocabulary DB connection ready`);
    } else {
        console.log(`❌ MISSING Vocabulary DB (Run vocab-init first)`);
        errors++;
    }

    if (errors === 0) {
        console.log(`\n🎉 Module ${level} ${num} is READY for creation!`);
    } else {
        console.log(`\n🚫 Module ${level} ${num} FAILED preflight checks (${errors} errors).`);
        process.exit(1);
    }
}

main();
