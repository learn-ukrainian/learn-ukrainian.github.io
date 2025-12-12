// Quiz Activity - supports multiple instances
const quizState = {};

function initQuiz(sectionId, data) {
  const c = document.getElementById(sectionId + '-container');
  if (!c || !data.questions || !data.questions.length) return;

  quizState[sectionId] = { score: 0, answered: 0, total: data.questions.length, data: data };

  c.innerHTML = '';
  data.questions.forEach((q, i) => {
    const sh = [...q.options].sort(() => Math.random() - 0.5);
    const cor = sh.indexOf(q.options[q.correctIndex]);
    const div = document.createElement('div');
    div.className = 'quiz-question';
    div.dataset.section = sectionId;
    div.innerHTML = '<h4>Q' + (i + 1) + ': ' + q.question + '</h4><div class="quiz-options">' + sh.map((o, j) => '<div class="quiz-option" data-c="' + (j === cor) + '" data-q="' + i + '" data-section="' + sectionId + '">' + o + '</div>').join('') + '</div><div class="quiz-explanation" id="' + sectionId + '-exp-' + i + '">' + (q.explanation || '') + '</div>';
    c.appendChild(div);
  });
  c.querySelectorAll('.quiz-option').forEach(o => o.addEventListener('click', handleQuiz));
}

function handleQuiz(e) {
  const opt = e.target, q = opt.closest('.quiz-question');
  const sectionId = opt.dataset.section;
  if (q.classList.contains('answered')) return;
  q.classList.add('answered');

  const state = quizState[sectionId];
  if (opt.dataset.c === 'true') {
    opt.classList.add('correct');
    state.score++;
  } else {
    opt.classList.add('wrong');
    q.querySelector('[data-c="true"]').classList.add('correct');
  }
  document.getElementById(sectionId + '-exp-' + opt.dataset.q)?.classList.add('show');
  document.getElementById(sectionId + '-score').textContent = state.score;
  state.answered++;
  if (state.answered === state.total) document.getElementById(sectionId + '-complete').classList.add('show');
}

function resetQuiz(sectionId) {
  const state = quizState[sectionId];
  if (!state) return;
  document.getElementById(sectionId + '-score').textContent = '0';
  document.getElementById(sectionId + '-complete')?.classList.remove('show');
  initQuiz(sectionId, state.data);
}
