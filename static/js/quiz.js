document.addEventListener('DOMContentLoaded', () => {
  const cards = Array.from(document.querySelectorAll('.quiz-card'));
  if (!cards.length) return;

  const counter = document.querySelector('#quiz-counter');
  const progress = document.querySelector('#quiz-progress');
  const complete = document.querySelector('.quiz-complete');
  let activeIndex = 0;
  let startedAt = performance.now();

  function setActive(index) {
    cards.forEach((card, cardIndex) => card.classList.toggle('active', cardIndex === index));
    activeIndex = index;
    startedAt = performance.now();
    if (counter) counter.textContent = `Card ${index + 1} of ${cards.length}`;
    if (progress) progress.style.width = `${(index / cards.length) * 100}%`;
  }

  function getUserAnswer(card) {
    const selected = card.querySelector('input[type="radio"]:checked');
    if (selected) return selected.value;
    const input = card.querySelector('[data-answer-input]');
    return input ? input.value : '';
  }

  function lockCard(card) {
    card.querySelectorAll('button, input, textarea').forEach((element) => {
      if (!element.classList.contains('next-card')) element.disabled = true;
    });
  }

  function showResult(card, data) {
    const result = card.querySelector('.result');
    const panel = card.querySelector('.answer-panel');
    if (panel) panel.hidden = false;
    if (result) {
      result.textContent = data.is_correct ? 'Correct — progress updated.' : `Missed — correct answer: ${data.correct_answer}`;
      result.classList.toggle('good', data.is_correct);
      result.classList.toggle('bad', !data.is_correct);
    }
    lockCard(card);
    const nextButton = card.querySelector('.next-card');
    if (nextButton) {
      nextButton.hidden = false;
      nextButton.disabled = false;
      nextButton.textContent = activeIndex === cards.length - 1 ? 'Finish quiz' : 'Next card';
    }
  }

  async function postAttempt(card, { isCorrect = null } = {}) {
    if (card.dataset.submitted === 'true' || card.dataset.submitting === 'true') return;
    card.dataset.submitting = 'true';

    const payload = {
      card_id: card.dataset.cardId,
      user_answer: getUserAnswer(card),
      elapsed_ms: Math.round(performance.now() - startedAt),
    };
    if (isCorrect !== null) payload.is_correct = isCorrect;

    const response = await fetch('/api/attempts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Unable to save attempt');
    card.dataset.submitted = 'true';
    showResult(card, data);
  }

  document.querySelectorAll('.reveal-answer').forEach((button) => {
    button.addEventListener('click', () => {
      const card = button.closest('.quiz-card');
      const panel = card.querySelector('.answer-panel');
      const selfGrade = card.querySelector('.self-grade');
      if (panel) panel.hidden = false;
      if (selfGrade) selfGrade.hidden = false;
      button.disabled = true;
    });
  });

  document.querySelectorAll('.submit-answer').forEach((button) => {
    button.addEventListener('click', async () => {
      const card = button.closest('.quiz-card');
      const result = card.querySelector('.result');
      const answer = getUserAnswer(card).trim();
      if (!answer) {
        if (result) {
          result.textContent = 'Enter or choose an answer before submitting.';
          result.classList.add('bad');
        }
        return;
      }

      try {
        button.disabled = true;
        await postAttempt(card);
      } catch (error) {
        card.dataset.submitting = 'false';
        button.disabled = false;
        if (result) {
          result.textContent = error.message;
          result.classList.add('bad');
        }
      }
    });
  });

  document.querySelectorAll('.grade-answer').forEach((button) => {
    button.addEventListener('click', async () => {
      const card = button.closest('.quiz-card');
      const result = card.querySelector('.result');
      const isCorrect = button.dataset.correct === 'true';
      const gradeButtons = card.querySelectorAll('.grade-answer');
      try {
        gradeButtons.forEach((gradeButton) => { gradeButton.disabled = true; });
        await postAttempt(card, { isCorrect });
      } catch (error) {
        card.dataset.submitting = 'false';
        gradeButtons.forEach((gradeButton) => { gradeButton.disabled = false; });
        if (result) {
          result.textContent = error.message;
          result.classList.add('bad');
        }
      }
    });
  });

  document.querySelectorAll('.next-card').forEach((button) => {
    button.addEventListener('click', () => {
      if (activeIndex >= cards.length - 1) {
        cards[activeIndex].classList.remove('active');
        if (counter) counter.textContent = 'Complete';
        if (progress) progress.style.width = '100%';
        if (complete) complete.hidden = false;
        return;
      }
      setActive(activeIndex + 1);
    });
  });

  setActive(0);
});
