// Fill-in Activity - supports multiple instances
const fillState = {};

function initFill(sectionId, data) {
  const c = document.getElementById(sectionId + '-container');
  if (!c || !data.items || !data.items.length) return;

  fillState[sectionId] = { score: 0, answered: 0, total: data.items.length, data: data };
  c.innerHTML = '';

  data.items.forEach((item, i) => {
    const div = document.createElement('div');
    div.className = 'fill-question';
    div.dataset.section = sectionId;

    // Generate options: correct answer + 3 distractors
    let options = [];
    if (item.options && item.options.length >= 4) {
      options = item.options;
    } else {
      // Fallback: generate distractors from other items' answers
      options = [item.answer];
      const otherAnswers = data.items
        .filter((_, idx) => idx !== i)
        .map(it => it.answer)
        .filter(a => a && a !== item.answer);

      const shuffled = otherAnswers.sort(() => Math.random() - 0.5);
      options.push(...shuffled.slice(0, 3));

      while (options.length < 4) {
        options.push('—');
      }
    }

    // Shuffle options
    const shuffledOptions = [...options].sort(() => Math.random() - 0.5);

    // Replace ___ in the sentence with a dropdown
    const sentence = (item.prompt || item.sentence || '').replace(/___/g,
      `<select class="fill-dropdown" data-idx="${i}" data-answer="${item.answer}" data-section="${sectionId}">
        <option value="" disabled selected>—</option>
        ${shuffledOptions.map(opt => `<option value="${opt}">${opt}</option>`).join('')}
      </select>`
    );

    div.innerHTML = `
      <div class="fill-sentence">
        <span class="fill-number">${i + 1}.</span>
        ${sentence}
      </div>
      <div class="fill-feedback" id="${sectionId}-fb-${i}"></div>
    `;
    c.appendChild(div);
  });

  // Event delegation for dropdown changes
  c.addEventListener('change', (e) => {
    if (e.target.classList.contains('fill-dropdown')) {
      handleFillChoice(e.target);
    }
  });
}

function handleFillChoice(dropdown) {
  const q = dropdown.closest('.fill-question');
  const sectionId = dropdown.dataset.section;
  const state = fillState[sectionId];
  if (q.classList.contains('answered')) return;

  const idx = dropdown.dataset.idx;
  const userAnswer = dropdown.value;
  const correctAnswer = dropdown.dataset.answer;
  const fb = document.getElementById(sectionId + '-fb-' + idx);

  q.classList.add('answered');
  dropdown.disabled = true;

  if (userAnswer === correctAnswer) {
    dropdown.classList.add('correct');
    fb.innerHTML = '<span class="correct-text">✓ Correct!</span>';
    state.score++;
  } else {
    dropdown.classList.add('wrong');
    fb.innerHTML = `<span class="wrong-text">✗ Answer: ${correctAnswer}</span>`;
  }

  document.getElementById(sectionId + '-score').textContent = state.score;
  state.answered++;
  if (state.answered === state.total) {
    document.getElementById(sectionId + '-complete').classList.add('show');
  }
}

function resetFill(sectionId) {
  const state = fillState[sectionId];
  if (!state) return;
  document.getElementById(sectionId + '-score').textContent = '0';
  document.getElementById(sectionId + '-complete')?.classList.remove('show');
  initFill(sectionId, state.data);
}
