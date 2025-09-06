document.addEventListener("DOMContentLoaded", function () {
  // Initialize game
  setupTipCarousel();
  setupGameCards();
});

function setupTipCarousel() {
  const tips = document.querySelectorAll(".tip");
  let currentTip = 0;

  // Show first tip
  tips[currentTip].classList.add("active");

  // Next tip button
  document.getElementById("nextTip").addEventListener("click", function () {
    tips[currentTip].classList.remove("active");
    currentTip = (currentTip + 1) % tips.length;
    tips[currentTip].classList.add("active");
  });
}

function setupGameCards() {
  document.querySelectorAll(".game-card").forEach((card) => {
    card.addEventListener("click", function () {
      const gameType = this.dataset.game;
      startGame(gameType);
    });
  });
}

function startGame(gameType) {
  switch (gameType) {
    case "quiz":
      startQuiz();
      break;
    case "budget":
      startBudgetChallenge();
      break;
    case "savings":
      startSavingsSimulator();
      break;
  }
}

function startQuiz() {
  const quizQuestions = [
    {
      question: "What is the recommended percentage of income to save?",
      options: ["5-10%", "10-15%", "15-20%", "20-25%"],
      answer: 2,
    },
    {
      question: "Which of these is NOT a good strategy for reducing debt?",
      options: [
        "Pay off high-interest debt first",
        "Make only minimum payments",
        "Consolidate debt with lower interest",
        "Create a debt repayment plan",
      ],
      answer: 1,
    },
    {
      question: "What is an emergency fund for?",
      options: [
        "Vacation expenses",
        "Unexpected financial emergencies",
        "Investment opportunities",
        "Luxury purchases",
      ],
      answer: 1,
    },
  ];

  let currentQuestion = 0;
  let score = 0;

  const quizModal = new bootstrap.Modal(document.getElementById("quizModal"));
  const quizContent = document.getElementById("quizContent");

  function showQuestion() {
    if (currentQuestion >= quizQuestions.length) {
      showResults();
      return;
    }

    const question = quizQuestions[currentQuestion];

    quizContent.innerHTML = `
          <h6>Question ${currentQuestion + 1} of ${quizQuestions.length}</h6>
          <p class="fw-bold">${question.question}</p>
          <div class="list-group">
              ${question.options
                .map(
                  (option, index) => `
                  <button type="button" class="list-group-item list-group-item-action" data-answer="${index}">
                      ${option}
                  </button>
              `
                )
                .join("")}
          </div>
      `;

    // Add event listeners to options
    quizContent.querySelectorAll(".list-group-item").forEach((button) => {
      button.addEventListener("click", function () {
        const selectedAnswer = parseInt(this.dataset.answer);
        if (selectedAnswer === question.answer) {
          score++;
          this.classList.add("list-group-item-success");
        } else {
          this.classList.add("list-group-item-danger");
          // Highlight correct answer
          quizContent
            .querySelector(`[data-answer="${question.answer}"]`)
            .classList.add("list-group-item-success");
        }

        // Move to next question after a delay
        setTimeout(() => {
          currentQuestion++;
          showQuestion();
        }, 1500);
      });
    });

    quizModal.show();
  }

  function showResults() {
    quizContent.innerHTML = `
          <div class="text-center">
              <h4>Quiz Completed!</h4>
              <div class="display-1 text-primary mb-3">
                  <i class="fas fa-trophy"></i>
              </div>
              <h5>Your Score: ${score}/${quizQuestions.length}</h5>
              <p>${
                score === quizQuestions.length
                  ? "Perfect! You're a financial expert!"
                  : score >= quizQuestions.length / 2
                  ? "Good job! Keep learning about personal finance."
                  : "Keep practicing! Financial knowledge is power."
              }</p>
              <button class="btn btn-primary" onclick="quizModal.hide()">Close</button>
          </div>
      `;
  }

  showQuestion();
}

function startBudgetChallenge() {
  alert(
    "Budget Challenge game would start here. This is a placeholder for the actual game implementation."
  );
}

function startSavingsSimulator() {
  alert(
    "Savings Simulator game would start here. This is a placeholder for the actual game implementation."
  );
}
