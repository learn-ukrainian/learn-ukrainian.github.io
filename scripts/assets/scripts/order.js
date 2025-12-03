// Order/Unjumble Activity - supports multiple instances
const orderState = {};

function initOrder(sectionId, data) {
  const c = document.getElementById(sectionId + '-container');
  if (!c || !data.items || !data.items.length) return;

  orderState[sectionId] = { score: 0, total: data.items.length, data: data };
  c.innerHTML = '';

  if (data.isUnjumble) {
    initUnjumble(sectionId, c, data);
  } else {
    initClassicOrder(sectionId, c, data);
  }
}

// UNJUMBLE: Drag-and-drop words to form sentences
function initUnjumble(sectionId, container, data) {
  data.items.forEach((item, idx) => {
    const question = document.createElement('div');
    question.className = 'unjumble-question';
    question.dataset.idx = idx;
    question.dataset.section = sectionId;

    // Shuffle words
    const shuffledWords = [...item.words].sort(() => Math.random() - 0.5);

    question.innerHTML = `
      <div class="unjumble-number">${idx + 1}.</div>
      <div class="unjumble-word-row" data-idx="${idx}" data-section="${sectionId}">
        ${shuffledWords.map((word, i) => `
          <span class="unjumble-word" draggable="true" data-word="${word}">${word}</span>
        `).join('')}
      </div>
      <div class="unjumble-actions">
        <button class="btn btn-sm btn-outline unjumble-check" data-idx="${idx}" data-section="${sectionId}">Check</button>
        <button class="btn btn-sm btn-outline unjumble-reset" data-idx="${idx}" data-section="${sectionId}">Reset</button>
      </div>
      <div class="unjumble-feedback" data-idx="${idx}" data-section="${sectionId}"></div>
    `;

    container.appendChild(question);

    // Initialize drag-and-drop for this row
    initUnjumbleDragDrop(question.querySelector('.unjumble-word-row'));
  });

  // Event delegation for buttons
  container.addEventListener('click', handleUnjumbleClick);
}

function initUnjumbleDragDrop(row) {
  let dragItem = null;

  row.querySelectorAll('.unjumble-word').forEach(word => {
    word.addEventListener('dragstart', (e) => {
      dragItem = word;
      word.classList.add('dragging');
      e.dataTransfer.effectAllowed = 'move';
    });

    word.addEventListener('dragend', () => {
      word.classList.remove('dragging');
      dragItem = null;
    });

    word.addEventListener('dragover', (e) => {
      e.preventDefault();
      if (!dragItem || dragItem === word) return;

      const rect = word.getBoundingClientRect();
      const midX = rect.left + rect.width / 2;

      if (e.clientX < midX) {
        row.insertBefore(dragItem, word);
      } else {
        row.insertBefore(dragItem, word.nextSibling);
      }
    });
  });

  // Touch support for mobile
  let touchItem = null;
  let touchClone = null;

  row.querySelectorAll('.unjumble-word').forEach(word => {
    word.addEventListener('touchstart', (e) => {
      touchItem = word;
      word.classList.add('dragging');

      // Create a clone for visual feedback
      touchClone = word.cloneNode(true);
      touchClone.classList.add('touch-clone');
      document.body.appendChild(touchClone);
      updateTouchClone(e.touches[0]);
    });

    word.addEventListener('touchmove', (e) => {
      e.preventDefault();
      if (!touchItem) return;
      updateTouchClone(e.touches[0]);

      // Find which word we're over
      const touch = e.touches[0];
      const elements = document.elementsFromPoint(touch.clientX, touch.clientY);
      const targetWord = elements.find(el => el.classList.contains('unjumble-word') && el !== touchItem);

      if (targetWord && targetWord.parentNode === row) {
        const rect = targetWord.getBoundingClientRect();
        const midX = rect.left + rect.width / 2;
        if (touch.clientX < midX) {
          row.insertBefore(touchItem, targetWord);
        } else {
          row.insertBefore(touchItem, targetWord.nextSibling);
        }
      }
    });

    word.addEventListener('touchend', () => {
      if (touchItem) touchItem.classList.remove('dragging');
      if (touchClone) touchClone.remove();
      touchItem = null;
      touchClone = null;
    });
  });

  function updateTouchClone(touch) {
    if (touchClone) {
      touchClone.style.left = (touch.clientX - 40) + 'px';
      touchClone.style.top = (touch.clientY - 20) + 'px';
    }
  }
}

function handleUnjumbleClick(e) {
  const target = e.target;

  if (target.classList.contains('unjumble-check')) {
    checkUnjumbleAnswer(target.dataset.section, parseInt(target.dataset.idx));
  }

  if (target.classList.contains('unjumble-reset')) {
    resetUnjumbleQuestion(target.dataset.section, parseInt(target.dataset.idx));
  }
}

