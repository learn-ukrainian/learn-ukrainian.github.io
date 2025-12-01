// Answer callout toggle (for new > [!answer] syntax)
function toggleAnswer(id, btn) {
  const el = document.getElementById(id);
  if (!el) return;
  const isUkrainian = document.querySelector('.level-badge')?.textContent.match(/B[12]|C[12]/);
  const showText = isUkrainian ? 'Показати відповідь' : 'Show Answer';
  const hideText = isUkrainian ? 'Сховати відповідь' : 'Hide Answer';
  const show = !el.classList.contains('show');
  if (show) {
    el.classList.add('show');
    btn.textContent = hideText;
    btn.classList.add('revealed');
  } else {
    el.classList.remove('show');
    btn.textContent = showText;
    btn.classList.remove('revealed');
  }
}

// Section navigation
function showSection(id) {
  document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
  document.getElementById(id)?.classList.add('active');
  document.querySelector('[data-section="' + id + '"]')?.classList.add('active');
}
document.querySelectorAll('.nav-tab').forEach(t => t.addEventListener('click', () => showSection(t.dataset.section)));

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
  initQuiz();
  initSort();
  initVocab();
});
