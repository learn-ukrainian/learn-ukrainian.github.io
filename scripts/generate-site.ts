// scripts/generate-site.ts
import { readdir, readFile, writeFile } from 'fs/promises';
import { join, dirname, relative } from 'path';

const CONTENT_DIR = 'course-content/l2-uk-en';

interface ModuleInfo {
  id: string;
  title: string;
  path: string;
  book: string;
}

interface BookInfo {
  id: string;
  title: string;
  modules: ModuleInfo[];
}

// Helper to extract title from markdown (first line # Title)
async function getTitle(mdPath: string): Promise<string> {
  try {
    const content = await readFile(mdPath, 'utf-8');
    const match = content.match(/^# (.*)$/m);
    return match ? match[1].trim() : 'Untitled Module';
  } catch (e) {
    return 'Untitled Module';
  }
}

async function generateSite() {
  console.log('Generating curriculum site...');
  
  const books: BookInfo[] = [];
  const entries = await readdir(CONTENT_DIR, { withFileTypes: true });

  // 1. Scan Structure
  for (const entry of entries) {
    if (entry.isDirectory() && entry.name.startsWith('book-')) {
      const bookId = entry.name;
      const bookPath = join(CONTENT_DIR, bookId);
      
      // Get Book Title from README if exists, else format ID
      let bookTitle = bookId.replace(/-/g, ' ').toUpperCase();
      try {
        const readme = await readFile(join(bookPath, 'README.md'), 'utf-8');
        const match = readme.match(/^# (.*)$/m);
        if (match) bookTitle = match[1];
      } catch (e) {}

      const moduleEntries = await readdir(bookPath, { withFileTypes: true });
      const modules: ModuleInfo[] = [];

      for (const modEntry of moduleEntries) {
        if (modEntry.isDirectory() && modEntry.name.startsWith('module-')) {
          const modPath = join(bookPath, modEntry.name);
          const mdPath = join(modPath, 'textbook.md');
          const title = await getTitle(mdPath);
          
          modules.push({
            id: modEntry.name,
            title,
            path: modPath,
            book: bookId
          });
        }
      }

      // Sort modules by name (module-01, module-02...)
      modules.sort((a, b) => a.id.localeCompare(b.id));
      books.push({ id: bookId, title: bookTitle, modules });
    }
  }

  // Sort books
  books.sort((a, b) => a.id.localeCompare(b.id));

  // 2. Generate Master Index (Landing Page)
  let indexHtml = `
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Neural Dojo: Ukrainian L2 Curriculum</title>
  <style>
    body { font-family: system-ui, sans-serif; line-height: 1.6; max-width: 900px; margin: 0 auto; padding: 2rem; background: #f4f4f9; color: #333; }
    h1 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 0.5rem; }
    .book-card { background: white; padding: 1.5rem; margin-bottom: 2rem; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
    .book-title { color: #e67e22; margin-top: 0; }
    .module-list { list-style: none; padding: 0; display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 1rem; }
    .module-item a { display: block; padding: 10px; background: #ecf0f1; color: #2c3e50; text-decoration: none; border-radius: 4px; transition: 0.2s; }
    .module-item a:hover { background: #3498db; color: white; }
    .badge { font-size: 0.8em; background: #95a5a6; color: white; padding: 2px 6px; border-radius: 4px; float: right; }
  </style>
</head>
<body>
  <h1>🇺🇦 Neural Dojo: Ukrainian L2 Curriculum</h1>
  <p>A theory-first, vocabulary-rich path from A1 to C1.</p>
`;

  const allModulesFlat: ModuleInfo[] = [];

  for (const book of books) {
    indexHtml += `<div class="book-card"><h2 class="book-title">${book.title}</h2><ul class="module-list">`;
    for (const mod of book.modules) {
      allModulesFlat.push(mod);
      const relPath = `${book.id}/${mod.id}/textbook.html`;
      indexHtml += `<li class="module-item"><a href="${relPath}">${mod.title}</a></li>`;
    }
    indexHtml += `</ul></div>`;
  }

  indexHtml += `</body></html>`;
  await writeFile(join(CONTENT_DIR, 'index.html'), indexHtml);
  console.log(`Generated Index: ${join(CONTENT_DIR, 'index.html')}`);

  // 3. Update Module HTMLs with Navigation
  // We assume 'convert-md-to-html.js' has already run and created basic HTMLs. 
  // We will inject a nav bar into them.

  for (let i = 0; i < allModulesFlat.length; i++) {
    const current = allModulesFlat[i];
    const prev = i > 0 ? allModulesFlat[i - 1] : null;
    const next = i < allModulesFlat.length - 1 ? allModulesFlat[i + 1] : null;

    const htmlPath = join(current.path, 'textbook.html');
    
    try {
      let htmlContent = await readFile(htmlPath, 'utf-8');
      
      // Calculate relative paths for links
      // current.path is absolute/root-relative. 
      // We need link from book/module/textbook.html to book/module/textbook.html
      // Actually simpler: we are in book/module/. 
      // Up one level is book/. Up two levels is root.
      
      const rootLink = '../../index.html';
      
      let navHtml = `<div style="background: #2c3e50; padding: 1rem; margin: -2rem -2rem 2rem -2rem; display: flex; justify-content: space-between; align-items: center; color: white;">`;
      
      // Prev Button
      if (prev) {
        const prevLink = `../../${prev.book}/${prev.id}/textbook.html`;
        navHtml += `<a href="${prevLink}" style="color: white; text-decoration: none;">← ${prev.title}</a>`;
      } else {
        navHtml += `<span></span>`;
      }

      // Home Button
      navHtml += `<a href="${rootLink}" style="color: white; font-weight: bold; text-decoration: none;">🏠 Curriculum Home</a>`;

      // Next Button
      if (next) {
        const nextLink = `../../${next.book}/${next.id}/textbook.html`;
        navHtml += `<a href="${nextLink}" style="color: white; text-decoration: none;">${next.title} →</a>`;
      } else {
        navHtml += `<span></span>`;
      }
      
      navHtml += `</div>`;

      // Inject Nav at top of body
      if (!htmlContent.includes('Curriculum Home')) {
        htmlContent = htmlContent.replace('<body>', '<body>' + navHtml);
        
        // Add bottom nav too
        htmlContent = htmlContent.replace('</body>', navHtml + '</body>');
        
        await writeFile(htmlPath, htmlContent);
        console.log(`Updated Nav: ${current.id}`);
      }

    } catch (e) {
      // File might not exist if we haven't generated it yet (Modules 11+)
      // console.log(`Skipping ${current.id} (no HTML found)`);
    }
  }
}

generateSite().catch(console.error);
