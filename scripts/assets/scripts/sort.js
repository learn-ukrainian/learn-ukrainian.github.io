// Sort Activity - supports multiple instances
const sortState = {};

function initSort(sectionId, data) {
  const pool = document.getElementById(sectionId + '-items');
  const groupsContainer = document.getElementById(sectionId + '-groups');
  if (!pool || !groupsContainer || !data.groups || !data.groups.length) return;

  const groups = data.groups;
  const totalItems = groups.reduce((sum, g) => sum + g.items.length, 0);
  sortState[sectionId] = { score: 0, total: totalItems, dragItem: null, data: data };

  // Create group containers
  groupsContainer.innerHTML = groups.map((g, i) =>
    '<div class="sort-group" data-group="' + i + '" data-section="' + sectionId + '"><h4>' + g.name + '</h4><div class="sort-items"></div></div>'
  ).join('');

  // Flatten and shuffle all items
  const allItems = groups.flatMap((g, gi) => g.items.map(item => ({ text: item, group: gi })));
  allItems.sort(() => Math.random() - 0.5);

  // Create draggable items
  pool.innerHTML = '';
  allItems.forEach(item => {
    const el = document.createElement('div');
    el.className = 'sort-item';
    el.textContent = item.text;
    el.draggable = true;
    el.dataset.group = item.group;
    el.dataset.section = sectionId;
    el.addEventListener('dragstart', () => {
      sortState[sectionId].dragItem = el;
      el.classList.add('dragging');
    });
    el.addEventListener('dragend', () => {
      el.classList.remove('dragging');
      sortState[sectionId].dragItem = null;
    });
    pool.appendChild(el);
  });

  // Setup drop zones
  groupsContainer.querySelectorAll('.sort-group').forEach(g => {
    g.addEventListener('dragover', e => {
      e.preventDefault();
      g.classList.add('drag-over');
    });
    g.addEventListener('dragleave', () => g.classList.remove('drag-over'));
    g.addEventListener('drop', e => handleSortDrop(e, g));
  });
}

function handleSortDrop(e, groupEl) {
  e.preventDefault();
  groupEl.classList.remove('drag-over');
  const sectionId = groupEl.dataset.section;
  const state = sortState[sectionId];
  const dragItem = state.dragItem;
  if (!dragItem) return;

  if (groupEl.dataset.group === dragItem.dataset.group) {
    dragItem.classList.add('correct');
    groupEl.querySelector('.sort-items').appendChild(dragItem);
    dragItem.draggable = false;
    state.score++;
    document.getElementById(sectionId + '-score').textContent = state.score;
    if (state.score === state.total) document.getElementById(sectionId + '-complete').classList.add('show');
  } else {
    dragItem.classList.add('wrong');
    setTimeout(() => dragItem.classList.remove('wrong'), 300);
  }
}

function resetSort(sectionId) {
  const state = sortState[sectionId];
  if (!state) return;
  document.getElementById(sectionId + '-score').textContent = '0';
  document.getElementById(sectionId + '-complete')?.classList.remove('show');
  initSort(sectionId, state.data);
}
