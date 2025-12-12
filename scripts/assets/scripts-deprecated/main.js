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

// Activity reset dispatcher
function resetActivity(sectionId) {
  const activity = activitiesData.find(a => a.id === sectionId);
  if (!activity) return;

  switch (activity.type) {
    case 'match-up':
      resetMatch(sectionId);
      break;
    case 'quiz':
      resetQuiz(sectionId);
      break;
    case 'true-false':
      resetTf(sectionId);
      break;
    case 'group-sort':
      resetSort(sectionId);
      break;
    case 'fill-blank':
    case 'gap-fill':
      resetFill(sectionId);
      break;
    case 'unjumble':
    case 'anagram':
      resetOrder(sectionId);
      break;
    case 'select':
      resetSelect(sectionId);
      break;
    case 'error-correction':
      resetErrorCorrection(sectionId);
      break;
  }
}




// Forvo Integration (Community Native Audio)
// Opens a specific word page on Forvo in a popup window.
function openForvo(text) {
  if (!text) return;

  // URL Encode the text (handles Cyrillic)
  const encodedText = encodeURIComponent(text);
  // Use Search URL with language filter 'uk' to avoid Russian results
  const url = `https://forvo.com/search/${encodedText}/uk/`;

  // Open popup
  const width = 800;
  const height = 600;
  const left = (window.innerWidth - width) / 2;
  const top = (window.innerHeight - height) / 2;

  window.open(
    url,
    'forvo_window',
    `width=${width},height=${height},top=${top},left=${left},resizable=yes,scrollbars=yes`
  );
}

// Initialize all activities from activitiesData array
document.addEventListener('DOMContentLoaded', () => {
  if (typeof activitiesData === 'undefined') return;

  activitiesData.forEach(activity => {
    switch (activity.type) {
      case 'match-up':
        initMatch(activity.id, activity.data);
        break;
      case 'quiz':
        initQuiz(activity.id, activity.data);
        break;
      case 'true-false':
        initTf(activity.id, activity.data);
        break;
      case 'group-sort':
        initSort(activity.id, activity.data);
        break;
      case 'fill-blank':
      case 'gap-fill':
        initFill(activity.id, activity.data);
        break;
      case 'unjumble':
      case 'anagram':
        initOrder(activity.id, activity.data);
        break;
      case 'select':
        initSelect(activity.id, activity.data);
        break;
      case 'error-correction':
        initErrorCorrection(activity.id, activity.data);
        break;
    }
  });

  // Initialize vocabulary
  if (typeof initVocab === 'function') initVocab();
});
