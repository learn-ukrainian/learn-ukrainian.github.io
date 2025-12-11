
import fs from 'fs';
import path from 'path';

// Config
const HTML_OUT_DIR = path.resolve(__dirname, '../output/html');

function getAllHtmlFiles(dir: string, fileList: string[] = []): string[] {
    const files = fs.readdirSync(dir);

    files.forEach(file => {
        const filePath = path.join(dir, file);
        if (fs.statSync(filePath).isDirectory()) {
            getAllHtmlFiles(filePath, fileList);
        } else {
            if (file.endsWith('.html')) {
                fileList.push(filePath);
            }
        }
    });

    return fileList;
}

function checkFile(filePath: string): boolean {
    const content = fs.readFileSync(filePath, 'utf-8');
    const fileName = path.basename(filePath);
    let passed = true;

    // 1. Basic Structure
    if (!content.includes('<!DOCTYPE html>') || !content.includes('</html>')) {
        console.error(`❌ [${fileName}] Invalid HTML Structure`);
        passed = false;
    }

    // 2. Check for render errors
    if (content.includes('undefined') || content.includes('null') || content.includes('NaN')) {
        // Be careful, 'null' might be in text. But 'undefined' usually isn't.
        // Let's check specifically for common render artifacts like ">undefined<" or "id=\"undefined\""
        if (content.match(/>\s*undefined\s*</) || content.match(/="\s*undefined\s*"/)) {
            console.error(`❌ [${fileName}] Contains 'undefined' in rendered content`);
            passed = false;
        }
        if (content.match(/>\s*NaN\s*</)) {
            console.error(`❌ [${fileName}] Contains 'NaN' in rendered content`);
            passed = false;
        }
    }

    // 3. Check for empty key sections if they should exist
    // All modules should have a title
    if (!content.includes('<h1')) {
        console.error(`❌ [${fileName}] Missing H1 Title`);
        passed = false;
    }

    // Check for broken activity rendering (e.g. empty divs where activities should be)
    // This is hard to detect generically without jsdom, but we can look for "Unknown Activity" or similar error strings
    // inherited from our renderers.
    if (content.includes('Unknown Activity') || content.includes('Error rendering')) {
        console.error(`❌ [${fileName}] Contains explicit rendering errors`);
        passed = false;
    }

    if (passed) {
        // console.log(`✅ [${fileName}] OK`);
    }

    return passed;
}

function main() {
    console.log(`Scanning ${HTML_OUT_DIR} for HTML files...`);

    if (!fs.existsSync(HTML_OUT_DIR)) {
        console.error(`Directory ${HTML_OUT_DIR} does not exist. Run 'npm run generate' first.`);
        process.exit(1);
    }

    const files = getAllHtmlFiles(HTML_OUT_DIR);
    console.log(`Found ${files.length} HTML files.`);

    let errors = 0;
    files.forEach(f => {
        if (!checkFile(f)) {
            errors++;
        }
    });

    if (errors > 0) {
        console.error(`\n❌ Validation Failed: ${errors} files have issues.`);
        process.exit(1);
    } else {
        console.log(`\n✅ All ${files.length} HTML files passed basic validation.`);
        process.exit(0);
    }
}

main();
