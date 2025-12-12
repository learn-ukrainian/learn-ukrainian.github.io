// Order/Unjumble/Anagram Activity - supports multiple instances
const orderState = {};

/**
 * Shuffle array ensuring result is NEVER in the correct order.
 * Uses Fisher-Yates shuffle, then verifies result differs from correct order.
 * If same, keeps shuffling until different (max 10 attempts, then force swap).
 * @param {Array} arr - Array to shuffle (will be mutated)
 * @param {Array} correctOrder - The correct order to avoid
 * @returns {Array} - Shuffled array guaranteed different from correctOrder
 */
function shuffleNotCorrect(arr, correctOrder) {
  // Helper: check if two arrays are identical
  const arraysEqual = (a, b) => a.length === b.length && a.every((val, idx) => val === b[idx]);

  // Fisher-Yates shuffle
  const shuffle = (array) => {
    for (let i = array.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [array[i], array[j]] = [array[j], array[i]];
    }
    return array;
  };

  // Try shuffling up to 10 times to get a different order
  for (let attempt = 0; attempt < 10; attempt++) {
    shuffle(arr);
    if (!arraysEqual(arr, correctOrder)) {
      return arr;
    }
  }

  // If still same after 10 attempts (very unlikely), force a difference
  if (arr.length >= 2) {
    // Rotate array: move first element to end
    arr.push(arr.shift());
    // If still same, swap first two
    if (arraysEqual(arr, correctOrder)) {
      [arr[0], arr[1]] = [arr[1], arr[0]];
    }
  }

  return arr;
}

