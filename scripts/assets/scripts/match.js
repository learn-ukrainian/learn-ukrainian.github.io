// Match Activity
let matchSel = null, matchScore = 0, matchPairsArr = [];

document.querySelectorAll('#match-left .match-item').forEach(item => {
  item.addEventListener('click', () => {
    if (item.classList.contains('matched')) return;
    document.querySelectorAll('#match-left .match-item').forEach(i => i.classList.remove('selected'));
    item.classList.add('selected');
    matchSel = { el: item, pair: item.dataset.pair };
  });
});

document.querySelectorAll('#match-right .match-item').forEach(item => {
  item.addEventListener('click', () => {
    if (item.classList.contains('matched') || !matchSel) return;
    if (matchSel.pair === item.dataset.pair) {
      matchSel.el.classList.remove('selected');
      matchSel.el.classList.add('matched');
      item.classList.add('matched');
      matchPairsArr.push({ left: matchSel.el, right: item });
      matchScore++;
      document.getElementById('match-score').textContent = matchScore;
      drawLines();
      if (matchScore === matchPairs.length) document.getElementById('match-complete').classList.add('show');
    } else {
      item.classList.add('wrong');
      setTimeout(() => item.classList.remove('wrong'), 300);
    }
    matchSel = null;
  });
});

function drawLines() {
  const svg = document.getElementById('match-lines'), c = document.getElementById('match-container');
  if (!svg || !c) return;
  const r = c.getBoundingClientRect();
  svg.innerHTML = '';
  svg.setAttribute('viewBox', '0 0 ' + r.width + ' ' + r.height);
  matchPairsArr.forEach(p => {
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

function resetMatch() {
  matchSel = null;
  matchScore = 0;
  matchPairsArr = [];
  document.getElementById('match-score').textContent = '0';
  document.getElementById('match-complete')?.classList.remove('show');
  document.getElementById('match-lines').innerHTML = '';
  document.querySelectorAll('#match-container .match-item').forEach(i => i.classList.remove('matched', 'selected', 'wrong'));
}

window.addEventListener('resize', drawLines);
