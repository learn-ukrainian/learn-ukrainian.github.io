// Vocabulary
function initVocab() {
  const grid = document.getElementById('vocab-grid');
  if (!grid) return;
  grid.innerHTML = '';
  vocabData.forEach(v => {
    const card = document.createElement('div');
    card.className = 'vocab-card';
    card.innerHTML = '<div class="uk">' + v.uk + '</div><div class="translit">' + v.translit + '</div><div class="en">' + v.en + '</div>' + (v.note ? '<div class="note">' + v.note + '</div>' : '');
    grid.appendChild(card);
  });
}
