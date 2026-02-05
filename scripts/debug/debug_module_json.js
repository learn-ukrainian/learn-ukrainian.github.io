
const fs = require('fs');
const path = require('path');

const filePath = 'docusaurus/docs/b2/module-99.mdx';
const content = fs.readFileSync(filePath, 'utf8');

const regex = /JSON\.parse\(`([\s\S]*?)`\)/g;
let match;
let index = 1;

while ((match = regex.exec(content)) !== null) {
    const jsonString = match[1];
    try {
        JSON.parse(jsonString);
        console.log(`Block ${index}: VALID`);
    } catch (e) {
        console.error(`Block ${index}: INVALID`);
        console.error(e.message);

        // Print context
        console.log('--- JSON snippet start ---');
        console.log(jsonString.substring(0, 100) + '...');
        console.log('--- JSON snippet end ---');
    }
    index++;
}
