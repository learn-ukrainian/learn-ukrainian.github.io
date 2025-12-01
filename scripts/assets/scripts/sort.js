// Sort Activity
let sortScore = 0, dragItem = null;

function initSort() {
  const pool = document.getElementById('sort-items');
  if (!pool || !Object.keys(sortData).length) return;
  const all = Object.values(sortData).flat().sort(() => Math.random() - 0.5);
  pool.innerHTML = '';
  all.forEach(letter => {
    const group = Object.keys(sortData).find(g => sortData[g].includes(letter));
    const item = document.createElement('div');
    item.className = 'sort-item';
    item.textContent = letter;
    item.draggable = true;
    item.dataset.group = group;
    item.addEventListener('dragstart', e => {
      dragItem = item;
      item.classList.add('dragging');
    });
    item.addEventListener('dragend', () => {
      item.classList.remove('dragging');
      dragItem = null;
    });
    pool.appendChild(item);
  });
  document.querySelectorAll('.sort-group').forEach(g => {
    g.addEventListener('dragover', e => {
      e.preventDefault();
      g.classList.add('drag-over');
    });
    g.addEventListener('dragleave', () => g.classList.remove('drag-over'));
    g.addEventListener('drop', e => {
      e.preventDefault();
      g.classList.remove('drag-over');
      if (!dragItem) return;
      if (g.dataset.group === dragItem.dataset.group) {
        dragItem.classList.add('correct');
        g.querySelector('.sort-items').appendChild(dragItem);
        dragItem.draggable = false;
        sortScore++;
        document.getElementById('sort-score').textContent = sortScore;
        if (sortScore === totalSort) document.getElementById('sort-complete').classList.add('show');
      } else {
        dragItem.classList.add('wrong');
        setTimeout(() => dragItem.classList.remove('wrong'), 300);
      }
    });
  });
}

function resetSort() {
  sortScore = 0;
  document.getElementById('sort-score').textContent = '0';
  document.getElementById('sort-complete')?.classList.remove('show');
  document.querySelectorAll('.sort-group .sort-items').forEach(g => g.innerHTML = '');
  initSort();
}
