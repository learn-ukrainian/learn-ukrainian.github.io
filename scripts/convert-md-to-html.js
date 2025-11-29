// scripts/convert-md-to-html.js
const showdown = require('showdown');
const fs = require('fs');
const path = require('path');

const converter = new showdown.Converter({
  tables: true,
  tasklists: true,
  openLinksInNewWindow: true
});

const inputPath = process.argv[2];
if (!inputPath) {
  console.error('Please provide input markdown file path');
  process.exit(1);
}

const mdContent = fs.readFileSync(inputPath, 'utf8');
const htmlBody = converter.makeHtml(mdContent);

const fullHtml = `
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Lesson Content</title>
  <style>
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      line-height: 1.6;
      color: #333;
      max-width: 800px;
      margin: 0 auto;
      padding: 2rem;
      background-color: #f9f9f9;
    }
    .container {
      background-color: white;
      padding: 2rem;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    h1, h2, h3 { color: #2c3e50; }
    h1 { border-bottom: 2px solid #eee; padding-bottom: 0.5rem; }
    h2 { margin-top: 2rem; }
    table {
      border-collapse: collapse;
      width: 100%;
      margin: 1rem 0;
    }
    th, td {
      border: 1px solid #ddd;
      padding: 8px;
      text-align: left;
    }
    th { background-color: #f2f2f2; }
    blockquote {
      border-left: 4px solid #3498db;
      margin: 0;
      padding-left: 1rem;
      color: #555;
      background-color: #f0f7fb;
      padding: 1rem;
    }
    code {
      background-color: #f0f0f0;
      padding: 2px 4px;
      border-radius: 3px;
      font-family: monospace;
    }
  </style>
</head>
<body>
  <div class="container">
    ${htmlBody}
  </div>
</body>
</html>
`;

const outputDir = path.dirname(inputPath);
const outputFilename = path.basename(inputPath, '.md') + '.html';
const outputPath = path.join(outputDir, outputFilename);

fs.writeFileSync(outputPath, fullHtml);
console.log(`Converted ${inputPath} -> ${outputPath}`);
