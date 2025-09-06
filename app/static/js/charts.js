document.addEventListener("DOMContentLoaded", function () {
  let currentTimeframe = "30d";

  // Initialize charts
  loadCharts(currentTimeframe);

  // Event listeners for timeframe buttons
  document.querySelectorAll(".timeframe-btn").forEach((button) => {
    button.addEventListener("click", function () {
      currentTimeframe = this.dataset.timeframe;
      document.querySelector(
        ".dropdown-toggle"
      ).textContent = `Timeframe: ${this.textContent}`;
      loadCharts(currentTimeframe);
    });
  });
});

function loadCharts(timeframe) {
  loadIncomeExpenseChart(timeframe);
  loadExpenseCategoryChart(timeframe);
  loadIncomeCategoryChart(timeframe);
  loadAccountBalanceChart();
}

function loadIncomeExpenseChart(timeframe) {
  fetch(`/api/charts/income-vs-expense?timeframe=${timeframe}`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  })
    .then((response) => response.json())
    .then((data) => {
      const ctx = document
        .getElementById("incomeExpenseChart")
        .getContext("2d");

      if (window.incomeExpenseChart) {
        window.incomeExpenseChart.destroy();
      }

      window.incomeExpenseChart = new Chart(ctx, {
        type: "bar",
        data: {
          labels: ["Income", "Expense", "Net Flow"],
          datasets: [
            {
              label: "Amount ($)",
              data: [data.total_income, data.total_expense, data.net_flow],
              backgroundColor: [
                "rgba(54, 185, 204, 0.7)",
                "rgba(231, 74, 59, 0.7)",
                "rgba(28, 200, 138, 0.7)",
              ],
              borderColor: [
                "rgb(54, 185, 204)",
                "rgb(231, 74, 59)",
                "rgb(28, 200, 138)",
              ],
              borderWidth: 1,
            },
          ],
        },
        options: {
          responsive: true,
          plugins: {
            legend: {
              display: false,
            },
            title: {
              display: true,
              text: "Income vs Expense",
            },
          },
          scales: {
            y: {
              beginAtZero: true,
            },
          },
        },
      });
    })
    .catch((error) => {
      console.error("Error loading income vs expense chart:", error);
    });
}

function loadExpenseCategoryChart(timeframe) {
  fetch(`/api/charts/expense-by-category?timeframe=${timeframe}`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  })
    .then((response) => response.json())
    .then((data) => {
      const ctx = document
        .getElementById("expenseCategoryChart")
        .getContext("2d");

      if (window.expenseCategoryChart) {
        window.expenseCategoryChart.destroy();
      }

      const labels = Object.keys(data);
      const values = Object.values(data);

      // Generate colors for each category
      const backgroundColors = generateColors(labels.length);

      window.expenseCategoryChart = new Chart(ctx, {
        type: "doughnut",
        data: {
          labels: labels,
          datasets: [
            {
              data: values,
              backgroundColor: backgroundColors,
              borderWidth: 1,
            },
          ],
        },
        options: {
          responsive: true,
          plugins: {
            legend: {
              position: "right",
            },
            title: {
              display: true,
              text: "Expenses by Category",
            },
          },
        },
      });
    })
    .catch((error) => {
      console.error("Error loading expense category chart:", error);
    });
}

function loadIncomeCategoryChart(timeframe) {
  fetch(`/api/charts/income-by-category?timeframe=${timeframe}`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  })
    .then((response) => response.json())
    .then((data) => {
      const ctx = document
        .getElementById("incomeCategoryChart")
        .getContext("2d");

      if (window.incomeCategoryChart) {
        window.incomeCategoryChart.destroy();
      }

      const labels = Object.keys(data);
      const values = Object.values(data);

      // Generate colors for each category
      const backgroundColors = generateColors(labels.length);

      window.incomeCategoryChart = new Chart(ctx, {
        type: "pie",
        data: {
          labels: labels,
          datasets: [
            {
              data: values,
              backgroundColor: backgroundColors,
              borderWidth: 1,
            },
          ],
        },
        options: {
          responsive: true,
          plugins: {
            legend: {
              position: "right",
            },
            title: {
              display: true,
              text: "Income by Category",
            },
          },
        },
      });
    })
    .catch((error) => {
      console.error("Error loading income category chart:", error);
    });
}

function loadAccountBalanceChart() {
  fetch("/api/charts/account-balances", {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  })
    .then((response) => response.json())
    .then((data) => {
      const ctx = document
        .getElementById("accountBalanceChart")
        .getContext("2d");

      if (window.accountBalanceChart) {
        window.accountBalanceChart.destroy();
      }

      // Generate colors for each account
      const backgroundColors = generateColors(data.labels.length);

      window.accountBalanceChart = new Chart(ctx, {
        type: "bar",
        data: {
          labels: data.labels,
          datasets: [
            {
              label: "Balance ($)",
              data: data.balances,
              backgroundColor: backgroundColors,
              borderWidth: 1,
            },
          ],
        },
        options: {
          responsive: true,
          plugins: {
            legend: {
              display: false,
            },
            title: {
              display: true,
              text: "Account Balances",
            },
          },
          scales: {
            y: {
              beginAtZero: true,
            },
          },
        },
      });
    })
    .catch((error) => {
      console.error("Error loading account balance chart:", error);
    });
}

function generateColors(count) {
  const colors = [];
  for (let i = 0; i < count; i++) {
    const hue = ((i * 360) / count) % 360;
    colors.push(`hsla(${hue}, 70%, 65%, 0.7)`);
  }
  return colors;
}
