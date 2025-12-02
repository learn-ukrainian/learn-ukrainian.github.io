// Order/Unjumble Activity
let orderScore = 0, orderTotal = 0;

function initOrder() {
  const c = document.getElementById('order-container');
  if (!c || !orderData.items.length) return;
  c.innerHTML = '';

  if (orderData.isUnjumble) {
    initUnjumble(c);
  } else {
    initClassicOrder(c);
  }
}

// UNJUMBLE: Drag-and-drop words to form sentences
function initUnjumble(container) {
  orderTotal = orderData.items.length;

  orderData.items.forEach((item, idx) => {
    const question = document.createElement('div');
    question.className = 'unjumble-question';
    question.dataset.idx = idx;

    // Shuffle words
    const shuffledWords = [...item.words].sort(() => Math.random() - 0.5);

    question.innerHTML = `
      <div class="unjumble-number">${idx + 1}.</div>
      <div class="unjumble-word-row" data-idx="${idx}">
        ${shuffledWords.map((word, i) => `
          <span class="unjumble-word" draggable="true" data-word="${word}">${word}</span>
        `).join('')}
      </div>
      <div class="unjumble-actions">
        <button class="btn btn-sm btn-outline unjumble-check" data-idx="${idx}">Check</button>
        <button class="btn btn-sm btn-outline unjumble-reset" data-idx="${idx}">Reset</button>
      </div>
      <div class="unjumble-feedback" data-idx="${idx}"></div>
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
    checkUnjumbleAnswer(parseInt(target.dataset.idx));
  }

  if (target.classList.contains('unjumble-reset')) {
    resetUnjumbleQuestion(parseInt(target.dataset.idx));
  }
}

function checkUnjumbleAnswer(idx) {
  const item = orderData.items[idx];
  const row = document.querySelector(`.unjumble-word-row[data-idx="${idx}"]`);
  const feedback = document.querySelector(`.unjumble-feedback[data-idx="${idx}"]`);
  const question = document.querySelector(`.unjumble-question[data-idx="${idx}"]`);

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
    orderScore++;
    document.getElementById('order-score').textContent = orderScore;

    feedback.innerHTML = `
      <span class="correct-text">✓ Correct!</span>
      <span class="translation">${item.translation || ''}</span>
    `;
    feedback.classList.add('show');

    if (orderScore === orderTotal) {
      document.getElementById('order-complete').classList.add('show');
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

function resetUnjumbleQuestion(idx) {
  const item = orderData.items[idx];
  const row = document.querySelector(`.unjumble-word-row[data-idx="${idx}"]`);
  const question = document.querySelector(`.unjumble-question[data-idx="${idx}"]`);
  const feedback = document.querySelector(`.unjumble-feedback[data-idx="${idx}"]`);

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
function initClassicOrder(container) {
  orderTotal = orderData.items.length;

  const shuffled = [...orderData.items].map((item, idx) => ({ text: item, origIdx: idx }));
  shuffled.sort(() => Math.random() - 0.5);

  const div = document.createElement('div');
  div.className = 'order-items';
  div.innerHTML = shuffled.map((item, i) => `
    <div class="order-item" draggable="true" data-orig="${item.origIdx}">
      <span class="order-handle">☰</span>
      <span class="order-text">${item.text}</span>
    </div>
  `).join('');
  container.appendChild(div);

  const checkBtn = document.createElement('button');
  checkBtn.className = 'btn btn-outline';
  checkBtn.textContent = 'Check Order';
  checkBtn.onclick = checkOrder;
  container.appendChild(checkBtn);

  initDragDrop();
}

function initDragDrop() {
  const items = document.querySelectorAll('.order-item');
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
      const container = item.parentNode;
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

function checkOrder() {
  const items = document.querySelectorAll('.order-item');
  const currentOrder = Array.from(items).map(item => parseInt(item.dataset.orig));

  let correct = true;
  currentOrder.forEach((val, idx) => {
    const expectedIdx = orderData.correctOrder.length ? orderData.correctOrder[idx] : idx;
    if (val !== expectedIdx) correct = false;
  });

  items.forEach((item, idx) => {
    const expectedIdx = orderData.correctOrder.length ? orderData.correctOrder[idx] : idx;
    if (parseInt(item.dataset.orig) === expectedIdx) {
      item.classList.add('correct');
      item.classList.remove('wrong');
    } else {
      item.classList.add('wrong');
      item.classList.remove('correct');
    }
  });

  if (correct) {
    orderScore = orderTotal;
    document.getElementById('order-score').textContent = orderScore;
    document.getElementById('order-complete').classList.add('show');
  }
}

function resetOrder() {
  orderScore = 0;
  document.getElementById('order-score').textContent = '0';
  document.getElementById('order-complete')?.classList.remove('show');
  initOrder();
}
