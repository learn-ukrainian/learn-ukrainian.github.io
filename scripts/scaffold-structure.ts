// scripts/scaffold-structure.ts
import { mkdir, writeFile } from 'fs/promises';
import { join } from 'path';

const BASE_DIR = 'course-content/l2-uk-en';

const STRUCTURE = {
  'book-01-survivor': {
    title: 'Book 1: The Survivor (A1)',
    modules: [
      { id: '01', name: 'module-01-cyrillic', title: 'The Cyrillic Code' },
      { id: '02', name: 'module-02-ghost-verb', title: 'The Ghost Verb' },
      { id: '03', name: 'module-03-declensions', title: 'Noun Architecture' },
      { id: '04', name: 'module-04-politeness', title: 'The Polite Stranger' },
      { id: '05', name: 'module-05-objects', title: 'Common Objects' },
      { id: '06', name: 'module-06-numbers', title: 'Numbers & Money' },
      { id: '07', name: 'module-07-locative', title: 'The GPS (Locative)' },
      { id: '08', name: 'module-08-city', title: 'The City Places' },
      { id: '09', name: 'module-09-accusative', title: 'I Want Pizza (Accusative)' },
      { id: '10', name: 'module-10-food', title: 'Food & Drink' },
      { id: '11', name: 'module-11-genitive', title: 'The Lord of Absence (Genitive)' },
      { id: '12', name: 'module-12-family', title: 'Family & Possessives' },
      { id: '13', name: 'module-13-past', title: 'The Time Traveler (Past)' },
      { id: '14', name: 'module-14-calendar', title: 'The Calendar' },
      { id: '15', name: 'module-15-future', title: 'The Planner (Future)' },
      { id: '16', name: 'module-16-routine', title: 'Daily Routine' },
      { id: '17', name: 'module-17-colors', title: 'Colors & Clothing' },
      { id: '18', name: 'module-18-weather', title: 'Weather' },
      { id: '19', name: 'module-19-modals', title: 'Can, Must, Want' },
      { id: '20', name: 'module-20-review', title: 'A1 Capstone' }
    ]
  },
  'book-02-explorer': {
    title: 'Book 2: The Explorer (A2)',
    modules: [
      { id: '21', name: 'module-21-instrumental', title: 'The Tool User (Instrumental)' },
      { id: '22', name: 'module-22-tools', title: 'Tools & Transport' },
      { id: '23', name: 'module-23-dative', title: 'The Receiver (Dative)' },
      { id: '24', name: 'module-24-health', title: 'Health & Body' },
      { id: '25', name: 'module-25-adjectives', title: 'The Comparator' },
      { id: '26', name: 'module-26-people', title: 'Describing People' },
      { id: '27', name: 'module-27-motion-1', title: 'Motion I (Go vs Drive)' },
      { id: '28', name: 'module-28-travel', title: 'Travel & Directions' },
      { id: '29', name: 'module-29-imperative', title: 'Do It! (Imperative)' },
      { id: '30', name: 'module-30-review', title: 'A2 Capstone' }
    ]
  },
  'book-03-expat': {
    title: 'Book 3: The Expat (B1)',
    modules: [
      { id: '31', name: 'module-31-aspects', title: 'Aspects (Process vs Result)' },
      { id: '32', name: 'module-32-motion-2', title: 'Motion II (Prefixed)' }
      // ... placeholders for future expansion
    ]
  },
  'track-history': {
    title: 'Track: The Historian',
    modules: [{ id: 'h01', name: 'module-h01-hetmanate', title: 'The Hetmanate Archives' }]
  },
  'track-science': {
    title: 'Track: The Scientist',
    modules: [{ id: 's01', name: 'module-s01-biology', title: 'Cellular Biology' }]
  },
  'track-cs': {
    title: 'Track: The Developer',
    modules: [{ id: 'cs01', name: 'module-cs01-algorithms', title: 'Algorithms' }]
  },
  'track-arts': {
    title: 'Track: The Critic',
    modules: [{ id: 'a01', name: 'module-a01-visual-arts', title: 'Visual Arts' }]
  }
};

async function scaffold() {
  console.log('Starting scaffold process...');
  
  for (const [bookDir, bookData] of Object.entries(STRUCTURE)) {
    const bookPath = join(BASE_DIR, bookDir);
    await mkdir(bookPath, { recursive: true });
    console.log(`Created Book: ${bookPath}`);

    // Create Book README
    await writeFile(join(bookPath, 'README.md'), `# ${bookData.title}\n\nCourse content and modules.`);

    for (const module of bookData.modules) {
      const modulePath = join(bookPath, module.name);
      await mkdir(modulePath, { recursive: true });
      
      // Create placeholder textbook
      const placeholderContent = `# ${module.title}\n\n*(Content pending)*\n\n## Objectives\n- [ ] Define learning goals\n- [ ] Write theory section\n`;
      await writeFile(join(modulePath, 'textbook.md'), placeholderContent);
      
      console.log(`  - Created Module: ${module.name}`);
    }
  }
  
  console.log('Scaffold complete!');
}

scaffold().catch(console.error);