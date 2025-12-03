// Select Activity - supports multiple instances
const selectState = {};

function initSelect(sectionId, data) {
  const c = document.getElementById(sectionId + '-container');
  if (!c || !data.items || !data.items.length) return;

  selectState[sectionId] = { score: 0, answered: 0, total: data.items.length, data: data };
  c.innerHTML = '';

  data.items.forEach((item, idx) => {
    const div = document.createElement('div');
    div.className = 'select-question';
    div.dataset.section = sectionId;
    div.dataset.idx = idx;

    const optionsHtml = item.options.map((opt, oi) =>
      `<label class="select-option" data-correct="${opt.correct}" data-section="${sectionId}" data-idx="${idx}">
        <input type="checkbox" class="select-checkbox" data-oi="${oi}">
        <span class="select-text">${opt.text}</span>
      </label>`
    ).join('');

    div.innerHTML = `
      <div class="select-number">${idx + 1}.</div>
      <div class="select-content">
        <p class="select-prompt">${item.question}</p>
        <div class="select-options">${optionsHtml}</div>
        <button class="btn btn-sm btn-outline select-check" data-section="${sectionId}" data-idx="${idx}">Check</button>
        <div class="select-feedback" id="${sectionId}-fb-${idx}"></div>
      </div>
    `;
    c.appendChild(div);
  });

  // Event delegation for check buttons
  c.addEventListener('click', (e) => {
    if (e.target.classList.contains('select-check')) {
      checkSelectAnswer(e.target.dataset.section, parseInt(e.target.dataset.idx));
    }
  });
}

function checkSelectAnswer(sectionId, idx) {
  const state = selectState[sectionId];
  const item = state.data.items[idx];
  const question = document.querySelector(`.select-question[data-section="${sectionId}"][data-idx="${idx}"]`);
  const fb = document.getElementById(sectionId + '-fb-' + idx);

  if (question.classList.contains('answered')) return;

  const options = question.querySelectorAll('.select-option');
  let allCorrect = true;

  options.forEach(opt => {
    const checkbox = opt.querySelector('.select-checkbox');
    const isChecked = checkbox.checked;
    const shouldBeChecked = opt.dataset.correct === 'true';

    if (isChecked === shouldBeChecked) {
      opt.classList.add(shouldBeChecked ? 'correct' : 'correct-unchecked');
    } else {
      opt.classList.add(shouldBeChecked ? 'missed' : 'wrong');
      allCorrect = false;
    }
    checkbox.disabled = true;
  });

  question.classList.add('answered');

  if (allCorrect) {
    fb.innerHTML = '<span class="correct-text">✓ Perfect!</span>';
    state.score++;
  } else {
    fb.innerHTML = '<span class="wrong-text">✗ Some answers were incorrect.</span>';
  }
  fb.classList.add('show');

  document.getElementById(sectionId + '-score').textContent = state.score;
  state.answered++;

  if (state.answered === state.total) {
    document.getElementById(sectionId + '-complete').classList.add('show');
  }
}

function resetSelect(sectionId) {
  const state = selectState[sectionId];
  if (!state) return;
  document.getElementById(sectionId + '-score').textContent = '0';
  document.getElementById(sectionId + '-complete')?.classList.remove('show');
  initSelect(sectionId, state.data);
}