function checkUnjumbleAnswer(sectionId, idx) {
  const state = orderState[sectionId];
  const item = state.data.items[idx];
  const row = document.querySelector(`.unjumble-word-row[data-section="${sectionId}"][data-idx="${idx}"]`);
  const feedback = document.querySelector(`.unjumble-feedback[data-section="${sectionId}"][data-idx="${idx}"]`);
  const question = document.querySelector(`.unjumble-question[data-section="${sectionId}"][data-idx="${idx}"]`);

  // Build user's answer from current word order
  const words = row.querySelectorAll('.unjumble-word');
  const userAnswer = Array.from(words).map(w => w.dataset.word).join(' ');

  // Normalize for comparison (handle punctuation)
  const normalize = (s) => s.replace(/[?!.,]/g, '').toLowerCase().trim();
  const isCorrect = normalize(userAnswer) === normalize(item.answer);

  if (isCorrect) {
    question.classList.add('answered', 'correct');
    row.classList.add('correct');
    words.forEach(w => w.setAttribute('draggable', 'false'));
    state.score++;
    document.getElementById(sectionId + '-score').textContent = state.score;

    feedback.innerHTML = `
      <span class="correct-text">✓ Correct!</span>
      <span class="translation">${item.translation || ''}</span>
    `;
    feedback.classList.add('show');

    if (state.score === state.total) {
      document.getElementById(sectionId + '-complete').classList.add('show');
    }
  } else {
    question.classList.add('wrong');
    row.classList.add('wrong');

    feedback.innerHTML = `
      <span class="wrong-text">✗ Try again. Hint: ${item.answer}</span>
    `;
    feedback.classList.add('show');

    setTimeout(() => {
      question.classList.remove('wrong');
      row.classList.remove('wrong');
      feedback.classList.remove('show');
    }, 2000);
  }
}

function resetUnjumbleQuestion(sectionId, idx) {
  const state = orderState[sectionId];
  const item = state.data.items[idx];
  const row = document.querySelector(`.unjumble-word-row[data-section="${sectionId}"][data-idx="${idx}"]`);
  const question = document.querySelector(`.unjumble-question[data-section="${sectionId}"][data-idx="${idx}"]`);
  const feedback = document.querySelector(`.unjumble-feedback[data-section="${sectionId}"][data-idx="${idx}"]`);

  if (question.classList.contains('correct')) return;

  // Re-shuffle and rebuild
  const shuffledWords = [...item.words].sort(() => Math.random() - 0.5);
  row.innerHTML = shuffledWords.map(word => `
    <span class="unjumble-word" draggable="true" data-word="${word}">${word}</span>
  `).join('');

  initUnjumbleDragDrop(row);

  question.classList.remove('wrong');
  row.classList.remove('wrong');
  feedback.innerHTML = '';
  feedback.classList.remove('show');
}

// CLASSIC ORDER: Drag items into correct sequence
function initClassicOrder(sectionId, container, data) {
  const state = orderState[sectionId];

  const shuffled = [...data.items].map((item, idx) => ({ text: item, origIdx: idx }));
  shuffled.sort(() => Math.random() - 0.5);

  const div = document.createElement('div');
  div.className = 'order-items';
  div.dataset.section = sectionId;
  div.innerHTML = shuffled.map((item, i) => `
    <div class="order-item" draggable="true" data-orig="${item.origIdx}" data-section="${sectionId}">
      <span class="order-handle">☰</span>
      <span class="order-text">${item.text}</span>
    </div>
  `).join('');
  container.appendChild(div);

  const checkBtn = document.createElement('button');
  checkBtn.className = 'btn btn-outline';
  checkBtn.textContent = 'Check Order';
  checkBtn.onclick = () => checkOrder(sectionId);
  container.appendChild(checkBtn);

  initDragDrop(div);
}

function initDragDrop(container) {
  const items = container.querySelectorAll('.order-item');
  let dragItem = null;

  items.forEach(item => {
    item.addEventListener('dragstart', (e) => {
      dragItem = item;
      item.classList.add('dragging');
    });

    item.addEventListener('dragend', () => {
      item.classList.remove('dragging');
      dragItem = null;
    });

    item.addEventListener('dragover', (e) => {
      e.preventDefault();
      if (!dragItem || dragItem === item) return;
      const rect = item.getBoundingClientRect();
      const midY = rect.top + rect.height / 2;
      if (e.clientY < midY) {
        container.insertBefore(dragItem, item);
      } else {
        container.insertBefore(dragItem, item.nextSibling);
      }
    });
  });
}

function checkOrder(sectionId) {
  const state = orderState[sectionId];
  const data = state.data;
  const items = document.querySelectorAll(`.order-item[data-section="${sectionId}"]`);
  const currentOrder = Array.from(items).map(item => parseInt(item.dataset.orig));

  let correct = true;
  currentOrder.forEach((val, idx) => {
    const expectedIdx = data.correctOrder && data.correctOrder.length ? data.correctOrder[idx] : idx;
    if (val !== expectedIdx) correct = false;
  });

  items.forEach((item, idx) => {
    const expectedIdx = data.correctOrder && data.correctOrder.length ? data.correctOrder[idx] : idx;
    if (parseInt(item.dataset.orig) === expectedIdx) {
      item.classList.add('correct');
      item.classList.remove('wrong');
    } else {
      item.classList.add('wrong');
      item.classList.remove('correct');
    }
  });

  if (correct) {
    state.score = state.total;
    document.getElementById(sectionId + '-score').textContent = state.score;
    document.getElementById(sectionId + '-complete').classList.add('show');
  }
}

function resetOrder(sectionId) {
  const state = orderState[sectionId];
  if (!state) return;
  document.getElementById(sectionId + '-score').textContent = '0';
  document.getElementById(sectionId + '-complete')?.classList.remove('show');
  initOrder(sectionId, state.data);
}
