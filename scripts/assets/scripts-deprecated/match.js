// Match Activity - supports multiple instances
const matchState = {};

function initMatch(sectionId, data) {
  const container = document.getElementById(sectionId + '-container');
  const leftCol = document.getElementById(sectionId + '-left');
  const rightCol = document.getElementById(sectionId + '-right');
  if (!container || !leftCol || !rightCol || !data.pairs || !data.pairs.length) return;

  const pairs = data.pairs;
  matchState[sectionId] = { selected: null, score: 0, matched: [], total: pairs.length, data: data };

  // Create left column items
  const shuffledLeft = pairs.map((p, i) => ({ text: p.left, idx: i })).sort(() => Math.random() - 0.5);
  leftCol.innerHTML = shuffledLeft.map(p => '<div class="match-item" data-pair="' + p.idx + '" data-section="' + sectionId + '" data-side="left">' + p.text + '</div>').join('');

  // Create right column items
  const shuffledRight = pairs.map((p, i) => ({ text: p.right, idx: i })).sort(() => Math.random() - 0.5);
  rightCol.innerHTML = shuffledRight.map(p => '<div class="match-item" data-pair="' + p.idx + '" data-section="' + sectionId + '" data-side="right">' + p.text + '</div>').join('');

  // Attach click handlers
  leftCol.querySelectorAll('.match-item').forEach(item => {
    item.addEventListener('click', () => handleMatchLeft(item));
  });
  rightCol.querySelectorAll('.match-item').forEach(item => {
    item.addEventListener('click', () => handleMatchRight(item));
  });
}

function handleMatchLeft(item) {
  const sectionId = item.dataset.section;
  const state = matchState[sectionId];
  if (item.classList.contains('matched')) return;

  const leftCol = document.getElementById(sectionId + '-left');
  leftCol.querySelectorAll('.match-item').forEach(i => i.classList.remove('selected'));
  item.classList.add('selected');
  state.selected = { el: item, pair: item.dataset.pair };
}

function handleMatchRight(item) {
  const sectionId = item.dataset.section;
  const state = matchState[sectionId];
  if (item.classList.contains('matched') || !state.selected) return;

  if (state.selected.pair === item.dataset.pair) {
    state.selected.el.classList.remove('selected');
    state.selected.el.classList.add('matched');
    item.classList.add('matched');
    state.matched.push({ left: state.selected.el, right: item });
    state.score++;
    document.getElementById(sectionId + '-score').textContent = state.score;
    drawMatchLines(sectionId);
    if (state.score === state.total) document.getElementById(sectionId + '-complete').classList.add('show');
  } else {
    item.classList.add('wrong');
    setTimeout(() => item.classList.remove('wrong'), 300);
  }
  state.selected = null;
}

function drawMatchLines(sectionId) {
  const svg = document.getElementById(sectionId + '-lines');
  const container = document.getElementById(sectionId + '-container');
  const state = matchState[sectionId];
  if (!svg || !container || !state) return;

  const r = container.getBoundingClientRect();
  svg.innerHTML = '';
  svg.setAttribute('viewBox', '0 0 ' + r.width + ' ' + r.height);
  state.matched.forEach(p => {
    const lr = p.left.getBoundingClientRect(), rr = p.right.getBoundingClientRect();
    const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    line.setAttribute('x1', lr.right - r.left);
    line.setAttribute('y1', lr.top + lr.height / 2 - r.top);
    line.setAttribute('x2', rr.left - r.left);
    line.setAttribute('y2', rr.top + rr.height / 2 - r.top);
    line.setAttribute('stroke', '#26a269');
    line.setAttribute('stroke-width', '2');
    svg.appendChild(line);
  });
}

function resetMatch(sectionId) {
  const state = matchState[sectionId];
  if (!state) return;
  document.getElementById(sectionId + '-score').textContent = '0';
  document.getElementById(sectionId + '-complete')?.classList.remove('show');
  document.getElementById(sectionId + '-lines').innerHTML = '';
  initMatch(sectionId, state.data);
}

// Redraw lines on resize for all match activities
window.addEventListener('resize', () => {
  Object.keys(matchState).forEach(sectionId => drawMatchLines(sectionId));
});