function initOrder(sectionId, data) {
  const c = document.getElementById(sectionId + '-container');
  if (!c || !data.items || !data.items.length) return;

  orderState[sectionId] = { score: 0, total: data.items.length, data: data };
  c.innerHTML = '';

  if (data.isAnagram) {
    initAnagram(sectionId, c, data);
  } else if (data.isUnjumble) {
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

    // Shuffle words - ensure NEVER in correct order (compare against ANSWER words)
    const correctOrder = item.answer.split(/\s+/);
    const shuffledWords = shuffleNotCorrect([...item.words], correctOrder);

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

  // Re-shuffle and rebuild - ensure NEVER in correct order (compare against ANSWER words)
  const correctOrder = item.answer.split(/\s+/);
  const shuffledWords = shuffleNotCorrect([...item.words], correctOrder);
  row.innerHTML = shuffledWords.map(word => `
    <span class="unjumble-word" draggable="true" data-word="${word}">${word}</span>
  `).join('');

  initUnjumbleDragDrop(row);

  question.classList.remove('wrong');
  row.classList.remove('wrong');
  feedback.innerHTML = '';
  feedback.classList.remove('show');
}

// ANAGRAM: Drag-and-drop letters to form a single word
function initAnagram(sectionId, container, data) {
  data.items.forEach((item, idx) => {
    const question = document.createElement('div');
    question.className = 'anagram-question';
    question.dataset.idx = idx;
    question.dataset.section = sectionId;

    // Shuffle letters - ensure NEVER in correct order (compare against ANSWER, not input)
    const correctOrder = item.answer.split('');
    const shuffledLetters = shuffleNotCorrect([...item.letters], correctOrder);

    question.innerHTML = `
      <div class="anagram-number">${idx + 1}.</div>
      <div class="anagram-letter-row" data-idx="${idx}" data-section="${sectionId}">
        ${shuffledLetters.map((letter, i) => `
          <span class="anagram-letter" draggable="true" data-letter="${letter}">${letter}</span>
        `).join('')}
      </div>
      <div class="anagram-actions">
        <button class="btn btn-sm btn-outline anagram-check" data-idx="${idx}" data-section="${sectionId}">Check</button>
        <button class="btn btn-sm btn-outline anagram-reset" data-idx="${idx}" data-section="${sectionId}">Reset</button>
      </div>
      <div class="anagram-feedback" data-idx="${idx}" data-section="${sectionId}"></div>
    `;

    container.appendChild(question);

    // Initialize drag-and-drop for this row
    initAnagramDragDrop(question.querySelector('.anagram-letter-row'));
  });

  // Event delegation for buttons
  container.addEventListener('click', handleAnagramClick);
}

function initAnagramDragDrop(row) {
  let dragItem = null;

  row.querySelectorAll('.anagram-letter').forEach(letter => {
    letter.addEventListener('dragstart', (e) => {
      dragItem = letter;
      letter.classList.add('dragging');
      e.dataTransfer.effectAllowed = 'move';
    });

    letter.addEventListener('dragend', () => {
      letter.classList.remove('dragging');
      dragItem = null;
    });

    letter.addEventListener('dragover', (e) => {
      e.preventDefault();
      if (!dragItem || dragItem === letter) return;

      const rect = letter.getBoundingClientRect();
      const midX = rect.left + rect.width / 2;

      if (e.clientX < midX) {
        row.insertBefore(dragItem, letter);
      } else {
        row.insertBefore(dragItem, letter.nextSibling);
      }
    });
  });

  // Touch support for mobile
  let touchItem = null;
  let touchClone = null;

  row.querySelectorAll('.anagram-letter').forEach(letter => {
    letter.addEventListener('touchstart', (e) => {
      touchItem = letter;
      letter.classList.add('dragging');

      // Create a clone for visual feedback
      touchClone = letter.cloneNode(true);
      touchClone.classList.add('touch-clone');
      document.body.appendChild(touchClone);
      updateAnagramTouchClone(e.touches[0], touchClone);
    });

    letter.addEventListener('touchmove', (e) => {
      e.preventDefault();
      if (!touchItem) return;
      updateAnagramTouchClone(e.touches[0], touchClone);

      // Find which letter we're over
      const touch = e.touches[0];
      const elements = document.elementsFromPoint(touch.clientX, touch.clientY);
      const targetLetter = elements.find(el => el.classList.contains('anagram-letter') && el !== touchItem);

      if (targetLetter && targetLetter.parentNode === row) {
        const rect = targetLetter.getBoundingClientRect();
        const midX = rect.left + rect.width / 2;
        if (touch.clientX < midX) {
          row.insertBefore(touchItem, targetLetter);
        } else {
          row.insertBefore(touchItem, targetLetter.nextSibling);
        }
      }
    });

    letter.addEventListener('touchend', () => {
      if (touchItem) touchItem.classList.remove('dragging');
      if (touchClone) touchClone.remove();
      touchItem = null;
      touchClone = null;
    });
  });

  function updateAnagramTouchClone(touch, clone) {
    if (clone) {
      clone.style.left = (touch.clientX - 20) + 'px';
      clone.style.top = (touch.clientY - 20) + 'px';
    }
  }
}

function handleAnagramClick(e) {
  const target = e.target;

  if (target.classList.contains('anagram-check')) {
    checkAnagramAnswer(target.dataset.section, parseInt(target.dataset.idx));
  }

  if (target.classList.contains('anagram-reset')) {
    resetAnagramQuestion(target.dataset.section, parseInt(target.dataset.idx));
  }
}

function checkAnagramAnswer(sectionId, idx) {
  const state = orderState[sectionId];
  const item = state.data.items[idx];
  const row = document.querySelector(`.anagram-letter-row[data-section="${sectionId}"][data-idx="${idx}"]`);
  const feedback = document.querySelector(`.anagram-feedback[data-section="${sectionId}"][data-idx="${idx}"]`);
  const question = document.querySelector(`.anagram-question[data-section="${sectionId}"][data-idx="${idx}"]`);

  // Build user's answer from current letter order
  const letters = row.querySelectorAll('.anagram-letter');
  const userAnswer = Array.from(letters).map(l => l.dataset.letter).join('');

  // Compare with correct answer
  const isCorrect = userAnswer.toLowerCase() === item.answer.toLowerCase();

  if (isCorrect) {
    question.classList.add('answered', 'correct');
    row.classList.add('correct');
    letters.forEach(l => l.setAttribute('draggable', 'false'));
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

function resetAnagramQuestion(sectionId, idx) {
  const state = orderState[sectionId];
  const item = state.data.items[idx];
  const row = document.querySelector(`.anagram-letter-row[data-section="${sectionId}"][data-idx="${idx}"]`);
  const question = document.querySelector(`.anagram-question[data-section="${sectionId}"][data-idx="${idx}"]`);
  const feedback = document.querySelector(`.anagram-feedback[data-section="${sectionId}"][data-idx="${idx}"]`);

  if (question.classList.contains('correct')) return;

  // Re-shuffle and rebuild - ensure NEVER in correct order (compare against ANSWER)
  const correctOrder = item.answer.split('');
  const shuffledLetters = shuffleNotCorrect([...item.letters], correctOrder);
  row.innerHTML = shuffledLetters.map(letter => `
    <span class="anagram-letter" draggable="true" data-letter="${letter}">${letter}</span>
  `).join('');

  initAnagramDragDrop(row);

  question.classList.remove('wrong');
  row.classList.remove('wrong');
  feedback.innerHTML = '';
  feedback.classList.remove('show');
}

// CLASSIC ORDER: Drag items into correct sequence
function initClassicOrder(sectionId, container, data) {
  const state = orderState[sectionId];

  // Create array with original indices, then shuffle
  const items = [...data.items].map((item, idx) => ({ text: item, origIdx: idx }));
  // Fisher-Yates shuffle
  for (let i = items.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [items[i], items[j]] = [items[j], items[i]];
  }

  // Create container div for all items
  const wrapper = document.createElement('div');
  wrapper.className = 'order-items-wrapper';
  wrapper.dataset.section = sectionId;

  // Create each sentence as a draggable item
  items.forEach((item, i) => {
    const div = document.createElement('div');
    div.className = 'order-sentence-card';
    div.draggable = true;
    div.dataset.orig = item.origIdx;
    div.dataset.section = sectionId;
    div.innerHTML = '<span class="order-card-num">' + (i + 1) + '</span><span class="order-card-text">' + item.text + '</span>';
    wrapper.appendChild(div);
  });

  container.appendChild(wrapper);

  // Add buttons
  const btnDiv = document.createElement('div');
  btnDiv.className = 'order-buttons';
  btnDiv.innerHTML = '<button class="btn btn-outline order-check-btn" data-section="' + sectionId + '">Check Order</button>';
  container.appendChild(btnDiv);

  // Add feedback area
  const feedback = document.createElement('div');
  feedback.className = 'order-feedback';
  feedback.dataset.section = sectionId;
  container.appendChild(feedback);

  // Initialize drag-and-drop
  initOrderCardDragDrop(wrapper);

  // Button click handler
  btnDiv.querySelector('.order-check-btn').onclick = function() { checkOrder(sectionId); };
}

function initOrderCardDragDrop(wrapper) {
  let dragItem = null;

  wrapper.querySelectorAll('.order-sentence-card').forEach(function(card) {
    card.addEventListener('dragstart', function(e) {
      dragItem = card;
      card.classList.add('dragging');
      e.dataTransfer.effectAllowed = 'move';
    });

    card.addEventListener('dragend', function() {
      card.classList.remove('dragging');
      dragItem = null;
      updateCardNumbers(wrapper);
    });

    card.addEventListener('dragover', function(e) {
      e.preventDefault();
      if (!dragItem || dragItem === card) return;
      const rect = card.getBoundingClientRect();
      const midY = rect.top + rect.height / 2;
      if (e.clientY < midY) {
        wrapper.insertBefore(dragItem, card);
      } else {
        wrapper.insertBefore(dragItem, card.nextSibling);
      }
    });
  });

  // Touch support
  let touchItem = null;
  let touchClone = null;

  wrapper.querySelectorAll('.order-sentence-card').forEach(function(card) {
    card.addEventListener('touchstart', function(e) {
      touchItem = card;
      card.classList.add('dragging');
      touchClone = card.cloneNode(true);
      touchClone.style.position = 'fixed';
      touchClone.style.zIndex = '1000';
      touchClone.style.pointerEvents = 'none';
      touchClone.style.opacity = '0.8';
      touchClone.style.maxWidth = '90vw';
      document.body.appendChild(touchClone);
      moveTouchClone(e.touches[0]);
    });

    card.addEventListener('touchmove', function(e) {
      e.preventDefault();
      if (!touchItem) return;
      moveTouchClone(e.touches[0]);
      const touch = e.touches[0];
      const els = document.elementsFromPoint(touch.clientX, touch.clientY);
      const target = els.find(function(el) { return el.classList.contains('order-sentence-card') && el !== touchItem; });
      if (target && target.parentNode === wrapper) {
        const rect = target.getBoundingClientRect();
        const midY = rect.top + rect.height / 2;
        if (touch.clientY < midY) {
          wrapper.insertBefore(touchItem, target);
        } else {
          wrapper.insertBefore(touchItem, target.nextSibling);
        }
      }
    });

    card.addEventListener('touchend', function() {
      if (touchItem) touchItem.classList.remove('dragging');
      if (touchClone) touchClone.remove();
      touchItem = null;
      touchClone = null;
      updateCardNumbers(wrapper);
    });
  });

  function moveTouchClone(touch) {
    if (touchClone) {
      touchClone.style.left = (touch.clientX - 100) + 'px';
      touchClone.style.top = (touch.clientY - 25) + 'px';
    }
  }
}

function updateCardNumbers(wrapper) {
  wrapper.querySelectorAll('.order-sentence-card').forEach(function(card, i) {
    card.querySelector('.order-card-num').textContent = i + 1;
  });
}

function initOrderSentenceDragDrop(row) {
  let dragItem = null;

  row.querySelectorAll('.order-sentence-item').forEach(item => {
    item.addEventListener('dragstart', (e) => {
      dragItem = item;
      item.classList.add('dragging');
      e.dataTransfer.effectAllowed = 'move';
    });

    item.addEventListener('dragend', () => {
      item.classList.remove('dragging');
      dragItem = null;
      // Update numbers after drag
      updateOrderNumbers(row);
    });

    item.addEventListener('dragover', (e) => {
      e.preventDefault();
      if (!dragItem || dragItem === item) return;

      const rect = item.getBoundingClientRect();
      const midY = rect.top + rect.height / 2;

      if (e.clientY < midY) {
        row.insertBefore(dragItem, item);
      } else {
        row.insertBefore(dragItem, item.nextSibling);
      }
    });
  });

  // Touch support
  let touchItem = null;
  let touchClone = null;

  row.querySelectorAll('.order-sentence-item').forEach(item => {
    item.addEventListener('touchstart', (e) => {
      touchItem = item;
      item.classList.add('dragging');
      touchClone = item.cloneNode(true);
      touchClone.classList.add('touch-clone');
      document.body.appendChild(touchClone);
      updateTouchClonePos(e.touches[0], touchClone);
    });

    item.addEventListener('touchmove', (e) => {
      e.preventDefault();
      if (!touchItem) return;
      updateTouchClonePos(e.touches[0], touchClone);

      const touch = e.touches[0];
      const elements = document.elementsFromPoint(touch.clientX, touch.clientY);
      const target = elements.find(el => el.classList.contains('order-sentence-item') && el !== touchItem);

      if (target && target.parentNode === row) {
        const rect = target.getBoundingClientRect();
        const midY = rect.top + rect.height / 2;
        if (touch.clientY < midY) {
          row.insertBefore(touchItem, target);
        } else {
          row.insertBefore(touchItem, target.nextSibling);
        }
      }
    });

    item.addEventListener('touchend', () => {
      if (touchItem) touchItem.classList.remove('dragging');
      if (touchClone) touchClone.remove();
      touchItem = null;
      touchClone = null;
      updateOrderNumbers(row);
    });
  });

  function updateTouchClonePos(touch, clone) {
    if (clone) {
      clone.style.left = (touch.clientX - 100) + 'px';
      clone.style.top = (touch.clientY - 20) + 'px';
    }
  }
}

function updateOrderNumbers(row) {
  row.querySelectorAll('.order-sentence-item').forEach((item, i) => {
    item.querySelector('.order-num').textContent = i + 1;
  });
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
  // Support multiple class names for order items
  let items = document.querySelectorAll('.order-sentence-card[data-section="' + sectionId + '"]');
  if (!items.length) {
    items = document.querySelectorAll('.order-sentence-item[data-section="' + sectionId + '"]');
  }
  if (!items.length) {
    items = document.querySelectorAll('.order-item[data-section="' + sectionId + '"]');
  }
  const currentOrder = Array.from(items).map(function(item) { return parseInt(item.dataset.orig); });
  const feedback = document.querySelector('.order-feedback[data-section="' + sectionId + '"]');

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
    if (feedback) {
      feedback.innerHTML = '<span class="correct-text">✓ Perfect order!</span>';
      feedback.classList.add('show');
    }
  } else {
    if (feedback) {
      feedback.innerHTML = '<span class="wrong-text">✗ Not quite right. Try again!</span>';
      feedback.classList.add('show');
    }
    setTimeout(function() {
      items.forEach(function(item) { item.classList.remove('wrong'); });
      if (feedback) feedback.classList.remove('show');
    }, 2000);
  }
}

function resetOrder(sectionId) {
  const state = orderState[sectionId];
  if (!state) return;
  document.getElementById(sectionId + '-score').textContent = '0';
  document.getElementById(sectionId + '-complete')?.classList.remove('show');
  initOrder(sectionId, state.data);
}
