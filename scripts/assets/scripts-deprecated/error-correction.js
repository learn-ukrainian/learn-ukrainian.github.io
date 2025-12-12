// Error-Correction Activity
// Two-step interaction: 1) Click wrong word, 2) Select correct form
const errorState = {};

function initErrorCorrection(sectionId, data) {
  const c = document.getElementById(sectionId + '-container');
  if (!c || !data.items || !data.items.length) return;

  errorState[sectionId] = {
    score: 0,
    completed: 0,
    total: data.items.length,
    data: data
  };
  c.innerHTML = '';

  data.items.forEach((item, i) => {
    const div = document.createElement('div');
    div.className = 'error-item';
    div.dataset.section = sectionId;
    div.dataset.idx = i;

    // Parse sentence into clickable words
    const words = item.sentence.split(/(\s+)/);
    const wordsHtml = words.map((word, wi) => {
      if (/^\s+$/.test(word)) return word; // preserve whitespace

      const cleanWord = word.replace(/[.,!?;:]/g, '').trim();
      const cleanError = (item.errorWord || '').trim();

      const isError = cleanError && cleanWord.toLowerCase() === cleanError.toLowerCase();

      return `<span class="error-word" data-word="${cleanWord}" data-is-error="${isError}">${word}</span>`;
    }).join('');

    const hasNoError = item.errorWord === null;

    div.innerHTML = `
      <div class="error-sentence" id="${sectionId}-sentence-${i}">
        <span class="error-number">${i + 1}.</span>
        <span class="error-words">${wordsHtml}</span>
        ${hasNoError ? '' : ''}
      </div>
      <div class="error-no-error-btn" id="${sectionId}-noerror-${i}">
        <button class="btn btn-outline btn-sm" onclick="handleNoError('${sectionId}', ${i})">No error</button>
      </div>
      <div class="error-options" id="${sectionId}-options-${i}" style="display:none;">
        <span class="error-prompt">Choose the correct form:</span>
        <div class="error-option-btns">
          ${[...(item.options || [])].sort(() => Math.random() - 0.5).map(opt =>
      `<button class="btn btn-outline btn-sm error-option"
                     data-option="${opt}"
                     data-correct="${opt === item.correctForm}"
                     onclick="handleErrorOption('${sectionId}', ${i}, '${opt}', ${opt === item.correctForm})">${opt}</button>`
    ).join('')}
        </div>
      </div>
      <div class="error-feedback" id="${sectionId}-fb-${i}" style="display:none;"></div>
    `;

    c.appendChild(div);
  });

  // Event delegation for word clicks
  c.addEventListener('click', (e) => {
    const wordEl = e.target.closest('.error-word');
    if (wordEl && !wordEl.closest('.error-item').classList.contains('completed')) {
      const item = wordEl.closest('.error-item');
      handleWordClick(item.dataset.section, parseInt(item.dataset.idx), wordEl);
    }
  });
}

function handleWordClick(sectionId, idx, wordEl) {
  const state = errorState[sectionId];
  const item = state.data.items[idx];
  const itemEl = document.querySelector(`.error-item[data-section="${sectionId}"][data-idx="${idx}"]`);

  if (itemEl.classList.contains('step2') || itemEl.classList.contains('completed')) return;

  // Clear previous selection in this item
  itemEl.querySelectorAll('.error-word.selected').forEach(w => w.classList.remove('selected'));

  const clickedWord = wordEl.dataset.word;
  const isError = wordEl.dataset.isError === 'true';

  if (isError) {
    // Correct identification! Move to step 2
    wordEl.classList.add('selected', 'found');
    itemEl.classList.add('step2');
    state.score++;
    document.getElementById(sectionId + '-score').textContent = state.score;

    // Hide no-error button, show options
    document.getElementById(`${sectionId}-noerror-${idx}`).style.display = 'none';
    document.getElementById(`${sectionId}-options-${idx}`).style.display = 'block';
  } else {
    // Wrong word selected
    wordEl.classList.add('selected', 'wrong-selection');
    setTimeout(() => wordEl.classList.remove('selected', 'wrong-selection'), 500);
  }
}

function handleNoError(sectionId, idx) {
  const state = errorState[sectionId];
  const item = state.data.items[idx];
  const itemEl = document.querySelector(`.error-item[data-section="${sectionId}"][data-idx="${idx}"]`);
  const fb = document.getElementById(`${sectionId}-fb-${idx}`);

  if (itemEl.classList.contains('completed')) return;

  itemEl.classList.add('completed');
  document.getElementById(`${sectionId}-noerror-${idx}`).style.display = 'none';

  if (item.errorWord === null) {
    // Correct! No error in this sentence
    state.score += 2; // Full points for no-error items
    fb.innerHTML = `<span class="correct-text">Correct! No error in this sentence.</span>`;
    if (item.explanation) {
      fb.innerHTML += `<div class="error-explanation">${item.explanation}</div>`;
    }
  } else {
    // Wrong - there was an error
    fb.innerHTML = `<span class="wrong-text">There was an error: <strong>${item.errorWord}</strong> → <strong>${item.correctForm}</strong></span>`;
    if (item.explanation) {
      fb.innerHTML += `<div class="error-explanation">${item.explanation}</div>`;
    }
  }

  fb.style.display = 'block';
  document.getElementById(sectionId + '-score').textContent = state.score;

  state.completed++;
  checkComplete(sectionId);
}

function handleErrorOption(sectionId, idx, option, isCorrect) {
  const state = errorState[sectionId];
  const item = state.data.items[idx];
  const itemEl = document.querySelector(`.error-item[data-section="${sectionId}"][data-idx="${idx}"]`);
  const fb = document.getElementById(`${sectionId}-fb-${idx}`);
  const optionsEl = document.getElementById(`${sectionId}-options-${idx}`);

  if (itemEl.classList.contains('completed')) return;

  itemEl.classList.add('completed');

  // Highlight correct/wrong options
  optionsEl.querySelectorAll('.error-option').forEach(btn => {
    btn.disabled = true;
    if (btn.dataset.correct === 'true') {
      btn.classList.add('correct');
    } else if (btn.dataset.option === option && !isCorrect) {
      btn.classList.add('wrong');
    }
  });

  if (isCorrect) {
    state.score++;
    fb.innerHTML = `<span class="correct-text">Correct!</span>`;
  } else {
    fb.innerHTML = `<span class="wrong-text">The correct form is: <strong>${item.correctForm}</strong></span>`;
  }

  if (item.explanation) {
    fb.innerHTML += `<div class="error-explanation">${item.explanation}</div>`;
  }

  fb.style.display = 'block';
  document.getElementById(sectionId + '-score').textContent = state.score;

  state.completed++;
  checkComplete(sectionId);
}

function checkComplete(sectionId) {
  const state = errorState[sectionId];
  if (state.completed === state.total) {
    document.getElementById(sectionId + '-complete').classList.add('show');
  }
}

function resetErrorCorrection(sectionId) {
  const state = errorState[sectionId];
  if (!state) return;
  document.getElementById(sectionId + '-score').textContent = '0';
  document.getElementById(sectionId + '-complete')?.classList.remove('show');
  initErrorCorrection(sectionId, state.data);
}
