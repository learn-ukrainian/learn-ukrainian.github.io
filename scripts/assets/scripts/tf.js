// True/False Activity - supports multiple instances
const tfState = {};

function initTf(sectionId, data) {
  const c = document.getElementById(sectionId + '-container');
  if (!c || !data.statements || !data.statements.length) return;

  tfState[sectionId] = { score: 0, answered: 0, total: data.statements.length, data: data };

  c.innerHTML = '';
  data.statements.forEach((s, i) => {
    const div = document.createElement('div');
    div.className = 'tf-statement';
    div.dataset.section = sectionId;
    div.innerHTML = '<p class="tf-text">' + s.statement + '</p>' +
      '<div class="tf-buttons">' +
      '<button class="tf-btn" data-value="true" data-idx="' + i + '" data-section="' + sectionId + '">True</button>' +
      '<button class="tf-btn" data-value="false" data-idx="' + i + '" data-section="' + sectionId + '">False</button>' +
      '</div>' +
      '<div class="tf-explanation" id="' + sectionId + '-exp-' + i + '">' + (s.explanation || '') + '</div>';
    div.dataset.correct = s.isTrue;
    c.appendChild(div);
  });
  c.querySelectorAll('.tf-btn').forEach(b => b.addEventListener('click', handleTf));
}

function handleTf(e) {
  const btn = e.target;
  const sectionId = btn.dataset.section;
  const idx = parseInt(btn.dataset.idx);
  const statement = btn.closest('.tf-statement');
  const state = tfState[sectionId];
  if (statement.classList.contains('answered')) return;

  statement.classList.add('answered');
  const correct = state.data.statements[idx].isTrue;
  const clicked = btn.dataset.value === 'true';

  if (clicked === correct) {
    btn.classList.add('correct');
    state.score++;
  } else {
    btn.classList.add('wrong');
    // Highlight the correct answer
    statement.querySelector('[data-value="' + correct + '"]').classList.add('correct');
  }

  const exp = document.getElementById(sectionId + '-exp-' + idx);
  if (exp && exp.textContent) exp.classList.add('show');

  document.getElementById(sectionId + '-score').textContent = state.score;
  state.answered++;
  if (state.answered === state.total) document.getElementById(sectionId + '-complete').classList.add('show');
}

function resetTf(sectionId) {
  const state = tfState[sectionId];
  if (!state) return;
  document.getElementById(sectionId + '-score').textContent = '0';
  document.getElementById(sectionId + '-complete')?.classList.remove('show');
  initTf(sectionId, state.data);
}
