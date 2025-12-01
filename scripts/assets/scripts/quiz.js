// Quiz Activity
let quizScore = 0, quizAns = 0;

function initQuiz() {
  const c = document.getElementById('quiz-container');
  if (!c || !quizData.length) return;
  c.innerHTML = '';
  quizData.forEach((q, i) => {
    const sh = [...q.options].sort(() => Math.random() - 0.5);
    const cor = sh.indexOf(q.options[q.correctIndex]);
    const div = document.createElement('div');
    div.className = 'quiz-question';
    div.innerHTML = '<h4>Q' + (i + 1) + ': ' + q.question + '</h4><div class="quiz-options">' + sh.map((o, j) => '<div class="quiz-option" data-c="' + (j === cor) + '" data-q="' + i + '">' + o + '</div>').join('') + '</div><div class="quiz-explanation" id="exp-' + i + '">' + q.explanation + '</div>';
    c.appendChild(div);
  });
  document.querySelectorAll('.quiz-option').forEach(o => o.addEventListener('click', handleQuiz));
}

function handleQuiz(e) {
  const opt = e.target, q = opt.closest('.quiz-question');
  if (q.classList.contains('answered')) return;
  q.classList.add('answered');
  if (opt.dataset.c === 'true') {
    opt.classList.add('correct');
    quizScore++;
  } else {
    opt.classList.add('wrong');
    q.querySelector('[data-c="true"]').classList.add('correct');
  }
  document.getElementById('exp-' + opt.dataset.q).classList.add('show');
  document.getElementById('quiz-score').textContent = quizScore;
  quizAns++;
  if (quizAns === quizData.length) document.getElementById('quiz-complete').classList.add('show');
}

function resetQuiz() {
  quizScore = 0;
  quizAns = 0;
  document.getElementById('quiz-score').textContent = '0';
  document.getElementById('quiz-complete')?.classList.remove('show');
  initQuiz();
}
